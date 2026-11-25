from pydantic import (
    BaseModel,
    Field,
    ConfigDict
)
from decimal import Decimal

class Customer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    customer_id: int = Field(gt=0)
    name: str
    segment: str
    
class Product(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    product_id: int
    sku: str
    product_name: str
    description: str | None
    category: str
    list_price: Decimal
    currency_code: str
    is_active: bool


class ProductCreate(BaseModel):

    sku: str = Field(
        min_length=2,
        max_length=50
    )

    product_name: str = Field(
        min_length=2,
        max_length=150
    )

    description: str | None = None

    category: str = Field(
        min_length=2,
        max_length=100
    )

    list_price: Decimal = Field(
        gt=0,
        max_digits=14,
        decimal_places=2
    )

    currency_code: str = Field(
        default="INR",
        pattern=r"^[A-Z]{3}$"
    )


class ProductUpdate(BaseModel):

    sku: str | None = Field(
        default=None,
        min_length=2,
        max_length=50
    )

    product_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    description: str | None = None

    category: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    list_price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=14,
        decimal_places=2
    )

    currency_code: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{3}$"
    )

    is_active: bool | None = None