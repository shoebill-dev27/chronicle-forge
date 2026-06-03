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

P0 (foundation): data model + deterministic world generation. See the roadmap
in the design document (section 14).

## Development

```bash
# install in editable mode with dev tooling
pip install -e ".[dev]"

# run tests
pytest

# format
black src tests
```

Copy `.env.example` to `.env` for the (optional) AI call sites; the core
simulation runs rules-only without any API key.

## License

TBD.
