# Maintenance: re-validation, SOURCES.lock, plugin packaging

Covers T4-11 (monthly re-validation), T4-12 (`SOURCES.lock`) and T4-13 (plugin manifest).
The same `tools/revalidate.py` ships in the iso999 repo; it picks its profile from the `name:` in `SKILL.md`.

## `tools/revalidate.py`

Standard library only. Run it from anywhere:

```sh
python3 tools/revalidate.py                  # --check (default): compare live state with SOURCES.lock
python3 tools/revalidate.py --update         # rewrite SOURCES.lock (refused unless every test is green)
python3 tools/revalidate.py --offline        # skip the network sources (errata, IANA, upstream releases)
python3 tools/revalidate.py --lock PATH      # use another lock (for example a copy you are testing)
python3 tools/revalidate.py --report PATH    # also write the Markdown report to PATH
```

| Exit | Meaning |
|---|---|
| 0 | No change against the lock |
| 1 | Drift: the report lists every changed key, with a plain-language summary first |
| 2 | Error: a source could not be read or parsed, the lock is missing or unreadable, or `--update` was refused |

What one run does (about 70 s; most of it is the unit suite):

| Area | Source | Lock section |
|---|---|---|
| Errata | `https://www.rfc-editor.org/errata/rfc3339` and `/rfc9557`: ID, status, type, date reported. Also checks that the errata list in `SKILL.md` `metadata.sources` matches the live list | `sources.errata`, `sources.skill_md_errata_list_matches_live` |
| IANA registry | `internet-date-time-format.xml`: created/updated dates, every key with status, date and description | `sources.iana_internet_date_time_format` |
| tzdata, leap seconds, ICU calendars | `scripts/rfcdt.py selfcheck --json` | `local.tzdata`, `local.leap_seconds_file_expires`, `tests.selfcheck` |
| Local toolchains | `python`, `node` (and native `Temporal`), `java`, `dotnet`, `ruby`, `go`, `rustc`, `swift`, where present | `local.tools` |
| Upstream releases | tzdb version and `leap-seconds.list` expiry (data.iana.org), Go (go.dev), Node (nodejs.org), .NET (release index), crates.io (chrono, time, jiff), PyPI (pydantic, python-dateutil, jsonschema), npm (ajv, ajv-formats) | `upstream` |
| Probed versions | The "Versions probed" column of the file map in `references/ecosystem/README.md` | `ecosystem_probed` |
| Artifacts | `vectors/vectors.json` sha256, `rfcdt` and runner versions | `artifacts` |
| Tests | unit suite (`scripts/test_*.py`), `run_vectors.py` built-in engine, `tools/gen_vectors.py --check` | `tests` |

The report also has an **Ecosystem freshness** table: for each ecosystem file it shows the probed version, the
local version and the latest upstream release. A row that is not `current` means that file may be stale: re-probe
(`probes/`) before relying on it, update the file, then run `--update`. This table is advice, not drift: drift is
only a change against the lock.

### Updating the lock

After you have reviewed a drift report and updated the skill (for example, added a new erratum to `SKILL.md` and
the catalogs), run `python3 tools/revalidate.py --update` and commit `SOURCES.lock` together with the change.
`--update --offline` keeps the previous lock's network sections. `meta.snapshots` records the date of each
section; `meta` is not compared.

The first lock was written on 2026-09-26. The skill's own baseline snapshot (in `SKILL.md`) is 2026-09-24; the
live errata IDs matched the list in `SKILL.md` on 2026-09-26, and the IANA registry held one key (`u-ca`,
Permanent, last updated 2024-05-22).

## Monthly run: local launchd job (not installed)

`tools/launchd/com.local.skill-revalidate.plist.template` runs `revalidate.py --check` for **both** skills on the
1st of each month at 09:00 (if the Mac is asleep then, launchd runs the job at the next wake; if it is off, that month is skipped). It writes
`~/Library/Logs/skill-revalidate/<skill>-<YYYY-MM-DD>.md` plus `runs.log`, and posts a macOS notification through
`osascript` only when a skill reports drift (exit 1) or an error (exit 2). A clean month is silent.

The job is **not** installed or loaded. That is the owner's decision. To install it:

```sh
PY=python3                   # any Python 3.9+ interpreter
dst="$HOME/Library/LaunchAgents/com.local.skill-revalidate.plist"
mkdir -p "$HOME/Library/Logs/skill-revalidate"
sed -e "s|__HOME__|$HOME|g" -e "s|__PYTHON__|$PY|g" -e "s|__PATH__|$PATH|g" \
  "$HOME/.claude/skills/rfc3339-ixdtf/tools/launchd/com.local.skill-revalidate.plist.template" > "$dst"
plutil -lint "$dst"
launchctl bootstrap "gui/$(id -u)" "$dst"
launchctl print "gui/$(id -u)/com.local.skill-revalidate" | head -20    # confirm it is loaded
launchctl kickstart -p "gui/$(id -u)/com.local.skill-revalidate"       # optional: run it once now
```

To uninstall:

```sh
launchctl bootout "gui/$(id -u)/com.local.skill-revalidate"
rm "$HOME/Library/LaunchAgents/com.local.skill-revalidate.plist"
# optional: rm -r "$HOME/Library/Logs/skill-revalidate"
```

Notes:
- Replace `__PATH__` in the template with a `PATH` that contains every toolchain you probe (python3, node,
  java, dotnet, ruby, go, rustc, swift); for example, copy the value of `echo $PATH` from your shell. A toolchain
  that launchd cannot find is recorded as `absent` and shows as drift.
- The first time `osascript` posts a notification, macOS may ask to allow notifications from Script Editor.
- The job does not commit or update any lock. You review the report and run `--update` yourself.

## Alternative: `/schedule` (cloud routine)

A Claude Code cloud routine (`/schedule`) could run the same check monthly in Anthropic's cloud against a pushed
copy of the repo, and open a PR or a report when something changes. It is fine for **rfc3339-ixdtf** only: the
content is public (RFC text under BCP 78, public registries) and every source is a public URL. Its limits here:
the cloud sandbox does not have this Mac's toolchains, tzdata or Temporal-enabled Node, so the `local` section
would always drift, and the repo would have to be pushed to a remote the routine can read.

It is **not suitable for iso999**. That skill paraphrases a single-user licensed ISO standard: its repo must not
leave this machine (the `pre-push` licence guard refuses pushes), and a cloud routine would need the repo in the
cloud. Keep iso999 on the local launchd job, which never touches the network for iso999 and never opens the ISO PDF.

## Plugin packaging (T4-13)

`.claude-plugin/plugin.json` at the repo root turns this skill into a plugin. `"skills": ["./"]` loads the root
`SKILL.md` as the plugin's only skill; no files move.

Checks (read-only; nothing was published or installed):

```sh
claude plugin validate ~/.claude/skills/rfc3339-ixdtf                                   # ✔ Validation passed
claude --plugin-dir ~/.claude/skills/rfc3339-ixdtf plugin details rfc3339-ixdtf
```

`claude plugin details` output on 2026-09-26 (SKILL.md 1.0.0, commit 674bdd3 plus the new files):

```
rfc3339-ixdtf 1.0.0
Component inventory
  Skills (1)  rfc3339-ixdtf
  Agents (0)  Hooks (0)  MCP servers (0)  LSP servers (0)
Projected token cost
  Always-on:   ~428 tok   added to every session
Per-component (rounded)
  component      always-on  on-invoke
  rfc3339-ixdtf       ~430      ~3.5k
```

So the plugin costs about 430 tokens in every session (the skill's name and description) and about 3.5k tokens
each time the skill fires (`SKILL.md`). Reference files, scripts and vectors load only when the skill reads them.

Owner decisions before sharing:
- **Code licence.** MIT (`license` in `plugin.json`; `LICENSE` at the repository root). Quoted RFC 3339 /
  RFC 9557 text (ABNF, short normative sentences) stays under the IETF Trust Legal Provisions (BCP 78); see
  `NOTICE` at the repository root.
- **What ships.** The plugin root is the whole repo, so `evals/` (answer keys, fixtures, results), `probes/` and
  `tools/` ship too. Either accept that, or publish from a clean export (for example `git archive` without
  `evals/`), or move the skill under `skills/rfc3339-ixdtf/` in a release branch.
- **Evals.** Run the plugin evals with `evals/run_plugin_eval.sh`, which loads the skill through
  `evals/plugin/` without `evals/`. Do not run `claude plugin eval` against the repo root: the skill would then
  be able to read the answer keys under `evals/`.
- **Version.** `plugin.json` says `1.0.0`, the same as `SKILL.md` `metadata.version`. Bump both together.
