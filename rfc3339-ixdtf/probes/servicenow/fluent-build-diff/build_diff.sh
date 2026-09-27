#!/usr/bin/env bash
# Build the fixture app under several host time zones and diff dist/ against TZ=UTC.
# Offline: no instance, no login. Needs @servicenow/sdk installed (see README.md).
# Usage: ./build_diff.sh [APP_DIR] [TZ ...]
#   APP_DIR defaults to ./app (the fixture); point it at your own Fluent app to audit it.
#   TZ list defaults to: UTC America/New_York Asia/Kolkata
# Env: NOW_SDK=/path/to/node_modules/@servicenow/sdk/bin/index.js (auto-detected otherwise)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
APP="$(cd "${1:-$HERE/app}" && pwd)"; shift || true
ZONES=("$@"); [ ${#ZONES[@]} -eq 0 ] && ZONES=(UTC America/New_York Asia/Kolkata)
OUT="${OUT:-$HERE/out}"
if [ -z "${NOW_SDK:-}" ]; then
  d="$APP"; while [ "$d" != "/" ]; do
    [ -f "$d/node_modules/@servicenow/sdk/bin/index.js" ] && NOW_SDK="$d/node_modules/@servicenow/sdk/bin/index.js" && break
    d="$(dirname "$d")"; done
fi
[ -f "${NOW_SDK:-}" ] || { echo "now-sdk not found: run 'npm install' in $HERE (or set NOW_SDK)" >&2; exit 2; }
rm -rf "$OUT"; mkdir -p "$OUT"
status=0
for tz in "${ZONES[@]}"; do
  tag="${tz//\//_}"
  rm -rf "$APP/dist"
  ( cd "$APP" && TZ="$tz" NO_TELEMETRY=1 NO_COLOR=1 node "$NOW_SDK" build ) > "$OUT/build-$tag.log" 2>&1
  rc=$?
  log="$OUT/build-$tag.log"
  errs=$(grep -c 'ERROR' "$log" || true)
  ok=$(grep -c 'Build completed successfully' "$log" || true)
  n=$(find "$APP/dist/app" -name '*.xml' 2>/dev/null | wc -l | tr -d ' ')
  printf '%-20s exit=%s success_msg=%s ERROR_lines=%s xml_files=%s\n' "$tz" "$rc" "$ok" "$errs" "$n"
  if [ "$rc" -eq 0 ] && [ "$errs" -gt 0 ]; then echo "  !! exit 0 with ERROR lines: records may be silently dropped (F12)"; status=1; fi
  [ -d "$APP/dist/app" ] && cp -R "$APP/dist/app" "$OUT/dist-$tag"
done
base="$OUT/dist-${ZONES[0]//\//_}"
for tz in "${ZONES[@]:1}"; do
  tag="${tz//\//_}"
  echo "=== diff ${ZONES[0]} vs $tz (any line here = host-TZ-dependent build output) ==="
  if diff -r -I '"serialNumber"' -I '"timestamp"' "$base" "$OUT/dist-$tag" > "$OUT/diff-$tag.txt"; then echo "(identical)"; else cat "$OUT/diff-$tag.txt"; status=1; fi
done
echo "Outputs: $OUT (logs, dist copies, diffs). The embedded bom.json serialNumber/timestamp lines are ignored: they change on every build by design."
exit $status
