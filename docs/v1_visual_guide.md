# Chronicle Forge v1 — Visual Style Guide / Art Direction (D-4)

Status: **Draft for Design Lock (7/23).** Deliverable D-4 of I-0 (execution plan
§131: *Visual style guide / art direction — typefaces, ink palette, motion*).
Per routing this is a Sonnet-draft / Opus-review slot; the architectural
decisions here (the print/Hand contrast, the 縦書き/横書き call, font licensing)
are owner/lead judgments and carry the Opus draft directly. Binds the exact
faces, measure, palette, and motion that UX §7 deliberately left open, **in
Japanese faces** (ADR-003).

Authority: subordinate to `v1_ux_spec.md` §7 (Visual Language — roles), the
North Star / Principle 10 ("the interface is the artifact") / Principle 11 ("one
page, one focus"), **ADR-002** (pywebview + local static HTML/CSS/JS; all fonts
bundled, no CDN), **ADR-003** (JP typography on the critical path: 明朝 vs
手書き contrast, vertical/horizontal, character measure, hold-target sizing,
Q-UX-5 legibility), and **ADR-001** (⟜/❧ only; Must-only scope — portrait plates
beyond the minimum are cut). Binds with **D-3**: D-4 sets the measure; D-3 sets
copy length.

**Convention.** `REVIEW_REQUIRED(owner)` marks a genuine art-direction / native
aesthetic / licensing judgment for the owner. Everything else is a ratified rule.

---

## 1. The two typefaces — the load-bearing contrast (in JP)

UX §7: the print/Hand contrast "is the single most load-bearing visual device."
In Japanese faces:

- **Print — 明朝体 (Mincho).** The historian. Upright, even color, dry authority.
  **Recommended: Noto Serif JP / 源ノ明朝 (Source Han Serif).** Rationale:
  SIL OFL — freely **bundleable** (ADR-002 no-CDN), 7 weights, excellent screen
  hinting, full kanji coverage, actively maintained. De-risks licensing entirely.
- **The Hand — 手書き／行書系.** The soul. Irregular baseline, warmer ink,
  human. **Recommended register: 行書系 (semi-cursive), *not* 草書 (fully
  cursive)** — the Hand carries readable content (entries, reveals), so it must
  stay legible at body size (Q-UX-5). Candidate open/free faces to evaluate:
  a brush/行書 OFL face (e.g. 源界明朝-adjacent brush families, or a free 手書き
  face with a genuine hand quality). *`REVIEW_REQUIRED(owner)`: choose the Hand
  face and confirm its license permits bundling + redistribution — this is the
  one real licensing risk (no dominant OFL brush face); the owner (native reader)
  also judges its "hand" quality, which is aesthetic, not mechanical.*

Rule **T-1 (contrast is legible before it is seen).** The faces must read as two
distinct voices at body size and at a flip-glance; the difference reinforces
D-3's register split (V-1), never substitutes for it.

Rule **T-2 (the Hand is reserved).** Script/手書き type appears **only** for the
soul (current entry, past sealed acts, S-02 reveals). No other element — UI,
headers, captions — may use it (UX §7).

## 2. Setting direction — 縦書き vs 横書き `REVIEW_REQUIRED(owner)`

The single biggest visual decision, explicitly deferred to D-4 by ADR-003.

**Recommendation: ship v1 in 横書き (horizontal), trial 縦書き at the 7/27
skeleton and let the owner make the final call on evidence.** Reasoning:

| Factor | 縦書き (vertical) | 横書き (horizontal) |
|---|---|---|
| Thematic fit ("illuminated book / real record") | **Stronger** — a Japanese reader feels "a book," reinforcing Principle 10 | Good, but more "modern page" |
| Generated proper nouns (generated worlds render engine truth — ADR-001; their names are **English/Latin** and unbounded — ADR-003 proper-noun policy / repo language) | Awkward — needs 縦中横 or rotation for every Latin name/year | **Natural** — Latin names/years sit inline |
| Margin-as-stage (UX §7: year ticks, marks, P-09 flicker live in margins) | Margin semantics rotate (needs rework of the §7 layout model) | Matches §7's implicit layout directly |
| Hold target / marks / map integration | All need vertical-axis rework | Reuse western-book assumptions |
| Build velocity (3-week solo, 7/27 skeleton, 7/30 alpha) | Higher risk — vertical metrics + 縦中横 + webfont vertical features are finicky | Lower risk — CSS default |
| Web feasibility (ADR-002) | Supported (`writing-mode: vertical-rl`) but heavier | Trivial |

The mixed-content problem is decisive for v1: **standard worlds emit engine
(English) proper nouns**, which read badly vertical, and D-5 ships those worlds
as the bulk of replay. 横書き keeps them clean without per-name special-casing.

**But this is an owner call** — the thematic pull of 縦書き for a *Japanese*
illuminated chronicle is real and the owner is the native reader judging it, with
SC-gate weight (the "object, not app" feeling, P-02). Binding the decision to the
**7/27 I-1 go/no-go** (an existing checkpoint) lets the skeleton render one page
both ways so the choice is made on a real screen, not in the abstract — no new
process. *`REVIEW_REQUIRED(owner)`: ratify 横書き for v1, or direct a 縦書き
build accepting the velocity/mixed-content cost; decide at/by 7/27.*

## 3. Measure, size, one-focus

- **M-1 (line measure).** Body 明朝: **28–32 全角 characters per line** (the JP
  equivalent of UX §7's ~55 Latin chars, since 1 全角 ≈ 2 Latin). A page needing
  more becomes two pages (UX §7). This **sets D-3's character budgets** (D-3 §5).
- **M-2 (one focal object per page).** Principle 11 — a single choice, passage,
  mark, or plate per spread; generous margins are the stage for time and marks,
  not filler (UX §7).
- **M-3 (body size).** Chosen so 28–32 全角 fills the measure comfortably at the
  target window size; Hand set slightly larger or looser to stay legible against
  its irregularity. Exact px is an I-1 tuning detail, floored by Q-UX-5 (§8).
- *`REVIEW_REQUIRED(owner)`: confirm 28–32 全角 reads comfortably in the chosen
  明朝 at the shipped size — a native legibility judgment (feeds Q-UX-5).*

## 4. Hold-target sizing (I-05)

**Amended 2026-09-08 (baseline UX-R2):** inspection's primary path is a
visible, labelled, keyboard-reachable "調べる" affordance; the hold below is an
**optional convenience gesture**, never the only way in, and no timed input is
required. The sizing rules apply to both the affordance and the hold target.

The optional hold-to-inspect gesture (UX §6, ~800 ms) needs an adequate target:

- **H-1.** The hit area is the **whole marked line**, minimum height ≥ 1.5×
  line-height and **≥ 44 CSS px** in the hold axis (touch/pointer floor).
- **H-2.** Hold duration ~800 ms; releasing early cancels with no reveal (UX
  I-05). A subtle ink-fill progress on the line indicates the hold (motion §7).
- **H-3.** In 横書き the target is the line's height; in 縦書き its width —
  resolves once §2 is decided.

## 5. Ink palette

The whole game lives in one ink world (UX §7 "same ink world"):

- **Paper:** aged warm cream (near-paper, not white).
- **Print ink (墨):** warm near-black; even, dry color.
- **Hand ink:** a warmer, slightly wetter sepia/brown-black — perceptibly the
  same medium, a different hand.
- **The one accent — 朱 (vermilion).** The single system-wide accent ink.
  **Amended 2026-09-08 (baseline UX-R5): reserved for a *confirmed connection to
  a past life*, and nothing else** — not for "still shaping the world", which is
  now carried by explicit text where a reached projection supports it. The P-12
  rubricated highlight is 朱 because it *is* a pre-revealed confirmed connection
  (D-06). UX §7 "one accent, one meaning, everywhere" is unchanged; the meaning
  is. 朱 is the traditional
  Japanese emphasis/annotation ink (朱書き) — culturally exact for "the line that
  still matters." No other color exists in v1. *`REVIEW_REQUIRED(owner)`: confirm
  朱 as the accent (vs. a darker red) — aesthetic + must pass the §8 contrast
  check.*

Rule **P-1 (color carries exactly one meaning).** 朱 = **confirmed past-life
 connection**, nowhere else (amended 2026-09-08, baseline UX-R5). Marks, Hand,
 ordinary selection and the S-03 promise mark are ink-family, never accent.

## 6. Marks — ⟜ / ❧

- **K-1.** Exactly two marks: **⟜ (echo)** and **❧ (legacy)** (ADR-001; ◦ cut).
  Hand-drawn strokes in the ink family, **not typeset chrome** (UX §7); always
  marginal, at decision/trace surfaces only (D-02).
- **K-2.** Rendered as small SVG/inline strokes (bundled), sized to sit in the
  margin without competing with the focal object (M-2). On the map (P-11) the
  same two glyphs are placed geographically.
- **K-3.** The glyph key (S-01 help, one line each, D-3 §8 U-glyphkey) is the only
  place their meaning is written.

## 7. The Hand's per-life variation

UX §7: "per-life the Hand varies subtly so a flipping reader senses 'different
life' before reading." In JP:

- **HV-1.** Vary **weight + baseline/rotation jitter + ink wetness**, cycling by
  life ordinal — **not** a different font (it is one soul). 2–3 subtle variants
  is enough; the reader should feel change, not catalog it.
- **HV-2.** Implemented in CSS (font-weight if the Hand face ships multiple
  weights; small `transform`/`letter-spacing`/baseline jitter otherwise). No new
  asset per life. *`REVIEW_REQUIRED(owner)`: confirm the variation reads as
  "same soul, different life" and not as "different person" — aesthetic.*

## 8. Q-UX-5 legibility check (the pass gate)

ADR-003 requires the two-typeface contrast to pass a Japanese legibility check.
Definition (owner-observed at the R0 table read, on the target display):

1. Print (明朝) and Hand (行書) are each **comfortably readable** at shipped body
   size (28–32 全角 measure).
2. The two are **distinguishable at a flip-glance** (T-1) *and* by register (D-3
   V-1) — the contrast survives both channels.
3. **朱 accent** is distinguishable from print ink for color-normal vision and
   still readable under a reduced-color / low-contrast simulation (a11y floor,
   I-7).
4. Hold target meets H-1 (≥44 px / ≥1.5 line-height).
5. Marks ⟜/❧ are legible at margin size without stealing focus (M-2).

Fail on any point → adjust face/size/measure before I-1 hardens. *This is a
native-reader judgment; the owner runs it.*

## 9. Plates, whitespace, motion (inherited, bound)

- **Plates:** tipped-in, framed, print-captioned; roles limited to front-matter
  era plates (temperament) and the Map (P-11); portrait plates are SHOULD/cut
  (ADR-001 Must-only). ≤1 plate per spread (UX §7).
- **Whitespace:** generous margins as the stage for time/marks (M-2); body never
  exceeds the measure.
- **Motion — ink is the only animation language (UX §7, bound):** page turns
  (short, physical); ink-dry on P-08 (~3 s, unskippable first world); margin
  year-flicker on P-09; the Hand **blooming** under print on S-02 (~1.5 s,
  savored, cancels nothing); seal setting on I-04; hold-fill (H-2). **No motion
  that is not ink, paper, or thread** — no particles, glows, or shake. This is a
  binding constraint, not an owner choice.

## 10. Owner decision points (summary)

Genuine art-direction / aesthetic / licensing judgments (each tagged above):

1. **縦書き vs 横書き** for v1 — the big one (§2); decide by 7/27 on the skeleton.
2. **Hand face selection + license** to bundle (§1) — the one real licensing risk.
3. Measure comfort — 28–32 全角 in the chosen 明朝 at shipped size (§3).
4. **朱** as the accent ink (§5).
5. Per-life Hand variation reads as "same soul" (§7).
6. Q-UX-5 pass judgment (§8) — native-reader gate.

The 明朝 recommendation (Noto Serif JP, OFL), the measure *rule* (28–32 全角
mapping ~55 Latin), the two-glyph inventory, the one-accent-one-meaning rule, and
the ink-only motion set are **ratified rules**, not owner calls.

## 11. Cross-check (no contradiction)

- **ADR-001**: ⟜/❧ only (K-1); portrait plates cut (§9) — consistent.
- **ADR-002**: all faces bundled, no CDN (§1); CSS/HTML feasibility of 縦/横 and
  ink motion (§2/§9); measure/typography control is the reason pywebview was
  chosen — consistent, and the 7/27 go/no-go (§2) is ADR-002's own checkpoint.
- **ADR-003**: 明朝 vs 手書き contrast (§1), vertical/horizontal (§2), character
  measure (§3), hold-target (§4), Q-UX-5 (§8) — this doc *is* the ADR-003
  typography obligation.
- **UX §7**: two voices, ~55-Latin→28–32-全角 measure, one-focus, plates,
  one-accent, ink-only motion — all bound here, none contradicted.
- **D-3**: measure (§3) → D-3 budgets (§5); typeface reinforces but never
  replaces register (T-1/V-1) — complementary.
- **D-5 / D-6**: 朱 = the P-12 seeded-confirm accent (one per world, D-06);
  reveal-state is D-6's, not visual — no overlap.
