from sqlalchemy import select
from app.database import (
    Base,
    engine,
    SessionLocal
)
from app.models import (
    CustomerModel,
    ProductModel,
    MetricModel,
    UserModel
)

def seed_database():

    #create table
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:

        # Seed customers
        if db.scalar(select(CustomerModel).limit(1)) is None:
            db.add_all([
                CustomerModel(
                    customer_id=101,
                    name="Aarav Sharma",
                    segment="Enterprise"
                ),
                    CustomerModel(
                    customer_id=102,
                    name="Priya Verma",
                    segment="Retail"
                ),
                    CustomerModel(
                    customer_id=103,
                    name="Rahul Singh",
                    segment="Enterprise"
                )
            ])

        # Seed products
        if db.scalar(select(ProductModel).limit(1)) is None:
            db.add_all([
                ProductModel(
                    product_id=4000,
                    product_name="iphone_16_pro",
                    price=100000,
                    category="smartphones"
                ),
                ProductModel(
                    product_id=5000,
                    product_name="macbook_pro_m5",
                    price=320000,
                    category="laptop"
                ),
                ProductModel(
                    product_id=4001,
                    product_name="iphone_17_pro",
                    price=120000,
                    category="smartphones"
                )
            ])

        # Seed business metrics
        if db.scalar(select(MetricModel).limit(1)) is None:
            db.add_all([
                MetricModel(
                    period="monthly",
                    region="north",
                    revenue=1250000,
                    orders=320
                ),
                MetricModel(
                    period="monthly",
                    region="south",
                    revenue=950000,
                    orders=280
                ),
                MetricModel(
                    period="quarterly",
                    region="north",
                    revenue=3700000,
                    orders=940
                )
            ])

        db.commit()

    print("Database tables and seed data ready")

if __name__ == "__main__":
    seed_database()