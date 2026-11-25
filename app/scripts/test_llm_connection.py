import os
from openai import (
    OpenAI,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
    APIStatusError
)

def main():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY enviornment variable is missing"
        )

    model = os.getenv(
        "OPENAI_MODEL",
        "gpt-6.2-sol",
    )

    client = OpenAI(
        timeout=30,
        max_retries=2,
    )

    try:
        response = client.responses.create(
            model=model,
            input=(
                "You are now connected to NexusFlow. Reply Exactly with: "
                "NexusFlow LLM connection is successfull"
            )
        )
        print(f"\nModel: {model}")
        print(f"\nResponse: {response.output_text}")

        if response.usage:
            print(f"\nTOKEN USAGE:--\nInput Tokens:"
                  f"{response.usage.input_tokens}\nTotal Tokens: {response.usage.total_tokens}")

    except AuthenticationError as exc:
        raise SystemExit(
            "Authentication failed. Check you API key"
        ) from exc

    except RateLimitError as exc:
        raise SystemExit(
            "API rate or usage limit reached. "
            "Check API billing and limits."
        ) from exc

    except APITimeoutError as exc:
        raise SystemExit(
            "The LLM request timed out."
        ) from exc

    except APIConnectionError as exc:
        raise SystemExit(
            "Could not connect to the LLM provider."
        ) from exc

    except APIStatusError as exc:
        raise SystemExit(
            f"API request failed. HTTP status: {exc.status_code}"
        ) from exc

if __name__ == "__main__":
    main()