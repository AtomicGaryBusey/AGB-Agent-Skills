#!/usr/bin/env python3
"""Build a local STE dictionary cache from the user's own copy of the spec PDF.

The ASD-STE100 specification is copyright ASD. This tool never ships any part
of it. It reads the PDF that the user downloaded, parses Part 2 (Dictionary),
and writes a compact lookup cache to ``.cache/`` (gitignored). The cache keeps
only: word, part of speech, approved flag, a short meaning (at most 12 words,
for local lookup), alternatives, cross-references and word forms. It does not
keep the STE or non-STE examples.

Usage:
    build_dictionary.py [--pdf PATH | --download] [--out PATH] [--check]

Requirements: Python 3.8+ standard library and the ``pdftotext`` command from
poppler (``brew install poppler`` or ``apt install poppler-utils``).

How the parser works (layout facts that were measured, not copied):
  * ``pdftotext -bbox`` gives every word with its box. Dictionary pages have a
    four-column table header ("Word", "Approved", "STE", "Non-STE") whose x
    positions give the column starts for that page.
  * Column 1 headwords are bold. In this PDF the bold font gives a box height
    of about 10.2 pt, and the body font about 15.1 pt. Help text that sits in
    column 1 (for example "No other verb forms.") uses the body font, so the
    height separates headwords from help text.
  * A headword ends at its part-of-speech tag, for example ``(v)``. A tag with
    a trailing comma starts a comma-separated list of verb forms. An
    upper-case group in parentheses after ``(adj)`` gives comparative and
    superlative forms. ``(also ...)`` adds more forms.
  * Column 2 text between one headword and the next belongs to that headword.
    Text at the column's left edge is a meaning or an alternative. Text that
    is indented by more than about 25 pt is help text.
"""

from __future__ import annotations

import argparse
import collections
import datetime as _dt
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

BUILDER_VERSION = "1.0.1"
SOURCE = "ASD-STE100 Issue 9"
ISSUE_DATE = "2025-01-15"
PUBLIC_URL = "https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf"
# Fallback totals if the intro text cannot be read. The build reads the real
# totals from the PDF's Part 2 introduction when it can.
DEFAULT_EXPECTED = {"approved": 875, "not_approved": 1274}

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / ".cache" / "ste100-dictionary.json"
DEFAULT_PDF = REPO_ROOT / ".cache" / "ASD-STE100_ISSUE9.pdf"

POS_TAGS = ("n", "v", "adj", "adv", "prep", "conj", "pron", "art", "prefix", "num")
ALT_TAGS = POS_TAGS + ("TN", "TV")
MEANING_MAX_WORDS = 12

# Layout thresholds (points).
BODY_TOP = 89.0          # below the running header and table header row
BODY_BOTTOM = 720.0      # above the running footer
BOLD_MAX_HEIGHT = 12.5   # column-1 headword font box height is ~10.2
HELP_INDENT = 25.0       # column-2 help text is indented ~34 pt
LINE_GAP = 14.0          # consecutive lines are ~12 pt apart
Y_TOLERANCE = 5.0        # baseline offset between fonts in one table row

_WORD_RE = re.compile(
    r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>'
)
_POS_RE = re.compile(r"\((%s)\)(,?)" % "|".join(POS_TAGS))
_ALT_RE = re.compile(r"(.+?)\s*\((%s)\)" % "|".join(ALT_TAGS))


class BuildError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# PDF text extraction
# --------------------------------------------------------------------------

def require_pdftotext() -> str:
    exe = shutil.which("pdftotext")
    if not exe:
        raise BuildError(
            "pdftotext was not found. Install poppler "
            "(macOS: brew install poppler; Debian/Ubuntu: apt install poppler-utils) "
            "and run this command again."
        )
    return exe


def pdf_bbox_pages(pdf: Path) -> list:
    """Return a list of pages; each page is a list of (x0, y0, x1, y1, text)."""
    exe = require_pdftotext()
    proc = subprocess.run(
        [exe, "-bbox", str(pdf), "-"], capture_output=True, check=False
    )
    if proc.returncode != 0:
        raise BuildError("pdftotext failed: %s" % proc.stderr.decode("utf-8", "replace").strip())
    return parse_bbox_html(proc.stdout.decode("utf-8", "replace"))


def parse_bbox_html(text: str) -> list:
    pages = []
    for chunk in text.split("<page ")[1:]:
        words = []
        for m in _WORD_RE.finditer(chunk):
            x0, y0, x1, y1 = (float(v) for v in m.groups()[:4])
            words.append((x0, y0, x1, y1, html.unescape(m.group(5))))
        pages.append(words)
    return pages


def page_text(words) -> str:
    return " ".join(w[4] for w in words)


def stated_totals(pages) -> dict:
    """Read the approved / not-approved totals from the Part 2 introduction."""
    for words in pages:
        text = page_text(words)
        a = re.search(r"\((\d[\d ,]*) approved words\)", text)
        n = re.search(r"not approved \((\d[\d ,]*) words\)", text)
        if a and n:
            return {
                "approved": int(re.sub(r"\D", "", a.group(1))),
                "not_approved": int(re.sub(r"\D", "", n.group(1))),
            }
    return dict(DEFAULT_EXPECTED)


# --------------------------------------------------------------------------
# Page model: dictionary pages, columns, lines
# --------------------------------------------------------------------------

def is_dictionary_page(words) -> bool:
    footer = [w[4] for w in words if w[1] > BODY_BOTTOM]
    header = {w[4] for w in words if 55 < w[1] < BODY_TOP}
    return any(re.fullmatch(r"2-1-[A-Z]+\d+", t) for t in footer) and {
        "Word", "Approved", "Non-STE"} <= header


def _edge_x(words, lo, hi, fallback):
    """Left edge of a column: the smallest x in [lo, hi) where 3+ words start.

    Cells are left aligned, so many words start at the column edge. Hanging
    indents and help text start further right. Column edges move by a few
    points from page to page, so the header position is only a fallback.
    """
    c = collections.Counter(round(w[0]) for w in words if lo <= w[0] < hi)
    edges = [x for x, n in c.items() if n >= 3]
    return min(edges) if edges else fallback


def column_starts(words):
    """Return x starts for columns 1..4 for one page."""
    hdr = {w[4]: w[0] for w in words if 55 < w[1] < BODY_TOP}
    c0 = hdr["Word"]
    body = [w for w in words if BODY_TOP < w[1] < BODY_BOTTOM]
    c1 = _edge_x(body, c0 + 95, c0 + 135, hdr.get("Approved", c0 + 108))
    c2 = _edge_x(body, c0 + 212, c0 + 250, hdr.get("STE", c0 + 237.6))
    c3 = _edge_x(body, c0 + 340, c0 + 385, hdr.get("Non-STE", c0 + 367.3))
    return (c0, c1 - 1.5, c2 - 1.5, c3 - 1.5)


class Line:
    __slots__ = ("page", "col", "y", "indent", "bold", "text")

    def __init__(self, page, col, y, indent, bold, text):
        self.page, self.col, self.y = page, col, y
        self.indent, self.bold, self.text = indent, bold, text

    def __repr__(self):
        return "Line(p%d c%d y%.0f i%.0f %s %r)" % (
            self.page, self.col, self.y, self.indent, "B" if self.bold else "-", self.text)


def page_lines(words, page_no):
    """Group words of one dictionary page into lines for columns 1 and 2."""
    cols = column_starts(words)
    groups = collections.defaultdict(list)
    for w in words:
        if not (BODY_TOP < w[1] < BODY_BOTTOM):
            continue
        col = 0
        for i, start in enumerate(cols):
            if w[0] >= start:
                col = i
        if col > 1:
            continue  # columns 3 and 4 are examples: never read
        bold = (w[3] - w[1]) < BOLD_MAX_HEIGHT
        groups[(col, round(w[1], 0), bold)].append(w)
    lines = []
    for (col, _y, bold), ws in groups.items():
        ws.sort(key=lambda w: w[0])
        lines.append(Line(page_no, col, ws[0][1], ws[0][0] - cols[col], bold,
                          " ".join(w[4] for w in ws)))
    lines.sort(key=lambda l: (l.y, l.col))
    return lines


# --------------------------------------------------------------------------
# Column 1: headwords, parts of speech, listed forms
# --------------------------------------------------------------------------

def _join(text, more, sep=" "):
    """Join two column-1 fragments. A fragment that ends in a letter plus "-"
    is a soft hyphen wrap, so it joins with no space and no hyphen."""
    more = more.strip()
    if not text:
        return more
    if text.endswith("-") and len(text) > 1 and text[-2].isalpha() and more[:1].isalpha():
        return text[:-1] + more
    return text + sep + more


def _norm(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\(\s+", "(", s)
    s = re.sub(r"\s+\)", ")", s)
    return s


def split_forms(text):
    text = re.sub(r"[()]", " ", text)
    text = re.sub(r"\balso\b", " ", text)
    return [_norm(f) for f in re.split(r"[,\n]", text) if _norm(f)]


def group_rows(lines):
    """Group bold column-1 lines into table rows.

    Lines in one cell are ~12 pt apart; the next row starts at least ~18 pt
    lower, because every row has padding. A page break also ends a row.
    """
    rows = []
    for ln in lines:
        if rows and rows[-1][-1].page == ln.page and ln.y - rows[-1][-1].y <= LINE_GAP:
            rows[-1].append(ln)
        else:
            rows.append([ln])
    return rows


def _looks_like_forms(text):
    """True for a row that holds only listed forms (a row split by a page break)."""
    t = text.strip()
    return bool(re.fullmatch(r"\(?(also )?[A-Z][A-Z ,'-]*\)?,?", t)) and "," in t


def parse_headwords(lines):
    """Parse bold column-1 lines into raw entries, one per table row.

    Returns (entries, leftovers). Each entry: dict(display, pos, forms_listed,
    line). The headword ends at its part-of-speech tag. Everything after the
    tag in the same cell is a list of forms (verb forms, or comparative and
    superlative forms in parentheses). The spec is not consistent about the
    commas after verb forms, so each cell line is also a separator.
    A few headwords have no part-of-speech tag; they get pos None.
    """
    entries, leftovers = [], []
    for row in group_rows(lines):
        text = ""
        for ln in row:
            text = _join(text, ln.text, "\n")
        tags = list(_POS_RE.finditer(text))
        if not tags:
            prev = entries[-1] if entries else None
            if prev and row[0].page != prev["line"].page and _looks_like_forms(text.replace("\n", ", ")):
                prev["forms_listed"] += split_forms(text)
                leftovers.append("forms continued on next page: %s %s" % (prev["display"], text))
                continue
            entries.append({"display": _norm(text), "pos": None, "forms_listed": [], "line": row[0]})
            continue
        if len(tags) > 1:
            leftovers.append("several part-of-speech tags in one cell: %s" % text)
        m = tags[0]
        head = _norm(text[:m.start()])
        forms = split_forms(text[m.end():])
        if forms and not is_approved(head):
            leftovers.append("forms on a not-approved entry %s: %s" % (head, forms))
            forms = []
        entries.append({"display": head, "pos": m.group(1), "forms_listed": forms, "line": row[0]})
    return entries, leftovers


# --------------------------------------------------------------------------
# Column 2: meanings, alternatives, help
# --------------------------------------------------------------------------

def paragraphs(lines):
    """Split column-2 lines into (kind, text, first_line) paragraphs.

    kind is "main" for text at the column edge and "help" for indented help.
    A new paragraph starts at a vertical gap, a change of kind, or a
    numbered meaning ("2. ...").
    """
    paras = []
    prev = None
    for ln in lines:
        kind = "help" if ln.indent > HELP_INDENT else "main"
        new = (
            prev is None
            or kind != paras[-1][0]
            or ln.page != prev.page
            or ln.y - prev.y > LINE_GAP
            or (kind == "main" and re.match(r"\d+\.\s", ln.text) and ln.indent < 5)
        )
        if new:
            paras.append([kind, ln.text, ln])
        else:
            paras[-1][1] += "\n" + ln.text
        prev = ln
    return [(k, "\n".join(_norm(x) for x in t.split("\n")), l) for k, t, l in paras]


def is_upper_text(s):
    letters = [c for c in s if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters if c not in "…")


def _alt_is_upper(s):
    # Allow unit symbols and lower-case parts of speech inside parentheses.
    core = re.sub(r"\((%s)\)" % "|".join(ALT_TAGS), "", s)
    letters = [c for c in core if c.isalpha()]
    return bool(letters) and sum(c.isupper() for c in letters) >= 0.8 * len(letters)


_TAG_RE = re.compile(r"\s*[\[(](%s)[\])]" % "|".join(ALT_TAGS))
_LONE_TAG_RE = re.compile(r"\((%s)\),?" % "|".join(ALT_TAGS))


def _alt(word, pos=None, kind="approved"):
    return {"word": _norm(word).lower(), "pos": pos, "kind": kind}


def parse_alternatives(text):
    """Parse one upper-case alternatives paragraph into alternative dicts.

    Forms handled (all invented here):
      "FOO (v)"                  -> foo, pos v
      "BAR (TN)"                 -> bar, kind TN
      "FOO (adj), BAR (adj)"     -> two alternatives
      "AT THE FOO"               -> a phrase, pos None
      "FOO (v) (WITH A BAR [TN])"-> foo, with context "with a bar"
      "FOO (v) … BAR"            -> one phrase "foo … bar", pos None
    """
    items = []
    closed = True
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if items and _LONE_TAG_RE.fullmatch(line):
            # The tag of a long alternative wraps to its own line.
            items[-1] += " " + line
        elif closed or not items or line.startswith("("):
            items.append(line)
        else:
            items[-1] += " " + line  # a phrase that wraps to the next line
        closed = bool(re.search(r"\)$", line))
    out = []
    for item in items:
        out += _parse_alt_item(item, out)
    return out


def _parse_alt_item(text, before):
    """Parse one alternatives item. ``before`` holds earlier results, so that a
    parenthesized qualifier can attach to the alternative before it."""
    text = _norm(text)
    if "…" in text or "..." in text or re.search(
            r"\((?:%s)\) [A-Z]" % "|".join(ALT_TAGS), text):
        # A phrase: "FOO (v) … BAR" or "FOO (TN) BAR".
        return [_alt(_TAG_RE.sub("", text))]
    out = []
    pos = 0
    chunks = []
    for m in _ALT_RE.finditer(text):
        chunks.append((text[pos:m.start()], None))
        chunks.append((m.group(1), m.group(2)))
        pos = m.end()
    chunks.append((text[pos:], None))
    for chunk, tag in chunks:
        chunk = chunk.strip(" ,;")
        if not chunk:
            continue
        # A parenthesized qualifier belongs to the alternative before it.
        ctx = re.match(r"^\((.*?)\)?$", chunk) if chunk.startswith("(") else None
        if ctx is None and chunk.startswith("("):
            ctx = re.match(r"^\((.*)", chunk)
        if ctx:
            target = out[-1] if out else (before[-1] if before else None)
            if target is not None:
                note = _norm(_TAG_RE.sub("", ctx.group(1))).lower().rstrip(")")
                target["context"] = (target.get("context", "") + " " + note).strip()
            continue
        if tag is None:
            if not _alt_is_upper(chunk):
                continue
            for part in re.split(r",\s+", chunk):
                if part:
                    out.append(_alt(part))
            continue
        # "A (adj), B (adj)": the text before the last comma is not part of B.
        parts = re.split(r",\s+(?=[A-Z])", chunk)
        for part in parts[:-1]:
            out.append(_alt(part))
        kind = tag if tag in ("TN", "TV") else "approved"
        out.append(_alt(parts[-1], None if kind != "approved" else tag, kind))
    return out


def short_meaning(text):
    t = re.sub(r"^\d+\.\s*", "", _norm(text)).strip()
    words = t.split()
    if len(words) > MEANING_MAX_WORDS:
        words = words[:MEANING_MAX_WORDS] + ["…"]
    return " ".join(words)


_REF_RE = re.compile(
    r"[Rr]efer(?: also)? to\s+(?:“([^”]+)”|((?:[A-Z][A-Z-]*\s?)+(?:\((?:%s)\))?))"
    % "|".join(POS_TAGS)
)


def parse_refs(help_text):
    refs = []
    for m in _REF_RE.finditer(help_text):
        r = _norm(m.group(1) or m.group(2) or "").rstrip(".,")
        if r and not re.match(r"(rule|section|part)\b", r, re.I):
            refs.append(r.lower())
    return refs


# --------------------------------------------------------------------------
# Forms
# --------------------------------------------------------------------------

def surface_forms_of_headword(display):
    """Surface forms for a headword such as "so (that)" or "MATT (or MATTE)"."""
    low = display.lower()
    m = re.fullmatch(r"(.+?)\s*\((.+)\)", low)
    if not m:
        return [low]
    base, inner = m.group(1).strip(), m.group(2).strip()
    if inner.startswith("or "):
        return [base, inner[3:].strip()]
    if base in inner:
        return [inner]
    return ["%s %s" % (base, inner)]


def _plural(noun):
    if " " in noun:
        head, last = noun.rsplit(" ", 1)
        return head + " " + _plural(last)
    if re.search(r"(s|x|z|ch|sh)$", noun):
        return noun + "es"
    if re.search(r"[^aeiou]y$", noun):
        return noun[:-1] + "ies"
    return noun + "s"


def _verb_variants(verb):
    """Regular inflections of a verb that is NOT approved (detection only)."""
    if " " in verb:
        head, tail = verb.split(" ", 1)
        return [v + " " + tail for v in _verb_variants(head)]
    s = _plural(verb)
    if verb.endswith("e"):
        ed, ing = verb + "d", verb[:-1] + "ing"
    elif re.search(r"[^aeiou]y$", verb):
        ed, ing = verb[:-1] + "ied", verb + "ing"
    else:
        ed, ing = verb + "ed", verb + "ing"
    out = [s, ed, ing]
    if re.search(r"[^aeiou][aeiou][b-df-hj-np-tvz]$", verb):
        # Consonant doubling ("-pped") is common but not predictable; add both.
        out += [verb + verb[-1] + "ed", verb + verb[-1] + "ing"]
    return out


def compute_forms(entry):
    """Return (forms, variants).

    forms: surface forms the spec permits for the entry (headword, the verb
    and adjective forms the dictionary lists, and plural forms of approved
    nouns, which Part 2 permits for countable nouns).
    variants: regular inflections of words that are not approved, so that a
    checker can find them in text. They are never permitted forms.
    """
    base = surface_forms_of_headword(entry["display"])
    forms = list(base)
    variants = []
    for f in entry["forms_listed"]:
        f = f.lower()
        if f not in forms:
            forms.append(f)
    single = len(base) == 1 and not re.search(r"[().…]", base[0])
    if entry["pos"] == "n" and single and not base[0].endswith("-"):
        pl = _plural(base[0])
        if entry["approved"]:
            if not entry.get("no_plural") and pl not in forms:
                forms.append(pl)
        else:
            variants.append(pl)
    if entry["pos"] == "v" and not entry["approved"] and single:
        variants += [v for v in _verb_variants(base[0]) if v not in forms]
    return forms, variants


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def is_approved(display):
    """Upper-case headword = approved. Ignore text inside parentheses."""
    core = re.sub(r"\(.*?\)", "", display)
    letters = [c for c in core if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def parse_dictionary(pages):
    """Parse bbox pages. Return (entries, diagnostics)."""
    dict_pages = [i for i, ws in enumerate(pages) if is_dictionary_page(ws)]
    if not dict_pages:
        raise BuildError("No Part 2 dictionary pages found. Is this the ASD-STE100 Issue 9 PDF?")
    col0, col1 = [], []
    for i in dict_pages:
        for ln in page_lines(pages[i], i + 1):
            if ln.col == 0 and ln.bold:
                col0.append(ln)
            elif ln.col == 0:
                # Help text in column 1 ("No other verb forms.").
                col1.append(Line(ln.page, 1, ln.y, 99.0, False, ln.text))
            else:
                col1.append(ln)
    raw, leftovers = parse_headwords(col0)

    # Assign column-2 lines to entries by (page, y).
    keys = [(e["line"].page, e["line"].y - Y_TOLERANCE) for e in raw]
    per_entry = [[] for _ in raw]
    orphan = []
    j = 0
    col1.sort(key=lambda l: (l.page, l.y))
    for ln in col1:
        while j + 1 < len(keys) and keys[j + 1] <= (ln.page, ln.y):
            j += 1
        if keys[0] > (ln.page, ln.y):
            orphan.append(ln)
        else:
            per_entry[j].append(ln)

    entries = []
    for e, lines in zip(raw, per_entry):
        approved = is_approved(e["display"])
        paras = paragraphs(lines)
        main = [p for p in paras if p[0] == "main"]
        helps = [p[1] for p in paras if p[0] == "help"]
        meaning = None
        alternatives = []
        for _k, t, _l in main:
            if approved and meaning is None and not is_upper_text(t):
                meaning = short_meaning(t)
            elif _alt_is_upper(t):
                alternatives += parse_alternatives(t)
        help_text = _norm(" ".join(helps))
        refs = parse_refs(help_text)
        no_plural = bool(re.search(r"\bno plural\b|\bonly (?:in )?the singular\b", help_text, re.I))
        entry = {
            "word": surface_forms_of_headword(e["display"])[0] if "(" in e["display"] else e["display"].lower(),
            "display": e["display"],
            "pos": e["pos"],
            "approved": approved,
            "meaning": meaning,
            "alternatives": alternatives,
            "forms_listed": e["forms_listed"],
            "no_plural": no_plural,
            "no_other_forms": bool(re.search(r"No other (verb )?forms", help_text)),
            "refs": refs,
            "help": bool(help_text),
            "page": e["line"].page,
        }
        entries.append(entry)
    diag = {"dictionary_pages": [dict_pages[0] + 1, dict_pages[-1] + 1],
            "leftover_text": leftovers, "orphan_lines": len(orphan)}
    return entries, diag


def finalize(entries):
    out = []
    index = collections.defaultdict(list)
    for e in entries:
        forms, variants = compute_forms(e)
        rec = {
            "word": e["word"],
            "display": e["display"],
            "pos": e["pos"],
            "approved": e["approved"],
            "meaning": e["meaning"] if e["approved"] else None,
            "forms": forms,
            "alternatives": e["alternatives"],
        }
        if variants:
            rec["variants"] = variants
        if e["refs"]:
            rec["refs"] = e["refs"]
        out.append(rec)
        for f in forms:
            index[f].append({"word": rec["word"], "pos": rec["pos"], "approved": rec["approved"]})
        for f in variants:
            if not any(x["word"] == rec["word"] and x["pos"] == rec["pos"] for x in index[f]):
                index[f].append({"word": rec["word"], "pos": rec["pos"],
                                 "approved": rec["approved"], "variant": True})
    return out, dict(sorted(index.items()))


def validate(entries, expected):
    """Return (counts, problems, notes).

    problems: things that suggest a parser error or a count mismatch.
    notes: facts about the source that are not parser errors.
    """
    approved = sum(1 for e in entries if e["approved"])
    not_approved = len(entries) - approved
    problems, notes = [], []
    if approved != expected["approved"]:
        problems.append("approved count %d != stated %d (%+d)"
                        % (approved, expected["approved"], approved - expected["approved"]))
    if not_approved != expected["not_approved"]:
        problems.append("not-approved count %d != stated %d (%+d)"
                        % (not_approved, expected["not_approved"], not_approved - expected["not_approved"]))
    seen = collections.Counter((e["display"], e["pos"]) for e in entries)
    for k, v in seen.items():
        if v > 1:
            problems.append("duplicate entry %s (%s) x%d" % (k[0], k[1], v))
    for e in entries:
        tag = "%s (%s)" % (e["display"], e["pos"])
        if e["pos"] is None:
            notes.append("no part of speech in column 1: %s" % e["display"])
        if not e["approved"] and not e["alternatives"]:
            if e["help"]:
                notes.append("no alternative word, help text only: %s" % tag)
            else:
                problems.append("no alternatives parsed: %s" % tag)
        if e["approved"] and not e["meaning"]:
            problems.append("no meaning parsed: %s" % tag)
        if e["approved"] and e["pos"] == "v" and not e["forms_listed"] and not e["no_other_forms"]:
            notes.append("approved verb lists no other forms and has no 'no other forms' help: %s" % tag)
    return {"approved": approved, "not_approved": not_approved, "entries": len(entries)}, problems, notes


def highlights_check(pages, entries):
    """Cross-check against the change list in the spec's Highlights section.

    Every word that the change list names (except the ones it says were
    removed) must be in the parsed dictionary, and no removed word may be.
    Returns a list of messages.
    """
    have = {(e["display"], e["pos"]) for e in entries}
    by_word = collections.defaultdict(list)
    for e in entries:
        by_word[e["display"]].append(e["pos"])
    named = 0
    msgs = []
    for ws in pages:
        if not any(w[4] == "Highlights" and w[1] > BODY_BOTTOM for w in ws):
            continue
        rows = collections.defaultdict(list)
        for w in ws:
            rows[round(w[1])].append(w)
        for y in sorted(rows):
            r = sorted(rows[y])
            if r[0][0] > 80:
                continue
            left = [r[0]]
            for w in r[1:]:
                if w[0] - left[-1][2] > 15:
                    break
                left.append(w)
            m = re.fullmatch(r"(.+?) \((%s)\)" % "|".join(POS_TAGS), " ".join(w[4] for w in left))
            if not m:
                continue
            named += 1
            key = (m.group(1), m.group(2))
            removed = "Removed from the word list" in " ".join(w[4] for w in r[len(left):])
            if removed and key in have:
                msgs.append("change list says removed, but present: %s (%s)" % key)
            elif not removed and key not in have:
                other = by_word.get(key[0])
                msgs.append("change list names %s (%s), not found%s" % (
                    key[0], key[1], "; dictionary has it as (%s)" % ", ".join(map(str, other)) if other else ""))
    return named, msgs


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build(pdf: Path):
    pages = pdf_bbox_pages(pdf)
    expected = stated_totals(pages)
    raw, diag = parse_dictionary(pages)
    counts, problems, notes = validate(raw, expected)
    named, hl = highlights_check(pages, raw)
    diag["highlights_named"] = named
    diag["highlights_mismatches"] = hl
    diag["notes"] = notes
    entries, index = finalize(raw)
    meta = {
        "source": SOURCE,
        "issue_date": ISSUE_DATE,
        "pdf_sha256": sha256_file(pdf),
        "built_at": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
        "builder_version": BUILDER_VERSION,
        "counts": counts,
        "expected_counts": expected,
        "notes": [
            "Local cache built from the user's own copy of the spec. Do not commit or publish.",
            "forms: headword, listed verb/adjective forms, and generated plurals of approved nouns.",
            "variants: generated inflections of not-approved words, for detection only.",
        ],
        "validation": {
            "discrepancies": problems,
            "highlights_named": named,
            "highlights_mismatches": hl,
            "notes": notes,
        },
    }
    return {"meta": meta, "entries": entries, "forms": index}, diag, problems


def download(dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    print("Downloading %s -> %s" % (PUBLIC_URL, dest), file=sys.stderr)
    req = urllib.request.Request(PUBLIC_URL, headers={"User-Agent": "ste100-build-dictionary"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as fh:
        shutil.copyfileobj(r, fh)
    return dest


def check(cache_path: Path, pdf: Path, sha_only: bool = False) -> int:
    if not cache_path.exists():
        print("FAIL: cache not found: %s" % cache_path)
        return 1
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        meta = data["meta"]
    except (ValueError, KeyError) as exc:
        print("FAIL: cache is not valid: %s" % exc)
        return 1
    ok = True
    if not pdf.exists():
        print("FAIL: PDF not found: %s" % pdf)
        return 1
    sha = sha256_file(pdf)
    if sha != meta.get("pdf_sha256"):
        print("FAIL: PDF sha256 %s does not match cache %s" % (sha, meta.get("pdf_sha256")))
        ok = False
    entries = data.get("entries", [])
    approved = sum(1 for e in entries if e.get("approved"))
    actual = {"approved": approved, "not_approved": len(entries) - approved, "entries": len(entries)}
    if actual != meta.get("counts"):
        print("FAIL: entry counts %s do not match meta counts %s" % (actual, meta.get("counts")))
        ok = False
    if ok and not sha_only:
        # Parse the PDF again and compare the counts.
        pages = pdf_bbox_pages(pdf)
        raw, _diag = parse_dictionary(pages)
        fresh, _p, _n = validate(raw, stated_totals(pages))
        if fresh != actual:
            print("FAIL: counts parsed from the PDF %s do not match the cache %s" % (fresh, actual))
            ok = False
        if meta.get("builder_version") != BUILDER_VERSION:
            print("note: cache was built by builder %s; this is %s"
                  % (meta.get("builder_version"), BUILDER_VERSION))
    if ok:
        print("OK: cache matches PDF (sha256 %s..., %d approved, %d not approved)"
              % (sha[:12], actual["approved"], actual["not_approved"]))
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--pdf", type=Path, help="path to your copy of the ASD-STE100 Issue 9 PDF")
    src.add_argument("--download", action="store_true",
                     help="download the public PDF into .cache/ (your own copy)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="cache path (default: %(default)s)")
    ap.add_argument("--check", action="store_true",
                    help="verify that the cache matches the PDF (sha256 and counts); exit 0/1")
    ap.add_argument("--quick", action="store_true",
                    help="with --check: compare sha256 and stored counts only (do not parse the PDF)")
    ap.add_argument("--verbose", action="store_true", help="print every discrepancy")
    args = ap.parse_args(argv)

    try:
        if args.download:
            pdf = download(DEFAULT_PDF)
        else:
            pdf = args.pdf or DEFAULT_PDF
        if args.check:
            return check(args.out, pdf, args.quick)
        if not pdf.exists():
            print("PDF not found: %s\nUse --pdf PATH or --download." % pdf, file=sys.stderr)
            return 2
        data, diag, problems = build(pdf)
    except BuildError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, args.out)
    c, x = data["meta"]["counts"], data["meta"]["expected_counts"]
    print("Wrote %s" % args.out)
    print("approved %d (stated %d), not approved %d (stated %d), entries %d"
          % (c["approved"], x["approved"], c["not_approved"], x["not_approved"], c["entries"]))
    if diag["leftover_text"] or diag["orphan_lines"]:
        print("parser leftovers: %r, orphan lines: %d" % (diag["leftover_text"], diag["orphan_lines"]))
    print("Highlights change list: %d entries named, %d mismatches"
          % (diag["highlights_named"], len(diag["highlights_mismatches"])))
    for m in diag["highlights_mismatches"]:
        print("  - " + m)
    if diag["notes"]:
        print("%d notes (source facts, not parser errors)%s"
              % (len(diag["notes"]), "" if args.verbose else "; use --verbose to list"))
        if args.verbose:
            for n in diag["notes"]:
                print("  - " + n)
    if problems:
        print("%d discrepancies" % len(problems))
        for p in problems:
            print("  - " + p)
    # Count mismatches alone do not fail the build: the stated totals in the
    # Issue 9 introduction are the same as in Issue 8 (see the report).
    hard = [p for p in problems if "count" not in p]
    return 0 if not hard else 1


if __name__ == "__main__":
    sys.exit(main())
