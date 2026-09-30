#!/usr/bin/env python3
"""Unit tests for tools/revalidate.py. No test touches the network: every fetch is mocked.

Run: python3 -m unittest discover -s tools -p "test_*.py"
"""

import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import revalidate as rv  # noqa: E402

RESPEC_HEAD = """<!DOCTYPE html><html><head><title>Web Content Accessibility Guidelines (WCAG) 2.2</title></head>
<body><div class="head"><h1>Web Content Accessibility Guidelines (WCAG) 2.2</h1>
<p id="w3c-state"><a href="https://www.w3.org/standards/types#REC">W3C Recommendation</a>
<time class="dt-published" datetime="2024-12-12">12 December 2024</time></p>
<details open><summary>More details about this document</summary><dl>
<dt>This version:</dt><dd><a class="u-url" href="https://www.w3.org/TR/2024/REC-WCAG22-20241212/">https://www.w3.org/TR/2024/REC-WCAG22-20241212/</a></dd>
<dt>Latest published version:</dt><dd><a href="https://www.w3.org/TR/WCAG22/">https://www.w3.org/TR/WCAG22/</a></dd>
<dt>Errata:</dt><dd><a href="https://www.w3.org/WAI/WCAG22/errata/">Errata exists</a>.</dd>
</dl></details></div></body></html>"""

OLD_HEAD = """<html><head><title>Web Content Accessibility Guidelines (WCAG) 2.0</title></head><body>
<div class="head"><h1>Web Content Accessibility Guidelines (WCAG) 2.0</h1>
<h2>W3C Recommendation 11 December 2008</h2>
<dl><dt>This version:</dt><dd><a href="http://www.w3.org/TR/2008/REC-WCAG20-20081211/">x</a></dd>
<dt>Latest version:</dt><dd><a href="http://www.w3.org/TR/WCAG20/">y</a></dd></dl></div></body></html>"""

ERRATA = """<html><body><p>Last modified: $Date: 2026/09/03 15:18:01 $</p>
<main><section id="since-current">
  <h2>Errata since <a href="https://www.w3.org/TR/WCAG22/">Current Publication</a></h2>
  <section id="editorial-current"><h3>Editorial Errata</h3><ul>
    <li>
      2026-08-17:
      In the definition for <a href="#x">widget</a>, fixing a typo
      (<a href="https://github.com/w3c/wcag/pull/5038" aria-label="pull request 5038">#5038</a>)
    </li>
    <li>2026-08-17: Second fix with the same date (<a href="https://github.com/w3c/wcag/pull/5039">#5039</a>, <a href="https://github.com/w3c/wcag/pull/5040">#5040</a>)</li>
  </ul></section>
  <section id="substantive-current"><h3>Substantive Errata</h3><ul>
    <li>2026-09-01: Changing a threshold</li>
  </ul></section>
</section><section id="since-2023-10-05">
  <h2>Errata since <a href="https://www.w3.org/TR/2023/REC-WCAG22-20231005/">05 October 2023 Publication</a></h2>
  <section id="editorial-2023"><h3>Editorial Errata</h3><ul>
    <li>2024-11-19: Removing a definition. (<a href="https://github.com/w3c/wcag/pull/3636">#3636</a>)</li>
  </ul></section>
</section></main></body></html>"""


class ParserTests(unittest.TestCase):
    def test_tr_head_respec(self):
        h = rv.parse_tr_head(RESPEC_HEAD)
        self.assertEqual(h["status"], "W3C Recommendation")
        self.assertEqual(h["date"], "12 December 2024")
        self.assertEqual(h["this_version"], "https://www.w3.org/TR/2024/REC-WCAG22-20241212/")
        self.assertEqual(h["latest_version"], "https://www.w3.org/TR/WCAG22/")

    def test_tr_head_old_format(self):
        h = rv.parse_tr_head(OLD_HEAD)
        self.assertEqual((h["status"], h["date"]), ("W3C Recommendation", "11 December 2008"))
        self.assertEqual(h["this_version"], "http://www.w3.org/TR/2008/REC-WCAG20-20081211/")
        self.assertEqual(h["latest_version"], "http://www.w3.org/TR/WCAG20/")

    def test_tr_head_other_statuses(self):
        for status in ("Working Draft", "Candidate Recommendation Snapshot", "Superseded Recommendation"):
            h = rv.parse_tr_head("<p>W3C %s 10 September 2026</p>" % status)
            self.assertEqual(h["status"], "W3C " + status)

    def test_tr_head_layout_change_is_error(self):
        with self.assertRaises(rv.SourceError):
            rv.parse_tr_head("<html><body>nothing here</body></html>")

    def test_errata(self):
        e = rv.parse_errata(ERRATA)
        self.assertEqual(e["last_modified"], "2026-09-03")
        self.assertEqual(set(e["publications"]), {"since-current", "since-2023-10-05"})
        self.assertEqual(e["publications"]["since-current"]["applies_to"], "https://www.w3.org/TR/WCAG22/")
        self.assertIn("2026-08-17#5038", e["entries"])
        self.assertIn("2026-08-17#5039+5040", e["entries"])
        self.assertEqual(e["entries"]["2026-08-17#5038"]["summary"], "In the definition for widget, fixing a typo")
        subst = [v for v in e["entries"].values() if v["class"] == "substantive"]
        self.assertEqual(len(subst), 1)
        c = rv.errata_counts(e)
        self.assertEqual((c["total"], c["editorial"], c["substantive"]), (4, 3, 1))
        self.assertEqual((c["since-current"], c["since-2023-10-05"]), (3, 1))

    def test_errata_duplicate_keys_are_kept(self):
        page = ERRATA.replace("pull/5039\">#5039</a>, <a href=\"https://github.com/w3c/wcag/pull/5040\">#5040",
                              "pull/5038\">#5038")
        e = rv.parse_errata(page)
        self.assertIn("2026-08-17#5038~2", e["entries"])

    def test_errata_layout_change_is_error(self):
        with self.assertRaises(rv.SourceError):
            rv.parse_errata("<html><body>moved</body></html>")

    def test_understanding_updated(self):
        self.assertEqual(rv.understanding_updated("<p><strong>Date:</strong> Updated 09 March 2026.</p>"), "2026-03-09")
        self.assertIsNone(rv.understanding_updated("<p>no date</p>"))

    def test_setup_pins(self):
        pins = rv.parse_setup_pins('#!/bin/sh\nPLAYWRIGHT_VERSION="1.63.0"\nAXE_CORE_VERSION="4.13.0"\n')
        self.assertEqual(pins, {"playwright": "1.63.0", "axe-core": "4.13.0"})

    def test_axe_sc_map_and_diff(self):
        rules = [("image-alt", ["cat.text-alternatives", "wcag2a", "wcag111"]),
                 ("duplicate-id", ["wcag2a-obsolete", "wcag411", "deprecated"]),
                 ("p-as-heading", ["wcag2a", "wcag131", "experimental"]),
                 ("reflow-x", ["wcag21aa", "wcag1410"]),
                 ("region", ["best-practice"])]
        m = rv.axe_sc_map(rules)
        self.assertEqual(m, {"1.1.1": ["image-alt"], "1.3.1": ["p-as-heading(experimental)"],
                             "1.4.10": ["reflow-x"], "4.1.1": ["duplicate-id(deprecated)"]})
        authored = {"1.1.1": ["image-alt"], "1.3.1": ["p-as-heading(experimental)"],
                    "4.1.1": ["duplicate-id(deprecated)"], "2.4.4": ["link-name"]}
        lines = rv.axe_map_diff(m, authored)
        self.assertEqual(len(lines), 2)
        self.assertTrue(any("1.4.10" in x and "reflow-x" in x for x in lines))
        self.assertTrue(any("2.4.4" in x and "link-name" in x for x in lines))
        self.assertEqual(rv.axe_map_diff(m, m), [])

    def test_node_and_unittest_summaries(self):
        spec = "ℹ tests 83\nℹ suites 3\nℹ pass 83\nℹ fail 0\nℹ skipped 0\n"
        tap = "# tests 5\n# pass 4\n# fail 1\n"
        self.assertEqual(rv.node_test_summary(spec), {"tests": 83, "pass": 83, "fail": 0, "skipped": 0})
        self.assertEqual(rv.node_test_summary(tap), {"tests": 5, "pass": 4, "fail": 1})
        s = rv.unittest_summary("....\nRan 159 tests in 1.7s\n\nOK (skipped=1)\n", 0)
        self.assertEqual(s, {"exit": 0, "ran": 159, "result": "OK", "skipped": 1})


class NetworkTests(unittest.TestCase):
    def test_fetch_sends_only_neutral_ua_with_timeout(self):
        seen = {}

        class Resp(io.BytesIO):
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout=None):
            seen["headers"] = dict(req.header_items())
            seen["timeout"] = timeout
            seen["url"] = req.full_url
            return Resp(b"ok")

        with mock.patch.object(rv.urllib.request, "urlopen", fake_urlopen):
            self.assertEqual(rv.fetch("https://example.invalid/x"), (200, b"ok"))
        self.assertEqual(list(seen["headers"]), ["User-agent"])
        self.assertEqual(seen["timeout"], rv.NET_TIMEOUT)
        self.assertTrue(seen["timeout"] and seen["timeout"] > 0)

    def test_ua_has_no_personal_data(self):
        self.assertNotRegex(rv.UA, r"@|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\b")
        self.assertIn("wcag22-a11y-revalidate", rv.UA)
        self.assertNotIn(os.path.expanduser("~"), rv.UA)
        user = os.environ.get("USER") or os.environ.get("LOGNAME")
        if user and len(user) > 2:
            self.assertNotIn(user, rv.UA)

    def test_fetch_errors_become_source_errors(self):
        def boom(req, timeout=None):
            raise OSError("no route")
        with mock.patch.object(rv.urllib.request, "urlopen", boom):
            with self.assertRaises(rv.SourceError):
                rv.fetch("https://example.invalid/")

    def test_collect_sources_parses_mocked_pages(self):
        pages = {rv.WCAG22_URL: RESPEC_HEAD, rv.ERRATA_URL: ERRATA,
                 rv.OTHER_SPECS["wcag21"]: OLD_HEAD.replace("2.0", "2.1"),
                 rv.OTHER_SPECS["wcag20"]: OLD_HEAD,
                 rv.OTHER_SPECS["wcag30"]: "<p>W3C Working Draft 10 September 2026</p>"}
        calls = []

        def fake_fetch(url, max_bytes=rv.MAX_BYTES):
            calls.append(url)
            return 200, pages[url].encode()
        errors = []
        with mock.patch.object(rv, "fetch", fake_fetch):
            src = rv.collect_sources(errors, {"cached_html": {"sha256": rv.sha256_bytes(RESPEC_HEAD.encode())}})
        self.assertEqual(errors, [])
        self.assertEqual(len(calls), 5)
        self.assertTrue(src["wcag22"]["matches_catalogue_cache"])
        self.assertEqual(src["wcag30"]["status"], "W3C Working Draft")
        self.assertEqual(src["errata"]["counts"]["total"], 4)

    def test_collect_upstream_and_deep(self):
        def fake_fetch(url, max_bytes=rv.MAX_BYTES):
            if "registry.npmjs.org" in url:
                return 200, json.dumps({"version": "9.9.9"}).encode()
            return 200, b"<p>Updated 01 June 2026.</p>"
        errors = []
        with mock.patch.object(rv, "fetch", fake_fetch):
            up = rv.collect_upstream(errors)
            deep = rv.collect_understanding_live(errors, sleep=lambda s: None)
        self.assertEqual(up, {"npm": {"playwright": "9.9.9", "axe-core": "9.9.9"}})
        self.assertTrue(deep["updated"])
        self.assertEqual(set(deep["updated"].values()), {"2026-06-01"})
        self.assertEqual(errors, [])

    def test_offline_collect_never_fetches(self):
        def no_network(*a, **k):
            raise AssertionError("network used in offline mode")
        errors, notes = [], []
        with mock.patch.object(rv, "fetch", no_network), \
                mock.patch.object(rv.urllib.request, "urlopen", no_network), \
                mock.patch.object(rv, "rebuild_offline", lambda e, n: {"ran": False}), \
                mock.patch.object(rv, "collect_engines", lambda e, n: {}):
            live = rv.collect(True, False, True, errors, notes)
        self.assertIsNone(live["sources"])
        self.assertIsNone(live["upstream"])
        self.assertIsNone(live["understanding_live"])
        self.assertIsNone(live["tests"])


class DiffTests(unittest.TestCase):
    def lock(self):
        return {"meta": {"schema": 1},
                "spec": {"dated_version_url": "https://www.w3.org/TR/2024/REC-WCAG22-20241212/",
                         "cached_html": {"sha256": "a"}},
                "catalogue": {"understanding": {"files": {"x.html": {"sha256": "1", "updated": "2026-01-01"}}},
                              "offline_rebuild": {"reproduces": True, "differs": []},
                              "outputs": {"references/sc-1-perceivable.md": "h"}, "inputs": {"b": "1"}},
                "engines": {"pinned": {"playwright": "1.63.0", "axe-core": "4.13.0"},
                            "installed": {"playwright": "1.63.0", "axe-core": "4.13.0"},
                            "node": "26.8.1", "axe": {"rules": ["a", "b"]}},
                "sources": {"wcag22": {"this_version": "https://www.w3.org/TR/2024/REC-WCAG22-20241212/",
                                       "status": "W3C Recommendation", "html_sha256": "a"},
                            "errata": {"entries": {"2026-08-17#5038": {"class": "editorial", "summary": "s"}}},
                            "wcag30": {"status": "W3C Working Draft", "date": "10 September 2026"}},
                "upstream": {"npm": {"playwright": "1.63.0", "axe-core": "4.13.0"}},
                "tests": {"unit_scripts": {"exit": 0, "ran": 159, "result": "OK"}}}

    def test_no_drift(self):
        lock = self.lock()
        self.assertEqual(rv.diff(lock, json.loads(json.dumps(lock)), []), [])

    def test_skipped_sections_are_not_compared(self):
        lock = self.lock()
        live = json.loads(json.dumps(lock))
        live["sources"] = live["upstream"] = live["tests"] = None
        self.assertEqual(rv.diff(lock, live, ["sources", "upstream", "tests"]), [])

    def test_summary_messages(self):
        lock = self.lock()
        live = json.loads(json.dumps(lock))
        live["sources"]["wcag22"]["this_version"] = "https://www.w3.org/TR/2027/REC-WCAG22-20270101/"
        live["sources"]["errata"]["entries"]["2026-10-01#6000"] = {"class": "substantive", "summary": "new"}
        live["sources"]["wcag30"] = {"status": "W3C Candidate Recommendation Snapshot", "date": "1 May 2027"}
        live["upstream"]["npm"]["axe-core"] = "4.14.0"
        live["engines"]["axe"]["rules"] = ["a", "c"]
        live["catalogue"]["offline_rebuild"] = {"reproduces": False, "differs": ["references/glossary.md"]}
        live["catalogue"]["understanding"]["files"]["x.html"]["updated"] = "2026-02-02"
        live["tests"]["unit_scripts"]["ran"] = 160
        rows = rv.diff(lock, live, [])
        self.assertTrue(rows)
        text = "\n".join(rv.summarize(lock, live, []))
        self.assertIn(rv.NEW_VERSION_MSG, text)
        self.assertIn("SUBSTANTIVE erratum 2026-10-01#6000", text)
        self.assertIn("WCAG 3.0 status changed", text)
        self.assertIn("npm axe-core latest release changed", text)
        self.assertIn("NEW axe-core rules: c", text)
        self.assertIn("REMOVED axe-core rules: b", text)
        self.assertIn("does NOT reproduce references/: references/glossary.md", text)
        self.assertIn("Cached Understanding pages changed: x.html", text)
        self.assertIn("test `unit_scripts` result differs", text)

    def test_engine_freshness_update_available(self):
        live = {"engines": {"pinned": {"playwright": "1.63.0", "axe-core": "4.13.0"},
                            "installed": {"playwright": "1.63.0", "axe-core": "4.12.0",
                                          "chromium_headless_shell": {"revision": "1243", "installed": True,
                                                                      "browser_version": "153"}}},
                "upstream": {"npm": {"playwright": "1.64.0", "axe-core": "4.13.0"}}}
        rows = {r[0]: r[-1] for r in rv.engine_freshness(live)}
        self.assertEqual(rows["playwright"], "update available")
        self.assertEqual(rows["axe-core"], "installed differs from pin")
        self.assertEqual(rows["chromium-headless-shell"], "current")

    def test_tests_ok(self):
        self.assertFalse(rv.tests_ok({"tests": None}))
        self.assertTrue(rv.tests_ok({"tests": {"a": {"exit": 0, "result": "OK"}}}))
        self.assertFalse(rv.tests_ok({"tests": {"a": {"exit": 1, "result": "FAILED"}}}))


class MainTests(unittest.TestCase):
    def run_main(self, argv, live, lock=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "SOURCES.lock")
            if lock is not None:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(lock, fh)
            with mock.patch.object(rv, "collect", lambda *a: json.loads(json.dumps(live))), \
                    mock.patch("sys.stdout", new_callable=io.StringIO):
                code = rv.main(argv + ["--lock", path])
            written = None
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    written = json.load(fh)
            return code, written

    LIVE = {"skill": {"name": "wcag22-a11y"}, "spec": {}, "catalogue": {}, "engines": {},
            "tests": None, "sources": None, "upstream": None, "understanding_live": None}

    def test_exit_codes(self):
        lock = dict(self.LIVE, meta={"schema": 1})
        self.assertEqual(self.run_main(["--offline"], self.LIVE, lock)[0], 0)
        drift = dict(self.LIVE, spec={"status": "changed"})
        self.assertEqual(self.run_main(["--offline"], drift, lock)[0], 1)
        self.assertEqual(self.run_main(["--offline"], self.LIVE, None)[0], 2)
        bad = dict(lock, meta={"schema": 99})
        self.assertEqual(self.run_main(["--offline"], self.LIVE, bad)[0], 2)

    def test_update_refused_without_green_tests(self):
        code, written = self.run_main(["--update", "--offline"], self.LIVE, None)
        self.assertEqual(code, 2)
        self.assertIsNone(written)

    def test_update_writes_lock_and_keeps_network_sections(self):
        live = dict(self.LIVE, tests={"unit_scripts": {"exit": 0, "result": "OK", "ran": 1, "tail": "x"}})
        old = dict(self.LIVE, meta={"schema": 1, "snapshots": {"sources": "2026-01-01"}},
                   sources={"wcag22": {"status": "W3C Recommendation"}})
        code, written = self.run_main(["--update", "--offline"], live, old)
        self.assertEqual(code, 0)
        self.assertEqual(written["sources"], {"wcag22": {"status": "W3C Recommendation"}})
        self.assertEqual(written["meta"]["snapshots"]["sources"], "2026-01-01")
        self.assertNotIn("tail", written["tests"]["unit_scripts"])
        self.assertEqual(written["meta"]["user_agent"], rv.UA)
        self.assertEqual(list(written)[0], "meta")


if __name__ == "__main__":
    unittest.main()
