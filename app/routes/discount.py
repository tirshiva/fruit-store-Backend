from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.utils.deps import get_db
from app.model.discount import Discount
from app.schemas.discount import DiscountCreate, DiscountOut
from app.schemas.common import ApiResponse
from app.utils.response import success_response

router = APIRouter(tags=["Discount"])

@router.post("/api/discount", response_model=ApiResponse[DiscountOut])
def set_discount(payload: DiscountCreate, db: Session = Depends(get_db)):
    # Keep only one discount row; update if exists, else create
    row = db.query(Discount).first()
    if row:
        row.text = payload.text
        db.add(row)
    else:
        row = Discount(text=payload.text)
        db.add(row)
    db.commit()
    db.refresh(row)
    return success_response("Discount updated successfully", DiscountOut.model_validate(row))

@router.get("/api/discount", response_model=ApiResponse[DiscountOut | None])
def get_discount(db: Session = Depends(get_db)):
    row = db.query(Discount).first()
    if not row:
        return success_response("No discount set", None)
    return success_response("Discount fetched successfully", DiscountOut.model_validate(row))
