"""Deterministic MVP world generation (P0).

Given a seed, produces a byte-identical world: 1 village + 1 dungeon + field
nodes, 4 factions (Lord/Merchant/Religious/Adventurer), 10 named NPCs (2 Tier-S
important + 8 Tier-A), and 1 WildCard. All names are procedurally composed from
fictional syllables so there is no correspondence to real peoples/nations (R8).
"""

from __future__ import annotations

from . import config
from .enums import (
    FactionType,
    LocationType,
    NPCTier,
    ThemeAxis,
    WildCardArchetype,
    WildCardStatus,
)
from .models import (
    Faction,
    Lifecycle,
    Location,
    NPC,
    Personality,
    Player,
    WildCard,
    WildCardRegistry,
    World,
    WorldTheme,
)
from .rng import DeterministicRNG, IdFactory

# Fictional syllable pools for procedural names (no real-world correspondence).
_NAME_PREFIXES = ["Ka", "Ve", "Tor", "Lyn", "Mor", "Sel", "Bra", "Dun", "Ash", "Wre"]
_NAME_SUFFIXES = [
    "dris",
    "wen",
    "mar",
    "thas",
    "lin",
    "gar",
    "veth",
    "ric",
    "non",
    "dal",
]

_FACTION_SPECS = [
    (FactionType.LORD, "House of the Iron Seat", "order through hereditary rule"),
    (FactionType.MERCHANT, "Coin Concord", "prosperity through free exchange"),
    (FactionType.RELIGIOUS, "Ember Communion", "salvation through the old flame"),
    (FactionType.ADVENTURER, "Free Lanterns", "freedom through the open road"),
]

# archetype, primary axis, secondary axis, trajectory
_WILDCARD_SPECS = [
    (
        WildCardArchetype.INVENTOR,
        ThemeAxis.INNOVATION,
        ThemeAxis.COMMERCE,
        ["perfects a lost formula", "founds a workshop", "sparks a magical revolution"],
    ),
    (
        WildCardArchetype.CONQUEROR,
        ThemeAxis.WARFARE,
        ThemeAxis.GOVERNANCE,
        ["raises a warband", "sacks a rival", "forges a war-state"],
    ),
    (
        WildCardArchetype.PROPHET,
        ThemeAxis.FAITH,
        ThemeAxis.CULTURE,
        ["preaches a new creed", "gathers disciples", "founds a faith"],
    ),
    (
        WildCardArchetype.MERCHANT_PRINCE,
        ThemeAxis.COMMERCE,
        ThemeAxis.GOVERNANCE,
        ["corners a trade", "founds a guild", "builds a mercantile bloc"],
    ),
    (
        WildCardArchetype.REFORMER,
        ThemeAxis.GOVERNANCE,
        ThemeAxis.CULTURE,
        ["drafts a new law", "rallies the people", "remakes the state"],
    ),
]


def _make_name(rng: DeterministicRNG) -> str:
    return rng.choice(_NAME_PREFIXES) + rng.choice(_NAME_SUFFIXES).strip()


def _make_personality(rng: DeterministicRNG) -> Personality:
    return Personality(
        brave=rng.randint(10, 90),
        greedy=rng.randint(10, 90),
        merciful=rng.randint(10, 90),
        ambitious=rng.randint(10, 90),
        devout=rng.randint(10, 90),
        cautious=rng.randint(10, 90),
    )


def _initial_theme() -> WorldTheme:
    return WorldTheme(axes={axis: 20 for axis in ThemeAxis})


def generate_world(seed: int, max_year: int = config.DEV_WORLD_MAX_YEARS) -> World:
    """Build a deterministic MVP world from an integer seed."""
    rng = DeterministicRNG(seed)
    ids = IdFactory()

    # --- Locations (ordering fixed for determinism) ---
    village = Location(
        id=ids.next("loc"),
        type=LocationType.VILLAGE,
        name="Hollowfen",
    )
    dungeon = Location(
        id=ids.next("loc"),
        type=LocationType.DUNGEON,
        name="The Sunken Vault",
        theme_affinity=ThemeAxis.INNOVATION,
    )
    fields = [
        Location(id=ids.next("loc"), type=LocationType.FIELD, name="Greywind Moor"),
        Location(id=ids.next("loc"), type=LocationType.FIELD, name="Thornreach"),
    ]
    locations = [village, dungeon, *fields]

    # --- Factions ---
    factions = [
        Faction(
            id=ids.next("fac"),
            type=ftype,
            name=fname,
            power=rng.randint(30, 70),
            ideology=ideology,
        )
        for ftype, fname, ideology in _FACTION_SPECS
    ]

    # --- NPCs: first MVP_IMPORTANT_NPC_COUNT are Tier-S, rest Tier-A ---
    npcs: list[NPC] = []
    for i in range(config.MVP_NPC_COUNT):
        tier = NPCTier.S if i < config.MVP_IMPORTANT_NPC_COUNT else NPCTier.A
        faction = rng.choice(factions)
        age = rng.randint(16, 60)
        npcs.append(
            NPC(
                id=ids.next("npc"),
                name=_make_name(rng),
                tier=tier,
                personality=_make_personality(rng),
                lifecycle=Lifecycle(
                    age=age,
                    faction_id=faction.id,
                    birth_year=-age,  # world starts at year 0
                ),
            )
        )

    # --- WildCard registry: one per archetype so no single axis dominates ---
    wildcards = WildCardRegistry(
        wildcards=[
            WildCard(
                id=ids.next("wc"),
                name=_make_name(rng),
                archetype=archetype,
                status=WildCardStatus.DORMANT,
                ignition_condition=(
                    f"{primary.value}_theme high and player seeds in {primary.value}"
                ),
                trajectory=list(trajectory),
                impact_vector={primary: 30, secondary: 10},
            )
            for archetype, primary, secondary, trajectory in _WILDCARD_SPECS
        ]
    )

    player = Player(id=ids.next("player"))

    return World(
        id=f"world-{seed}",
        seed=seed,
        max_year=max_year,
        theme=_initial_theme(),
        population=rng.randint(200, 400),
        player=player,
        locations=locations,
        factions=factions,
        npcs=npcs,
        wildcards=wildcards,
    )
