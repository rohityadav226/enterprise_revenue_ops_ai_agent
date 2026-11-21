from sqlalchemy.orm import Session
from app.models import CustomerModel, ProductModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

def get_customer_by_id(
        db: Session,
        customer_id: int
):
    return db.get(CustomerModel, customer_id)

def get_product_by_id(
        db: Session,
        product_id: int
):
    return db.get(ProductModel, product_id)

def create_product(
        db: Session,
        product_data: dict
):
    product = ProductModel(**product_data)
    db.add(product)
    
    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    db.refresh(product)
    return product

def get_all_products(
    db: Session,
    skip: int,
    limit: int
):

    statement = (
        select(ProductModel)
        .order_by(ProductModel.product_id)
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())

def update_product(
    db: Session,
    product_id: int,
    update_data: dict
):

    product = db.get(
        ProductModel,
        product_id
    )

    if product is None:
        return None

    for field, value in update_data.items():

        setattr(
            product,
            field,
            value
        )

    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    db.refresh(product)

    return product


def delete_product(
    db: Session,
    product_id: int
):

    product = db.get(
        ProductModel,
        product_id
    )

    if product is None:
        return None

    db.delete(product)

    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    return True