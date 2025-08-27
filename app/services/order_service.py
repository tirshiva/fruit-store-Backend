from typing import List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.model.product import Product
from app.model.order import Order, OrderStatus
from app.model.ordered_item import OrderedItem
from app.schemas.order import OrderedItemIn

def compute_total_and_validate(db: Session, items: List[OrderedItemIn]) -> Tuple[float, List[OrderedItem]]:
    total = 0.0
    ordered_rows: List[OrderedItem] = []

    product_ids = [it.product_id for it in items]
    products = {p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()}

    for it in items:
        product = products.get(it.product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product not found: {it.product_id}")
        if not product.in_stock:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product out of stock: {product.name}")
        line_total = it.quantity_in_kg * product.price_per_kg
        total += line_total
        ordered_rows.append(OrderedItem(product_id=product.id, quantity_in_kg=it.quantity_in_kg))

    return total, ordered_rows

def create_order(db: Session, name: str, address: str, phone_number: str, items: List[OrderedItemIn]) -> Order:
    total, ordered_rows = compute_total_and_validate(db, items)

    order = Order(name=name, address=address, phone_number=phone_number, total_price=total, status=OrderStatus.Pending)
    db.add(order)
    db.flush()  # get order.id

    for row in ordered_rows:
        row.order_id = order.id
        db.add(row)

    db.commit()
    db.refresh(order)
    return order
