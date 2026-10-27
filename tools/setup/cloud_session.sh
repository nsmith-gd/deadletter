#!/usr/bin/env bash
# Tools a Claude cloud session needs for Dead Letter (issue #19, U-04).
# dotnet 8 builds and tests the pure-C# DeadLetter.Core; the dotnet download hosts are blocked by the
# proxy, but Ubuntu 24.04's apt carries the SDK. bpy (Blender as a Python module) runs the art/**
# generators headless; it is large, so it installs only when DL_NEEDS_BLENDER=1.
# Use it as the environment's setup script, or run it by hand: bash tools/setup/cloud_session.sh
set -euo pipefail

if ! command -v dotnet >/dev/null 2>&1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq dotnet-sdk-8.0 >/dev/null
fi

if [ "${DL_NEEDS_BLENDER:-0}" = "1" ] && ! python3 -c "import bpy" >/dev/null 2>&1; then
  python3 -m pip install --quiet --break-system-packages bpy
fi

echo "dead letter setup: dotnet $(dotnet --version)$(python3 -c 'import bpy; print(", bpy", bpy.app.version_string)' 2>/dev/null || true)"
