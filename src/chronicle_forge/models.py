"""Authoritative pydantic data model for Chronicle Forge (section 11).

The world state plus the causal graph (CausalNode/CausalEdge/CausalSeed) are the
single source of truth. AI output is always derived and subordinate to these.
"""

from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BaseModel, Field

from .enums import (
    ActivationMode,
    CausalEdgeKind,
    DeathCause,
    DiscoveryType,
    EventScale,
    FactionType,
    HeritageType,
    LocationType,
    ManifestTargetKind,
    MemoryType,
    NPCTier,
    PlayerInteraction,
    SeedDomain,
    Talent,
    ThemeAxis,
    WildCardArchetype,
    WildCardStatus,
)

# 0..100 trait/score value.
Score = Annotated[int, Field(ge=0, le=100)]
# -100..100 signed relation/affinity value.
Signed = Annotated[int, Field(ge=-100, le=100)]


# --- NPCs ---------------------------------------------------------------


class Personality(BaseModel):
    """Drives action weighting in the rule-based utility function (section 6.3)."""

    brave: Score = 50
    greedy: Score = 50
    merciful: Score = 50
    ambitious: Score = 50
    devout: Score = 50
    cautious: Score = 50


class Relation(BaseModel):
    affinity: Signed = 0
    trust: Signed = 0
    fear: Signed = 0


class Lifecycle(BaseModel):
    age: int = 0
    occupation: str = "villager"
    faction_id: Optional[str] = None
    life_stage: str = "adult"


class Lineage(BaseModel):
    """Reserved for the Post-MVP descendant/bloodline system (section 10).

    Present in the schema so future "the orphan you raised has a descendant who
    becomes emperor" tracing needs no migration. Unused by MVP logic.
    """

    lineage_id: Optional[str] = None
    parent_ids: list[str] = Field(default_factory=list)
    generation: int = 0


class NPC(BaseModel):
    id: str
    name: str
    tier: NPCTier
    alive: bool = True
    personality: Personality = Field(default_factory=Personality)
    desires: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    relations: dict[str, Relation] = Field(default_factory=dict)
    traits: list[str] = Field(default_factory=list)
    lifecycle: Lifecycle = Field(default_factory=Lifecycle)
    lineage: Lineage = Field(default_factory=Lineage)


# --- World structure ----------------------------------------------------


class Faction(BaseModel):
    id: str
    type: FactionType
    name: str
    power: Score = 50
    ideology: str = ""
    relations: dict[str, Signed] = Field(default_factory=dict)


class Location(BaseModel):
    id: str
    type: LocationType
    name: str
    state: dict = Field(default_factory=dict)
    theme_affinity: Optional[ThemeAxis] = None


class ThemeSnapshot(BaseModel):
    """A point-in-time record of the World Theme, kept per generation step so
    the theme trajectory can be overlaid with personal history (section C)."""

    year: int
    axes: dict[ThemeAxis, int] = Field(default_factory=dict)
    dominant: Optional[ThemeAxis] = None


class WorldTheme(BaseModel):
    """Bidirectional world tendency (section C): emergent indicator that the
    player can also push."""

    axes: dict[ThemeAxis, int] = Field(default_factory=dict)
    history: list[ThemeSnapshot] = Field(default_factory=list)

    @property
    def dominant(self) -> Optional[ThemeAxis]:
        if not self.axes:
            return None
        return max(self.axes, key=self.axes.__getitem__)


# --- Player -------------------------------------------------------------


class PlayerPowers(BaseModel):
    """Shared reincarnator prerogatives (section A-1)."""

    imprint_enabled: bool = True
    foresight_enabled: bool = True
    bequest_enabled: bool = True
    manifest_charges: int = 1  # limited budget; amplifier, not generator


class Inheritance(BaseModel):
    knowledge: list[str] = Field(default_factory=list)
    titles: list[str] = Field(default_factory=list)
    traits: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


class Player(BaseModel):
    id: str
    current_life_id: Optional[str] = None
    powers: PlayerPowers = Field(default_factory=PlayerPowers)
    inherited: Inheritance = Field(default_factory=Inheritance)


# --- Lives --------------------------------------------------------------


class ActivityRecord(BaseModel):
    category: str  # ActivityCategory value
    world_year: int
    seed_id: Optional[str] = None


class Evaluation(BaseModel):
    """8 lenses (section 8). Culture/Mentoring/Heritage are the high-weight,
    long-term-impact lenses."""

    military: int = 0
    politics: int = 0
    economy: int = 0
    academia: int = 0
    culture: int = 0
    faith: int = 0
    mentoring: int = 0
    heritage: int = 0


class LifeSummary(BaseModel):
    """Generated at death; consumed by personal history, inheritance, and
    ending generation (review request)."""

    life_id: str
    title: str = ""
    dominant_axis: Optional[ThemeAxis] = None
    seeds_created: list[str] = Field(default_factory=list)
    heritage_created: list[str] = Field(default_factory=list)
    notable_events: list[str] = Field(default_factory=list)


class Life(BaseModel):
    id: str
    player_id: str
    birth_year: int
    age: int = 0  # current age during the life
    turns: int = 0  # action-time turns elapsed (drives aging)
    death_year: Optional[int] = None
    age_at_death: Optional[int] = None
    death_cause: Optional[DeathCause] = None
    talent: Optional[Talent] = None
    activity_log: list[ActivityRecord] = Field(default_factory=list)
    evaluation: Evaluation = Field(default_factory=Evaluation)
    summary: Optional[LifeSummary] = None


# --- Memory -------------------------------------------------------------


class Memory(BaseModel):
    """Structured (not natural-language) memory record (section 7.1)."""

    id: str
    subject_id: str
    actor_id: str
    type: MemoryType
    valence: Signed
    intensity: Score
    decay_rate: float = 0.05
    event_ref: Optional[str] = None
    timestamp: int = 0  # world year


# --- Causal graph (core, section 9) ------------------------------------


class CausalSeed(BaseModel):
    """A tagged player action that can later become the parent of events."""

    id: str
    domain: SeedDomain
    magnitude: Score
    target_id: Optional[str] = None
    maturation_time: int = 0  # years until it can fire
    decay: float = 0.0
    planted_year: int = 0
    planted_by_life_id: Optional[str] = None
    fired: bool = False
    # Firing model (section 9.3). P1/P2 use GUARANTEED; PROBABILISTIC is for P3.
    activation_mode: ActivationMode = ActivationMode.GUARANTEED
    base_probability: float = 1.0


class CausalEdge(BaseModel):
    from_id: str  # cause node or seed id
    to_id: str  # effect node id
    weight: int = 1
    kind: CausalEdgeKind = CausalEdgeKind.ENABLE


class CausalNode(BaseModel):
    id: str
    scale: EventScale
    domain: SeedDomain
    year: int
    title: str = ""
    location_id: Optional[str] = None
    actors: list[str] = Field(default_factory=list)
    caused_by: list[CausalEdge] = Field(default_factory=list)


class HeritageNode(BaseModel):
    """Promoted long-lived causal seed; the basis of the Heritage lens (section D).

    Reach (breadth) and longevity (depth in time) are tracked separately; the
    composite ``heritage_score`` is computed from both (see heritage.py).
    """

    id: str
    seed_id: str
    type: HeritageType
    reach: int = 0  # breadth: transitive descendant events in the causal DAG
    longevity: int = 0  # depth: years the legacy has propagated since its event
    heritage_score: int = 0  # = round(weight * longevity * (1 + reach))


# --- Discovery / dungeon link (section B) ------------------------------


class Discovery(BaseModel):
    id: str
    type: DiscoveryType
    location_id: str
    theme_affinity: ThemeAxis
    seed_id: Optional[str] = None


# --- WildCards (section 8, designed for N) -----------------------------


class WildCardInteraction(BaseModel):
    """Future multi-WildCard hook; unused in MVP."""

    other_id: str
    relation: str  # "rival" | "resonant"


class WildCard(BaseModel):
    id: str
    name: str
    archetype: WildCardArchetype
    status: WildCardStatus = WildCardStatus.DORMANT
    ignition_condition: str = ""
    trajectory: list[str] = Field(default_factory=list)
    impact_vector: dict[ThemeAxis, int] = Field(default_factory=dict)
    player_interaction: Optional[PlayerInteraction] = None
    interactions_with: list[WildCardInteraction] = Field(default_factory=list)


class WildCardRegistry(BaseModel):
    wildcards: list[WildCard] = Field(default_factory=list)


# --- Manifest amplifier (section A redesign) ---------------------------


class ManifestEffect(BaseModel):
    """An amplifier of existing causality. Never inserts a CausalNode; it only
    applies bounded multipliers to an existing target. Neutral defaults (1.0/0)
    mean "no amplification", which keeps the causal graph intact (R1).
    """

    target_kind: ManifestTargetKind
    target_id: str
    weight_mult: float = 1.0
    firing_prob_mult: float = 1.0
    maturation_delta: int = 0
    heritage_growth_mult: float = 1.0
    trajectory_influence_mult: float = 1.0


# --- World aggregate ----------------------------------------------------


class World(BaseModel):
    id: str
    seed: int
    current_year: int = 0
    max_year: int
    theme: WorldTheme = Field(default_factory=WorldTheme)
    population: int = 0  # Tier-B crowd as a number, not individuals
    player: Player
    locations: list[Location] = Field(default_factory=list)
    factions: list[Faction] = Field(default_factory=list)
    npcs: list[NPC] = Field(default_factory=list)
    wildcards: WildCardRegistry = Field(default_factory=WildCardRegistry)
    lives: list[Life] = Field(default_factory=list)
    memories: list[Memory] = Field(default_factory=list)
    seeds: list[CausalSeed] = Field(default_factory=list)
    causal_nodes: list[CausalNode] = Field(default_factory=list)
    heritage: list[HeritageNode] = Field(default_factory=list)
    discoveries: list[Discovery] = Field(default_factory=list)
    ending_class: Optional[str] = None


class Chronicle(BaseModel):
    world_id: str
    generated_text: str = ""
    ending_class: Optional[str] = None
