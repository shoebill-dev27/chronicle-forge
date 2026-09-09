"""Client bridge tests.

These exercise the bridge's JSON contract WITHOUT launching a GUI, and assert the
ADR-002 isolation invariant (importing the client pulls in no webview backend, so
CI without pywebview stays green). The stream contract itself is pinned by
``test_beat_stream.py``; what is checked here is that the client's *seam* is that
stream and nothing else — the bridge no longer recovers the game by parsing its
own printed prose, and the frontend has no world copy of its own to fall back on.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import chronicle_forge.client.bridge

from chronicle_forge.client.bridge import BookBridge

_WEB_DIR = (
    Path(__file__).resolve().parents[1] / "src" / "chronicle_forge" / "client" / "web"
)
_PROBE = Path(__file__).resolve().parent / "js" / "client_probe.js"
_SEEDS = (1, 7, 42, 99, 123)

needs_node = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is not installed"
)


def _source(name: str) -> str:
    """One frontend file with its comments removed.

    The assertions below are about what the page *emits*. A comment explaining
    which phrasings are forbidden must not itself trip the check for them.
    """
    text = (_WEB_DIR / name).read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"^\s*//.*$", "", text, flags=re.M)


# A run somebody played. `play(seed)` with no choices entrusts every juncture to
# the world, which is the right stream for "does the page invent a decision?" and
# the wrong one for any assertion about what the player chose.
PLAYED = ["1"] * 60


def _probe(tmp_path: Path, seed: int, choices=PLAYED) -> dict:
    """Run the shipped strings.js/time.js under node against a real stream."""
    stream = tmp_path / f"s{seed}.json"
    stream.write_text(
        json.dumps(BookBridge(seed=seed).play(choices=choices), ensure_ascii=False),
        encoding="utf-8",
    )
    out = subprocess.run(
        ["node", str(_PROBE), str(stream)],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "CF_WEB": str(_WEB_DIR)},
    )
    return json.loads(out.stdout)


def test_play_returns_a_deterministic_json_stream():
    a = BookBridge(seed=1).play()
    b = BookBridge(seed=1).play()
    assert a == b  # same seed -> the same stream, byte for byte
    assert a["place"] and a["lives"] and a["beats"]
    json.dumps(a)  # the bridge must hand JS plain JSON
    kinds = {beat["t"] for beat in a["beats"]}
    # The whole loop, not just the one beat the old regex seam could reach.
    assert {"rebirth", "juncture", "death", "years", "aftermath", "closing"} <= kinds


def test_play_accepts_an_explicit_seed_and_the_choices_made_so_far():
    assert BookBridge().play(2)["seed"] == 2
    sealed = BookBridge(seed=1).play(None, [1])
    assert sealed["seed"] == 1 and sealed["beats"]


def test_the_bridge_never_parses_its_own_prose():
    # The I-1 bridge ran the engine and regex-matched the printed turn screen
    # back into fields, which could recover one beat of five and re-broke every
    # time the renderer changed wording. Nothing in the client may go back to it.
    source = Path(chronicle_forge.client.bridge.__file__).read_text(encoding="utf-8")
    assert "import re" not in source and "re.compile" not in source
    for name in ("book.js", "time.js", "strings.js"):
        js = _source(name)
        for banned in (
            # `.match(` and not `match(`: the old guard let through anything
            # that merely started with those letters, e.g. `matchMedia(`.
            ".match(",
            "RegExp",
            "\u2500\u2500",
        ):  # ── was the header's own decoration
            assert banned not in js, f"{name} parses prose again: {banned!r}"


def test_the_frontend_carries_no_world_copy_of_its_own():
    # A reveal used to print a fixed sentence about a former self regardless of
    # whether the world had one. Every player-facing world fact must now come
    # from a stream field; the only literal names left in the page are its own
    # sample fixture, which is stamped 見本 and can never reach a live window.
    js = (_WEB_DIR / "book.js").read_text(encoding="utf-8")
    assert (
        "\u3053\u306e\u624b\u306f\u3001\u524d\u306b\u3082\u3053\u308c\u3092\u9078\u3093\u3060"
        not in js
    )  # the old hard-coded Hand line
    assert "DEFAULT_REMEMBER" not in js
    # the mark is placed by the stream's own answer, never by position
    assert "data.recognition ? data.recognition.option : null" in js


def test_importing_the_client_imports_no_gui_backend():
    # ADR-002 isolation: no GUI toolkit at import time.
    sys.modules.pop("webview", None)
    import chronicle_forge.client  # noqa: F401

    assert "webview" not in sys.modules


def test_web_assets_are_self_contained():
    # ADR-002 no-CDN: the frontend is three static, fully local files — no
    # network, no external fonts/images/scripts. Every fetchable reference
    # must stay inside the package.
    forbidden = re.compile(r"http://|https://|//cdn|@import\s+url\(")
    for name in ("index.html", "book.css", "strings.js", "book.js", "time.js"):
        text = (_WEB_DIR / name).read_text(encoding="utf-8")
        assert not forbidden.search(text), f"{name} references an external resource"
        for m in re.finditer(r'src=["\']([^"\']+)["\']', text):
            src = m.group(1)
            assert not src.startswith(
                ("http://", "https://", "//")
            ), f"{name} has an off-package src={src!r}"


def test_bundled_fonts_ship_with_their_licences():
    # OD-9 / ADR-002: the print/Hand contrast may not depend on system fonts —
    # no 楷書 face exists on a clean Linux target (T3 U-7) — so both faces are
    # bundled, and SIL OFL requires the licence to travel with them.
    fonts = _WEB_DIR / "fonts"
    for face in ("NotoSerifJP-subset.woff2", "YujiSyuku-subset.woff2"):
        assert (fonts / face).is_file(), f"missing bundled face {face}"
        assert (fonts / face).stat().st_size > 100_000, f"{face} looks truncated"
    licences = list(fonts.glob("OFL-*.txt"))
    assert len(licences) == 2, "each bundled face ships its OFL licence"
    for licence in licences:
        assert "SIL OPEN FONT LICENSE" in licence.read_text(encoding="utf-8").upper()

    css = (_WEB_DIR / "book.css").read_text(encoding="utf-8")
    assert css.count("@font-face") == 2
    for face in ("NotoSerifJP-subset.woff2", "YujiSyuku-subset.woff2"):
        assert f'url("fonts/{face}")' in css, f"{face} is not loaded by book.css"
    # The bundled families must lead their stacks, or a system font would win.
    assert '--print:"Chronicle Print"' in css
    assert '--hand:"Chronicle Hand"' in css


# --------------------------------------------------------------------------
# navigation: the book walks LIVES, not juncture indices
# --------------------------------------------------------------------------


@needs_node
@pytest.mark.parametrize("seed", _SEEDS)
def test_every_life_has_a_page_and_the_page_never_names_another_life(tmp_path, seed):
    """The bug this pins: the book advanced by juncture index, so a life the
    world never asked anything of was stepped over whole. On seed 99 life 2 has
    no juncture, and the surface said "you are born again" as life 2 while the
    page it turned to belonged to life 3 — its death, its years and its
    aftermath (hardened marks included) were unreachable."""
    probe = _probe(tmp_path, seed)
    shown = {step["life"] for step in probe["walk"]}
    assert shown == set(
        probe["lives"]
    ), f"lives never shown: {set(probe['lives']) - shown}"
    for step in probe["walk"]:
        # whatever page the book is on, the beat under it belongs to that life
        assert step["life"] == step["beatLife"], step


@needs_node
@pytest.mark.parametrize("seed", _SEEDS)
def test_every_life_is_shown_its_own_death_years_and_aftermath(tmp_path, seed):
    surfaced = {
        s["life"] for s in _probe(tmp_path, seed)["walk"] if s["page"] == "surface"
    }
    lives = _probe(tmp_path, seed)["lives"]
    assert surfaced == set(lives)


def test_the_book_advances_by_life_not_by_juncture_index():
    js = _source("book.js")
    assert "advanceTo(state.lifeShown + 1)" in js
    # and the surface's own page-turn is offered on whether a life FOLLOWS,
    # not on whether a juncture remains
    assert "!win.rebirth" in js


# --------------------------------------------------------------------------
# the strata scale may not read a future the player has not reached
# --------------------------------------------------------------------------


@needs_node
@pytest.mark.parametrize("seed", _SEEDS)
def test_the_strata_scale_does_not_read_the_future(tmp_path, seed):
    """Band heights were normalised by a total counted over EVERY beat in the
    stream, so a later choice that changed the world's total silently rescaled
    strata already laid down (seed 42 moved 59 -> 56 mid-run), and I-2's
    incremental loop could not supply the number at all. Bolting a louder future
    onto the stream must not move one pixel of the window being drawn."""
    assert _probe(tmp_path, seed)["scaleStable"] is True


# --------------------------------------------------------------------------
# voice: D-3's closed tables, and no copy composed outside the inventory
# --------------------------------------------------------------------------


def test_no_life_signature_outside_the_ratified_table():
    """D-3 §7's epithet table is closed: a former self is `最初のあなた` /
    `N度目のあなた` and nothing else. The page had invented `第Nの生のあなた`."""
    for name in ("book.js", "time.js", "strings.js"):
        assert "\u306e\u751f" not in _source(
            name
        ), f"{name} coins its own life signature"
    strings = _source("strings.js")
    for form in (
        "\u6700\u521d\u306e\u3042\u306a\u305f",
        "\u5ea6\u76ee\u306e\u3042\u306a\u305f",
    ):
        assert form in strings


@needs_node
def test_the_epithet_follows_the_table(tmp_path):
    probe = _probe(tmp_path, 1)
    assert probe["epithets"][:4] == [
        "\u6700\u521d\u306e\u3042\u306a\u305f",
        "\u4e8c\u5ea6\u76ee\u306e\u3042\u306a\u305f",
        "\u4e09\u5ea6\u76ee\u306e\u3042\u306a\u305f",
        "\u56db\u5ea6\u76ee\u306e\u3042\u306a\u305f",
    ]
    assert probe["reveal"]["confirm"].startswith(
        "\u2014\u2014\u4e8c\u5ea6\u76ee\u306e\u3042\u306a\u305f"
    )


def test_the_page_composes_no_copy_outside_the_string_inventory():
    """Every sentence the page writes itself lives in strings.js. The English
    opening/rebirth/closing lines used to be inline in book.js and so escaped
    the D-3 inventory entirely."""
    inventory = _source("strings.js")
    for sentence in (
        "A life opens in ",
        "You are born again into ",
        "It closed in ",
        "The ink sets.",
        "A book waits: ",
        "This will echo.",
        "you let the season pass.",
    ):
        assert sentence in inventory, f"{sentence!r} is not in the inventory"
        for name in ("book.js", "time.js"):
            assert sentence not in _source(name), f"{name} still writes {sentence!r}"


def test_the_closing_line_is_grammatical():
    # "It closed in a Imperial Age." — every ending class the engine emits is
    # vowel-initial or not at the author's whim; the definite article is right
    # for all of them.
    assert "It closed in a ${" not in _source("strings.js")
    assert "It closed in the ${" in _source("strings.js")


@needs_node
@pytest.mark.parametrize("seed", _SEEDS)
def test_no_caption_or_reveal_prints_a_missing_year(tmp_path, seed):
    """`planted_year` is Optional in the stream. It is never None in a measured
    seed, but the caption interpolated it raw, so the first world that carried a
    dateless mark would have printed `null年`."""
    probe = _probe(tmp_path, seed)
    printed = list(probe["captions"].values()) + list(probe["reveal"].values())
    for line in printed:
        if line is None:
            continue
        assert "null" not in line and "undefined" not in line, line
    # and the dateless forms simply drop the date rather than leaving a hole
    assert "null" not in probe["captions"]["sealedWithoutYear"]
    assert "\u5e74" not in probe["captions"]["sealedWithoutYear"]
    assert "\u5e74" not in probe["reveal"]["bloomWithoutYear"]


# --------------------------------------------------------------------------
# I-2: the entry (P-05) and the act arriving in it (P-07)
# --------------------------------------------------------------------------


def test_the_entry_never_writes_ahead_of_its_reader():
    """Sealing replays the WHOLE world, so the stream always runs to the end.
    The entry therefore has to be cut to the acts the player has actually
    sealed; without the cut, a life asked twice showed its second act on the
    page for its first (measured on seeds 7 and 123, in the real window).
    """
    js = _source("book.js")
    assert "slice(0, state.cursor)" in js
    # and the acts it does show are filtered to the life whose page this is
    assert "b.life === life" in js


def test_the_entry_offers_no_way_to_answer_a_juncture_twice():
    """UX §P-06: flipping back to reread is a BEFORE-sealing affordance, and
    §P-07 shows exactly one verb. An entry that offered `flip` would put an
    already-answered juncture back on the page with its seal re-armed."""
    html = (_WEB_DIR / "index.html").read_text(encoding="utf-8")
    entry = html.split('data-page="entry"', 1)[1].split("</section>", 1)[0]
    assert 'data-verb="turn"' in entry
    assert 'data-verb="flip"' not in entry
    assert 'data-verb="seal"' not in entry
    # and the seal itself refuses a second run
    assert "if (state.selected == null || state.sealed) return;" in _source("book.js")


def test_the_plant_cue_fires_on_the_data_and_not_on_the_page():
    """S-03 is a promise; a promise the world did not make is a lie. The cue is
    drawn only where the stream counted something planted."""
    js = _source("book.js")
    assert "act.planted > 0" in js
    # exactly two marks exist in this design (ADR-001 K-1): the echo and the
    # legacy. The plant cue reuses the echo — it must not coin a third.
    marks = {ch for ch in js if ch in "\u27dc\u2767"}
    assert marks <= {"\u27dc"}, f"the page draws a mark outside ADR-001: {marks}"


def test_the_shelf_names_the_real_book_it_opens():
    """P-01 was a stub that returned `books: []` and a bare place name. It now
    describes the book the empty slot opens into with facts worldgen has
    already fixed — and still refuses to invent spines for books that cannot be
    reopened (that needs the discovery-state store, I-6)."""
    from chronicle_forge.worldgen import generate_world

    shelf = BookBridge(seed=7).shelf()
    world = generate_world(7)
    assert shelf["seed"] == 7
    assert shelf["span_years"] == world.max_year
    assert shelf["invitation"]
    assert shelf["books"] == [] and shelf["empty_slot"] is True
    json.dumps(shelf)


def test_the_act_the_page_shows_is_the_act_the_stream_recorded():
    """The entry prints `outcome.label` and nothing else: no re-wording, and no
    reconstruction from the option list (which would drift the moment the
    engine's labels changed — the whole reason the regex seam died)."""
    js = _source("book.js")
    assert "STRINGS.actLine(act.year, act.label)" in js
    assert "act.option === 0" in js  # a season let pass is said, not credited


# --------------------------------------------------------------------------
# I-3 — the rebirth digest (P-10)
# --------------------------------------------------------------------------


@needs_node
@pytest.mark.parametrize("seed", _SEEDS)
def test_the_digest_sits_between_the_years_and_the_life_they_lead_to(tmp_path, seed):
    """The loop the increment closes: surface -> digest -> the next life. Before
    I-3 the surface handed straight to the next rebirth and the world never said
    what the years had done with the life just buried."""
    walk = _probe(tmp_path, seed)["walk"]
    digests = [i for i, s in enumerate(walk) if s["page"] == "digest"]
    assert digests, "this world delivers no digest at all"
    for i in digests:
        assert walk[i - 1]["page"] == "surface"
        # the digest names the life whose years were just shown, not the next one
        assert walk[i]["beatLife"] == walk[i - 1]["life"] == walk[i]["life"]
        # and the page after it belongs to the NEXT life
        assert i + 1 < len(walk) and walk[i + 1]["life"] == walk[i]["life"] + 1


@needs_node
@pytest.mark.parametrize("seed", _SEEDS)
def test_the_first_digest_delivers_the_players_own_act(tmp_path, seed):
    """SP-1 at the page, not just in the stream: the first rebirth's digest has
    at least one line whose act the player sealed themselves — and it is the
    line the page shows first, because the stream ordered it that way."""
    walk = _probe(tmp_path, seed)["walk"]
    first = next(s for s in walk if s["page"] == "digest")
    assert first["beatLife"] == 1
    assert first["sealed"] >= 1
    assert 1 <= first["lines"] <= 3


def test_the_digest_page_renders_the_stream_and_reasons_about_nothing():
    """The act->consequence join is a real causal edge, made where the world is.
    A page that re-derived it would be guessing at causality from strings, and a
    page that re-sorted would be overruling D-03's delivery order."""
    js = _source("book.js")
    body = js.split("function toDigest", 1)[1].split("function toJuncture", 1)[0]
    assert "win.aftermath.changes" in body
    # no ranking, no filtering, no arithmetic on the digest's ordering fields
    for forbidden in ("sort(", "filter(", "change.times", "change.first_year"):
        assert forbidden not in body, f"the digest page does its own {forbidden!r}"
    # fails closed: no life to return to, or nothing named -> no page
    assert "!win.rebirth || !win.aftermath.changes.length" in body


def test_the_digest_offers_no_way_back_into_spent_years():
    html = (_WEB_DIR / "index.html").read_text(encoding="utf-8")
    page = html.split('data-page="digest"', 1)[1].split("</section>", 1)[0]
    assert 'data-verb="turn"' in page
    assert 'data-verb="flip"' not in page
    assert 'data-verb="seal"' not in page
    assert 'if (state.page === "digest") return;' in _source("book.js")


def test_the_digest_prints_no_number_and_coins_no_mark():
    """UX §P-10 hides everything numeric from the digest's own lines: `times`
    and `first_year` are ordering inputs the stream uses, never words the page
    says. (The running head is the book's furniture and carries the year on
    every page, as it does on the entry.) And the only mark drawn here is the
    echo (ADR-001 K-1) — the lines on this page ARE echoes."""
    js = _source("book.js")
    body = js.split("function toDigest", 1)[1].split("function toJuncture", 1)[0]
    marks = {ch for ch in body if ch in "\u27dc\u2767"}
    assert marks == {"\u27dc"}
    inventory = _source("strings.js")
    assert "digestLine:" in inventory
    line = inventory.split("digestLine:", 1)[1].split("\n", 1)[0]
    for field in ("times", "first_year"):
        assert field not in line
    # the page's own words for this spread live in the inventory, not in book.js
    for sentence in ("The world you return to",):
        assert sentence in inventory
        assert sentence not in _source("book.js")
