#!/usr/bin/env python3
"""Convert pkgsite HTML (local server) into iso999_lint.py text input.

Ordering is never changed: entries are emitted in the exact order they
appear in the HTML.

Package pages (the "Index" section, ul.Documentation-indexList):
  level 0 = li.Documentation-indexConstants / -indexVariables / -indexFunction
            / -indexType (and anything else directly in the top list)
  level 1 = li inside ul.Documentation-indexTypeFunctions and
            ul.Documentation-indexTypeMethods (constructors, then methods,
            rendered by pkgsite as two consecutive, unlabelled sub-lists)
  locator = 1-based line number, in the same HTML file, of the element whose
            id= equals the link's #anchor (the "page" the entry points to).
            Missing target -> locator "0" and a note on stderr.
  views:
    display  heading = link text up to the identifier (parameter lists and
             results dropped, because they contain commas that the linter
             would read as locator separators; they never decide order since
             sibling names are unique). e.g. "func (t Time) Add".
    ident    heading = the bare identifier (anchor tail: "Time.Add" -> "Add";
             "pkg-constants" -> "Constants").

Std listing (/std): rows of the UnitDirectories table; pathCell rows are
level 0, subdirectory rows level 1 (their displayed text is the last path
element). Rows with class containing "internal" are hidden by default in the
UI and are skipped unless --include-internal. Locator = row ordinal (the
listing has no in-page targets; each link opens another page).
"""
import re
from urllib.parse import unquote
import sys
from html.parser import HTMLParser


class IndexParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_index = False
        self.depth_ul = 0
        self.sub_ul = 0
        self.cur = None
        self.items = []  # (level, cls, href, text)
        self.li_cls = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class") or ""
        if tag == "ul" and "Documentation-indexList" in cls:
            self.in_index = True
            self.depth_ul = 1
            return
        if not self.in_index:
            return
        if tag == "ul":
            self.depth_ul += 1
        elif tag == "li":
            self.li_cls = cls
        elif tag == "a" and "href" in a:
            self.cur = [self.depth_ul - 1, self.li_cls, a["href"], ""]

    def handle_endtag(self, tag):
        if not self.in_index:
            return
        if tag == "a" and self.cur is not None:
            self.cur[3] = " ".join(self.cur[3].split())
            self.items.append(tuple(self.cur))
            self.cur = None
        elif tag == "ul":
            self.depth_ul -= 1
            if self.depth_ul == 0:
                self.in_index = False

    def handle_data(self, data):
        if self.cur is not None:
            self.cur[3] += data


def anchor_lines(html):
    lines = {}
    for n, line in enumerate(html.split("\n"), 1):
        for m in re.finditer(r'\bid="([^"]+)"', line):
            lines.setdefault(m.group(1), n)
    return lines


def display_head(text):
    # "func (t Time) Add(d Duration) Time" -> "func (t Time) Add"
    m = re.match(r"^(func\s+(\([^)]*\)\s*)?\w+|type\s+\w+)", text)
    return m.group(1) if m else text


def pkg(path, view):
    html = open(path, encoding="utf-8").read()
    p = IndexParser()
    p.feed(html)
    ids = anchor_lines(html)
    out = []
    for level, cls, href, text in p.items:
        anchor = href.split("#", 1)[1] if "#" in href else href
        loc = ids.get(anchor) or ids.get(unquote(anchor))
        anchor = unquote(anchor)
        if loc is None:
            print(f"{path}: no target for {href}", file=sys.stderr)
            loc = 0
        if view == "display":
            head = display_head(text)
        else:
            head = {"pkg-constants": "Constants", "pkg-variables": "Variables",
                    "pkg-notes": "Notes"}.get(anchor, anchor.split(".")[-1])
        out.append("  " * level + f"{head}, {loc}")
    return out


def std(path, include_internal):
    html = open(path, encoding="utf-8").read()
    out = []
    n = 0
    rows = re.finditer(
        r'<tr[^>]*?(?:data-id="([^"]*)")?[^>]*?class="([^"]*)"[^>]*>\s*<td[^>]*>\s*'
        r'<div class="(UnitDirectories-(?:pathCell|subdirectory))">(.*?)</div>',
        html, re.S)
    for m in rows:
        rowcls, kind, body = m.group(2), m.group(3), m.group(4)
        if "internal" in rowcls and not include_internal:
            continue
        a = re.search(r'<a href="([^"]+)">([^<]+)</a>', body)
        if a:
            text = a.group(2).strip()
        else:
            t = re.sub(r"<[^>]+>", " ", body)
            text = " ".join(t.split()) or "?"
        n += 1
        level = 0 if kind.endswith("pathCell") else 1
        out.append("  " * level + (f"{text}, {n}" if a else text))
    return out


if __name__ == "__main__":
    mode, path = sys.argv[1], sys.argv[2]
    if mode == "std":
        lines = std(path, "--include-internal" in sys.argv)
    else:
        lines = pkg(path, mode)
    print("\n".join(lines))
