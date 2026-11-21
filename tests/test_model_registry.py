from sqlalchemy.orm import configure_mappers

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
    BookingModel
)


def test_all_revops_models_registered():

    expected_tables = {
        "users",
        "accounts",
        "contacts",
        "products",
        "opportunities",
        "opportunity_line_items",
        "sales_activities",
        "sales_targets",
        "bookings"
    }

    actual_tables = set(Base.metadata.tables.keys())

    assert expected_tables.issubset(actual_tables)


def test_sqlalchemy_relationships_configure():

    configure_mappers()

    assert UserModel.manager.property is not None
    assert AccountModel.contacts.property is not None
    assert OpportunityModel.line_items.property is not None
    assert OpportunityModel.booking.property is not None
    assert ProductModel.opportunity_line_items.property is not None