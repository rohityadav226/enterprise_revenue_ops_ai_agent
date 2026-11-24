
from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import (
    select,
    func,
    case,
    cast,
    extract,
    literal,
    Integer,
    Numeric,
    DateTime,
)

from sqlalchemy.orm import Session

from app.services.revops_query_service import (
    OpportunityFilters,
    build_opportunity_detail_query,
    get_open_pipeline_summary,
)


BUSINESS_TIMEZONE = ZoneInfo("Asia/Kolkata")


def get_filtered_open_opportunities(filters: OpportunityFilters):
    """
    Reuse the Day 16 query builder.

    Only open opportunities are included.
    """

    return (
        build_opportunity_detail_query(
            filters=filters,
            open_only=True,
        )
        .order_by(None)
        .subquery("filtered_open_opportunities")
    )


def get_as_of_timestamp(as_of: datetime | None = None):
    """
    Return an aware timestamp for ageing calculations.
    """

    if as_of is None:
        return datetime.now(timezone.utc)

    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")

    return as_of



def get_pipeline_overview(
    db: Session,
    filters: OpportunityFilters,
):
    """
    Calculate all pipeline overview metrics
    with a single aggregate query.
    """

    base = get_filtered_open_opportunities(filters)

    zero_amount = literal(
        Decimal("0.00"),
        type_=Numeric(14, 2),
    )

    total_count = func.count(
        base.c.opportunity_id
    )

    open_pipeline = func.coalesce(
        func.sum(base.c.opportunity_value),
        zero_amount,
    )

    weighted_pipeline = func.coalesce(
        func.sum(base.c.weighted_value),
        zero_amount,
    )

    average_value = func.coalesce(
        func.avg(base.c.opportunity_value),
        zero_amount,
    )

    weighted_probability = cast(
        weighted_pipeline
        * Decimal("100.00")
        / func.nullif(open_pipeline, 0),
        Numeric(7, 2),
    )

    statement = (
        select(
            total_count.label("open_opportunity_count"),

            open_pipeline.label("open_pipeline"),

            weighted_pipeline.label("weighted_pipeline"),

            average_value.label(
                "average_opportunity_value"
            ),

            func.coalesce(
                weighted_probability,
                literal(Decimal("0.00")),
            ).label("weighted_probability_pct"),
        )
    )

    result = db.execute(
        statement
    ).mappings().one()

    return dict(result)


def get_pipeline_stage_distribution(
    db: Session,
    filters: OpportunityFilters,
):
    """
    Distribute open opportunities by sales stage.
    """

    base = get_filtered_open_opportunities(filters)

    zero_amount = literal(
        Decimal("0.00"),
        type_=Numeric(14, 2),
    )

    total_count = (
        select(func.count(base.c.opportunity_id))
        .select_from(base)
        .scalar_subquery()
    )

    total_pipeline = (
        select(
            func.coalesce(
                func.sum(base.c.opportunity_value),
                zero_amount,
            )
        )
        .select_from(base)
        .scalar_subquery()
    )

    stage_count = func.count(
        base.c.opportunity_id
    )

    stage_pipeline = func.coalesce(
        func.sum(base.c.opportunity_value),
        zero_amount,
    )

    stage_weighted_pipeline = func.coalesce(
        func.sum(base.c.weighted_value),
        zero_amount,
    )

    count_percentage = func.coalesce(
        cast(
            stage_count
            * literal(Decimal("100.00"))
            / func.nullif(total_count, 0),
            Numeric(5, 2),
        ),
        literal(Decimal("0.00")),
    )

    pipeline_percentage = func.coalesce(
        cast(
            stage_pipeline
            * literal(Decimal("100.00"))
            / func.nullif(total_pipeline, 0),
            Numeric(5, 2),
        ),
        literal(Decimal("0.00")),
    )

    stage_sort = case(
        (base.c.stage == "qualification", 1),
        (base.c.stage == "discovery", 2),
        (base.c.stage == "proposal", 3),
        (base.c.stage == "negotiation", 4),
        else_=5,
    )

    statement = (
        select(
            base.c.stage,

            stage_count.label("opportunity_count"),

            stage_pipeline.label("pipeline_value"),

            stage_weighted_pipeline.label(
                "weighted_pipeline"
            ),

            func.avg(
                base.c.probability_pct
            ).label("average_probability_pct"),

            count_percentage.label(
                "opportunity_count_pct"
            ),

            pipeline_percentage.label(
                "pipeline_value_pct"
            ),
        )
        .group_by(base.c.stage)
        .order_by(stage_sort)
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]



def build_opportunity_ageing_query(
    filters: OpportunityFilters,
    as_of: datetime | None = None,
):
    """
    Calculate the age of every filtered open opportunity.

    Age is measured from created_at to the as_of timestamp.
    """

    as_of = get_as_of_timestamp(as_of)

    base = get_filtered_open_opportunities(filters)

    as_of_expression = literal(
        as_of,
        type_=DateTime(timezone=True),
    )

    elapsed_seconds = extract(
        "epoch",
        as_of_expression - base.c.created_at,
    )

    age_days = cast(
        func.floor(elapsed_seconds / 86400),
        Integer,
    )

    ageing_bucket = case(
        (age_days < 0, "Future-dated"),
        (age_days <= 30, "0-30 days"),
        (age_days <= 60, "31-60 days"),
        (age_days <= 90, "61-90 days"),
        else_="91+ days",
    )

    business_today = (
        as_of.astimezone(BUSINESS_TIMEZONE).date()
    )

    is_overdue = (
        base.c.expected_close_date < business_today
    )

    statement = (
        select(
            base.c.opportunity_id,
            base.c.opportunity_name,
            base.c.account_name,
            base.c.stage,
            base.c.probability_pct,
            base.c.expected_close_date,

            base.c.owner_id,
            base.c.owner_name,
            base.c.region,

            base.c.created_at,

            base.c.opportunity_value,
            base.c.weighted_value,

            age_days.label("age_days"),

            ageing_bucket.label("ageing_bucket"),

            is_overdue.label("is_overdue"),
        )
        .order_by(
            age_days.desc(),
            base.c.weighted_value.desc(),
        )
    )

    return statement


def get_opportunity_ageing(
    db: Session,
    filters: OpportunityFilters,
    as_of: datetime | None = None,
):
    """
    Return open opportunities sorted from oldest to newest.
    """

    statement = build_opportunity_ageing_query(
        filters=filters,
        as_of=as_of,
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def get_opportunity_ageing_summary(
    db: Session,
    filters: OpportunityFilters,
    as_of: datetime | None = None,
):
    """
    Aggregate opportunity ageing into predefined buckets.
    """

    ageing_query = (
        build_opportunity_ageing_query(
            filters=filters,
            as_of=as_of,
        )
        .order_by(None)
        .subquery("opportunity_ageing")
    )

    zero_amount = literal(
        Decimal("0.00"),
        type_=Numeric(14, 2),
    )

    overdue_count = func.sum(
        case(
            (ageing_query.c.is_overdue.is_(True), 1),
            else_=0,
        )
    )

    overdue_pipeline = func.sum(
        case(
            (
                ageing_query.c.is_overdue.is_(True),
                ageing_query.c.opportunity_value,
            ),
            else_=zero_amount,
        )
    )

    bucket_order = case(
        (ageing_query.c.ageing_bucket == "Future-dated", 0),
        (ageing_query.c.ageing_bucket == "0-30 days", 1),
        (ageing_query.c.ageing_bucket == "31-60 days", 2),
        (ageing_query.c.ageing_bucket == "61-90 days", 3),
        else_=4,
    )

    statement = (
        select(
            ageing_query.c.ageing_bucket,

            func.count(
                ageing_query.c.opportunity_id
            ).label("opportunity_count"),

            func.sum(
                ageing_query.c.opportunity_value
            ).label("pipeline_value"),

            func.sum(
                ageing_query.c.weighted_value
            ).label("weighted_pipeline"),

            func.avg(
                ageing_query.c.age_days
            ).label("average_age_days"),

            overdue_count.label("overdue_count"),

            func.coalesce(
                overdue_pipeline,
                zero_amount,
            ).label("overdue_pipeline"),
        )
        .group_by(ageing_query.c.ageing_bucket)
        .order_by(bucket_order)
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def get_at_risk_opportunities(
    db: Session,
    filters: OpportunityFilters,
    min_age_days: int = 60,
    as_of: datetime | None = None,
):
    """
    Return ageing or overdue open opportunities.

    Risk criteria:
    1. Age is greater than or equal to min_age_days.
    2. Expected close date is before the reporting date.
    """

    if min_age_days < 0:
        raise ValueError("min_age_days cannot be negative")

    ageing_query = (
        build_opportunity_ageing_query(
            filters=filters,
            as_of=as_of,
        )
        .subquery("at_risk_opportunities")
    )

    statement = (
        select(ageing_query)
        .where(
            (ageing_query.c.age_days >= min_age_days)
            | ageing_query.c.is_overdue.is_(True)
        )
        .order_by(
            ageing_query.c.weighted_value.desc(),
            ageing_query.c.age_days.desc(),
        )
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]


def get_pipeline_overview(
    db: Session,
    filters: OpportunityFilters,
):
    """
    Reuse Day 16 pipeline calculations and
    add average value and weighted probability.
    """

    # Reuse existing Day 16 pipeline calculation
    pipeline = get_open_pipeline_summary(
        db,
        filters,
    )

    base = get_filtered_open_opportunities(filters)

    average_value = db.scalar(
        select(
            func.avg(base.c.opportunity_value)
        )
    )

    open_pipeline = (
        pipeline["open_pipeline"] or Decimal("0.00")
    )

    weighted_pipeline = (
        pipeline["weighted_pipeline"] or Decimal("0.00")
    )

    weighted_probability = (
        weighted_pipeline * Decimal("100.00")
        / open_pipeline
        if open_pipeline > 0
        else Decimal("0.00")
    )

    return {
        **pipeline,
        "average_opportunity_value": (
            average_value or Decimal("0.00")
        ),
        "weighted_probability_pct": weighted_probability,
    }
