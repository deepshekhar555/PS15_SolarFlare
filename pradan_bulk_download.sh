#!/usr/bin/env bash
set -euo pipefail

# PRADAN bulk downloader template
# Usage:
# 1) Create a file named pradan_urls.txt containing one download URL per line (from the PRADAN download script).
# 2) Export your PRADAN cookie string into PRADAN_COOKIE, e.g.:
#      export PRADAN_COOKIE="session=abcd1234; other=..."
# 3) Run:
#      bash pradan_bulk_download.sh
# The script will download files into data/solexs/ and skip files that already exist.

DEST_DIR="data/solexs"
URL_FILE="pradan_urls.txt"

if [ ! -f "$URL_FILE" ]; then
  echo "Error: $URL_FILE not found. Please create it with one PRADAN download URL per line."
  exit 1
fi

if [ -z "${PRADAN_COOKIE:-}" ]; then
  echo "Error: PRADAN_COOKIE environment variable not set."
  echo "Set it like: export PRADAN_COOKIE='session=...; other=...'
  "
  exit 1
fi

mkdir -p "$DEST_DIR"

echo "Starting PRADAN bulk download into $DEST_DIR"
while IFS= read -r url || [ -n "$url" ]; do
  url="$(echo "$url" | sed -e 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [ -z "$url" ] && continue
  fname=$(basename "$url")
  out="$DEST_DIR/$fname"
  if [ -f "$out" ]; then
    echo "Skipping existing: $fname"
    continue
  fi
  echo "Downloading: $fname"
  curl -L --retry 3 --fail --header "Cookie: $PRADAN_COOKIE" -o "$out" "$url"
  sleep 0.2
done < "$URL_FILE"

echo "Done. Downloaded files are in $DEST_DIR"
