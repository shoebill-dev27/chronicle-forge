"""Human-readable, deterministic labels for seeds, events, and heritage.

The goal is a chain a person can *retell* — "a warrior taught the faith, it
became the Doctrine of the Long Dawn, and the world ended in a Theocratic Age" —
instead of `seed-0014 -> node-0012 -> her:seed-0014`.

Everything here is rules-based and deterministic (a stable integer derived from
the seed id indexes fixed word pools). No randomness, no AI. Read-only.
"""

from __future__ import annotations

from ..enums import ActivityCategory, DiscoveryType, HeritageType, SeedDomain
from ..models import CausalNode, HeritageNode, World

# --- seed action phrases -----------------------------------------------

_ACTIVITY_PHRASE = {
    ActivityCategory.EXPLORATION: "explore the wild places",
    ActivityCategory.COMBAT: "wage a battle",
    ActivityCategory.RESEARCH: "pursue new knowledge",
    ActivityCategory.EDUCATION: "teach the villagers",
    ActivityCategory.POLITICS: "found a local council",
    ActivityCategory.COMMERCE: "open a trade route",
    ActivityCategory.RELIGION: "spread the faith",
    ActivityCategory.CONSTRUCTION: "raise a great work",
}

_DISCOVERY_PHRASE = {
    DiscoveryType.TECH: "unearth a lost technique",
    DiscoveryType.RELIC: "recover a holy relic",
    DiscoveryType.SEAL: "disturb a sealed power",
    DiscoveryType.LORE: "uncover ancient lore",
}

_DOMAIN_PHRASE = {
    SeedDomain.DISCOVERY: "make a discovery",
    SeedDomain.MILITARY: "take up arms",
    SeedDomain.TECHNOLOGY: "advance a craft",
    SeedDomain.HERITAGE: "mentor a successor",
    SeedDomain.GOVERNANCE: "shape the law",
    SeedDomain.ECONOMY: "build wealth",
    SeedDomain.FAITH: "spread the faith",
    SeedDomain.MONUMENT: "raise a monument",
}

# --- event phrases ------------------------------------------------------

_EVENT_PHRASE = {
    SeedDomain.DISCOVERY: "a discovery echoes outward",
    SeedDomain.MILITARY: "war breaks out",
    SeedDomain.TECHNOLOGY: "a new craft spreads",
    SeedDomain.HERITAGE: "a school takes hold",
    SeedDomain.GOVERNANCE: "the order of rule shifts",
    SeedDomain.ECONOMY: "trade flourishes",
    SeedDomain.FAITH: "the faith takes root",
    SeedDomain.MONUMENT: "a monument rises",
}

# --- heritage naming ----------------------------------------------------

_ADJ = [
    "Ember",
    "Iron",
    "Silver",
    "Hollow",
    "Ashen",
    "Verdant",
    "Gilded",
    "Sunken",
    "Thorn",
    "Grey",
]
_NOUN = [
    "Seven Fires",
    "Open Road",
    "Old Flame",
    "Quiet Hand",
    "Long Dawn",
    "Stone Pact",
    "First Light",
    "Deep Vow",
    "Bright Ledger",
    "Last Gate",
]

_HERITAGE_TEMPLATE = {
    HeritageType.THOUGHT: "Doctrine of the {noun}",
    HeritageType.SCHOOL: "Academy of the {noun}",
    HeritageType.TECHNOLOGY: "The {adj} Engine",
    HeritageType.INSTITUTION: "Order of the {noun}",
    HeritageType.HEIR: "The {adj} Line",
    HeritageType.MONUMENT: "The {adj} Monument",
}


def _sid_num(seed_id: str) -> int:
    digits = "".join(ch for ch in seed_id if ch.isdigit())
    return int(digits) if digits else sum(ord(c) for c in seed_id)


def _seed_category_map(world: World) -> dict:
    out = {}
    for life in world.lives:
        for rec in life.activity_log:
            if rec.seed_id:
                out[rec.seed_id] = rec.category
    return out


def seed_label(world: World, seed_id: str) -> str:
    """Short human verb-phrase for what a seed *was* (the player's action)."""
    cat = _seed_category_map(world).get(seed_id)
    if cat is not None:
        try:
            return _ACTIVITY_PHRASE[ActivityCategory(cat)]
        except (ValueError, KeyError):
            pass
    disc = next((d for d in world.discoveries if d.seed_id == seed_id), None)
    if disc is not None:
        return _DISCOVERY_PHRASE.get(disc.type, "make a discovery")
    seed = next((s for s in world.seeds if s.id == seed_id), None)
    if seed is not None:
        return _DOMAIN_PHRASE.get(seed.domain, seed.domain.value)
    return seed_id


def event_phrase(node: CausalNode) -> str:
    return _EVENT_PHRASE.get(node.domain, node.title)


def heritage_name(heritage: HeritageNode) -> str:
    """A deterministic proper name, e.g. 'Doctrine of the Long Dawn'."""
    n = _sid_num(heritage.seed_id)
    adj = _ADJ[n % len(_ADJ)]
    noun = _NOUN[n % len(_NOUN)]
    template = _HERITAGE_TEMPLATE.get(heritage.type, "The {adj} Legacy")
    return template.format(adj=adj, noun=noun)
