from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2)
    # Accepts either a full URL or a served path like /uploads/products/<file>
    image: Optional[str] = None
    price_per_kg: float = Field(..., gt=0, alias="price_per_kg")
    in_stock: bool = Field(default=True, alias="in_stock")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    image: Optional[str] = None
    price_per_kg: Optional[float] = Field(None, gt=0, alias="price_per_kg")
    in_stock: Optional[bool] = Field(None, alias="in_stock")

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def validate_non_empty(cls, values):
        if not any(values.get(k) is not None for k in ["name", "image", "price_per_kg", "in_stock"]):
            raise ValueError("At least one of name, price_per_kg, image, in_stock must be provided")
        return values


class ProductOut(BaseModel):
    id: str
    name: str
    image: Optional[str] = None
    price_per_kg: float = Field(..., alias="price_per_kg")
    in_stock: bool = Field(..., alias="in_stock")
    created_at: datetime = Field(..., alias="created_at")
    updated_at: datetime = Field(..., alias="updated_at")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)