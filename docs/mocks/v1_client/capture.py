"""Headless capture of the REAL client, on real engine data.

No Playwright and no pywebview (neither is installable in this branch's venv):
this stages `client/web/` into a Windows-visible temp directory, drops the typed
beat stream beside it as `capture-beats.js`, and drives the Windows Chrome that
WSL already has over `file://`. The page is the shipped one — same book.js, same
time.js, same fonts — so what is captured is the client, not a mock of it.

The stream is produced by `play.beats.stream()`, i.e. the same call the bridge
makes, so nothing in these frames is fixture data. Every still is taken at an
exact `t` (`?t=`), so a capture is reproducible rather than whatever frame the
animation happened to be on.

    python docs/mocks/v1_client/capture.py            # every seed
    python docs/mocks/v1_client/capture.py --seed 42
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
WEB = os.path.join(REPO, "src", "chronicle_forge", "client", "web")
sys.path.insert(0, os.path.join(REPO, "src"))

STAGE = "/mnt/c/Windows/Temp/cf_v1client"
STAGE_WIN = r"C:\Windows\Temp\cf_v1client"
# A THROWAWAY browser profile, wiped before every run. Without it Chrome uses
# the machine's default profile, whose disk cache is keyed by URL — and every
# seed stages its stream at the same `capture-beats.js` path, so a re-run served
# an earlier seed's world from cache and wrote it into a frame named for this
# one. (Measured: re-running seed 42 drew "Order of the Seven Fires", a legacy
# from another world; the two 292px sheets of one run came out byte-identical.)
# Isolating the profile makes a re-run byte-identical to the first instead.
PROFILE = "/mnt/c/Windows/Temp/cf_v1client_profile"
PROFILE_WIN = r"C:\Windows\Temp\cf_v1client_profile"
CHROME = "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
SHOTS = os.path.join(HERE, "shots")

SEEDS = (1, 7, 42, 99, 123)
# One still per beat of the surface's cut, at the moment the beat reads best.
MOMENTS = (
    ("b2-death", 0.08),
    ("b3-years-early", 0.22),
    ("b3-years-late", 0.44),
    ("b4-aftermath", 0.60),
    ("b4-climax", 0.695),
    ("b4-rebirth", 0.78),
)


def stream_for(seed: int) -> dict:
    from chronicle_forge.client.bridge import BookBridge

    return BookBridge(seed=seed).play()


def windows_of(data: dict) -> dict:
    """`{"quiet": life, "sealed": life|None}` — the two registers to shoot.

    The quiet one is the first window (in every measured seed the first
    aftermath hardens nothing, which is the case a surface has to survive); the
    sealed one is the first window whose aftermath actually names a mark.
    """
    beats = data["beats"]
    quiet = sealed = None
    for i, b in enumerate(beats):
        if b["t"] != "death":
            continue
        aftermath = beats[i + 2] if i + 2 < len(beats) else None
        if not aftermath or aftermath["t"] != "aftermath":
            continue
        if quiet is None:
            quiet = b["life"]
        if sealed is None and aftermath["hardened"]:
            sealed = b["life"]
    return {"quiet": quiet, "sealed": sealed}


def stage(seed: int) -> None:
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    shutil.copytree(WEB, STAGE)
    with open(os.path.join(STAGE, "capture-beats.js"), "w", encoding="utf-8") as fh:
        fh.write("window.CF_BEATS=")
        json.dump(stream_for(seed), fh, ensure_ascii=False, separators=(",", ":"))
        fh.write(";")
    # Chrome blocks fetch() on file://, so the stream is injected as a script.
    # The tag is added to the STAGED copy only — the shipped index.html stays
    # free of it, and `test_web_assets_are_self_contained` still holds.
    index = os.path.join(STAGE, "index.html")
    with open(index, encoding="utf-8") as fh:
        html = fh.read()
    html = html.replace(
        '<script src="time.js"></script>',
        '<script src="capture-beats.js"></script>\n  <script src="time.js"></script>',
    )
    with open(index, "w", encoding="utf-8") as fh:
        fh.write(html)


def shot(page: str, query: str, out_name: str, w: int, h: int) -> str:
    """One headless screenshot. `--virtual-time-budget` lets the bundled faces
    land before the frame is taken; the page itself is static at a fixed `t`."""
    win_out = STAGE_WIN + "\\" + out_name
    subprocess.run(
        [
            CHROME,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            "--virtual-time-budget=3000",
            f"--user-data-dir={PROFILE_WIN}",
            "--disk-cache-size=1",
            # The page-turn keyframes are wall-clock, so a still of a DOM page
            # (the B1' juncture, which has no `?t=`) landed mid-animation and
            # differed run to run. book.css already stops exactly those
            # animations under `prefers-reduced-motion`; this settles the page
            # instead of adding a capture-only code path to the client.
            "--force-prefers-reduced-motion",
            f"--screenshot={win_out}",
            f"--window-size={w},{h}",
            f"file:///C:/Windows/Temp/cf_v1client/{page}?{query}",
        ],
        capture_output=True,
        timeout=180,
    )
    src = os.path.join(STAGE, out_name)
    return src if os.path.exists(src) else ""


def take(page: str, query: str, name: str, w: int, h: int) -> bool:
    src = shot(page, query, name, w, h)
    if not src:
        print("  MISSED", name, file=sys.stderr)
        return False
    shutil.move(src, os.path.join(SHOTS, name))
    return True


def contact_sheet(seed: int, names: list, tag: str) -> bool:
    """The 292px store test, built in the browser: the stills are laid out at the
    thumbnail's real width and re-shot, so nothing is resampled by a second
    toolchain. (No Pillow: the harness stays dependency-free.)"""
    # The stills live in the repo (WSL side); Chrome is Windows-side, so they are
    # copied next to the sheet rather than linked across the boundary.
    sheet_dir = os.path.join(STAGE, "sheet")
    os.makedirs(sheet_dir, exist_ok=True)
    cells = ""
    for n in names:
        shutil.copy(os.path.join(SHOTS, n), os.path.join(sheet_dir, n))
        cells += (
            f'<figure><img src="{n}" width="292">'
            f"<figcaption>{n[:-4]}</figcaption></figure>"
        )
    html = (
        "<meta charset='utf-8'><style>body{margin:0;background:#1b1713;"
        "display:flex;flex-wrap:wrap;gap:10px;padding:12px;font:11px/1.6 sans-serif}"
        "figure{margin:0;color:#9d8f78}img{display:block}</style>" + cells
    )
    with open(os.path.join(sheet_dir, "sheet.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    name = f"s{seed}-SHEET292-{tag}.png"
    return take("sheet/sheet.html", "", name, 960, 460)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    if not os.path.exists(CHROME):
        print("Windows Chrome not found:", CHROME, file=sys.stderr)
        return 1
    os.makedirs(SHOTS, exist_ok=True)
    if os.path.isdir(PROFILE):  # a run always starts from a cold cache
        shutil.rmtree(PROFILE, ignore_errors=True)
    os.makedirs(PROFILE, exist_ok=True)

    made = 0
    for seed in [args.seed] if args.seed else list(SEEDS):
        data = stream_for(seed)
        wins = windows_of(data)
        stage(seed)
        print(f"seed {seed}: quiet=life {wins['quiet']} sealed=life {wins['sealed']}")
        for register, life in wins.items():
            if life is None:
                print(f"  (no {register} window in this seed)")
                continue
            names = []
            for tag, t in MOMENTS:
                name = f"s{seed}-{register}-{tag}.png"
                if take("index.html", f"surface={life}&t={t}", name, 900, 720):
                    names.append(name)
                    made += 1
            # B1' — the juncture the surface hands off to, on the same data.
            if take(
                "index.html",
                f"surface={life}&page=juncture",
                f"s{seed}-{register}-b1-juncture.png",
                900,
                720,
            ):
                made += 1
            if names and contact_sheet(seed, names, register):
                made += 1
    print(f"{made} frames -> {SHOTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
