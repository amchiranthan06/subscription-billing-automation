from fastapi import APIRouter
from app.api.endpoints import plans, customers, subscriptions, audit_logs

api_router = APIRouter()
api_router.include_router(plans.router)
api_router.include_router(customers.router)
api_router.include_router(subscriptions.router)
api_router.include_router(audit_logs.router)
