from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

class RevOpsQuestion(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    intent: Literal[
        "opportunity_pipeline",
        "bookings",
        "pipeline_health",
        "sales_performance",
        "quota_attainment",
        "account_summary",
        "unknown",
    ] = Field(
        description="The RevOps capability needed to answer the question."
    )

    region: str | None = Field(
        description="Explicitly requested sales region, otherwise null."
    )

    salesperson: str | None = Field(
        description="Explicitly named salesperson, otherwise null."
    )

    product: str | None = Field(
        description="Explicitly named product, otherwise null."
    )

    account: str | None = Field(
        description="Explicitly named customer account, otherwise null."
    )

    period_start: date | None = Field(
        description="Explicit start date in YYYY-MM-DD format, otherwise null."
    )

    period_end: date | None = Field(
        description="Explicit end date in YYYY-MM-DD format, otherwise null."
    )

    period_expression: str | None = Field(
        description="Original relative period phrase, such as last quarter, otherwise null."
    )

    group_by: Literal[
        "month",
        "region",
        "product",
        "salesperson",
        "stage",
        "none",
    ] = Field(
        description="Requested aggregation or grouping."
    )

    needs_clarification: bool = Field(
        description="Whether the question needs clarification before execution."
    )

    clarification_question: str | None = Field(
        description="A specific clarification question, otherwise null."
    )

    @model_validator(mode="after")
    def validate_period(self):

        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_start > self.period_end
        ):
            raise ValueError(
                "period_start cannot be later than period_end."
            )

        if (
            self.needs_clarification
            and not self.clarification_question
        ):
            raise ValueError(
                "A clarification question is required when clarification is needed."
            )

        return self