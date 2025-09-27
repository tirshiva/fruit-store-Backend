from __future__ import annotations

from datetime import datetime
import enum
import uuid
from typing import List

from sqlalchemy import DateTime, Enum, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.model.ordered_item import OrderedItem


class OrderStatus(str, enum.Enum):
    Pending = "Pending"
    Paid = "Paid"
    OutForDelivery = "OutForDelivery"
    Delivered = "Delivered"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)

    total_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), nullable=False, default=OrderStatus.Pending
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # One-to-many: Order -> OrderedItem
    items: Mapped[List["OrderedItem"]] = relationship(
        "OrderedItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )