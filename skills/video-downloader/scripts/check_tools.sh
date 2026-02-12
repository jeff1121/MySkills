#!/usr/bin/env bash
set -euo pipefail

missing=0

check_cmd() {
  local cmd="$1"
  local ver_cmd="$2"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "missing: $cmd"
    missing=1
    return
  fi
  # Print first line of version output for a quick sanity check
  if output=$(eval "$ver_cmd" 2>/dev/null | head -n 1); then
    echo "found: $cmd -> $output"
  else
    echo "found: $cmd"
  fi
}

check_cmd "yt-dlp" "yt-dlp --version"
check_cmd "ffmpeg" "ffmpeg -version"

if [ "$missing" -ne 0 ]; then
  echo "Please install the missing tools and retry."
  exit 1
fi
