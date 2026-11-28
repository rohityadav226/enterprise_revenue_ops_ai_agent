import pytest

from pydantic import ValidationError

from app.services.llm import tool_executor
from app.services.llm.tool_executor import execute_revops_tool


def test_pipeline_tool_calls_existing_service(monkeypatch):

    fake_db = object()

    def fake_pipeline_overview(db, filters):

        assert db is fake_db
        assert filters.region == "North"

        return {
            "open_opportunity_count": 8,
            "open_pipeline": 5000000,
            "weighted_pipeline": 3200000,
            "average_opportunity_value": 625000,
            "weighted_probability_pct": 64,
        }

    monkeypatch.setattr(
        tool_executor.pipeline_analytics_service,
        "get_pipeline_overview",
        fake_pipeline_overview,
    )

    result = execute_revops_tool(
        db=fake_db,
        tool_name="get_pipeline_overview",
        arguments={"region": "North"},
    )

    assert result["open_opportunity_count"] == 8
    assert result["open_pipeline"] == 5000000


def test_pipeline_tool_accepts_all_regions(monkeypatch):

    def fake_pipeline_overview(db, filters):

        assert filters.region is None

        return {"open_opportunity_count": 10}

    monkeypatch.setattr(
        tool_executor.pipeline_analytics_service,
        "get_pipeline_overview",
        fake_pipeline_overview,
    )

    result = execute_revops_tool(
        db=object(),
        tool_name="get_pipeline_overview",
        arguments={"region": None},
    )

    assert result["open_opportunity_count"] == 10


def test_invalid_arguments_are_rejected():

    with pytest.raises(ValidationError):

        execute_revops_tool(
            db=None,
            tool_name="get_pipeline_overview",
            arguments={
                "region": "North",
                "unexpected": "value",
            },
        )


def test_unknown_tool_is_rejected():

    with pytest.raises(ValueError, match="Unknown tool"):

        execute_revops_tool(
            db=None,
            tool_name="execute_sql",
            arguments={},
        )