
import os

import pytest

from dotenv import load_dotenv

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


load_dotenv()


@pytest.fixture(scope="session")
def pg_engine():

    test_url = os.getenv("TEST_DATABASE_URL")

    if not test_url:
        raise RuntimeError(
            "TEST_DATABASE_URL is not configured"
        )

    parsed_url = make_url(test_url)

    # Safety check: never allow this fixture to
    # connect to the development database.
    if (
        parsed_url.database is None
        or not parsed_url.database.endswith("_test")
    ):
        raise RuntimeError(
            "Integration tests require a database "
            "whose name ends with _test"
        )

    engine = create_engine(
        test_url,
        pool_pre_ping=True,
    )

    with engine.connect() as connection:

        database_name = connection.scalar(
            text("SELECT current_database()")
        )

        if not database_name.endswith("_test"):
            raise RuntimeError(
                "Connected to a non-test database"
            )

    yield engine

    engine.dispose()


@pytest.fixture
def pg_session(pg_engine):

    connection = pg_engine.connect()

    outer_transaction = connection.begin()

    session = Session(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session

    finally:
        session.close()

        if outer_transaction.is_active:
            outer_transaction.rollback()

        connection.close()


from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.models import (
    UserModel,
    AccountModel,
    ContactModel,
    ProductModel,
    OpportunityModel,
    OpportunityLineItemModel,
    SalesActivityModel,
    SalesTargetModel,
    BookingModel,
)


TZ = ZoneInfo("Asia/Kolkata")


@pytest.fixture
def revenue_scenario(pg_session):

    db = pg_session

    # -------------------------------------
    # 1. Sales representatives
    # -------------------------------------

    riya = UserModel(
        username="test_riya",
        hashed_password="test-hash",
        full_name="Riya Mehta",
        role="sales_rep",
        region="North",
        is_active=True,
    )

    kabir = UserModel(
        username="test_kabir",
        hashed_password="test-hash",
        full_name="Kabir Singh",
        role="sales_rep",
        region="West",
        is_active=True,
    )

    db.add_all([riya, kabir])
    db.flush()

    # -------------------------------------
    # 2. Accounts
    # -------------------------------------

    northstar = AccountModel(
        company_name="Test Northstar Logistics",
        industry="Logistics",
        country="India",
        account_status="customer",
        owner_id=riya.user_id,
    )

    westline = AccountModel(
        company_name="Test Westline Technologies",
        industry="Technology",
        country="India",
        account_status="customer",
        owner_id=kabir.user_id,
    )

    db.add_all([northstar, westline])
    db.flush()

    # -------------------------------------
    # 3. Products
    # -------------------------------------

    crm = ProductModel(
        sku="TEST-CRM",
        product_name="Test CRM",
        description="CRM test product",
        category="CRM",
        list_price=Decimal("400000.00"),
        currency_code="INR",
        is_active=True,
    )

    analytics = ProductModel(
        sku="TEST-ANALYTICS",
        product_name="Test Analytics",
        description="Analytics test product",
        category="Analytics",
        list_price=Decimal("600000.00"),
        currency_code="INR",
        is_active=True,
    )

    db.add_all([crm, analytics])
    db.flush()

    # -------------------------------------
    # 4. Opportunities
    # -------------------------------------

    won_riya = OpportunityModel(
        account_id=northstar.account_id,
        owner_id=riya.user_id,
        opportunity_name="Test CRM Transformation",
        stage="closed_won",
        probability_pct=Decimal("100.00"),
        expected_close_date=date(2026, 1, 31),
        currency_code="INR",
        created_at=datetime(2026, 1, 1, 10, tzinfo=TZ),
        closed_at=datetime(2026, 1, 31, 10, tzinfo=TZ),
    )

    lost_riya = OpportunityModel(
        account_id=northstar.account_id,
        owner_id=riya.user_id,
        opportunity_name="Test Analytics Expansion",
        stage="closed_lost",
        probability_pct=Decimal("0.00"),
        expected_close_date=date(2026, 2, 4),
        currency_code="INR",
        created_at=datetime(2026, 1, 5, 10, tzinfo=TZ),
        closed_at=datetime(2026, 2, 4, 10, tzinfo=TZ),
    )

    open_riya = OpportunityModel(
        account_id=northstar.account_id,
        owner_id=riya.user_id,
        opportunity_name="Test CRM Upgrade",
        stage="proposal",
        probability_pct=Decimal("60.00"),
        expected_close_date=date(2026, 3, 20),
        currency_code="INR",
        created_at=datetime(2026, 1, 20, 10, tzinfo=TZ),
        closed_at=None,
    )

    won_kabir = OpportunityModel(
        account_id=westline.account_id,
        owner_id=kabir.user_id,
        opportunity_name="Test CRM Deployment",
        stage="closed_won",
        probability_pct=Decimal("100.00"),
        expected_close_date=date(2026, 2, 9),
        currency_code="INR",
        created_at=datetime(2026, 1, 10, 10, tzinfo=TZ),
        closed_at=datetime(2026, 2, 9, 10, tzinfo=TZ),
    )

    db.add_all([
        won_riya,
        lost_riya,
        open_riya,
        won_kabir,
    ])

    db.flush()

    # -------------------------------------
    # 5. Opportunity line items
    # -------------------------------------

    line_items = [
        # Riya's won opportunity:
        # Original line value = ₹10 lakh.
        OpportunityLineItemModel(
            opportunity_id=won_riya.opportunity_id,
            product_id=crm.product_id,
            quantity=1,
            agreed_unit_price=Decimal("400000.00"),
        ),

        OpportunityLineItemModel(
            opportunity_id=won_riya.opportunity_id,
            product_id=analytics.product_id,
            quantity=1,
            agreed_unit_price=Decimal("600000.00"),
        ),

        # Riya's lost opportunity.
        OpportunityLineItemModel(
            opportunity_id=lost_riya.opportunity_id,
            product_id=crm.product_id,
            quantity=1,
            agreed_unit_price=Decimal("300000.00"),
        ),

        # Riya's open opportunity.
        OpportunityLineItemModel(
            opportunity_id=open_riya.opportunity_id,
            product_id=crm.product_id,
            quantity=1,
            agreed_unit_price=Decimal("500000.00"),
        ),

        # Kabir's won opportunity.
        OpportunityLineItemModel(
            opportunity_id=won_kabir.opportunity_id,
            product_id=crm.product_id,
            quantity=1,
            agreed_unit_price=Decimal("600000.00"),
        ),
    ]

    db.add_all(line_items)
    db.flush()

    # -------------------------------------
    # 6. Actual bookings
    # -------------------------------------

    bookings = [
        BookingModel(
            opportunity_id=won_riya.opportunity_id,
            recorded_by_id=riya.user_id,
            contract_value=Decimal("900000.00"),
            currency_code="INR",
            booked_at=datetime(2026, 1, 31, 10, tzinfo=TZ),
        ),

        BookingModel(
            opportunity_id=won_kabir.opportunity_id,
            recorded_by_id=kabir.user_id,
            contract_value=Decimal("600000.00"),
            currency_code="INR",
            booked_at=datetime(2026, 2, 9, 10, tzinfo=TZ),
        ),
    ]

    db.add_all(bookings)

    # -------------------------------------
    # 7. Q1 sales targets
    # -------------------------------------

    targets = [
        SalesTargetModel(
            user_id=riya.user_id,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
            target_amount=Decimal("1000000.00"),
            currency_code="INR",
        ),

        SalesTargetModel(
            user_id=kabir.user_id,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 3, 31),
            target_amount=Decimal("500000.00"),
            currency_code="INR",
        ),
    ]

    db.add_all(targets)

    # -------------------------------------
    # 8. Account contacts
    # -------------------------------------

    contact = ContactModel(
        account_id=northstar.account_id,
        first_name="Arjun",
        last_name="Test",
        email="arjun@test-northstar.example",
        job_title="CTO",
        is_primary=True,
    )

    db.add(contact)
    db.flush()

    # -------------------------------------
    # 9. Completed sales activity
    # -------------------------------------

    activity = SalesActivityModel(
        account_id=northstar.account_id,
        opportunity_id=open_riya.opportunity_id,
        contact_id=contact.contact_id,
        owner_id=riya.user_id,
        activity_type="meeting",
        subject="Test discovery meeting",
        notes="Test sales activity",
        activity_status="completed",
        due_at=datetime(2026, 2, 5, 10, tzinfo=TZ),
        completed_at=datetime(2026, 2, 5, 10, tzinfo=TZ),
    )

    db.add(activity)
    db.flush()

    return {
        "riya": riya,
        "kabir": kabir,
        "northstar": northstar,
        "westline": westline,
        "crm": crm,
        "analytics": analytics,
        "won_riya": won_riya,
        "lost_riya": lost_riya,
        "open_riya": open_riya,
        "won_kabir": won_kabir,
    }
