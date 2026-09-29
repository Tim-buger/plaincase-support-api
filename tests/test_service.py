from pathlib import Path

import pytest

from app.core.config import Settings
from app.providers.base import LLMProvider, ProviderResult, TransientProviderError
from app.schemas import ExtractionRequest, SupportTicket
from app.services.audit import AuditStore
from app.services.extraction import ExtractionService


class FlakyProvider(LLMProvider):
    name = "mock"

    def __init__(self) -> None:
        self.calls = 0

    async def extract_ticket(self, text: str) -> ProviderResult:
        self.calls += 1
        if self.calls == 1:
            raise TransientProviderError("temporary outage")
        return ProviderResult(
            model="flaky-test-v1",
            data=SupportTicket(
                category="technical",
                priority="high",
                summary=text,
                next_action="Retry succeeded; continue normal processing.",
                sentiment="neutral",
                requires_human=True,
                tags=["retry"],
            ),
        )


@pytest.mark.asyncio
async def test_retries_transient_provider_failure(tmp_path: Path, monkeypatch):
    provider = FlakyProvider()
    monkeypatch.setattr(
        "app.services.extraction.build_provider", lambda _name, _settings: provider
    )
    settings = Settings(database_path=tmp_path / "audit.db", max_retries=2)
    store = AuditStore(settings.database_path)
    store.initialize()
    service = ExtractionService(settings, store)

    response = await service.extract(
        ExtractionRequest(text="The API failed and our team is blocked.", provider="mock"),
        idempotency_key=None,
    )

    assert response.meta.attempts == 2
    assert provider.calls == 2
    assert response.data.tags == ["retry"]

