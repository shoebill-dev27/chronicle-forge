# P9-2 Transcript Export — Detailed Design (For Review, test-first)

Status: **Design + failing tests submitted for review. No implementation, no
commit, no formatter.** Parent: `docs/design_p9_persistent_history.md` (approved).
Builds on P9-3 replay (`replay_transcript`, pushed at `e44fb28`).

## Scope

Export "the story I lived" as a durable, readable artifact — txt / Markdown /
JSON — so a run can be re-read outside a session. The artifact **stores the
transcript body** and **embeds the Recipe as a reference**, with metadata that
lets any consumer re-validate the stored text against regeneration.

Out of scope: any new prose (the transcript is P8/P7 verbatim via P9-3); styling
themes/HTML; persisting a transcript *as the save* (the recipe stays canonical —
see Decision 1).

## Decision 1 — Export saves the transcript, but it stays a non-authoritative cache

The reviewer's call: **the export stores the transcript text and embeds the
Recipe as a reference.** This is deliberately different from P9-3 (where the
transcript is regenerated and never stored) because the *purpose* differs:

- P9-3 replay = *re-experience*; the transcript is ephemeral, the recipe is the
  save.
- P9-2 export = *keep a readable copy*; the transcript text is the point, so it
  is written into the artifact.

Crucially, **authority still rests with the recipe.** The stored transcript is a
**cache**: the artifact carries `transcript_hash` and the embedded recipe, so a
consumer can regenerate (`replay_transcript(embedded_recipe)`) and confirm the
stored text matches its hash. A cache that disagrees with regeneration is stale,
not truth. This keeps P9-2 consistent with P9-3's "regeneration is canonical".

## Decision 2 — Three formats

| format | contents | audience |
|---|---|---|
| **txt** | metadata header lines + blank line + transcript body | plain reading |
| **md** | `#` title, metadata bullet list, the recipe as a fenced ```json``` block (replayable), `---`, then the transcript | readable + self-contained |
| **json** | `{"metadata": {…}, "recipe": {…}, "transcript": "…"}` | tooling / re-validation |

- The **recipe is embedded** fully in `md` and `json` (so the artifact is itself
  replayable); `txt` references it by `recipe_hash` only (txt is the human-reading
  copy, kept clean).
- All formats are **byte-deterministic** for a given recipe (sorted-key JSON,
  fixed layout, deterministic transcript) — re-exporting yields identical bytes.

## Decision 3 — Metadata

Exactly the reviewer's five fields, in a new `ExportMetadata` schema (not in
`models.py`):

```text
ExportMetadata:
  seed            : int    # recipe.seed
  engine_version  : str    # recipe.engine_version
  recipe_hash     : str    # sha256 of the canonical recipe JSON (sorted, compact)
  transcript_hash : str    # sha256 of the regenerated transcript
  world_hash      : str    # sha256 of world.model_dump_json()
```

- Hashes are **full sha256 hex** (64 chars). For seed42 they begin
  `world_hash = e62d8f2c…`, `transcript_hash = 98bea862…` — tying the export to
  the permanent golden guards.
- `recipe_hash` is over the **canonical** recipe form
  (`json.dumps(recipe.model_dump(), sort_keys=True, separators=(",",":"))`), so it
  is stable regardless of on-disk indentation.

## Architecture

- **`persistence/export.py` (new):**
  - `ExportMetadata` (pydantic).
  - `export_transcript(recipe, *, fmt) -> (artifact: str, meta: ExportMetadata)`
    — regenerate via `replay_transcript`, compute metadata, render the format.
  - `write_export(recipe, path, *, fmt=None) -> ExportMetadata` — infer `fmt`
    from the path extension (`.txt`/`.md`/`.json`) when not given; write; return
    metadata.
- Reuses **P9-3** `replay_transcript` (read-only) for the world+transcript.
- **Untouched (inviolable):** `models.py`, P6, P7, P8, P9-1 (`save`/`load`/
  `schema`/`version`), P9-3 (`replay`/`record`). `export.py` only imports them.

## API (signatures)

```python
ExportFormat = Literal["txt", "md", "json"]

class ExportMetadata(BaseModel):
    seed: int
    engine_version: str
    recipe_hash: str
    transcript_hash: str
    world_hash: str

def export_transcript(recipe: Recipe, *, fmt: ExportFormat = "md") -> tuple[str, ExportMetadata]
def write_export(recipe: Recipe, path, *, fmt: Optional[ExportFormat] = None) -> ExportMetadata
```

## CLI — proposal (open question, no failing tests yet)

The brief did not pin a CLI for P9-2 (it did for P9-3). **Proposed**, additively
on the play CLI: `--export FILE`, format inferred from FILE's extension,
combinable with the existing sources:

```
python -m chronicle_forge.play --replay recipe.json --export story.md
python -m chronicle_forge.play --seed 42 --auto --export story.json   # via the recorded recipe
```

Because this touches the P8 CLI again (additive only, existing flags byte-
identical), **I am deferring CLI failing tests until the CLI shape is approved**,
exactly as the library contract below is the firm part. Please confirm: (a)
`--export` on the play CLI vs. a separate entrypoint; (b) whether `--seed …
--export` should export the *recorded* recipe (requires recording, like
`--save`). The library is usable and testable without any CLI.

## Determinism & seed42 guards

- `export_transcript(recipe, fmt)` is byte-deterministic per format.
- seed42 metadata pins `world_hash` to `e62d8f2c…` and `transcript_hash` to
  `98bea862…` — the golden guards, now surfaced in the export.
- The stored transcript re-validates: regenerating from the embedded recipe
  reproduces `transcript_hash` and the stored body.

## Test plan (failing — `tests/test_export.py`, RED until implemented)

- **Metadata:** `test_export_metadata_fields` (seed/engine_version, world_hash
  `e62d8f2c…`, transcript_hash `98bea862…`, 64-char recipe_hash).
- **Formats:** `test_export_txt_contains_transcript_and_reference`,
  `test_export_md_has_metadata_and_transcript`,
  `test_export_json_embeds_recipe_and_transcript` (keys {metadata,recipe,
  transcript}; embedded recipe re-validates equal).
- **Determinism:** `test_export_is_deterministic` (all three formats).
- **Cache re-validation:** `test_export_transcript_hash_matches_regeneration`
  (regenerate from the embedded recipe → same hash and body).
- **File writing:** `test_write_export_infers_format` (.txt/.md/.json),
  `test_write_export_rejects_unknown_extension`.

## Implementation plan (after approval — small commits)

1. `persistence/export.py` (`ExportMetadata`, `export_transcript`,
   `write_export`) + `__init__` exports → library tests green.
2. (If CLI approved) additive `--export` wiring on the play CLI → CLI tests
   green; re-verify seed42 `--auto` stdout `98bea862` unchanged.

## Constraints honored

- `models.py` / P6 / P7 / P8 / P9-1 / P9-3 unchanged; `export.py` only consumes
  `replay_transcript`.
- Transcript is **stored but non-authoritative**; the recipe stays canonical and
  the stored text is re-validatable.
- seed42 golden inviolable, and now reflected in export metadata.
