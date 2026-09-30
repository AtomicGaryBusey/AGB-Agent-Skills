#!/usr/bin/env bash
# Install the rendered-page runner dependencies for wcag_page.mjs.
#
# Installs pinned playwright + axe-core into <skill>/.cache/node (npm --prefix)
# and the Chromium build into <skill>/.cache/ms-playwright. Nothing is vendored
# into git (.cache/ is gitignored). Idempotent: re-running is a no-op when the
# pinned versions are already present.
#
# Usage: setup_page_runner.sh [--check] [--help]
#   --check   verify the install only (exit 0 ok, 1 missing/mismatch)
set -euo pipefail

PLAYWRIGHT_VERSION="1.63.0"
AXE_CORE_VERSION="4.13.0"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CACHE_DIR="${WCAG22_CACHE_DIR:-$SKILL_DIR/.cache}"
NODE_PREFIX="$CACHE_DIR/node"
export PLAYWRIGHT_BROWSERS_PATH="$CACHE_DIR/ms-playwright"

# Print the leading comment block (line 2 up to the first non-comment line), without the "# " prefix.
usage() { awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"; }

installed_version() { # $1 = package name
  local pj="$NODE_PREFIX/node_modules/$1/package.json"
  [ -f "$pj" ] || { echo ""; return; }
  node -e 'process.stdout.write(require(process.argv[1]).version)' "$pj"
}

chromium_ok() {
  # Real verification: launch headless Chromium (the headless shell) and print its version.
  (cd "$NODE_PREFIX" && node -e '
    const { chromium } = require("playwright");
    chromium.launch({ headless: true }).then(async (b) => {
      process.stdout.write("Chromium " + b.version() + " (headless shell)");
      await b.close();
    }).catch(() => process.exit(1));
  ') 2>/dev/null
}

check() {
  local ok=0 pw axe exe
  command -v node >/dev/null || { echo "node: MISSING (Node 18+ required)"; return 1; }
  echo "node:        $(node --version)"
  pw="$(installed_version playwright)"; axe="$(installed_version axe-core)"
  if [ "$pw" = "$PLAYWRIGHT_VERSION" ]; then echo "playwright:  $pw"; else echo "playwright:  ${pw:-MISSING} (want $PLAYWRIGHT_VERSION)"; ok=1; fi
  if [ "$axe" = "$AXE_CORE_VERSION" ]; then echo "axe-core:    $axe"; else echo "axe-core:    ${axe:-MISSING} (want $AXE_CORE_VERSION)"; ok=1; fi
  if [ -n "$pw" ] && exe="$(chromium_ok)"; then
    echo "chromium:    $exe"
  else
    echo "chromium:    MISSING"; ok=1
  fi
  [ -d "$CACHE_DIR" ] && echo "cache size:  $(du -sh "$CACHE_DIR" | cut -f1)  ($CACHE_DIR)"
  return $ok
}

case "${1:-}" in
  -h|--help) usage; exit 0 ;;
  --check) check; exit $? ;;
  "") ;;
  *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
esac

command -v npm >/dev/null || { echo "npm is required" >&2; exit 2; }
mkdir -p "$NODE_PREFIX" "$PLAYWRIGHT_BROWSERS_PATH"
[ -f "$NODE_PREFIX/package.json" ] || echo '{"name":"wcag22-a11y-page-runner","private":true}' > "$NODE_PREFIX/package.json"

if [ "$(installed_version playwright)" != "$PLAYWRIGHT_VERSION" ] || [ "$(installed_version axe-core)" != "$AXE_CORE_VERSION" ]; then
  echo "Installing playwright@$PLAYWRIGHT_VERSION axe-core@$AXE_CORE_VERSION into $NODE_PREFIX"
  npm install --prefix "$NODE_PREFIX" --no-audit --no-fund --save-exact \
    "playwright@$PLAYWRIGHT_VERSION" "axe-core@$AXE_CORE_VERSION"
else
  echo "npm packages already at pinned versions"
fi

if chromium_ok >/dev/null; then
  echo "Chromium already installed"
else
  echo "Downloading Chromium into $PLAYWRIGHT_BROWSERS_PATH"
  (cd "$NODE_PREFIX" && npx --no-install playwright install --only-shell chromium)
fi

echo
check
