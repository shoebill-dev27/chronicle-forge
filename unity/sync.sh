#!/usr/bin/env bash
# Mirror the version-controlled Unity project to the Windows-side workspace.
#
# WHY: Unity cannot open a project over a UNC path — `Unity.exe -createProject
# \\wsl.localhost\...` fails with "CreateDirectory '/wsl.localhost' failed:
# アクセスが拒否されました". So the repo holds the project (the source of truth,
# what gets committed) and `$CF_UNITY_WS` holds the live Editor workspace, which
# lives under /mnt/c and is therefore the same bytes to both WSL and Windows.
#
#   ./sync.sh push   repo -> workspace   (before opening / compiling in Unity)
#   ./sync.sh pull   workspace -> repo   (after the Editor has written assets)
#
# Only Assets/, Packages/ and ProjectSettings/ cross. Library/, Temp/, Logs/ and
# UserSettings/ are Editor-generated caches and never belong in the repo.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="${CF_UNITY_WS:-/mnt/c/Users/shiny/cf-unity}"
DIRS=(Assets Packages ProjectSettings)

case "${1:-push}" in
  push)
    mkdir -p "$WS"
    for d in "${DIRS[@]}"; do
      rsync -a --delete "$HERE/$d/" "$WS/$d/"
    done
    echo "pushed -> $WS"
    ;;
  pull)
    for d in "${DIRS[@]}"; do
      # --delete is deliberately absent: the Editor adds .meta files we want,
      # and a stale workspace must never silently delete repo content.
      rsync -a "$WS/$d/" "$HERE/$d/"
    done
    echo "pulled <- $WS"
    ;;
  *) echo "usage: sync.sh [push|pull]" >&2; exit 2 ;;
esac
