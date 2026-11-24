
import os

# Configure test-only environment variables before importing the app.
# These defaults allow tests to run without a local .env file.

os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+pysqlite:///:memory:"
)

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-only-secret-key-do-not-use-in-production-123456"
)

os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from decimal import Decimal
from app.models import (
    CustomerModel,
    ProductModel,
    MetricModel
)

@pytest.fixture
def client():

    # Create an isolated in-memory SQLite database

    test_engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False
    )

    # Create database tables
    Base.metadata.create_all(bind=test_engine)

    # Insert test records
    with TestingSessionLocal() as db:

        db.add_all([

            CustomerModel(
                customer_id=101,
                name="Test Customer",
                segment="Enterprise"
            ),

            ProductModel(
                sku="TEST-001",
                product_name="Test Enterprise Product",
                description="Test product for API testing",
                category="Analytics",
                list_price=Decimal("100.00"),
                currency_code="INR",
                is_active=True
            ),

            MetricModel(
                period="monthly",
                region="north",
                revenue=1250000,
                orders=320
            )

        ])

        db.commit()

    # Replace the production database dependency
    # with our test database session.

    def override_get_db():

        with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:

        with TestClient(app) as test_client:
            yield test_client

    finally:

        # Remove dependency override
        app.dependency_overrides.clear()

        # Clean up the temporary database
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()