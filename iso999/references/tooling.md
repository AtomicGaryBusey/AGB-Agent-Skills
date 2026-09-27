# Tooling reference

Standard-library Python 3 tools in `scripts/`. Both are heuristic: every
finding is a prompt for review, to be confirmed against the index or source
before it goes in a report. Exit status for both: 0 no warnings, 1 warnings,
2 usage, read or parse error. `--list-rules` prints rule ID, clause and
severity; `--json` gives machine-readable output.

## `scripts/iso999_lint.py` (0.3.0): generated index output

```bash
python3 scripts/iso999_lint.py <index-file|-> [--format auto|text|ind|html] \
    [--filing word|letter|identifier] [--numerals numeric|ignore] [--ignore-function-words] \
    [--inversion before|after] [--roman strict|off] [--roman-list FILE] \
    [--subheading-order alpha|page] [--locale-fold none|basic] [--max-locators N] \
    [--locators numeric|anchor|none|auto] [--sections split|merge] [--heading-regex REGEX] \
    [--case-significant|--no-case-significant] [--only-section REGEX] \
    [--qualifier-suffix LIST] [--compare-locales L1,L2] [--ignore-honorifics] \
    [--skip-until REGEX | --no-auto-preamble] [--verbose-pairs] [--dump-tree] \
    [--min-severity info|warn] [--json]
```

**Check the parse first.** If the run reports `ISO999-PARSE-HEALTH` (many
entries with nothing to point to, headings ending in a digit or full stop,
suspected turnover lines), inspect `--dump-tree` (parsed entry tree as JSON)
and fix the flags before trusting any other finding.

What it checks: filing order (§8.1–8.3, 8.5–8.6), locator order, duplicates
and ranges (§7.4.3), locator separators and numbering sequences
(§7.4.2.2.1), special-matter markers (§7.4.4), long locator strings
(§7.2.3.5), heading/locator separation (§7.4.5), cross-reference integrity,
separators and placement (§7.5), reference text in the sort key (§8.7),
two-alphabet case sorts (§8.1), near-duplicate headings (§8.1, §7.2.2.2,
§7.3.1.1), article, abbreviation and initialism handling (§7.3.4.2, §7.3.6),
text indentation and turnover lines (§9.1.2.4, §9.4.1.4) and run-on
punctuation (§9.5). It cannot see false ranges, inconsistent inversion,
missing synonym cross-references or coverage gaps.

### Input parsing

- **Text / Markdown:** a closing full stop is punctuation, not part of the
  last locator; repeated-heading dashes ("—, of x") are subheadings, depth by
  dash count; lower-case continuation lines (turnovers) and locator-only
  lines after a trailing comma are joined; run-on entries (§9.5,
  "heading, 4; sub, 12; sub, 8", also "lead: sub 7; sub 9" and a
  parenthesised third level "sub 33 (a 33; b 40)") become heading +
  subheadings; an "Index" caption is not an entry. Explicit heading lines
  (a Markdown heading of 2+ characters, or a caption such as "INDEX OF
  NAMES") start sections; with 2+ of them each is linted as its own
  sequence (`--sections merge` turns this off). A leading introductory note is detected and
  skipped (`ISO999-7.1.3-NOTE`); `--skip-until REGEX` sets where entries
  start, `--no-auto-preamble` turns detection off.
- **HTML:** nested `<ul>/<ol>/<dl>` lists (including sibling `<li><ul>`),
  `<p>`/`<br>` indexes (depth from Word `MsoIndex1-3` or LibreOffice
  `Index_20_1` classes, else margin rank), and `<table>` layouts. Site chrome
  and inline badges are skipped; h1–h4 and kind ids split sequences.
- **LaTeX `.ind`:** including hyperref's `\hyperindexformat` wrappers.
- **Locator forms:** `2:45`, `2/45`, `II.45`, `II:45` (volume prefixes),
  `A3` (letter prefix), `22f`/`31t` (suffixes), `12 (map)`. Read only as a
  comma-separated token, never after one space: `A-3`, `A.3` and
  `fig. 3`/`table 4` (a figure or table number, kept out of ascending and
  overlap checks). Emphasis is typed: bold (`**12**`, `<b>`, `\textbf`),
  italic (`*12*`, `<i>`, `\textit`), bracket (`[12]`).
- Known limits: a heading ending in a bare number ("Apollo 11" in a
  single-space-separated index) may be read as heading + locator (the
  separator style is chosen by majority vote); full locale tailoring (e.g.
  Swedish å after z) needs an external collator.

### Flags

- `--filing word|letter|identifier`: match the declared method. If none is declared, let
  `ISO999-8.2-MODE` report the apparent method, then check consistency.
  `identifier` splits code names at `_`, `::`, case humps, acronym ends and
  digit runs (an assumption to declare) and turns on `--case-significant`
  (case-only pairs are distinct: `ISO999-3.10-HOMOGRAPH`, info);
  `--no-case-significant` turns it off.
- `--inversion before|after` (default `after`): where "term, x" files
  relative to "term (x)" (§8.5 does not decide it; match the index).
- `--roman strict|off` (default `strict`): a leading roman numeral is a
  number only when listed in `--roman-list FILE` or followed by a counting
  noun, so acronyms file as letters (§7.3.6).
- `--subheading-order page`: only when the introductory note declares page
  order; otherwise 3+ page-order subheadings are `ISO999-8.6-PAGEORDER`.
- `--locale-fold basic|none` (default `basic`): fold case and common
  diacritics for §8.1.
- `--max-locators N` (default 6): threshold for `ISO999-7.2.3.5-MAXLOC`;
  report it.
- `--ignore-honorifics`: file "Surname, Mr. X." as "Surname, X.". Without
  it, a pair in order only when honorifics are ignored is
  `ISO999-7.3.1-HONORIFIC` (info), not an order finding.
- `--verbose-pairs`: keep the per-pair order findings that an
  `ISO999-8-ROOTCAUSE` summary replaces (as info), and rules repeated 10+
  times.
- Generated/API indexes: `--locators
  numeric|anchor|none|auto`, `--sections split|merge`, `--heading-regex
  REGEX`, `--qualifier-suffix LIST`, `--compare-locales L1,L2`.
- `--only-section REGEX` (case-insensitive): HTML, the h1–h4 or kind-id
  sections whose label matches; text, the explicit-heading sections
  ("INDEX OF PLACES", "## Index of names") or single-letter groups
  (`'^B$'`) whose label matches. No match is exit 2. `.ind` input has no
  sections.

### Rule IDs added in 0.3.0

- `ISO999-8-ROOTCAUSE` (warn): most order findings are explained by one other
  sort key (code point, lower-cased code point, case-sensitive, or the other
  filing method). One summary replaces the pairs: report it as one finding.
- `ISO999-7.3.4.2-ARTICLE` (warn): a leading article kept in front in some
  headings and moved to the end in others (§7.3.4.2 is a hard requirement).
- `ISO999-7.3.6-ABBREV` (warn): an abbreviation filed as if spelled out or
  run into the next word, not as written.
- `ISO999-7.3.6-VARIANT` (info): abbreviated and spelled-out forms both used
  (St/Saint, Mc/Mac, Dr/Doctor, &/and).
- `ISO999-7.3.1-HONORIFIC` (info): see `--ignore-honorifics`.
- `ISO999-PARSE-HEALTH` (info): the layout was probably misread.

### Rule IDs added after 0.3.0 (FIN-ISO; version string unchanged)

- `ISO999-7.4.2-LOCSEP` (warn, §7.4.2.2.1; check 7.4-03): a heading ends in
  page numbers separated by spaces or semicolons ("glaciers 14 22 90",
  "kelp, 4; 12"). Spaces count only with 2+ numbers left in the heading, 3+
  in all, in ascending order, so "Route 66" stays a heading. 10+ become one
  summary.
- `ISO999-7.4.2-SEQUENCE` (warn, 7.4-04): 2+ locators carry a volume/part
  prefix and others are bare arabic numbers. Appendix letters (A3) and
  roman front matter beside an unprefixed body are distinct already and
  pass.
- `ISO999-7.4.2-PREFIX` (warn, 7.4-04): volume prefixes in 2+ notations
  (`2:45` and `II.45`), or letter prefixes with 2+ separators (`A3` and
  `A-3`). Volume and letter prefixes are compared only within their own
  kind.
- `ISO999-7.4.2-SEQORDER` (info, 7.4-04 with 7.4-15): a roman front-matter
  locator after an arabic one in an entry. Replaces ASCENDING when that is
  the only disorder, and says when the roman locator sits among the arabic
  ones by value (a sort that dropped the sequence). Info because §7.4 only
  illustrates the order.
- `ISO999-7.4.4-SPECIAL` (info = Advisory, 7.4-17): locators marked in 2+
  of these ways: marker word (`fig. 3`, `12 (map)`), letter suffix
  (f t i m p), italics, brackets. Bold is taken as the principal-locator
  mark (7.4-16) and not counted. If italics mark the principal locator in
  the audited index, discard the finding.
- `ISO999-9.1.2.4-INDENT` (warn, text only, 9.1.2.4-01): one level set at
  2+ indents. Markdown bullets and dash-repeated lines are not measured.
- `ISO999-9.4.1.4-TURNOVER` (warn, text only, 9.4.1.4-01): turnover lines
  that the parser joined (a lower-case continuation, or a locator line
  after a trailing comma) sit at or left of the deepest indent used. One
  finding per index, because the wrap routine is the cause.
- `ISO999-9.5-RUNON` (warn, 9.5-02): in run-on lines (all `;` parts after
  the first contain words), one finding for each kind of fault: a colon
  after a lead that has locators; a lead without locators followed by `;`
  (only with 2+ run-on lines, so a prose semicolon in a set-out index is
  ignored); a comma between siblings after a locator; unbalanced
  parentheses.
- Coverage added to existing IDs: `ISO999-7.3.4.2-ARTICLE` now also
  replaces an ORDER finding when a front article is ignored in filing
  ("The Orchard" among the O's). It gives one extra warn when some front
  articles are filed on the article and some ignoring it, and one info
  when every one is ignored (French practice, consistent).
  `ISO999-7.3.6-ABBREV` now also covers initialisms filed by their
  punctuation ("N.A.T.O." ahead of every N word, or "U N" filed as "UN").

### Why 3-subheading groups stay PAGEORDER (T3-9)

A group of 3 subheadings that is not alphabetical but is in page order is
still `ISO999-8.6-PAGEORDER`, not `ISO999-8.6-RUNS`, on purpose. Of the 6
possible orders of 3 items, 4 split into exactly 2 alphabetical runs, so at
n = 3 a run structure is what chance gives and is no evidence of merged
sources. Page order has a 1 in 6 chance, which makes it the more specific
explanation. RUNS keeps its threshold (runs averaging 2+ entries, at most
one single-entry run), which a 3-item group cannot meet. No other rule was
found that could be tested without also flagging chance orders.

### Objective checks still not automated

- 7.4-03, a mix of comma and non-comma separators across one index, is
  covered only when the non-comma separators leave page numbers in a
  heading. Per-level separator settings in code (makeindex `delim_n`) are
  for code review.
- 7.4-04, "same bare number from two sequences" when no locator in the
  index has a prefix: the index text alone cannot show that the work has
  several volumes.
- 7.4-17, "one letter used for two meanings" and "letters not explained in
  the note": this needs the meaning of each letter. Letter prefixes (A3,
  T4) are ambiguous between appendix sequences and special matter, so they
  are not counted.
- 9.1.2.4-01 and 9.4.1.4-01 in HTML or PDF: this needs the rendered
  x-offsets (CSS `text-indent`), and the linter does not render. In text,
  a turnover set exactly at a subheading column in a lower-case index
  cannot be told apart from a subheading.
- 9.5-02, a third level that is not in parentheses, or parentheses that
  hold the wrong level: a flat run-on line does not show which level was
  intended.

Earlier additions still in use: `ISO999-8.1-CASE-ORDER`, `ISO999-8-DISPLACED`,
`ISO999-8.6-RUNS`, `ISO999-7.4-ANCHOR`, `ISO999-3.10-HOMOGRAPH`,
`ISO999-8.1-LOCALE`.

## `scripts/iso999_markup.py`: index markup in doc sources

```bash
python3 scripts/iso999_markup.py <files|dirs> [--format auto|latex|idx|rst|dita|custom] \
    [--entry-regex REGEX] [--xref-sep SEP] [--target-sep SEP] [--ext EXT] \
    [--entries] [--min-severity info|warn] [--json]
```

- Formats: `latex` (`\index{}`, makeindex `!`/`@`/`|see{}`/`|(`…`|)`),
  `idx` (makeindex `.idx`), `rst` (Sphinx `.. index::` and `:index:`),
  `dita` (`<indexterm>`, `<index-see>`, `<index-sort-as>`, start/end ranges),
  `custom` (any inline syntax), `auto` (by extension; the default).
- `custom`: `--entry-regex` needs a named group `body` and may have `kind`
  (`see`/`seealso` make the body `SOURCE<xref-sep>TARGETS`; anything else is
  an entry in makeindex-lite syntax). `--xref-sep` defaults to `|`,
  `--target-sep` to `,`; `--ext` limits the extensions walked.
- Rules (`--list-rules`): singular/plural variants (§7.2.2.2), initials vs
  full forenames (§7.3.1.1), inconsistent inversion (§6.3, §7.2.2.4),
  case-only variants (§6.3), missing sort-as keys for symbol- or
  numeral-initial headings (§8.1, §8.3), dangling, chained, looping and self
  cross-references (§7.5), a *see* heading with locators (§3.13), unclosed or
  stray ranges (§7.4.3.1), `MARKUP-PARSE`. Pairs already linked by a
  cross-reference are not reported.
- Files not available locally are skipped and counted.
- `--entries` lists every extracted entry: use it to confirm a finding.

Example for inline `{{index: …}}` / `{{see: …}}` / `{{seealso: …}}` markup
in Markdown sources:

```bash
python3 scripts/iso999_markup.py docs/ --format custom \
    --entry-regex '\{\{\s*(?P<kind>index|see|seealso)\s*:\s*(?P<body>.*?)\s*\}\}'
```

## Golden corpus and evals

- `evals/golden/golden.json` pins the linter's finding counts, per rule and
  severity, on real and self-built indexes (a public-domain book index as
  text and HTML, a Sphinx `genindex.html`, a hyperref/xindy `.ind`).
  `python3 -m unittest discover -s scripts` fails when a count changes. After
  an intended change, regenerate with
  `python3 scripts/test_iso999_lint.py --update-golden` and review the diff.
- `evals/baselines/api-audits/` holds worked audits of the Go, Rust and
  ServiceNow documentation indexes, with their converters and inputs. An
  audit never needs `evals/`.
