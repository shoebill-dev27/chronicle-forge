"""C-5 — the client's persistent book state (D-6 minimum).

The world half of a save already exists and is not reinvented here: a
:class:`~chronicle_forge.persistence.schema.Recipe` (seed + max_year + mode +
ordered inputs) reconstructs the world byte-exactly, so *the recipe is the save*
(P9). What the recipe cannot hold is the part that belongs to the reader rather
than the world — which attributions they have uncovered, and where they had got
to. That is this module.

Three rules carry the whole design:

* **A reveal belongs to one world, not to a seed.** Two books grown from the same
  seed under different choices are different worlds, and an engine coordinate
  means a different fact in each. So a reveal set is trusted only while the
  recipe it was stored beside still hashes to the recorded ``canonical_hash``
  (CS-2). A swapped or hand-edited recipe drops its reveals rather than
  mis-rendering them against the wrong history.
* **The past is immutable and the recipe only grows.** Sealing appends one input;
  it never rewrites an earlier one. An earlier reveal therefore still resolves
  under the longer recipe, which is what lets the hash be rewritten on every seal
  without invalidating what the player already earned.
* **Reading earns nothing.** The reveal set is monotone (CS-3) and only an
  explicit confirm adds to it, so navigating the archive can never move state
  (D-04).

The store stays *below* the app boundary: raw engine coordinates live here and
are never emitted through a lens DTO or a golden surface, so no engine golden and
no id-free contract is touched (CS-1).
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import List, Literal, Optional, Sequence, Union

from pydantic import BaseModel, ConfigDict, ValidationError

from ..persistence.schema import EngineVersionMismatch, Recipe
from ..persistence.version import ENGINE_VERSION

PathLike = Union[str, Path]

# The client store's own schema, versioned independently of the engine: a change
# to how a cursor is shaped is not a change to what the world is.
SCHEMA_VERSION = "1"

Status = Literal["UNFINISHED", "FINISHED"]

# How a reveal was earned. Kept on the reveal so an audit can assert D-03
# (delivered reveals name only the previous life) and D-05 (earned reveals
# follow a player action) without re-deriving where each one came from.
Surface = Literal["P10_DIGEST", "S02_HOLD", "P14_TRACE", "P12_SEED"]


class CorruptBookState(Exception):
    """The file is not a book this build can open. Raised rather than repaired:
    a half-understood save would resume someone into a world that is not theirs.
    """


def canonical_hash(recipe: Recipe) -> str:
    """The identity of one exact world, as grown so far.

    Digested over the same canonical JSON the recipe is saved with, so the hash
    of a recipe on disk and of the same recipe in memory always agree. All of the
    recipe's fields participate: ``engine_version`` is one input among several,
    not the whole gate, which is what makes same-seed/different-choice books
    distinguishable.
    """
    blob = json.dumps(recipe.model_dump(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class Reveal(BaseModel):
    """One attribution the player has uncovered.

    ``coord`` is a raw engine coordinate. It is meaningless outside the world its
    book names, which is exactly why the hash gate exists.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    surface: Surface
    coord: str


class Cursor(BaseModel):
    """Where the reader was, precisely enough to put them back.

    ``selected_option`` is the I-03 selected-*not*-sealed option. It is restored
    faintly previewed and still unsealed, because selection commits nothing —
    only I-04 appends to the recipe. An open inspection is deliberately absent:
    inspecting is not a place in the book, so resume re-opens the page beneath it.
    """

    model_config = ConfigDict(extra="forbid")

    page: str = "shelf"
    life_ordinal: Optional[int] = None
    juncture_index: Optional[int] = None
    selected_option: Optional[int] = None
    reading_offset: int = 0
    # Set while the reader is back in the archive; the page named above is the
    # unresolved one 「今の頁へ」 returns to. Navigation is not commitment, so this
    # never affects the recipe.
    archive_life: Optional[int] = None


class BookMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created_at: str = ""
    last_opened_at: str = ""
    display_title: str = ""


class BookState(BaseModel):
    """One shelf slot: the world it is, what has been uncovered, where we were."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION
    engine_version: str = ENGINE_VERSION
    # Rewritten with the recipe on every seal (§3.3). On load it is checked
    # against the recipe actually present, which is the CS-2 gate.
    canonical_hash: str
    # Client-minted and local, deliberately not derived from world content: two
    # books from one seed are two shelf entries, not one.
    book_id: str
    recipe: Recipe
    status: Status = "UNFINISHED"
    reveals: List[Reveal] = []
    cursor: Cursor = Cursor()
    meta: BookMeta = BookMeta()

    # -- construction ------------------------------------------------------

    @classmethod
    def new(
        cls,
        *,
        seed: int,
        max_year: int,
        inputs: Sequence[str] = (),
        book_id: Optional[str] = None,
    ) -> "BookState":
        recipe = Recipe(
            engine_version=ENGINE_VERSION,
            seed=seed,
            max_year=max_year,
            mode="human" if inputs else "auto",
            inputs=list(inputs),
        )
        return cls(
            canonical_hash=canonical_hash(recipe),
            book_id=book_id or uuid.uuid4().hex,
            recipe=recipe,
        )

    # -- the two things play does to a book --------------------------------

    def seal(self, option: int) -> "BookState":
        """Commit one choice. The only operation that grows the recipe.

        Append-only by construction: an earlier input is never rewritten, so
        every reveal earned under the shorter recipe still names the same fact.
        """
        if self.status == "FINISHED":
            raise ValueError("a finished book's recipe never changes again")
        recipe = self.recipe.model_copy(
            update={
                "inputs": [*self.recipe.inputs, str(option)],
                "mode": "human",
            }
        )
        return self.model_copy(
            update={"recipe": recipe, "canonical_hash": canonical_hash(recipe)}
        )

    def confirm(self, surface: Surface, coord: str) -> "BookState":
        """Record one uncovered attribution. Idempotent and monotone (CS-3).

        There is no un-confirm. D-04 makes a reveal permanent, and permanence is
        cheaper to guarantee than to re-derive.
        """
        entry = Reveal(surface=surface, coord=coord)
        if entry in self.reveals:
            return self
        return self.model_copy(update={"reveals": [*self.reveals, entry]})

    def knows(self, coord: str) -> bool:
        """Has this attribution been uncovered? Drives render, never state.

        Deliberately ignores ``surface``: once a connection is confirmed it stays
        confirmed everywhere it appears, however it was first earned.
        """
        return any(r.coord == coord for r in self.reveals)

    def at(self, **cursor) -> "BookState":
        return self.model_copy(update={"cursor": self.cursor.model_copy(update=cursor)})

    def finish(self) -> "BookState":
        """P-15: the book closes. Its recipe is frozen; its reveals may still
        grow, because revisiting a finished world and tracing still earns them."""
        return self.model_copy(update={"status": "FINISHED"})


# --------------------------------------------------------------------------
# the store
# --------------------------------------------------------------------------


def save_book(state: BookState, path: PathLike) -> None:
    """Write the book atomically.

    Through a temporary file in the same directory and then ``os.replace``, which
    is atomic on a single filesystem: a save interrupted by a crash or a full
    disk leaves the *previous* book intact rather than a truncated one. Losing
    the last choice is recoverable; losing the world is not.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(state.model_dump(), sort_keys=True, indent=2) + "\n"
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)


def load_book(path: PathLike) -> BookState:
    """Read a book back, failing closed.

    Three refusals, in order of how wrong they are:

    * unreadable or off-schema → :class:`CorruptBookState`; nothing is guessed.
    * recorded under another engine → :class:`EngineVersionMismatch`, mirroring
      the recipe's own gate: a snapshot-free save can only be reconstructed by
      re-running the engine, and a different engine reconstructs a different
      world.
    * recipe no longer hashes to ``canonical_hash`` → the world these coordinates
      were minted in is not the world in this file, so **the reveals are
      dropped** and the book opens with nothing uncovered. The recipe is the
      canon and survives; the reader simply has to find things again, which is
      the honest failure — showing them a stranger's discoveries is not.
    """
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise CorruptBookState(f"cannot read {path}: {exc}") from exc
    try:
        state = BookState.model_validate_json(raw)
    except ValidationError as exc:
        raise CorruptBookState(f"not a book this build can open: {path}") from exc

    if state.recipe.engine_version != ENGINE_VERSION:
        raise EngineVersionMismatch(
            f"book recorded under {state.recipe.engine_version}, "
            f"this engine is {ENGINE_VERSION}"
        )
    if canonical_hash(state.recipe) != state.canonical_hash:
        return state.model_copy(
            update={"reveals": [], "canonical_hash": canonical_hash(state.recipe)}
        )
    return state
