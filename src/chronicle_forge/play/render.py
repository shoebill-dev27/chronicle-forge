"""Rendering for P8 — turn screens, the yearly digest, and life transitions.

All output is player-facing prose built from existing data: it reuses the P7
renderers (death, chronicle, timeline, legacy) and the deterministic ``labels``,
adds no new aggregation, and never mutates the world. Signals are spoken in
words, never as raw numbers (the P7 discipline).

Former-self recognition is shown only the *first* time a given heritage is
encountered within a life — re-meeting a past self should feel like discovery,
not a notification. The per-life ``seen`` set is volatile and lives in the play
session, never in the world.

The death → time-skip → rebirth beats (:func:`death_passage`, :func:`aftermath`)
and the closing page (:func:`closing_page`) compose the P7 renderers' *data* but
not their layout: the P7 text generators are frozen, so a few of their private
helpers are imported and reused verbatim to keep one voice, while what is said
*when* is decided here. That split matters, because the timing is the bug it
fixes — see :func:`death_passage`.
"""

from __future__ import annotations

import re
from typing import Optional

from ..opportunity import OpportunityKind, Signals
from ..reporting._data import (
    SCALE_ORDER,
    heritage_rows,
    life_index,
    place,
    seed_by_id,
    seeds_of_life,
)
from ..reporting.experience import _age_at_death, _cap_number, _strongest_bond, _title
from ..reporting.heritage_explorer import _is_living
from ..reporting.labels import event_phrase, heritage_name
from .gate import REASON_CRISIS, REASON_FLOOR, REASON_HISTORY, REASON_NOVELTY

# Trigger reason -> the header that frames why the world turned to the player.
_HEADER = {
    REASON_CRISIS: "A crisis gathers",
    REASON_NOVELTY: "Something new stirs",
    REASON_HISTORY: "History remembers",
    REASON_FLOOR: "The world turns to you",
}

# Volatile kind -> a plain noun for display.
_KIND_WORD = {
    OpportunityKind.NPC: "Person",
    OpportunityKind.FACTION: "Faction",
    OpportunityKind.LOCATION: "Place",
    OpportunityKind.WILDCARD: "Wildcard",
    OpportunityKind.LEGACY: "Legacy",
}

# The four signals, spoken. Order is the deterministic tie-break (Δ>Σ>Ω>Ρ).
_WHY = (
    ("delta", "tension rising"),
    ("sigma", "long neglected"),
    ("omega", "your past pulls here"),
    ("rho", "an ally awaits"),
)


def why_now(sig: Signals) -> str:
    """The dominant signal, in words (never a number). Deterministic tie-break."""
    return max(_WHY, key=lambda w: getattr(sig, w[0]))[1]


def _heritage_by_id(world, hid: str):
    return next((h for h in world.heritage if h.id == hid), None)


_ORDINALS = (
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
    "ninth",
    "tenth",
)


def _ordinal(n: int) -> str:
    """A life's 1-based ordinal, spoken. Lives are how the player counts time, so
    every surface that attributes a mark says 'your third life', never 'life-0002'
    and never a distance."""
    return _ORDINALS[n - 1] if 1 <= n <= len(_ORDINALS) else f"{n}th"


def _former_self_line(world, heritage) -> Optional[str]:
    """Recognition prose for a heritage that a *past life of the player* founded.
    Every life is the player reincarnated, so a heritage is always a former self's
    work; name it and the life that made it.

    The life is named by its *ordinal* ("your first life"), not by a distance.
    This line used to read "1 life ago" for a heritage founded by life 1 no matter
    which life met it, because the founder's ordinal was being spoken as though it
    were a count of lifetimes — so meeting life 1's work in life 4 claimed it was
    one life back. The ordinal is also what :func:`aftermath` and
    :func:`closing_page` use, so the same legacy is attributed the same way
    wherever the player meets it."""
    seed = seed_by_id(world, heritage.seed_id)
    if seed is None or seed.planted_by_life_id is None:
        return None
    idx = life_index(world).get(seed.planted_by_life_id)
    founder = next((lf for lf in world.lives if lf.id == seed.planted_by_life_id), None)
    talent = founder.talent.value if founder and founder.talent else "soul"
    whose = f"your {_ordinal(idx)} life" if idx else "a life you once lived"
    return (
        f'You come upon "{heritage_name(heritage)}" —\n'
        f"the work of {whose}, when you were a {talent}."
    )


def _era(world) -> str:
    dom = world.theme.dominant
    return f"an age of {dom.value}" if dom is not None else "an unsettled age"


def _top3(options):
    """The three highest-tension actionable options, deterministically ordered
    (tension desc, then target id to break ties without relying on input order)."""
    actionable = [o for o in options if o.opportunity is not None]
    return sorted(
        actionable, key=lambda o: (-o.opportunity.tension, o.opportunity.target_id)
    )[:3]


def _display_label(world, option) -> str:
    """A player-facing action label. The Execution layer's label is for logging
    and exposes internal ids for Legacy actions (e.g. 'Tend legacy:seed-0005');
    the player must never see those, so a Legacy action is named by its heritage,
    and every verb is Title-cased for a uniform reading."""
    opp = option.opportunity
    if opp is None:
        return option.label
    if opp.kind is OpportunityKind.LEGACY:
        her = _heritage_by_id(world, opp.target_id)
        if her is not None:
            return f"Tend the {heritage_name(her)}"
    label = option.label
    return label[:1].upper() + label[1:] if label else label


def heritage_label(world, heritage_id) -> Optional[str]:
    """The player-visible name of a heritage, or None. The recognition set is
    keyed by this (what the player saw), not the internal id, so two heritages
    that happen to share a generated name are recognized only once between them."""
    her = _heritage_by_id(world, heritage_id)
    return heritage_name(her) if her is not None else None


def recognizable_heritage(world, options, seen) -> Optional[str]:
    """The heritage id of a former self worth recognizing this turn, or None.

    Pure: reads ``seen`` (already-recognized heritage *names*), never mutates it —
    the caller owns the recognition state. Recognition is shown only the first
    time a name is met, so a re-encounter reads as discovery, not notification."""
    for o in _top3(options):
        opp = o.opportunity
        if opp.kind is OpportunityKind.LEGACY:
            her = _heritage_by_id(world, opp.target_id)
            if her is not None and heritage_name(her) not in seen:
                return opp.target_id
    return None


def turn_screen(world, life, options, reason: str, recognize_id: Optional[str] = None):
    """Render one juncture: header, the top options, and 'let it pass'. Pure and
    read-only on every argument.

    ``options`` are ExecutionOptions (P6 may offer 3-5; the display trims to the
    three highest-tension, since a juncture is a single decisive stroke). The
    free-action fallback (opportunity is None) is always rendered as ``[0]``.
    ``recognize_id``, if given, is a heritage id whose former-self line to show
    once above the choices; the caller decides first-time-ness (see
    :func:`recognizable_heritage`)."""
    header = _HEADER.get(reason, "The world turns to you")
    lines = [
        f"── Year {world.current_year} · age {life.age} · {_era(world)} ──"
        f"   ❰ {header} ❱",
    ]

    fallback = next((o for o in options if o.opportunity is None), None)
    top3 = _top3(options)

    if recognize_id is not None:
        her = _heritage_by_id(world, recognize_id)
        line = _former_self_line(world, her) if her else None
        if line:
            lines.append("")
            lines.append(line)

    lines.append("")
    for n, o in enumerate(top3, start=1):
        opp = o.opportunity
        kind = _KIND_WORD.get(opp.kind, "Chance")
        label = _display_label(world, o)
        lines.append(f"  [{n}] {label}   · {kind}   ({why_now(opp.signals)})")
    if fallback is not None:
        lines.append("  [0] Let this season pass.")

    return "\n".join(lines)


def option_index_for_choice(options, choice_number: int):
    """Map the displayed number (1..3, or 0) back to an index into ``options``.
    The display trims to top-3; this resolves the player's pick to the real
    option (0 -> the fallback)."""
    fallback_idx = next(
        (i for i, o in enumerate(options) if o.opportunity is None), None
    )
    top3 = _top3(options)
    if choice_number == 0:
        return fallback_idx
    if 1 <= choice_number <= len(top3):
        return options.index(top3[choice_number - 1])
    return None


def year_digest(world, year: int, action_phrase: str, promoted: bool) -> str:
    """One line for a year the world advanced on its own. Promotion years (a new
    heritage or a resolved wildcard) are emphasized."""
    mark = "  ✧ " if promoted else "  "
    return f"{mark}Year {year}  {action_phrase}"


def _founder_ordinal(row: dict) -> str:
    """'Life 2' (how ``heritage_rows`` reports a founder) spoken as 'second'."""
    match = re.match(r"Life (\d+)", row["origin_life"])
    return _ordinal(int(match.group(1))) if match else "own"


def _location_name(world, location_id) -> Optional[str]:
    if not location_id:
        return None
    return next((loc.name for loc in world.locations if loc.id == location_id), None)


def _event_line(world, node) -> str:
    """One event, as a reader would say it: the phrase, and where it happened."""
    where = _location_name(world, node.location_id)
    phrase = event_phrase(node)
    return f"{phrase} at {where}" if where else phrase


def _seed_ids(world, life) -> set:
    return {s.id for s in seeds_of_life(world, life.id)}


def _named_marks(world, life) -> list:
    """Heritage already promoted from this life's own seeds. Usually empty at the
    moment of death — which is the whole point of :func:`death_passage`."""
    mine = _seed_ids(world, life)
    return [h for h in world.heritage if h.seed_id in mine]


def death_passage(world, life) -> str:
    """One beat for a death: plain prose, and no verdict on what survived.

    This replaced a chain of four Markdown renderers that restated the same two
    facts and printed their own syntax (``#``, ``>``, ``**``) into a terminal.
    More importantly it replaced a *false* verdict. The P7 death screen asserted
    "nothing you built survived long after your death" at the one moment when
    nothing could have: heritage is promoted during the time-skip that follows,
    so the line was passed before the evidence existed and routinely contradicted
    the world's own chronicle — the same life would be listed there as the
    founder of institutions that outlasted the age.

    So a death says only what is true at a death: who mattered, and what is still
    in motion. What became of it is reported by the years (:func:`aftermath`),
    which is also where it belongs — a mark you can see land is not a legacy.
    """
    years = _age_at_death(life)
    lines = [
        f"─ {_title(world, life)} ─",
        "You lived a single season." if years == 0 else f"You lived {years} years.",
        "",
    ]

    bond = _strongest_bond(world, life)
    if bond is not None:
        verb, name, people = bond
        line = f"You {verb} {name}."
        if people > 1:
            line += f" In all, your choices fell across {people} lives."
        lines.append(line)

    marks = _named_marks(world, life)
    if marks:
        lines.append(
            f'What you built already bears a name: "{heritage_name(marks[0])}".'
        )

    pending = len(_seed_ids(world, life)) - len(marks)
    if pending > 0:
        # ``_cap_number`` only words the small counts; past that a bare figure
        # reads as a statistic, which is exactly what the P7 voice forbids.
        if pending > 9:
            lines.append("Much of what you set in motion outlives you, unfinished.")
        else:
            things = "thing" if pending == 1 else "things"
            lines.append(
                f"{_cap_number(pending)} {things} you set in motion "
                "outlive you, unfinished."
            )
        # The last life has no years left to decide anything; the closing page
        # follows immediately and answers it instead.
        if world.current_year < world.max_year:
            lines.append("What becomes of them is for the years to decide.")
    elif not marks:
        lines.append("You set nothing in motion that the world has yet taken up.")

    return "\n".join(lines)


def _echoes(world, life) -> list:
    """Events the world produced *after* this life ended, from something the life
    itself set in motion — a direct causal edge from one of its own seeds.

    Read-only and invents nothing: these events, their causes and their places
    are all already in the world. The player simply never saw them, because they
    happened after the death. Ordered by how loud they were (scale, then year),
    so the one worth naming comes first."""
    mine = _seed_ids(world, life)
    if not mine:
        return []
    end = life.death_year if life.death_year is not None else world.current_year
    out = [
        node
        for node in world.causal_nodes
        if node.year > end and any(e.from_id in mine for e in node.caused_by)
    ]
    out.sort(key=lambda n: (SCALE_ORDER.get(n.scale, 9), n.year, n.id))
    return out


def _hardened(world, promoted_seed_ids) -> list:
    """``(founder ordinal, [heritage, ...])`` for heritage that gained a name
    during the skip that just ran, grouped by the life that planted it and
    ordered by that life. A seed usually hardens a life or two after the one that
    planted it, so this is normally *not* the life that just died — which is the
    beat the design wants: felt time between the mark and finding it."""
    if not promoted_seed_ids:
        return []
    idx = life_index(world)
    by_founder: dict = {}
    for her in world.heritage:
        if her.seed_id not in promoted_seed_ids:
            continue
        seed = seed_by_id(world, her.seed_id)
        ordinal = idx.get(seed.planted_by_life_id) if seed else None
        if ordinal is None:
            continue
        by_founder.setdefault(ordinal, []).append(her)
    return sorted(by_founder.items())


def _and_more(n: int) -> str:
    """' — and N more.' / '.' — the tail that keeps a list to one line."""
    if n <= 0:
        return "."
    return f" — and {n} more." if n > 1 else " — and one more."


def aftermath(world, life, promoted_seed_ids) -> Optional[str]:
    """What the years that just passed did with what the player left, or None.

    This is the payoff the loop was missing. The first life's marks cannot be
    recognized in the first life — they need time to become anything — so before
    this beat existed the opening of the game was two lives of choices whose only
    feedback was a death screen saying nothing had survived. Measured over seeds
    1–30, the first recognition never landed before the *third* life.

    Two things can be reported, and both are real: events the player's own seeds
    caused after they died (available from the very first skip), and marks that
    hardened into a named legacy (usually one life later). Neither is invented:
    if there is nothing to say, this says nothing.
    """
    lines = []

    echoes = _echoes(world, life)
    if echoes:
        lines.append("In those years the world moved on what you left:")
        lines.append(f"  {_event_line(world, echoes[0])}{_and_more(len(echoes) - 1)}")

    for ordinal, marks in _hardened(world, promoted_seed_ids):
        if lines:
            lines.append("")
        names = ", ".join(f'"{heritage_name(h)}"' for h in marks[:2])
        lines.append(f"What your {_ordinal(ordinal)} life set down has taken a name:")
        lines.append(f"  {names}{_and_more(len(marks) - 2)}")

    return "\n".join(lines) if lines else None


def _by_origin(world, rows) -> list:
    """``[((founder ordinal, choice), [legacy name, ...]), ...]`` in row order.

    Marks are grouped by the life *and* the choice behind them, because that pair
    is what the player has to be able to say back ("my first life founded a
    council, and these three came of it")."""
    grouped: list = []
    for row in rows:
        key = (_founder_ordinal(row), row["origin_action"])
        living = " · still shaping the world" if _is_living(world, row) else ""
        if grouped and grouped[-1][0] == key:
            grouped[-1][1].append(row["name"] + living)
        else:
            grouped.append((key, [row["name"] + living]))
    return grouped


def closing_page(world) -> str:
    """The world's last page: how it ended, what outlived the player, and the way
    back in.

    ``play`` used to stop dead on "the world stands at its end" — no ending, no
    account of what was left, and no way to reach the chronicle without having
    passed ``--save`` and then running a second command. The two things the
    design asks a finished world to deliver (name the life that caused an event;
    want to leave a *different* mark next time) had nowhere to happen.
    """
    lives = len(world.lives)
    rows = heritage_rows(world)
    lines = [
        f"━━ The Chronicle of {place(world)} ━━",
        f"{world.current_year} years, {lives} {'life' if lives == 1 else 'lives'}. "
        f"It closed in {'an' if world.ending_class[0] in 'AEIOU' else 'a'} "
        f"{world.ending_class}.",
        "",
    ]

    if rows:
        lines.append("What you left behind:")
        # Grouped by the life and the choice that made them: that pairing is the
        # answer to "which life caused this?", and stating it once per group
        # keeps three legacies from three identical sentences (several marks
        # commonly come from one choice of one life).
        for (ordinal, action), names in _by_origin(world, rows[:3]):
            lines.append(f"  Your {ordinal} life chose to {action}. It left:")
            lines.extend(f"    {name}" for name in names)
        if len(rows) > 3:
            rest = len(rows) - 3
            lines.append(f"  … and {rest} more that outlived the lives that made them.")
    else:
        lines.append(
            "Nothing you built outlasted the age — but the world marked your passing."
        )

    lines.extend(
        [
            "",
            f"This was seed {world.seed}. Saved with --save, it can be read whole:",
            "  chronicle-forge explore RECIPE",
            "",
            "Another world is waiting. What will you leave in that one?",
            f"  chronicle-forge play --seed {world.seed + 1}",
        ]
    )
    return "\n".join(lines)


def skip_transition(skip: dict) -> str:
    """The years that pass between lives."""
    years = skip.get("years_run", 0)
    if years <= 0:
        return "Time holds its breath; the world stands at its end."
    return f"… {years} {'year' if years == 1 else 'years'} pass …"


def rebirth_intro(world, life) -> str:
    """The fated new life — given, never chosen."""
    talent = life.talent.value if life.talent else "soul"
    return (
        f"You are born again into {place(world)} —\n" f"a {talent}, in {_era(world)}."
    )
