from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from sqlalchemy import (
    select,
    func,
    literal,
    Numeric
)
from sqlalchemy.orm import Session
from app.models import (
    UserModel,
    AccountModel,
    ProductModel,
    OpportunityModel,
    OpportunityLineItemModel
)

OPEN_STAGES = (
    "qualification",
    "discovery",
    "proposal",
    "negotiation",
)

ALL_STAGES = OPEN_STAGES + (
    "closed_won",
    "closed_lost",
)


@dataclass(frozen=True)
class OpportunityFilters:
    start_date: date | None = None
    end_date: date | None = None

    region: str | None = None
    owner_id: int | None = None

    product_ids: tuple[int, ...] = ()

    stages: tuple[str, ...] = ()

    def __post_init__(self):

        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        ):
            raise ValueError(
                "start_date cannot be after end_date"
            )

        if self.owner_id is not None and self.owner_id <= 0:
            raise ValueError("owner_id must be positive")

        if any(product_id <= 0 for product_id in self.product_ids):
            raise ValueError("product_ids must be positive")

        invalid_stages = set(self.stages) - set(ALL_STAGES)

        if invalid_stages:
            raise ValueError(
                f"Invalid opportunity stages: {invalid_stages}"
            )


def build_opportunity_value_subquery(
    filters: OpportunityFilters,
):
    """
    Calculate opportunity value from its line items.

    If product_ids are supplied, calculate only the
    monetary contribution from those selected products.
    """

    statement = select(
        OpportunityLineItemModel.opportunity_id.label(
            "opportunity_id"
        ),
        func.sum(
            OpportunityLineItemModel.quantity
            * OpportunityLineItemModel.agreed_unit_price
        ).label("opportunity_value"),
    )

    # Apply product filter at line-item level
    if filters.product_ids:

        statement = statement.where(
            OpportunityLineItemModel.product_id.in_(
                filters.product_ids
            )
        )

    statement = statement.group_by(
        OpportunityLineItemModel.opportunity_id
    )

    return statement.subquery("opportunity_values")


def build_opportunity_detail_query(
    filters: OpportunityFilters,
    open_only: bool = False,
):
    """
    Build a reusable opportunity query with optional filters.

    Period filters use expected_close_date.
    Region is taken from the opportunity owner's region.
    Product filters calculate selected product contributions.
    """

    value_subquery = build_opportunity_value_subquery(filters)

    zero_value = literal(
        Decimal("0.00"),
        type_=Numeric(14, 2),
    )

    opportunity_value = func.coalesce(
        value_subquery.c.opportunity_value,
        zero_value,
    )

    weighted_value = (
        opportunity_value
        * OpportunityModel.probability_pct
        / 100
    )

    statement = (
        select(
            OpportunityModel.opportunity_id,
            OpportunityModel.opportunity_name,

            AccountModel.company_name.label("account_name"),

            OpportunityModel.stage,
            OpportunityModel.probability_pct,
            OpportunityModel.expected_close_date,
            OpportunityModel.created_at,

            UserModel.user_id.label("owner_id"),
            UserModel.full_name.label("owner_name"),
            UserModel.region,

            opportunity_value.label("opportunity_value"),
            weighted_value.label("weighted_value"),
        )
        .join(
            AccountModel,
            AccountModel.account_id
            == OpportunityModel.account_id,
        )
        .join(
            UserModel,
            UserModel.user_id
            == OpportunityModel.owner_id,
        )
        .outerjoin(
            value_subquery,
            value_subquery.c.opportunity_id
            == OpportunityModel.opportunity_id,
        )
    )

    conditions = []

    # Period filter: expected closing date
    if filters.start_date is not None:
        conditions.append(
            OpportunityModel.expected_close_date
            >= filters.start_date
        )

    if filters.end_date is not None:
        conditions.append(
            OpportunityModel.expected_close_date
            <= filters.end_date
        )

    # Sales region filter
    if filters.region is not None:
        conditions.append(
            UserModel.region == filters.region
        )

    # Opportunity owner filter
    if filters.owner_id is not None:
        conditions.append(
            OpportunityModel.owner_id == filters.owner_id
        )

    # Opportunity stage filter
    if filters.stages:
        conditions.append(
            OpportunityModel.stage.in_(filters.stages)
        )

    # Product filter
    if filters.product_ids:
        conditions.append(
            value_subquery.c.opportunity_id.is_not(None)
        )

    # Pipeline-only filter
    if open_only:
        conditions.append(
            OpportunityModel.stage.in_(OPEN_STAGES)
        )

    if conditions:
        statement = statement.where(*conditions)

    statement = statement.order_by(
        OpportunityModel.expected_close_date
    )

    return statement


def get_opportunity_details(
    db: Session,
    filters: OpportunityFilters,
    open_only: bool = False,
):
    """
    Execute the opportunity query and return dictionaries.
    """

    statement = build_opportunity_detail_query(
        filters=filters,
        open_only=open_only,
    )

    results = db.execute(statement).mappings().all()

    return [dict(row) for row in results]


def get_open_pipeline_summary(
    db: Session,
    filters: OpportunityFilters,
):
    """
    Calculate open pipeline and weighted pipeline
    using the reusable opportunity query.
    """

    filtered_opportunities = (
        build_opportunity_detail_query(
            filters=filters,
            open_only=True,
        )
        .subquery("filtered_opportunities")
    )

    zero_value = literal(
        Decimal("0.00"),
        type_=Numeric(14, 2),
    )

    statement = select(
        func.count(
            filtered_opportunities.c.opportunity_id
        ).label("opportunity_count"),

        func.coalesce(
            func.sum(
                filtered_opportunities.c.opportunity_value
            ),
            zero_value,
        ).label("open_pipeline"),

        func.coalesce(
            func.sum(
                filtered_opportunities.c.weighted_value
            ),
            zero_value,
        ).label("weighted_pipeline"),
    )

    result = db.execute(statement).mappings().one()

    return dict(result)
