import pytest

from datetime import date

from pydantic import ValidationError

from app.schemas.llm import RevOpsQuestion


def valid_question_data():

    return {
        "intent": "opportunity_pipeline",
        "region": "North",
        "salesperson": None,
        "product": None,
        "account": None,
        "period_start": date(2026, 1, 1),
        "period_end": date(2026, 3, 31),
        "period_expression": None,
        "group_by": "stage",
        "needs_clarification": False,
        "clarification_question": None,
    }


def test_valid_revops_question():

    result = RevOpsQuestion.model_validate(
        valid_question_data()
    )

    assert result.intent == "opportunity_pipeline"
    assert result.region == "North"


def test_invalid_intent_rejected():

    data = valid_question_data()

    data["intent"] = "generate_sql"

    with pytest.raises(ValidationError):

        RevOpsQuestion.model_validate(data)


def test_invalid_date_range_rejected():

    data = valid_question_data()

    data["period_start"] = date(2026, 4, 1)
    data["period_end"] = date(2026, 1, 1)

    with pytest.raises(ValidationError):

        RevOpsQuestion.model_validate(data)


def test_clarification_requires_question():

    data = valid_question_data()

    data["needs_clarification"] = True

    with pytest.raises(ValidationError):

        RevOpsQuestion.model_validate(data)


def test_unexpected_field_rejected():

    data = valid_question_data()

    data["sql_query"] = "SELECT * FROM opportunities"

    with pytest.raises(ValidationError):

        RevOpsQuestion.model_validate(data)