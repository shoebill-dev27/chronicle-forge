# Chronicle Forge v1 — JP Voice & Copy Style Guide (D-3)

Status: **Draft for Design Lock (7/23).** Deliverable D-3 of I-0 (execution
plan §130: *Voice & copy style guide, incl. UI-string inventory + epithet
table*). Opus draft; owner review required on the marked points. This is the
**anti-drift instrument for all shipped Japanese copy** — every future JP string
(tutorial and standard-world lenses) conforms to it, and the JP audit lane
(DoD-7) enforces it.

> **2026-09-08 baseline ratification.** The Astra UI/UX review's change ledger is
> **adopted** as [`design_v1_uiux_baseline.md`](design_v1_uiux_baseline.md).
> Binding here: **UX-R9** adds an explicit A-1 exemption for non-diegetic UI
> control labels (§4); **UX-R2** gives inspection a visible label `U-investigate`
> = 調べる (§8); **UX-R7** makes the P-10 digest one emphasized line with up to two
> more on request (§5 budget unchanged, ≤3 lines); **UX-R10** confirms ⟜/❧ only.

Authority: subordinate to `design_v1_definition.md` (North Star, 11 principles),
`design_v1_direction.md` (the historian as a specified character),
`v1_ux_spec.md` §5/§7 (discovery rules, the two voices), and **ADR-003**
(Japanese-first; the historian's voice is a specified character; second-person
audit; character budgets; name table). Binds together with **D-4** (typography):
D-4 sets characters-per-line; D-3 sets copy length and voice. Glyph inventory is
**⟜/❧ only** (ADR-001 §3 — the ◦ memory mark is cut; any ◦ in older SoT drafts
is superseded).

**Convention.** A point that is a genuine native-language/style judgment the
owner must make is tagged **`REVIEW_REQUIRED(owner)`**. Everything else is a
mechanical or already-ratified rule and is not an owner decision.

---

## 1. The two voices, in Japanese

The load-bearing device is the print/Hand contrast (UX §7). In Japanese it is
carried by **register and person**, reinforced by typeface (D-4):

- **Print — the Historian (印刷体 / 明朝).** Everything the *world* says: front
  matter, event passages, the chronicle, digests. A specified character:
  dry, factual, terse, occasionally quietly astonished but never sentimental
  (direction doc; Principle 1 "dramatize the telling, never the events").
- **The Hand — the Soul (手 / 手書き).** Everything the *player* did: the current
  life's entry, past sealed acts, S-02 reveals. First-person, plainer, warmer;
  the record of a self, not of a world.

Rule **V-1 (the contrast is register, not decoration).** The two voices must be
distinguishable **by reading register alone**, before typeface is perceived —
so a reader who cannot yet see the type still feels "world" vs "self." Typeface
(D-4) is the second, reinforcing channel, never the only one.

## 2. Register, person, tense

- **V-2 (Historian register).** Plain declarative chronicle register — no 敬語,
  no reader address. Recommended base: **常体（だ・である体）**, nominal and
  terse, past/perfective for events (…した／…であった), present for enduring
  states (…が残る／…と伝わる). *`REVIEW_REQUIRED(owner)`: ratify である vs. a
  more literary 文語調 tint for era headers/front matter — a native voice call.*
- **V-3 (Hand register).** First-person past, plain and unadorned; the soul
  records, it does not perform. Person pronoun for the self kept minimal
  (Japanese drops it); when needed, neutral. No 敬語.
- **V-4 (No second person outside Confirm).** This is the JP re-derivation of
  D-01 and the old "you/your" grep. The reader is addressed as **あなた／…の
  あなた** *only* on Tier-Confirm surfaces (P-10 digest, S-02 reveal, P-14
  origin card, P-12 highlight). Everywhere else — all print history, all Hand
  entries — there is **no 呼びかけ (second-person address) at all**; descended
  content reads as plain history (D-01). *`REVIEW_REQUIRED(owner)`: confirm あなた
  as the address pronoun (vs. 汝/君/お前 — register-loaded); recommend あなた for
  intimacy without archaism.*
- **V-5 (Astonishment is the world's, once).** The historian may show restrained
  wonder at scale/consequence (Emotional Arc), but rarely and never at the
  player. Budget: at most one "astonished" line per world surface set.

## 3. The Confirm reveal grammar (the single most important line)

UX §5 D-05 fixes the grammar: *the print stays, the Hand blooms underneath, and
one line names the origin* — English exemplar *"— your third life, who chose to
⟨act⟩."* Japanese template:

> **「——〈N〉度目のあなた、〈act〉を選んだ者。」**

- `〈N〉度目のあなた` = the attributing epithet (§7 epithet table).
- `〈act〉を選んだ者` = the sealed act, named as a **choice** — D-05's grammar
  names *who chose to ⟨act⟩*, the act itself, not merely its consequence.
- The em-dash opener (——) marks the register break into address.

*`REVIEW_REQUIRED(owner)`: ratify the exemplar phrasing and the …者 vs …あなた
tail — this line recurs at every earned recognition and is the emotional core;
it must be owner-authored.* Once ratified, every S-02/P-14/P-12 confirm uses this
one grammar (D-05 "always the same grammar").

## 4. Copy-audit rules (JP) — the DoD-7 rule set

The audit lane (local LLM / Haiku, ADR-003) runs these mechanically on every
shipped JP string; **zero waivers** (DoD-7).

- **A-1 (Second-person / 呼びかけ audit).** Flag any あなた／君／汝／お前 or
  imperative 呼びかけ appearing on a **non-Confirm** surface. Replaces the
  English "you/your" grep. (Enforces V-4 / D-01.)
  **A-1 exemption (2026-09-08, baseline UX-R9) — non-diegetic UI control labels.**
  The §8 UI-string inventory (記す／封じる, 調べる, その前には？, 続きから, 本を
  閉じる…) is **exempt** from A-1: these name an operation the player performs,
  they are not the historian addressing the reader. Diegetic prose — every page
  body, digest line, reveal line, aside — is **not** exempt. This is a rule, not a
  waiver, so DoD-7's "zero waivers" is unaffected. Anything outside the §8
  inventory that reads as an imperative still fails.
- **A-2 (Character budgets).** Every string ≤ its surface budget (§5). Counted in
  全角 characters; 半角 digits/Latin count as ½. Over-budget = fail (a page that
  needs more becomes two pages — UX §7).
- **A-3 (Glyph usage).** Only ⟜ and ❧ may appear as marks; any ◦ or other glyph
  in copy = fail (ADR-001). Marks are never named in body text and never carry a
  name/ordinal inline (D-02).
- **A-4 (Name-table conformance).** Every proper noun matches the ratified name
  table (§6) exactly — no ad-hoc coinage in copy. Unknown proper noun = fail.
- **A-5 (No fabricated attribution).** No copy attributes to a past life outside
  a Confirm surface, and no Confirm attributes deeper than its tier allows
  (P-10 digest = previous life only, D-03). (Enforces the tier boundary in prose.)
- **A-6 (Register separation).** Heuristic check that Hand strings are 常体
  first-person and Historian strings carry no 呼びかけ — flags voice bleed for
  human review. (Advisory, not a hard gate — voice is ultimately human-judged.)

## 5. Character budgets (per surface)

Budgets are **JP-character caps derived from D-4's line measure** (D-4 sets
全角 chars/line; these convert copy length). Numbers below are the design
targets; D-4 ratifies the exact per-line measure and any budget shifts follow it
mechanically.

| Surface | Budget (design target) | Notes |
|---|---|---|
| P-10 digest line | ≤ 1 measure line each, **≤ 3 lines total** | D-03 hard cap; each line one echo |
| P-06 option label | ≤ ~24 全角 | must fit one line at option size |
| S-02 / P-14 confirm line | ≤ 2 measure lines | the §3 grammar; the em-dash line |
| P-12 highlight | ≤ 2 measure lines | the single rubricated line |
| ✎ historian's aside | ≤ 2 measure lines | at most three exist (UX §8) |
| Era header | ≤ ~16 全角 | small-caps-equivalent; year range separate |
| Ribbon/menu string | ≤ ~12 全角 | UI inventory (§8) |

*Note (mechanical dependency — not an owner judgment): these budgets follow
D-4's ratified line measure, which the 縦書き/横書き decision affects; update them
mechanically once D-4 §2/§3 are ratified.*

## 6. Proper-noun policy and name table

ADR-003: canonical docs keep English names (repo policy); the JP voice guide
binds their Japanese renderings **once**, before any JP copy is written. Policy:

- **N-1.** Coined world/place names of the setting → **kanji coinage** (漢語)
  that reads as an old place-name; katakana only for names meant to feel foreign.
- **N-2.** Institution/heritage names (the ❧ legacy targets: Pact/Rule/Charter)
  → kanji, chosen to read as law/lore (…盟, …律, …憲章).
- **N-3.** Person names → kanji or kana per character register.
- **N-4.** One rendering per canon name, forever (A-4 enforces).

**Name table (TEMPLATE — entries are `REVIEW_REQUIRED(owner)`).** Every JP cell
is an owner-authored coinage; the English column is the structural canon. **The
tutorial's English names are themselves pending the DR revision pass** (Undermount
→ Wellmount, Aldis → Tavin, Brant Ford → Marle Ford — deferred), so the *rows*
below are the current canon and may be renamed upstream before the JP cells are
filled; fill the JP column only after DR-pass names are final.

| English canon (structural) | Kind | JP rendering |
|---|---|---|
| Brant Ford *(→ Marle Ford, DR-pass)* | place | `REVIEW_REQUIRED(owner)` |
| Undermount *(→ Wellmount, DR-pass)* | place (shrine city) | `REVIEW_REQUIRED(owner)` |
| Aldis *(→ Tavin, DR-pass)* | person (the witness) | `REVIEW_REQUIRED(owner)` |
| the Undercroft Pact | institution (❧) | `REVIEW_REQUIRED(owner)` |
| the Channel Rule / Stair Rule | institution (❧) | `REVIEW_REQUIRED(owner)` |
| era names (Imperial/Warring/Arcane/Golden Age) | era headers | `REVIEW_REQUIRED(owner)` |

Standard (generated) worlds emit English place/heritage names from the engine;
their JP rendering is a **transliteration/coinage rule**, not a fixed table
(generated names are unbounded). *`REVIEW_REQUIRED(owner)`: ratify the
generated-name rendering rule (romaji-katakana vs. on-yomi kanji coinage) — a
native call that sets the feel of every standard world's proper nouns.*

## 7. Epithet table (life signatures)

The Hand is "signed with ordinals" (UX §7); Confirm lines name the origin life by
ordinal, never by identity (D-02: no names/ordinals on hints, but Confirm *does*
attribute). JP forms:

| English | JP form (recommended) |
|---|---|
| your first life | 最初のあなた |
| your second life | 二度目のあなた |
| your third life | 三度目のあなた |
| your last life *(P-10 digest, prev-life)* | 前世のあなた *(or 一つ前のあなた)* |

*`REVIEW_REQUIRED(owner)`: ratify 最初のあなた／N度目のあなた and the P-10
"previous life" epithet (前世 carries Buddhist weight — intended or too strong?).*
This table is closed once ratified; no other life-signature phrasing ships.

## 8. UI-string inventory

All non-diegetic strings (ribbon menu S-01, glyph key, verbs, system lines). Each
is `REVIEW_REQUIRED(owner)` for final wording; the English gloss fixes meaning.

| ID | Where | English gloss | JP (draft — owner ratifies) |
|---|---|---|---|
| U-ribbon | S-01 | (menu title) | 栞 / メニュー |
| U-settings | S-01 | Settings | 設定 |
| U-glyphkey | S-01 help | Glyph key (one line each) | ⟜ = 過去の行いがここに響く／❧ = 築かれたものが今も立つ |
| U-close | S-01 | Close the book (save) | 本を閉じる（保存） |
| U-quit | S-01 | Quit | 終わる |
| U-newbook | P-01 | (empty slot) | 新しい世界 |
| U-resume | P-01 | (wet-ink tab) | 続きから |
| U-seal | P-06 | Seal | 記す / 封じる |
| U-investigate | P-05/06/13 + any historical consequence | Investigate (the visible inspect affordance — **primary** path, keyboard-reachable) | 調べる |
| ~~U-remember~~ | — | ~~(hold-to-remember affordance)~~ | **Superseded 2026-09-08 (UX-R2)** by `U-investigate`; the ~800 ms hold survives as an unlabelled optional gesture on the same target |
| U-nowpage | P-05/06/13 (while flipped back) | Back to the wet ink | 今の頁へ |
| U-reread | P-12 | Read the history again | 歴史を読み返す |
| U-shelf | P-12/15 | To the shelf | 本棚へ |
| U-follow | P-12/13 | Follow this thread | この糸をたどる |
| U-before | P-14 | What came before? | その前には？ |

Rules: the **glyph key is the only place a mark's meaning is written** (D-02); it
lives in S-01 help, one line each, ⟜/❧ only. **Amended 2026-09-08 (baseline
UX-R2):** inspection now has a visible, keyboard-reachable label (`U-investigate`
= 調べる). Teaching the *operation* is required; it reveals no answer. The hold
remains available as an optional convenience on the same target and carries no
label of its own.

## 9. Tone exemplars (one per surface)

Illustrative only — final copy is owner-authored; these fix *register*, not wording.

- **Front-matter aside ✎#1** (Historian, wonder): *「幾度も この世に還る魂に
  ついて、記録はただ一つを告げる——その手は、そのたびに変わる。」*
  (role seated, power unknown.)
- **P-10 digest line** (Delivered confirm, prev-life): *「前世のあなたが開いた
  丘は、いまや聖都となった。」* (⟜, one echo, ≤ its line.)
- **S-02 reveal** (Earned confirm, §3 grammar): *「——三度目のあなた、水の流れを
  変えることを選んだ者。」*
- **P-12 highlight** (Seeded, rubricated): *「そしてこの盟約は、いまも世界を
  かたちづくっている。」* (the one accent line.)

*`REVIEW_REQUIRED(owner)`: these exemplars set register targets; owner replaces
with authored copy. They are not shipped strings.*

## 10. Owner decision points (summary)

Genuine native-language/style judgments only (each tagged above):

1. Historian register ratification — である vs. 文語調 tint (V-2).
2. Address pronoun — あなた vs. alternatives (V-4).
3. The Confirm reveal-grammar exemplar (§3) — the emotional core line.
4. Name-table JP coinages (§6), after DR-pass names finalize.
5. Generated-name rendering rule (§6).
6. Epithet phrasing incl. 前世 weight (§7).
7. Final UI-string wording (§8).

Everything else (audit mechanism A-1..6, budgets §5 as a D-4 dependency, glyph
inventory, tier boundaries) is ratified rule, not an owner call.

## 11. Cross-check (no contradiction)

- **ADR-001**: ⟜/❧ only (A-3); no ◦; standard worlds emit engine names only (§6)
  — consistent (no authored overlay).
- **ADR-002**: strings are data rendered by the client; nothing here needs engine
  change; JP webfont concerns are D-4's — consistent.
- **ADR-003**: JP-first, historian-as-character, second-person→呼びかけ audit
  (A-1), word→character budgets (§5), name table (§6) — this doc *is* the ADR-003
  voice-guide obligation.
- **UX §5/§7**: V-4 = D-01; §3 grammar = D-05; A-5 = D-03; two voices = §7;
  glyph key placement = D-02 — consistent.
- **D-4**: budgets (§5) and register-vs-typeface (V-1) explicitly defer measure
  and faces to D-4 — complementary, no overlap.
- **D-5**: the three-tier delivery (Delivered/Earned/Seeded) is honored by the
  surface list in §4/§5 — consistent.
