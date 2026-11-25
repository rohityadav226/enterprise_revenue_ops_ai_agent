from fastapi import FastAPI
from app.routers import (
    system,
    customers,
    products,
    analytics,
    auth,
    llm_router
)
from contextlib import asynccontextmanager
from app.services.llm.openai_provider import OpenAIProvider

@asynccontextmanager
async def lifespan(app: FastAPI):
    provider = OpenAIProvider()
    app.state.llm_provider = provider
    yield
    await provider.close()

app = FastAPI(
    title="NexusFlow",
    lifespan=lifespan,
    description="Backend for our enterprise AI assistant",
    version="1.0.0"
)

app.include_router(llm_router.router)
app.include_router(system.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(analytics.router)
app.include_router(auth.router)



