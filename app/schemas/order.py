from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.model.order import OrderStatus

class OrderedItemIn(BaseModel):
    product_id: str = Field(..., alias="productId")
    quantity_in_kg: float = Field(..., gt=0, alias="quantityInKg")

    model_config = ConfigDict(populate_by_name=True)

class OrderCreate(BaseModel):
    name: str
    address: str
    phone_number: str = Field(..., alias="phoneNumber")
    ordered_items: List[OrderedItemIn] = Field(..., min_length=1, alias="orderedItems")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("phone_number")
    @classmethod
    def phone_must_be_10_digits(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Must be 10 digits")
        return v

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class OrderOut(BaseModel):
    id: str
    name: str
    total_price: float = Field(..., alias="totalPrice")
    status: OrderStatus
    created_at: datetime = Field(..., alias="createdAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class OrderDetailItem(BaseModel):
    product_id: str = Field(..., alias="productId")
    quantity_in_kg: float = Field(..., alias="quantityInKg")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class OrderDetailOut(OrderOut):
    address: str
    phone_number: str = Field(..., alias="phoneNumber")
    items: List[OrderDetailItem] = Field(..., alias="orderedItems")