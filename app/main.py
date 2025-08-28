from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base
from app.routes import product, order, discount

app = FastAPI(
    title="Fruits & Vegetables Store API",
    version="1.0.1",
    description="Backend service for products, orders, and discounts"
)

# Dev convenience: create tables if not exist. For production, use Alembic.
Base.metadata.create_all(bind=engine)

app.include_router(product.router)
app.include_router(order.router)
app.include_router(discount.router)

# Health check
@app.get("/health")
def health():
    return {"status": "ok"}