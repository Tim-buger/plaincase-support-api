import asyncio
import logging
import random
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from app.core.config import Settings
from app.providers.base import ProviderError, TransientProviderError
from app.providers.registry import build_provider
from app.schemas import ExtractionRequest, ExtractionResponse, RunMetadata
from app.services.audit import AuditStore

logger = logging.getLogger(__name__)


class ExtractionService:
    def __init__(self, settings: Settings, audit_store: AuditStore) -> None:
        self.settings = settings
        self.audit_store = audit_store

    async def extract(
        self, request: ExtractionRequest, idempotency_key: str | None
    ) -> ExtractionResponse:
        if idempotency_key:
            existing = await asyncio.to_thread(
                self.audit_store.get_by_idempotency_key, idempotency_key
            )
            if existing:
                return existing.model_copy(
                    update={"meta": existing.meta.model_copy(update={"cached": True})}
                )

        request_id = f"req_{uuid4().hex[:16]}"
        provider_name = request.provider or self.settings.default_provider
        provider = build_provider(provider_name, self.settings)
        started = perf_counter()
        attempts = 0

        try:
            while True:
                attempts += 1
                try:
                    provider_result = await asyncio.wait_for(
                        provider.extract_ticket(request.text),
                        timeout=self.settings.request_timeout_seconds,
                    )
                    break
                except (TransientProviderError, TimeoutError):
                    if attempts > self.settings.max_retries:
                        raise
                    delay = min(0.25 * (2 ** (attempts - 1)) + random.uniform(0, 0.1), 2)
                    logger.warning(
                        "provider_retry",
                        extra={
                            "request_id": request_id,
                            "provider": provider_name,
                            "attempt": attempts,
                        },
                    )
                    await asyncio.sleep(delay)

            latency_ms = round((perf_counter() - started) * 1000)
            response = ExtractionResponse(
                data=provider_result.data,
                meta=RunMetadata(
                    request_id=request_id,
                    provider=provider_name,
                    model=provider_result.model,
                    attempts=attempts,
                    latency_ms=latency_ms,
                    cached=False,
                    created_at=datetime.now(UTC),
                ),
            )
            await asyncio.to_thread(self.audit_store.save_success, response, idempotency_key)
            logger.info(
                "extraction_complete",
                extra={
                    "request_id": request_id,
                    "provider": provider_name,
                    "latency_ms": latency_ms,
                },
            )
            return response
        except (ProviderError, TimeoutError):
            latency_ms = round((perf_counter() - started) * 1000)
            await asyncio.to_thread(
                self.audit_store.save_failure,
                request_id,
                provider_name,
                attempts,
                latency_ms,
            )
            raise
