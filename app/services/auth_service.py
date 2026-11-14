from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models import UserModel
from app.security import (
    hash_password,
    verify_password
)

def get_user_by_username(
        db: Session,
        username: str
):
    statement = select(UserModel).where(UserModel.username == username)
    return db.scalar(statement)

def create_user(
        db: Session,
        username: str,
        password: str
):
    user = UserModel(
        username = username,
        hashed_password = hash_password(password),
        role = "analyst",
        is_active = True
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(user)

    return user

def authenticate_user(
    db: Session,
    username: str,
    password: str
):
    user = get_user_by_username(
        db,
        username
    )

    if user is None:
        return None

    if not verify_password(
        password,
        user.hashed_password
    ):
        return None

    return user