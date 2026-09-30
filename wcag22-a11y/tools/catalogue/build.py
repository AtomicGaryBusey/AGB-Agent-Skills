"""Render references/sc-*.md, glossary.md, conformance.md from extracted W3C data + authored content."""
import json, os, re, html, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "references")
AXE_VERSION = "4.13.0"

d = json.load(open(os.path.join(HERE, ".cache", "wcag.json")))
techs = json.load(open(os.path.join(HERE, ".cache", "techs.json")))
axe = json.load(open(os.path.join(HERE, "axe_map.json")))
auth = {}
for f in ("p1.json", "p2.json", "p34.json"):
    auth.update(json.load(open(os.path.join(HERE, "authored", f))))

SPEC = "https://www.w3.org/TR/WCAG22/"
RAW = open(os.path.join(HERE, ".cache", "wcag22.html"), encoding="utf-8").read()

ATTR = """> **Source and licence.** Normative text quoted in this file (marked as block quotes{extra}) is copied verbatim from
> *Web Content Accessibility Guidelines (WCAG) 2.2*, W3C Recommendation, 12 December 2024 edition,
> <https://www.w3.org/TR/WCAG22/>. Copyright © 2024 World Wide Web Consortium.
> <https://www.w3.org/copyright/document-license-2023/>. Status: W3C Recommendation.
{tech}> All other text (summaries, testability, procedures, code patterns and examples) is original to this skill.
> See `NOTICE` at the skill root."""
TECH_ATTR = """> Technique and failure IDs/titles and ACT rule names are taken from *Understanding WCAG 2.2* and
> *Techniques for WCAG 2.2* (W3C Group Notes, informative), <https://www.w3.org/WAI/WCAG22/Understanding/>,
> <https://www.w3.org/WAI/WCAG22/Techniques/>, Copyright © 2024 World Wide Web Consortium, under the same licence.
"""


def key(sid):
    return [int(p) for p in sid.split(".")]


def guideline_text(slug):
    i = re.search(r'<section[^>]*id="%s"' % re.escape(slug), RAW).start()
    m = re.compile(r'How to Meet [^<]*</a></div><p>(.*?)</p>', re.S).search(RAW, i)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1)))).strip()


def quote(lines):
    out = []
    for i, block in enumerate(lines):
        if i:
            out.append(">")
        for ln in block.split("\n"):
            out.append("> " + ln if ln else ">")
    return "\n".join("  " + l for l in out)


def strip_id(tid, title):
    return re.sub(r"^%s:\s*" % re.escape(tid), "", title)


def render_sc(s):
    a = auth[s["id"]]
    t = techs[s["id"]]
    obsolete = s["level"] is None
    lvl = "Obsolete; Level A in WCAG 2.0/2.1" if obsolete else "Level " + s["level"]
    head = f"### WCAG-{s['id']} — {s['title']} ({lvl})" + (" — new in 2.2" if s["new"] else "")
    L = [f'<a id="wcag-{s["id"].replace(".", "-")}"></a>', head, ""]
    L.append(f"Spec: <{SPEC}#{s['slug']}> · Understanding: <{s['understanding']}>")
    L.append("")
    L.append("- **Text:**")
    L.append("")
    L.append(quote(s["text"]))
    L.append("")
    L.append(f"- **Applies to:** {a['applies']}")
    L.append(f"- **Testability:** {a['testability']} — {a['tools']}")
    rules = axe.get(s["id"], [])
    L.append("  - **axe-core rules (" + AXE_VERSION + "):** " + (", ".join(f"`{r}`" for r in rules) if rules else "none"))
    L.append("- **Test procedure:**")
    for i, st in enumerate(a["procedure"], 1):
        L.append(f"  {i}. {st}")
    L.append("- **Common failures:**")
    if t["failure"]:
        for tid, ti in t["failure"].items():
            L.append(f"  - {tid} — {strip_id(tid, ti)}")
    else:
        L.append("  - No W3C failure techniques are documented for this SC.")
    for p in a["patterns"]:
        L.append(f"  - Pattern: {p}")
    notes = t.get("suf_note") or []
    if t["sufficient"]:
        L.append("- **Sufficient techniques:**")
    elif len(notes) == 1:
        L.append("- **Sufficient techniques:** " + notes[0])
    elif notes:
        L.append("- **Sufficient techniques** (no numbered techniques; Understanding lists):")
        L.extend("  - " + n for n in notes)
    else:
        L.append("- **Sufficient techniques:** none documented (obsolete criterion).")
    for tid, ti in t["sufficient"].items():
        L.append(f"  - {tid} — {strip_id(tid, ti)}")
    if t["act"]:
        L.append("- **ACT test rules:** " + "; ".join(
            f"[{n}](https://www.w3.org{u})" if u.startswith("/") else f"[{n}]({u})" for n, u in t["act"]))
    if a.get("pass") and a.get("fail"):
        L.append("- **Pass/fail example:**")
        L.append("")
        L.append("  Pass:")
        L.append("")
        L.append(f"  ```{a['pass']['lang']}")
        L.extend("  " + ln if ln else "" for ln in a["pass"]["code"].rstrip("\n").split("\n"))
        L.append("  ```")
        L.append("")
        L.append("  Fail:")
        L.append("")
        L.append(f"  ```{a['fail']['lang']}")
        L.extend("  " + ln if ln else "" for ln in a["fail"]["code"].rstrip("\n").split("\n"))
        L.append("  ```")
    else:
        L.append("- **Pass/fail example:** not applicable (obsolete; see the notes above).")
    L.append("")
    return "\n".join(L)


FILES = {"1": "sc-1-perceivable.md", "2": "sc-2-operable.md", "3": "sc-3-understandable.md", "4": "sc-4-robust.md"}


def build_sc():
    for p, fname in FILES.items():
        pr = d["principles"][p]
        scs = sorted([s for s in d["scs"] if s["principle"] == p], key=lambda s: key(s["id"]))
        gls = sorted([g for g in d["guidelines"] if g.startswith(p + ".")], key=key)
        L = [f"# WCAG 2.2 success criteria — Principle {p}: {pr['title']}", "",
             ATTR.format(extra=", including SC text, notes and guideline statements", tech=TECH_ATTR), ""]
        L.append(f"Principle {p} has {len(scs)} success-criterion sections. Each entry uses the check ID `WCAG-<sc>` "
                 "(see `check-index.md`). Testability: **automated** = a tool can decide the core requirement for most "
                 "content; **assisted** = tools find candidates or partial failures and a human confirms; **manual** = "
                 "human judgement dominates. \"Static scanner\" means the skill's source-code scanner; \"page runner\" "
                 f"means the live-page runner (axe-core {AXE_VERSION} plus custom checks).")
        L.append("")
        L.append("## Contents")
        L.append("")
        for g in gls:
            L.append(f"- Guideline {g} {d['guidelines'][g]['title']}")
            for s in scs:
                if s["guideline"] == g:
                    lv = "obsolete" if s["level"] is None else s["level"]
                    L.append(f"  - [WCAG-{s['id']} {s['title']}](#wcag-{s['id'].replace('.', '-')}) ({lv}{', new in 2.2' if s['new'] else ''})")
        L.append("")
        for g in gls:
            gd = d["guidelines"][g]
            L.append(f"## Guideline {g} — {gd['title']}")
            L.append("")
            L.append("> " + guideline_text(gd["slug"]))
            L.append("")
            for s in scs:
                if s["guideline"] == g:
                    L.append(render_sc(s))
        open(os.path.join(OUT, fname), "w").write("\n".join(L).rstrip() + "\n")


def build_glossary():
    g = d["glossary"]
    used = {}
    for s in d["scs"]:
        for r in s["dfn_refs"]:
            used.setdefault(r, []).append(s["id"])
    L = ["# WCAG 2.2 glossary (defined terms)", "",
         ATTR.format(extra=", i.e. every definition", tech=""), "",
         "All terms defined in WCAG 2.2 section 6 (Glossary), in the specification's order, with verbatim definitions. "
         "\"Used by\" lists the success criteria whose normative text links to the term (computed from the spec's "
         "markup). Terms auditors most often need when deciding pass/fail are marked **(key)**.", ""]
    KEY = {"programmatically determined (programmatically determinable)", "relative luminance", "contrast ratio", "target",
           "focus indicator", "perimeter", "minimum bounding box", "large scale (text)", "user interface component",
           "name", "role", "state", "essential", "mechanism", "keyboard interface", "pointer input", "single pointer",
           "dragging movement", "cognitive function test", "status message", "changes of context",
           "accessibility supported", "text alternative", "non-text content", "pure decoration", "image of text",
           "relationships", "structure", "CSS pixel", "viewport", "set of web pages", "web page", "process",
           "conforming alternate version", "same relative order", "same functionality", "content (web content)",
           "label", "general flash and red flash thresholds", "real-time event", "user inactivity", "section",
           "blocks of text", "input error", "legal commitments", "link purpose", "programmatically determined link context",
           "prerecorded", "live", "synchronized media", "captions", "audio description", "media alternative for text",
           "keyboard shortcut", "down-event", "up-event", "used in an unusual or restricted way", "style property",
           "on a full-screen window", "satisfies a success criterion", "relied upon (technologies that are)"}
    L.append("## Index")
    L.append("")
    L.append(", ".join(f"[{t}](#{v['id']})" for t, v in g.items()))
    L.append("")
    for t, v in g.items():
        L.append(f'<a id="{v["id"]}"></a>')
        L.append(f"### {t}" + (" (key)" if t in KEY else "") + (" — new in 2.2" if v["new"] else ""))
        L.append("")
        for i, b in enumerate(v["text"]):
            if i:
                L.append(">")
            for ln in b.split("\n"):
                L.append("> " + ln)
        L.append("")
        u = sorted(set(used.get(v["id"], [])), key=key)
        L.append("Used by: " + (", ".join(f"WCAG-{x}" for x in u) if u else "no SC text links it directly (used in conformance or other definitions)")
                 + f" · Spec: <{SPEC}#{v['id']}>")
        L.append("")
    missing = sorted(KEY - set(g))
    open(os.path.join(OUT, "glossary.md"), "w").write("\n".join(L).rstrip() + "\n")
    return missing


def build_conformance():
    conf = "\n\n".join(d["conformance"])
    conf = re.sub(r"^(#+) ", lambda m: "#" * (len(m.group(1))) + " ", conf, flags=re.M)
    quoted = "\n".join(("> " + l) if l else ">" for l in conf.split("\n"))
    lv = {}
    for s in d["scs"]:
        lv.setdefault(s["level"], []).append(s["id"])
    na, naa, naaa = len(lv["A"]), len(lv["AA"]), len(lv["AAA"])
    new_aa = [s for s in d["scs"] if s["new"] and s["level"] in ("A", "AA")]
    new_aaa = [s for s in d["scs"] if s["new"] and s["level"] == "AAA"]
    L = ["# WCAG 2.2 conformance", "",
         ATTR.format(extra="", tech=""), "",
         "Part 1 is our own auditor guidance. Part 2 reproduces WCAG 2.2 section 5 (Conformance) verbatim, "
         "with notes in *italics* as in the spec. The normative definitions of *conformance*, *accessibility supported*, "
         "*web page*, *process* and *conforming alternate version* are in `glossary.md`.", "",
         "## Part 1 — Auditor guidance (original to this skill)", "",
         "### The five conformance requirements at a glance", "",
         "| # | Requirement | What the auditor checks |", "|---|---|---|",
         "| 1 | Conformance level (5.2.1) | Every SC at the target level and below is satisfied (or not applicable), or a conforming alternate version exists at that level. |",
         "| 2 | Full pages (5.2.2) | The whole page is in scope — including every responsive variation and content revealed from the page (dialogs, menus, long descriptions). Parts cannot be excluded. |",
         "| 3 | Complete processes (5.2.3) | If a page is one step of a process (sign-up, checkout), every step is in scope; one failing step fails the process at that level. |",
         "| 4 | Accessibility-supported uses only (5.2.4) | Techniques relied on to pass an SC must actually work with the user agents and assistive technology the audience uses (e.g. an ARIA pattern that screen readers do not expose cannot be relied upon). |",
         "| 5 | Non-interference (5.2.5) | Content not relied upon must not block the rest of the page, and 1.4.2, 2.1.2, 2.3.1 and 2.2.2 apply to all content on the page, even content that is not relied upon. |",
         "",
         "### Conformance levels and counts", "",
         f"WCAG 2.2 contains 87 success-criterion sections: {na} at Level A, {naa} at Level AA, {naaa} at Level AAA, "
         "plus 4.1.1 Parsing, which is obsolete and removed (86 active criteria). Levels are cumulative:", "",
         f"- **Level A** — the {na} Level A criteria.",
         f"- **Level AA** — Level A plus the {naa} Level AA criteria = **{na + naa} criteria**.",
         f"- **Level AAA** — all {na + naa + naaa} active criteria. W3C does not recommend AAA as a blanket policy "
         "for whole sites because some AAA criteria cannot be met for some content.", "",
         "### What \"audit against WCAG 2.2 AA\" means", "",
         f"1. Evaluate every page in scope against all {na + naa} Level A and AA criteria. Each criterion ends as "
         "**pass**, **fail** or **not applicable** (a criterion with no matching content on the page is satisfied — "
         "e.g. 1.2.2 on a page with no video).",
         "2. Do not test 4.1.1 Parsing as a WCAG 2.2 criterion. Route real markup defects (duplicate IDs referenced by "
         "`for`/`aria-labelledby`, broken nesting that changes the accessibility tree) to 1.3.1 or 4.1.2. If a contract or "
         "policy still names WCAG 2.0/2.1, the spec notes that authors \"may need to continue to test and report 4.1.1\" "
         "(see the quote below).",
         "3. Include the whole page and all its states: responsive breakpoints, open menus and dialogs, error states, "
         "and every step of each process (requirements 2 and 3).",
         "4. Automated tools (axe-core, the static scanner) find a subset of failures only. A clean automated run is not "
         "a conformance result; each A/AA criterion marked assisted or manual in `check-index.md` needs human review, "
         "usually with a keyboard and at least one screen reader.",
         "5. AAA criteria are out of scope for an AA audit. Report any AAA criteria met as optional extra information "
         "(5.3.2), never as failures.",
         "6. A conformance claim is optional. If one is made it must have the five required components of 5.3.1 "
         "(date; guideline title, version and URI; level; the pages covered; technologies relied upon).", "",
         "### New at Level A/AA in WCAG 2.2 (delta from 2.1 AA)", "",
         *[f"- {s['id']} {s['title']} (Level {s['level']})" for s in sorted(new_aa, key=lambda s: key(s['id']))],
         "- Removed: 4.1.1 Parsing.",
         "", "New at AAA: " + ", ".join(f"{s['id']} {s['title']}" for s in sorted(new_aaa, key=lambda s: key(s['id']))) + ".", "",
         "### Partial conformance statements", "",
         "WCAG 2.2 defines two forms (5.4 and 5.5). Use the third-party form only for content that is genuinely not "
         "under the author's control (user comments, injected ads, aggregated feeds), and identify that content "
         "concretely. Use the language form only when the failure is caused by missing accessibility support for a "
         "language. Neither form turns a failing page into a conforming one; they describe what would conform. "
         "\"Partially conforms\" is not a WCAG conformance level — in an audit report, list each failing criterion instead.", "",
         "### Accessibility supported, in practice", "",
         "A technique only counts toward an SC if the audience's user agents and assistive technology support it. "
         "Record which browser and AT combinations were tested (an optional claim component in 5.3.2), and treat an ARIA "
         "pattern that fails in mainstream screen readers as not relied upon. The full normative definition is in "
         "`glossary.md` under *accessibility supported*.", "",
         "### Relationship to earlier versions (quoted)", "",
         "> " + html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", re.search(r"<p>(WCAG 2\.2 builds on and is backwards compatible.*?)</p>", RAW, re.S).group(1)))).strip(),
         ">",
         "> " + html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", re.search(r"<p>(WCAG 2\.2 uses the same conformance model.*?)</p>", RAW, re.S).group(1)))).strip(),
         "", f"— WCAG 2.2, Introduction, Comparison with WCAG 2.1 (<{SPEC}#comparison-with-wcag-2-1>).", "",
         "## Part 2 — WCAG 2.2 section 5, Conformance (verbatim)", "",
         f"Source: <{SPEC}#conformance>", "", quoted, ""]
    open(os.path.join(OUT, "conformance.md"), "w").write("\n".join(L).rstrip() + "\n")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build_sc()
    print("glossary key terms not found:", build_glossary())
    build_conformance()
