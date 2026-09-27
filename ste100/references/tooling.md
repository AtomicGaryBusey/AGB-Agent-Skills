# Tooling reference

Two tools: `scripts/ste_check.py` (the checker) and
`tools/build_dictionary.py` (the dictionary builder). Both use the Python
standard library only. This file does not record versions: get the checker
version from `python3 $S/scripts/ste_check.py --version` (or `meta.version`
in the JSON output) and the builder version from `meta.builder_version` in
the cache. Give the checker version in the Reproduction section. Below, `S=~/.claude/skills/ste100`.

## `scripts/ste_check.py`

```
python3 $S/scripts/ste_check.py [--dictionary FILE] [--terms FILE] [--json]
        [--min-severity {info,warn}] [--profile {auto,procedure,description}]
        [--unknown-words] [--list-rules] [--version] [PATH ...]
```

### Inputs

- **PATH** is a file or a directory. A directory is read recursively for
  `.md`, `.markdown`, `.mdx`, `.txt`, `.rst`, and `.adoc` files (and their
  other common extensions). Hidden files and folders, and `node_modules`,
  `vendor`, `venv`, `dist`, `build`, `target`, and `_build`, are not read. A
  code or data file that you name directly is skipped with an error line.
- **`-`** reads standard input as Markdown. Use it for a word question:
  `echo "Frobnicate the valve." | python3 $S/scripts/ste_check.py -`.
- **Masked text.** The checker removes code blocks, inline code, URLs, e-mail
  addresses, link targets, HTML, file paths, command flags, identifiers with
  `_`, `::`, or camelCase, version numbers, and text in quotation marks
  before it checks the prose. Masked text counts as one word.
- **Labels.** `WARNING`, `CAUTION`, and `DANGER` blocks are safety
  instructions. `NOTE`, `TIP`, `IMPORTANT`, `NOTICE`, and `ATTENTION` blocks
  are notes. The checker finds a label at the start of a paragraph (`NOTE:`,
  `**WARNING:**`, `CAUTION -`), on its own line before a paragraph, in a
  GitHub alert (`> [!WARNING]`), in an rST directive (`.. warning::`), and
  in an AsciiDoc admonition. `DANGER`, `NOTICE`, and `ATTENTION` also get an
  STE-7.1 INFO finding.

### Flags

| Flag | Effect |
|---|---|
| `--dictionary FILE` | Use this dictionary cache. Without the flag the checker uses `$STE100_DICTIONARY`, then `.cache/ste100-dictionary.json` in the skill folder, then in the current folder. A named file that is missing or not valid is a usage error (exit 2). A default file that is missing gives one `STE-X-NODICT` INFO finding, and the vocabulary checks do not run. |
| `--terms FILE` | Use this term list. Without the flag the checker looks for the nearest `DOCS_TERMS.md`: from each PATH folder up to the folder that holds `.git`, then from the current folder. The term list file is never checked as prose, and a file named `DOCS_TERMS.md` never is. |
| `--json` | Write one JSON object (shape below). With `--unknown-words`, write a list. With `--list-rules`, write the rule catalogue as a list. |
| `--min-severity {info,warn}` | Do not report findings below this level (default `info`). |
| `--profile {auto,procedure,description}` | Sentence-length limit: `procedure` applies 20 words (STE-5.1) to all sentences, `description` applies 25 (STE-6.3), and `auto` (default) decides for each sentence. |
| `--unknown-words` | Print only the words that neither the dictionary nor the term list has (STE-1.6), with a use count and a TN or TV guess, most frequent first. Use the list to seed `DOCS_TERMS.md`. Review each word. |
| `--list-rules` | Print the rule catalogue: ID, title, judgment (`objective`, `heuristic`, `editorial`), whether it needs the dictionary, and whether the script checks it. Then stop. |
| `--version` | Print the version. |

`--profile auto` decides as follows: a safety block is procedural, a note is
descriptive, an item of a numbered list is procedural, and any other
sentence is procedural only if it starts with an imperative.

### Term list format

The checker reads Markdown tables. The first column holds the term; its
heading decides the tag (`Technical noun` gives TN, `Technical verb` gives
TV; `Term` uses the tag of the section heading). The `Definition` column is
optional. Words in the `Do not use` column are rejected synonyms: each use in
the prose becomes an STE-1.11 finding that names the preferred term.

```
## Technical nouns

| Technical noun | Definition | Do not use |
|---|---|---|
| access token | The string that the API accepts as proof of identity | auth token, bearer |

## Technical verbs

| Technical verb | Definition | Do not use |
|---|---|---|
| encrypt | To change data into a form that only a key holder can read | - |
```

The checker also accepts one term on each line, with an optional tag and
rejected synonyms: `access token (TN) - do not use: auth token, bearer`. A
line that is not a list item, has no tag, and has more than five words is
read as prose and ignored.

### Text output

One line for each finding, then a total line:

```
docs/setup.md:12:5 WARN STE-5.1 procedural sentence has 24 words (maximum 20)
    suggestion: Divide the sentence, or use a vertical list.
3 finding(s): 1 warn, 2 info in 1 file(s)
```

### JSON output (`--json`)

```
{
  "meta": {
    "tool": "ste_check.py", "version": "<checker version>",
    "dictionary": {"path": ..., "loaded": true, "source": ..., "issue_date": ..., "counts": {...}},
    "terms": {"path": ..., "count": N},
    "profile": "auto", "min_severity": "info",
    "files": [...], "skipped": [...], "errors": [...]
  },
  "summary": {
    "files": N, "findings": N, "groups": N,
    "by_severity": {"warn": N, "info": N},
    "by_rule": {"STE-1.6": N, ...}, "groups_by_rule": {"STE-1.6": N, ...}
  },
  "findings": [
    {"file": ..., "line": N, "col": N, "severity": "warn|info", "rule": "STE-...",
     "message": ..., "suggestion": ..., "excerpt": ..., "count": N,
     "locations": [{"file": ..., "line": N, "col": N}, ...]}
  ]
}
```

`summary.findings` counts occurrences. `summary.groups` counts rows. Use
`meta.dictionary.loaded` to decide if the vocabulary rules ran, and
`meta.files` and `meta.errors` for the "Not run" section.

`--unknown-words --json` writes a list of
`{"word", "count", "tag": "TN|TV", "files": [...]}`.

### Grouping

- Vocabulary findings for STE-1.1, STE-1.2, STE-1.4, STE-1.6, and STE-1.14
  are grouped across all files of one run: one row for each word and message,
  with `count` and `locations`. STE-1.6 groups by the singular form of the
  word alone, and its JSON `locations` holds the first five. Text output
  shows five locations and the total.
- Each word token gets at most one vocabulary finding. The most specific
  rule wins: STE-1.11, then 1.1, 1.2, 1.4, 1.7 or 1.13, and 1.6 last.
- Word-count rules 8.4 to 8.7 have no findings of their own. The checker
  applies them inside STE-5.1 and STE-6.3.

### Exit status

| Code | Meaning |
|---|---|
| 0 | No WARN findings. Also for `--list-rules`, `--version`, and `--unknown-words` |
| 1 | One or more WARN findings |
| 2 | Usage error: no PATH, a named dictionary or term list that is missing or not valid, or no PATH could be read |

## `tools/build_dictionary.py`

```
python3 $S/tools/build_dictionary.py [--pdf PDF | --download] [--out OUT]
        [--check [--quick]] [--verbose]
```

It needs `pdftotext` from poppler (`brew install poppler` or
`apt install poppler-utils`).

| Flag | Effect |
|---|---|
| `--download` | Download the public Issue 9 PDF into `.cache/ASD-STE100_ISSUE9.pdf` (your own copy), then build |
| `--pdf PDF` | Build from your copy of the PDF. Without `--pdf` or `--download`, the tool uses `.cache/ASD-STE100_ISSUE9.pdf` |
| `--out OUT` | Cache path (default `.cache/ste100-dictionary.json` in the skill folder) |
| `--check` | Do not build. Make sure that the cache matches the PDF: sha256, the stored counts, and a new parse of the PDF |
| `--quick` | With `--check`: compare the sha256 and the stored counts only |
| `--verbose` | Print each note and discrepancy |

Exit status: 0 on success; 1 if `--check` fails or the build finds a
discrepancy that is not a count; 2 if the PDF is missing or cannot be parsed.
A difference between the counted totals and the totals that the PDF states
does not fail the build.

### Cache schema (no entries shown)

`.cache/ste100-dictionary.json` is local and gitignored. Do not commit,
publish, or quote it.

- `meta`: `source`, `issue_date`, `pdf_sha256`, `built_at`,
  `builder_version`, `counts` (`approved`, `not_approved`, `entries`),
  `expected_counts` (the totals that the PDF states), `notes`, and
  `validation` (discrepancies, and a comparison with the change list in the PDF).
- `entries`: one object for each headword and part of speech, with `word`,
  `display` (the printed case), `pos`, `approved`, `meaning` (a short gloss
  of at most 12 words, for local look-up only), `forms`, and `alternatives`
  (each with `word`, `pos`, and `kind`: `approved`, `TN`, or `TV`). The STE
  and non-STE examples of the specification are not stored.
- The `meaning` text, and any checker output that shows it, is ASD text. Use
  it to decide a finding, then give the meaning in your own words. Never copy
  it into a report, issue, commit, or shared file.
- `forms`: an index from each lower-case surface form to the entries that
  permit it (`word`, `pos`, `approved`).

## Tests

```bash
python3 -m unittest discover -s scripts             # checker, with an invented mini dictionary
python3 -m unittest tools/test_build_dictionary.py   # builder
python3 -m unittest discover -s evals/regression     # checker regression; skips without .cache/
```

Tests that need the locally built cache skip when `.cache/` is absent.
