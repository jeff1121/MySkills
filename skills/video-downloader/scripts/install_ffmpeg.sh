#!/usr/bin/env bash
set -euo pipefail

print_help() {
  cat <<'USAGE'
install_ffmpeg.sh

Installs ffmpeg using the system package manager.
Supported: macOS (Homebrew), Debian/Ubuntu (apt), RHEL/Fedora (dnf/yum), Windows (winget/choco).
USAGE
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  print_help
  exit 0
fi

uname_s="$(uname -s 2>/dev/null || true)"

if command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is already installed."
  ffmpeg -version | head -n 1 || true
  exit 0
fi

case "$uname_s" in
  Darwin)
    if ! command -v brew >/dev/null 2>&1; then
      echo "Homebrew not found. Please install Homebrew first: https://brew.sh/"
      exit 1
    fi
    brew update
    brew install ffmpeg
    ;;
  Linux)
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update
      sudo apt-get install -y ffmpeg
    elif command -v dnf >/dev/null 2>&1; then
      sudo dnf install -y ffmpeg
    elif command -v yum >/dev/null 2>&1; then
      sudo yum install -y ffmpeg
    else
      echo "No supported package manager found (apt/dnf/yum)."
      exit 1
    fi
    ;;
  MINGW*|MSYS*|CYGWIN*)
    if command -v winget >/dev/null 2>&1; then
      winget install --id Gyan.FFmpeg -e
    elif command -v choco >/dev/null 2>&1; then
      choco install ffmpeg -y
    else
      echo "Please install ffmpeg via winget or Chocolatey."
      exit 1
    fi
    ;;
  *)
    echo "Unsupported OS: $uname_s"
    exit 1
    ;;
esac

if command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg installed successfully."
  ffmpeg -version | head -n 1 || true
else
  echo "ffmpeg install attempted but command not found."
  exit 1
fi
