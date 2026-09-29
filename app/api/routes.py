from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Query, Request, status

from app.providers.base import ProviderError
from app.schemas import AuditRecord, ExtractionRequest, ExtractionResponse

router = APIRouter(prefix="/api/v1")


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    return {
        "status": "ok",
        "service": request.app.state.settings.app_name,
        "environment": request.app.state.settings.app_env,
    }


@router.post("/extract/support-ticket", response_model=ExtractionResponse)
async def extract_support_ticket(
    payload: ExtractionRequest,
    request: Request,
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", min_length=8, max_length=128),
    ] = None,
) -> ExtractionResponse:
    try:
        return await request.app.state.extraction_service.extract(payload, idempotency_key)
    except ProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "provider_error", "message": str(exc)},
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"code": "provider_timeout", "message": "The provider timed out"},
        ) from exc


@router.get("/audit/recent", response_model=list[AuditRecord])
async def recent_audit_runs(
    request: Request, limit: Annotated[int, Query(ge=1, le=50)] = 10
) -> list[AuditRecord]:
    return request.app.state.audit_store.recent(limit)

