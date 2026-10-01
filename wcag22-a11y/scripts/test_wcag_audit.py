#!/usr/bin/env python3
"""Tests for wcag_audit.py (stdlib unittest). Run: python3 scripts/test_wcag_audit.py

Unit tests use synthetic tool envelopes and need no browser. The integration
test runs the real wcag_scan.py on scripts/fixtures (page runner skipped).
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wcag_audit as wa  # noqa: E402

SCRIPT = os.path.join(HERE, "wcag_audit.py")
FIX = os.path.join(HERE, "fixtures")


def f(tool, sc, sev, rule="r", **kw):
    d = {"tool": tool, "sc": sc, "level": "A", "rule": rule, "severity": sev,
         "message": "%s %s" % (rule, sev), "help": "https://example.test/%s" % sc}
    d.update(kw)
    return d


def env(tool, findings, **meta):
    m = {"tool": tool, "version": "9.9.9", "wcag": wa.WCAG, "target": "x", "date": "2026-01-01T00:00:00Z"}
    m.update(meta)
    return {"meta": m, "summary": {}, "findings": findings}


def args(target, **kw):
    a = types.SimpleNamespace(target=target, url=None, level="AA", pages=1, no_page=False,
                              no_scan=False, json=None, report="md", out=None, argv=[target])
    for k, v in kw.items():
        setattr(a, k, v)
    return a


class IndexTests(unittest.TestCase):
    def test_index_has_87_sc(self):
        idx = wa.load_index()
        self.assertEqual(len(idx), 87)
        self.assertEqual(idx["1.4.3"]["level"], "AA")
        self.assertEqual(idx["4.1.1"]["level"], "obsolete")
        self.assertEqual(idx["1.1.1"]["anchor"], "wcag-1-1-1")
        self.assertTrue(idx["1.1.1"]["file"].startswith("sc-1"))

    def test_scope_counts(self):
        idx = wa.load_index()
        self.assertEqual(len(wa.in_scope(idx, "A")), 31)
        self.assertEqual(len(wa.in_scope(idx, "AA")), 55)
        self.assertEqual(len(wa.in_scope(idx, "AAA")), 86)
        self.assertNotIn("4.1.1", [r["sc"] for r in wa.in_scope(idx, "AAA")])

    def test_procedures_extracted(self):
        procs = wa.load_procedures()
        self.assertIn("wcag-1-1-1", procs)
        self.assertTrue(procs["wcag-1-1-1"])

    def test_parse_rule_list(self):
        text = ("RULE SC LEVEL SEV DESCRIPTION\n"
                "img-missing-alt 1.1.1 A fail x\n"
                "contrast-unresolved 1.4.3 AA manual y\n"
                "focus-app 2.4.13 AAA warn z\n"
                "redundant 3.3.7 A info q\n")
        self.assertEqual(wa.parse_rule_list(text, "AA"), {"1.1.1", "3.3.7"})
        self.assertEqual(wa.parse_rule_list(text, "AAA"), {"1.1.1", "3.3.7", "2.4.13"})


class MergeTests(unittest.TestCase):
    def test_cross_tool_dedup_on_line(self):
        a = env("wcag_scan", [f("wcag_scan", "1.1.1", "fail", "img-missing-alt", file="p.html", line=3,
                                snippet='<img src="a.png">')])
        b = env("wcag_page", [f("wcag_page", "1.1.1", "fail", "axe-image-alt", file="p.html", line=3,
                                selector="img")])
        rows = wa.merge([a, b])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["tools"], ["wcag_page", "wcag_scan"])
        self.assertEqual(len(rows[0]["sources"]), 2)

    def test_cross_tool_dedup_on_snippet_whitespace(self):
        a = env("wcag_scan", [f("wcag_scan", "3.1.1", "fail", file="p.html", line=2, snippet="<html>")])
        b = env("wcag_page", [f("wcag_page", "3.1.1", "fail", file="p.html", selector="html",
                                snippet="  <HTML>\n")])
        self.assertEqual(len(wa.merge([a, b])), 1)

    def test_cross_tool_dedup_on_selector(self):
        a = env("wcag_scan", [f("wcag_scan", "1.4.3", "warn", file="s.css", line=4, selector=".hint")])
        b = env("wcag_page", [f("wcag_page", "1.4.3", "fail", file="s.css", selector=".hint")])
        rows = wa.merge([a, b])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["tool_severity"], "fail")
        self.assertEqual(rows[0]["severity"], "Nonconformity")
        self.assertEqual(rows[0]["line"], 4)

    def test_no_merge_different_sc_or_location(self):
        a = env("wcag_scan", [f("wcag_scan", "1.1.1", "fail", file="p.html", line=3)])
        b = env("wcag_page", [f("wcag_page", "4.1.2", "fail", file="p.html", line=3),
                              f("wcag_page", "1.1.1", "fail", file="q.html", line=3)])
        self.assertEqual(len(wa.merge([a, b])), 3)

    def test_no_merge_conflicting_lines(self):
        a = env("wcag_scan", [f("wcag_scan", "1.1.1", "fail", file="p.html", line=3, selector="img"),
                              f("wcag_scan", "1.1.1", "fail", file="p.html", line=9, selector="img")])
        b = env("wcag_page", [f("wcag_page", "1.1.1", "fail", file="p.html", line=9, selector="img")])
        rows = wa.merge([a, b])
        self.assertEqual(len(rows), 2)
        merged = [r for r in rows if len(r["tools"]) == 2]
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["line"], 9)

    def test_same_tool_distinct_findings_not_merged(self):
        a = env("wcag_scan", [f("wcag_scan", "1.1.1", "fail", "img-missing-alt", file="p.html", line=3),
                              f("wcag_scan", "1.1.1", "fail", "button-icon-no-name", file="p.html", line=3)])
        self.assertEqual(len(wa.merge([a])), 2)

    def test_exact_duplicates_collapse(self):
        x = f("wcag_scan", "1.1.1", "fail", file="p.html", line=3)
        rows = wa.merge([env("wcag_scan", [x, dict(x)])])
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]["sources"]), 1)

    def test_url_fragment_normalised(self):
        a = env("wcag_page", [f("wcag_page", "2.4.4", "fail", url="https://e.test/a#x", selector="a")])
        b = env("wcag_other", [f("wcag_other", "2.4.4", "fail", url="https://e.test/a", selector="a")])
        self.assertEqual(len(wa.merge([a, b])), 1)

    def test_tool_defaults_from_meta_and_id_fallback(self):
        rows = wa.merge([env("wcag_scan", [{"id": "WCAG-2.4.2", "severity": "fail", "file": "p.html", "line": 1}])])
        self.assertEqual(rows[0]["tools"], ["wcag_scan"])
        self.assertEqual(rows[0]["sc"], "2.4.2")
        self.assertEqual(rows[0]["check_id"], "WCAG-2.4.2")


class SeverityTests(unittest.TestCase):
    def test_mapping(self):
        idx = wa.load_index()
        e = env("wcag_scan", [f("wcag_scan", "1.1.1", s, file="p.html", line=i)
                              for i, s in enumerate(["fail", "warn", "manual", "info"], 1)])
        rows = {r["tool_severity"]: r["severity"] for r in wa.merge([e], idx)}
        self.assertEqual(rows, {"fail": "Nonconformity", "warn": "Deviation",
                                "manual": "Review note", "info": "Advisory"})
        s = wa.summarise(wa.merge([e], idx))
        self.assertEqual((s["nonconformities"], s["deviations"], s["advisories"], s["review_notes"]),
                         (1, 1, 1, 1))

    def test_unknown_severity_is_advisory(self):
        rows = wa.merge([env("t", [f("t", "1.1.1", "bogus", file="p.html", line=1)])])
        self.assertEqual(rows[0]["severity"], "Advisory")

    def test_best_practice_check_id(self):
        self.assertEqual(wa.check_id("BP-landmark"), "WCAG-BP-landmark")
        self.assertEqual(wa.check_id("2.5.8"), "WCAG-2.5.8")

    def test_target_kind(self):
        self.assertEqual(wa.target_kind({"file": "a.scss"}), "stylesheet")
        self.assertEqual(wa.target_kind({"file": "a.tsx"}), "component")
        self.assertEqual(wa.target_kind({"file": "a.njk"}), "template")
        self.assertEqual(wa.target_kind({"file": "a.html"}), "page")
        self.assertEqual(wa.target_kind({"tool": "wcag_page", "file": "a.css"}), "page")

    def test_sort_by_severity_then_sc(self):
        """SKILL.md: rank by severity, then by SC order."""
        rows = wa.merge([env("t", [f("t", "1.1.1", "warn", file="a", line=1),
                                   f("t", "2.4.7", "fail", file="a", line=2),
                                   f("t", "1.1.1", "info", file="a", line=3),
                                   f("t", "2.4.7", "warn", file="a", line=4),
                                   f("t", "1.4.3", "fail", file="a", line=5)])])
        order = [(r["sc"], r["tool_severity"]) for r in wa.sort_rows(rows)]
        self.assertEqual(order, [("1.4.3", "fail"), ("2.4.7", "fail"), ("1.1.1", "warn"), ("2.4.7", "warn"),
                                 ("1.1.1", "info")])


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.idx = wa.load_index()

    def cov(self, findings, covered, level="AA"):
        rows = wa.merge([env("t", findings)], self.idx)
        return {c["sc"]: c for c in wa.coverage(self.idx, level, rows, covered, wa.load_procedures())}

    def test_statuses(self):
        c = self.cov([f("t", "1.1.1", "fail", file="a", line=1),
                      f("t", "1.3.1", "warn", file="a", line=2),
                      f("t", "2.4.11", "manual", file="a", line=3)],
                     {"1.1.1": ["t"], "1.3.1": ["t"], "3.1.1": ["t"]})
        self.assertEqual(c["1.1.1"]["status"], wa.ST_FAIL)
        self.assertEqual(c["1.3.1"]["status"], wa.ST_WARN)
        self.assertEqual(c["3.1.1"]["status"], wa.ST_PASS)
        self.assertEqual(c["1.2.1"]["status"], wa.ST_MANUAL)
        self.assertEqual(c["2.4.11"]["status"], wa.ST_MANUAL)
        self.assertEqual(c["2.4.11"]["counts"]["manual"], 1)
        self.assertEqual(c["1.4.3"]["status"], wa.ST_NOTRUN)  # automated SC, nothing ran
        self.assertEqual(len(c), 55)
        self.assertNotIn("1.4.6", c)

    def test_needs_human_and_pointer(self):
        c = self.cov([], {"3.1.1": ["t"], "1.1.1": ["t"]})
        self.assertFalse(c["3.1.1"]["needs_human"])  # automated + passed
        self.assertTrue(c["1.1.1"]["needs_human"])   # assisted: partial coverage
        self.assertTrue(c["1.2.1"]["needs_human"])
        self.assertTrue(c["1.1.1"]["procedure_ref"].endswith("sc-1-perceivable.md#wcag-1-1-1"))
        self.assertTrue(c["1.1.1"]["procedure"])

    def test_level_a_and_aaa(self):
        self.assertEqual(len(self.cov([], {}, "A")), 31)
        self.assertEqual(len(self.cov([], {}, "AAA")), 86)

    def test_page_coverage_from_meta(self):
        cov = wa.page_coverage({"checks": ["axe", "reflow", "target-size"], "axe_sc_covered": ["1.1.1"]})
        self.assertEqual(cov, {"1.1.1", "1.4.10", "2.5.8"})
        cov = wa.page_coverage({"checks": ["reflow"], "checks_sc": {"reflow": ["1.4.10", "1.4.4"]}})
        self.assertEqual(cov, {"1.4.10", "1.4.4"})
        # sc_covered alone is authoritative too: no fallback expansion from "checks"
        cov = wa.page_coverage({"checks": ["focus"], "sc_covered": ["2.4.7"]})
        self.assertEqual(cov, {"2.4.7"})
        # fallback (old envelopes) knows the newer check groups
        cov = wa.page_coverage({"checks": ["non-text-contrast", "auto-update", "status-messages", "dialogs"]})
        self.assertEqual(cov, {"1.4.11", "2.2.2", "4.1.3", "2.1.2"})

    def test_fallback_map_matches_page_runner_checks(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "wcag_page.mjs")).read()
        block = re.search(r"export const CHECKS = \{(.*?)\n\};", src, re.S).group(1)
        js = {}
        for name, body in re.findall(r"'([\w-]+)':\s*(null|\[[^\]]*\])", block):
            if body != "null":
                js[name] = re.findall(r"'([\d.]+)'", body)
        self.assertEqual(js, wa.PAGE_CHECK_SC)


class AuditDriverTests(unittest.TestCase):
    """audit() with injected runners: no subprocesses, no browser."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="wcagaudit")
        self.html = os.path.join(self.tmp, "index.html")
        with open(self.html, "w") as fh:
            fh.write("<html><img src=a.png></html>")

    def runner(self, cmd):
        if cmd[0] == "node":
            return env("wcag_page", [f("wcag_page", "1.1.1", "fail", "image-alt", file=self.html, line=1,
                                       selector="img"),
                                     f("wcag_page", "2.5.8", "warn", "target-size", file=self.html,
                                       selector="button")],
                       checks=["axe", "target-size"], axe_sc_covered=["1.1.1"],
                       engine={"playwright": "1.0", "axe": "4.0"}, pages=[{"file": self.html}]), 1, None
        return env("wcag_scan", [f("wcag_scan", "1.1.1", "fail", "img-missing-alt", file=self.html, line=1,
                                   snippet="<img src=a.png>")], files_scanned=1, errors=[]), 1, None

    def test_probe_actions_passed_to_page_runner(self):
        seen = []
        def runner(cmd):
            seen.append(cmd)
            return self.runner(cmd)
        wa.audit(args(self.tmp, url="https://example.org/"), runner=runner, page_check=lambda: (True, "ok"),
                 scan_rules=lambda lvl: {"1.1.1"})
        page = [c for c in seen if c[0] == "node"][0]
        self.assertNotIn("--probe-actions", page)
        seen.clear()
        wa.audit(args(self.tmp, url="https://example.org/", probe_actions=True), runner=runner,
                 page_check=lambda: (True, "ok"), scan_rules=lambda lvl: {"1.1.1"})
        page = [c for c in seen if c[0] == "node"][0]
        self.assertIn("--probe-actions", page)

    def test_both_tools_merged(self):
        res = wa.audit(args(self.tmp), runner=self.runner, page_check=lambda: (True, "ok"),
                       scan_rules=lambda lvl: {"1.1.1"})
        self.assertEqual([r["tool"] for r in res["meta"]["runs"]], ["wcag_scan", "wcag_page"])
        self.assertEqual(len(res["findings"]), 2)
        self.assertEqual(res["summary"]["merged"], 1)
        self.assertEqual(res["summary"]["nonconformities"], 1)
        cov = {c["sc"]: c for c in res["coverage"]}
        self.assertEqual(cov["1.1.1"]["covered_by"], ["wcag_page", "wcag_scan"])
        self.assertEqual(cov["2.5.8"]["status"], wa.ST_WARN)

    def test_page_runner_not_installed(self):
        res = wa.audit(args(self.tmp), runner=self.runner, page_check=lambda: (False, "chromium: MISSING"),
                       scan_rules=lambda lvl: set())
        self.assertTrue(any("page runner not installed" in n for n in res["meta"]["not_run"]))
        self.assertEqual(len(res["findings"]), 1)
        md = wa.render_md(res)
        self.assertIn("page runner not installed", md)

    def test_no_scan_and_url(self):
        res = wa.audit(args("https://example.test/", no_scan=False), runner=self.runner,
                       page_check=lambda: (True, ""), scan_rules=lambda lvl: set())
        self.assertTrue(any("TARGET is a URL" in n for n in res["meta"]["not_run"]))
        self.assertEqual([r["tool"] for r in res["meta"]["runs"]], ["wcag_page"])

    def test_no_page_flag_and_non_html_dir(self):
        res = wa.audit(args(self.tmp, no_page=True), runner=self.runner, page_check=lambda: (True, ""),
                       scan_rules=lambda lvl: set())
        self.assertTrue(any("--no-page" in n for n in res["meta"]["not_run"]))
        d = tempfile.mkdtemp(prefix="wcagaudit")
        res = wa.audit(args(d), runner=self.runner, page_check=lambda: (True, ""), scan_rules=lambda lvl: set())
        self.assertTrue(any("no top-level *.html" in n for n in res["meta"]["not_run"]))

    def test_tool_failure_recorded(self):
        res = wa.audit(args(self.tmp, no_page=True), runner=lambda cmd: (None, 2, "boom"),
                       page_check=lambda: (True, ""), scan_rules=lambda lvl: set())
        self.assertTrue(any("failed — boom" in n for n in res["meta"]["not_run"]))
        self.assertFalse(res["meta"]["runs"][0]["ok"])


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="wcagaudit")
        run = AuditDriverTests.runner
        holder = types.SimpleNamespace(html=os.path.join(self.tmp, "index.html"))
        with open(holder.html, "w") as fh:
            fh.write("<html></html>")
        self.res = wa.audit(args(self.tmp), runner=lambda cmd: run(holder, cmd),
                            page_check=lambda: (True, ""), scan_rules=lambda lvl: {"1.1.1", "3.1.1"})
        self.md = wa.render_md(self.res)

    def test_sections_in_order(self):
        heads = ["# WCAG 2.2 Level AA audit — ", "Scope: ",
                 "Summary: 1 nonconformity, 1 deviation, 0 advisories, 0 review notes; SC: ",
                 "Evidence: ", "## Findings", "## SC coverage", "## Review notes", "## Manual checks required",
                 "## Not run / not applicable", "## Assumptions", "## Reproduction"]
        pos = [self.md.find(h) for h in heads]
        self.assertTrue(all(p >= 0 for p in pos), pos)
        self.assertEqual(pos, sorted(pos))

    def test_findings_table(self):
        self.assertIn("| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |", self.md)
        self.assertIn("| 1 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page |", self.md)
        self.assertIn("wcag_page `image-alt` (fail)", self.md)
        self.assertIn("wcag_scan `img-missing-alt` (fail)", self.md)
        self.assertIn("Deviation | WCAG-2.5.8 | WCAG 2.2 SC 2.5.8 (Level AA)", self.md)

    def test_evidence_and_reproduction(self):
        self.assertIn("wcag_scan 9.9.9: 1 files, 1 findings", self.md)
        self.assertIn("wcag_page 9.9.9: 1 pages, 2 findings", self.md)
        self.assertIn("(1 merged across tools)", self.md)
        self.assertIn("python3 scripts/wcag_scan.py --json --level AA", self.md)
        self.assertIn("node scripts/wcag_page.mjs", self.md)
        self.assertIn("playwright 1.0", self.md)

    def test_manual_checks_and_coverage(self):
        self.assertIn("| WCAG-1.2.1 | A | List all prerecorded", self.md)
        self.assertIn("(references/sc-1-perceivable.md#wcag-1-2-1)", self.md)
        manual = self.md.split("## Manual checks required")[1].split("## Not run")[0]
        self.assertNotIn("| WCAG-3.1.1 |", manual)  # automated + passed needs no human
        self.assertIn("| WCAG-3.1.1 | Language of Page | A | Not evaluated | automated checks passed", self.md)

    def test_pipe_escaping(self):
        self.assertEqual(wa.cell("a|b\nc"), "a\\|b c")
        self.assertEqual(wa.code("x`y"), "`x'y`")

    def test_json_serialisable(self):
        json.dumps(self.res)


class ReportFormatTests(unittest.TestCase):
    """The Markdown skeleton follows SKILL.md's report format (items 1-5, 8 of the format review)."""

    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="wcagaudit"))
        os.makedirs(os.path.join(self.tmp, "css"))
        self.css = os.path.join(self.tmp, "css", "site.css")
        self.pages = [os.path.join(self.tmp, "p%02d.html" % i) for i in range(11)]
        for path in [self.css] + self.pages:
            with open(path, "w") as fh:
                fh.write("x")

    def page_env(self, errors=None):
        fs = []
        for p in self.pages:
            for k in range(1, 8):
                fs.append(f("wcag_page", "2.4.7", "fail", "focus-not-visible", file=p,
                            selector="html > body > nav.site-nav > ul > li:nth-of-type(%d) > a" % k))
        fs.append(f("wcag_page", "2.4.7", "warn", "focus-indicator-faint", file=self.pages[0],
                    selector="html > body > nav.site-nav > ul > li:nth-of-type(1) > a"))
        pages = [{"file": p} for p in self.pages]
        for i, e in (errors or {}).items():
            pages[i]["errors"] = e
        return env("wcag_page", fs, checks=["focus"], checks_sc={"focus": ["2.4.7"]}, pages=pages)

    def scan_env(self):
        return env("wcag_scan", [f("wcag_scan", "2.4.7", "fail", "focus-outline-removed", file=self.css, line=52,
                                   col=3, snippet="a:focus{outline:none}"),
                                 f("wcag_scan", "1.4.3", "warn", "contrast-css", file=self.css, line=60),
                                 f("wcag_scan", "1.4.3", "warn", "contrast-css", file=self.css, line=61),
                                 f("wcag_scan", "3.3.7", "manual", "redundant", file=self.pages[1], line=4,
                                   message="Same field as on %s: re-entry" % self.pages[0]),
                                 f("wcag_scan", "BP-heading-order", "info", "heading-skip", file=self.pages[2],
                                   line=9)],
                   files_scanned=12, errors=[])

    def run_audit(self, errors=None, **kw):
        page_env, scan_env = self.page_env(errors), self.scan_env()

        def runner(cmd):
            return (page_env if cmd[0] == "node" else scan_env), 1, None
        a = args(self.tmp, pages=12, **kw)
        return wa.audit(a, runner=runner, page_check=lambda: (True, ""), scan_rules=lambda lvl: {"2.4.7", "1.4.3"})

    def head(self, md):
        return md.split("\n## Findings")[0]

    # 1. order and header lines
    def test_header_lines_in_skill_order(self):
        md = wa.render_md(self.run_audit())
        lines = md.splitlines()
        self.assertTrue(lines[0].startswith("# WCAG 2.2 Level AA audit — "))
        self.assertEqual(lines[1], "")
        self.assertTrue(lines[2].startswith("Scope: 11 pages (p00.html, p01.html"), lines[2])
        self.assertTrue(lines[3].startswith("Summary: "), lines[3])
        self.assertTrue(lines[4].startswith("Evidence: "), lines[4])
        scope = lines[2]
        for part in (", processes [", ", level AA (55 SC; 4.1.1 obsolete), tools wcag_scan, wcag_page, ",
                     "AT/browsers ["):
            self.assertIn(part, scope)
        self.assertIn("wcag_scan 9.9.9: 12 files, 5 findings (1 fail, 2 warn, 1 manual, 1 info)", lines[4])
        heads = ["## Findings", "## SC coverage", "## Review notes", "## Manual checks required",
                 "## Not run / not applicable", "## Assumptions", "## Reproduction"]
        pos = [md.find("\n" + h + "\n") for h in heads]
        self.assertTrue(all(p > 0 for p in pos), pos)
        self.assertEqual(pos, sorted(pos))

    def test_scope_without_pages_names_source(self):
        res = self.run_audit(no_page=True)
        self.assertIn("Scope: source `%s` (no rendered pages), processes" % wa.display_target(self.tmp),
                      wa.render_md(res))
        self.assertEqual(wa.display_target("src"), "src")
        self.assertEqual(wa.display_target("https://e.test/"), "https://e.test/")

    # 2. summary: severity counts and SC status counts
    def test_summary_counts(self):
        res = self.run_audit()
        line = [x for x in wa.render_md(res).splitlines() if x.startswith("Summary: ")][0]
        # report rows: 2.4.7 fail nav pattern, 2.4.7 fail css:52, 2 x 1.4.3 warn, 2.4.7 warn, 3.3.7, BP
        self.assertTrue(line.startswith("Summary: 2 nonconformities, 3 deviations, 1 advisory, 1 review note; "
                                        "SC: 1 fail (tool), [n] pass, [n] N/A, [n] not evaluated — "
                                        "54 of 55 SC still to be judged"), line)
        s = res["summary"]
        self.assertEqual(s["sc_status"]["fail"], 1)
        self.assertEqual(s["sc_status"]["to_be_judged"], 54)
        self.assertIsNone(s["sc_status"]["pass"])
        self.assertEqual(s["report_rows"]["nonconformities"], 2)
        self.assertEqual(s["nonconformities"], 78)  # raw findings still counted in the JSON

    # 3. SC coverage uses the SKILL.md status vocabulary; raw counts move to an appendix
    def test_coverage_vocabulary_and_appendix(self):
        res = self.run_audit()
        md = wa.render_md(res)
        cov = md.split("## SC coverage")[1].split("## Review notes")[0]
        self.assertIn("| Check ID | Success criterion | Level | Status | Tool signal | Automated by |", cov)
        self.assertNotIn("F/W/R/A", md)
        statuses = set()
        for line in cov.splitlines():
            if line.startswith("| WCAG-"):
                statuses.add(line.split("|")[4].strip())
        self.assertEqual(statuses, {"Fail", "Not evaluated"})
        self.assertIn("| WCAG-2.4.7 | Focus Visible | AA | Fail | failures found |", cov)
        self.assertIn("| WCAG-1.4.3 | Contrast (Minimum) | AA | Not evaluated | warnings |", cov)
        self.assertEqual({c["report_status"] for c in res["coverage"]}, {wa.RS_FAIL, wa.RS_NOTEVAL})
        appendix = md.split("## Appendix: raw tool finding counts per SC")[1]
        self.assertIn("| WCAG-2.4.7 | 78 | 1 | 0 | 0 |", appendix)
        self.assertIn("| WCAG-1.4.3 | 0 | 2 | 0 | 0 |", appendix)
        self.assertLess(md.find("## Reproduction"), md.find("## Appendix"))

    # 4. locations relative to the TARGET root
    def test_locations_relative_to_target(self):
        res = self.run_audit(errors={3: [{"check": "focus", "error": "timed out after 120s"}]})
        md = wa.render_md(res)
        self.assertNotIn(self.tmp, md.split("## Reproduction")[0])
        self.assertIn(self.head(md).splitlines()[0].split(" — ")[1], (os.path.basename(self.tmp),
                                                                      os.path.relpath(self.tmp)))
        self.assertIn("| stylesheet | css/site.css:52:3 |", md)
        self.assertIn("Same field as on p00.html: re-entry", md)  # paths inside tool messages too
        self.assertIn("p03.html", md.split("## Not run")[1])
        by_file = {r["path"] for r in res["findings"] if r.get("path")}
        self.assertIn("css/site.css", by_file)

    def test_rel_path(self):
        roots = wa.path_roots(self.tmp)
        self.assertEqual(wa.rel_path(self.css, roots), os.path.join("css", "site.css"))
        self.assertEqual(wa.rel_path("https://e.test/a", roots), "https://e.test/a")
        outside = os.path.join(os.path.dirname(self.tmp), "other.html")
        self.assertFalse(os.path.isabs(wa.rel_path(outside, roots)))
        # a file TARGET roots at its directory; a local --url dir is a second root
        self.assertEqual(wa.rel_path(self.css, wa.path_roots(self.css)), "site.css")
        site = os.path.realpath(tempfile.mkdtemp(prefix="wcagsite"))
        roots = wa.path_roots(self.tmp, site)
        self.assertEqual(wa.rel_path(os.path.join(site, "index.html"), roots), "index.html")

    # 5. grouping of repeated patterns across pages
    def test_sel_pattern(self):
        self.assertEqual(wa.sel_pattern("html > body > ul > li:nth-of-type(3) > a"), "ul > li > a")
        self.assertEqual(wa.sel_pattern(".event:nth-child(4)>.meta"), ".event > .meta")
        self.assertEqual(wa.sel_pattern("#email"), "#email")

    def test_grouping_collapses_pages(self):
        res = self.run_audit()
        md = wa.render_md(res)
        self.assertEqual(len(res["findings"]), 83)          # JSON keeps every instance
        self.assertEqual(len(res["report_rows"]), 7)
        nav = [g for g in res["report_rows"] if g["pattern"] == "nav.site-nav > ul > li > a"
               and g["tool_severity"] == "fail"]
        self.assertEqual(len(nav), 1)
        self.assertEqual(nav[0]["instances"], 77)
        self.assertEqual(len(nav[0]["pages"]), 11)
        self.assertEqual(len(nav[0]["findings"]), 77)
        self.assertIn("`nav.site-nav > ul > li > a` × 11 pages (77 instances): p00.html, p01.html, p02.html, "
                      "p03.html, +7 more", md)
        self.assertIn("(first of 77; all in the JSON)", md)
        # different severity or different source line: not collapsed
        faint = [g for g in res["report_rows"] if g["tool_severity"] == "warn" and g["sc"] == "2.4.7"]
        self.assertEqual(len(faint), 1)
        self.assertEqual(len([g for g in res["report_rows"] if g["sc"] == "1.4.3"]), 2)
        # report rows are numbered 1..N in the Findings table
        table = md.split("## Findings")[1].split("## SC coverage")[0]
        nums = [int(l.split("|")[1]) for l in table.splitlines() if re.match(r"\| \d+ \|", l)]
        self.assertEqual(nums, list(range(1, 8)))
        self.assertIn("collapse repeated instances", md)
        json.dumps(res)

    def test_grouping_shrinks_report(self):
        res = self.run_audit()
        grouped = len(wa.render_md(res))
        res["report_rows"] = [dict(n=i, findings=[r["n"]], instances=1, pages=[r.get("path")], pattern=None,
                                   tool_severity=r["tool_severity"], severity=r["severity"],
                                   check_id=r["check_id"], sc=r["sc"])
                              for i, r in enumerate(res["findings"], 1)]
        self.assertLess(grouped * 1.5, len(wa.render_md(res)))

    # 8. page-level errors still reach the skeleton
    def test_page_errors_shown(self):
        errs = {i: [{"check": "focus", "error": "timed out after 120s"}] for i in (2, 5, 7)}
        errs[9] = [{"check": "navigation", "error": "HTTP 404 for http://127.0.0.1:1/x"}]
        res = self.run_audit(errors=errs)
        md = wa.render_md(res)
        notrun = md.split("## Not run / not applicable")[1].split("## Assumptions")[0]
        self.assertIn("wcag_page check `focus` errored on p02.html, p05.html, p07.html: timed out after 120s", notrun)
        self.assertIn("wcag_page check `navigation` errored on p09.html: HTTP 404", notrun)
        self.assertIn("— page not audited", notrun)
        self.assertTrue(md.splitlines()[2].startswith("Scope: 10 pages (p00.html"), md.splitlines()[2])
        self.assertIn("p10.html) + 1 not loaded (see Not run), processes", md.splitlines()[2])
        self.assertIn("4 page-level errors (see Not run)", md.splitlines()[4])
        page_run = [r for r in res["meta"]["runs"] if r["tool"] == "wcag_page"][0]
        self.assertEqual(len(page_run["page_errors"]), 4)


class PassThroughTests(unittest.TestCase):
    """--screenshots and --check-timeout reach wcag_page.mjs (items 6 and 7)."""

    def page_cmd(self, **kw):
        seen = []

        def runner(cmd):
            seen.append(cmd)
            return env(cmd[0] == "node" and "wcag_page" or "wcag_scan", []), 0, None
        wa.audit(args("https://example.test/", **kw), runner=runner, page_check=lambda: (True, ""),
                 scan_rules=lambda lvl: set())
        return [c for c in seen if c[0] == "node"][0]

    def test_screenshots(self):
        self.assertNotIn("--screenshots", self.page_cmd())
        cmd = self.page_cmd(screenshots="shots")
        self.assertEqual(cmd[cmd.index("--screenshots") + 1], "shots")

    def test_check_timeout(self):
        self.assertNotIn("--check-timeout", self.page_cmd())
        cmd = self.page_cmd(check_timeout=45000)
        self.assertEqual(cmd[cmd.index("--check-timeout") + 1], "45000")

    def test_parser_and_validation(self):
        a = wa.build_parser().parse_args(["x", "--screenshots", "d", "--check-timeout", "5000"])
        self.assertEqual((a.screenshots, a.check_timeout), ("d", 5000))
        p = subprocess.run([sys.executable, SCRIPT, FIX, "--check-timeout", "10"], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("--check-timeout", p.stderr)
        self.assertIn("--screenshots DIR", wa.build_parser().format_help())


class CliTests(unittest.TestCase):
    def run_cli(self, *argv):
        return subprocess.run([sys.executable, SCRIPT] + list(argv), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, universal_newlines=True, timeout=600)

    def test_usage_errors(self):
        self.assertEqual(self.run_cli().returncode, 2)
        self.assertEqual(self.run_cli(FIX, "--no-scan", "--no-page").returncode, 2)
        self.assertEqual(self.run_cli(FIX, "--level", "B").returncode, 2)
        self.assertEqual(self.run_cli(FIX, "--pages", "0").returncode, 2)

    def test_integration_fixtures(self):
        """Real wcag_scan.py on scripts/fixtures; page runner skipped."""
        out = tempfile.mkdtemp(prefix="wcagaudit")
        jpath, mpath = os.path.join(out, "a.json"), os.path.join(out, "a.md")
        p = self.run_cli(FIX, "--no-page", "--json", jpath, "--out", mpath)
        self.assertEqual(p.returncode, 1, p.stderr)
        self.assertEqual(p.stdout, "")
        with open(jpath) as fh:
            res = json.load(fh)
        with open(mpath) as fh:
            md = fh.read()
        self.assertTrue(md.startswith("# WCAG 2.2 Level AA audit — "))
        self.assertGreater(res["summary"]["nonconformities"], 0)
        self.assertEqual(len(res["coverage"]), 55)
        run = res["meta"]["runs"][0]
        self.assertEqual(run["tool"], "wcag_scan")
        self.assertTrue(run["ok"])
        self.assertEqual(run["n_findings"], res["summary"]["tool_findings"])
        kinds = {r["target"] for r in res["findings"]}
        self.assertTrue({"page", "component", "stylesheet", "template"} <= kinds, kinds)
        statuses = {c["status"] for c in res["coverage"]}
        self.assertTrue({wa.ST_FAIL, wa.ST_MANUAL} <= statuses)
        self.assertIn("wcag_page (rendered pages): skipped by --no-page", md)
        findings = md.split("## Findings")[1].split("## SC coverage")[0]
        self.assertNotIn(FIX, findings)  # Location paths are relative to TARGET
        self.assertRegex(findings, r"\| stylesheet \| css/[\w.-]+\.css:\d+")
        # scanner-only: every fail finding in the scanner output is a Nonconformity row
        scan = subprocess.run([sys.executable, os.path.join(HERE, "wcag_scan.py"), "--json", FIX],
                              stdout=subprocess.PIPE, universal_newlines=True)
        n_fail = sum(1 for x in json.loads(scan.stdout)["findings"] if x["severity"] == "fail")
        self.assertEqual(res["summary"]["nonconformities"], n_fail)

    def test_report_json_stdout(self):
        p = self.run_cli(os.path.join(FIX, "css", "good.css"), "--no-page", "--report", "json")
        self.assertIn(p.returncode, (0, 1), p.stderr)
        res = json.loads(p.stdout)
        self.assertEqual(res["meta"]["tool"], "wcag_audit")

    @unittest.skipUnless(os.environ.get("WCAG_AUDIT_PAGE") == "1" and wa.page_runner_installed()[0],
                         "set WCAG_AUDIT_PAGE=1 with the page runner installed")
    def test_integration_page_runner(self):
        p = self.run_cli(os.path.join(FIX, "html"), "--report", "json")
        res = json.loads(p.stdout)
        self.assertEqual([r["tool"] for r in res["meta"]["runs"] if r["ok"]], ["wcag_scan", "wcag_page"])
        self.assertGreater(res["summary"]["merged"], 0)

class TestNonUtf8Stdout(unittest.TestCase):
    """Windows pipes default to cp1252: the Markdown report on stdout must not raise."""

    def test_markdown_report_to_cp1252_stdout(self):
        env = dict(os.environ, PYTHONIOENCODING="cp1252")
        env.pop("PYTHONUTF8", None)
        target = os.path.join(HERE, "..", "evals", "fixtures", "brightwater", "project")
        cp = subprocess.run([sys.executable, SCRIPT, target, "--no-page"], capture_output=True, env=env)
        self.assertNotIn(b"UnicodeEncodeError", cp.stderr)
        self.assertIn(cp.returncode, (0, 1))
        self.assertIn(b"## Findings", cp.stdout)



if __name__ == "__main__":
    unittest.main(verbosity=1)
