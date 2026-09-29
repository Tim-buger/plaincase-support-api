from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError

from app.core.config import Settings
from app.providers.base import LLMProvider, ProviderError, ProviderResult, TransientProviderError
from app.schemas import SupportTicket


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ProviderError("OPENAI_API_KEY is required when provider=openai")
        self.model = settings.openai_model
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.request_timeout_seconds,
            max_retries=0,
        )

    async def extract_ticket(self, text: str) -> ProviderResult:
        try:
            response = await self.client.responses.parse(
                model=self.model,
                instructions=(
                    "Extract a customer support ticket. Be concise and operational. "
                    "Set requires_human for urgent, high-risk, account access, or billing cases."
                ),
                input=text,
                text_format=SupportTicket,
            )
        except (APITimeoutError, APIConnectionError, RateLimitError) as exc:
            raise TransientProviderError(str(exc)) from exc
        except Exception as exc:  # SDK errors are normalized at the provider boundary.
            raise ProviderError(str(exc)) from exc

        if response.output_parsed is None:
            raise ProviderError("The model returned no structured output")
        return ProviderResult(data=response.output_parsed, model=self.model)

