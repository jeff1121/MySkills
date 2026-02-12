#!/usr/bin/env bash
set -euo pipefail

clean_originals=0
target=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --clean-originals)
      clean_originals=1
      shift 1
      ;;
    --keep-originals)
      clean_originals=0
      shift 1
      ;;
    -h|--help)
      echo "Usage: cleanup_temp.sh [--clean-originals] <final_output_path>"
      exit 0
      ;;
    *)
      if [ -z "$target" ]; then
        target="$1"
      fi
      shift 1
      ;;
  esac
done

if [ -z "$target" ]; then
  exit 0
fi
dirname "$target" >/dev/null 2>&1 || exit 0

dir="$(dirname "$target")"
base="$(basename "$target")"
base_no_ext="${base%.*}"
final_ext="${base##*.}"

if [ ! -d "$dir" ]; then
  exit 0
fi

prefix_temp="${base_no_ext}.temp."
prefix_f="${base_no_ext}.f"
prefix_part="${base}.part"

while IFS= read -r -d '' path; do
  name="$(basename "$path")"
  if [ "$name" = "$base" ]; then
    continue
  fi

  if [[ "$name" == "$prefix_temp"* ]]; then
    rm -f -- "$path"
    continue
  fi
  if [[ "$name" == "$prefix_f"* ]]; then
    rm -f -- "$path"
    continue
  fi
  if [[ "$name" == "$prefix_part"* ]]; then
    rm -f -- "$path"
    continue
  fi

done < <(find "$dir" -maxdepth 1 -type f -print0)

if [ "$clean_originals" -eq 1 ]; then
  for ext in webm mkv; do
    if [ "$ext" = "$final_ext" ]; then
      continue
    fi
    candidate="$dir/$base_no_ext.$ext"
    if [ -f "$candidate" ]; then
      rm -f -- "$candidate"
    fi
  done
fi
