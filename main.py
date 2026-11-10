from fastapi import FastAPI, HTTPException, status, Path
from pydantic import BaseModel, Field, model_validator
from datetime import date
from typing import Literal, List

# creating the fast api application
app = FastAPI(
    title="Enterprise Revenue OP's AI Agent",
    description="Backend for our ai assistant",
    version="1.0.0"
)

# Temporary business data.
# Later we will replace this with PostgreSQL.

customers = {
    101: {
        "customer_id": 101,
        "name": "Aarav Sharma",
        "segment": "Enterprise"
    },
    102: {
        "customer_id": 102,
        "name": "Priya Verma",
        "segment": "Retail"
    },
    103: {
        "customer_id": 103,
        "name": "Rahul Singh",
        "segment": "Enterprise"
    }
}

metrics = [
    {
        "period": "monthly",
        "region": "north",
        "revenue": 1250000,
        "orders": 320
    },
    {
        "period": "monthly",
        "region": "south",
        "revenue": 950000,
        "orders": 280
    },
    {
        "period": "quarterly",
        "region": "north",
        "revenue": 3700000,
        "orders": 940
    }
]

products = [
    {
        "product_id": 4000,
        "product_name": "iphone_16_pro",
        "price": 100000,
        "category": "smartphones"
    },
    {
        "product_id": 5000,
        "product_name": "macbook_pro_m5",
        "price": 320000,
        "category": "laptop"
    },
    {
        "product_id": 4001,
        "product_name": "iphone_17_pro",
        "price": 120000,
        "category": "smartphones"
    }
]

# Request body model
class AnalysisRequest(BaseModel):
    question: str
    department: str
    include_recommendations: bool

class SalesAnalysisRequest(BaseModel):
        start_date: date
        end_date: date
        minimum_revenue: float = Field(gt=0, le=100_000_000)
        region: Literal['north', 'south', 'east', 'west']
        analysis_type: Literal['revenue', 'orders', 'customers']
        notes: str | None = Field(default=None, max_length=300)
        @model_validator(mode="after")
        def date_validator(self):
            if self.end_date < self.start_date:
                raise ValueError("End date cannot be earlier than start date")
            return self

class product(BaseModel):
    product_id: int = Field(gt=0)
    product_name: str = Field(min_length=2, max_length=100)
    price: int = Field(gt=0)
    category: str

class metrics_model(BaseModel):
    period: str = Literal["monthly", "quaterly", "yearly"]
    region: str = Literal["east", "west", "north", "south"]
    results: dict | List|dict

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "Healthy",
        "message": "Enterprise Rev Ops AI Agent API is Running"
    }

# About the application endpoint
@app.get("/about")
def about_application():
    return {
        "application": "Enterprise AI Agent" ,
        "version": "1.0.0",
        "purpose": "Business Automation"
    }

# Path parameters endpoint
@app.get("/customers/{customer_id}")
def get_customer(customer_id: int = Path(gt=0)):
    customer = customers.get(customer_id)
    if customer is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "Customer not found"
        )
    return customer

# Query endpoint
@app.get("/metrics", response_model=metrics_model)
def get_metrics(period: str = "monthly", region: str = "all"):
    results = [item for item in metrics if item["period"] == period]
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data available for inserted period"
        )
    if region != "all":
        results = [item for item in results if item['region'] == region]
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Region not found"
            )
    return {
        "period": period,
        "region": region,
        "results": results
    }

# Request body endpoint
@app.post("/analysis")
def create_analysis(request: AnalysisRequest):
    return {
        "message": "Analysis request recieved",
        "question": request.question,
        "department": request.department,
        "include_recommendations": request.include_recommendations
    }

# Products endpoint
@app.get("/products/{product_id}", response_model=product)
def fetch_product(product_id: int = Path(gt=0)):
    product_details = next((item for item in products if item["product_id"] == product_id), None)
    if product_details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product_details

# Sales analysis request body endpoint
@app.post("/sales-analysis", response_model=dict, status_code=status.HTTP_200_OK)
def sales_analysis(request: SalesAnalysisRequest):
    return {
        "message": "Sales analysis request recieved",
        "status": "Recieved",
        "filters": {
            "start_date": request.start_date,
            "end_date": request.end_date,
            "minimum_revenue": request.minimum_revenue,
            "region": request.region,
            "analysis_type": request.analysis_type,
            "notes": request.notes
        }
    }