"""Ending narration (P4.2).

The ending *class* is decided by the rules (``ending.derive_ending_class``); the
AI only writes the flavor epilogue for it. The world is never mutated.
"""

from __future__ import annotations

from typing import Optional

from ..ending import derive_ending_class
from ..models import World
from .client import AIClient, AIRequest, AIResponse, get_ai_client

_SYSTEM = (
    "You write a short, evocative epilogue for a fictional world's ending. You "
    "are given the ending classification (already decided) and statistics; write "
    "only flavor prose that fits. Do not change the classification, do not invent "
    "facts, and do not reference any real people, nations, or religions."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "epitaph": {"type": "string"},
        "text": {"type": "string"},
    },
    "required": ["epitaph", "text"],
}

_FLAVOR = {
    "Golden Age": "an age of flourishing remembered with longing",
    "Imperial Age": "an age of crowns and borders drawn in iron",
    "Theocratic Age": "an age ruled from altars, where faith was law",
    "Warring Age": "an age that knew the drum better than the harvest",
    "Arcane Age": "an age lit by discoveries that outran their makers",
    "Mercantile Age": "an age weighed in coin and bound by trade",
    "Apocalyptic Age": "an age that ended as it was always going to end",
    "Forgotten Age": "an age that left too little to be remembered",
}


def _assemble(structured: dict) -> str:
    epitaph = structured.get("epitaph", "").strip()
    text = structured.get("text", "").strip()
    return f"{epitaph}\n\n{text}" if epitaph else text


def _top_heritage(world: World):
    if not world.heritage:
        return None
    return max(world.heritage, key=lambda h: h.heritage_score)


def _dossier(world: World, ending_class: str) -> str:
    dom = world.theme.dominant.value if world.theme.dominant else "—"
    top = _top_heritage(world)
    legacy = (
        f"{top.type.value} (score {top.heritage_score}, {top.longevity}y)"
        if top
        else "no enduring legacy"
    )
    return (
        f"Ending: {ending_class}\n"
        f"Final dominant theme: {dom}\n"
        f"Lives lived: {len(world.lives)}; years: {world.current_year}; "
        f"events: {len(world.causal_nodes)}; heritage: {len(world.heritage)}\n"
        f"Greatest legacy: {legacy}"
    )


def _fallback_response(world: World, ending_class: str) -> AIResponse:
    flavor = _FLAVOR.get(ending_class, "an age now passed")
    top = _top_heritage(world)
    legacy_clause = (
        f" Its longest shadow was a {top.type.value} that endured {top.longevity} years."
        if top
        else " It left little that outlived its makers."
    )
    structured = {
        "epitaph": f"Thus ended the {ending_class}.",
        "text": (
            f"After {len(world.lives)} lives and {world.current_year} years, the world came "
            f"to rest as {flavor}.{legacy_clause}"
        ),
    }
    return AIResponse(
        text=_assemble(structured), structured=structured, source="fallback"
    )


class EndingNarrator:
    """Writes the epilogue for a world's (rules-decided) ending. Read-only."""

    def __init__(self, client: Optional[AIClient] = None) -> None:
        self.client = client or get_ai_client()

    def narrate(self, world: World) -> str:
        ending_class = world.ending_class or derive_ending_class(world)
        request = AIRequest(
            system=_SYSTEM,
            user="Write the epilogue from this data:\n\n"
            + _dossier(world, ending_class),
            assemble=_assemble,
            schema=_SCHEMA,
            max_tokens=400,
            cache_prefix=_SYSTEM,
            purpose="ending",
        )
        response = self.client.complete(
            request, lambda: _fallback_response(world, ending_class)
        )
        return response.text


def narrate_ending(world: World, client: Optional[AIClient] = None) -> str:
    return EndingNarrator(client).narrate(world)
