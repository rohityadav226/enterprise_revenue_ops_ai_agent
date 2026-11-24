
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    select,
    func,
    case,
    cast,
    literal,
    Numeric,
    extract,
)

from sqlalchemy.orm import Session

from app.models import (
    UserModel,
    OpportunityModel,
    OpportunityLineItemModel,
    BookingModel,
)


@dataclass(frozen=True)
class SalesPerformanceFilters:

    start_at: datetime | None = None
    end_at: datetime | None = None

    region: str | None = None
    owner_id: int | None = None

    product_ids: tuple[int, ...] = ()

    def __post_init__(self):

        if (
            self.start_at is not None
            and (
                self.start_at.tzinfo is None
                or self.start_at.utcoffset() is None
            )
        ):
            raise ValueError("start_at must be timezone-aware")

        if (
            self.end_at is not None
            and (
                self.end_at.tzinfo is None
                or self.end_at.utcoffset() is None
            )
        ):
            raise ValueError("end_at must be timezone-aware")

        if (
            self.start_at is not None
            and self.end_at is not None
            and self.start_at >= self.end_at
        ):
            raise ValueError("start_at must be before end_at")

        if self.owner_id is not None and self.owner_id <= 0:
            raise ValueError("owner_id must be positive")

        if any(product_id <= 0 for product_id in self.product_ids):
            raise ValueError("product_ids must be positive")


def build_product_exists_condition(product_ids):
    """
    Check whether an opportunity contains
    at least one of the selected products.
    """

    if not product_ids:
        return None

    return (
        select(1)
        .select_from(OpportunityLineItemModel)
        .where(
            OpportunityLineItemModel.opportunity_id
            == OpportunityModel.opportunity_id,

            OpportunityLineItemModel.product_id.in_(
                product_ids
            ),
        )
        .exists()
    )


def apply_owner_region_product_filters(
    conditions,
    filters: SalesPerformanceFilters,
):

    if filters.region is not None:
        conditions.append(
            UserModel.region == filters.region
        )

    if filters.owner_id is not None:
        conditions.append(
            OpportunityModel.owner_id == filters.owner_id
        )

    product_condition = build_product_exists_condition(
        filters.product_ids
    )

    if product_condition is not None:
        conditions.append(product_condition)

    return conditions


def build_opportunity_scope(
    filters: SalesPerformanceFilters,
    period_column,
    stages: tuple[str, ...] | None = None,
    require_closed: bool = False,
):
    """
    Build an opportunity scope with owner, region
    and product filters.

    period_column determines which event date to filter.
    """

    statement = (
        select(
            OpportunityModel.opportunity_id,
            OpportunityModel.stage,
            OpportunityModel.created_at,
            OpportunityModel.closed_at,
            OpportunityModel.owner_id,

            UserModel.full_name.label("owner_name"),
            UserModel.region,
        )
        .select_from(OpportunityModel)
        .join(
            UserModel,
            UserModel.user_id == OpportunityModel.owner_id,
        )
    )

    conditions = []

    if filters.start_at is not None:
        conditions.append(
            period_column >= filters.start_at
        )

    if filters.end_at is not None:
        conditions.append(
            period_column < filters.end_at
        )

    if stages is not None:
        conditions.append(
            OpportunityModel.stage.in_(stages)
        )

    if require_closed:
        conditions.append(
            OpportunityModel.closed_at.is_not(None)
        )

    conditions = apply_owner_region_product_filters(
        conditions,
        filters,
    )

    return statement.where(*conditions).subquery(
        "opportunity_scope"
    )


CLOSED_STAGES = ("closed_won", "closed_lost")

OPEN_STAGES = (
    "qualification",
    "discovery",
    "proposal",
    "negotiation",
)


def get_opportunity_conversion_summary(
    db: Session,
    filters: SalesPerformanceFilters,
):
    """
    Analyse opportunities created during a reporting period.

    Open opportunities remain in the denominator.
    Conversion is measured as wins / all created opportunities.
    """

    scope = build_opportunity_scope(
        filters=filters,
        period_column=OpportunityModel.created_at,
    )

    total = func.count(
        scope.c.opportunity_id
    )

    won = func.coalesce(
        func.sum(
            case(
                (scope.c.stage == "closed_won", 1),
                else_=0,
            )
        ),
        0,
    )

    lost = func.coalesce(
        func.sum(
            case(
                (scope.c.stage == "closed_lost", 1),
                else_=0,
            )
        ),
        0,
    )

    open_count = func.coalesce(
        func.sum(
            case(
                (scope.c.stage.in_(OPEN_STAGES), 1),
                else_=0,
            )
        ),
        0,
    )

    hundred = literal(Decimal("100.00"))

    conversion_rate = cast(
        won * hundred / func.nullif(total, 0),
        Numeric(7, 2),
    )

    resolution_rate = cast(
        (won + lost) * hundred / func.nullif(total, 0),
        Numeric(7, 2),
    )

    statement = select(
        total.label("created_opportunities"),
        won.label("closed_won"),
        lost.label("closed_lost"),
        open_count.label("still_open"),

        func.coalesce(
            conversion_rate,
            literal(Decimal("0.00")),
        ).label("opportunity_conversion_pct"),

        func.coalesce(
            resolution_rate,
            literal(Decimal("0.00")),
        ).label("opportunity_resolution_pct"),
    ).select_from(scope)

    result = db.execute(statement).mappings().one()

    return dict(result)


def _build_win_rate_aggregate(scope):

    won = func.sum(
        case(
            (scope.c.stage == "closed_won", 1),
            else_=0,
        )
    )

    lost = func.sum(
        case(
            (scope.c.stage == "closed_lost", 1),
            else_=0,
        )
    )

    total_closed = func.count(
        scope.c.opportunity_id
    )

    win_rate = cast(
        won * literal(Decimal("100.00"))
        / func.nullif(total_closed, 0),
        Numeric(7, 2),
    )

    return (
        func.coalesce(won, 0),
        func.coalesce(lost, 0),
        total_closed,
        func.coalesce(
            win_rate,
            literal(Decimal("0.00")),
        ),
    )


def get_win_rate_summary(
    db: Session,
    filters: SalesPerformanceFilters,
):
    """
    Calculate win rate using opportunities closed
    within the requested reporting period.
    """

    scope = build_opportunity_scope(
        filters=filters,
        period_column=OpportunityModel.closed_at,
        stages=CLOSED_STAGES,
        require_closed=True,
    )

    won, lost, total_closed, win_rate = (
        _build_win_rate_aggregate(scope)
    )

    statement = (
        select(
            won.label("closed_won"),
            lost.label("closed_lost"),
            total_closed.label("total_closed"),
            win_rate.label("win_rate_pct"),
        )
        .select_from(scope)
    )

    result = db.execute(statement).mappings().one()

    return dict(result)



def get_win_rate_by_region(
    db: Session,
    filters: SalesPerformanceFilters,
):
    """
    Calculate win rate for each sales region.
    """

    scope = build_opportunity_scope(
        filters=filters,
        period_column=OpportunityModel.closed_at,
        stages=CLOSED_STAGES,
        require_closed=True,
    )

    won, lost, total_closed, win_rate = (
        _build_win_rate_aggregate(scope)
    )

    region_name = func.coalesce(
        scope.c.region,
        "Unassigned",
    )

    statement = (
        select(
            region_name.label("region"),
            won.label("closed_won"),
            lost.label("closed_lost"),
            total_closed.label("total_closed"),
            win_rate.label("win_rate_pct"),
        )
        .group_by(region_name)
        .order_by(win_rate.desc())
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]



def get_win_rate_by_owner(
    db: Session,
    filters: SalesPerformanceFilters,
):
    """
    Calculate win rate for each sales representative.
    """

    scope = build_opportunity_scope(
        filters=filters,
        period_column=OpportunityModel.closed_at,
        stages=CLOSED_STAGES,
        require_closed=True,
    )

    won, lost, total_closed, win_rate = (
        _build_win_rate_aggregate(scope)
    )

    statement = (
        select(
            scope.c.owner_id,
            scope.c.owner_name,
            scope.c.region,

            won.label("closed_won"),
            lost.label("closed_lost"),
            total_closed.label("total_closed"),
            win_rate.label("win_rate_pct"),
        )
        .group_by(
            scope.c.owner_id,
            scope.c.owner_name,
            scope.c.region,
        )
        .order_by(win_rate.desc())
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def build_booked_deal_scope(
    filters: SalesPerformanceFilters,
):
    """
    Build a common dataset of valid closed-won bookings.

    Period filtering uses bookings.booked_at.
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
            UserModel.user_id == OpportunityModel.owner_id,
        )
    )

    conditions = [
        OpportunityModel.stage == "closed_won"
    ]

    if filters.start_at is not None:
        conditions.append(
            BookingModel.booked_at >= filters.start_at
        )

    if filters.end_at is not None:
        conditions.append(
            BookingModel.booked_at < filters.end_at
        )

    if filters.region is not None:
        conditions.append(
            UserModel.region == filters.region
        )

    if filters.owner_id is not None:
        conditions.append(
            OpportunityModel.owner_id == filters.owner_id
        )

    product_condition = build_product_exists_condition(
        filters.product_ids
    )

    if product_condition is not None:
        conditions.append(product_condition)

    return statement.where(*conditions).subquery(
        "booked_deal_scope"
    )


def get_average_deal_size(
    db: Session,
    filters: SalesPerformanceFilters,
):
    """
    Calculate total booking value, booking count
    and average deal size separately by currency.
    """

    scope = build_booked_deal_scope(filters)

    zero_amount = literal(
        Decimal("0.00"),
        type_=Numeric(14, 2),
    )

    average_value = cast(
        func.avg(scope.c.contract_value),
        Numeric(14, 2),
    )

    statement = (
        select(
            scope.c.currency_code,

            func.count(
                scope.c.booking_id
            ).label("booking_count"),

            func.coalesce(
                func.sum(scope.c.contract_value),
                zero_amount,
            ).label("total_booking_value"),

            func.coalesce(
                average_value,
                zero_amount,
            ).label("average_deal_size"),
        )
        .group_by(scope.c.currency_code)
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def get_average_deal_size_by_region(
    db: Session,
    filters: SalesPerformanceFilters,
):
    """
    Calculate average booking size for each region
    and currency.
    """

    scope = build_booked_deal_scope(filters)

    region_name = func.coalesce(
        scope.c.region,
        "Unassigned",
    )

    statement = (
        select(
            region_name.label("region"),
            scope.c.currency_code,

            func.count(
                scope.c.booking_id
            ).label("booking_count"),

            func.sum(
                scope.c.contract_value
            ).label("total_booking_value"),

            cast(
                func.avg(scope.c.contract_value),
                Numeric(14, 2),
            ).label("average_deal_size"),
        )
        .group_by(
            region_name,
            scope.c.currency_code,
        )
        .order_by(
            func.avg(scope.c.contract_value).desc()
        )
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def get_average_deal_size_by_owner(
    db: Session,
    filters: SalesPerformanceFilters,
):
    """
    Calculate average signed contract value
    for each sales representative.
    """

    scope = build_booked_deal_scope(filters)

    statement = (
        select(
            scope.c.owner_id,
            scope.c.owner_name,
            scope.c.region,
            scope.c.currency_code,

            func.count(
                scope.c.booking_id
            ).label("booking_count"),

            func.sum(
                scope.c.contract_value
            ).label("total_booking_value"),

            cast(
                func.avg(scope.c.contract_value),
                Numeric(14, 2),
            ).label("average_deal_size"),
        )
        .group_by(
            scope.c.owner_id,
            scope.c.owner_name,
            scope.c.region,
            scope.c.currency_code,
        )
        .order_by(
            func.avg(scope.c.contract_value).desc()
        )
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def build_sales_cycle_scope(
    filters: SalesPerformanceFilters,
):
    """
    Create a dataset of closed-won opportunities
    with elapsed sales cycle duration.
    """

    opportunity_scope = build_opportunity_scope(
        filters=filters,
        period_column=OpportunityModel.closed_at,
        stages=("closed_won",),
        require_closed=True,
    )

    seconds_per_day = literal(Decimal("86400"))

    cycle_days = cast(
        extract(
            "epoch",
            opportunity_scope.c.closed_at
            - opportunity_scope.c.created_at,
        ) / seconds_per_day,
        Numeric(12, 2),
    )

    statement = select(
        opportunity_scope.c.opportunity_id,
        opportunity_scope.c.owner_id,
        opportunity_scope.c.owner_name,
        opportunity_scope.c.region,

        opportunity_scope.c.created_at,
        opportunity_scope.c.closed_at,

        cycle_days.label("sales_cycle_days"),
    )

    return statement.subquery("sales_cycle_scope")


def get_sales_cycle_summary(
    db: Session,
    filters: SalesPerformanceFilters,
):
    """
    Calculate average, minimum and maximum sales cycle
    for closed-won opportunities.
    """

    scope = build_sales_cycle_scope(filters)

    statement = select(
        func.count(
            scope.c.opportunity_id
        ).label("won_opportunity_count"),

        cast(
            func.avg(scope.c.sales_cycle_days),
            Numeric(12, 2),
        ).label("average_sales_cycle_days"),

        func.min(
            scope.c.sales_cycle_days
        ).label("minimum_sales_cycle_days"),

        func.max(
            scope.c.sales_cycle_days
        ).label("maximum_sales_cycle_days"),
    )

    result = db.execute(statement).mappings().one()

    return dict(result)


def get_sales_cycle_by_region(
    db: Session,
    filters: SalesPerformanceFilters,
):
    """
    Compare average sales cycle across regions.
    """

    scope = build_sales_cycle_scope(filters)

    region_name = func.coalesce(
        scope.c.region,
        "Unassigned",
    )

    statement = (
        select(
            region_name.label("region"),

            func.count(
                scope.c.opportunity_id
            ).label("won_opportunity_count"),

            cast(
                func.avg(scope.c.sales_cycle_days),
                Numeric(12, 2),
            ).label("average_sales_cycle_days"),

            func.min(
                scope.c.sales_cycle_days
            ).label("minimum_sales_cycle_days"),

            func.max(
                scope.c.sales_cycle_days
            ).label("maximum_sales_cycle_days"),
        )
        .group_by(region_name)
        .order_by(
            func.avg(scope.c.sales_cycle_days)
        )
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def get_sales_cycle_by_owner(
    db: Session,
    filters: SalesPerformanceFilters,
):
    """
    Compare average sales cycle by sales representative.
    """

    scope = build_sales_cycle_scope(filters)

    statement = (
        select(
            scope.c.owner_id,
            scope.c.owner_name,
            scope.c.region,

            func.count(
                scope.c.opportunity_id
            ).label("won_opportunity_count"),

            cast(
                func.avg(scope.c.sales_cycle_days),
                Numeric(12, 2),
            ).label("average_sales_cycle_days"),
        )
        .group_by(
            scope.c.owner_id,
            scope.c.owner_name,
            scope.c.region,
        )
        .order_by(
            func.avg(scope.c.sales_cycle_days)
        )
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def get_invalid_sales_cycle_records(
    db: Session,
    filters: SalesPerformanceFilters,
):
    """
    Find won opportunities where the closing timestamp
    precedes the creation timestamp.
    """

    scope = build_opportunity_scope(
        filters=filters,
        period_column=OpportunityModel.closed_at,
        stages=("closed_won",),
        require_closed=True,
    )

    statement = (
        select(
            scope.c.opportunity_id,
            scope.c.owner_name,
            scope.c.created_at,
            scope.c.closed_at,
        )
        .where(
            scope.c.closed_at < scope.c.created_at
        )
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]
