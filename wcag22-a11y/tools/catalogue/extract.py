"""Extract SC, guidelines, glossary and conformance from local WCAG 2.2 HTML into JSON."""
import json, re, sys
from html.parser import HTMLParser

VOID = {"br", "img", "hr", "meta", "link", "input", "wbr", "source", "col"}


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    def cls(self):
        return (self.attrs.get("class") or "").split()

    def iter(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.iter()

    def text(self):
        out = []
        for c in self.children:
            out.append(c if isinstance(c, str) else c.text())
        return "".join(out)


class B(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root", [])
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, d):
        self.cur.children.append(d)


def parse(html):
    b = B()
    b.feed(html)
    return b.root


def ws(s):
    return re.sub(r"\s+", " ", s)


def inline(n):
    if isinstance(n, str):
        return ws(n)
    if n.tag in ("script", "style"):
        return ""
    if "self-link" in n.cls() or "screenreader" in n.cls():
        return ""
    inner = "".join(inline(c) for c in n.children)
    if n.tag == "code":
        return "`" + inner.strip() + "`"
    if n.tag in ("em", "i", "dfn", "strong", "b"):
        mk = "**" if n.tag in ("strong", "b") else "*"
        if not inner.strip():
            return inner
        lead = " " if inner[:1].isspace() else ""
        trail = " " if inner[-1:].isspace() else ""
        return lead + mk + inner.strip() + mk + trail
    if n.tag == "br":
        return " "
    return inner


BLOCK = {"p", "ul", "ol", "dl", "div", "section", "table", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "dt", "dd", "li", "details", "aside"}


def blocks(n, depth=0):
    """Render children of n as list of markdown lines (paragraph blocks)."""
    out = []
    buf = []

    def flush():
        t = "".join(buf).strip()
        if t:
            out.append(t)
        buf.clear()

    for c in n.children:
        if isinstance(c, str) or c.tag not in BLOCK:
            buf.append(inline(c))
            continue
        flush()
        out.extend(block(c, depth))
    flush()
    return out


def ind(s):
    return "\n".join("  " + l for l in s.split("\n"))


def block(c, depth=0):
    cls = c.cls()
    if "doclinks" in cls or "header-wrapper" in cls or "note-title" in cls:
        return []
    if c.tag == "p":
        t = inline(c).strip()
        return [t] if t else []
    if c.tag in ("ul", "ol"):
        res = []
        i = 0
        for li in c.children:
            if isinstance(li, Node) and li.tag == "li":
                i += 1
                sub = blocks(li, depth + 1)
                mark = "-" if c.tag == "ul" else f"{i}."
                if sub:
                    res.append(f"{mark} {sub[0]}")
                    res.extend(ind(s) for s in sub[1:])
        return ["\n".join(res)] if res else []
    if c.tag == "dl":
        res = []
        for d in c.children:
            if not isinstance(d, Node):
                continue
            if d.tag == "dt":
                res.append("- **" + inline(d).strip() + ":**")
            elif d.tag == "dd":
                sub = blocks(d, depth + 1)
                if sub and res and res[-1].endswith(":**"):
                    res[-1] += " " + sub[0]
                    res.extend(ind(s) for s in sub[1:])
                else:
                    res.extend(ind(s) for s in sub)
        return ["\n".join(res)] if res else []
    if "note" in cls or "example" in cls:
        title = "Note" if "note" in cls else "Example"
        for x in c.iter():
            if x is not c and ("note-title" in x.cls() or "marker" in x.cls()):
                tt = ws(x.text()).strip()
                if tt:
                    title = tt
                break
        sub = blocks(c, depth)
        if sub and re.fullmatch(r"(Note|Example)( \d+)?", sub[0].strip()):
            title = sub.pop(0).strip()
        if not sub:
            return []
        return [f"*{title}:* {sub[0]}"] + sub[1:]
    return blocks(c, depth)


def main(path):
    root = parse(open(path, encoding="utf-8").read())
    secs = [n for n in root.iter() if n.tag == "section"]
    principles, guidelines, scs = {}, {}, []
    for s in secs:
        h = next((x for x in s.children if isinstance(x, Node) and "header-wrapper" in x.cls()), None)
        if h is None:
            continue
        hd = next(x for x in h.children if isinstance(x, Node) and x.tag.startswith("h"))
        head = ws(hd.text()).strip()
        m = re.match(r"Success Criterion (\d+\.\d+\.\d+)\s+(.*)", head)
        if m and "guideline" in s.cls():
            sid, title = m.groups()
            lvl = None
            for n in s.iter():
                if n.tag == "p" and "conformance-level" in n.cls():
                    lvl = re.search(r"Level (A+)", n.text()).group(1)
                    break
            body = [x for x in s.children if not (isinstance(x, Node) and "conformance-level" in x.cls())]
            tmp = Node("div", [])
            tmp.children = body
            text = blocks(tmp)
            und = None
            for n in s.iter():
                if n.tag == "a" and "Understanding/" in n.attrs.get("href", ""):
                    und = n.attrs["href"]
                    break
            refs = []
            for n in s.iter():
                h2 = n.attrs.get("href", "") if n.tag == "a" else ""
                if h2.startswith("#dfn-") and h2[1:] not in refs:
                    refs.append(h2[1:])
            new = bool(text) and text[0].strip() == "New"
            if new:
                text = text[1:]
            scs.append(dict(id=sid, slug=s.attrs["id"], title=title, level=lvl, text=text, understanding=und, new=new, principle=sid[0], guideline=sid.rsplit(".", 1)[0], dfn_refs=refs))
            continue
        m = re.match(r"Guideline (\d+\.\d+)\s+(.*)", head)
        if m:
            guidelines[m.group(1)] = dict(title=m.group(2), slug=s.attrs["id"])
            continue
        m = re.match(r"Principle (\d)\s+(.*)", head) or re.match(r"(\d)\.\s+(Perceivable|Operable|Understandable|Robust)$", head)
        if m:
            principles[m.group(1)] = dict(title=m.group(2), slug=s.attrs["id"])
    # glossary
    gl = {}
    gsec = next(n for n in secs if n.attrs.get("id") == "glossary")
    for dl in gsec.iter():
        if dl.tag != "dl":
            continue
        cur = None
        for d in dl.children:
            if not isinstance(d, Node):
                continue
            if d.tag == "dt":
                dfn = next((x for x in d.iter() if x.tag == "dfn"), None)
                cur = dict(term=ws(d.text()).strip(), id=(dfn.attrs.get("id") if dfn else None), text=[], new=False)
                gl[cur["term"]] = cur
            elif d.tag == "dd" and cur is not None:
                cur["text"] = blocks(d)
                if cur["text"] and cur["text"][0].strip() == "New":
                    cur["text"] = cur["text"][1:]
                    cur["new"] = True
        break
    csec = next(n for n in secs if n.attrs.get("id") == "conformance")
    conf = []
    for c in csec.children:
        if isinstance(c, Node) and c.tag == "section":
            conf.append(section_md(c, 3))
        elif isinstance(c, Node):
            conf.extend(block(c))
    json.dump(dict(principles=principles, guidelines=guidelines, scs=scs, glossary=gl, conformance=conf), open("wcag.json", "w"), indent=1, ensure_ascii=False)
    print(len(scs), "SC", len(guidelines), "guidelines", principles.keys(), len(gl), "terms")


def section_md(s, lvl):
    out = []
    for c in s.children:
        if not isinstance(c, Node):
            continue
        if "header-wrapper" in c.cls():
            hd = next(x for x in c.children if isinstance(x, Node) and x.tag.startswith("h"))
            out.append("#" * lvl + " " + ws(hd.text()).strip())
        elif c.tag == "section":
            out.append(section_md(c, lvl + 1))
        else:
            out.extend(block(c))
    return "\n\n".join(x for x in out if x)


if __name__ == "__main__":
    main(sys.argv[1])
