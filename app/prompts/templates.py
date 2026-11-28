import json

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


def json_serializer(value: Any):

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")

    raise TypeError(
        f"Object of type {type(value).__name__} "
        "is not JSON serializable"
    )


def build_classifier_input(
    user_question: str,
) -> str:

    if not user_question.strip():
        raise ValueError(
            "User question cannot be empty."
        )

    payload = {
        "user_question": user_question,
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )


def build_evidence_answer_input(
    user_question: str,
    validated_request: dict,
    tool_name: str,
    filters: dict,
    evidence: Any,
) -> str:

    if not user_question.strip():
        raise ValueError(
            "User question cannot be empty."
        )

    if not tool_name.strip():
        raise ValueError(
            "Analytics tool name cannot be empty."
        )

    payload = {
        "user_question": user_question,

        "validated_request": validated_request,

        "analytics_evidence": {
            "tool_name": tool_name,
            "filters": filters,
            "result": evidence,
        },
    }

    return json.dumps(
        payload,
        default=json_serializer,
        ensure_ascii=False,
        indent=2,
    )