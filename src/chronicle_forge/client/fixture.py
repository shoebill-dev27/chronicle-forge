"""Export one played world as a Unity-readable DVS fixture.

WHY THIS EXISTS
    The Unity presentation client (``unity/``) is a second reader of the same
    world the web client reads. It must not re-derive anything: no RNG, no
    causal inference, no attribution of its own. So it is handed the *same*
    typed beat stream ``client/bridge.py`` hands the page — ``play.beats`` —
    written to a file it can load without a Python process alive.

    This module adds no truth. It runs the engine under a recorded input list
    and serialises :func:`play.beats.to_dict` verbatim. Every field in the
    output already existed; the only things composed here are the envelope
    (which world, under which inputs) and the discovery index, which is a
    re-keying of marks and cases the stream already carries.

WHAT UNITY IS NOT GIVEN
    Nothing is withheld that the web client gets, and nothing extra is added.
    In particular ``Mark.founder_life`` and ``CausePath.origin_*`` ARE in the
    file, exactly as they are in the browser's payload — because D-03 is a rule
    about what a *surface* may draw, not about what the reader process may hold.
    ``discovery.locked`` names every coordinate that starts hidden, so the Unity
    side can enforce the same gate the page does rather than inventing one.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from ..persistence.version import ENGINE_VERSION
from ..play import beats as beat_stream
from .state import BookState, canonical_hash

# The DVS reference run. Seed 1 is the world every G0 gate and every screenshot
# in ``docs/screenshots/g0`` is measured against, and answering "1" at every
# juncture is what makes the run *played* rather than entrusted — which is the
# only way ``Recognition.sealed_act`` can be populated at all (C-2).
DVS_SEED = 1
DVS_CHOICES: Sequence[str] = tuple(["1"] * 60)


def _locked(stream: Dict) -> List[str]:
    """Every coordinate a reader must earn before a surface may attribute it.

    Two kinds, both already in the stream and both keyed the way the web client
    keys them (``client/web/book.js``): a hardened mark's ``ref`` (D-03 — the
    surface may draw the mark and name it, never say whose it is), and a case's
    ``ref`` (D-04 — inspecting a consequence reveals nothing until the reader
    explicitly confirms the origin).
    """
    refs: List[str] = []
    for beat in stream["beats"]:
        if beat["t"] == "aftermath":
            refs += [m["ref"] for m in beat["hardened"]]
        elif beat["t"] == "closing":
            refs += [c["ref"] for c in beat["cases"]]
        elif beat["t"] == "juncture" and beat.get("recognition"):
            # The recognition standing at a juncture is proved by the engine,
            # but D-04 still says the reader must act to earn it: arriving on a
            # page may not hand over an attribution. Its coordinate is the
            # heritage the option carries, which is stable across runs.
            carrier = next(
                (o for o in beat["options"] if o["n"] == beat["recognition"]["option"]),
                None,
            )
            if carrier and carrier.get("heritage_id"):
                refs.append(carrier["heritage_id"])
    # Sorted and de-duplicated: a mark can harden once but be cited by several
    # cases, and the gate is about the coordinate, not about how it was reached.
    return sorted(set(refs))


def dvs_fixture(seed: int = DVS_SEED, choices: Optional[Sequence[str]] = None) -> Dict:
    """One played world, plus the identity and the gate Unity needs."""
    picks = list(DVS_CHOICES if choices is None else choices)
    stream = beat_stream.to_dict(beat_stream.stream(seed, picks))
    # The same identity the book store mints, so a Unity fixture and a real
    # resumed book can be compared without a second notion of "which world".
    state = BookState.new(seed=seed, max_year=stream["max_year"], inputs=picks)
    return {
        "fixture_version": "1",
        "engine_version": ENGINE_VERSION,
        "canonical_hash": canonical_hash(state.recipe),
        "inputs": picks,
        "stream": stream,
        "discovery": {"locked": _locked(stream)},
    }


def write_fixture(path: Path, **kwargs) -> Dict:
    """Write the fixture as canonical JSON. Deterministic byte-for-byte."""
    data = dvs_fixture(**kwargs)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return data


if __name__ == "__main__":  # pragma: no cover - a one-line exporter CLI
    import sys

    target = Path(sys.argv[1] if len(sys.argv) > 1 else "dvs_fixture.json")
    data = write_fixture(target)
    print(
        f"{target}  hash={data['canonical_hash'][:12]}  locked={len(data['discovery']['locked'])}"
    )
