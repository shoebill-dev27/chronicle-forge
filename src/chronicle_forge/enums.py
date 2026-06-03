"""Enumerations shared across the Chronicle Forge data model.

All values are string-backed so that serialized worlds are stable and
human-readable. See docs/design.md for the conceptual meaning of each type.
"""

from __future__ import annotations

from enum import Enum


class EvaluationLens(str, Enum):
    """The 8 evaluation lenses (section 8). Culture/Mentoring/Heritage are
    weighted high to enforce "long-term causal impact > combat power"."""

    MILITARY = "military"
    POLITICS = "politics"
    ECONOMY = "economy"
    ACADEMIA = "academia"
    CULTURE = "culture"
    FAITH = "faith"
    MENTORING = "mentoring"
    HERITAGE = "heritage"


class ActivityCategory(str, Enum):
    """Life activity templates (section 4.4). Play archetypes emerge from the
    distribution of these, rather than being hard-coded classes."""

    EXPLORATION = "exploration"
    COMBAT = "combat"
    RESEARCH = "research"
    EDUCATION = "education"
    POLITICS = "politics"
    COMMERCE = "commerce"
    RELIGION = "religion"
    CONSTRUCTION = "construction"


class SeedDomain(str, Enum):
    """Domain of a causal seed / event."""

    DISCOVERY = "discovery"
    MILITARY = "military"
    TECHNOLOGY = "technology"
    HERITAGE = "heritage"
    GOVERNANCE = "governance"
    ECONOMY = "economy"
    FAITH = "faith"
    MONUMENT = "monument"


class ThemeAxis(str, Enum):
    """World Theme axes (section C)."""

    WARFARE = "warfare"
    INNOVATION = "innovation"
    FAITH = "faith"
    COMMERCE = "commerce"
    GOVERNANCE = "governance"
    CULTURE = "culture"


class Talent(str, Enum):
    """Per-life build talent (section A-2), discarded on death."""

    SCHOLAR = "scholar"
    WARRIOR = "warrior"
    MERCHANT = "merchant"
    STATESMAN = "statesman"
    MENTOR = "mentor"
    EXPLORER = "explorer"
    PRIEST = "priest"
    BUILDER = "builder"


class FactionType(str, Enum):
    LORD = "lord"
    MERCHANT = "merchant"
    RELIGIOUS = "religious"
    ADVENTURER = "adventurer"


class NPCTier(str, Enum):
    """Compute-cost tiers (section 6.1). B is a crowd number, not individuals."""

    S = "S"  # important: rules + bounded AI decisions
    A = "A"  # named: rule-based FSM
    B = "B"  # crowd: aggregate statistics only


class LocationType(str, Enum):
    VILLAGE = "village"
    DUNGEON = "dungeon"
    FIELD = "field"


class MemoryType(str, Enum):
    SAVED = "saved"
    BETRAYED = "betrayed"
    EDUCATED = "educated"
    BEREAVED = "bereaved"
    RESCUED = "rescued"
    HUMILIATED = "humiliated"


class CausalEdgeKind(str, Enum):
    ENABLE = "enable"
    TRIGGER = "trigger"
    AMPLIFY = "amplify"
    SUPPRESS = "suppress"


class EventScale(str, Enum):
    LARGE = "large"
    MEDIUM = "medium"
    SMALL = "small"


class HeritageType(str, Enum):
    SCHOOL = "school"
    THOUGHT = "thought"
    TECHNOLOGY = "technology"
    INSTITUTION = "institution"
    HEIR = "heir"
    MONUMENT = "monument"


class WildCardArchetype(str, Enum):
    REVOLUTIONARY = "revolutionary"
    PROPHET = "prophet"
    INVENTOR = "inventor"
    CONQUEROR = "conqueror"
    ZEALOT = "zealot"


class WildCardStatus(str, Enum):
    DORMANT = "dormant"
    IGNITED = "ignited"
    RESOLVED = "resolved"
    DEAD = "dead"


class PlayerInteraction(str, Enum):
    SUPPORT = "support"
    ELIMINATE = "eliminate"
    EXPLOIT = "exploit"
    IGNORE = "ignore"


class DiscoveryType(str, Enum):
    TECH = "tech"
    RELIC = "relic"
    SEAL = "seal"
    LORE = "lore"


class ManifestTargetKind(str, Enum):
    """What a Manifest amplifier can target (section A redesign). Manifest never
    creates a CausalNode; it only amplifies existing causality."""

    SEED = "seed"
    HERITAGE = "heritage"
    WILDCARD = "wildcard"
    THEME_AXIS = "theme_axis"


class DeathCause(str, Enum):
    LIFESPAN = "lifespan"
    COMBAT = "combat"
    CHOICE = "choice"


class ActivationMode(str, Enum):
    """How a causal seed fires (section 9.3). P1/P2 use GUARANTEED only;
    PROBABILISTIC firing is introduced in P3 when world state drives probability."""

    GUARANTEED = "guaranteed"
    PROBABILISTIC = "probabilistic"
