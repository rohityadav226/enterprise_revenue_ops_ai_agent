import asyncio
import logging

from app.schemas.llm import RevOpsQuestion

from app.prompts.system_prompts import (
    REVOPS_CLASSIFIER_INSTRUCTIONS,
    REVOPS_ANSWER_INSTRUCTIONS,
    REVOPS_CLASSIFIER_PROMPT_VERSION,
    REVOPS_ANSWER_PROMPT_VERSION,
)

from app.prompts.templates import (
    build_classifier_input,
    build_evidence_answer_input,
)

from app.services.llm.openai_provider import (
    OpenAIProvider,
    LLMServiceError,
)


logging.basicConfig(level=logging.INFO)


async def main():

    provider = OpenAIProvider()

    question = (
        "What is our open pipeline in the North region?"
    )

    try:

        # STEP 1: Classify the user's question.

        classification = await provider.generate_structured(
            prompt=build_classifier_input(question),

            output_model=RevOpsQuestion,

            instructions=REVOPS_CLASSIFIER_INSTRUCTIONS,
        )

        request = classification.data

        print("\nCLASSIFICATION:")
        print(request.model_dump_json(indent=2))

        # STEP 2: Example evidence from an analytics service.
        # This is synthetic test data, not a database result.

        evidence = {
            "metric": "open_pipeline",
            "region": "North",
            "value": "5000000.00",
            "currency_code": "INR",
            "opportunity_count": 8,
        }

        # STEP 3: Assemble the answer context.

        answer_input = build_evidence_answer_input(
            user_question=question,

            validated_request=request.model_dump(
                mode="json"
            ),

            tool_name="get_pipeline_overview",

            filters={
                "region": request.region,
                "expected_close_date": None,
            },

            evidence=evidence,
        )

        # STEP 4: Generate an evidence-based answer.

        answer = await provider.generate(
            prompt=answer_input,

            instructions=REVOPS_ANSWER_INSTRUCTIONS,
        )

        print("\nFINAL ANSWER:")
        print(answer.text)

        print("\nPROMPT VERSIONS:")
        print(
            "Classifier:",
            REVOPS_CLASSIFIER_PROMPT_VERSION,
        )
        print(
            "Answer:",
            REVOPS_ANSWER_PROMPT_VERSION,
        )

        print("\nANSWER TOKEN USAGE:")
        print("Input:", answer.usage.input_tokens)
        print("Output:", answer.usage.output_tokens)
        print("Total:", answer.usage.total_tokens)

        print(
            "Estimated cost:",
            answer.usage.estimated_cost_usd,
            "USD",
        )

    except LLMServiceError as exc:

        print("\nLLM WORKFLOW FAILED:")
        print(type(exc).__name__)
        print(str(exc))

    finally:

        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())