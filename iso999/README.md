# iso999 (tool-only edition)

Linters that check back-of-book indexes, index-generating code, and index
markup against ISO 999:1996. Each finding carries a rule ID and a clause
number.

**The clause-by-clause guidance for ISO 999:1996 is not included because the
standard is licensed; use your own licensed copy to interpret findings.**

## What is included

- `SKILL.md`: tool-only instructions (rule IDs and clause numbers, usage, report format).
- `scripts/iso999_lint.py`, `scripts/iso999_markup.py` and their tests (all test fixtures are invented).
- `references/tooling.md`: flags, input parsing, and limits of both tools.
- `evals/golden/`: golden corpus pinned by the tests (Darwin index from Project Gutenberg with its licence header, a self-built Sphinx index, a self-built xindy/hyperref `.ind`).
- `evals/baselines/api-audits/`: worked audits of the Go, Rust and ServiceNow documentation indexes, with converters and inputs. Findings cite clause numbers only.

Run the tests with `python3 -m unittest discover -s scripts`. The seven tests that use the excluded `pellow-valley` fixture skip.

## What is not included and why

The following files of the private source repository are not in this edition (149 files).

- `SKILL.md` (original): the full skill instructions summarise and interpret clauses of ISO 999:1996 and point to the licensed PDF. It is replaced by a tool-only `SKILL.md`.

**Eval fixture and answer key. The answer key quotes and paraphrases the standard, and the fixture is only meaningful with it.**

- `evals/fixtures/pellow-valley/answer-key.md`
- `evals/fixtures/pellow-valley/project/build/index.txt`
- `evals/fixtures/pellow-valley/project/docs/01-origins.md`
- `evals/fixtures/pellow-valley/project/docs/02-construction.md`
- `evals/fixtures/pellow-valley/project/docs/03-operations.md`
- `evals/fixtures/pellow-valley/project/docs/04-flood-and-decline.md`
- `evals/fixtures/pellow-valley/project/docs/05-preservation.md`
- `evals/fixtures/pellow-valley/project/docs/index-note.txt`
- `evals/fixtures/pellow-valley/project/indexer/build_index.py`
- `evals/fixtures/pellow-valley/project/README.md`

**Eval graders keyed to the answer key and the catalogue.**

- `evals/graders/gen_suite.py`
- `evals/graders/keyspec.json`
- `evals/graders/summarize.py`

**Plugin-eval cases and graders. They test the full skill with the catalogue, which this edition does not have.**

- `evals/plugin/.claude-plugin/plugin.json`
- `evals/plugin/cases/iso-code/case.yaml`
- `evals/plugin/cases/iso-code/graders/no-peek.md`
- `evals/plugin/cases/iso-code/graders/nodecoy-D3.md`
- `evals/plugin/cases/iso-code/graders/nodecoy-judge.md`
- `evals/plugin/cases/iso-code/graders/recall-C1.md`
- `evals/plugin/cases/iso-code/graders/recall-C2.md`
- `evals/plugin/cases/iso-code/graders/recall-C3.md`
- `evals/plugin/cases/iso-code/graders/recall-C4.md`
- `evals/plugin/cases/iso-code/graders/recall-C5.md`
- `evals/plugin/cases/iso-code/graders/recall-C6.md`
- `evals/plugin/cases/iso-code/graders/recall-C7.md`
- `evals/plugin/cases/iso-code/graders/severity-C1.md`
- `evals/plugin/cases/iso-code/graders/severity-C2.md`
- `evals/plugin/cases/iso-code/graders/severity-C3.md`
- `evals/plugin/cases/iso-code/graders/severity-C4.md`
- `evals/plugin/cases/iso-code/graders/severity-C5.md`
- `evals/plugin/cases/iso-code/graders/severity-C6.md`
- `evals/plugin/cases/iso-code/graders/severity-C7.md`
- `evals/plugin/cases/iso-code/graders/skill-used.md`
- `evals/plugin/cases/iso-code/scaffold.sh`
- `evals/plugin/cases/iso-decoys/case.yaml`
- `evals/plugin/cases/iso-decoys/graders/decoy-verdicts.md`
- `evals/plugin/cases/iso-decoys/graders/no-peek.md`
- `evals/plugin/cases/iso-decoys/graders/nodecoy-D2.md`
- `evals/plugin/cases/iso-decoys/graders/nodecoy-D3.md`
- `evals/plugin/cases/iso-decoys/graders/nodecoy-judge.md`
- `evals/plugin/cases/iso-decoys/graders/skill-used.md`
- `evals/plugin/cases/iso-decoys/scaffold.sh`
- `evals/plugin/cases/iso-markup/case.yaml`
- `evals/plugin/cases/iso-markup/graders/no-peek.md`
- `evals/plugin/cases/iso-markup/graders/nodecoy-D2.md`
- `evals/plugin/cases/iso-markup/graders/nodecoy-D3.md`
- `evals/plugin/cases/iso-markup/graders/nodecoy-judge.md`
- `evals/plugin/cases/iso-markup/graders/recall-M1.md`
- `evals/plugin/cases/iso-markup/graders/recall-M2.md`
- `evals/plugin/cases/iso-markup/graders/recall-M3.md`
- `evals/plugin/cases/iso-markup/graders/recall-M4.md`
- `evals/plugin/cases/iso-markup/graders/recall-M5.md`
- `evals/plugin/cases/iso-markup/graders/severity-M1.md`
- `evals/plugin/cases/iso-markup/graders/severity-M2.md`
- `evals/plugin/cases/iso-markup/graders/severity-M3.md`
- `evals/plugin/cases/iso-markup/graders/severity-M4.md`
- `evals/plugin/cases/iso-markup/graders/severity-M5.md`
- `evals/plugin/cases/iso-markup/graders/skill-used.md`
- `evals/plugin/cases/iso-markup/scaffold.sh`
- `evals/plugin/cases/iso-output/case.yaml`
- `evals/plugin/cases/iso-output/graders/no-peek.md`
- `evals/plugin/cases/iso-output/graders/nodecoy-D2.md`
- `evals/plugin/cases/iso-output/graders/nodecoy-D3.md`
- `evals/plugin/cases/iso-output/graders/nodecoy-judge.md`
- `evals/plugin/cases/iso-output/graders/recall-O1.md`
- `evals/plugin/cases/iso-output/graders/recall-O2.md`
- `evals/plugin/cases/iso-output/graders/recall-O3.md`
- `evals/plugin/cases/iso-output/graders/severity-O1.md`
- `evals/plugin/cases/iso-output/graders/severity-O2.md`
- `evals/plugin/cases/iso-output/graders/severity-O3.md`
- `evals/plugin/cases/iso-output/graders/skill-used.md`
- `evals/plugin/cases/iso-output/scaffold.sh`
- `evals/plugin/cases/iso-refusal-db-index/case.yaml`
- `evals/plugin/cases/iso-refusal-db-index/graders/skill-not-used.md`
- `evals/plugin/cases/iso-refusal-pandas/case.yaml`
- `evals/plugin/cases/iso-refusal-pandas/graders/skill-not-used.md`
- `evals/plugin/skills/iso999/references`
- `evals/plugin/skills/iso999/scripts`
- `evals/plugin/skills/iso999/SKILL.md`
- `evals/plugin/skills/iso999/SOURCES.lock`

**Describes the excluded eval harness.**

- `evals/README.md`

**Recorded eval runs. Model replies paraphrase the catalogue and the standard.**

- `evals/results/2026-09-25/plugin-eval-attempt1/aggregate-result.json`
- `evals/results/2026-09-25/plugin-eval-attempt1/console.log`
- `evals/results/2026-09-25/plugin-eval-attempt1/replies/iso-code-run1.md`
- `evals/results/2026-09-25/plugin-eval-attempt1/replies/iso-decoys-run1.md`
- `evals/results/2026-09-25/plugin-eval-attempt1/replies/iso-markup-run1.md`
- `evals/results/2026-09-25/plugin-eval-attempt1/replies/iso-output-run1.md`
- `evals/results/2026-09-25/plugin-eval-attempt1/replies/iso-refusal-db-index-run1.md`
- `evals/results/2026-09-25/plugin-eval-attempt1/replies/iso-refusal-pandas-run1.md`
- `evals/results/2026-09-25/plugin-eval-attempt1/report.html`
- `evals/results/2026-09-25/plugin-eval-attempt1/summary.json`
- `evals/results/2026-09-25/plugin-eval-attempt1/summary.md`
- `evals/results/2026-09-25/plugin-eval/aggregate-result.json`
- `evals/results/2026-09-25/plugin-eval/console.log`
- `evals/results/2026-09-25/plugin-eval/replies/iso-code-run1.md`
- `evals/results/2026-09-25/plugin-eval/replies/iso-decoys-run1.md`
- `evals/results/2026-09-25/plugin-eval/replies/iso-markup-run1.md`
- `evals/results/2026-09-25/plugin-eval/replies/iso-output-run1.md`
- `evals/results/2026-09-25/plugin-eval/replies/iso-refusal-db-index-run1.md`
- `evals/results/2026-09-25/plugin-eval/replies/iso-refusal-pandas-run1.md`
- `evals/results/2026-09-25/plugin-eval/report.html`
- `evals/results/2026-09-25/plugin-eval/summary.json`
- `evals/results/2026-09-25/plugin-eval/summary.md`
- `evals/results/2026-09-25/RESULTS.md`
- `evals/results/2026-09-25/triggers.json`
- `evals/results/2026-09-25/triggers.log`
- `evals/results/2026-09-26/o3-fix/aggregate-result.json`
- `evals/results/2026-09-26/o3-fix/console.log`
- `evals/results/2026-09-26/o3-fix/replies/iso-output-run1.md`
- `evals/results/2026-09-26/o3-fix/report.html`
- `evals/results/2026-09-26/o3-fix/summary.json`
- `evals/results/2026-09-26/o3-fix/summary.md`
- `evals/results/2026-09-26/post-move/aggregate-result.json`
- `evals/results/2026-09-26/post-move/console.log`
- `evals/results/2026-09-26/post-move/replies/iso-output-run1.md`
- `evals/results/2026-09-26/post-move/report.html`
- `evals/results/2026-09-26/post-move/summary.json`
- `evals/results/2026-09-26/post-move/summary.md`
- `evals/results/2026-09-26/post-wave2/aggregate-result.json`
- `evals/results/2026-09-26/post-wave2/console.log`
- `evals/results/2026-09-26/post-wave2/replies/iso-code-run1.md`
- `evals/results/2026-09-26/post-wave2/replies/iso-decoys-run1.md`
- `evals/results/2026-09-26/post-wave2/replies/iso-markup-run1.md`
- `evals/results/2026-09-26/post-wave2/replies/iso-output-run1.md`
- `evals/results/2026-09-26/post-wave2/replies/iso-refusal-db-index-run1.md`
- `evals/results/2026-09-26/post-wave2/replies/iso-refusal-pandas-run1.md`
- `evals/results/2026-09-26/post-wave2/report.html`
- `evals/results/2026-09-26/post-wave2/summary.json`
- `evals/results/2026-09-26/post-wave2/summary.md`
- `evals/results/2026-09-26/triggers.json`

**Runner for the excluded plugin evals.**

- `evals/run_plugin_eval.sh`

**Trigger evals for the full skill.**

- `evals/triggers/run_trigger_eval.py`
- `evals/triggers/trigger-eval.json`

**Clause-by-clause paraphrase catalogue of ISO 999:1996 (check index, interpretation rules, hotspots, per-clause checks). ISO 999 is licensed for a single user, so a paraphrase catalogue is not published.**

- `references/arrangement-and-presentation.md`
- `references/check-index.md`
- `references/general-and-glossary.md`
- `references/headings.md`
- `references/hotspots.md`
- `references/interpretation.md`
- `references/locators-and-crossrefs.md`
- `references/names-and-titles.md`
- `references/software-indexes.md`

**Maintainer lock file: hashes and local paths of the licensed source PDF.**

- `SOURCES.lock`

**Maintainer tooling: pre-push licence guard, hook installer, revalidation job and its launchd template, maintenance notes. They refer to the licensed PDF and to the private repository.**

- `tools/install-hooks.sh`
- `tools/launchd/com.local.skill-revalidate.plist.template`
- `tools/pre-push`
- `tools/README-maintenance.md`
- `tools/revalidate.py`
