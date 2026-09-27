# AGB Agent Skills

Claude Code skills (Agent Skills format) that audit documentation and code
against published standards: Internet timestamp formats, back-of-book
indexes, and Simplified Technical English. Each skill ships a
`SKILL.md`, standard-library Python tools, and a test suite.

| Skill | What it checks | Edition | Key tools |
|---|---|---|---|
| [`rfc3339-ixdtf`](rfc3339-ixdtf/) | Code, schemas and APIs that parse, validate or emit RFC 3339 timestamps and RFC 9557 (IXDTF) suffixes | Full | `scripts/rfcdt.py` (checker and risky-API scanner), `scripts/run_vectors.py` (conformance vectors), `vectors/vectors.json` |
| [`iso999`](iso999/) | Back-of-book indexes, index-generating code, and index markup against ISO 999:1996 | Tool-only | `scripts/iso999_lint.py` (generated index output), `scripts/iso999_markup.py` (index markup in sources) |
| [`ste100`](ste100/) | Technical documentation against ASD-STE100 Simplified Technical English, Issue 9 | Tool-only | `scripts/ste_check.py` (checker), `tools/build_dictionary.py` (builds the local dictionary) |

## Installation

Clone the repository, then link or copy each skill folder into
`~/.claude/skills/<name>`:

```bash
git clone https://github.com/AtomicGaryBusey/AGB-Agent-Skills.git
cd AGB-Agent-Skills
mkdir -p ~/.claude/skills
for s in rfc3339-ixdtf iso999 ste100; do ln -s "$PWD/$s" ~/.claude/skills/$s; done
# or: cp -R rfc3339-ixdtf iso999 ste100 ~/.claude/skills/
```

Prerequisites:

- All skills: Python 3.9 or later (standard library only).
- `ste100`: poppler's `pdftotext` (`brew install poppler` or
  `apt install poppler-utils`), and your own download of the ASD-STE100
  specification, built into a local dictionary:
  `python3 ~/.claude/skills/ste100/tools/build_dictionary.py --download`.
  Without the dictionary, the vocabulary checks do not run.
- `iso999`: your own licensed copy of ISO 999:1996 to interpret findings.

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
```

## Testing

Run each suite from the repository root:

```bash
(cd rfc3339-ixdtf && python3 -m unittest discover -s scripts)
(cd iso999 && python3 -m unittest discover -s scripts)
(cd ste100 && python3 -m unittest discover -s scripts \
  && python3 -m unittest tools/test_build_dictionary.py \
  && python3 -m unittest discover -s evals/regression)
```

Tests that need material not in this repository (the local ASD-STE100
dictionary, excluded eval fixtures, or third-party checkouts) are skipped.

## Licensing

- The code and documentation in this repository are licensed under the MIT
  License (see `LICENSE`).
- Excerpts of RFC 3339 and RFC 9557 in `rfc3339-ixdtf/references/` are used
  under the IETF Trust Legal Provisions (BCP 78).
- Third-party pages and text used as test baselines keep their own licences.
  See `NOTICE`.
- `iso999` and `ste100` are tool-only editions. They contain no text,
  paraphrase, or data from ISO 999 or ASD-STE100, because both
  specifications are copyrighted and ISO 999 is licensed per user. Each
  edition's `README.md` lists what is not included and why.
