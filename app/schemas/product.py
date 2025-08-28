from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2)
    # Accepts either a full URL or a served path like /uploads/products/<file>
    image: Optional[str] = None
    price_per_kg: float = Field(..., gt=0, alias="pricePerKg")
    in_stock: bool = Field(default=True, alias="inStock")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    image: Optional[str] = None
    price_per_kg: Optional[float] = Field(None, gt=0, alias="pricePerKg")
    in_stock: Optional[bool] = Field(None, alias="inStock")

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def validate_non_empty(cls, values):
        if not any(values.get(k) is not None for k in ["image", "price_per_kg", "in_stock"]):
            raise ValueError("At least one of pricePerKg, image, inStock must be provided")
        return values


class ProductOut(BaseModel):
    id: str
    name: str
    image: Optional[str] = None
    price_per_kg: float = Field(..., alias="pricePerKg")
    in_stock: bool = Field(..., alias="inStock")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
