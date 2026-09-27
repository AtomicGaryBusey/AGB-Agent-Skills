# ste100 (tool-only edition)

A heuristic checker for ASD-STE100 Simplified Technical English (Issue 9)
and a tool that builds the STE dictionary on your machine from your own
download of the specification.

**ASD-STE100 is copyright ASD. This edition contains no rule text, no rule
paraphrases, and no dictionary data.** The dictionary cache (`.cache/`) is
local only and is gitignored; never commit it.

## What is included

- `SKILL.md`: tool-only instructions (setup, usage, rule IDs and Issue 9 rule numbers, report format).
- `scripts/ste_check.py` and its tests, with an invented mini dictionary (`scripts/fixtures/`).
- `tools/build_dictionary.py` and its tests, with an invented fixture (`tools/fixtures/`).
- `references/tooling.md`: flags, JSON shape, term-list format, and cache schema.
- `evals/fixtures/kestrel/project/`: an invented documentation project used by the regression tests.
- `evals/regression/*.py`: checker regression tests. They skip when the local cache is absent.

Build the dictionary with `python3 tools/build_dictionary.py --download` (needs poppler's `pdftotext`). Run the tests with `python3 -m unittest discover -s scripts`, `python3 -m unittest tools/test_build_dictionary.py` and `python3 -m unittest discover -s evals/regression`. Tests that need the local cache skip without it.

## What is not included and why

The following files of the private source repository are not in this edition (141 files).

- `SKILL.md` (original): the full skill instructions summarise and interpret ASD-STE100 rules. It is replaced by a tool-only `SKILL.md`.

**Answer key for the Kestrel fixture. It cites and paraphrases rules and dictionary entries.**

- `evals/fixtures/kestrel/answer-key.md`

**Eval graders keyed to the answer key and the catalogue.**

- `evals/graders/gen_suite.py`
- `evals/graders/keyspec.json`
- `evals/graders/summarize.py`

**Plugin-eval cases and graders. They test the full skill with the catalogue, which this edition does not have.**

- `evals/plugin/.claude-plugin/plugin.json`
- `evals/plugin/cases/ste-decoys/case.yaml`
- `evals/plugin/cases/ste-decoys/graders/decoy-verdicts.md`
- `evals/plugin/cases/ste-decoys/graders/no-peek.md`
- `evals/plugin/cases/ste-decoys/graders/nodecoy-judge.md`
- `evals/plugin/cases/ste-decoys/graders/nodecoy-X1.md`
- `evals/plugin/cases/ste-decoys/graders/nodecoy-X2.md`
- `evals/plugin/cases/ste-decoys/graders/nodecoy-X3.md`
- `evals/plugin/cases/ste-decoys/graders/nodecoy-X4.md`
- `evals/plugin/cases/ste-decoys/graders/nodecoy-X5.md`
- `evals/plugin/cases/ste-decoys/graders/skill-used.md`
- `evals/plugin/cases/ste-decoys/scaffold.sh`
- `evals/plugin/cases/ste-refusal-marketing/case.yaml`
- `evals/plugin/cases/ste-refusal-marketing/graders/skill-not-used.md`
- `evals/plugin/cases/ste-refusal-python-style/case.yaml`
- `evals/plugin/cases/ste-refusal-python-style/graders/skill-not-used.md`
- `evals/plugin/cases/ste-safety-punctuation/case.yaml`
- `evals/plugin/cases/ste-safety-punctuation/graders/no-peek.md`
- `evals/plugin/cases/ste-safety-punctuation/graders/nodecoy-judge.md`
- `evals/plugin/cases/ste-safety-punctuation/graders/nodecoy-X1.md`
- `evals/plugin/cases/ste-safety-punctuation/graders/nodecoy-X4.md`
- `evals/plugin/cases/ste-safety-punctuation/graders/recall-D12.md`
- `evals/plugin/cases/ste-safety-punctuation/graders/recall-D15.md`
- `evals/plugin/cases/ste-safety-punctuation/graders/recall-D20.md`
- `evals/plugin/cases/ste-safety-punctuation/graders/recall-D21.md`
- `evals/plugin/cases/ste-safety-punctuation/graders/severity-D12.md`
- `evals/plugin/cases/ste-safety-punctuation/graders/severity-D15.md`
- `evals/plugin/cases/ste-safety-punctuation/graders/severity-D20.md`
- `evals/plugin/cases/ste-safety-punctuation/graders/severity-D21.md`
- `evals/plugin/cases/ste-safety-punctuation/graders/skill-used.md`
- `evals/plugin/cases/ste-safety-punctuation/scaffold.sh`
- `evals/plugin/cases/ste-sentences/case.yaml`
- `evals/plugin/cases/ste-sentences/graders/no-peek.md`
- `evals/plugin/cases/ste-sentences/graders/nodecoy-judge.md`
- `evals/plugin/cases/ste-sentences/graders/nodecoy-X1.md`
- `evals/plugin/cases/ste-sentences/graders/nodecoy-X5.md`
- `evals/plugin/cases/ste-sentences/graders/recall-D06.md`
- `evals/plugin/cases/ste-sentences/graders/recall-D07.md`
- `evals/plugin/cases/ste-sentences/graders/recall-D08.md`
- `evals/plugin/cases/ste-sentences/graders/recall-D09.md`
- `evals/plugin/cases/ste-sentences/graders/recall-D11.md`
- `evals/plugin/cases/ste-sentences/graders/recall-D14.md`
- `evals/plugin/cases/ste-sentences/graders/recall-D19.md`
- `evals/plugin/cases/ste-sentences/graders/severity-D06.md`
- `evals/plugin/cases/ste-sentences/graders/severity-D07.md`
- `evals/plugin/cases/ste-sentences/graders/severity-D08.md`
- `evals/plugin/cases/ste-sentences/graders/severity-D09.md`
- `evals/plugin/cases/ste-sentences/graders/severity-D11.md`
- `evals/plugin/cases/ste-sentences/graders/severity-D14.md`
- `evals/plugin/cases/ste-sentences/graders/severity-D19.md`
- `evals/plugin/cases/ste-sentences/graders/skill-used.md`
- `evals/plugin/cases/ste-sentences/scaffold.sh`
- `evals/plugin/cases/ste-vocabulary/case.yaml`
- `evals/plugin/cases/ste-vocabulary/graders/no-peek.md`
- `evals/plugin/cases/ste-vocabulary/graders/nodecoy-judge.md`
- `evals/plugin/cases/ste-vocabulary/graders/nodecoy-X1.md`
- `evals/plugin/cases/ste-vocabulary/graders/nodecoy-X2.md`
- `evals/plugin/cases/ste-vocabulary/graders/nodecoy-X3.md`
- `evals/plugin/cases/ste-vocabulary/graders/nodecoy-X4.md`
- `evals/plugin/cases/ste-vocabulary/graders/recall-D01.md`
- `evals/plugin/cases/ste-vocabulary/graders/recall-D02.md`
- `evals/plugin/cases/ste-vocabulary/graders/recall-D03.md`
- `evals/plugin/cases/ste-vocabulary/graders/recall-D04.md`
- `evals/plugin/cases/ste-vocabulary/graders/recall-D05.md`
- `evals/plugin/cases/ste-vocabulary/graders/recall-D10.md`
- `evals/plugin/cases/ste-vocabulary/graders/recall-D13.md`
- `evals/plugin/cases/ste-vocabulary/graders/recall-D16.md`
- `evals/plugin/cases/ste-vocabulary/graders/recall-D17.md`
- `evals/plugin/cases/ste-vocabulary/graders/recall-D18.md`
- `evals/plugin/cases/ste-vocabulary/graders/severity-D01.md`
- `evals/plugin/cases/ste-vocabulary/graders/severity-D02.md`
- `evals/plugin/cases/ste-vocabulary/graders/severity-D03.md`
- `evals/plugin/cases/ste-vocabulary/graders/severity-D04.md`
- `evals/plugin/cases/ste-vocabulary/graders/severity-D05.md`
- `evals/plugin/cases/ste-vocabulary/graders/severity-D10.md`
- `evals/plugin/cases/ste-vocabulary/graders/severity-D13.md`
- `evals/plugin/cases/ste-vocabulary/graders/severity-D16.md`
- `evals/plugin/cases/ste-vocabulary/graders/severity-D17.md`
- `evals/plugin/cases/ste-vocabulary/graders/severity-D18.md`
- `evals/plugin/cases/ste-vocabulary/graders/skill-used.md`
- `evals/plugin/cases/ste-vocabulary/scaffold.sh`
- `evals/plugin/skills/ste100/references`
- `evals/plugin/skills/ste100/scripts`
- `evals/plugin/skills/ste100/SKILL.md`
- `evals/plugin/skills/ste100/SOURCES.lock`

**Describes the excluded eval harness.**

- `evals/README.md`

**Checker output summary that contains word lists derived from the dictionary.**

- `evals/regression/kestrel-summary.json`

**Recorded eval runs. Model replies quote dictionary statuses and paraphrase rules.**

- `evals/results/2026-09-26/post-docs/aggregate-result.json`
- `evals/results/2026-09-26/post-docs/console.log`
- `evals/results/2026-09-26/post-docs/replies/ste-decoys-run1.md`
- `evals/results/2026-09-26/post-docs/replies/ste-refusal-marketing-run1.md`
- `evals/results/2026-09-26/post-docs/replies/ste-refusal-python-style-run1.md`
- `evals/results/2026-09-26/post-docs/replies/ste-safety-punctuation-run1.md`
- `evals/results/2026-09-26/post-docs/replies/ste-sentences-run1.md`
- `evals/results/2026-09-26/post-docs/replies/ste-vocabulary-run1.md`
- `evals/results/2026-09-26/post-docs/report.html`
- `evals/results/2026-09-26/post-docs/summary.json`
- `evals/results/2026-09-26/post-docs/summary.md`
- `evals/results/2026-09-26/pre-docs/aggregate-result.json`
- `evals/results/2026-09-26/pre-docs/console.log`
- `evals/results/2026-09-26/pre-docs/replies/ste-decoys-run1.md`
- `evals/results/2026-09-26/pre-docs/replies/ste-refusal-marketing-run1.md`
- `evals/results/2026-09-26/pre-docs/replies/ste-refusal-python-style-run1.md`
- `evals/results/2026-09-26/pre-docs/replies/ste-safety-punctuation-run1.md`
- `evals/results/2026-09-26/pre-docs/replies/ste-sentences-run1.md`
- `evals/results/2026-09-26/pre-docs/replies/ste-vocabulary-run1.md`
- `evals/results/2026-09-26/pre-docs/report.html`
- `evals/results/2026-09-26/pre-docs/summary.json`
- `evals/results/2026-09-26/pre-docs/summary.md`
- `evals/results/2026-09-26/RESULTS.md`
- `evals/results/2026-09-26/triggers-post-docs.json`
- `evals/results/2026-09-26/triggers-pre-docs.json`
- `evals/results/2026-09-26/triggers-pre-docs.log`

**Runner for the excluded plugin evals.**

- `evals/run_plugin_eval.sh`

**Trigger evals for the full skill.**

- `evals/triggers/run_trigger_eval.py`
- `evals/triggers/trigger-eval.json`

**Rule-by-rule paraphrase catalogue of ASD-STE100 Issue 9 (rules 1-9, glossary, check index, interpretation, workflow). ASD-STE100 is ASD copyright, so no rule paraphrase is published.**

- `references/check-index.md`
- `references/glossary.md`
- `references/interpretation.md`
- `references/rules-1-words.md`
- `references/rules-2-multi-word-nouns.md`
- `references/rules-3-verbs.md`
- `references/rules-4-sentences.md`
- `references/rules-5-procedural-writing.md`
- `references/rules-6-descriptive-writing.md`
- `references/rules-7-safety-instructions.md`
- `references/rules-8-punctuation-and-word-count.md`
- `references/rules-9-writing-practices.md`
- `references/workflow.md`

**Maintainer lock file: hashes and local paths of the specification and cache.**

- `SOURCES.lock`

**Generates the excluded check index from the excluded rule files.**

- `tools/gen_check_index.py`

**Maintainer tooling: pre-push licence guard, hook installer, revalidation job and its launchd template, maintenance notes. They refer to the private repository and the local cache.**

- `tools/install-hooks.sh`
- `tools/launchd/com.local.ste100-revalidate.plist.template`
- `tools/pre-push`
- `tools/README-maintenance.md`
- `tools/revalidate.py`
