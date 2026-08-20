"""The P8 driver — a thin wiring layer for a reincarnating, human-played world.

This module only *connects* existing pieces: it runs the world through the same
opportunity-mode engine as autoplay, asks the gate whether each turn is a
juncture, renders and prompts on the ones that are, and chains the P7 renderers
at death. It owns exactly one piece of volatile state of its own — the
former-self recognition set, which spans the whole run so a past self is
recognized only once, ever — and nothing else.

It contains no game logic, no RNG of its own, and no clock. World advancement,
selection (P6), execution (the funnel), and interpretation (P7) are reused
verbatim. With a player who always lets the season pass (or an EOF reader),
every turn delegates to the auto-chooser and the run is byte-identical to
``simulate_world(seed, mode="opportunity")``.
"""

from __future__ import annotations

import sys
from typing import Callable, Optional

from .. import config
from ..ending import classify_ending
from ..enums import DeathCause, Talent
from ..execution import (
    EXECUTION_SALT,
    execute_option,
    expand_options,
    make_auto_chooser,
)
from ..life import (
    TURNS_PER_YEAR,
    begin_life,
    draw_natural_span,
    end_life,
    lifespan_reached,
)
from ..macro import derive_rng, time_skip
from ..opportunity import OpportunitySession, select_opportunities
from ..worldgen import generate_world
from . import render
from .gate import JunctureGate
from .human import make_human_chooser

Reader = Callable[[], Optional[str]]
Writer = Callable[[str], None]


def _stdin_reader() -> Optional[str]:
    try:
        return input()
    except EOFError:
        return None


def _stdout_writer(text: str) -> None:
    sys.stdout.write(text)


def _emit(writer: Writer, block: str) -> None:
    writer(block.rstrip("\n") + "\n\n")


def run_human_world(
    seed: int,
    *,
    reader: Optional[Reader] = None,
    writer: Optional[Writer] = None,
    life_cap: int = 60,
    social_memory: bool = False,
    observer=None,
):
    """Play a whole reincarnating world. Mirrors ``simulate_world``'s
    opportunity-mode outer loop exactly (derive rng per life, live, time-skip,
    classify ending), so determinism and the seed42 golden assets are preserved.
    ``social_memory`` (P11-B L2) gates the cross-life decay/bias pipeline; off
    (default) the run is byte-identical to today. Returns the finished world.

    ``observer`` (I-1b) is an optional listener that is handed the *data* behind
    each beat at the moment the beat is spoken — see :mod:`play.beats`. It is
    told, never asked: it cannot choose, cannot write, and cannot change what is
    rendered, so with no observer (the default) the run is byte-identical and the
    goldens are untouched. It exists because the client used to recover this data
    by regex-parsing the transcript, which could carry one beat out of five."""
    reader = reader or _stdin_reader
    writer = writer or _stdout_writer
    seen_recognitions: set = set()  # spans the run: a former self is met once

    world = generate_world(seed)
    while world.current_year < world.max_year and len(world.lives) < life_cap:
        rng = derive_rng(world, len(world.lives), salt=EXECUTION_SALT)
        life = _live_one(
            world, rng, reader, writer, seen_recognitions, social_memory, observer
        )

        # The skip is where marks harden into heritage, so what the years did
        # with the player's work can only be told *after* it runs — telling it at
        # the death instead is the contradiction `render.death_passage` documents.
        before = {h.seed_id for h in world.heritage}
        skip = time_skip(world, life, social_memory)
        # A skip that ran no years has nothing to say; the closing page follows.
        transition = render.skip_transition(skip)
        if transition:
            _emit(writer, transition)
        if observer is not None:
            observer.on_years(world, skip)
        promoted = {h.seed_id for h in world.heritage} - before
        block = render.aftermath(world, life, promoted)
        if block is not None:
            _emit(writer, block)
        if observer is not None:
            # Told even when the prose says nothing: an aftermath that names no
            # mark is the majority case (73 of 117 measured), and the surface
            # has to render that silence rather than skip the beat.
            observer.on_aftermath(world, life, promoted)

        if skip["world_ended"]:
            break
    classify_ending(world)
    _emit(writer, render.closing_page(world))
    if observer is not None:
        observer.on_closing(world)
    return world


def _live_one(
    world,
    rng,
    reader: Reader,
    writer: Writer,
    seen: set,
    social_memory: bool = False,
    observer=None,
):
    """One life: birth → juncture-gated turns → death reading. Reproduces the
    opportunity-mode life mechanics (lifespan, per-action combat death) exactly;
    the only added behaviour is asking the player at junctures. The auto-chooser
    is consulted on every non-ask turn and whenever the player lets the season
    pass, so the RNG stream matches autoplay unless the player actually acts."""
    talent = rng.choice(list(Talent))
    life = begin_life(world, talent=talent)
    _emit(writer, render.rebirth_intro(world, life))
    if observer is not None:
        observer.on_rebirth(world, life)

    death_year = life.birth_year + draw_natural_span(rng)
    per_action_combat = config.COMBAT_DEATH_PROB_PER_YEAR / TURNS_PER_YEAR

    session = OpportunitySession()
    auto = make_auto_chooser(rng)
    human = make_human_chooser(reader, writer, on_let_pass=auto)
    gate = JunctureGate()
    combat_death = False

    while (
        world.current_year < world.max_year
        and world.current_year < death_year
        and not lifespan_reached(life)
    ):
        opps = select_opportunities(world, life, session, social_memory)
        options = expand_options(opps, world, life, rng)

        remaining = min(death_year, world.max_year) - world.current_year
        decision = gate.decide(
            world,
            opps,
            session.turn_index,
            world.current_year,
            is_final_turn=remaining <= 1,
        )

        if decision.ask:
            recognize = render.recognizable_heritage(world, options, seen)
            _emit(
                writer,
                render.turn_screen(world, life, options, decision.reason, recognize),
            )
            if observer is not None:
                observer.on_juncture(world, life, options, decision.reason, recognize)
            if recognize is not None:
                # The session owns recognition state, keyed by the player-visible
                # name so a former self is recognized once across the whole run.
                seen.add(render.heritage_label(world, recognize))
            index = human(options)
        else:
            index = auto(options)

        choice = options[index]
        # Read the seeds before the verb runs, so what THIS act set in motion is
        # a measured delta rather than a guess. Only when someone is listening
        # and only at a juncture: the turns the world takes on its own are not
        # entries in anyone's book.
        seeds_before = (
            {s.id for s in world.seeds}
            if observer is not None and decision.ask
            else None
        )
        execute_option(world, life, choice)
        if seeds_before is not None:
            observer.on_outcome(
                world,
                life,
                options,
                choice,
                {s.id for s in world.seeds} - seeds_before,
            )
        selected_id = choice.opportunity.target_id if choice.opportunity else None
        session.commit_turn(opps, selected_id)

        if rng.random() < per_action_combat:
            combat_death = True
            break

    end_life(world, life, DeathCause.COMBAT if combat_death else DeathCause.LIFESPAN)
    _emit(writer, render.death_passage(world, life))
    if observer is not None:
        observer.on_death(world, life)
    return life
