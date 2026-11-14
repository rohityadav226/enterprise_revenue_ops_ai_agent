from fastapi import (
    APIRouter,
    Depends
)
from sqlalchemy.orm import Session
from app.database import get_db
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
from app.dependencies import get_current_user
from app.models import UserModel

router = APIRouter(
    tags=["Analytics"]
    )

@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(db: Session = Depends(get_db),
                period: Literal["monthly", "quarterly"] = "monthly",
                region: Literal["north", "south", "east", "west", "all"] = "all",
                current_user: UserModel = Depends(get_current_user)
):
    metrics_details = get_filtered_metric(
        db,
        period,
        region
    )
    return {
        "period": period,
        "region": region,
        "results": metrics_details
    }

@router.post("/analysis", response_model=AnalysisResponse)
def create_analysis(
    request: AnalysisRequest,
    current_user: UserModel = Depends(get_current_user)
):
    return prepare_analysis(request)

@router.post(
        "/sales-analysis",
        response_model=SalesAnalysisResponse
)
def sales_analysis(
    request: SalesAnalysisRequest,
    current_user: UserModel = Depends(get_current_user)
):
    return prepare_sales_analysis(request)