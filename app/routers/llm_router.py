from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from functools import partial

from app.dependencies import get_current_user

# Import get_db from wherever your existing database
# session dependency is defined.
from app.database import get_db

from app.services.llm.tool_definitions import REVOPS_TOOLS
from app.services.llm.tool_executor import execute_revops_tool
from app.prompts.system_prompts import REVOPS_TOOL_INSTRUCTIONS


router = APIRouter(
    prefix="/llm",
    tags=["LLM"],
)


class LLMQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


# Keep your existing /test endpoint here.

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

@router.post("/ask")
async def ask_llm(
    payload: LLMQuestionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    provider = request.app.state.llm_provider

    tool_executor = partial(
        execute_revops_tool,
        db,
    )

    result = await provider.generate_with_tools(
        prompt=payload.question,
        tools=REVOPS_TOOLS,
        tool_executor=tool_executor,
        instructions=REVOPS_TOOL_INSTRUCTIONS,
    )

    return {
        "answer": result.text,
        "model": result.model,
        "request_id": result.request_id,
        "latency_ms": result.latency_ms,
        "usage": {
            "input_tokens": result.usage.input_tokens,
            "cached_input_tokens": result.usage.cached_input_tokens,
            "output_tokens": result.usage.output_tokens,
            "total_tokens": result.usage.total_tokens,
            "estimated_cost_usd": (
                str(result.usage.estimated_cost_usd)
                if result.usage.estimated_cost_usd is not None
                else None
            ),
        },
    }