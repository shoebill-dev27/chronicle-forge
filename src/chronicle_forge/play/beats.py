"""I-1b — the typed beat stream: the client's seam onto a played world.

WHY THIS EXISTS
    The I-1 client obtained its one juncture by regex-parsing ``play.render``'s
    printed prose (``client/bridge.py:_OPTION_RE``). That seam could express
    exactly one of the loop's five beats, and it broke in spirit the moment
    X-1..X-4 rewrote the renderer underneath it. This module replaces it with a
    typed stream of what actually happened, read off the world.

WHAT IT DOES NOT DO
    It adds no truth. Every field below is read from the world the engine already
    built, using the same helpers ``play.render`` uses to *speak* them, so the
    surface and the transcript can never disagree. It draws no RNG, holds no
    clock, and mutates nothing. ``run_human_world`` takes an observer that
    defaults to ``None``; with no observer the run is byte-identical to today's,
    which is what keeps the goldens and ENGINE_VERSION untouched.

    Deliberately absent: a spatial axis. ``CausalNode.location_id`` is ``None``
    on 100% of nodes across seeds 1/7/42/99/123, so there is nothing to place;
    the stream carries time and authorship, which is also the pair of axes the
    Core Experience itself is made of.

THE BEATS
    rebirth · juncture · outcome · death · years · aftermath · closing

    Recognition is not a beat of its own: it only ever occurs *at* a juncture,
    so it rides on the juncture beat and names the option that carries it. That
    is what stops the client marking a line no former self ever touched.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import ClassVar, Dict, List, Optional, Sequence, Tuple

from ..reporting._data import (
    heritage_rows,
    life_index,
    place,
    seed_by_id,
    seeds_of_life,
)
from ..causal import CausalGraph
from ..reporting.labels import event_phrase, heritage_name, seed_label
from . import render
from .human import null_writer, scripted_reader

# --------------------------------------------------------------------------
# value objects
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Event:
    """One thing the world did, and whose earlier choice it descends from."""

    year: int
    scale: str
    phrase: str
    owners: Tuple[int, ...]  # life ordinals whose own seeds directly caused it


@dataclass(frozen=True)
class Option:
    """One offered action, exactly as ``render.turn_screen`` would print it."""

    n: int  # the displayed number (1..3)
    label: str
    kind: str
    why: str
    heritage_id: Optional[str] = None  # set only for a Legacy action


@dataclass(frozen=True)
class Recognition:
    """A former self met at this juncture. Present only when the engine says so."""

    option: int  # which displayed option carries it — never invented
    name: str
    founder_life: int
    founder_talent: str
    planted_year: Optional[int]
    reach: int
    # C-2 (baseline UX-R6): the words the founding life was sealed under, if that
    # life was played in this run and the player chose the act themselves. A
    # confirmation is a comparison, and it can only resolve against the wording
    # the player actually read — not the world's own phrase for the same act.
    # ``None`` means the engine cannot prove the player chose it; the client must
    # then say so rather than borrow the world's phrasing and call it a memory.
    sealed_act: Optional[str] = None


@dataclass(frozen=True)
class Change:
    """One thing the world did with one act of the life that just ended.

    The two halves are joined by a causal edge that already exists: the events
    of ``render._echoes`` descend from that life's own seeds, and a seed is the
    act that planted it. Neither half is authored here — ``act`` is the label
    the player was shown (or the world's own phrase for an act it took on its
    own), ``consequence`` is ``event_phrase``.
    """

    act: str
    sealed: bool  # True when this act was the player's own sealed choice
    consequence: str
    times: int  # how many events, so the page can weigh without a score
    first_year: int


@dataclass(frozen=True)
class Mark:
    """A seed that gained a name during the skip that just ran."""

    name: str
    founder_life: int
    planted_year: Optional[int]
    reach: int
    longevity: int


@dataclass(frozen=True)
class Legacy:
    name: str
    founder_life: str
    action: str
    living: bool


@dataclass(frozen=True)
class CauseStep:
    """One real hop on the way back from a consequence toward its origin.

    A step exists only where a ``CausalEdge`` exists. Nothing is interpolated:
    if two events are drawn as adjacent, the world really put an edge there.
    """

    year: int
    phrase: str


@dataclass(frozen=True)
class CausePath:
    """One consequence and the ordered real path back to the act that began it.

    This is the investigation contract (C-3, baseline UX-R6). Three things it
    deliberately is *not*:

    * ``steps`` is a **path**, not a count. P18's ``CauseChain.steps`` is the
      number of ancestors an event has, which is a summary; drawing it as a
      distance would invent links the graph does not contain. Every entry here
      is one existing edge, effect-first and origin-last.
    * ``other_origins`` keeps a shared cause honest. An event can descend from
      several of the player's acts; the earliest is *one contributing origin*,
      never proof that one life alone caused it. A non-zero count is the
      client's obligation to say so.
    * ``origin_sealed`` separates what the player chose from what their life did
      on its own (C-6). An autonomous origin is traced truthfully, but it is
      narrated as history and may never be captioned "the choice you made".
    """

    # An opaque, deterministic handle for *this* consequence. The engine's five
    # event phrases repeat, so (year, phrase) does not identify an event: two
    # different "war breaks out" in the same year are two different threads. The
    # client needs one stable key to bind a reveal to and to resume onto, and it
    # must not be an engine id — so it is a digest of one. Never displayed.
    ref: str
    event: str
    year: int
    steps: Tuple[CauseStep, ...]  # effect-first, origin-last; real edges only
    origin_life: int
    origin_year: int
    origin_act: str
    origin_sealed: bool
    other_origins: int
    posthumous: bool  # the consequence outlived the life that seeded it


@dataclass(frozen=True)
class Life:
    ordinal: int
    talent: str
    birth_year: int
    death_year: int


# --------------------------------------------------------------------------
# beats
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Rebirth:
    KIND: ClassVar[str] = "rebirth"
    life: int
    year: int
    talent: str
    era: str


@dataclass(frozen=True)
class Juncture:
    KIND: ClassVar[str] = "juncture"
    life: int
    year: int
    age: int
    reason: str
    header: str  # the framing phrase ("A crisis gathers") — engine's own words
    era: str
    options: Tuple[Option, ...]
    recognition: Optional[Recognition] = None


@dataclass(frozen=True)
class Outcome:
    """What the act the player sealed actually did (P-07).

    The engine prints nothing at this moment — the transcript goes from one turn
    screen straight to the next — so this beat is not a re-reading of prose; it
    is the world read immediately after the verb ran, in the same breath as the
    choice. ``planted`` counts the causal seeds that act set in motion, and it
    is the only honest basis for the plant cue: a life that planted nothing must
    not be told that it did.

    Emitted only for a juncture the player was actually asked. The turns the
    world takes on its own are the life's weather, not its entry.
    """

    KIND: ClassVar[str] = "outcome"
    life: int
    year: int
    age: int
    option: int  # the displayed number sealed; 0 when the season was let pass
    label: str
    kind: str
    planted: int


@dataclass(frozen=True)
class Death:
    KIND: ClassVar[str] = "death"
    life: int
    year: int
    age: int
    talent: str
    title: str
    named: Tuple[str, ...]  # marks of this life that already bear a name
    pending: int  # things set in motion that do not yet
    seed_years: Tuple[int, ...]


@dataclass(frozen=True)
class Years:
    KIND: ClassVar[str] = "years"
    after_life: int
    from_year: int
    to_year: int
    span: int
    world_ended: bool
    events: Tuple[Event, ...]


@dataclass(frozen=True)
class Aftermath:
    KIND: ClassVar[str] = "aftermath"
    after_life: int
    year: int
    echoes: Tuple[Event, ...]
    hardened: Tuple[Mark, ...]
    # P-10's digest: the echoes above, grouped by the act behind them and cut to
    # what one page delivers. Never sourced from `hardened` — see `_changes`.
    changes: Tuple[Change, ...] = ()


@dataclass(frozen=True)
class Closing:
    KIND: ClassVar[str] = "closing"
    year: int
    lives: int
    ending: str
    legacies: Tuple[Legacy, ...]
    # The threads the finished book can honestly offer (C-3). Carried on the
    # closing beat because the whole world is reached by then — there is no
    # unreached future left to leak. Nothing here is *shown* until the player
    # inspects: D-04 forbids reading from confirming anything on its own.
    cases: Tuple[CausePath, ...] = ()


# P-10 delivers at most three lines (UX spec §P-10). The cut is made HERE, not
# on the page: D-03 reserves everything beyond it for the player to discover, so
# a stream that carried the remainder would be handing the client truth it is
# forbidden to deliver.
DIGEST_MAX = 3

# The ending offers threads to pull, not a database to browse. The bound keeps
# the closing payload finite on a long world; the *ordering* below decides which
# survive, so the ones the player chose come first.
# ponytail: a flat cap, fine while a world is ~200 years; page it if worlds grow.
CASES_MAX = 12

BEAT_KINDS = (
    "rebirth",
    "juncture",
    "outcome",
    "death",
    "years",
    "aftermath",
    "closing",
)


@dataclass(frozen=True)
class WorldBeats:
    """One played world, as beats."""

    seed: int
    place: str
    max_year: int
    end_year: int
    ending: str
    lives: Tuple[Life, ...]
    beats: Tuple[object, ...] = field(default=())


def beat_dict(beat) -> Dict:
    """One beat as plain JSON, discriminated by ``t``."""
    out = asdict(beat)
    out["t"] = beat.KIND
    return out


def to_dict(world_beats: WorldBeats) -> Dict:
    """The whole stream as plain JSON — what the bridge hands the frontend."""
    return {
        "seed": world_beats.seed,
        "place": world_beats.place,
        "max_year": world_beats.max_year,
        "end_year": world_beats.end_year,
        "ending": world_beats.ending,
        "lives": [asdict(life) for life in world_beats.lives],
        "beats": [beat_dict(b) for b in world_beats.beats],
    }


# --------------------------------------------------------------------------
# the recorder
# --------------------------------------------------------------------------


def _ordinal_of(world, life_id) -> Optional[int]:
    return life_index(world).get(life_id)


def _ref(engine_id: str) -> str:
    """A stable, opaque handle for an engine id — the same every run, and not
    the id itself, so nothing downstream can start reading meaning into it."""
    return hashlib.sha256(engine_id.encode()).hexdigest()[:12]


def _cause_steps(nodes: Dict[str, object], node_id: str, target_id: str):
    """The shortest real edge path from a consequence back to one origin seed.

    Breadth-first over ``caused_by``, with every expansion sorted, so one world
    always yields one path. Returns the events lying *between* the two ends,
    effect-first; an empty tuple is the honest answer when the origin caused the
    consequence directly. ``None`` means no path exists at all — the caller's
    premise was wrong and it must drop the case rather than draw a link.

    Breadth-first rather than ``CausalGraph.trace_to_roots``: that enumerates
    *every* path and is exponential on a branchy DAG, and the page only ever
    draws one.
    """
    if node_id == target_id:
        return ()
    prev: Dict[str, Optional[str]] = {node_id: None}
    frontier = [node_id]
    while frontier:
        nxt: List[str] = []
        for cur in frontier:
            node = nodes.get(cur)
            if node is None:  # a seed id: a root, nothing behind it
                continue
            for cause in sorted({e.from_id for e in node.caused_by}):
                if cause in prev:
                    continue
                prev[cause] = cur
                if cause == target_id:
                    chain = [cause]
                    walk = prev[cause]
                    while walk is not None:
                        chain.append(walk)
                        walk = prev[walk]
                    chain.reverse()  # effect-first: node_id … target_id
                    return tuple(
                        CauseStep(year=nodes[i].year, phrase=event_phrase(nodes[i]))
                        for i in chain[1:-1]
                    )
                nxt.append(cause)
        frontier = nxt
    return None


def _owners(world, node) -> Tuple[int, ...]:
    """Life ordinals whose own seeds directly caused this event.

    Direct ``caused_by`` edges only — the same rule :func:`render._echoes` uses,
    so the surface attributes an event exactly the way the text does. Sorted
    explicitly: the graph's ancestor sets are unordered, and an unsorted read
    would make the stream differ between runs of the same seed.
    """
    out = set()
    for edge in node.caused_by:
        seed = seed_by_id(world, edge.from_id)
        if seed is None or seed.planted_by_life_id is None:
            continue
        ordinal = _ordinal_of(world, seed.planted_by_life_id)
        if ordinal:
            out.add(ordinal)
    return tuple(sorted(out))


def _event(world, node) -> Event:
    return Event(
        year=node.year,
        scale=str(node.scale).rsplit(".", 1)[-1].lower(),
        phrase=event_phrase(node),
        owners=_owners(world, node),
    )


def _planted_year(world, heritage) -> Optional[int]:
    seed = seed_by_id(world, heritage.seed_id)
    return seed.planted_year if seed is not None else None


class BeatRecorder:
    """The observer ``run_human_world`` calls. Read-only on every argument."""

    def __init__(self, choices: Sequence = ()) -> None:
        self.beats: List[object] = []
        self._life = 0
        self._death_year = 0
        # Which junctures the PLAYER answered. The recorder sees only the chosen
        # option, and the session picks for the player on EOF, on empty input and
        # on an explicit pass — in all three the world decided. Without the
        # original input list there is no way to tell those apart from a real
        # decision, and "the choice you made" would end up printed over an act
        # nobody chose. Reading the list here keeps the judgement conservative:
        # anything unrecognised is recorded as the world's doing, never as the
        # player's.
        self._choices: Tuple[str, ...] = tuple(str(c).strip() for c in choices)
        self._asked = 0
        # life ordinal -> {seed id: the label the player sealed it under}. The
        # digest's strongest line is an act the player CHOSE, named in the words
        # they read it in; that pairing exists nowhere else, which is why the
        # digest is built here and not in a reporting lens.
        self._sealed: Dict[int, Dict[str, str]] = {}

    # -- hooks (called by play.session; each mirrors one render call site) --

    def on_rebirth(self, world, life) -> None:
        self._life = _ordinal_of(world, life.id) or (self._life + 1)
        self.beats.append(
            Rebirth(
                life=self._life,
                year=life.birth_year,
                talent=life.talent.value if life.talent else "soul",
                era=render._era(world),
            )
        )

    def on_juncture(self, world, life, options, reason, recognize_id) -> None:
        self._asked += 1
        top3 = render._top3(options)
        rows = []
        for n, option in enumerate(top3, start=1):
            opp = option.opportunity
            rows.append(
                Option(
                    n=n,
                    label=render._display_label(world, option),
                    kind=render._KIND_WORD.get(opp.kind, "Chance"),
                    why=render.why_now(opp.signals),
                    heritage_id=(
                        opp.target_id
                        if opp.kind.name == "LEGACY"  # the only kind that names one
                        else None
                    ),
                )
            )
        self.beats.append(
            Juncture(
                life=self._life,
                year=world.current_year,
                age=life.age,
                reason=reason,
                header=render._HEADER.get(reason, "The world turns to you"),
                era=render._era(world),
                options=tuple(rows),
                recognition=self._recognition(world, rows, recognize_id),
            )
        )

    def on_outcome(self, world, life, options, choice, planted_ids) -> None:
        """The verb has run; read what it did before anything else moves.

        ``choice`` is matched by identity, not equality: two options of a turn
        can compare equal by value, and the entry must name the one that was
        actually taken. A choice outside the displayed three is the season let
        pass — the world answered for the player — and is recorded as option 0.
        """
        top3 = render._top3(options)
        opp = choice.opportunity
        label = render._display_label(world, choice)
        option = next((i for i, o in enumerate(top3, 1) if o is choice), 0)
        # Option 0 is the season let pass: the world answered, the player did
        # not. Recording it here would let an autonomous act be captioned "the
        # choice you made" on the digest and in a trace — C-6, and the one thing
        # the discovery loop cannot afford to be wrong about. The act is still
        # real and still traceable; it is simply narrated as history.
        if option and self._player_answered(len(top3)):
            sealed = self._sealed.setdefault(self._life, {})
            for seed_id in planted_ids:
                sealed[seed_id] = label
        self.beats.append(
            Outcome(
                life=self._life,
                year=world.current_year,
                age=life.age,
                option=option,
                label=label,
                kind=render._KIND_WORD.get(opp.kind, "Chance") if opp else "Chance",
                planted=len(planted_ids),
            )
        )

    def on_death(self, world, life) -> None:
        mine = {s.id for s in seeds_of_life(world, life.id)}
        named = [h for h in world.heritage if h.seed_id in mine]
        self._death_year = (
            life.death_year if life.death_year is not None else world.current_year
        )
        planted = sorted(
            {
                seed.planted_year
                for seed in (seed_by_id(world, sid) for sid in mine)
                if seed is not None
            }
        )
        self.beats.append(
            Death(
                life=self._life,
                year=self._death_year,
                age=render._age_at_death(life),
                talent=life.talent.value if life.talent else "soul",
                title=render._title(world, life),
                named=tuple(heritage_name(h) for h in named),
                pending=len(mine) - len(named),
                seed_years=tuple(planted),
            )
        )

    def on_years(self, world, skip) -> None:
        span = skip.get("years_run", 0)
        start = self._death_year
        end = start + span
        self.beats.append(
            Years(
                after_life=self._life,
                from_year=start,
                to_year=end,
                span=span,
                world_ended=bool(skip.get("world_ended")),
                # The skip is where the world is loudest — measured over seeds
                # 1/7/42/99/123, nearly every event of a skip descends from the
                # life that just died. This list is that, and only that.
                events=tuple(
                    _event(world, node)
                    for node in sorted(world.causal_nodes, key=lambda n: (n.year, n.id))
                    if start < node.year <= end
                ),
            )
        )

    def on_aftermath(self, world, life, promoted_seed_ids) -> None:
        hardened: List[Mark] = []
        for ordinal, marks in render._hardened(world, promoted_seed_ids):
            hardened.extend(
                Mark(
                    name=heritage_name(h),
                    founder_life=ordinal,
                    planted_year=_planted_year(world, h),
                    reach=h.reach,
                    longevity=h.longevity,
                )
                for h in marks
            )
        self.beats.append(
            Aftermath(
                after_life=self._life,
                year=world.current_year,
                echoes=tuple(_event(world, n) for n in render._echoes(world, life)),
                hardened=tuple(hardened),
                changes=self._changes(world, life),
            )
        )

    def _changes(self, world, life) -> Tuple[Change, ...]:
        """P-10's digest: what the years did with the acts of the life that just
        ended, one line per distinct act-and-consequence.

        ``hardened`` is deliberately not an input. Measured over seeds 1-30,
        **none** of 229 hardened marks was founded by the life that just died —
        a seed needs a life or two to gain a name — so delivering them would
        attribute changes to OLDER lives, which D-03 reserves for the player to
        discover. Hardened marks stay on the aftermath as their own field, for
        the surface and for tracing; they never become a digest line.

        Raw echoes cannot be the digest either: seed 1's first rebirth has 31 of
        them carrying 4 distinct phrases, so the top three would print the same
        sentence three times. Repetition is not more truth, so this groups.
        """
        mine = render._seed_ids(world, life)
        sealed = self._sealed.get(self._life, {})
        grouped: Dict[Tuple[bool, str, str], set] = {}
        for node in render._echoes(world, life):
            phrase = event_phrase(node)
            # one seed may reach a node by several edges; the node is still one
            # thing the world did, so causes are taken as a set
            for seed_id in {e.from_id for e in node.caused_by} & mine:
                label = sealed.get(seed_id)
                key = (label is not None, label or seed_label(world, seed_id), phrase)
                grouped.setdefault(key, set()).add((node.id, node.year))
        rows = [
            Change(
                act=act,
                sealed=was_sealed,
                consequence=phrase,
                times=len(nodes),
                first_year=min(year for _, year in nodes),
            )
            for (was_sealed, act, phrase), nodes in grouped.items()
        ]
        # A total order, so the same (seed, choices) always yields the same page:
        # what the player chose first, then what the world did most with it.
        rows.sort(
            key=lambda c: (not c.sealed, -c.times, c.first_year, c.act, c.consequence)
        )
        return tuple(rows[:DIGEST_MAX])

    def on_closing(self, world) -> None:
        self.beats.append(
            Closing(
                year=world.current_year,
                lives=len(world.lives),
                ending=world.ending_class,
                legacies=tuple(
                    Legacy(
                        name=row["name"],
                        founder_life=render._founder_ordinal(row),
                        action=row["origin_action"],
                        living=render._is_living(world, row),
                    )
                    for row in heritage_rows(world)
                ),
                cases=self._cases(world),
            )
        )

    # -- internals --

    def _recognition(self, world, rows, recognize_id) -> Optional[Recognition]:
        """The former self this juncture actually offers, or ``None``.

        ``None`` is the common case and must stay legible as such: a client that
        marks a line anyway is claiming a past the world does not have.
        """
        if recognize_id is None:
            return None
        her = render._heritage_by_id(world, recognize_id)
        if her is None:
            return None
        seed = seed_by_id(world, her.seed_id)
        founder = _ordinal_of(world, seed.planted_by_life_id) if seed else None
        if founder is None:
            return None
        carrier = next((r.n for r in rows if r.heritage_id == recognize_id), None)
        if carrier is None:
            return None
        life = next(
            (x for x in world.lives if seed and x.id == seed.planted_by_life_id), None
        )
        return Recognition(
            option=carrier,
            name=heritage_name(her),
            founder_life=founder,
            founder_talent=(life.talent.value if life and life.talent else "soul"),
            planted_year=seed.planted_year if seed else None,
            reach=her.reach,
            # C-2: only if THIS run played that life and the player sealed that
            # very seed. `seed_label` would always return something, but it is
            # the world's phrase for the act, not the sentence the player chose
            # — offering it as a memory would be putting words in their mouth.
            sealed_act=self._sealed.get(founder, {}).get(seed.id) if seed else None,
        )

    def _player_answered(self, offered: int) -> bool:
        """Did a person answer the juncture just resolved?

        ``on_juncture`` and ``on_outcome`` fire once each per asked turn, so the
        counter indexes the input list. An input that is not a plain pick — EOF
        past the end, "", "0", anything unparsed — is the world being entrusted
        with the turn. Unrecognised input fails to *autonomous*: over-claiming a
        choice is the expensive direction of this error.
        """
        i = self._asked - 1
        if not (0 <= i < len(self._choices)):
            return False
        raw = self._choices[i]
        return raw.isdigit() and 1 <= int(raw) <= offered

    def _cases(self, world) -> Tuple[CausePath, ...]:
        """Every consequence the finished book can trace back to the player.

        One case per event that has a player-planted seed in its ancestry. The
        origin is the *earliest-planted* such seed — one contributing origin,
        which is why ``other_origins`` travels with it rather than being quietly
        dropped.

        ``player_seeds_in_ancestry`` walks a ``set``, so its order is not stable
        across runs; sorting before taking the first is what makes the same world
        produce the same book twice.
        """
        graph = CausalGraph.from_world(world)
        nodes = {n.id: n for n in world.causal_nodes}
        death_of = {
            i: (lf.death_year if lf.death_year is not None else world.current_year)
            for i, lf in enumerate(world.lives, start=1)
        }

        out: List[CausePath] = []
        for node in world.causal_nodes:
            seeds = sorted(
                graph.player_seeds_in_ancestry(node.id),
                key=lambda sd: (sd.planted_year, sd.id),
            )
            if not seeds:
                continue
            origin = seeds[0]
            ordinal = _ordinal_of(world, origin.planted_by_life_id)
            if ordinal is None:
                continue
            steps = _cause_steps(nodes, node.id, origin.id)
            if steps is None:  # no real path: say nothing rather than draw one
                continue
            sealed = self._sealed.get(ordinal, {})
            out.append(
                CausePath(
                    ref=_ref(node.id),
                    event=event_phrase(node),
                    year=node.year,
                    steps=steps,
                    origin_life=ordinal,
                    origin_year=origin.planted_year,
                    # the player's own words where they exist, the world's phrase
                    # otherwise — and ``origin_sealed`` says which of the two it is
                    origin_act=sealed.get(origin.id) or seed_label(world, origin.id),
                    origin_sealed=origin.id in sealed,
                    other_origins=len(seeds) - 1,
                    posthumous=node.year > death_of.get(ordinal, node.year),
                )
            )
        # what the player chose, then the longest fuse, then oldest first
        out.sort(key=lambda c: (not c.origin_sealed, -len(c.steps), c.year, c.event))
        return tuple(out[:CASES_MAX])


# --------------------------------------------------------------------------
# the public entry point
# --------------------------------------------------------------------------


def stream(
    seed: int, choices: Sequence[object] = (), *, life_cap: int = 60
) -> WorldBeats:
    """Play a whole world under ``choices`` and return it as beats.

    ``choices`` are displayed numbers, one per juncture, in order; once they run
    out every remaining juncture is entrusted to the world (the EOF path), so
    ``stream(seed)`` is the fully-entrusted run. Deterministic in
    ``(seed, choices)``: no clock, no RNG of its own, and the transcript it
    discards is the same one the CLI would print.
    """
    from .session import run_human_world  # local: session imports render, not us

    recorder = BeatRecorder(choices)
    world = run_human_world(
        seed,
        reader=scripted_reader(choices),
        writer=null_writer,
        life_cap=life_cap,
        observer=recorder,
    )
    return WorldBeats(
        seed=seed,
        place=place(world),
        max_year=world.max_year,
        end_year=world.current_year,
        ending=world.ending_class,
        lives=tuple(
            Life(
                ordinal=i,
                talent=lf.talent.value if lf.talent else "soul",
                birth_year=lf.birth_year,
                death_year=(
                    lf.death_year if lf.death_year is not None else world.current_year
                ),
            )
            for i, lf in enumerate(world.lives, start=1)
        ),
        beats=tuple(recorder.beats),
    )
