from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .order import Order
    from .product import Product


class OrderedItem(Base):
    __tablename__ = "ordered_items"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    order_id: Mapped[str] = mapped_column(
        String, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[str] = mapped_column(
        String, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )

    quantity_in_kg: Mapped[float] = mapped_column(Float, nullable=False)

    # Many-to-one: OrderedItem -> Order
    order: Mapped["Order"] = relationship(back_populates="items")

    # Many-to-one: OrderedItem -> Product (no reverse needed right now)
    product: Mapped["Product"] = relationship()
