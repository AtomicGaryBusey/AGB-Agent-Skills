# Maintenance: re-validation and SOURCES.lock

`tools/revalidate.py` compares the live state of the wcag22-a11y skill with `SOURCES.lock` at the repo root.
It uses the same flags, exit codes and lock layout as the scripts in the rfc3339-ixdtf, iso999 and ste100 repos,
plus `--run-tests` and `--deep`.

**Licence.** WCAG 2.2 and the Understanding documents are W3C documents (W3C Document License; see `NOTICE`).
`SOURCES.lock` and the reports hold hashes, dates, versions, counts, URLs and one-line errata summaries only.

**Network.** Every request is a GET with the neutral User-Agent
`wcag22-a11y-revalidate/<version> (+https://www.w3.org/WAI/WCAG22/)` and a 30 s timeout. No request carries a
name, email address or user name. `--offline` makes no request at all. The unit tests never use the network.


## First run on a fresh clone

The W3C source copies (`tools/catalogue/.cache/`) and the page-runner engines (`.cache/`) are gitignored, so
`revalidate.py` reports ERROR until you fetch them:

```bash
tools/catalogue/rebuild.sh          # online: downloads WCAG 2.2 and the 87 Understanding pages (neutral User-Agent)
scripts/setup_page_runner.sh        # Playwright, axe-core and Chromium headless shell into .cache/
python3 tools/revalidate.py --check --offline
```

A drift report after this means W3C has changed a page since the lock was written; review it as described below.

## `tools/revalidate.py`

Standard library only. The engine checks need `node`; the page-runner suite needs `scripts/setup_page_runner.sh`
to have been run.

```sh
python3 tools/revalidate.py                  # --check (default): compare live state with SOURCES.lock
python3 tools/revalidate.py --run-tests      # also run the five test suites and compare their counts
python3 tools/revalidate.py --update         # rewrite SOURCES.lock (runs the tests; refused unless all green)
python3 tools/revalidate.py --offline        # skip the network sources
python3 tools/revalidate.py --deep           # also fetch all 87 live Understanding pages (1 request/s)
python3 tools/revalidate.py --lock PATH      # use another lock (for example a copy you are testing)
python3 tools/revalidate.py --report PATH    # also write the Markdown report to PATH
```

| Exit | Meaning |
|---|---|
| 0 | No change against the lock |
| 1 | Drift: the report gives a plain-language summary, then every changed key |
| 2 | Error: the lock is missing or unreadable, a source could not be read, or `--update` was refused |

A check takes under 1 s offline plus the time of seven network requests online; with `--run-tests` about 45 s,
most of it the page-runner suite.

| Area | Source | Lock section |
|---|---|---|
| Skill | `SKILL.md` front matter (`name`, `metadata.version`, `metadata.standard`) | `skill` |
| Pinned WCAG 2.2 | `tools/catalogue/.cache/wcag22.html`, the copy the catalogue was built from: sha256, size, status line, dated version and its URL; whether `SKILL.md` names the same dated version | `spec` |
| Understanding pages | `tools/catalogue/.cache/understanding/*.html` (the 87 URLs in `und_urls.txt`): sha256 and "Updated" date of each | `catalogue.understanding` |
| Techniques | Not cached separately. Technique IDs come from the Understanding pages (`.cache/techs.json`): count of SC and technique IDs | `catalogue.techniques` |
| Catalogue build | sha256 of `.cache/wcag.json` and `.cache/techs.json`; tree sha256 of `tools/catalogue/` (builder, `authored/`, `axe_map.json`, `und_urls.txt`); sha256 of the generated `references/sc-*.md`, `glossary.md`, `conformance.md`, `check-index.md` | `catalogue.derived`, `catalogue.inputs`, `catalogue.outputs` |
| Reproducibility | Copies `tools/` and `references/` to a temp folder, runs `tools/catalogue/rebuild.sh --offline` there, and compares every file in `references/` byte for byte | `catalogue.offline_rebuild` |
| Engines | Pins in `scripts/setup_page_runner.sh`; installed `playwright`, `playwright-core`, `axe-core` in `.cache/node`; the Chromium headless-shell revision from `playwright-core/browsers.json` and whether it is installed in `.cache/ms-playwright`; `node --version`. `WCAG22_CACHE_DIR` moves `.cache/`, as it does for the installer | `engines.pinned`, `engines.installed`, `engines.node` |
| axe-core rules | `axe.getRules()` of the installed axe-core: every rule ID (with `(deprecated)` / `(experimental)`), and whether the `wcagNNN` tags still give exactly `tools/catalogue/axe_map.json` | `engines.axe` |
| Tests (`--run-tests`, `--update`) | see the table below | `tests` |
| WCAG 2.2 (network) | <https://www.w3.org/TR/WCAG22/>: status, date, "This version" URL, sha256, and whether the bytes equal the catalogue cache | `sources.wcag22` |
| Errata (network) | <https://www.w3.org/WAI/WCAG22/errata/>: last-modified date, each publication section, every entry (date, class, one-line summary), counts | `sources.errata` |
| Other WCAG versions (network) | Status line and dated URL of <https://www.w3.org/TR/WCAG21/>, <https://www.w3.org/TR/WCAG20/> and <https://www.w3.org/TR/wcag-3.0/> (first 400 KB of each page) | `sources.wcag21`, `sources.wcag20`, `sources.wcag30` |
| npm releases (network) | `https://registry.npmjs.org/<pkg>/latest` for playwright and axe-core. Shown as "update available" in the Engines table; nothing is installed | `upstream.npm` |
| Live Understanding (`--deep`, network) | The "Updated" date of each live Understanding page | `understanding_live` |

Test suites (run from the repo root):

| Lock key | Command |
|---|---|
| `unit_scripts` | `python3 -m unittest discover -s scripts -p "test_*.py"` |
| `page_runner` | `caffeinate -d node --test scripts/test_wcag_page.mjs` (`caffeinate -d` on macOS only) |
| `gen_check_index_check` | `python3 tools/gen_check_index.py --check` |
| `grader_selftest` | `python3 evals/graders/selftest.py` |
| `unit_revalidate` | `python3 -m unittest discover -s tools -p "test_*.py"` |

Sections that a run does not check are listed in the report header ("not checked") and are not compared:
`sources` and `upstream` with `--offline`, `tests` without `--run-tests`, `understanding_live` without `--deep`.
An `--update` keeps the previous lock's copy of any network section it did not check. `meta` is never compared.

### Reading drift

- **"new dated version of WCAG 2.2 published"**: `/TR/WCAG22/` now points at a new dated version. Re-run
  `tools/catalogue/rebuild.sh` online (it re-downloads `wcag22.html`), review the diff of `references/`, update
  `metadata.standard` in `SKILL.md` and `NOTICE`, run the suites, then `--update`.
- **WCAG 2.2 page bytes changed without a new dated version**: W3C re-published the same version (markup or
  errata links). Download it to a scratch file and diff it against `tools/catalogue/.cache/wcag22.html` before
  you rebuild.
- **NEW editorial / SUBSTANTIVE erratum**: `references/` quotes the dated Recommendation, not the errata.
  Read the entry. A substantive erratum may change what an SC requires in practice: note it in
  `references/interpretation.md` or the SC file. Then `--update`.
- **WCAG 2.1 / 2.0 / 3.0 status changed**: for example a new WCAG 3.0 draft, a Candidate Recommendation, or a
  version marked Superseded. Check whether `SKILL.md` (authority, version mapping) needs a line.
- **Cached Understanding pages changed / live Understanding page updated (`--deep`)**: `rebuild.sh` downloads
  an Understanding page only when it is not cached. To refresh one, delete it from
  `tools/catalogue/.cache/understanding/` and re-run `rebuild.sh` online; then review `references/`.
- **Offline catalogue rebuild does NOT reproduce references/**: someone edited a generated file by hand, or the
  builder, `authored/*.json` or the cache changed without a rebuild. Run `tools/catalogue/rebuild.sh --offline`,
  review the diff, and move hand edits into `authored/`.
- **engines.installed differs from engines.pinned**: run `scripts/setup_page_runner.sh`.
- **"update available"** (Engines table) or **npm latest release changed**: advice only. To adopt it, change
  `PLAYWRIGHT_VERSION` / `AXE_CORE_VERSION` in `scripts/setup_page_runner.sh`, run it, check the new axe rules
  in the report, update `tools/catalogue/axe_map.json` if the SC tags moved, rebuild the catalogue, run
  `--run-tests`, then `--update`.
- **NEW / REMOVED axe-core rules** or **axe_map.json no longer matches**: the Notes list every SC whose rules
  differ. Edit `tools/catalogue/axe_map.json`, run `rebuild.sh --offline` (the SC files list axe rules), then
  `--update`.
- **Test counts changed**: usually a deliberate change (new tests). Review, then `--update`.

### Updating the lock

After you have reviewed a drift report and updated the skill, run `python3 tools/revalidate.py --update` and
commit `SOURCES.lock` with the change. `--update` always runs the test suites and refuses to write the lock
unless every suite is green. `meta.snapshots` records the date of each section.

The first lock was written on 2026-09-29: WCAG 2.2 Recommendation of 12 December 2024
(`https://www.w3.org/TR/2024/REC-WCAG22-20241212/`, bytes identical to the catalogue cache), 28 editorial
errata and no substantive errata, Playwright 1.63.0 with Chromium headless shell r1243, axe-core 4.13.0
(105 rules, `axe_map.json` matching).

## Monthly run: local launchd job (not installed)

`tools/launchd/com.local.wcag22-a11y-revalidate.plist.template` runs `revalidate.py --check --run-tests` on the
3rd of each month at 09:30 local time (if the Mac is asleep then, launchd runs the job at the next wake; if it is
off, that month is skipped). It writes `~/Library/Logs/skill-revalidate/wcag22-a11y-<YYYY-MM-DD>.md` and a line
in `runs.log`, and posts a macOS notification only on drift (exit 1) or error (exit 2). A clean month is silent.
The other skills' jobs use the same log folder on the 1st and 2nd.

The template holds no machine paths: `__HOME__`, `__PYTHON__`, `__REPO__` and `__PATH__` are filled at install
time. `__PATH__` must reach `node`; the commands below copy your shell's `PATH`.

The job is **not** installed or loaded. To install it:

```sh
PY="$(command -v python3)"                                   # a Python 3.9+
REPO="$HOME/.claude/skills/wcag22-a11y"                      # or wherever the repo lives
dst="$HOME/Library/LaunchAgents/com.local.wcag22-a11y-revalidate.plist"
mkdir -p "$HOME/Library/Logs/skill-revalidate"
sed -e "s|__HOME__|$HOME|g" -e "s|__PYTHON__|$PY|g" -e "s|__REPO__|$REPO|g" -e "s|__PATH__|$PATH|g" \
  "$REPO/tools/launchd/com.local.wcag22-a11y-revalidate.plist.template" > "$dst"
plutil -lint "$dst"
launchctl bootstrap "gui/$(id -u)" "$dst"
launchctl print "gui/$(id -u)/com.local.wcag22-a11y-revalidate" | head -20    # confirm it is loaded
launchctl kickstart -p "gui/$(id -u)/com.local.wcag22-a11y-revalidate"       # optional: run it once now
```

To make no network requests, add `--offline` after `--check` in the installed plist. To skip the 45 s test run,
remove `--run-tests`.

To uninstall:

```sh
launchctl bootout "gui/$(id -u)/com.local.wcag22-a11y-revalidate"
rm "$HOME/Library/LaunchAgents/com.local.wcag22-a11y-revalidate.plist"
# optional: rm "$HOME"/Library/Logs/skill-revalidate/wcag22-a11y-*
```

## `/schedule` (cloud routine)

Possible but limited. The sources are public, so nothing licensed would leave the machine. But the catalogue
cache (`tools/catalogue/.cache/`) and the engines (`.cache/`) are gitignored, so a cloud clone has neither: the
`spec`, `catalogue` and `engines` sections would always drift unless the routine first ran `rebuild.sh` and
`setup_page_runner.sh`, and the page-runner suite needs a Chromium that can run there. The local launchd job
avoids all of this.
