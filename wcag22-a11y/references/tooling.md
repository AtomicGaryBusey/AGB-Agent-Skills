# Tooling reference

> **Attribution.** SC numbers, names and levels are those of *Web Content Accessibility Guidelines (WCAG) 2.2*,
> W3C Recommendation, 12 December 2024, <https://www.w3.org/TR/WCAG22/>. Copyright © 2024 World Wide Web
> Consortium, <https://www.w3.org/copyright/document-license-2023/>. No normative text is quoted in this file;
> everything else is original to this skill. See `NOTICE`.

Four tools, all in `scripts/`. `S=~/.claude/skills/wcag22-a11y/scripts` below.

| Tool | Runtime | Input | Role |
|---|---|---|---|
| `wcag_audit.py` | Python 3.9+, stdlib | source path and/or URL | Runs the two auditors, merges, writes the report skeleton |
| `wcag_scan.py` | Python 3.9+, stdlib | source files and directories | Static scan of markup, components, templates, CSS |
| `wcag_page.mjs` | Node 18+ | URL, `.html` file, or directory | Rendered-page audit in headless Chromium: axe-core + custom checks |
| `setup_page_runner.sh` | bash, npm | — | Installs the page runner dependencies into `.cache/` |

All auditors share one contract: a JSON envelope `{"meta", "summary", "findings"}` and the exit codes
**0** = no `fail` finding, **1** = at least one `fail`, **2** = usage or runtime error.

## 1. `wcag_audit.py` (orchestrator)

```
python3 $S/wcag_audit.py TARGET [--url URL] [--level A|AA|AAA] [--pages N]
                        [--no-page] [--no-scan] [--probe-actions] [--screenshots DIR]
                        [--check-timeout MS] [--json OUT] [--report md|json] [--out FILE] [--version]
```

| Flag | Meaning |
|---|---|
| `TARGET` | Source directory or file for the static scan, or a URL (then the scan is skipped and the URL goes to the page runner) |
| `--url URL` | Rendered URL, local `.html` file or directory for the page runner |
| `--level` | Audit level, default `AA` (55 SC). Passed to both tools |
| `--pages N` | Pages for the page runner to crawl (same origin), default 1 |
| `--no-page` / `--no-scan` | Skip the page runner / the static scanner |
| `--probe-actions` | Let the page runner press ordinary buttons on http(s) targets (always on for local files) |
| `--screenshots DIR` | Passed to the page runner: page, reflow and failing-focus screenshots |
| `--check-timeout MS` | Passed to the page runner: time budget per check per page (default 120000) |
| `--json OUT` | Also write the merged machine-readable result to OUT |
| `--report md\|json` | Report format on stdout or `--out` (default `md`) |
| `--out FILE` | Write the report to FILE instead of stdout |

Page target resolution: `--url` if given; else TARGET if it is a URL; else TARGET if it is an `.html` file or a
directory with top-level `*.html` files; else the page runner is listed under "Not run". Before it starts the
page runner, the orchestrator runs `setup_page_runner.sh --check`; if that fails, the page runner is listed as
"not installed" under "Not run" and the static scan result is still reported.

Exit codes: 0 = no nonconformities, 1 = nonconformities, 2 = usage or error.

**Markdown report** (the skeleton you complete) follows the SKILL.md format: title, `Scope`, `Summary`,
`Evidence` lines; `## Findings` in the shared 9-column table, ranked by severity then SC; `## SC coverage`
(Check ID, Success criterion, Level, Status, Tool signal, Automated by); `## Review notes`; `## Manual checks
required` (Check ID, level, first step, procedure link); `## Not run / not applicable` (includes page-level
errors such as timed-out checks, grouped by check with the SC coverage they cost); `## Assumptions`;
`## Reproduction`; and `## Appendix: raw tool finding counts per SC`.

- `Summary` counts report rows by severity and gives SC status as `N fail (tool), [n] pass, [n] N/A,
  [n] not evaluated`. The placeholders are yours to fill after the manual pass.
- Coverage `Status` is only `Fail` (a tool found a failure) or `Not evaluated`. The tool's own signal
  (`failures found`, `warnings`, `automated checks passed (partial coverage)`, `not automatable`, `not checked`)
  is in the `Tool signal` column. None of these is "pass"; you set pass, fail, N/A or not evaluated.
- Locations are relative to the target root (for example `css/site.css:52`).
- Rows with the same check, SC, severity and rules plus the same source line or selector pattern (`:nth-*`
  indexes removed) collapse into one row, for example `` `.site-nav a` × 11 pages (77 instances) ``. The JSON
  keeps every finding.

Severity mapping in the skeleton: `fail` → Nonconformity, `warn` → Deviation, `manual` → Review note,
`info` → Advisory. Findings from different tools with the same SC, location and line/selector/snippet are merged
into one row; the most severe tool severity wins.

**Merged JSON** (`--json OUT` or `--report json`):

```json
{
  "meta": {"tool": "wcag_audit", "version": "0.1.0", "wcag": "2.2 (2024-12-12)", "target": "...", "url": "...",
           "level": "AA", "date": "...", "command": "...",
           "runs": [{"tool": "wcag_scan", "command": "...", "exit_code": 1, "ok": true, "meta": {...},
                     "n_findings": 18, "by_severity": {...}}]},
  "summary": {"nonconformities": 17, "deviations": 3, "advisories": 0, "review_notes": 0, "by_sc": {...},
              "report_rows": {...}, "sc_status": {"fail": 9, "to_be_judged": 46, "pass": null, "na": null,
                                                 "not_evaluated": null}},
  "report_rows": [{"findings": [1, 4], "pages": ["index.html"], "instances": 2, "pattern": "..."}],
  "findings": [{"check_id": "WCAG-1.1.1", "sc": "1.1.1", "sc_name": "...", "level": "A",
                "tool_severity": "fail", "severity": "Nonconformity", "target": "page|component|stylesheet|template",
                "file": "...", "path": "css/site.css", "url": null, "line": 13, "col": 3, "selector": "img", "snippet": "...",
                "message": "...", "help": "<Understanding URL>", "tools": ["wcag_scan"],
                "rules": ["wcag_scan:img-missing-alt"], "sources": [<raw tool findings>], "n": 1}],
  "coverage": [{"check_id": "WCAG-1.1.1", "sc": "1.1.1", "title": "...", "level": "A", "testability": "assisted",
                "status": "failures found", "report_status": "Fail", "counts": {"fail": 3, "warn": 0, "manual": 0, "info": 0},
                "covered_by": ["wcag_page", "wcag_scan"], "needs_human": true,
                "procedure": "<first step>", "procedure_ref": "references/sc-1-perceivable.md#wcag-1-1-1"}]
}
```

## 2. `wcag_scan.py` (static scanner)

```
python3 $S/wcag_scan.py [PATH ...] [--json] [--level A|AA|AAA] [--min-severity info|manual|warn|fail]
                       [--list-rules] [--version]
```

| Flag | Meaning |
|---|---|
| `PATH` | Files or directories (recursive) |
| `--json` | Emit the JSON envelope (default: one text line per finding, `file:line:col: SEV WCAG-x.y.z (level) [rule] message`, then the source line) |
| `--level` | Highest level to report, default `AA` |
| `--min-severity` | Lowest severity to report; order `info < manual < warn < fail`; default `info` |
| `--list-rules` | Print every rule: slug, SC, level, default severity, description |

Script linking: the scanner reads external `.js` files, inline scripts and Vue/Svelte script blocks, and links
listeners (`addEventListener`, `el.onX =`, jQuery, delegated `closest`/`matches`) to elements in the HTML
pages that load the script via `getElementById`, `querySelector(All)` and simple aliases. A script that no page
loads is linked to every page. Findings from linking are reported at the element's HTML location with the
listener's `file:line` in the evidence, and are never `fail`: confirm them in the browser or the source.

Exit codes: 0 no `fail`, 1 `fail` findings, 2 usage or I/O error.

**File types** (by extension): HTML (`.html .htm .xhtml`); JSX/JS (`.jsx .tsx .js .mjs`); script-only JS
(`.ts .cjs`); `.vue`; `.svelte`; templates (`.erb .hbs .handlebars .njk .liquid .mustache .jinja .jinja2 .j2
.twig .ejs .php .cshtml .razor`); CSS (`.css .less`, `.scss`); Markdown (`.md .markdown .mdx`). Minified and
bundle files (`.min.js`, `.min.css`, `.bundle.js`, `.d.ts`) are skipped.

**Skipped directories** while walking: `node_modules dist build out .git vendor .cache .next .nuxt .svelte-kit
coverage __pycache__ .venv venv bower_components` and any other hidden directory. A directory you pass
explicitly (for example `dist/`) is scanned; only its nested matches are skipped. Template constructs are
replaced with a placeholder character, so dynamic values are treated as unknown, not as empty.

**Envelope:**

```json
{"meta": {"tool": "wcag_scan", "version": "0.1.0", "wcag": "2.2 (2024-12-12)", "target": "...",
          "date": "...", "level": "AA", "files_scanned": 2, "errors": ["<file>: <reason>"]},
 "summary": {"by_sc": {"1.1.1": {"fail": 3, "warn": 0, "manual": 0, "info": 0}},
             "by_severity": {"fail": 16, "warn": 3, "manual": 0, "info": 0}},
 "findings": [{"tool": "wcag_scan", "id": "WCAG-2.4.2", "sc": "2.4.2", "sc_name": "Page Titled", "level": "A",
               "rule": "page-title-missing", "severity": "fail", "file": "...", "line": 2, "col": 1,
               "selector": "html", "snippet": "<html>", "message": "...", "help": "<Understanding URL>",
               "evidence": {}}]}
```

`meta.errors` lists files that could not be read or were too deeply nested; they are not "clean". `evidence`
holds measured values where a rule has them (contrast `ratio`, `color`, `background`; ids; target file/line).

**Rules** (`--list-rules` is authoritative; 70 rules on 32 SC). Default severity in brackets.

| SC | Rules |
|---|---|
| 1.1.1 | `img-missing-alt` [fail], `img-alt-empty-in-control` [fail], `button-icon-no-name` [fail], `input-image-missing-alt` [fail], `area-missing-alt` [fail], `svg-img-no-name` [fail], `img-alt-suspicious` [warn], `icon-button-component-no-name` [warn], `svg-icon-no-alt` [warn] |
| 1.3.1 | `control-no-label` [fail], `li-outside-list` [fail], `heading-skip` [warn], `layout-table-with-th` [warn], `radio-group-no-fieldset` [warn], `required-asterisk-only` [warn], `table-no-th` [warn] |
| 1.3.5 | `autocomplete-invalid` [fail], `autocomplete-missing` [warn] |
| 1.4.2 | `media-autoplay-audio` [warn] |
| 1.4.3 | `contrast-text` [fail], `contrast-unresolved` [manual] |
| 1.4.4 | `viewport-zoom-disabled` [fail] |
| 1.4.1 | `color-only-reference` [manual] |
| 1.4.10 | `fixed-width-no-max` [warn] |
| 1.4.11 | `focus-indicator-contrast` [warn], `ui-border-contrast` [warn] |
| 1.4.13 | `hover-content-no-dismiss` [manual] |
| 1.4.12 | `text-spacing-important` [warn] |
| 2.1.1 | `click-no-keyboard` [fail in markup; warn when the listener is found by linking an external script] |
| 2.2.1 | `meta-refresh-delay` [fail] |
| 2.2.2 | `marquee-blink` [fail], `media-autoplay-no-controls` [warn] |
| 2.4.1 | `bypass-blocks-missing` [warn] |
| 2.4.2 | `page-title-missing` [fail] |
| 2.4.3 | `tabindex-positive` [warn] |
| 2.4.4 | `link-empty` [fail], `link-icon-no-name` [fail], `link-text-generic` [warn] |
| 2.4.6 | `heading-empty` [fail] |
| 2.4.7 | `focus-outline-removed` [fail], `focus-outline-removed-maybe` [warn] |
| 2.4.11 / 2.4.12 / 2.4.13 | `focus-obscured-check` [manual], `focus-obscured-enhanced-check` [manual, AAA], `focus-appearance-check` [manual, AAA] |
| 2.5.3 | `label-in-name` [fail] |
| 2.5.7 | `drag-no-alternative` [warn], `drag-library-check` [manual] |
| 2.5.8 | `target-size-small` [warn] |
| 3.1.1 / 3.1.2 | `html-lang-missing` [fail], `html-lang-invalid` [fail], `lang-invalid` [fail] |
| 3.2.2 | `onchange-navigates` [warn] |
| 3.3.1 | `error-not-described` [warn] |
| 3.3.2 | `placeholder-only-label` [fail] |
| 3.3.7 | `redundant-entry` [warn], `redundant-entry-same-step` [manual] |
| 3.3.8 | `paste-blocked` [fail], `paste-blocked-maybe` [warn], `captcha-on-auth` [warn], `password-autocomplete-off` [warn] |
| 4.1.2 | `aria-attr-invalid`, `aria-attr-value-invalid`, `aria-hidden-focusable`, `aria-required-attr`, `aria-role-invalid`, `button-empty`, `custom-control-no-name`, `duplicate-id-referenced`, `iframe-no-title` [fail]; `aria-idref-missing`, `click-handler-no-role`, `focusable-no-role` [warn], `aria-state-not-updated` [warn] |
| 4.1.3 | `status-message-no-live` [warn], `status-message-js-no-live` [warn] |

## 3. `wcag_page.mjs` (rendered-page runner)

```
node $S/wcag_page.mjs <url|file.html|dir> [--json] [--level A|AA|AAA] [--viewport WxH] [--pages N]
                     [--screenshots DIR] [--timeout MS] [--max-tabs N] [--observe MS] [--check-timeout MS]
                     [--rules LIST] [--no-axe] [--probe-actions] [--help]
```

| Flag | Meaning (default) |
|---|---|
| `--json` | Print the JSON envelope instead of the text report |
| `--level` | Level to test (`AA`); selects axe tags and custom checks |
| `--viewport WxH` | Viewport in CSS px (`1280x800`) |
| `--pages N` | Crawl same-origin links; audit up to N pages (1) |
| `--screenshots DIR` | Save page, reflow (320 px) and failing-focus screenshots |
| `--check-timeout MS` | Time budget per check per page (default 120000); an overrun is a page error and the rest of that page is skipped |
| `--timeout MS` | Navigation timeout (30000) |
| `--max-tabs N` | Tab presses in the keyboard walk (60). Raise it for long pages |
| `--observe MS` | How long to watch carousels, tickers and marquees for 2.2.2 (6000; minimum 500) |
| `--rules LIST` | Comma list of check groups and/or SC ids, e.g. `focus,reflow` or `2.5.8,1.4.12` |
| `--no-axe` | Skip axe-core; run custom checks only |

Local files and directories are served by a built-in static server on 127.0.0.1. For a directory,
`index.html` is the start page; otherwise every `*.html` file is a seed.

**Check groups** and the SC they report on (`--help` lists the current set): `axe` (whatever axe maps; see
`meta.axe_sc_covered`), `contrast-sample` (1.4.3, 1.4.6), `non-text-contrast` (1.4.11), `target-size` (2.5.8),
`auto-update` (2.2.2), `status-messages` (4.1.3), `focus` (2.4.7, 2.4.11, 2.4.12, 2.1.2, 2.4.3, 1.4.11),
`dialogs` (2.1.2), `reflow` (1.4.10), `text-spacing` (1.4.12), `resize-text` (1.4.4), `consistent-help` (3.2.6),
`auth` (3.3.7, 3.3.8, 3.3.9).

**Rules** (rule slug [severity]):

| Group | Rules |
|---|---|
| axe | `axe:<rule-id>`: axe *violations* → [fail]; axe *incomplete* ("needs review") → [manual]. Incomplete colour-contrast nodes go to `contrast-sample` instead. When the custom `target-size` check runs, axe's `target-size` rule is disabled |
| contrast-sample | `contrast-sampled-background` [warn when below threshold, info when it passes]: measures text over images and gradients from screenshots (up to 30 nodes per page) |
| non-text-contrast | `ui-boundary-contrast` [fail], `ui-boundary-contrast-maybe` [warn], `ui-boundary-unresolved` [manual] (control boundaries on images or gradients) |
| target-size | `target-size-undersized` [warn] (below 24×24 and fails the 24 px circle spacing test); `target-size-exception` [info] (inline or other exception detected) |
| focus | `focus-not-visible` [fail] (focused and unfocused screenshots identical), `focus-indicator-faint` [warn], `focus-offscreen` [warn], `focus-obscured-fully` [fail, 2.4.11] and [warn, 2.4.12], `focus-obscured-partially` [warn, 2.4.12 AAA], `focus-indicator-contrast` [fail or warn, 1.4.11], `keyboard-trap` [fail], `modal-focus-containment` [warn], `focus-contained` [manual], `positive-tabindex` [warn], `focus-order-anomaly` [manual] |
| dialogs | `keyboard-trap-dialog` [fail] (a dialog that keeps focus with no way out), `dialog-focus-contained-documented` [manual] (containment with a documented exit) |
| auto-update | `auto-update-no-pause` [warn] (content changes repeatedly during `--observe` with no pause, stop or hide control) |
| status-messages | `status-message-not-announced` [warn] (a message appears after an action outside any live region) |
| reflow | `reflow-horizontal-scroll` [fail], `reflow-content-clipped` [warn], `reflow-exempt-content` [manual] (at 320×256 CSS px) |
| text-spacing | `text-spacing-clipped` [fail], `text-spacing-overlap` [warn] (with the 1.4.12 metrics applied) |
| resize-text | `resize-text-clipped` [warn], `resize-text-overlap` [warn] (text at 200%) |
| consistent-help | `help-order-inconsistent` [warn] (across crawled pages), `help-single-page` [manual] |
| auth | `password-paste-blocked` [fail], `otp-paste-blocked` [fail], `password-autocomplete-off` [warn], `captcha-cognitive-test` [manual, 3.3.8 and 3.3.9], `possible-redundant-entry` [manual, 3.3.7] |

**Envelope:** same `summary` and finding fields as the scanner, with `url` or `file` for the location,
`line`/`col` null, and a CSS `selector`. `meta` adds (`checks_sc` and `sc_covered` are limited to the tested
level and `--rules`):

```json
{"tool": "wcag_page", "version": "0.1.0", "wcag": "2.2 (2024-12-12)", "target": "...", "date": "...",
 "level": "AA", "viewport": "1280x800", "checks": ["axe", "contrast-sample", "..."],
 "engine": {"playwright": "1.63.0", "axe": "4.13.0", "chromium": "...", "axe_runtime": "4.13.0"},
 "axe_sc_covered": ["1.1.1", "1.3.1", "..."],
 "checks_sc": {"axe": ["1.1.1", "..."], "focus": ["1.4.11", "2.1.2", "2.4.3", "2.4.7", "2.4.11"], "...": []},
 "sc_covered": ["1.1.1", "1.2.2", "..."],
 "pages": [{"file|url": "...", "title": "...", "runtime_ms": 1900,
            "keyboard_walk": {"presses": 4, "focused": 3, "tabbable_on_page": 3,
                              "stop": "wrapped|wrapped-in-document|max-tabs|navigated|no-focusable|trap",
                              "focus_visible_checked": 3},
            "errors": [{"check": "navigation|axe|focus|...", "error": "..."}]}]}
```

`evidence` on a finding carries measurements: target `width`/`height` and the `conflict` target; axe `impact`,
`related_sc`, `nodes_total`; reflow `client_width`/`scroll_width`; focus sample points and covering element;
screenshot paths. A keyboard walk that stopped at `max-tabs` did not reach every element: raise `--max-tabs` or
record the rest as not evaluated. A `navigated` stop means a focused element changed the URL (check 3.2.1).

Exit codes: 0 no `fail`, 1 `fail` findings, 2 usage error or no page could load.

## 4. `setup_page_runner.sh`

```
bash $S/setup_page_runner.sh            # install (idempotent)
bash $S/setup_page_runner.sh --check    # verify: exit 0 ok, 1 missing or version mismatch
```

Installs pinned `playwright@1.63.0` and `axe-core@4.13.0` with `npm --prefix .cache/node`, then the Chromium
headless shell with `playwright install --only-shell chromium`. `--check` launches Chromium to prove it works
and prints the node, playwright, axe-core and Chromium versions and the cache size. Needs Node 18+ and npm, and
network access on first run.

**`.cache/` layout** (gitignored; about 220 MB):

| Path | Contents | Size |
|---|---|---|
| `.cache/node/` | `package.json`, `node_modules/playwright`, `node_modules/axe-core` | ~21 MB |
| `.cache/ms-playwright/` | `chromium_headless_shell-<rev>/`, `ffmpeg-<rev>/` | ~200 MB |

Environment: `WCAG22_CACHE_DIR` moves the cache (both the installer and the runner honour it);
`PLAYWRIGHT_BROWSERS_PATH` is set to `<cache>/ms-playwright` when unset.

**Re-validation.** `python3 tools/revalidate.py` (maintainers) compares the pinned Playwright, axe-core and
Chromium versions, the installed axe rules and `tools/catalogue/axe_map.json` with `SOURCES.lock`, and reports
newer npm releases as "update available". It never installs anything. See `tools/README-maintenance.md`.

## 5. Runtime notes

- The page runner takes a few seconds per simple page: a keyboard walk, two text-integrity passes, a reflow
  pass, and the `--observe` window (6 s by default) when the page has moving content. Heavy pages with many
  focusable elements take longer. `--pages 20` on a real site can take
  minutes. The orchestrator allows each tool up to 30 minutes.
- Each check has a time budget (`--check-timeout`, default 120 s). A check that overruns is reported as a
  page error by name, and the rest of that page is skipped. `meta.pages[].check_ms` shows where time went.
- macOS: keep the display awake during long runs (`caffeinate -d`, or a keep-awake app set to prevent
  display sleep). Keeping only the system awake is not enough. With the display asleep, headless Chromium
  logs `CVDisplayLinkCreateWithCGDisplay failed`, frame-driven checks stall, and background processes are
  throttled. Symptoms: pages that normally take 20 s take minutes, and checks time out.
- The scanner reads files as UTF-8 with replacement; binary or huge generated files belong in skipped folders.
- Tests: `python3 scripts/test_wcag_scan.py`, `python3 scripts/test_wcag_audit.py`,
  `node --test scripts/test_wcag_page.mjs` (browser tests skip when the runner is not installed).

## 6. Known limits

- **Coverage is partial.** On the 55 AA SC, the scanner has rules for 29 and the page runner covers about 30
  (`meta.sc_covered`); together 34. "Covered" means the tool looks at part of the SC. The remaining SC (media, meaningful sequence, sensory
  characteristics, hover/focus content, shortcuts, pointer gestures and cancellation, multiple ways, consistent
  navigation and identification, error handling, and more) have no automated signal.
- **The static scanner sees source, not the page.** It cannot resolve the CSS cascade across files, runtime
  state, framework output, props passed from elsewhere, or ids rendered by another component
  (`aria-idref-missing`). Contrast is computed only from colour pairs it can resolve in one rule or element.
- **The page runner sees one viewport and mostly the load state.** Apart from its own probes (the keyboard
  walk, dialog focus, a watch window for moving content, simulated paste), it does not log in, open menus,
  submit forms, play media, or trigger error states. It tests reflow only at 320×256 and uses the
  default desktop viewport for everything else. Pages behind authentication must be served locally or checked
  by hand.
- **axe-core** reports only what its rules detect; "incomplete" results are review items, not failures.
  Experimental and deprecated axe rules are not counted as coverage.
- **No tool** judges alt-text quality, heading and label wording, reading order meaning, caption accuracy,
  screen reader announcements in real AT, or whether an exception applies. Those are manual
  (`references/manual-checks.md`).
