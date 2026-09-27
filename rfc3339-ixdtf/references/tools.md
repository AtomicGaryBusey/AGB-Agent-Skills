# Tools: `rfcdt.py` and `run_vectors.py`

Full reference for the two scripts. SKILL.md has the short form. The module docstrings
(`scripts/rfcdt.py`, `scripts/run_vectors.py`) are the source of truth; `--help` lists every flag.
Both use the Python 3 standard library only (`zoneinfo` when tz data is present).

## `scripts/rfcdt.py` (rfcdt 1.1.0)

### `check`: validate one string

```bash
python3 scripts/rfcdt.py check [--profile rfc3339|ixdtf] [--allow-space-separator] \
    [--leap-seconds iers-months|table|any-month-end|grammar] [--tzdata auto|off] \
    [--experimental-key KEY ...] [--production date-time|full-date|full-time|partial-time] \
    [--lmt-tolerance nearest|any-sub-minute] [--json] [--] STRING
```

- Put `--` before a string that starts with `-`.
- `--leap-seconds`: `iers-months` (default) accepts `23:59:60` UTC only at the end of Mar/Jun/Sep/Dec from 1972;
  `table` only known insertions through 2016-12-31; `any-month-end` the §5.7 positional rule only; `grammar` the
  ABNF only. All but `grammar` apply the §5.7 offset shift.
- `--lmt-tolerance`: how a sub-minute zone offset (LMT, e.g. Paris `+00:09:21`) is matched against the written
  `hh:mm`. `nearest` (default) accepts only the offset rounded to the nearest minute (both neighbours on an exact
  `:30` tie, e.g. Monrovia `-00:44:30`); `any-sub-minute` accepts any `hh:mm` less than 60 s away.
- `--production`: validate a partial production (erratum 5624, held); default `date-time`.
- `--experimental-key`: treat this `_key` as a configured experiment (RFC 9557 §3.2); repeatable.
- `--json`: `{ok, input, profile, errors, warnings, fields, options, meta}`. `errors`/`warnings` are reason codes
  `R<rfc>-<section>/<slug>`; `fields` are the parsed fields (the names the vector runner compares); `meta` gives
  the rfcdt version, Python, tz source and release, host TZ and the UTC date.

### `adapter`: rfcdt as a vector-runner target

`python3 scripts/rfcdt.py adapter [same options as check]` reads one string on stdin and prints the adapter
JSON (`ok` plus `fields`). It is the reference adapter for the per-process protocol.

### `scan`: static scan for risky date-time APIs

```bash
python3 scripts/rfcdt.py scan PATH [PATH ...] [--json] [--include-dist] [--max-bytes N]
```

- 86 patterns: Python, JS/TS (incl. `.vue`, `.svelte`), Java/Kotlin, .NET, Go, Rust, Ruby (incl. `.erb`), PHP,
  Elixir, Dart, Swift, SQL, `.proto`, Apex, ServiceNow Glide/Flow/Fluent, JSON/YAML schemas, plus
  language-neutral patterns for every text file. Statements split over lines are joined before matching and
  reported at their first line.
- Walking prunes `dist`, `node_modules`, `build`, `vendor`, `target`, venv and VCS directories;
  `--include-dist` keeps `dist` (built SDK code). Explicit path arguments are always scanned.
- `--max-bytes N`: skip (and count) files larger than N bytes; default 2000000; `0` = no limit.
- Files that are not available locally (for example evicted to iCloud) are skipped and counted.
- Suppress one line with `# rfcdt: ignore` (any comment syntax).
- `--json` prints `{"meta", "summary", "findings"}`:
  - `meta`: tool, version, Python, platform, tz source/version, host TZ, date.
  - `summary` is the **denominator**: `files_seen`, `files_scanned`, `files_skipped`, `skipped` by reason
    (too-large, binary, extension, unreadable, not available locally, timeouts), `excluded_dirs`,
    `scanned_by_ext`, `skipped_by_ext`, `generic_only_by_ext` (extensions only the language-neutral patterns
    cover), `skipped_files`, `max_bytes`.
  - `findings`: `{file, line, id, check, severity, message, fix, text}`; `check` is the reason code / check it
    points at.
  The text output ends with the same summary. **Never call a file clean when the summary says it was not
  scanned**, and report the skip counts under "Not run / not applicable".

### `selfcheck`: are the embedded tables current?

`python3 scripts/rfcdt.py selfcheck [--json] [--leap-file PATH] [--zoneinfo DIR ...] [--node BIN]
[--calendars a,b,...] [--today YYYY-MM-DD] [--tz-max-age-years N]` compares the embedded leap-second table with
the host's `leapseconds` file (and its expiry date), the known calendars with ICU (via `node`), and warns when the
tz release is old. Run it once per audit and put the result in Reproduction.

## `scripts/run_vectors.py` (runner 0.3.0)

```bash
python3 scripts/run_vectors.py [--target "<adapter cmd>"] [--mode stdin|argv] [--batch] [--jobs N] \
    [--profile rfc3339|ixdtf] [--target-kind rfc3339|ixdtf|both] [--target-options configurable|fixed] \
    [--target-has-tzdata yes|no|auto] [--tz-matrix TZ1,TZ2,...] [--timeout S] [--vectors PATH] \
    [--report text|json|md] [--json]
```

Without `--target` it runs the built-in rfcdt engine (a self-test).

**Vectors.** `vectors/vectors.json`: 310 vectors (108 valid, 167 invalid, 35 `either`; 182 in the `rfc3339`
profile, 128 in `ixdtf`; 32 with non-default options, 36 that need tz data). Each vector has `id`, `input`,
`profile`, `expect`, `reason`, `section`, `checks` (check IDs from `references/check-index.md`), and optionally
`options`, `requires`, `fields`, `interpretation`, `resolvable`, `rfcdt_default`. The vectors cover 74 of the 109
check IDs, and every objective consumer or grammar check has at least one vector (enforced by
`scripts/test_vectors.py`; the checks no single string can exercise are listed there with a reason).

**Adapter protocol** (details and Python/Node examples in the `run_vectors.py` docstring):
- Per-process (default): the string on stdin with no trailing newline (`--mode argv`: last argument after `--`);
  environment `RFCDT_PROFILE`, `RFCDT_OPTIONS` (JSON), `RFCDT_VECTOR_ID`. Print one JSON object:
  `{"ok": true|false}`, `{"skip": true}`, or `{"ok": true, "resolved": true}` (critical inconsistency resolved
  by programmed behaviour). `--jobs N` runs N processes in parallel.
- `--batch`: the adapter is started once with `RFCDT_BATCH=1`, reads JSON lines
  `{"id", "input", "profile", "options"}` and writes one result line per input, in order, echoing `id`. An adapter
  that prints `{"batch": false}` falls back to per-process mode. Use it for JVM, .NET and Node targets.
- **fields**: return what the target made of the string (`year` … `second`, `secfrac`, `offset`,
  `offset_minutes`, `offset_unknown`, `separator`, `leap_second`, `time_zone`, `tags`, `effective_tags`). Only
  the keys you return are compared.

**Scoping.** `--target-kind ixdtf` skips rfc3339 vectors that are invalid only because of a suffix;
`--target-kind rfc3339` skips the ixdtf profile. `--target-options fixed` (alias `--default-options-only`) skips
non-default-option vectors, so one fixed policy is not counted once per option. `--target-has-tzdata no` (alias
`--no-tzdata`) skips vectors marked `requires: tzdata`. `--profile P` drops the other profile entirely.

**Result buckets.**
- **TOO LENIENT**: invalid input accepted. **TOO STRICT**: valid input rejected.
- **WRONG VALUE**: accepted, but a returned field differs from the vector's `fields` (a failure on `either`
  vectors too: e.g. last-wins duplicate tags, two-digit years remapped).
- **HOST-TZ DEPENDENT** (`--tz-matrix` only): the run is repeated with `TZ` set to each zone (for example
  `UTC,America/St_Johns,Asia/Kathmandu`); a verdict or field that changes is a failure. Use it for any target
  that might fall back to host-local time.
- **ADAPTER ERROR**: no usable answer (non-JSON, missing `ok`, timeout, lost batch line).
- **INTERPRETATION** (never a failure): `either` vectors and `resolved` answers on `resolvable` vectors. The
  report lists the target's choice for each; report them as Review notes.
- Built-in engine only: REASON MISMATCH.

**Reports.** `--report text` (default); `--report json` / `--json`: `{meta, target, totals, sections, results}`,
where `meta` holds the runner version, vectors sha256, Python, platform, host TZ, tzdata version, tz-matrix,
date, target command, mode, batch, jobs and elapsed time; `--report md`: a Markdown findings-table skeleton
(severity guess, check IDs, section, vector, input → output, expected) grouped by root cause, then the
interpretation-choice table. Its columns map onto the report's findings table (Section → Ref, vector input → output → Evidence); add Target and Location, and confirm each severity guess with `interpretation.md` rule 1. Exit status 0 when there are no failures or adapter errors, else 1.

## Tests

`python3 -m unittest discover -s scripts` runs the unit tests for both scripts and the vector set.
