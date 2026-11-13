from pydantic import (
    BaseModel,
    Field,
    ConfigDict
)

class Customer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    customer_id: int = Field(gt=0)
    name: str
    segment: str
    
class Product(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int = Field(gt=0)
    product_name: str = Field(min_length=2, max_length=100)
    price: int = Field(gt=0)
    category: str