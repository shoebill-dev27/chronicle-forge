"""Rule-based NPC behavior (section 6.3).

Deliberately minimal: the protagonist of this game is history, not the NPCs
(review guidance). An NPC's step is a single utility pick over its personality
drives, recording the current intent. Richer faction/lifecycle dynamics happen
during the macro skip (P3), not here.
"""

from __future__ import annotations

from typing import Optional

from .models import NPC, World


def choose_intent(npc: NPC) -> str:
    """Pick the NPC's dominant drive from its personality (the utility argmax)."""
    drives = {
        "seek_power": npc.personality.ambitious,
        "seek_wealth": npc.personality.greedy,
        "spread_faith": npc.personality.devout,
        "seek_valor": npc.personality.brave,
        "keep_peace": npc.personality.merciful,
    }
    return max(drives, key=drives.__getitem__)


def step_npc(world: World, npc: NPC) -> Optional[str]:
    """Advance one NPC by one step. Returns the chosen intent, or None if dead."""
    if not npc.alive:
        return None
    intent = choose_intent(npc)
    npc.goals = [intent]
    return intent
