from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Path,
    Query    
)
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.catalog import (
    Product,
    ProductCreate,
    ProductUpdate
)
from app.services.catalog_service import (
    get_product_by_id,
    create_product,
    update_product,
    delete_product,
    get_all_products
)
from app.dependencies import (
    get_current_user,
    require_admin
)

from app.models import UserModel

router = APIRouter(
    prefix="/products",
    tags=["Products"]
    )

# GET PRODUCT BY ID
@router.get(
        "/{product_id}",
        response_model=Product
        )
def fetch_product(
    db: Session = Depends(get_db),
    product_id: int = Path(gt=0),
    current_user: UserModel = Depends(get_current_user)
    ):
    product_details = get_product_by_id(db, product_id)
    if product_details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product_details

# CREATE A NEW PRODUCT
@router.post(
    "",
    response_model=Product,
    status_code=status.HTTP_201_CREATED
)

def create_product_endpoint(
    request: ProductCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):
    return create_product(
        db,
        request.model_dump()
    )

# GET ALL PRODUCTS
@router.get(
    "",
    response_model=list[Product]
)
def fetch_all_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return get_all_products(
        db,
        skip,
        limit
    )

# UPDATE PRODUCT
@router.patch(
    "/{product_id}",
    response_model=Product
)
def update_product_endpoint(
    db: Session = Depends(get_db),
    product_id: int = Path(ge=0),
    request: ProductUpdate = ...,
    current_user: UserModel = Depends(get_current_user)
):
    update_data = request.model_dump(
        exclude_unset=True
    )

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update"
        )

    if any(value is None for value in update_data.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Product fields cannot be null"
        )

    product = update_product(
        db,
        product_id,
        update_data
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return product

# DELETE PRODUCT
@router.delete("/{product_id}")
def delete_product_endpoint(
    product_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin)
):

    deleted = delete_product(
        db,
        product_id
    )

    if deleted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return {
        "message": "Product deleted successfully",
        "product_id": product_id
    }