#!/bin/sh
# Rebuild references/sc-*.md, glossary.md and conformance.md from W3C sources.
# Downloads WCAG 2.2 and its Understanding pages into tools/catalogue/.cache/ (gitignored),
# then extracts, joins the authored content (authored/*.json) and renders the references.
# Usage: tools/catalogue/rebuild.sh [--offline]   (--offline reuses .cache/ without fetching)
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
CACHE="$HERE/.cache"; mkdir -p "$CACHE/understanding"
UA="wcag22-a11y-catalogue-builder (+https://www.w3.org/WAI/WCAG22/)"   # no personal data in requests
if [ "${1:-}" != "--offline" ]; then
  curl -sSfL -A "$UA" -o "$CACHE/wcag22.html" https://www.w3.org/TR/WCAG22/
  while read -r url; do
    f="$CACHE/understanding/$(basename "$url")"
    [ -s "$f" ] || { curl -sSfL -A "$UA" -o "$f" "$url"; sleep 1.5; }
  done < "$HERE/und_urls.txt"
fi
(cd "$CACHE" && python3 "$HERE/extract.py" "$CACHE/wcag22.html")
python3 "$HERE/techs.py"
python3 "$HERE/build.py"
python3 "$HERE/../gen_check_index.py"
