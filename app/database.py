import os
from collections.abc import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker
)

# Load enviornment variables

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not configured")

# Create database engine

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Create database connection
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)

# Base class for database models
class Base(DeclarativeBase):
    pass 

# Database dependency
def get_db() -> Generator['Session', None, None]:
    with SessionLocal() as session:
        yield session

