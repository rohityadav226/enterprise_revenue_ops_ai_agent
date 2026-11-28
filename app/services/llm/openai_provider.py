import os
from starlette.concurrency import run_in_threadpool
import time
import json
import logging

from app.services.llm.tool_executor import make_json_safe

from dataclasses import dataclass
from decimal import Decimal

from openai import (
    AsyncOpenAI,
    APITimeoutError,
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    BadRequestError,
)
from typing import Generic, TypeVar, Callable, Any
from pydantic import BaseModel, ValidationError
from app.services.llm.pricing import calculate_estimated_cost

logger = logging.getLogger(__name__)

# Application level expectations

class LLMServiceError(Exception):
    pass

class LLMTimeoutError(LLMServiceError):
    pass


class LLMConnectionError(LLMServiceError):
    pass


class LLMRateLimitError(LLMServiceError):
    pass


class LLMConfigurationError(LLMServiceError):
    pass


class LLMRequestError(LLMServiceError):
    pass


class LLMProviderUnavailableError(LLMServiceError):
    pass

class LLMStructuredOutputError(LLMServiceError):
    pass

# Structured response objects
T = TypeVar("T", bound=BaseModel)

@dataclass(frozen=True)
class StructuredLLMResult(Generic[T]):
    data: T
    model: str
    request_id: str | None
    latency_ms: int
    usage: TokenUsage

@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: Decimal | None

@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str
    request_id: str | None
    latency_ms: int
    usage: TokenUsage

class OpenAIProvider:
    def __init__(self):

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-6.2-sol",
        )

        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=30.0,
            max_retries=2,
        )

    async def generate(
            self,
            prompt: str,
            instructions: str | None = None,
    ) -> LLMResult:

        start_time = time.perf_counter()

        try:
            response = await self.client.responses.create(
                model=self.model,
                input=prompt,
                instructions=instructions,
            )

        except APITimeoutError as exc:

            raise LLMTimeoutError(
                "LLM provider request timed out."
            ) from exc

        except RateLimitError as exc:

            raise LLMRateLimitError(
                "LLM provider rate limit or quota limit reached."
            ) from exc

        except AuthenticationError as exc:

            raise LLMConfigurationError(
                "LLM API authentication failed."
            ) from exc

        except PermissionDeniedError as exc:

            raise LLMConfigurationError(
                "LLM API permission denied."
            ) from exc

        except BadRequestError as exc:

            raise LLMRequestError(
                "LLM provider rejected the request."
            ) from exc

        except APIConnectionError as exc:

            raise LLMConnectionError(
                "Could not connect to the LLM provider."
            ) from exc

        except APIStatusError as exc:

            if exc.status_code >= 500:

                raise LLMProviderUnavailableError(
                    "LLM provider returned a server error."
                ) from exc

            raise LLMServiceError(
                f"LLM provider returned HTTP {exc.status_code}."
            ) from exc

        latency_ms = int((time.perf_counter() - start_time)*1000)

        response_usage = response.usage

        input_tokens = response_usage.input_tokens
        output_tokens = response_usage.output_tokens
        total_tokens = response_usage.total_tokens

        input_details = getattr(
            response_usage,
            "input_token_details",
            None,
        )

        cached_input_tokens = getattr(
            input_details,
            "cached_tokens",
            0,
        ) or 0

        estimated_cost = calculate_estimated_cost(
            model=self.model,
            input_tokens=input_tokens,
            cached_input_tokens=cached_input_tokens,
            output_tokens=output_tokens,
        )

        usage = TokenUsage(
            input_tokens=input_tokens,
            cached_input_tokens=cached_input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost,
        )

        result = LLMResult(
            text=response.output_text,
            model=self.model,
            request_id=getattr(
                response,
                "_request_id",
                None
            ),
            latency_ms=latency_ms,
            usage=usage,
        )

        logger.info(
            "LLm request completed",
            extra={
                "model": result.model,
                "request_id": result.request_id,
                "latency_ms": result.latency_ms,
                "input_tokens": usage.input_tokens,
                "cached_input_tokens": usage.cached_input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
                "estimated_cost_usd": (
                    str(usage.estimated_cost_usd)
                    if usage.estimated_cost_usd is not None
                    else None
                ),
            },
        )

        return result

    async def generate_structured(
        self,
        prompt: str,
        output_model: type[T],
        instructions: str | None = None,
) -> StructuredLLMResult[T]:
        start_time = time.perf_counter()

        try:

            response = await self.client.responses.parse(
                model=self.model,
                input=prompt,
                instructions=instructions,
                text_format=output_model,
            )

        except ValidationError as exc:

            raise LLMStructuredOutputError(
                "The model response failed Pydantic validation."
            ) from exc

        except APITimeoutError as exc:

            raise LLMTimeoutError(
                "LLM structured request timed out."
            ) from exc

        except RateLimitError as exc:

            raise LLMRateLimitError(
                "LLM provider rate or quota limit reached."
            ) from exc

        except AuthenticationError as exc:

            raise LLMConfigurationError(
                "LLM API authentication failed."
            ) from exc

        except PermissionDeniedError as exc:

            raise LLMConfigurationError(
                "LLM API permission denied."
            ) from exc

        except BadRequestError as exc:

            raise LLMRequestError(
                "LLM provider rejected the structured output request. "
                "Check model and JSON Schema compatibility."
            ) from exc

        except APIConnectionError as exc:

            raise LLMConnectionError(
                "Could not connect to the LLM provider."
            ) from exc

        except APIStatusError as exc:

            if exc.status_code >= 500:

                raise LLMProviderUnavailableError(
                    "LLM provider returned a server error."
                ) from exc

            raise LLMServiceError(
                f"LLM provider returned HTTP {exc.status_code}."
            ) from exc

        # Retrieve the parsed Pydantic object.

        parsed_output = response.output_parsed

        if parsed_output is None:

            raise LLMStructuredOutputError(
                "No structured output was returned. "
                "The model may have refused the request."
            )

        # Calculate latency.

        latency_ms = int(
            (time.perf_counter() - start_time) * 1000
        )

        # Retrieve token usage.

        response_usage = response.usage

        if response_usage is None:

            raise LLMStructuredOutputError(
                "Structured response did not contain usage information."
            )

        input_tokens = response_usage.input_tokens
        output_tokens = response_usage.output_tokens
        total_tokens = response_usage.total_tokens

        input_details = getattr(
            response_usage,
            "input_tokens_details",
            None,
        )

        cached_input_tokens = getattr(
            input_details,
            "cached_tokens",
            0,
        ) or 0

        estimated_cost = calculate_estimated_cost(
            model=self.model,
            input_tokens=input_tokens,
            cached_input_tokens=cached_input_tokens,
            output_tokens=output_tokens,
        )

        usage = TokenUsage(
            input_tokens=input_tokens,
            cached_input_tokens=cached_input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost,
        )

        return StructuredLLMResult(
            data=parsed_output,
            model=self.model,
            request_id=getattr(
                response,
                "_request_id",
                None,
            ),
            latency_ms=latency_ms,
            usage=usage,
        )

    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict],
        tool_executor: Callable[[str, dict], dict],
        instructions: str | None = None,
        max_tool_rounds: int = 3,
    ) -> LLMResult:

        start_time = time.perf_counter()

        input_items = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        total_cached_tokens = 0

        request_id = None

        def collect_usage(response):

            nonlocal total_input_tokens
            nonlocal total_output_tokens
            nonlocal total_tokens
            nonlocal total_cached_tokens
            nonlocal request_id

            usage_data = response.usage

            if usage_data is not None:

                total_input_tokens += usage_data.input_tokens
                total_output_tokens += usage_data.output_tokens
                total_tokens += usage_data.total_tokens

                input_details = getattr(
                    usage_data,
                    "input_tokens_details",
                    None,
                )

                cached_tokens = getattr(
                    input_details,
                    "cached_tokens",
                    0,
                ) or 0

                total_cached_tokens += cached_tokens

            request_id = getattr(
                response,
                "_request_id",
                request_id,
            )

        try:

            # Initial LLM request.
            response = await self.client.responses.create(
                model=self.model,
                input=input_items,
                tools=tools,
                instructions=instructions,
                tool_choice="auto",
            )

            collect_usage(response)

            for round_number in range(max_tool_rounds + 1):

                function_calls = [
                    item
                    for item in response.output
                    if item.type == "function_call"
                ]

                # Model has produced its final answer.
                if not function_calls:

                    latency_ms = int(
                        (time.perf_counter() - start_time) * 1000
                    )

                    estimated_cost = calculate_estimated_cost(
                        model=self.model,
                        input_tokens=total_input_tokens,
                        cached_input_tokens=total_cached_tokens,
                        output_tokens=total_output_tokens,
                    )

                    usage = TokenUsage(
                        input_tokens=total_input_tokens,
                        cached_input_tokens=total_cached_tokens,
                        output_tokens=total_output_tokens,
                        total_tokens=total_tokens,
                        estimated_cost_usd=estimated_cost,
                    )

                    logger.info(
                        "LLM completed response without requesting another tool"
                    )

                    return LLMResult(
                        text=response.output_text or "",
                        model=self.model,
                        request_id=request_id,
                        latency_ms=latency_ms,
                        usage=usage,
                    )

                if round_number == max_tool_rounds:
                    raise RuntimeError(
                        "Maximum tool-calling rounds exceeded."
                    )

                # Preserve all output items from the previous response.
                input_items.extend(response.output)

                tool_outputs = []

                for call in function_calls:

                    try:
                        logger.info(
                            "LLM requested tool execution",
                            extra={
                                "tool_name": call.name,
                                "tool_call_id": call.call_id,
                            },
                        )
                        
                        arguments = json.loads(call.arguments)

                        # Run synchronous SQLAlchemy work outside
                        # the async event loop.
                        result = await run_in_threadpool(
                            tool_executor,
                            call.name,
                            arguments,
                        )

                        output = json.dumps(
                            result,
                            default=make_json_safe,
                        )

                        logger.info(
                            "LLM requested tool execution",
                            extra={
                                "tool_name": call.name,
                                "tool_call_id": call.call_id,
                            },
                        )
                    except Exception:

                        logger.exception(
                            "Tool execution failed: %s",
                            call.name,
                        )

                        output = json.dumps({
                            "error": (
                                "The requested analytics operation "
                                "could not be completed."
                            )
                        })

                    tool_outputs.append({
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": output,
                    })

                input_items.extend(tool_outputs)

                # Send tool results back to the model.
                response = await self.client.responses.create(
                    model=self.model,
                    input=input_items,
                    tools=tools,
                    instructions=instructions,
                    tool_choice="auto",
                )

                collect_usage(response)

        except APITimeoutError as exc:

            raise LLMTimeoutError(
                "LLM tool-calling request timed out."
            ) from exc

        except RateLimitError as exc:

            raise LLMRateLimitError(
                "LLM provider rate or quota limit reached."
            ) from exc

        except AuthenticationError as exc:

            raise LLMConfigurationError(
                "LLM API authentication failed."
            ) from exc

        except PermissionDeniedError as exc:

            raise LLMConfigurationError(
                "LLM API permission denied."
            ) from exc

        except BadRequestError as exc:

            raise LLMRequestError(
                "LLM provider rejected the tool-calling request."
            ) from exc

        except APIConnectionError as exc:

            raise LLMConnectionError(
                "Could not connect to the LLM provider."
            ) from exc

        except APIStatusError as exc:

            if exc.status_code >= 500:

                raise LLMProviderUnavailableError(
                    "LLM provider returned a server error."
                ) from exc

            raise LLMServiceError(
                f"LLM provider returned HTTP {exc.status_code}."
            ) from exc

        raise RuntimeError(
            "Tool-calling loop ended unexpectedly."
        )

    async def close(self):
        await self.client.close()