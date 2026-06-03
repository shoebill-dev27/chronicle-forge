"""Activity profiles (section 4.4).

Each of the 8 life activity categories is the single funnel through which
evaluation, causal seeds, and World Theme pushes emerge. Encoding this as a
static table lets play archetypes (scholar / merchant / adventurer / politician
/ educator) be emergent rather than hard-coded classes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .enums import ActivityCategory, EvaluationLens, SeedDomain, Talent, ThemeAxis


class ActivityProfile(BaseModel):
    category: ActivityCategory
    primary_lens: EvaluationLens
    secondary_lenses: list[EvaluationLens] = Field(default_factory=list)
    seed_domain: SeedDomain
    theme_push: dict[ThemeAxis, int] = Field(default_factory=dict)
    talent_affinity: Talent


ACTIVITY_PROFILES: dict[ActivityCategory, ActivityProfile] = {
    ActivityCategory.EXPLORATION: ActivityProfile(
        category=ActivityCategory.EXPLORATION,
        primary_lens=EvaluationLens.ACADEMIA,  # cross-cutting "discovery"
        seed_domain=SeedDomain.DISCOVERY,
        theme_push={ThemeAxis.INNOVATION: 1},
        talent_affinity=Talent.EXPLORER,
    ),
    ActivityCategory.COMBAT: ActivityProfile(
        category=ActivityCategory.COMBAT,
        primary_lens=EvaluationLens.MILITARY,
        seed_domain=SeedDomain.MILITARY,
        theme_push={ThemeAxis.WARFARE: 2},
        talent_affinity=Talent.WARRIOR,
    ),
    ActivityCategory.RESEARCH: ActivityProfile(
        category=ActivityCategory.RESEARCH,
        primary_lens=EvaluationLens.ACADEMIA,
        seed_domain=SeedDomain.TECHNOLOGY,
        theme_push={ThemeAxis.INNOVATION: 2},
        talent_affinity=Talent.SCHOLAR,
    ),
    ActivityCategory.EDUCATION: ActivityProfile(
        category=ActivityCategory.EDUCATION,
        primary_lens=EvaluationLens.MENTORING,
        secondary_lenses=[EvaluationLens.HERITAGE],
        seed_domain=SeedDomain.HERITAGE,
        theme_push={ThemeAxis.CULTURE: 2},
        talent_affinity=Talent.MENTOR,
    ),
    ActivityCategory.POLITICS: ActivityProfile(
        category=ActivityCategory.POLITICS,
        primary_lens=EvaluationLens.POLITICS,
        seed_domain=SeedDomain.GOVERNANCE,
        theme_push={ThemeAxis.GOVERNANCE: 2},
        talent_affinity=Talent.STATESMAN,
    ),
    ActivityCategory.COMMERCE: ActivityProfile(
        category=ActivityCategory.COMMERCE,
        primary_lens=EvaluationLens.ECONOMY,
        seed_domain=SeedDomain.ECONOMY,
        theme_push={ThemeAxis.COMMERCE: 2},
        talent_affinity=Talent.MERCHANT,
    ),
    ActivityCategory.RELIGION: ActivityProfile(
        category=ActivityCategory.RELIGION,
        primary_lens=EvaluationLens.FAITH,
        seed_domain=SeedDomain.FAITH,
        theme_push={ThemeAxis.FAITH: 2},
        talent_affinity=Talent.PRIEST,
    ),
    ActivityCategory.CONSTRUCTION: ActivityProfile(
        category=ActivityCategory.CONSTRUCTION,
        primary_lens=EvaluationLens.CULTURE,
        secondary_lenses=[EvaluationLens.HERITAGE],
        seed_domain=SeedDomain.MONUMENT,
        theme_push={ThemeAxis.CULTURE: 2},
        talent_affinity=Talent.BUILDER,
    ),
}
