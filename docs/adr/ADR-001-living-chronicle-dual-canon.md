# ADR-001 — Living Chronicle Presentation, Dual Canon, and v1 Scope

- Status: **Accepted** (owner-ratified 2026-07-20)
- Deciders: Owner (product), Design Lead / Tech Lead
- Informed by: five-lens delegate review (2026-07-19/20), Engine feasibility
  review (code-grounded), `docs/v1_execution_plan.md` §1–§3

## Context

The v1 design (SoT: definition, direction, UX spec, tutorial proof, content
proof) required three linked product decisions: the presentation frame, the
tutorial realization mode, and the integrity boundary between authored and
generated content. The Engine review established hard facts: generated worlds
have `MAX_SKIP = 8` years (since 2026-09 a fixed 10-year gap — `design_time_domain.md`) and a 200-year span cap; junctures are
tension-driven and cannot be authored into position; lineage memory is not a
persisted, generated artifact. The tutorial canon (54-year and 250-year skips,
year 803, staged junctures, a remembering lineage) is therefore outside the
generation envelope.

## Decision

1. **The Living Chronicle is the v1 presentation.** The game is an illuminated
   book; every screen is a page or spread; low-poly 3D is rejected as a frame
   (not deferred — rejected; see `design_v1_direction.md` §6–7).
2. **Dual Canon model.**
   - The **tutorial world is a fully authored canon**: a hand-written,
     internally consistent causal history (the Salt Kingdoms catalog,
     `v1_content_proof.md`) rendered through the same book UI. It is honest as
     fiction: every connection the player discovers really exists in the
     canon. Its timeline is authored beyond the engine envelope, and no claim
     of engine generation is made.
   - **Generated worlds (world 2+) are 100% engine truth.** Every mark, digest
     line, and trace chain derives from engine-emitted data. **No authored
     overlay may ever be blended into a generated world, and no generated
     world may be edited to "improve" its history.** This boundary is
     non-negotiable; it is what keeps D-08 ("marks never lie") true.
3. **The ◦ (memory) glyph is removed from v1.** Generated worlds cannot honor
   it (witnesses die during skips; lineage is unused; social-memory decay is
   transient). Teaching a glyph in the tutorial that the rest of the game can
   never honor would poison trust in the mark vocabulary. v1 ships **two
   glyphs: ⟜ (echo) and ❧ (legacy)**; a memory mark may return post-v1 if the
   engine ever grows persisted lineage memory.
   *Interpretation note:* the owner's ratification text said "removal of glyph
   markers"; this ADR records the agreed meaning as **removal of the ◦ marker
   only**. Removing all glyphs would delete the Hint tier (D-02) and with it
   the North Star's "through my own reasoning" — if full removal was intended,
   that is a critical conflict and must be re-raised, not silently applied.
4. **v1 scope is Must-only.** Cut: Threads spread (P-16), world sharing, sound
   system, portrait plates/illustrations beyond the minimum (~~map +~~ two glyphs
   + typography), "remembers you" tags. Nothing returns without a green
   schedule checkpoint (2026-08-07).
   *Amended by ADR-005 (2026-09-08):* the geographic **map** is struck from the
   v1 illustration minimum — the engine emits no spatial axis; deferred until
   W-1. The v1 minimum is two glyphs (⟜/❧) + typography.

## Consequences

- The DR revision pass (execution plan §4) updates the SoT docs to match
  (D-07 tutorial exception, two-canon notes, glyph reduction, renames).
- The tutorial ships as a curated content pack + the shared book UI; the
  engine and its frozen goldens are untouched by construction.
- Standard-world surfaces are built exclusively from existing engine data
  (compose-only / new read-model lenses; no engine change).
- A "curated seed shelf" (choosing which seeds the shelf offers as new books)
  is a *presentation-layer selection* and is permitted; editing a generated
  world's content is not.
