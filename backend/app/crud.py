import os
from collections import defaultdict
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from .models import Customer, Order, OrderItem, Product
from .schemas import CustomerCreate, OrderCreate, ProductCreate, ProductUpdate


def _commit_or_422(db: Session, detail: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def create_product(db: Session, payload: ProductCreate) -> Product:
    product = Product(**payload.model_dump())
    db.add(product)
    _commit_or_422(db, "Product SKU must be unique")
    db.refresh(product)
    return product


def list_products(db: Session):
    return db.query(Product).order_by(Product.id.desc()).all()


def get_product(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def update_product(db: Session, product_id: int, payload: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    _commit_or_422(db, "Product SKU must be unique")
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> None:
    product = get_product(db, product_id)
    in_orders = db.query(OrderItem).filter(OrderItem.product_id == product.id).first()
    if in_orders:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a product that exists in an order",
        )
    db.delete(product)
    db.commit()


def create_customer(db: Session, payload: CustomerCreate) -> Customer:
    customer = Customer(**payload.model_dump())
    db.add(customer)
    _commit_or_422(db, "Customer email must be unique")
    db.refresh(customer)
    return customer


def list_customers(db: Session):
    return db.query(Customer).order_by(Customer.id.desc()).all()


def get_customer(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


def delete_customer(db: Session, customer_id: int) -> None:
    customer = get_customer(db, customer_id)
    has_orders = db.query(Order).filter(Order.customer_id == customer.id).first()
    if has_orders:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a customer that has orders",
        )
    db.delete(customer)
    db.commit()


def create_order(db: Session, payload: OrderCreate) -> Order:
    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    consolidated_items = []
    quantity_by_product = defaultdict(int)

    for item in payload.items:
        if item.product_id not in quantity_by_product:
            consolidated_items.append({"product_id": item.product_id, "quantity": item.quantity})
        else:
            for line in consolidated_items:
                if line["product_id"] == item.product_id:
                    line["quantity"] += item.quantity
                    break
        quantity_by_product[item.product_id] += item.quantity

    product_ids = list(quantity_by_product.keys())
    products = (
        db.query(Product)
        .filter(Product.id.in_(product_ids))
        .with_for_update()
        .all()
    )

    if len(products) != len(product_ids):
        found_ids = {p.id for p in products}
        missing_ids = [pid for pid in product_ids if pid not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product(s) not found: {missing_ids}",
        )

    product_map = {product.id: product for product in products}
    for product_id, qty in quantity_by_product.items():
        if product_map[product_id].quantity_in_stock < qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient inventory for product id {product_id}",
            )

    order = Order(customer_id=customer.id, total_amount=Decimal("0.00"))
    db.add(order)
    db.flush()

    total = Decimal("0.00")
    for item in consolidated_items:
        product = product_map[item["product_id"]]
        product.quantity_in_stock -= item["quantity"]
        unit_price = Decimal(product.price)
        line_total = unit_price * item["quantity"]
        total += line_total
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item["quantity"],
                unit_price=unit_price,
                line_total=line_total,
            )
        )

    order.total_amount = total
    db.commit()
    db.refresh(order)
    return order


def list_orders(db: Session):
    return (
        db.query(Order)
        .options(joinedload(Order.customer), joinedload(Order.items).joinedload(OrderItem.product))
        .order_by(Order.id.desc())
        .all()
    )


def get_order(db: Session, order_id: int) -> Order:
    order = (
        db.query(Order)
        .options(joinedload(Order.customer), joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def delete_order(db: Session, order_id: int) -> None:
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    for item in order.items:
        product = db.get(Product, item.product_id)
        if product:
            product.quantity_in_stock += item.quantity

    db.delete(order)
    db.commit()


def dashboard_summary(db: Session):
    threshold = int(os.getenv("LOW_STOCK_THRESHOLD", "5"))
    total_products = db.query(func.count(Product.id)).scalar() or 0
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    low_stock_products = (
        db.query(Product)
        .filter(Product.quantity_in_stock <= threshold)
        .order_by(Product.quantity_in_stock.asc(), Product.id.desc())
        .all()
    )
    return {
        "total_products": total_products,
        "total_customers": total_customers,
        "total_orders": total_orders,
        "low_stock_products": low_stock_products,
    }
