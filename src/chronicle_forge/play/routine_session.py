"""The played life: choose how to live, then live it for years.

This is the human loop of the new core. The player is a real sixteen-year-old
the world already holds; they pick a way of living from the people and the
place actually around them, and then spend years in it. Time moves only when
they say so, and only through ``routine.continue_routine`` — which is to say
only through ``advance_year``, one year at a time.

It deliberately shares nothing with the old juncture loop. It never calls
``select_opportunities``, ``expand_options``, ``JunctureGate``,
``execute_option`` or ``perform_activity``; it emits no Option, no Outcome and
no CausePath. That loop still runs the auto-player and the goldens
(:mod:`play.session`), and is reached from here never.

What it does **not** do: tell the player what any of it meant. A routine that
ended because the person beside them died is reported as that and nothing more.
No consequence is promised, no bond is named, no number goes up.
"""

from __future__ import annotations

import sys
from typing import Callable, List, Optional

from .. import config
from .. import population as pop
from ..enums import RoutineEndReason, RoutineKind
from ..life import begin_life
from ..macro import time_skip
from ..population import NoSuccessor
from ..routine import (
    RoutineRefused,
    active_routine,
    begin_routine,
    change_routine,
    continue_routine,
)
from ..worldgen import generate_world
from . import view

Reader = Callable[[], Optional[str]]
Writer = Callable[[str], None]

# A session guard, not a game rule: enough to prove a multi-year routine
# without letting one line of input swallow a century.
MAX_CONTINUE_YEARS = 10

HELP = """commands
  work at                 spend your years working here
  work with <n>           spend them working beside someone
  associate with <n>      spend them in someone's company
  continue [years]        live the years (1-%d, default 1)
  status                  where you are, who is here, how you live
  history                 the years you have spent, and with whom
  help                    this list
""" % (MAX_CONTINUE_YEARS,)

_END_REASON = {
    RoutineEndReason.TARGET_DIED: "They died. That way of living ended with them.",
    RoutineEndReason.ACTOR_DIED: "You died.",
    RoutineEndReason.WORLD_ENDED: "The chronicle reaches its end here.",
    RoutineEndReason.PLAYER_CHANGED: "You left that life behind.",
}

_KIND_PHRASE = {
    RoutineKind.WORK_AT: "working",
    RoutineKind.WORK_WITH: "working beside",
    RoutineKind.ASSOCIATE_WITH: "in the company of",
}


def _stdin_reader() -> Optional[str]:
    try:
        return input()
    except EOFError:
        return None


def _stdout_writer(text: str) -> None:
    sys.stdout.write(text)


# --- what the player reads -------------------------------------------------


def _routine_line(r: view.RoutineView) -> str:
    where = f"in {r.location_name}"
    who = f" {r.target_name}" if r.target_name else ""
    span = f"year {r.start_year}" + (
        f"-{r.end_year}" if r.end_year is not None else " onward"
    )
    years = f"{r.years} year" + ("" if r.years == 1 else "s")
    return f"{_KIND_PHRASE[r.kind]}{who} {where} · {span} · {years}"


def render_status(world) -> str:
    me = view.self_view(world)
    if me is None:
        return "You are no one at the moment.\n"
    lines = [
        f"Year {me.year}. You are {me.name}, {me.age}, in {me.location_name}.",
    ]
    if me.parents:
        lines.append("Your parent: " + ", ".join(me.parents) + ".")
    if me.routine is None:
        lines.append("You have not settled into anything yet.")
    else:
        lines.append("You are " + _routine_line(me.routine) + ".")
    people = view.nearby(world)
    if people:
        lines.append("")
        lines.append("Here with you:")
        for i, p in enumerate(people, start=1):
            lines.append(f"  [{i}] {p.name}, {p.age}")
    else:
        lines.append("")
        lines.append("No grown person is here with you.")
    return "\n".join(lines) + "\n"


def render_history(world, person_id: str) -> str:
    spans = view.history(world, person_id)
    lines: List[str] = []
    if not spans:
        lines.append("You have not yet spent your years on anything.")
    else:
        lines.append("Your years:")
        for span in spans:
            lines.append("  " + _routine_line(span))
    bonds = view.ties(world, person_id)
    if bonds:
        lines.append("")
        lines.append("People your life has touched:")
        for tie in bonds:
            parts = []
            if tie.shared_years:
                parts.append(
                    f"{tie.shared_years} year"
                    + ("" if tie.shared_years == 1 else "s")
                    + " together"
                )
            if tie.parent_or_child:
                parts.append(f"your {tie.parent_or_child}")
            if not tie.alive:
                parts.append("now dead")
            lines.append(f"  {tie.name} — " + ", ".join(parts))
    return "\n".join(lines) + "\n"


def _render_death(world, life) -> str:
    # Read the body by id: the life is over, so nobody is "current" any more.
    person = pop.person_by_id(world, life.person_id)
    name = person.name if person is not None else "You"
    return f"\n{name} died in year {life.death_year}, aged {life.age_at_death}.\n"


def _render_closing(world) -> str:
    n = len(world.lives)
    lives = "1 life" if n == 1 else f"{n} lives"
    return (
        f"\nThe chronicle of {world.locations[0].name} closes in year "
        f"{world.current_year}, after {lives}.\n"
    )


# --- commands --------------------------------------------------------------


def _target(world, rest: str):
    """Resolve a listed number to the person it names, or raise."""
    people = view.nearby(world)
    try:
        n = int(rest.strip())
    except ValueError:
        raise RoutineRefused(f"{rest.strip()!r} is not one of the listed numbers")
    if not 1 <= n <= len(people):
        raise RoutineRefused(f"nobody is listed as [{n}]")
    return people[n - 1].person_id


def _parse_years(rest: str) -> int:
    text = rest.strip()
    if not text:
        return 1
    try:
        years = int(text)
    except ValueError:
        raise RoutineRefused(f"{text!r} is not a number of years")
    if years < 1:
        raise RoutineRefused("a year is the smallest thing you can spend")
    if years > MAX_CONTINUE_YEARS:
        raise RoutineRefused(
            f"{MAX_CONTINUE_YEARS} years is as far as you may go at once"
        )
    return years


def _start(world, kind: RoutineKind, target_person_id: Optional[str]) -> str:
    """Begin or change a way of living. Never moves the clock."""
    if active_routine(world) is None:
        routine = begin_routine(world, kind, target_person_id)
    else:
        routine = change_routine(world, kind, target_person_id)
    return "Now " + _routine_line(view._routine_view(world, routine)) + ".\n"


def _continue(world, years: int) -> str:
    """Live the years. The clock is ``advance_year``, reached one year at a
    time inside ``continue_routine``; nothing here touches ``current_year``."""
    result = continue_routine(world, years)
    ran = result["years_run"]
    lines = [
        (
            f"{ran} year" + ("" if ran == 1 else "s") + " pass."
            if ran
            else "No year passes."
        )
    ]
    if result["ended"]:
        reason = result["end_reason"]
        lines.append(_END_REASON.get(reason, "That way of living ended."))
        total = result["years"]
        lines.append(
            f"It lasted {total} year" + ("" if total == 1 else "s") + " in all."
        )
    return "\n".join(lines) + "\n"


def handle(world, line: str) -> str:
    """Run one command against the world. Returns what the player reads.

    ``status`` and ``history`` move no time; only ``continue`` does, and only
    through the routine domain.
    """
    text = " ".join(line.strip().lower().split())
    if not text:
        return ""
    if text in ("help", "?"):
        return HELP
    if text == "status":
        return render_status(world)
    if text == "history":
        me = view.current_person(world)
        return render_history(world, me.id) if me is not None else ""
    if text == "work at":
        return _start(world, RoutineKind.WORK_AT, None)
    if text.startswith("work with"):
        return _start(
            world, RoutineKind.WORK_WITH, _target(world, text[len("work with") :])
        )
    if text.startswith("associate with"):
        return _start(
            world,
            RoutineKind.ASSOCIATE_WITH,
            _target(world, text[len("associate with") :]),
        )
    if text == "continue" or text.startswith("continue "):
        return _continue(world, _parse_years(text[len("continue") :]))
    raise RoutineRefused(f"{text!r} is not something you can do. Try 'help'.")


# --- the loop ---------------------------------------------------------------


def run_routine_world(
    seed: int,
    *,
    reader: Optional[Reader] = None,
    writer: Optional[Writer] = None,
    life_cap: int = 60,
    max_year: int = config.WORLD_MAX_YEARS,
):
    """Play a world as a succession of lived lives. Returns the finished world.

    The run ends when the world reaches its horizon, when the player closes
    their input, or when the world has nobody left of an age to be taken up.
    It never advances a year the player did not ask for: a life with no command
    is a life that does not move, which is the opposite of the old loop's
    decades of silence.
    """
    reader = reader or _stdin_reader
    writer = writer or _stdout_writer

    world = generate_world(seed, max_year=max_year)
    writer(HELP)

    while world.current_year < world.max_year and len(world.lives) < life_cap:
        try:
            life = begin_life(world)
        except NoSuccessor as exc:
            writer(f"\nNo one is of an age to be lived as: {exc}\n")
            break
        writer("\n")
        writer(render_status(world))

        closed = _live_one(world, life, reader, writer)
        if not closed:  # the player left
            break
        if life.alive:  # the horizon came first; the person does not die
            break

        writer(_render_death(world, life))
        writer(render_history(world, life.person_id))
        skip = time_skip(world)
        writer(f"\n{skip['years_run']} years pass in the world.\n")
        if skip["world_ended"]:
            break

    writer(_render_closing(world))
    return world


def _live_one(world, life, reader: Reader, writer: Writer) -> bool:
    """One life's command loop. Returns False if the player closed their input
    (the run stops), True if the life or the world ended on its own."""
    while life.alive and world.current_year < world.max_year:
        writer("\n> ")
        line = reader()
        writer("\n")
        if line is None:  # the player is done; the world is not advanced for them
            return False
        try:
            writer(handle(world, line))
        except RoutineRefused as exc:
            writer(f"{exc}\n")
    return True
