from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, check_db_connection
from app.api.api_v1 import api_router
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("billflow")

# Initialize FastAPI with customized Swagger/OpenAPI documentation
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## BillFlow Subscription Billing Automation Engine
    
    A production-ready recurring billing infrastructure built with **FastAPI** and **PostgreSQL**.
    
    ### Key Features:
    * **Customer & Plan Management**: Define pricing tiers, feature entitlements, and trial periods.
    * **Subscription Lifecycle**: Manage transitions across `trial`, `active`, `past_due`, `paused`, and `cancelled`.
    * **Billing Cycle Engine**: Automated recurring billing runs.
    * **Proration Calculator**: Automatic credit/debit calculation for mid-cycle plan changes.
    * **Dunning & Retries**: Automated 1-3-7 day retry schedule for failed transactions.
    * **ReportLab Invoicing**: Branded, itemized PDF invoice generation.
    * **Compliance Audit Trail**: Immutable event logging for financial reconciliation.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Health & Database",
            "description": "Endpoints for verifying server health and PostgreSQL connectivity."
        },
        {
            "name": "Plans",
            "description": "Create, update, and manage subscription pricing tiers."
        },
        {
            "name": "Customers",
            "description": "Customer profiles and tokenized payment methods."
        },
        {
            "name": "Subscriptions",
            "description": "Subscriber lifecycle, trial periods, pause/resume, and cancellations."
        },
        {
            "name": "Audit Logs",
            "description": "Immutable audit trail of all financial and subscription state changes."
        }
    ]
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """Verify PostgreSQL connectivity on startup and initialize schema if connected."""
    logger.info("Initializing BillFlow backend application...")
    db_check = check_db_connection()
    if db_check["status"] == "connected":
        logger.info("Successfully connected to PostgreSQL! Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    else:
        logger.warning(
            f"Could not connect to PostgreSQL on startup: {db_check.get('error')}. "
            "Please verify that your PostgreSQL service is running and credentials in .env are correct."
        )

# Mount API routers under /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health & Database"])
def root():
    """Root endpoint providing system information and documentation links."""
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational",
        "swagger_docs": "/docs",
        "redoc_docs": "/redoc"
    }

@app.get("/health", tags=["Health & Database"])
def health_check():
    """General health check of the FastAPI service."""
    return {
        "status": "healthy",
        "service": "FastAPI",
        "version": settings.VERSION
    }

@app.get("/health/db", tags=["Health & Database"])
def database_health_check():
    """
    Directly tests the PostgreSQL database connection by executing 'SELECT 1'.
    Returns detailed connection diagnostics.
    """
    connection_status = check_db_connection()
    return connection_status
