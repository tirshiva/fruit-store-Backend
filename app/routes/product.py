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


def _delete_local_image_if_owned(image_path: Optional[str]) -> dict:
    """
    Delete an image file from disk if it resides under our uploads/products directory.
    Returns a status dict indicating outcome instead of raising to the client.

    Accepted inputs: public paths like "/uploads/products/<file>". External URLs are ignored.
    {"deleted": True} when removed; otherwise {"deleted": False, "reason": <why>}.
    """
    if not image_path:
        return {"deleted": False, "reason": "no_image_set"}
    try:
        if not image_path.startswith("/uploads/"):
            return {"deleted": False, "reason": "external_or_unmanaged_path"}

        rel_root = image_path.lstrip("/")
        rel_part = rel_root.split("/", 1)[1] if "/" in rel_root else ""
        if not rel_part:
            return {"deleted": False, "reason": "invalid_path"}

        fs_path = UPLOAD_ROOT / rel_part

        # Ensure the file is under the products subdirectory
        try:
            fs_path.resolve().relative_to(PRODUCTS_SUBDIR.resolve())
        except Exception:
            return {"deleted": False, "reason": "not_in_products_dir"}

        if fs_path.exists() and fs_path.is_file():
            fs_path.unlink(missing_ok=True)
            return {"deleted": True}
        else:
            return {"deleted": False, "reason": "file_not_found"}
    except Exception:
        return {"deleted": False, "reason": "filesystem_error"}


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

    if (
        payload.name is None
        and payload.image is None
        and payload.price_per_kg is None
        and payload.in_stock is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of name, price_per_kg, image, in_stock must be provided",
        )

    if payload.name is not None:
        product.name = payload.name
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
    image_status = _delete_local_image_if_owned(product.image)
    db.delete(product)
    db.commit()
    return success_response("Product deleted successfully", {"id": product_id, "image_delete_status": image_status})