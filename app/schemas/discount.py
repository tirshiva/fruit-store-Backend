from pydantic import BaseModel, Field, ConfigDict

class DiscountCreate(BaseModel):
    text: str

class DiscountOut(BaseModel):
    text: str

    model_config = ConfigDict(from_attributes=True)
