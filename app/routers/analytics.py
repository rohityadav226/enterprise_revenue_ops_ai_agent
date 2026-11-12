from fastapi import APIRouter
from app.schemas.analytics import (
    MetricsResponse,
    AnalysisResponse,
    AnalysisRequest,
    SalesAnalysisResponse
)
from app.services.analytics_service import (
    get_filtered_metric,
    prepare_analysis,
    SalesAnalysisRequest,
    prepare_sales_analysis
)
from typing import Literal

router = APIRouter(tags=["Analystics"])

@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(period: Literal["monthly", "quarterly"] = "monthly",
                 region: Literal["north", "south", "east", "west", "all"] = "all"):
    metrics_details = get_filtered_metric(period, region)
    return {
        "period": period,
        "region": region,
        "results": metrics_details
    }

@router.post("/analysis", response_model=AnalysisResponse)
def create_analysis(request: AnalysisRequest):
    return prepare_analysis(request)

@router.post("/sales-analysis", response_model=SalesAnalysisResponse)
def sales_analysis(request: SalesAnalysisRequest):
    return prepare_sales_analysis(request)
