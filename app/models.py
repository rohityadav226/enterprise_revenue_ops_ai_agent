from sqlalchemy import (
    Boolean,
    Integer,
    String
)
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

# Customer Table
class CustomerModel(Base):
    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    segment: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

# Product table
class ProductModel(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    product_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    price: Mapped[str] = mapped_column(
        Integer,
        nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

# Business metrics table
class MetricModel(Base):
    __tablename__ = "business_metrics"

    metric_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    period: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    region: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    revenue: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    orders: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
class UserModel(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(30),
        default="analyst",
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )