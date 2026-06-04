# Chronicle Forge

A history-creation RPG / reincarnation roguelite / AI-assisted world simulation.

You are the world's only reincarnator. When you die you reincarnate, but the
world keeps running: NPCs, factions, and history continue. Your goal is not to
save the world — it is to intervene in history and witness how your choices
shape the future. The core experience is the traceable causal link between what
you did and the history that resulted: *"my actions created this history."*

The world lives for a fixed span (200 years in production, 40 in dev/CI). On
reaching the limit the game produces a Chronicle and an Ending classification.

## Design

The full, design-locked specification lives in
[`docs/design.md`](docs/design.md) (v0.3). The causal-link system is the core
engine; history generation, evaluation, and the chronicle viewer are all
subordinate to it. Guiding architectural rule: **rules own truth, AI owns
prose** — state transitions are deterministic; the LLM only narrates and makes a
few bounded decisions.

## Status

P0–P5 complete: deterministic foundation, causal core, micro loop (a life),
macro loop (death → time-skip → history → reincarnation, reproducible from the
seed), and a read-only observability layer. See the roadmap in the design
document (section 14). Next: P4 (AI integration).

## Running a world

```bash
# simulate a full world deterministically and print the developer report
PYTHONPATH=src python -m chronicle_forge 42
```

The report (read-only, no AI) shows the world summary, player lives, personal
history, theme trajectory, major events, wildcard history, the heritage Top 10,
and the NPC codex — enough to read a finished world and judge it as a game.

## Development

```bash
# run tests (no install needed; pytest uses pythonpath=src)
pytest

# format
black src tests
```

Copy `.env.example` to `.env` for the (optional) AI call sites; the core
simulation runs rules-only without any API key.

## License

TBD.
