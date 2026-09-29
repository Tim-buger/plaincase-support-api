from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.audit import AuditStore
from app.services.extraction import ExtractionService

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    audit_store = AuditStore(settings.database_path)
    audit_store.initialize()
    app.state.settings = settings
    app.state.audit_store = audit_store
    app.state.extraction_service = ExtractionService(settings, audit_store)
    yield


app = FastAPI(
    title="Plaincase Support API",
    description=(
        "Reliable structured LLM extraction with provider adapters and operational telemetry."
    ),
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def demo() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
