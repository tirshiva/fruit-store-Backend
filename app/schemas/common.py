from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, ConfigDict
from pydantic.generics import GenericModel

T = TypeVar("T")

class ApiResponse(GenericModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None

    model_config = ConfigDict(populate_by_name=True)