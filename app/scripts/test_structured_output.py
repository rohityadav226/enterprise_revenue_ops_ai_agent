import asyncio

from app.schemas.llm import RevOpsQuestion

from app.services.llm.openai_provider import (
    OpenAIProvider,
    LLMServiceError,
)


async def main():

    provider = OpenAIProvider()

    question = """
    Show open pipeline for the North region,
    grouped by sales stage, between January 1, 2026
    and March 31, 2026.
    """

    prompt = f"""
    You are the NexusFlow RevOps question classifier.

    Your task is to classify the user's business question
    and extract its explicitly stated filters.

    Rules:

    1. Select exactly one supported intent.
    2. Never invent filters.
    3. Return null for filters not explicitly provided.
    4. Extract explicit calendar dates into period_start
       and period_end.
    5. For relative periods such as "last quarter",
       preserve the original phrase in period_expression
       and leave the date fields null.
    6. Select the requested group_by value.
    7. Set needs_clarification to true if the request
       cannot be classified sufficiently.
    8. Never generate SQL or calculate business metrics.

    User question:

    {question}
    """

    try:

        result = await provider.generate_structured(
            prompt=prompt,
            output_model=RevOpsQuestion,
        )

        print("\nSTRUCTURED OUTPUT:")
        print(
            result.data.model_dump_json(
                indent=2
            )
        )

        print("\nVALIDATION:")
        print(
            isinstance(
                result.data,
                RevOpsQuestion,
            )
        )

        print("\nUSAGE:")
        print("Input:", result.usage.input_tokens)
        print("Output:", result.usage.output_tokens)
        print("Total:", result.usage.total_tokens)

        print("\nPERFORMANCE:")
        print("Model:", result.model)
        print("Latency:", result.latency_ms, "ms")
        print(
            "Estimated cost:",
            result.usage.estimated_cost_usd,
            "USD",
        )

    except LLMServiceError as exc:

        print("\nSTRUCTURED REQUEST FAILED:")
        print(type(exc).__name__)
        print(str(exc))

    finally:

        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())