from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, condecimal, conint, constr


class ProductBase(BaseModel):
    name: constr(min_length=1, max_length=200)
    sku: constr(min_length=1, max_length=100)
    price: condecimal(max_digits=10, decimal_places=2, gt=0)
    quantity_in_stock: conint(ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=200)] = None
    sku: Optional[constr(min_length=1, max_length=100)] = None
    price: Optional[condecimal(max_digits=10, decimal_places=2, gt=0)] = None
    quantity_in_stock: Optional[conint(ge=0)] = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class CustomerBase(BaseModel):
    full_name: constr(min_length=1, max_length=200)
    email: EmailStr
    phone_number: constr(min_length=5, max_length=50)


class CustomerCreate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: conint(gt=0)


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    product_name: str
    sku: str


class OrderCreate(BaseModel):
    customer_id: int
    items: List[OrderItemCreate] = Field(min_length=1)


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    total_amount: Decimal
    created_at: datetime
    customer_name: str
    items: List[OrderItemRead]


class SummaryRead(BaseModel):
    total_products: int
    total_customers: int
    total_orders: int
    low_stock_products: List[ProductRead]
