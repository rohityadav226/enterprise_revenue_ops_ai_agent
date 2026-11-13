from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Path)
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.catalog import Product
from app.services.catalog_service import get_product_by_id

router = APIRouter(
    prefix="/products",
    tags=["Products"]
    )

@router.get(
        "/{product_id}",
        response_model=Product
        )
def fetch_product(
    db: Session = Depends(get_db),
    product_id: int = Path(gt=0)
    ):
    product_details = get_product_by_id(db, product_id)
    if product_details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product_details