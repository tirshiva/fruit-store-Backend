from fastapi import FastAPI
from pathlib import Path
from app.db.session import engine
from app.db.base import Base
from app.routes import product, order, discount
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Fruits & Vegetables Store API",
    version="1.0.1",
    description="Backend service for products, orders, and discounts"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Allow all origins (dev only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dev convenience: create tables if not exist. For production, use Alembic.
Base.metadata.create_all(bind=engine)

app.include_router(product.router)
app.include_router(order.router)
app.include_router(discount.router)

# To mount static files to server uploaded images
# Use absolute path for static mount to avoid CWD issues
BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = (BASE_DIR / "uploads").resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Health check
@app.get("/health")
def health():
    return {"status": "ok"}