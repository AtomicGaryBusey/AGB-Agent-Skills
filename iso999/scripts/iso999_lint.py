#!/usr/bin/env python3
"""iso999_lint.py - heuristic linter for GENERATED back-of-book index output.

Checks a finished index (plain text / Markdown, LaTeX ``.ind`` from makeindex
or xindy, or an HTML ``<ul>``/``<dl>`` index - including generated API
listings such as rustdoc 'all items' or pkgsite package indexes, and
heading-only lists such as CLI topic lists) against a subset of the
guidance in ISO 999:1996 (Information and documentation - Guidelines for the
content, organization and presentation of indexes).

IMPORTANT CAVEATS
-----------------
* This is a HEURISTIC tool. It parses loosely structured text and will
  sometimes misread a heading as a locator or vice versa. Treat every finding
  as a prompt for human review, not as a verdict.
* ISO 999 is a set of GUIDELINES. Most of its provisions are "should", and it
  explicitly treats its examples and punctuation as illustrative. Where the
  standard offers alternatives (for example word-by-word vs letter-by-letter
  filing), the linter checks that ONE method is applied CONSISTENTLY; it does
  not claim one is mandatory. Severity ``warn`` means "probably inconsistent
  or likely to mislead a reader"; ``info`` means "worth a look".
* No text of the standard is reproduced here; rule messages are paraphrases.

FILING-RULE INTERPRETATION CHOICES (clauses 8.1-8.7)
----------------------------------------------------
Sort keys are built as follows (these are the linter's choices, stated so that
a reviewer can disagree with them):

* Case: upper and lower case file identically (8.1).
* Diacritics (``--locale-fold``): ``basic`` (default) folds modified letters
  to their base letter (e.g. an umlauted o files as o; ae/oe ligatures
  expand; sharp s -> ss). ``none`` only case-folds, so accented letters sort
  by code point, after z. ISO 999 leaves this to local practice. Full locale
  tailoring (e.g. Swedish å filed after z) needs a collator such as ICU,
  which this standard-library tool does not ship.
* Punctuation such as apostrophes, periods, quotation marks, asterisks,
  underscores (Markdown emphasis) and ampersands gets a null filing value.
* Word-by-word (default, ``--filing word``): a space files before any letter
  or digit. Hyphens, en/em dashes and slashes are treated as spaces.
* Letter-by-letter (``--filing letter``): spaces, hyphens, dashes and slashes
  are ignored (8.2).
* Same first term (8.5): the standard names three classes - the bare term
  (with or without subheadings), the term with a qualifier, and the term as
  the first element of a longer term - and says nothing about an inverted
  "term, x". ``--inversion after`` (default) treats "term, x" as heading the
  longer-term class: bare term < term (qualifier) < term, x < term x...
  ``--inversion before`` gives: bare term < term, x < term (qualifier) <
  term x... Neither choice is reported as a finding; a mix of the two cannot
  be told apart from a genuine misfiling, so the flag is simply applied. In
  both filing modes the comma and opening parenthesis act as terminators;
  that is a common convention the standard does not spell out.
* Numerals (8.3), default ``--numerals numeric``: this linter reads 8.3 a) as
  "headings that begin with a numeral form one group placed before the
  alphabetical sequence, ordered by numeric value". Digits inside a heading
  (8.3 d) compare by numeric value and file before letters, so "Route 9" <
  "Route 66" < "Route one". ``--numerals ignore`` excludes numeral-initial
  headings from order checks (use it when numerals are filed as if spelled
  out, 8.3 b, or when chemical locant prefixes are disregarded, 8.3 c -
  neither can be checked mechanically).
* Roman numerals (``--roman``): upper-case strings such as CD, DC, MIX, DIV,
  CV or VI are far more often abbreviations than numbers, and abbreviations
  file as written (7.3.6). In ``strict`` mode (default) a leading upper-case
  roman numeral of 2+ letters interfiles with arabic numerals only when it
  is the whole first token AND either the next word is a counting noun from
  ROMAN_CONTEXT_WORDS (century, dynasty, congress, olympiad ...) or the
  numeral is listed in ``--roman-list FILE``. Everything else files as
  letters. ``off`` never reads a heading-initial roman numeral as a number.
  Lower-case roman numerals are only recognised as locators.
* Cross-references never affect the filing position of a heading (8.7); they
  are removed before sort keys are built.
* Subheadings (8.6) are checked with the same rules. A group that is not
  alphabetical but is in ascending numeric/date order is reported as
  ``info`` (SYSTEMATIC). A group of 3+ subheadings in page (first-locator)
  order but not alphabetical is a ``warn`` (PAGEORDER): it is more often an
  unsorted dump than a deliberate arrangement. ``--subheading-order page``
  declares page order as the systematic arrangement and downgrades it to
  ``info``. Leading prepositions/conjunctions (never articles) in
  subheadings are significant unless ``--ignore-function-words`` is given
  (8.6 lets an index ignore them if it does so throughout).

PARSING CHOICES
---------------
* Heading/locator boundary (7.4.5 allows a comma, two spaces or another
  unambiguous mark). A comma or two spaces/tab always separates. A trailing
  locator run after ONE space ("kelp 12, 30") is read as locators when the
  run is a comma list or a range, or - for a single bare number such as
  "kelp 12" - when most lines in the index use the one-space style. When
  most lines use a comma or two spaces, a number after one space stays in
  the heading ("Route 66, 12" = heading "Route 66"). A number directly
  after a word such as "volumes", "part" or "no." is kept in the heading.
  A lower-case roman token after one space ("preface iv, vii") is peeled
  only in a one-space index, before a comma list, and only with 2+ letters,
  so "vitamin c" keeps its letter. Known ambiguity that remains: a heading
  ending in ", <number>" (a place and a year, say "Oslo, 1952") is always
  read as a heading plus a locator.
* Qualified cross-references (7.5.3): a reference limited to some volumes,
  issues or dates - "see also quills for entries up to 1850", "(for
  references before 1990)", or a heading like "quills in later issues see
  pens" - has the qualifier stripped before the target is resolved. Such a
  conditional 'see' is not treated as a redirect, so it never produces
  CHAIN or CYCLE findings, and a qualified heading also resolves under its
  bare term.

* Introductory note (text input only; 7.1.3, 9.2): paragraphs at the top of
  the file that read as prose (8+ words, 5+ words per line, a sentence end,
  most lines without a locator tail) are skipped, with a lone short caption
  just before them, up to the first single-letter group header or the first
  entry-like paragraph. An info NOTE finding reports the skipped lines.
  ``--skip-until REGEX`` skips everything before the first matching line
  instead; ``--no-auto-preamble`` turns detection off.

ATTRIBUTION AND EXTRA CHECKS
----------------------------
* A misordered pair whose sort keys first differ at a digit run is reported
  as 8.3-ORDER (8.3 d), even when the headings share a first word.
* 8.7-SORTKEY: a pair out of order by bare heading that would be in order if
  one heading's 'see'/'see also' text were part of its key - the reference
  has leaked into the sort key. Reported instead of the ORDER finding.
* 8.1-CASEBLOCK: a single-letter group header repeated, or a capitalised
  A-Z run followed by a lower-case run restarting the alphabet (the mark of
  a case-sensitive sort). One finding; the ORDER finding at the restart is
  suppressed.
* 7.5-SEPARATOR: a cross-reference target that is not a heading, but whose
  comma-separated parts all are, is several targets joined by commas; the
  parts are then checked for TARGETORDER instead of reporting DANGLING.
* 7.4.5-SEPARATOR: in an index that separates locators by one space, each
  heading ending in a digit is a warning (the boundary is ambiguous);
  otherwise one info notes that the style is legal only while unambiguous.
* 7.5.2.1-PLACEMENT: 'see also' consistently before locators is one info
  (the standard places it after, except in card, screen or very detailed
  indexes); inconsistent placement stays a warning.
* 7.2.2.2-NUMBER (info): sibling headings that differ only by a simple
  English plural (-s, -es, -ies/-y) when neither has a parenthetical
  qualifier and neither refers to the other.
* 7.3.1.1-VARIANT (info): 'Surname, Forenames' and 'Surname, Initials'
  where each initial matches the corresponding forename.

LOCATORS (``--locators``)
-------------------------
* ``auto`` (default): numeric page locators as above; an entry with none
  falls back to its link hrefs (HTML) or a trailing '#frag' / URL /
  '.html' token or TAB column (text).
* ``numeric``: page locators only (the v1 behaviour).
* ``anchor``: the locator is an href, URL or '#fragment'. HTML: link text
  at the end of an item ('abacus, 4, 9' where 4 and 9 are links) is peeled
  off; otherwise the links in the heading (typically the whole heading is
  a link) are its locators. Text: 'heading<TAB>locator' or a trailing
  anchor token. Nothing else is split off, so signatures with commas stay
  in the heading. Order, range and elision checks skip anchor locators.
  7.4-ANCHOR: an in-document '#frag' that names no id in the same file.
* ``none``: the heading is its own locator/retrieval key (CLI topic
  lists, title lists). Nothing is split off; a trailing '[gloss]' or TAB
  column is dropped. 'see also' with no locators is not NOREFS here.

HTML STRUCTURE
--------------
* ``<nav>``, ``<header>``, ``<footer>``, ``<aside>``, ``<script>``,
  ``<style>``, ``<template>`` are site chrome and are not read.
* A sibling ``<li>`` that only wraps a nested list files its items as
  subheadings of the preceding item (API-page pattern: a type, then its
  constructors and methods in two wrapper lists).
* ``--sections split`` (default): an ``<h1>``-``<h4>`` outside a list item,
  or an element whose id is an API-listing kind (structs, functions ...),
  starts a new sequence. Ordering, duplicate and near-duplicate checks run
  per sequence and findings carry '[Section]'; locator and cross-reference
  checks run over the whole file. A single-letter heading is a letter-group
  header, not a section. ``--sections merge`` lints one sequence;
  ``--only-section REGEX`` keeps matching sections only (text input: see
  'Text sections' below).
* Items that share a source line (minified HTML) are reported as
  ``line:col``.

IDENTIFIER FILING AND IDENTITY
------------------------------
* ``--filing identifier``: identifiers are segmented into words at
  camelCase humps, acronym runs (HTTPServer -> HTTP Server), digit runs,
  ``::``, ``_``, ``.``, ``-`` and ``/`` (so ``_`` and ``.`` are word breaks,
  not null), then filed word-by-word, case-folded, accents folded per
  ``--locale-fold``, digit runs by value. The raw string is the final
  tie-break, so the order is total; a pair that differs only in that
  tie-break (case variants) is not reported as misordered.
* ``--heading-regex REGEX``: group 1 is the filing text (e.g. the name in
  a display heading 'func (r Recv) Name(args) result'); the rest is noise
  or a leading qualifier. ``--qualifier-suffix LIST``: 'term-guide' files
  as 'term (guide)' (8.5).
* ``--case-significant`` (on with identifier filing): headings whose keys
  are equal but whose text differs (case, separators) are distinct
  identifiers - info 3.10-HOMOGRAPH instead of warn 8.1-DUPLICATE.

ORDER ATTRIBUTION (v2)
----------------------
For each misordered adjacent pair, first match wins: 8.7-SORTKEY (leaked
reference text); 8.3-ORDER (numeral group, or first difference at a digit
run); 8.1-CASE-ORDER (out of order once case is folded with accents left
alone, but in order under a case-sensitive code-point comparison);
8.5-ORDER (one term - the text before '(' or an inverting comma - equals
or is a leading word run of the other's: bare / qualified / inverted /
longer); 8.6-ORDER (subheadings); else 8.2-ORDER.
* Per-pair findings that fall in one block of consecutive out-of-place
  entries are collapsed into one finding naming the block size.
* 8-DISPLACED (info, per sequence): entries minus the longest
  non-decreasing subsequence under the active key, with the first 20
  displaced entries and a count of displaced subheadings.
* 8.6-RUNS (warn): a subheading group that restarts the alphabet (ignoring
  case-caused breaks) into 2+ runs averaging 2+ entries, with at most one
  single-entry run. Replaces PAGEORDER; PAGEORDER remains for page-ordered
  groups without such a run structure. Anchor locators give page order
  only when their '#frag' target position is known.
* ``--compare-locales L1,L2``: re-sort each sequence's top-level headings
  with ``locale.strxfrm`` under each locale (unavailable ones are skipped
  and named) and report 8.1-LOCALE (info) for entries whose relative
  position changes - evidence that output collated with a default locale
  is not predictable across machines.

LAYOUTS AND SUMMARIES (v3)
--------------------------
* A full stop that closes an entry ("kelp, 3, 3.") is punctuation, not
  part of the last locator; "Lyell, Sir C." and "etc." keep theirs.
* A heading whose first token is made only of symbols ('!=', '*', '**',
  '# (hash)') files by code point in a symbols group ahead of numerals and
  letters (the linter's choice). Symbols attached to a word ("'Tis",
  '--verbose') keep a null value (8.1).
* Text layouts: repeated-heading dashes ("—, of x" = subheading of the
  heading above; the depth is the number of dash units over the smallest
  run used, so "——"/"————" give depths 1/2); a lower-case line after an
  open heading (no locators, no final punctuation) is a turnover and is
  joined - flush-left in an index of capitalised or dash-repeated
  headings, or deeper-indented when the open line is long and the
  continuation would otherwise be its only subheading; a line of
  locators after a trailing comma is joined; run-on entries (9.5: "kelp,
  4; drying, 12; zinc in, 8") become a heading and subheadings; an
  "INDEX." / "Index" caption is not an entry.
* HTML without list items: a <p>/<br> index (Gutenberg; Word
  p.MsoIndex1-3; LibreOffice margins) is read line by line, from the
  heading "Index" onwards if there is one; depth comes from the index
  class, else the rank of margin-left/padding-left, plus leading no-break
  spaces. Failing that, a <table>: the first cell of each row is the
  heading (its first link's text) and its links are the locators; a
  class containing 'sub'/'child' makes a subheading.
* HTML chrome: elements with role navigation/search/banner/contentinfo,
  class sphinxsidebar/related, <search>, <dialog>, and inline badges
  (class containing 'badge'/'deprecated') are skipped. A 'Symbols' or '_'
  section ends at the next letter-group header. In ``--locators auto`` an
  item whose heading is itself link text is read in anchor mode
  ('Route 66' keeps its number).
* LaTeX: hyperref's \\hyperindexformat{\\see{x}}{n} and
  \\hyperindexformat{\\textbf}{n} are unwrapped.
* 8-ROOTCAUSE (warn): when 4+ per-pair order findings exist and at least
  60% of them are in order under one other key - lower-cased code point,
  code point, case-sensitive, or the other of word/letter filing - one
  summary names the key, the count per rule and examples; the pairs (and
  RUNS/PAGEORDER groups in order under that key) are dropped, or kept as
  info with ``--verbose-pairs``. 8.6-ORDER findings are merged into one
  per subheading group. MAXLOC, NUMBER and non-identical DUPLICATE
  findings repeated 10+ times become one summary each.
* 7.3.4.2-ARTICLE (warn): initial articles kept in front ("The Tempest")
  and moved to the end ("Winter's Tale, The") in one index.
* 7.3.6-ABBREV (warn) replaces the ORDER finding when a misordered pair is
  explained by an initial abbreviation (St., Mt., Dr., Mc, M') filed as if
  spelled out or run into the next word; 7.3.6-VARIANT (info): the same
  heading abbreviated and spelled out (St/Saint, Mc/Mac, Dr/Doctor,
  &/and), or both 'St.' and 'Saint' (or 'Dr.' and 'Doctor') as first
  words.
* 7.3.1-HONORIFIC (info) replaces 8.5-ORDER when the pair is in order once
  honorifics after an inverting comma are ignored ('Forbes, Mr. D.' before
  'Forbes, E.'); ``--ignore-honorifics`` files that way outright.
* PARSE-HEALTH (info, clause 'tool'): the share of entries with nothing to
  point to, headings ending in a digit or full stop (numeric locators
  only), and suspected turnover lines, when high enough to suggest a
  misread layout. ``--dump-tree`` prints the parsed tree as JSON.

NUMBERING SEQUENCES, MARKERS AND LAYOUT (after 0.3.0)
-----------------------------------------------------
* Locator forms: '2:45' / '2/45' (arabic volume prefix), 'II.45' /
  'II:45' (roman volume prefix), 'A3' (letter prefix), and - only as a
  comma-separated token, never peeled off a heading after one space -
  'A-3' / 'A.3', 'fig. 3' / 'table 4' (a figure or table number: its own
  sequence, left out of ascending and overlap checks) and '12 (map)'.
  Markdown/HTML emphasis is typed: '**12**' / <b> / \\textbf bold, '*12*'
  / <i> / \\textit italic, '[12]' bracket.
* 7.4.2-LOCSEP (warn, 7.4.2.2.1): a heading that ends in page numbers
  separated by spaces or semicolons ('glaciers 14 22 90', 'kelp, 4; 12').
  Spaces count only for 2+ numbers in the heading, 3+ in all, ascending
  (so 'Route 66' and 'Airliner 747 400' stay headings).
* 7.4.2-SEQUENCE (warn): 2+ locators carry a volume prefix while others
  are bare arabic numbers. Letter prefixes (appendix A3) and roman front
  matter beside an unprefixed body are separate sequences and pass.
* 7.4.2-PREFIX (warn): volume prefixes in 2+ notations ('2:45' and
  'II.45'), or letter prefixes with 2+ separators ('A3' and 'A-3').
* 7.4.2-SEQORDER (info) replaces ASCENDING when the only disorder in an
  entry is a roman (front-matter) locator after an arabic one; the message
  says when the roman one sits among the arabic ones by value (sequence
  dropped by an integer sort).
* 7.4.4-SPECIAL (info, Advisory): special-matter marks of 2+ kinds among
  marker word, letter suffix (f t i m p; not n or a-d), italics and
  brackets. Bold is taken to mark the principal locator and is not
  counted; letter prefixes are not counted (they may be sequence
  prefixes).
* 9.1.2.4-INDENT (warn, text only): items at one level set at 2+ indents
  (Markdown bullets and dash-repeated lines are not measured).
* 9.4.1.4-TURNOVER (warn, text only): turnover lines that the reader
  joined (lower-case continuation, or a locator line after a trailing
  comma) at or left of the deepest indent used by any heading or
  subheading. One finding per index. A turnover set exactly at a
  subheading column in a lower-case index is indistinguishable from a
  subheading and is not seen.
* 9.5-RUNON (warn): in lines whose ';'-parts after the first all contain
  words: a colon after a lead with locators; a lead without locators
  followed by ';' (only with 2+ run-on lines); a comma between siblings
  after a locator; unbalanced parentheses. One finding per kind. Run-on
  parsing reads 'lead: first sub N; sub N' and a parenthesised third
  level 'sub N (a N; b N)'.
* 7.3.4.2-ARTICLE also covers filing: a pair in order only if a front
  article ('The Orchard' among the O's) is ignored is reported as
  ARTICLE, not ORDER. Front-article headings filed both on and ignoring
  the article give one extra warn; when every one ignores it (French
  practice) the pair findings become one info.
* 7.3.6-ABBREV also covers initialisms: 'N.A.T.O.' filed as separate
  letters (ahead of every N word) or 'U N' filed as one word.
* Text sections: an explicit heading line - a Markdown heading of 2+
  characters ('## Index of places') or an index caption ('INDEX OF
  NAMES') - starts a section. With 2+ sections, ``--sections split``
  (default) lints each as its own sequence, as for HTML. ``--only-section
  REGEX`` keeps the sections, or single-letter groups ('^B$'), whose label
  matches.
* 8.6 PAGEORDER vs RUNS for a 3-subheading group: unchanged on purpose.
  4 of the 6 orders of 3 items split into exactly 2 alphabetical runs, so
  a run structure is no evidence at n=3; page order (1 in 6 by chance) is
  the more specific explanation and is kept.

LOCATOR SEVERITIES
------------------
* ASCENDING is ``info``: 7.4 only illustrates ascending order.
* DUPLICATE stays ``warn``: a locator given twice is an outright defect.

Exit status: 0 = no ``warn`` findings, 1 = at least one ``warn``,
2 = usage or parse error.

Python 3 standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, Iterable, List, Optional, Tuple

__version__ = "0.4.0"

# ---------------------------------------------------------------------------
# Rule catalogue: id -> (clause, default severity, short title)
# ---------------------------------------------------------------------------
RULES: Dict[str, Tuple[str, str, str]] = {
    "ISO999-7.1.3-NOTE": ("7.1.3; 9.2", "info",
        "Introductory note detected (or skipped) before the entries"),
    "ISO999-8.1-DUPLICATE": ("8.1", "warn",
        "Headings identical once case, spacing and diacritics are folded"),
    "ISO999-8.1-CASEBLOCK": ("8.1", "warn",
        "Two alphabets: letter groups repeat (case-sensitive sort)"),
    "ISO999-8.2-MODE": ("8.2", "info",
        "Filing method the index appears to use"),
    "ISO999-8.2-MIXED": ("8.2", "warn",
        "Evidence of both word-by-word and letter-by-letter filing"),
    "ISO999-8.2-ORDER": ("8.2", "warn",
        "Heading out of order under the chosen filing method"),
    "ISO999-8.3-ORDER": ("8.3", "warn",
        "Numeral out of numeric position (numeral-initial group, or digits "
        "inside a heading, 8.3 d)"),
    "ISO999-8.5-ORDER": ("8.5", "warn",
        "Headings sharing a first term not in term / qualifier / longer order"),
    "ISO999-8.7-SORTKEY": ("8.7", "warn",
        "Cross-reference text appears to have been filed as part of the key"),
    "ISO999-8.6-ORDER": ("8.6", "warn",
        "Subheading out of order within its heading"),
    "ISO999-8.6-SYSTEMATIC": ("8.6", "info",
        "Subheadings follow a numeric/date order, or a declared page order"),
    "ISO999-8.6-PAGEORDER": ("8.6", "warn",
        "3+ subheadings in page order, not alphabetical, and not declared"),
    "ISO999-7.2.3.5-MAXLOC": ("7.2.3.5; 7.4.3", "warn",
        "Long string of undifferentiated locators"),
    "ISO999-7.4.3-ASCENDING": ("7.4.3", "info",
        "Locators within an entry not in ascending order (convention only)"),
    "ISO999-7.4.3-DUPLICATE": ("7.4.3", "warn",
        "Same locator given more than once in an entry"),
    "ISO999-7.4.3-OVERLAP": ("7.4.3.1", "warn",
        "Locator range overlaps or contains another locator"),
    "ISO999-7.4.3.1-REVERSED": ("7.4.3.1", "warn",
        "Range whose end is not after its start"),
    "ISO999-7.4.3.1-DASH": ("7.4.3.1", "warn",
        "Range separator (hyphen / en dash / em dash) not used consistently"),
    "ISO999-7.4.3.1-ELISION": ("7.4.3.1", "warn",
        "Elided and full range forms mixed, or elision used at all (info)"),
    "ISO999-7.4.3.1-TEENS": ("7.4.3.1", "info",
        "Elided range in the 10-19 band of a hundred not kept at two digits"),
    "ISO999-7.4.3.1-OPEN": ("7.4.3.1", "warn",
        "Open-ended locator such as 'ff' or 'et seq.'"),
    "ISO999-7.4.3.2-PASSIM": ("7.4.3.2", "warn",
        "Use of 'passim' instead of listing each locator"),
    "ISO999-7.4.5-SEPARATOR": ("7.4.5", "warn",
        "Single-space heading/locator separator is ambiguous (info when "
        "it is not)"),
    "ISO999-7.2.2.2-NUMBER": ("7.2.2.2", "info",
        "Headings differing only by singular/plural form"),
    "ISO999-7.3.1.1-VARIANT": ("7.3.1.1", "info",
        "Same person under full forenames and under initials"),
    "ISO999-7.5-SEPARATOR": ("7.5.1; 7.5.2.1", "warn",
        "Several cross-reference targets separated by commas, not "
        "semicolons"),
    "ISO999-7.5.1-DANGLING": ("7.5.1", "warn",
        "'see' target is not a heading in the index"),
    "ISO999-7.5.2-DANGLING": ("7.5.2", "warn",
        "'see also' target is not a heading in the index"),
    "ISO999-7.5.1-LOCATORS": ("7.5.1", "warn",
        "'see' entry also carries locators or subheadings"),
    "ISO999-7.5.1-CHAIN": ("7.5.1", "warn",
        "'see' reference leads to another 'see' reference"),
    "ISO999-7.5.1-CYCLE": ("7.5.1", "warn",
        "'see' references form a loop"),
    "ISO999-7.5.1-FEW": ("7.5.1", "info",
        "'see' target has so few locators that a direct entry may be better"),
    "ISO999-7.5-SELF": ("7.5", "warn",
        "Cross-reference points to its own heading"),
    "ISO999-7.5-TARGETORDER": ("7.5.1; 7.5.2.1", "warn",
        "Multiple cross-reference targets not in alphabetical order"),
    "ISO999-7.5.2.1-PLACEMENT": ("7.5.2.1", "warn",
        "'see also' placed inconsistently (info: consistently before "
        "locators)"),
    "ISO999-7.5.2.1-SAMELOC": ("7.5.2.1", "warn",
        "'see also' sends the reader to identical locators"),
    "ISO999-7.5.2.1-NOREFS": ("7.5.2.1", "info",
        "'see also' on an entry with no locators or subheadings"),
    "ISO999-8.1-CASE-ORDER": ("8.1", "warn",
        "Pair out of order only because capitals were filed apart from "
        "lower case (case-sensitive sort)"),
    "ISO999-3.10-HOMOGRAPH": ("3.10", "info",
        "Distinct identifiers differing only by case or separators "
        "(case-significant mode)"),
    "ISO999-8-DISPLACED": ("8", "info",
        "Entries out of place in a sequence (n minus the longest in-order "
        "subsequence)"),
    "ISO999-8.6-RUNS": ("8.6", "warn",
        "Subheadings form 2+ alphabetical runs that restart without a "
        "label"),
    "ISO999-7.4-ANCHOR": ("7.4", "warn",
        "In-document #fragment locator does not resolve to an id in the "
        "same file"),
    "ISO999-8.1-LOCALE": ("8.1; 8.4", "info",
        "Entries whose relative order changes with the collation locale "
        "(--compare-locales)"),
    "ISO999-8-ROOTCAUSE": ("8.1; 8.4", "warn",
        "Most order findings are explained by one other sort key (code "
        "point, lower-cased code point, letter-by-letter, case-sensitive)"),
    "ISO999-7.3.4.2-ARTICLE": ("7.3.4.2", "warn",
        "Leading article kept in front in some headings and moved to the "
        "end in others, or a front article ignored in filing for some "
        "headings only"),
    "ISO999-7.3.6-ABBREV": ("7.3.6", "warn",
        "Abbreviation or initialism filed as if spelled out, run into the "
        "next word, or by its punctuation, not as written"),
    "ISO999-7.3.6-VARIANT": ("7.3.6", "info",
        "Abbreviated and spelled-out forms both used (St/Saint, Mc/Mac, "
        "Dr/Doctor, &/and)"),
    "ISO999-7.3.1-HONORIFIC": ("7.3.1", "info",
        "Inverted names in order only if honorifics are ignored "
        "(--ignore-honorifics)"),
    "ISO999-7.4.2-LOCSEP": ("7.4.2.2.1", "warn",
        "Page locators separated by spaces or semicolons, not commas"),
    "ISO999-7.4.2-SEQUENCE": ("7.4.2.2.1", "warn",
        "Some locators carry a volume/part prefix and others none"),
    "ISO999-7.4.2-PREFIX": ("7.4.2.2.1", "warn",
        "Sequence prefixes written in more than one notation (2:45 / "
        "II.45, A3 / A-3)"),
    "ISO999-7.4.2-SEQORDER": ("7.4.2.2.1; 7.4.3", "info",
        "Roman front-matter locator listed after arabic ones in an entry"),
    "ISO999-7.4.4-SPECIAL": ("7.4.4", "info",
        "Special-matter locators marked in more than one way (word, "
        "letter suffix, italics, brackets)"),
    "ISO999-9.1.2.4-INDENT": ("9.1.2.4", "warn",
        "Items at one level set at different indents (text layout)"),
    "ISO999-9.4.1.4-TURNOVER": ("9.1.2.4; 9.4.1.4", "warn",
        "Turnover lines not indented beyond the deepest subheading"),
    "ISO999-9.5-RUNON": ("9.5; 7.2.3.3", "warn",
        "Run-on punctuation inconsistent (colon after locators, ';' after a "
        "lead without locators, comma between siblings, unbalanced "
        "parentheses)"),
    "ISO999-PARSE-HEALTH": ("tool", "info",
        "Parse health: signs that the layout was misread (no locators, "
        "headings ending in digits, turnover lines)"),
}

# rustdoc / API-page section ids that start a new sequence (--sections)
KNOWN_SECTION_IDS = frozenset(
    "structs enums functions traits macros constants statics types unions "
    "primitives modules keywords attributes derives trait-aliases reexports "
    "variables foreign-types externcrates".split())

# 8.6 allows leading prepositions and conjunctions of subheadings to be
# ignored. Articles are NOT in this list: 8.6 does not extend the option to
# them.
FUNCTION_WORDS = frozenset(
    "of in on at for by with and or nor but to from as into onto upon "
    "during among between versus vs via under over about against".split())


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
class Pos(int):
    """A line number that may also carry a 1-based column.

    Minified HTML puts a whole index on one line; items that share a line
    get a column so that findings read ``1:2345`` instead of ``1``. It is
    an ``int`` for sorting and arithmetic; ``str()`` shows ``line:col``.
    """
    col: Optional[int]

    def __new__(cls, line: int, col: Optional[int] = None) -> "Pos":
        obj = int.__new__(cls, line)
        obj.col = col
        return obj

    def __str__(self) -> str:
        if self.col is None:
            return str(int(self))
        return f"{int(self)}:{self.col}"

    def __format__(self, spec: str) -> str:
        return format(str(self), spec)


def _pos_key(line: int) -> Tuple[int, int]:
    return int(line), (getattr(line, "col", None) or 0)


@dataclass
class Finding:
    rule: str
    line: int
    message: str
    severity: str = ""
    section: Optional[str] = None
    # internal: the misordered pair (previous, current heading) and the id
    # of its sibling group, used to find root causes and collapse groups
    pair: Optional[Tuple[str, str]] = field(default=None, repr=False,
                                            compare=False)
    group: Optional[int] = field(default=None, repr=False, compare=False)
    # internal: the headings of a subheading group (RUNS / PAGEORDER)
    members: Optional[tuple] = field(default=None, repr=False,
                                     compare=False)

    def __post_init__(self) -> None:
        if not self.severity:
            self.severity = RULES[self.rule][1]

    @property
    def clause(self) -> str:
        return RULES[self.rule][0]

    def as_dict(self) -> dict:
        d = {"rule": self.rule, "clause": self.clause,
             "severity": self.severity, "line": int(self.line),
             "message": self.message}
        col = getattr(self.line, "col", None)
        if col is not None:
            d["col"] = col
        if self.section is not None:
            d["section"] = self.section
        return d


@dataclass
class Locator:
    raw: str
    line: int
    start: int
    end: Optional[int] = None          # expanded end of a range
    roman: bool = False
    prefix: Optional[int] = None       # volume/part, e.g. "2:" in "2:15"
    suffix: str = ""                   # e.g. n for note
    tag: str = ""                      # e.g. T for table
    dash: Optional[str] = None         # 'hyphen' | 'en' | 'em'
    elided: Optional[bool] = None      # True elided, False full, None n/a
    teen_issue: bool = False
    open_ended: bool = False
    passim: bool = False
    emphasis: bool = False
    style: str = ""                    # bold | italic | bracket (emphasis)
    pstyle: str = ""                   # sequence prefix notation (7.4.2)
    marker: str = ""                   # special-matter word: fig, table ...
    wprefix: bool = False              # 'fig. 3': a figure number, not a page
    anchor: Optional[str] = None       # href / URL / #fragment locator
    target_pos: Optional[int] = None   # document order of the #fragment id

    @property
    def is_range(self) -> bool:
        return self.end is not None

    @property
    def numeric(self) -> bool:
        return self.anchor is None

    def order_key(self) -> tuple:
        if self.anchor is not None:
            return (-2, 0, self.target_pos if self.target_pos is not None
                    else -1, "", "")
        return (self.prefix if self.prefix is not None else -1,
                0 if self.roman else 1, self.start, self.suffix, self.tag)

    def identity(self) -> tuple:
        if self.anchor is not None:
            return ("anchor", self.anchor)
        return (self.prefix, self.roman, self.start, self.end,
                self.suffix, self.tag)

    def group(self) -> tuple:
        return (self.prefix, self.roman)


@dataclass
class CrossRef:
    target: str
    generic: bool = False   # italic/generic reference ("see also names of ...")


@dataclass
class Entry:
    heading: str
    level: int
    line: int
    locators: List[Locator] = field(default_factory=list)
    see: List[CrossRef] = field(default_factory=list)
    see_also: List[CrossRef] = field(default_factory=list)
    see_also_placement: Optional[str] = None   # before | after | sub | None
    children: List["Entry"] = field(default_factory=list)
    parent: Optional["Entry"] = None

    def path(self) -> str:
        if self.parent is None:
            return self.heading
        return self.parent.path() + ": " + self.heading


@dataclass
class ParsedLine:
    """Format-neutral result of parsing one logical index line."""
    level: int
    line: int
    heading: str
    locators: List[Locator]
    see: List[CrossRef]
    see_also: List[CrossRef]
    placement: Optional[str]
    see_line_only: bool = False   # the line is just a cross-reference
    sep_kind: Optional[str] = None  # heading/locator separator evidence
    section: Optional[str] = None   # section label (--sections)
    group: Optional[str] = None     # text: letter-group header in force


class ParseError(Exception):
    pass


# ---------------------------------------------------------------------------
# Text normalisation and sort keys
# ---------------------------------------------------------------------------
_SPECIAL_FOLD = {"ß": "ss", "æ": "ae", "Æ": "ae", "œ": "oe", "Œ": "oe",
                 "ø": "o", "Ø": "o", "ł": "l", "Ł": "l", "đ": "d", "Đ": "d",
                 "þ": "th", "Þ": "th", "ı": "i"}
_MARKUP_RE = re.compile(r"[*_`]")


def fold(text: str, locale_fold: str = "basic",
         keep_case: bool = False) -> str:
    """Case-fold and, in ``basic`` mode, strip diacritics (8.1).

    ``none`` only case-folds, so accented letters keep their own code points
    and sort after z. Neither mode is a real locale collation.
    ``keep_case`` skips the case fold (used only to test whether a
    misordered pair is explained by a case-sensitive sort).
    """
    if locale_fold == "none":
        t = unicodedata.normalize("NFC", text)
        return t if keep_case else t.casefold()
    text = "".join(_SPECIAL_FOLD.get(c, c) for c in text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text if keep_case else text.casefold()


_ID_BREAK_CHARS = "_.-/‐‑‒–—"


def segment_identifier(text: str) -> str:
    """Split a code identifier into words for ``--filing identifier``.

    Breaks at camelCase humps (fooBar -> foo Bar), at the end of an acronym
    run before a capitalised word (HTTPServer -> HTTP Server), around digit
    runs (Len16 -> Len 16), and at ``::``, ``_``, ``.``, ``-`` and ``/``.
    Parentheses and commas are kept, so qualifier structure survives.
    """
    s = text.replace("::", " ")
    out: List[str] = []
    n = len(s)
    for i, c in enumerate(s):
        if c in _ID_BREAK_CHARS:
            out.append(" ")
            continue
        if i > 0:
            p = s[i - 1]
            nxt = s[i + 1] if i + 1 < n else ""
            if c.isalpha() and p.isalpha():
                if c.isupper() and p.islower():
                    out.append(" ")
                elif c.isupper() and p.isupper() and nxt.islower():
                    out.append(" ")
            elif (c.isdigit() and p.isalpha()) or \
                    (c.isalpha() and p.isdigit()):
                out.append(" ")
        out.append(c)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def norm_heading(text: str, locale_fold: str = "basic") -> str:
    """Identity form used for duplicate detection and target resolution."""
    t = fold(_MARKUP_RE.sub("", text), locale_fold)
    t = re.sub(r"\s+", " ", t).strip()
    t = t.rstrip(".;:, ")
    if not re.search(r"\w", t):
        # a heading made only of symbols ('*', '**', '...') is its own
        # identity; markup stripping must not make them all empty
        t = re.sub(r"\s+", " ", text).strip()
    return t


# Qualifiers that restrict a cross-reference to part of a serial or a period
# (7.5.3), e.g. "see also quills for entries up to 1850" or a heading such as
# "quills in later issues see pens". They are not part of the target heading.
_XREF_QUAL_RE = re.compile(r"""
    \s*[(\[]?\s*
    (?:
        for\s+(?:references?|entries|entry|material|items?|articles?|works?
               |information|citations?|pages?|issues?|volumes?)\b
      | (?:before|after|until|since|prior\s+to|up\s+to|from)\s+
            (?:\d|(?:[A-Z][a-z]+\.?\s+)+\d|the\s)
      | in\s+(?:(?:the\s+)?(?:earlier|later|previous|subsequent|former|
                              current|recent|first|last|this|these|those|
                              all|other)\s+)?
            (?:vols?\b\.?|volumes?|issues?|editions?|years?|parts?|numbers?
               |series)\b
    )
    .*$""", re.X | re.I)


def split_qualifier(text: str) -> Tuple[str, str]:
    """Split 'target for references before 1990' into (target, qualifier).

    Only qualifiers that restrict a reference by volume, issue, edition or
    date are recognised; an ordinary parenthetical qualifier such as
    'Mercury (planet)' is part of the heading and is left alone.
    """
    m = _XREF_QUAL_RE.search(text)
    if not m or m.start() == 0:
        return text.strip(), ""
    return text[:m.start()].strip(" ,;"), text[m.start():].strip()


_ROMAN_RE = re.compile(r"^(?=[mdclxvi])m{0,3}(cm|cd|d?c{0,3})"
                       r"(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$")
_ROMAN_VALUES = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500,
                 "m": 1000}


def roman_to_int(s: str) -> Optional[int]:
    s = s.lower()
    if not s or not _ROMAN_RE.match(s):
        return None
    total = 0
    for i, ch in enumerate(s):
        v = _ROMAN_VALUES[ch]
        if i + 1 < len(s) and _ROMAN_VALUES[s[i + 1]] > v:
            total -= v
        else:
            total += v
    return total


# Sort-key element classes. Lower files first. The comma (inverted heading)
# takes one of two values depending on --inversion (8.5 is silent on it).
_SEP_COMMA_BEFORE, _SEP_PAREN, _SEP_COMMA_AFTER, _SEP_SPACE, _SYMBOL, \
    _DIGITS, _LETTER = 1, 2, 3, 4, 5, 6, 7

# A leading token made only of symbols ('!=', '*', '# (hash)', '...') is the
# subject of the heading, not ignorable punctuation: it files by code point
# in a symbols group ahead of numerals and letters. Symbols attached to a
# word ("'Tis", '--verbose', '$HOME') stay ignorable (null value, 8.1).
_SYM_TOKEN_RE = re.compile(r"^([^\w\s(]+)(?=\s|\(|$)")

# Words that, following a leading upper-case roman numeral, make it clear the
# numeral is a number (strict --roman mode). Deliberately short.
ROMAN_CONTEXT_WORDS = frozenset(
    "century centuries millennium dynasty dynasties congress corps army "
    "armies legion olympiad olympiads olympics amendment amendments "
    "symposium synod".split())


def _lead_roman(raw: str, roman: str, roman_list: frozenset
                ) -> Tuple[Optional[int], int]:
    """Value and length of a leading roman numeral that should interfile.

    ``off``: never. ``strict``: the whole first token is an upper-case roman
    numeral of 2+ letters and either appears in ``roman_list`` or is followed
    by a word in ROMAN_CONTEXT_WORDS. Anything else (CD, DC, MIX, VI ...)
    files as letters, as abbreviations are filed as written (7.3.6).
    """
    if roman == "off":
        return None, 0
    m = re.match(r"^([IVXLCDM]{2,})(?=$|[\s,.:;)-])", raw)
    if not m:
        return None, 0
    tok = m.group(1)
    val = roman_to_int(tok)
    if val is None:
        return None, 0
    if tok not in roman_list:
        nxt = re.match(r"[\s,.:;-]*([A-Za-z]+)", raw[m.end():])
        if not nxt or nxt.group(1).lower() not in ROMAN_CONTEXT_WORDS:
            return None, 0
    return val, m.end()


def sort_key(text: str, mode: str = "word", func_words: bool = False, *,
             roman: str = "strict", roman_list: frozenset = frozenset(),
             inversion: str = "after", locale_fold: str = "basic",
             keep_case: bool = False) -> Tuple[int, tuple]:
    """Return (group, elements). group -1 = symbol-initial (a leading token
    made only of symbols, filed by code point), 0 = numeral-initial,
    1 = alphabetic."""
    src = text.strip()
    sym = _SYM_TOKEN_RE.match(src)
    if sym:
        sym_elems = [(_SYMBOL, ord(c)) for c in sym.group(1)]
        raw = _MARKUP_RE.sub("", src[sym.end():])
    else:
        sym_elems = []
        raw = _MARKUP_RE.sub("", src).strip()
        raw = re.sub(r"^[^\w(]+", "", raw)      # leading symbols: null value
    lead_roman, cut = _lead_roman(raw, roman, roman_list)
    if lead_roman is not None:
        raw = raw[cut:]
    t = fold(raw, locale_fold, keep_case)
    if func_words:
        parts = t.split(None, 1)
        if len(parts) == 2 and parts[0].casefold() in FUNCTION_WORDS:
            t = parts[1]
    sep_comma = _SEP_COMMA_AFTER if inversion == "after" else \
        _SEP_COMMA_BEFORE
    elems: list = list(sym_elems)
    if lead_roman is not None:
        elems.append((_DIGITS, lead_roman))
    i, n = 0, len(t)
    while i < n:
        c = t[i]
        if c.isdigit():
            j = i
            while j < n and t[j].isdigit():
                j += 1
            elems.append((_DIGITS, int(t[i:j])))
            i = j
            continue
        if c.isalpha():
            elems.append((_LETTER, c))
        elif c == ",":
            while elems and elems[-1] == (_SEP_SPACE,):
                elems.pop()
            elems.append((sep_comma,))
        elif c == "(":
            while elems and elems[-1] == (_SEP_SPACE,):
                elems.pop()
            elems.append((_SEP_PAREN,))
        elif c.isspace() or c in "-\u2010\u2011\u2012\u2013\u2014/":
            if mode == "word" and elems and elems[-1][0] > _SEP_SPACE:
                elems.append((_SEP_SPACE,))
        # every other character: null filing value
        i += 1
    while elems and elems[-1][0] <= _SEP_SPACE:
        elems.pop()
    if sym_elems:
        group = -1
    else:
        group = 0 if elems and elems[0][0] == _DIGITS else 1
    return group, tuple(elems)


def first_word(text: str, locale_fold: str = "basic") -> str:
    t = fold(_MARKUP_RE.sub("", text), locale_fold).strip()
    m = re.match(r"[^\s,(]+", t)
    return m.group(0) if m else ""


# ---------------------------------------------------------------------------
# Locator parsing
# ---------------------------------------------------------------------------
_MARKER_WORDS = (r"figs?|figures?|illus|ill|illustrations?|tables?|tabs?|"
                 r"maps?|pls?|plates?")
_LOC_RE = re.compile(r"""^
    (?P<word>(?i:""" + _MARKER_WORDS + r""")(?:\.\s*|\s+))?
    (?:(?P<pre>\d+)(?P<psep>[:/])|
       (?P<rpre>[IVXLC]{2,}|[IVXLC](?=:))(?P<rsep>[.:]))?
    (?P<tag>[A-Z])?(?P<tsep>[-.](?=\d))?
    (?P<start>\d+|[ivxlc]+)(?P<ssuf>[a-z])?
    (?:\s*(?P<dash>--|-|\u2010|\u2011|\u2013|\u2014)\s*
       (?P<end>\d+|[ivxlc]+)(?P<esuf>[a-z])?)?
    (?P<open>\s*(?:ff\.?|f\.|et\s+seq\.?))?
    (?P<passim>\s+passim)?
    (?P<wsuf>\s*\((?i:""" + _MARKER_WORDS + r""")\.?\))?
    $""", re.X)
# letter suffixes read as special-matter markers (7.4.4): figure, table,
# illustration, map, plate. 'n' (note) and a-d (page columns/sections)
# are not special matter.
SPECIAL_SUFFIXES = frozenset("ftimp")
_MARKER_NORM = (("fig", "figure"), ("ill", "illustration"),
                ("tab", "table"), ("map", "map"), ("pl", "plate"))


def _marker_name(word: str) -> str:
    w = word.strip(" .()").lower()
    for pre, name in _MARKER_NORM:
        if w.startswith(pre):
            return name
    return w

_DASH_KIND = {"-": "hyphen", "\u2010": "hyphen", "\u2011": "hyphen",
              "--": "en", "\u2013": "en", "\u2014": "em"}


def parse_locator(token: str, line: int, ext: bool = False
                  ) -> Optional[Locator]:
    """Parse one locator token. ``ext`` also accepts the forms that are
    safe only as a comma-separated token of their own (never peeled off a
    heading after one space): a special-matter word before the number
    ('fig. 3', 'table 4'), a roman volume prefix ('II.45') and a letter
    prefix with a separator ('A-3', 'A.3')."""
    tok = token.strip()
    emphasis = False
    style = ""
    em = re.fullmatch(r"(\*{1,2}|_{1,2}|\[)(.*?)(\*{1,2}|_{1,2}|\])", tok)
    if em:
        emphasis = True
        style = ("bracket" if em.group(1) == "[" else
                 "bold" if len(em.group(1)) == 2 else "italic")
        tok = em.group(2).strip()
    if not tok:
        return None
    m = _LOC_RE.match(tok)
    if not m:
        return None
    if not ext and (m.group("word") or m.group("rpre") or m.group("tsep")):
        return None
    start_s, end_s = m.group("start"), m.group("end")
    roman = not start_s.isdigit()
    if roman:
        start = roman_to_int(start_s)
        if start is None or start > 399:
            return None
    else:
        start = int(start_s)
    prefix: Optional[int] = None
    pstyle = ""
    if m.group("pre"):
        prefix, pstyle = int(m.group("pre")), "arabic" + m.group("psep")
    elif m.group("rpre"):
        prefix = roman_to_int(m.group("rpre").lower())
        if prefix is None:
            return None
        pstyle = "roman" + m.group("rsep")
    tag = m.group("tag") or ""
    if tag:
        pstyle = pstyle or ("letter" + (m.group("tsep") or ""))
    marker = ""
    if m.group("word"):
        marker = _marker_name(m.group("word"))
        tag = marker          # its own numbering sequence (figure numbers)
    elif m.group("wsuf"):
        marker = _marker_name(m.group("wsuf"))
    loc = Locator(raw=token.strip(), line=line, start=start, roman=roman,
                  prefix=prefix,
                  suffix=m.group("ssuf") or "", tag=tag,
                  open_ended=bool(m.group("open")),
                  passim=bool(m.group("passim")), emphasis=emphasis,
                  style=style, pstyle=pstyle, marker=marker,
                  wprefix=bool(m.group("word")))
    if end_s is not None:
        loc.dash = _DASH_KIND[m.group("dash")]
        if roman or not end_s.isdigit():
            end = roman_to_int(end_s) if not end_s.isdigit() else None
            if end is None or roman != (not end_s.isdigit()):
                return None
            loc.end = end
        else:
            if len(end_s) < len(start_s):
                loc.elided = True
                expanded = start_s[:len(start_s) - len(end_s)] + end_s
                loc.end = int(expanded)
                # teens convention: 10-19 of a hundred kept at two digits
                if len(end_s) == 1 and len(start_s) >= 2 and \
                        10 <= loc.end % 100 <= 19:
                    loc.teen_issue = True
            else:
                loc.end = int(end_s)
                if len(end_s) == len(start_s) >= 2 and end_s[0] == start_s[0]:
                    loc.elided = False
    return loc


# ---------------------------------------------------------------------------
# Cross-reference extraction (text / HTML)
# ---------------------------------------------------------------------------
_SEE_RE = re.compile(
    r"(?P<paren>\(\s*)?(?P<em1>[*_]{1,2})?\b(?P<kw>see\s+also|see)\b"
    r"(?P<em2>[*_]{1,2})?(?=\s+\S)", re.I)


def _split_targets(text: str) -> List[CrossRef]:
    out: List[CrossRef] = []
    for part in text.split(";"):
        p = part.strip().rstrip(".").strip()
        if not p:
            continue
        generic = bool(re.fullmatch(r"(\*[^*]+\*|_[^_]+_)", p))
        p = _MARKUP_RE.sub("", p).strip()
        p = re.sub(r"^under\s+", "", p, flags=re.I)
        if p:
            out.append(CrossRef(p, generic))
    return out


def _find_see(s: str):
    for m in _SEE_RE.finditer(s):
        before = s[:m.start()]
        if before and not re.search(r"[\s,.;:(]$", before):
            continue
        return m
    return None


_NUMBERED_NOUN_RE = re.compile(
    r"(?:vols?|volumes?|issues?|nos?|numbers?|parts?|chapters?|chaps?|ch|"
    r"pp?|pages?|editions?|eds?|years?|series|sections?|§)\.?", re.I)


def _space_peel_ok(loc: Locator, comma_run: bool, style: str) -> bool:
    """May a locator joined to the heading by ONE space be read as a locator?

    ``style`` is the index-wide separator style (see ``detect_sep_style``):
    ``space`` - the index writes "heading 12"; peel any trailing locator.
    ``explicit`` - the index separates with a comma or two spaces; a number
    after a single space is part of the heading ("Route 66, 12").
    ``unknown`` - peel only on strong evidence: the run is a comma list
    ("kelp 12, 30") or the token is a range ("kelp 12-15").
    A lower-case roman token is peeled only in a space-style index, only when
    a comma list follows and only if it has 2+ letters, so that "vitamin c"
    or "appendix d" keep their final letter.
    """
    if loc.roman:
        letters = re.sub(r"[^ivxlc]", "", loc.raw)
        return style == "space" and comma_run and len(letters) >= 2
    if style == "space":
        return True
    if style == "explicit":
        return False
    return comma_run or loc.is_range


def _strip_closing_stop(rest: str, line: int) -> str:
    """Drop a full stop that closes an entry ('kelp, 3, 3.'): it follows a
    digit, an emphasis mark or a locator token, so it is punctuation and
    not part of the last locator. 'Lyell, Sir C.' and 'etc.' keep theirs."""
    if not rest.endswith(".") or rest.endswith(".."):
        return rest
    body = rest[:-1].rstrip()
    if re.search(r"[\d*_\]]$", body):
        return body
    parts = re.split(r"\s*,\s*", body)
    if len(parts) > 1 and parse_locator(parts[-1], line) is not None and \
            not re.fullmatch(r"[a-z]\.?|[A-Z]", parts[-1]):
        return body
    return rest


def split_locators(rest: str, line: int, style: str = "unknown"
                   ) -> Tuple[str, List[Locator], Optional[str]]:
    """Split 'Heading, 3, 7-9' into heading and locators (right to left).

    Returns (heading, locators, separator kind). The kind is ``explicit``
    when the heading/locator boundary is a comma or two spaces/tab (7.4.5),
    ``space`` when the last word of the heading looks like an arabic
    locator after a single space, else None. The kinds feed
    ``detect_sep_style``; ``style`` controls single-space peeling.

    Known ambiguity: a heading that itself ends in ", <number>" (e.g. a
    place and year, "Oslo, 1952") is always read as heading + locator.
    """
    rest = rest.strip().rstrip(",;:").strip()
    rest = _strip_closing_stop(rest, line)
    if not rest:
        return "", [], None
    tokens = [t for t in re.split(r"\s*,\s*", rest)]
    locs: List[Locator] = []
    while len(tokens) > 1:
        loc = parse_locator(tokens[-1], line, ext=True)
        if loc is None:
            break
        locs.insert(0, loc)
        tokens.pop()
    comma_run = bool(locs)
    kind: Optional[str] = None
    # two-space / tab separator between heading and first locator (7.4.5)
    parts = re.split(r"\s{2,}|\t", tokens[-1])
    loc = parse_locator(parts[-1], line) if len(parts) > 1 else None
    if loc is not None:
        locs.insert(0, loc)
        tokens[-1] = " ".join(parts[:-1])
        kind = "explicit"
    else:
        # single space: try the longest trailing word run that is one
        # locator ("40 - 42", "30-40 passim"), never the first word
        words = tokens[-1].split()
        cand: Optional[Locator] = None
        k_used = 0
        for k in range(min(4, len(words) - 1), 0, -1):
            cand = parse_locator(" ".join(words[-k:]), line)
            if cand is not None:
                k_used = k
                break
        # "in volumes 1-4", "part 2": the number belongs to the heading
        if cand is not None and \
                _NUMBERED_NOUN_RE.fullmatch(words[-k_used - 1]):
            cand = None
        if cand is not None and not cand.roman:
            kind = "space"
        elif comma_run:
            kind = "explicit"
        if cand is not None and _space_peel_ok(cand, comma_run, style):
            locs.insert(0, cand)
            tokens[-1] = " ".join(words[:-k_used])
    heading = ", ".join(t.strip() for t in tokens).strip()
    return heading, locs, kind


def detect_sep_style(kinds: Iterable[Optional[str]]) -> str:
    """Majority vote of per-line separator kinds: space | explicit | unknown."""
    kinds = list(kinds)
    sp = kinds.count("space")
    ex = kinds.count("explicit")
    if sp > ex:
        return "space"
    if ex > sp:
        return "explicit"
    return "unknown"


# A non-numeric locator in text input: '#fragment', a URL, or a file path
# ending in .html/.htm (optionally with a fragment).
_ANCHOR_RE = re.compile(
    r"^(?:#[^\s,;]*|[A-Za-z][\w+.-]*://\S+|[\w./%~-]+\.x?html?(?:#\S*)?)$")
_GLOSS_RE = re.compile(r"\s+\[[^\]]*\]\s*$")


def anchor_locator(href: str, line: int, raw: Optional[str] = None,
                   ids: Optional[Dict[str, int]] = None) -> Locator:
    """A Locator for an href / URL / #fragment (``--locators anchor``)."""
    pos = None
    if ids is not None and href.startswith("#"):
        frag = href[1:]
        pos = ids.get(frag, ids.get(_unquote(frag)))
    return Locator(raw=raw or href, line=line, start=0, anchor=href,
                   target_pos=pos)


def _unquote(s: str) -> str:
    from urllib.parse import unquote
    return unquote(s)


def _peel_anchors(s: str, line: int) -> Tuple[str, List[Locator]]:
    """Split 'heading<TAB>locator' or 'heading, #frag' / 'heading URL'."""
    if "\t" in s:
        head, tail = s.split("\t", 1)
        toks = [t for t in re.split(r"[\s,;]+", tail) if t]
        if toks and all(_ANCHOR_RE.match(t) for t in toks):
            return head.strip(), [anchor_locator(t, line) for t in toks]
    words = re.split(r"(\s*,\s*|\s+)", s)
    locs: List[Locator] = []
    while len(words) >= 3 and _ANCHOR_RE.match(words[-1]):
        locs.insert(0, anchor_locator(words[-1], line))
        words = words[:-2]
    return "".join(words).strip(), locs


def parse_content(text: str, level: int, line: int, style: str = "unknown",
                  locmode: str = "numeric") -> ParsedLine:
    """Parse one entry line. ``locmode``: numeric (default), auto (numeric,
    else anchors), anchor (href/URL/#frag locators only), none (the
    heading is its own locator: nothing is split off)."""
    s = text.strip()
    anchors: List[Locator] = []
    if locmode == "none":
        s = _GLOSS_RE.sub("", s.split("\t", 1)[0]).strip()
    elif locmode == "anchor":
        s, anchors = _peel_anchors(s, line)
    elif locmode == "auto":
        pl = parse_content(s, level, line, style, "numeric")
        if pl.locators:
            return pl
        s2, anchors = _peel_anchors(s, line)
        if not anchors:
            return pl
        s = s2
    if locmode != "numeric":
        pl = _parse_see(s, level, line, style, split=False)
        pl.locators = anchors + pl.locators
        return pl
    return _parse_see(s, level, line, style, split=True)


def _parse_see(s: str, level: int, line: int, style: str,
               split: bool = True) -> ParsedLine:
    see: List[CrossRef] = []
    see_also: List[CrossRef] = []
    placement: Optional[str] = None
    rest = s
    m = _find_see(s)
    if m:
        kw_also = "also" in m.group("kw").lower()
        if m.group("paren"):
            depth, close = 0, len(s)
            for idx in range(m.start(), len(s)):
                if s[idx] == "(":
                    depth += 1
                elif s[idx] == ")":
                    depth -= 1
                    if depth == 0:
                        close = idx
                        break
            tgt_text = s[m.end():close]
            before, after = s[:m.start()], s[close + 1:]
            _, after_locs, _ = split_locators("x, " + after.strip(" ,"),
                                              line, style)
            _, before_locs, _ = split_locators(before, line, style)
            rest = (before.rstrip() + (", " + after.strip(" ,")
                                       if after.strip(" ,") else ""))
            if after_locs:
                placement = "before"
            elif before_locs:
                placement = "after"
        else:
            tgt_text = s[m.end():]
            rest = s[:m.start()].rstrip(" ,.;:")
        # a 'see' clause may be followed by a 'see also' clause
        inner = _find_see(tgt_text)
        extra_also: List[CrossRef] = []
        if inner is not None and not kw_also and \
                "also" in inner.group("kw").lower():
            extra_also = _split_targets(tgt_text[inner.end():])
            tgt_text = tgt_text[:inner.start()].rstrip(" ,.;")
        targets = _split_targets(tgt_text)
        if kw_also:
            see_also = targets
        else:
            see = targets
            see_also = extra_also
    if split:
        heading, locs, kind = split_locators(rest, line, style)
    else:
        heading, locs, kind = rest.strip().rstrip(",;:").strip(), [], None
    if m and m.group("paren"):
        kind = None   # the ", " in rest was inserted here: not evidence
    if see_also and not m.group("paren"):
        placement = "after" if locs else None
    return ParsedLine(level=level, line=line, heading=heading, locators=locs,
                      see=see, see_also=see_also,
                      placement=placement if see_also else None,
                      see_line_only=bool(m) and not heading,
                      sep_kind=kind)


# ---------------------------------------------------------------------------
# Format readers -> List[ParsedLine]
# ---------------------------------------------------------------------------
_BULLET_RE = re.compile(r"^((?:[-*+\u2013\u2014\u2022]\s+)+)")


def _is_group_separator(content: str) -> bool:
    if re.match(r"^#{1,6}\s", content) or re.fullmatch(r"[-*_=]{3,}",
                                                        content):
        return True
    core = re.sub(r"[\s*_#\-\u2013\u2014=]", "", content)
    return len(core) <= 1


def _letter_header(content: str) -> Optional[str]:
    """The letter of a single-letter group header ('A', '## B', '-- C --')."""
    if not _is_group_separator(content):
        return None
    core = re.sub(r"[\s*_#\-–—=]", "", content)
    return core.upper() if len(core) == 1 and core.isalpha() else None


_LOC_TAIL_RE = re.compile(
    r"(?:,|\s)\s*[ivxlc]*\d*(?:\s*[-–—]\s*\d+)?[a-z]?\s*$")


def _is_prose(para: List[str]) -> bool:
    """Does a paragraph read as running prose rather than index entries?

    Prose: 8+ words, 5+ words per line on average, at least one sentence
    end (lower-case letter + . ! ? then a capital or the end), and most lines
    without a locator-like tail.
    """
    text = " ".join(para)
    words = text.split()
    if len(words) < 8 or len(words) / len(para) < 5:
        return False
    if not re.search(r"[a-z\)][.!?](?:\s+[A-Z(\"'‘“]|\s*$)", text):
        return False
    tails = sum(1 for ln in para if re.search(r"\d\s*$", ln) and
                _LOC_TAIL_RE.search(ln))
    return (tails + sum(1 for ln in para if _is_see_entry(ln))) * 3 \
        <= len(para)


def _is_see_entry(line: str) -> bool:
    """'harbours see anchorages; berths ...': a short heading + 'see' whose
    target is not note wording ('see the list', 'see page 4')."""
    m = _find_see(line)
    if not m or m.start() == 0 or len(line[:m.start()].split()) > 4:
        return False
    return not re.match(r"\s*(?:the|page|pages|p\.|pp\.|below|above|"
                        r"overleaf|also\s+the)\b", line[m.end():], re.I)


def _is_title_line(para: List[str]) -> bool:
    """A lone short caption such as 'About this index' (no digits/commas)."""
    return (len(para) == 1 and len(para[0].split()) <= 6 and
            not re.search(r"[\d,;]|\bsee\b", para[0], re.I))


def detect_preamble(lines: List[str]) -> int:
    """Number of leading lines that form an introductory note (0 if none).

    Paragraphs (separated by blank lines or group headers) are scanned from
    the top. Titles such as '# Index' are passed over; the scan stops at the
    first single-letter group header or the first paragraph that is not
    prose. A lone short caption directly before a prose paragraph belongs
    to the note. Never claims the whole file.
    """
    paras: List[Tuple[int, int, List[str]]] = []   # start, end (excl), lines
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if not s or s.startswith("<!--"):
            i += 1
            continue
        if _is_group_separator(s):
            if _letter_header(s):
                break
            i += 1
            continue
        j = i
        while j < n and lines[j].strip() and \
                not _is_group_separator(lines[j].strip()):
            j += 1
        paras.append((i, j, [ln.strip() for ln in lines[i:j]]))
        i = j
    end = 0
    for k, (start, stop, para) in enumerate(paras):
        if _is_prose(para):
            end = stop
        elif (_is_title_line(para) and k + 1 < len(paras) and
              _is_prose(paras[k + 1][2])):
            end = stop
        else:
            break
    rest = lines[end:]
    if not any(ln.strip() and not _is_group_separator(ln.strip())
               for ln in rest):
        return 0
    return end


def read_text(text: str, meta: Optional[dict] = None,
              skip_until: Optional[str] = None,
              auto_preamble: bool = True,
              locators: str = "numeric") -> List[ParsedLine]:
    """Parse a plain-text / Markdown index.

    ``meta`` (if given) receives ``style`` (separator style), ``groups``
    (single-letter group headers as (letter, line)) and ``preamble``
    ((first line, last line, how) of a skipped introductory note).
    ``skip_until`` is a regex: lines before the first line it matches are
    skipped. Otherwise, with ``auto_preamble``, a leading prose note is
    detected and skipped (see ``detect_preamble``).
    """
    meta = meta if meta is not None else {}
    meta.setdefault("groups", [])
    all_lines = text.splitlines()
    first = 0
    if skip_until is not None:
        try:
            rx = re.compile(skip_until)
        except re.error as exc:
            raise ParseError(f"bad --skip-until pattern: {exc}")
        for idx, ln in enumerate(all_lines):
            if rx.search(ln.strip()):
                first = idx
                break
        else:
            raise ParseError(f"--skip-until pattern {skip_until!r} matched "
                             f"no line")
        how = "skip-until"
    elif auto_preamble:
        first = detect_preamble(all_lines)
        how = "auto"
    if first:
        used = [k + 1 for k in range(first) if all_lines[k].strip()]
        if used:
            meta["preamble"] = (used[0], used[-1], how)
    pairs = [(lineno, line) for lineno, line in enumerate(all_lines, 1)
             if lineno > first]
    meta["text_layout"] = True   # leading whitespace is real indentation
    return _read_rows(pairs, meta, locators)


# Repeated-heading dashes (ditto): "—, of organic beings, 378" repeats the
# heading above; the number of dash units gives the depth ("——" / "————"
# with a 2-unit base). A single dash followed by a space is a bullet.
_DITTO_RE = re.compile(
    r"^([\u2014\u2015\u2E3A\u2E3B]+|-{2,})((?:\s*[,.:])+\s*|\s+)")
_INDEX_CAPTION_RE = re.compile(
    r"^(?:general\s+|subject\s+|name\s+|author\s+)?index"
    r"(?:\s+of\s+\w+(?:\s+\w+)?)?\s*[.:]?$", re.I)


def _ditto(content: str) -> Optional[Tuple[int, str]]:
    """(dash units, rest) for a repeated-heading line, else None."""
    m = _DITTO_RE.match(content)
    if not m:
        return None
    run, sep = m.group(1), m.group(2)
    punct = bool(re.search(r"[,.:]", sep))
    if run.startswith("-"):
        if not punct:
            return None
        units = len(run) // 2
    else:
        units = sum(2 if c == "\u2E3A" else 3 if c == "\u2E3B" else 1
                    for c in run)
        if not punct and units < 2:
            return None
    rest = content[m.end():].strip()
    return (units, rest) if rest else None


def _is_caption(content: str, seen_entries: bool) -> bool:
    """'INDEX.', '# Index', 'General Index': a caption, not an entry."""
    core = content.strip("#*_ \t")
    if not _INDEX_CAPTION_RE.match(core):
        return False
    return not seen_entries or core.isupper()


def _open_heading(content: str) -> bool:
    """A line that neither carries locators/cross-references nor ends in
    punctuation: its text may continue on the next (turnover) line."""
    pl = parse_content(content, 0, 0, "unknown", "numeric")
    return (not pl.locators and not pl.see and not pl.see_also and
            not re.search(r"[.:;,]$", content.strip()))


def _has_refs(content: str) -> bool:
    pl = parse_content(content, 0, 0, "unknown", "numeric")
    return bool(pl.locators or pl.see or pl.see_also)


def _paren_split(s: str, sep: str) -> List[str]:
    parts, depth, cur = [], 0, []
    for ch in s:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(depth - 1, 0)
        if ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def _split_runon(content: str) -> Optional[List[Tuple[int, str]]]:
    """Split a run-on entry 'kelp, 4; drying, 12; zinc in, 8' (9.5) into
    (depth, text) parts: the main heading (0) and its subheadings (1). A
    lead with no locators may end in a colon ('beacons: coastal 7; inland
    9'), and a subheading may end in a parenthesised third level ('fuel
    33 (oil 33; paraffin 40)', depth 2). Every subheading must be a
    heading with locators; a trailing 'see (also)' clause belongs to the
    main heading. Returns None when the line is not run-on."""
    if ";" not in content:
        return None
    m = _find_see(content)
    head = content[:m.start()] if m else content
    tail = content[m.start():] if m else ""
    parts = [x.strip() for x in _paren_split(head, ";")]
    parts = [x for x in parts if x]
    if len(parts) < 2:
        return None
    out: List[Tuple[int, str]] = []
    cm = re.match(r"^([^:()]*?[^\W\d_][^:()]*?)\s*:\s+([^\W\d_].*)$",
                  parts[0])
    if cm and not _has_refs(cm.group(1)):
        out.append((0, cm.group(1)))
        subs = [cm.group(2)] + parts[1:]
    else:
        out.append((0, parts[0]))
        subs = parts[1:]
    first = parse_content(out[0][1], 0, 0, "unknown", "numeric")
    if not first.heading or first.see or first.see_also:
        return None
    for x in subs:
        third: List[str] = []
        pm = re.match(r"^(.*?\S)\s*\(([^()]*)\)\s*$", x)
        if pm and re.search(r"[^\W\d_]{2,}.*\d", pm.group(2)) and \
                not _find_see(pm.group(2)):
            x = pm.group(1)
            third = [y.strip() for y in pm.group(2).split(";") if y.strip()]
        for depth, text in [(1, x)] + [(2, y) for y in third]:
            # after a ';' a trailing number is a locator even after one
            # space ('keepers 31')
            q = parse_content(text, 0, 0, "space", "numeric")
            if not q.heading or not q.locators or \
                    not re.search(r"[^\W\d_]", q.heading):
                return None
            out.append((depth, text))
    if tail:
        out[0] = (0, out[0][1] + " " + tail)
    return out


def _read_rows(pairs: List[Tuple[int, str]], meta: dict,
               locators: str = "numeric") -> List[ParsedLine]:
    """Turn (line number, text line) pairs into ParsedLines: bullets and
    indentation give the level; repeated-heading dashes, wrapped locator
    strings, turnover lines and run-on subheadings are resolved first."""
    meta.setdefault("groups", [])
    items = [(ln, line) for ln, line in pairs
             if line.strip() and not line.strip().startswith("<!--")]
    has_ditto = any(_ditto(line.strip()) for _, line in items)
    col0 = [line.strip() for _, line in items
            if not line[:1].isspace() and re.match(r"[^\W\d_]",
                                                    line.strip())]
    caps = (sum(1 for c in col0 if c[:1].isupper()) / len(col0)
            if col0 else 0.0)
    indents = [len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip(" "))
               for _, line in items]
    meta.setdefault("turnovers", [])
    rows: List[dict] = []
    section: Optional[str] = None     # explicit heading line in force
    base_section: Optional[str] = None
    in_group_section = False
    letter_group: Optional[str] = None
    for k, (lineno, line) in enumerate(items):
        indent = indents[k]
        content = line.strip()
        bullets = 0
        dit = _ditto(content)
        units: Optional[int] = None
        if dit:
            units, content = dit
        else:
            bm = _BULLET_RE.match(content)
            if bm:
                bullets = len(re.findall(r"[-*+\u2013\u2014\u2022]",
                                         bm.group(1)))
                content = content[bm.end():].strip()
            if not content:
                continue
            if _is_group_separator(content):
                letter = _letter_header(content)
                if letter:
                    meta["groups"].append((letter, lineno))
                    letter_group = letter
                    if in_group_section:
                        section, in_group_section = base_section, False
                else:
                    label = _section_label(content)
                    if label:
                        section, letter_group = label, None
                        in_group_section = bool(_GROUP_LABEL_RE.match(label))
                        if not in_group_section:
                            base_section = label
                continue
            if _is_caption(content, bool(rows)):
                section = base_section = content.strip("#*_ \t")
                letter_group, in_group_section = None, False
                continue
        if rows and units is None and not bullets:
            prev = rows[-1]
            # wrapped continuation of a long locator string (a line of
            # locators only after a trailing comma cannot be an entry)
            if prev["content"].rstrip().endswith(","):
                toks = [t for t in re.split(r"\s*,\s*", _strip_closing_stop(
                    content.rstrip(","), lineno)) if t.strip()]
                if toks and all(parse_locator(t, lineno) for t in toks):
                    prev["content"] = prev["content"].rstrip() + " " + content
                    if not prev["bullets"]:
                        meta["turnovers"].append((lineno, indent,
                                                  prev["lineno"]))
                    continue
            if locators != "none" and re.match(r"[a-z]", content) and \
                    _open_heading(prev["content"]) and _has_refs(content):
                nxt = indents[k + 1] if k + 1 < len(items) else 0
                # flush-left turnover: in an index whose headings are
                # capitalised (or that repeats headings with dashes), a
                # lower-case line after an open heading continues it
                flush = indent <= prev["indent"] and (has_ditto or
                                                      caps >= 0.8)
                # deeper-indented turnover of a long subheading that would
                # otherwise become its only sub-subheading
                deeper = (indent > prev["indent"] and
                          len(prev["content"]) >= 40 and
                          nxt <= prev["indent"])
                if flush or deeper:
                    prev["content"] = prev["content"].rstrip() + " " + content
                    if not prev["bullets"]:
                        meta["turnovers"].append((lineno, indent,
                                                  prev["lineno"]))
                    continue
        rows.append({"indent": indent, "bullets": bullets,
                     "content": content, "lineno": lineno, "ditto": units,
                     "sub": False, "section": section,
                     "group": letter_group})
    if not rows:
        return []
    if locators != "none":
        meta["runon_rows"] = [(r["lineno"], r["content"]) for r in rows
                              if ";" in r["content"]]
    expanded: List[dict] = []
    for r in rows:
        segs = _split_runon(r["content"]) if locators != "none" else None
        if not segs:
            expanded.append(r)
            continue
        expanded.append(dict(r, content=segs[0][1]))
        expanded.extend(dict(r, content=x, sub=d, ditto=None, bullets=0)
                        for d, x in segs[1:])
    rows = expanded
    meta["runon"] = sum(1 for r in rows if r["sub"])
    meta["ditto"] = sum(1 for r in rows if r["ditto"])
    unit = min((r["ditto"] for r in rows if r["ditto"]), default=1)
    plain_col0 = sum(1 for r in rows if r["indent"] == 0 and
                     r["bullets"] == 0 and not r["ditto"] and not r["sub"])
    bulleted = sum(1 for r in rows if r["bullets"] > 0)
    dash_mode = plain_col0 >= 2 and bulleted >= 1
    style = detect_sep_style(parse_content(r["content"], 0, r["lineno"],
                                           "unknown", locators).sep_kind
                             for r in rows)
    meta["style"] = style
    out: List[ParsedLine] = []
    stack: List[int] = []
    prev_level = -1
    main_level = 0
    for r in rows:
        if r["sub"]:
            level = main_level + int(r["sub"])
        elif r["ditto"]:
            level = max(1, round(r["ditto"] / unit))
        elif dash_mode and r["bullets"]:
            level = r["bullets"]
        else:
            indent = r["indent"]
            while stack and stack[-1] > indent:
                stack.pop()
            if not stack or stack[-1] < indent:
                stack.append(indent)
            level = len(stack) - 1
        level = min(level, prev_level + 1)
        prev_level = level
        if not r["sub"]:
            main_level = level
        if not (r["sub"] or r["bullets"]):
            # set-out layout: the indent actually used for this level
            meta.setdefault("indents", []).append(
                (level, r["indent"], r["lineno"], bool(r["ditto"])))
        pl = parse_content(r["content"], level, r["lineno"], style,
                           locators)
        pl.section, pl.group = r["section"], r["group"]
        out.append(pl)
    return out


def _section_label(content: str) -> Optional[str]:
    """The text of a Markdown heading line ('## Index of names') that is
    not a single-letter group header: an explicit section of the index."""
    m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", content)
    if not m:
        return None
    label = m.group(1).strip("*_ \t")
    return label if len(label) > 1 or _GROUP_LABEL_RE.match(label) else None


def _brace_split(s: str, sep: str = ",") -> List[str]:
    parts, depth, cur = [], 0, []
    for ch in s:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def _brace_arg(s: str, pos: int) -> Tuple[str, int]:
    """Return content of the braced group starting at s[pos] == '{'."""
    depth = 0
    for i in range(pos, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[pos + 1:i], i + 1
    return s[pos + 1:], len(s)


def latex_clean(s: str) -> str:
    s = re.sub(r"\\hyperindexformat\{\\?\w+\}", "", s)
    s = s.replace("--", "\u2013")
    s = re.sub(r"\\([&%$#_{}])", r"\1", s)
    s = s.replace("~", " ").replace("\\ ", " ")
    s = re.sub(r"\\[A-Za-z@]+\*?\s*", "", s)
    s = s.replace("{", "").replace("}", "").replace("$", "")
    return re.sub(r"\s+", " ", s).strip()


_IND_ITEM_RE = re.compile(r"^\\(item|subitem|subsubitem)\b\s*(.*)$")
_IND_LEVEL = {"item": 0, "subitem": 1, "subsubitem": 2}
_SEE_MACRO_RE = re.compile(r"^\\(see|seealso|seeonly|seealsoonly)\s*\{")
_GENERIC_TEX_RE = re.compile(r"\\(emph|textit|itshape|em|textsl)\b")


def _unwrap_hyperindexformat(body: str) -> str:
    """hyperref writes '\\hyperindexformat{\\see{kelp}}{3}' for a 'see' and
    '\\hyperindexformat{\\textbf}{9}' for a formatted page. Rewrite them as
    the plain makeindex forms '\\see{kelp}{3}' and '\\textbf{9}'."""
    out, i = [], 0
    key = "\\hyperindexformat"
    while True:
        j = body.find(key, i)
        if j < 0:
            out.append(body[i:])
            return "".join(out)
        k = j + len(key)
        while k < len(body) and body[k].isspace():
            k += 1
        if k >= len(body) or body[k] != "{":
            out.append(body[i:k])
            i = k
            continue
        fmt, k2 = _brace_arg(body, k)
        page = ""
        if k2 < len(body) and body[k2] == "{":
            page, k2 = _brace_arg(body, k2)
        out.append(body[i:j])
        fmt = fmt.strip()
        if _SEE_MACRO_RE.match(fmt):
            out.append(fmt + "{" + page + "}")
        elif re.fullmatch(r"\\[A-Za-z]+", fmt):
            out.append(fmt + "{" + page + "}")
        else:
            out.append(page)
        i = k2


def read_ind(text: str) -> List[ParsedLine]:
    logical: List[list] = []
    in_gap = False
    saw_item = False
    for lineno, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("%"):
            continue
        m = _IND_ITEM_RE.match(s)
        if m:
            saw_item = True
            in_gap = False
            logical.append([lineno, _IND_LEVEL[m.group(1)], m.group(2)])
        elif s.startswith("\\indexspace") or s.startswith("\\begin") or \
                s.startswith("\\end") or s.startswith("\\lettergroup"):
            in_gap = True
        elif logical and not in_gap:
            logical[-1][2] += " " + s
    if not saw_item:
        raise ParseError("no \\item lines found in .ind input")
    out: List[ParsedLine] = []
    for lineno, level, body in logical:
        body = _unwrap_hyperindexformat(body)
        body = re.sub(r"\\(dotfill|hfill|quad|qquad)\b\s*", ", ", body)
        tokens = [t.strip() for t in _brace_split(body)]
        tokens = [t for t in tokens if t]
        kinds: List[str] = []
        locs: List[Locator] = []
        see: List[CrossRef] = []
        also: List[CrossRef] = []
        idx = len(tokens)
        tail: List[Tuple[str, object]] = []
        while idx > 1:
            tok = tokens[idx - 1]
            sm = _SEE_MACRO_RE.match(tok)
            if sm:
                arg, _ = _brace_arg(tok, sm.end() - 1)
                generic = bool(_GENERIC_TEX_RE.search(arg))
                refs = [CrossRef(latex_clean(p).rstrip("."), generic)
                        for p in arg.split(";") if latex_clean(p)]
                tail.insert(0, ("also" if "also" in sm.group(1) else "see",
                                refs))
                idx -= 1
                continue
            loc = parse_locator(latex_clean(tok), lineno, ext=True)
            if loc is None:
                break
            loc.raw = tok
            loc.emphasis = bool(re.search(r"\\(textbf|textit|emph|bf|it)\b",
                                          tok))
            if re.search(r"\\(textbf|bf)\b", tok):
                loc.style = "bold"
            elif loc.emphasis:
                loc.style = "italic"
            tail.insert(0, ("loc", loc))
            idx -= 1
        heading = latex_clean(", ".join(tokens[:idx]))
        last_loc_pos = max((i for i, (k, _) in enumerate(tail) if k == "loc"),
                           default=-1)
        placement = None
        for i, (kind, val) in enumerate(tail):
            kinds.append(kind)
            if kind == "loc":
                locs.append(val)  # type: ignore[arg-type]
            elif kind == "see":
                see.extend(val)  # type: ignore[arg-type]
            else:
                also.extend(val)  # type: ignore[arg-type]
                if last_loc_pos >= 0:
                    placement = "before" if i < last_loc_pos else "after"
        out.append(ParsedLine(level=level, line=lineno, heading=heading,
                              locators=locs, see=see, see_also=also,
                              placement=placement if also else None,
                              see_line_only=bool(see or also) and not heading))
    return out


_HTML_SKIP = frozenset(
    "nav header footer aside script style template search dialog".split())
_HTML_HEADINGS = frozenset("h1 h2 h3 h4".split())
# site chrome marked by ARIA role or by a well-known sidebar class
_HTML_SKIP_ROLES = frozenset("navigation search banner contentinfo".split())
_HTML_SKIP_CLASSES = frozenset("sphinxsidebar sphinxsidebarwrapper related "
                               "genindex-jumpbox".split())
# inline badges that run into a heading ("type Packagedeprecated") and
# Gutenberg page-number markers (<span class="pagenum">[492]</span>)
_HTML_BADGE_RE = re.compile(r"badge|deprecated|pagenum", re.I)
_HTML_VOID = frozenset("area base br col embed hr img input link meta param "
                       "source track wbr".split())
# block elements that end a line of a <p>/<br> index
_HTML_BLOCKS = frozenset("p div blockquote section article main body center "
                         "pre h5 h6 table tr td th".split())
# section headings that name a non-alphabetic group (Sphinx 'Symbols', '_')
_GROUP_LABEL_RE = re.compile(
    r"^(?:symbols?|numbers?|numerals?|non-?alphabetic(?:al)?|"
    r"symbols?\s*(?:&|and)\s*numbers?|\W|_)$", re.I)
_MSO_INDEX_RE = re.compile(r"(?:^|\s)(?:mso)?index(?:_20_)?[\s_-]?(\d)\b",
                           re.I)
_MARGIN_RE = re.compile(r"(?:margin|padding)-left\s*:\s*(-?[\d.]+)\s*"
                        r"(cm|mm|in|pt|px|em|rem|%)?", re.I)
_UNIT_PX = {"cm": 37.8, "mm": 3.78, "in": 96.0, "pt": 1.333, "px": 1.0,
            "em": 16.0, "rem": 16.0, "%": 8.0, None: 1.0}


def _html_skip_attrs(tag: str, a: dict) -> bool:
    if tag in _HTML_VOID:
        return False
    if (a.get("role") or "").lower() in _HTML_SKIP_ROLES:
        return True
    classes = set((a.get("class") or "").split())
    if classes & _HTML_SKIP_CLASSES:
        return True
    return tag in ("span", "small", "sup", "mark") and \
        bool(_HTML_BADGE_RE.search(a.get("class") or ""))


class _HTMLIndexParser(HTMLParser):
    """Collect list items (li / dt / dd) with their nesting level.

    * ``<nav>``, ``<header>``, ``<footer>``, ``<aside>``, ``<search>``,
      ``<dialog>``, ``<script>``, ``<style>`` and ``<template>`` are site
      chrome and are
      skipped, as is any element with role navigation/search/banner/
      contentinfo or class sphinxsidebar/related, and inline badges
      and page markers (class containing 'badge', 'deprecated' or
      'pagenum').
    * ``<h1>``-``<h4>`` outside an item (and elements whose id is a known
      API-listing kind such as 'structs' or 'functions') start a new
      section; a heading that is a single letter is a letter-group header
      instead (recorded in ``groups``). A section named for a non-letter
      group ('Symbols', '_') ends at the next letter-group header, where
      the enclosing section label resumes.
    * A sibling ``<li>`` with no text of its own that only wraps a nested
      list (``<li>type T</li><li><ul>...</ul></li>``) contributes nothing,
      so the nested items are subheadings of the preceding item.
    * Links inside items are kept (href + link text) for anchor locators;
      every id / a[name] is recorded with its document order.
    * Also collected for pages without list items: text lines of a
      ``<p>``/``<br>`` index (``plines``, with class and style) and the
      first cell of each table row (``rows``).
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.stack: List[dict] = []
        self.items: List[dict] = []
        self.skip_stack: List[list] = []
        self.ids: Dict[str, int] = {}
        self.sections: List[Optional[str]] = []
        self.hbuf: Optional[dict] = None
        self.groups: List[Tuple[str, int]] = []
        self.base_label: Optional[str] = None
        self.in_group_section = False
        # <p>/<br> lines
        self.plines: List[dict] = []
        self.pcur: Optional[dict] = None
        self.blocks: List[Tuple[str, dict]] = []
        self.index_mark: Optional[int] = None
        # table rows
        self.rows: List[dict] = []
        self.tr: Optional[dict] = None

    # -- li / dt / dd -----------------------------------------------------
    def _flush(self, buf: dict) -> None:
        if buf["done"]:
            return
        buf["done"] = True
        pieces = buf["text"]
        text = re.sub(r"\s+", " ", "".join(pieces)).strip()
        if text:
            links = []
            for href, a, b in buf["links"]:
                lt = re.sub(r"\s+", " ", "".join(
                    pieces[a:b if b is not None else len(pieces)])).strip()
                links.append((href, lt))
            self.items.append({"level": buf["level"], "text": text,
                               "line": buf["line"], "col": buf["col"],
                               "tag": buf["tag"], "links": links,
                               "section": len(self.sections) - 1})

    def _pop_until(self, tags: Iterable[str]) -> None:
        tags = set(tags)
        while self.stack:
            buf = self.stack.pop()
            self._flush(buf)
            if buf["tag"] in tags:
                break

    def _new_buf(self, tag: str, level: int) -> dict:
        line, col = self.getpos()
        return {"tag": tag, "level": level, "text": [], "line": line,
                "col": col + 1, "done": False, "depth": self.depth,
                "links": []}

    # -- <p>/<br> lines ---------------------------------------------------
    def _pflush(self) -> None:
        cur, self.pcur = self.pcur, None
        if cur is None:
            return
        raw = "".join(cur["text"])
        lead = len(raw) - len(raw.lstrip("\xa0 \t\n"))
        nbsp = raw[:lead].count("\xa0")
        text = re.sub(r"\s+", " ", raw.replace("\xa0", " ")).strip()
        if text:
            cur.update(text=text, nbsp=nbsp)
            self.plines.append(cur)

    def _pdata(self, data: str) -> None:
        if self.pcur is None:
            if not data.strip():
                return
            line, col = self.getpos()
            cls, style = "", ""
            for _, attrs in reversed(self.blocks):
                if attrs.get("class") or attrs.get("style"):
                    cls = attrs.get("class") or ""
                    style = attrs.get("style") or ""
                    break
            self.pcur = {"text": [], "line": line, "col": col + 1,
                         "cls": cls, "style": style,
                         "group": len(self.sections) - 1}
        self.pcur["text"].append(data)

    # -- table rows -------------------------------------------------------
    def _rflush(self) -> None:
        tr, self.tr = self.tr, None
        if tr is None or not tr["cells"]:
            return
        pieces = tr["text"]
        text = re.sub(r"\s+", " ", "".join(pieces)).strip()
        links = []
        for href, a, b in tr["links"]:
            lt = re.sub(r"\s+", " ", "".join(
                pieces[a:b if b is not None else len(pieces)])).strip()
            if lt:
                links.append((href, lt))
        head = links[0][1] if links else text
        if head:
            self.rows.append({"text": head, "links": links,
                              "line": tr["line"], "col": tr["col"],
                              "sub": tr["sub"], "style": tr["style"]})

    # -- events -----------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for key in ("id",) + (("name",) if tag == "a" else ()):
            v = a.get(key)
            if v and v not in self.ids:
                self.ids[v] = len(self.ids)
        if self.skip_stack:
            if tag == self.skip_stack[-1][0] and tag not in _HTML_VOID:
                self.skip_stack[-1][1] += 1
            return
        if tag in _HTML_SKIP or _html_skip_attrs(tag, a):
            self.skip_stack.append([tag, 1])
            return
        if tag in _HTML_HEADINGS and not self.stack:
            self._pflush()
            self.hbuf = {"tag": tag, "text": [], "id": a.get("id"),
                         "line": self.getpos()[0]}
            return
        if self.hbuf is not None:
            return
        if tag in _HTML_BLOCKS or tag == "br" or tag in ("ul", "ol", "dl",
                                                         "li", "dt", "dd"):
            self._pflush()
            if tag in _HTML_BLOCKS:
                self.blocks.append((tag, a))
        if tag == "tr":
            self._rflush()
            line, col = self.getpos()
            self.tr = {"cells": 0, "text": [], "links": [], "line": line,
                       "col": col + 1, "sub": False, "style": "",
                       "cap": False}
        elif tag in ("td", "th") and self.tr is not None:
            self.tr["cap"] = False
            if tag == "td" and not self.tr["cells"]:
                self.tr["cap"] = True
                self.tr["style"] = a.get("style") or ""
            self.tr["cells"] += 1 if tag == "td" else 0
        elif self.tr is not None and self.tr["cap"]:
            if re.search(r"(?:^|[\s_-])sub|child", a.get("class") or "",
                         re.I):
                self.tr["sub"] = True
            if tag == "a" and a.get("href") is not None:
                self.tr["links"].append([a["href"], len(self.tr["text"]),
                                         None])
        if not self.stack and a.get("id") in KNOWN_SECTION_IDS and \
                tag not in ("ul", "ol", "dl", "li", "dt", "dd"):
            self.sections.append(a["id"].replace("-", " ").title())
        if tag in ("ul", "ol", "dl"):
            if self.stack:
                self._flush(self.stack[-1])
            self.depth += 1
        elif tag == "li":
            if self.stack and self.stack[-1]["tag"] == "li" and \
                    self.stack[-1]["depth"] == self.depth:
                self._pop_until(["li"])
            self.stack.append(self._new_buf("li", max(self.depth - 1, 0)))
        elif tag in ("dt", "dd"):
            if self.stack and self.stack[-1]["tag"] in ("dt", "dd") and \
                    self.stack[-1]["depth"] == self.depth:
                self._pop_until(["dt", "dd"])
            level = max(self.depth - 1, 0) + (1 if tag == "dd" else 0)
            self.stack.append(self._new_buf(tag, level))
        elif self.stack:
            buf = self.stack[-1]
            if tag in ("em", "i", "cite"):
                buf["text"].append("*")
            elif tag in ("strong", "b"):
                buf["text"].append("**")
            elif tag == "br":
                buf["text"].append(" ")
            elif tag == "a" and a.get("href") is not None and \
                    not buf["done"]:
                buf["links"].append([a["href"], len(buf["text"]), None])
        elif self.pcur is not None and tag in ("em", "i", "cite"):
            self.pcur["text"].append("*")
        elif self.pcur is not None and tag in ("strong", "b"):
            self.pcur["text"].append("**")

    def handle_endtag(self, tag):
        if self.skip_stack:
            top = self.skip_stack[-1]
            if tag == top[0]:
                top[1] -= 1
                if top[1] <= 0:
                    self.skip_stack.pop()
            return
        if self.hbuf is not None:
            if tag == self.hbuf["tag"]:
                self._heading_done()
            return
        if tag in _HTML_BLOCKS:
            self._pflush()
            for k in range(len(self.blocks) - 1, -1, -1):
                if self.blocks[k][0] == tag:
                    del self.blocks[k:]
                    break
        if tag in ("tr", "table"):
            self._rflush()
        elif tag in ("td", "th") and self.tr is not None:
            self.tr["cap"] = False
        elif tag == "a" and self.tr is not None and self.tr["cap"] and \
                self.tr["links"] and self.tr["links"][-1][2] is None:
            self.tr["links"][-1][2] = len(self.tr["text"])
        if tag in ("ul", "ol", "dl"):
            while self.stack and self.stack[-1]["depth"] >= self.depth:
                self._flush(self.stack.pop())
            self.depth = max(self.depth - 1, 0)
        elif tag in ("li", "dt", "dd"):
            if any(b["tag"] == tag for b in self.stack):
                self._pop_until([tag])
        elif self.stack:
            buf = self.stack[-1]
            if tag in ("em", "i", "cite"):
                buf["text"].append("*")
            elif tag in ("strong", "b"):
                buf["text"].append("**")
            elif tag == "a" and buf["links"] and buf["links"][-1][2] is None:
                buf["links"][-1][2] = len(buf["text"])
        elif self.pcur is not None and tag in ("em", "i", "cite"):
            self.pcur["text"].append("*")
        elif self.pcur is not None and tag in ("strong", "b"):
            self.pcur["text"].append("**")

    def _heading_done(self) -> None:
        label = re.sub(r"\s+", " ", "".join(self.hbuf["text"]))
        label = label.replace("¶", "").strip()
        if len(label) == 1 and label.isalpha():
            self.groups.append((label.upper(), self.hbuf["line"]))
            if self.in_group_section:
                # a letter group after 'Symbols' / '_': back to the
                # enclosing section, not a continuation of the symbol group
                self.sections.append(self.base_label)
                self.in_group_section = False
        elif label or self.hbuf["id"]:
            lab = label or self.hbuf["id"]
            self.sections.append(lab)
            self.in_group_section = bool(_GROUP_LABEL_RE.match(label))
            if not self.in_group_section:
                self.base_label = lab
            if _INDEX_CAPTION_RE.match(label):
                self.index_mark = len(self.plines)
        self.hbuf = None

    def handle_data(self, data):
        if self.skip_stack:
            return
        if self.hbuf is not None:
            self.hbuf["text"].append(data)
            return
        if self.stack and not self.stack[-1]["done"]:
            self.stack[-1]["text"].append(data)
        elif not self.stack:
            self._pdata(data)
        if self.tr is not None and self.tr["cap"]:
            self.tr["text"].append(data)


def _html_anchor_locs(pl: ParsedLine, links: List[Tuple[str, str]],
                      line: int, ids: Dict[str, int]) -> None:
    """Attach link hrefs of an item to ``pl`` as anchor locators.

    Link texts at the end of the heading ('abacus, 4, 9' with 4 and 9 as
    links) are peeled off the heading; links whose text lies in what is
    left of the heading (typically the whole heading is a link) become
    locators too, in front. Links that are cross-reference targets are
    left alone.
    """
    targets = {norm_heading(r.target) for r in pl.see + pl.see_also}
    cand = [(h, t) for h, t in links if norm_heading(t) not in targets]
    heading = pl.heading
    peeled: List[Locator] = []
    rest = list(cand)
    for href, lt in reversed(cand):
        core = heading.rstrip(" ,;")
        if lt and core.endswith(lt) and len(core) > len(lt) and \
                re.search(r"[\s,;]$", core[:-len(lt)]):
            heading = core[:-len(lt)].rstrip(" ,;")
            peeled.insert(0, anchor_locator(href, line, lt, ids))
            rest.pop()
        else:
            break
    plain = _MARKUP_RE.sub("", heading)
    head_locs = [anchor_locator(href, line, lt, ids) for href, lt in rest
                 if lt and _MARKUP_RE.sub("", lt) in plain]
    if peeled:
        pl.heading = heading
    pl.locators = head_locs + peeled + pl.locators


def _link_heading(text: str, links: List[Tuple[str, str]]) -> bool:
    """Is the item's heading itself link text (Sphinx genindex 'Route 66',
    '__abs__() (in module operator)'), with nothing but further links
    after it? Then digits in it are part of the heading, not locators."""
    if not links or not links[0][1]:
        return False
    plain = _MARKUP_RE.sub("", text).strip()
    first = _MARKUP_RE.sub("", links[0][1]).strip()
    if not first or not plain.startswith(first):
        return False
    return not re.sub(r"[\s,;.]", "", _strip_link_texts(text, links))


def _pline_depths(plines: List[dict]) -> List[int]:
    """Indentation (in spaces) of each <p>/<br> index line: Word/LibreOffice
    index classes (MsoIndex1-3, Index_20_1 ...) give the level directly;
    otherwise the rank of a margin-left/padding-left value; leading
    non-breaking spaces add to it."""
    margins = []
    for pl in plines:
        m = _MARGIN_RE.search(pl["style"])
        pl["margin"] = (float(m.group(1)) * _UNIT_PX.get(
            (m.group(2) or "").lower() or None, 1.0)) if m else None
        if pl["margin"] is not None:
            margins.append(round(pl["margin"], 1))
    ranks = {v: i for i, v in enumerate(sorted(set(margins)))}
    out = []
    for pl in plines:
        m = _MSO_INDEX_RE.search(pl["cls"])
        if m:
            depth = max(int(m.group(1)) - 1, 0)
        elif pl["margin"] is not None:
            depth = ranks[round(pl["margin"], 1)]
        else:
            depth = 0
        out.append(depth * 4 + pl.get("nbsp", 0))
    return out


def _read_html_lines(p: _HTMLIndexParser, plines: List[dict], meta: dict,
                     locators: str) -> List[ParsedLine]:
    """A <p>/<br> index: each line becomes a text line (with indentation
    from class, margin or leading spaces) for the text reader, so dittos,
    turnovers and run-on entries are handled as in plain text."""
    per_line: Dict[int, int] = {}
    for pl in plines:
        per_line[pl["line"]] = per_line.get(pl["line"], 0) + 1
    depths = _pline_depths(plines)
    pairs = []
    for pl, d in zip(plines, depths):
        pos = Pos(pl["line"], pl["col"] if per_line[pl["line"]] > 1 else None)
        pairs.append((pos, " " * d + pl["text"]))
    groups = list(p.groups)
    lines = _read_rows(pairs, meta, "numeric" if locators == "anchor"
                       else locators)
    meta["groups"] = sorted(groups + meta.get("groups", []),
                            key=lambda g: int(g[1]))
    meta["layout"] = "paragraph"
    return lines


def _read_html_rows(p: _HTMLIndexParser, meta: dict,
                    locators: str) -> List[ParsedLine]:
    """A <table> index: the first cell of each row is the heading (its
    first link's text when it has links) and its links are the locators;
    a class containing 'sub'/'child' in that cell, or a larger left
    margin, makes the row a subheading."""
    per_line: Dict[int, int] = {}
    for r in p.rows:
        per_line[r["line"]] = per_line.get(r["line"], 0) + 1
    out: List[ParsedLine] = []
    for r in p.rows:
        pos = Pos(r["line"], r["col"] if per_line[r["line"]] > 1 else None)
        level = 1 if r["sub"] else 0
        if locators in ("anchor", "auto", "none"):
            pl = _parse_see(r["text"], level, pos, "unknown", split=False)
            if locators != "none":
                pl.locators = [anchor_locator(h, pos, t, p.ids)
                               for h, t in r["links"]]
        else:
            pl = parse_content(r["text"], level, pos, "unknown", "numeric")
        out.append(pl)
    meta["layout"] = "table"
    return out


def read_html(text: str, meta: Optional[dict] = None,
              locators: str = "numeric") -> List[ParsedLine]:
    """Parse an HTML index (``<ul>``/``<ol>``/``<dl>``; failing that, a
    ``<p>``/``<br>`` index or a ``<table>`` of rows).

    ``locators``: numeric | auto | anchor | none (see ``parse_content``).
    Items that share a source line (minified HTML) get a column in their
    position. Each ParsedLine carries its section label (``--sections``).
    In ``auto`` mode an item whose heading is itself link text is read in
    anchor mode, so 'Route 66' keeps its number.
    """
    meta = meta if meta is not None else {}
    p = _HTMLIndexParser()
    p.feed(text)
    p.close()
    while p.stack:
        p._flush(p.stack.pop())
    p._pflush()
    p._rflush()
    meta["ids"] = p.ids
    if not p.items:
        plines = p.plines
        if p.index_mark is not None and p.plines[p.index_mark:]:
            plines = p.plines[p.index_mark:]
        elif any(_MSO_INDEX_RE.search(pl["cls"]) for pl in p.plines):
            plines = [pl for pl in p.plines if _MSO_INDEX_RE.search(
                pl["cls"]) or re.search(r"indexheading", pl["cls"], re.I)]
        elif len(p.rows) >= 2:
            plines = []
        if plines:
            meta["groups"] = []
            return _read_html_lines(p, plines, meta, locators)
        if p.rows:
            meta["groups"] = list(p.groups)
            meta["style"] = "unknown"
            return _read_html_rows(p, meta, locators)
        raise ParseError("no <li>, <dt>, <dd>, <p>/<br> lines or table rows "
                         "found in HTML input")
    per_line: Dict[int, int] = {}
    for it in p.items:
        per_line[it["line"]] = per_line.get(it["line"], 0) + 1
    for it in p.items:
        it["pos"] = Pos(it["line"], it["col"]
                        if per_line[it["line"]] > 1 else None)
        it["linkhead"] = locators == "auto" and it["tag"] != "dd" and \
            _link_heading(it["text"], it["links"])
    textmode = "none" if locators in ("anchor", "none") else "numeric"
    style = detect_sep_style(
        parse_content(it["text"], 0, it["pos"], "unknown", textmode).sep_kind
        for it in p.items if it["tag"] != "dd" and not it["linkhead"])
    meta["style"] = style
    meta["groups"] = list(p.groups)
    out: List[ParsedLine] = []
    for it in p.items:
        level, text_, line, tag = it["level"], it["text"], it["pos"], \
            it["tag"]
        section = p.sections[it["section"]] if it["section"] >= 0 else None
        # <dt>heading</dt><dd>12, 40</dd>: a dd holding only locators/see
        if tag == "dd" and out:
            probe = parse_content("x, " + text_, level, line)
            toks = [t for t in re.split(r"\s*,\s*", text_) if t.strip()]
            only_locs = toks and all(parse_locator(t, line) for t in toks)
            link_only = bool(it["links"]) and not re.sub(
                r"[\s,;.]", "", _strip_link_texts(text_, it["links"]))
            if locators in ("anchor", "auto") and link_only and \
                    not (locators == "auto" and only_locs):
                out[-1].locators.extend(anchor_locator(h, line, t, p.ids)
                                        for h, t in it["links"])
                continue
            if locators != "none" and (only_locs or
                                       re.match(r"^\(?[*_]*see\b", text_,
                                                re.I)):
                prev = out[-1]
                if locators != "anchor":
                    prev.locators.extend(probe.locators)
                prev.see.extend(probe.see)
                prev.see_also.extend(probe.see_also)
                if probe.see_also:
                    prev.placement = "after" if prev.locators else None
                continue
        if it["linkhead"]:
            pl = _parse_see(text_.strip(), level, line, style, split=False)
            _html_anchor_locs(pl, it["links"], line, p.ids)
        else:
            pl = parse_content(text_, level, line, style, textmode)
            if locators == "anchor" or (locators == "auto" and
                                        not pl.locators):
                _html_anchor_locs(pl, it["links"], line, p.ids)
        pl.section = section
        out.append(pl)
    return out


def _strip_link_texts(text: str, links: List[Tuple[str, str]]) -> str:
    for _, lt in links:
        if lt:
            text = text.replace(lt, "", 1)
    return text


def detect_format(path: str, text: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".ind":
        return "ind"
    if ext in (".html", ".htm", ".xhtml"):
        return "html"
    if ext in (".txt", ".md", ".markdown", ".text"):
        return "text"
    if re.search(r"\\begin\{theindex\}|^\s*\\item\b", text, re.M):
        return "ind"
    if re.search(r"<(ul|dl|ol|html|li)\b", text, re.I):
        return "html"
    return "text"


# ---------------------------------------------------------------------------
# Tree building
# ---------------------------------------------------------------------------
def build_tree(lines: List[ParsedLine]) -> List[Entry]:
    roots: List[Entry] = []
    stack: List[Entry] = []
    for pl in lines:
        while stack and stack[-1].level >= pl.level:
            stack.pop()
        parent = stack[-1] if stack else None
        if pl.see_line_only and parent is not None:
            # a 'see also' / 'see' line nested under its heading
            parent.see.extend(pl.see)
            if pl.see_also:
                parent.see_also.extend(pl.see_also)
                parent.see_also_placement = "sub"
            continue
        if not pl.heading:
            continue
        e = Entry(heading=pl.heading, level=pl.level, line=pl.line,
                  locators=pl.locators, see=pl.see, see_also=pl.see_also,
                  see_also_placement=pl.placement, parent=parent)
        (parent.children if parent else roots).append(e)
        stack.append(e)
    return roots


def walk(entries: List[Entry]) -> Iterable[Entry]:
    for e in entries:
        yield e
        yield from walk(e.children)


def sibling_groups(roots: List[Entry]) -> Iterable[Tuple[Optional[Entry],
                                                          List[Entry]]]:
    yield None, roots
    for e in walk(roots):
        if e.children:
            yield e, e.children


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
@dataclass
class Options:
    filing: str = "word"                  # word | letter | identifier
    numerals: str = "numeric"
    max_locators: int = 6
    func_words: bool = False
    roman: str = "strict"                 # strict | off
    roman_list: frozenset = frozenset()   # numerals always read as numbers
    inversion: str = "after"              # before | after (8.5)
    subheading_order: str = "alpha"       # alpha | page (8.6)
    locale_fold: str = "basic"            # basic | none
    skip_until: Optional[str] = None      # regex: text lines before skipped
    auto_preamble: bool = True            # detect a leading prose note
    locators: str = "auto"                # auto | numeric | anchor | none
    sections: str = "split"               # split | merge (HTML sections)
    only_section: Optional[str] = None    # regex: lint matching sections
    heading_regex: Optional[str] = None   # group 1 = filing text
    qualifier_suffixes: tuple = ()        # e.g. ("-api", "-guide")
    case_significant: Optional[bool] = None   # None: on with identifier
    compare_locales: tuple = ()           # locale names (--compare-locales)
    ignore_honorifics: bool = False       # Mr, Dr, Prof ... in inverted names
    verbose_pairs: bool = False           # keep pairs a ROOTCAUSE explains

    @property
    def case_sig(self) -> bool:
        if self.case_significant is None:
            return self.filing == "identifier"
        return self.case_significant


_MODE_NAMES = {"word": "word-by-word", "letter": "letter-by-letter",
               "identifier": "identifier (segmented, word-by-word)"}


def _mode_name(opts: Options) -> str:
    return _MODE_NAMES.get(opts.filing, opts.filing)


# Honorifics and titles that an inverted personal name may carry after the
# comma ('Forbes, Mr. D.', 'Wollaston, Mr., on insects'). 'M.' is left out:
# it cannot be told from an initial.
_HONORIFIC_RE = re.compile(
    r"(?<=,)\s*(?:(?:Mr|Mrs|Ms|Messrs|Mme|Mlle|Miss|Dr|Prof|Professor|Sir|"
    r"Dame|Lord|Lady|Rev|Revd|Reverend|Hon|Capt|Captain|Col|Colonel|Gen|"
    r"General|Maj|Major|Lieut|Lt|Sgt|Fr|Father|Sr|Sister|Herr|Frau|Dean|"
    r"Bishop)\.?(?=[\s,]|$)\s*,?\s*)+")


def strip_honorifics(heading: str) -> str:
    """'Forbes, Mr. D.' -> 'Forbes, D.' (only after an inverting comma)."""
    if "," not in heading:
        return heading
    t = _HONORIFIC_RE.sub(" ", heading)
    t = re.sub(r"\s+", " ", t).strip()
    return t.rstrip(" ,") if t.rstrip(" ,") else heading


def filing_text(heading: str, opts: Options) -> str:
    """The part of a heading that files (before identifier segmentation).

    ``--heading-regex``: group 1 of a match is the filing text, so display
    noise such as 'func (r Recv)' or a signature is not filed on; the rest
    acts as a leading qualifier (it only breaks ties). ``--qualifier-suffix``:
    a heading ending in one of the suffixes files as 'term (suffix)'.
    """
    t = heading
    if opts.ignore_honorifics:
        t = strip_honorifics(t)
    if opts.heading_regex:
        m = re.search(opts.heading_regex, t)
        if m and m.groups() and m.group(1):
            t = m.group(1)
    for suf in opts.qualifier_suffixes:
        if suf and len(t) > len(suf) and t.lower().endswith(suf.lower()):
            core = t[:-len(suf)].rstrip(" -_")
            if core:
                t = f"{core} ({suf.strip(' -_')})"
                break
    return t


def key_text(heading: str, opts: Options) -> str:
    t = filing_text(heading, opts)
    return segment_identifier(t) if opts.filing == "identifier" else t


def okey(text: str, opts: Options, mode: Optional[str] = None,
         func_words: bool = False, *, keep_case: bool = False,
         lf: Optional[str] = None, raw: bool = False) -> tuple:
    """Sort key of a heading with the filing options in ``opts``.

    Word/letter: (group, elements). Identifier: (group, elements, heading)
    - the raw heading is the final tie-break, so case-distinct identifiers
    keep a total, predictable order. ``raw`` skips ``filing_text`` (the
    text is already a filing text).
    """
    t = filing_text(text, opts) if not raw else text
    m = mode or opts.filing
    lf = lf or opts.locale_fold
    if opts.filing == "identifier":
        t = segment_identifier(t)
    if m == "identifier":
        g, el = sort_key(t, "word", func_words, roman="off",
                         inversion=opts.inversion, locale_fold=lf,
                         keep_case=keep_case)
        return g, el, text
    return sort_key(t, m, func_words, roman=opts.roman,
                    roman_list=opts.roman_list, inversion=opts.inversion,
                    locale_fold=lf, keep_case=keep_case)


def _q(s: str) -> str:
    return '"' + s + '"'


def check_duplicates(roots: List[Entry], opts: Optional[Options] = None
                     ) -> List[Finding]:
    """8.1 duplicates. In case-significant mode (``--case-significant``,
    on with ``--filing identifier``) headings that differ only by case or
    separators are distinct identifiers: info 3.10-HOMOGRAPH, not a
    DUPLICATE warning. Identical raw headings are always DUPLICATE."""
    opts = opts or Options()
    lf = opts.locale_fold
    out = []
    for parent, sibs in sibling_groups(roots):
        seen: Dict[object, Entry] = {}
        for e in sibs:
            if opts.case_sig:
                k: object = okey(e.heading, opts)[:2]
            else:
                k = norm_heading(e.heading, lf)
            if k in seen:
                first = seen[k]
                where = "subheading" if parent else "heading"
                same = re.sub(r"\s+", " ", first.heading.strip()) == \
                    re.sub(r"\s+", " ", e.heading.strip())
                if opts.case_sig and not same:
                    ft = filing_text(e.heading, opts)
                    extra = (f" (both file as {_q(ft)} under "
                             f"--heading-regex)" if opts.heading_regex and
                             (ft != e.heading or
                              filing_text(first.heading, opts) !=
                              first.heading) else "")
                    out.append(Finding("ISO999-3.10-HOMOGRAPH", e.line,
                        f"{where} {_q(e.heading)} and {_q(first.heading)} "
                        f"(line {first.line}) are distinct identifiers "
                        f"differing only by case or separators{extra}; "
                        f"they file together - consider a qualifier so "
                        f"readers can tell them apart"))
                    continue
                how = ("identical" if first.heading == e.heading else
                       "differs only in case, spacing or accents from")
                out.append(Finding("ISO999-8.1-DUPLICATE", e.line,
                    f"{where} {_q(e.heading)} {how} {_q(first.heading)} at "
                    f"line {first.line}; merge them, or add a qualifier if "
                    f"they are different things",
                    pair=(first.heading, e.heading, None)))
            else:
                seen[k] = e
    return out


def _order_eligible(e: Entry, opts: Options) -> bool:
    if opts.numerals == "ignore":
        return okey(e.heading, opts)[0] != 0
    return True


def _systematic(sibs: List[Entry]) -> Optional[str]:
    """Name the non-alphabetical order a subheading group follows, if any.

    Returns "numeric" (ascending leading numbers or dates, e.g. years), or
    "page" (3+ subheadings ordered by first locator), or None. Anchor
    locators count only when their #fragment target position is known.
    """
    nums = []
    for e in sibs:
        m = re.match(r"^\W*(\d+)", e.heading)
        if not m:
            nums = None
            break
        nums.append(int(m.group(1)))
    if nums and all(a <= b for a, b in zip(nums, nums[1:])):
        return "numeric"
    # page order is only credible evidence with 3+ subheadings
    if len(sibs) >= 3 and all(e.locators for e in sibs):
        if any(e.locators[0].anchor is not None and
               e.locators[0].target_pos is None for e in sibs):
            return None
        firsts = [e.locators[0].order_key() for e in sibs]
        if all(a <= b for a, b in zip(firsts, firsts[1:])):
            return "page"
    return None


def _first_diff_is_digit(a: tuple, b: tuple) -> bool:
    """Is the first differing sort-key element of a and b a digit run?"""
    for x, y in zip(a, b):
        if x != y:
            return x[0] == _DIGITS or y[0] == _DIGITS
    return False


def _leaked_keys(e: Entry, opts: Options, fw: bool) -> List[tuple]:
    """Sort keys ``e`` would get if its cross-reference text were filed too.

    Variants: 'heading see target' and 'heading target' (the keyword
    itself may or may not have leaked). Empty if ``e`` has no references.
    """
    out = []
    head = filing_text(e.heading, opts)
    for kw, refs in (("see", e.see), ("see also", e.see_also)):
        if not refs:
            continue
        tgt = "; ".join(r.target for r in refs)
        for txt in (f"{head} {kw} {tgt}", f"{head} {tgt}"):
            out.append(okey(txt, opts, None, fw, raw=True)[:2])
    return out


def _xref_leak(prev: Entry, cur: Entry, opts: Options, fw: bool) -> bool:
    """Would the misordered pair be in order with cross-ref text in the key?
    """
    lp = _leaked_keys(prev, opts, fw)
    lc = _leaked_keys(cur, opts, fw)
    if not lp and not lc:
        return False
    kp = lp or [okey(prev.heading, opts, None, fw)[:2]]
    kc = lc or [okey(cur.heading, opts, None, fw)[:2]]
    return any(a <= b for a in kp for b in kc)


def _case_caused(prev: Entry, cur: Entry, opts: Options, fw: bool) -> bool:
    """8.1-CASE-ORDER test: the pair is misordered once case is folded (with
    diacritics left alone, so accent effects do not count) but in order
    under a case-sensitive code-point comparison - the mark of a sort that
    files capitals before lower case."""
    a = okey(prev.heading, opts, None, fw, lf="none")[:2]
    b = okey(cur.heading, opts, None, fw, lf="none")[:2]
    if not b < a:
        return False
    ra = okey(prev.heading, opts, None, fw, lf="none", keep_case=True)[:2]
    rb = okey(cur.heading, opts, None, fw, lf="none", keep_case=True)[:2]
    return ra <= rb


def _first_term(heading: str, opts: Options) -> Tuple[str, str]:
    """(first term, folded filing text) - hyphens/dashes/slashes break
    words except in letter-by-letter filing."""
    t = fold(_MARKUP_RE.sub("", key_text(heading, opts)),
             opts.locale_fold).strip()
    if opts.filing != "letter":
        t = re.sub(r"[-‐‑‒–—/]", " ", t)
        t = re.sub(r"\s+", " ", t)
    m = re.match(r"[^\s,(]+", t)
    return (m.group(0) if m else ""), t


def _qualifier_pair(prev: Entry, cur: Entry, opts: Options) -> bool:
    """8.5 applies: one heading's term (the text before any '(' qualifier
    or inverting comma) equals, or is a leading word run of, the other's -
    i.e. the pair is bare term / term (qualifier) / term, x / longer
    heading beginning with the term. Two longer headings that merely share
    a first word are an ordinary 8.2 case."""
    _, ta = _first_term(prev.heading, opts)
    _, tb = _first_term(cur.heading, opts)

    def core(t: str) -> str:
        return re.split(r"\s*[(,]", t, maxsplit=1)[0].strip()
    ca, cb = core(ta), core(tb)
    if not ca or not cb:
        return False
    if ca == cb:
        return ta != tb
    short, long_ = (ca, cb) if len(ca) < len(cb) else (cb, ca)
    return long_.startswith(short + " ")


# Abbreviations that begin a heading, with their spelled-out forms (7.3.6).
_ABBREVS = [
    (re.compile(r"^St\.?(?=\s)"), "Saint"),
    (re.compile(r"^Ste\.?(?=\s)"), "Sainte"),
    (re.compile(r"^Mt\.?(?=\s)"), "Mount"),
    (re.compile(r"^Ft\.?(?=\s)"), "Fort"),
    (re.compile(r"^Dr\.?(?=\s)"), "Doctor"),
    (re.compile(r"^Mc(?=[A-Z])"), "Mac"),
    (re.compile(r"^M['\u2019](?=[A-Z])"), "Mac"),
]


def _abbrev_pair(prev: Entry, cur: Entry, opts: Options, fw: bool
                 ) -> Optional[str]:
    """7.3.6: is a misordered pair explained by an abbreviation at the
    start of one heading being filed as if spelled out ('McDonnell' as
    'MacDonnell', before 'Madeira') or run into the next word ('St.
    Helena' as 'sthelena', after 'Sterility')? Returns the reason."""
    for h, other in ((prev, cur), (cur, prev)):
        ft = filing_text(h.heading, opts)
        for rx, exp in _ABBREVS:
            m = rx.match(ft)
            if not m:
                continue
            tok = m.group(0)
            spelled = exp + ft[m.end():]
            kh = okey(spelled, opts, None, fw, raw=True)[:2]
            ko = okey(filing_text(other.heading, opts), opts, None, fw,
                      raw=True)[:2]
            if (h is prev and kh <= ko) or (h is cur and ko <= kh):
                return (f"{_q(h.heading)} begins with the abbreviation "
                        f"{_q(tok)}, which seems to have been filed as if "
                        f"spelled out ({_q(exp)}); abbreviations file as "
                        f"written (7.3.6) - or add a 'see' from the "
                        f"spelled-out form")
            letters = re.sub(r"\W", "", tok).lower()
            ow = first_word(other.heading, opts.locale_fold)
            kp = okey(prev.heading, opts, "letter", fw)[:2]
            kc = okey(cur.heading, opts, "letter", fw)[:2]
            if kp <= kc and ow.startswith(letters) and \
                    ow.rstrip(".") != letters:
                return (f"{_q(h.heading)} begins with the abbreviation "
                        f"{_q(tok)}, which seems to have been run into the "
                        f"next word (as if one word); abbreviations file as "
                        f"written, as a word of their own (7.3.6)")
    return None


_INITIALISM_DOTTED_RE = re.compile(r"^((?:[A-Z]\.){2,})")
_INITIALISM_SPACED_RE = re.compile(r"^([A-Z](?: [A-Z])+)(?=[\s,(]|$)")


def _initialism_pair(prev: Entry, cur: Entry, opts: Options, fw: bool
                     ) -> Optional[str]:
    """7.3.6 (initialisms): is a misordered pair explained by an
    initialism filed by its punctuation - 'N.A.T.O.' filed as separate
    letters 'N A T O' (ahead of every N word) although it is keyed here,
    like 'NATO', as one word; or 'U N' filed as one word 'UN' although
    written with spaces? Returns the reason."""
    if opts.filing == "identifier":
        return None
    for h, other in ((prev, cur), (cur, prev)):
        ft = filing_text(h.heading, opts)
        m = _INITIALISM_DOTTED_RE.match(ft)
        if m:
            alt = " ".join(m.group(1).replace(".", " ").split()) + \
                ft[m.end():]
            how = ("as separate one-letter words, by its full stops, "
                   "while an unpointed initialism files as one word")
        else:
            m = _INITIALISM_SPACED_RE.match(ft)
            if not m:
                continue
            alt = m.group(1).replace(" ", "") + ft[m.end():]
            how = "as one word although it is written with spaces"
        kh = okey(alt, opts, None, fw, raw=True)[:2]
        ko = okey(filing_text(other.heading, opts), opts, None, fw,
                  raw=True)[:2]
        if (h is prev and kh <= ko) or (h is cur and ko <= kh):
            return (f"the initialism {_q(m.group(1))} in {_q(h.heading)} "
                    f"seems to be filed {how}; initialisms should file the "
                    f"same way every time, whatever their punctuation "
                    f"(7.3.6)")
    return None


def _strip_front_article(heading: str, opts: Options) -> Optional[str]:
    """The filing text without a leading capitalised article ('The
    Orchard' -> 'Orchard'), or None if there is none."""
    ft = _MARKUP_RE.sub("", filing_text(heading, opts)).strip()
    m = _ART_INITIAL_RE.match(ft)
    return ft[m.end(1):].lstrip() if m else None


def _article_pair(prev: Entry, cur: Entry, opts: Options, fw: bool
                  ) -> Optional[str]:
    """7.3.4.2: is a misordered pair in order once the leading article of
    one heading is ignored ('The Orchard' filed among the O's)?"""
    if opts.filing == "identifier":
        return None
    for h, other in ((prev, cur), (cur, prev)):
        alt = _strip_front_article(h.heading, opts)
        if alt is None:
            continue
        kh = okey(alt, opts, None, fw, raw=True)[:2]
        ko = okey(other.heading, opts, None, fw)[:2]
        if (h is prev and kh <= ko) or (h is cur and ko <= kh):
            return (f"{_q(h.heading)} keeps its leading article in front "
                    f"but is filed as if the article were absent (the "
                    f"French practice); keep the method the same for every "
                    f"such heading and state it in the note - English "
                    f"practice moves the article to the end (7.3.4.2)")
    return None


def _article_filing(findings: List[Finding],
                    sequences: List[Tuple[Optional[str], List[Entry]]],
                    opts: Options) -> List[Finding]:
    """7.3.4.2: headings that keep a leading article in front must all be
    filed the same way - on the article, or ignoring it. Evidence per
    heading: it fits between its neighbours under one reading only. Both
    kinds present: one warn (the per-pair ARTICLE findings stay). Only
    'ignoring' evidence: the index files front articles consistently the
    French way, so the per-pair findings become one info."""
    if opts.filing == "identifier":
        return findings
    under: List[Entry] = []
    ignoring: List[Entry] = []
    for _, roots in sequences:
        for parent, sibs in sibling_groups(roots):
            seq = [e for e in sibs if _order_eligible(e, opts)]
            fw = opts.func_words and parent is not None
            keys = [okey(e.heading, opts, None, fw)[:2] for e in seq]
            for i, e in enumerate(seq):
                alt = _strip_front_article(e.heading, opts)
                if alt is None:
                    continue
                ka = okey(alt, opts, None, fw, raw=True)[:2]

                def fits(k: tuple) -> bool:
                    return ((i == 0 or keys[i - 1] <= k) and
                            (i == len(seq) - 1 or k <= keys[i + 1]))
                lit, ign = fits(keys[i]), fits(ka)
                if lit and not ign:
                    under.append(e)
                elif ign and not lit:
                    ignoring.append(e)
    pairs = [f for f in findings if f.rule == "ISO999-7.3.4.2-ARTICLE" and
             f.pair is not None]
    if not ignoring:
        return findings

    def ex(es: List[Entry]) -> str:
        return ", ".join(f"{_q(e.heading)} (line {e.line})" for e in es[:3]) \
            + (f" (+{len(es) - 3} more)" if len(es) > 3 else "")
    if under:
        return findings + [Finding("ISO999-7.3.4.2-ARTICLE", ignoring[0].line,
            f"headings that keep a leading article in front are filed two "
            f"ways: under the article in {len(under)} ({ex(under)}) and "
            f"ignoring it in {len(ignoring)} ({ex(ignoring)}); one index "
            f"must treat leading articles one way (7.3.4.2)")]
    drop = {id(f) for f in pairs}
    return [f for f in findings if id(f) not in drop] + [
        Finding("ISO999-7.3.4.2-ARTICLE", ignoring[0].line,
            f"{len(ignoring)} heading(s) keep a leading article in front "
            f"and are consistently filed as if it were absent ({ex(ignoring)}"
            f"): the French practice. Consistent, but say so in the "
            f"introductory note; English practice moves the article to the "
            f"end (7.3.4.2)", severity="info")]


def _honorific_pair(prev: Entry, cur: Entry, opts: Options, fw: bool
                    ) -> bool:
    """Is the pair in order once honorifics in inverted names are ignored
    ('Forbes, Mr. D.' before 'Forbes, E.')?"""
    if opts.ignore_honorifics:
        return False
    a, b = strip_honorifics(prev.heading), strip_honorifics(cur.heading)
    if a == prev.heading and b == cur.heading:
        return False
    return okey(a, opts, None, fw)[:2] <= okey(b, opts, None, fw)[:2]


def _keep_set(keys: List[tuple]) -> set:
    """Indices of one longest non-decreasing subsequence of ``keys``."""
    import bisect
    tails: List[tuple] = []
    tails_idx: List[int] = []
    prev = [-1] * len(keys)
    for i, k in enumerate(keys):
        j = bisect.bisect_right(tails, k)
        if j == len(tails):
            tails.append(k)
            tails_idx.append(i)
        else:
            tails[j] = k
            tails_idx[j] = i
        prev[i] = tails_idx[j - 1] if j > 0 else -1
    out = set()
    i = tails_idx[-1] if tails_idx else -1
    while i >= 0:
        out.add(i)
        i = prev[i]
    return out


def _runs_finding(parent: Entry, seq: List[Entry], restarts: List[int]
                  ) -> Optional[Finding]:
    """8.6-RUNS: 2+ internally alphabetical runs separated by restarts of
    the alphabet. Needs 3+ subheadings, runs averaging 2+ entries and at
    most one run of a single entry (a lone constructor before a run of
    methods is a run; 'c b a' is plain disorder)."""
    if not restarts or len(seq) < 3:
        return None
    bounds = [0] + restarts + [len(seq)]
    sizes = [b - a for a, b in zip(bounds, bounds[1:])]
    if len(sizes) * 2 > len(seq) or sizes.count(1) > 1:
        return None
    where = ", ".join(f"{_q(seq[i].heading)} (line {seq[i].line})"
                      for i in restarts)
    return Finding("ISO999-8.6-RUNS", parent.line,
        f"{len(sizes)} alphabetical runs restart without a label under "
        f"{_q(parent.heading)} (run sizes {'+'.join(map(str, sizes))}; "
        f"restart at {where}) - declare the grouping (label each run, or "
        f"explain it in the introductory note) or merge the runs into one "
        f"alphabetical sequence", members=tuple(e.heading for e in seq))


def check_filing(roots: List[Entry], opts: Options,
                 skip: Optional[set] = None) -> List[Finding]:
    """Order checks. ``skip``: ids of top-level entries whose misorder with
    the previous heading is already explained (8.1-CASEBLOCK restart)."""
    skip = skip or set()
    out: List[Finding] = []
    word_ev = letter_ev = 0
    word_ex: Optional[Tuple[Entry, Entry]] = None
    letter_ex: Optional[Tuple[Entry, Entry]] = None
    mname = _mode_name(opts)
    top_displaced: List[Entry] = []
    top_n = 0
    sub_displaced = sub_groups = 0
    for parent, sibs in sibling_groups(roots):
        seq = [e for e in sibs if _order_eligible(e, opts)]
        # mode evidence from adjacent pairs
        for a, b in zip(seq, seq[1:]):
            kw_a, kw_b = okey(a.heading, opts, "word"), \
                okey(b.heading, opts, "word")
            kl_a, kl_b = (okey(a.heading, opts, "letter"),
                          okey(b.heading, opts, "letter"))
            if kw_a < kw_b and kl_a > kl_b:
                word_ev += 1
                word_ex = word_ex or (a, b)
            elif kw_a > kw_b and kl_a < kl_b:
                letter_ev += 1
                letter_ex = letter_ex or (a, b)
        use_fw = opts.func_words and parent is not None
        # identifier keys carry a raw-string tie-break; a pair that differs
        # only in that tie-break (case variants) is not a misorder
        keys = [okey(e.heading, opts, None, use_fw)[:2] for e in seq]
        if parent is None:
            top_n += len(seq)
        bad = [i for i in range(1, len(seq)) if keys[i] < keys[i - 1]]
        if not bad:
            continue
        keep = _keep_set(keys)
        displaced = [i for i in range(len(seq)) if i not in keep]
        if parent is None:
            top_displaced.extend(seq[i] for i in displaced)
        else:
            sub_displaced += len(displaced)
            sub_groups += 1
        leak = {i: _xref_leak(seq[i - 1], seq[i], opts, use_fw)
                for i in bad}
        case = {i: (not leak[i]) and
                _case_caused(seq[i - 1], seq[i], opts, use_fw) for i in bad}
        if parent is not None:
            sysname = _systematic(sibs)
            restarts = [i for i in bad if not leak[i] and not case[i]]
            runs = _runs_finding(parent, seq, restarts)
            if sysname == "numeric":
                out.append(Finding("ISO999-8.6-SYSTEMATIC", parent.line,
                    f"subheadings under {_q(parent.heading)} are not "
                    f"alphabetical but follow ascending numeric/date order; "
                    f"acceptable if deliberate and explained in an "
                    f"introductory note"))
                continue
            if sysname == "page" and opts.subheading_order == "page":
                out.append(Finding("ISO999-8.6-SYSTEMATIC", parent.line,
                    f"subheadings under {_q(parent.heading)} follow page "
                    f"(first-locator) order, declared with "
                    f"--subheading-order page; explain it in the "
                    f"introductory note"))
                continue
            if runs is not None:
                out.append(runs)
                # the restarts are explained; case-caused pairs inside the
                # runs are still reported below
                bad = [i for i in bad if case[i] or leak[i]]
            elif sysname == "page":
                out.append(Finding("ISO999-8.6-PAGEORDER", parent.line,
                    f"{len(sibs)} subheadings under {_q(parent.heading)} are "
                    f"in page (first-locator) order, not alphabetical; "
                    f"page order is usually an unsorted dump rather than a "
                    f"systematic arrangement - sort them, or if the order "
                    f"is deliberate pass --subheading-order page and "
                    f"explain it in the introductory note",
                    members=tuple(e.heading for e in seq)))
                continue
        disp = set(displaced)
        done_blocks: set = set()
        for i in bad:
            prev, cur = seq[i - 1], seq[i]
            if parent is None and id(cur) in skip:
                continue
            # the displaced block this break belongs to (collapse blocks)
            block: Optional[Tuple[int, int]] = None
            if i in disp:
                t = i
                while t + 1 < len(seq) and t + 1 in disp:
                    t += 1
                s = i
                while s - 1 >= 0 and s - 1 in disp:
                    s -= 1
                block = (s, t)
            elif i - 1 in disp:
                s = i - 1
                while s - 1 >= 0 and s - 1 in disp:
                    s -= 1
                block = (s, i - 1)
            if block is not None:
                if block in done_blocks:
                    continue
                done_blocks.add(block)
            btxt = ""
            if block is not None and block[1] > block[0]:
                s, t = block
                btxt = (f"; this is one block of {t - s + 1} consecutive "
                        f"out-of-place entries ({_q(seq[s].heading)} ... "
                        f"{_q(seq[t].heading)}, lines {seq[s].line}-"
                        f"{seq[t].line})")
            if leak[i]:
                ref = cur if (cur.see or cur.see_also) else prev
                out.append(Finding("ISO999-8.7-SORTKEY", cur.line,
                    f"{_q(cur.heading)} files before {_q(prev.heading)} "
                    f"(line {prev.line}) by heading alone, but the pair is "
                    f"in order if the cross-reference text of "
                    f"{_q(ref.heading)} (line {ref.line}) is treated as "
                    f"part of the heading; the reference seems to have "
                    f"leaked into the sort key - file by the heading "
                    f"only{btxt}"))
                continue
            if keys[i][0] == 0 or keys[i - 1][0] == 0:
                rule = "ISO999-8.3-ORDER"
                why = ("numeral-initial headings should form a numerically "
                       "ordered group ahead of the alphabetical sequence; "
                       "digits inside headings compare by value")
            elif _first_diff_is_digit(keys[i - 1][1], keys[i][1]):
                rule = "ISO999-8.3-ORDER"
                why = ("the headings first differ at a number, and digits "
                       "inside a heading file by numeric value, not digit "
                       "by digit (8.3 d)")
            elif _abbrev_pair(prev, cur, opts, use_fw):
                rule = "ISO999-7.3.6-ABBREV"
                why = _abbrev_pair(prev, cur, opts, use_fw)
            elif _initialism_pair(prev, cur, opts, use_fw):
                rule = "ISO999-7.3.6-ABBREV"
                why = _initialism_pair(prev, cur, opts, use_fw)
            elif _article_pair(prev, cur, opts, use_fw):
                rule = "ISO999-7.3.4.2-ARTICLE"
                why = _article_pair(prev, cur, opts, use_fw)
            elif case[i]:
                rule = "ISO999-8.1-CASE-ORDER"
                why = ("the pair is in order only if capitals file before "
                       "lower case (a case-sensitive, code-point sort); "
                       "upper and lower case should file together (8.1)")
            elif _honorific_pair(prev, cur, opts, use_fw):
                rule = "ISO999-7.3.1-HONORIFIC"
                why = ("the pair is in order if the honorific in the "
                       "inverted name is ignored, a common convention for "
                       "personal names (7.3.1); state it in the note, or "
                       "pass --ignore-honorifics")
            elif _qualifier_pair(prev, cur, opts):
                rule = "ISO999-8.5-ORDER"
                inv = ("before 'term (qualifier)'" if opts.inversion ==
                       "before" else "after 'term (qualifier)', at the head "
                       "of the longer headings")
                why = ("for a shared first term the expected sequence is: "
                       "bare term, then term with qualifier, then longer "
                       "headings beginning with the term (inverted "
                       f"'term, x' files {inv}: --inversion "
                       f"{opts.inversion})")
            elif parent is not None:
                rule = "ISO999-8.6-ORDER"
                why = f"subheadings of {_q(parent.heading)} are out of order"
            else:
                rule = "ISO999-8.2-ORDER"
                why = f"out of {mname} order"
            hint = ""
            if parent is not None and not opts.func_words:
                fk = [okey(e.heading, opts, None, True)[:2] for e in seq]
                if fk[i] >= fk[i - 1]:
                    hint = ("; would be in order if leading prepositions/"
                            "conjunctions were ignored (--ignore-function-"
                            "words) - state that choice in the index note")
            out.append(Finding(rule, cur.line,
                f"{_q(cur.heading)} files before {_q(prev.heading)} "
                f"(line {prev.line}) under {mname} "
                f"filing: {why}{hint}{btxt}",
                pair=(prev.heading, cur.heading,
                      parent.heading if parent is not None else None),
                group=id(parent) if parent is not None else None))
    if top_displaced or sub_displaced:
        names = ", ".join(_q(e.heading) for e in top_displaced[:20])
        more = (f" (+{len(top_displaced) - 20} more)"
                if len(top_displaced) > 20 else "")
        subs = (f"; plus {sub_displaced} out-of-place subheading(s) in "
                f"{sub_groups} group(s)" if sub_displaced else "")
        first = top_displaced[0].line if top_displaced else 0
        out.append(Finding("ISO999-8-DISPLACED", first,
            f"{len(top_displaced)} of {top_n} top-level entries are out of "
            f"place under {mname} filing (entries minus the longest "
            f"in-order subsequence){subs}"
            + (f": {names}{more}" if names else "")))
    # report detected method
    if word_ev and not letter_ev:
        detected = "appears to be filed word-by-word"
    elif letter_ev and not word_ev:
        detected = "appears to be filed letter-by-letter"
    elif not word_ev and not letter_ev:
        detected = ("gives no evidence either way (no adjacent headings "
                    "distinguish the two methods)")
    else:
        detected = "mixes both filing methods"
    msg = (f"index {detected} "
           f"({word_ev} adjacent pair(s) fit only word-by-word, "
           f"{letter_ev} fit only letter-by-letter); checking with "
           f"--filing {opts.filing}")
    if opts.filing in ("word", "letter"):
        other = "letter" if opts.filing == "word" else "word"
        if detected.endswith(other + "-by-" + other):
            msg += (f"; consider --filing {other} if that is the intended "
                    f"method")
    out.insert(0, Finding("ISO999-8.2-MODE", 0, msg))
    if word_ev and letter_ev and word_ex and letter_ex:
        (a1, b1), (a2, b2) = word_ex, letter_ex
        out.append(Finding("ISO999-8.2-MIXED", b2.line if opts.filing ==
                           "word" else b1.line,
            f"both filing methods appear: {_q(a1.heading)} before "
            f"{_q(b1.heading)} (line {b1.line}) is word-by-word, but "
            f"{_q(a2.heading)} before {_q(b2.heading)} (line {b2.line}) is "
            f"letter-by-letter; pick one and apply it throughout"))
    return out


def check_locators(roots: List[Entry], opts: Options) -> List[Finding]:
    out: List[Finding] = []
    all_locs: List[Tuple[Entry, Locator]] = []
    for e in walk(roots):
        locs = e.locators
        all_locs.extend((e, l) for l in locs)
        label = _q(e.path())
        if len(locs) > opts.max_locators:
            out.append(Finding("ISO999-7.2.3.5-MAXLOC", e.line,
                f"{label} has {len(locs)} locators (limit "
                f"{opts.max_locators}); readers cannot tell them apart - "
                f"consider breaking them up with subheadings (heuristic "
                f"threshold)"))
        nums = [l for l in locs if l.numeric]
        # figure/table numbers ('fig. 3') are their own sequence
        pages = [l for l in nums if not l.wprefix]
        viol = [(a, b) for a, b in zip(pages, pages[1:])
                if b.order_key() < a.order_key()]
        if viol and all(b.roman and not a.roman and a.prefix == b.prefix
                        for a, b in viol):
            a, b = viol[0]
            inter = any(x.roman for x in pages) and any(
                pages[k].roman and not pages[k - 1].roman and
                k + 1 < len(pages) and not pages[k + 1].roman
                for k in range(1, len(pages)))
            how = (" - interleaved among the arabic numbers by value, as "
                   "if the locators were compared as plain integers and "
                   "the numbering sequence was dropped" if inter else "")
            out.append(Finding("ISO999-7.4.2-SEQORDER", e.line,
                f"{label}: roman (front-matter) locator {b.raw} follows "
                f"arabic {a.raw}{how}; the front matter comes first in the "
                f"document, so its sequence is normally listed first "
                f"(7.4.2.2.1; 7.4.3 illustrations)"))
        elif viol:
            a, b = viol[0]
            out.append(Finding("ISO999-7.4.3-ASCENDING", e.line,
                f"{label}: locator {b.raw} follows {a.raw}; locators are "
                f"normally listed in ascending order (7.4 shows this "
                f"but does not require it)"))
        seen: Dict[tuple, Locator] = {}
        for l in locs:
            k = l.identity()
            if k in seen:
                out.append(Finding("ISO999-7.4.3-DUPLICATE", e.line,
                    f"{label}: locator {l.raw} repeats {seen[k].raw}"))
            else:
                seen[k] = l
        for i, a in enumerate(nums):
            for b in nums[i + 1:]:
                if a.group() != b.group() or a.suffix or b.suffix or \
                        a.tag != b.tag:
                    continue
                if not (a.is_range or b.is_range) or \
                        a.identity() == b.identity():
                    continue
                a0, a1 = a.start, a.end if a.end is not None else a.start
                b0, b1 = b.start, b.end if b.end is not None else b.start
                if a1 < a0 or b1 < b0:
                    continue
                if max(a0, b0) <= min(a1, b1):
                    if (a0 <= b0 and b1 <= a1) or (b0 <= a0 and a1 <= b1):
                        kind = "is contained in"
                        inner, outer = (b, a) if a0 <= b0 and b1 <= a1 \
                            else (a, b)
                    else:
                        kind, inner, outer = "overlaps", b, a
                    out.append(Finding("ISO999-7.4.3-OVERLAP", e.line,
                        f"{label}: {inner.raw} {kind} {outer.raw}; merge "
                        f"into a single range or locator"))
        for l in locs:
            if l.end is not None and l.end <= l.start:
                out.append(Finding("ISO999-7.4.3.1-REVERSED", e.line,
                    f"{label}: range {l.raw} does not run forwards "
                    f"(end {l.end} vs start {l.start})"))
            if l.open_ended:
                out.append(Finding("ISO999-7.4.3.1-OPEN", e.line,
                    f"{label}: open-ended locator {l.raw}; give the first "
                    f"and last page of the discussion instead"))
            if l.passim:
                out.append(Finding("ISO999-7.4.3.2-PASSIM", e.line,
                    f"{label}: 'passim' in {l.raw}; list each page where "
                    f"the subject is treated instead"))
            if l.teen_issue:
                out.append(Finding("ISO999-7.4.3.1-TEENS", e.line,
                    f"{label}: elided range {l.raw}; by convention the "
                    f"10-19 band of each hundred keeps two digits"))
    # index-wide consistency: dash style
    ranges = [(e, l) for e, l in all_locs if l.dash]
    styles: Dict[str, int] = {}
    for _, l in ranges:
        styles[l.dash] = styles.get(l.dash, 0) + 1  # type: ignore[index]
    if len(styles) > 1:
        major = max(styles, key=lambda k: (styles[k], k == "en"))
        for e, l in ranges:
            if l.dash != major:
                out.append(Finding("ISO999-7.4.3.1-DASH", e.line,
                    f"{_q(e.path())}: range {l.raw} uses a {l.dash} dash "
                    f"but most ranges ({styles[major]}) use {major}; "
                    f"pick one range separator"))
    # index-wide consistency: elision
    el = [(e, l) for e, l in all_locs if l.elided is True]
    full = [(e, l) for e, l in all_locs if l.elided is False]
    if el and full:
        minority = el if len(el) <= len(full) else full
        form = "elided" if minority is el else "full"
        for e, l in minority:
            out.append(Finding("ISO999-7.4.3.1-ELISION", e.line,
                f"{_q(e.path())}: range {l.raw} is in {form} form while "
                f"{len(el)} range(s) are elided and {len(full)} are full; "
                f"the index should use one form throughout (full is the "
                f"normal choice)"))
    elif el:
        e, l = el[0]
        out.append(Finding("ISO999-7.4.3.1-ELISION", e.line,
            f"{len(el)} elided range(s) (first: {l.raw}); full ranges are "
            f"normally clearer - elide only under real space pressure",
            severity="info"))
    return out


_TAIL_SPLIT_RE = re.compile(r"(\s*;\s*|\s*,\s*|\s+)")


def _heading_locator_tail(heading: str, line: int
                          ) -> Tuple[List[Locator], List[str]]:
    """Arabic locator tokens at the end of a heading and the separators
    between them (and after the last one): the remains of a locator list
    that was not comma-separated ('glaciers 14 22', 'kelp, 4; 12')."""
    parts = _TAIL_SPLIT_RE.split(_MARKUP_RE.sub("", heading).strip())
    # parts: token, sep, token, sep, ... token ; a trailing ';' leaves ''
    run: List[Locator] = []
    seps: List[str] = []
    k = len(parts) - 1
    if parts and parts[-1] == "" and len(parts) >= 2:
        seps.append(parts[-2].strip() or " ")
        k -= 2
    while k >= 2:
        loc = parse_locator(parts[k], line)
        if loc is None or loc.roman or loc.tag:
            break
        run.insert(0, loc)
        seps.insert(0, parts[k - 1].strip() or " ")
        k -= 2
    # seps[0] joins the heading word and the run; drop it
    return run, seps[1:] if run else []


def check_locator_separators(roots: List[Entry], opts: Options
                             ) -> List[Finding]:
    """7.4.2.2.1 (7.4-03): successive page locators are separated by
    commas. A heading that ends in a run of page numbers separated by
    spaces or semicolons ('glaciers 14 22 90', 'kelp, 4; 12') is a locator
    list written without commas: the parser could not split it off."""
    if opts.locators in ("anchor", "none") or opts.filing == "identifier":
        return []
    out: List[Finding] = []
    for e in walk(roots):
        if any(l.anchor for l in e.locators):
            continue
        run, seps = _heading_locator_tail(e.heading, e.line)
        if not run:
            continue
        semi = ";" in seps
        allnums = run + [l for l in e.locators if l.numeric]
        asc = all(b.start > (a.end or a.start)
                  for a, b in zip(allnums, allnums[1:]))
        if semi and (len(run) >= 2 or e.locators or seps[-1:] == [";"]):
            kind = "semicolons"
        elif not semi and len(run) >= 2 and len(allnums) >= 3 and asc:
            kind = "spaces only"
        else:
            continue
        shown = " ".join(l.raw for l in run)
        out.append(Finding("ISO999-7.4.2-LOCSEP", e.line,
            f"{_q(e.path())}: locators {shown!r} are separated by {kind}, "
            f"not commas; successive locators should be separated by "
            f"commas (semicolons separate cross-reference targets, 7.5.1), "
            f"otherwise they are read as part of the heading"))
    return out


def _ex_locs(pairs: List[Tuple[Entry, Locator]], n: int = 3) -> str:
    return ", ".join(f"{l.raw} ({_q(e.heading)}, line {e.line})"
                     for e, l in pairs[:n]) + (
        f" (+{len(pairs) - n} more)" if len(pairs) > n else "")


_PSTYLE_NAMES = {"arabic:": "arabic + colon (2:45)",
                 "arabic/": "arabic + slash (2/45)",
                 "roman.": "roman + full stop (II.45)",
                 "roman:": "roman + colon (II:45)",
                 "letter": "letter joined (A3)",
                 "letter-": "letter + hyphen (A-3)",
                 "letter.": "letter + full stop (A.3)"}


def check_locator_sequences(roots: List[Entry], opts: Options
                            ) -> List[Finding]:
    """7.4.2.2.1 (7.4-04): several numbering sequences must be told apart,
    with one consistent prefix scheme.

    * SEQUENCE: some page locators carry a volume/part prefix ('2:45',
      'II.45') and others are bare arabic numbers - a bare number does not
      say which volume it is in. Letter prefixes ('A3', appendix) and
      roman front matter are separate sequences beside an unprefixed main
      sequence, so they do not trigger this.
    * PREFIX: volume prefixes written in more than one notation ('2:45'
      and 'II.45'), or letter prefixes with more than one separator ('A3'
      and 'A-3')."""
    if opts.locators in ("anchor", "none"):
        return []
    vol: Dict[str, List[Tuple[Entry, Locator]]] = {}
    let: Dict[str, List[Tuple[Entry, Locator]]] = {}
    bare: List[Tuple[Entry, Locator]] = []
    for e in walk(roots):
        for l in e.locators:
            if not l.numeric or l.wprefix:
                continue
            if l.pstyle.startswith(("arabic", "roman")):
                vol.setdefault(l.pstyle, []).append((e, l))
            elif l.pstyle.startswith("letter"):
                let.setdefault(l.pstyle, []).append((e, l))
            elif not l.roman and not l.tag:
                bare.append((e, l))
    out: List[Finding] = []
    nvol = sum(len(v) for v in vol.values())
    if nvol >= 2 and bare:
        first = min(bare, key=lambda p: _pos_key(p[0].line))
        out.append(Finding("ISO999-7.4.2-SEQUENCE", first[0].line,
            f"{nvol} locator(s) carry a volume/part prefix (e.g. "
            f"{_ex_locs(next(iter(vol.values())), 2)}) but {len(bare)} "
            f"page locator(s) have none (e.g. {_ex_locs(bare)}); in a work "
            f"with several numbering sequences every locator should show "
            f"which sequence it belongs to (7.4.2.2.1)"))
    for kinds, what in ((vol, "volume/part prefixes"),
                        (let, "letter prefixes")):
        if len(kinds) < 2:
            continue
        order = sorted(kinds, key=lambda k: -len(kinds[k]))
        minority = [p for k in order[1:] for p in kinds[k]]
        minority.sort(key=lambda p: _pos_key(p[0].line))
        counts = ", ".join(f"{_PSTYLE_NAMES.get(k, k)} x{len(kinds[k])}"
                           for k in order)
        out.append(Finding("ISO999-7.4.2-PREFIX", minority[0][0].line,
            f"{what} are written in {len(kinds)} notations ({counts}); "
            f"use one prefix scheme throughout (7.4.2.2.1). Minority "
            f"form(s): {_ex_locs(minority)}"))
    return out


def _special_class(l: Locator) -> Optional[str]:
    if l.marker:
        return "word"
    if l.suffix in SPECIAL_SUFFIXES and not l.roman:
        return "suffix"
    if l.style in ("italic", "bracket"):
        return l.style
    return None


_SPECIAL_NAMES = {"word": "a word ('fig. 3', '12 (map)')",
                  "suffix": "a letter suffix ('22f', '31t')",
                  "italic": "italics", "bracket": "brackets"}


def check_special_markers(roots: List[Entry], opts: Options
                          ) -> List[Finding]:
    """7.4.4 (7.4-17), Advisory: locators to special matter (figures,
    tables, maps ...) may be marked; when several marker types are used,
    one scheme for all of them is preferable. Classes: marker word, letter
    suffix (f t i m p), italics, brackets. Bold is not counted: it is the
    usual mark of the principal locator (7.4.4, first paragraph)."""
    if opts.locators in ("anchor", "none"):
        return []
    found: Dict[str, List[Tuple[Entry, Locator]]] = {}
    for e in walk(roots):
        for l in e.locators:
            c = _special_class(l) if l.numeric else None
            if c:
                found.setdefault(c, []).append((e, l))
    if len(found) < 2:
        return []
    order = sorted(found, key=lambda k: -len(found[k]))
    parts = "; ".join(f"{_SPECIAL_NAMES[k]} x{len(found[k])}: "
                      f"{_ex_locs(found[k], 2)}" for k in order)
    first = min((p for k in order[1:] for p in found[k]),
                key=lambda p: _pos_key(p[0].line))
    return [Finding("ISO999-7.4.4-SPECIAL", first[0].line,
        f"locators are marked in {len(found)} different ways ({parts}); if "
        f"these mark special matter (figures, tables, maps), one marking "
        f"scheme for all kinds is preferable, explained in the note "
        f"(7.4.4). Italics are counted as a special-matter mark; if they "
        f"mark the principal locator instead, ignore this")]


def _resolver(roots: List[Entry], lf: str = "basic"):
    top: Dict[str, Entry] = {}
    paths: Dict[str, Entry] = {}
    for e in roots:
        top.setdefault(norm_heading(e.heading, lf), e)
    # a heading restricted by a 7.5.3 qualifier ("quills in later issues")
    # also answers to its bare term, unless a bare entry exists
    for e in roots:
        core, qual = split_qualifier(e.heading)
        if qual:
            top.setdefault(norm_heading(core, lf), e)
    for e in walk(roots):
        if e.parent is not None:
            p = norm_heading(e.parent.path(), lf) + ": " + \
                norm_heading(e.heading, lf)
            paths.setdefault(p, e)

    def resolve(target: str) -> Optional[Entry]:
        t = norm_heading(target, lf)
        if t in top:
            return top[t]
        for sep in (":", " \u2014 ", " \u2013 ", " - "):
            if sep in t:
                a, b = t.split(sep, 1)
                key = a.strip() + ": " + b.strip()
                if key in paths:
                    return paths[key]
        if "," in t:
            a, b = t.split(",", 1)
            key = a.strip() + ": " + b.strip()
            if key in paths:
                return paths[key]
        return None
    return resolve


def _unconditional_see(e: Entry) -> List[CrossRef]:
    """'see' references of ``e`` that are not limited by a 7.5.3 qualifier."""
    if split_qualifier(e.heading)[1]:
        return []
    return [r for r in e.see if not split_qualifier(r.target)[1]]


def check_crossrefs(roots: List[Entry], opts: Options) -> List[Finding]:
    out: List[Finding] = []
    lf = opts.locale_fold
    resolve = _resolver(roots, lf)
    see_graph: Dict[int, List[Entry]] = {}
    for e in walk(roots):
        label = _q(e.path())
        head_qual = bool(split_qualifier(e.heading)[1])
        for kind, refs in (("see", e.see), ("see also", e.see_also)):
            # 7.5: a target that does not resolve but whose comma-separated
            # parts all do is several targets joined with the wrong mark
            split_refs: List[CrossRef] = []
            for r in refs:
                target, tqual = split_qualifier(r.target)
                parts = [p.strip() for p in target.split(",") if p.strip()]
                if (not r.generic and len(parts) >= 2 and
                        resolve(target) is None and
                        all(resolve(p) is not None for p in parts)):
                    out.append(Finding("ISO999-7.5-SEPARATOR", e.line,
                        f"{label}: '{kind}' target {_q(target)} is not a "
                        f"heading, but its comma-separated parts "
                        f"({'; '.join(parts)}) all are; separate multiple "
                        f"targets with semicolons"))
                    split_refs.extend(CrossRef(p + (" " + tqual if tqual
                                                    else ""))
                                      for p in parts)
                else:
                    split_refs.append(r)
            refs = split_refs
            names = [split_qualifier(r.target)[0] for r in refs
                     if not r.generic]
            keys = [okey(n, opts) for n in names]
            if any(b < a for a, b in zip(keys, keys[1:])):
                out.append(Finding("ISO999-7.5-TARGETORDER", e.line,
                    f"{label}: '{kind}' targets ({'; '.join(names)}) are "
                    f"not in alphabetical order"))
            for r in refs:
                if r.generic:
                    continue
                target, tqual = split_qualifier(r.target)
                qualified = bool(tqual) or head_qual
                tgt = resolve(target)
                if tgt is e or norm_heading(target, lf) in (
                        norm_heading(e.heading, lf),
                        norm_heading(e.path(), lf)):
                    out.append(Finding("ISO999-7.5-SELF", e.line,
                        f"{label}: '{kind}' {_q(target)} points back to "
                        f"the same heading"))
                    continue
                if tgt is None:
                    rule = ("ISO999-7.5.1-DANGLING" if kind == "see"
                            else "ISO999-7.5.2-DANGLING")
                    out.append(Finding(rule, e.line,
                        f"{label}: '{kind}' target {_q(target)} is not a "
                        f"heading in this index"))
                    continue
                if kind == "see" and qualified:
                    # a 7.5.3 reference limited to some volumes or dates is
                    # conditional: it is not a redirect that can chain/loop
                    continue
                if kind == "see":
                    see_graph.setdefault(id(e), []).append(tgt)
                    if (not tgt.see and not tgt.children and
                            len(tgt.locators) == 1 and
                            tgt.locators[0].numeric):
                        out.append(Finding("ISO999-7.5.1-FEW", e.line,
                            f"{label} sends the reader to {_q(tgt.path())}, "
                            f"which has only {len(tgt.locators)} locator(s); "
                            f"giving the locator here directly may serve "
                            f"readers better"))
                else:
                    if e.locators and tgt.locators and \
                            {l.identity() for l in e.locators} == \
                            {l.identity() for l in tgt.locators}:
                        out.append(Finding("ISO999-7.5.2.1-SAMELOC", e.line,
                            f"{label}: 'see also' {_q(tgt.path())} leads to "
                            f"exactly the same locators"))
        if e.see and (e.locators or e.children):
            what = "locators" if e.locators else "subheadings"
            out.append(Finding("ISO999-7.5.1-LOCATORS", e.line,
                f"{label} has a 'see' reference but also {what}; a 'see' "
                f"entry should only redirect (use 'see also' if the entry "
                f"has its own references)"))
        if e.see_also and not e.see and not e.locators and \
                not e.children and opts.locators != "none":
            out.append(Finding("ISO999-7.5.2.1-NOREFS", e.line,
                f"{label} has only a 'see also' reference and nothing of its "
                f"own; a plain 'see' may be intended"))
    # see-graph: cycles, then chains
    by_id = {id(e): e for e in walk(roots)}
    in_cycle: set = set()
    reported: set = set()
    for start_id in list(see_graph):
        path_ids = [start_id]
        cur = start_id
        while cur in see_graph:
            nxt = id(see_graph[cur][0])
            if nxt in path_ids:
                cyc = path_ids[path_ids.index(nxt):]
                key = frozenset(cyc)
                in_cycle.update(cyc)
                if key not in reported:
                    reported.add(key)
                    names = " -> ".join(by_id[i].path() for i in cyc +
                                        [nxt])
                    out.append(Finding("ISO999-7.5.1-CYCLE",
                        min(by_id[i].line for i in cyc),
                        f"'see' references loop and never reach an entry "
                        f"with locators: {names}"))
                break
            path_ids.append(nxt)
            cur = nxt
    for sid, targets in see_graph.items():
        if sid in in_cycle:
            continue
        e = by_id[sid]
        for t in targets:
            if _unconditional_see(t) and id(t) not in in_cycle:
                out.append(Finding("ISO999-7.5.1-CHAIN", e.line,
                    f"{_q(e.path())} sends the reader to {_q(t.path())}, "
                    f"which itself says 'see' {_q(t.see[0].target)}; point "
                    f"directly at the final heading"))
    # 'see also' placement consistency
    placed = [(e, e.see_also_placement) for e in walk(roots)
              if e.see_also and e.see_also_placement]
    counts: Dict[str, int] = {}
    for _, p in placed:
        counts[p] = counts.get(p, 0) + 1  # type: ignore[index]
    if list(counts) == ["before"]:
        e0 = placed[0][0]
        out.append(Finding("ISO999-7.5.2.1-PLACEMENT", e0.line,
            f"all {counts['before']} 'see also' reference(s) come before "
            f"the locators (first: {_q(e0.path())}); this is consistent, "
            f"but 7.5.2.1 normally places 'see also' after the locators "
            f"(or subheadings) - placing it first is the recognised "
            f"exception for card, screen or very detailed indexes",
            severity="info"))
    if len(counts) > 1:
        major = max(counts, key=lambda k: (counts[k], k == "after"))
        desc = {"before": "before the locators", "after": "after the "
                "locators", "sub": "on its own line under the heading"}
        for e, p in placed:
            if p != major:
                out.append(Finding("ISO999-7.5.2.1-PLACEMENT", e.line,
                    f"{_q(e.path())}: 'see also' is placed {desc[p]}, but "
                    f"most entries ({counts[major]}) place it {desc[major]}"))
    return out


def _initial_letter(heading: str) -> str:
    raw = re.sub(r"^[^\w]+", "", _MARKUP_RE.sub("", heading).strip())
    return raw[:1] if raw[:1].isalpha() else ""


def check_caseblock(roots: List[Entry], opts: Options,
                    meta: Optional[dict] = None
                    ) -> Tuple[List[Finding], set]:
    """8.1: detect two alphabets produced by a case-sensitive sort.

    Evidence: (a) a single-letter group header that occurs twice, or (b) a
    run of capitalised headings in A-Z order followed by a run of
    lower-case headings that restarts the alphabet. At most one finding.
    Returns the findings and the ids of entries whose ORDER finding the
    restart already explains.
    """
    meta = meta or {}
    lf = opts.locale_fold
    evidence: List[str] = []
    line = 0
    skip: set = set()
    seq = [(e, _initial_letter(filing_text(e.heading, opts))) for e in roots
           if _order_eligible(e, opts)]
    seq = [(e, c) for e, c in seq if c]
    for k in range(1, len(seq)):
        (ep, cp), (ec, cc) = seq[k - 1], seq[k]
        if not (cp.isupper() and cc.islower() and fold(cc, lf) < fold(cp, lf)):
            continue
        before, after = seq[:k], seq[k:]
        up = sum(1 for _, c in before if c.isupper())
        low = sum(1 for _, c in after if c.islower())
        if len(before) < 2 or len(after) < 2 or up < 0.8 * len(before) or \
                low < 0.8 * len(after):
            continue
        both = sorted({fold(c, lf).upper() for _, c in before} &
                      {fold(c, lf).upper() for _, c in after})
        letters = ", ".join(both) if both else "none shared"
        evidence.append(
            f"a capitalised run (lines {before[0][0].line}-{ep.line}) is "
            f"followed by a lower-case run restarting at {_q(ec.heading)} "
            f"(line {ec.line}); letters in both runs: {letters}")
        line = ec.line
        skip.add(id(ec))
        break
    seen: Dict[str, int] = {}
    rep: Dict[str, List[int]] = {}
    for letter, ln in meta.get("groups", []):
        if letter in seen:
            rep.setdefault(letter, [seen[letter]]).append(ln)
        else:
            seen[letter] = ln
    if rep:
        desc = "; ".join(f"{g} (lines {', '.join(map(str, ls))})"
                         for g, ls in sorted(rep.items()))
        evidence.append(f"letter group header(s) repeated: {desc}")
        first_rep = min(ls[1] for ls in rep.values())
        line = min(line, first_rep) if line else first_rep
    if not evidence:
        return [], skip
    return [Finding("ISO999-8.1-CASEBLOCK", line,
        "the index appears to contain two alphabets, as a case-sensitive "
        "sort produces: " + "; and ".join(evidence) + ". Upper and lower "
        "case should file together (8.1); re-sort case-insensitively")], skip


def check_space_separator(roots: List[Entry], meta: Optional[dict] = None
                          ) -> List[Finding]:
    """7.4.5: a single space between heading and locator is acceptable only
    when the boundary is unambiguous, i.e. no heading ends in a digit."""
    if not meta or meta.get("style") != "space":
        return []
    amb = [e for e in walk(roots)
           if re.search(r"\d$", _MARKUP_RE.sub("", e.heading).strip())]
    if not amb:
        return [Finding("ISO999-7.4.5-SEPARATOR", 0,
            "headings and locators are separated by a single space; that "
            "is acceptable only while it stays unambiguous (no heading in "
            "this index ends in a number) - a comma or two spaces is safer",
            severity="info")]
    return [Finding("ISO999-7.4.5-SEPARATOR", e.line,
        f"{_q(e.path())} ends in a number and the index separates locators "
        f"by a single space, so a reader cannot tell where the heading "
        f"ends; use a comma or two spaces before locators")
        for e in amb]


def _singulars(word: str) -> List[str]:
    out = []
    if word.endswith("ies") and len(word) > 4:
        out.append(word[:-3] + "y")
    if word.endswith("es") and len(word) > 3:
        out.append(word[:-2])
    if word.endswith("s") and not word.endswith("ss") and len(word) > 2:
        out.append(word[:-1])
    return out


def _refers(a: Entry, b: Entry, lf: str) -> bool:
    nb = norm_heading(b.heading, lf)
    return any(norm_heading(split_qualifier(r.target)[0], lf) == nb
               for r in a.see + a.see_also)


_NAME_RE = re.compile(r"^\s*([^\W\d_][\w'\u2019-]*)\s*,\s*(.+)$")


def _name_parts(heading: str, lf: str) -> Optional[Tuple[str, List[str]]]:
    h = re.sub(r"\([^)]*\)", "", _MARKUP_RE.sub("", heading)).strip()
    m = _NAME_RE.match(h)
    if not m or not m.group(1)[:1].isupper():
        return None
    fore = m.group(2)
    toks = re.findall(r"[^\W\d_]+", fore)
    if not toks or not all(t[:1].isupper() for t in toks):
        return None
    return fold(m.group(1), lf), [fold(t, lf) for t in toks]


def check_near_duplicates(roots: List[Entry], opts: Options
                          ) -> List[Finding]:
    """7.2.2.2 singular/plural pairs and 7.3.1.1 name-form variants (info)."""
    lf = opts.locale_fold
    out: List[Finding] = []
    for parent, sibs in sibling_groups(roots):
        by_norm: Dict[str, Entry] = {}
        for e in sibs:
            by_norm.setdefault(norm_heading(e.heading, lf), e)
        for e in sibs:
            if "(" in e.heading:
                continue
            words = norm_heading(e.heading, lf).split(" ")
            hit: Optional[Entry] = None
            for i, w in enumerate(words):
                for sg in _singulars(w):
                    cand = by_norm.get(" ".join(words[:i] + [sg] +
                                                words[i + 1:]))
                    if cand is not None and cand is not e and \
                            "(" not in cand.heading:
                        hit = cand
                        break
                if hit:
                    break
            if hit is None or _refers(e, hit, lf) or _refers(hit, e, lf):
                continue
            out.append(Finding("ISO999-7.2.2.2-NUMBER", e.line,
                f"{_q(e.path())} and {_q(hit.path())} (line {hit.line}) "
                f"differ only in singular/plural form; choose one form, or "
                f"add qualifiers if they are different concepts"))
        names: Dict[str, List[Tuple[Entry, List[str]]]] = {}
        for e in sibs:
            np_ = _name_parts(e.heading, lf)
            if np_:
                names.setdefault(np_[0], []).append((e, np_[1]))
        for group in names.values():
            for i, (a, ta) in enumerate(group):
                for b, tb in group[i + 1:]:
                    if len(ta) != len(tb) or ta == tb:
                        continue
                    ok, initials = True, False
                    for x, y in zip(ta, tb):
                        if x == y:
                            continue
                        short, long_ = (x, y) if len(x) < len(y) else (y, x)
                        if len(short) == 1 and long_.startswith(short) and \
                                len(long_) > 1:
                            initials = True
                        else:
                            ok = False
                            break
                    if not ok or not initials or _refers(a, b, lf) or \
                            _refers(b, a, lf):
                        continue
                    out.append(Finding("ISO999-7.3.1.1-VARIANT", b.line,
                        f"{_q(b.path())} and {_q(a.path())} (line {a.line}) "
                        f"look like the same person under initials and under "
                        f"full forenames; use one form of the name and, if "
                        f"needed, refer from the other"))
    return out


_ART_INITIAL_RE = re.compile(r"^(The|An|A)\s+[A-Z0-9\"'\u201c\u2018]")
_ART_INVERTED_RE = re.compile(r",\s*(The|An|A)\s*(?:\([^)]*\))?\s*$")


def check_articles(roots: List[Entry]) -> List[Finding]:
    """7.3.4.2: a leading article must be handled the same way throughout
    one index. Warn when some headings keep it in front ('The Tempest')
    and others move it to the end ('Winter's Tale, The'). Which method is
    right depends on national usage (editorial); consistency is objective.
    """
    initial: List[Entry] = []
    inverted: List[Entry] = []
    for e in walk(roots):
        h = _MARKUP_RE.sub("", e.heading).strip()
        if _ART_INITIAL_RE.match(h):
            initial.append(e)
        elif _ART_INVERTED_RE.search(h):
            inverted.append(e)
    if not initial or not inverted:
        return []
    minority = initial if len(initial) <= len(inverted) else inverted

    def ex(es: List[Entry]) -> str:
        return ", ".join(f"{_q(e.heading)} (line {e.line})" for e in es[:3]) \
            + (f" (+{len(es) - 3} more)" if len(es) > 3 else "")
    return [Finding("ISO999-7.3.4.2-ARTICLE", minority[0].line,
        f"leading articles are handled two ways: kept in front in "
        f"{len(initial)} heading(s) ({ex(initial)}) and moved to the end in "
        f"{len(inverted)} ({ex(inverted)}); one index must treat them one "
        f"way (7.3.4.2) - English practice moves the article to the end, "
        f"French keeps it in front but ignores it in filing")]


def _expand_abbrev(heading: str, lf: str) -> str:
    t = norm_heading(heading, lf)
    t = re.sub(r"(?:(?<=^)|(?<=\s))st\.?\s", "saint ", t)
    t = re.sub(r"(?:(?<=^)|(?<=\s))ste\.?\s", "sainte ", t)
    t = re.sub(r"(?:(?<=^)|(?<=\s))mt\.?\s", "mount ", t)
    t = re.sub(r"(?:(?<=^)|(?<=\s))dr\.?\s", "doctor ", t)
    t = re.sub(r"(?:(?<=^)|(?<=\s))(?:mc|m['\u2019])(?=\w)", "mac", t)
    t = re.sub(r"\s*&\s*", " and ", t)
    return re.sub(r"\s+", " ", t).strip()


def check_abbrev_variants(roots: List[Entry], opts: Options
                          ) -> List[Finding]:
    """7.3.6 (info): the same heading under an abbreviated and a spelled-out
    form (St/Saint, Mc/Mac, Dr/Doctor, &/and), and index-wide use of both
    'St'/'Saint' or 'Dr'/'Doctor' as a first word."""
    lf = opts.locale_fold
    out: List[Finding] = []
    for parent, sibs in sibling_groups(roots):
        seen: Dict[str, Entry] = {}
        for e in sibs:
            k = _expand_abbrev(e.heading, lf)
            first = seen.get(k)
            if first is None:
                seen[k] = e
            elif norm_heading(first.heading, lf) != norm_heading(e.heading,
                                                                 lf):
                out.append(Finding("ISO999-7.3.6-VARIANT", e.line,
                    f"{_q(e.path())} and {_q(first.path())} (line "
                    f"{first.line}) are the same heading in abbreviated "
                    f"and spelled-out form; use one form (abbreviations "
                    f"file as written, 7.3.6) and refer from the other"))
    reported = {f.line for f in out}
    for short, long_ in (("st", "saint"), ("dr", "doctor")):
        a = [e for e in roots if first_word(e.heading, lf).rstrip(".") ==
             short]
        b = [e for e in roots if first_word(e.heading, lf) == long_]
        if a and b and not any(e.line in reported for e in a + b):
            out.append(Finding("ISO999-7.3.6-VARIANT", a[0].line,
                f"headings begin with both {_q(short.title() + '.')} "
                f"({_q(a[0].heading)}, line {a[0].line}) and "
                f"{_q(long_.title())} ({_q(b[0].heading)}, line "
                f"{b[0].line}); if the index abbreviates, do so "
                f"consistently - abbreviations file as written (7.3.6)"))
    return out


def check_parse_health(roots: List[Entry], opts: Options,
                       meta: Optional[dict] = None) -> List[Finding]:
    """Parse health (info): signs that the layout was misread - many
    entries with nothing to point to, headings that end in a number or a
    full stop (a locator left in the heading), lower-case lines read as
    entries of their own (turnovers). Silent when nothing looks wrong."""
    meta = meta or {}
    ents = list(walk(roots))
    n = len(ents)
    if n < 10:
        return []
    bare = [] if opts.locators == "none" else [
        e for e in ents if not (e.locators or e.see or e.see_also or
                                e.children)]
    # a number left in the heading only matters where locators are numbers
    tail = [] if opts.filing == "identifier" else [
        e for e in ents if not any(l.anchor for l in e.locators) and
        re.search(r"\d\.?$|[^\W\d_]{4,}\.$",
                  _MARKUP_RE.sub("", e.heading).strip())]
    top = [e for e in roots if re.match(r"[^\W\d_]", e.heading)]
    caps = (sum(1 for e in top if e.heading[:1].isupper()) / len(top)
            if top else 0.0)
    turn = [e for e in top if caps >= 0.8 and len(top) >= 10 and
            e.heading[:1].islower()]
    turn += [e for e in ents if e.parent is not None and
             len(e.parent.children) == 1 and e.heading[:1].islower() and
             not (e.parent.locators or e.parent.see or e.parent.see_also) and
             len(e.parent.heading) >= 40]
    pb, pt = len(bare) / n, len(tail) / n
    if pb < 0.2 and pt < 0.05 and len(turn) < 3:
        return []

    def ex(es: List[Entry]) -> str:
        return "; e.g. " + ", ".join(f"{_q(e.heading)} (line {e.line})"
                                    for e in es[:3]) if es else ""
    notes = []
    for key, what in (("ditto", "repeated-heading dash lines"),
                      ("runon", "run-on subheadings")):
        if meta.get(key):
            notes.append(f"{meta[key]} {what} resolved")
    extra = f" ({'; '.join(notes)})" if notes else ""
    return [Finding("ISO999-PARSE-HEALTH", 0,
        f"parse health: {n} entries{extra}; {len(bare)} ({pb:.0%}) have no "
        f"locators, cross-references or subheadings{ex(bare)}; {len(tail)} "
        f"({pt:.0%}) headings end in a digit or full stop{ex(tail)}; "
        f"{len(turn)} suspected turnover line(s){ex(turn)}. High values "
        f"usually mean the layout was misread, not that the index is bad - "
        f"inspect the parse with --dump-tree before trusting other findings")]


def check_indentation(meta: Optional[dict]) -> List[Finding]:
    """Text layouts (set-out, not Markdown bullets).

    * 9.1.2.4-INDENT: every item at one level has the same indentation,
      and each level is indented further than the one above. Reported
      once per level whose items use more than one indent.
    * 9.4.1.4-TURNOVER: a turnover line (the wrapped rest of an entry that
      the reader joined: a lower-case continuation or a line of locators
      after a trailing comma) must be indented beyond the deepest
      subheading, or it reads as a heading or subheading. One finding for
      the index (the wrap routine is at fault, not each entry)."""
    if not meta or not meta.get("indents") or not meta.get("text_layout"):
        return []
    rows = meta["indents"]
    out: List[Finding] = []
    per: Dict[int, Dict[int, List[int]]] = {}
    for level, indent, lineno, ditto in rows:
        if not ditto:
            per.setdefault(level, {}).setdefault(indent, []).append(lineno)
    for level in sorted(per):
        used = per[level]
        if len(used) < 2:
            continue
        common = max(used, key=lambda i: len(used[i]))
        odd = sorted((ln, i) for i, lns in used.items() if i != common
                     for ln in lns)
        desc = ", ".join(f"{i} ({len(used[i])}x)" for i in sorted(used))
        exs = ", ".join(f"line {ln} ({i})" for ln, i in odd[:3]) + (
            f" (+{len(odd) - 3} more)" if len(odd) > 3 else "")
        out.append(Finding("ISO999-9.1.2.4-INDENT", odd[0][0],
            f"level-{level} {'headings' if level == 0 else 'subheadings'} "
            f"are set at {len(used)} different indents (columns {desc}; "
            f"most use {common}): e.g. {exs}; every item at one level "
            f"should have the same indentation (9.1.2.4)"))
    turns = meta.get("turnovers") or []
    if turns:
        deepest = max(indent for _, indent, _, _ in rows)
        bad = [(ln, ind) for ln, ind, _ in turns if ind <= deepest]
        if bad:
            what = ("the deepest subheading" if
                    any(lv > 0 for lv, _, _, _ in rows) else "the headings")
            exs = ", ".join(f"line {ln} (column {ind})" for ln, ind in
                            bad[:3]) + (f" (+{len(bad) - 3} more)"
                                        if len(bad) > 3 else "")
            out.append(Finding("ISO999-9.4.1.4-TURNOVER", bad[0][0],
                f"{len(bad)} of {len(turns)} turnover line(s) are not "
                f"indented beyond {what} (column {deepest}): e.g. {exs}; a "
                f"wrapped entry should continue deeper than any subheading "
                f"so that it cannot be taken for a new heading or "
                f"subheading (9.1.2.4, 9.4.1.4)"))
    return out


_RUNON_STRONG_MIN = 2


def _loc_token(tok: str, line: int) -> bool:
    t = tok.strip().rstrip(".")
    return bool(t) and parse_locator(t, line, ext=True) is not None


def _comma_sibling(text: str, line: int) -> Optional[str]:
    """In one run-on segment, a comma-separated token with words that
    follows a locator ('keepers 31, fuel 33'): a sibling separated by a
    comma. Returns the offending token."""
    seen_loc = False
    for tok in _paren_split(text, ","):
        tok = tok.strip()
        if not tok:
            continue
        if _loc_token(tok, line):
            seen_loc = True
            continue
        if seen_loc and re.search(r"[^\W\d_]{2,}", tok) and \
                not _find_see(tok) and not re.match(
                    r"(?:n|nn|notes?|and|&)\b", tok):
            return tok
        # words then a trailing locator after one space ('fuel 33')
        seen_loc = seen_loc or bool(re.search(r"\s\d+[a-z]?$", tok))
    return None


def check_runon(meta: Optional[dict]) -> List[Finding]:
    """9.5 (run-on layout; 7.2.3.3): punctuation replaces indentation, so
    it must be consistent. For each text line whose ';'-separated parts
    after the first all contain words (a run-on entry):

    * a colon after a lead that has locators ('lighthouses: 14; ...') -
      the colon marks a lead with no locators;
    * a lead with no locators followed by ';' instead of ':' (only when
      the index has 2+ run-on entries, so that a prose semicolon in a
      set-out entry is not taken for layout);
    * siblings separated by a comma after a locator ('keepers 31, fuel
      33') where the index separates siblings by ';';
    * unbalanced parentheses (the third level is enclosed in them).
    One finding per kind of fault, with a count and examples."""
    if not meta or not meta.get("runon_rows"):
        return []
    runon: List[Tuple[int, str, str, List[str]]] = []
    for lineno, content in meta["runon_rows"]:
        m = _find_see(content)
        head = content[:m.start()] if m else content
        parts = [x.strip() for x in _paren_split(head, ";") if x.strip()]
        if len(parts) < 2:
            continue
        subs = parts[1:]
        if not all(re.search(r"[^\W\d_]{2,}", x) for x in subs) or \
                not any(re.search(r"\d", x) for x in subs):
            continue
        runon.append((lineno, content, parts[0], subs))
    if not runon:
        return []
    faults: Dict[str, List[Tuple[int, str]]] = {}
    for lineno, content, lead, subs in runon:
        segs = list(subs)
        cm = re.match(r"^([^:()]*?\S)\s*:\s*(.*)$", lead)
        if cm:
            head, tail = cm.group(1), cm.group(2)
            first_tok = re.split(r"\s*,\s*|\s+", tail, maxsplit=1)[0]
            if tail and _loc_token(first_tok, lineno):
                faults.setdefault("colon", []).append((lineno, lead))
            elif tail:
                segs.insert(0, tail)
        else:
            style = meta.get("style") or "unknown"
            pl = parse_content(lead, 0, lineno,
                               "space" if style == "unknown" else style,
                               "numeric")
            if not pl.locators and not pl.see and not pl.see_also:
                faults.setdefault("nocolon", []).append((lineno, lead))
        if content.count("(") != content.count(")"):
            faults.setdefault("paren", []).append((lineno, content))
        for seg in segs:
            inner = re.findall(r"\(([^()]*)\)", seg)
            outer = re.sub(r"\([^()]*\)", " ", seg)
            for piece in [outer] + [x for y in inner for x in
                                    _paren_split(y, ";")]:
                tok = _comma_sibling(piece, lineno)
                if tok:
                    faults.setdefault("comma", []).append((lineno, tok))
                    break
    if len(runon) < _RUNON_STRONG_MIN:
        faults.pop("nocolon", None)
    what = {
        "colon": "a colon follows a heading that has locators (the colon "
                 "marks a heading with no locators before its first "
                 "subheading)",
        "nocolon": "a heading with no locators is followed by a semicolon, "
                   "not a colon, before its first subheading",
        "comma": "subheadings are separated by a comma after a locator "
                 "while others are separated by semicolons (commas "
                 "already separate locators)",
        "paren": "parentheses are unbalanced (the third level is enclosed "
                 "in parentheses)",
    }
    out: List[Finding] = []
    for kind in ("colon", "nocolon", "comma", "paren"):
        fs = faults.get(kind)
        if not fs:
            continue
        exs = "; ".join(f"line {ln}: {_q(t[:60])}" for ln, t in fs[:3]) + (
            f" (+{len(fs) - 3} more)" if len(fs) > 3 else "")
        out.append(Finding("ISO999-9.5-RUNON", fs[0][0],
            f"run-on layout ({len(runon)} run-on entr"
            f"{'y' if len(runon) == 1 else 'ies'}): {what[kind]} in "
            f"{len(fs)} entr{'y' if len(fs) == 1 else 'ies'}; e.g. {exs}. "
            f"In run-on layout punctuation replaces indentation, so one "
            f"mark per level must be used throughout (9.5)"))
    return out


def check_note(meta: Optional[dict]) -> List[Finding]:
    if not meta or "preamble" not in meta:
        return []
    a, b, how = meta["preamble"]
    src = ("--skip-until" if how == "skip-until" else
           "detected automatically; use --no-auto-preamble or "
           "--skip-until to change")
    return [Finding("ISO999-7.1.3-NOTE", a,
        f"lines {a}-{b} read as an introductory note ({src}) and not "
        f"linted as entries; check that it explains the filing method and "
        f"any conventions the index uses")]


def check_anchors(roots: List[Entry], meta: Optional[dict] = None
                  ) -> List[Finding]:
    """7.4 locator integrity for HTML: every in-document '#fragment'
    locator must name an id (or a[name]) in the same file."""
    ids = (meta or {}).get("ids")
    if ids is None:
        return []
    out: List[Finding] = []
    for e in walk(roots):
        for l in e.locators:
            if l.anchor is None or not l.anchor.startswith("#"):
                continue
            frag = l.anchor[1:]
            if frag and (frag in ids or _unquote(frag) in ids):
                continue
            out.append(Finding("ISO999-7.4-ANCHOR", e.line,
                f"{_q(e.path())}: locator {l.anchor} "
                + ("is an empty fragment" if not frag else
                   "does not match any id in this file")
                + "; the entry leads nowhere"))
    return out


def check_locales(sequences: List[Tuple[Optional[str], List[Entry]]],
                  opts: Options, collators: Optional[dict] = None
                  ) -> List[Finding]:
    """8.1-LOCALE (``--compare-locales``): re-sort each sequence's top-level
    headings with ``locale.strxfrm`` under each locale and list entries
    whose relative position differs from the first available locale.

    ``collators`` (tests) maps a locale name to a key function; otherwise
    each locale is set with ``setlocale(LC_COLLATE)`` (unavailable ones are
    skipped and named) and restored afterwards.
    """
    if not opts.compare_locales:
        return []
    import locale
    out: List[Finding] = []
    seqs = [(lab, [e for e in r]) for lab, r in sequences]
    texts = [[filing_text(e.heading, opts) for e in r] for _, r in seqs]
    orders: Dict[str, List[List[int]]] = {}
    skipped: List[str] = []
    saved = locale.setlocale(locale.LC_COLLATE)
    try:
        for name in opts.compare_locales:
            if collators is not None:
                if name not in collators:
                    skipped.append(name)
                    continue
                key = collators[name]
            else:
                got = None
                for cand in (name, name + ".UTF-8", name + ".utf8"):
                    try:
                        locale.setlocale(locale.LC_COLLATE, cand)
                        got = cand
                        break
                    except (locale.Error, ValueError):
                        continue
                if got is None:
                    skipped.append(name)
                    continue
                key = locale.strxfrm
            orders[name] = [sorted(range(len(t)), key=lambda i, t=t:
                                   (key(t[i]), t[i])) for t in texts]
    finally:
        try:
            locale.setlocale(locale.LC_COLLATE, saved)
        except locale.Error:
            pass
    note = (f" (skipped, not available here: {', '.join(skipped)})"
            if skipped else "")
    names = list(orders)
    if len(names) < 2:
        return [Finding("ISO999-8.1-LOCALE", 0,
            f"--compare-locales needs two available locales; available: "
            f"{', '.join(names) or 'none'}{note}")]
    base = names[0]
    for other in names[1:]:
        for si, (lab, r) in enumerate(seqs):
            b_order, o_order = orders[base][si], orders[other][si]
            rank = {idx: k for k, idx in enumerate(b_order)}
            seq = [(rank[idx],) for idx in o_order]
            keep = _keep_set(seq)
            moved = [o_order[j] for j in range(len(o_order))
                     if j not in keep]
            prefix = f"[{lab}] " if lab else ""
            if not moved:
                out.append(Finding("ISO999-8.1-LOCALE", 0,
                    f"{prefix}{base} and {other} collate the "
                    f"{len(r)} headings identically{note}", section=lab))
                continue
            opos = {idx: k for k, idx in enumerate(o_order)}
            desc = ", ".join(
                f"{_q(r[i].heading)} ({rank[i] + 1}->{opos[i] + 1})"
                for i in sorted(moved, key=lambda i: rank[i])[:20])
            out.append(Finding("ISO999-8.1-LOCALE", r[moved[0]].line,
                f"{prefix}{len(moved)} of {len(r)} headings change relative "
                f"position between {base} and {other} (position under "
                f"{base} -> {other}): {desc}; output that collates with the "
                f"reader's default locale files differently on different "
                f"machines - fix the collation locale and declare it"
                f"{note}", section=lab))
    return out


def lint_entries(roots: List[Entry], opts: Options,
                 meta: Optional[dict] = None,
                 sequences: Optional[List[Tuple[Optional[str],
                                                List[Entry]]]] = None
                 ) -> List[Finding]:
    """Run all checks. ``sequences`` (label, roots) are linted separately
    for ordering and duplicates (HTML ``--sections split``); locator,
    cross-reference and anchor checks run once over the whole index."""
    sequences = sequences or [(None, roots)]
    findings: List[Finding] = []
    for label, sroots in sequences:
        case_f, skip = check_caseblock(
            sroots, opts, meta if len(sequences) == 1 else None)
        fs = (check_filing(sroots, opts, skip) + case_f +
              check_duplicates(sroots, opts) +
              check_near_duplicates(sroots, opts))
        if label:
            # one 'no evidence' MODE note per section is noise
            fs = [f for f in fs if not (f.rule == "ISO999-8.2-MODE" and
                                        "no evidence" in f.message)]
            for f in fs:
                f.section = label
                f.message = f"[{label}] {f.message}"
        findings.extend(fs)
    findings += (check_locators(roots, opts) + check_crossrefs(roots, opts) +
                 check_locator_separators(roots, opts) +
                 check_locator_sequences(roots, opts) +
                 check_special_markers(roots, opts) +
                 check_indentation(meta) + check_runon(meta) +
                 check_space_separator(roots, meta) + check_note(meta) +
                 check_anchors(roots, meta) +
                 check_locales(sequences, opts) + check_articles(roots) +
                 check_abbrev_variants(roots, opts) +
                 check_parse_health(roots, opts, meta))
    findings = _article_filing(findings, sequences, opts)
    findings = _root_cause(findings, opts)
    findings = _collapse_subheading_order(findings, opts)
    findings = _collapse_repeats(findings, opts)
    findings.sort(key=lambda f: (_pos_key(f.line), f.rule))
    return findings


_PAIR_RULES = frozenset((
    "ISO999-8.2-ORDER", "ISO999-8.1-CASE-ORDER", "ISO999-8.5-ORDER",
    "ISO999-8.6-ORDER", "ISO999-8.3-ORDER", "ISO999-7.3.6-ABBREV",
    "ISO999-7.3.4.2-ARTICLE"))


def _alt_keys(opts: Options) -> List[Tuple[str, object]]:
    """Other sort keys a generator may have used instead of ISO 999 filing;
    each maps a heading to a comparable key."""
    def ft(h: str) -> str:
        # a generator sorts the text, not the emphasis we mark with '*'
        t = filing_text(h, opts)
        m = re.fullmatch(r"(\*{1,2})([^*].*?)\1(.*)", t)
        return m.group(2) + m.group(3) if m else t
    keys: List[Tuple[str, object]] = [
        ("lower-cased code-point order (a plain lower()/casefold string "
         "sort, as Sphinx uses)", lambda h: ft(h).lower()),
        ("code-point order (raw character values: capitals before lower "
         "case, punctuation by its code)", ft),
        ("case-sensitive filing (capitals filed before lower case)",
         lambda h: okey(ft(h), opts, keep_case=True, lf="none", raw=True
                        )[:2]),
    ]
    other = "letter" if opts.filing != "letter" else "word"
    keys.append((f"{_MODE_NAMES[other]} filing",
                 lambda h: okey(ft(h), opts, other, raw=True)[:2]))
    return keys


def _root_cause(findings: List[Finding], opts: Options) -> List[Finding]:
    """8-ROOTCAUSE: when most per-pair order findings are pairs that are in
    order under one other sort key, the index is simply sorted by that key.
    Emit one summary (count, key, examples) and drop the pairs it explains
    (``--verbose-pairs`` keeps them as info)."""
    pairs = [f for f in findings if f.rule in _PAIR_RULES and f.pair and
             f.severity == "warn"]
    if len(pairs) < 4:
        return findings
    scored = []
    for name, key in _alt_keys(opts):
        try:
            hit = [f for f in pairs if key(f.pair[0]) <= key(f.pair[1])]
        except TypeError:
            continue
        scored.append((len(hit), name, hit))
    if not scored:
        return findings
    best_n = max(n for n, _, _ in scored)
    if best_n < 4 or best_n < 0.6 * len(pairs):
        return findings
    tops = [(name, hit) for n, name, hit in scored if n == best_n]
    name, hit = tops[0]
    best_key = dict((nm, k) for nm, k in _alt_keys(opts))[name]
    # subheading groups reported as RUNS / PAGEORDER that are simply in
    # order under the same key have the same cause
    groups = []
    for f in findings:
        if f.rule in ("ISO999-8.6-RUNS", "ISO999-8.6-PAGEORDER") and \
                f.members and f.severity == "warn":
            ks = [best_key(h) for h in f.members]
            if all(a <= b for a, b in zip(ks, ks[1:])):
                groups.append(f)
    also = (" (equally consistent with " + "; ".join(t[0] for t in tops[1:])
            + ")" if len(tops) > 1 else "")
    by_rule: Dict[str, int] = {}
    for f in hit:
        by_rule[f.rule] = by_rule.get(f.rule, 0) + 1
    rules = ", ".join(f"{r.replace('ISO999-', '')} {c}"
                      for r, c in sorted(by_rule.items(),
                                         key=lambda x: -x[1]))
    secs = sorted({f.section for f in hit if f.section})
    where = (f" in {len(secs)} section(s)" if secs else "")
    exs = "; ".join(f"{_q(f.pair[1])} before {_q(f.pair[0])} (line "
                    f"{f.line})" for f in hit[:3])
    rest = len(pairs) - len(hit)
    gtxt = (f" It also explains {len(groups)} subheading group(s) reported "
            f"as 8.6 RUNS/PAGEORDER." if groups else "")
    mname = _mode_name(opts)
    summary = Finding("ISO999-8-ROOTCAUSE", hit[0].line,
        f"{len(hit)} of {len(pairs)} per-pair order findings{where} are "
        f"pairs that are in order under {name}{also}: the index is sorted "
        f"by that rule rather than by {mname} filing - one cause, fixed in "
        f"one place (the sort key; 8.1, 8.4). By rule: {rules}. E.g. "
        f"{exs}.{gtxt} "
        + (f"{rest} order finding(s) not explained by it are still listed. "
           if rest else "")
        + ("Per-pair findings follow as info." if opts.verbose_pairs else
           "Pass --verbose-pairs to list each pair."))
    hit_ids = {id(f) for f in hit + groups}
    out = []
    for f in findings:
        if id(f) in hit_ids:
            if not opts.verbose_pairs:
                continue
            f.severity = "info"
            f.message = f"(explained by 8-ROOTCAUSE) {f.message}"
        out.append(f)
    out.append(summary)
    return out


_REPEAT_MIN = 10


def _variant_only(f: Finding) -> bool:
    """A DUPLICATE between headings that are not written identically
    (they differ in case, separators, spacing or accents)."""
    if not f.pair:
        return False
    a, b = f.pair[0], f.pair[1]
    return re.sub(r"\s+", " ", a.strip()) != re.sub(r"\s+", " ", b.strip())


def _collapse_repeats(findings: List[Finding], opts: Options
                      ) -> List[Finding]:
    """When one per-entry rule fires 10+ times (long locator strings,
    headings differing only by case, singular/plural pairs) the cause is
    the index's practice, not each entry: keep one summary with the count
    and examples (``--verbose-pairs`` keeps every finding)."""
    if opts.verbose_pairs:
        return findings
    kinds = (
        ("ISO999-7.2.3.5-MAXLOC", lambda f: True,
         "entries have more locators than the limit"),
        ("ISO999-8.1-DUPLICATE", _variant_only,
         "headings differ from another heading only by case, separators "
         "or accents (if these distinguish different things, as with "
         "options -b and -B or GET_ITEM and GetItem, pass "
         "--case-significant; otherwise merge them)"),
        ("ISO999-7.2.2.2-NUMBER", lambda f: True,
         "heading pairs differ only in singular/plural form"),
        ("ISO999-7.4.2-LOCSEP", lambda f: True,
         "entries separate their locators by spaces or semicolons, not "
         "commas"),
    )
    drop: set = set()
    extra: List[Finding] = []
    for rule, pred, what in kinds:
        fs = [f for f in findings if f.rule == rule and pred(f)]
        if len(fs) < _REPEAT_MIN:
            continue
        fs.sort(key=lambda f: _pos_key(f.line))
        exs = "; ".join(f"line {f.line}: " +
                        re.sub(r"^\[[^]]*\] ", "", f.message)[:120]
                        for f in fs[:3])
        extra.append(Finding(rule, fs[0].line,
            f"{len(fs)} {what} (one summary; --verbose-pairs lists each). "
            f"E.g. {exs}", severity=fs[0].severity))
        drop.update(id(f) for f in fs)
    return [f for f in findings if id(f) not in drop] + extra


def _collapse_subheading_order(findings: List[Finding], opts: Options
                               ) -> List[Finding]:
    """One 8.6-ORDER finding per subheading group: repeated per-pair
    findings under one heading are merged into a count and examples."""
    groups: Dict[tuple, List[Finding]] = {}
    for f in findings:
        if f.rule == "ISO999-8.6-ORDER" and f.group is not None and \
                f.severity == "warn":
            groups.setdefault((f.section, f.group), []).append(f)
    drop = set()
    mname = _mode_name(opts)
    for (sec, _), fs in groups.items():
        if len(fs) < 2:
            continue
        first = fs[0]
        parent = first.pair[2] if first.pair else "?"
        exs = "; ".join(f"{_q(f.pair[1])} before {_q(f.pair[0])} (line "
                        f"{f.line})" for f in fs[:3])
        more = f" (+{len(fs) - 3} more)" if len(fs) > 3 else ""
        prefix = f"[{sec}] " if sec else ""
        first.message = (f"{prefix}{len(fs)} subheadings of {_q(parent)} "
                         f"are out of place under {mname} filing: {exs}"
                         f"{more}")
        drop.update(id(f) for f in fs[1:])
    return [f for f in findings if id(f) not in drop]


def lint_text(text: str, fmt: str, opts: Options) -> Tuple[List[Entry],
                                                             List[Finding]]:
    sequences, meta = parse_index(text, fmt, opts)
    roots = [e for _, r in sequences for e in r]
    return roots, lint_entries(roots, opts, meta, sequences)


def parse_index(text: str, fmt: str, opts: Options
                ) -> Tuple[List[Tuple[Optional[str], List[Entry]]], dict]:
    """Parse ``text`` into (section label, root entries) sequences."""
    meta: dict = {}
    if fmt == "text":
        lines = read_text(text, meta, skip_until=opts.skip_until,
                          auto_preamble=opts.auto_preamble,
                          locators=opts.locators)
    elif fmt == "html":
        lines = read_html(text, meta, locators=opts.locators)
    else:
        lines = read_ind(text)
    groups: List[Tuple[Optional[str], List[ParsedLine]]] = []
    if fmt == "text" and opts.only_section:
        # text: a section is an explicit heading line ('INDEX OF NAMES',
        # '## Index of places') or a single-letter group header
        rx = re.compile(opts.only_section, re.I)
        lines = [pl for pl in lines
                 if (pl.section is not None and rx.search(pl.section)) or
                 (pl.group is not None and rx.search(pl.group))]
        if not lines:
            raise ParseError(f"--only-section {opts.only_section!r} matched "
                             f"no section or letter group")
    if fmt == "text":
        # explicit headings split sequences only when there are 2+ of them
        # (one caption such as 'INDEX.' is not a division of the index)
        labels = {pl.section for pl in lines if pl.section is not None}
        if len(labels) < 2 or opts.sections == "merge":
            for pl in lines:
                pl.section = None
    if fmt in ("html", "text") and opts.sections == "split":
        for pl in lines:
            if not groups or groups[-1][0] != pl.section:
                groups.append((pl.section, []))
            groups[-1][1].append(pl)
    else:
        groups = [(None, lines)]
    if opts.only_section and fmt != "text":
        rx = re.compile(opts.only_section, re.I)
        groups = [(lab, ls) for lab, ls in groups
                  if lab is not None and rx.search(lab)]
        if not groups:
            raise ParseError(f"--only-section {opts.only_section!r} matched "
                             f"no section")
    sequences = [(lab, build_tree(ls)) for lab, ls in groups]
    sequences = [(lab, r) for lab, r in sequences if r]
    if not any(r for _, r in sequences):
        raise ParseError("no index entries could be parsed")
    return sequences, meta


def _entry_dict(e: Entry) -> dict:
    d: dict = {"heading": e.heading, "line": int(e.line), "level": e.level,
               "locators": [l.anchor if l.anchor is not None else l.raw
                            for l in e.locators]}
    if e.see:
        d["see"] = [r.target for r in e.see]
    if e.see_also:
        d["see_also"] = [r.target for r in e.see_also]
    if e.children:
        d["children"] = [_entry_dict(c) for c in e.children]
    return d


def dump_tree(sequences: List[Tuple[Optional[str], List[Entry]]],
              meta: dict) -> dict:
    """JSON-ready parse tree (``--dump-tree``)."""
    return {"layout": meta.get("layout", "list"),
            "style": meta.get("style"),
            "sections": [{"label": lab, "entries": [_entry_dict(e)
                                                    for e in r]}
                         for lab, r in sequences]}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="iso999_lint.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Heuristic linter for generated index output (text/Markdown, "
            "LaTeX .ind, simple HTML) against ISO 999:1996 guidance.\n"
            "ISO 999 is guidance, not law: findings are prompts for review."),
        epilog=(
            "Filing interpretation (see module docstring for detail):\n"
            "  - case-insensitive; diacritics folded to base letters;\n"
            "    apostrophes, periods, quotes, emphasis marks are ignored\n"
            "  - word: space (and hyphen/dash/slash) files before letters;\n"
            "    letter: spaces/hyphens/dashes/slashes ignored\n"
            "  - 8.5: bare term < 'term (x)' < longer headings. 8.5 is silent\n"
            "    on inverted 'term, x': --inversion after (default) files it\n"
            "    after 'term (x)' at the head of the longer headings;\n"
            "    --inversion before files it between the bare term and\n"
            "    'term (x)'. Neither choice is itself a finding.\n"
            "  - numerals (8.3a as read here): headings starting with a\n"
            "    numeral file before all alphabetical headings, by numeric\n"
            "    value; digits inside headings compare by value and before\n"
            "    letters (8.3d). --numerals ignore skips numeral-initial\n"
            "    headings (spelled-out option 8.3b, chemical locants 8.3c).\n"
            "  - roman numerals (--roman strict, default): a leading\n"
            "    upper-case roman numeral counts as a number only if it is\n"
            "    the whole first token and is followed by a counting word\n"
            "    (century, dynasty, congress, olympiad ...) or is listed in\n"
            "    --roman-list. Otherwise it files as letters, since\n"
            "    abbreviations file as written (7.3.6): CD, DC, MIX, VI.\n"
            "    --roman off never reads roman numerals as numbers.\n"
            "  - diacritics: --locale-fold basic folds accented letters to\n"
            "    their base letter; none only case-folds (accented letters\n"
            "    then sort by code point, after z). Full locale tailoring,\n"
            "    e.g. Swedish å after z, needs a collator (such as ICU)\n"
            "    that this tool does not ship.\n"
            "  - locators after ONE space ('kelp 12, 30') are read as\n"
            "    locators when the trailing run is a comma list or a range,\n"
            "    or when most lines of the index use a single space before\n"
            "    locators. In an index that mostly uses a comma or two\n"
            "    spaces, a number after one space stays in the heading\n"
            "    ('Route 66, 12'). 'Place, 1900' is always read as heading\n"
            "    'Place' + locator 1900.\n"
            "  - subheadings in page order (3+, not alphabetical) warn\n"
            "    unless --subheading-order page declares that arrangement;\n"
            "    ascending numeric/date subheadings are reported as info.\n"
            "  - introductory note (text input): leading prose paragraphs\n"
            "    (sentences, long lines, no locator tails) before the first\n"
            "    entries or letter header are skipped and reported as info\n"
            "    (7.1.3/9.2). --skip-until REGEX skips every line before the\n"
            "    first match instead; --no-auto-preamble lints everything.\n"
            "  - misorder whose first difference is a number is 8.3 (8.3 d);\n"
            "    misorder explained by filing the 'see' text is 8.7-SORTKEY;\n"
            "    a restarted A-Z (case-sensitive sort) is one 8.1-CASEBLOCK.\n"
            "  - a single-space locator separator is flagged (7.4.5) where a\n"
            "    heading ends in a number; otherwise one info note.\n"
            "  - v2 attribution: case-sensitive-sort pairs are 8.1-CASE-ORDER;\n"
            "    8.5 only with bare/qualified/inverted/longer term structure;\n"
            "    consecutive out-of-place entries collapse into one finding;\n"
            "    8-DISPLACED (info) = entries - longest in-order subsequence;\n"
            "    8.6-RUNS replaces PAGEORDER for restarted alphabets.\n"
            "  - v3: one 8-ROOTCAUSE summary when most order pairs fit another\n"
            "    sort key (--verbose-pairs keeps them as info); repeated\n"
            "    MAXLOC/NUMBER/DUPLICATE findings are summarised; dittos,\n"
            "    turnovers, run-on entries, <p>/<br> and <table> HTML are\n"
            "    parsed; --dump-tree shows the parse.\n"
            "Examples:\n"
            "  rustdoc all.html:  --locators anchor --filing identifier\n"
            "  pkgsite page:      --locators anchor --filing identifier\n"
            "                     --only-section '^Index$' --heading-regex\n"
            "                     '^(?:func\\s+(?:\\([^)]*\\)\\s*)?|type\\s+)?(\\w+)'\n"
            "  CLI topic list:    --locators none\n"
            "                     --qualifier-suffix=-api,-guide,-reference\n"
            "Exit: 0 no warnings, 1 warnings, 2 usage/parse error."))
    p.add_argument("path", nargs="?", help="index file ('-' for stdin)")
    p.add_argument("--format", choices=["auto", "text", "ind", "html"],
                   default="auto", help="input format (default: auto)")
    p.add_argument("--filing", choices=["word", "letter", "identifier"],
                   default="word",
                   help="expected filing method (default: word). "
                        "identifier: code names segmented into words at "
                        "camelCase humps, acronym runs, digit runs, _ :: . "
                        "- and filed word-by-word, case-folded, numbers by "
                        "value, raw-string tie-break")
    p.add_argument("--case-significant", dest="case_significant",
                   action="store_const", const=True, default=None,
                   help="headings differing only by case/separators are "
                        "distinct (3.10-HOMOGRAPH info, not 8.1-DUPLICATE); "
                        "on by default with --filing identifier")
    p.add_argument("--no-case-significant", dest="case_significant",
                   action="store_const", const=False,
                   help="turn case-significant identity off again")
    p.add_argument("--locators", choices=["auto", "numeric", "anchor",
                                          "none"], default="auto",
                   help="auto (default): numeric page locators, falling "
                        "back per entry to links/URLs; numeric: page "
                        "locators only; anchor: href / URL / #fragment is "
                        "the locator (text: 'heading<TAB>locator'); none: "
                        "the heading is its own locator (nothing split off; "
                        "a trailing [gloss] or TAB column is ignored)")
    p.add_argument("--sections", choices=["split", "merge"],
                   default="split",
                   help="HTML: h1-h4 headings (and ids such as 'structs', "
                        "'functions'); text: 2+ explicit heading lines "
                        "('## Index of places', 'INDEX OF NAMES'). They "
                        "separate sequences that are linted separately "
                        "(split, default) or as one (merge)")
    p.add_argument("--only-section", metavar="REGEX",
                   help="lint only sections whose label matches REGEX "
                        "(case-insensitive), e.g. '^Index$'; for text also "
                        "a single-letter group, e.g. '^B$'")
    p.add_argument("--heading-regex", metavar="REGEX",
                   help="file each heading on group 1 of REGEX (the rest "
                        "is display noise or a leading qualifier), e.g. "
                        r"'^(?:func (?:\([^)]*\) )?|type )?(\w+)'")
    p.add_argument("--qualifier-suffix", metavar="LIST",
                   help="comma-separated suffixes that act as qualifiers: "
                        "'term-guide' files as 'term (guide)' (8.5), e.g. "
                        "'-api,-guide,-reference'")
    p.add_argument("--compare-locales", metavar="L1,L2,...",
                   help="re-sort top-level headings with locale.strxfrm "
                        "under each locale and report (8.1-LOCALE info) "
                        "entries whose relative position changes; "
                        "unavailable locales are skipped and named")
    p.add_argument("--numerals", choices=["numeric", "ignore"],
                   default="numeric",
                   help="how to treat numeral-initial headings")
    p.add_argument("--max-locators", type=int, default=6, metavar="N",
                   help="warn when an entry has more than N undifferentiated "
                        "locators (default 6; heuristic, 7.2.3.5/7.4.3)")
    p.add_argument("--ignore-function-words", action="store_true",
                   help="ignore a leading preposition/conjunction (not an "
                        "article) when filing subheadings (8.6)")
    p.add_argument("--roman", choices=["strict", "off"], default="strict",
                   help="when a leading upper-case roman numeral files as a "
                        "number (default strict; see below)")
    p.add_argument("--roman-list", metavar="FILE",
                   help="file of roman numerals (one per line, '#' "
                        "comments) that always file as numbers when they "
                        "begin a heading (strict mode)")
    p.add_argument("--inversion", choices=["before", "after"],
                   default="after",
                   help="where inverted 'term, x' files relative to "
                        "'term (x)' (8.5; default after)")
    p.add_argument("--subheading-order", choices=["alpha", "page"],
                   default="alpha",
                   help="declare a deliberate page-order arrangement of "
                        "subheadings (8.6; default alpha)")
    p.add_argument("--locale-fold", choices=["basic", "none"],
                   default="basic",
                   help="basic: fold diacritics to base letters (default); "
                        "none: case-fold only. No locale collation is "
                        "shipped (e.g. Swedish å after z)")
    p.add_argument("--skip-until", metavar="REGEX",
                   help="text input: skip lines before the first line "
                        "matching REGEX (an introductory note); disables "
                        "automatic note detection")
    p.add_argument("--no-auto-preamble", action="store_true",
                   help="text input: do not auto-detect and skip a leading "
                        "prose introductory note")
    p.add_argument("--ignore-honorifics", action="store_true",
                   help="file inverted names without honorifics ('Forbes, "
                        "Mr. D.' as 'Forbes, D.'); without it, a pair in "
                        "order only when they are ignored is 7.3.1-"
                        "HONORIFIC info")
    p.add_argument("--verbose-pairs", action="store_true",
                   help="list every finding that a summary replaces: "
                        "order pairs an 8-ROOTCAUSE explains (as info), "
                        "and rules repeated 10+ times")
    p.add_argument("--dump-tree", action="store_true",
                   help="print the parsed entry tree as JSON and exit "
                        "(check how the layout was read)")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("--min-severity", choices=["info", "warn"],
                   default="info", help="hide findings below this level")
    p.add_argument("--list-rules", action="store_true",
                   help="print the rule catalogue and exit")
    p.add_argument("--version", action="version", version=__version__)
    return p


# Output encoding. On Windows a redirected or piped stdout uses the ANSI code page
# (often cp1252). When stdout is not UTF-8, JSON is written ASCII-only (\uXXXX
# escapes: valid and lossless) and text output uses backslashreplace, so printing
# never raises UnicodeEncodeError.
_JSON_ASCII = False


def _is_utf8(stream):
    enc = (getattr(stream, "encoding", None) or "").lower().replace("-", "").replace("_", "")
    return enc in ("utf8", "utf8sig")


def _safe_stdio():
    global _JSON_ASCII
    _JSON_ASCII = not _is_utf8(sys.stdout)
    for stream in (sys.stdout, sys.stderr):
        if not _is_utf8(stream) and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="backslashreplace")
            except (ValueError, OSError):
                pass


def main(argv: Optional[List[str]] = None) -> int:
    _safe_stdio()
    ap = _build_argparser()
    args = ap.parse_args(argv)
    if args.list_rules:
        for rid, (clause, sev, title) in RULES.items():
            print(f"{rid:28} §{clause:14} {sev:5} {title}")
        print("\nSeverity notes: ASCENDING is info because 7.4 only "
              "illustrates ascending order; DUPLICATE stays warn because a "
              "repeated locator is a defect. PAGEORDER becomes SYSTEMATIC "
              "(info) with --subheading-order page. 7.4.5-SEPARATOR and "
              "7.5.2.1-PLACEMENT are info when the style is consistent and "
              "unambiguous (see-also before locators is the exception for "
              "card/screen/very detailed indexes). NOTE, NUMBER and VARIANT "
              "are info. CASE-ORDER replaces 8.2/8.5-ORDER for a pair that "
              "is in order under a case-sensitive code-point sort; 8.5 "
              "needs a bare term, 'term (qualifier)' or inverted 'term, x' "
              "in the pair. RUNS replaces PAGEORDER when the subheadings "
              "restart the alphabet in 2+ runs of 2+. DISPLACED (info) "
              "counts entries minus the longest in-order subsequence. "
              "HOMOGRAPH (info) replaces DUPLICATE in case-significant "
              "mode. LOCALE (info) only with --compare-locales. "
              "ROOTCAUSE (warn) replaces the per-pair order findings one "
              "other sort key explains (--verbose-pairs keeps them as "
              "info). ABBREV replaces ORDER for abbreviation misfilings; "
              "HONORIFIC (info) replaces 8.5-ORDER when ignoring an "
              "honorific explains the pair. PARSE-HEALTH (info) flags a "
              "probable misread layout. SEQORDER (info) replaces ASCENDING "
              "when the only disorder is roman front matter after arabic "
              "pages. SPECIAL is info (Advisory: one special-matter scheme "
              "is preferable; bold is treated as the principal-locator "
              "mark and not counted). INDENT and TURNOVER read text "
              "layouts only. ARTICLE also replaces ORDER for a front "
              "article ignored in filing (one info if every such heading "
              "does so); ABBREV also covers initialisms filed by their "
              "punctuation.")
        return 0
    if not args.path:
        ap.print_usage(sys.stderr)
        print("iso999_lint.py: error: a path is required", file=sys.stderr)
        return 2
    if args.max_locators < 1:
        print("iso999_lint.py: error: --max-locators must be >= 1",
              file=sys.stderr)
        return 2
    try:
        if args.path == "-":
            text = sys.stdin.read()
        else:
            with open(args.path, encoding="utf-8-sig") as fh:
                text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"iso999_lint.py: error: cannot read {args.path}: {exc}",
              file=sys.stderr)
        return 2
    roman_list: frozenset = frozenset()
    if args.roman_list:
        try:
            with open(args.roman_list, encoding="utf-8-sig") as fh:
                roman_list = frozenset(
                    ln.split("#", 1)[0].strip().upper() for ln in fh
                    if ln.split("#", 1)[0].strip())
        except (OSError, UnicodeDecodeError) as exc:
            print(f"iso999_lint.py: error: cannot read {args.roman_list}: "
                  f"{exc}", file=sys.stderr)
            return 2
        bad = sorted(r for r in roman_list if roman_to_int(r) is None)
        if bad:
            print(f"iso999_lint.py: error: not roman numerals in "
                  f"{args.roman_list}: {', '.join(bad)}", file=sys.stderr)
            return 2
    if args.skip_until is not None:
        try:
            re.compile(args.skip_until)
        except re.error as exc:
            print(f"iso999_lint.py: error: bad --skip-until pattern: {exc}",
                  file=sys.stderr)
            return 2
    if args.heading_regex is not None:
        try:
            if re.compile(args.heading_regex).groups < 1:
                raise re.error("needs a capturing group (group 1 = filing "
                               "text)")
        except re.error as exc:
            print(f"iso999_lint.py: error: bad --heading-regex: {exc}",
                  file=sys.stderr)
            return 2
    if args.only_section is not None:
        try:
            re.compile(args.only_section)
        except re.error as exc:
            print(f"iso999_lint.py: error: bad --only-section: {exc}",
                  file=sys.stderr)
            return 2
    suffixes = tuple(x.strip() for x in (args.qualifier_suffix or
                                         "").split(",") if x.strip())
    locales = tuple(x.strip() for x in (args.compare_locales or
                                        "").split(",") if x.strip())
    fmt = args.format if args.format != "auto" else \
        detect_format(args.path, text)
    opts = Options(filing=args.filing, numerals=args.numerals,
                   max_locators=args.max_locators,
                   func_words=args.ignore_function_words,
                   roman=args.roman, roman_list=roman_list,
                   inversion=args.inversion,
                   subheading_order=args.subheading_order,
                   locale_fold=args.locale_fold,
                   skip_until=args.skip_until,
                   auto_preamble=not args.no_auto_preamble,
                   locators=args.locators, sections=args.sections,
                   only_section=args.only_section,
                   heading_regex=args.heading_regex,
                   qualifier_suffixes=suffixes,
                   case_significant=args.case_significant,
                   compare_locales=locales,
                   ignore_honorifics=args.ignore_honorifics,
                   verbose_pairs=args.verbose_pairs)
    if args.dump_tree:
        try:
            sequences, meta = parse_index(text, fmt, opts)
        except ParseError as exc:
            print(f"iso999_lint.py: parse error ({fmt}): {exc}",
                  file=sys.stderr)
            return 2
        d = {"file": args.path, "format": fmt}
        d.update(dump_tree(sequences, meta))
        json.dump(d, sys.stdout, indent=1, ensure_ascii=_JSON_ASCII)
        print()
        return 0
    try:
        roots, findings = lint_text(text, fmt, opts)
    except ParseError as exc:
        print(f"iso999_lint.py: parse error ({fmt}): {exc}", file=sys.stderr)
        return 2
    shown = [f for f in findings
             if args.min_severity == "info" or f.severity == "warn"]
    n_warn = sum(1 for f in findings if f.severity == "warn")
    n_info = sum(1 for f in findings if f.severity == "info")
    n_entries = sum(1 for _ in walk(roots))
    if args.json:
        json.dump({"file": args.path, "format": fmt, "filing": opts.filing,
                   "numerals": opts.numerals, "roman": opts.roman,
                   "inversion": opts.inversion,
                   "subheading_order": opts.subheading_order,
                   "locale_fold": opts.locale_fold, "entries": n_entries,
                   "locators": opts.locators, "sections": opts.sections,
                   "case_significant": opts.case_sig,
                   "summary": {"warn": n_warn, "info": n_info},
                   "findings": [f.as_dict() for f in shown]},
                  sys.stdout, indent=2, ensure_ascii=_JSON_ASCII)
        print()
    else:
        print(f"{args.path}: format={fmt} filing={opts.filing} "
              f"locators={opts.locators} entries={n_entries}")
        for f in shown:
            loc = f"{str(f.line):>5}" if f.line else "    -"
            print(f"{loc}  {f.severity.upper():4}  {f.rule} (§{f.clause})  "
                  f"{f.message}")
        print(f"{n_warn} warning(s), {n_info} info. Heuristic check against "
              f"ISO 999 guidance; review each finding.")
    return 1 if n_warn else 0


if __name__ == "__main__":
    sys.exit(main())
