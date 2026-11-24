
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import (
    select,
    func,
    case,
    and_,
    literal,
    Numeric,
)

from sqlalchemy.orm import Session

from app.models import (
    UserModel,
    OpportunityModel,
    BookingModel,
    SalesTargetModel,
)


BUSINESS_TIMEZONE = ZoneInfo("Asia/Kolkata")


@dataclass(frozen=True)
class QuotaFilters:

    period_start: date
    period_end: date

    region: str | None = None
    owner_id: int | None = None

    def __post_init__(self):

        if self.period_start > self.period_end:
            raise ValueError(
                "period_start cannot be after period_end"
            )

        if self.owner_id is not None and self.owner_id <= 0:
            raise ValueError(
                "owner_id must be positive"
            )


def get_booking_period_boundaries(filters: QuotaFilters):

    start_at = datetime.combine(
        filters.period_start,
        time.min,
        tzinfo=BUSINESS_TIMEZONE,
    )

    end_at = datetime.combine(
        filters.period_end + timedelta(days=1),
        time.min,
        tzinfo=BUSINESS_TIMEZONE,
    )

    return start_at, end_at


def build_actual_bookings_subquery(filters: QuotaFilters):
    """
    Aggregate valid closed-won bookings by
    opportunity owner and currency.

    Returns one row per salesperson and currency.
    """

    start_at, end_at = get_booking_period_boundaries(filters)

    statement = (
        select(
            OpportunityModel.owner_id.label("owner_id"),

            BookingModel.currency_code.label("currency_code"),

            func.count(
                BookingModel.booking_id
            ).label("booking_count"),

            func.sum(
                BookingModel.contract_value
            ).label("actual_bookings"),
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
        .where(
            OpportunityModel.stage == "closed_won",

            BookingModel.booked_at >= start_at,

            BookingModel.booked_at < end_at,
        )
        .group_by(
            OpportunityModel.owner_id,
            BookingModel.currency_code,
        )
    )

    if filters.region is not None:
        statement = statement.where(
            UserModel.region == filters.region
        )

    if filters.owner_id is not None:
        statement = statement.where(
            OpportunityModel.owner_id == filters.owner_id
        )

    return statement.subquery("actual_bookings")


def build_salesperson_quota_query(
    filters: QuotaFilters,
):
    """
    Match exact target periods with actual booking totals.

    Representatives without a matching target are
    intentionally excluded from quota attainment.
    """

    actuals = build_actual_bookings_subquery(filters)

    zero_amount = literal(
        Decimal("0.00"),
        type_=Numeric(14, 2),
    )

    actual_bookings = func.coalesce(
        actuals.c.actual_bookings,
        zero_amount,
    )

    booking_count = func.coalesce(
        actuals.c.booking_count,
        0,
    )

    target_gap = (
        SalesTargetModel.target_amount - actual_bookings
    )

    attainment = (
        actual_bookings
        * Decimal("100.00")
        / func.nullif(
            SalesTargetModel.target_amount,
            0,
        )
    )

    remaining_to_target = case(
        (
            target_gap > 0,
            target_gap,
        ),
        else_=zero_amount,
    )

    over_target_amount = case(
        (
            target_gap < 0,
            -target_gap,
        ),
        else_=zero_amount,
    )

    statement = (
        select(
            UserModel.user_id,
            UserModel.full_name.label("owner_name"),
            UserModel.region,

            SalesTargetModel.period_start,
            SalesTargetModel.period_end,

            SalesTargetModel.currency_code,
            SalesTargetModel.target_amount,

            booking_count.label("booking_count"),

            actual_bookings.label("actual_bookings"),

            attainment.label("quota_attainment_pct"),

            target_gap.label("target_gap"),

            remaining_to_target.label(
                "remaining_to_target"
            ),

            over_target_amount.label(
                "over_target_amount"
            ),

            (
                actual_bookings
                / func.nullif(booking_count, 0)
            ).label("average_booking_size"),
        )
        .select_from(SalesTargetModel)
        .join(
            UserModel,
            UserModel.user_id == SalesTargetModel.user_id,
        )
        .outerjoin(
            actuals,
            and_(
                actuals.c.owner_id == UserModel.user_id,

                actuals.c.currency_code
                == SalesTargetModel.currency_code,
            ),
        )
        .where(
            SalesTargetModel.period_start
            == filters.period_start,

            SalesTargetModel.period_end
            == filters.period_end,

            UserModel.role == "sales_rep",
        )
    )

    if filters.region is not None:
        statement = statement.where(
            UserModel.region == filters.region
        )

    if filters.owner_id is not None:
        statement = statement.where(
            UserModel.user_id == filters.owner_id
        )

    return statement.subquery("salesperson_quota_performance")


def get_salesperson_performance(
    db: Session,
    filters: QuotaFilters,
):
    """
    Return salesperson performance ranked by
    quota attainment, separately for each currency.
    """

    base = build_salesperson_quota_query(filters)

    quota_rank = func.rank().over(
        partition_by=base.c.currency_code,
        order_by=base.c.quota_attainment_pct.desc(),
    )

    statement = (
        select(
            base,
            quota_rank.label("quota_rank"),
        )
        .order_by(
            base.c.currency_code,
            base.c.quota_attainment_pct.desc(),
            base.c.actual_bookings.desc(),
        )
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def get_quota_attainment_by_region(
    db: Session,
    filters: QuotaFilters,
):
    """
    Aggregate salesperson targets and bookings by region.
    """

    base = build_salesperson_quota_query(filters)

    zero_amount = literal(
        Decimal("0.00"),
        type_=Numeric(14, 2),
    )

    total_target = func.sum(base.c.target_amount)
    total_actual = func.sum(base.c.actual_bookings)

    attainment = (
        total_actual
        * Decimal("100.00")
        / func.nullif(total_target, 0)
    )

    statement = (
        select(
            func.coalesce(
                base.c.region,
                "Unassigned",
            ).label("region"),

            base.c.currency_code,

            func.count(
                base.c.user_id.distinct()
            ).label("salesperson_count"),

            total_target.label("total_target"),

            total_actual.label("actual_bookings"),

            func.coalesce(
                attainment,
                zero_amount,
            ).label("quota_attainment_pct"),

            func.sum(
                base.c.remaining_to_target
            ).label("remaining_to_target"),

            func.sum(
                base.c.over_target_amount
            ).label("over_target_amount"),
        )
        .group_by(
            base.c.region,
            base.c.currency_code,
        )
        .order_by(attainment.desc())
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def get_team_quota_summary(
    db: Session,
    filters: QuotaFilters,
):
    """
    Calculate overall team quota performance by currency.
    """

    base = build_salesperson_quota_query(filters)

    zero_amount = literal(
        Decimal("0.00"),
        type_=Numeric(14, 2),
    )

    total_target = func.sum(base.c.target_amount)
    total_actual = func.sum(base.c.actual_bookings)

    attainment = (
        total_actual
        * Decimal("100.00")
        / func.nullif(total_target, 0)
    )

    statement = (
        select(
            base.c.currency_code,

            func.count(
                base.c.user_id.distinct()
            ).label("salesperson_count"),

            total_target.label("total_target"),

            total_actual.label("actual_bookings"),

            func.coalesce(
                attainment,
                zero_amount,
            ).label("quota_attainment_pct"),

            func.sum(
                base.c.remaining_to_target
            ).label("remaining_to_target"),

            func.sum(
                base.c.over_target_amount
            ).label("over_target_amount"),
        )
        .group_by(base.c.currency_code)
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def get_sales_reps_without_target(
    db: Session,
    filters: QuotaFilters,
):
    """
    Find active sales representatives without
    a target for the selected reporting period.
    """

    matching_target = (
        select(1)
        .where(
            SalesTargetModel.user_id == UserModel.user_id,

            SalesTargetModel.period_start == filters.period_start,

            SalesTargetModel.period_end == filters.period_end,
        )
        .exists()
    )

    statement = (
        select(
            UserModel.user_id,
            UserModel.full_name.label("owner_name"),
            UserModel.region,
        )
        .where(
            UserModel.role == "sales_rep",
            UserModel.is_active.is_(True),
            ~matching_target,
        )
    )

    if filters.region is not None:
        statement = statement.where(
            UserModel.region == filters.region
        )

    if filters.owner_id is not None:
        statement = statement.where(
            UserModel.user_id == filters.owner_id
        )

    return [
        dict(row)
        for row in db.execute(statement).mappings().all()
    ]
