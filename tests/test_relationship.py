"""Relationships: what two people have between them, read off what happened.

What this pins: a tie exists only where the world has evidence for it; shared
time is the union of the routines that actually put two people together; the
gaps between them are not shared; genealogy is directional and buys no shared
years; and nothing — a routine ending, a death, a hand-over to the next life —
takes any of it away.

Nothing here asks the engine how two people *felt*. It never will.
"""

from __future__ import annotations

import pytest

from chronicle_forge import (
    config,
    population as pop,
    relationship as rel,
    routine as rt,
)
from chronicle_forge.enums import DeathCause, RoutineKind
from chronicle_forge.life import begin_life, end_life
from chronicle_forge.macro import advance_to_next_life
from chronicle_forge.relationship import GenealogicalRole, RelationshipEvidence
from chronicle_forge.worldgen import generate_world


def _world():
    """A played world, the person being played, and two of their neighbours."""
    world = generate_world(seed=4, max_year=120)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    here = [
        p
        for p in pop.adults(world)
        if p.id != actor.id and p.lifecycle.location_id == actor.lifecycle.location_id
    ]
    return world, life, actor, here[0], here[1]


def _tie(world, a, b):
    return rel.relationship_between(world, a.id, b.id)


# --- evidence ----------------------------------------------------------------


def test_two_strangers_have_no_relationship():
    world, _life, actor, neighbour, _other = _world()
    assert _tie(world, actor, neighbour) is None


def test_nobody_has_a_relationship_with_themselves():
    world, _life, actor, _n, _o = _world()
    assert rel.relationship_between(world, actor.id, actor.id) is None


def test_working_somewhere_is_not_a_relationship_with_the_people_there():
    """Sharing a village is not sharing a life."""
    world, _life, actor, neighbour, _other = _world()
    rt.begin_routine(world, RoutineKind.WORK_AT)
    rt.continue_routine(world, 10)
    assert _tie(world, actor, neighbour) is None
    # The neighbour still has their own family; what they do not have is a
    # single year of shared routine with anybody.
    for tie in rel.relationships_of(world, neighbour.id):
        assert RelationshipEvidence.SHARED_ROUTINE not in tie.evidence
        assert tie.shared_years == 0


@pytest.mark.parametrize("kind", [RoutineKind.WORK_WITH, RoutineKind.ASSOCIATE_WITH])
def test_spending_years_beside_somebody_is_evidence(kind):
    world, _life, actor, neighbour, _other = _world()
    rt.begin_routine(world, kind, target_person_id=neighbour.id)
    rt.continue_routine(world, 7)

    tie = _tie(world, actor, neighbour)
    assert tie is not None
    assert tie.evidence == (RelationshipEvidence.SHARED_ROUTINE,)
    assert tie.routine_kinds == (kind,)
    assert tie.shared_years == 7


# --- which routines count as time together -----------------------------------


def test_only_the_two_named_kinds_count_as_shared_time():
    """The set is spelled out in the relationship module on purpose, so that
    adding a person-facing routine kind is never silently a decision about
    what "we spent years together" means."""
    assert rel.SHARED_TIME_ROUTINE_KINDS == (
        RoutineKind.WORK_WITH,
        RoutineKind.ASSOCIATE_WITH,
    )


def test_a_new_person_facing_kind_does_not_become_shared_time_by_itself(monkeypatch):
    """Widen what a routine may aim at a person, and relationships must not
    widen with it. A future one-shot or hostile kind has to be admitted here
    deliberately, not inherited from ``routine.PERSON_KINDS``."""
    world, _life, actor, neighbour, _other = _world()
    # Pretend WORK_AT became person-facing, as a future kind would be.
    monkeypatch.setattr(
        rt,
        "PERSON_KINDS",
        rt.PERSON_KINDS + (RoutineKind.WORK_AT,),
    )
    rt.begin_routine(world, RoutineKind.WORK_AT, target_person_id=neighbour.id)
    rt.continue_routine(world, 9)

    assert rt.active_routine(world).target_person_id == neighbour.id  # it was allowed
    assert _tie(world, actor, neighbour) is None  # and it bought no shared history
    assert neighbour.id not in {
        t.person_b_id for t in rel.relationships_of(world, actor.id)
    }


# --- how much time, exactly ---------------------------------------------------


def test_a_seven_year_routine_is_seven_shared_years():
    world, _life, actor, neighbour, _other = _world()
    start = world.current_year
    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=neighbour.id)
    rt.continue_routine(world, 7)

    tie = _tie(world, actor, neighbour)
    assert tie.shared_years == 7
    assert tie.first_shared_year == start
    assert tie.last_shared_year_exclusive == start + 7  # the first year apart


def test_beginning_a_routine_is_not_a_year_together():
    world, _life, actor, neighbour, _other = _world()
    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=neighbour.id)
    tie = _tie(world, actor, neighbour)
    assert tie.shared_years == 0
    assert tie.sharing_now


def test_changing_away_in_the_same_year_leaves_nothing_shared():
    world, _life, actor, neighbour, _other = _world()
    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=neighbour.id)
    rt.change_routine(world, RoutineKind.WORK_AT)
    assert _tie(world, actor, neighbour).shared_years == 0


def test_a_routine_still_running_counts_the_years_already_lived():
    world, _life, actor, neighbour, _other = _world()
    rt.begin_routine(world, RoutineKind.ASSOCIATE_WITH, target_person_id=neighbour.id)
    rt.continue_routine(world, 4)
    tie = _tie(world, actor, neighbour)
    assert tie.shared_years == 4  # four completed years, not five
    assert tie.sharing_now


def test_two_separated_stretches_add_up_and_the_gap_between_does_not():
    """The Phase 7 life: seven years together, three apart, five together."""
    world, _life, actor, neighbour, _other = _world()
    start = world.current_year

    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=neighbour.id)
    rt.continue_routine(world, 7)
    rt.change_routine(world, RoutineKind.WORK_AT)  # three years elsewhere
    rt.continue_routine(world, 3)
    rt.change_routine(world, RoutineKind.ASSOCIATE_WITH, target_person_id=neighbour.id)
    rt.continue_routine(world, 5)

    tie = _tie(world, actor, neighbour)
    assert tie.shared_years == 12  # 7 + 5; the three apart are not shared
    assert len(tie.shared_spans) == 2
    assert tie.routine_kinds == (RoutineKind.ASSOCIATE_WITH, RoutineKind.WORK_WITH)
    assert tie.first_shared_year == start
    assert tie.last_shared_year_exclusive == start + 15
    assert tie.sharing_now


def test_overlapping_stretches_are_counted_once():
    """One player cannot currently produce an overlap, but the rule must not
    quietly assume that: a year lived once is one shared year."""
    world, _life, actor, neighbour, _other = _world()
    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=neighbour.id)
    rt.continue_routine(world, 8)
    first = rt.routines_of(world, actor.id)[0]
    # A second span over the same years, as a future rule might allow.
    world.routines.append(
        first.model_copy(
            update={"id": "routine-overlap", "start_year": 4, "end_year": 12}
        )
    )
    tie = _tie(world, actor, neighbour)
    assert tie.shared_years == 12  # the union [0,12), not 8 + 8
    assert tie.first_shared_year == 0
    assert tie.last_shared_year_exclusive == 12


# --- it reads the same from either side ----------------------------------------


def test_shared_history_is_the_same_fact_from_both_sides():
    world, _life, actor, neighbour, _other = _world()
    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=neighbour.id)
    rt.continue_routine(world, 6)

    forward = _tie(world, actor, neighbour)
    backward = _tie(world, neighbour, actor)
    assert backward is not None
    assert backward.shared_years == forward.shared_years == 6
    assert backward.shared_spans == forward.shared_spans
    assert backward.routine_kinds == forward.routine_kinds
    assert backward.first_shared_year == forward.first_shared_year
    assert backward.last_shared_year_exclusive == forward.last_shared_year_exclusive
    assert backward.sharing_now == forward.sharing_now


# --- genealogy ------------------------------------------------------------------


def _parent_and_child(world):
    child = next(p for p in world.npcs if p.lineage.parent_ids)
    return pop.person_by_id(world, child.lineage.parent_ids[0]), child


def test_a_parent_is_a_relationship_without_any_shared_routine():
    world = generate_world(seed=4)
    parent, child = _parent_and_child(world)
    tie = rel.relationship_between(world, child.id, parent.id)
    assert tie is not None
    assert tie.evidence == (RelationshipEvidence.GENEALOGY,)
    assert tie.genealogical_role is GenealogicalRole.PARENT


def test_genealogy_invents_no_time_together():
    """The world knows who someone's parent is. It does not know they were
    ever in the same room, so it does not say they were."""
    world = generate_world(seed=4)
    parent, child = _parent_and_child(world)
    tie = rel.relationship_between(world, child.id, parent.id)
    assert tie.shared_years == 0
    assert tie.shared_spans == ()
    assert tie.routine_kinds == ()
    assert tie.first_shared_year is None
    assert tie.last_shared_year_exclusive is None
    assert tie.sharing_now is False


def test_the_role_inverts_with_the_direction_of_the_question():
    world = generate_world(seed=4)
    parent, child = _parent_and_child(world)
    assert (
        rel.relationship_between(world, child.id, parent.id).genealogical_role
        is GenealogicalRole.PARENT
    )
    assert (
        rel.relationship_between(world, parent.id, child.id).genealogical_role
        is GenealogicalRole.CHILD
    )


def test_a_grandparent_is_ancestry_not_a_relationship():
    world = generate_world(seed=4, max_year=60)
    begin_life(world)
    for _ in range(40):
        from chronicle_forge.macro import advance_year

        advance_year(world)
    grandchild = next(
        p
        for p in reversed(world.npcs)
        if p.lineage.generation >= 2 and p.lineage.parent_ids
    )
    parent = pop.person_by_id(world, grandchild.lineage.parent_ids[0])
    grandparent = pop.person_by_id(world, parent.lineage.parent_ids[0])
    assert rel.relationship_between(world, grandchild.id, grandparent.id) is None
    assert rel.relationship_between(world, grandchild.id, parent.id) is not None


def test_both_grounds_are_reported_when_both_hold():
    """A person who spends years beside their own parent. The first playable
    person is a founder with no family, so this is the *second* life: somebody
    born in the world, whose parent is still alive where they grew up."""
    world, life, _actor, _n, _o = _world()
    end_life(world, life, DeathCause.COMBAT)
    _skip, second = advance_to_next_life(world)
    me = pop.person_by_id(world, second.person_id)
    parent = pop.person_by_id(world, me.lineage.parent_ids[0])
    # Nobody moves, so a child grew up where their parent still is.
    assert parent.alive and parent.lifecycle.location_id == me.lifecycle.location_id

    listed = [
        p.id
        for p in pop.adults(world)
        if p.lifecycle.location_id == me.lifecycle.location_id
    ]
    assert parent.id in listed
    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=parent.id)
    rt.continue_routine(world, 5)

    tie = _tie(world, me, parent)
    assert set(tie.evidence) == {
        RelationshipEvidence.SHARED_ROUTINE,
        RelationshipEvidence.GENEALOGY,
    }
    assert tie.genealogical_role is GenealogicalRole.PARENT
    assert tie.shared_years == 5


# --- history outlives everybody --------------------------------------------------


def test_ending_a_routine_does_not_end_the_relationship():
    world, _life, actor, neighbour, other = _world()
    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=neighbour.id)
    rt.continue_routine(world, 9)
    rt.change_routine(world, RoutineKind.ASSOCIATE_WITH, target_person_id=other.id)
    rt.continue_routine(world, 4)

    tie = _tie(world, actor, neighbour)
    assert tie.shared_years == 9
    assert tie.sharing_now is False


def test_the_other_persons_death_keeps_every_year_they_shared():
    world, _life, actor, neighbour, _other = _world()
    neighbour.lifecycle.birth_year = world.current_year - (config.LIFESPAN_CAP - 4)
    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=neighbour.id)
    rt.continue_routine(world, 10)
    assert not neighbour.alive

    tie = _tie(world, actor, neighbour)
    assert tie.shared_years == 4
    assert tie.sharing_now is False
    assert tie.a_alive and not tie.b_alive


def test_the_players_own_death_keeps_every_year_they_shared():
    world, life, actor, neighbour, _other = _world()
    rt.begin_routine(world, RoutineKind.ASSOCIATE_WITH, target_person_id=neighbour.id)
    rt.continue_routine(world, 11)
    end_life(world, life, DeathCause.COMBAT)

    tie = _tie(world, actor, neighbour)
    assert tie.shared_years == 11
    assert tie.sharing_now is False
    assert not tie.a_alive


def test_the_next_life_does_not_inherit_the_last_ones_people():
    """Player continuity is not character relationship continuity."""
    world, life, actor, neighbour, _other = _world()
    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=neighbour.id)
    rt.continue_routine(world, 8)
    end_life(world, life, DeathCause.COMBAT)
    _skip, nxt = advance_to_next_life(world)

    assert rel.relationship_between(world, nxt.person_id, neighbour.id) is None
    predecessor = _tie(world, actor, neighbour)
    assert predecessor.shared_years == 8  # still history, just not theirs


# --- the listing ------------------------------------------------------------------


def test_only_people_the_evidence_names_are_listed():
    world, _life, actor, neighbour, _other = _world()
    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=neighbour.id)
    rt.continue_routine(world, 5)

    ties = rel.relationships_of(world, actor.id)
    listed = {t.person_b_id for t in ties}
    assert neighbour.id in listed
    assert len(listed) < len(world.npcs)  # not a world of two hundred relationships
    for tie in ties:
        assert tie.evidence
        assert tie.person_a_id == actor.id


def test_the_listing_is_ordered_and_repeatable():
    world, _life, actor, neighbour, other = _world()
    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=neighbour.id)
    rt.continue_routine(world, 3)
    rt.change_routine(world, RoutineKind.ASSOCIATE_WITH, target_person_id=other.id)
    rt.continue_routine(world, 3)

    first = rel.relationships_of(world, actor.id)
    assert [t.person_b_id for t in first] == sorted(t.person_b_id for t in first)
    assert [t.person_b_id for t in first] == [
        t.person_b_id for t in rel.relationships_of(world, actor.id)
    ]


def test_a_person_the_world_never_heard_of_has_no_relationships():
    world, _life, _a, _n, _o = _world()
    assert rel.relationships_of(world, "npc-9999") == []
    assert rel.relationship_between(world, "npc-9999", "npc-0000") is None


# --- determinism --------------------------------------------------------------------


def _projection(seed):
    world = generate_world(seed=seed, max_year=120)
    life = begin_life(world)
    actor = pop.person_by_id(world, life.person_id)
    here = [
        p
        for p in pop.adults(world)
        if p.id != actor.id and p.lifecycle.location_id == actor.lifecycle.location_id
    ]
    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=here[0].id)
    rt.continue_routine(world, 6)
    rt.change_routine(world, RoutineKind.ASSOCIATE_WITH, target_person_id=here[1].id)
    rt.continue_routine(world, 4)
    return [
        (
            t.person_b_id,
            t.evidence,
            t.shared_years,
            t.routine_kinds,
            t.first_shared_year,
            t.last_shared_year_exclusive,
            t.sharing_now,
            t.genealogical_role,
        )
        for t in rel.relationships_of(world, actor.id)
    ]


def test_the_same_history_projects_the_same_relationships():
    assert _projection(4) == _projection(4)


def test_nothing_in_the_projection_is_a_feeling():
    """A guard against the thing this module must never become."""
    world, _life, actor, neighbour, _other = _world()
    rt.begin_routine(world, RoutineKind.WORK_WITH, target_person_id=neighbour.id)
    rt.continue_routine(world, 20)
    fields = set(vars(_tie(world, actor, neighbour)))
    assert not fields & {
        "affinity",
        "trust",
        "fear",
        "friendship",
        "closeness",
        "score",
        "sentiment",
        "hostility",
    }
