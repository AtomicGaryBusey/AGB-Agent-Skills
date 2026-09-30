# Evals for `wcag22-a11y`

Keep runs local: the runner always passes `--no-publish`. Results are scrubbed of machine paths before they are written under `results/`.

## Layout

| Path | What it is |
|---|---|
| `fixtures/larkspur/ (project/ + answer-key.md)` | Seeded Larkspur Library site (5 HTML pages, CSS, JS, React sources) and its answer key: 30 defects D01-D30 (SC, level, detectability static/rendered/manual), 6 decoys K1-K6, 3 non-scored notes N1-N3. |
| `fixtures/brightwater/ (project/ + answer-key.md + VALIDATION.md)` | Brightwater Transit site (11 HTML pages, `css/site.css`, `js/`, `img/`, unbuilt Vue SFCs in `components/`, an empty `fonts/`) and its answer key: 26 defects H01-H26 (H26 was found in blind validation, not seeded) and 6 decoys HK1-HK6. It was a held-out set (built 2026-09-28), used once for blind validation on 2026-09-29 (`VALIDATION.md`), and is now a regular fixture: **scores on it are no longer blind.** Git does not track the empty `fonts/`, so a clone has no `fonts/` directory; the icon font is missing either way. |
| `graders/keyspec.json` | Shared settings: skill and plugin names, `tolerance` (default ±lines), severity vocabulary, the base `no_peek` pattern, the list of fixture specs (`fixtures`) and the refusal prompts. |
| `graders/specs/<fixture>.json` | One machine-readable answer key per fixture: `fixture` (the project dir that is scaffolded), `answer_key`, `case_glob`, case prompts and in-scope decoys, seeded locations (file:line, ± `tolerance`, per-defect `tol` override, `anchors`), SC ids, disambiguating keywords, accepted severities, decoy definitions, optional `no_peek_extra`. Defect and decoy IDs must be unique across fixtures. **Edit these and keyspec.json, not the generated files.** |
| `graders/spec.py` | Loads keyspec.json and the fixture specs into one merged view (checks for duplicate case names and IDs). Used by the three scripts below. |
| `graders/gen_suite.py` | Generates `plugin/` from the specs. |
| `graders/selftest.py` | Checks the generated regex graders against synthetic rows in the SKILL.md findings-table shape, per fixture (each matches only its own defect/decoy; rows from the same fixture are the cross-talk set), plus severity strictness, prose, no-peek for both fixtures, and regression rows from real replies (list/continuation/range locations, decoy lines cited only in Evidence or Fix, manual-check bullets, wide ranges). Run after editing a spec; adding a fixture means adding its rows here. |
| `graders/summarize.py` | Turns a raw `aggregate-result.json` into `results/<date>/plugin-eval/` (scrubbed), with overall recall by detectability for each fixture whose cases ran (marked partial if only some ran). |
| `plugin/` | Generated eval-only wrapper plugin (`.claude-plugin/plugin.json`, `experimental.evals: cases`). `plugin/skills/wcag22-a11y/` symlinks the skill's SKILL.md, `references/`, `scripts/`, NOTICE, but **not** `evals/` or `tools/`, so the answer key is not inside the skill's base directory. SKILL.md is linked even before it exists (dangling link, with a warning). |
| `plugin/cases/<case>/` | `case.yaml`, `scaffold.sh` (copies only the case's own fixture `project/`, never an answer key or another fixture, into the run workspace), `graders/*.md` (hidden from the agent). |
| `run_plugin_eval.sh` | Regenerates the suite, runs it, writes `results/<date>/plugin-eval/`. `FIXTURE=larkspur\|brightwater` limits the run to one fixture's cases. Exits 3 without running if SKILL.md does not exist yet. |
| `triggers/trigger-eval.json` | 10 should-trigger + 10 should-not-trigger prompts, in the run_eval.py / run_loop.py format. |
| `triggers/run_trigger_eval.py` | Runs skill-creator's `run_eval` with a detector that also counts the installed copy of the skill (see its docstring). Needs SKILL.md. |
| `results/<date>/` | Recorded results. |

## Cases

| Case | Fixture | Scored IDs | Decoys / notes in scope |
|---|---|---|---|
| `wcag-perceivable` | larkspur | D01-D10 (1.x) | K1, K2, K5, N1, N3 |
| `wcag-operable` | larkspur | D11-D21 (2.x) | K3, K6 |
| `wcag-understandable-robust` | larkspur | D22-D30 (3.x, 4.x) | K4, N2 |
| `wcag-decoys` | larkspur | none; the user queries all nine decoys/notes | K1-K6, N1-N3 (`decoy-verdicts`: every one must be judged compliant) |
| `bw-perceivable` | brightwater | H01-H08, H26 (1.x) | HK1, HK2, HK6 |
| `bw-operable` | brightwater | H09-H16 (2.x) | HK3, HK4, HK5 |
| `bw-understandable-robust` | brightwater | H17-H25 (3.x, 4.x) | none (no Brightwater decoy is a 3.x/4.x item, so this case has no `nodecoy-*` or `nodecoy-judge` grader) |
| `bw-decoys` | brightwater | none; the user queries all six decoys | HK1-HK6 (`decoy-verdicts`: every one must be judged compliant) |
| `wcag-refusal-sql-perf` | - | Postgres query tuning; skill must not load | - |
| `wcag-refusal-caption-poem` | - | poetic photo captions for a blog; skill must not load | - |

The Brightwater prompts describe the site as neutrally as the Larkspur ones (pages, `css/site.css`, `js/`, `img/`, unbuilt Vue components) and give no hints about the defects. Brightwater scores are not blind (see the fixture's `VALIDATION.md`), so do not report them as held-out results.

## Graders per audit case

- `recall-<ID>` (regex): a findings-table row (`^|...`) that cites one of the seeded locations (file:line within ±1 of the key, or an anchor such as `help-bar` for page-level defects) **and** a disambiguating keyword or the SC number. A cited location may be a single line, a comma list (`catalog.html:2,8`), bare continuations after a file-qualified item (`` `SavedTrips.vue:5`, `:7-15`, `:31-40` ``), or a range (`styles.css:19-28`); a range counts if it overlaps a seeded line ± tolerance. Recall looks anywhere in the row. Keywords separate defects that share a file region. Larkspur: `events.html:36/37/39` = D03 heading / D06 contrast / D09 text spacing; `signup.html:34` = D04 autocomplete / D07 placeholder; `catalog.html:28/29` = D26 input / D27 icon button, tolerance 0. Brightwater: `fares.html:62-64` and `site.css:121/122` = H02 table headers / H04 red-only peak fares, and `fares.html:43` = HK1 reflow (H04's `1.4.1` keyword cannot match `1.4.10`); `alerts.html` and `js/alerts.js` = H16 targets / H23 switch state / H25 status / H06 reflow / H10 modal trap; `site.css:132-136` = H16 / H06; `claim-1.html:40/44` = H03 autocomplete / H21 redundant entry; `feedback.html:39-40, 52-53` = H05 label contrast / H20 error display; `site.css:187/189` = H20 / H14. H26 (footer focus ring) is keyed on `site.css:10-11, 31, 57-58` or a footer anchor (`site-footer`, `footer-links`) with `1.4.11`, `non-text contrast`, `1.97` or `#12324f`, and deliberately not on `footer`, `outline` or `focus`, so the H14 dock-footer and H13 `outline:none` rows do not count for it.
- `severity-<ID>` (regex): the same row also carries an accepted severity:
  - static objective failures: `Nonconformity`;
  - static-but-heuristic (D16 / H12 positive tabindex, D18 / H13 `outline:none`) and every `rendered` defect (inferred statically in a no-shell run): `Nonconformity` or `Deviation`;
  - `manual` defects: `Nonconformity`, `Deviation` or `Review note`.
- `nodecoy-<K|N>` (regex, not_contains): no findings-table row (the SKILL.md shape `| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |`) has `Nonconformity` or `Deviation` in its Severity cell, cites the decoy/note location in its **Location** cell (6th), and carries the decoy's keyword in its Check ID, Ref or Finding cell. Mentions in Target, Evidence or Fix, bullets, prose and other tables do not count. For decoys, a single line must be within ± tolerance, and a range must lie inside the hull of the decoy's seeded lines on that file ± tolerance. A wide range that only overlaps a decoy line (`styles.css:19-28` against K6's `:25-26`) does not count. Anchors (such as `pad-for-header`) also count only in the Location cell.
- `nodecoy-judge` (llm, `JUDGE`, default sonnet): none of the case's decoys/notes is reported as a Level A/AA failure. Omitted when a case has no decoys in scope (`bw-understandable-robust`). `decoy-verdicts` (decoys cases only): every queried item gets an explicit "compliant" verdict.
- `skill-used` (tool_used Skill, input matches `wcag22-a11y`). Refusal cases use `skill-not-used` (max 0).
- `no-peek` (regex over the trace): the agent never touched `answer-key.md`, `keyspec.json`, a `graders/` path (this includes `graders/specs/`) or `evals/fixtures` (so neither fixture, nor Brightwater's `VALIDATION.md`). Brightwater cases also fail on `fixtures/brightwater`, `holdout-key.md` or `wcag22-holdout` (the fixture's pre-repo name), from `no_peek_extra`.

The severity words live in `keyspec.json` (`severity_words`, `finding_severities`). If SKILL.md ends up using a different vocabulary, change them there and regenerate.

## How to run

```bash
# regenerate + structural check (works before SKILL.md exists)
python3 evals/graders/gen_suite.py && claude plugin validate evals/plugin
# grader self-test (synthetic rows; cross-talk, severity strictness, no-peek)
python3 evals/graders/selftest.py
# plugin eval, all 10 cases (1 run per case, single arm, local report only)
RUNS=1 MAX_COST=15 ./evals/run_plugin_eval.sh
# one fixture only (larkspur's glob 'wcag-*' also runs the two refusal cases)
FIXTURE=larkspur ./evals/run_plugin_eval.sh
FIXTURE=brightwater ./evals/run_plugin_eval.sh
# 3-run version with the no-skill baseline arm (about 6x the cost)
RUNS=3 ABLATION=with-without MAX_COST=<cap> ./evals/run_plugin_eval.sh
# one case, or let the skill run its scanner (see Known limits)
CASE='*decoys*' ./evals/run_plugin_eval.sh
EVAL_BASH=1 CASE='wcag-operable' LABEL=with-bash ./evals/run_plugin_eval.sh
# trigger eval (run_eval, not the optimisation loop)
python3 evals/triggers/run_trigger_eval.py --runs-per-query 1 --out evals/results/$(date +%F)/triggers.json
```

### Cost

Running every case costs more now that there are two fixtures. The Larkspur-only suite (4 audit cases and 2 refusal cases, 1 run, single arm) cost about **$2.47** on 2026-09-28: $0.51-0.66 per audit case and under $0.10 per refusal case. The Brightwater source is about twice the size of Larkspur's (11 pages, about 62 KB against 32 KB), so expect roughly $0.8-1.3 per Brightwater audit case. That makes about **$3-5 for `FIXTURE=brightwater`** and about **$6-7.5 for the full suite** (`RUNS=1`, `ABLATION=none`). These are estimates; check `summary.md` after the first full run. `RUNS=3 ABLATION=with-without` is about 6x that, roughly $35-45, so raise `MAX_COST` above the default 15 for it. The default `MAX_COST=15` stops a single full run well before a runaway, but leaves little headroom if cases take many more turns than usual.

## Known limits

- **`nodecoy-judge` is informational (weight 0.001; the eval rejects 0).** In the 2026-09-29 runs the eval's Sonnet judge voted FAIL 3/3 on audit reports that the same rubric passes 6/6 under `claude -p --model sonnet` (the reports name each decoy only as compliant, an Advisory or an AAA note). A verdict-first rewrite of the rubric did not change it, and how `claude plugin eval` reads llm verdicts is not documented. Decoys are scored by the `nodecoy-<ID>` regex graders and `decoy-verdicts`; read the replies for any judge FAIL before trusting it.
- **No Bash by default.** On this machine `claude plugin eval` has refused Bash-granting cases (Docker credential-store symlink; see the iso999/ste100 harnesses). Cases therefore grant Read/Glob/Grep/Skill only, and the prompts say no shell is available, so `scripts/wcag_scan.py` and the Playwright page runner are not exercised: rendered defects (D06-D10, D19, D21) must be inferred from CSS. `EVAL_BASH=1` adds Bash to the audit cases and `--allow-tools Bash` to the run; try it once the sandbox issue is fixed.
- Recall is graded on the final reply's table rows. A finding given only in prose, or cited outside ±1 line of the key, counts as a miss. Check `results/<date>/plugin-eval/replies/` before trusting a miss.
- One row that cites several IDs' locations (for example D01 and D11 in one `catalog.html` row) can satisfy both recall graders if it carries both keywords; the judge and the reply are authoritative.
- The regex no-decoy graders are heuristics: they fire on any Nonconformity/Deviation findings row whose Location cell cites the decoy location and whose Check ID/Ref/Finding carries its keyword. They depend on the SKILL.md table layout; if the column order changes, update `finding_row_pattern` in `gen_suite.py`. K3's keyword covers only target size (`2.5.8`, `target size`, `24px`, `16px`, `too small`), so a finding about where the same "access guide" link points (2.4.4) does not trip it. K6 is keyed only on `index.html:2/9` and `styles.css:5` (not the shared sticky rule at `styles.css:25-26`, which is D19). HK1 (`fares.html:43`) sits next to H04's legend line 42; a row about the red legend does not trip HK1 unless it also talks about scrolling or reflow. Treat `nodecoy-judge` plus the reply as authoritative.
- Brightwater has no rendered-only verification here: the key's "Verified" notes come from the one headless-Chrome run in 2026-09. In a no-shell run, the five `rendered` defects (H05, H06, H07, H16, H26) must be inferred from CSS, as for Larkspur.
- The answer key's location lines are the fixture's actual lines. Two CSS lines in the original held-out key were one line off (H02 is `site.css:121`, H04 is `site.css:122`) and are corrected here, and H05's first affected label is `feedback.html:35` (the original key cited the input on line 34; the grader accepts both). The ±1 tolerance covered all three anyway.
- The answer key cites WCAG 2.2 text under the W3C document license; keep its quotes short in any results you share.
