import os
import logging
import time

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

# Structured response objects

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
    ) -> LLMResult:

        start_time = time.perf_counter()

        try:
            response = await self.client.responses.create(
                model=self.model,
                input=prompt,
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

    async def close(self):
        await self.client.close()