
import pytest

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import (
    create_engine,
    event,
    select,
    func,
    text
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base

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


# --------------------------------------------------
# 1. Isolated test database
# --------------------------------------------------

@pytest.fixture
def db_session():

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record):

        cursor = dbapi_connection.cursor()

        cursor.execute("PRAGMA foreign_keys=ON")

        cursor.close()

    Base.metadata.create_all(bind=engine)

    TestSession = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    try:

        with TestSession() as session:
            yield session

    finally:

        Base.metadata.drop_all(bind=engine)
        engine.dispose()


# --------------------------------------------------
# 2. Reusable test data helpers
# --------------------------------------------------

def create_user(db, username="test_rep", role="sales_rep"):

    user = UserModel(
        username=username,
        hashed_password="test-password-hash",
        full_name=username,
        role=role,
        is_active=True,
    )

    db.add(user)
    db.flush()

    return user


def create_account(db, owner_id, name="Test Company"):

    account = AccountModel(
        company_name=name,
        industry="Technology",
        country="India",
        account_status="prospect",
        owner_id=owner_id,
    )

    db.add(account)
    db.flush()

    return account


def create_product(db, sku="TEST-001"):

    product = ProductModel(
        sku=sku,
        product_name="Test Enterprise Product",
        description="Test product",
        category="Analytics",
        list_price=Decimal("50000.00"),
        currency_code="INR",
        is_active=True,
    )

    db.add(product)
    db.flush()

    return product


def create_opportunity(db, account_id, owner_id, stage="proposal"):

    opportunity = OpportunityModel(
        account_id=account_id,
        owner_id=owner_id,
        opportunity_name="Test Opportunity",
        stage=stage,
        probability_pct=Decimal("60.00"),
        expected_close_date=date.today() + timedelta(days=30),
        currency_code="INR",
    )

    db.add(opportunity)
    db.flush()

    return opportunity


# --------------------------------------------------
# 3. Helper to test database constraint violations
# --------------------------------------------------

def assert_integrity_error(db, record):

    with pytest.raises(IntegrityError):

        with db.begin_nested():

            db.add(record)
            db.flush()


# --------------------------------------------------
# 4. Test ORM relationships
# --------------------------------------------------

def test_revops_relationships(db_session):

    db = db_session

    manager = create_user(
        db,
        username="test_manager",
        role="sales_manager",
    )

    rep = UserModel(
        username="relationship_rep",
        hashed_password="test-hash",
        full_name="Relationship Rep",
        role="sales_rep",
        manager_id=manager.user_id,
        is_active=True,
    )

    db.add(rep)
    db.flush()

    account = create_account(db, rep.user_id)

    contact = ContactModel(
        account_id=account.account_id,
        first_name="Rahul",
        last_name="Sharma",
        email="rahul@testcompany.example",
        job_title="CTO",
        is_primary=True,
    )

    product = create_product(db)

    opportunity = create_opportunity(
        db,
        account.account_id,
        rep.user_id,
        stage="closed_won",
    )

    line_item = OpportunityLineItemModel(
        opportunity_id=opportunity.opportunity_id,
        product_id=product.product_id,
        quantity=2,
        agreed_unit_price=Decimal("45000.00"),
    )

    db.add_all([contact, line_item])
    db.flush()

    booking = BookingModel(
        opportunity_id=opportunity.opportunity_id,
        recorded_by_id=manager.user_id,
        contract_value=Decimal("90000.00"),
        currency_code="INR",
    )

    db.add(booking)
    db.flush()

    # User hierarchy
    assert rep.manager.username == "test_manager"
    assert rep in manager.direct_reports

    # Account relationships
    assert account.owner.user_id == rep.user_id
    assert contact in account.contacts

    # Opportunity relationships
    assert opportunity.account == account
    assert opportunity.owner == rep
    assert line_item in opportunity.line_items

    # Product relationships
    assert line_item.product == product
    assert line_item in product.opportunity_line_items

    # Booking relationship
    assert opportunity.booking == booking
    assert booking.recorded_by == manager


# --------------------------------------------------
# 5. Test foreign key integrity
# --------------------------------------------------

def test_account_rejects_nonexistent_owner(db_session):

    invalid_account = AccountModel(
        company_name="Invalid Company",
        industry="Technology",
        country="India",
        account_status="prospect",
        owner_id=999999,
    )

    assert_integrity_error(db_session, invalid_account)


def test_contact_rejects_nonexistent_account(db_session):

    invalid_contact = ContactModel(
        account_id=999999,
        first_name="Invalid",
        last_name="Contact",
        email="invalid@example.com",
        is_primary=True,
    )

    assert_integrity_error(db_session, invalid_contact)


# --------------------------------------------------
# 6. Test unique constraints
# --------------------------------------------------

def test_user_username_must_be_unique(db_session):

    db = db_session

    create_user(db, username="duplicate_user")

    duplicate = UserModel(
        username="duplicate_user",
        hashed_password="test-hash",
        full_name="Duplicate User",
        role="sales_rep",
        is_active=True,
    )

    assert_integrity_error(db, duplicate)


def test_product_sku_must_be_unique(db_session):

    db = db_session

    create_product(db, sku="NFX-CRM")

    duplicate = ProductModel(
        sku="NFX-CRM",
        product_name="Duplicate Product",
        category="CRM",
        list_price=Decimal("1000.00"),
        currency_code="INR",
        is_active=True,
    )

    assert_integrity_error(db, duplicate)


def test_contact_email_must_be_unique_per_account(db_session):

    db = db_session

    user = create_user(db)
    account = create_account(db, user.user_id)

    first_contact = ContactModel(
        account_id=account.account_id,
        first_name="A",
        last_name="Person",
        email="same@example.com",
        is_primary=True,
    )

    db.add(first_contact)
    db.flush()

    duplicate = ContactModel(
        account_id=account.account_id,
        first_name="Another",
        last_name="Person",
        email="same@example.com",
        is_primary=False,
    )

    assert_integrity_error(db, duplicate)


# --------------------------------------------------
# 7. Test opportunity line item uniqueness
# --------------------------------------------------

def test_opportunity_product_combination_must_be_unique(db_session):

    db = db_session

    user = create_user(db)
    account = create_account(db, user.user_id)
    product = create_product(db)

    opportunity = create_opportunity(
        db,
        account.account_id,
        user.user_id,
    )

    first_item = OpportunityLineItemModel(
        opportunity_id=opportunity.opportunity_id,
        product_id=product.product_id,
        quantity=2,
        agreed_unit_price=Decimal("50000.00"),
    )

    db.add(first_item)
    db.flush()

    duplicate = OpportunityLineItemModel(
        opportunity_id=opportunity.opportunity_id,
        product_id=product.product_id,
        quantity=3,
        agreed_unit_price=Decimal("45000.00"),
    )

    assert_integrity_error(db, duplicate)


# --------------------------------------------------
# 8. Test check constraints
# --------------------------------------------------

def test_invalid_opportunity_stage_is_rejected(db_session):

    db = db_session

    user = create_user(db)
    account = create_account(db, user.user_id)

    invalid_opportunity = OpportunityModel(
        account_id=account.account_id,
        owner_id=user.user_id,
        opportunity_name="Invalid Stage Deal",
        stage="contract_signed",
        probability_pct=Decimal("100.00"),
        expected_close_date=date.today(),
        currency_code="INR",
    )

    assert_integrity_error(db, invalid_opportunity)


def test_invalid_probability_is_rejected(db_session):

    db = db_session

    user = create_user(db)
    account = create_account(db, user.user_id)

    invalid_opportunity = OpportunityModel(
        account_id=account.account_id,
        owner_id=user.user_id,
        opportunity_name="Invalid Probability Deal",
        stage="proposal",
        probability_pct=Decimal("150.00"),
        expected_close_date=date.today(),
        currency_code="INR",
    )

    assert_integrity_error(db, invalid_opportunity)


def test_zero_quantity_line_item_is_rejected(db_session):

    db = db_session

    user = create_user(db)
    account = create_account(db, user.user_id)
    product = create_product(db)
    opportunity = create_opportunity(
        db, account.account_id, user.user_id
    )

    invalid_item = OpportunityLineItemModel(
        opportunity_id=opportunity.opportunity_id,
        product_id=product.product_id,
        quantity=0,
        agreed_unit_price=Decimal("50000.00"),
    )

    assert_integrity_error(db, invalid_item)


# --------------------------------------------------
# 9. Test transaction rollback
# --------------------------------------------------

def test_transaction_rollback_is_atomic(db_session):

    db = db_session

    user = create_user(db)
    user_id = user.user_id

    db.commit()

    account = create_account(
        db,
        user_id,
        name="Rollback Test Company",
    )

    account_id = account.account_id

    invalid_contact = ContactModel(
        account_id=999999,
        first_name="Invalid",
        last_name="Contact",
        email="rollback@example.com",
        is_primary=True,
    )

    db.add(invalid_contact)

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()

    # The earlier account insert is also rolled back.
    assert db.get(AccountModel, account_id) is None

    # Previously committed user still exists.
    assert db.get(UserModel, user_id) is not None


def test_successful_commit_persists_record(db_session):

    db = db_session

    user = create_user(db)

    account = create_account(
        db,
        user.user_id,
        name="Committed Test Company",
    )

    account_id = account.account_id

    db.commit()

    saved_account = db.get(AccountModel, account_id)

    assert saved_account is not None
    assert saved_account.company_name == "Committed Test Company"

def test_opportunity_can_have_only_one_booking(db_session):

    db = db_session

    manager = create_user(
        db,
        username="booking_manager",
        role="sales_manager",
    )

    rep = create_user(db)

    account = create_account(db, rep.user_id)

    opportunity = create_opportunity(
        db,
        account.account_id,
        rep.user_id,
        stage="closed_won",
    )

    booking = BookingModel(
        opportunity_id=opportunity.opportunity_id,
        recorded_by_id=manager.user_id,
        contract_value=Decimal("100000.00"),
        currency_code="INR",
    )

    db.add(booking)
    db.flush()

    duplicate = BookingModel(
        opportunity_id=opportunity.opportunity_id,
        recorded_by_id=manager.user_id,
        contract_value=Decimal("100000.00"),
        currency_code="INR",
    )

    assert_integrity_error(db, duplicate)

def test_sales_target_period_must_be_unique(db_session):

    db = db_session
    user = create_user(db)

    target = SalesTargetModel(
        user_id=user.user_id,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 12, 31),
        target_amount=Decimal("12000000.00"),
        currency_code="INR",
    )

    db.add(target)
    db.flush()

    duplicate = SalesTargetModel(
        user_id=user.user_id,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 12, 31),
        target_amount=Decimal("15000000.00"),
        currency_code="INR",
    )

    assert_integrity_error(db, duplicate)


def test_deleting_opportunity_deletes_line_items(db_session):

    db = db_session

    user = create_user(db)
    account = create_account(db, user.user_id)
    product = create_product(db)

    opportunity = create_opportunity(
        db,
        account.account_id,
        user.user_id,
    )

    item = OpportunityLineItemModel(
        opportunity_id=opportunity.opportunity_id,
        product_id=product.product_id,
        quantity=2,
        agreed_unit_price=Decimal("50000.00"),
    )

    db.add(item)
    db.flush()

    opportunity_id = opportunity.opportunity_id

    # Check whether SQLite foreign keys are enabled
    fk_status = db.scalar(text("PRAGMA foreign_keys"))

    print("\nForeign key enforcement:", fk_status)

    assert fk_status == 1, "SQLite foreign keys are disabled"

    # Inspect the actual foreign-key definition
    fk_details = db.execute(
        text("PRAGMA foreign_key_list(opportunity_line_items)")
    ).mappings().all()

    print("\nForeign key definitions:")
    for fk in fk_details:
        print(dict(fk))

    cascade_exists = any(
        fk["from"] == "opportunity_id"
        and fk["table"] == "opportunities"
        and fk["on_delete"].upper() == "CASCADE"
        for fk in fk_details
    )

    assert cascade_exists, "ON DELETE CASCADE is missing"

    # Delete opportunity
    db.delete(opportunity)
    db.flush()

    # Verify parent deletion
    assert db.get(OpportunityModel, opportunity_id) is None

    # Verify child deletion directly in database
    remaining_items = db.scalar(
        select(func.count())
        .select_from(OpportunityLineItemModel)
        .where(
            OpportunityLineItemModel.opportunity_id == opportunity_id
        )
    )

    print("\nRemaining line items:", remaining_items)

    assert remaining_items == 0
