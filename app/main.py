from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

# API Routers

from app.api.v1.auth import router as auth_router

from app.api.v1.users import router as user_router

from app.api.v1.organizations import router as organization_router

from app.api.v1.workflows import router as workflow_router

from app.api.v1.workflow_actions import router as workflow_action_router

from app.api.v1.workflow_conditions import router as workflow_condition_router

from app.api.v1.events import router as event_router

from app.api.v1.executions import router as execution_router

from app.api.v1.notifications import router as notification_router

# WebSocket

from app.websocket.websocket_routes import router as websocket_router

# Middleware

from app.middleware.logging_middleware import LoggingMiddleware

from app.middleware.rate_limit_middleware import RateLimitMiddleware

# Monitoring

from sqlalchemy import text

from prometheus_fastapi_instrumentator import Instrumentator

from app.db.session import engine

# =====================================================
# Application Life Cycle
# =====================================================


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Starting Enterprise Workflow Platform...")

    # startup tasks:
    # database connection check
    # redis check
    # rabbitmq check

    yield

    print("Shutting down Enterprise Workflow Platform...")


# =====================================================
# FastAPI Application
# =====================================================


app = FastAPI(
    title="Enterprise Workflow Automation Platform",
    description="""
    Scalable Event Driven Workflow Platform
    
    Features:
    
    - JWT Authentication
    - Multi Tenant Organizations
    - Workflow Automation
    - RabbitMQ Event Bus
    - Celery Workers
    - Redis Cache
    - WebSocket Notifications
    - Retry System
    - Monitoring
    """,
    version="1.0.0",
    lifespan=lifespan,
)


# =====================================================
# CORS Middleware
# =====================================================


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# Custom Middleware
# =====================================================


app.add_middleware(LoggingMiddleware)


app.add_middleware(RateLimitMiddleware)


# =====================================================
# Register API Routes
# =====================================================


API_PREFIX = "/api/v1"


app.include_router(auth_router, prefix=API_PREFIX)


app.include_router(user_router, prefix=API_PREFIX)


app.include_router(organization_router, prefix=API_PREFIX)


app.include_router(workflow_router, prefix=API_PREFIX)


app.include_router(workflow_action_router, prefix=API_PREFIX)


app.include_router(workflow_condition_router, prefix=API_PREFIX)


app.include_router(event_router, prefix=API_PREFIX)


app.include_router(execution_router, prefix=API_PREFIX)


app.include_router(notification_router, prefix=API_PREFIX)


# WebSocket Routes


app.include_router(websocket_router)


# =====================================================
# Prometheus Monitoring
# =====================================================


Instrumentator().instrument(app).expose(app)


# =====================================================
# Health Check
# =====================================================


@app.get("/")
async def root():

    return {
        "application": "Enterprise Workflow Automation Platform",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    database = "disconnected"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        database = "connected"
    except Exception:
        database = "disconnected"

    return {
        "status": "healthy" if database == "connected" else "unhealthy",
        "database": database,
        "redis": "not_checked",
        "rabbitmq": "not_checked",
    }
