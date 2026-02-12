#!/usr/bin/env bash
set -euo pipefail

print_help() {
  cat <<'USAGE'
install_yt-dlp.sh

Installs yt-dlp using the system package manager.
Supported: macOS (Homebrew), Debian/Ubuntu (apt), RHEL/Fedora (dnf/yum), Windows (winget/choco).
Options:
  --skip-update   Skip Homebrew update (macOS only)
Environment:
  SKIP_BREW_UPDATE=1  Skip Homebrew update (macOS only)
USAGE
}

skip_update=0
if [ "${SKIP_BREW_UPDATE:-}" = "1" ]; then
  skip_update=1
fi

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help)
      print_help
      exit 0
      ;;
    --skip-update)
      skip_update=1
      shift 1
      ;;
    *)
      echo "Unknown option: $1"
      print_help
      exit 2
      ;;
  esac
done

uname_s="$(uname -s 2>/dev/null || true)"

if command -v yt-dlp >/dev/null 2>&1; then
  echo "yt-dlp is already installed."
  yt-dlp --version || true
  exit 0
fi

case "$uname_s" in
  Darwin)
    if ! command -v brew >/dev/null 2>&1; then
      echo "Homebrew not found. Please install Homebrew first: https://brew.sh/"
      exit 1
    fi
    if [ "$skip_update" -eq 0 ]; then
      brew update
    else
      echo "Skipping Homebrew update."
    fi
    brew install yt-dlp
    ;;
  Linux)
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update
      sudo apt-get install -y yt-dlp
    elif command -v dnf >/dev/null 2>&1; then
      sudo dnf install -y yt-dlp
    elif command -v yum >/dev/null 2>&1; then
      sudo yum install -y yt-dlp
    else
      echo "No supported package manager found (apt/dnf/yum)."
      exit 1
    fi
    ;;
  MINGW*|MSYS*|CYGWIN*)
    if command -v winget >/dev/null 2>&1; then
      winget install --id yt-dlp.yt-dlp -e
    elif command -v choco >/dev/null 2>&1; then
      choco install yt-dlp -y
    else
      echo "Please install yt-dlp via winget or Chocolatey."
      exit 1
    fi
    ;;
  *)
    echo "Unsupported OS: $uname_s"
    exit 1
    ;;
esac

if command -v yt-dlp >/dev/null 2>&1; then
  echo "yt-dlp installed successfully."
  yt-dlp --version || true
else
  echo "yt-dlp install attempted but command not found."
  exit 1
fi
