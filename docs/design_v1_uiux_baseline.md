# Chronicle Forge v1 — UI/UX Baseline (reconciliation of the Astra UI/UX review)

Date: **2026-09-07**. Branch `design/v1`, working tree carrying the uncommitted
I-1b/I-2/I-3 client + `play/beats.py` changes.

Status: **Design proposal. Not an implementation, not a new Design Lock, not an
increment authorization.** This document verifies the Astra review
([`design_v1_uiux_review.md`](design_v1_uiux_review.md)) UX-R1..UX-R10 against the
accepted ADRs and the SoT specs, records an explicit Adopt / Adopt-with-modification
/ Reject verdict per item, lists the accepted documents that conflict, names the
ADR/spec amendments each verdict needs, and redefines the next design object as the
**Discovery Vertical Slice**. No engine, client, save, or test file was changed to
produce it. The North Star of every judgement below is the
[v1 definition](design_v1_definition.md) §4: *does this strengthen the player
discovering, unaided and across felt time, their own past lives' marks on the world.*

The Astra review is a **proposal**, not an authority. Where it and an accepted ADR
disagree, the ADR is the baseline until the ADR is amended.

---

## 1. Verification method

- Read in full: all four ADRs, [`design_v1_definition.md`](design_v1_definition.md),
  the Astra review.
- Read the load-bearing sections of: [`v1_ux_spec.md`](v1_ux_spec.md),
  [`design_v1_direction.md`](design_v1_direction.md),
  [`v1_client_state_spec.md`](v1_client_state_spec.md),
  [`design_v1_time_surface.md`](design_v1_time_surface.md),
  [`v1_implementation_roadmap.md`](v1_implementation_roadmap.md),
  [`design_v1_visual_language.md`](design_v1_visual_language.md),
  [`v1_jp_voice_guide.md`](v1_jp_voice_guide.md),
  [`design_p18_investigation_surface.md`](design_p18_investigation_surface.md),
  [`design_v1_i2_life_loop.md`](design_v1_i2_life_loop.md),
  [`design_v1_i3_rebirth_digest.md`](design_v1_i3_rebirth_digest.md).
- Grep-checked `src/chronicle_forge/play/beats.py`,
  `client/web/book.js`, `client/web/render`/`render.py` for the current data shapes.
- No fresh playtest, no seed sweep, no runtime run. Where the review's §3.1
  five-seed data is cited, it is cited as the review's, not re-measured.

Product-code change from this work: **zero.** `git diff --stat -- src/` shows only
the pre-existing uncommitted I-1b/I-2/I-3 increment
(`beats.py`, `book.js/css`, `index.html`, `strings.js`); nothing in it is authored
or modified here.

---

## 2. UX-R1..UX-R10 — consistency matrix and verdicts

Legend: **Adopt** · **Adopt-mod** (adopt with the stated modification) · **Reject**.
"Conflicts" lists **accepted** documents whose current text the verdict contradicts
and that must be amended together on adoption.

### UX-R1 — Compact history + expandable investigation; non-geographic history surface for v1 instead of a mandatory geographic map

**Verdict: Adopt-mod.**

- **Fact.** The engine emits no spatial axis: `CausalNode.location_id` is `None`
  on 0 of ~301 causal nodes across seeds 1/7/42/99/123
  ([`design_v1_time_surface.md`](design_v1_time_surface.md):54–56;
  [`design_v1_i3_rebirth_digest.md`](design_v1_i3_rebirth_digest.md) §1). A map
  plate would have to invent a position for every mark it draws.
- **Conflicts.** `ADR-001` §4 lists "map" inside the illustration minimum
  (`ADR-001-living-chronicle-dual-canon.md`:49); `direction` §4 Must Have "The Map
  spread" (`design_v1_direction.md`:209–211), §7 concept (:399), §9 deliverable 7
  (:508–510), §10 R-D (:556–557); `v1_ux_spec.md` P-10 right page + **P-11 Map
  Spread = MUST** (:99–100, :247–262).
- **Modification.** Keep the *requirement* "the player can see at least one change
  their past life caused" (direction §4); satisfy it with the **rebirth digest
  (P-10 left) + the C1 time surface**, not a map. Demote **P-11 to deferred**,
  re-openable only when W-1 puts a spatial axis in worldgen. This is a genuine
  scope change to three owner-ratified documents → **new ADR-005** (§4).
- **North Star.** Passes: the "what changed while I was gone" beat is preserved;
  only its *geographic* rendering is deferred. Fabricating geography would violate
  definition Principle 1 and ADR-001's 100%-engine-truth boundary.

### UX-R2 — Teach investigation explicitly; optional hold with an ordinary accessible activation; separate inspect / select / commit

**Verdict: Adopt.**

- **Fact.** Today the discovery verb is a hidden ~800 ms hold with **no visible
  label** (`v1_jp_voice_guide.md` §8 `U-remember`: "*no label — physical hold;
  tooltip only*"; `v1_ux_spec.md` I-05 :396). Selection and inspection are
  entangled: I-03 "Selection previews the act *written faintly* in the Hand"
  (`v1_ux_spec.md`:395).
- **Conflicts.** `v1_ux_spec.md` §6 I-03/I-05; `v1_jp_voice_guide.md` §8
  (`U-remember` no label); `design_v1_visual_language.md`:215 (hold verb as the
  affordance); `v1_client_state_spec.md` §4.1 (resumable states — add an
  inspect-open, non-persistent, state).
- **Spec.** Three distinct actions, none of which performs another:
  **inspect** (opens evidence; never selects, never commits; visible "調べる"
  button + keyboard + optional ~800 ms hold as a convenience), **select**
  (I-03; previews the pending act, commits nothing), **commit/seal** (I-04;
  irreversible). Screen-reader text and focus styling carry the same meaning as
  the hold's ink-fill.
- **North Star.** Passes: "調べる" names an operation, it does not reveal the
  answer. A hidden gesture is not itself a historical mystery
  (definition Principle 2; review §4 :142–145).

### UX-R3 — D-03 / D-04 apply to every visual and caption, including C1; unconfirmed origins are never pre-attached to a life's strata layer or personal seal

**Verdict: Adopt.**

- **Fact.** `time.js` draws `aftermath.hardened` and captions its founder without
  checking discovery state (review §3 :98–100); the C1 `echo` register "the
  caption counts the echoes" (`design_v1_time_surface.md`:295) is not guarded.
  D-03/D-04 as written name only the P-10 digest and P-05/P-13 reading
  (`v1_ux_spec.md`:344–355) — the time surface is not in scope.
- **Conflicts.** `v1_ux_spec.md` §5 D-03/D-04 wording; the time-renderer spec in
  `design_v1_time_surface.md`; `v1_client_state_spec.md` §3.4 `surface` tags
  (add the C1 surface).
- **Spec.** Extend D-03/D-04 to enumerate **every** surface — entry, time
  surface, digest, history, trace, resume. Before confirmation, no older-life
  founder identity may surface through text, accessible label, geometry, colour,
  or focus behaviour. The current C1 `sealed` register (朱 + camera push toward
  the player's **own** just-sealed seal) is current-life and stays; the `echo`
  register must count events without naming or moving toward a founder.
- **North Star.** Passes: this is the definition's "induced, not delivered"
  (Principle 2) made uniform.

### UX-R4 — One temporal encoding: year = horizontal position; strata depth = historical order and material, not an event count standing in for years

**Verdict: Adopt.**

- **Fact.** The spike sells depth as elapsed time ("カメラは8年の中にいる",
  `design_v1_time_surface.md`:103) but the shipped renderer made strata
  **thickness a fixed px-per-event count** (:298–303). Depth therefore encodes
  neither years nor order unambiguously.
- **Conflicts.** `design_v1_time_surface.md` (depth semantics vs. §10 update);
  `design_v1_visual_language.md` (strata as material); the `time.js` renderer
  spec.
- **Spec.** Horizontal position = **year** (actual duration; stable per-view
  scale, viewport moved deliberately, no rescale-after-choice; future area holds
  no predicted names/count/ending/density). Strata depth = **historical order**
  (ordinal layering), explicitly *not* a quantitative year count. Event density
  is neither age nor importance; a shared cause is never drawn as exclusive
  ownership. The same visual coordinate survives from act record → later history.
- **Not re-opened.** C1's *adoption* over the five rivals stands; this fixes its
  encoding contract only.

### UX-R5 — 朱 means "confirmed connection to a past life"; ⟜/❧ stay trace-kind labels; current influence gets its own truthful text

**Verdict: Adopt-mod.**

- **Fact.** `design_v1_visual_language.md` is internally inconsistent: :148 "on a
  confirmed reveal the mark's leaf goes 朱", :213–214 "Size, not colour, carries
  confirmation; 朱 is added only for *still shaping the world*."
- **Conflicts.** `design_v1_visual_language.md` §5/§6 (D-4 colour rule);
  `v1_ux_spec.md` §5 (glyph semantics) and D-06 (:360, "one highlighted
  **still-shaping** legacy" — the *concept* must survive).
- **Modification.** 朱 = confirmed past-life connection, consistently in prose,
  diagrams, and client. Ordinary selection/promise marks stay ink. ⟜ = echo,
  ❧ = legacy remain **kind** labels, never the "unconfirmed→confirmed" state.
  "Still-shaping" is retained as a **concept** (D-06 needs it) but expressed as a
  small explicit text annotation, and only when a current/reached projection
  supports it — a `hardened` *name* does not confer it. Replaces D-4's 朱 rule;
  propagate with the rest of the ledger, not piecemeal.

### UX-R6 — Recognition and trace are proven by the exact original sealed act and an ordered real causal path; player decisions, autonomous life actions, and contributing causes are never conflated

**Verdict: Adopt.**

- **Fact.** `beats.py::Recognition` (`beats.py`:73–82) carries `option`, `name`,
  `founder_life`, `founder_talent`, `planted_year`, `reach` — **no field for the
  founder life's original sealed-act label/text**, so the reveal cannot quote
  "the same wording the player saw when committing it" (review §3 :95–97, §6.3).
  P18 `CauseChain.steps` is an **ancestor count**, `origin_life` the earliest
  player seed's ordinal — **not** an ordered path
  (`design_p18_investigation_surface.md` §3.1, §4; review §7 :333–339).
  `Change.sealed` already distinguishes player choice from autonomous action
  (`beats.py`:97). The juncture renders bare tension vocabulary
  (`render.py`:61 `"your past pulls here"` as `why`).
- **Conflicts.** The recognition-beat contract in `v1_ux_spec.md` §5 (D-05 reveal
  grammar); `design_p18_investigation_surface.md` (`steps` must not be drawn as a
  path); `v1_ux_spec.md` P-14 (ordered links) vs. P18's count;
  `v1_client_state_spec.md` D-6 reveal identity.
- **Spec (all additive; no engine / RNG / worldgen / recipe change).**
  - **C-2** Sealed-act identity: the founder life's original displayed label +
    text (recoverable in `BeatRecorder._sealed`) is carried on the digest line
    and on `Recognition`, stable across surfaces and resume.
  - **C-3** Ordered causal path: the trace presenter consumes a concrete list of
    existing edges (`trace_to_roots`, roadmap I-4), the original act where
    recoverable, and a truthful "other causes contributed" indication. P18
    `steps`/`origin_life` stay a summary, never the drawn path. An ellipsis over
    grouped events is never drawn as a direct edge.
  - **C-6** Three display categories, never merged: **player-sealed act** (Hand;
    may be called "the choice you made"); **autonomous life action** (historical
    narration; same character, never "your choice"); **contributing cause** (one
    origin among several). An autonomous origin can be traced honestly but does
    **not** satisfy Success Criterion 2; a run whose only traceable origin is
    autonomous records a content-gate miss, it is not relabelled.
- **Kept.** I-3's existing `(act → consequence)` join and SP-1
  (`design_v1_i3_rebirth_digest.md` §2.3–2.4) are **not** disturbed — no evidence
  contradicts them and SP-1's guaranteed first recognition rests on the join.

### UX-R7 — One emphasized last-life feedback item at return, further items on request; quiet years and empty endings are specified

**Verdict: Adopt.**

- **Fact.** P-10 is already capped at 3 lines, last-life only
  (`v1_ux_spec.md`:241–250, D-03); 17/116 empty digests across seeds 1–30 are all
  terminal (`design_v1_i3_rebirth_digest.md` §2.5).
- **Conflicts.** `v1_ux_spec.md` P-10/P-12 emphasis wording; standard-world RD
  rules; `design_v1_i3_rebirth_digest.md`; `v1_jp_voice_guide.md` §5 budgets.
- **Spec.** Return shows the changed present first, then **one** explicit sealed
  act + its consequence as the default emphasis; up to two further lines on
  request, within the existing three-change budget. This is **delivered feedback
  that teaches persistence — explicitly not the earned-recognition climax**;
  digest comprehension alone can never pass the SC-1 earned bar
  (review §11 :476). A life with no juncture, and a skip with an empty echo list,
  still gets its own dated entry and temporal place — never a fabricated decision
  or an enlarged non-event.

### UX-R8 — A full read-only past and a minimum of persistent state belong in the first complete prototype; rereading never re-executes

**Verdict: Adopt.**

- **Fact.** The client has no persistent save/resume and flip-back is limited to
  opening/shelf navigation (review §3 :104–106). I-2 deliberately gave the entry
  **no flip** and pushed save/resume to I-6
  (`design_v1_i2_life_loop.md`:65–66, :165). The full contract already exists as
  `v1_client_state_spec.md` (D-6) and is mandated by `ADR-002`.
- **Conflicts.** `v1_implementation_roadmap.md` §2 increment order (save/resume =
  I-6); `design_v1_i2_life_loop.md` "no flip"/"no save/resume"; `v1_ux_spec.md`
  navigation (§3.3 read-only past is specified but unbuilt).
- **Spec.** Pull the **minimum** D-6 slice forward into the vertical slice: a
  read-only archive of prior decisions available during play, plus an atomic save
  of `{sealed inputs, reveal set, cursor}` and exact resume, plus the persistent
  「今の頁へ」 that restores the unresolved choice, selection, focus, and scroll.
  Navigation and commitment are separate state; past options are readable but
  inert. This is a **roadmap sequencing amendment**, not an ADR change
  (ADR-002 already owns the module).

### UX-R9 — Accessibility and skip from the first world; explicit operational UI copy is allowed; understanding is assessed separately from gesture execution

**Verdict: Adopt.**

- **Fact.** `v1_jp_voice_guide.md` A-1 flags imperative address on non-Confirm
  surfaces (§4 :87–90), yet `U-seal` already ships as 記す / 封じる (§8) — an
  implicit, unstated exception for UI controls. Reduced motion, text scaling,
  keyboard operation, and skip are currently deferred to I-7 hardening
  (`v1_implementation_roadmap.md` §2).
- **Conflicts.** `v1_jp_voice_guide.md` §4 A-1 and §8 UI inventory; `v1_ux_spec.md`
  §6/§8; `v1_implementation_roadmap.md` I-7 (a11y floor); DoD-1/DoD-7 proxy
  wording.
- **Spec.** Baseline from world 1: reduced motion, readable static time
  transitions, text scaling that reflows rather than shrinking to a fixed
  rectangle, full keyboard operation, and a skip that settles before a separate
  continuation input. Add an **explicit A-1 carve-out**: non-diegetic UI control
  labels (記す, 調べる, その前には？, 続きから) are exempt from the
  second-person/imperative audit; diegetic prose is not; DoD-7 "zero waivers"
  is unaffected because the carve-out is a rule, not a waiver. The DoD-1 "hold
  path" proxy is replaced by **player-initiated recognition supported by an
  explanation** (button or keyboard inspection equally eligible; a fallback
  reveal is recorded as assisted exposure).

### UX-R10 — Reconcile the already-decided two-glyph set and the Japanese-first baseline; separate historical schedules from current status

**Verdict: Adopt.**

- **Fact.** `ADR-001` §3 removed ◦ and ships **⟜/❧ only** (:37–42);
  `v1_jp_voice_guide.md` A-3 already enforces ⟜/❧-only. But `v1_ux_spec.md` §5
  still tables three glyphs including ◦ (:322–326) and D-02 still references the
  P-11 map and ◦. `ADR-004` says 縦書き is blocked until "world text is Japanese,
  which ADR-003 schedules after v1" (`ADR-004-horizontal-layout-v1.md`:36) — an
  imprecise cross-reference: `ADR-003` defers the **English release** to v1.1 and
  keeps English proper nouns in the canonical docs with their Japanese renderings
  bound in the name table (`ADR-003-language-strategy.md`:34–37, :52–58). The
  roadmap's August 2026 dates are historical (`v1_implementation_roadmap.md`
  :3–8, :10).
- **Conflicts.** `v1_ux_spec.md` §4/§5 stale ◦ / "remembers you" passages vs.
  `ADR-001` §3; `ADR-004` Context/Decision cross-reference vs. `ADR-003` text.
- **Spec.** (a) Delete the ◦ row and all descendant-memory / "remembers you"
  passages from `v1_ux_spec.md` §4/§5 and the tutorial asides — glyph set is
  ⟜/❧. (b) Add a **non-decisional erratum** to `ADR-004`: 横書き stands on the
  unbounded-English-proper-noun evidence (:29–36); the language cross-reference
  does not authorize an English-content v1; v1 player-facing copy is Japanese
  (ADR-003). ADR-004's decision is unchanged. (c) Stamp the roadmap/exec-plan
  dates as historical. All of this is housekeeping toward already-accepted ADRs —
  **no new decision, no new ADR.**

### Summary table

| ID | Verdict | New ADR? | SoT amendments |
|---|---|---|---|
| UX-R1 | Adopt-mod | **ADR-005 (new)** | ADR-001 §4; direction §4/§7/§9-7/§10; ux_spec P-10/P-11 |
| UX-R2 | Adopt | no | ux_spec §6 I-03/I-05; jp_voice §8; visual_language; client_state §4.1 |
| UX-R3 | Adopt | no | ux_spec §5 D-03/D-04; time_surface renderer; client_state §3.4 |
| UX-R4 | Adopt | no | time_surface §depth + §10; visual_language; time.js spec |
| UX-R5 | Adopt-mod | no | visual_language §5/§6 (D-4); ux_spec §5 + D-06 wording check |
| UX-R6 | Adopt | no | recognition-beat contract; P18 doc; ux_spec P-14; client_state D-6 |
| UX-R7 | Adopt | no | ux_spec P-10/P-12; standard-world RD; i3; jp_voice §5 |
| UX-R8 | Adopt | no | roadmap §2 order; i2; ux_spec §3.3/navigation; client_state (subset) |
| UX-R9 | Adopt | no | jp_voice §4 A-1 + §8; ux_spec §6/§8; roadmap I-7→slice; DoD-1/7 proxy |
| UX-R10 | Adopt | no | ux_spec §4/§5 (delete ◦); ADR-004 erratum; roadmap dates |

**Rejects: none.** Every item is either adopted or adopted with a narrowing
modification. UX-R1 and UX-R5 are the only two carrying a modification; UX-R1 is
the only one needing a fresh owner decision.

---

## 3. The new baseline — how discovery state is represented, consistently, across every surface

One knowledge-state enum, honoured identically by every renderer (this is
**C-4** in §5; it supersedes the surface-specific phrasing scattered through
`v1_ux_spec.md` §5 and `design_v1_time_surface.md`):

| Knowledge state | The only permitted representation, on **every** surface |
|---|---|
| An explicit act just recorded | The act in the Hand; a promise mark iff a seed was actually planted; no future result |
| Historical consequence, uninvestigated | Ordinary historical text + a truthful inspect affordance; **no** founder-specific text, geometry, colour, camera move, or focus behaviour |
| Delivered last-life feedback (P-10) | The permitted previous-life `(sealed act → consequence)` pair, one emphasized (UX-R7); **no** deeper attribution; not the earned climax |
| Confirmed connection | Origin life, dated original sealed act **in its original wording** (C-2), and the ordered evidence path (C-3); 朱 (UX-R5); persistent across every appearance and across resume |
| Single ending invitation (D-06) | At most one pre-revealed still-shaping legacy, identified separately in observation data |

Glyphs: ⟜ = echo, ❧ = legacy — **trace kinds, not stages.** State is carried by an
added line / revealed annotation, never by swapping the glyph. Colour: ink for
selection and promise; 朱 only for a confirmed past-life connection.

Temporal coordinate (UX-R4): horizontal = year, strata depth = historical order;
the same coordinate for one event survives from its act-record through the time
surface, the digest, history, and the trace.

**Verification obligation** (from review §11): every check runs against the
*actual reached prefix*, not the fully-replayed world — because a full replay
already knows what will happen and can leak it. Before confirmation, no older-life
founder identity on any surface; after confirmation, its evidence is consistent
everywhere; inspection cannot commit; a keyboard event cannot both turn a page
and seal; an old choice cannot be re-executed; every drawn causal link is a real
edge; multiple contributors are not shown as one; same-seed / different-choice
books never share reveals (`v1_client_state_spec.md` CS-2).

---

## 4. Required ADR / spec amendments

### ADR-005 (new) — the geographic Map is deferred past v1

- **Decision.** P-11 (the geographic Map spread) is removed from the v1 MUST set.
  The "what changed while I was gone" beat is delivered by the P-10 rebirth digest
  and the C1 time surface. The direction §4 minimum bar — "the player can see at
  least one change their past life caused" — is met by those two surfaces.
- **Rationale.** Every causal node in the current engine is placeless
  (`location_id` `None`, 0/301 across five seeds). A map plate on generated worlds
  would be invented geography, which `ADR-001`'s dual-canon boundary and the
  definition's Principle 1 forbid.
- **Supersedes / amends.** `ADR-001` §4 ("map" in the illustration minimum);
  `design_v1_direction.md` §4 Must Have, §7, §9 deliverable 7, §10 R-D;
  `v1_ux_spec.md` P-10 right page and P-11.
- **Re-open gate.** W-1 (a spatial axis in worldgen). Not a date.
- **Status.** Needs **owner ratification** — it is the one real scope reduction.

### ADR-004 erratum (non-decisional)

Add a one-line correction: 横書き is the v1 baseline on the
unbounded-English-proper-noun evidence (`ADR-004`:29–36); the ADR-003
cross-reference is not authorization for an English-content v1; v1 player-facing
copy is Japanese. ADR-004's decision is unchanged. Owner is **informed**, not asked.

### D-4 amendment (visual language SoT — Design-Lead ratifiable per the I-0 process)

朱 = confirmed past-life connection (was: still-shaping). Plus the D-03/D-04
surface-scope extension in `v1_ux_spec.md` §5 to name every surface. Owner is
**informed**; can be sent back as gating if the owner wants to hold 朱 semantics.

### SoT doc corrections (no decision, apply with the ledger)

Delete ◦ from `v1_ux_spec.md` §4/§5 and tutorial asides; stamp roadmap/exec-plan
August 2026 dates as historical; the inspect/select/commit split, C-2/C-3/C-6
contract fields, UX-R4 encoding wording, UX-R7 one-emphasis rule, and the A-1 UI
carve-out are reconciliations of already-accepted intent.

---

## 5. The next implementation unit — the **Discovery Vertical Slice** (DVS)

Replaces "the next increment". **A design object for owner review, not an
authorization to implement.** One complete playable sequence on real generated
data:

> readable choice → recorded act → death → years → return → later investigation
> → ending → reopen

### Start state (entry conditions — all must hold before build)

1. The uncommitted I-1b/I-2/I-3 working tree is committed (or rebased in) as the
   base: typed six-beat stream, entry leaf (P-05/P-07), C1 time surface, P-10
   digest.
2. The §2 ledger is merged into the SoT docs; **ADR-005 is ratified**; no
   interface teaches a removed feature (◦, map-as-MUST, 朱-as-still-shaping,
   hidden-only hold).
3. One small set of real generated-world choices + consequences has authored
   **Japanese** presentation copy satisfying the choice-content contract (C-1);
   the exact sealed-act wording is retained for later quotation.
4. Engine untouched: the 8 frozen goldens + chronicle `aa4c67a416178e92` +
   replay-transcript `98bea8622c686d8e` byte-identical
   (`v1_implementation_roadmap.md` DoD-2). No RNG / worldgen / canonical-recipe
   change.

### Required contracts (must be specified and verified before or with the build)

| ID | Contract | Home |
|---|---|---|
| **C-1** | Choice-content: target name, known role/affiliation, current condition, immediate action — every clause sourced in reached world data; a missing world fact is escalated as a content/engine issue, never invented | `play/beats.py` + presenter/app seam |
| **C-2** | Sealed-act identity: original displayed label + text for every sealed act, carried on the digest line and on `Recognition`, stable across surfaces and resume | `play/beats.py` (`BeatRecorder._sealed`) + seam |
| **C-3** | Ordered causal path: a concrete list of existing edges consequence→origin, the original act where recoverable, and an honest alternate-cause indication; ancestor count is never the path | P18 / `app` trace composition over `trace_to_roots` |
| **C-4** | Discovery-state surface: the §3 enum honoured identically by entry, time surface, digest, history, trace, and resume; SR text + focus == glyph meaning | `client/web/*.js` + renderer specs |
| **C-5** | Persistence (minimum D-6 subset): atomic save of `{sealed inputs, reveal set, cursor}`; exact resume; canonical-hash trust gate | new `chronicle_forge` client-persistence module (per ADR-002) |
| **C-6** | Autonomous / authored separation: a flag on every displayed act line; the Hand is reserved for sealed acts and confirmed recollections | `play/beats.py` (`Change.sealed` exists) + renderers |

### End state (exit criteria)

- **One generated seed** plays end-to-end through all eight beats **including a
  quiet interval** (a life with no juncture and/or an empty-echo skip), no crash,
  no fabricated content.
- **Readable choice**: a fresh reader can state what each option *does now*
  (target + action) before any outcome; every factual clause has a world-data
  source.
- **Recorded act**: the sealed act is written to the entry in the Hand and
  persisted (C-5).
- **Death → years → return**: death closes with a dated factual passage and no
  grade; C1 uses the UX-R4 encoding; return shows the changed present, then one
  delivered `(sealed act → consequence)` line, further lines on request (UX-R7).
- **Later investigation**: from one ordinary historical consequence, an
  accessible inspect path (button + keyboard + optional hold) reaches the earlier
  life and its **original sealed act in the original wording** (C-2), via a real
  ordered edge path (C-3); player-choice / autonomous / contributing-cause are
  visually distinct (C-6).
- **Ending**: one authored historical closing passage grounded in the world, one
  substantiated connection inviting a trace, two actions **「歴史を読み返す」 /
  「本棚へ」**; if the run has no still-shaping legacy, another traceable
  contribution is used, and if none exists the ending closes honestly and records
  the content-gate miss.
- **Reopen**: quit/resume restores sealed choices, reveals, and cursor exactly;
  one confirmed trace survives the reopen; same-seed / different-choice books
  cannot share reveals.
- **Consistency**: the §3 discovery-state representation is identical across
  entry / time surface / digest / history / trace / resume, verified against the
  reached prefix.
- **Change budget**: nothing outside `client/web/*`, `play/beats.py` (+ its app
  seam), and the new client-persistence module; `reporting/` byte-identical; each
  contract extension carries its own focused verification.

### Mapping to the old I-4 / I-5 / I-6 phase order

| DVS piece | Old phase(s) | Disposition |
|---|---|---|
| current life + recorded act + entry archive | I-2 (done) + **read-only slice of I-6** | I-2 kept; pull read-only past + C-5 minimum forward from I-6 (UX-R8) |
| years + return + digest emphasis | I-3 (done) | I-3 kept; digest gains C-2 + the UX-R7 one-emphasis rule; C1 encoding fixed (UX-R4); founder-name guard (UX-R3) |
| geographic Map (P-11) | I-3 roadmap line / direction §4 | **retired from v1** → ADR-005; W-1-gated |
| one investigation + ending + reopen | I-4 (P-12/13/14/15 + trace + P18 lens) | I-4 **scoped down** to one trace thread on one seed, built on C-3; P18 `steps` demoted to a summary |
| tutorial branches, generated variation, long text, target runtimes | I-5 + parts of I-7 | deferred to **after** the slice |
| a11y floor (reduced motion, scaling, keyboard, skip) | I-7 | **pulled forward** into the slice baseline (UX-R9) |
| curated seed shelf, full save/resume, epithets | I-6 | full version stays **post-slice**; only the C-5 minimum is in the slice |

### Disposition of I-1b / I-2 / I-3

- **I-1b (typed beat stream + C1 surface) — KEEP.** The six-beat stream is the
  read-model. **Modify:** C1 renderer takes the UX-R4 encoding wording and a
  discovery-state guard on captions (UX-R3). `strings.js` remains the copy SoT.
  No structural change.
- **I-2 (life loop / entry leaf / shelf) — KEEP, MODIFY.** **Add:** a read-only
  archive of prior decisions during play + the 「今の頁へ」 return + C-5 minimum
  persistence. The "entry offers no flip" rule (`design_v1_i2_life_loop.md`:65)
  is replaced by "navigation ≠ commitment; past options readable but inert."
- **I-3 (rebirth digest P-10) — KEEP, MODIFY.** **Keep** the `(act →
  consequence)` join and SP-1. **Add** C-2 (original sealed-act wording), the
  UX-R7 one-emphasis rule, and the UX-R3 guard so no older-life founder is named.
- **P-11 map (the third item in I-3's roadmap wording) — RETIRE for v1**
  (ADR-005).
- Nothing in the three increments is discarded; all three are additive-compatible
  with this baseline.

---

## 6. Owner decisions that genuinely gate implementation (the only ones)

Everything not on this list — ◦ deletion, roadmap de-dating, the ADR-004 erratum,
the UX-R4 encoding wording, the inspect/select/commit split, the C-2/C-3/C-6
contract fields, the autonomous/authored separation, the A-1 UI carve-out — is
reconciliation of already-accepted intent and proceeds as SoT-doc amendments
without a fresh gate.

1. **Ratify ADR-005** — demote the geographic Map from a v1 MUST to a W-1-gated
   deferral. This is the single real scope reduction; it edits `ADR-001` §4,
   `direction` §4/§7/§9/§10, and `v1_ux_spec.md` P-10/P-11.
2. **Approve the sequencing pull-forward** — a minimum D-6 persistence + read-only
   archive slice ahead of I-6, and the a11y baseline ahead of I-7, both into the
   Discovery Vertical Slice.
3. **Ratify (or hold) the 朱 re-meaning** — 朱 = confirmed past-life connection,
   replacing D-4's 朱 = still-shaping, together with the D-03/D-04 surface-scope
   extension. Non-gating if delegated back to the Design Lead.
4. **Confirm the dual-canon reading** — authored *Japanese presentation
   templates* over real engine facts (with **no** authored historical events) are
   acceptable for generated worlds. Astra assumes yes
   (`design_v1_uiux_review.md`:240–241); a one-word confirmation is wanted because
   it sits on the ADR-001 non-negotiable boundary.

No implementation begins until items 1 and 2 are answered.
