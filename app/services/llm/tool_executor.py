import json

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session

from app.services import pipeline_analytics_service
from app.services.revops_query_service import OpportunityFilters


class PipelineOverviewArguments(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    region: str | None

    @field_validator("region")
    @classmethod
    def validate_region(cls, value):

        if value is not None:
            value = value.strip()

            if not value:
                raise ValueError(
                    "Region cannot be blank. Use null instead."
                )

        return value


def make_json_safe(value):

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")

    raise TypeError(
        f"Unsupported result type: {type(value).__name__}"
    )


def execute_revops_tool(
    db: Session,
    tool_name: str,
    arguments: str | dict,
) -> dict:

    # Parse JSON arguments if necessary.
    if isinstance(arguments, str):
        arguments = json.loads(arguments)

    if not isinstance(arguments, dict):
        raise ValueError(
            "Tool arguments must be a JSON object."
        )

    # Only execute explicitly registered tools.
    if tool_name == "get_pipeline_overview":

        validated_args = PipelineOverviewArguments.model_validate(
            arguments
        )

        # Construct the actual analytics filter object.
        filters = OpportunityFilters(
            region=validated_args.region
        )

        # Call the existing revenue analytics service.
        result = pipeline_analytics_service.get_pipeline_overview(
            db=db,
            filters=filters,
        )

        return result

    raise ValueError(
        f"Unknown tool: {tool_name}"
    )