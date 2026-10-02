"""World Diversity — analysis.

Three questions:
  1. per feature: how many distinct values does the ENGINE have (pool), and how
     many does ONE WORLD show (sample)?
  2. what is fixed / variable / dead?
  3. if we improved one generator, how much would two random worlds stop
     looking alike?

The headline metric is READ-ALIKE: the expected Jaccard similarity between the
sets of player-readable strings of two random worlds. 1.0 = identical reading.
"""

import json
import math
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, "corpus.json"), encoding="utf-8"))
N = len(C)


def H(counter):
    """Normalised Shannon entropy, 0..1. 0 = one value only."""
    tot = sum(counter.values())
    if tot == 0 or len(counter) <= 1:
        return 0.0
    h = -sum((c / tot) * math.log(c / tot) for c in counter.values() if c)
    return h / math.log(len(counter))


# ---------------------------------------------------------------- feature map
# name -> (per-world extractor returning a list of strings, "family")
F = {
    "place name":            (lambda w: [w["place"]], "world"),
    "ending class":          (lambda w: [w["ending"]], "world"),
    "location name":         (lambda w: [l["n"] for l in w["locations"]], "place"),
    "location type":         (lambda w: [l["t"] for l in w["locations"]], "place"),
    "location theme":        (lambda w: [str(l["th"]) for l in w["locations"]], "place"),
    "faction name":          (lambda w: [f["n"] for f in w["factions"]], "faction"),
    "faction type":          (lambda w: [f["t"] for f in w["factions"]], "faction"),
    "faction ideology":      (lambda w: [f["ide"] for f in w["factions"]], "faction"),
    "npc name":              (lambda w: [n["n"] for n in w["npcs"]], "actor"),
    "npc occupation":        (lambda w: [str(n["occ"]) for n in w["npcs"]], "actor"),
    "npc tier":              (lambda w: [n["tier"] for n in w["npcs"]], "actor"),
    "npc lineage id":        (lambda w: [str(n["lineage"]) for n in w["npcs"]], "dynasty"),
    "event phrase":          (lambda w: [e["t"] for e in w["events"]], "event"),
    "event domain":          (lambda w: [e["d"] for e in w["events"]], "event"),
    "event scale":           (lambda w: [e["s"] for e in w["events"]], "event"),
    "event location":        (lambda w: [str(e["loc"]) for e in w["events"]], "event"),
    "raw node title":        (lambda w: w["raw_titles"], "event"),
    "institution name":      (lambda w: [m["n"] for m in w["marks"]], "institution"),
    "institution kind":      (lambda w: [m["k"] for m in w["marks"]], "institution"),
    "heritage type":         (lambda w: [h["type"] for h in w["heritage"]], "institution"),
    "seed domain":           (lambda w: [s["dom"] for s in w["planted_seeds"]], "institution"),
    "life title":            (lambda w: [str(l["title"]) for l in w["lives"]], "life"),
    "life talent":           (lambda w: [l["talent"] for l in w["lives"]], "life"),
    "life death cause":      (lambda w: [l["death_cause"] for l in w["lives"]], "life"),
    "life dominant axis":    (lambda w: [str(l["dominant"]) for l in w["lives"]], "life"),
    "reputation sentiment":  (lambda w: [r["s"] for r in w["reputation"]], "lens"),
    "recognition hint":      (lambda w: [r["hint"] for r in w["recognitions"]], "lens"),
    "world shape axis":      (lambda w: [s["axis"] for s in w["shape"]], "lens"),
    "dominant-axis path":    (lambda w: ["-".join(w["dominant_seq"])], "lens"),
}

rows = []
pools = {}
for name, (fn, fam) in F.items():
    pool = Counter()
    per_world = []
    for w in C:
        vals = [v for v in fn(w) if v is not None]
        pool.update(vals)
        per_world.append(len(set(vals)))
    pools[name] = pool
    n_pool = len(pool)
    mean_k = sum(per_world) / N
    top_share = (pool.most_common(1)[0][1] / sum(pool.values())) if pool else 0
    # how many worlds show a value that no other world shows
    val_worlds = defaultdict(set)
    for i, w in enumerate(C):
        for v in set(fn(w)):
            if v is not None:
                val_worlds[v].add(i)
    excl = sum(1 for v, ws in val_worlds.items() if len(ws) == 1)
    rows.append({
        "feature": name, "family": fam, "pool": n_pool, "per_world": round(mean_k, 2),
        "H": round(H(pool), 3), "top_share": round(top_share, 3),
        "world_exclusive_values": excl,
        "coverage": round(mean_k / n_pool, 3) if n_pool else 0,
    })


def klass(r):
    if r["pool"] <= 1:
        return "FIXED"
    if r["pool"] == 2 and r["top_share"] > 0.98:
        return "NEAR-FIXED"
    if r["coverage"] >= 0.999:
        return "FIXED-SET"      # every world shows the whole pool: pool != variety
    if r["top_share"] > 0.90:
        return "NEAR-FIXED"
    return "VARIABLE"


for r in rows:
    r["class"] = klass(r)

# ------------------------------------------------------------- READ-ALIKE
VISIBLE = ["place name", "location name", "faction name", "faction ideology", "npc name",
           "event phrase", "institution name", "life title", "ending class",
           "reputation sentiment", "recognition hint"]


def sig(w, feats=VISIBLE):
    s = set()
    for f in feats:
        s.update("%s::%s" % (f, v) for v in F[f][0](w) if v is not None)
    return s


import random  # noqa: E402
random.seed(0)
PAIRS = [(random.randrange(N), random.randrange(N)) for _ in range(20000)]
PAIRS = [(a, b) for a, b in PAIRS if a != b][:15000]
sigs = [sig(w) for w in C]


def readalike(feats=VISIBLE, sigcache=None):
    sg = sigcache or [sig(w, feats) for w in C]
    tot = 0.0
    for a, b in PAIRS:
        A, B = sg[a], sg[b]
        u = len(A | B)
        tot += (len(A & B) / u) if u else 1.0
    return tot / len(PAIRS)


BASE = readalike(sigcache=sigs)

# per-family ablation: how much read-alike is removed by deleting a family?
ABL = {}
fams = sorted({F[f][1] for f in VISIBLE})
for fam in fams:
    keep = [f for f in VISIBLE if F[f][1] != fam]
    ABL[fam] = readalike(keep) if keep else 0.0

# shared-string decomposition: which features actually make two worlds identical?
share = Counter()
for a, b in PAIRS[:4000]:
    for v in sigs[a] & sigs[b]:
        share[v.split("::")[0]] += 1
tot_share = sum(share.values())

# ----------------------------------------------------------------- fingerprint
def fingerprint(w):
    ax = w["axes_final"]
    tot = sum(ax.values()) or 1
    return (w["ending"],
            tuple(sorted(ax, key=lambda k: -ax[k])[:2]),
            len(w["lives"]),
            tuple(sorted({m["k"] for m in w["marks"]})),
            min(9, len({e["t"] for e in w["events"]})))


fps = Counter(fingerprint(w) for w in C)
eff = math.exp(-sum((c / N) * math.log(c / N) for c in fps.values()))

# ------------------------------------------------------------------- ROI model
# each family draws k distinct items per world from a pool of P.
# expected shared items between two worlds ~= k^2 / P  (k << P)
# improving P -> P' scales that family's shared mass by P/P'.
CAND = [
    ("location names 4 -> 200", "location name", 200),
    ("event phrases 6 -> 120", "event phrase", 120),
    ("institution names 24 -> 600", "institution name", 600),
    ("npc names 20 -> 400", "npc name", 400),
    ("faction names 8 -> 160", "faction name", 160),
    ("life titles 60 -> 600", "life title", 600),
    ("ending classes 3 -> 12", "ending class", 12),
    ("recognition hints 5 -> 40", "recognition hint", 40),
    ("reputation sentiments 8 -> 40", "reputation sentiment", 40),
    ("place names 1 -> 200", "place name", 200),
]


def roi():
    mean_int = sum(len(sigs[a] & sigs[b]) for a, b in PAIRS) / len(PAIRS)
    mean_uni = sum(len(sigs[a] | sigs[b]) for a, b in PAIRS) / len(PAIRS)
    per_feat_int = {f: share[f] / 4000 for f in VISIBLE}
    out = []
    for label, feat, newP in CAND:
        r = next(x for x in rows if x["feature"] == feat)
        P, k = max(1, r["pool"]), r["per_world"]
        cur_int = per_feat_int.get(feat, 0.0)
        new_int = cur_int * (P / newP) if newP > P else cur_int
        d_int = cur_int - new_int
        new_uni = mean_uni + d_int          # what stops being shared becomes distinct
        new_ra = (mean_int - d_int) / new_uni if new_uni else 0
        out.append({"改善": label, "feature": feat, "pool": P, "per_world": k,
                    "shared_now": round(cur_int, 2), "shared_after": round(new_int, 2),
                    "read_alike_after": round(new_ra, 4),
                    "delta": round(BASE - new_ra, 4)})
    return sorted(out, key=lambda x: -x["delta"]), mean_int, mean_uni


ROI, MEAN_INT, MEAN_UNI = roi()

if __name__ == "__main__":
    print("=" * 96)
    print("CORPUS: %d worlds (seeds 1..%d), engine 0.1.0-p8-mvp, max_year=40, mode=auto" % (N, N))
    print("=" * 96)
    print("\n### 1. FEATURE DIVERSITY  (pool = distinct values in ALL 1000 worlds;"
          " per_world = distinct in ONE)")
    print("%-24s %-11s %6s %9s %6s %9s %8s  %s"
          % ("feature", "family", "pool", "per_world", "H", "top_share", "excl", "class"))
    for r in sorted(rows, key=lambda x: (x["class"], -x["pool"])):
        print("%-24s %-11s %6d %9.2f %6.3f %9.3f %8d  %s"
              % (r["feature"], r["family"], r["pool"], r["per_world"], r["H"],
                 r["top_share"], r["world_exclusive_values"], r["class"]))

    print("\n### 2. READ-ALIKE  (expected Jaccard of player-readable strings, 15k random pairs)")
    print("  BASE read-alike            = %.4f   (1.00 = two random worlds read identically)" % BASE)
    print("  mean shared strings / pair = %.1f of %.1f union" % (MEAN_INT, MEAN_UNI))
    print("  effective distinct worlds  = %.1f  (of %d; by coarse fingerprint)" % (eff, N))
    print("  distinct fingerprints      = %d ; most common covers %.1f%% of worlds"
          % (len(fps), 100 * fps.most_common(1)[0][1] / N))
    print("\n  what the shared strings ARE:")
    for f, c in share.most_common():
        print("    %-24s %6.1f%%  (%0.1f strings per pair)" % (f, 100 * c / tot_share, c / 4000))
    print("\n  family ablation (read-alike if that family were made perfectly unique):")
    for fam in fams:
        print("    remove %-12s -> %.4f   (%+.4f)" % (fam, ABL[fam], ABL[fam] - BASE))

    print("\n### 3. IMPROVEMENT ROI  (ranked by drop in read-alike)")
    print("%-32s %6s %6s %9s %9s %10s %8s"
          % ("candidate", "pool", "k/world", "shared", "->after", "read-alike", "Δ"))
    for r in ROI:
        print("%-32s %6d %6.1f %9.2f %9.2f %10.4f %8.4f"
              % (r["改善"], r["pool"], r["per_world"], r["shared_now"],
                 r["shared_after"], r["read_alike_after"], r["delta"]))

    print("\n### 4. DENSITY / DEPTH DISTRIBUTIONS")
    for key, get in (("lives", lambda w: len(w["lives"])),
                     ("events", lambda w: len(w["events"])),
                     ("distinct event phrases", lambda w: len({e["t"] for e in w["events"]})),
                     ("marks", lambda w: len(w["marks"])),
                     ("recognitions", lambda w: len(w["recognitions"])),
                     ("trace_depth", lambda w: w["trace_depth"]),
                     ("causal edges", lambda w: w["n_edges"]),
                     ("planted seeds", lambda w: len(w["planted_seeds"])),
                     ("seeds fired", lambda w: sum(1 for s in w["planted_seeds"] if s["fired"])),
                     ("npc lineage ids", lambda w: len({n["lineage"] for n in w["npcs"]} - {None})),
                     ("npc traits total", lambda w: sum(n["traits"] for n in w["npcs"])),
                     ("npc goals total", lambda w: sum(n["goals"] for n in w["npcs"])),
                     ("npc desires total", lambda w: sum(n["desires"] for n in w["npcs"])),
                     ("events w/ location", lambda w: sum(1 for e in w["events"] if e["loc"])),
                     ("marks not by life 1", lambda w: sum(1 for m in w["marks"] if m["founder"] != 1)),
                     ):
        v = sorted(get(w) for w in C)
        print("  %-24s min %4d  p50 %4d  p90 %4d  max %4d  mean %6.1f"
              % (key, v[0], v[N // 2], v[int(N * .9)], v[-1], sum(v) / N))

    print("\n### 5. M-1 FLOOR RE-CHECK (D-5 SEL: past_self_marks>=4 AND trace_depth>=20)")
    ok = sum(1 for w in C if len(w["marks"]) >= 4 and w["trace_depth"] >= 20)
    print("  seeds admitted: %d/%d (%.1f%%)" % (ok, N, 100 * ok / N))

    json.dump({"rows": rows, "base_read_alike": BASE, "share": dict(share), "roi": ROI,
               "ablation": ABL, "eff_worlds": eff, "n_fingerprints": len(fps)},
              open(os.path.join(HERE, "report.json"), "w"), ensure_ascii=False, indent=1)


# ------------------------------------------------- structural + combined ROI
def scenario(mult):
    """mult: feature -> pool multiplier applied to that feature's shared mass."""
    per_feat_int = {f: share[f] / 4000 for f in VISIBLE}
    d = 0.0
    for f, m in mult.items():
        d += per_feat_int.get(f, 0.0) * (1 - 1.0 / m)
    return (MEAN_INT - d) / (MEAN_UNI + d)


def report2():
    print("\n### 6. STRUCTURAL FIXES vs VOCABULARY FIXES")
    print("  (a vocabulary fix buys new nouns; a structural fix buys new SENTENCES)")
    S1 = [
        ("STRUCT bind events to a location (8 phrases x 4 places = 32 effective, 0 new writing)",
         {"event phrase": 4.0}),
        ("STRUCT institution kind actually varies (4 kinds used, not 98.8% one)",
         {"institution name": 4.0}),
        ("STRUCT stop instantiating the whole catalogue: draw 4 of 40 places / 4 of 40 factions",
         {"location name": 10.0, "faction name": 10.0, "faction ideology": 10.0}),
        ("VOCAB  institution names 31 -> 600", {"institution name": 600 / 31}),
        ("VOCAB  event phrases 8 -> 120", {"event phrase": 120 / 8}),
        ("VOCAB  place name 1 -> 200", {"place name": 200.0}),
    ]
    for label, m in S1:
        r = scenario(m)
        print("  %-78s %.4f  (%+.4f)" % (label, r, r - BASE))

    print("\n### 7. COMBINED SCENARIOS")
    combos = [
        ("A. cheapest structural bundle: locations+factions sampled (4 of 40) + event->location bind",
         {"location name": 10.0, "faction name": 10.0, "faction ideology": 10.0, "event phrase": 4.0}),
        ("B. A + institution names 31 -> 600 + kind varies",
         {"location name": 10.0, "faction name": 10.0, "faction ideology": 10.0,
          "event phrase": 4.0, "institution name": 600 / 31 * 4}),
        ("C. B + place name 1 -> 200 + event phrases 8 -> 120",
         {"location name": 10.0, "faction name": 10.0, "faction ideology": 10.0,
          "event phrase": 120 / 8 * 4, "institution name": 600 / 31 * 4, "place name": 200.0}),
        ("D. everything nameable made unique per world (theoretical floor)",
         {f: 1e6 for f in VISIBLE}),
    ]
    for label, m in combos:
        r = scenario(m)
        print("  %-78s %.4f  (%+.4f)" % (label, r, r - BASE))

    print("\n### 8. WHO PLANTS THE MARKS")
    tot = Counter()
    for w in C:
        for m in w["marks"]:
            tot[m["founder"]] += 1
    s = sum(tot.values())
    for k in sorted(tot):
        print("  life %d: %5d marks (%.1f%%)" % (k, tot[k], 100 * tot[k] / s))
    solo = sum(1 for w in C if len({m["founder"] for m in w["marks"]}) == 1)
    print("  worlds where EVERY mark has the same founder: %d/%d (%.1f%%)" % (solo, N, 100 * solo / N))

    print("\n### 9. DEAD SUBSYSTEMS (present in schema, empty in all %d worlds)" % N)
    for label, get in (("npc.lineage.lineage_id", lambda w: len({n["lineage"] for n in w["npcs"]} - {None})),
                       ("npc.traits", lambda w: sum(n["traits"] for n in w["npcs"])),
                       ("npc.goals", lambda w: sum(n["goals"] for n in w["npcs"])),
                       ("npc.desires", lambda w: sum(n["desires"] for n in w["npcs"])),
                       ("CausalNode.location_id", lambda w: sum(1 for e in w["events"] if e["loc"])),
                       ("Seed.target_id", lambda w: sum(1 for s in w["planted_seeds"] if s["target"])),
                       ("LifeSummary.notable_events", lambda w: sum(l["n_notable"] for l in w["lives"])),
                       ("LifeSummary.heritage_created", lambda w: sum(l["n_heritage"] for l in w["lives"]))):
        mx = max(get(w) for w in C)
        print("  %-34s max across corpus = %d   %s" % (label, mx, "DEAD" if mx == 0 else "alive"))


report2()
