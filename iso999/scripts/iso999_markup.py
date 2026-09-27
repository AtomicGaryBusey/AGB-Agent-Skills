#!/usr/bin/env python3
"""iso999_markup.py - extract and lint index MARKUP embedded in doc sources.

Where ``iso999_lint.py`` checks a finished index, this tool reads the index
entries that authors embed in the documents themselves, across a whole doc
set, and reports problems that show up in the markup before any index is
built. Standard library only.

Supported syntaxes (``--format``)
---------------------------------
* ``latex``  ``\\index{...}`` in .tex/.ltx/.dtx/.sty sources (makeindex
  syntax: ``!`` levels, ``sort@display``, ``|see{..}`` / ``|seealso{..}``,
  ``|(`` / ``|)`` ranges, other ``|encap`` such as ``|textbf``, ``"`` quoting,
  ``\\`` escape before a quote). ``\\index[name]{...}`` (imakeidx) is accepted.
  Choice: ``!``, ``@`` and ``|`` inside a nested ``{...}`` group are treated
  as literal text.
* ``idx``    makeindex ``.idx`` files (``\\indexentry{body}{page}``).
* ``rst``    Sphinx/docutils ``.. index::`` directives (``single:``, ``pair:``,
  ``triple:``, ``see:``, ``seealso:``, the old ``module:``/``keyword:``...
  pair types, plain comma lists, ``!`` main-entry marks) and the
  ``:index:`` role (``:index:`term``` and ``:index:`text <single: a; b>```).
* ``dita``   ``<indexterm>`` (nested levels, ``<index-see>``,
  ``<index-see-also>``, ``<index-sort-as>``, ``start=``/``end=`` ranges).
* ``custom`` any inline syntax, given ``--entry-regex`` with a named group
  ``body`` and optionally ``kind``. A ``kind`` of ``see`` or ``seealso``
  (``see also``, ``see-also``) makes the body ``SOURCE<xref-sep>TARGETS``;
  anything else is an index entry whose body uses the makeindex-lite syntax
  (``!`` levels, ``@`` sort-as, ``|(``/``|)`` ranges, ``|see{}``). The regex
  is compiled with re.DOTALL.
* ``auto``   (default) chooses by file extension, sniffing .txt/.xml/.md.

Rules (ids, clauses, severities: ``--list-rules``)
-------------------------------------------------
Consistency across the doc set (top-level headings, and subentries under
the same parent): singular/plural variants of one heading (7.2.2.2), one
person under initials and full forenames (7.3.1.1), the same words both
direct and inverted, or an inverted "noun, modifier" heading beside direct
"modifier noun" siblings (6.3, 7.2.2.4), and capitalisation-only variants.
Pairs already linked by a see/see-also are not reported. Headings with
different parenthetical qualifiers are treated as different concepts.

Sort-key hygiene: a heading level that starts with a symbol, quote or markup
(8.1) or a numeral (8.3) and has no sort-as key.

Cross-references: see/see-also targets that no entry defines (7.5.1/7.5.2),
see targets that are themselves only see references (chains) and loops,
see references on headings that also carry locators or subentries (3.13),
self-references.

Ranges: ``|(`` never closed, ``|)`` without an open (DITA start/end ids).

HEURISTIC: every finding is a prompt for human review. No text of the
standard is reproduced here; messages are paraphrases citing clause numbers.

Exit status: 0 no warnings, 1 warnings found, 2 usage or read error.
"""

import argparse
import json
import os
import re
import stat
import sys
import threading
import unicodedata
import xml.parsers.expat
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:  # share the case/diacritic fold with the output linter when available
    from iso999_lint import fold as _lint_fold  # type: ignore
except Exception:  # pragma: no cover - fallback when run standalone
    _lint_fold = None


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
# id -> (clause, severity, title, checklist ids)
RULES: Dict[str, Tuple[str, str, str, str]] = {
    "ISO999-7.2.2.2-NUMBER": ("7.2.2.2", "warn",
        "One concept indexed in both singular and plural form",
        "ISO999-7.2.2.2-01"),
    "ISO999-7.3.1.1-VARIANT": ("7.3.1.1", "warn",
        "One person indexed under initials and under full forenames",
        "ISO999-7.3.1.1-02"),
    "ISO999-6.3-INVERSION": ("6.3; 7.2.2.4", "warn",
        "Inversion applied inconsistently (same words direct and inverted, "
        "or an inverted heading beside direct siblings)",
        "ISO999-6-07; ISO999-7.2.2.4-01"),
    "ISO999-6.3-CASE": ("6.3", "warn",
        "Headings differing only in capitalisation", "ISO999-6-07"),
    "ISO999-8.1-SORTAS": ("8.1", "warn",
        "Heading begins with a symbol, quote or markup and has no sort-as "
        "key (info: non-ASCII initial in makeindex input)",
        "ISO999-8.1-04"),
    "ISO999-8.3-SORTAS": ("8.3", "info",
        "Heading begins with a numeral and has no sort-as key",
        "ISO999-8.3-01; ISO999-8.3-02"),
    "ISO999-7.5.1-DANGLING": ("7.5.1; 3.13", "warn",
        "'see' target is not defined by any entry",
        "ISO999-7.5-02; ISO999-6-09"),
    "ISO999-7.5.2-DANGLING": ("7.5.2", "warn",
        "'see also' target is not defined by any entry",
        "ISO999-7.5-06; ISO999-6-09"),
    "ISO999-7.5.1-CHAIN": ("7.5.1; 3.13", "warn",
        "Cross-reference target is itself only a 'see' reference",
        "ISO999-7.5-03"),
    "ISO999-7.5.1-CYCLE": ("7.5.1", "warn",
        "'see' references form a loop", "ISO999-7.5-03"),
    "ISO999-3.13-LOCATORS": ("3.13; 7.5.1", "warn",
        "Heading with a 'see' reference also has locators or subentries",
        "ISO999-3-02; ISO999-7.5-03"),
    "ISO999-7.5-SELF": ("7.5", "warn",
        "Cross-reference points to its own heading", "ISO999-6-09"),
    "ISO999-7.4.3.1-UNCLOSED": ("7.4.3.1", "warn",
        "Range opened but never closed (or opened twice)", "ISO999-7.4-10"),
    "ISO999-7.4.3.1-STRAY": ("7.4.3.1", "warn",
        "Range closed without a matching open", "ISO999-7.4-10"),
    "MARKUP-PARSE": ("-", "info",
        "Index markup could not be parsed", "-"),
}

CONSISTENCY_RULES = ("ISO999-7.2.2.2-NUMBER", "ISO999-7.3.1.1-VARIANT",
                     "ISO999-6.3-INVERSION", "ISO999-6.3-CASE")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entry:
    file: str
    line: int
    fmt: str
    levels: List[Tuple[str, Optional[str]]]   # (display, sort-as or None)
    kind: str = "index"                       # index | see | seealso | range
    targets: List[str] = field(default_factory=list)
    range: Optional[str] = None               # "open" | "close" | None
    range_key: Optional[str] = None           # DITA start/end id
    encap: str = ""
    locator: Optional[str] = None             # page, for .idx input

    @property
    def path(self) -> Tuple[str, ...]:
        return tuple(clean(d, self.fmt) for d, _ in self.levels)

    @property
    def heading(self) -> str:
        return self.path[0] if self.levels else ""

    def where(self) -> str:
        return f"{self.file}:{self.line}"

    def as_dict(self) -> dict:
        d = {"file": self.file, "line": self.line, "format": self.fmt,
             "kind": self.kind, "path": list(self.path)}
        sorts = [s for _, s in self.levels]
        if any(s is not None for s in sorts):
            d["sort_as"] = sorts
        if self.targets:
            d["targets"] = self.targets
        if self.range:
            d["range"] = self.range
        if self.encap:
            d["encap"] = self.encap
        if self.locator is not None:
            d["locator"] = self.locator
        return d


@dataclass
class Finding:
    rule: str
    file: str
    line: int
    message: str
    related: List[Tuple[str, int]] = field(default_factory=list)
    severity: str = ""
    cluster: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.severity:
            self.severity = RULES[self.rule][1]

    @property
    def clause(self) -> str:
        return RULES[self.rule][0]

    def as_dict(self) -> dict:
        d = {"rule": self.rule, "clause": self.clause,
             "checklist": RULES[self.rule][3], "severity": self.severity,
             "file": self.file, "line": self.line, "message": self.message}
        if self.related:
            d["related"] = [{"file": f, "line": ln} for f, ln in self.related]
        return d


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
_SPECIAL_FOLD = {"ß": "ss", "æ": "ae", "Æ": "ae", "œ": "oe", "Œ": "oe",
                 "ø": "o", "Ø": "o", "ł": "l", "Ł": "l", "đ": "d", "Đ": "d",
                 "þ": "th", "Þ": "th", "ı": "i"}


def fold(text: str) -> str:
    """Case-fold and strip diacritics."""
    if _lint_fold is not None:
        try:
            return _lint_fold(text)
        except Exception:  # pragma: no cover
            pass
    text = "".join(_SPECIAL_FOLD.get(c, c) for c in text)
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text
                   if not unicodedata.combining(c)).casefold()


def ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def nk(text: str) -> str:
    """Identity key: folded, spacing collapsed, trailing punctuation off."""
    return ws(fold(text)).rstrip(".;:, ")


_TEX_ACCENTS = {'"': "\u0308", "'": "\u0301", "`": "\u0300", "^": "\u0302",
                "~": "\u0303", "=": "\u0304", ".": "\u0307", "c": "\u0327",
                "u": "\u0306", "v": "\u030c", "H": "\u030b", "k": "\u0328"}
_TEX_LETTERS = {"ss": "ß", "o": "ø", "O": "Ø", "ae": "æ", "AE": "Æ",
                "oe": "œ", "OE": "Œ", "aa": "å", "AA": "Å", "l": "ł",
                "L": "Ł", "i": "ı"}


def tex_to_text(s: str) -> str:
    """Rough LaTeX-to-text for comparing headings (not for display)."""
    s = re.sub(r"\\([\"'`^~=.])\s*\{?\s*(\\?[A-Za-z])\s*\}?",
               lambda m: m.group(2).lstrip("\\") + _TEX_ACCENTS[m.group(1)],
               s)
    s = re.sub(r"\\([cuvHk])\s*\{\s*([A-Za-z])\s*\}",
               lambda m: m.group(2) + _TEX_ACCENTS[m.group(1)], s)
    s = re.sub(r"\\(ss|ae|AE|oe|OE|aa|AA|o|O|l|L|i)(?![A-Za-z])\s*",
               lambda m: _TEX_LETTERS[m.group(1)], s)
    s = re.sub(r"\\([&%$#_{}])", r"\1", s)
    s = s.replace("~", " ").replace("--", "\u2013")
    s = re.sub(r"\\[A-Za-z@]+\*?\s*", "", s)
    s = re.sub(r"\\(.)", r"\1", s)
    s = s.replace("{", "").replace("}", "").replace("$", "")
    return ws(unicodedata.normalize("NFC", s))


def clean(display: str, fmt: str) -> str:
    if fmt in ("latex", "idx"):
        return tex_to_text(display)
    return ws(display)


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


_QUAL_RE = re.compile(r"^(.*?)\s*\(([^()]*)\)\s*$")


def split_qualifier(h: str) -> Tuple[str, str]:
    m = _QUAL_RE.match(h)
    if m and m.group(1):
        return m.group(1), m.group(2)
    return h, ""


def singulars(word: str) -> List[str]:
    out = []
    if word.endswith("ies") and len(word) > 4:
        out.append(word[:-3] + "y")
    if word.endswith("es") and len(word) > 3:
        out.append(word[:-2])
    if word.endswith("s") and not word.endswith("ss") and len(word) > 2:
        out.append(word[:-1])
    return out


# ---------------------------------------------------------------------------
# makeindex body syntax (shared by latex, idx and custom)
# ---------------------------------------------------------------------------
class MarkupError(ValueError):
    pass


@dataclass
class MiBody:
    levels: List[Tuple[str, Optional[str]]]
    encap: Optional[str]


def parse_mi_body(body: str, quote: Optional[str] = '"',
                  escape: Optional[str] = "\\", level: str = "!",
                  actual: str = "@", encap: str = "|") -> MiBody:
    """Split a makeindex entry body into levels and an encap string."""
    chars: List[Tuple[str, bool]] = []     # (char, literal?)
    i, n, depth = 0, len(body), 0
    while i < n:
        c = body[i]
        if escape and c == escape and i + 1 < n:
            chars.append((c, True))
            chars.append((body[i + 1], True))
            i += 2
            continue
        if quote and c == quote and i + 1 < n:
            chars.append((body[i + 1], True))
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth = max(0, depth - 1)
        chars.append((c, depth > 0 and c not in "{}"))
        i += 1
    enc: Optional[str] = None
    for j, (c, lit) in enumerate(chars):
        if c == encap and not lit:
            enc = "".join(ch for ch, _ in chars[j + 1:])
            chars = chars[:j]
            break
    levels: List[Tuple[str, Optional[str]]] = []
    cur: List[Tuple[str, bool]] = []
    for c, lit in chars + [(level, False)]:
        if c == level and not lit:
            sort: Optional[str] = None
            disp = cur
            for k, (ch, lt) in enumerate(cur):
                if ch == actual and not lt:
                    sort = "".join(x for x, _ in cur[:k])
                    disp = cur[k + 1:]
                    break
            levels.append(("".join(x for x, _ in disp).strip(),
                           sort.strip() if sort is not None else None))
            cur = []
        else:
            cur.append((c, lit))
    if not any(d or s for d, s in levels):
        raise MarkupError("empty index entry")
    return MiBody(levels, enc)


_SEE_ENCAP_RE = re.compile(
    r"^\s*\\?(see|seealso|seeonly|seealsoonly|alsoindex)\s*\{(.*)\}\s*$", re.S)


def mi_entry(body: str, file: str, line: int, fmt: str,
             locator: Optional[str] = None, quote: Optional[str] = '"'
             ) -> Entry:
    mb = parse_mi_body(body, quote=quote)
    e = Entry(file, line, fmt, mb.levels, locator=locator)
    enc = (mb.encap or "").strip()
    if enc.startswith("("):
        e.range, enc = "open", enc[1:]
    elif enc.startswith(")"):
        e.range, enc = "close", enc[1:]
    m = _SEE_ENCAP_RE.match(enc)
    if m and e.range is None:
        e.kind = "see" if m.group(1) in ("see", "seeonly") else "seealso"
        e.targets = [clean(m.group(2), fmt)]
    else:
        e.encap = enc.strip()
    return e


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------
def _strip_tex_comments(text: str) -> str:
    out = []
    for ln in text.split("\n"):
        m = re.search(r"(?<!\\)%", ln)
        out.append(ln[:m.start()] if m else ln)
    return "\n".join(out)


def _brace_arg(text: str, pos: int) -> Tuple[str, int]:
    """text[pos] == '{'; return (content, index after the closing brace)."""
    depth, i = 0, pos
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[pos + 1:i], i + 1
        i += 1
    raise MarkupError("unbalanced braces")


_TEX_INDEX_RE = re.compile(r"\\index(?![A-Za-z@])\s*(\[[^\]]*\])?\s*(?=\{)")


def read_latex(text: str, file: str, findings: List[Finding]
               ) -> List[Entry]:
    text = _strip_tex_comments(text)
    out = []
    for m in _TEX_INDEX_RE.finditer(text):
        ln = line_of(text, m.start())
        try:
            body, _ = _brace_arg(text, m.end())
            out.append(mi_entry(body, file, ln, "latex"))
        except MarkupError as exc:
            findings.append(Finding("MARKUP-PARSE", file, ln,
                                    f"\\index: {exc}"))
    return out


_IDX_RE = re.compile(r"\\indexentry\s*(?=\{)")


def read_idx(text: str, file: str, findings: List[Finding]) -> List[Entry]:
    out = []
    for m in _IDX_RE.finditer(text):
        ln = line_of(text, m.start())
        try:
            body, end = _brace_arg(text, m.end())
            page = None
            rest = text[end:]
            mp = re.match(r"\s*\{", rest)
            if mp:
                page, _ = _brace_arg(text, end + mp.end() - 1)
            out.append(mi_entry(body, file, ln, "idx", locator=page))
        except MarkupError as exc:
            findings.append(Finding("MARKUP-PARSE", file, ln,
                                    f"\\indexentry: {exc}"))
    return out


# --- reStructuredText / Sphinx ---------------------------------------------
_RST_DIRECTIVE_RE = re.compile(r"^(\s*)\.\.\s+index::(.*)$")
_RST_TYPED_RE = re.compile(
    r"^!?\s*(single|pair|triple|see|seealso|module|keyword|operator|object|"
    r"exception|statement|builtin)\s*:\s*(.*)$", re.S)
_RST_ROLE_RE = re.compile(r":index:`([^`]+)`")


def _rst_parts(value: str) -> List[str]:
    return [ws(p).lstrip("!").strip() for p in value.split(";")]


def rst_entries(spec: str, file: str, line: int,
                findings: List[Finding]) -> List[Entry]:
    spec = ws(spec)
    if not spec:
        return []
    main = spec.startswith("!")
    m = _RST_TYPED_RE.match(spec.lstrip("!").strip() if main else spec)

    def mk(levels: Sequence[str], kind: str = "index",
           targets: Sequence[str] = ()) -> Entry:
        return Entry(file, line, "rst", [(x, None) for x in levels], kind,
                     list(targets))

    if not m:
        return [mk([ws(x).lstrip("!").strip()]) for x in spec.split(",")
                if x.strip().lstrip("!").strip()]
    typ, parts = m.group(1), [p for p in _rst_parts(m.group(2)) if p]
    if typ == "single":
        return [mk(parts)] if parts else []
    if typ in ("see", "seealso"):
        if len(parts) < 2:
            findings.append(Finding("MARKUP-PARSE", file, line,
                f"'{typ}:' needs 'term; target'"))
            return []
        return [mk([parts[0]], typ, [parts[1]])]
    if typ == "pair":
        if len(parts) != 2:
            findings.append(Finding("MARKUP-PARSE", file, line,
                "'pair:' needs exactly two parts"))
            return [mk(parts)] if parts else []
        return [mk([parts[0], parts[1]]), mk([parts[1], parts[0]])]
    if typ == "triple":
        if len(parts) != 3:
            findings.append(Finding("MARKUP-PARSE", file, line,
                "'triple:' needs exactly three parts"))
            return [mk(parts)] if parts else []
        a, b, c = parts
        return [mk([a, f"{b} {c}"]), mk([b, f"{c}, {a}"]),
                mk([c, f"{a} {b}"])]
    value = ws(m.group(2))            # module:, keyword: ... -> pair
    return [mk([typ, value]), mk([value, typ])] if value else []


def read_rst(text: str, file: str, findings: List[Finding]) -> List[Entry]:
    lines = text.split("\n")
    out: List[Entry] = []
    i = 0
    while i < len(lines):
        m = _RST_DIRECTIVE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        base = len(m.group(1).expandtabs())
        if m.group(2).strip():
            out.extend(rst_entries(m.group(2), file, i + 1, findings))
        j = i + 1
        while j < len(lines):
            ln = lines[j]
            if ln.strip() and len(ln.expandtabs()) - \
                    len(ln.expandtabs().lstrip()) <= base:
                break
            s = ln.strip()
            if s and not re.match(r"^:[\w-]+:", s):
                out.extend(rst_entries(s, file, j + 1, findings))
            j += 1
        i = j
    for m in _RST_ROLE_RE.finditer(text):
        ln = line_of(text, m.start())
        content = m.group(1)
        mt = re.match(r"^(.*?)\s*<(.+)>\s*$", content, re.S)
        if mt:
            out.extend(rst_entries(mt.group(2), file, ln, findings))
        else:
            out.append(Entry(file, ln, "rst", [(ws(content), None)]))
    out.sort(key=lambda e: e.line)
    return out


# --- DITA -------------------------------------------------------------------
_DITA_SPECIAL = ("indexterm", "index-see", "index-see-also", "index-sort-as")
_XML_ENTITY_RE = re.compile(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)"
                            r"[\w.-]+;")


class _Node:
    def __init__(self, tag: str, attrs: dict, line: int) -> None:
        self.tag, self.attrs, self.line = tag, attrs, line
        self.parts: List[object] = []

    def children(self, tag: str) -> List["_Node"]:
        return [p for p in self.parts
                if isinstance(p, _Node) and p.tag == tag]

    def all_text(self) -> str:
        return "".join(p if isinstance(p, str) else p.all_text()
                       for p in self.parts)

    def own_text(self) -> str:
        return ws("".join(
            p if isinstance(p, str) else
            ("" if p.tag in _DITA_SPECIAL else p.all_text())
            for p in self.parts))


def _mask_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->",
                  lambda m: re.sub(r"[^\n]", " ", m.group(0)), text,
                  flags=re.S)


def _parse_xml_fragment(block: str, base_line: int) -> _Node:
    root = _Node("#root", {}, base_line)
    stack = [root]
    p = xml.parsers.expat.ParserCreate()

    def start(tag, attrs):
        n = _Node(tag, attrs, base_line + p.CurrentLineNumber - 1)
        stack[-1].parts.append(n)
        stack.append(n)

    def end(tag):
        stack.pop()

    def chars(data):
        stack[-1].parts.append(data)

    p.StartElementHandler = start
    p.EndElementHandler = end
    p.CharacterDataHandler = chars
    p.Parse("<r>" + _XML_ENTITY_RE.sub(" ", block) + "</r>", True)
    return root


def _dita_walk(node: _Node, prefix: List[Tuple[str, Optional[str]]],
               file: str, out: List[Entry]) -> None:
    end_id = node.attrs.get("end")
    label = node.own_text()
    if end_id and not label and not node.children("indexterm"):
        out.append(Entry(file, node.line, "dita", list(prefix) or [("", None)],
                         kind="range", range="close", range_key=end_id))
        return
    sort_nodes = node.children("index-sort-as")
    sort = ws(sort_nodes[0].all_text()) if sort_nodes else None
    levels = prefix + [(label, sort)]
    subs = node.children("indexterm")
    start_id = node.attrs.get("start")
    if subs:
        if start_id:
            out.append(Entry(file, node.line, "dita", levels, range="open",
                             range_key=start_id))
        for s in subs:
            _dita_walk(s, levels, file, out)
        return

    def target_text(n: _Node) -> str:
        parts = [n.own_text()]
        cur = n.children("indexterm")
        while cur:
            parts.append(cur[0].own_text())
            cur = cur[0].children("indexterm")
        return ", ".join(p for p in parts if p)

    sees, alsos = node.children("index-see"), node.children("index-see-also")
    if sees:
        out.append(Entry(file, node.line, "dita", levels, "see",
                         [target_text(s) for s in sees]))
    if alsos:
        out.append(Entry(file, node.line, "dita", levels, "seealso",
                         [target_text(s) for s in alsos]))
    if not sees and (not alsos or start_id):
        out.append(Entry(file, node.line, "dita", levels,
                         range="open" if start_id else None,
                         range_key=start_id))


_DITA_TAG_RE = re.compile(r"<(/?)indexterm\b[^>]*?(/?)>")


def read_dita(text: str, file: str, findings: List[Finding]) -> List[Entry]:
    text = _mask_comments(text)
    out: List[Entry] = []
    depth, start = 0, None
    for m in _DITA_TAG_RE.finditer(text):
        closing, selfclose = m.group(1) == "/", m.group(2) == "/"
        if not closing:
            if depth == 0:
                start = m.start()
            if selfclose:
                if depth == 0:
                    _dita_block(text, start, m.end(), file, out, findings)
            else:
                depth += 1
        else:
            depth -= 1
            if depth == 0 and start is not None:
                _dita_block(text, start, m.end(), file, out, findings)
                start = None
            depth = max(depth, 0)
    if depth > 0 and start is not None:
        findings.append(Finding("MARKUP-PARSE", file, line_of(text, start),
                                "<indexterm> is never closed"))
    return out


def _dita_block(text: str, a: int, b: int, file: str, out: List[Entry],
                findings: List[Finding]) -> None:
    ln = line_of(text, a)
    try:
        root = _parse_xml_fragment(text[a:b], ln)
    except xml.parsers.expat.ExpatError as exc:
        findings.append(Finding("MARKUP-PARSE", file, ln,
                                f"<indexterm> is not well-formed: {exc}"))
        return
    for it in root.children("r")[0].children("indexterm"):
        _dita_walk(it, [], file, out)


# --- custom -----------------------------------------------------------------
@dataclass
class CustomSyntax:
    regex: "re.Pattern"
    xref_sep: str = "|"
    target_sep: str = ","


def read_custom(text: str, file: str, findings: List[Finding],
                syn: CustomSyntax) -> List[Entry]:
    out = []
    for m in syn.regex.finditer(text):
        ln = line_of(text, m.start())
        body = m.group("body") or ""
        kind = ""
        if "kind" in syn.regex.groupindex and m.group("kind"):
            kind = re.sub(r"[\s_-]+", "", m.group("kind").lower())
        if kind in ("see", "seealso"):
            src, sep, dest = body.partition(syn.xref_sep)
            targets = [ws(t) for t in dest.split(syn.target_sep)
                       if t.strip()] if syn.target_sep else [ws(dest)]
            if not sep or not targets or not src.strip():
                findings.append(Finding("MARKUP-PARSE", file, ln,
                    f"{kind} markup needs 'source{syn.xref_sep}target': "
                    f"{body!r}"))
                continue
            levels = [(ws(x), None) for x in src.split("!") if x.strip()]
            out.append(Entry(file, ln, "custom", levels, kind, targets))
            continue
        try:
            out.append(mi_entry(body, file, ln, "custom", quote=None))
        except MarkupError as exc:
            findings.append(Finding("MARKUP-PARSE", file, ln, str(exc)))
    return out


# ---------------------------------------------------------------------------
# Format detection and file walking
# ---------------------------------------------------------------------------
EXT_FORMAT = {".tex": "latex", ".ltx": "latex", ".dtx": "latex",
              ".sty": "latex", ".cls": "latex", ".idx": "idx",
              ".rst": "rst", ".rest": "rst", ".dita": "dita",
              ".ditamap": "dita"}
SNIFF_EXT = {".txt", ".xml", ".md", ".markdown", ".inc"}
SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "_build", "__pycache__",
             ".tox", ".venv", "venv"}


def sniff(text: str) -> Optional[str]:
    if "\\indexentry{" in text:
        return "idx"
    if re.search(r"\\index\s*(\[[^\]]*\])?\s*\{", text):
        return "latex"
    if re.search(r"(?m)^\s*\.\.\s+index::", text) or \
            _RST_ROLE_RE.search(text):
        return "rst"
    if "<indexterm" in text:
        return "dita"
    return None


# iCloud / dataless files: reading a file that iCloud Drive (or another File
# Provider) has evicted blocks until it is downloaded, which can stall a walk
# over ~/Documents for a very long time at 0% CPU.  Such files carry
# SF_DATALESS in st_flags (<sys/stat.h>: 0x40000000); a regular file with
# st_size > 0 and st_blocks == 0 is treated as a likely placeholder too
# (unless UF_COMPRESSED).  ``.icloud`` stub files are never read.
SF_DATALESS = getattr(stat, "SF_DATALESS", 0x40000000)
_UF_COMPRESSED = getattr(stat, "UF_COMPRESSED", 0x20)
NOT_LOCAL = "not-local (iCloud/dataless)"
READ_TIMEOUT = "read-timeout"
DEFAULT_FILE_TIMEOUT = 10.0
SKIP_REASONS = (NOT_LOCAL, READ_TIMEOUT)


def is_icloud_stub(path: str) -> bool:
    return os.path.basename(path).endswith(".icloud")


def is_dataless(path: str, dir_ok: bool = False) -> bool:
    """True when ``path`` is (likely) not stored locally.  Uses only stat,
    which never triggers a download.  For directories (``dir_ok``) only the
    SF_DATALESS flag counts."""
    try:
        st = os.stat(path)
    except OSError:
        return False
    flags = getattr(st, "st_flags", 0) or 0
    if flags & SF_DATALESS:
        return True
    if dir_ok or not stat.S_ISREG(st.st_mode) or flags & _UF_COMPRESSED:
        return False
    return getattr(st, "st_blocks", None) == 0 and st.st_size > 0


class ReadTimeout(OSError):
    """A file read did not finish within the per-file budget."""


def read_bytes(path: str, timeout: Optional[float] = DEFAULT_FILE_TIMEOUT
               ) -> bytes:
    """Read ``path``; with ``timeout`` (seconds, > 0) the read runs in a
    daemon worker thread and ReadTimeout is raised when it overruns.  The
    blocked thread cannot be cancelled; it lingers (as a daemon, so it never
    keeps the process alive) until the OS read returns."""
    if not timeout:
        with open(path, "rb") as fh:
            return fh.read()
    box: dict = {}

    def work() -> None:
        try:
            with open(path, "rb") as fh:
                box["data"] = fh.read()
        except BaseException as exc:  # noqa: BLE001 - re-raised below
            box["err"] = exc

    t = threading.Thread(target=work, name="iso999-read", daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise ReadTimeout(f"read did not finish in {timeout:g}s")
    if "err" in box:
        raise box["err"]
    return box["data"]


def iter_files(paths: Sequence[str], include_evicted: bool = False,
               skipped: Optional[List[dict]] = None
               ) -> Iterable[Tuple[str, bool]]:
    """Yield (path, explicit?) in a stable order.  ``.icloud`` stubs and
    (unless ``include_evicted``) dataless directories are not yielded or
    entered; they are appended to ``skipped`` as {"file", "reason", "dir"}."""
    def note(path: str, is_dir: bool) -> None:
        if skipped is not None:
            skipped.append({"file": path, "reason": NOT_LOCAL, "dir": is_dir})

    for p in paths:
        if os.path.isdir(p):
            if not include_evicted and is_dataless(p, dir_ok=True):
                note(p, True)
                continue
            for root, dirs, files in os.walk(p):
                keep = []
                for d in sorted(dirs):
                    if d in SKIP_DIRS or d.startswith("."):
                        continue
                    if not include_evicted and \
                            is_dataless(os.path.join(root, d), dir_ok=True):
                        note(os.path.join(root, d), True)
                        continue
                    keep.append(d)
                dirs[:] = keep
                for f in sorted(files):
                    if f.endswith(".icloud"):
                        note(os.path.join(root, f), False)
                    elif not f.startswith("."):
                        yield os.path.join(root, f), False
        else:
            yield p, True


def choose_format(path: str, text: str, requested: str, explicit: bool
                  ) -> Optional[str]:
    if requested not in ("auto",):
        return requested
    ext = os.path.splitext(path)[1].lower()
    if ext in EXT_FORMAT:
        return EXT_FORMAT[ext]
    if ext in SNIFF_EXT or explicit:
        return sniff(text)
    return None


def read_file(path: str, text: str, fmt: str, findings: List[Finding],
              custom: Optional[CustomSyntax] = None) -> List[Entry]:
    if fmt == "latex":
        return read_latex(text, path, findings)
    if fmt == "idx":
        return read_idx(text, path, findings)
    if fmt == "rst":
        return read_rst(text, path, findings)
    if fmt == "dita":
        return read_dita(text, path, findings)
    if fmt == "custom":
        assert custom is not None
        return read_custom(text, path, findings, custom)
    raise ValueError(fmt)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
def _occ(entries: Sequence[Entry], limit: int = 4) -> str:
    seen = list(OrderedDict.fromkeys(e.where() for e in entries))
    s = ", ".join(seen[:limit])
    if len(seen) > limit:
        s += f" (+{len(seen) - limit} more)"
    return s


def _q(s: str) -> str:
    return f'"{s}"'


class DocSet:
    def __init__(self, entries: List[Entry]) -> None:
        self.entries = entries
        self.headed = [e for e in entries if e.kind != "range" and
                       e.levels and e.heading]
        # live: paths (folded) that have locators or subentries under them
        self.live = set()
        self.exists = set()
        self.see_src: Dict[Tuple[str, ...], List[Entry]] = defaultdict(list)
        self.also_src: Dict[Tuple[str, ...], List[Entry]] = defaultdict(list)
        for e in self.headed:
            key = tuple(nk(p) for p in e.path)
            for k in range(1, len(key) + 1):
                self.exists.add(key[:k])
            if e.kind == "index":
                for k in range(1, len(key) + 1):
                    self.live.add(key[:k])
            elif e.kind == "see":
                self.see_src[key].append(e)
            elif e.kind == "seealso":
                self.also_src[key].append(e)
                # a see-also source with subentries is live; else it exists
        self.see_only = {k for k in self.see_src if k not in self.live}
        self.links = set()
        for src, es in list(self.see_src.items()) + \
                list(self.also_src.items()):
            for e in es:
                for t in e.targets:
                    for r in self.resolve(t) or ():
                        self.links.add((src[0], r[0]))
                        self.links.add((r[0], src[0]))

    def resolve_one(self, t: str) -> Optional[Tuple[str, ...]]:
        t = nk(t)
        if not t:
            return None
        if (t,) in self.exists:
            return (t,)
        for sep in ("!", ":", ", ", ";"):
            if sep in t:
                parts = tuple(nk(x) for x in t.split(sep) if x.strip())
                if parts in self.exists:
                    return parts
        return None

    def resolve(self, target: str) -> Optional[List[Tuple[str, ...]]]:
        """Resolve a target (possibly several joined) to existing paths."""
        whole = self.resolve_one(target)
        if whole:
            return [whole]
        for sep in (";", ","):
            if sep in target:
                parts = [x for x in target.split(sep) if x.strip()]
                res = [self.resolve_one(x) for x in parts]
                if all(res):
                    return res  # type: ignore
        return None

    def linked(self, a: str, b: str) -> bool:
        return (nk(a), nk(b)) in self.links


def _sibling_groups(ds: DocSet) -> Iterable[Tuple[Tuple[str, ...],
                                                   Dict[str, List[Entry]]]]:
    """Yield (parent path, {surface form: [entries]}) for every level."""
    groups: Dict[Tuple[str, ...], Dict[str, List[Entry]]] = \
        defaultdict(lambda: defaultdict(list))
    for e in ds.headed:
        p = e.path
        for depth in range(len(p)):
            if not p[depth]:
                continue
            parent = tuple(nk(x) for x in p[:depth])
            groups[parent][p[depth]].append(e)
    for parent, g in groups.items():
        yield parent, g


def _name_parts(h: str) -> Optional[Tuple[str, List[str], str]]:
    main, qual = split_qualifier(h)
    m = re.match(r"^\s*((?:[^\W\d_][\w'\u2019-]*\s+){0,2}[^\W\d_]"
                 r"[\w'\u2019-]*)\s*,\s*(.+)$", main)
    if not m or not m.group(1).split()[-1][:1].isupper():
        return None
    toks = re.findall(r"[^\W\d_]+", m.group(2))
    particles = {"de", "la", "le", "du", "des", "van", "von", "der", "den",
                 "di", "da", "del", "ap", "ab", "y", "bin", "ibn", "af"}
    toks = [t for t in toks if not (t.lower() in particles and t.islower())]
    if not toks or not all(t[:1].isupper() for t in toks):
        return None
    return fold(m.group(1)), [fold(t) for t in toks], nk(qual)


def _names_compatible(ta: List[str], tb: List[str]) -> bool:
    if ta == tb:
        return False
    short, long_ = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    initials = False
    for x, y in zip(short, long_):
        if x == y:
            continue
        a, b = (x, y) if len(x) < len(y) else (y, x)
        if len(a) == 1 and b.startswith(a) and len(b) > 1:
            initials = True
        else:
            return False
    if len(short) != len(long_):
        return any(len(t) == 1 for t in short)
    return initials


def _words(s: str) -> List[str]:
    return re.findall(r"[^\W_]+(?:['\u2019][^\W_]+)*", fold(s))


def check_consistency(ds: DocSet) -> List[Finding]:
    out: List[Finding] = []
    for parent, group in _sibling_groups(ds):
        top = not parent
        where = "" if top else f" under {_q(' > '.join(parent))}"

        def linked(a: str, b: str) -> bool:
            return top and ds.linked(a, b)

        # case-only variants
        by_cf: Dict[str, List[str]] = defaultdict(list)
        for s in group:
            by_cf[ws(s).casefold()].append(s)
        for forms in by_cf.values():
            if len(forms) > 1:
                forms.sort(key=lambda f: (-len(group[f]), f))
                keep, rest = forms[0], forms[1:]
                for r in rest:
                    out.append(Finding("ISO999-6.3-CASE", group[r][0].file,
                        group[r][0].line,
                        f"{_q(r)}{where} differs from {_q(keep)} only in "
                        f"capitalisation ({_occ(group[keep])}); they will "
                        f"file or print as two headings. Use one form.",
                        [(e.file, e.line) for e in group[keep]],
                        cluster=(r, keep)))
        # one representative surface per case-folded form
        rep: Dict[str, str] = {}
        ents: Dict[str, List[Entry]] = defaultdict(list)
        for cf, forms in by_cf.items():
            forms.sort(key=lambda f: (-len(group[f]), f))
            rep[cf] = forms[0]
            for f in forms:
                ents[cf].extend(group[f])
        by_nk = {nk(rep[cf]): cf for cf in rep}

        # singular / plural
        done = set()
        for cf in rep:
            main, qual = split_qualifier(nk(rep[cf]))
            if qual:
                continue
            toks = main.split(" ")
            for i, tok in enumerate(toks):
                core = tok.rstrip(",.;:")
                tail = tok[len(core):]
                hit = None
                for sg in singulars(core):
                    cand = " ".join(toks[:i] + [sg + tail] + toks[i + 1:])
                    if cand in by_nk and by_nk[cand] != cf:
                        hit = by_nk[cand]
                        break
                if hit is None:
                    continue
                pair = frozenset((cf, hit))
                if pair in done or linked(rep[cf], rep[hit]):
                    break
                done.add(pair)
                pl, sg_ = cf, hit
                minor = pl if len(ents[pl]) <= len(ents[sg_]) else sg_
                major = sg_ if minor == pl else pl
                out.append(Finding("ISO999-7.2.2.2-NUMBER",
                    ents[minor][0].file, ents[minor][0].line,
                    f"{_q(rep[minor])}{where} ({_occ(ents[minor])}) and "
                    f"{_q(rep[major])} ({_occ(ents[major])}) differ only "
                    f"in singular/plural form. Use one form, or add "
                    f"qualifiers if they are different concepts.",
                    [(e.file, e.line) for e in ents[major]],
                    cluster=(rep[minor], rep[major])))
                break

        # personal-name variants
        names: Dict[str, List[Tuple[str, List[str], str]]] = defaultdict(list)
        for cf in rep:
            np_ = _name_parts(rep[cf])
            if np_:
                names[np_[0]].append((cf, np_[1], np_[2]))
        for grp in names.values():
            for i, (a, ta, qa) in enumerate(grp):
                for b, tb, qb in grp[i + 1:]:
                    if qa and qb and qa != qb:
                        continue
                    if not _names_compatible(ta, tb) or \
                            linked(rep[a], rep[b]):
                        continue
                    rank = {a: (len(ents[a]), sum(map(len, ta))),
                            b: (len(ents[b]), sum(map(len, tb)))}
                    minor, major = (a, b) if rank[a] <= rank[b] else (b, a)
                    out.append(Finding("ISO999-7.3.1.1-VARIANT",
                        ents[minor][0].file, ents[minor][0].line,
                        f"{_q(rep[minor])}{where} ({_occ(ents[minor])}) and "
                        f"{_q(rep[major])} ({_occ(ents[major])}) look like "
                        f"one person under two name forms. Use one form "
                        f"(normally the fuller) and refer from the other.",
                        [(e.file, e.line) for e in ents[major]],
                        cluster=(rep[minor], rep[major])))

        # inversion: identical words in a different order
        by_words: Dict[Tuple[str, ...], List[str]] = defaultdict(list)
        for cf in rep:
            w = _words(split_qualifier(rep[cf])[0])
            if len(w) > 1:
                by_words[tuple(sorted(w))].append(cf)
        for cfs in by_words.values():
            if len(cfs) < 2:
                continue
            cfs.sort(key=lambda c: (-len(ents[c]), c))
            major = cfs[0]
            for minor in cfs[1:]:
                if linked(rep[major], rep[minor]):
                    continue
                out.append(Finding("ISO999-6.3-INVERSION",
                    ents[minor][0].file, ents[minor][0].line,
                    f"{_q(rep[minor])}{where} ({_occ(ents[minor])}) and "
                    f"{_q(rep[major])} ({_occ(ents[major])}) are the same "
                    f"words in a different order. Choose one form and refer "
                    f"from the other if needed.",
                    [(e.file, e.line) for e in ents[major]],
                    cluster=(rep[minor], rep[major])))

        # inversion: "noun, modifier" beside direct "modifier noun" siblings
        heads: Dict[str, List[str]] = defaultdict(list)   # noun -> direct
        for cf in rep:
            h = rep[cf]
            main, qual = split_qualifier(h)
            if "," in main or qual:
                continue
            words = main.split()
            if len(words) < 2 or sum(1 for w in words if w[:1].isupper()) > 1:
                continue
            noun = nk(words[-1])
            for key in [noun] + singulars(noun):
                heads[key].append(cf)
        for cf in rep:
            main, qual = split_qualifier(rep[cf])
            m = re.match(r"^([^,]+),\s*([^,]+)$", main)
            if not m:
                continue
            noun, mod = m.group(1).strip(), m.group(2).strip()
            if not mod or not all(w[:1].islower() for w in mod.split()) or \
                    len(noun.split()) > 2 or _name_parts(rep[cf]):
                continue
            keys = [nk(noun)] + singulars(nk(noun))
            sibs = list(OrderedDict.fromkeys(
                d for k in keys for d in heads.get(k, ())
                if d != cf and not linked(rep[cf], rep[d])))
            if not sibs:
                continue
            direct = "; ".join(f"{_q(rep[d])} ({_occ(ents[d], 2)})"
                               for d in sibs[:3])
            out.append(Finding("ISO999-6.3-INVERSION", ents[cf][0].file,
                ents[cf][0].line,
                f"{_q(rep[cf])}{where} ({_occ(ents[cf])}) is inverted, but "
                f"the parallel heading(s) {direct} are in direct order. "
                f"Treat parallel terms alike: all direct, or all as "
                f"subentries of one heading.",
                [(e.file, e.line) for d in sibs for e in ents[d]],
                cluster=tuple([rep[cf]] + [rep[d] for d in sibs])))
    return out


def check_sortas(ds: DocSet) -> List[Finding]:
    out: List[Finding] = []
    seen: Dict[Tuple[str, str], List[Entry]] = OrderedDict()
    for e in ds.headed:
        for depth, (disp, sort) in enumerate(e.levels):
            raw = disp.strip()
            if not raw or sort:
                continue
            c = raw[0]
            if c.isdigit():
                rid = "ISO999-8.3-SORTAS"
            elif not c.isalpha():
                rid = "ISO999-8.1-SORTAS"
            elif e.fmt in ("latex", "idx") and ord(c) > 127:
                rid = "ISO999-8.1-SORTAS/nonascii"
            else:
                continue
            seen.setdefault((rid, raw), []).append(e)
    for (rid, raw), es in seen.items():
        e = es[0]
        more = f" (also {_occ(es[1:], 3)})" if len(es) > 1 else ""
        fmt = e.fmt
        how = {"latex": "add a sort key, e.g. \\index{key@...}",
               "idx": "add a sort key (key@display) in the source",
               "custom": "add a sort key (key@display)",
               "dita": "add <index-sort-as>",
               "rst": "Sphinx has no sort-as field; reword the heading or "
                      "accept the symbols group"}[fmt]
        if rid == "ISO999-8.3-SORTAS":
            msg = (f"{_q(raw)} begins with a numeral and has no sort-as key"
                   f"{more}. Numerals file before letters in numeric order "
                   f"or as if spelled out; decide which, and {how} if the "
                   f"tool would otherwise sort it as text.")
            out.append(Finding(rid, e.file, e.line, msg))
        elif rid.endswith("/nonascii"):
            out.append(Finding("ISO999-8.1-SORTAS", e.file, e.line,
                f"{_q(raw)} begins with a non-ASCII letter and has no "
                f"sort-as key{more}. makeindex sorts by byte value, so it "
                f"will file after z; {how} (xindy/upmendex with a locale "
                f"do not need this).", severity="info"))
        else:
            what = "markup" if raw[0] in "\\{$<" else "a symbol or quote"
            out.append(Finding(rid, e.file, e.line,
                f"{_q(raw)} begins with {what} and has no sort-as key"
                f"{more}; it will file by that character, not by its first "
                f"word. Symbols and punctuation should be ignored in "
                f"filing: {how}."))
    return out


def check_xrefs(ds: DocSet) -> List[Finding]:
    out: List[Finding] = []
    reported = set()

    def emit(rule: str, es: List[Entry], msg: str, key) -> None:
        if (rule, key) in reported:
            return
        reported.add((rule, key))
        e = es[0]
        more = f" Also at {_occ(es[1:], 3)}." if len(es) > 1 else ""
        out.append(Finding(rule, e.file, e.line, msg + more,
                           [(x.file, x.line) for x in es[1:]]))

    # group entries by (kind, source, target)
    xgroups: Dict[Tuple[str, Tuple[str, ...], str], List[Entry]] = \
        OrderedDict()
    for kind, src_map in (("see", ds.see_src), ("seealso", ds.also_src)):
        for src, es in src_map.items():
            for e in es:
                for t in e.targets:
                    if t.strip():
                        xgroups.setdefault((kind, src, t), []).append(e)

    # cycles among see-only headings
    graph: Dict[Tuple[str, ...], List[Tuple[str, ...]]] = defaultdict(list)
    for (kind, src, t), es in xgroups.items():
        if kind != "see" or src not in ds.see_only:
            continue
        for r in ds.resolve(t) or ():
            if r in ds.see_only and r != src:
                graph[src].append(r)
    in_cycle = set()
    cycles = []
    for startn in sorted(graph):
        stack = [(startn, [startn])]
        while stack:
            node, path = stack.pop()
            for nxt in graph.get(node, ()):
                if nxt == startn:
                    cyc = path
                    rot = min(range(len(cyc)), key=lambda i: cyc[i])
                    canon = tuple(cyc[rot:] + cyc[:rot])
                    if canon not in cycles:
                        cycles.append(canon)
                elif nxt not in path and len(path) < 20:
                    stack.append((nxt, path + [nxt]))
    for cyc in cycles:
        in_cycle.update(cyc)
        es = ds.see_src[cyc[0]]
        names = " -> ".join(ds.see_src[c][0].path[-1] for c in cyc)
        names += " -> " + ds.see_src[cyc[0]][0].path[-1]
        emit("ISO999-7.5.1-CYCLE", es,
             f"'see' references loop: {names}. The reader never reaches a "
             f"heading with locators.", cyc)

    for (kind, src, t), es in xgroups.items():
        e = es[0]
        label = " > ".join(e.path)
        rel = "see" if kind == "see" else "see also"
        res = ds.resolve(t)
        if res == [src]:
            emit("ISO999-7.5-SELF", es,
                 f"{_q(label)} has '{rel} {t}', which points to itself.",
                 (kind, src, t))
            continue
        if res is None:
            rule = "ISO999-7.5.1-DANGLING" if kind == "see" else \
                "ISO999-7.5.2-DANGLING"
            emit(rule, es,
                 f"{_q(label)} {rel} {_q(t)}: no entry in the doc set "
                 f"defines that heading, so the reference is blind.",
                 (kind, src, t))
            continue
        for r in res:
            if r in ds.see_only and not (kind == "see" and src in in_cycle
                                         and r in in_cycle):
                nxt = [x for es2 in [ds.see_src[r]] for x in es2]
                onward = "; ".join(OrderedDict.fromkeys(
                    tt for x in nxt for tt in x.targets))
                emit("ISO999-7.5.1-CHAIN", es,
                     f"{_q(label)} {rel} {_q(t)}, but {_q(t)} is itself only "
                     f"a 'see' reference (to {_q(onward)}, "
                     f"{nxt[0].where()}). Point directly at the preferred "
                     f"heading.", (kind, src, t))
    # see headings that also carry locators or subentries (3.13)
    for src, es in ds.see_src.items():
        if src not in ds.live:
            continue
        loc = [e for e in ds.headed if e.kind == "index" and
               tuple(nk(p) for p in e.path)[:len(src)] == src]
        subs = any(len(e.path) > len(src) for e in loc)
        what = "subentries" if subs and not any(
            len(e.path) == len(src) for e in loc) else "locators"
        emit("ISO999-3.13-LOCATORS", es,
             f"{_q(' > '.join(es[0].path))} has a 'see' reference but also "
             f"{what} ({_occ(loc, 3)}). A 'see' heading carries no "
             f"locators; use 'see also', or move the locators to the "
             f"target.", ("loc", src))
    return out


def check_ranges(ds: DocSet) -> List[Finding]:
    out: List[Finding] = []
    open_: Dict[Tuple, Entry] = OrderedDict()
    for e in ds.entries:
        if e.range is None:
            continue
        if e.range_key is not None:
            key: Tuple = ("id", e.range_key)
            label = f"range id {_q(e.range_key)}"
        else:
            p = tuple(nk(x) for x in e.path)
            key = (e.file if e.fmt == "idx" else "", p)
            label = _q(" > ".join(e.path))
        if e.range == "open":
            if key in open_:
                prev = open_[key]
                out.append(Finding("ISO999-7.4.3.1-UNCLOSED", prev.file,
                    prev.line, f"Range for {label} opened here and opened "
                    f"again at {e.where()} before it was closed.",
                    [(e.file, e.line)]))
            open_[key] = e
        else:
            if open_.pop(key, None) is None:
                out.append(Finding("ISO999-7.4.3.1-STRAY", e.file, e.line,
                    f"Range close for {label} has no matching open."))
    for key, e in open_.items():
        label = _q(" > ".join(e.path)) if e.range_key is None else \
            f"range id {_q(e.range_key)}"
        out.append(Finding("ISO999-7.4.3.1-UNCLOSED", e.file, e.line,
            f"Range for {label} is opened but never closed; the index will show a single "
            f"page or an open-ended range."))
    return out


def lint_entries(entries: List[Entry]) -> List[Finding]:
    ds = DocSet(entries)
    return (check_consistency(ds) + check_sortas(ds) + check_xrefs(ds) +
            check_ranges(ds))


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
def clusters(findings: List[Finding], entries: List[Entry], top: int = 10
             ) -> List[dict]:
    parent: Dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for f in findings:
        if f.rule in CONSISTENCY_RULES and f.cluster:
            for c in f.cluster[1:]:
                parent[find(c)] = find(f.cluster[0])
            find(f.cluster[0])
    counts: Counter = Counter()
    for e in entries:
        if e.kind == "range":
            continue
        for p in e.path:
            if p in parent:
                counts[p] += 1
    groups: Dict[str, List[str]] = defaultdict(list)
    for x in parent:
        groups[find(x)].append(x)
    res = []
    for members in groups.values():
        members.sort(key=lambda m: (-counts[m], m))
        res.append({"forms": members,
                    "occurrences": {m: counts[m] for m in members},
                    "total": sum(counts[m] for m in members)})
    res.sort(key=lambda c: (-len(c["forms"]), -c["total"], c["forms"][0]))
    return res[:top]


def summarise(files: List[Tuple[str, str, int]], entries: List[Entry],
              findings: List[Finding],
              skipped: Optional[List[dict]] = None) -> dict:
    heads = {nk(e.heading) for e in entries if e.kind != "range" and
             e.heading}
    paths = {tuple(nk(p) for p in e.path) for e in entries
             if e.kind != "range" and e.heading}
    kinds = Counter(e.kind for e in entries)
    return {
        "files": [{"file": f, "format": fmt, "entries": n}
                  for f, fmt, n in files],
        "entries": len(entries),
        "kinds": dict(kinds),
        "distinct_headings": len(heads),
        "distinct_paths": len(paths),
        "warn": sum(1 for f in findings if f.severity == "warn"),
        "info": sum(1 for f in findings if f.severity == "info"),
        "by_rule": dict(Counter(f.rule for f in findings)),
        "variant_clusters": clusters(findings, entries),
        "skipped": {r: sum(1 for x in skipped or () if x["reason"] == r)
                    for r in SKIP_REASONS},
        "skipped_files": list(skipped or ()),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="iso999_markup.py",
        description="Extract index markup from doc sources and lint it "
                    "against ISO 999 guidance (heuristic).")
    ap.add_argument("paths", nargs="*", metavar="PATH",
                    help="files or directories (walked recursively)")
    ap.add_argument("--format", default="auto",
                    choices=["auto", "latex", "idx", "rst", "dita", "custom"])
    ap.add_argument("--entry-regex",
                    help="custom format: regex with named group 'body' and "
                         "optional 'kind' (see/seealso/index)")
    ap.add_argument("--xref-sep", default="|",
                    help="custom format: separator between see source and "
                         "targets (default '|')")
    ap.add_argument("--target-sep", default=",",
                    help="custom format: separator between several targets "
                         "(default ','; '' for none)")
    ap.add_argument("--ext", default="",
                    help="custom format: comma-separated file extensions to "
                         "read when walking directories (default: all)")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--entries", action="store_true",
                    help="include the extracted entries in the output")
    ap.add_argument("--min-severity", choices=["info", "warn"],
                    default="info")
    ap.add_argument("--list-rules", action="store_true")
    ap.add_argument("--include-evicted", action="store_true",
                    help="read files that are not stored locally (iCloud-"
                         "evicted / dataless); this triggers downloads and "
                         "can block for a long time")
    ap.add_argument("--file-timeout", type=_file_timeout,
                    default=DEFAULT_FILE_TIMEOUT, metavar="SECONDS",
                    help="per-file read budget; a slower read is skipped as "
                         f"read-timeout (default {DEFAULT_FILE_TIMEOUT:g}; "
                         "0 = no limit)")
    return ap


def _file_timeout(v: str) -> float:
    try:
        n = float(v)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "--file-timeout must be a number of seconds")
    if n < 0 or n != n:
        raise argparse.ArgumentTypeError(
            "--file-timeout must be >= 0 (0 = no limit)")
    return n


def run(paths: Sequence[str], fmt: str = "auto",
        custom: Optional[CustomSyntax] = None, exts: Sequence[str] = (),
        include_evicted: bool = False,
        file_timeout: Optional[float] = DEFAULT_FILE_TIMEOUT,
        skipped: Optional[List[dict]] = None
        ) -> Tuple[List[Tuple[str, str, int]], List[Entry], List[Finding],
                   List[str]]:
    """Walk ``paths`` and lint the index markup found.  Files not stored
    locally (iCloud/dataless, ``.icloud`` stubs) are not opened unless
    ``include_evicted``; reads over ``file_timeout`` seconds are abandoned.
    Both are appended to ``skipped`` (reason ``not-local (iCloud/dataless)``
    or ``read-timeout``)."""
    files: List[Tuple[str, str, int]] = []
    entries: List[Entry] = []
    findings: List[Finding] = []
    errors: List[str] = []
    if skipped is None:
        skipped = []
    for path, explicit in iter_files(paths, include_evicted, skipped):
        if fmt == "custom" and exts and not explicit and \
                os.path.splitext(path)[1].lower() not in exts:
            continue
        if not explicit and fmt not in ("auto", "custom"):
            ext = os.path.splitext(path)[1].lower()
            if EXT_FORMAT.get(ext) != fmt and ext not in SNIFF_EXT:
                continue
        if is_icloud_stub(path) or \
                (not include_evicted and is_dataless(path)):
            skipped.append({"file": path, "reason": NOT_LOCAL, "dir": False})
            continue
        try:
            raw = read_bytes(path, file_timeout)
        except ReadTimeout:
            skipped.append({"file": path, "reason": READ_TIMEOUT,
                            "dir": False})
            continue
        except OSError as exc:
            errors.append(f"cannot read {path}: {exc}")
            continue
        if b"\0" in raw[:4096]:
            if explicit:
                errors.append(f"{path}: binary file skipped")
            continue
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        f = choose_format(path, text, fmt, explicit)
        if f is None:
            if explicit:
                errors.append(f"{path}: no index markup format recognised "
                              f"(use --format)")
            continue
        es = read_file(path, text, f, findings, custom)
        files.append((path, f, len(es)))
        entries.extend(es)
    findings.extend(lint_entries(entries))
    findings.sort(key=lambda x: (x.file, x.line, x.rule))
    return files, entries, findings, errors


def main(argv: Optional[List[str]] = None) -> int:
    ap = build_argparser()
    args = ap.parse_args(argv)
    if args.list_rules:
        for rid, (clause, sev, title, chk) in RULES.items():
            print(f"{rid:26} §{clause:13} {sev:5} {title}  [{chk}]")
        return 0
    if not args.paths:
        ap.print_usage(sys.stderr)
        print("iso999_markup.py: error: at least one PATH is required",
              file=sys.stderr)
        return 2
    custom = None
    if args.format == "custom" or args.entry_regex:
        if not args.entry_regex:
            print("iso999_markup.py: error: --format custom needs "
                  "--entry-regex", file=sys.stderr)
            return 2
        try:
            rx = re.compile(args.entry_regex, re.S)
        except re.error as exc:
            print(f"iso999_markup.py: error: bad --entry-regex: {exc}",
                  file=sys.stderr)
            return 2
        if "body" not in rx.groupindex:
            print("iso999_markup.py: error: --entry-regex needs a named "
                  "group (?P<body>...)", file=sys.stderr)
            return 2
        if not args.xref_sep:
            print("iso999_markup.py: error: --xref-sep must not be empty",
                  file=sys.stderr)
            return 2
        custom = CustomSyntax(rx, args.xref_sep, args.target_sep)
        args.format = "custom"
    for p in args.paths:
        if not os.path.exists(p):
            print(f"iso999_markup.py: error: no such path: {p}",
                  file=sys.stderr)
            return 2
    exts = tuple("." + x.strip().lstrip(".").lower()
                 for x in args.ext.split(",") if x.strip())
    skipped: List[dict] = []
    files, entries, findings, errors = run(
        args.paths, args.format, custom, exts,
        include_evicted=args.include_evicted, file_timeout=args.file_timeout,
        skipped=skipped)
    for err in errors:
        print(f"iso999_markup.py: warning: {err}", file=sys.stderr)
    summary = summarise(files, entries, findings, skipped)
    shown = [f for f in findings
             if args.min_severity == "info" or f.severity == "warn"]
    if args.json:
        doc = {"summary": summary, "findings": [f.as_dict() for f in shown]}
        if args.entries:
            doc["entries"] = [e.as_dict() for e in entries]
        json.dump(doc, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        for f in shown:
            print(f"{f.file}:{f.line}: {f.severity.upper()} {f.rule} "
                  f"(§{f.clause}) {f.message}")
        if args.entries:
            print("\nEntries:")
            for e in entries:
                extra = f" {e.kind} {'; '.join(e.targets)}" \
                    if e.targets else ""
                rng = f" |{'(' if e.range == 'open' else ')'}" \
                    if e.range else ""
                print(f"  {e.where()}: {' ! '.join(e.path)}{extra}{rng}")
        print("\nSummary:")
        for fl in summary["files"]:
            print(f"  {fl['file']}: {fl['format']}, {fl['entries']} "
                  f"entries")
        print(f"  {summary['entries']} entries, "
              f"{summary['distinct_headings']} distinct headings, "
              f"{summary['distinct_paths']} distinct heading paths")
        if summary["variant_clusters"]:
            print("  Top variant clusters:")
            for c in summary["variant_clusters"]:
                print("    " + " | ".join(
                    f"{m} ({c['occurrences'][m]})" for m in c["forms"]))
        if summary["skipped_files"]:
            print("  Not read: " + ", ".join(
                f"{r} {n}" for r, n in summary["skipped"].items()))
            for x in summary["skipped_files"]:
                what = "dir" if x.get("dir") else "file"
                print(f"    {x['reason']} ({what}): {x['file']}")
            if summary["skipped"][NOT_LOCAL]:
                print("    not-local items were not opened (reading would "
                      "trigger a download); use --include-evicted to force")
            if summary["skipped"][READ_TIMEOUT]:
                print(f"    reads over {args.file_timeout:g}s were abandoned "
                      "(worker threads may linger until the OS read returns)")
        print(f"  {summary['warn']} warning(s), {summary['info']} info. "
              f"Heuristic check against ISO 999 guidance; review each "
              f"finding.")
    return 1 if summary["warn"] else 0


if __name__ == "__main__":
    sys.exit(main())
