from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import register_middleware
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger
from app.cache.redis import connect_redis, disconnect_redis
from app.metrics.prometheus import setup_metrics

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await connect_redis()
    yield
    # Shutdown
    await disconnect_redis()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise-grade multi-tenant SaaS API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register middleware + exception handlers
register_middleware(app)
register_exception_handlers(app)

# Prometheus metrics
setup_metrics(app)

from app.routers import register_routers
register_routers(app)

# System routes (inline — too simple for separate router)
@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/ready", tags=["System"])
async def ready():
    from app.cache.redis import redis_client
    from app.database import SessionLocal
    checks = {}

    # Check Redis
    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"

    # Check DB
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "ready" if all_ok else "degraded",
        "checks": checks
    }


@app.get("/", include_in_schema=False)
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")