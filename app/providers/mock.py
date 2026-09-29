import asyncio
import re

from app.providers.base import LLMProvider, ProviderResult
from app.schemas import SupportTicket, TicketCategory, TicketPriority, TicketSentiment


class MockProvider(LLMProvider):
    name = "mock"

    async def extract_ticket(self, text: str) -> ProviderResult:
        await asyncio.sleep(0.18)
        value = text.lower()

        def contains_any(words: tuple[str, ...]) -> bool:
            return any(re.search(rf"\b{re.escape(word)}\b", value) for word in words)

        category = TicketCategory.other
        if contains_any(("invoice", "charged", "refund", "billing", "payment")):
            category = TicketCategory.billing
        elif contains_any(("login", "password", "account", "locked")):
            category = TicketCategory.account
        elif contains_any(("error", "api", "timeout", "bug", "failed", "broken")):
            category = TicketCategory.technical
        elif contains_any(("feature", "would be great", "please add")):
            category = TicketCategory.feature_request

        priority = TicketPriority.medium
        if contains_any(("urgent", "production", "down", "immediately", "asap")):
            priority = TicketPriority.urgent
        elif contains_any(("blocked", "cannot", "can't", "failed")):
            priority = TicketPriority.high
        elif contains_any(("question", "whenever", "minor")):
            priority = TicketPriority.low

        frustrated = contains_any(("angry", "frustrated", "unacceptable", "again"))
        positive = contains_any(("thanks", "thank you", "great"))
        sentiment = (
            TicketSentiment.frustrated
            if frustrated
            else TicketSentiment.positive
            if positive
            else TicketSentiment.neutral
        )

        cleaned = re.sub(r"\s+", " ", text).strip()
        summary = cleaned if len(cleaned) <= 150 else f"{cleaned[:147]}..."
        action_by_category = {
            TicketCategory.billing: (
                "Review the transaction and confirm the refund or billing correction."
            ),
            TicketCategory.account: "Verify account ownership and restore access securely.",
            TicketCategory.technical: (
                "Reproduce the issue and inspect service logs using the supplied context."
            ),
            TicketCategory.feature_request: (
                "Validate demand and add the request to product triage."
            ),
            TicketCategory.other: (
                "Ask one clarifying question and route the request to the right owner."
            ),
        }
        keywords = [
            keyword
            for keyword in ("api", "payment", "login", "timeout", "refund", "production")
            if keyword in value
        ][:5]

        ticket = SupportTicket(
            category=category,
            priority=priority,
            summary=summary,
            next_action=action_by_category[category],
            sentiment=sentiment,
            requires_human=priority in {TicketPriority.high, TicketPriority.urgent},
            tags=keywords or [category.value],
        )
        return ProviderResult(data=ticket, model="deterministic-rules-v1")
