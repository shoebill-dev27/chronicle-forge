"""Demo-asset generation (reporting).

Read-only renderers that turn a finished ``simulate_world(seed)`` into
README/X/GitHub-ready assets. No game-logic changes, no AI — everything is
derived from existing world data. The goal is that ``docs/examples/seed42/``
alone conveys what makes Chronicle Forge interesting.
"""

from __future__ import annotations

from .build import build_gallery, build_seed_assets
from .causal_dot import causal_dot
from .experience import dead_summary, legacy_view, life_chronicle, life_timeline
from .gallery import GALLERY_SEEDS, gallery_md, key_ending_decision, why_phrase
from .chronicle_md import chronicle_report_md, why_this_ending_md
from .heritage_table import heritage_csv, heritage_table_md
from .labels import heritage_name, seed_label
from .story_md import (
    one_causal_chain_md,
    render_story_of_life,
    stories_md,
    why_ending_chain_md,
)
from .summary_md import summarize_world
from .timeline_md import timeline_md

__all__ = [
    "build_seed_assets",
    "build_gallery",
    "gallery_md",
    "GALLERY_SEEDS",
    "key_ending_decision",
    "why_phrase",
    "stories_md",
    "render_story_of_life",
    "one_causal_chain_md",
    "why_ending_chain_md",
    "seed_label",
    "heritage_name",
    "chronicle_report_md",
    "why_this_ending_md",
    "causal_dot",
    "heritage_table_md",
    "heritage_csv",
    "timeline_md",
    "summarize_world",
    "dead_summary",
    "life_chronicle",
    "life_timeline",
    "legacy_view",
]
