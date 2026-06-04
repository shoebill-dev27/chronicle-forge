"""AI integration (P4): prose generation only — Rules own truth, AI owns prose.

All generators are read-only on world state and fall back to deterministic
templates when no ANTHROPIC_API_KEY (or no SDK) is available.
"""

from __future__ import annotations

from .client import (
    AIBudget,
    AIClient,
    AnthropicAIClient,
    AIRequest,
    AIResponse,
    FallbackAIClient,
    get_ai_client,
)
from .ending_narrator import EndingNarrator, narrate_ending
from .historybook import HistoryBookGenerator, generate_history_book

__all__ = [
    "AIClient",
    "AIRequest",
    "AIResponse",
    "AIBudget",
    "FallbackAIClient",
    "AnthropicAIClient",
    "get_ai_client",
    "HistoryBookGenerator",
    "generate_history_book",
    "EndingNarrator",
    "narrate_ending",
]
