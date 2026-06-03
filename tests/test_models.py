"""Schema-level guarantees that encode key design decisions."""

from __future__ import annotations

from chronicle_forge.enums import ActivityCategory, EvaluationLens, ManifestTargetKind
from chronicle_forge.models import Evaluation, ManifestEffect
from chronicle_forge.profiles import ACTIVITY_PROFILES


def test_evaluation_has_eight_lenses_including_heritage():
    fields = set(Evaluation.model_fields)
    assert fields == {
        "military",
        "politics",
        "economy",
        "academia",
        "culture",
        "faith",
        "mentoring",
        "heritage",
    }


def test_manifest_is_a_neutral_amplifier_by_default():
    # Neutral defaults mean "no amplification" -> never fabricates causality (R1).
    eff = ManifestEffect(target_kind=ManifestTargetKind.SEED, target_id="seed-0000")
    assert eff.weight_mult == 1.0
    assert eff.firing_prob_mult == 1.0
    assert eff.maturation_delta == 0
    assert eff.heritage_growth_mult == 1.0
    assert eff.trajectory_influence_mult == 1.0


def test_all_activity_categories_have_a_profile():
    assert set(ACTIVITY_PROFILES) == set(ActivityCategory)


def test_heritage_activities_feed_the_heritage_lens():
    education = ACTIVITY_PROFILES[ActivityCategory.EDUCATION]
    construction = ACTIVITY_PROFILES[ActivityCategory.CONSTRUCTION]
    assert EvaluationLens.HERITAGE in education.secondary_lenses
    assert EvaluationLens.HERITAGE in construction.secondary_lenses
