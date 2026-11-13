from sqlalchemy.orm import Session
from app.models import CustomerModel, ProductModel

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