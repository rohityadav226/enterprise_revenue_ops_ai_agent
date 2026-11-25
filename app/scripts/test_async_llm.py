import asyncio
import logging

from app.services.llm.openai_provider import (
    OpenAIProvider,
    LLMServiceError
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

async def main():

    provider = OpenAIProvider()

    try:
        result = await provider.generate(
            """
            You are the NexusFlow Revenue Operations assistant.
            Explain in two sentences why actual bookings
            and open pipeline should be tracked separately.
            """
        )

        print(f"\nMODEL RESPONSE: {result.text}"
              f"\n\nREQUEST DETAILS:- "
              f"\nModel: {result.model}"
              f"\nRequest ID: {result.request_id}"
              f"\nLatency: {result.latency_ms} ms"
              "\n\nTOKEN USAGE:-"
              f"\nInput: {result.usage.input_tokens}"
              f"\nCached input token: {result.usage.cached_input_tokens}"
              f"\nOutput: {result.usage.output_tokens}"
              f"\nTotal: {result.usage.total_tokens}"
              "\n\nESTIMATED COST:-"
              f"\n$ {result.usage.estimated_cost_usd} USD")

    except LLMServiceError as exc:
        print(f"\nLLM REQUEST FAILED:-"
              f"\n{type(exc).__name__}"
              f"\n{str(exc)}")

    finally:
        await provider.close()

if __name__ == "__main__":
    asyncio.run(main())
    