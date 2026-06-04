"""AI client abstraction (P4.0).

Design principle: **Rules own truth, AI owns prose.** An ``AIClient`` only turns
already-computed data into text; it never sees or mutates world state directly
(callers pass in pre-rendered prompts and a deterministic fallback).

Guarantees:
- Works with no ANTHROPIC_API_KEY: ``get_ai_client`` returns the deterministic
  :class:`FallbackAIClient`, which calls the caller's template fallback.
- The Anthropic implementation falls back on *any* failure (timeout, parse
  error, exhausted budget), so callers always get usable text.
- Structured output via a JSON schema; the caller supplies an ``assemble``
  function that turns the structured dict into final prose, used identically on
  the model path and the fallback path.
- Prompt-caching-ready: a large static ``cache_prefix`` is sent as a separate,
  cache-controlled system block.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional

# Rough output-token prices (USD per 1K tokens); only used for budget tracking.
_MODEL_COST_PER_1K = {
    "claude-opus-4-8": 0.015,
    "claude-sonnet-4-6": 0.003,
    "claude-haiku-4-5-20251001": 0.0008,
}
_DEFAULT_COST_PER_1K = 0.015


@dataclass
class AIBudget:
    """Cumulative guard so AI narration cannot run away in cost/tokens."""

    max_tokens_per_call: int = 2000
    max_total_tokens: int = 20_000
    max_total_cost_usd: float = 0.50
    used_tokens: int = 0
    used_cost_usd: float = 0.0

    def can_afford(self, est_tokens: int) -> bool:
        return (
            est_tokens <= self.max_tokens_per_call
            and self.used_tokens + est_tokens <= self.max_total_tokens
            and self.used_cost_usd < self.max_total_cost_usd
        )

    def record(self, tokens: int, cost: float) -> None:
        self.used_tokens += tokens
        self.used_cost_usd += cost


@dataclass
class AIRequest:
    system: str
    user: str
    assemble: Callable[[dict], str]  # structured dict -> final prose
    schema: Optional[dict] = None
    max_tokens: int = 1500
    cache_prefix: Optional[str] = None  # large static context (cacheable)
    timeout: float = 30.0
    purpose: str = "generic"


@dataclass
class AIResponse:
    text: str
    structured: Optional[dict] = None
    source: str = "fallback"  # "anthropic" | "fallback"
    tokens_used: int = 0
    cost_usd: float = 0.0


class AIClient(ABC):
    """Turns an AIRequest into prose, with a guaranteed deterministic fallback."""

    @abstractmethod
    def complete(
        self, request: AIRequest, fallback: Callable[[], AIResponse]
    ) -> AIResponse: ...


class FallbackAIClient(AIClient):
    """Never touches the network; always uses the caller's template fallback."""

    def complete(
        self, request: AIRequest, fallback: Callable[[], AIResponse]
    ) -> AIResponse:
        response = fallback()
        response.source = "fallback"
        return response


def _estimate_cost(tokens: int, model: str) -> float:
    return (tokens / 1000.0) * _MODEL_COST_PER_1K.get(model, _DEFAULT_COST_PER_1K)


class AnthropicAIClient(AIClient):
    """Anthropic-backed client. Falls back on any failure or budget exhaustion.

    ``transport`` is an injectable callable(AIRequest) -> dict for tests; it must
    return ``{"structured": {...}, "tokens": int, "cost": float}``. In production
    it defaults to the real SDK call.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        budget: Optional[AIBudget] = None,
        transport: Optional[Callable[[AIRequest], dict]] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self.model = model or os.getenv("CF_NARRATIVE_MODEL", "claude-opus-4-8")
        self.budget = budget or AIBudget()
        self._transport = transport
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    def complete(
        self, request: AIRequest, fallback: Callable[[], AIResponse]
    ) -> AIResponse:
        if not self.budget.can_afford(request.max_tokens):
            return self._fallback(fallback)
        try:
            raw = (self._transport or self._call_api)(request)
            structured = raw["structured"]
            text = request.assemble(structured)
            tokens = int(raw.get("tokens", request.max_tokens))
            cost = float(raw.get("cost", _estimate_cost(tokens, self.model)))
            self.budget.record(tokens, cost)
            return AIResponse(
                text=text,
                structured=structured,
                source="anthropic",
                tokens_used=tokens,
                cost_usd=cost,
            )
        except Exception:
            # Timeout, network, parse, schema, anything -> deterministic prose.
            return self._fallback(fallback)

    @staticmethod
    def _fallback(fallback: Callable[[], AIResponse]) -> AIResponse:
        response = fallback()
        response.source = "fallback"
        return response

    def _call_api(self, request: AIRequest) -> dict:
        import anthropic  # imported lazily so the dep stays optional

        client = anthropic.Anthropic(api_key=self._api_key, timeout=request.timeout)

        system_blocks = []
        if request.cache_prefix:
            # Static, cacheable context block (prompt caching).
            system_blocks.append(
                {
                    "type": "text",
                    "text": request.cache_prefix,
                    "cache_control": {"type": "ephemeral"},
                }
            )
        system_blocks.append({"type": "text", "text": request.system})

        schema_hint = (
            f"\n\nReturn ONLY valid JSON matching this schema:\n{json.dumps(request.schema)}"
            if request.schema
            else ""
        )
        message = client.messages.create(
            model=self.model,
            max_tokens=request.max_tokens,
            system=system_blocks,
            messages=[{"role": "user", "content": request.user + schema_hint}],
        )
        text = "".join(
            block.text
            for block in message.content
            if getattr(block, "type", "") == "text"
        )
        structured = json.loads(text)
        tokens = message.usage.output_tokens + message.usage.input_tokens
        return {
            "structured": structured,
            "tokens": tokens,
            "cost": _estimate_cost(message.usage.output_tokens, self.model),
        }


def get_ai_client(budget: Optional[AIBudget] = None) -> AIClient:
    """Return the best available client: Anthropic if a key + SDK are present,
    otherwise the deterministic fallback. Never raises."""
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            import anthropic  # noqa: F401

            return AnthropicAIClient(budget=budget)
        except Exception:
            pass
    return FallbackAIClient()
