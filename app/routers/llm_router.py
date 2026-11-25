from fastapi import APIRouter, Request
from fastapi import Depends
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/llm",
    tags=["LLM"],
)


@router.post("/test")
async def test_llm(
    request: Request,
    current_user=Depends(get_current_user),
):

    provider = request.app.state.llm_provider

    result = await provider.generate(
        "Explain open pipeline in one sentence."
    )

    return {
        "answer": result.text,
        "model": result.model,
        "request_id": result.request_id,
        "latency_ms": result.latency_ms,
        "usage": {
            "input_tokens": result.usage.input_tokens,
            "output_tokens": result.usage.output_tokens,
            "total_tokens": result.usage.total_tokens,
            "estimated_cost_usd": (
                str(result.usage.estimated_cost_usd)
                if result.usage.estimated_cost_usd is not None
                else None
            ),
        },
    }