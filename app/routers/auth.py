from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import UserModel
from app.schemas.auth import (
    UserCreate,
    UserRead,
    LoginRequest,
    TokenResponse
)
from app.security import create_access_token
from app.dependencies import (
    get_current_user,
    require_admin
)
from app.services.auth_service import (
    get_user_by_username,
    create_user,
    authenticate_user
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# User Register
@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    request: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = get_user_by_username(
        db,
        request.username
    )
    if existing_user is not None:
        raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Username already exists"
    )

    try:
        user = create_user(
            db,
            request.username,
            request.password
        )

    except IntegrityError:
        raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Username already exists"
    )

    return user

# User Login
@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    user = authenticate_user(
        db,
        request.username,
        request.password
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = create_access_token(
        user.username
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get(
    "/me",
    response_model=UserRead
)
def get_my_profile(
    current_user: UserModel = Depends(get_current_user)
):
    return current_user

# Administrator-only endpoint
@router.get("/admin-check")
def admin_check(
    current_user: UserModel = Depends(require_admin)
):

    return {
        "message": "Administrator access verified",
        "username": current_user.username,
        "role": current_user.role
    }