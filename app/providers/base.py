from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas import SupportTicket


class ProviderError(RuntimeError):
    """Base provider failure."""


class TransientProviderError(ProviderError):
    """A provider failure that may succeed when retried."""


@dataclass(frozen=True)
class ProviderResult:
    data: SupportTicket
    model: str


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def extract_ticket(self, text: str) -> ProviderResult:
        raise NotImplementedError

