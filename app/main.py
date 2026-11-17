 """FastAPI application entry point.  Run with:  uvicorn app.main:app --reload"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.error import DomainError
from app.routers import billing, customers, plans, subscriptions

app = FastAPI(
    title="Subscription Billing Automation System",
    version="1.0.0-milestone1",
    description=(
        "Milestone 1: plans, customers, subscription lifecycle (state machine), "
        "billing cycle scheduler and audit log."
    ),
)


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app.include_router(plans.router)
app.include_router(customers.router)
app.include_router(subscriptions.router)
app.include_router(billing.router)


@app.get("/", tags=["System"])
def root():
    return {"message": "Subscription Billing Automation System - Milestone 1", "docs": "/docs"}


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok"}
