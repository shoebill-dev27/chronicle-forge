# Unity Presentation Client — audit note and the three DVS mocks

*2026-09-12 · branch `design/v1` on `4751e2f` · uncommitted by instruction.*

The Python engine stays authoritative. `unity/` is a second **reader** of the
same beat stream the web client reads; it re-derives nothing. This note records
what was found in the audit, how the project is wired, and what the three
mocks are — the comparison itself is in the session report.

## 1. Audit — where responsibility lives

| Class | What | Where |
|---|---|---|
| **A. KEEP IN PYTHON** | worldgen, RNG, causal graph, P6 selection, discovery truth (D-01..D-08 *sources*), choice validity, recipe identity (`canonical_hash`), sealed-vs-autonomous (`_player_answered`), C-3 BFS path, digest cut (`DIGEST_MAX`), case cap/order | `worldgen.py`, `causal.py`, `play/session.py`, `play/beats.py`, `client/state.py` |
| **B. EXPOSE TO UNITY** | the typed beat stream `beats.to_dict()` verbatim + envelope (`engine_version`, `canonical_hash`, `inputs`) + `discovery.locked` (every coordinate that starts hidden) | `client/fixture.py` → `unity/Assets/ChronicleForge/Resources/dvs_fixture.json` |
| **C. REIMPLEMENT AS UNITY PRESENTATION** | the surface-side *gate* (D-01/D-03/D-04/C-2/C-6/朱 as render predicates), navigation, selection≠commitment, focus, keyboard, reduced-motion, composition per beat, JP furniture | `Core/DiscoveryGate.cs`, `Core/DvsSession.cs`, `Core/Voice.cs`, `Concepts/*` |
| **D. FREEZE (web client)** | `client/web/*` stays as the G0/DVS reference; nothing was ported from it — layout, CSS and `strings.js` were deliberately not reused | untouched |
| **E. ASSETS REUSABLE** | Noto Serif JP / Yuji Syuku (the vendored woff2 carry 13 467 / 7 356 glyphs; converted to TTF, OFL texts copied), the fixture, the closed epithet table | `Resources/*.ttf`, `Fonts/OFL-*.txt` |
| **F. DISCARD** | the web page composition (3-page book), `book.css`, the Time-Surface canvas code, G0 screenshots as layout reference | — |

Things the audit established that the Unity side must never do: name a founder
before its `ref` is confirmed; print `"your past pulls here"` on a juncture;
caption an autonomous origin as a choice; use 朱 for anything but a confirmed
past-life connection; draw a link where `CausePath.steps` holds no edge; invent
a location (every `location_id` is `None`).

## 2. Data contract (transcribed, not designed)

`Model/DvsFixture.cs` + `Model/BeatStream.cs` are field-for-field transcriptions
of `play/beats.py`. `Optional[...]` → `int?`/`string` so "unprovable" stays
distinct from zero/empty (`Recognition.sealed_act == null` is load-bearing).
`BeatConverter` dispatches on `"t"` and **throws** on an unknown kind. The
loader refuses a fixture from another `engine_version` or without a hash.

**C-3 correction found while transcribing:** `CausePath.steps` are the events
*between* the consequence and the origin (empty = direct cause); the two ends
are `(event, year)` and `(origin_act, origin_year)`. The first draft of the
Unity walk — and the first draft of `tests/test_unity_fixture.py` — read
`steps[0]` as the consequence. Both are fixed; seed 1's twelve cases are all
**two-hop** (consequence → one intermediate event in year 8 → origin in year 0),
so the hop-by-hop investigation is exercised by the shipped fixture.

## 3. How it runs

* Unity **2023.1.12f1** (Windows, `C:\Program Files\Unity\Hub\Editor\2023.1.12f1`).
  Unity 6 is not installed, so Unity's first-party MCP (`com.unity.ai.assistant`,
  6000.0+) is out of reach; **MCP for Unity v10.0.0** (`CoplayDev/unity-mcp`,
  MIT, 2021.3→6.x) is used. The name `unity-mcp-client` does not exist.
* Unity cannot open a project over `\\wsl.localhost\...` (verified:
  `CreateDirectory '/wsl.localhost' failed`). The repo `unity/` is the source of
  truth; `unity/sync.sh push|pull` mirrors `Assets/ Packages/ ProjectSettings/`
  to the workspace `C:\Users\shiny\cf-unity` (`/mnt/c/...` is the same bytes
  to both sides).
* WSL→Windows TCP is blocked by the firewall and there is no admin. So the MCP
  server runs **as a Windows process over stdio**: Claude Code spawns
  `uvx.exe --from mcpforunityserver==10.0.0 mcp-for-unity` (registered in the
  git-ignored `.mcp.json` as `UnityMCP`); it reaches the Editor on Windows
  localhost:6400. Nothing crosses the firewall.
* `Editor/CfBridgeBoot.cs` starts `StdioBridgeHost` on domain load (the
  service-level `StartAsync` picks HTTP by default and the stdio server then
  finds "0 Unity instances").
* **Run the Editor in `-batchmode` (without `-nographics`) for automation.** A
  GUI Editor launched from WSL never gets activated when the user is working in
  another app, and an un-activated / minimised / occluded Editor does not tick
  `EditorApplication.update` — the bridge never comes up and play mode never
  advances. Batchmode ticks unconditionally; the bridge is up in ~8 s.
* Captures are rendered by `Core/CfCaptureWalk.cs` into a `RenderTexture`
  (`PanelSettings.targetTexture`) and read back with `ReadPixels`; batchmode
  never repaints runtime panels on its own, so the walker calls the internal
  `UIElementsRuntimeUtility.RepaintOffscreenPanels()` first (reflection —
  pinned to 2023.1). `WaitForEndOfFrame` never fires in batchmode.
* Code change → stop Editor → `sync.sh push` → batchmode `-quit` compile →
  relaunch batchmode → drive over MCP. `refresh_unity` on a live Editor with a
  stale server connection hung a domain reload once; it is not used.
* Scenes: `Editor/CfSetup.cs` builds them, but a batchmode UIDocument clears
  its `m_PanelSettings` on serialise, so the committed `.unity` files carry the
  reference by GUID (`3f0cb858…`) directly.

## 4. The three concepts (same `DvsSession`, same fixture)

| | A — Living Chronicle | B — Life + History | C — Causal Archive |
|---|---|---|---|
| Composition | desk: archive stack (L) · one sheet (C) · loose slips (R) | play stage over a persistent C1 strip; ratio inverts at death | dark fragment floor + focus bar; the graph is drawn only under excavation |
| Dominant object | the sheet | the choice cards / the year counter / the strip | the lit fragment / the dug chain |
| Investigation | pull a thread; origin sheet laid beside, 朱 line | hops rise from the strip into the stage | nodes+edges appear one real hop at a time; stubs for other origins |

Required beats 1–14 are all reachable in each (walker script in
`CfCaptureWalk.Script`); captures in `docs/screenshots/unity/`
(`<A|B|C>-NN-<state>-<phase>.png`, plus `-ultrawide` 2560×1080 and `-4x3`
1280×960 passes, `292px-test.png`, `aspect-*.png`, `*-contact-sheet.png`).

## 5. Verification

* Python: **762 passed** (P18 RED 17 unchanged); `tests/test_unity_fixture.py` 10
  (stream byte-identity, hash identity with the book store, determinism, every
  mark/case/recognition locked, D-01 on every option, C-3 ordering, shipped
  file current); black clean; `git diff --check` clean; engine / worldgen /
  causal / models / reporting / persistence **diff = 0**; digest golden and all
  non-P18 goldens unchanged.
* Unity: compile errors **0**; EditMode `ChronicleForge.Tests` **15/15** via MCP
  `run_tests` (fixture loads / other-engine refused / unknown beat refused /
  founder withheld until confirmed / reading earns nothing / monotone confirm /
  D-01 / sealed wording gated / autonomous never "your choice" / paths ordered /
  origin only at end of walk / selection commits nothing / juncture cannot be
  turned past / whole chain reachable / no read-ahead); Console errors during
  every capture walk: 0.
* MCP round trip proven from WSL: `read_console`, `manage_scene get_hierarchy`
  /`load`, `manage_gameobject create/modify/delete`, `manage_editor play/stop`,
  `execute_code`, `run_tests`/`get_test_job`, and the walker-driven captures.

## 6. Known limits (honest)

* Seal is a rail: only the recorded option is sealable (a fixture is one
  history; the notice says so). A live bridge removes the rail.
* The five-phrase event vocabulary makes a two-hop chain read as
  "the order of rule shifts ↑ the order of rule shifts" — truthful, ugly, an
  engine-content fact (see world-diversity analysis).
* Reduced motion is an opt-out (`CF_REDUCE_MOTION=1` / PlayerPrefs); Unity has
  no cross-platform query.
* C's fragment scatter can overlap; A/B/C are mocks, not production layouts.
* TTFs add 19 MB; subset them before any commit that ships fonts.
