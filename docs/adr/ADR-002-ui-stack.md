# ADR-002 — UI Stack for the Living Chronicle Client

- Status: **Accepted** (Tech Lead decision, 2026-07-20; day-7 go/no-go
  checkpoint 2026-07-27)
- Deciders: Tech Lead (architecture is lead-owned per project policy)

## Context

The repo is a pure-Python deterministic engine + read-model/app layer emitting
id-free JSON-able views (`app/contracts.py`, `app/services.py`); the only
presentation today is terminal prose. v1 needs a shippable graphical book:
16 page types, a spine/flip state machine, two-typeface typography as the
core device, ink-motion, pointer+keyboard input, hold-to-remember, packaged
for desktop by a solo developer in ~3 weeks of build time. Typography quality
IS the product (UX spec §7); the client renders views and owns only
presentation + discovery/reveal state (Client State Spec, D-6).

## Options considered

| Option | Verdict | Why |
|---|---|---|
| **pywebview + local static HTML/CSS/JS** | **Chosen** | Best-in-class typography control (webfonts, OpenType features, line-height/measure control — critical for 明朝/手書き contrast per ADR-003); ink/pulse/hold animation trivial in CSS; consumes the existing JSON contracts directly; stays a Python-launched single app (no server exposure); HTML/CSS is also the medium LLM build agents are most fluent in — a real velocity factor for this team shape |
| Qt (QML/Widgets) | Rejected | Weaker fine typography + text-flow control for a text-as-product game; slower iteration for this team |
| Godot | Rejected | Second runtime + IPC to the Python engine; capability overkill (no scene/physics needs); packaging complexity |
| Textual (TUI) | Rejected | Cannot deliver the two-typeface print/Hand device — the load-bearing visual |
| Electron / Tauri + Python sidecar | Rejected | Two-process architecture and heavier packaging for no additional capability over pywebview here |

## Decision

**pywebview shell over a static, fully local HTML/CSS/JS frontend**, consuming
the app layer's JSON views through the pywebview bridge. No network access; no
external CDN (all fonts/assets bundled). The frontend holds the page state
machine and the client-side discovery-state store (per D-6); all world truth
comes from the Python app layer. Packaging: PyInstaller bundle including the
webview backend, per-OS smoke-tested in CI.

## Consequences & risks

- **Risk: webview backend variance per OS** (WebView2 / WebKitGTK / Cocoa).
  Mitigation: pin supported OS targets now (Windows + Linux first; macOS if CI
  allows), per-OS smoke test in the packaging lane.
- **Go/no-go 2026-07-27:** if the walking-skeleton increment (I-1, roadmap)
  cannot render two-typeface pages with turn/seal/hold verbs through the
  bridge by then, fall back to the same static frontend served on
  `localhost` + system browser (degraded but identical frontend code), and
  re-plan packaging.
- The read-model contracts stay the API; nothing in the client may import
  engine internals — the P23 API-contract phase is effectively brought
  forward in "internal contract" form.
