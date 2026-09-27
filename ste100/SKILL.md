---
name: ste100
description: "Write, rewrite, audit, or answer questions about ASD-STE100 Simplified Technical English (STE, STE100), the controlled language for technical documentation. USE FOR: drafting or rewriting READMEs, guides, manuals, runbooks, install docs, procedures, and help text in STE; technical writing review and STE conformance audits with rule IDs and severities; word questions such as 'Is utilize allowed in ASD-STE100?' or 'is this an approved word?'; approved words, part of speech, technical nouns and technical verbs, a DOCS_TERMS.md term list; sentence length (20/25 words), active voice, imperative steps, WARNING/CAUTION/NOTE safety instructions, punctuation. DO NOT USE FOR: code, code comments, commit messages, chat replies, marketing copy, non-English text, ISO 999 indexes, RFC 3339 timestamps."
metadata:
  author: Alex Harmon
  version: "2.0.0-tools"
  standard: "ASD-STE100 Issue 9 (2025-01-15) (not included)"
  edition: tool-only
---

# ASD-STE100 checker (tool-only edition)

> **Licence note.** ASD-STE100 is copyright ASD (the AeroSpace, Security and
> Defence Industries Association of Europe). This edition contains no rule
> text, no rule paraphrases, and no dictionary data. It contains a heuristic
> checker and a tool that builds the dictionary on your machine from your
> own download of the specification. Read the specification to interpret
> each finding.
>
> The dictionary cache (`.cache/`) is **local only**. Never commit, publish,
> or quote it. The `.gitignore` in this folder excludes `.cache/`; keep it.
> Never paste dictionary entries, rule text, or specification examples into
> a report, commit, issue, or shared file. Cite rule numbers.

## Setup: build the local dictionary

The specification is a free public PDF from ASD. Download it yourself and
build the cache once:

```bash
S=~/.claude/skills/ste100
python3 $S/tools/build_dictionary.py --download        # fetches the public Issue 9 PDF into .cache/, then builds
python3 $S/tools/build_dictionary.py --pdf PATH.pdf    # or build from a copy you already have
python3 $S/tools/build_dictionary.py --check --quick   # confirm the cache matches the PDF
```

The builder needs Python 3.9+ and `pdftotext` from poppler
(`brew install poppler` or `apt install poppler-utils`). It writes
`.cache/ste100-dictionary.json`. Without the cache, the checker reports
`STE-X-NODICT` and does not run the vocabulary checks; all other checks run.

## Checker usage

```bash
C=$S/scripts/ste_check.py
python3 $C docs/ --json                      # all findings, grouped
python3 $C docs/ --unknown-words             # technical noun / verb candidates for DOCS_TERMS.md
python3 $C docs/install.md --profile procedure
echo "Frobnicate the valve." | python3 $C -  # check one sentence
python3 $C --list-rules                      # rule IDs, judgment, whether the script checks them
python3 $C --version
```

- Input: Markdown, text, reStructuredText and AsciiDoc files or folders, or
  `-` for standard input. Code, inline code, URLs, paths and identifiers are
  masked before the prose is checked.
- Term list: the checker reads the nearest `DOCS_TERMS.md` (or `--terms
  FILE`). Format:
  ```
  | Technical noun | Definition | Do not use |
  |---|---|---|
  | log file | The file where the service records its events | logfile, journal |
  ```
  Use a second table with the first column `Technical verb` for technical
  verbs.
- Exit status: 0 no WARN findings, 1 one or more WARN findings, 2 usage
  error.
- The checker is heuristic. It guesses parts of speech and sentence types.
  Confirm each finding in context before you report it.

`references/tooling.md` documents every flag, the JSON shape, the term-list
format, and the cache schema.

## Rule IDs

Checker ID `STE-s.r` is rule s.r of ASD-STE100 Issue 9, Part 1.
`STE-GR-n` is general recommendation n. `STE-X-*` are checker heuristics
with no rule in the specification. **Judgment** is `objective`,
`heuristic` or `editorial`; the script does not check editorial rules.

| Checker ID | Issue 9 reference | Judgment | Needs dictionary | Checked by script |
|---|---|---|---|---|
| `STE-1.1` | Issue 9 §1.1 | objective | yes | yes |
| `STE-1.2` | Issue 9 §1.2 | heuristic | yes | yes |
| `STE-1.3` | Issue 9 §1.3 | editorial | yes | no |
| `STE-1.4` | Issue 9 §1.4 | objective | yes | yes |
| `STE-1.5` | Issue 9 §1.5 | editorial | no | no |
| `STE-1.6` | Issue 9 §1.6 | heuristic | yes | yes |
| `STE-1.7` | Issue 9 §1.7 | heuristic | no | yes |
| `STE-1.8` | Issue 9 §1.8 | editorial | no | no |
| `STE-1.9` | Issue 9 §1.9 | editorial | no | no |
| `STE-1.10` | Issue 9 §1.10 | editorial | no | no |
| `STE-1.11` | Issue 9 §1.11 | objective | no | yes |
| `STE-1.12` | Issue 9 §1.12 | editorial | no | no |
| `STE-1.13` | Issue 9 §1.13 | heuristic | no | yes |
| `STE-1.14` | Issue 9 §1.14 | objective | no | yes |
| `STE-2.1` | Issue 9 §2.1 | heuristic | no | yes |
| `STE-2.2` | Issue 9 §2.2 | heuristic | no | yes |
| `STE-3.1` | Issue 9 §3.1 | objective | yes | no |
| `STE-3.2` | Issue 9 §3.2 | heuristic | no | yes |
| `STE-3.3` | Issue 9 §3.3 | heuristic | no | no |
| `STE-3.4` | Issue 9 §3.4 | heuristic | no | yes |
| `STE-3.5` | Issue 9 §3.5 | heuristic | no | yes |
| `STE-3.6` | Issue 9 §3.6 | heuristic | no | yes |
| `STE-3.7` | Issue 9 §3.7 | heuristic | yes | yes |
| `STE-4.1` | Issue 9 §4.1 | editorial | no | no |
| `STE-4.2` | Issue 9 §4.2 | heuristic | no | yes |
| `STE-4.3` | Issue 9 §4.3 | heuristic | no | yes |
| `STE-4.4` | Issue 9 §4.4 | editorial | no | no |
| `STE-4.5` | Issue 9 §4.5 | heuristic | yes | yes |
| `STE-5.1` | Issue 9 §5.1 | objective | no | yes |
| `STE-5.2` | Issue 9 §5.2 | heuristic | no | yes |
| `STE-5.3` | Issue 9 §5.3 | heuristic | no | yes |
| `STE-5.4` | Issue 9 §5.4 | heuristic | no | yes |
| `STE-5.5` | Issue 9 §5.5 | heuristic | no | yes |
| `STE-6.1` | Issue 9 §6.1 | editorial | no | no |
| `STE-6.2` | Issue 9 §6.2 | editorial | no | no |
| `STE-6.3` | Issue 9 §6.3 | objective | no | yes |
| `STE-6.4` | Issue 9 §6.4 | editorial | no | no |
| `STE-6.5` | Issue 9 §6.5 | editorial | no | no |
| `STE-6.6` | Issue 9 §6.6 | objective | no | yes |
| `STE-7.1` | Issue 9 §7.1 | heuristic | no | yes |
| `STE-7.2` | Issue 9 §7.2 | heuristic | no | yes |
| `STE-7.3` | Issue 9 §7.3 | heuristic | no | yes |
| `STE-8.1` | Issue 9 §8.1 | objective | no | yes |
| `STE-8.2` | Issue 9 §8.2 | editorial | no | no |
| `STE-8.3` | Issue 9 §8.3 | editorial | no | no |
| `STE-8.4` | Issue 9 §8.4 | objective | no | no |
| `STE-8.5` | Issue 9 §8.5 | objective | no | no |
| `STE-8.6` | Issue 9 §8.6 | objective | no | no |
| `STE-8.7` | Issue 9 §8.7 | objective | no | no |
| `STE-9.1` | Issue 9 §9.1 | editorial | no | no |
| `STE-9.2` | Issue 9 §9.2 | editorial | no | no |
| `STE-9.3` | Issue 9 §9.3 | heuristic | no | yes |
| `STE-9.4` | Issue 9 §9.4 | editorial | no | no |
| `STE-GR-1` | GR-1 (recommendation) | editorial | no | no |
| `STE-GR-2` | GR-2 (recommendation) | editorial | no | no |
| `STE-GR-3` | GR-3 (recommendation) | editorial | no | no |
| `STE-GR-4` | GR-4 (recommendation) | editorial | no | no |
| `STE-GR-5` | GR-5 (recommendation) | editorial | no | no |
| `STE-GR-6` | GR-6 (recommendation) | objective | no | yes |
| `STE-GR-7` | GR-7 (recommendation) | heuristic | no | yes |
| `STE-GR-8` | GR-8 (recommendation) | editorial | no | no |
| `STE-X-NODICT` | checker heuristic (no Issue 9 rule) | objective | no | yes |
| `STE-X-OBLIGATION` | checker heuristic (no Issue 9 rule) | heuristic | no | yes |
| `STE-X-FIRST-PERSON` | checker heuristic (no Issue 9 rule) | heuristic | no | yes |
| `STE-X-SLASH` | checker heuristic (no Issue 9 rule) | heuristic | no | yes |

## Report format

```
# ASD-STE100 Issue 9 conformance — <target>

Scope: <files>, type <procedure|description|mixed>, term list <path|none>, dictionary <loaded, counts|missing>
Summary: N nonconformities, N deviations, N advisories, N review notes
Evidence: <tool runs with counts, e.g. "ste_check --json docs/: 4 files, 37 findings (12 warn, 25 info)">

## Findings
| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|

## Review notes
## Not run / not applicable
## Assumptions
## Reproduction
```

- **Severity** is one of these words: **Nonconformity**, **Deviation**,
  **Advisory**, or **Review note**. The checker's WARN and INFO levels are
  not report severities: decide the severity from the rule in your copy of
  the specification. `STE-GR-*` and `STE-X-*` findings are Advisory at
  most.
- **Check ID** is the checker ID (`STE-5.1`, `STE-GR-6`, `STE-X-SLASH`).
  **Ref** is `Issue 9 §s.r` or `GR-n`. **Target** is `procedure`,
  `description`, `safety`, `title`, or `term list`. **Location** is
  `file:line`.
- **Evidence** is the offending words (a few words only) plus the fact that
  proves the finding (word count, dictionary status, checker ID). **Fix** is
  a rewrite that you wrote.
- One root cause is one row: list the other rule IDs in that row. Rank by
  severity, then by occurrences.
- **Reproduction** gives the commands and the checker version (`--version`).
  If the dictionary was missing, list the vocabulary rules under "Not run".
- Never report a clean result for checks that you did not run.
