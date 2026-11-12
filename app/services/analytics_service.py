from app.data.mock_data import metrics
from app.schemas.analytics import (
    AnalysisRequest, SalesAnalysisRequest
)

def get_filtered_metric(period: int, region: str):
    results = [
        item for item in metrics if item["period"] == period
    ]
    if region != "all":
        results = [
            item for item in results if item['region'] == region
        ]
    return results

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