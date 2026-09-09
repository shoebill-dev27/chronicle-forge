# ADR-005 — The geographic Map (P-11) is deferred past v1

- Status: **Accepted** (owner-directed 2026-09-08, on the evidence in
  `docs/design_v1_uiux_baseline.md` §2 UX-R1 and the five-seed placelessness check).
- Deciders: Owner (scope decision), Design Lead (evaluation).
- Supersedes / amends: `ADR-001` §4 ("map" inside the illustration minimum);
  `design_v1_direction.md` §4 Must Have "The Map spread", §7 concept, §9
  deliverable 7, §10 R-D; `v1_ux_spec.md` P-10 right page and **P-11 Map Spread**
  (MUST → deferred).

## Context

`design_v1_direction.md` §4 and `v1_ux_spec.md` P-10/P-11 carry a geographic
**Map spread** as a v1 MUST: an illustrated world map, redrawn between lives, with
the player's caused changes marked *geographically*. `ADR-001` §4 keeps "map" in
the minimum illustration set.

The engine emits **no spatial axis**. Measured across seeds 1/7/42/99/123:
`CausalNode.location_id` is `None` on **0 of ~301** causal nodes
(`design_v1_time_surface.md` §1; `design_v1_i3_rebirth_digest.md` §1). Every event
this engine produces is placeless. A map plate for a generated world would have to
**invent a position** for every mark it draws — which `ADR-001`'s dual-canon
boundary ("generated worlds are 100% engine truth; no authored overlay") and the
[v1 definition](../design_v1_definition.md) Principle 1 ("never fabricate history")
both forbid.

The "what changed while I was gone" beat that the Map was meant to carry
(direction §4: *"the player can see at least one change their past life caused"*)
is already delivered without geography by the **P-10 rebirth digest** (the
attributed `(sealed act → consequence)` lines) and the **C1 time surface** (the
strata + camera push on the player's own mark).

## Decision

1. **P-11, the geographic Map spread, is removed from the v1 MUST set** and is
   not implemented in v1. No map plate, no `location_id` rendering, no invented
   coordinates.
2. **The direction §4 minimum bar is met by the P-10 digest + the C1 time
   surface.** "The player can see at least one change their past life caused" is
   satisfied by attributed digest lines and the seal push, not by a map.
3. **`v1_ux_spec.md` P-10 loses its right page** (the Map plate); the rebirth
   spread is the digest (left page) alone. P-11 is struck from the page inventory
   for v1 and marked deferred.
4. **Re-open gate: W-1** — a spatial axis in worldgen (real `location_id` on
   causal nodes). Not a date. If W-1 lands, this ADR is the first to re-open and
   the Map returns to scope as originally specified.

## Consequences

- `direction` §4 Must Have, §7, §9 deliverable 7, and §10 R-D are annotated
  "deferred per ADR-005"; deliverable 7 (Map spread spec) is not required for v1.
- `ADR-001` §4's illustration minimum reads "two glyphs + typography" for v1;
  "map" is struck with an ADR-005 pointer.
- `v1_implementation_roadmap.md` I-3's third bullet (P-11 map plate) is closed as
  "retired — ADR-005"; I-3 remains **P-10 left page only**, as already built.
- DoD-4's "trace-walk in the client" is unaffected; DoD has no map criterion.
- No engine, worldgen, RNG, `reporting/`, or canonical-recipe change. The 8
  frozen engine goldens + chronicle `aa4c67a416178e92` + replay transcript
  `98bea8622c686d8e` are untouched by construction.
