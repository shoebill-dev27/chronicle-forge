# Code Review — P4 (AI Integration, Phases 4.0–4.2)

Scope: AI client abstraction, history book generation, ending narration.
NPC decision / memory interpretation / death narration are deferred.

Design principle enforced throughout: **Rules own truth, AI owns prose.** AI code
is read-only on world state and only turns already-computed data into text.

## 1. Implementation files

| File | Phase | Responsibility |
|---|---|---|
| `src/chronicle_forge/ai/__init__.py` | 4.0 | Public surface for the AI subpackage |
| `src/chronicle_forge/ai/client.py` | 4.0 | `AIClient` ABC, `AIRequest`/`AIResponse`, `AIBudget`, `FallbackAIClient`, `AnthropicAIClient`, `get_ai_client` |
| `src/chronicle_forge/ai/historybook.py` | 4.1 | `HistoryBookGenerator` / `generate_history_book` → `Chronicle.generated_text` |
| `src/chronicle_forge/ai/ending_narrator.py` | 4.2 | `EndingNarrator` / `narrate_ending` → ending epilogue text |

Modified (non-AI):
- `ending.py`: split out pure `derive_ending_class` (no mutation) from `classify_ending`.
- `autoplay.py`: `simulate_report(seed, narrate=False)` optionally appends chronicle + ending.
- `__init__.py`: export the AI surface.
- `pyproject.toml`: optional `ai` extra (`anthropic>=0.40`).

## 2. Dependencies added

- **Optional only:** `anthropic>=0.40` under `[project.optional-dependencies].ai`.
- No new required runtime dependency. With neither key nor SDK, everything runs
  via deterministic templates.

## 3. How the required guarantees are met

| Requirement | Mechanism |
|---|---|
| AIClient interface | `AIClient` ABC with `complete(request, fallback)` |
| Anthropic vs Fallback separated | `AnthropicAIClient` and `FallbackAIClient`; chosen by `get_ai_client()` |
| Works with no `ANTHROPIC_API_KEY` | `get_ai_client` returns `FallbackAIClient`; generators always pass a template fallback |
| Fallback = templates | `_fallback_response` in each generator builds structured + prose deterministically |
| Structured output (JSON Schema) | `AIRequest.schema`; model told to return JSON; parsed and `assemble`d |
| Prompt-caching ready | `AIRequest.cache_prefix` sent as a separate `cache_control: ephemeral` system block |
| Budget guard | `AIBudget` (per-call + cumulative tokens/cost); `can_afford` gates the call |
| Timeout → fallback | `AnthropicAIClient.complete` wraps the call in `try/except` (timeouts included) → fallback |
| No change to deterministic sim | AI never writes world state; `simulate_world` does not call AI; `simulate_report(narrate=True)` only appends text and, without a key, is itself deterministic |

Note: the same `assemble(structured)` function is used on both the model and
fallback paths, so output shape is identical regardless of source.

## 4. New tests (`tests/test_ai.py`, 9 tests)

- `test_get_ai_client_without_key_is_fallback`
- `test_fallback_client_uses_template`
- `test_anthropic_client_uses_injected_transport` (model path via injected transport)
- `test_anthropic_client_falls_back_on_transport_error` (timeout/error → fallback)
- `test_budget_guard_forces_fallback` (transport never called when unaffordable)
- `test_history_book_fallback_is_readable_and_pure` (≥100 chars, mentions ending, **world unchanged**)
- `test_ending_narration_fallback_mentions_class` (**world unchanged**)
- `test_history_book_uses_model_when_client_provided` (stub client output flows through)
- `test_simulate_report_narrate_is_deterministic_without_key`

All tests run with **no API key and no network** (Anthropic path exercised via an
injected transport / stub client).

Full suite: **86 passing** (was 77; +9). Existing tests unchanged and green.

## 5. Sample output (seed 42, fallback prose)

**Chronicle:**
```
The Chronicle of Hollowfen — Theocratic Age

## Prologue
Over 40 years the land of Hollowfen passed through 3 lives of its one reincarnated
soul, beginning in an age of governance and ending in one of faith — remembered as
the Theocratic Age.

## The Reincarnator's Lives
The Warrior of Hollowfen lived from year 0 to 7. From this life's deeds, 33 later
events would grow. The Merchant of Hollowfen lived from year 15 to 20 ... The Priest
of Hollowfen lived from year 28 to 35 ...

## Legacies
The thought (from seed seed-0014) endured 32 years and set 18 further events in
motion, the surest mark the reincarnator left on history. The school (from seed
seed-0007) endured 29 years and set 15 further events in motion ...

## Turning Points
Wreveth the conqueror rose and ran their course, bending the age.

## Epilogue
So Hollowfen settled into the Theocratic Age, its shape owed less to fate than to
the choices of the one who lived and died and returned.
```

**Ending:**
```
Thus ended the Theocratic Age.

After 3 lives and 40 years, the world came to rest as an age ruled from altars,
where faith was law. Its longest shadow was a thought that endured 32 years.
```

(With `ANTHROPIC_API_KEY` set and the `ai` extra installed, the same data is sent
to the model and richer prose is produced; on any failure it returns exactly the
text above.)

## 6. Review notes / trade-offs

- The Anthropic structured output uses a JSON-in-prompt + `json.loads` approach
  rather than tool-forced JSON; if parsing fails, the fallback fires. A future
  hardening could use tool/`response_format` enforcement.
- `_call_api` is not unit-tested against the live SDK (no network in CI); it is
  covered structurally via the injected `transport` seam.
- Cost numbers are coarse estimates for budget tracking, not billing-accurate.

## 7. Commit

- Branch: `design/v0.3-foundation` (local only; not pushed).
- Hash: see commit `P4: AI integration ...` recorded alongside this document.
