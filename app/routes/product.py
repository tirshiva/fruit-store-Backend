from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.utils.deps import get_db
from app.model.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from app.schemas.common import ApiResponse
from app.utils.response import success_response

router = APIRouter(tags=["Products"])

@router.get("/api/products", response_model=ApiResponse[List[ProductOut]])
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return success_response("Products fetched successfully", [ProductOut.model_validate(p) for p in products])

@router.post("/api/products", response_model=ApiResponse[ProductOut], status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(
        name=payload.name,
        image=str(payload.image) if payload.image else None,
        price_per_kg=payload.price_per_kg,
        in_stock=payload.in_stock,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return success_response("Product created successfully", ProductOut.model_validate(product))

@router.put("/api/products/{product_id}", response_model=ApiResponse[ProductOut])
def update_product(product_id: str, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # ensure at least one field present
    if payload.image is None and payload.price_per_kg is None and payload.in_stock is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one of pricePerKg, image, inStock must be provided")

    if payload.image is not None:
        product.image = str(payload.image)
    if payload.price_per_kg is not None:
        product.price_per_kg = payload.price_per_kg
    if payload.in_stock is not None:
        product.in_stock = payload.in_stock

    db.add(product)
    db.commit()
    db.refresh(product)
    return success_response("Product updated successfully", ProductOut.model_validate(product))

@router.delete("/api/products/{product_id}", response_model=ApiResponse[dict])
def delete_product(product_id: str, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    db.delete(product)
    db.commit()
    return success_response("Product deleted successfully", {"id": product_id})