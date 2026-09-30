# AGB Agent Skills

Claude Code skills (Agent Skills format) that audit documentation and code
against published standards: Internet timestamp formats, back-of-book
indexes, Simplified Technical English, and web accessibility (WCAG 2.2). Each skill ships a
`SKILL.md`, standard-library Python tools, and a test suite. (`wcag22-a11y` also has an
optional Node.js page runner for rendered checks.)

| Skill | What it checks | Edition | Key tools |
|---|---|---|---|
| [`rfc3339-ixdtf`](rfc3339-ixdtf/) | Code, schemas and APIs that parse, validate or emit RFC 3339 timestamps and RFC 9557 (IXDTF) suffixes | Full | `scripts/rfcdt.py` (checker and risky-API scanner), `scripts/run_vectors.py` (conformance vectors), `vectors/vectors.json` |
| [`iso999`](iso999/) | Back-of-book indexes, index-generating code, and index markup against ISO 999:1996 | Tool-only | `scripts/iso999_lint.py` (generated index output), `scripts/iso999_markup.py` (index markup in sources) |
| [`ste100`](ste100/) | Technical documentation against ASD-STE100 Simplified Technical English, Issue 9 | Tool-only | `scripts/ste_check.py` (checker), `tools/build_dictionary.py` (builds the local dictionary) |
| [`wcag22-a11y`](wcag22-a11y/) | Web pages, sites, HTML, CSS and components (React, Vue, Svelte, templates) against WCAG 2.2 Level A/AA, with evidence for VPAT/ACR, Section 508 and EN 301 549 at the WCAG level | Full | `scripts/wcag_audit.py` (runs both tools, drafts the report), `scripts/wcag_scan.py` (static scanner), `scripts/wcag_page.mjs` (rendered checks with Playwright and axe-core) |

## Installation

Clone the repository, then link or copy each skill folder into
`~/.claude/skills/<name>`:

```bash
git clone https://github.com/AtomicGaryBusey/AGB-Agent-Skills.git
cd AGB-Agent-Skills
mkdir -p ~/.claude/skills
for s in rfc3339-ixdtf iso999 ste100 wcag22-a11y; do ln -s "$PWD/$s" ~/.claude/skills/$s; done
# or: cp -R rfc3339-ixdtf iso999 ste100 wcag22-a11y ~/.claude/skills/
```

Prerequisites:

- All skills: Python 3.9 or later (standard library only).
- `ste100`: poppler's `pdftotext` (`brew install poppler` or
  `apt install poppler-utils`), and your own download of the ASD-STE100
  specification, built into a local dictionary:
  `python3 ~/.claude/skills/ste100/tools/build_dictionary.py --download`.
  Without the dictionary, the vocabulary checks do not run.
- `iso999`: your own licensed copy of ISO 999:1996 to interpret findings.
- `wcag22-a11y`: the static scanner needs only Python. For rendered checks
  (contrast, focus, reflow, target size, keyboard traps and more), install
  Node.js 18 or later, then run
  `~/.claude/skills/wcag22-a11y/scripts/setup_page_runner.sh`. It installs
  pinned Playwright, axe-core and Chromium headless shell (about 220 MB) into
  the skill's gitignored `.cache/` folder. On macOS, keep the display awake
  during long page runs (for example `caffeinate -d`).

## Usage

The skills load automatically when a request matches their description.
The tools also run on their own:

```bash
# rfc3339-ixdtf: validate one timestamp, then scan a source tree
python3 ~/.claude/skills/rfc3339-ixdtf/scripts/rfcdt.py check --profile ixdtf '2026-09-24T12:00:00+02:00[Europe/Paris]'
python3 ~/.claude/skills/rfc3339-ixdtf/scripts/rfcdt.py scan src/ --json

# iso999: lint a generated index
python3 ~/.claude/skills/iso999/scripts/iso999_lint.py build/index.txt --filing word

# ste100: check a documentation folder
python3 ~/.claude/skills/ste100/scripts/ste_check.py docs/ --json

# wcag22-a11y: static scan plus rendered checks of a local site, as a report skeleton
python3 ~/.claude/skills/wcag22-a11y/scripts/wcag_audit.py site/ --pages 20 --out audit.md
```

## Testing

Run each suite from the repository root:

```bash
(cd rfc3339-ixdtf && python3 -m unittest discover -s scripts)
(cd iso999 && python3 -m unittest discover -s scripts)
(cd ste100 && python3 -m unittest discover -s scripts \
  && python3 -m unittest tools/test_build_dictionary.py \
  && python3 -m unittest discover -s evals/regression)
(cd wcag22-a11y && python3 -m unittest discover -s scripts -p "test_*.py" \
  && node --test scripts/test_wcag_page.mjs)
```

Tests that need material not in this repository (the local ASD-STE100
dictionary, excluded eval fixtures, third-party checkouts, or the wcag22-a11y
page runner before `setup_page_runner.sh` has run) are skipped.

## Licensing

- The code and documentation in this repository are licensed under the MIT
  License (see `LICENSE`).
- Excerpts of RFC 3339 and RFC 9557 in `rfc3339-ixdtf/references/` are used
  under the IETF Trust Legal Provisions (BCP 78).
- WCAG 2.2, Understanding WCAG 2.2 and WAI-ARIA 1.2 text quoted in
  `wcag22-a11y/references/` is used under the W3C Document License, with
  attribution in `wcag22-a11y/NOTICE`.
- Third-party pages and text used as test baselines keep their own licences.
  See `NOTICE`.
- `iso999` and `ste100` are tool-only editions. They contain no text,
  paraphrase, or data from ISO 999 or ASD-STE100, because both
  specifications are copyrighted and ISO 999 is licensed per user. Each
  edition's `README.md` lists what is not included and why.
