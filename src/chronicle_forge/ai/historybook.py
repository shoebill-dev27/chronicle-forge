"""History book generation (P4.1).

Turns a finished World into a readable Chronicle that emphasizes causality and
centers the player's heritage. The rules engine has already decided everything
that happened; this only narrates it. The world is never mutated.
"""

from __future__ import annotations

from typing import Optional

from ..causal import CausalGraph
from ..heritage import _triggered_node
from ..models import Chronicle, World
from .client import AIClient, AIRequest, AIResponse, get_ai_client

_SYSTEM = (
    "You are the chronicler of a wholly fictional world. Write an engaging "
    "history that emphasizes cause and effect and centers the deeds and legacy "
    "of the world's single reincarnator. Do not reference any real people, "
    "nations, religions, or political groups. Do not invent events that are not "
    "in the provided data; only narrate what is given."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "chapters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": ["heading", "text"],
            },
        },
    },
    "required": ["title", "chapters"],
}


def _assemble(structured: dict) -> str:
    parts = [structured.get("title", "Chronicle")]
    for chapter in structured.get("chapters", []):
        parts.append(f"\n## {chapter['heading']}\n{chapter['text']}")
    return "\n".join(parts)


def _place(world: World) -> str:
    village = next(
        (loc for loc in world.locations if loc.type.value == "village"), None
    )
    return village.name if village else world.id


def _life_impact(world: World, life_id: str) -> int:
    owned = {s.id for s in world.seeds if s.planted_by_life_id == life_id}
    return sum(
        1 for n in world.causal_nodes if any(e.from_id in owned for e in n.caused_by)
    )


def _heritage_rows(world: World, top: int = 3) -> list[tuple]:
    graph = CausalGraph.from_world(world)
    rows = []
    for h in world.heritage:
        founding = _triggered_node(world, h.seed_id)
        derived = len(graph.descendants(founding.id)) if founding else 0
        rows.append(
            (h.heritage_score, h.type.value, h.seed_id, h.longevity, h.reach, derived)
        )
    rows.sort(key=lambda r: (-r[0], r[2]))
    return rows[:top]


def _dossier(world: World) -> str:
    place = _place(world)
    hist = world.theme.history
    arc = (
        f"{hist[0].dominant.value} -> {hist[len(hist) // 2].dominant.value} -> "
        f"{hist[-1].dominant.value}"
        if hist
        else "n/a"
    )
    lines = [
        f"World: {place} (id {world.id}), years 0..{world.current_year}, "
        f"ending: {world.ending_class}",
        f"Theme arc (dominant): {arc}",
        f"Lives: {len(world.lives)}; events: {len(world.causal_nodes)}; "
        f"heritage: {len(world.heritage)}",
        "",
        "Reincarnator's lives:",
    ]
    for life in world.lives:
        s = life.summary
        lines.append(
            f"- {s.title if s else life.id}: talent {life.talent.value if life.talent else '-'}, "
            f"born y{life.birth_year} died y{life.death_year} "
            f"({life.death_cause.value if life.death_cause else '-'}), "
            f"dominant {s.dominant_axis.value if s and s.dominant_axis else '-'}, "
            f"world impact {_life_impact(world, life.id)} events"
        )
    lines.append("")
    lines.append("Greatest legacies (heritage, with downstream events):")
    for score, htype, seed, lon, reach, derived in _heritage_rows(world):
        lines.append(
            f"- {htype} (seed {seed}): score {score}, propagated {lon}y, "
            f"reach {reach}, {derived} downstream events"
        )
    resolved = [
        wc
        for wc in world.wildcards.wildcards
        if wc.status.value in ("ignited", "resolved")
    ]
    if resolved:
        lines.append("")
        lines.append("World-shaking figures (WildCards):")
        for wc in resolved:
            lines.append(f"- {wc.name} the {wc.archetype.value}: {wc.status.value}")
    return "\n".join(lines)


def _fallback_response(world: World, dossier: str) -> AIResponse:
    """Deterministic, template-based chronicle that still reads as a story."""
    place = _place(world)
    hist = world.theme.history
    opening_axis = hist[0].dominant.value if hist else "uncertainty"
    closing_axis = hist[-1].dominant.value if hist else "silence"

    chapters = []
    chapters.append(
        {
            "heading": "Prologue",
            "text": (
                f"Over {world.current_year} years the land of {place} passed through "
                f"{len(world.lives)} lives of its one reincarnated soul, beginning in an "
                f"age of {opening_axis} and ending in one of {closing_axis} — remembered "
                f"as the {world.ending_class}."
            ),
        }
    )

    life_lines = []
    for life in world.lives:
        s = life.summary
        impact = _life_impact(world, life.id)
        life_lines.append(
            f"{s.title if s else life.id} lived from year {life.birth_year} to "
            f"{life.death_year}. From this life's deeds, {impact} later events would grow."
        )
    chapters.append(
        {"heading": "The Reincarnator's Lives", "text": " ".join(life_lines)}
    )

    rows = _heritage_rows(world)
    if rows:
        legacy_lines = []
        for score, htype, seed, lon, reach, derived in rows:
            legacy_lines.append(
                f"The {htype} (from seed {seed}) endured {lon} years and set {derived} "
                f"further events in motion, the surest mark the reincarnator left on history."
            )
        chapters.append({"heading": "Legacies", "text": " ".join(legacy_lines)})

    resolved = [wc for wc in world.wildcards.wildcards if wc.status.value == "resolved"]
    if resolved:
        turn = " ".join(
            f"{wc.name} the {wc.archetype.value} rose and ran their course, bending the age."
            for wc in resolved
        )
        chapters.append({"heading": "Turning Points", "text": turn})

    chapters.append(
        {
            "heading": "Epilogue",
            "text": (
                f"So {place} settled into the {world.ending_class}, its shape owed less to "
                f"fate than to the choices of the one who lived and died and returned."
            ),
        }
    )

    structured = {
        "title": f"The Chronicle of {place} — {world.ending_class}",
        "chapters": chapters,
    }
    return AIResponse(
        text=_assemble(structured), structured=structured, source="fallback"
    )


class HistoryBookGenerator:
    """Generates a Chronicle from a finished world (P4.1). Read-only on the world."""

    def __init__(self, client: Optional[AIClient] = None) -> None:
        self.client = client or get_ai_client()

    def generate(self, world: World) -> Chronicle:
        dossier = _dossier(world)
        request = AIRequest(
            system=_SYSTEM,
            user="Write the chronicle from this data:\n\n" + dossier,
            assemble=_assemble,
            schema=_SCHEMA,
            max_tokens=2000,
            cache_prefix=_SYSTEM,
            purpose="history_book",
        )
        response = self.client.complete(
            request, lambda: _fallback_response(world, dossier)
        )
        return Chronicle(
            world_id=world.id,
            generated_text=response.text,
            ending_class=world.ending_class,
        )


def generate_history_book(world: World, client: Optional[AIClient] = None) -> Chronicle:
    return HistoryBookGenerator(client).generate(world)
