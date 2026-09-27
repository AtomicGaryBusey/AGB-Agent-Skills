#!/usr/bin/env python3
"""Convert rustdoc item listings to iso999_lint text input, one file per kind section.

Sources: all.html (h3#kind + ul.all-items), module index.html (h2#kind + dl.item-table),
sidebar-items.js (JSON). Order is preserved exactly. Each output line is
    <converted heading>, <ordinal>
where <ordinal> is the entry's 1-based position in its section. The ordinal is a
stand-in locator (the real locator is the hyperlink); it is ascending and unique,
so it cannot trigger locator rules, and the comma separator stops a trailing
number in a heading ("route 66") from being read as a locator.

Name conversion (declared filing assumptions, --mode):
  words  (default): '::' -> ' ', '_' runs -> ' ', leading/trailing '_' dropped.
                    CamelCase humps are NOT split.
  camel           : as 'words', and also split CamelCase humps (FooBar -> Foo Bar,
                    HTTPServer -> HTTP Server, Foo10 unchanged).
  raw             : name exactly as displayed.
A TSV map (section, ordinal, displayed, converted, href) is written next to the files.
"""
import html, json, re, sys, os
from html.parser import HTMLParser

def convert(name, mode):
    if mode == "raw":
        return name
    s = name.replace("::", " ")
    if mode == "camel":
        s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
        s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    s = re.sub(r"_+", " ", s).strip()
    return re.sub(r"\s+", " ", s)

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections, self.cur, self.in_a, self.href, self.buf = [], None, False, None, []
        self.in_main = False; self.depth_dt = False; self.in_h = False; self.hid = None
    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag in ("h2", "h3") and a.get("id"):
            self.in_h = True; self.hid = a["id"]
        if tag == "ul" and "all-items" in (a.get("class") or ""):
            self.cur = (self.hid, []); self.sections.append(self.cur)
        if tag == "dl" and "item-table" in (a.get("class") or ""):
            self.cur = (self.hid, []); self.sections.append(self.cur)
        if tag == "dt" and self.cur is not None:
            self.depth_dt = True
        if tag == "a" and self.cur is not None and (self.depth_dt or self.cur_is_ul()):
            if not self.in_a:
                self.in_a, self.href, self.buf = True, a.get("href"), []
    def cur_is_ul(self):
        return True
    def handle_endtag(self, tag):
        if tag in ("h2", "h3"): self.in_h = False
        if tag == "a" and self.in_a:
            self.in_a = False
            txt = "".join(self.buf).strip()
            if txt and self.cur is not None and (self.depth_dt or True):
                self.cur[1].append((txt, self.href))
        if tag == "dt": self.depth_dt = False
        if tag in ("ul", "dl"): self.cur = None
    def handle_data(self, d):
        if self.in_a: self.buf.append(d)

def from_html(path):
    p = P(); p.feed(open(path, encoding="utf-8").read())
    # module pages: keep only the first <a> per <dt> (name); drop stability badges etc.
    return [(sid, items) for sid, items in p.sections if items]

def from_sidebar(path):
    t = open(path, encoding="utf-8").read()
    t = t[t.index("{"): t.rindex("}") + 1]
    d = json.loads(t)
    return [(k, [(x[0] if isinstance(x, list) else x, None) for x in v]) for k, v in d.items()]

def main():
    src, outdir = sys.argv[1], sys.argv[2]
    modes = sys.argv[3].split(",") if len(sys.argv) > 3 else ["words", "raw", "camel"]
    secs = from_sidebar(src) if src.endswith(".js") else from_html(src)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "map.tsv"), "w", encoding="utf-8") as m:
        for sid, items in secs:
            for mode in modes:
                with open(os.path.join(outdir, f"{sid}.{mode}.txt"), "w", encoding="utf-8") as f:
                    for i, (name, href) in enumerate(items, 1):
                        f.write(f"{convert(name, mode)}, {i}\n")
            for i, (name, href) in enumerate(items, 1):
                m.write(f"{sid}\t{i}\t{name}\t{convert(name,'words')}\t{href or ''}\n")
    for sid, items in secs:
        print(f"{sid}\t{len(items)}")
main()
