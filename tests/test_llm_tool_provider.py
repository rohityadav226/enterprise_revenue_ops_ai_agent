import json

from decimal import Decimal
from types import SimpleNamespace

import pytest
import httpx

from openai import APITimeoutError

from app.services.llm.openai_provider import (
    OpenAIProvider,
    LLMTimeoutError,
)


class FakeResponses:

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    async def create(self, **kwargs):

        self.requests.append(kwargs)

        response = self.responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response


def make_response(
    output=None,
    output_text="",
):

    usage = SimpleNamespace(
        input_tokens=10,
        output_tokens=5,
        total_tokens=15,
        input_tokens_details=SimpleNamespace(
            cached_tokens=2
        ),
    )

    return SimpleNamespace(
        output=output or [],
        output_text=output_text,
        usage=usage,
        _request_id="test-request-123",
    )


def make_provider(responses):

    provider = OpenAIProvider.__new__(OpenAIProvider)

    provider.model = "test-model"

    provider.client = SimpleNamespace(
        responses=FakeResponses(responses)
    )

    return provider


@pytest.fixture
def mock_pricing(monkeypatch):

    monkeypatch.setattr(
        "app.services.llm.openai_provider.calculate_estimated_cost",
        lambda **kwargs: Decimal("0.001"),
    )


@pytest.mark.asyncio
async def test_pipeline_tool_call_executes_and_returns_result(
    mock_pricing,
):

    function_call = SimpleNamespace(
        type="function_call",
        name="get_pipeline_overview",
        arguments='{"region": "North"}',
        call_id="call_123",
    )

    provider = make_provider([
        make_response(
            output=[function_call]
        ),
        make_response(
            output_text=(
                "North has 2 open opportunities "
                "and 7,520,000 in open pipeline."
            )
        ),
    ])

    executed_tools = []

    def fake_executor(name, arguments):

        executed_tools.append({
            "name": name,
            "arguments": arguments,
        })

        return {
            "open_opportunity_count": 2,
            "open_pipeline": Decimal("7520000"),
        }

    result = await provider.generate_with_tools(
        prompt="Show open pipeline for North.",
        tools=[],
        tool_executor=fake_executor,
    )

    assert len(executed_tools) == 1

    assert executed_tools[0]["name"] == (
        "get_pipeline_overview"
    )

    assert executed_tools[0]["arguments"] == {
        "region": "North"
    }

    assert "7,520,000" in result.text

    assert result.usage.input_tokens == 20
    assert result.usage.output_tokens == 10
    assert result.usage.total_tokens == 30

    # Verify that the second model request contains
    # the result linked to the original call ID.
    requests = provider.client.responses.requests

    assert len(requests) == 2

    returned_tool_output = requests[1]["input"][-1]

    assert returned_tool_output["type"] == (
        "function_call_output"
    )

    assert returned_tool_output["call_id"] == "call_123"

    returned_data = json.loads(
        returned_tool_output["output"]
    )

    assert returned_data["open_pipeline"] == "7520000"


@pytest.mark.asyncio
async def test_unsupported_question_does_not_execute_tool(
    mock_pricing,
):

    provider = make_provider([
        make_response(
            output_text=(
                "Bookings analytics is not currently available."
            )
        )
    ])

    def fake_executor(name, arguments):

        pytest.fail(
            "The executor should not run for an unsupported question."
        )

    result = await provider.generate_with_tools(
        prompt="What were our actual bookings?",
        tools=[],
        tool_executor=fake_executor,
    )

    assert "not currently available" in result.text
    assert len(provider.client.responses.requests) == 1


@pytest.mark.asyncio
async def test_tool_execution_failure_is_returned_to_model(
    mock_pricing,
):

    function_call = SimpleNamespace(
        type="function_call",
        name="get_pipeline_overview",
        arguments='{"region": "North"}',
        call_id="call_failure",
    )

    provider = make_provider([
        make_response(
            output=[function_call]
        ),
        make_response(
            output_text=(
                "I could not retrieve the pipeline data."
            )
        ),
    ])

    def failing_executor(name, arguments):

        raise RuntimeError("Database connection failed")

    result = await provider.generate_with_tools(
        prompt="Show North pipeline.",
        tools=[],
        tool_executor=failing_executor,
    )

    assert "could not retrieve" in result.text.lower()

    tool_output = provider.client.responses.requests[1]["input"][-1]

    error_data = json.loads(tool_output["output"])

    assert "error" in error_data


@pytest.mark.asyncio
async def test_provider_timeout_is_mapped_to_llm_timeout_error():

    timeout = APITimeoutError(
        request=httpx.Request(
            "POST",
            "https://api.openai.com/v1/responses",
        )
    )

    provider = make_provider([
        timeout
    ])

    def fake_executor(name, arguments):
        return {}

    with pytest.raises(LLMTimeoutError):

        await provider.generate_with_tools(
            prompt="Show North pipeline.",
            tools=[],
            tool_executor=fake_executor,
        )