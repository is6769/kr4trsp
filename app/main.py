from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import ValidationError
from itertools import count
from threading import Lock

from app.database import engine, get_db, Base
from app.models import Product, User as UserModel
from app.schemas import ProductCreate, ProductOut, User, UserOut
from app.exceptions import CustomExceptionA, CustomExceptionB, ValidationErrorHandler

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI Контрольная работа №4")

_users_db: dict[int, dict] = {}
_id_seq = count(start=1)
_id_lock = Lock()


def next_user_id() -> int:
    with _id_lock:
        return next(_id_seq)


@app.exception_handler(CustomExceptionA)
async def custom_exception_a_handler(request: Request, exc: CustomExceptionA):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_type": "CustomExceptionA"}
    )


@app.exception_handler(CustomExceptionB)
async def custom_exception_b_handler(request: Request, exc: CustomExceptionB):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_type": "CustomExceptionB"}
    )


@app.exception_handler(ValidationErrorHandler)
async def validation_error_handler(request: Request, exc: ValidationErrorHandler):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors}
    )


@app.post("/products", response_model=ProductOut, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise CustomExceptionB(f"Product with id {product_id} not found")
    return product


@app.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise CustomExceptionB(f"Product with id {product_id} not found")
    db.delete(product)
    db.commit()
    return None


@app.get("/test-exception-a")
def test_exception_a(trigger: bool = False):
    if trigger:
        raise CustomExceptionA("This is a custom exception A (bad request)")
    return {"message": "No error. Set ?trigger=true to trigger exception"}


@app.get("/test-exception-b")
def test_exception_b(trigger: bool = False):
    if trigger:
        raise CustomExceptionB("This is a custom exception B (not found)")
    return {"message": "No error. Set ?trigger=true to trigger exception"}


@app.post("/users", response_model=UserOut, status_code=201)
def create_user(user: User):
    user_id = next_user_id()
    user_data = user.model_dump()
    _users_db[user_id] = user_data
    return {"id": user_id, "username": user_data["username"], "age": user_data["age"]}


@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    if user_id not in _users_db:
        raise HTTPException(status_code=404, detail="User not found")
    user = _users_db[user_id]
    return {"id": user_id, "username": user["username"], "age": user["age"]}


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    if _users_db.pop(user_id, None) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return None


@app.get("/health")
def health_check():
    return {"status": "ok"}
