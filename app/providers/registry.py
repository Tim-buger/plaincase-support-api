from app.core.config import Settings
from app.providers.base import LLMProvider, ProviderError
from app.providers.mock import MockProvider
from app.providers.openai import OpenAIProvider


def build_provider(name: str, settings: Settings) -> LLMProvider:
    if name == "mock":
        return MockProvider()
    if name == "openai":
        return OpenAIProvider(settings)
    raise ProviderError(f"Unsupported provider: {name}")

