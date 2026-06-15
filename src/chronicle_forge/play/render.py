"""Rendering for P8 — turn screens, the yearly digest, and life transitions.

All output is player-facing prose built from existing data: it reuses the P7
renderers (death, chronicle, timeline, legacy) and the deterministic ``labels``,
adds no new aggregation, and never mutates the world. Signals are spoken in
words, never as raw numbers (the P7 discipline).

Former-self recognition is shown only the *first* time a given heritage is
encountered within a life — re-meeting a past self should feel like discovery,
not a notification. The per-life ``seen`` set is volatile and lives in the play
session, never in the world.
"""

from __future__ import annotations

from typing import Optional

from ..opportunity import OpportunityKind, Signals
from ..reporting._data import life_index, place, seed_by_id
from ..reporting.experience import (
    dead_summary,
    legacy_view,
    life_chronicle,
    life_timeline,
)
from ..reporting.labels import heritage_name
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


def _lives_ago(n: int) -> str:
    """A human count of lifetimes, correctly singular ('1 life ago')."""
    return "1 life ago" if n == 1 else f"{n} lives ago"


def _former_self_line(world, heritage) -> Optional[str]:
    """Recognition prose for a heritage that a *past life of the player* founded.
    Every life is the player reincarnated, so a heritage is always a former self's
    work; name it and the life that made it."""
    seed = seed_by_id(world, heritage.seed_id)
    if seed is None or seed.planted_by_life_id is None:
        return None
    idx = life_index(world).get(seed.planted_by_life_id)
    founder = next((lf for lf in world.lives if lf.id == seed.planted_by_life_id), None)
    talent = founder.talent.value if founder and founder.talent else "soul"
    when = f"a life you lived, {_lives_ago(idx)}" if idx else "a life you once lived"
    return (
        f'You come upon "{heritage_name(heritage)}" —\n'
        f"the work of {when}, when you were a {talent}."
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


def death_transition(world, life) -> str:
    """The death -> history -> legacy reading, chaining the P7 renderers."""
    return "\n\n".join(
        [
            dead_summary(world, life),
            life_chronicle(world, life),
            life_timeline(world, life),
            legacy_view(world, life),
        ]
    )


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
