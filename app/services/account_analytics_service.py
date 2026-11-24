
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import (
    select,
    func,
    case,
    literal,
    Numeric,
    union,
    and_,
)

from sqlalchemy.orm import Session

from app.models import (
    AccountModel,
    UserModel,
    OpportunityModel,
    OpportunityLineItemModel,
    BookingModel,
    SalesActivityModel,
    ContactModel
)


OPEN_STAGES = (
    "qualification",
    "discovery",
    "proposal",
    "negotiation",
)


@dataclass(frozen=True)
class AccountSummaryFilters:

    region: str | None = None
    owner_id: int | None = None
    account_status: str | None = None

    def __post_init__(self):

        if self.owner_id is not None and self.owner_id <= 0:
            raise ValueError("owner_id must be positive")

        allowed_statuses = {
            "prospect",
            "customer",
            "churned",
            "inactive",
        }

        if (
            self.account_status is not None
            and self.account_status not in allowed_statuses
        ):
            raise ValueError("Invalid account status")


def build_opportunity_line_value_subquery():

    statement = (
        select(
            OpportunityLineItemModel.opportunity_id,

            func.sum(
                OpportunityLineItemModel.quantity
                * OpportunityLineItemModel.agreed_unit_price
            ).label("line_value"),
        )
        .group_by(
            OpportunityLineItemModel.opportunity_id
        )
    )

    return statement.subquery("account_opportunity_values")


def build_account_opportunity_metrics():

    line_values = build_opportunity_line_value_subquery()

    zero_amount = literal(
        Decimal("0.00"),
        type_=Numeric(14, 2),
    )

    open_condition = OpportunityModel.stage.in_(OPEN_STAGES)

    opportunity_value = func.coalesce(
        line_values.c.line_value,
        zero_amount,
    )

    statement = (
        select(
            OpportunityModel.account_id,
            OpportunityModel.currency_code,

            func.sum(
                case(
                    (open_condition, 1),
                    else_=0,
                )
            ).label("open_opportunity_count"),

            func.sum(
                case(
                    (open_condition, opportunity_value),
                    else_=zero_amount,
                )
            ).label("open_pipeline"),

            func.sum(
                case(
                    (
                        open_condition,
                        (
                            opportunity_value
                            * OpportunityModel.probability_pct
                            / 100
                        ),
                    ),
                    else_=zero_amount,
                )
            ).label("weighted_pipeline"),

            func.sum(
                case(
                    (OpportunityModel.stage == "closed_won", 1),
                    else_=0,
                )
            ).label("closed_won_count"),

            func.sum(
                case(
                    (OpportunityModel.stage == "closed_lost", 1),
                    else_=0,
                )
            ).label("closed_lost_count"),
        )
        .select_from(OpportunityModel)
        .outerjoin(
            line_values,
            line_values.c.opportunity_id
            == OpportunityModel.opportunity_id,
        )
        .group_by(
            OpportunityModel.account_id,
            OpportunityModel.currency_code,
        )
    )

    return statement.subquery("account_opportunity_metrics")


def build_account_activity_metrics():

    statement = (
        select(
            SalesActivityModel.account_id,

            func.count(
                SalesActivityModel.activity_id
            ).label("completed_activity_count"),

            func.max(
                SalesActivityModel.completed_at
            ).label("last_completed_activity_at"),
        )
        .where(
            SalesActivityModel.activity_status == "completed"
        )
        .group_by(
            SalesActivityModel.account_id
        )
    )

    return statement.subquery("account_activity_metrics")


def build_account_booking_metrics():

    statement = (
        select(
            OpportunityModel.account_id,
            BookingModel.currency_code,

            func.count(
                BookingModel.booking_id
            ).label("booking_count"),

            func.sum(
                BookingModel.contract_value
            ).label("total_bookings"),
        )
        .select_from(BookingModel)
        .join(
            OpportunityModel,
            OpportunityModel.opportunity_id
            == BookingModel.opportunity_id,
        )
        .where(
            OpportunityModel.stage == "closed_won"
        )
        .group_by(
            OpportunityModel.account_id,
            BookingModel.currency_code,
        )
    )

    return statement.subquery("account_booking_metrics")


def build_account_contact_metrics():
    """
    Calculate the number of contacts associated
    with each account.
    """

    statement = (
        select(
            ContactModel.account_id,

            func.count(
                ContactModel.contact_id
            ).label("contact_count"),
        )
        .group_by(
            ContactModel.account_id
        )
    )

    return statement.subquery("account_contact_metrics")


def get_account_summaries(
    db: Session,
    filters: AccountSummaryFilters | None = None,
):
    """
    Return account-level pipeline, bookings and
    completed sales activity information.

    One row is returned per account and currency.
    Accounts without financial activity return
    a row with a NULL currency.
    """

    filters = filters or AccountSummaryFilters()
    opportunity_metrics = build_account_opportunity_metrics()
    booking_metrics = build_account_booking_metrics()
    activity_metrics = build_account_activity_metrics()
    contact_metrics = build_account_contact_metrics()

    # Currency combinations found in either opportunities
    # or bookings. UNION removes duplicates.
    currency_keys = union(
        select(
            opportunity_metrics.c.account_id,
            opportunity_metrics.c.currency_code,
        ),
        select(
            booking_metrics.c.account_id,
            booking_metrics.c.currency_code,
        ),
    ).subquery("account_currency_keys")

    zero_count = literal(0)

    zero_amount = literal(
        Decimal("0.00"),
        type_=Numeric(14, 2),
    )

    statement = (
        select(
            AccountModel.account_id,
            AccountModel.company_name,
            AccountModel.industry,
            AccountModel.country,
            AccountModel.account_status,

            UserModel.user_id.label("owner_id"),
            UserModel.full_name.label("owner_name"),
            UserModel.region,

            currency_keys.c.currency_code,

            func.coalesce(
                opportunity_metrics.c.open_opportunity_count,
                zero_count,
            ).label("open_opportunity_count"),

            func.coalesce(
                opportunity_metrics.c.open_pipeline,
                zero_amount,
            ).label("open_pipeline"),

            func.coalesce(
                opportunity_metrics.c.weighted_pipeline,
                zero_amount,
            ).label("weighted_pipeline"),

            func.coalesce(
                opportunity_metrics.c.closed_won_count,
                zero_count,
            ).label("closed_won_count"),

            func.coalesce(
                opportunity_metrics.c.closed_lost_count,
                zero_count,
            ).label("closed_lost_count"),

            func.coalesce(
                booking_metrics.c.booking_count,
                zero_count,
            ).label("booking_count"),

            func.coalesce(
                booking_metrics.c.total_bookings,
                zero_amount,
            ).label("total_bookings"),

            func.coalesce(
                activity_metrics.c.completed_activity_count,
                zero_count,
            ).label("completed_activity_count"),

            func.coalesce(
                contact_metrics.c.contact_count,
                0,
            ).label("contact_count"),

            activity_metrics.c.last_completed_activity_at,
        )
        .select_from(AccountModel)
        .outerjoin(
            UserModel,
            UserModel.user_id == AccountModel.owner_id,
        )
        .outerjoin(
            currency_keys,
            currency_keys.c.account_id
            == AccountModel.account_id,
        )
        .outerjoin(
            opportunity_metrics,
            and_(
                opportunity_metrics.c.account_id
                == AccountModel.account_id,

                opportunity_metrics.c.currency_code
                == currency_keys.c.currency_code,
            ),
        )
        .outerjoin(
            booking_metrics,
            and_(
                booking_metrics.c.account_id
                == AccountModel.account_id,

                booking_metrics.c.currency_code
                == currency_keys.c.currency_code,
            ),
        )
        .outerjoin(
            activity_metrics,
            activity_metrics.c.account_id
            == AccountModel.account_id,
        )
        .outerjoin(
            contact_metrics,
            contact_metrics.c.account_id
            == AccountModel.account_id,
        )
    )

    conditions = []

    if filters.region is not None:
        conditions.append(
            UserModel.region == filters.region
        )

    if filters.owner_id is not None:
        conditions.append(
            AccountModel.owner_id == filters.owner_id
        )

    if filters.account_status is not None:
        conditions.append(
            AccountModel.account_status
            == filters.account_status
        )

    if conditions:
        statement = statement.where(*conditions)

    statement = statement.order_by(
        AccountModel.company_name,
        currency_keys.c.currency_code,
    )

    results = db.execute(
        statement
    ).mappings().all()

    return [dict(row) for row in results]
