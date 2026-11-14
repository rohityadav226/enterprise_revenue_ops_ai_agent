import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import (
    Depends,
    HTTPException,
    status    
)
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)
from sqlalchemy.orm import Session
from app.security import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM
)
from app.database import get_db
from app.models import UserModel
from app.services.auth_service import get_user_by_username

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        db: Session = Depends(get_db)
):
    
    unauthorized_exception  = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if credentials is None:
        raise unauthorized_exception

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"]}
        )

        username = payload.get("sub")
        if (
            payload.get("token_type") != "access"
            or not isinstance(username, str)
        ):
            raise unauthorized_exception

    except InvalidTokenError:
        raise unauthorized_exception

    user = get_user_by_username(
        db,
        username
    )

    if user is None:
        raise unauthorized_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user

def require_admin(
        current_user: UserModel = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privilages required"
        )

    return current_user