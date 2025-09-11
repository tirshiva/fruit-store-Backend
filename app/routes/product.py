from typing import List, Optional
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.utils.deps import get_db
from app.model.product import Product
from app.schemas.product import ProductUpdate, ProductOut
from app.schemas.common import ApiResponse
from app.utils.response import success_response

router = APIRouter(tags=["Products"])

UPLOAD_ROOT = Path("uploads")
PRODUCTS_SUBDIR = UPLOAD_ROOT / "products"
PRODUCTS_SUBDIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _save_image(file: UploadFile, subdir: Path = PRODUCTS_SUBDIR) -> str:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image type. Allowed: JPEG, PNG, WEBP",
        )

    suffix = ALLOWED_IMAGE_TYPES[file.content_type]
    unique_name = f"{uuid.uuid4().hex}{suffix}"
    out_path = subdir / unique_name

    with out_path.open("wb") as f:
        f.write(file.file.read())

    # Public path served by StaticFiles in main.py
    return f"/uploads/{subdir.relative_to(UPLOAD_ROOT)}/{unique_name}"


def _delete_local_image_if_owned(image_path: Optional[str]) -> None:
    """
    Delete an image file from disk if it resides under our uploads/products directory.
    Accepts public paths like "/uploads/products/<file>" and ignores external URLs.
    """
    if not image_path:
        return
    try:
        # Only handle our served uploads path
        if not image_path.startswith("/uploads/"):
            return
        # Normalize to filesystem path under uploads root
        # Example: "/uploads/products/abc.jpg" -> uploads/products/abc.jpg
        rel_part = image_path.lstrip("/").split("/", 1)[1] if "/" in image_path.lstrip("/") else ""
        fs_path = UPLOAD_ROOT / rel_part
        # Restrict deletion to the products subdirectory
        try:
            fs_path_relative_to_products = fs_path.resolve().relative_to(PRODUCTS_SUBDIR.resolve())
        except Exception:
            return
        if fs_path.exists() and fs_path.is_file():
            fs_path.unlink(missing_ok=True)
    except Exception:
        # Best-effort cleanup; do not block deletion on file errors
        pass


@router.get("/api/products", response_model=ApiResponse[List[ProductOut]])
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return success_response(
        "Products fetched successfully",
        [ProductOut.model_validate(p) for p in products],
    )


@router.post("/api/products", response_model=ApiResponse[ProductOut], status_code=status.HTTP_201_CREATED)
def create_product(
    name: str = Form(...),
    price_per_kg: float = Form(..., alias="price_per_kg"),
    in_stock: bool = Form(True, alias="inStock"),
    image_file: Optional[UploadFile] = File(None),
    image: Optional[str] = Form(None),  # URL or relative path
    db: Session = Depends(get_db),
):
    # Auto-handle mutual exclusivity
    if image_file and image:
        # Prefer the uploaded file
        image = None
    elif image and not image_file:
        image_file = None

    if not image_file and not image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either an image file upload or an image URL/path",
        )

    stored_image: Optional[str] = image
    if image_file:
        stored_image = _save_image(image_file)

    product = Product(
        name=name,
        image=stored_image,
        price_per_kg=price_per_kg,
        in_stock=in_stock,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return success_response("Product created successfully", ProductOut.model_validate(product))


@router.put("/api/products/{product_id}", response_model=ApiResponse[ProductOut])
def update_product(
    product_id: str,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if payload.image is None and payload.price_per_kg is None and payload.in_stock is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of price_per_kg, image, in_stock must be provided",
        )

    if payload.image is not None:
        product.image = payload.image
    if payload.price_per_kg is not None:
        product.price_per_kg = payload.price_per_kg
    if payload.in_stock is not None:
        product.in_stock = payload.in_stock

    db.add(product)
    db.commit()
    db.refresh(product)
    return success_response("Product updated successfully", ProductOut.model_validate(product))


@router.put("/api/products/{product_id}/image", response_model=ApiResponse[ProductOut])
def update_product_image(
    product_id: str,
    image_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product.image = _save_image(image_file)
    db.add(product)
    db.commit()
    db.refresh(product)
    return success_response("Product image updated successfully", ProductOut.model_validate(product))


@router.delete("/api/products/{product_id}", response_model=ApiResponse[dict])
def delete_product(product_id: str, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    # Best-effort remove associated local image file if managed by us
    _delete_local_image_if_owned(product.image)
    db.delete(product)
    db.commit()
    return success_response("Product deleted successfully", {"id": product_id})
