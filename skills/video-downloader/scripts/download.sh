#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  download.sh -u <URL> [options] [-- <extra yt-dlp args>]

Options:
  -u <URL>        Video URL (required)
  -o <OUT_DIR>    Output directory (default: /Users/jeff/Downloads)
  -t <TEMPLATE>   Output template (default: "%(title)s.%(ext)s")
  -f <FORMAT>     Format selector (default: "bv*+ba/b")
  -s <LANGS>      Subtitle languages (e.g. "zh-TW,zh-Hant,zh")
  -e              Embed subtitles (requires -s)
  -a              Audio only (mp3)
  -n              No playlist (single item only)
  -c <BROWSER>    Use cookies from browser (e.g. chrome, firefox)
  --keep-originals  Keep original container files (webm/mkv) after conversion
  -h              Show help

Examples:
  download.sh -u "<URL>" -o ./videos
  download.sh -u "<URL>" -s "zh-TW,zh" -e
  download.sh -u "<URL>" -a
  download.sh -u "<URL>" -- --retries 5 --fragment-retries 5

Default output:
  - mp4 container with H.264 video (libx264) + AAC audio
  - Output directory: /Users/jeff/Downloads
  - Original webm/mkv files are removed after successful conversion
USAGE
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/yt-dlp.XXXXXX")"
CLEANUP_SCRIPT="$SCRIPT_DIR/cleanup_temp.sh"

cleanup_tempdir() {
  if [ -n "${TEMP_DIR:-}" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf -- "$TEMP_DIR"
  fi
}
trap cleanup_tempdir EXIT INT TERM

URL=""
OUT_DIR="/Users/jeff/Downloads"
TEMPLATE="%(title)s.%(ext)s"
FORMAT="bv*+ba/b"
MERGE_FORMAT="mkv"
RECODE_VIDEO="mp4"
POSTPROCESSOR_ARGS="ffmpeg:-c:v libx264 -c:a aac"
SUB_LANGS=""
EMBED_SUBS=0
AUDIO_ONLY=0
NO_PLAYLIST=0
COOKIES_BROWSER=""
CLEAN_ORIGINALS=1
EXTRA_ARGS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    -u)
      URL=${2:-""}
      shift 2
      ;;
    -o)
      OUT_DIR=${2:-""}
      shift 2
      ;;
    -t)
      TEMPLATE=${2:-""}
      shift 2
      ;;
    -f)
      FORMAT=${2:-""}
      shift 2
      ;;
    -s)
      SUB_LANGS=${2:-""}
      shift 2
      ;;
    -e)
      EMBED_SUBS=1
      shift 1
      ;;
    -a)
      AUDIO_ONLY=1
      shift 1
      ;;
    -n)
      NO_PLAYLIST=1
      shift 1
      ;;
    -c)
      COOKIES_BROWSER=${2:-""}
      shift 2
      ;;
    --keep-originals)
      CLEAN_ORIGINALS=0
      shift 1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift 1
      EXTRA_ARGS=("$@")
      break
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 2
      ;;
  esac

done

if [ -z "$URL" ]; then
  echo "URL is required."
  usage
  exit 2
fi

if [ "$AUDIO_ONLY" -eq 1 ]; then
  # Prefer audio-only format unless user explicitly set -f
  if [ "$FORMAT" = "bv*+ba/b" ]; then
    FORMAT="ba"
  fi
fi

args=(
  -P "$OUT_DIR"
  -o "$TEMPLATE"
  -f "$FORMAT"
  --paths "temp:$TEMP_DIR"
)

EXEC_CMD="$CLEANUP_SCRIPT"
if [ "$CLEAN_ORIGINALS" -eq 1 ]; then
  EXEC_CMD="$EXEC_CMD --clean-originals"
fi
args+=( --exec "after_move:$EXEC_CMD" )

if [ "$AUDIO_ONLY" -eq 1 ]; then
  args+=( -x --audio-format mp3 )
else
  args+=( --merge-output-format "$MERGE_FORMAT" )
  args+=( --recode-video "$RECODE_VIDEO" )
  args+=( --postprocessor-args "$POSTPROCESSOR_ARGS" )
fi

if [ -n "$SUB_LANGS" ]; then
  args+=( --write-sub --sub-lang "$SUB_LANGS" --sub-format vtt )
  if [ "$EMBED_SUBS" -eq 1 ]; then
    args+=( --embed-subs )
  fi
fi

if [ "$NO_PLAYLIST" -eq 1 ]; then
  args+=( --no-playlist )
fi

if [ -n "$COOKIES_BROWSER" ]; then
  args+=( --cookies-from-browser "$COOKIES_BROWSER" )
fi

if [ "${#EXTRA_ARGS[@]}" -gt 0 ]; then
  args+=( "${EXTRA_ARGS[@]}" )
fi

yt-dlp "${args[@]}" "$URL"
