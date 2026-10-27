#!/usr/bin/env bash
# Upload the DRM-free desktop builds to itch.io with butler (U-17). Documented, not run in CI.
#
# Prerequisites
#   1. Build the Itch players first (no DL_STEAM define), from unity/DeadLetter, one per OS host:
#        Unity -batchmode -quit -projectPath unity/DeadLetter -executeMethod DeadLetter.Editor.Build.BuildScripts.BuildWindowsItch -logFile -
#        Unity -batchmode -quit -projectPath unity/DeadLetter -executeMethod DeadLetter.Editor.Build.BuildScripts.BuildMacItch -logFile -
#        Unity -batchmode -quit -projectPath unity/DeadLetter -executeMethod DeadLetter.Editor.Build.BuildScripts.BuildLinuxItch -logFile -
#      Output: unity/DeadLetter/Builds/{windows,mac,linux}-itch/ (IL2CPP symbol folders are already moved out to Builds/symbols/).
#   2. Install butler (https://itch.io/docs/butler/) and log in once: `butler login`
#      (CI: set BUTLER_API_KEY instead; never commit it).
#   3. Set ITCH_TARGET to "<itch-user>/<game-slug>" (placeholder below; the page does not exist yet).
#
# Usage
#   ITCH_TARGET=someone/dead-letter tools/build/itch_push.sh 0.1.0            # every channel whose build exists
#   ITCH_TARGET=someone/dead-letter tools/build/itch_push.sh 0.1.0 windows    # one channel
#   DRY_RUN=1 ... prints the butler commands instead of running them.
#
# Channels: windows, mac, linux (itch.io tags the platform from the channel name). butler uploads only the
# difference from the previous push, and --userversion shows the version on the itch page and in the itch app.
set -euo pipefail

VERSION="${1:-}"
ONLY="${2:-}"
TARGET="${ITCH_TARGET:-<itch-user>/<game-slug>}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILDS="$ROOT/unity/DeadLetter/Builds"

if [[ -z "$VERSION" ]]; then
  echo "usage: ITCH_TARGET=user/game $0 <version> [windows|mac|linux]" >&2
  exit 2
fi
if [[ "$TARGET" == *"<"* ]]; then
  echo "Set ITCH_TARGET=<itch-user>/<game-slug> first." >&2
  exit 2
fi
command -v butler >/dev/null 2>&1 || [[ -n "${DRY_RUN:-}" ]] || { echo "butler not found on PATH." >&2; exit 2; }

pushed=0
for channel in windows mac linux; do
  [[ -n "$ONLY" && "$ONLY" != "$channel" ]] && continue
  dir="$BUILDS/$channel-itch"
  if [[ ! -d "$dir" ]]; then
    echo "skip $channel: $dir not built"
    continue
  fi
  if [[ -e "$dir/steam_appid.txt" ]]; then
    echo "refusing $channel: $dir contains steam_appid.txt (a Steam test build?)" >&2
    exit 1
  fi
  # .dl-build-output is BuildScripts' marker (it guards -dlOut deletes); it is not part of the game.
  cmd=(butler push "$dir" "$TARGET:$channel" --userversion "$VERSION" --ignore ".dl-build-output")
  if [[ -n "${DRY_RUN:-}" ]]; then echo "${cmd[*]}"; else "${cmd[@]}"; fi
  pushed=$((pushed + 1))
done

[[ $pushed -gt 0 ]] || { echo "nothing pushed" >&2; exit 1; }
