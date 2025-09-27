from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.utils.deps import get_db
from app.model.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate, OrderDetailOut, OrderDetailItem
from app.schemas.common import ApiResponse
from app.utils.response import success_response
from app.services.order_service import create_order

router = APIRouter(tags=["Orders"])

@router.post("/api/orders", response_model=ApiResponse[OrderOut], status_code=status.HTTP_201_CREATED)
def place_order(payload: OrderCreate, db: Session = Depends(get_db)):
    order = create_order(db, name=payload.name, address=payload.address, phone_number=payload.phone_number, items=payload.ordered_items)
    
    # Send Telegram Notification
    try:
        from app.utils.telegram_notifier import send_telegram_message
        message = f"""
📦 <b>New Order Received!</b>
Order ID: {order.id}
Customer: {order.name}
Phone: {order.phone_number}
Address: {order.address}
Total: ₹{order.total_price}
Status: {order.status}
"""
        send_telegram_message(message)
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")
    
    data = OrderOut.model_validate(order)
    return success_response("Order placed successfully", data)

@router.get("/api/orders", response_model=ApiResponse[List[OrderOut]])
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return success_response("Orders fetched successfully", [OrderOut.model_validate(o) for o in orders])

@router.get("/api/orders/{order_id}", response_model=ApiResponse[OrderDetailOut])
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    items = [
        OrderDetailItem(productId=i.product_id, quantityInKg=i.quantity_in_kg)
        for i in order.items
    ]
    detail = OrderDetailOut(
        id=order.id,
        name=order.name,
        address=order.address,
        phoneNumber=order.phone_number,
        totalPrice=order.total_price,
        status=order.status,
        createdAt=order.created_at,
        orderedItems=items,  # uses alias; pydantic will map
    )
    return success_response("Order fetched successfully", detail)

@router.put("/api/orders/{order_id}", response_model=ApiResponse[OrderOut])
def update_order_status(order_id: str, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    order.status = payload.status
    db.add(order)
    db.commit()
    db.refresh(order)
    return success_response("Order updated successfully", OrderOut.model_validate(order))

@router.delete("/api/orders/{order_id}", response_model=ApiResponse[dict])
def delete_order(order_id: str, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    db.delete(order)
    db.commit()
    return success_response("Order deleted successfully", {"id": order_id})

