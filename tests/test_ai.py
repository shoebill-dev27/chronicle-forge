"""AI integration (P4): fallback works with no key, mock client exercises the
model path, and generators never mutate world state."""

from __future__ import annotations

from chronicle_forge import generate_history_book, narrate_ending, simulate_world
from chronicle_forge.ai import (
    AIBudget,
    AnthropicAIClient,
    FallbackAIClient,
    get_ai_client,
)
from chronicle_forge.ai.client import AIClient, AIRequest, AIResponse

# --- client layer -------------------------------------------------------


def test_get_ai_client_without_key_is_fallback(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert isinstance(get_ai_client(), FallbackAIClient)


def test_fallback_client_uses_template(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = FallbackAIClient()
    req = AIRequest(system="s", user="u", assemble=lambda d: d["text"])
    resp = client.complete(
        req, lambda: AIResponse(text="TEMPLATE", structured={"text": "TEMPLATE"})
    )
    assert resp.source == "fallback"
    assert resp.text == "TEMPLATE"


def test_anthropic_client_uses_injected_transport():
    # Transport simulates a successful structured model response.
    def transport(request: AIRequest) -> dict:
        return {"structured": {"text": "MODEL"}, "tokens": 100, "cost": 0.001}

    client = AnthropicAIClient(transport=transport, api_key="x")
    req = AIRequest(system="s", user="u", assemble=lambda d: d["text"], max_tokens=500)
    resp = client.complete(req, lambda: AIResponse(text="FB", structured={}))
    assert resp.source == "anthropic"
    assert resp.text == "MODEL"
    assert resp.tokens_used == 100


def test_anthropic_client_falls_back_on_transport_error():
    def boom(request: AIRequest) -> dict:
        raise TimeoutError("simulated timeout")

    client = AnthropicAIClient(transport=boom, api_key="x")
    req = AIRequest(system="s", user="u", assemble=lambda d: d["text"], max_tokens=500)
    resp = client.complete(
        req, lambda: AIResponse(text="FB", structured={"text": "FB"})
    )
    assert resp.source == "fallback"
    assert resp.text == "FB"


def test_budget_guard_forces_fallback():
    budget = AIBudget(max_tokens_per_call=100)
    calls = {"n": 0}

    def transport(request: AIRequest) -> dict:
        calls["n"] += 1
        return {"structured": {"text": "MODEL"}, "tokens": 10}

    client = AnthropicAIClient(transport=transport, budget=budget, api_key="x")
    req = AIRequest(system="s", user="u", assemble=lambda d: d["text"], max_tokens=999)
    resp = client.complete(req, lambda: AIResponse(text="FB", structured={}))
    assert resp.source == "fallback"
    assert calls["n"] == 0  # transport never invoked when unaffordable


# --- generators (read-only on world) ------------------------------------


def test_history_book_fallback_is_readable_and_pure(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    world = simulate_world(42)
    before = world.model_dump_json()

    chronicle = generate_history_book(world)
    assert chronicle.world_id == world.id
    assert chronicle.ending_class == world.ending_class
    assert len(chronicle.generated_text) > 100
    assert world.ending_class in chronicle.generated_text
    # Rules own truth: generating prose must not mutate world state.
    assert world.model_dump_json() == before


def test_ending_narration_fallback_mentions_class(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    world = simulate_world(42)
    before = world.model_dump_json()
    text = narrate_ending(world)
    assert world.ending_class in text
    assert world.model_dump_json() == before


def test_history_book_uses_model_when_client_provided():
    world = simulate_world(7)

    class StubClient(AIClient):
        def complete(self, request, fallback):
            structured = {
                "title": "STUB TITLE",
                "chapters": [{"heading": "H", "text": "model chapter"}],
            }
            return AIResponse(
                text=request.assemble(structured),
                structured=structured,
                source="anthropic",
            )

    chronicle = generate_history_book(world, client=StubClient())
    assert "STUB TITLE" in chronicle.generated_text
    assert "model chapter" in chronicle.generated_text


def test_simulate_report_narrate_is_deterministic_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from chronicle_forge import simulate_report

    a = simulate_report(42, narrate=True)
    b = simulate_report(42, narrate=True)
    assert a == b
    assert "CHRONICLE (narrative)" in a
    assert "=== ENDING ===" in a
