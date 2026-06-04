"""Demo-asset generation (reporting).

Read-only renderers that turn a finished ``simulate_world(seed)`` into
README/X/GitHub-ready assets. No game-logic changes, no AI — everything is
derived from existing world data. The goal is that ``docs/examples/seed42/``
alone conveys what makes Chronicle Forge interesting.
"""

from __future__ import annotations

from .build import build_seed_assets
from .causal_dot import causal_dot
from .chronicle_md import chronicle_report_md, why_this_ending_md
from .heritage_table import heritage_csv, heritage_table_md
from .story_md import render_story_of_life, stories_md
from .summary_md import summarize_world
from .timeline_md import timeline_md

__all__ = [
    "build_seed_assets",
    "stories_md",
    "render_story_of_life",
    "chronicle_report_md",
    "why_this_ending_md",
    "causal_dot",
    "heritage_table_md",
    "heritage_csv",
    "timeline_md",
    "summarize_world",
]
