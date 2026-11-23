from __future__ import annotations
from sqlalchemy import (
    Boolean,
    Integer,
    String,
    CHAR,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    INTEGER,
    Numeric,
    text,
    Text,
    UniqueConstraint,
    func,
    true
)
from datetime import date, datetime
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from app.database import Base
from decimal import Decimal

# Customer Table
class CustomerModel(Base):
    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    segment: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

# Product table

class ProductModel(Base):
    __tablename__ = "products"

    __table_args__ = (
        UniqueConstraint("sku", name="uq_products_sku"),
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    sku: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    product_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    list_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    currency_code: Mapped[str] = mapped_column(
        CHAR(3),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    opportunity_line_items: Mapped[list["OpportunityLineItemModel"]] = (
        relationship(back_populates="product")
    )


# Business metrics table
class MetricModel(Base):
    __tablename__ = "business_metrics"

    metric_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    period: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    region: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    revenue: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    orders: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint(
            "username",
            name="uq_users_username"
        ),
        CheckConstraint(
            "role IN ('sales_rep', 'sales_manager', "
            "'revops_analyst', 'executive', 'admin')",
            name="ck_users_role"
        ),
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(30),
        default="revops_analyst",
        nullable=False
    )

    region: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.user_id",
            name="fk_users_manager_id_users",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Self-referencing management hierarchy

    manager: Mapped[UserModel | None] = relationship(
        back_populates="direct_reports",
        remote_side=lambda: [UserModel.user_id]
    )

    direct_reports: Mapped[list[UserModel]] = relationship(
        back_populates="manager"
    )

    # Business relationships

    owned_accounts: Mapped[list[AccountModel]] = relationship(
        back_populates="owner",
        foreign_keys=lambda: [AccountModel.owner_id]
    )

    opportunities: Mapped[list[OpportunityModel]] = relationship(
        back_populates="owner",
        foreign_keys=lambda: [OpportunityModel.owner_id]
    )

    sales_activities: Mapped[list[SalesActivityModel]] = relationship(
        back_populates="owner",
        foreign_keys=lambda: [SalesActivityModel.owner_id]
    )

    sales_targets: Mapped[list[SalesTargetModel]] = relationship(
        back_populates="user"
    )

    recorded_bookings: Mapped[list[BookingModel]] = relationship(
        back_populates="recorded_by",
        foreign_keys=lambda: [BookingModel.recorded_by_id]
    )

class AccountModel(Base):

    __tablename__ = "accounts"

    __table_args__ = (
        CheckConstraint(
            "account_status IN ('prospect', 'customer', 'churned', 'inactive')",
            name="ck_accounts_status"
        ),

        Index(
            "ix_accounts_owner_id",
            "owner_id"
        ),

        Index(
            "ix_accounts_company_name",
            "company_name"
        ),
    )

    account_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    company_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    industry: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    website: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    country: Mapped[str] = mapped_column(
        String(100),
        default="India",
        nullable=False
    )

    account_status: Mapped[str] = mapped_column(
        String(30),
        default="prospect",
        nullable=False
    )

    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.user_id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships

    owner: Mapped[UserModel | None] = relationship(
        back_populates="owned_accounts",
        foreign_keys=[owner_id]
    )

    contacts: Mapped[list[ContactModel]] = relationship(
        back_populates="account"
    )

    opportunities: Mapped[list[OpportunityModel]] = relationship(
        back_populates="account"
    )

    sales_activities: Mapped[list[SalesActivityModel]] = relationship(
        back_populates="account"
    )

class ContactModel(Base):

    __tablename__ = "contacts"

    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "email",
            name="uq_contacts_account_email"
        ),

        Index(
            "ix_contacts_account_id",
            "account_id"
        )
    )

    contact_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    account_id: Mapped[int] = mapped_column(
        ForeignKey(
            "accounts.account_id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    first_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False
    )

    last_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    job_title: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    account: Mapped[AccountModel] = relationship(
        back_populates="contacts"
    )

    sales_activities: Mapped[list[SalesActivityModel]] = relationship(
        back_populates="contact"
    )

class OpportunityModel(Base):

    __tablename__ = "opportunities"

    __table_args__ = (
        CheckConstraint(
            "stage IN ('qualification', 'discovery', "
            "'proposal', 'negotiation', "
            "'closed_won', 'closed_lost')",
            name="ck_opportunities_stage"
        ),

        CheckConstraint(
            "probability_pct >= 0 AND probability_pct <= 100",
            name="ck_opportunities_probability"
        ),

        Index(
            "ix_opportunities_owner_stage",
            "owner_id",
            "stage"
        ),

        Index(
            "ix_opportunities_stage_close_date",
            "stage",
            "expected_close_date"
        )
    )

    opportunity_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    account_id: Mapped[int] = mapped_column(
        ForeignKey(
            "accounts.account_id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.user_id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    opportunity_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    stage: Mapped[str] = mapped_column(
        String(30),
        default="qualification",
        nullable=False
    )

    probability_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=0,
        nullable=False
    )

    expected_close_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    currency_code: Mapped[str] = mapped_column(
        CHAR(3),
        default="INR",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships

    account: Mapped[AccountModel] = relationship(
        back_populates="opportunities"
    )

    owner: Mapped[UserModel] = relationship(
        back_populates="opportunities",
        foreign_keys=[owner_id]
    )

    line_items: Mapped[
        list["OpportunityLineItemModel"]
    ] = relationship(
        back_populates="opportunity",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    sales_activities: Mapped[
        list[SalesActivityModel]
    ] = relationship(
        back_populates="opportunity"
    )

    booking: Mapped[BookingModel | None] = relationship(
        back_populates="opportunity",
        uselist=False
    )

    @property
    def opportunity_value(self) -> Decimal:

        return sum(
            (
                item.quantity * item.agreed_unit_price
                for item in self.line_items
            ),
            start=Decimal("0.00")
        )

class OpportunityLineItemModel(Base):

    __tablename__ = "opportunity_line_items"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_opportunity_items_quantity"
        ),

        CheckConstraint(
            "agreed_unit_price > 0",
            name="ck_opportunity_items_price"
        ),

        UniqueConstraint(
            "opportunity_id",
            "product_id",
            name="uq_opportunity_product"
        ),

        Index(
            "ix_opportunity_items_product_id",
            "product_id"
        )
    )

    line_item_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey(
            "opportunities.opportunity_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey(
            "products.product_id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    agreed_unit_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    opportunity: Mapped[OpportunityModel] = relationship(
        back_populates="line_items"
    )

    product: Mapped[ProductModel] = relationship(
        back_populates="opportunity_line_items"
    )

class SalesActivityModel(Base):

    __tablename__ = "sales_activities"

    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('call', 'email', 'meeting', 'demo', 'task')",
            name="ck_sales_activity_type"
        ),

        CheckConstraint(
            "activity_status IN ('planned', 'completed', 'cancelled')",
            name="ck_sales_activity_status"
        ),

        Index(
            "ix_sales_activities_owner_due",
            "owner_id",
            "due_at"
        ),

        Index(
            "ix_sales_activities_account_id",
            "account_id"
        )
    )

    activity_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    account_id: Mapped[int] = mapped_column(
        ForeignKey(
            "accounts.account_id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    opportunity_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "opportunities.opportunity_id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "contacts.contact_id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.user_id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    activity_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    subject: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    activity_status: Mapped[str] = mapped_column(
        String(30),
        default="planned",
        nullable=False
    )

    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    account: Mapped[AccountModel] = relationship(
        back_populates="sales_activities"
    )

    opportunity: Mapped[OpportunityModel | None] = relationship(
        back_populates="sales_activities"
    )

    contact: Mapped[ContactModel | None] = relationship(
        back_populates="sales_activities"
    )

    owner: Mapped[UserModel] = relationship(
        back_populates="sales_activities",
        foreign_keys=[owner_id]
    )

class SalesTargetModel(Base):

    __tablename__ = "sales_targets"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "period_start",
            "period_end",
            name="uq_sales_target_user_period"
        ),

        CheckConstraint(
            "period_end >= period_start",
            name="ck_sales_target_period"
        ),

        CheckConstraint(
            "target_amount > 0",
            name="ck_sales_target_amount"
        )
    )

    target_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.user_id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    period_start: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    period_end: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    target_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    currency_code: Mapped[str] = mapped_column(
        CHAR(3),
        default="INR",
        nullable=False
    )

    user: Mapped[UserModel] = relationship(
        back_populates="sales_targets"
    )

class BookingModel(Base):

    __tablename__ = "bookings"

    __table_args__ = (
        CheckConstraint(
            "contract_value > 0",
            name="ck_bookings_contract_value"
        ),

        Index(
            "ix_bookings_booked_at",
            "booked_at"
        )
    )

    booking_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey(
            "opportunities.opportunity_id",
            ondelete="RESTRICT"
        ),
        unique=True,
        nullable=False
    )

    recorded_by_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.user_id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    contract_value: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    currency_code: Mapped[str] = mapped_column(
        CHAR(3),
        default="INR",
        nullable=False
    )

    booked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    opportunity: Mapped[OpportunityModel] = relationship(
        back_populates="booking"
    )

    recorded_by: Mapped[UserModel] = relationship(
        back_populates="recorded_bookings",
        foreign_keys=[recorded_by_id]
    )

