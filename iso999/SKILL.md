---
name: iso999
description: "Audit indexes and index-producing software for adherence to ISO 999:1996 (content, organization and presentation of indexes). USE FOR: reviewing a back-of-book index or book index; code that generates indexes (collation/filing, locators and page ranges, see/see also resolution, subheading nesting; makeindex/xindy styles, Sphinx genindex, Docusaurus/MkDocs index plugins, custom indexers); linting a generated index (text, Markdown, LaTeX .ind, HTML); reviewing index entries and markup in doc sources (\\index{}, .. index::, DITA indexterm). DO NOT USE FOR: general source-code quality, search-engine/database indexes, keyword extraction, tables of contents, or choosing what subjects to index (ISO 5963)."
metadata:
  author: Alex Harmon
  version: "1.1.0-tools"
  standard: "ISO 999:1996(E), second edition (not included)"
  edition: tool-only
---

# ISO 999 index audit tools (tool-only edition)

> **The clause-by-clause guidance for ISO 999:1996 is not included because the
> standard is licensed; use your own licensed copy to interpret findings.**
>
> This edition contains the two linters, their tests, and a golden corpus.
> Each finding carries a rule ID and a clause number. The tools do not tell
> you what the clause requires. Read that clause in your licensed copy
> before you report the finding. Do not paste text of the standard into
> reports, issues or commits: cite clause numbers.

## What the tools check

Both tools are standard-library Python 3 (3.9+) and heuristic: every
finding is a prompt for review, to be confirmed against the index or the
source before it goes in a report.

| Tool | Input | Scope |
|---|---|---|
| `scripts/iso999_lint.py` | A finished index: plain text, Markdown, LaTeX `.ind` (makeindex, xindy, hyperref), HTML lists, paragraphs or tables, generated API listings | Filing order, subheading order, locators and ranges, cross-references, special-matter markers, layout of text indexes |
| `scripts/iso999_markup.py` | Index markup in doc sources: LaTeX `\index{}`, makeindex `.idx`, Sphinx `.. index::` and `:index:`, DITA `<indexterm>`, or a custom inline syntax | Variant headings, inversion, sort-as keys, cross-reference integrity, unclosed ranges |

`references/tooling.md` documents every flag, the input parser, and the
known limits.

### Rule IDs and clauses

The clause number is part of each rule ID. `--list-rules` prints the same
table with a one-line description of what the tool detects.

| Rule ID | Tool | Clause | Severity |
|---|---|---|---|
| `ISO999-7.1.3-NOTE` | lint | §7.1.3; 9.2 | info |
| `ISO999-8.1-DUPLICATE` | lint | §8.1 | warn |
| `ISO999-8.1-CASEBLOCK` | lint | §8.1 | warn |
| `ISO999-8.2-MODE` | lint | §8.2 | info |
| `ISO999-8.2-MIXED` | lint | §8.2 | warn |
| `ISO999-8.2-ORDER` | lint | §8.2 | warn |
| `ISO999-8.3-ORDER` | lint | §8.3 | warn |
| `ISO999-8.5-ORDER` | lint | §8.5 | warn |
| `ISO999-8.7-SORTKEY` | lint | §8.7 | warn |
| `ISO999-8.6-ORDER` | lint | §8.6 | warn |
| `ISO999-8.6-SYSTEMATIC` | lint | §8.6 | info |
| `ISO999-8.6-PAGEORDER` | lint | §8.6 | warn |
| `ISO999-7.2.3.5-MAXLOC` | lint | §7.2.3.5; 7.4.3 | warn |
| `ISO999-7.4.3-ASCENDING` | lint | §7.4.3 | info |
| `ISO999-7.4.3-DUPLICATE` | lint | §7.4.3 | warn |
| `ISO999-7.4.3-OVERLAP` | lint | §7.4.3.1 | warn |
| `ISO999-7.4.3.1-REVERSED` | lint | §7.4.3.1 | warn |
| `ISO999-7.4.3.1-DASH` | lint | §7.4.3.1 | warn |
| `ISO999-7.4.3.1-ELISION` | lint | §7.4.3.1 | warn |
| `ISO999-7.4.3.1-TEENS` | lint | §7.4.3.1 | info |
| `ISO999-7.4.3.1-OPEN` | lint | §7.4.3.1 | warn |
| `ISO999-7.4.3.2-PASSIM` | lint | §7.4.3.2 | warn |
| `ISO999-7.4.5-SEPARATOR` | lint | §7.4.5 | warn |
| `ISO999-7.2.2.2-NUMBER` | lint | §7.2.2.2 | info |
| `ISO999-7.3.1.1-VARIANT` | lint | §7.3.1.1 | info |
| `ISO999-7.5-SEPARATOR` | lint | §7.5.1; 7.5.2.1 | warn |
| `ISO999-7.5.1-DANGLING` | lint | §7.5.1 | warn |
| `ISO999-7.5.2-DANGLING` | lint | §7.5.2 | warn |
| `ISO999-7.5.1-LOCATORS` | lint | §7.5.1 | warn |
| `ISO999-7.5.1-CHAIN` | lint | §7.5.1 | warn |
| `ISO999-7.5.1-CYCLE` | lint | §7.5.1 | warn |
| `ISO999-7.5.1-FEW` | lint | §7.5.1 | info |
| `ISO999-7.5-SELF` | lint | §7.5 | warn |
| `ISO999-7.5-TARGETORDER` | lint | §7.5.1; 7.5.2.1 | warn |
| `ISO999-7.5.2.1-PLACEMENT` | lint | §7.5.2.1 | warn |
| `ISO999-7.5.2.1-SAMELOC` | lint | §7.5.2.1 | warn |
| `ISO999-7.5.2.1-NOREFS` | lint | §7.5.2.1 | info |
| `ISO999-8.1-CASE-ORDER` | lint | §8.1 | warn |
| `ISO999-3.10-HOMOGRAPH` | lint | §3.10 | info |
| `ISO999-8-DISPLACED` | lint | §8 | info |
| `ISO999-8.6-RUNS` | lint | §8.6 | warn |
| `ISO999-7.4-ANCHOR` | lint | §7.4 | warn |
| `ISO999-8.1-LOCALE` | lint | §8.1; 8.4 | info |
| `ISO999-8-ROOTCAUSE` | lint | §8.1; 8.4 | warn |
| `ISO999-7.3.4.2-ARTICLE` | lint | §7.3.4.2 | warn |
| `ISO999-7.3.6-ABBREV` | lint | §7.3.6 | warn |
| `ISO999-7.3.6-VARIANT` | lint | §7.3.6 | info |
| `ISO999-7.3.1-HONORIFIC` | lint | §7.3.1 | info |
| `ISO999-7.4.2-LOCSEP` | lint | §7.4.2.2.1 | warn |
| `ISO999-7.4.2-SEQUENCE` | lint | §7.4.2.2.1 | warn |
| `ISO999-7.4.2-PREFIX` | lint | §7.4.2.2.1 | warn |
| `ISO999-7.4.2-SEQORDER` | lint | §7.4.2.2.1; 7.4.3 | info |
| `ISO999-7.4.4-SPECIAL` | lint | §7.4.4 | info |
| `ISO999-9.1.2.4-INDENT` | lint | §9.1.2.4 | warn |
| `ISO999-9.4.1.4-TURNOVER` | lint | §9.1.2.4; 9.4.1.4 | warn |
| `ISO999-9.5-RUNON` | lint | §9.5; 7.2.3.3 | warn |
| `ISO999-PARSE-HEALTH` | lint | §tool | info |
| `ISO999-7.2.2.2-NUMBER` | markup | §7.2.2.2 | warn |
| `ISO999-7.3.1.1-VARIANT` | markup | §7.3.1.1 | warn |
| `ISO999-6.3-INVERSION` | markup | §6.3; 7.2.2.4 | warn |
| `ISO999-6.3-CASE` | markup | §6.3 | warn |
| `ISO999-8.1-SORTAS` | markup | §8.1 | warn |
| `ISO999-8.3-SORTAS` | markup | §8.3 | info |
| `ISO999-7.5.1-DANGLING` | markup | §7.5.1; 3.13 | warn |
| `ISO999-7.5.2-DANGLING` | markup | §7.5.2 | warn |
| `ISO999-7.5.1-CHAIN` | markup | §7.5.1; 3.13 | warn |
| `ISO999-7.5.1-CYCLE` | markup | §7.5.1 | warn |
| `ISO999-3.13-LOCATORS` | markup | §3.13; 7.5.1 | warn |
| `ISO999-7.5-SELF` | markup | §7.5 | warn |
| `ISO999-7.4.3.1-UNCLOSED` | markup | §7.4.3.1 | warn |
| `ISO999-7.4.3.1-STRAY` | markup | §7.4.3.1 | warn |
| `MARKUP-PARSE` | markup | §- | info |

`warn` means probably inconsistent or likely to mislead a reader. `info`
means worth a look. Neither is a verdict of conformance: you assign the
report severity after you read the clause.

## How to run the tools

Set `S` to this skill's `scripts` folder, for example
`S=~/.claude/skills/iso999/scripts`.

Generated index output:

```bash
python3 $S/iso999_lint.py index.txt --filing word    # match the declared filing method
python3 $S/iso999_lint.py index.txt --dump-tree      # if ISO999-PARSE-HEALTH fires, fix flags first
python3 $S/iso999_lint.py index.html --json          # machine-readable output
python3 $S/iso999_lint.py --list-rules               # rule ID, clause, severity
```

Index markup in doc sources:

```bash
python3 $S/iso999_markup.py docs/ --format auto      # latex | idx | rst | dita
python3 $S/iso999_markup.py docs/ --format custom \
    --entry-regex '\{\{\s*(?P<kind>index|see|seealso)\s*:\s*(?P<body>.*?)\s*\}\}'
python3 $S/iso999_markup.py docs/ --entries          # list every extracted entry
```

Exit status for both tools: 0 no warnings, 1 warnings, 2 usage, read or
parse error. Files that are not available locally (for example evicted
cloud-synced files) are skipped and counted.

Workflow:

1. Identify the targets (code, output, markup), the index language and
   locale, and any declared conventions (introductory note, style guide).
2. If the index is generated, rebuild it from source and lint the rebuilt
   copy. If only code is in scope, build a sample index with it and lint
   that.
3. Check parse health first. `ISO999-8-ROOTCAUSE` is one finding, not
   many.
4. Confirm each finding against the index, then read the cited clause in
   your licensed copy and decide the report severity.

## Report format

```
# ISO 999:1996 adherence — <target>

Scope: <targets audited>, locale <xx>, declared conventions: <list or "none found">
Summary: N nonconformities, N deviations, N advisories, N review notes
Evidence: <tool runs with counts, e.g. "iso999_lint --filing word: 412 entries, 9 warn, 2 info">

## Findings
| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|

## Review notes
## Not run / not applicable
## Assumptions
## Reproduction
```

- **Severity** is one of these words: **Nonconformity**, **Deviation**,
  **Advisory** or **Review note**. Choose it from the strength of the
  clause in your licensed copy; the tool's `warn`/`info` is only a hint.
- **Check ID** is the rule ID (for example `ISO999-8.2-ORDER`). **Ref** is
  the clause (`§x.y`). **Target** is `code`, `output` or `markup`.
- **Location** is a file:line or an index heading. **Evidence** gives the
  tool output or the entries concerned.
- One root cause is one finding: list the other rule IDs in the same row.
- Rank findings by severity, then by entries affected.
- Do not report a clean result for checks you did not run.

## Worked examples

`evals/baselines/api-audits/` holds audits of the Go, Rust and ServiceNow
documentation indexes in this format, with the converters and inputs used.
`evals/golden/` pins the linter's finding counts on public indexes; see
`references/tooling.md`.
