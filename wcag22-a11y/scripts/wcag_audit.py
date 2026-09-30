#!/usr/bin/env python3
"""WCAG 2.2 audit orchestrator: run the static scanner and the rendered-page
runner, merge and de-duplicate their findings, build the SC coverage table for
the chosen level, and emit the report skeleton in the skills' shared format.

Stdlib only, Python 3.9+. Tool contract: every tool prints a JSON envelope
{"meta", "summary", "findings"}; only that envelope is relied on.

Usage:
  wcag_audit.py TARGET [--url URL] [--level A|AA|AAA] [--pages N]
                [--no-page] [--no-scan] [--probe-actions] [--screenshots DIR]
                [--check-timeout MS] [--json OUT] [--report md|json] [--out FILE]

TARGET is a source directory or file (static scan with wcag_scan.py), or a URL.
The page runner (node wcag_page.mjs) audits --url, a URL TARGET, or a local
TARGET that is an .html file or a directory with top-level *.html files.

Exit codes: 0 = no nonconformities, 1 = nonconformities found, 2 = usage/error.
"""

import argparse
import datetime
import json
import os
import re
import shlex
import subprocess
import sys

VERSION = "0.1.0"
WCAG = "2.2 (2024-12-12)"

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
REFS = os.path.join(SKILL, "references")
SCAN = os.path.join(HERE, "wcag_scan.py")
PAGE = os.path.join(HERE, "wcag_page.mjs")
SETUP = os.path.join(HERE, "setup_page_runner.sh")

LEVEL_RANK = {"A": 1, "AA": 2, "AAA": 3}
SEV_RANK = {"fail": 0, "warn": 1, "manual": 2, "info": 3}
REPORT_SEV = {
    "fail": "Nonconformity",
    "warn": "Deviation",
    "manual": "Review note",
    "info": "Advisory",
}
REPORT_SEV_LONG = {
    "fail": "Nonconformity",
    "warn": "Deviation (needs confirmation)",
    "manual": "Review note (manual check)",
    "info": "Advisory",
}

ST_FAIL = "failures found"
ST_WARN = "warnings"
ST_PASS = "automated checks passed (partial coverage)"
ST_MANUAL = "not automatable — manual check required"
ST_NOTRUN = "not checked — no tool run covered it"

# Report statuses (SKILL.md vocabulary). Tools can only establish Fail; Pass and N/A are the
# auditor's judgement, so every other SC starts as Not evaluated. The ST_* values above are the
# "tool signal" shown beside the status.
RS_FAIL = "Fail"
RS_PASS = "Pass"
RS_NA = "N/A"
RS_NOTEVAL = "Not evaluated"

# Coverage comes from the page envelope itself (meta.checks_sc / meta.sc_covered, which
# wcag_page derives from its CHECKS table, filtered by level and --rules). This map mirrors
# wcag_page.mjs CHECKS and is only a fallback for envelopes from older runners that do not
# state coverage; test_wcag_audit.py checks it against the JS table so it cannot drift.
PAGE_CHECK_SC = {
    "contrast-sample": ["1.4.3", "1.4.6"],
    "non-text-contrast": ["1.4.11"],
    "target-size": ["2.5.8"],
    "auto-update": ["2.2.2"],
    "status-messages": ["4.1.3"],
    "focus": ["2.4.7", "2.4.11", "2.4.12", "2.1.2", "2.4.3", "1.4.11"],
    "dialogs": ["2.1.2"],
    "reflow": ["1.4.10"],
    "text-spacing": ["1.4.12"],
    "resize-text": ["1.4.4"],
    "consistent-help": ["3.2.6"],
    "auth": ["3.3.7", "3.3.8", "3.3.9"],
}

STYLE_EXT = {".css", ".scss", ".sass", ".less", ".styl", ".pcss"}
COMPONENT_EXT = {".jsx", ".tsx", ".js", ".ts", ".mjs", ".vue", ".svelte", ".astro"}
TEMPLATE_EXT = {".njk", ".erb", ".hbs", ".handlebars", ".mustache", ".liquid", ".j2",
                ".jinja", ".jinja2", ".twig", ".ejs", ".php", ".cshtml", ".razor",
                ".tpl", ".haml", ".pug", ".slim"}


# --------------------------------------------------------------------------- index

def sc_key(sc):
    """Sort key for an SC id such as '2.4.11'; non-numeric ids sort last."""
    try:
        return tuple(int(p) for p in str(sc).split("."))
    except ValueError:
        return (99, str(sc))


def load_index(path=None):
    """Parse references/check-index.md -> {sc: {sc,title,level,testability,file,anchor}}."""
    path = path or os.path.join(REFS, "check-index.md")
    rows = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("| WCAG-"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 8:
                continue
            sc = cells[0][len("WCAG-"):]
            m = re.search(r"\(([^)#]+)#([^)]+)\)", cells[7])
            rows[sc] = {
                "sc": sc,
                "title": cells[1],
                "level": cells[2],
                "testability": cells[5],
                "file": m.group(1) if m else "",
                "anchor": m.group(2) if m else "wcag-" + sc.replace(".", "-"),
            }
    return rows


def load_procedures(refs=None):
    """First step of each SC's 'Test procedure' list -> {anchor: text}."""
    refs = refs or REFS
    out = {}
    try:
        names = sorted(n for n in os.listdir(refs) if n.startswith("sc-") and n.endswith(".md"))
    except OSError:
        return out
    for name in names:
        anchor, in_proc = None, False
        with open(os.path.join(refs, name), encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r'<a id="(wcag-[0-9-]+)"></a>', line)
                if m:
                    anchor, in_proc = m.group(1), False
                    continue
                if anchor and "**Test procedure:**" in line:
                    in_proc = True
                    continue
                if in_proc:
                    m = re.match(r"\s+1\.\s+(.*)", line)
                    if m and anchor not in out:
                        out[anchor] = m.group(1).strip()
                        in_proc = False
    return out


def in_scope(index, level):
    lim = LEVEL_RANK[level]
    return [r for r in sorted(index.values(), key=lambda r: sc_key(r["sc"]))
            if r["level"] in LEVEL_RANK and LEVEL_RANK[r["level"]] <= lim]


# ------------------------------------------------------------------ tool running

def run_json(cmd, cwd=None, timeout=1800):
    """Run a tool that prints a JSON envelope. Returns (envelope|None, exit_code, error)."""
    try:
        p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           universal_newlines=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, None, str(e)
    if p.returncode not in (0, 1):
        lines = (p.stderr or p.stdout or "").strip().splitlines()
        return None, p.returncode, lines[-1] if lines else "exit %d" % p.returncode
    try:
        return json.loads(p.stdout), p.returncode, None
    except ValueError as e:
        return None, p.returncode, "invalid JSON from tool: %s" % e


def page_runner_installed():
    """(ok, detail) from setup_page_runner.sh --check."""
    if not os.path.exists(SETUP):
        return False, "setup_page_runner.sh not found"
    try:
        p = subprocess.run(["bash", SETUP, "--check"], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, universal_newlines=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)
    return p.returncode == 0, p.stdout.strip()


def scanner_rule_sc(level):
    """SCs the static scanner has objective (fail/warn/info) rules for, from --list-rules."""
    try:
        p = subprocess.run([sys.executable, SCAN, "--list-rules"], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, universal_newlines=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return set()
    return parse_rule_list(p.stdout, level)


def parse_rule_list(text, level):
    covered = set()
    lim = LEVEL_RANK[level]
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 4 or parts[0] == "RULE":
            continue
        sc, lvl, sev = parts[1], parts[2], parts[3]
        if lvl in LEVEL_RANK and LEVEL_RANK[lvl] <= lim and sev in ("fail", "warn", "info"):
            covered.add(sc)
    return covered


def is_url(s):
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", s or ""))


def local_page_target(target):
    """Return the local path the page runner can audit, or None with a reason."""
    if os.path.isfile(target):
        if target.lower().endswith((".html", ".htm")):
            return target, None
        return None, "TARGET is not an HTML file; pass --url to audit rendered pages"
    if os.path.isdir(target):
        try:
            names = os.listdir(target)
        except OSError as e:
            return None, str(e)
        if any(n.lower().endswith((".html", ".htm")) for n in names):
            return target, None
        return None, ("TARGET directory has no top-level *.html entry page; "
                      "pass --url (a running app or a built HTML directory)")
    return None, "TARGET not found"


# ----------------------------------------------------------------- normalisation

def norm_loc(f):
    """Location identity for de-duplication: real path for files, URL minus fragment."""
    if f.get("url"):
        return "url:" + str(f["url"]).split("#")[0].rstrip("/")
    fp = f.get("file")
    if fp:
        if is_url(fp):
            return "url:" + fp.split("#")[0].rstrip("/")
        return "file:" + os.path.realpath(fp)
    return "none:"


def norm_snip(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def match_keys(f):
    sc, loc = str(f.get("sc") or f.get("id") or ""), norm_loc(f)
    keys = []
    if f.get("line") not in (None, ""):
        keys.append((sc, loc, "line", str(f["line"])))
    if f.get("selector"):
        keys.append((sc, loc, "sel", str(f["selector"]).strip()))
    if f.get("snippet"):
        keys.append((sc, loc, "snip", norm_snip(f["snippet"])))
    return keys


def target_kind(f):
    if f.get("tool") == "wcag_page" or f.get("url"):
        return "page"
    ext = os.path.splitext(str(f.get("file") or ""))[1].lower()
    if ext in STYLE_EXT:
        return "stylesheet"
    if ext in COMPONENT_EXT:
        return "component"
    if ext in TEMPLATE_EXT:
        return "template"
    return "page"


def check_id(sc):
    sc = str(sc or "")
    if sc.startswith("WCAG-"):
        return sc
    if re.match(r"^\d+\.\d+\.\d+$", sc):
        return "WCAG-" + sc
    return "WCAG-BP-" + (sc.replace("BP-", "") or "unknown")


# ------------------------------------------------------------------------ merge

def merge(envelopes, index=None):
    """Merge findings from tool envelopes; de-duplicate across tools.

    Two findings merge when they share SC and location and at least one of line,
    selector or normalised snippet, and come from different tools (or are exact
    duplicates). The merged row keeps the most severe tool severity.
    """
    index = index or {}
    rows, key_map = [], {}
    for env in envelopes:
        meta = env.get("meta") or {}
        tool_name = meta.get("tool") or "unknown"
        for f in env.get("findings") or []:
            f = dict(f)
            f.setdefault("tool", tool_name)
            if not f.get("sc") and f.get("id"):
                f["sc"] = str(f["id"]).replace("WCAG-", "")
            keys = match_keys(f)
            target = None
            for k in keys:
                for r in key_map.get(k, []):
                    tools = {s["tool"] for s in r["sources"]}
                    exact = any(_same(s, f) for s in r["sources"])
                    if exact or (f["tool"] not in tools and not _line_conflict(r, f)):
                        target = r
                        break
                if target:
                    break
            if target is None:
                target = {"sources": []}
                rows.append(target)
            if not any(_same(s, f) for s in target["sources"]):
                target["sources"].append(f)
            for k in keys:
                lst = key_map.setdefault(k, [])
                if target not in lst:
                    lst.append(target)
    return [_finalise(r, index) for r in rows]


def _line_conflict(row, f):
    """True when both carry a line number and the lines differ (different elements)."""
    if f.get("line") in (None, ""):
        return False
    lines = {str(s.get("line")) for s in row["sources"] if s.get("line") not in (None, "")}
    return bool(lines) and str(f["line"]) not in lines


def _same(a, b):
    fields = ("tool", "sc", "rule", "severity", "file", "url", "line", "col", "selector", "snippet")
    return all(a.get(k) == b.get(k) for k in fields)


def _finalise(r, index):
    src = sorted(r["sources"], key=lambda s: (SEV_RANK.get(s.get("severity"), 9), s.get("tool") != "wcag_scan"))
    lead = src[0]
    sc = str(lead.get("sc") or "")
    tsev = lead.get("severity") if lead.get("severity") in SEV_RANK else "info"
    level = (index.get(sc) or {}).get("level") or lead.get("level") or ""
    line = next((s.get("line") for s in src if s.get("line") not in (None, "")), None)
    col = next((s.get("col") for s in src if s.get("line") == line and s.get("col") not in (None, "")), None)
    return {
        "check_id": check_id(sc),
        "sc": sc,
        "sc_name": (index.get(sc) or {}).get("title") or lead.get("sc_name") or "",
        "level": level,
        "tool_severity": tsev,
        "severity": REPORT_SEV[tsev],
        "target": target_kind(lead),
        "file": next((s.get("file") for s in src if s.get("file")), None),
        "url": next((s.get("url") for s in src if s.get("url")), None),
        "line": line,
        "col": col,
        "selector": next((s.get("selector") for s in src if s.get("selector")), None),
        "snippet": lead.get("snippet") or next((s.get("snippet") for s in src if s.get("snippet")), None),
        "message": lead.get("message") or "",
        "help": next((s.get("help") for s in src if s.get("help")), None),
        "tools": sorted({s.get("tool") for s in src}),
        "rules": sorted({"%s:%s" % (s.get("tool"), s.get("rule")) for s in src}),
        "sources": src,
    }


def sort_rows(rows):
    """Rank rows by severity, then SC order, then location (the order SKILL.md prescribes)."""
    return sorted(rows, key=lambda r: (SEV_RANK[r["tool_severity"]], sc_key(r["sc"]),
                                       str(r.get("file") or r.get("url") or ""), r.get("line") or 0,
                                       str(r.get("selector") or "")))


def summarise(rows):
    c = {"nonconformities": 0, "deviations": 0, "advisories": 0, "review_notes": 0}
    name = {"fail": "nonconformities", "warn": "deviations", "info": "advisories", "manual": "review_notes"}
    by_sc = {}
    for r in rows:
        c[name[r["tool_severity"]]] += 1
        d = by_sc.setdefault(r["sc"], {"fail": 0, "warn": 0, "manual": 0, "info": 0})
        d[r["tool_severity"]] += 1
    c["by_sc"] = {k: by_sc[k] for k in sorted(by_sc, key=sc_key)}
    return c


# ------------------------------------------------------------ paths and grouping

def path_roots(target, url=None):
    """Local roots that report paths are made relative to: the TARGET root, then a local --url root."""
    roots = []
    for t in (target, url):
        if not t or is_url(t) or not os.path.exists(t):
            continue
        root = t if os.path.isdir(t) else os.path.dirname(os.path.abspath(t))
        root = os.path.realpath(root)
        if root not in roots:
            roots.append(root)
    return roots


def rel_path(p, roots):
    """A file path relative to the first root that contains it; never absolute.

    URLs are returned unchanged. A path outside every root is made relative to the
    first root (or the working directory when there is none).
    """
    if not p or is_url(str(p)):
        return p
    p = str(p)
    real = os.path.realpath(p)
    for root in roots:
        if real == root or real.startswith(root.rstrip(os.sep) + os.sep):
            return os.path.relpath(real, root)
    base = roots[0] if roots else os.getcwd()
    try:
        return os.path.relpath(real, base)
    except ValueError:  # different drive (Windows)
        return os.path.basename(p)


_NTH = re.compile(r":(nth-child|nth-of-type|nth-last-child|nth-last-of-type)\([^)]*\)")


def sel_pattern(sel):
    """Selector pattern for grouping: drop :nth-*() indexes and a leading 'html > body >'."""
    s = _NTH.sub("", str(sel or ""))
    s = re.sub(r"\s*>\s*", " > ", re.sub(r"\s+", " ", s)).strip()
    s = re.sub(r"^html > body > ", "", s)
    return s


def group_key(r):
    """Rows with the same key collapse into one report row.

    Source findings (file + line) group only on the identical file:line; rendered-page
    findings group on the selector pattern, whatever page they came from.
    """
    base = (r["check_id"], r["sc"], r["tool_severity"], tuple(r["rules"]))
    if r.get("line") not in (None, ""):
        return base + ("src", norm_loc(r), str(r["line"]))
    if r.get("selector"):
        return base + ("sel", sel_pattern(r["selector"]))
    return base + ("page", norm_snip(r.get("message")))


def group_rows(rows, roots=None):
    """Collapse rows (already numbered and sorted) into report rows.

    Each report row keeps the numbers of its member findings, the pages (files relative to
    the roots, or URLs) and the instance count. The full list stays in the JSON findings.
    """
    roots = roots or []
    groups, by_key = [], {}
    for r in rows:
        k = group_key(r)
        g = by_key.get(k)
        if g is None:
            g = {"lead": r, "members": []}
            by_key[k] = g
            groups.append(g)
        g["members"].append(r)
    out = []
    for i, g in enumerate(groups, 1):
        lead = g["lead"]
        pages = []
        for m in g["members"]:
            loc = rel_path(m.get("file"), roots) if m.get("file") else (m.get("url") or "?")
            if loc not in pages:
                pages.append(loc)
        out.append({
            "n": i, "findings": [m.get("n") for m in g["members"]],
            "instances": len(g["members"]), "pages": pages,
            "pattern": sel_pattern(lead.get("selector")) if lead.get("selector") else None,
            "tool_severity": lead["tool_severity"], "severity": lead["severity"],
            "check_id": lead["check_id"], "sc": lead["sc"],
        })
    return out


# --------------------------------------------------------------------- coverage

def page_coverage(meta):
    """SCs the page runner checked, from its envelope meta.

    Prefers what the envelope states (sc_covered, checks_sc, axe_sc_covered); the
    PAGE_CHECK_SC fallback is used only when neither sc_covered nor checks_sc is present.
    """
    cov = set()
    for k in ("sc_covered", "checks_sc"):
        v = meta.get(k)
        if isinstance(v, list):
            cov.update(str(x) for x in v)
        elif isinstance(v, dict):
            for scs in v.values():
                cov.update(str(x) for x in (scs or []))
    cov.update(str(x) for x in (meta.get("axe_sc_covered") or []))
    if not meta.get("checks_sc") and not meta.get("sc_covered"):
        for chk in meta.get("checks") or []:
            cov.update(PAGE_CHECK_SC.get(chk, []))
    return cov


def coverage(index, level, rows, covered, procedures=None):
    """Coverage table rows for every in-scope SC.

    covered: {sc: [tool names that ran an automated check for it]}.
    """
    procedures = procedures or {}
    counts = summarise(rows)["by_sc"]
    out = []
    for r in in_scope(index, level):
        sc = r["sc"]
        n = counts.get(sc, {"fail": 0, "warn": 0, "manual": 0, "info": 0})
        tools = sorted(covered.get(sc, []))
        if n["fail"]:
            status = ST_FAIL
        elif n["warn"]:
            status = ST_WARN
        elif tools:
            status = ST_PASS
        elif r["testability"] in ("manual", "assisted"):
            status = ST_MANUAL
        else:
            status = ST_NOTRUN
        needs_human = not (r["testability"] == "automated" and status in (ST_FAIL, ST_PASS))
        ref = "references/%s#%s" % (r["file"], r["anchor"])
        out.append({
            "check_id": "WCAG-" + sc, "sc": sc, "title": r["title"], "level": r["level"],
            "testability": r["testability"], "status": status,
            "report_status": RS_FAIL if status == ST_FAIL else RS_NOTEVAL, "counts": n,
            "covered_by": tools, "needs_human": needs_human,
            "procedure": procedures.get(r["anchor"], ""), "procedure_ref": ref,
        })
    return out


# ------------------------------------------------------------------------ render

def cell(s, limit=None):
    s = re.sub(r"\s+", " ", str(s if s is not None else "")).strip()
    if limit and len(s) > limit:
        s = s[: limit - 1].rstrip() + "…"
    return s.replace("|", "\\|")


def code(s, limit=70):
    s = cell(s, limit).replace("`", "'")
    return "`%s`" % s if s else ""


def location(r, roots=None):
    """Location cell for one finding: path relative to the TARGET root (or URL), line, selector."""
    base = rel_path(r.get("file"), roots or []) if r.get("file") else (r.get("url") or "?")
    if r.get("line") not in (None, ""):
        base += ":%s" % r["line"]
        if r.get("col") not in (None, ""):
            base += ":%s" % r["col"]
    if r.get("selector") and (r.get("line") in (None, "") or "wcag_page" in r["tools"]):
        base += " `%s`" % cell(r["selector"], 60).replace("`", "'")
    return cell(base)


def group_location(g, lead, roots=None, max_pages=4):
    """Location cell for a report row; a collapsed row gives pattern × pages (instances) and the pages."""
    if g["instances"] == 1:
        return location(lead, roots)
    pages = g["pages"]
    shown = ", ".join(cell(p) for p in pages[:max_pages])
    if len(pages) > max_pages:
        shown += ", +%d more" % (len(pages) - max_pages)
    if g.get("pattern"):
        head = "`%s`" % cell(g["pattern"], 60).replace("`", "'")
    else:
        head = "page-level"
    return "%s × %d page%s (%d instances): %s" % (head, len(pages), "" if len(pages) == 1 else "s",
                                                  g["instances"], shown)


def evidence(r, n_more=0):
    parts = []
    for s in r["sources"]:
        ev = s.get("evidence") or {}
        bits = []
        for k in ("ratio", "color", "background", "width", "height", "px", "engine"):
            if k in ev and ev[k] not in (None, ""):
                bits.append("%s=%s" % (k, ev[k]))
        parts.append("%s `%s` (%s)%s" % (s.get("tool"), s.get("rule"), s.get("severity"),
                                          (" " + ", ".join(bits)) if bits else ""))
    snip = code(r.get("snippet"))
    text = "; ".join(parts) + ((" — " + snip) if snip else "")
    if n_more:
        text += " (first of %d; all in the JSON)" % (n_more + 1)
    return cell(text)


def fix(r):
    if r["tool_severity"] == "warn":
        pre = "Confirm, then fix per "
    elif r["tool_severity"] == "manual":
        pre = "Check manually per "
    else:
        pre = "Fix per "
    return pre + ("[Understanding %s](%s)" % (r["sc"], r["help"]) if r.get("help") else
                  "the SC's sufficient techniques")


def ref(r):
    if r["check_id"].startswith("WCAG-BP-"):
        return "Best practice (no SC)"
    return "WCAG 2.2 SC %s (Level %s)" % (r["sc"], r["level"] or "?")


def display_target(t):
    """TARGET for the title and Scope line: as given, but an absolute path is shown relative."""
    if not t or is_url(t) or not os.path.isabs(t):
        return t
    rel = os.path.relpath(t)
    return rel if not rel.startswith("..") else os.path.basename(t.rstrip(os.sep)) or t


def strip_roots(text, roots):
    """Make absolute paths under the roots inside free text (tool messages) relative."""
    text = str(text if text is not None else "")
    for root in sorted(roots or [], key=len, reverse=True):
        text = text.replace(root.rstrip(os.sep) + os.sep, "")
    return text


def _plural(n, one, many):
    return "%d %s" % (n, one if n == 1 else many)


def summary_line(result):
    g = result["summary"]["report_rows"]
    sc = result["summary"]["sc_status"]
    n_sc = len(result["coverage"])
    return ("Summary: %s, %s, %s, %s; SC: %d fail (tool), [n] pass, [n] N/A, [n] not evaluated — "
            "%d of %d SC still to be judged (tool severities before review; update after the manual pass)" % (
                _plural(g["nonconformities"], "nonconformity", "nonconformities"),
                _plural(g["deviations"], "deviation", "deviations"),
                _plural(g["advisories"], "advisory", "advisories"),
                _plural(g["review_notes"], "review note", "review notes"),
                sc["fail"], n_sc - sc["fail"], n_sc))


def scope_line(result):
    m = result["meta"]
    roots = m.get("roots") or []
    pages, failed = [], []
    for r in m["runs"]:
        if r.get("tool") == "wcag_page" and r.get("ok"):
            for p in (r.get("meta") or {}).get("pages") or []:
                loc = rel_path(p["file"], roots) if p.get("file") else p.get("url")
                if any(isinstance(e, dict) and e.get("check") == "navigation" for e in p.get("errors") or []):
                    failed.append(loc)
                elif loc and loc not in pages:
                    pages.append(loc)
    if pages or failed:
        shown = ", ".join(pages[:12]) + (", +%d more" % (len(pages) - 12) if len(pages) > 12 else "")
        what = "%s (%s)" % (_plural(len(pages), "page", "pages"), shown)
        if failed:
            what += " + %d not loaded (see Not run)" % len(failed)
    else:
        what = "source `%s` (no rendered pages)" % display_target(m["target"])
    n_sc = len(result["coverage"])
    tools = ", ".join(r["tool"] for r in m["runs"] if r.get("ok")) or "none"
    return ("Scope: %s, processes [list every step, or none], level %s (%d SC; 4.1.1 obsolete), tools %s, "
            "AT/browsers [matrix, or none]" % (what, m["level"], n_sc, tools))


def render_md(result):
    m = result["meta"]
    roots = m.get("roots") or []
    by_n = {r["n"]: r for r in result["findings"]}
    groups = result["report_rows"]
    L = []
    L.append("# WCAG 2.2 Level %s audit — %s" % (m["level"], display_target(m["target"])))
    L.append("")
    L.append(scope_line(result))
    L.append(summary_line(result))
    L.append("Evidence: " + evidence_line(result))
    L.append("")
    L.append("## Findings")
    L.append("")
    L.append("| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for g in groups:
        r = by_n[g["findings"][0]]
        L.append("| %d | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            g["n"], r["severity"], r["check_id"], ref(r), r["target"], group_location(g, r, roots),
            cell(strip_roots(r["message"], roots), 220), strip_roots(evidence(r, g["instances"] - 1), roots),
            fix(r)))
    if not groups:
        L.append("| — | — | — | — | — | — | No tool findings (this is not a conformance claim) | — | — |")
    L.append("")
    L.append("## SC coverage")
    L.append("")
    L.append("Status is Fail where a tool reported a fail, otherwise Not evaluated. After the manual pass, set "
             "each SC to Fail, Pass, N/A (with a reason) or Not evaluated. Tool signal is what the tools saw; "
             "it is never a pass.")
    L.append("")
    L.append("| Check ID | Success criterion | Level | Status | Tool signal | Automated by |")
    L.append("|---|---|---|---|---|---|")
    for c in result["coverage"]:
        L.append("| %s | %s | %s | %s | %s | %s |" % (
            c["check_id"], cell(c["title"]), c["level"], c["report_status"], c["status"],
            ", ".join(c["covered_by"]) or "—"))
    L.append("")
    L.append("## Review notes")
    L.append("")
    for line in review_notes(result):
        L.append("- " + line)
    L.append("")
    L.append("## Manual checks required")
    L.append("")
    L.append("Complete these before any conformance claim. \"Automated checks passed\" means only that the tools "
             "found nothing; tools cover part of each SC.")
    L.append("")
    L.append("| Check ID | Level | First step | Procedure |")
    L.append("|---|---|---|---|")
    for c in result["coverage"]:
        if not c["needs_human"]:
            continue
        L.append("| %s | %s | %s | [%s](%s) |" % (
            c["check_id"], c["level"], cell(c["procedure"], 140) or "—",
            c["procedure_ref"].split("/")[-1], c["procedure_ref"]))
    L.append("")
    L.append("## Not run / not applicable")
    L.append("")
    for line in m["not_run"]:
        L.append("- " + line)
    L.append("")
    L.append("## Assumptions")
    L.append("")
    for line in assumptions(result):
        L.append("- " + line)
    L.append("")
    L.append("## Reproduction")
    L.append("")
    L.append("```sh")
    L.append(m["command"])
    for r in m["runs"]:
        if r.get("command"):
            L.append(r["command"])
    L.append("```")
    L.append("")
    for r in m["runs"]:
        L.append("- " + run_versions(r))
    L.append("- wcag_audit %s, WCAG %s, run %s" % (VERSION, WCAG, m["date"]))
    counted = [c for c in result["coverage"] if any(c["counts"].values())]
    if counted:
        L.append("")
        L.append("## Appendix: raw tool finding counts per SC")
        L.append("")
        L.append("Before grouping. Fail / Warn / Manual / Info are tool severities "
                 "(Nonconformity / Deviation / Review note / Advisory in the Findings table).")
        L.append("")
        L.append("| Check ID | Fail | Warn | Manual | Info |")
        L.append("|---|---|---|---|---|")
        for c in counted:
            n = c["counts"]
            L.append("| %s | %d | %d | %d | %d |" % (c["check_id"], n["fail"], n["warn"], n["manual"], n["info"]))
    return "\n".join(L) + "\n"


def evidence_line(result):
    parts = []
    for r in result["meta"]["runs"]:
        if not r.get("ok"):
            continue
        tm = r.get("meta") or {}
        sev = r.get("by_severity") or {}
        sevs = ", ".join("%d %s" % (sev.get(k, 0), k) for k in ("fail", "warn", "manual", "info"))
        if r["tool"] == "wcag_scan":
            what = "%s files" % tm.get("files_scanned", "?")
        else:
            what = "%d pages" % len(tm.get("pages") or [])
        extra = ""
        n_err = len(r.get("page_errors") or [])
        if n_err:
            extra = ", %s (see Not run)" % _plural(n_err, "page-level error", "page-level errors")
        parts.append("%s %s: %s, %d findings (%s)%s" % (r["tool"], tm.get("version", "?"), what,
                                                        r.get("n_findings", 0), sevs, extra))
    s = result["summary"]
    parts.append("merged: %d tool findings → %d rows (%d merged across tools) → %d report rows "
                 "(repeated patterns collapsed; full list in the JSON)" % (
                     s["tool_findings"], len(result["findings"]), s["merged"], len(result["report_rows"])))
    if not any(r.get("ok") for r in result["meta"]["runs"]):
        parts.insert(0, "no tool ran")
    parts.append("manual checks [keyboard walk, screen reader, zoom/reflow: add what you did]")
    return "; ".join(parts)


def run_versions(r):
    tm = r.get("meta") or {}
    if not r.get("ok"):
        return "%s: not run (%s)" % (r["tool"], r.get("error") or "skipped")
    eng = tm.get("engine") or {}
    extra = ", ".join("%s %s" % (k, v) for k, v in eng.items() if v)
    return "%s %s (WCAG %s)%s, exit %s, meta.date %s" % (
        r["tool"], tm.get("version", "?"), tm.get("wcag", "?"),
        (": " + extra) if extra else "", r.get("exit_code"), tm.get("date", "?"))


def review_notes(result):
    notes = []
    rows = result["report_rows"]
    rn = [r for r in rows if r["tool_severity"] == "manual"]
    dv = [r for r in rows if r["tool_severity"] == "warn"]
    if rn:
        notes.append("Rows %s are manual-check prompts from the tools (Review note): verify each by hand." %
                     _row_list(rn))
    if dv:
        notes.append("Rows %s are Deviations: likely failures that need confirmation (exceptions such as "
                     "large text, the target-size spacing/equivalent exceptions or essential presentation may apply)." %
                     _row_list(dv))
    by_n = {r["n"]: r for r in result["findings"]}
    multi = [g for g in rows if any(len(by_n[n]["tools"]) > 1 for n in g["findings"] if n in by_n)]
    if multi:
        notes.append("Rows %s were reported by more than one tool and merged into one row." % _row_list(multi))
    grouped = [g for g in rows if g["instances"] > 1]
    if grouped:
        notes.append("Rows %s collapse repeated instances of one pattern (same check, SC, severity and "
                     "source line or selector pattern); the JSON findings list every instance." % _row_list(grouped))
    notes.append("Static findings come from source; they can differ from the rendered page "
                 "(CSS cascade, runtime state, framework output). Confirm source-only Deviations in a browser.")
    return notes


def _row_list(rows, limit=25):
    ids = ["#%d" % r["n"] for r in rows]
    return ", ".join(ids[:limit]) + (" and %d more" % (len(ids) - limit) if len(ids) > limit else "")


def assumptions(result):
    m = result["meta"]
    a = [
        "Audit level %s: all Level A%s success criteria of WCAG 2.2 are in scope; 4.1.1 Parsing is obsolete "
        "and treated as not applicable." % (m["level"], {"A": "", "AA": " and AA", "AAA": ", AA and AAA"}[m["level"]]),
        "Severity mapping: tool fail → Nonconformity, warn → Deviation (needs confirmation), "
        "manual → Review note (manual check), info → Advisory.",
        "De-duplication: findings with the same SC and location and the same line, selector or snippet "
        "from different tools are one row; the most severe tool severity is kept.",
        "Target column: page (rendered page, HTML, Markdown), component (JSX/TSX/Vue/Svelte/JS), "
        "stylesheet (CSS/SCSS/Less), template (Nunjucks, ERB, Handlebars and similar), by file extension.",
        "Grouping: rows with the same check, SC, severity and source line or selector pattern (:nth-*() "
        "indexes removed) are one report row with a page list and instance count; the JSON keeps every finding. "
        "Locations are relative to the TARGET root.",
        "Coverage: an SC is \"automated\" by a tool when the scanner has a fail/warn/info rule for it "
        "(wcag_scan --list-rules) or the page runner's envelope lists it (axe_sc_covered and its check groups).",
    ]
    return a


# ------------------------------------------------------------------------ driver

def audit(args, runner=run_json, page_check=page_runner_installed, scan_rules=scanner_rule_sc):
    index = load_index()
    procedures = load_procedures()
    level = args.level
    target = args.target
    runs, not_run, envelopes = [], [], []
    covered = {}
    roots = path_roots(target, args.url)

    # static scan
    if args.no_scan:
        not_run.append("wcag_scan (static scan): skipped by --no-scan")
    elif is_url(target):
        not_run.append("wcag_scan (static scan): TARGET is a URL; pass a source path to scan code")
    elif not os.path.exists(target):
        not_run.append("wcag_scan (static scan): TARGET %s not found" % target)
    else:
        cmd = [sys.executable, SCAN, "--json", "--level", level, target]
        env, code, err = runner(cmd)
        run = {"tool": "wcag_scan", "command": _cmd_str(cmd), "exit_code": code}
        if env is None:
            run.update(ok=False, error=err)
            not_run.append("wcag_scan (static scan): failed — %s" % err)
        else:
            run.update(ok=True, meta=env.get("meta") or {})
            for sc in scan_rules(level):
                covered.setdefault(sc, set()).add("wcag_scan")
            for e in (env.get("meta") or {}).get("errors") or []:
                if isinstance(e, dict) and e.get("file"):
                    e = dict(e, file=rel_path(e["file"], roots))
                not_run.append("wcag_scan skipped/errored on %s" % (
                    e if isinstance(e, str) else json.dumps(e, sort_keys=True)))
            envelopes.append(env)
        runs.append(run)

    # rendered pages
    page_target, reason = None, None
    if args.url:
        page_target = args.url
    elif is_url(target):
        page_target = target
    else:
        page_target, reason = local_page_target(target)
    if args.no_page:
        not_run.append("wcag_page (rendered pages): skipped by --no-page")
    elif page_target is None:
        not_run.append("wcag_page (rendered pages): %s" % reason)
    else:
        ok, detail = page_check()
        if not ok:
            not_run.append("wcag_page (rendered pages): page runner not installed "
                           "(run scripts/setup_page_runner.sh; --check said: %s)" %
                           cell(detail.splitlines()[-1] if detail else "missing", 120))
            runs.append({"tool": "wcag_page", "ok": False, "error": "page runner not installed"})
        else:
            cmd = ["node", PAGE, page_target, "--json", "--level", level]
            if args.pages and args.pages > 1:
                cmd += ["--pages", str(args.pages)]
            if getattr(args, "probe_actions", False):
                cmd.append("--probe-actions")
            if getattr(args, "screenshots", None):
                cmd += ["--screenshots", args.screenshots]
            if getattr(args, "check_timeout", None):
                cmd += ["--check-timeout", str(args.check_timeout)]
            env, code, err = runner(cmd)
            run = {"tool": "wcag_page", "command": _cmd_str(cmd), "exit_code": code}
            if env is None:
                run.update(ok=False, error=err)
                not_run.append("wcag_page (rendered pages): failed — %s" % err)
            else:
                meta = env.get("meta") or {}
                run.update(ok=True, meta=meta)
                for sc in page_coverage(meta):
                    covered.setdefault(sc, set()).add("wcag_page")
                run["page_errors"] = page_errors(meta, roots)
                not_run.extend(page_error_lines(run["page_errors"], roots))
                envelopes.append(env)
            runs.append(run)

    for r, env in zip([r for r in runs if r.get("ok")], envelopes):
        fs = env.get("findings") or []
        r["n_findings"] = len(fs)
        r["by_severity"] = {k: sum(1 for f in fs if f.get("severity") == k) for k in SEV_RANK}

    rows = sort_rows(merge(envelopes, index))
    for i, r in enumerate(rows, 1):
        r["n"] = i
        if r.get("file"):
            r["path"] = rel_path(r["file"], roots)
    report_rows = group_rows(rows, roots)
    # findings for SCs above the chosen level are dropped from coverage but kept as rows
    cov = coverage(index, level, rows, {k: sorted(v) for k, v in covered.items()}, procedures)
    above = sorted({r["sc"] for r in rows if r["sc"] in index and index[r["sc"]]["level"] in LEVEL_RANK
                    and LEVEL_RANK[index[r["sc"]]["level"]] > LEVEL_RANK[level]}, key=sc_key)
    if above:
        not_run.append("Findings for SCs above Level %s (%s) are listed but outside the audit scope." % (
            level, ", ".join(above)))
    not_run.append("WCAG-4.1.1 Parsing: obsolete and removed in WCAG 2.2; not applicable.")
    if LEVEL_RANK[level] < 3:
        not_run.append("Level %s success criteria: out of scope for a Level %s audit." % (
            "AA and AAA" if level == "A" else "AAA", level))

    summary = summarise(rows)
    n_tool = sum(len(e.get("findings") or []) for e in envelopes)
    summary["tool_findings"] = n_tool
    summary["merged"] = sum(len(r["sources"]) - 1 for r in rows)
    summary["coverage"] = {st: sum(1 for c in cov if c["status"] == st)
                           for st in (ST_FAIL, ST_WARN, ST_PASS, ST_MANUAL, ST_NOTRUN)}
    grouped = summarise(report_rows)
    grouped.pop("by_sc", None)
    summary["report_rows"] = grouped
    fails = sum(1 for c in cov if c["report_status"] == RS_FAIL)
    summary["sc_status"] = {"fail": fails, "pass": None, "na": None, "not_evaluated": None,
                            "to_be_judged": len(cov) - fails}
    meta = {
        "tool": "wcag_audit", "version": VERSION, "wcag": WCAG, "target": target, "url": args.url,
        "level": level, "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "command": _cmd_str(["python3", os.path.join("scripts", "wcag_audit.py")] + (args.argv or [])),
        "runs": runs, "not_run": not_run, "roots": roots,
    }
    return {"meta": meta, "summary": summary, "findings": rows, "report_rows": report_rows, "coverage": cov}


def page_errors(meta, roots=None):
    """Page-level errors from the page runner envelope (check timed out, navigation failed, ...)."""
    out = []
    for p in meta.get("pages") or []:
        where = rel_path(p["file"], roots or []) if p.get("file") else (p.get("url") or "?")
        for e in p.get("errors") or []:
            if isinstance(e, str):
                e = {"check": "?", "error": e}
            out.append({"page": where, "check": e.get("check"), "error": e.get("error")})
    for e in meta.get("errors") or []:
        if isinstance(e, str):
            e = {"check": "?", "error": e}
        out.append({"page": e.get("page") or e.get("url") or "run", "check": e.get("check"),
                    "error": e.get("error") or json.dumps(e, sort_keys=True)})
    return out


def page_error_lines(errors, roots=None, max_pages=6):
    """One 'Not run' line per distinct (check, error), listing the pages it hit."""
    groups = {}
    for e in errors:
        k = (str(e.get("check")), cell(strip_roots(e.get("error"), roots), 160))
        groups.setdefault(k, [])
        if e["page"] not in groups[k]:
            groups[k].append(e["page"])
    lines = []
    for (chk, err), pages in groups.items():
        shown = ", ".join(pages[:max_pages]) + (", +%d more" % (len(pages) - max_pages)
                                                if len(pages) > max_pages else "")
        effect = ("page not audited" if chk == "navigation"
                  else "the SC this check covers are not checked on these pages")
        lines.append("wcag_page check `%s` errored on %s: %s — %s" % (chk, shown, err, effect))
    return lines


def _cmd_str(cmd):
    out = []
    for c in cmd:
        if c == sys.executable:
            c = "python3"
        elif isinstance(c, str) and c.startswith(SKILL + os.sep):
            c = os.path.relpath(c, SKILL)
        out.append(c)
    return " ".join(shlex.quote(str(c)) for c in out)


def build_parser():
    p = argparse.ArgumentParser(
        prog="wcag_audit.py",
        description="Run the WCAG 2.2 static scanner and page runner, merge findings, "
                    "and emit an audit report skeleton with an SC coverage table.",
        epilog="Exit codes: 0 = no nonconformities, 1 = nonconformities, 2 = usage or error.")
    p.add_argument("target", metavar="TARGET", help="source directory/file to scan, or a URL")
    p.add_argument("--url", help="rendered URL (or local HTML file/dir) for the page runner")
    p.add_argument("--level", choices=["A", "AA", "AAA"], default="AA", help="audit level (default AA)")
    p.add_argument("--pages", type=int, default=1, help="pages for the page runner to crawl (default 1)")
    p.add_argument("--no-page", action="store_true", help="do not run the page runner")
    p.add_argument("--probe-actions", action="store_true",
                   help="let the page runner activate ordinary buttons on http(s) URLs "
                        "(4.1.3 status probe, dialogs opened by plain buttons); always on for local files")
    p.add_argument("--screenshots", metavar="DIR",
                   help="pass --screenshots DIR to the page runner (page, reflow and failing-focus screenshots)")
    p.add_argument("--check-timeout", metavar="MS", type=int,
                   help="pass --check-timeout MS to the page runner (time budget per check per page, >= 1000)")
    p.add_argument("--no-scan", action="store_true", help="do not run the static scanner")
    p.add_argument("--json", metavar="OUT", help="also write the merged machine-readable result to OUT")
    p.add_argument("--report", choices=["md", "json"], default="md", help="report format (default md)")
    p.add_argument("--out", metavar="FILE", help="write the report to FILE instead of stdout")
    p.add_argument("--version", action="version", version="wcag_audit " + VERSION)
    return p


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    args.argv = argv
    if args.no_scan and args.no_page:
        sys.stderr.write("error: --no-scan and --no-page leave nothing to run\n")
        return 2
    if args.pages < 1:
        sys.stderr.write("error: --pages must be >= 1\n")
        return 2
    if args.check_timeout is not None and args.check_timeout < 1000:
        sys.stderr.write("error: --check-timeout must be >= 1000 (ms)\n")
        return 2
    try:
        result = audit(args)
    except OSError as e:
        sys.stderr.write("error: %s\n" % e)
        return 2
    if not any(r.get("ok") for r in result["meta"]["runs"]):
        sys.stderr.write("error: no tool ran:\n  " + "\n  ".join(result["meta"]["not_run"]) + "\n")
        return 2
    text = render_md(result) if args.report == "md" else json.dumps(result, indent=2) + "\n"
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
            fh.write("\n")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    return 1 if result["summary"]["nonconformities"] else 0


if __name__ == "__main__":
    sys.exit(main())
