from pydantic import BaseModel, Field, model_validator
from typing import List, Literal
from datetime import date

class AnalysisRequest(BaseModel):
    question: str = Field(min_length=5, max_length=500)
    department: str
    include_recommendations: bool = True

class AnalysisResponse(BaseModel):
    message: str
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

class SalesAnalysisFilters(BaseModel):
     start_date: date
     end_date: date
     minimum_revenue: float
     region: str
     analysis_type: str
     notes: str | None = None

class SalesAnalysisResponse(BaseModel):
     message: str
     status: str
     filters: SalesAnalysisFilters

class MetricRecord(BaseModel):
    period: str
    region: str
    revenue: int
    orders: int

class MetricsResponse(BaseModel):
    period: str
    region: str
    results: list[MetricRecord]