"""Inheritance derivation and mechanical bonuses (P3.5, Priority 1).

A life leaves behind knowledge / skills / traits derived from how it was lived,
and those carry forward (Bequest) to make later lives measurably stronger — the
roguelite "build that compounds across reincarnations". This replaces the old
title-only, effect-less inheritance.
"""

from __future__ import annotations

from .enums import ActivityCategory
from .models import Life, Player

# Tags are plain strings stored in Player.inherited.{knowledge,skills,traits}.
KNOWLEDGE_TECHNICAL = "technical_lore"
KNOWLEDGE_COMMERCE = "commerce_ledger"
KNOWLEDGE_SACRED = "sacred_texts"
KNOWLEDGE_CIVIC = "civic_code"
SKILL_MARTIAL = "martial"
SKILL_CRAFT = "craft"
TRAIT_MENTORSHIP = "mentorship"
TRAIT_PATRON = "patron"
TRAIT_VISIONARY = "visionary"
TRAIT_EXPLORER = "explorer_instinct"

EVAL_BONUS = 6  # evaluation bonus when a relevant tag is inherited
MAGNITUDE_BONUS = 12  # seed magnitude bonus when expertise is inherited
DISCOVERY_BONUS = 12  # discovery magnitude bonus
COMBAT_BONUS = 12  # combat power bonus


def derive_inheritance(life: Life, discovery_count: int = 0) -> dict:
    """Return the knowledge/skills/traits a life bequeaths, from its evaluation."""
    ev = life.evaluation
    knowledge: list[str] = []
    skills: list[str] = []
    traits: list[str] = []

    if ev.academia >= 40:
        knowledge.append(KNOWLEDGE_TECHNICAL)
    if ev.economy >= 40:
        knowledge.append(KNOWLEDGE_COMMERCE)
    if ev.faith >= 40:
        knowledge.append(KNOWLEDGE_SACRED)
    if ev.politics >= 30:
        knowledge.append(KNOWLEDGE_CIVIC)
    if ev.military >= 40:
        skills.append(SKILL_MARTIAL)
    if ev.culture >= 30:
        skills.append(SKILL_CRAFT)
    if ev.mentoring >= 30:
        traits.append(TRAIT_MENTORSHIP)
    if ev.culture >= 40:
        traits.append(TRAIT_PATRON)
    if ev.heritage >= 30:
        traits.append(TRAIT_VISIONARY)
    if discovery_count >= 2:
        traits.append(TRAIT_EXPLORER)

    return {"knowledge": knowledge, "skills": skills, "traits": traits}


def _has(player: Player, *, knowledge=None, skills=None, traits=None) -> bool:
    inh = player.inherited
    if knowledge and knowledge in inh.knowledge:
        return True
    if skills and skills in inh.skills:
        return True
    if traits and traits in inh.traits:
        return True
    return False


# category -> (knowledge/skill/trait tag that boosts it)
_ACTIVITY_TAG = {
    ActivityCategory.RESEARCH: ("knowledge", KNOWLEDGE_TECHNICAL),
    ActivityCategory.EXPLORATION: ("traits", TRAIT_EXPLORER),
    ActivityCategory.EDUCATION: ("traits", TRAIT_MENTORSHIP),
    ActivityCategory.COMMERCE: ("knowledge", KNOWLEDGE_COMMERCE),
    ActivityCategory.RELIGION: ("knowledge", KNOWLEDGE_SACRED),
    ActivityCategory.POLITICS: ("knowledge", KNOWLEDGE_CIVIC),
    ActivityCategory.CONSTRUCTION: ("skills", SKILL_CRAFT),
}


def activity_bonus(player: Player, category: ActivityCategory) -> tuple[int, int]:
    """Return (evaluation_bonus, magnitude_bonus) for an activity given inheritance."""
    tag = _ACTIVITY_TAG.get(category)
    if tag and _has(player, **{tag[0]: tag[1]}):
        return EVAL_BONUS, MAGNITUDE_BONUS
    return 0, 0


def discovery_bonus(player: Player) -> int:
    """Extra discovery magnitude from inherited technical lore / explorer instinct."""
    bonus = 0
    if _has(player, knowledge=KNOWLEDGE_TECHNICAL):
        bonus += DISCOVERY_BONUS
    if _has(player, traits=TRAIT_EXPLORER):
        bonus += DISCOVERY_BONUS // 2
    return bonus


def combat_bonus(player: Player) -> int:
    """Extra combat power from inherited martial skill."""
    return COMBAT_BONUS if _has(player, skills=SKILL_MARTIAL) else 0
