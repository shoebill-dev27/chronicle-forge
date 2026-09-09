# ADR-004 — Horizontal setting (横書き) is the v1 baseline; vertical is deferred

- Status: **Accepted** (2026-08-02). Closes owner decision **OD-8**, which the
  Design Lock (2026-07-24) bound to evidence from the walking-skeleton run.
- Deciders: Tech Lead, on the T3 GUI smoke evidence; ratified into the P0 pass.
- Supersedes: the "decide at/by 7/27" placeholder in `v1_visual_guide.md` §2.

> **Erratum (2026-09-08, non-decisional).** The line below — "縦書き … becomes a
> real option only once world text is Japanese, which ADR-003 schedules after v1"
> — is an imprecise cross-reference. `ADR-003` defers the **English release** to
> v1.1; it keeps English proper nouns in the canonical docs with their Japanese
> renderings bound in the name table, so v1 player-facing copy **is** Japanese.
> 横書き stands for v1 on its own evidence (the engine emits unbounded English
> proper nouns — see Evidence below); the language cross-reference is **not**
> authorization for an English-content v1. This ADR's decision is unchanged.

## Context

D-4 §2 recommended 横書き for v1 but deliberately refused to settle it on paper:
the call was tied to the first real skeleton run, because the arguments on both
sides (a Japanese book *should* be vertical vs. the engine emits English) could
only be weighed by looking at a rendered page.

That run happened: **T3 GUI smoke, 2026-08-02** (`docs/v1_t3_gui_smoke.md`,
screenshots `docs/screenshots/t3/`). Vertical was exercised with both real
engine content and the long fixture.

## Evidence

With `writing-mode: vertical-rl`, the current build fails four ways at once
(`A-12-long-vertical.png`, `A-13-vertical-real.png`): Latin stacks one letter
per line, the verbs render outside the leaf, options overflow the paper edge,
and the Hand bloom collides with the confirm line. Three of those are ordinary
CSS defects (T3 B-3/B-4/B-5) and could be fixed in a day.

The fourth finding is not a defect and cannot be fixed in CSS:

> The engine emits **English** proper nouns and option labels of unbounded
> length (`Rebuild the seawall your grandmother's guild first raised against
> the tide`). In a vertical setting those must either stack one letter per line
> or rotate 90° as sideways runs. A page whose *majority* content is sideways
> Latin is not a Japanese book — it is a Japanese frame around English text.

縦書き is therefore blocked on **content**, not on layout. It becomes a real
option only once world text is Japanese, which ADR-003 schedules after v1.

## Decision

1. **横書き is the v1 baseline** and the only setting that ships. The visible
   縦/横 toggle is removed from the client.
2. **縦書き is deferred past v1.** Its CSS is kept, unmaintained and known
   broken, reachable only via `?axis=vertical` for engineering evaluation. It
   carries no test coverage and no support commitment.
3. Revisiting is gated on Japanese world content existing, not on a date.

## Consequences

- D-4's measure (28–32 全角), the margin stage, and the hold axis are all read
  in the horizontal sense for v1; the logical-property work done in T2 stays,
  so the vertical path is not actively deleted.
- T3 B-3/B-4/B-5 are **accepted as known defects**, not scheduled: fixing them
  would mean maintaining a mode that cannot ship.
- If the Japanese content layer lands for v1.1, this ADR is the first thing to
  re-open — the decision is about content, and the content is what would change.
