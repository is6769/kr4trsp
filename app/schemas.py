from pydantic import BaseModel, EmailStr, conint, constr
from typing import Optional


class User(BaseModel):
    username: str
    age: conint(gt=18)  # type: ignore
    email: EmailStr
    password: constr(min_length=8, max_length=16)  # type: ignore
    phone: Optional[str] = "Unknown"

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: int
    username: str
    age: int

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    title: str
    price: float
    count: int
    description: str = "No description"


class ProductOut(BaseModel):
    id: int
    title: str
    price: float
    count: int
    description: str

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
