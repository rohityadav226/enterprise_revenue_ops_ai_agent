from pydantic import BaseModel, Field, model_validator
from typing import List, Literal

class Customer(BaseModel):
    customer_id: int = Field(gt=0)
    name: str
    segment: str
    
class Product(BaseModel):
    product_id: int = Field(gt=0)
    product_name: str = Field(min_length=2, max_length=100)
    price: int = Field(gt=0)
    category: str