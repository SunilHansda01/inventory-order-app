
import os
import time
from decimal import Decimal

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session  # type: ignore[import]
from sqlalchemy import inspect  # type: ignore[import]

from . import crud, models, schemas
from .database import Base, engine, get_db

app = FastAPI(title="Inventory & Order Management System", version="1.0.0")

frontend_origin = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5173,https://inventory-order-manager.netlify.app"
)

allow_origins = [origin.strip() for origin in frontend_origin.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup") #Helps me to load or create the database tables when the application starts. This ensures that the necessary tables are available before handling any requests.
def startup_event():
    from . import models  # makes sure all ORM classes are registered

    print("Registered ORM tables:", list(Base.metadata.tables.keys()))
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    print("DB tables in public schema:", inspector.get_table_names(schema="public"))

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=allow_origins or ["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/products", response_model=schemas.ProductRead, status_code=201)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, payload)


@app.get("/products", response_model=list[schemas.ProductRead])
def list_products(db: Session = Depends(get_db)):
    return crud.list_products(db)


@app.get("/products/{product_id}", response_model=schemas.ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return crud.get_product(db, product_id)


@app.put("/products/{product_id}", response_model=schemas.ProductRead)
def update_product(product_id: int, payload: schemas.ProductUpdate, db: Session = Depends(get_db)):
    return crud.update_product(db, product_id, payload)


@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    crud.delete_product(db, product_id)
    return None


@app.post("/customers", response_model=schemas.CustomerRead, status_code=201)
def create_customer(payload: schemas.CustomerCreate, db: Session = Depends(get_db)):
    return crud.create_customer(db, payload)


@app.get("/customers", response_model=list[schemas.CustomerRead])
def list_customers(db: Session = Depends(get_db)):
    return crud.list_customers(db)


@app.get("/customers/{customer_id}", response_model=schemas.CustomerRead)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    return crud.get_customer(db, customer_id)


@app.delete("/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    crud.delete_customer(db, customer_id)
    return None


@app.post("/orders", response_model=schemas.OrderRead, status_code=201)
def create_order(payload: schemas.OrderCreate, db: Session = Depends(get_db)):
    order = crud.create_order(db, payload)
    return build_order_read(order)


@app.get("/orders", response_model=list[schemas.OrderRead])
def list_orders(db: Session = Depends(get_db)):
    orders = crud.list_orders(db)
    return [build_order_read(order) for order in orders]


@app.get("/orders/{order_id}", response_model=schemas.OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = crud.get_order(db, order_id)
    return build_order_read(order)


@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    crud.delete_order(db, order_id)
    return None


@app.get("/dashboard/summary", response_model=schemas.SummaryRead)
def dashboard_summary(db: Session = Depends(get_db)):
    summary = crud.dashboard_summary(db)
    return summary


def build_order_read(order: models.Order) -> schemas.OrderRead:
    return schemas.OrderRead(
        id=order.id,
        customer_id=order.customer_id,
        total_amount=Decimal(order.total_amount),
        created_at=order.created_at,
        customer_name=order.customer.full_name if order.customer else "",
        items=[
            schemas.OrderItemRead(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=Decimal(item.unit_price),
                line_total=Decimal(item.line_total),
                product_name=item.product.name if item.product else "",
                sku=item.product.sku if item.product else "",
            )
            for item in order.items
        ],
    )
