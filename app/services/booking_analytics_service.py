
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import (
    select,
    func,
)
from sqlalchemy.orm import Session

from app.models import (
    BookingModel,
    OpportunityModel,
    UserModel,
    OpportunityLineItemModel,
    ProductModel,
)


REPORTING_TIME_ZONE = "Asia/Kolkata"


@dataclass(frozen=True)
class BookingFilters:
    start_at: datetime | None = None
    end_at: datetime | None = None

    region: str | None = None
    owner_id: int | None = None

    def __post_init__(self):

        if (
            self.start_at is not None
            and (
                self.start_at.tzinfo is None
                or self.start_at.utcoffset() is None
            )
        ):
            raise ValueError(
                "start_at must be timezone-aware"
            )

        if (
            self.end_at is not None
            and (
                self.end_at.tzinfo is None
                or self.end_at.utcoffset() is None
            )
        ):
            raise ValueError(
                "end_at must be timezone-aware"
            )

        if (
            self.start_at is not None
            and self.end_at is not None
            and self.start_at >= self.end_at
        ):
            raise ValueError(
                "start_at must be before end_at"
            )

        if self.owner_id is not None and self.owner_id <= 0:
            raise ValueError(
                "owner_id must be positive"
            )


def build_booking_scope(filters: BookingFilters):
    """
    Build a base query containing valid bookings,
    opportunity owners and sales regions.

    Only bookings attached to closed-won opportunities
    are included.
    """

    statement = (
        select(
            BookingModel.booking_id,
            BookingModel.opportunity_id,
            BookingModel.contract_value,
            BookingModel.currency_code,
            BookingModel.booked_at,

            OpportunityModel.owner_id,

            UserModel.full_name.label("owner_name"),
            UserModel.region,
        )
        .select_from(BookingModel)
        .join(
            OpportunityModel,
            OpportunityModel.opportunity_id
            == BookingModel.opportunity_id,
        )
        .join(
            UserModel,
            UserModel.user_id
            == OpportunityModel.owner_id,
        )
    )

    conditions = [
        OpportunityModel.stage == "closed_won"
    ]

    # Booking period
    if filters.start_at is not None:
        conditions.append(
            BookingModel.booked_at >= filters.start_at
        )

    if filters.end_at is not None:
        conditions.append(
            BookingModel.booked_at < filters.end_at
        )

    # Sales region
    if filters.region is not None:
        conditions.append(
            UserModel.region == filters.region
        )

    # Sales representative
    if filters.owner_id is not None:
        conditions.append(
            OpportunityModel.owner_id == filters.owner_id
        )

    return statement.where(*conditions)


def get_bookings_by_month(
    db: Session,
    filters: BookingFilters,
):
    """
    Monthly booking count, contract value and
    average booking size.
    """

    booking_scope = (
        build_booking_scope(filters)
        .subquery("booking_scope")
    )

    month_bucket = func.date_trunc(
        "month",
        booking_scope.c.booked_at,
        REPORTING_TIME_ZONE,
    )

    statement = (
        select(
            month_bucket.label("month"),

            booking_scope.c.currency_code,

            func.count(
                booking_scope.c.booking_id
            ).label("booking_count"),

            func.sum(
                booking_scope.c.contract_value
            ).label("total_bookings"),

            func.avg(
                booking_scope.c.contract_value
            ).label("average_booking_size"),
        )
        .group_by(
            month_bucket,
            booking_scope.c.currency_code,
        )
        .order_by(
            month_bucket,
            booking_scope.c.currency_code,
        )
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def get_bookings_by_region(
    db: Session,
    filters: BookingFilters,
):
    """
    Regional booking count, contract value
    and average booking size.
    """

    booking_scope = (
        build_booking_scope(filters)
        .subquery("booking_scope")
    )

    region_name = func.coalesce(
        booking_scope.c.region,
        "Unassigned",
    )

    statement = (
        select(
            region_name.label("region"),

            booking_scope.c.currency_code,

            func.count(
                booking_scope.c.booking_id
            ).label("booking_count"),

            func.sum(
                booking_scope.c.contract_value
            ).label("total_bookings"),

            func.avg(
                booking_scope.c.contract_value
            ).label("average_booking_size"),
        )
        .group_by(
            region_name,
            booking_scope.c.currency_code,
        )
        .order_by(
            func.sum(
                booking_scope.c.contract_value
            ).desc()
        )
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def build_product_line_value_subquery():
    """
    Calculate the original monetary value
    of each product within each opportunity.
    """

    statement = (
        select(
            OpportunityLineItemModel.opportunity_id.label(
                "opportunity_id"
            ),

            OpportunityLineItemModel.product_id.label(
                "product_id"
            ),

            func.sum(
                OpportunityLineItemModel.quantity
                * OpportunityLineItemModel.agreed_unit_price
            ).label("product_line_value"),
        )
        .group_by(
            OpportunityLineItemModel.opportunity_id,
            OpportunityLineItemModel.product_id,
        )
    )

    return statement.subquery("product_line_values")


def build_opportunity_line_totals_subquery(
    product_line_values,
):
    """
    Calculate the complete line-item value
    of each opportunity across all products.
    """

    statement = (
        select(
            product_line_values.c.opportunity_id,

            func.sum(
                product_line_values.c.product_line_value
            ).label("total_line_value"),
        )
        .group_by(
            product_line_values.c.opportunity_id
        )
    )

    return statement.subquery("opportunity_line_totals")


def build_booking_product_allocation_query(
    filters: BookingFilters,
):
    """
    Allocate each valid booking's contract value
    proportionally across its products.
    """

    booking_scope = (
        build_booking_scope(filters)
        .subquery("booking_scope")
    )

    product_line_values = (
        build_product_line_value_subquery()
    )

    opportunity_totals = (
        build_opportunity_line_totals_subquery(
            product_line_values
        )
    )

    allocated_booking_value = (
        booking_scope.c.contract_value
        * product_line_values.c.product_line_value
        / func.nullif(
            opportunity_totals.c.total_line_value,
            0,
        )
    )

    statement = (
        select(
            booking_scope.c.booking_id,
            booking_scope.c.opportunity_id,
            booking_scope.c.booked_at,
            booking_scope.c.currency_code,

            booking_scope.c.owner_id,
            booking_scope.c.owner_name,
            booking_scope.c.region,

            ProductModel.product_id,
            ProductModel.sku,
            ProductModel.product_name,
            ProductModel.category,

            product_line_values.c.product_line_value,
            opportunity_totals.c.total_line_value,

            allocated_booking_value.label(
                "allocated_booking_value"
            ),
        )
        .select_from(booking_scope)
        .join(
            product_line_values,
            product_line_values.c.opportunity_id
            == booking_scope.c.opportunity_id,
        )
        .join(
            opportunity_totals,
            opportunity_totals.c.opportunity_id
            == booking_scope.c.opportunity_id,
        )
        .join(
            ProductModel,
            ProductModel.product_id
            == product_line_values.c.product_id,
        )
    )

    return statement


def get_bookings_by_product(
    db: Session,
    filters: BookingFilters,
    product_ids: tuple[int, ...] = (),
):
    """
    Product-level booking count and allocated
    contract value.

    Product selection is optional.
    """

    allocation_query = (
        build_booking_product_allocation_query(filters)
        .subquery("booking_product_allocations")
    )

    if any(product_id <= 0 for product_id in product_ids):
        raise ValueError("product_ids must be positive")

    conditions = []

    if product_ids:
        conditions.append(
            allocation_query.c.product_id.in_(product_ids)
        )

    statement = (
        select(
            allocation_query.c.product_id,
            allocation_query.c.sku,
            allocation_query.c.product_name,
            allocation_query.c.category,
            allocation_query.c.currency_code,

            func.count(
                func.distinct(
                    allocation_query.c.booking_id
                )
            ).label("booking_count"),

            func.sum(
                allocation_query.c.allocated_booking_value
            ).label("allocated_bookings"),
        )
        .group_by(
            allocation_query.c.product_id,
            allocation_query.c.sku,
            allocation_query.c.product_name,
            allocation_query.c.category,
            allocation_query.c.currency_code,
        )
        .order_by(
            func.sum(
                allocation_query.c.allocated_booking_value
            ).desc()
        )
    )

    if conditions:
        statement = statement.where(*conditions)

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def get_bookings_by_month_region_product(
    db: Session,
    filters: BookingFilters,
    product_ids: tuple[int, ...] = (),
):
    """
    Three-dimensional booking analysis:
    month + region + product.
    """

    allocations = (
        build_booking_product_allocation_query(filters)
        .subquery("booking_product_allocations")
    )

    month_bucket = func.date_trunc(
        "month",
        allocations.c.booked_at,
        REPORTING_TIME_ZONE,
    )

    region_name = func.coalesce(
        allocations.c.region,
        "Unassigned",
    )

    if any(product_id <= 0 for product_id in product_ids):
        raise ValueError("product_ids must be positive")

    statement = (
        select(
            month_bucket.label("month"),
            region_name.label("region"),

            allocations.c.product_id,
            allocations.c.sku,
            allocations.c.product_name,
            allocations.c.currency_code,

            func.count(
                func.distinct(allocations.c.booking_id)
            ).label("booking_count"),

            func.sum(
                allocations.c.allocated_booking_value
            ).label("allocated_bookings"),
        )
    )

    if product_ids:
        statement = statement.where(
            allocations.c.product_id.in_(product_ids)
        )

    statement = (
        statement
        .group_by(
            month_bucket,
            region_name,
            allocations.c.product_id,
            allocations.c.sku,
            allocations.c.product_name,
            allocations.c.currency_code,
        )
        .order_by(
            month_bucket,
            region_name,
            func.sum(
                allocations.c.allocated_booking_value
            ).desc(),
        )
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def get_unallocated_bookings_summary(
    db: Session,
    filters: BookingFilters,
):
    """
    Find closed-won bookings whose opportunities
    have no associated line items.
    """

    booking_scope = (
        build_booking_scope(filters)
        .subquery("booking_scope")
    )

    has_line_items = (
        select(1)
        .where(
            OpportunityLineItemModel.opportunity_id
            == booking_scope.c.opportunity_id
        )
        .exists()
    )

    statement = (
        select(
            booking_scope.c.currency_code,

            func.count(
                booking_scope.c.booking_id
            ).label("unallocated_booking_count"),

            func.sum(
                booking_scope.c.contract_value
            ).label("unallocated_booking_value"),
        )
        .where(~has_line_items)
        .group_by(
            booking_scope.c.currency_code
        )
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]
