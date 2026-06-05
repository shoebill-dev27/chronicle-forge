# Example World — Seed 42

> The player's actions continued affecting history long after death.

| Lives | Events | Heritage | Ending |
|---|---|---|---|
| 3 | 77 | 8 | Theocratic Age |

## One causal chain

_One thread, from a single choice to the world's ending — the kind of story this game is built to let you tell:_

```
Life 1 — the warrior
   │  "spread the faith"   (seed-0014)
   ▼
Event (year 8) — the faith takes root
   │  endures 32 years, 18 events follow
   ▼
Heritage — "Doctrine of the Long Dawn"  (thought)
   │  tilts the world
   ▼
Ending — Theocratic Age
```

## How to read this (~5 minutes)

Read in this order:

**1. [summary.md](summary.md) — _~1 min, read first._**  
What this world is and what happened, for a first-time reader.

**2. [story.md](story.md) — _~2–3 min, the heart of it._**  
Each life traced Life → Seeds → Events → Heritage → Ending. Look for how one early life's single seed grows into the world's ending.

**3. [chronicle.md](chronicle.md) — _~1–2 min._**  
The full factual report. Jump to **"Why this Ending"** to see the `Ending ← Event ← Seed ← Life` chain spelled out.

**Then, by interest (optional):**

- [causal.dot](causal.dot) — _~1 min_ — the same lineages as a graph (`dot -Tpng causal.dot -o causal.png`). Look for gold ★ player seeds flowing down to the green `ENDING` node.
- [heritage.md](heritage.md) / [heritage.csv](heritage.csv) — _~1 min_ — the legacy ranking: which seed, from which life, mattered most.
- [timeline.md](timeline.md) — _~1 min_ — the year-by-year arc of the world.

_Everything here is generated from `simulate_world(42)` — fully reproducible, rules-only, no AI._
