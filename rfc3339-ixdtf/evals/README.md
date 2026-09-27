# Evals for `rfc3339-ixdtf`

## Layout

| Path | What it is |
|---|---|
| `fixtures/tempo/ (project/ + answer-key.md)` | Seeded test project and its answer key (ground truth, with an Expected severity column). |
| `graders/keyspec.json` | Machine-readable answer key: case prompts, seeded defect locations, disambiguating keywords, accepted severities, decoys, refusal prompts. **Edit this, not the generated files.** |
| `graders/gen_suite.py` | Generates `plugin/` from `keyspec.json`. |
| `graders/summarize.py` | Turns a raw `aggregate-result.json` into `results/<date>/plugin-eval/` (scrubbed of machine paths). |
| `plugin/` | Generated eval-only wrapper plugin (`.claude-plugin/plugin.json`, `experimental.evals: cases`). `plugin/skills/rfc3339-ixdtf/` symlinks the skill's SKILL.md and folders but **not** `evals/`, so the answer key is not inside the skill's base directory. |
| `plugin/cases/<case>/` | `case.yaml`, `scaffold.sh` (copies the fixture project, without the answer key, into the run workspace), `graders/*.md` (hidden from the agent). |
| `run_plugin_eval.sh` | Runs the suite and writes `results/<date>/plugin-eval/`. |
| `triggers/trigger-eval.json` | 10 should-trigger + 10 should-not-trigger prompts (TODO appendix), in the run_eval.py / run_loop.py format. |
| `triggers/run_trigger_eval.py` | Runs skill-creator's `run_eval` with a detector that also counts the installed copy of the skill (see its docstring). |
| `results/<date>/` | Recorded results. |

Cases: rfc-producer, rfc-consumer, rfc-schema, rfc-decoys, rfc-refusal-duration, rfc-refusal-httpdate.

## Graders per audit case

- `recall-<ID>` (regex): a findings-table row (`^|...`) that cites one of the seeded locations (file:line within ±1 line of the key, or the index heading the key names) and, where locations are shared, a disambiguating keyword.
- `severity-<ID>` (regex): the same row also carries an accepted severity word (Nonconformity / Deviation / Advisory / Review).
- `nodecoy-<D>` (regex, not_contains): no findings row with a severity word cites the decoy.
- `nodecoy-judge` (llm, haiku): none of the case's decoys is reported as a defect. `decoy-verdicts` (decoys-only case): every queried item is judged compliant.
- `skill-used` (tool_used Skill, input matches the skill name). Refusal cases use `skill-not-used` (max 0).
- `no-peek` (regex over the trace): the agent never touched `answer-key.md`, `keyspec.json` or a `graders/` path.

## How to run

```bash
# plugin eval (1 run per case, single arm, local report only)
RUNS=1 MAX_COST=15 ./evals/run_plugin_eval.sh
# 3-run version with the no-skill baseline arm (about 6x the cost of the line above)
RUNS=3 ABLATION=with-without MAX_COST=<cap> ./evals/run_plugin_eval.sh
# one case
CASE='*decoys*' ./evals/run_plugin_eval.sh
# trigger eval (run_eval, not the optimisation loop)
python3 evals/triggers/run_trigger_eval.py --runs-per-query 1 --out evals/results/$(date +%F)/triggers.json
# description optimisation later (T2-3): skill-creator's run_loop.py takes the same trigger-eval.json
```

## Known limits

- **No Bash in the runs.** On this machine `claude plugin eval` refuses any Bash-granting case ("the Docker credential store ... holds a symbolic link inside it, so the Bash sandbox cannot reliably exclude it"). Cases therefore grant Read/Glob/Grep/Skill only, and the prompts say no shell is available. The skill's scripts (linter, validator, vectors) are not exercised; this is a static-review eval until that is fixed.
- Recall is graded on the final reply's table rows. A finding given only in prose, or cited with a line outside ±1 of the key, counts as a miss. Check `results/<date>/plugin-eval/replies/` before trusting a miss.
- Where the key shares one root cause across IDs (iso999 C1-C3 all in `sort_key`), SKILL.md asks for one row, so the merged row's severity is accepted for each ID.
- The runner grants `Read` on the skill's real SKILL.md and folders (`--allow-tools Read(/<path>/**)`). Without the grant, the run's don't-ask mode denies reading `references/`. A Read through the sandbox-HOME symlink `~/.claude/skills/<skill>/...` may still be denied.
- The regex no-decoy graders are heuristics: they fire on any severity row that mentions the decoy's line or heading, which can be a real finding. Decoys that overlap real findings have `"regex": false` in keyspec.json. Treat `nodecoy-judge` (sonnet) plus reading the reply as authoritative.
- The judge follows the answer key strictly. An "optional, Advisory (may)" remark about a decoy counts as a flag.
- Costs: about $2.3-2.9 per skill for 1 run per case, single arm. `RUNS=3 ABLATION=with-without` is about 6x that (roughly $15-18 per skill), so raise `MAX_COST` above 15 for that run.
