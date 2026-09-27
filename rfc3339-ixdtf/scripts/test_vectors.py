"""Tests for the vector set (check coverage) and run_vectors.py features:
--tz-matrix, meta, --batch / --jobs, --report md.  stdlib unittest only.

    python3 -m unittest discover -s scripts
"""
import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import rfcdt  # noqa: E402
import run_vectors  # noqa: E402

GEN = os.path.join(ROOT, "tools", "gen_vectors.py")
RUNNER = os.path.join(HERE, "run_vectors.py")
TZ = rfcdt.tzdata_available()

# Objective consumer/grammar checks that no single-string vector can exercise.
# Every entry needs a reason; a stale entry (the check now has vectors) fails.
EXEMPT = {
    "R3339-5.1-01": "ordering property of a PAIR of timestamps (lexical order = time order "
                    "only under stated conditions); a per-string accept/reject verdict "
                    "cannot exercise it -- audit sort code instead",
}


def required_checks(index):
    """Objective checks a consumer (or the grammar) must satisfy."""
    out = []
    for cid, row in index.items():
        if row["judgment"] != "objective":
            continue
        if "not checkable" in (row["level"] + row["title"]).lower():
            continue
        if "consumer" in row["roles"] or "grammar" in row["level"]:
            out.append(cid)
    return out


class TestCheckCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = run_vectors.load_vectors()
        cls.index = run_vectors.load_check_index()
        cls.by_input = {}
        for v in cls.vectors:
            cls.by_input.setdefault(v["input"], []).append(v)

    def test_index_parsed(self):
        self.assertGreaterEqual(len(self.index), 100)
        row = self.index["R3339-5.6-07"]
        self.assertEqual(row["judgment"], "objective")
        self.assertIn("consumer", row["roles"])
        self.assertIn("grammar", row["level"])

    def test_every_vector_has_known_checks(self):
        for v in self.vectors:
            self.assertTrue(v.get("checks"), v["id"])
            self.assertEqual(v["checks"], sorted(set(v["checks"])), v["id"])
            unknown = set(v["checks"]) - set(self.index)
            self.assertFalse(unknown, (v["id"], unknown))

    def test_objective_consumer_checks_have_vectors(self):
        covered = {c for v in self.vectors for c in v["checks"]}
        required = required_checks(self.index)
        self.assertGreater(len(required), 50)
        missing = [c for c in required if c not in covered and c not in EXEMPT]
        self.assertEqual(missing, [], "objective consumer/grammar checks with no vector "
                                      "(add vectors in tools/gen_vectors.py or EXEMPT with a "
                                      "reason)")

    def test_exemptions_are_justified_and_current(self):
        covered = {c for v in self.vectors for c in v["checks"]}
        required = set(required_checks(self.index))
        for cid, why in EXEMPT.items():
            self.assertIn(cid, self.index, cid)
            self.assertIn(cid, required, f"{cid} is exempt but not required")
            self.assertGreater(len(why), 30, cid)
            self.assertNotIn(cid, covered, f"{cid} now has vectors: drop the exemption")

    def _one(self, inp, **want):
        vs = [v for v in self.by_input.get(inp, [])
              if all(v.get(k) == x for k, x in want.items() if k != "check")]
        self.assertTrue(vs, (inp, want))
        if "check" in want:
            self.assertTrue(any(want["check"] in v["checks"] for v in vs), (inp, want))
        return vs[0]

    def test_known_gap_vectors(self):
        # R3339-A-03 / App. A: fraction on minutes, fraction without seconds digits
        self._one("2024-01-01T12:00.5Z", expect="invalid", check="R3339-A-03")
        self._one("2024-01-01T12:00:.5Z", expect="invalid", check="R3339-A-03")
        self._one("2020-01-01T00:00:0.5Z", expect="invalid", check="R3339-A-03")
        # R3339-5.7-05 negative leap second
        self._one("2016-12-31T23:59:58Z", expect="valid", check="R3339-5.7-05")
        v = self._one("2035-06-30T23:59:59Z", check="R3339-5.7-05")
        self.assertEqual(v["expect"], "either")
        # weekday
        self._one("Fri, 1985-04-12T23:20:50Z", expect="invalid", check="R3339-5.4-01")
        self._one("Sat, 1985-04-12T23:20:50Z", expect="invalid", check="R3339-B-02")

    def test_hardening_vectors(self):
        hard = [v for v in self.vectors if "R9557-7.2-01" in v["checks"]]
        self.assertTrue(any(v["input"].count("[a=b]") == 5000 for v in hard))
        self.assertTrue(any(v["input"].endswith("[" * 5000) and v["expect"] == "invalid"
                            for v in hard))
        self.assertTrue(any(v["input"].endswith("Z[") and v["expect"] == "invalid"
                            for v in hard))
        late = [v for v in hard if v["input"].endswith("[!knort=x]")]
        self.assertEqual([v["expect"] for v in late], ["invalid"])
        for v in hard:  # bounded time in the reference engine
            r = rfcdt.check(v["input"], v["profile"])
            self.assertEqual(r.ok, {"valid": True, "invalid": False}.get(v["expect"], r.ok))

    def test_tz_link_and_lmt_vectors(self):
        for inp in ("2022-07-08T00:14:07-07:00[!US/Pacific]",
                    "2022-07-08T00:14:07+03:00[!Europe/Kiev]",
                    "2022-07-08T00:14:07+03:00[!Europe/Kyiv]"):
            v = self._one(inp, expect="either")
            self.assertIn("tzdata", v.get("requires", []))
        # inconsistent with the link target, or unknown: invalid either way
        self._one("2022-07-08T00:14:07+02:00[!Europe/Kiev]", expect="invalid")
        lmt = self._one("1900-01-01T00:00:00+00:10[!Europe/Paris]", expect="either")
        self.assertIn("R3339-4.2-03", lmt["checks"])
        self.assertIn("§", lmt["interpretation"])
        self._one("1900-01-01T00:00:00+00:09[!Europe/Paris]", expect="valid")

    def test_generator_reproduces_committed_file(self):
        cp = subprocess.run([sys.executable, GEN, "--check"], capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)


# ---------------------------------------------------------------------------
def _script(d, name, body):
    path = os.path.join(d, name)
    with open(path, "w") as fh:
        fh.write(body)
    return f"{sys.executable} {path}"


def _vec(i, inp, expect="valid", fields=None, **kw):
    v = {"id": f"t-{i}", "input": inp, "profile": "rfc3339", "expect": expect, "reason": "ok",
         "section": "test", "checks": ["R3339-5.6-10"], "notes": "test vector"}
    if fields:
        v["fields"] = fields
    v.update(kw)
    return v


# A fake parser that consults the host TZ: rejects 'Z' strings under Kathmandu
# and reports a local hour of 5 under St Johns.  Works per-process and batch.
TZ_FAKE = r'''
import os, sys, json
def one(s):
    tz = os.environ.get("TZ", "")
    ok = not (tz == "Asia/Kathmandu" and s.endswith("Z"))
    return {"ok": ok, "fields": {"hour": 5 if tz == "America/St_Johns" else 12}}
if os.environ.get("RFCDT_BATCH") == "1":
    for line in sys.stdin:
        if line.strip():
            req = json.loads(line)
            print(json.dumps({"id": req["id"], **one(req["input"])}))
else:
    print(json.dumps(one(sys.stdin.read())))
'''


class TestTzMatrix(unittest.TestCase):
    ZONES = ["UTC", "America/St_Johns", "Asia/Kathmandu"]

    def setUp(self):
        self.vecs = [_vec(1, "2024-01-01T12:00:00Z", fields={"hour": 12}),
                     _vec(2, "2024-01-01T12:00:00+01:00", fields={"hour": 12}),
                     _vec(3, "2024-01-01T12:00:00+01:00")]

    def _check(self, res):
        by = {r["id"]: r for r in res}
        self.assertEqual(by["t-1"]["status"], "tz-dependent")
        self.assertIn("verdict", by["t-1"]["detail"])
        self.assertIn("Asia/Kathmandu=rejected", by["t-1"]["detail"])
        self.assertIn("fields.hour", by["t-1"]["detail"])
        self.assertEqual(by["t-2"]["status"], "tz-dependent")
        self.assertNotIn("verdict", by["t-2"]["detail"])
        self.assertIn("America/St_Johns=5", by["t-2"]["detail"])
        self.assertEqual(by["t-2"]["base_status"], "pass")
        self.assertEqual(set(by["t-2"]["tz_outputs"]), set(self.ZONES))
        # fields differ even though the vector has no expected fields: still a finding
        self.assertEqual(by["t-3"]["status"], "tz-dependent")
        _, tot = run_vectors.summarize(res)
        self.assertEqual(tot["tz-dependent"], 3)
        self.assertIn("tz-dependent", run_vectors.FAILURES)

    def test_per_process(self):
        with tempfile.TemporaryDirectory() as d:
            tgt = _script(d, "tzfake.py", TZ_FAKE)
            res = run_vectors.run(self.vecs, target=tgt, tz_matrix=self.ZONES)
            self._check(res)
            # without the matrix the TZ dependence is invisible (UTC-like pass)
            plain = run_vectors.run(self.vecs, target=tgt, tz_matrix=None)
            self.assertNotIn("tz-dependent", {r["status"] for r in plain})
            buf = io.StringIO()
            run_vectors.print_report(res, tgt, out=buf)
            self.assertIn("HOST-TZ DEPENDENT", buf.getvalue())

    def test_batch_and_jobs(self):
        with tempfile.TemporaryDirectory() as d:
            tgt = _script(d, "tzfake.py", TZ_FAKE)
            self._check(run_vectors.run(self.vecs, target=tgt, tz_matrix=self.ZONES,
                                        batch=True))
            self._check(run_vectors.run(self.vecs, target=tgt, tz_matrix=self.ZONES, jobs=3))

    def test_tz_independent_target(self):
        with tempfile.TemporaryDirectory() as d:
            acc = _script(d, "acc.py", "import json,sys; sys.stdin.read(); "
                                       "print(json.dumps({'ok': True, 'fields': {'hour': 12}}))\n")
            res = run_vectors.run(self.vecs, target=acc, tz_matrix=self.ZONES)
            self.assertEqual({r["status"] for r in res}, {"pass"})

    def test_builtin_engine_is_tz_independent(self):
        vecs = [v for v in run_vectors.load_vectors() if not v.get("requires")][:60]
        before = os.environ.get("TZ")
        res = run_vectors.run(vecs, tz_matrix=self.ZONES)
        self.assertNotIn("tz-dependent", {r["status"] for r in res})
        self.assertEqual(os.environ.get("TZ"), before)  # restored

    def test_cli_exit_status(self):
        with tempfile.TemporaryDirectory() as d:
            tgt = _script(d, "tzfake.py", TZ_FAKE)
            p = os.path.join(d, "v.json")
            with open(p, "w") as fh:
                json.dump({"vectors": self.vecs}, fh)
            with contextlib.redirect_stdout(io.StringIO()) as out:
                rc = run_vectors.main(["--target", tgt, "--vectors", p, "--json",
                                       "--tz-matrix", ",".join(self.ZONES)])
            self.assertEqual(rc, 1)
            doc = json.loads(out.getvalue())
            self.assertEqual(doc["meta"]["tz_matrix"], self.ZONES)
            self.assertEqual(doc["totals"]["tz-dependent"], 3)


class TestMeta(unittest.TestCase):
    def test_json_meta(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            run_vectors.main(["--json", "--profile", "rfc3339"])
        doc = json.loads(out.getvalue())
        meta = doc["meta"]
        for k in ("runner_version", "vectors_sha256", "python", "host_tz", "tz_matrix", "date",
                  "target", "tzdata", "vector_count"):
            self.assertIn(k, meta)
        with open(run_vectors.DEFAULT_VECTORS, "rb") as fh:
            self.assertEqual(meta["vectors_sha256"], hashlib.sha256(fh.read()).hexdigest())
        self.assertEqual(meta["runner_version"], run_vectors.RUNNER_VERSION)
        self.assertEqual(meta["python"], sys.version.split()[0])
        self.assertRegex(meta["date"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertTrue(rfcdt.check(meta["date"]).ok)
        self.assertEqual(meta["target"], "rfcdt (built-in)")
        self.assertIsNone(meta["tz_matrix"])
        self.assertNotIn(os.path.expanduser("~"), json.dumps(meta))  # no home paths

    def test_text_header(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            run_vectors.main(["--profile", "rfc3339", "--tz-matrix", "UTC,Asia/Kathmandu"])
        head = out.getvalue().splitlines()[1]
        self.assertIn(f"runner {run_vectors.RUNNER_VERSION}", head)
        self.assertIn("sha256:", head)
        self.assertIn("python", head)
        self.assertIn("host TZ", head)
        self.assertIn("tz-matrix UTC,Asia/Kathmandu", head)


class TestBatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = run_vectors.load_vectors()

    def test_batch_request_is_one_ascii_line(self):
        v = _vec(1, "2024-01-01T00:00:00Z\x00\r\n\u2028é")
        line = run_vectors.batch_request_line(v)
        self.assertNotIn("\n", line)
        line.encode("ascii")
        self.assertEqual(json.loads(line)["input"], v["input"])
        self.assertEqual(set(json.loads(line)), {"id", "input", "profile", "options"})

    def test_rfcdt_batch_adapter_matches_builtin(self):
        tgt = f"{sys.executable} {RUNNER} --rfcdt-adapter"
        info = {}
        res = run_vectors.run(self.vectors, target=tgt, batch=True, info=info)
        self.assertEqual(info["batch"], "yes")
        builtin = run_vectors.run(self.vectors)
        self.assertEqual(len(res), len(builtin))
        for a, b in zip(res, builtin):
            self.assertEqual(a["id"], b["id"])
            if b["status"] == "skip":
                self.assertEqual(a["status"], "skip", a["id"])
                continue
            self.assertEqual(a["output"]["ok"], b["output"]["ok"], a["id"])
            self.assertEqual(a["output"]["fields"], json.loads(json.dumps(
                b["output"]["fields"], ensure_ascii=False)), a["id"])
        bad = [r["id"] for r in res if r["status"] not in ("pass", "interpretation", "skip")]
        self.assertEqual(bad, [])

    def test_rfcdt_adapter_single_modes(self):
        tgt = f"{sys.executable} {RUNNER} --rfcdt-adapter"
        sample = [v for v in self.vectors if "\x00" not in v["input"]][:25]
        for mode in ("stdin", "argv"):
            res = run_vectors.run(sample, target=tgt, mode=mode)
            bad = [r["id"] for r in res if r["status"] not in ("pass", "interpretation")]
            self.assertEqual(bad, [], mode)

    def test_fallback_when_adapter_declines(self):
        body = ("import os, sys, json\n"
                "if os.environ.get('RFCDT_BATCH') == '1':\n"
                "    print(json.dumps({'batch': False})); sys.exit(0)\n"
                "s = sys.stdin.read()\n"
                "print(json.dumps({'ok': s.endswith('Z')}))\n")
        vecs = [_vec(1, "2024-01-01T00:00:00Z"), _vec(2, "2024-01-01T00:00:00", "invalid")]
        with tempfile.TemporaryDirectory() as d:
            info = {}
            res = run_vectors.run(vecs, target=_script(d, "nob.py", body), batch=True,
                                  jobs=2, info=info)
        self.assertTrue(info["batch"].startswith("fallback"), info)
        self.assertEqual([r["status"] for r in res], ["pass", "pass"])

    def test_lost_and_reordered_lines_are_errors(self):
        vecs = [_vec(i, "2024-01-01T00:00:00Z") for i in range(1, 4)]
        lost = ("import sys, json\n"
                "reqs = [json.loads(l) for l in sys.stdin if l.strip()]\n"
                "for r in reqs[:2]: print(json.dumps({'id': r['id'], 'ok': True}))\n")
        swap = ("import sys, json\n"
                "reqs = [json.loads(l) for l in sys.stdin if l.strip()]\n"
                "reqs[0], reqs[1] = reqs[1], reqs[0]\n"
                "for r in reqs: print(json.dumps({'id': r['id'], 'ok': True}))\n")
        with tempfile.TemporaryDirectory() as d:
            res = run_vectors.run(vecs, target=_script(d, "lost.py", lost), batch=True)
            self.assertEqual([r["status"] for r in res], ["pass", "pass", "error"])
            self.assertIn("no result line", res[2]["detail"])
            res = run_vectors.run(vecs, target=_script(d, "swap.py", swap), batch=True)
            self.assertEqual([r["status"] for r in res], ["error", "error", "pass"])
            self.assertIn("reordered", res[0]["detail"])

    def test_jobs_preserve_order_and_results(self):
        sample = self.vectors[:40]
        tgt = f"{sys.executable} {os.path.join(HERE, 'rfcdt.py')} adapter"
        seq = run_vectors.run(sample, target=tgt, jobs=1)
        par = run_vectors.run(sample, target=tgt, jobs=6)
        self.assertEqual([(r["id"], r["status"]) for r in seq],
                         [(r["id"], r["status"]) for r in par])
        with self.assertRaises(ValueError):
            run_vectors.run(sample[:1], target=tgt, jobs=0)


class TestMarkdownReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = run_vectors.load_vectors()
        cls.index = run_vectors.load_check_index()

    def test_severity_guess(self):
        g = run_vectors.severity_guess
        self.assertEqual(g({"status": "too-lenient", "checks": ["R3339-5.6-07"],
                            "reason": "R3339-5.6/time-second"}, self.index), "Nonconformity")
        self.assertEqual(g({"status": "too-lenient", "checks": ["R9557-3.3-05"],
                            "reason": "x"}, self.index), "Nonconformity")  # MUST
        self.assertEqual(g({"status": "too-strict", "checks": ["R3339-5.6-13"],
                            "reason": "ok"}, self.index), "Deviation")  # SHOULD
        self.assertEqual(g({"status": "too-strict", "checks": ["R3339-2-03"],
                            "reason": "ok"}, self.index), "Advisory")  # informative
        self.assertEqual(g({"status": "wrong-value", "checks": ["R3339-2-03"],
                            "reason": "ok"}, self.index), "Nonconformity")
        self.assertEqual(g({"status": "tz-dependent", "checks": [], "reason": "ok"},
                           self.index), "Nonconformity")

    def test_md_report_for_accept_all(self):
        sample = [v for v in self.vectors if v["profile"] == "rfc3339"][:120]
        with tempfile.TemporaryDirectory() as d:
            acc = _script(d, "acc.py", "import json,sys; sys.stdin.read(); "
                                       "print(json.dumps({'ok': True}))\n")
            res = run_vectors.run(sample, target=acc)
            buf = io.StringIO()
            run_vectors.markdown_report(res, "accept_all", out=buf)
        md = buf.getvalue()
        self.assertIn("| Severity (guess) | Check ID(s) | Section | Vector | "
                      "input → target output | expected |", md)
        self.assertIn("### TOO LENIENT -- R3339-5.6/time-offset", md)
        self.assertIn("R3339-5.6-10", md)
        self.assertIn("| Nonconformity |", md)
        self.assertIn("→ accepted |", md)
        self.assertIn("## Interpretation choices", md)
        self.assertIn("| Vector | Section | Check ID(s) | Input | Target choice |", md)
        # one heading per root cause: no reason code heads two groups of the same status
        heads = [ln for ln in md.splitlines() if ln.startswith("### ")]
        causes = [h.split(" (")[0] for h in heads]
        self.assertEqual(len(causes), len(set(causes)))
        lenient = {r["reason"] for r in res if r["status"] == "too-lenient"}
        self.assertEqual(len([c for c in causes if c.startswith("### TOO LENIENT")]),
                         len(lenient))

    def test_md_cli_long_inputs_shortened(self):
        hard = [v for v in self.vectors if "R9557-7.2-01" in v["checks"]]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "v.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump({"vectors": hard}, fh, ensure_ascii=False)
            rej = _script(d, "rej.py", "import json,sys; sys.stdin.read(); "
                                       "print(json.dumps({'ok': False}))\n")
            with contextlib.redirect_stdout(io.StringIO()) as out:
                rc = run_vectors.main(["--target", rej, "--vectors", p, "--report", "md"])
        md = out.getvalue()
        self.assertEqual(rc, 0)  # rejecting everything here is permitted (either/invalid)
        self.assertLess(max(len(ln) for ln in md.splitlines()), 1200)
        self.assertIn("chars)", md)
        self.assertIn("No failing vectors.", md)


class TestProbeInputs(unittest.TestCase):
    """probes/inputs.json is generated from vectors.json by tools/gen_probe_inputs.py."""

    GEN_PROBES = os.path.join(ROOT, "tools", "gen_probe_inputs.py")

    def test_probe_inputs_not_stale(self):
        cp = subprocess.run([sys.executable, self.GEN_PROBES, "--check"],
                            capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0,
                         "probes/inputs.json is stale; run python3 tools/gen_probe_inputs.py\n"
                         + cp.stdout + cp.stderr)

    def test_probe_inputs_cover_every_vector(self):
        with open(os.path.join(ROOT, "probes", "inputs.json"), encoding="utf-8") as fh:
            doc = json.load(fh)
        vecs = run_vectors.load_vectors()
        self.assertEqual([e["vector"] for e in doc["inputs"]], [v["id"] for v in vecs])
        for e, v in zip(doc["inputs"], vecs):
            self.assertEqual(e["s"], v["input"])
            for k in ("expect", "profile", "checks", "options", "requires"):
                self.assertEqual(e.get(k), v.get(k), (e["id"], k))
        inputs = {e["s"] for e in doc["inputs"]}
        for e in doc["legacy"]:
            self.assertNotIn(e["s"], inputs, e["id"])
            self.assertTrue(e["legacy_reason"])


class TestGradingRules(unittest.TestCase):
    """R2 (leap-second representation) and R3 (fraction truncation/rounding)."""

    @classmethod
    def setUpClass(cls):
        cls.vec = {v["id"]: v for v in run_vectors.load_vectors()}

    def classify(self, vid, fields, ok=True):
        rec = {}
        run_vectors._classify(self.vec[vid], rec, {"ok": ok, "fields": fields}, [])
        return rec

    # -- R2 ---------------------------------------------------------------
    def test_leap_vectors_exist(self):
        for vid in ("3339-5.8-003", "3339-5.8-004", "3339-5.7-025"):
            self.assertTrue(run_vectors._is_leap_vector(self.vec[vid]), vid)
        self.assertFalse(run_vectors._is_leap_vector(self.vec["3339-5.6-001"]))

    def test_leap_as_59_same_minute(self):
        rec = self.classify("3339-5.8-004", {"year": 1990, "month": 12, "day": 31, "hour": 15,
                                             "minute": 59, "second": 59, "leap_second": False,
                                             "offset_minutes": -480})
        self.assertEqual(rec["status"], "interpretation")
        self.assertIn("leap-second representation", rec["interpretation"])
        self.assertIn(":59", rec["choice"])

    def test_leap_as_next_minute_rolls_over_day_and_year(self):
        rec = self.classify("3339-5.8-003", {"year": 1991, "month": 1, "day": 1, "hour": 0,
                                             "minute": 0, "second": 0, "leap_second": False})
        self.assertEqual(rec["status"], "interpretation")
        self.assertIn("next minute", rec["choice"])
        # offset-shifted leap second: next minute is 16:00 local, same day
        rec = self.classify("3339-5.8-004", {"year": 1990, "month": 12, "day": 31, "hour": 16,
                                             "minute": 0, "second": 0, "offset_minutes": -480})
        self.assertEqual(rec["status"], "interpretation")

    def test_leap_vector_with_only_leap_second_flag(self):
        # 3339-5.7-025 expects only leap_second: true; the wall clock comes from rfcdt
        rec = self.classify("3339-5.7-025", {"year": 2016, "month": 12, "day": 31, "hour": 23,
                                             "minute": 59, "second": 59, "leap_second": False})
        self.assertEqual(rec["status"], "interpretation")

    def test_leap_other_values_stay_wrong(self):
        bad = [
            # :00 without the roll-over
            {"year": 1990, "month": 12, "day": 31, "hour": 23, "minute": 59, "second": 0},
            # :59 of the wrong minute
            {"year": 1990, "month": 12, "day": 31, "hour": 23, "minute": 58, "second": 59},
            # next minute but the date not rolled over
            {"year": 1990, "month": 12, "day": 31, "hour": 0, "minute": 0, "second": 0},
            # a different second altogether
            {"second": 58},
            # leap_second claimed true but second 59
            {"second": 59, "leap_second": True},
        ]
        for f in bad:
            self.assertEqual(self.classify("3339-5.8-003", f)["status"], "wrong-value", f)
        # a mismatch outside the wall-clock fields is never excused
        vec = dict(self.vec["3339-5.8-004"])
        vec["fields"] = dict(vec["fields"], offset_minutes=-480)
        rec = {}
        run_vectors._classify(vec, rec, {"ok": True, "fields": {"hour": 15, "minute": 59,
                                                                "second": 59, "offset_minutes": 0}}, [])
        self.assertEqual(rec["status"], "wrong-value")

    def test_leap_exact_60_passes_and_non_leap_unaffected(self):
        self.assertEqual(self.classify("3339-5.8-003", {"second": 60, "leap_second": True})["status"],
                         "pass")
        v = next(v for v in self.vec.values() if v["expect"] == "valid"
                 and (v.get("fields") or {}).get("hour") is not None
                 and not run_vectors._is_leap_vector(v))
        f = dict(v["fields"], hour=(v["fields"]["hour"] + 1) % 24)
        self.assertEqual(self.classify(v["id"], f)["status"], "wrong-value")

    def test_leap_rule_in_text_report(self):
        rec = self.classify("3339-5.8-003", {"second": 59})
        rec.update({k: self.vec["3339-5.8-003"][k] for k in ("id", "section", "input", "notes")})
        buf = io.StringIO()
        run_vectors.print_report([rec], "t", out=buf)
        self.assertIn("leap-second representation", buf.getvalue())
        self.assertIn("1 interpretation", buf.getvalue())

    # -- R3 ---------------------------------------------------------------
    def test_secfrac_truncation_and_rounding(self):
        m = run_vectors._secfrac_match
        self.assertTrue(m("52", "520"))                        # decimal equality
        self.assertTrue(m("000000000001", "000000000"))        # truncation
        self.assertTrue(m("123456789", "123"))                 # truncation
        self.assertTrue(m("123456789", "1235"))                # half-up / half-even (> half)
        self.assertTrue(m("125", "13"))                        # exactly half: half-up
        self.assertTrue(m("125", "12"))                        # exactly half: half-even (and trunc)
        self.assertTrue(m("135", "14"))                        # exactly half: both round up
        self.assertTrue(m("1251", "13"))                       # above half
        self.assertTrue(m("1234567890" * 105, "1234568"))      # 3339-5.6-073, .NET ticks
        self.assertFalse(m("124", "13"))                       # below half: no round-up
        self.assertFalse(m("123456789", "1236"))
        self.assertFalse(m("123456789", "124"))
        self.assertFalse(m("5", "6"))                          # longer/equal length: exact only
        self.assertFalse(m("9996", "000"))                     # carry into seconds: not accepted
        self.assertTrue(m("9996", "999"))                      # truncation still fine
        self.assertTrue(m(None, None))
        self.assertFalse(m("5", None))

    def test_round_digits_modes(self):
        r = run_vectors._round_digits
        self.assertEqual(r("125", 2, "truncate"), "12")
        self.assertEqual(r("125", 2, "half-up"), "13")
        self.assertEqual(r("125", 2, "half-even"), "12")
        self.assertEqual(r("135", 2, "half-even"), "14")
        self.assertEqual(r("0995", 3, "half-up"), "100")
        self.assertEqual(r("0995", 3, "half-even"), "100")
        self.assertIsNone(r("9995", 3, "half-up"))
        self.assertEqual(r("009", 2, "half-up"), "01")

    def test_rounded_fraction_classified_pass(self):
        rec = self.classify("3339-5.6-073", {"secfrac": "1234568"})
        self.assertEqual(rec["status"], "pass")
        rec = self.classify("3339-5.6-073", {"secfrac": "1234569"})
        self.assertEqual(rec["status"], "wrong-value")


if __name__ == "__main__":
    unittest.main()
