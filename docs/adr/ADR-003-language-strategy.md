# ADR-003 — v1 Language Strategy: Japanese First

- Status: **Accepted** (owner-directed 2026-07-20, evaluated and endorsed by
  Design Lead)
- Deciders: Owner (product decision), Design Lead (evaluation)

## Context

The execution plan (and all five delegate reviews) recommended English-first,
Japanese later. The owner has directed the reverse: **v1 ships Japanese;
English follows in a later release.** This ADR evaluates that reversal rather
than rubber-stamping it.

The delegate consensus for English rested on three premises: (1) the reference
audience (Pentiment / Sir Brante) is English-first; (2) the existing golden-
path copy is authored in English; (3) "a week-4 rush translation cannot
preserve a specified voice." Premises (2)–(3) argued against a *late JP
translation* — not against JP as the primary authored language.

## Decision

**v1 is Japanese-first.** Rationale — the consensus premises invert under this
team's reality:

1. **The release gate is only valid in Japanese.** The gate is two observed
   fresh-cohort playtests (R1/R2) with strict SC bars. The owner recruits and
   moderates testers in Japanese; testing a specified *voice* through
   non-native readers, or recruiting an English cohort remotely in two weeks,
   would invalidate the gate far more than any market argument justifies.
2. **Voice control is stronger in Japanese.** The historian's voice is a
   specified character and the product IS prose. The owner can author/review
   Japanese natively; English copy would be LLM-drafted with weak human voice
   review — the actual quality risk sat on the English path all along.
3. The English catalog in `v1_content_proof.md` remains the **structural
   canon** (events, years, causality, discovery staging are language-
   independent); Japanese player-facing copy is authored *from* it under the
   JP voice guide — an authored original, not a translation.

## Consequences

- **Q-UX-9 lands on the critical path**: JP typographic rules — print = 明朝
  体, Hand = 手書き/行書系 contrast; vertical vs. horizontal setting decision;
  line-length (characters, not ~55 Latin chars) and hold-target sizing — are
  bound in the visual & voice guides (D-3/D-4) *before* page implementation
  hardens. The two-typeface contrast must pass the Q-UX-5 legibility check in
  Japanese faces (licensing included).
- The copy-audit rules are re-derived for Japanese (the "you/your" grep
  becomes a second-person/呼びかけ audit; word budgets become character
  budgets). Audit lane (local LLM/Haiku) gets the JP rule set.
- Playtest cohorts are Japanese (profiles per `v1_tutorial_world_proof.md`
  §4.2, JP equivalents of the reader-gamer/general-gamer split).
- **English becomes v1.1**: authored from the same canon under an EN voice
  pass, with its own reduced gate (at minimum one fresh-cohort SC check); the
  existing EN copy in the canon docs is its head start. Store/positioning
  implications are the owner's domain.
- Proper-noun policy: canonical docs keep English names (repo language
  policy); the JP voice guide binds their Japanese renderings (kanji coinage
  vs. katakana) once, in a name table, before any JP copy is written.
