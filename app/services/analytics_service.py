from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import MetricModel

from app.schemas.analytics import (
    AnalysisRequest, SalesAnalysisRequest
)

def get_filtered_metric(
        db: Session,
        period: int,
        region: str
):
    statement = select(MetricModel).where(MetricModel.period == period)
    if region != "all":
        statement = select(MetricModel).where(MetricModel.region == region)
    return list(db.scalars(statement).all())

def prepare_analysis(request: AnalysisRequest):
    return {
        "message": "Analysis request recieved",
        "question": request.question,
        "department": request.department,
        "include_recommendations": request.include_recommendations
    }

def prepare_sales_analysis(request: SalesAnalysisRequest):
    return {
        "message": "Sales analysis request recieved",
        "status": "Recieved",
        "filters": request.model_dump()
    }