"""Demo-asset reporting (read-only). All generators must be pure on world state
and deterministic for seed=42."""

from __future__ import annotations

from chronicle_forge import simulate_world
from chronicle_forge.reporting import (
    build_seed_assets,
    causal_dot,
    chronicle_report_md,
    heritage_csv,
    heritage_table_md,
    render_story_of_life,
    stories_md,
    summarize_world,
    timeline_md,
    why_this_ending_md,
)


def _world():
    return simulate_world(42)


def test_generators_do_not_mutate_world():
    world = _world()
    before = world.model_dump_json()
    stories_md(world)
    chronicle_report_md(world)
    causal_dot(world)
    heritage_table_md(world)
    heritage_csv(world)
    timeline_md(world)
    summarize_world(world)
    assert world.model_dump_json() == before


def test_story_traces_life_to_heritage_and_ending():
    world = _world()
    text = stories_md(world)
    assert "Life 1" in text
    assert "Causal chains" in text
    assert "Heritage" in text
    assert world.ending_class in text
    # per-life helper works too
    one = render_story_of_life(world, world.lives[0].id)
    assert one.startswith("## Life 1")


def test_chronicle_has_sections_and_causal_why():
    world = _world()
    text = chronicle_report_md(world)
    for section in [
        "## World Overview",
        "## The Reincarnator's Lives",
        "## How the World Turned",
        "## Legacies",
        "## Wild Cards",
        "## Why this Ending",
    ]:
        assert section in text
    why = why_this_ending_md(world)
    assert "⇐" in why  # the ⇐ causal chain arrow
    assert "Life" in why


def test_causal_dot_is_well_formed():
    world = _world()
    dot = causal_dot(world)
    assert dot.lstrip().startswith("digraph")
    assert dot.count("{") == dot.count("}")
    assert '"ENDING"' in dot
    assert "fillcolor=gold" in dot  # player seeds
    assert "doubleoctagon" in dot  # heritage
    # every heritage in the focus graph reaches ENDING
    assert '-> "ENDING"' in dot


def test_heritage_table_and_csv_align():
    world = _world()
    md = heritage_table_md(world, top=10)
    assert md.startswith("# Heritage Ranking")
    assert "| Rank |" in md
    csv_text = heritage_csv(world, top=10)
    header = csv_text.splitlines()[0]
    assert header == (
        "rank,name,score,longevity,reach,source_seed,domain,derived_events,"
        "origin_life,origin_action"
    )
    # at most 10 data rows, and md/csv agree on count
    csv_rows = len(csv_text.strip().splitlines()) - 1
    md_rows = sum(
        1
        for line in md.splitlines()
        if line.startswith("| ") and "Rank" not in line and "---" not in line
    )
    assert csv_rows == md_rows
    assert csv_rows <= 10


def test_timeline_has_a_row_per_year():
    world = _world()
    tl = timeline_md(world)
    data_rows = [
        l
        for l in tl.splitlines()
        if l.startswith("| ") and "Year" not in l and "---" not in l
    ]
    assert len(data_rows) == len(world.theme.history)


def test_summary_is_within_word_band_and_factual():
    world = _world()
    s = summarize_world(world)
    assert 200 <= len(s.split()) <= 300  # word count, first-timer friendly
    assert world.ending_class in s
    assert "long after death" in s


def test_story_has_why_this_world_matters():
    world = _world()
    text = stories_md(world)
    assert "## Why this world matters" in text


def test_labels_are_human_and_deterministic():
    from chronicle_forge.reporting import heritage_name, seed_label

    world = _world()
    # a player seed gets a verb-phrase label, not its id
    pseed = next(s for s in world.seeds if s.planted_by_life_id)
    label = seed_label(world, pseed.id)
    assert label and label != pseed.id and " " in label
    assert seed_label(world, pseed.id) == label  # deterministic

    # heritage gets a proper name distinct from its bare type
    h = world.heritage[0]
    name = heritage_name(h)
    assert name and name != h.type.value
    assert heritage_name(h) == name


def test_story_uses_names_not_just_ids():
    from chronicle_forge.reporting._data import heritage_rows

    world = _world()
    text = stories_md(world)
    top_name = heritage_rows(world, top=1)[0]["name"]
    assert top_name in text  # heritage proper name appears
    assert '"' in text  # quoted human action labels


def test_readme_has_one_causal_chain(tmp_path):
    build_seed_assets(42, out_dir=str(tmp_path), png=False)
    readme = (tmp_path / "seed42" / "README.md").read_text()
    assert "## One causal chain" in readme
    assert "Ending —" in readme


def test_readme_has_why_this_ending(tmp_path):
    build_seed_assets(42, out_dir=str(tmp_path), png=False)
    readme = (tmp_path / "seed42" / "README.md").read_text()
    assert "## Why this ending happened" in readme
    assert "(player action)" in readme


def test_story_has_key_decisions_and_origin():
    world = _world()
    text = stories_md(world)
    assert "**Key Decisions:**" in text
    assert "Origin: Life" in text  # heritage origin line


def test_build_writes_bundle(tmp_path):
    written = build_seed_assets(42, out_dir=str(tmp_path), png=False)
    names = {p.split("/")[-1] for p in written}
    assert {
        "story.md",
        "chronicle.md",
        "causal.dot",
        "heritage.md",
        "heritage.csv",
        "timeline.md",
        "summary.md",
        "README.md",
    } <= names
    seed_dir = tmp_path / "seed42"
    assert (seed_dir / "story.md").exists()
    assert (seed_dir / "README.md").read_text().startswith("# Example World — Seed 42")
