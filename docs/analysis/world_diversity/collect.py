"""World Diversity — corpus collector.

Replays N seeds through the real engine and extracts one feature record per
world. Engine is read-only: no file in src/ is touched, nothing is written back.

Usage: PYTHONPATH=src python3 collect.py [N]   ->  corpus.json
"""

import json
import os
import sys
import time
from collections import Counter

sys.path.insert(0, "src")

from chronicle_forge.app import services as S  # noqa: E402
from chronicle_forge.persistence.schema import Recipe  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus.json")
EV = "0.1.0-p8-mvp"


def g(o, k, dflt=None):
    """lifecycle/lineage are models in some builds and dicts in others."""
    if o is None:
        return dflt
    if isinstance(o, dict):
        return o.get(k, dflt)
    return getattr(o, k, dflt)


def enum(v):
    return str(v).split(".")[-1] if v is not None else None


def depth(nodes):
    """Longest causal chain, memoised over the DAG."""
    byid = {n.id: n for n in nodes}
    memo = {}

    def d(nid, stack=()):
        if nid in memo:
            return memo[nid]
        if nid in stack or nid not in byid:
            return 0
        best = 0
        for e in byid[nid].caused_by or []:
            best = max(best, d(e.from_id, stack + (nid,)))
        memo[nid] = best + 1
        return memo[nid]

    return max((d(n.id) for n in nodes), default=0)


def feature(seed):
    w, _ = S.replay_transcript(
        Recipe(engine_version=EV, seed=seed, max_year=40, mode="auto", inputs=[], social_memory=False)
    )
    tl = S.timeline_model(w)
    lg = S.legacy_model(w)

    lives = [
        {
            "i": i + 1,
            "birth": L.birth_year,
            "death": L.death_year,
            "age": L.age_at_death,
            "talent": enum(L.talent),
            "death_cause": enum(L.death_cause),
            "title": (L.summary.title if L.summary else None),
            "dominant": enum(L.summary.dominant_axis) if L.summary else None,
            "n_seeds": len(L.summary.seeds_created) if L.summary else 0,
            "n_heritage": len(L.summary.heritage_created) if L.summary else 0,
            "n_notable": len(L.summary.notable_events) if L.summary else 0,
        }
        for i, L in enumerate(w.lives)
    ]

    ev = [{"y": e.year, "t": e.title, "d": e.domain, "s": e.scale,
           "loc": e.location, "pd": bool(e.player_driven)} for e in tl.entries]

    return {
        "seed": seed,
        "span": w.current_year,
        "ending": str(w.ending_class),
        "place": lg.place,
        # --- structure
        "locations": [{"t": enum(l.type), "n": l.name, "th": enum(l.theme_affinity)} for l in w.locations],
        "npcs": [{"n": n.name, "tier": enum(n.tier), "occ": g(n.lifecycle, "occupation"),
                  "fac": g(n.lifecycle, "faction_id"),
                  "lineage": g(n.lineage, "lineage_id"),
                  "gen": g(n.lineage, "generation"),
                  "parents": len(g(n.lineage, "parent_ids") or []),
                  "traits": len(n.traits or []), "desires": len(n.desires or []),
                  "goals": len(n.goals or [])} for n in w.npcs],
        "factions": [{"n": f.name, "t": enum(f.type), "ide": f.ideology, "pow": f.power} for f in w.factions],
        "lives": lives,
        # --- content
        "events": ev,
        "raw_titles": sorted({n.title for n in w.causal_nodes}),
        "node_domains": dict(Counter(enum(n.domain) for n in w.causal_nodes)),
        "node_scales": dict(Counter(enum(n.scale) for n in w.causal_nodes)),
        "n_nodes": len(w.causal_nodes),
        "n_edges": sum(len(n.caused_by or []) for n in w.causal_nodes),
        "trace_depth": depth(w.causal_nodes),
        "planted_seeds": [{"dom": enum(sd.domain), "mag": sd.magnitude, "fired": bool(sd.fired),
                           "mode": enum(sd.activation_mode), "by": sd.planted_by_life_id,
                           "target": sd.target_id, "year": sd.planted_year} for sd in w.seeds],
        "heritage": [{"type": enum(h.type), "reach": h.reach, "long": h.longevity,
                      "score": h.heritage_score} for h in w.heritage],
        # --- player-facing lenses
        "marks": [{"n": m.name, "k": m.kind, "founder": m.founder_life, "reach": m.reach,
                   "derived": m.derived_events, "long": m.longevity, "living": bool(m.living)}
                  for m in lg.marks],
        "recognitions": [{"n": r.mark_name, "life": r.founder_life, "living": bool(r.living),
                          "hint": r.hint} for r in lg.recognitions],
        "reputation": [{"s": r.sentiment, "c": r.count} for r in lg.reputation],
        "shape": [{"axis": s.axis, "w": s.weight, "living": bool(s.living)} for s in lg.shape],
        "axes_final": {enum(k): v for k, v in w.theme.axes.items()},
        "dominant_seq": [enum(h.dominant) for h in w.theme.history],
    }


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    t0 = time.time()
    rows = []
    for s in range(1, n + 1):
        rows.append(feature(s))
        if s % 100 == 0:
            print("  %d/%d  %.1fs" % (s, n, time.time() - t0), flush=True)
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print("wrote %s  seeds=%d  %.1fs  %.1fMB"
          % (OUT, len(rows), time.time() - t0, os.path.getsize(OUT) / 1e6))
