# Chronicle Forge v1 — Client State Spec (D-6)

Status: **Draft for Design Lock (7/23).** Deliverable D-6 of I-0. Authority
order: this doc is subordinate to `design_v1_definition.md`, `design_v1_direction.md`,
and `v1_ux_spec.md`; it *implements* their state requirements and invents no
UX. Owner-ratified ADRs it must honor: ADR-001 (Dual Canon, ◦ cut, Must-only),
ADR-002 (pywebview), ADR-003 (Japanese-first — irrelevant to this doc, which is
mechanism only, but the store carries no player copy).

Scope: the **client-side persistent state** for one book (world) — everything
the client must remember so that (a) reveals are permanent within a world
(D-04), (b) quit/resume returns to the *exact* page state left (UX §3.2), and
(c) canonical world data is never mutated (DoD-6). It defines the state model,
the reveal-identity mechanism, the enumerated resumable states, write-through
timing, storage format, versioning, and the DoD-6 verification surface.

This doc does **not** cover: engine truth (frozen), the recipe/replay contract
(inherited, see below), page layout or copy (UX spec / voice guide), or the
standard-world shelf (D-5).

> **2026-09-08 baseline ratification.** The Astra UI/UX review's change ledger is
> **adopted** as [`design_v1_uiux_baseline.md`](design_v1_uiux_baseline.md).
> Binding here:
> - **UX-R8** — a **minimum** of this spec (atomic `{sealed inputs, reveal set,
>   cursor}` + exact resume + the canonical-hash trust gate) moves *forward* into
>   the Discovery Vertical Slice; it is no longer deferred to I-6. Read-only past
>   is available **during play**, and navigation is separate state from commitment.
> - **UX-R2** — inspection is an overlay state that never selects or commits.
> - **UX-R3** — the reveal `surface` tag must also cover the C1 time surface, so
>   audits can assert D-03/D-04 there. Checks run against the reached prefix.
> - **UX-R6** — a confirmed reveal must carry enough to re-render the origin's
>   **exact sealed-act wording** (C-2) after resume.
> - **ADR-005** — P-11 map state is removed.

---

## 1. The two-canon separation (why there are two stores)

Chronicle Forge already has one save mechanism, inherited and frozen:

- **Canon store = the Recipe.** A world *is* `Recipe(seed, max_year, mode,
  inputs)`. `app.explore(recipe)` replays it byte-deterministically into a
  `World`, over which the P10–P14 lenses read. The recipe pins `engine_version`;
  a version mismatch **refuses** replay (inherited invariant). Nothing the client
  does may change how a world is grown or what it contains.

The book client adds exactly one new persistent thing:

- **Client store = Reveal + Cursor.** What the *player* has uncovered and where
  they are reading. This is UI progress over a fixed world, not world data. It
  is additive, per-book, and disposable: deleting it loses the player's
  discoveries and reading position but **never** the world (the recipe regrows
  it identically).

**Invariant CS-1 (no write-back).** The client store is write-only from the
client and read-only to the engine. No code path writes reveal/cursor state into
`World`, `Recipe`, the lens DTOs, or any golden-pinned surface. The id-free
boundary of the app layer (`contracts.py`) is unchanged; the client store lives
*below* that boundary, in a new `chronicle_forge` client-persistence module, and
is never surfaced through a view DTO.

**Invariant CS-2 (reveals bind to the canonical world, not to engine+seed).**
A reveal set is trusted **only** against the exact canonical world it was earned
in, identified by a **Canonical Hash** over the *full* recipe — not merely
`engine_version` or `seed`. `engine_version` alone (and even
`engine_version + seed`) does **not** identify a world: two books with the same
seed but different sealed choices are genuinely different worlds, so a raw-id
reveal from one must never be interpreted against the other (that would let a
mark point at the wrong fact — a D-08 violation). See §3.3 for the exact hash,
the append-only correctness argument, and the trust gate. Consequence: the
reveal store is co-invalidated with the recipe by *any* change to the world
identity (engine bump, or a different/edited recipe), not just an engine bump.
There is no state in which reveals point at a world that does not reproduce them.

---

## 2. What one book's state is

A book on the shelf (UX P-01) persists as one **BookState** record:

```
BookState
├─ schema_version        client-store schema (this doc), NOT engine_version
├─ engine_version        copied from the recipe; one field *inside* canonical_hash
├─ canonical_hash        H(engine_version, seed, max_year, mode, inputs) — the
│                        identity of the exact world as grown so far; rewritten
│                        atomically with the recipe on every Seal (§3.3, CS-2)
├─ book_id               stable local id for the shelf slot (client-minted UUID)
├─ recipe                the canon store (seed, max_year, mode, inputs)  ← grows in play
├─ status                UNFINISHED | FINISHED
├─ reveals               RevealSet — the set of earned/delivered reveals (§3)
├─ cursor                Cursor — exact resume position (§4)
└─ meta                  created_at, last_opened_at, display_title (earned, e.g.
                         "A Chronicle of Fire")
```

Notes:

- `recipe.inputs` **grows during play**: each `I-04 Seal` appends the sealed
  option to `inputs`. The recipe is thus both the in-progress save and the
  finished save — there is no separate "in-progress world" format. Resuming an
  unfinished book replays `inputs` to the current head, then continues.
- `status` flips to `FINISHED` when P-15 is reached (the book closes; the shelf
  shows its spine + a new empty slot, UX §3.2 P-15 row). A finished book is
  re-openable read-only; its recipe never changes again, but its **reveal set may
  still grow** (revisiting a finished world and tracing/holding still earns
  reveals — D-04 permanence applies forward, never backward).
- `book_id` is client-minted and local; it is *not* derived from world content,
  so two books from the same seed are distinct shelf entries (the empty-slot
  replay intent, UX §3.5 note).

---

## 3. Reveal identity — how a reveal is keyed durably

The central mechanism. A "reveal" is the transition of one attribution from
*withheld* (D-01) to *shown* (Confirm), earned by player input (D-05) or
delivered in the recency window (D-03). The client must record *which*
attributions are revealed so the state is permanent (D-04) and survives resume.

### 3.1 The reveal key

**A reveal is keyed by the stable engine coordinate of the attribution it
uncovers.** Concretely: the causal attribution a mark points to resolves, on
replay, to a specific engine element (the `CausalNode` / heritage attribution
with its `planted_by_life_id`). Because replay is byte-deterministic under a
pinned `engine_version`, that coordinate is **reproducible**: the same recipe
always yields the same node, so the same key always points at the same fact.

```
RevealKey = (surface, engine_coord)
  surface     ∈ { S02_HOLD, P10_DIGEST, P14_TRACE, P12_SEED }   (how it was earned)
  engine_coord = the stable identity of the attributed node
                 (raw engine id; internal to the client store only)
```

The raw engine id is only ever valid **within one canonical world**. It is
*not* self-identifying: the same integer means different facts in different
worlds. So the reveal store is only trustworthy when paired with a proof that the
recipe still describes the world those ids were minted in — that proof is the
Canonical Hash gate (§3.3). Given that gate, the raw id is the right *intra-world*
key:

- It is **stable under replay** of the *same* recipe, and, thanks to the
  append-only/immutable-past property (§3.3), stable as the recipe grows forward.
- It stays **internal**: the reveal store is below the app boundary and is never
  emitted through a lens DTO or golden surface, so no golden hash and no id-free
  contract is affected (Invariant CS-1).
- The alternative — a content-addressed coordinate `(life_ordinal, surface,
  in-surface index)` — is *derivable* from the same replay and is the fallback if
  we later want the store to survive an engine bump that preserves semantics. For
  v1 we do **not** need cross-version reveal survival (a bumped engine reprints
  the whole book), so the simplest stable key wins. **Open Q-CS-1** records the
  content-address option for post-v1.

### 3.3 The Canonical Hash and the trust gate

**A reveal set is trusted iff the recipe it is stored with still hashes to the
book's recorded `canonical_hash`.** This is the binding CS-2 requires: reveals
are pinned to the *identity of a canonical world*, not to engine version or seed.

```
canonical_hash = H( engine_version ‖ seed ‖ max_year ‖ mode ‖ inputs )
```

- `H` is a stable digest (e.g. SHA-256 over the recipe's canonical JSON, the same
  serialization the recipe is saved with — a pure client-side helper
  `canonical_hash(recipe)`; **it adds no field to `Recipe` and no code to the
  engine**, so no engine golden moves — Invariant CS-1).
- All five recipe fields are included. `engine_version` is thus *one input among
  five*, not the whole gate: same-seed/different-`inputs` books produce different
  hashes and can never share a reveal set; an edited or swapped recipe fails the
  gate and its reveals are discarded rather than silently mis-rendered (D-08
  protection).

**Trust gate (on open / on load).** Recompute `canonical_hash(recipe)` from the
BookState's own recipe. If it equals the stored `canonical_hash`, trust the whole
reveal set; otherwise **discard the reveal store** (the world it described is not
this one) and open the book with an empty reveal set. The engine's existing
`engine_version` replay refusal (`EngineVersionMismatch`) still fires first for a
version bump; the Canonical Hash gate additionally catches every *other* identity
change (seed, params, inputs, corruption) that the version gate cannot see.

**Correctness under forward growth (why refreshing the hash on Seal never
over-invalidates).** Sealing appends one input; the past is immutable (UX §3.1
spine rule — no choice is unmade), so for any earlier reveal earned when the
recipe was a prefix `inputs[:k]`, replaying the longer `inputs` reproduces
`inputs[:k]`'s lives **byte-identically** and mints the *same* node ids. Every
already-earned reveal therefore still resolves correctly under the grown recipe.
So we may refresh `canonical_hash` to cover the full current `inputs` on every
Seal (in the same atomic write, §5/§6) and still trust the whole accumulated
reveal set. The gate rejects only *non-prefix* changes — a different world — which
is exactly what must be rejected.

**Atomic coupling.** `canonical_hash` and `recipe` are always written together in
one atomic `BookState` replace (§6). They can never diverge in a completed write;
a torn write leaves the prior consistent pair (CS-9). The hash is therefore a
faithful witness of "which world these reveals belong to" at all times.

### 3.4 Reveal set operations

### 3.2 What is *not* stored per reveal

- No copy, no rendered Hand text, no numbers. The reveal set stores only *that*
  key X is uncovered; the client re-renders the reveal grammar (S-02 print→Hand,
  UX §5) from the live replayed world at display time. This keeps the store tiny
  and keeps all player-facing text on the Japanese copy path (ADR-003), never in
  the save file.
- No "hint" state. Marks (D-02) are a pure function of the world (D-08: mark
  present ⇔ connection real); they are recomputed on every render and are never
  persisted. Only *Confirms* (reveals) are state.

### 3.3 Reveal set operations

```
reveals.add(key)      idempotent; first add is the only observable transition
reveals.has(key)      drives render: Hand shown vs. withheld
reveals.count()       feeds nothing canonical; UI-only (ADR-005 removed the map)
```

**Invariant CS-3 (monotone).** The reveal set only grows within a book's
lifetime. There is no "un-reveal". D-04 (reveals permanent once earned) is
literally this monotonicity. Flip-back (UX §3.3) and re-reading (P-13) call only
`has`, never `add` — reading never earns a reveal (D-04, "no passive confirms").

**Invariant CS-4 (delivered vs earned both land here).** P-10 digest lines
(delivered, D-03, last-life-only) and S-02/P-14/P-12 (earned) all write the same
reveal set with a distinguishing `surface`. The `surface` tag exists so audits
can assert D-03 (delivered reveals are last-life only) and D-05 (earned reveals
followed player input), and so P-11's map can style delivered-recent vs.
old-revealed marks (UX P-11 "faded unlabeled marks for revealed-but-old").

---

## 4. The cursor — resume returns *exactly*

UX §3.2 requires every resumable transition to "return to the exact page state
left". The **Cursor** captures that position. It is a discriminated union keyed
by page, carrying only the intra-page state needed to re-enter identically.

### 4.1 Resumable-state enumeration

Every page/state and the cursor payload that makes resume exact. DoD-6 names two
hard cases explicitly (**mid-juncture selection**, **mid-trace**); both are
first-class below.

| Cursor page | Payload (beyond page id) | Resume behavior |
|---|---|---|
| P-01 Shelf | — | Shelf; no book open |
| P-03 Front Matter | — | Re-enter front matter |
| P-04 Life Opening | `life_ordinal` | Re-open the life's opening |
| P-05 Life Page | `life_ordinal`, `reading_offset` | Return to the wet ink at the read position |
| **Flipped-back (read-only past)** | `under: Cursor` (the unresolved state), `archive_offset` | **Baseline UX-R8.** Reading an earlier entry is *navigation only*: past options are inert, nothing re-executes, and reading earns no reveal (D-04). Resume restores the **underlying** unresolved cursor — `U-nowpage`「今の頁へ」 is always available and returns page + selected-not-sealed option + focus + scroll exactly |
| Inspection open (overlay) | `under: Cursor`, `inspect_target` | **Baseline UX-R2, non-persistent.** Inspection never selects and never commits, so it is *not* written through; on resume the underlying cursor re-opens with the overlay closed |
| **P-06 Juncture** | `life_ordinal`, `juncture_index`, `selected_option?` | **Mid-juncture:** a *selected-not-sealed* option (I-03) is restored faintly-previewed in the Hand, **unsealed**. Nothing is committed to the recipe until I-04 Seal. |
| P-07 Outcome Passage | `life_ordinal`, `juncture_index` | Re-show the sealed outcome |
| P-08 Death Page | `life_ordinal` | — |
| P-09 Passage of Years | `from_life_ordinal` | Non-resumable target: on resume, snap to the P-10 that follows (P-09 is a transition, has no ribbon, UX I-08/I-09 exclusions) |
| P-10 Rebirth Spread | `life_ordinal` (the newborn) | Re-show the delivered digest; its reveals are already in the set (added when first shown) |
| ~~P-11 Map Spread~~ | — | **Removed — ADR-005.** No map state exists in v1 |
| P-12 Final Chronicle | — | Re-enter; the single D-06 seeded confirm is already in the reveal set |
| P-13 Chronicle Reading | `reading_offset` | Return to reading position |
| **P-14 Trace** | `origin_event_key`, `steps_revealed` | **Mid-trace:** the chain is re-drawn with exactly `steps_revealed` links shown (each I-07 step is one revealed link, D-05); the next "what came before?" continues from there. Each already-revealed origin card is in the reveal set. |
| P-15 Closing | — | On resume, treat as FINISHED → open to P-01 Shelf |
| S-01 Ribbon (overlay) | `under: Cursor` | Overlay over a page; resume restores the *underlying* cursor and re-raises the ribbon (UX §3.2 "resume returns exactly") |

Rules:

- **CS-5 (unsealed selection is client-only).** A restored P-06 `selected_option`
  is **never** in the recipe. Only Seal (I-04) appends to `recipe.inputs`. So a
  crash between select and seal loses at most one *unsealed* selection — the world
  is unchanged and re-selecting is free. This preserves determinism: the recipe
  only ever contains sealed, irreversible acts (UX §3.1 spine rule).
- **CS-6 (transitions are not resume targets).** P-02 (cover ritual) and P-09
  (passage of years) have no ribbon (I-09 excludes P-02/P-09) and are not saved
  as a resting cursor; if a quit is requested during them, the cursor is the
  nearest stable page (P-03 after P-02; P-10 after P-09).
- **CS-7 (flip-back is not a cursor move).** Flipping back (I-02) is a transient
  read view with a persistent "return to wet ink" tab (UX §3.3). The saved cursor
  is always the **wet-ink head**, never a flipped-back page; resume returns to the
  head, matching "no choice can be unmade" and "reading is not progress".

### 4.2 Map/overlay tabs

The map tab (I-08) exists from the first rebirth onward (UX §8). Opening the map
from a page pushes an overlay cursor (`P-11` with `under`) exactly like the
ribbon; closing it pops back. Overlays never replace the underlying resting
cursor on disk until an actual page transition occurs (§5).

---

## 5. Write-through timing (when state is saved)

**CS-8 (save is invisible and safe).** There is no explicit "save" verb; "close
the book" (I-09) is a *save-safe exit*, not the only save point. The client
writes through on the events below so that a crash at any moment loses no earned
reveal and no sealed act.

Write-through points (each is an atomic replace of `BookState`, §6):

1. **On Seal (I-04)** — after `recipe.inputs` is appended. This is the only
   canon-mutating event; it must be durable before the outcome page (P-07)
   renders. (Ordering: append input → persist → advance cursor to P-07.)
2. **On reveal add** — S-02 (I-05 hold completes), P-10 digest shown, P-14 step
   (I-07), P-12 seeded confirm. Persist the grown reveal set before the reveal
   animation is acknowledged as permanent.
3. **On resting-cursor change** — arriving at any page in the §4.1 table that is
   a resume target (not a transition). Cursor writes are cheap and may coalesce
   within an animation frame, but must be durable before the next input is
   accepted.
4. **On close-book / quit (I-09)** — flush current cursor (including a
   mid-juncture `selected_option` and mid-trace `steps_revealed`) and mark
   `last_opened_at`.
5. **On P-15** — set `status = FINISHED`, cursor → shelf.

**CS-9 (crash equivalence).** For any interruption (crash, power loss, kill),
resume state equals the last completed write-through. Because Seal persists
before P-07 and reveals persist before their animation, the worst loss is: an
in-progress hold that had not completed (no reveal earned — hypothesis stays the
player's, which is exactly the intended I-05 semantics), or an unsealed P-06
selection (CS-5). No sealed act and no earned reveal is ever lost.

---

## 6. Storage format, location, atomicity

- **Format:** JSON, one file per book, `schema_version`-tagged. Human-diffable,
  matches the repo's existing recipe/JSON posture. No player copy inside (§3.2),
  so no encoding/locale concerns from ADR-003.
- **Location:** an OS-appropriate per-user app-data dir (e.g.
  `%APPDATA%/ChronicleForge/books/<book_id>.json` on Windows,
  `$XDG_DATA_HOME/chronicle-forge/books/…` on Linux — ADR-002 targets both).
  Exact path is a packaging detail (I-7), not a Lock blocker; the module exposes
  a single `books_dir()` seam.
- **Atomicity:** write-through is **write-temp-then-rename** (atomic replace) so a
  crash mid-write leaves the previous good `BookState` intact (satisfies CS-9).
- **Shelf index:** P-01 lists books by scanning `books_dir()` and reading each
  `meta` + `status`; no separate index file to fall out of sync. (If scan cost
  matters later, an index is an additive cache, not a source of truth.)
- **Versioning:** `schema_version` is this doc's client schema, **independent of
  `engine_version`** (mirrors `contracts.SCHEMA_VERSION` being decoupled from
  `ENGINE_VERSION`). A client-schema bump ships a migration. World-identity
  changes are handled by the Canonical Hash gate, not by `schema_version`: an
  engine bump fails both the recipe's replay-refusal *and* the hash gate; any
  other identity change (seed/params/inputs/corruption) fails the hash gate alone
  (§3.3, CS-2), and the reveal store is discarded on open.

---

## 7. DoD-6 verification surface (the state-machine test suite)

DoD-6 is met by a state-machine test suite asserting the invariants above.
Named, repeatable checks:

| Check | Asserts | Invariant |
|---|---|---|
| T-CS-permanence | A reveal earned in life N is still present on flip-back, on a later life, and after quit/resume | D-04, CS-3 |
| T-CS-no-passive | Reading (P-05 flip-back, P-13) and P-14 re-view call `has` only; reveal set unchanged | D-04, CS-3 |
| T-CS-resume-exact × pages | For every resume-target row in §4.1, quit→resume returns the identical cursor+payload | UX §3.2 |
| T-CS-mid-juncture | Select (I-03) → quit → resume restores the unsealed selection; `recipe.inputs` unchanged; Seal then appends exactly once | CS-5, DoD-6 |
| T-CS-mid-trace | Reveal k of n trace links → quit → resume shows exactly k; next step continues to k+1; k origin cards in reveal set | CS-4, DoD-6 |
| T-CS-no-writeback | After a full play+trace session, the world replayed from `recipe` alone is byte-identical to the world during play; all 8 engine goldens + chronicle `aa4c67…` + transcript `98bea8…` untouched | CS-1, DoD-2 |
| T-CS-canon-bind | A BookState whose recipe no longer hashes to its stored `canonical_hash` (engine bump, or any seed/param/inputs edit/corruption) discards its reveal store on open; no reveal survives pointing at a non-reproducing world | CS-2, §3.3 |
| T-CS-cross-world | Two books, **same seed** but different sealed choices, have different `canonical_hash`es; pairing one book's reveal set with the other's recipe fails the gate and reveals nothing (a mark never points at the wrong fact) | CS-2, D-08 |
| T-CS-grow-keeps | Refreshing `canonical_hash` on each Seal never invalidates reveals earned at an earlier `inputs` prefix; all remain resolvable after the append | CS-2, §3.3 |
| T-CS-crash | Kill after Seal-persist but before P-07 → resume at P-07 with the sealed input present; kill mid-hold → no reveal, hypothesis intact | CS-8, CS-9 |
| T-CS-atomic | Interrupt mid-write → previous BookState loads intact | §6 atomicity |
| T-CS-monotone | Reveal set never shrinks across any sequence of inputs | CS-3 |

These run in CI alongside the engine goldens; none of them may move an existing
golden hash (the store is additive and below the boundary).

---

## 8. Open questions carried to Lock

- **Q-CS-1 (post-v1 reveal survival).** Should the reveal key be the raw engine
  id (simplest, co-invalidated — the v1 choice) or a content-addressed
  coordinate `(life_ordinal, surface, in-surface index)` that could survive a
  semantics-preserving engine bump? v1 needs neither, but recording the
  content-address recipe now costs nothing and de-risks a future migration.
  *Proposed for Lock: accept raw-id for v1, note the content-address fallback.*
- **Q-CS-2 (finished-book reveal growth).** Confirm the ruling in §2: revisiting a
  FINISHED book can still grow its reveal set (D-04 forward-only). No canon
  change, so this is safe; flagged only because it means a FINISHED book's file
  is not immutable. *Proposed for Lock: yes, reveals grow forever; recipe is
  frozen at FINISHED.*
- **Q-CS-3 (books_dir on packaged builds).** Exact per-OS data dir + first-run
  creation is an I-7 packaging detail; only the `books_dir()` seam is needed at
  Lock. *Not a Lock blocker.*
- **Q-CS-4 (multi-book concurrency).** v1 opens one book at a time (single-window
  pywebview, ADR-002). The store assumes a single writer; a file lock is
  unnecessary for v1. *Proposed for Lock: single-writer assumption, no lock.*

---

## 9. Summary for reviewers

- One new persistent thing: a per-book **Reveal + Cursor** store, additive and
  below the app boundary. Canon stays the frozen recipe.
- Reveals are keyed by the stable engine coordinate that replay reproduces, and
  the whole set is **bound to the canonical world identity via a Canonical Hash**
  over the full recipe (engine_version + seed + max_year + mode + inputs) — not
  engine version or seed alone (CS-2, §3.3). So they are permanent (D-04),
  discarded the moment the recipe describes a different world (D-08 protection),
  and never leak into any id-free view or golden.
- Every UX §3.2 resume target — including mid-juncture selection and mid-trace —
  has an exact cursor payload; unsealed selections never touch the recipe.
- Write-through on Seal, on reveal, on resting-cursor, and on close makes crash
  loss impossible for sealed acts and earned reveals.
- DoD-6 is a named state-machine suite that also re-proves DoD-2 (no golden
  moves). Four open questions, all with proposed Lock rulings; none blocks Lock.
