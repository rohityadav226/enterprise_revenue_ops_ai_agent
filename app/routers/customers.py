from fastapi import APIRouter, HTTPException, status, Path
from app.schemas.catalog import Customer
from app.services.catalog_service import get_customer_by_id

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("/{customer_id}", response_model=Customer)
def fetch_customer(customer_id: int = Path(gt=0)):
    customer_detail = get_customer_by_id(customer_id)
    if customer_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer_detail