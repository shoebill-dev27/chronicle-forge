"""The Python side of the Living Chronicle client (ADR-002).

This is the ``js_api`` object exposed to the frontend; every method returns
plain JSON-serialisable dicts. It imports NO GUI toolkit (``webview`` is touched
only by ``shell.py``), so it is unit-testable without a display and cannot
affect the frozen engine goldens.

I-1b: the bridge no longer reads the game by parsing prose. It used to run the
engine and regex the printed ``turn_screen`` block back into fields, which could
recover exactly one of the loop's five beats and re-broke every time the
renderer changed wording. It now hands the frontend the typed beat stream
(:mod:`play.beats`) whole, so death / the years / the aftermath / the next life
are as available to the page as the juncture is.

What the client may draw is therefore bounded by what the engine produced: an
aftermath with no hardened mark carries no mark, and a juncture with no
recognition carries no ``recognition`` — the page has nothing to invent from.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence

from ..play import beats as beat_stream
from ..reporting._data import place
from ..worldgen import generate_world
from .state import (
    BookState,
    CorruptBookState,
    Cursor,
    Surface,
    load_book,
    save_book,
)


class BookBridge:
    """The ``js_api`` object exposed to the frontend (ADR-002).

    Every method returns a plain dict; pywebview serialises it to JS. No method
    imports or requires a GUI backend.
    """

    def __init__(self, seed: int = 1, store: Optional[Path] = None) -> None:
        self._seed = seed
        # Where books are kept. Injected so a test drives a temp directory and
        # the shipped client keeps its own; ``None`` means this build is running
        # without a store at all, which is the pre-C-5 behaviour and still legal
        # (every persistence method then answers honestly that it saved nothing).
        self._store = Path(store) if store else None

    def shelf(self) -> Dict:
        """P-01: the shelf, as far as this build can honestly fill it.

        The book that the empty slot opens into is described by the world it
        will really be — its place and the span of years it runs to, both read
        from ``generate_world`` and neither of them a spoiler: worldgen fixes
        them before a single life is lived. ``books`` is empty and stays empty
        until there is somewhere to keep a finished one; a shelf of resumable
        and finished books needs the discovery-state store, which is I-6, and
        inventing spines for books that cannot be reopened would be a worse
        stub than an empty shelf.
        """
        world = generate_world(self._seed)
        return {
            "empty_slot": True,
            "books": [],
            "invitation": place(world),
            "seed": self._seed,
            "span_years": world.max_year,
        }

    def play(
        self, seed: Optional[int] = None, choices: Optional[Sequence] = None
    ) -> Dict:
        """Play a whole world under ``choices`` and return its beat stream.

        ``choices`` are the displayed numbers the player sealed, in order; every
        juncture past the end of that list is entrusted to the world. Pure in
        ``(seed, choices)`` — calling it twice returns the same stream, and
        calling it with the empty list returns the run whose *first* juncture is
        the one the player is about to answer (the options at a juncture are
        drawn before the choice, so they do not depend on it).
        """
        seed = self._seed if seed is None else int(seed)
        picks: List[str] = [str(c) for c in (choices or [])]
        return beat_stream.to_dict(beat_stream.stream(seed, picks))

    # -- C-5: the book that survives quitting -------------------------------

    def _path(self, book_id: str) -> Path:
        if self._store is None:
            raise CorruptBookState("this build has no book store")
        return self._store / f"{book_id}.json"

    def open_book(self, book_id: Optional[str] = None, seed: Optional[int] = None):
        """Resume ``book_id`` if it is there, else start a new book.

        Returns the book's persistent state beside the stream it describes, so
        the page can restore the reader's cursor and their reveals in one step
        rather than reconstructing either.
        """
        seed = self._seed if seed is None else int(seed)
        state = None
        if book_id and self._store is not None:
            try:
                state = load_book(self._path(book_id))
            except CorruptBookState:
                # Fail closed and start clean rather than resume a reader into a
                # book this build cannot vouch for.
                state = None
        if state is None:
            world = generate_world(seed)
            state = BookState.new(seed=seed, max_year=world.max_year)
        return self._book(state)

    def seal_choice(self, book_id: str, option: int) -> Dict:
        """Commit one choice and write the book before returning.

        The write happens *before* the new stream is handed back, so a crash
        between the two loses the frame, never the choice.
        """
        state = load_book(self._path(book_id)).seal(int(option))
        save_book(state, self._path(state.book_id))
        return self._book(state)

    def confirm(self, book_id: str, surface: Surface, coord: str) -> Dict:
        """Record one earned confirmation. Monotone, and persisted immediately."""
        state = load_book(self._path(book_id)).confirm(surface, coord)
        save_book(state, self._path(state.book_id))
        return self._book(state)

    def move_cursor(self, book_id: str, cursor: Optional[Dict] = None) -> Dict:
        """Remember where the reader is. Never touches the recipe: navigating
        the archive is not committing to anything (baseline UX-R8).

        ``cursor`` arrives as one object because that is how the frontend can
        send it: pywebview marshals JS arguments positionally, so a ``**kwargs``
        signature is unreachable from the page — every call from the real client
        raised a TypeError the page never saw, and the reader's position was
        silently never written.
        """
        patch = {k: v for k, v in (cursor or {}).items() if k in Cursor.model_fields}
        state = load_book(self._path(book_id)).at(**patch)
        save_book(state, self._path(state.book_id))
        return self._book(state)

    def _book(self, state: BookState) -> Dict:
        """One book, as the page needs it: the world so far, plus what the
        reader has earned and where they were."""
        if self._store is not None:
            save_book(state, self._path(state.book_id))
        return {
            "book_id": state.book_id,
            "status": state.status,
            "seed": state.recipe.seed,
            "choices": list(state.recipe.inputs),
            "cursor": state.cursor.model_dump(),
            # Coordinates only. The page asks "do I know this?" and never gets a
            # list of facts it has not earned.
            "known": sorted({r.coord for r in state.reveals}),
            "stream": beat_stream.to_dict(
                beat_stream.stream(state.recipe.seed, list(state.recipe.inputs))
            ),
        }
