from fastapi import FastAPI
from app.routers import (
    system,
    customers,
    products,
    analytics,
    auth
)

app = FastAPI(
    title="Enterprise Revenue Operations AI Agent",
    description="Backend for our enterprise AI assistant",
    version="1.0.0"
)

app.include_router(system.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(analytics.router)
app.include_router(auth.router)
