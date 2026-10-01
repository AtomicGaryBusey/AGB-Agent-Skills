"""Unit tests for rfcdt.py and run_vectors.py (stdlib unittest)."""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import rfcdt  # noqa: E402
import run_vectors  # noqa: E402

RFCDT = os.path.join(HERE, "rfcdt.py")
# Optional regression fixture from a blind audit (not shipped with the skill).
AUDIT_TARGET = os.path.abspath(os.path.join(HERE, "..", "..", "..", "rfc-target"))
TZ = rfcdt.tzdata_available()


def codes(r):
    return r.error_codes


class TestRFC3339Grammar(unittest.TestCase):
    def test_rfc_examples_valid(self):
        for s in ("1985-04-12T23:20:50.52Z", "1996-12-19T16:39:57-08:00",
                  "1990-12-31T23:59:60Z", "1990-12-31T15:59:60-08:00",
                  "1937-01-01T12:00:27.87+00:20"):
            self.assertTrue(rfcdt.is_valid(s), s)

    def test_fields(self):
        f = rfcdt.parse("1985-04-12T23:20:50.52Z")
        self.assertEqual((f["year"], f["month"], f["day"]), (1985, 4, 12))
        self.assertEqual((f["hour"], f["minute"], f["second"]), (23, 20, 50))
        self.assertEqual(f["secfrac"], "52")
        self.assertTrue(f["offset_unknown"])

    def test_offset_unknown_semantics(self):
        self.assertTrue(rfcdt.parse("2024-01-01T00:00:00Z")["offset_unknown"])
        self.assertTrue(rfcdt.parse("2024-01-01T00:00:00-00:00")["offset_unknown"])
        self.assertFalse(rfcdt.parse("2024-01-01T00:00:00+00:00")["offset_unknown"])

    def test_lowercase_is_valid_with_warning(self):
        r = rfcdt.check("2024-01-01t00:00:00z")
        self.assertTrue(r.ok)
        self.assertIn("R3339-5.6/lowercase-letter", r.warning_codes)

    def test_space_separator_option(self):
        self.assertIn("R3339-5.6/date-time-separator", codes(rfcdt.check("2024-01-01 00:00:00Z")))
        r = rfcdt.check("2024-01-01 00:00:00Z", allow_space_separator=True)
        self.assertTrue(r.ok)
        self.assertIn("R3339-5.6/space-separator", r.warning_codes)

    def test_non_ascii_digits_rejected(self):
        self.assertFalse(rfcdt.is_valid("٢٠٢٤-01-01T00:00:00Z"))

    def test_trailing_newline_rejected(self):
        self.assertIn("R3339-5.6/trailing-characters", codes(rfcdt.check("2024-01-01T00:00:00Z\n")))

    def test_offset_ranges(self):
        self.assertTrue(rfcdt.is_valid("2024-01-01T00:00:00+23:59"))
        self.assertIn("R3339-5.6/time-numoffset-hour", codes(rfcdt.check("2024-01-01T00:00:00+24:00")))
        self.assertIn("R3339-5.6/time-numoffset-minute", codes(rfcdt.check("2024-01-01T00:00:00+00:60")))
        self.assertIn("R3339-5.6/time-numoffset", codes(rfcdt.check("2024-01-01T00:00:00+0000")))

    def test_hour_24(self):
        self.assertIn("R3339-5.7/time-hour-24", codes(rfcdt.check("2024-01-01T24:00:00Z")))

    def test_non_string(self):
        self.assertFalse(rfcdt.check(None).ok)

    def test_bad_options_raise(self):
        with self.assertRaises(ValueError):
            rfcdt.check("x", profile="iso")
        with self.assertRaises(ValueError):
            rfcdt.check("x", profile="ixdtf", production="full-date")

    def test_syntax_reported_before_semantics(self):
        # the §5.7 day limit must not hide a syntax error later in the string
        self.assertEqual(codes(rfcdt.check("2023-02-30Tgarbage")), ["R3339-5.6/time-hour"])
        self.assertEqual(codes(rfcdt.check("2023-02-30T00:00:00Zjunk")),
                         ["R3339-5.6/trailing-characters"])
        self.assertEqual(codes(rfcdt.check("2023-02-30T00:00:00Z[x]", "ixdtf")),
                         ["R3339-5.7/date-mday"])
        self.assertEqual(codes(rfcdt.check("2023-02-30T00:00:00Z[!x]]", "ixdtf")),
                         ["R9557-4.1/suffix-syntax"])
        self.assertEqual(codes(rfcdt.check("2023-02-30", production="full-date")),
                         ["R3339-5.7/date-mday"])
        # and the date error suppresses leap-second checks on an impossible date
        self.assertEqual(codes(rfcdt.check("2023-02-30T23:59:60Z")), ["R3339-5.7/date-mday"])

    def test_control_and_lookalike_chars(self):
        for s in ("2024-01-01T00:00:00Z\x00", "2024-01-01T00:00:00Z\r", "\ufeff2024-01-01T00:00:00Z",
                  "2024-01-01\uff3400:00:00Z", "2024-01-01T00\uff1a00:00Z",
                  "2024-01-01\u00a000:00:00Z"):
            self.assertFalse(rfcdt.is_valid(s), repr(s))
            self.assertFalse(rfcdt.is_valid(s, allow_space_separator=True), repr(s))

    def test_long_fraction(self):
        frac = "9" * 5000
        self.assertEqual(rfcdt.parse(f"2024-01-01T00:00:00.{frac}Z")["secfrac"], frac)

    def test_parse_raises(self):
        with self.assertRaises(ValueError) as cm:
            rfcdt.parse("2024-02-30T00:00:00Z")
        self.assertIn("R3339-5.7/date-mday", str(cm.exception))


class TestDates(unittest.TestCase):
    def test_leap_years(self):
        for y, leap in ((2024, True), (2023, False), (1900, False), (2000, True), (0, True),
                        (2100, False)):
            self.assertEqual(rfcdt.is_leap_year(y), leap, y)
            self.assertEqual(rfcdt.is_valid(f"{y:04d}-02-29T00:00:00Z"), leap, y)

    def test_month_lengths(self):
        for m in range(1, 13):
            dim = rfcdt.days_in_month(2023, m)
            self.assertTrue(rfcdt.is_valid(f"2023-{m:02d}-{dim:02d}T00:00:00Z"))
            if dim < 31:
                self.assertIn("R3339-5.7/date-mday",
                              codes(rfcdt.check(f"2023-{m:02d}-{dim + 1:02d}T00:00:00Z")))


class TestLeapSeconds(unittest.TestCase):
    def test_default_is_iers_months(self):
        self.assertEqual(rfcdt.DEFAULT_LEAP_MODE, "iers-months")
        self.assertEqual(rfcdt.check("x").options["leap_seconds"], "iers-months")
        self.assertTrue(rfcdt.is_valid("2016-12-31T23:59:60Z"))
        self.assertTrue(rfcdt.is_valid("2017-01-01T00:59:60+01:00"))
        self.assertIn("R3339-5.7/leap-second-offset",
                      codes(rfcdt.check("2016-12-31T23:59:60+01:00")))
        self.assertIn("R3339-5.7/leap-second-position",
                      codes(rfcdt.check("2016-12-30T23:59:60Z")))
        for d in ("2016-03-31", "2016-06-30", "2016-09-30", "2024-12-31", "1972-03-31"):
            self.assertTrue(rfcdt.is_valid(d + "T23:59:60Z"), d)
        self.assertEqual(codes(rfcdt.check("2016-01-31T23:59:60Z")),
                         ["R3339-AppD/leap-second-month"])
        self.assertEqual(codes(rfcdt.check("1971-12-31T23:59:60Z")),
                         ["R3339-AppD/leap-second-pre-1972"])
        # month/year are judged in UTC: local 2017-01-01 at +01:00 is 2016-12-31Z
        self.assertTrue(rfcdt.is_valid("2017-01-01T00:59:60+01:00"))
        # UTC 2016-11-30T23:59:60Z shown at +01:00 is local 12-01: month 11 -> rejected
        self.assertIn("R3339-AppD/leap-second-month",
                      codes(rfcdt.check("2016-12-01T00:59:60+01:00")))

    def test_any_month_end_mode(self):
        kw = {"leap_seconds": "any-month-end"}
        self.assertTrue(rfcdt.is_valid("2016-01-31T23:59:60Z", **kw))
        self.assertTrue(rfcdt.is_valid("1971-12-31T23:59:60Z", **kw))
        self.assertIn("R3339-5.7/leap-second-position",
                      codes(rfcdt.check("2016-12-30T23:59:60Z", **kw)))

    def test_old_mode_names_rejected(self):
        with self.assertRaises(ValueError):
            rfcdt.check("x", leap_seconds="any")

    def test_table_mode(self):
        self.assertTrue(rfcdt.is_valid("2016-12-31T23:59:60Z", leap_seconds="table"))
        self.assertIn("R3339-AppD/leap-second-table",
                      codes(rfcdt.check("2016-06-30T23:59:60Z", leap_seconds="table")))
        self.assertEqual(len(rfcdt.LEAP_SECONDS), 27)
        self.assertEqual(rfcdt.LEAP_SECONDS_CUTOFF, "2016-12-31")

    def test_grammar_mode(self):
        self.assertTrue(rfcdt.is_valid("2016-12-31T12:00:60Z", leap_seconds="grammar"))
        self.assertTrue(rfcdt.is_valid("2016-12-30T23:59:60Z", leap_seconds="grammar"))
        self.assertFalse(rfcdt.is_valid("2016-12-31T12:00:61Z", leap_seconds="grammar"))

    def test_full_time_unverifiable(self):
        r = rfcdt.check("00:59:60+01:00", production="full-time")
        self.assertTrue(r.ok)
        self.assertIn("R3339-5.7/leap-second-unverifiable", r.warning_codes)

    def test_year_boundary_shift(self):
        # 1990-12-31T23:59:60Z expressed at +14:00 lands on 1991-01-01
        self.assertTrue(rfcdt.is_valid("1991-01-01T13:59:60+14:00", leap_seconds="table"))


class TestIXDTF(unittest.TestCase):
    def ix(self, s, **kw):
        return rfcdt.check(s, "ixdtf", **kw)

    def test_suffix_fields(self):
        r = self.ix("1996-12-19T16:39:57-08:00[America/Los_Angeles][!u-ca=hebrew]")
        self.assertTrue(r.ok, r.errors)
        self.assertEqual(r.fields["time_zone"]["name"], "America/Los_Angeles")
        self.assertFalse(r.fields["time_zone"]["critical"])
        self.assertEqual(r.fields["tags"][0]["key"], "u-ca")
        self.assertTrue(r.fields["tags"][0]["critical"])

    def test_critical_unknown_key(self):
        self.assertIn("R9557-3.3/critical-unknown-key", codes(self.ix("2022-07-08T00:14:07Z[!knort=blargel]")))
        r = self.ix("2022-07-08T00:14:07Z[knort=blargel]")
        self.assertTrue(r.ok)
        self.assertIn("R9557-3.3/elective-unknown-key", r.warning_codes)

    def test_experimental(self):
        self.assertIn("R9557-3.2/experimental-key", codes(self.ix("2022-07-08T00:14:07Z[_x=y]")))
        self.assertTrue(self.ix("2022-07-08T00:14:07Z[_x=y]", experimental_keys=["_x"]).ok)

    def test_duplicates(self):
        r = self.ix("2022-07-08T00:14:07Z[u-ca=chinese][u-ca=japanese]")
        self.assertTrue(r.ok)
        self.assertEqual(r.fields["effective_tags"]["u-ca"], "chinese")
        self.assertFalse(self.ix("2022-07-08T00:14:07Z[u-ca=chinese][!u-ca=japanese]").ok)

    def test_tz_position(self):
        self.assertIn("R9557-4.1/time-zone-position",
                      codes(self.ix("2022-07-08T00:14:07Z[u-ca=hebrew][Europe/Paris]")))

    def test_tz_name_syntax(self):
        for bad in ("[.]", "[..]", "[a/../b]", "[]", "[a//b]", "[1a]"):
            self.assertIn("R9557-4.1/time-zone-name",
                          codes(self.ix("2022-07-08T00:14:07Z" + bad)), bad)

    def test_offset_time_zone(self):
        self.assertTrue(self.ix("2022-07-08T00:14:07+08:45[!+08:45]").ok)
        self.assertIn("R9557-3.4/critical-inconsistency",
                      codes(self.ix("2022-07-08T00:14:07+08:45[!+08:00]")))
        self.assertTrue(self.ix("2022-07-08T00:14:07Z[!+08:00]").ok)

    def test_rfc3339_profile_rejects_suffix(self):
        self.assertIn("R3339-5.6/trailing-characters",
                      codes(rfcdt.check("2022-07-08T00:14:07Z[Europe/Paris]")))

    @unittest.skipUnless(TZ, "needs tz data")
    def test_tz_inconsistency(self):
        self.assertIn("R9557-3.4/critical-inconsistency",
                      codes(self.ix("2022-07-08T00:14:07+01:00[!Europe/Paris]")))
        r = self.ix("2022-07-08T00:14:07+01:00[Europe/Paris]")
        self.assertTrue(r.ok)
        self.assertIn("R9557-3.4/elective-inconsistency", r.warning_codes)
        self.assertTrue(self.ix("2022-07-08T00:14:07Z[!Europe/Paris]").ok)
        self.assertTrue(r.fields["tz_checked"])

    @unittest.skipUnless(TZ, "needs tz data")
    def test_unknown_zone(self):
        self.assertIn("R9557-4.1/critical-unknown-time-zone",
                      codes(self.ix("2022-07-08T00:14:07Z[!Mars/Base]")))

    def test_tzdata_off_critical_is_unprocessable(self):
        # §3.3: MUST NOT act on the string unless the critical tag can be processed
        for s in ("2022-07-08T00:14:07+01:00[!Europe/Paris]", "2022-07-08T00:14:07Z[!Europe/Paris]",
                  "2022-07-08T02:14:07+02:00[!Europe/Paris]"):
            r = self.ix(s, tzdata="off")
            self.assertEqual(codes(r), ["R9557-3.3/critical-unprocessable"], s)
            self.assertFalse(r.fields["tz_checked"])

    def test_tzdata_off_elective_is_warning(self):
        r = self.ix("2022-07-08T00:14:07+01:00[Europe/Paris]", tzdata="off")
        self.assertTrue(r.ok)
        self.assertIn("R9557-3.4/time-zone-unchecked", r.warning_codes)
        self.assertFalse(r.fields["tz_checked"])

    def test_offset_zone_needs_no_tzdata(self):
        self.assertTrue(self.ix("2022-07-08T00:14:07+01:00[!+01:00]", tzdata="off").ok)

    @unittest.skipUnless(TZ, "needs tz data")
    def test_out_of_range_critical_unprocessable(self):
        for s in ("0000-01-01T00:00:00+01:00[!Europe/Paris]", "0000-06-01T00:00:00Z[!Europe/Paris]",
                  "0001-01-01T00:00:00+01:00[!Europe/Paris]"):
            self.assertIn("R9557-3.3/critical-unprocessable", codes(self.ix(s)), s)
        r = self.ix("0000-01-01T00:00:00+01:00[Europe/Paris]")
        self.assertTrue(r.ok)
        self.assertIn("R9557-3.4/time-zone-unchecked", r.warning_codes)
        self.assertTrue(self.ix("0001-01-01T12:00:00Z[!Europe/Paris]").ok)

    @unittest.skipUnless(TZ, "needs tz data")
    def test_unknown_critical_zone_codes(self):
        self.assertEqual(codes(self.ix("2022-07-08T00:14:07Z[!u-ca]")),
                         ["R9557-4.1/critical-unknown-time-zone",
                          "R9557-3.3/critical-unprocessable"])
        r = self.ix("2022-07-08T00:14:07Z[u-ca]")
        self.assertTrue(r.ok)
        self.assertEqual(r.fields["time_zone"]["name"], "u-ca")
        self.assertEqual(r.fields["tags"], [])

    def test_identical_elective_duplicates_warn(self):
        r = self.ix("2022-07-08T00:14:07Z[u-ca=hebrew][u-ca=hebrew]")
        self.assertTrue(r.ok)
        self.assertIn("R9557-3.3/duplicate-elective-key", r.warning_codes)
        r = self.ix("2022-07-08T00:14:07Z[!u-ca=hebrew][u-ca=hebrew]")
        self.assertTrue(r.ok)
        self.assertNotIn("R9557-3.3/duplicate-elective-key", r.warning_codes)
        self.assertEqual(codes(self.ix("2022-07-08T00:14:07Z[!a=b][a=b]")),
                         ["R9557-3.3/critical-unknown-key"])

    def test_critical_configured_experimental_key(self):
        self.assertTrue(self.ix("2022-07-08T00:14:07Z[!_foo=bar]", experimental_keys=["_foo"]).ok)

    def test_suffix_on_full_date_rejected(self):
        self.assertIn("R3339-5.6/date-time-separator",
                      codes(self.ix("2022-07-08[Europe/Paris]")))


class TestCLI(unittest.TestCase):
    def run_cli(self, *args, stdin=b"", env=None):
        e = dict(os.environ)
        e.update(env or {})
        return subprocess.run([sys.executable, RFCDT, *args], input=stdin,
                              capture_output=True, env=e)

    def test_check_json(self):
        cp = self.run_cli("check", "2016-12-31T23:59:60+01:00", "--json")
        self.assertEqual(cp.returncode, 1)
        out = json.loads(cp.stdout)
        self.assertFalse(out["ok"])
        self.assertEqual(out["errors"][0]["code"], "R3339-5.7/leap-second-offset")

    def test_check_text_valid(self):
        cp = self.run_cli("check", "--profile", "ixdtf", "2022-07-08T00:14:07Z[u-ca=hebrew]")
        self.assertEqual(cp.returncode, 0)
        self.assertTrue(cp.stdout.startswith(b"VALID"))

    def test_check_double_dash(self):
        cp = self.run_cli("check", "--json", "--", "-0001-01-01T00:00:00Z")
        self.assertEqual(cp.returncode, 1)
        self.assertEqual(json.loads(cp.stdout)["errors"][0]["code"], "R3339-5.6/date-fullyear")

    def test_leap_help_documents_modes(self):
        cp = self.run_cli("check", "--help")
        for m in (b"iers-months", b"any-month-end", b"1972", b"2016-12-31"):
            self.assertIn(m, cp.stdout)

    def test_adapter(self):
        cp = self.run_cli("adapter", stdin=b"2024-01-01T00:00:00Z")
        self.assertTrue(json.loads(cp.stdout)["ok"])
        cp = self.run_cli("adapter", stdin=b"2024-01-01T00:00:00Z\n")
        self.assertFalse(json.loads(cp.stdout)["ok"])
        cp = self.run_cli("adapter", stdin=b"2024-06-30T23:59:60Z",
                          env={"RFCDT_OPTIONS": '{"leap_seconds": "table"}'})
        self.assertFalse(json.loads(cp.stdout)["ok"])


class TestScan(unittest.TestCase):
    SAMPLES = {
        "a.py": [
            ('ts = now.strftime("%Y-%m-%dT%H:%M:%S%z")', "SCAN-STRFTIME-Z"),
            ('s = datetime.now().isoformat() + "Z"', "SCAN-ISOFORMAT-PLUS-Z"),
            ("d = datetime.fromisoformat(request.args['t'])", "SCAN-PY-FROMISOFORMAT"),
            ('local.strftime("%Y-%m-%dT%H:%M:%SZ")', "SCAN-LITERAL-Z"),
            ("RX = re.compile(r'\\d{4}-\\d{1,2}-\\d{1,2}')", "SCAN-REGEX-SHORT-FIELD"),
            ("RX = re.compile(r'\\d{4}-\\d{2}-\\d{2}T')", "SCAN-REGEX-UNANCHORED"),
            ("RX = re.compile(r'^\\d{4}-\\d{2}-\\d{2}$')", "SCAN-REGEX-UNICODE-DIGIT"),
        ],
        "b.js": [("const t = Date.parse(input);", "SCAN-JS-DATE-PARSE")],
        "c.cs": [("var d = DateTime.Parse(s);", "SCAN-NET-PARSE")],
        "d.java": [
            ("String out = zonedDateTime.toString();", None),
            ("String out = ZonedDateTime.now().toString();", "SCAN-JAVA-TOSTRING"),
            ('fmt = "yyyy-MM-dd\'T\'HH:mm:ssZ";', "SCAN-JAVA-OFFSET-PATTERN"),
        ],
        "e.go": [('t.Format("2006-01-02T15:04:05Z")', "SCAN-LITERAL-Z")],
        "f.php": [("$s = $d->format(DATE_ISO8601);", "SCAN-PHP-ISO8601")],
    }

    def test_patterns_hit(self):
        for fname, rows in self.SAMPLES.items():
            for line, pid in rows:
                ids = {x["id"] for x in rfcdt.scan_text(line, fname)}
                if pid:
                    self.assertIn(pid, ids, f"{fname}: {line}")

    def test_clean_lines(self):
        clean = [
            ("t = now.strftime('%Y-%m-%dT%H:%M:%S%:z')", "a.py"),
            ("t = datetime.now(timezone.utc).isoformat()", "a.py"),
            ("RX = re.compile(r'\\A[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\\Z')", "a.py"),
            ("var d = DateTimeOffset.ParseExact(s, fmt, CultureInfo.InvariantCulture);", "c.cs"),
            ('t.Format(time.RFC3339)', "e.go"),
            ("x = datetime.fromisoformat(s)  # rfcdt: ignore", "a.py"),
        ]
        for line, fname in clean:
            self.assertEqual(rfcdt.scan_text(line, fname), [], line)

    def test_scan_paths_and_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "m.py")
            with open(p, "w") as fh:
                fh.write("import datetime\nx = datetime.datetime.fromisoformat(s)\n")
            os.mkdir(os.path.join(d, "node_modules"))
            with open(os.path.join(d, "node_modules", "z.js"), "w") as fh:
                fh.write("Date.parse(x)\n")
            f = rfcdt.scan_paths([d])
            self.assertEqual([(x["line"], x["id"]) for x in f], [(2, "SCAN-PY-FROMISOFORMAT")])
            cp = subprocess.run([sys.executable, RFCDT, "scan", d], capture_output=True)
            self.assertEqual(cp.returncode, 1)
            self.assertIn(b"m.py:2: SCAN-PY-FROMISOFORMAT", cp.stdout)

    def test_pattern_table_shape(self):
        ids = [p[0] for p in rfcdt.SCAN_PATTERNS]
        self.assertEqual(len(ids), len(set(ids)))
        for row in rfcdt.SCAN_PATTERNS:
            self.assertEqual(len(row), 8)
            self.assertRegex(row[1], r"^R(3339|9557)-")
            self.assertIn(row[5], ("error", "warn", "info"))
            self.assertTrue(row[7], f"{row[0]} needs a safe replacement")
        self.assertTrue(set(rfcdt._SCAN_CONTEXT) <= set(ids))

    def test_findings_carry_fix(self):
        f = rfcdt.scan_text("x = datetime.fromisoformat(s)", "a.py")
        self.assertTrue(f and f[0]["fix"])

    def _ids(self, text, fname):
        return [(x["line"], x["id"]) for x in rfcdt.scan_text(text, fname)]

    def test_js_new_date_numeric_not_flagged(self):
        for line in ("iso: new Date(epochMs).toISOString(),", "const d = new Date(Date.now());",
                     "new Date(ms)", "new Date(2024, 0, 1)", "const t = new Date();"):
            self.assertNotIn("SCAN-JS-DATE-PARSE", {i for _, i in self._ids(line, "x.mjs")}, line)
        for line in ("new Date(input)", "new Date('2024-01-01')", "new Date(`${d}T00:00`)",
                     "new Date(dateStr)", "new Date(req.body.when)", "new Date(s)",
                     "new Date(row.isoText)", "Date.parse(x)"):
            self.assertIn("SCAN-JS-DATE-PARSE", {i for _, i in self._ids(line, "x.mjs")}, line)

    def test_py_regex_dollar_multiline(self):
        src = ('import re\n_RE = re.compile(\n    r"(?P<y>[0-9]{4})-(?P<m>[0-9]{2})"\n'
               '    r"(?P<off>Z|[+-][0-9]{2}:[0-9]{2})$"\n)\n'
               'def p(t):\n    return _RE.match(t)\n')
        self.assertIn((4, "SCAN-PY-REGEX-DOLLAR"), self._ids(src, "t.py"))
        fixed = src.replace('$"', '\\Z"')
        self.assertNotIn("SCAN-PY-REGEX-DOLLAR", {i for _, i in self._ids(fixed, "t.py")})
        full = src.replace("_RE.match(t)", "_RE.fullmatch(t)")
        self.assertNotIn("SCAN-PY-REGEX-DOLLAR", {i for _, i in self._ids(full, "t.py")})
        # '$' with no date component in the statement
        other = 'import re\nA = re.compile(r"[a-z]+$")\nB = re.compile(r"[0-9]{4}")\nA.match(x)\n'
        self.assertNotIn("SCAN-PY-REGEX-DOLLAR", {i for _, i in self._ids(other, "t.py")})

    def test_js_regexp_without_caret(self):
        head = "const DATE = '(\\\\d{4})-(\\\\d{2})-(\\\\d{2})';\n"
        bad = head + "const RE = new RegExp(DATE + TIME + '$');\n"
        self.assertIn((2, "SCAN-JS-REGEXP-NO-CARET"), self._ids(bad, "p.mjs"))
        good = head + "const RE = new RegExp('^' + DATE + TIME + '$');\n"
        self.assertNotIn("SCAN-JS-REGEXP-NO-CARET", {i for _, i in self._ids(good, "p.mjs")})
        nodate = "const RE = new RegExp(NAME + '$');\n"
        self.assertEqual(self._ids(nodate, "p.mjs"), [])

    def test_naive_now_sources(self):
        hits = [("created: datetime = field(default_factory=datetime.now)", True),
                ("t = datetime.now()", True), ("t = datetime.utcnow()", True),
                ("t = datetime.now(timezone.utc)", False),
                ("LOCAL = datetime.now().astimezone().tzinfo", False),
                ("f = field(default_factory=lambda: datetime.now(timezone.utc))", False)]
        for line, want in hits:
            got = "SCAN-PY-NAIVE-NOW" in {i for _, i in self._ids(line, "a.py")}
            self.assertEqual(got, want, line)

    def test_no_seconds_format(self):
        for line, want in (('FMT = "%Y-%m-%dT%H:%M"', True), ('f = "%Y-%m-%dT%H:%M%z"', True),
                           ('p = "yyyy-MM-dd\'T\'HH:mmXXX"', True),
                           ('FMT = "%Y-%m-%dT%H:%M:%S%z"', False), ('label = "%H:%M"', False)):
            ext = "a.java" if "yyyy" in line else "a.py"
            got = "SCAN-NO-SECONDS" in {i for _, i in self._ids(line, ext)}
            self.assertEqual(got, want, line)

    def test_tz_str_suffix(self):
        src = ('def label(tz):\n    return getattr(tz, "key", None) or str(tz)\n'
               'def fmt(dt):\n    return dt.isoformat() + f"[{label(dt.tzinfo)}]"\n')
        self.assertIn((2, "SCAN-PY-TZ-STR"), self._ids(src, "a.py"))
        self.assertIn((1, "SCAN-PY-TZ-STR"), self._ids('s = "[" + dt.tzname() + "]"', "a.py"))
        self.assertEqual(self._ids("print(str(tz))", "a.py"), [])  # no suffix built

    def test_utc_isoformat_advisory(self):
        for line in ("datetime.fromtimestamp(s, tz=timezone.utc).isoformat()",
                     "x = dt.astimezone(timezone.utc).isoformat(timespec='seconds')"):
            f = [x for x in rfcdt.scan_text(line, "a.py") if x["id"] == "SCAN-PY-UTC-ISOFORMAT"]
            self.assertTrue(f, line)
            self.assertEqual(f[0]["severity"], "info")
        self.assertEqual(self._ids("t = datetime.now(timezone.utc).isoformat()", "a.py"), [])

    def test_js_date_utc_year_and_last_wins(self):
        self.assertIn("SCAN-JS-DATE-UTC-YEAR",
                      {i for _, i in self._ids("const w = Date.UTC(year, month - 1, day);", "p.js")})
        self.assertEqual(self._ids("const w = Date.UTC(2000, 0, 1);", "p.js"), [])
        self.assertIn("SCAN-TAG-LAST-WINS",
                      {i for _, i in self._ids("    out.tags[key] = value;", "p.mjs")})
        self.assertIn("SCAN-TAG-LAST-WINS", {i for _, i in self._ids("tags[k] = v", "p.py")})
        for ok in ("out.tags[key] ??= value;", "if (out.tags[key] === value) {}",
                   "tags.setdefault(k, v)"):
            self.assertNotIn("SCAN-TAG-LAST-WINS",
                             {i for _, i in self._ids(ok, "p.mjs" if ";" in ok or "{" in ok
                                                      else "p.py")}, ok)

    # id -> (file name, positive source, negative source).  Each positive must
    # produce the id, each negative must not.
    GO_RUST_SAMPLES = {
        "SCAN-GO-PARSE-LENIENT": (
            "p.go", "t, err := time.Parse(time.RFC3339, s)",
            "t, err := parseRFC3339Strict(s)"),
        "SCAN-GO-JSON-V1-TIME": (
            "p.go", 'import "encoding/json"\ntype E struct {\n\tAt time.Time `json:"at"`\n}\n',
            'import json "encoding/json/v2"\ntype E struct {\n\tAt time.Time `json:"at"`\n}\n'),
        "SCAN-GO-OFFSET-SECONDS": (
            "p.go", 'z := time.FixedZone("LMT", -2670)\ns := t.In(z).Format(time.RFC3339)\n',
            'z := time.FixedZone("CET", 3600)\ns := t.UTC().Format(time.RFC3339)\n'),
        "SCAN-GO-OFFSET-NO-COLON": (
            "p.go", 's := t.Format("2006-01-02T15:04:05-0700")',
            's := t.Format("2006-01-02T15:04:05Z07:00")'),
        "SCAN-GO-NON-RFC-LAYOUT": (
            "p.go", 's := t.Format("2006-01-02 15:04:05Z07:00")',
            "s := t.Format(time.RFC3339Nano)"),
        "SCAN-GO-STRING": (
            "p.go", 'body := fmt.Sprintf(`{"at":"%s"}`, createdAt.String())',
            "name := user.String()"),
        "SCAN-GO-NANO-SORT": (
            "p.go", "sortKey := t.UTC().Format(time.RFC3339Nano)",
            "msg := t.UTC().Format(time.RFC3339Nano)"),
        "SCAN-GO-ZERO-OMITEMPTY": (
            "p.go", 'At time.Time `json:"at,omitempty"`',
            'At time.Time `json:"at,omitzero"`'),
        "SCAN-GO-ZONELESS-PARSE": (
            "p.go", 't, _ := time.Parse("2006-01-02T15:04:05", s)',
            't, _ := time.Parse(time.RFC3339, s)'),
        "SCAN-GO-FIXED-FRACTION-PARSE": (
            "p.go", 't, _ := time.Parse("2006-01-02T15:04:05.000Z07:00", s)',
            's := t.UTC().Format("2006-01-02T15:04:05.000000000Z07:00")'),
        "SCAN-RS-CHRONO-FROMSTR": (
            "p.rs", "let t = s.parse::<DateTime<Utc>>()?;",
            "let t = DateTime::parse_from_rfc3339(s)?;"),
        "SCAN-RS-SERDE-CHRONO": (
            "p.rs", "#[derive(Deserialize)]\nstruct E {\n    pub at: DateTime<Utc>,\n}\n",
            "#[derive(Deserialize)]\nstruct E {\n    #[serde(deserialize_with = \"strict\")]\n"
            "    pub at: DateTime<Utc>,\n}\n"),
        "SCAN-RS-CHRONO-TO-RFC3339": (
            "p.rs", "let s = dt.to_rfc3339();",
            "let s = dt.with_timezone(&Utc).to_rfc3339_opts(SecondsFormat::AutoSi, true);"),
        "SCAN-RS-DISPLAY": (
            "p.rs", "let s = created_at.to_string();",
            "let s = dt.format(\"%Y\").to_string();"),
        "SCAN-RS-TIME-ISO8601": (
            "p.rs", "let t = OffsetDateTime::parse(s, &Iso8601::DEFAULT)?;",
            "let t = OffsetDateTime::parse(s, &Rfc3339)?;"),
        "SCAN-RS-TIME-SERDE-DEFAULT": (
            "p.rs", "#[derive(Serialize)]\nstruct E {\n    at: OffsetDateTime,\n}\n",
            "#[derive(Serialize)]\nstruct E {\n    #[serde(with = \"time::serde::rfc3339\")]\n"
            "    at: OffsetDateTime,\n}\n"),
        "SCAN-RS-TIME-RFC3339-VALIDATOR": (
            "p.rs", "let ok = OffsetDateTime::parse(s, &Rfc3339).is_ok();",
            "let s = t.format(&Rfc3339)?;"),
        "SCAN-RS-JIFF-TIMESTAMP-PARSE": (
            "p.rs", "let ts = s.parse::<jiff::Timestamp>()?;",
            "let z = s.parse::<jiff::Zoned>()?;"),
    }

    def test_go_rust_patterns(self):
        new_ids = {p[0] for p in rfcdt.SCAN_PATTERNS
                   if p[0].startswith(("SCAN-GO-", "SCAN-RS-"))}
        self.assertEqual(new_ids, set(self.GO_RUST_SAMPLES))
        for pid, (fname, pos, neg) in self.GO_RUST_SAMPLES.items():
            self.assertIn(pid, {i for _, i in self._ids(pos, fname)}, f"{pid}: {pos!r}")
            self.assertNotIn(pid, {i for _, i in self._ids(neg, fname)}, f"{pid}: {neg!r}")
        # language gating: a Go pattern does not fire in a .py file
        self.assertEqual(self._ids("t, err := time.Parse(time.RFC3339, s)", "p.py"), [])

    def test_go_offset_seconds_context(self):
        pid = "SCAN-GO-OFFSET-SECONDS"
        for line, want in (('z := time.FixedZone("x", 30)', True),
                           ('z := time.FixedZone("x", 5*60*60)', False),
                           ('z := time.FixedZone("x", 24*3600)', True),
                           ('z := time.FixedZone("x", off)', True),
                           ("loc, _ := time.LoadLocation(name)", True),
                           ("s := t.Format(time.RFC3339)", False)):
            got = pid in {i for _, i in self._ids(line, "p.go")}
            self.assertEqual(got, want, line)

    def test_rust_extended_shared_patterns(self):
        for line, pid in (('d.format("%Y-%m-%dT%H:%M:%S%.3fZ")', "SCAN-LITERAL-Z"),
                          ('format_description!("[hour]:[minute]:[second]Z")', "SCAN-LITERAL-Z"),
                          ('format_description!("[second][subsecond digits:3]Z")', "SCAN-LITERAL-Z"),
                          ('d.format("%Y-%m-%dT%H:%M:%S%.3f%z")', "SCAN-STRFTIME-Z"),
                          ('ts.strftime("%Y-%m-%dT%H:%M:%S%z")', "SCAN-STRFTIME-Z"),
                          ('format_description!("[offset_hour sign:mandatory][offset_minute]")',
                           "SCAN-STRFTIME-Z"),
                          ('t, _ := time.Parse("2006-01-02T15:04:05Z", s)', "SCAN-LITERAL-Z")):
            fname = "p.go" if "time.Parse" in line else "p.rs"
            self.assertIn(pid, {i for _, i in self._ids(line, fname)}, line)
        for line in ('d.format("%Y-%m-%dT%H:%M:%S%.3f%:z")', 'ts.strftime("%Y-%m-%dT%H:%M:%S%:z")',
                     'format_description!("[offset_hour sign:mandatory]:[offset_minute]")',
                     'utc.format("%Y-%m-%dT%H:%M:%S%.3fZ")'):
            self.assertEqual(self._ids(line, "p.rs"), [], line)

    def test_go_rust_eval_samples(self):
        root = os.path.join(HERE, "..", "probes")
        go = os.path.join(root, "go", "testdata", "risky_go.txt")
        rs = os.path.join(root, "rust", "scan-sample", "sample.rs")
        if not (os.path.isfile(go) and os.path.isfile(rs)):
            self.skipTest("eval samples not present")
        with open(go) as fh:
            lines = fh.read()
        hit = {ln for ln, _ in self._ids(lines, "risky.go")}
        # every sample line except the correct Z07:00 layout (line 14)
        self.assertEqual(hit, set(range(1, 20)) - {14})
        with open(rs) as fh:
            hit = {ln for ln, _ in self._ids(fh.read(), "sample.rs")}
        self.assertEqual(hit, set(range(1, 9)))

    @unittest.skipUnless(os.path.isdir(AUDIT_TARGET), "audit regression fixture not present")
    def test_audit_target_regression(self):
        # Blind-audit fixture: these were false negatives / a false positive.
        found = {(os.path.relpath(x["file"], AUDIT_TARGET), x["line"])
                 for x in rfcdt.scan_paths([AUDIT_TARGET])}
        for want in (("timeutil.py", 25), ("timeutil.py", 14), ("timeutil.py", 66),
                     ("timeutil.py", 70), ("api.py", 25), ("client/parse.mjs", 13),
                     ("client/parse.mjs", 51), ("client/parse.mjs", 77)):
            self.assertIn(want, found)
        self.assertNotIn(("client/parse.mjs", 97), found)


GLIDE = "var gdt = new GlideDateTime();\n"
FLUENT = "import { Record, Time, ScheduledScript } from '@servicenow/sdk/core'\n"
SN_SDK = os.path.abspath(os.path.join(HERE, "..", "..", "..", "snsdk", "node_modules",
                                      "@servicenow"))


class TestScanJsHostZoneAndServiceNow(unittest.TestCase):
    # id -> (file name, [positive sources], [negative sources]).  Each positive
    # must produce the id, each negative must not.
    SAMPLES = {
        "SCAN-JS-LOCAL-DATE-PARTS": ("t.js", [
            "const d = new Date(y, m - 1, day, h, mi, s);",
            "const epoch = new Date(1970, 0, 1, 0, 0, 0);",
            "return new Date(1970, 0, // January\n    1, hours, minutes, seconds);",
            "const d = new Date(\n  c.year,\n  c.month - 1,\n  c.day,\n  c.hours\n)",
            "const n = new Date(year!, month!, day!)",
        ], [
            "const d = new Date(Date.UTC(y, m - 1, d));",
            "const d = new Date(ms);", "const d = new Date();",
            "const d = new Date(y, m);",
            "// new Date(1982, 0, 1) is local midnight",
            "const s = new Date('2024', '01', '01');",
        ]),
        "SCAN-JS-FLOOR-MOD-SPLIT": ("t.ts", [
            "return new Date(Date.UTC(1970, 0, 1, Math.floor(totalMinutes / 60), totalMinutes % 60, s));",
            "const h = Math.floor(off / 60);\nconst m = off % 60;",
            "const m = off % 60;\nconst h = Math.floor(off / 60);",
        ], [
            "const h = Math.floor(off / 60);\nconst m = ((off % 60) + 60) % 60;",
            "const h = Math.floor(off / 60);\nconst m = other % 60;",
            "if (off < 0) sign = -1;\nconst h = Math.floor(off / 60);\nconst m = off % 60;",
            "const h = Math.floor(off / 60);\n\n\nconst m = off % 60;",
        ]),
        "SCAN-JS-INTL-HOUR-OFFSET": ("t.js", [
            "const s = d.toLocaleString('en-US', {timeZone, hour12: false});\n"
            "const off = (tzHour - 12) * 60 + tzMin;",
        ], [
            "const off = (tzHour - 12) * 60 + tzMin;",  # no hour12:false in the file
            "const f = new Intl.DateTimeFormat('en', {hour12: false});\nconst x = hours + 12;",
        ]),
        "SCAN-SN-STRING-SURGERY": ("br.js", [
            GLIDE + "var iso = gdt.getValue().replace(' ', 'T') + 'Z';",
            GLIDE + "var s = gdt.getDisplayValue() + 'Z';",
            GLIDE + "var s = d + 'T' + gdt.getValue();",
            GLIDE + "body.at = current.sys_updated_on.toString().replace(/ /g, 'T');",
        ], [
            GLIDE + "var iso = new Date(Number(String(gdt.getNumericValue()))).toISOString();",
            "var iso = row.when.replace(' ', 'T') + 'Z';",  # not a Glide script
            GLIDE + "var s = gdt.getValue() + ' UTC';",
        ]),
        "SCAN-SN-DISPLAY-VALUE-OUT": ("rest.js", [
            "var r = new sn_ws.RESTMessageV2('x', 'post');\n"
            "r.setRequestBody(JSON.stringify({opened: current.opened_at.getDisplayValue()}));",
            "var r = new sn_ws.RESTMessageV2('x', 'post');\nvar body = {now: gs.nowDateTime()};",
        ], [
            "gs.info(current.opened_at.getDisplayValue());",  # no integration context
            "var r = new sn_ws.RESTMessageV2('x', 'post');\n"
            "r.setRequestBody(JSON.stringify({who: current.caller_id.getDisplayValue()}));",
        ]),
        "SCAN-SN-GDT-UNCHECKED": ("si.js", [
            "var g = new GlideDateTime(request.body.data.when);",
            "var gdt = new GlideDateTime();\nstartDate.setValue(payload.start);",
        ], [
            "var g = new GlideDateTime(input);\nif (!g.isValid()) { throw 'bad'; }",
            "var g = new GlideDateTime(current.sys_created_on);",
            "var g = new GlideDateTime(otherGdt);",
            "var g = new GlideDateTime();\ncurrent.short_description.setValue(text);",
            "var g = new GlideDateTime('2026-01-01 00:00:00');",
        ]),
        "SCAN-SN-T-TO-SPACE": ("si.js", [
            GLIDE + "var v = input.replace('T', ' ').replace('Z', '');",
            FLUENT + "const v = s.replace(/T/, ' ')",
        ], [
            FLUENT + "const v = d.toISOString().slice(0, 19).replace('T', ' ')",
            "const v = s.replace('T', ' ');",  # not ServiceNow code
        ]),
        "SCAN-SN-SYSPARM-DISPLAY": ("client.py", [
            "url = base + '/api/now/table/incident?sysparm_display_value=true'",
            "params = {'sysparm_display_value': 'all'}",
            "q = '?sysparm_input_display_value=true'",
        ], [
            "url = base + '/api/now/table/incident?sysparm_display_value=false'",
            "params = {'sysparm_exclude_reference_link': 'true'}",
        ]),
        "SCAN-SN-FLOW-Z-FORMAT": ("flow.ts", [
            "const out = dateToString(d, \"yyyy-MM-dd'T'HH:mm:ss'Z'\")",
        ], [
            "const out = dateToString(d, 'yyyy-MM-dd HH:mm:ss')",
            "fmt = \"yyyy-MM-dd'T'HH:mm:ss'Z'\"",  # no ServiceNow marker in the file
        ]),
        "SCAN-SN-FLUENT-DT-VALUE": ("x.now.ts", [
            FLUENT + "Record({ table: 't', data: { dt: '2024-01-01T12:00:00Z' as any } })",
            FLUENT + "dt: DateTimeColumn({ label: 'DT', default: '2024-01-01 00:00:00Z' }),",
            FLUENT + "Record({ table: 't', data: { opened_at: value as any } })",
            FLUENT + "// @ts-ignore\n  due_date: '2024-01-01',",
        ], [
            FLUENT + "Record({ table: 't', data: { dt: '2024-01-01 12:00:00' } })",
            FLUENT + "ScheduledScript({ name: 'x', timeZone: 'Europe/Paris' as any })",
            "const x = { dt: '2024-01-01T12:00:00Z' as any }",  # not Fluent
            FLUENT + "// @ts-ignore\n  label: foo,",
        ]),
        "SCAN-SN-SCHEDULE-FLOATING": ("s.now.ts", [
            FLUENT + "ScheduledScript({ name: 's', executionStart: '2026-03-02 14:30:00', "
                     "timeZone: 'floating' })",
            FLUENT + "ScheduledScript({\n  name: 's',\n  executionStart: '2026-03-02 14:30:00',\n"
                     "  script: 'x',\n})",
        ], [
            FLUENT + "ScheduledScript({\n  name: 's',\n  executionStart: '2026-03-02 14:30:00',\n"
                     "  timeZone: 'Asia/Kolkata',\n})",
            "const o = { executionStart: '2026-03-02 14:30:00' }",  # no ScheduledScript call
        ]),
        "SCAN-SN-HOST-ZONE-CONVERT": ("p.js", [
            "const s = dateTimeFieldToXML('2026-03-02 14:30:00', 'floating');",
            "const s = (0, tz_1.convertXMLToDateTime)(v);",
            "const t = timeFieldToXML({ hours: 1, minutes: 0 });",
        ], [
            "const s = dateTimeFieldToXML('2026-03-02 14:30:00', 'UTC');",
            "const t = timeFieldToXML({ hours: 1, minutes: 0 }, timeZone);",
            "function dateTimeFieldToXML(dateTimeStr, timeZone) {",
        ]),
        "SCAN-SN-TIME-NO-ZONE": ("t.now.ts", [
            FLUENT + "executionTime: Time({ hours: 1, minutes: 0 }),",
            FLUENT + "tm: Time(\n  {\n    hours: 1,\n  }\n),",
        ], [
            FLUENT + "executionTime: Time({ hours: 1, minutes: 0 }, 'UTC'),",
            FLUENT + "tm: Time(\n  {\n    hours: 1,\n  },\n  'Asia/Kolkata'\n),",
            "const t = Time({ hours: 1 })",  # not Fluent
        ]),
    }

    def _ids(self, text, fname):
        return {x["id"] for x in rfcdt.scan_text(text, fname)}

    def test_positive_and_negative(self):
        for pid, (fname, pos, neg) in self.SAMPLES.items():
            for src in pos:
                self.assertIn(pid, self._ids(src, fname), f"{pid} should hit: {src!r}")
            for src in neg:
                self.assertNotIn(pid, self._ids(src, fname), f"{pid} should not hit: {src!r}")

    def test_every_new_pattern_has_samples(self):
        new = {p[0] for p in rfcdt.SCAN_PATTERNS
               if p[0].startswith("SCAN-SN-") or p[0] in (
                   "SCAN-JS-LOCAL-DATE-PARTS", "SCAN-JS-FLOOR-MOD-SPLIT",
                   "SCAN-JS-INTL-HOUR-OFFSET")}
        self.assertEqual(new, set(self.SAMPLES))

    def test_severities(self):
        sev = {p[0]: p[5] for p in rfcdt.SCAN_PATTERNS}
        for pid in ("SCAN-JS-INTL-HOUR-OFFSET", "SCAN-SN-SYSPARM-DISPLAY",
                    "SCAN-SN-FLOW-Z-FORMAT", "SCAN-SN-SCHEDULE-FLOATING"):
            self.assertEqual(sev[pid], "info", pid)
        for pid in ("SCAN-JS-LOCAL-DATE-PARTS", "SCAN-JS-FLOOR-MOD-SPLIT",
                    "SCAN-SN-STRING-SURGERY", "SCAN-SN-GDT-UNCHECKED", "SCAN-SN-TIME-NO-ZONE",
                    "SCAN-SN-HOST-ZONE-CONVERT", "SCAN-SN-FLUENT-DT-VALUE"):
            self.assertEqual(sev[pid], "warn", pid)

    def test_js_local_date_line_numbers(self):
        src = "a();\nreturn new Date(1970, 0, // January\n    1, hours, minutes, seconds);\n"
        hits = [(x["line"], x["id"]) for x in rfcdt.scan_text(src, "t.js")]
        self.assertEqual(hits, [(2, "SCAN-JS-LOCAL-DATE-PARTS")])

    def test_date_utc_year_on_sdk_line(self):
        line = "    const utcDate = new Date(Date.UTC(year, month - 1, day, hours, minutes, seconds));"
        ids = self._ids(line, "timeZoneConverter.js")
        self.assertIn("SCAN-JS-DATE-UTC-YEAR", ids)
        self.assertNotIn("SCAN-JS-LOCAL-DATE-PARTS", ids)

    def test_long_line_is_fast(self):
        # SCAN-REGEX-SHORT-FIELD used an unanchored (?=.*…) lookahead: quadratic
        # on minified bundles / source maps.  Must stay linear.
        import time
        line = "x" * 200_000 + "\\d{4}"
        t0 = time.monotonic()
        rfcdt.scan_text(line, "bundle.js.map")
        self.assertLess(time.monotonic() - t0, 2.0)
        self.assertIn("SCAN-REGEX-SHORT-FIELD",
                      self._ids("RX = re.compile(r'\\d{4}-\\d{1,2}')", "a.py"))


class TestScanIncludeDist(unittest.TestCase):
    def _tree(self, d):
        for sub in ("src", "dist", os.path.join("dist", "node_modules"), "node_modules"):
            os.makedirs(os.path.join(d, sub), exist_ok=True)
        for sub in ("src", "dist", os.path.join("dist", "node_modules"), "node_modules"):
            with open(os.path.join(d, sub, "a.js"), "w") as fh:
                fh.write("const t = Date.parse(input);\n")

    def _rel(self, d, findings):
        return sorted(os.path.relpath(x["file"], d) for x in findings)

    def test_default_skips_dist_and_node_modules(self):
        with tempfile.TemporaryDirectory() as d:
            self._tree(d)
            self.assertEqual(self._rel(d, rfcdt.scan_paths([d])), [os.path.join("src", "a.js")])

    def test_include_dist_keeps_node_modules_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            self._tree(d)
            got = self._rel(d, rfcdt.scan_paths([d], include_dist=True))
            self.assertEqual(got, [os.path.join("dist", "a.js"), os.path.join("src", "a.js")])

    def test_explicit_paths_always_scanned(self):
        with tempfile.TemporaryDirectory() as d:
            self._tree(d)
            nm = os.path.join(d, "node_modules")
            self.assertEqual(self._rel(d, rfcdt.scan_paths([nm])),
                             [os.path.join("node_modules", "a.js")])
            dist_file = os.path.join(d, "dist", "a.js")
            self.assertEqual(self._rel(d, rfcdt.scan_paths([dist_file])),
                             [os.path.join("dist", "a.js")])
            self.assertEqual(self._rel(d, rfcdt.scan_paths([os.path.join(d, "dist")])),
                             [os.path.join("dist", "a.js")])

    def test_cli_flag(self):
        with tempfile.TemporaryDirectory() as d:
            self._tree(d)
            cp = subprocess.run([sys.executable, RFCDT, "scan", d, "--include-dist", "--json"],
                                capture_output=True)
            self.assertEqual(cp.returncode, 1)
            files = self._rel(d, json.loads(cp.stdout)["findings"])
            self.assertIn(os.path.join("dist", "a.js"), files)
            self.assertNotIn(os.path.join("node_modules", "a.js"), files)
            cp = subprocess.run([sys.executable, RFCDT, "scan", "--json", d], capture_output=True)
            self.assertNotIn(os.path.join("dist", "a.js"),
                             self._rel(d, json.loads(cp.stdout)["findings"]))

    @unittest.skipUnless(os.path.isdir(os.path.join(SN_SDK, "sdk-build-core", "dist")),
                         "ServiceNow SDK regression fixture not present")
    def test_servicenow_sdk_regression(self):
        roots = [os.path.join(SN_SDK, "sdk-build-core"), os.path.join(SN_SDK, "sdk-build-plugins")]
        found = {(os.path.relpath(x["file"], SN_SDK), x["line"], x["id"])
                 for x in rfcdt.scan_paths(roots, include_dist=True)}
        time_js = os.path.join("sdk-build-core", "dist", "plugins", "time.js")
        tzc = os.path.join("sdk-build-plugins", "dist", "schedule-script", "timeZoneConverter.js")
        for want in ((time_js, 37, "SCAN-JS-LOCAL-DATE-PARTS"),
                     (time_js, 38, "SCAN-JS-LOCAL-DATE-PARTS"),
                     (time_js, 191, "SCAN-JS-FLOOR-MOD-SPLIT"),
                     (time_js, 195, "SCAN-JS-LOCAL-DATE-PARTS"),
                     (time_js, 187, "SCAN-JS-INTL-HOUR-OFFSET"),
                     (tzc, 92, "SCAN-JS-LOCAL-DATE-PARTS"),
                     (tzc, 133, "SCAN-JS-DATE-UTC-YEAR")):
            self.assertIn(want, found)
        # without the flag the dist copies are not reached
        plain = {os.path.relpath(x["file"], SN_SDK) for x in rfcdt.scan_paths(roots)}
        self.assertNotIn(time_js, plain)


MASTODON = os.path.expanduser("~/Documents/GitHub/mastodon")


def _ids_of(text, fname):
    return {x["id"] for x in rfcdt.scan_text(text, fname)}


class TestScanParseIdioms(unittest.TestCase):
    """T1-5: Ruby / JS / Python / C# parse idioms missed before."""
    # id -> (file name, [positive sources], [negative sources])
    SAMPLES = {
        "SCAN-RB-ISO8601": ("q.rb", [
            "      DateTime.iso8601(term) unless term.match?(EPOCH_RE)",
            "t = Time.iso8601(params[:since])",
            "d = DateTime.xmlschema(value)",
        ], [
            "t = Time.iso8601('2024-01-01T00:00:00Z')",  # literal, not untrusted
            "s = time.iso8601",                          # formatting an instance
            "s = Time.now.utc.iso8601(3)",
        ]),
        "SCAN-RB-TO-DATETIME": ("p.rb", [
            "    datetime = @object['published']&.to_datetime",
            "t = json[:updated].to_time",
            "t = params_value.to_datetime",
        ], [
            "MIN = '0000-01-01T00:00:00Z'.to_datetime.freeze",  # constant, not untrusted
            "t = record.created_at.to_time",   # already a time value
            "d = Date.today.to_datetime",
        ]),
        "SCAN-RB-PARSE": ("z.rb", [
            "t = Time.zone.parse(params[:at])",
            "t = DateTime.parse(s)",
        ], [
            "t = Time.zone.now",
            "t = Time.rfc3339(s)",
        ]),
        "SCAN-JS-APPEND-Z": ("a.tsx", [
            "  const date = new Date(value + 'Z');",
            "const d = new Date(`${value}Z`);",
            "const t = Date.parse(row.at + \"Z\");",
            "const d = dayjs(s + 'Z')",
        ], [
            "const d = new Date(value);",
            "const s = d.toISOString().slice(0, 19) + 'Z';",  # formatting, not parsing
        ]),
        "SCAN-JS-DATE-PARSE": ("s.tsx", [
            "<span>{new Date(status.created_at).toLocaleString()}</span>",
            "const d = new Date(status.get('created_at'));",
            "const d = new Date(account?.updated_at);",
            "const d = new Date(item.published);",
            "const d = new Date(obj['timestamp']);",
            "const d = new Date(props.post.date)",
        ], [
            "const d = new Date(value + 'Z');",  # reported as SCAN-JS-APPEND-Z only
            "const d = new Date(Date.now());",
            "const d = new Date(created_at_ms_total * 1)",
        ]),
        "SCAN-JS-DAYJS": ("d.ts", [
            "const d = dayjs(s);", "const d = dayjs.utc(row.get('at'));",
        ], [
            "const d = dayjs();", "const d = dayjs(s, 'YYYY-MM-DDTHH:mm:ssZ', true);",
            "const d = dayjs(0);",
        ]),
        "SCAN-JS-PARSEISO": ("f.ts", ["const d = parseISO(s)"], ["const d = parse(s, fmt, ref)"]),
        "SCAN-JS-LUXON-FROMISO": ("l.ts", [
            "const d = DateTime.fromISO(s)", "const d = DateTime.fromSQL(row.at)",
        ], ["const s = DateTime.now().toISO()"]),
        "SCAN-JS-MOMENT-LENIENT": ("m.js", [
            "const m = moment(x)", "const m = moment(status.get('created_at'))",
            "const m = moment.utc('2024-01-01')",
        ], ["const m = moment()", "const m = moment(s, moment.ISO_8601, true)"]),
        "SCAN-PY-ARROW-GET": ("a.py", ["t = arrow.get(s)", "t = arrow.get(row['at'])"],
                              ["t = arrow.get(s, 'YYYY-MM-DDTHH:mm:ssZZ')", "t = arrow.utcnow()"]),
        "SCAN-PY-PANDAS-TO-DATETIME": ("p.py", [
            "df['t'] = pd.to_datetime(df['t'])", "s = pandas.to_datetime(col, errors='coerce')",
        ], ["df['t'] = pd.to_datetime(df['t'], format='ISO8601', utc=True)"]),
        "SCAN-PY-DATEUTIL": ("u.py", [
            "from dateutil.parser import parse\nx = parse(s)",
            "from dateutil import parser\nx = parser.parse(s)",
            "x = isoparse(s)",
        ], ["x = parse(s)", "x = ast.parse(src)"]),
        "SCAN-NET-SORTABLE-Z": ("c.cs", [
            'var s = dt.ToString("s") + "Z";',
            'var s = dt.ToString("s", CultureInfo.InvariantCulture) + "Z";',
            'var s = $"{dt:s}Z";',
        ], [
            'var s = dt.ToUniversalTime().ToString("s") + "Z";',
            'var s = DateTime.UtcNow.ToString("s") + "Z";',
            'var s = dt.ToString("o");',
        ]),
    }

    def test_positive_and_negative(self):
        for pid, (fname, pos, neg) in self.SAMPLES.items():
            for src in pos:
                self.assertIn(pid, _ids_of(src, fname), f"{pid} should hit: {src!r}")
            for src in neg:
                self.assertNotIn(pid, _ids_of(src, fname), f"{pid} should not hit: {src!r}")

    def test_messages_carry_probed_behaviour(self):
        msg = {p[0]: p[6] for p in rfcdt.SCAN_PATTERNS}
        self.assertIn('DateTime.iso8601("2024") is TODAY at 20:24', msg["SCAN-RB-ISO8601"])
        self.assertIn("':60' becomes ':59'", msg["SCAN-RB-ISO8601"])
        self.assertIn("':60' down to ':59'", msg["SCAN-RB-PARSE"])

    def test_severities(self):
        sev = {p[0]: p[5] for p in rfcdt.SCAN_PATTERNS}
        for pid in self.SAMPLES:
            self.assertEqual(sev[pid], "warn", pid)

    @unittest.skipUnless(os.path.isdir(MASTODON), "Mastodon checkout not present")
    def test_mastodon_regression(self):
        # The three misses from the TODO evidence (scan only these files: the
        # full tree is slow to read).
        want = {("app/lib/search_query_transformer.rb", 229, "SCAN-RB-ISO8601"),
                ("app/lib/activitypub/parser/status_parser.rb", 64, "SCAN-RB-TO-DATETIME"),
                ("app/javascript/entrypoints/admin.tsx", 242, "SCAN-JS-APPEND-Z")}
        paths = [os.path.join(MASTODON, f) for f, _, _ in want]
        if not all(os.path.isfile(p) for p in paths):
            self.skipTest("Mastodon files moved")
        got = {(os.path.relpath(x["file"], MASTODON), x["line"], x["id"])
               for x in rfcdt.scan_paths(paths)}
        self.assertLessEqual(want, got)


class TestScanNewFileTypes(unittest.TestCase):
    """T3-13: .vue .svelte .erb .ex/.exs .dart .proto .cls .sql .swift .kt."""
    SAMPLES = {
        "SCAN-EX-NAIVE": ("a.ex", [
            "s = NaiveDateTime.utc_now() |> NaiveDateTime.to_iso8601()",
            "field :published_at, :naive_datetime",
            "use Ecto.Schema\nschema \"x\" do\n  timestamps()\nend",
        ], [
            "s = DateTime.utc_now() |> DateTime.to_iso8601()",
            "  timestamps(type: :utc_datetime_usec)",
            "  timestamps()",  # no Ecto in the file
        ]),
        "SCAN-EX-FROM-ISO8601": ("b.exs", ["{:ok, dt, _} = DateTime.from_iso8601(s)"],
                                 ["{:ok, dt} = DateTime.from_unix(n)"]),
        "SCAN-DART-PARSE": ("a.dart", ["final d = DateTime.parse(s);",
                                       "final d = DateTime.tryParse(json['at']);"],
                            ["final d = DateTime.now().toUtc();"]),
        "SCAN-DART-ISO-STRING": ("b.dart", ["final o = d.toIso8601String();"],
                                 ["final o = d.toUtc().toIso8601String();",
                                  "final o = DateTime.now().toUtc().toIso8601String();"]),
        "SCAN-PROTO-STRING-TIME": ("a.proto", [
            "  string created_at = 1;", "  optional string start_time = 3;",
            "  string timestamp = 7;", "  repeated string event_date = 9;",
        ], [
            "  string time_zone = 2;", "  google.protobuf.Timestamp created_at = 1;",
            "  string name = 4;", "  string date_format = 5;",
        ]),
        "SCAN-PROTO-ISO8601-COMMENT": ("b.proto", [
            "  // ISO 8601 timestamp of creation", "  /* ISO-8601 */", "   * in ISO8601 format",
        ], ["  // RFC 3339 timestamp in UTC ('Z')"]),
        "SCAN-APEX-VALUEOF": ("A.cls", ["Datetime d = Datetime.valueOf(s);",
                                        "DateTime d = DATETIME.VALUEOF(req.at);"],
                              ["Datetime d = Datetime.valueOf('2024-01-01 00:00:00');",
                               "\\NeedsTeXFormat{LaTeX2e}\n\\ProvidesClass{x}\nDatetime.valueOf(s)"]),
        "SCAN-APEX-FORMAT-LOCAL-Z": ("B.cls", [
            "String o = d.format('yyyy-MM-dd\\'T\\'HH:mm:ss\\'Z\\'');",
        ], ["String g = d.formatGmt('yyyy-MM-dd\\'T\\'HH:mm:ss\\'Z\\'');"]),
        "SCAN-SQL-TO-CHAR-Z": ("a.sql", [
            "SELECT to_char(created_at, 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') FROM t;",
            "SELECT to_char(ts, 'YYYY-MM-DD\"T\"HH24:MI:SS.MSZ') FROM t;",
        ], [
            "SELECT to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') FROM t;",
        ]),
        "SCAN-SQL-TO-CHAR-OFFSET": ("b.sql", [
            "SELECT to_char(ts, 'YYYY-MM-DD\"T\"HH24:MI:SSOF') FROM t;",
            "SELECT to_char(ts, 'YYYY-MM-DD HH24:MI:SS TZ') FROM t;",
            "SELECT to_char(\n  ts,\n  'YYYY-MM-DD\"T\"HH24:MI:SStz'\n) FROM t;",
        ], [
            "SELECT to_char(ts, 'YYYY-MM-DD\"T\"HH24:MI:SSTZH:TZM') FROM t;",
            "SELECT to_char(n, 'FM999') FROM t;",
        ]),
        "SCAN-SQL-MYSQL-FORMAT-Z": ("c.sql", [
            "SELECT DATE_FORMAT(created_at, '%Y-%m-%dT%H:%i:%sZ') FROM t;",
            "select date_format(ts, '%Y-%m-%dT%TZ') from t;",
        ], ["SELECT DATE_FORMAT(UTC_TIMESTAMP(), '%Y-%m-%dT%H:%i:%sZ');"]),
        "SCAN-SQL-TEXT-CAST": ("d.sql", [
            "SELECT created_at::text FROM t;", "SELECT now()::text;",
            "SELECT CAST(updated_at AS text) FROM t;", "SELECT e.event_time :: varchar FROM e;",
        ], ["SELECT birth_date::text FROM t;", "SELECT id::text FROM t;"]),
        "SCAN-SWIFT-ISO8601-DEFAULT": ("a.swift", [
            "let f = ISO8601DateFormatter()\nlet d = f.date(from: s)",
        ], [
            "let f = ISO8601DateFormatter()\nf.formatOptions = [.withInternetDateTime]",
        ]),
        "SCAN-SWIFT-FRACTIONAL-ONLY": ("b.swift", [
            "f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]",
        ], ["f.formatOptions = [.withInternetDateTime]"]),
        "SCAN-SWIFT-POSIX-LOCALE": ("c.swift", [
            "let df = DateFormatter()\ndf.dateFormat = \"yyyy-MM-dd'T'HH:mm:ssXXXXX\"",
        ], [
            "let df = DateFormatter()\ndf.locale = Locale(identifier: \"en_US_POSIX\")\n"
            "df.dateFormat = \"yyyy-MM-dd'T'HH:mm:ssXXXXX\"",
            "let df = DateFormatter()\ndf.dateStyle = .medium",  # display only
        ]),
    }

    def test_positive_and_negative(self):
        for pid, (fname, pos, neg) in self.SAMPLES.items():
            for src in pos:
                self.assertIn(pid, _ids_of(src, fname), f"{pid} should hit: {src!r}")
            for src in neg:
                self.assertNotIn(pid, _ids_of(src, fname), f"{pid} should not hit: {src!r}")

    def test_every_new_language_pattern_has_samples(self):
        new = {p[0] for p in rfcdt.SCAN_PATTERNS
               if p[0].split("-")[1] in ("EX", "DART", "PROTO", "APEX", "SQL", "SWIFT")}
        self.assertEqual(new, set(self.SAMPLES))

    def test_existing_rules_reach_new_extensions(self):
        cases = [
            ("<script>\nconst d = new Date(props.post.published)\n</script>", "a.vue",
             "SCAN-JS-DATE-PARSE"),
            ("<script>\n  const d = dayjs(s)\n</script>", "a.svelte", "SCAN-JS-DAYJS"),
            ("<%= DateTime.parse(params[:at]) %>", "a.html.erb", "SCAN-RB-PARSE"),
            ("val t = ZonedDateTime.parse(s)", "a.kt", "SCAN-JAVA-LENIENT-PARSE"),
            ("val f = DateTimeFormatter.ofPattern(\"yyyy-MM-dd'T'HH:mm:ssZ\")", "a.kt",
             "SCAN-JAVA-OFFSET-PATTERN"),
            ("df.dateFormat = \"yyyy-MM-dd'T'HH:mm:ssZ\"", "a.swift", "SCAN-JAVA-OFFSET-PATTERN"),
            ("df.dateFormat = \"yyyy-MM-dd'T'HH:mm:ss'Z'\"", "a.swift", "SCAN-LITERAL-Z"),
            ("String s = d.format('yyyy-MM-dd\\'T\\'HH:mm:ssZ');", "A.cls",
             "SCAN-JAVA-OFFSET-PATTERN"),
        ]
        for src, fname, pid in cases:
            self.assertIn(pid, _ids_of(src, fname), f"{fname}: {src!r}")

    def test_language_rules_stay_in_their_files(self):
        self.assertNotIn("SCAN-DART-PARSE", _ids_of("final d = DateTime.parse(s);", "a.java"))
        self.assertNotIn("SCAN-SQL-TEXT-CAST", _ids_of("x = created_at::text", "a.py"))
        self.assertNotIn("SCAN-PROTO-STRING-TIME", _ids_of("  string created_at = 1;", "a.cs"))


class TestScanMultiline(unittest.TestCase):
    """T3-14: statements split over lines are joined; reported at the first line."""

    def _hits(self, src, fname):
        return [(x["line"], x["id"]) for x in rfcdt.scan_text(src, fname)]

    def test_split_calls_found(self):
        cases = [
            ("a();\nconst d = new Date(\n  s)\n", "t.js", (2, "SCAN-JS-DATE-PARSE")),
            ("const d = new Date(\n  value +\n  'Z');", "t.ts", (1, "SCAN-JS-APPEND-Z")),
            ("x = 1\nd = datetime.fromisoformat(\n    s)\n", "t.py", (2, "SCAN-PY-FROMISOFORMAT")),
            ("t = Time\n  .zone\n  .parse(s)", "t.rb", (1, "SCAN-RB-PARSE")),
            ("datetime = @object['published']\n  &.to_datetime", "t.rb",
             (1, "SCAN-RB-TO-DATETIME")),
            ("var s = dt.ToString(\"s\")\n    + \"Z\";", "t.cs", (1, "SCAN-NET-SORTABLE-Z")),
            ("const d = moment( // parse\n  status.get('created_at'))", "t.js",
             (1, "SCAN-JS-MOMENT-LENIENT")),
            ("String out = ZonedDateTime\n    .now()\n    .toString();", "T.java",
             (1, "SCAN-JAVA-TOSTRING")),
        ]
        for src, fname, want in cases:
            self.assertIn(want, self._hits(src, fname), f"{fname}: {src!r}")

    def test_no_duplicate_for_hit_on_continuation_line(self):
        src = ("f = DateTimeFormatter.ofPattern(\n"
               "    \"yyyy-MM-dd'T'HH:mm:ssZ\")\n")
        self.assertEqual(self._hits(src, "T.java"), [(2, "SCAN-JAVA-OFFSET-PATTERN")])
        src = "const d =\n  new Date(value + 'Z');\n"
        self.assertEqual(self._hits(src, "t.ts"), [(2, "SCAN-JS-APPEND-Z")])
        src = "RX = re.compile(\n    r'\\d{4}-\\d{1,2}')\n"
        self.assertEqual([h for h in self._hits(src, "a.py") if h[1] == "SCAN-REGEX-SHORT-FIELD"],
                         [(2, "SCAN-REGEX-SHORT-FIELD")])

    def test_statements_are_not_over_joined(self):
        # A complete statement is not glued to the next one.
        src = "const s = input;\nconst d = new Date(0);\n"
        self.assertEqual(self._hits(src, "t.js"), [])
        src = "function f(a) {\n  return a;\n}\nconst x = { created_at: 1 };\n"
        self.assertEqual(self._hits(src, "t.js"), [])
        # a trailing ',' at depth 0 (struct / object literal) does not join
        src = "x := T{\n\tKey: k,\n\tStamp: t.Format(time.RFC3339Nano),\n}\n"
        self.assertEqual(self._hits(src, "t.go"), [])
        # a // comment does not hide the continuation
        src = "const d = new Date( // input from the API\n  raw)\n"
        self.assertIn((1, "SCAN-JS-DATE-PARSE"), self._hits(src, "t.js"))

    def test_join_is_bounded(self):
        import time
        src = "x = f(\n" + "  a,\n" * 5000 + ")\n"
        t0 = time.monotonic()
        rfcdt.scan_text(src, "t.js")
        self.assertLess(time.monotonic() - t0, 5.0)


class TestScanSummary(unittest.TestCase):
    """T4-3: the scan denominator (files scanned / skipped by reason)."""

    def _tree(self, d):
        os.makedirs(os.path.join(d, "src"))
        os.makedirs(os.path.join(d, "node_modules", "x"))
        with open(os.path.join(d, "src", "a.py"), "w") as fh:
            fh.write("x = datetime.fromisoformat(s)\n")
        with open(os.path.join(d, "src", "b.js"), "w") as fh:
            fh.write("const d = new Date(input);\n")
        with open(os.path.join(d, "src", "notes.md"), "w") as fh:
            fh.write("nothing\n")
        with open(os.path.join(d, "src", "big.rb"), "w") as fh:
            fh.write("t = DateTime.parse(s)\n" + "#" * 3000 + "\n")
        with open(os.path.join(d, "src", "blob.dat"), "wb") as fh:
            fh.write(b"abc\x00def")
        with open(os.path.join(d, "src", "logo.png"), "wb") as fh:
            fh.write(b"\x89PNG")
        with open(os.path.join(d, "node_modules", "x", "c.js"), "w") as fh:
            fh.write("Date.parse(x)\n")

    def test_summary_counts(self):
        with tempfile.TemporaryDirectory() as d:
            self._tree(d)
            s = {}
            f = rfcdt.scan_paths([d], max_bytes=1000, summary=s)
            self.assertEqual(s["files_seen"], 6)
            self.assertEqual(s["files_scanned"], 3)
            self.assertEqual(s["files_skipped"], 3)
            self.assertEqual(s["skipped"], {"too-large": 1, "binary": 1, "extension": 1,
                                            "unreadable": 0, rfcdt.NOT_LOCAL: 0,
                                            rfcdt.READ_TIMEOUT: 0})
            self.assertEqual(s["excluded_dirs"], {"node_modules": 1})
            self.assertEqual(s["scanned_by_ext"], {".py": 1, ".js": 1, ".md": 1})
            self.assertEqual(s["generic_only_by_ext"], {".md": 1})
            self.assertEqual(s["skipped_by_ext"], {".rb": 1, ".dat": 1, ".png": 1})
            self.assertEqual([(os.path.basename(x["file"]), x["reason"])
                              for x in s["skipped_files"]], [("big.rb", "too-large")])
            self.assertEqual(sorted(os.path.basename(x["file"]) for x in f), ["a.py", "b.js"])
            # no limit: the large file is scanned
            s2 = {}
            f2 = rfcdt.scan_paths([d], max_bytes=0, summary=s2)
            self.assertEqual(s2["skipped"]["too-large"], 0)
            self.assertIn("big.rb", {os.path.basename(x["file"]) for x in f2})

    def test_cli_json_and_text(self):
        with tempfile.TemporaryDirectory() as d:
            self._tree(d)
            cp = subprocess.run([sys.executable, RFCDT, "scan", "--json", "--max-bytes", "1000", d],
                                capture_output=True)
            self.assertEqual(cp.returncode, 1)
            out = json.loads(cp.stdout)
            self.assertEqual(set(out), {"meta", "summary", "findings"})
            self.assertEqual(out["summary"]["max_bytes"], 1000)
            self.assertEqual(out["summary"]["skipped"]["too-large"], 1)
            self.assertEqual(out["meta"]["version"], rfcdt.__version__)
            cp = subprocess.run([sys.executable, RFCDT, "scan", "--max-bytes", "1000", d],
                                capture_output=True, text=True)
            self.assertIn("scan summary: 3 file(s) scanned, 3 skipped of 6 seen", cp.stdout)
            self.assertIn("too-large 1 (>1000 bytes), binary 1, extension 1", cp.stdout)
            self.assertIn("node_modules x1", cp.stdout)
            self.assertIn("NOT SCANNED too-large:", cp.stdout)
            self.assertIn("generic patterns only (no language rules): .md 1", cp.stdout)
            cp = subprocess.run([sys.executable, RFCDT, "scan", "--max-bytes", "-1", d],
                                capture_output=True)
            self.assertEqual(cp.returncode, 2)

    def test_default_cap_unchanged(self):
        self.assertEqual(rfcdt.DEFAULT_MAX_BYTES, 2_000_000)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.py")
            with open(p, "w") as fh:
                fh.write("x = datetime.fromisoformat(s)\n" + "#" * 2_000_001)
            s = {}
            self.assertEqual(rfcdt.scan_paths([p], summary=s), [])
            self.assertEqual(s["skipped"]["too-large"], 1)


class TestScanEvicted(unittest.TestCase):
    """T4-14: iCloud-evicted (dataless) files and slow reads never stall a scan.
    os.stat and open are faked; no real iCloud file is touched."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="rfcdt-evict")
        self.addCleanup(__import__("shutil").rmtree, self.d, True)
        for name in ("ok.py", "gone.py", "sparse.py", "slow.py"):
            with open(os.path.join(self.d, name), "w") as fh:
                fh.write("x = datetime.fromisoformat(s)\n")
        with open(os.path.join(self.d, ".notes.py.icloud"), "wb") as fh:
            fh.write(b"bplist00")
        os.makedirs(os.path.join(self.d, "cloudy"))
        with open(os.path.join(self.d, "cloudy", "c.py"), "w") as fh:
            fh.write("x = datetime.fromisoformat(s)\n")

    def _fake_stat(self, flags=None, blocks0=()):
        """Patch os.stat: paths in ``flags`` get those st_flags, basenames in
        ``blocks0`` report st_blocks == 0 with their real size."""
        real = os.stat
        flags = flags or {}

        def fake(path, *a, **kw):
            st = real(path, *a, **kw)
            p = os.fspath(path)
            name = os.path.basename(p)
            if name in flags or name in blocks0:
                return type("S", (), {"st_mode": st.st_mode, "st_size": st.st_size,
                                      "st_flags": flags.get(name, 0),
                                      "st_blocks": 0 if name in blocks0 else st.st_blocks,
                                      "st_mtime": st.st_mtime})()
            return st
        patcher = unittest.mock.patch.object(rfcdt.os, "stat", fake)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_constant(self):
        self.assertEqual(rfcdt.SF_DATALESS, 0x40000000)

    def test_dataless_and_placeholders_skipped(self):
        self._fake_stat(flags={"gone.py": rfcdt.SF_DATALESS, "cloudy": rfcdt.SF_DATALESS},
                        blocks0=("sparse.py",))
        s = {}
        f = rfcdt.scan_paths([self.d], summary=s)
        self.assertEqual(sorted(os.path.basename(x["file"]) for x in f), ["ok.py", "slow.py"])
        self.assertEqual(s["skipped"][rfcdt.NOT_LOCAL], 3)   # gone, sparse, .icloud stub
        self.assertEqual(sorted(os.path.basename(x["file"]) for x in s["skipped_files"]
                                if x["reason"] == rfcdt.NOT_LOCAL),
                         [".notes.py.icloud", "gone.py", "sparse.py"])
        self.assertEqual([os.path.basename(x) for x in s["not_local_dirs"]], ["cloudy"])
        text = rfcdt.format_scan_summary(s)
        self.assertIn("not-local (iCloud/dataless) 3", text)
        self.assertIn("NOT ENTERED not-local (iCloud/dataless):", text)
        self.assertIn("NOT SCANNED not-local (iCloud/dataless):", text)
        # --include-evicted reads them (the .icloud stub stays skipped)
        s2 = {}
        f2 = rfcdt.scan_paths([self.d], summary=s2, include_evicted=True)
        self.assertEqual(sorted(os.path.basename(x["file"]) for x in f2),
                         ["c.py", "gone.py", "ok.py", "slow.py", "sparse.py"])
        self.assertEqual(s2["skipped"][rfcdt.NOT_LOCAL], 1)
        # an explicit dataless file or root directory is not opened either
        s3 = {}
        self.assertEqual(rfcdt.scan_paths([os.path.join(self.d, "gone.py"),
                                           os.path.join(self.d, "cloudy")], summary=s3), [])
        self.assertEqual(s3["skipped"][rfcdt.NOT_LOCAL], 1)
        self.assertEqual(len(s3["not_local_dirs"]), 1)

    def test_is_dataless_heuristics(self):
        self.assertFalse(rfcdt._is_dataless(os.path.join(self.d, "ok.py")))
        self.assertFalse(rfcdt._is_dataless(os.path.join(self.d, "missing.py")))
        empty = os.path.join(self.d, "empty.py")
        open(empty, "w").close()
        self._fake_stat(blocks0=("empty.py",))
        self.assertFalse(rfcdt._is_dataless(empty))   # size 0: not a placeholder

    def test_read_timeout(self):
        import threading
        import time
        release = threading.Event()
        self.addCleanup(release.set)
        real_open = open

        def slow_open(path, *a, **kw):
            if os.path.basename(os.fspath(path)) == "slow.py":
                release.wait(10)
            return real_open(path, *a, **kw)
        rfcdt.open = slow_open
        self.addCleanup(delattr, rfcdt, "open")
        s = {}
        t0 = time.monotonic()
        f = rfcdt.scan_paths([self.d], summary=s, file_timeout=0.2)
        self.assertLess(time.monotonic() - t0, 5)
        self.assertEqual(s["skipped"][rfcdt.READ_TIMEOUT], 1)
        self.assertEqual([os.path.basename(x["file"]) for x in s["skipped_files"]
                          if x["reason"] == rfcdt.READ_TIMEOUT], ["slow.py"])
        self.assertNotIn("slow.py", {os.path.basename(x["file"]) for x in f})
        self.assertIn("ok.py", {os.path.basename(x["file"]) for x in f})
        self.assertIn("read-timeout 1", rfcdt.format_scan_summary(s))
        lingering = [t for t in threading.enumerate() if t.name == "rfcdt-read"]
        self.assertTrue(lingering and all(t.daemon for t in lingering))
        release.set()
        # read errors still surface as unreadable through the worker thread
        with self.assertRaises(OSError):
            rfcdt._read_file(os.path.join(self.d, "missing.py"), 1)

    def test_cli_flags(self):
        cp = subprocess.run([sys.executable, RFCDT, "scan", "--json", "--file-timeout", "3",
                             "--include-evicted", self.d], capture_output=True)
        out = json.loads(cp.stdout)
        self.assertEqual(out["summary"]["file_timeout"], 3.0)
        self.assertTrue(out["summary"]["include_evicted"])
        self.assertIn(rfcdt.NOT_LOCAL, out["summary"]["skipped"])
        for bad in ("-1", "x"):
            cp = subprocess.run([sys.executable, RFCDT, "scan", "--file-timeout", bad, self.d],
                                capture_output=True)
            self.assertEqual(cp.returncode, 2)


@unittest.skipUnless(TZ, "tz data not available")
class TestLmtTolerance(unittest.TestCase):
    """T1-6: sub-minute (LMT) zone offsets: nearest-minute rule."""

    def test_paris_1900_nearest(self):
        self.assertTrue(rfcdt.check("1900-01-01T00:00:00+00:09[!Europe/Paris]", "ixdtf").ok)
        r = rfcdt.check("1900-01-01T00:00:00+00:10[!Europe/Paris]", "ixdtf")
        self.assertFalse(r.ok)
        self.assertEqual(r.error_codes, ["R9557-3.4/critical-inconsistency"])
        self.assertIn("+00:09:21", r.errors[0].message)
        self.assertIn("nearest representable: +00:09", r.errors[0].message)

    def test_elective_is_a_warning(self):
        r = rfcdt.check("1900-01-01T00:00:00+00:10[Europe/Paris]", "ixdtf")
        self.assertTrue(r.ok)
        self.assertIn("R9557-3.4/elective-inconsistency", r.warning_codes)

    def test_any_sub_minute_option(self):
        r = rfcdt.check("1900-01-01T00:00:00+00:10[!Europe/Paris]", "ixdtf",
                        lmt_tolerance="any-sub-minute")
        self.assertTrue(r.ok)
        self.assertEqual(r.options["lmt_tolerance"], "any-sub-minute")
        self.assertFalse(rfcdt.check("1900-01-01T00:00:00+00:11[!Europe/Paris]", "ixdtf",
                                     lmt_tolerance="any-sub-minute").ok)

    def test_monrovia_tie_allows_both(self):
        # Africa/Monrovia was -00:44:30 until 1972: both -00:44 and -00:45.
        for off, ok in (("-00:44", True), ("-00:45", True), ("-00:43", False), ("-00:46", False)):
            r = rfcdt.check(f"1970-01-01T11:15:30{off}[!Africa/Monrovia]", "ixdtf")
            self.assertEqual(r.ok, ok, off)

    def test_whole_minute_zones_unaffected(self):
        self.assertTrue(rfcdt.check("2024-01-01T01:00:00+01:00[!Europe/Paris]", "ixdtf").ok)
        self.assertFalse(rfcdt.check("2024-01-01T01:00:00+01:01[!Europe/Paris]", "ixdtf").ok)

    def test_bad_option_and_cli(self):
        with self.assertRaises(ValueError):
            rfcdt.check("x", lmt_tolerance="loose")
        cp = subprocess.run([sys.executable, RFCDT, "check", "--profile", "ixdtf",
                             "--lmt-tolerance", "any-sub-minute",
                             "1900-01-01T00:00:00+00:10[!Europe/Paris]"], capture_output=True)
        self.assertEqual(cp.returncode, 0)
        cp = subprocess.run([sys.executable, RFCDT, "adapter"],
                            input=b"1900-01-01T00:00:00+00:10[!Europe/Paris]", capture_output=True,
                            env=dict(os.environ, RFCDT_PROFILE="ixdtf",
                                     RFCDT_OPTIONS='{"lmt_tolerance": "any-sub-minute"}'))
        self.assertTrue(json.loads(cp.stdout)["ok"])
        cp = subprocess.run([sys.executable, RFCDT, "check", "--help"], capture_output=True)
        self.assertIn(b"nearest", cp.stdout)
        self.assertIn(b"any-sub-minute", cp.stdout)


class TestMeta(unittest.TestCase):
    """T4-4: meta block in check --json / scan --json."""

    def test_version(self):
        self.assertRegex(rfcdt.__version__, r"^[0-9]+\.[0-9]+\.[0-9]+$")
        cp = subprocess.run([sys.executable, RFCDT, "--version"], capture_output=True, text=True)
        self.assertIn(rfcdt.__version__, cp.stdout)

    def test_check_json_meta(self):
        cp = subprocess.run([sys.executable, RFCDT, "check", "--json", "2024-01-01T00:00:00Z"],
                            capture_output=True, env=dict(os.environ, TZ="America/New_York"))
        meta = json.loads(cp.stdout)["meta"]
        for k in ("tool", "version", "python", "tz", "host_tz", "date"):
            self.assertIn(k, meta)
        self.assertEqual(meta["host_tz"]["TZ"], "America/New_York")
        self.assertTrue(rfcdt.check(meta["date"]).ok, meta["date"])
        self.assertTrue(meta["date"].endswith("Z"))
        self.assertIn(meta["tz"]["source"], ("system", "tzdata-package", None))
        if TZ:
            self.assertTrue(meta["tz"]["available"])

    def test_tz_info_injected(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(rfcdt.tz_info([d])["source"],
                             "tzdata-package" if rfcdt.tz_info([d])["tzdata_package"] else None)
            open(os.path.join(d, "UTC"), "wb").close()
            with open(os.path.join(d, "tzdata.zi"), "w") as fh:
                fh.write("# version 2031z\n")
            i = rfcdt.tz_info([d])
            self.assertEqual((i["source"], i["path"], i["version"]), ("system", d, "2031z"))
            with open(os.path.join(d, "+VERSION"), "w") as fh:
                fh.write("2032a\n")
            self.assertEqual(rfcdt.tz_info([d])["version"], "2032a")


def _write_leapseconds(path, days, expires="2027 Jun 28"):
    months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    with open(path, "w") as fh:
        fh.write("# test copy\n")
        for y, m, d in sorted(days):
            fh.write(f"Leap\t{y}\t{months[m - 1]}\t{d}\t23:59:60\t+\tS\n")
        if expires:
            fh.write(f"#Expires {expires} 00:00:00\n")


class TestSelfcheck(unittest.TestCase):
    """T4-5: rfcdt.py selfcheck (tampered copies injected by path)."""
    ICU = sorted(rfcdt.KNOWN_CALENDARS - {"ethiopic-amete-alem", "islamicc"})  # ICU names
    TODAY = __import__("datetime").date(2026, 9, 25)

    def _status(self, res):
        return {r["check"]: r["status"] for r in res}

    def _run(self, d, **kw):
        kw.setdefault("calendars", self.ICU)
        kw.setdefault("today", self.TODAY)
        return rfcdt.selfcheck(zoneinfo_dirs=[d], **kw)

    def _zone_dir(self, d, version="2026a"):
        open(os.path.join(d, "UTC"), "wb").close()
        with open(os.path.join(d, "+VERSION"), "w") as fh:
            fh.write(version + "\n")

    def test_matching_copy_is_ok(self):
        with tempfile.TemporaryDirectory() as d:
            self._zone_dir(d)
            _write_leapseconds(os.path.join(d, "leapseconds"), rfcdt.LEAP_SECONDS)
            st = self._status(self._run(d))
            self.assertEqual(st, {"leap-seconds": "OK", "leap-seconds-expiry": "OK",
                                  "calendars": "OK", "tz-version": "OK"})

    def test_tampered_leap_table(self):
        with tempfile.TemporaryDirectory() as d:
            self._zone_dir(d)
            days = set(rfcdt.LEAP_SECONDS) - {(2016, 12, 31)} | {(2029, 6, 30)}
            _write_leapseconds(os.path.join(d, "leapseconds"), days)
            res = self._run(d)
            self.assertEqual(self._status(res)["leap-seconds"], "WARN")
            detail = next(r["detail"] for r in res if r["check"] == "leap-seconds")
            self.assertIn("2029-06-30", detail)
            self.assertIn("2016-12-31", detail)

    def test_expired_file(self):
        with tempfile.TemporaryDirectory() as d:
            self._zone_dir(d)
            _write_leapseconds(os.path.join(d, "leapseconds"), rfcdt.LEAP_SECONDS,
                               expires="2026 Jan 28")
            res = self._run(d)
            self.assertEqual(self._status(res)["leap-seconds-expiry"], "WARN")
            self.assertIn("EXPIRED on 2026-01-28",
                          next(r["detail"] for r in res if r["check"] == "leap-seconds-expiry"))

    def test_leap_seconds_list_format(self):
        from datetime import date, timedelta
        ntp0 = date(1900, 1, 1)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "leap-seconds.list")
            with open(p, "w") as fh:
                fh.write(f"#@\t{(date(2026, 6, 28) - ntp0).days * 86400}\n")
                fh.write(f"{(date(1972, 1, 1) - ntp0).days * 86400}\t10\t# 1 Jan 1972\n")
                for n, (y, m, dd) in enumerate(sorted(rfcdt.LEAP_SECONDS), 11):
                    t = (date(y, m, dd) + timedelta(days=1) - ntp0).days * 86400
                    fh.write(f"{t}\t{n}\t# leap\n")
            dates, expires, negative = rfcdt.parse_leap_file(p)
            self.assertEqual(dates, set(rfcdt.LEAP_SECONDS))
            self.assertEqual(expires, date(2026, 6, 28))
            self.assertEqual(negative, set())

    def test_calendar_drift(self):
        with tempfile.TemporaryDirectory() as d:
            self._zone_dir(d)
            _write_leapseconds(os.path.join(d, "leapseconds"), rfcdt.LEAP_SECONDS)
            res = self._run(d, calendars=self.ICU + ["mars"])
            self.assertEqual(self._status(res)["calendars"], "WARN")
            self.assertIn("mars", next(r["detail"] for r in res if r["check"] == "calendars"))
            res = self._run(d, calendars=[c for c in self.ICU if c != "roc"])
            self.assertEqual(self._status(res)["calendars"], "WARN")
            res = self._run(d, calendars=None, node=None)
            self.assertEqual(self._status(res)["calendars"], "SKIP")

    def test_old_tz_release(self):
        with tempfile.TemporaryDirectory() as d:
            self._zone_dir(d, "2019c")
            _write_leapseconds(os.path.join(d, "leapseconds"), rfcdt.LEAP_SECONDS)
            self.assertEqual(self._status(self._run(d))["tz-version"], "WARN")
            self.assertEqual(self._status(self._run(d, tz_max_age_years=10))["tz-version"], "OK")

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            self._zone_dir(d)
            leap = os.path.join(d, "leapseconds")
            _write_leapseconds(leap, rfcdt.LEAP_SECONDS)
            base = [sys.executable, RFCDT, "selfcheck", "--zoneinfo", d, "--node", "",
                    "--calendars", ",".join(self.ICU), "--today", "2026-09-25"]
            cp = subprocess.run(base, capture_output=True, text=True)
            self.assertEqual(cp.returncode, 0, cp.stdout)
            self.assertIn("selfcheck: OK", cp.stdout)
            _write_leapseconds(leap, set(rfcdt.LEAP_SECONDS) - {(1972, 6, 30)})
            cp = subprocess.run(base + ["--json"], capture_output=True, text=True)
            self.assertEqual(cp.returncode, 1)
            out = json.loads(cp.stdout)
            self.assertEqual(out["status"], "WARN")
            self.assertIn("meta", out)
            cp = subprocess.run(base + ["--today", "garbage"], capture_output=True)
            self.assertEqual(cp.returncode, 2)

    def test_host_run(self):
        # Whatever the host has, selfcheck runs and returns OK/WARN/SKIP lines.
        res = rfcdt.selfcheck(node=None)
        self.assertTrue(res)
        self.assertTrue(all(r["status"] in ("OK", "WARN", "SKIP") for r in res))


class TestVectors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = run_vectors.load_vectors()

    def test_schema_and_count(self):
        self.assertGreaterEqual(len(self.vectors), 120)
        ids = set()
        for v in self.vectors:
            for k in ("id", "input", "profile", "expect", "reason", "section", "notes"):
                self.assertIn(k, v)
            self.assertIn(v["expect"], ("valid", "invalid", "either"))
            self.assertIn(v["profile"], rfcdt.PROFILES)
            self.assertNotIn(v["id"], ids)
            ids.add(v["id"])
            if v["expect"] == "invalid":
                self.assertTrue(v["reason"].startswith("R"), v["id"])
            if v["expect"] == "either":
                self.assertRegex(v.get("interpretation", ""), "§", v["id"])
                self.assertIn(v.get("rfcdt_default"), ("valid", "invalid"), v["id"])
            else:
                self.assertNotIn("rfcdt_default", v, v["id"])
            if v.get("resolvable"):
                self.assertEqual(v["expect"], "invalid", v["id"])
                self.assertIn("interpretation", v, v["id"])
            for k in ("leap_seconds",):
                if k in (v.get("options") or {}):
                    self.assertIn(v["options"][k], rfcdt.LEAP_MODES, v["id"])

    def test_interpretation_vectors_present(self):
        by_id = {v["id"]: v for v in self.vectors}
        for i in ("9557-3.4-001", "9557-3.4-006", "9557-3.4-011", "9557-3.3-005",
                  "9557-3.4-013", "9557-4.1-006", "9557-4.1-007", "3339-5.7-039",
                  "3339-5.7-040", "9557-3.4-022"):
            self.assertEqual(by_id[i]["expect"], "either", i)
        # the 'first value wins' assertion survives as a fields check on an either vector
        self.assertTrue(any(v["expect"] == "either" and v.get("fields", {}).get("effective_tags")
                            == {"u-ca": "chinese"} for v in self.vectors))
        self.assertTrue(any(v.get("resolvable") for v in self.vectors))

    def test_requires_tzdata_marked(self):
        by_id = {v["id"]: v for v in self.vectors}
        for i in ("9557-3.4-003", "9557-3.4-007", "9557-3.4-008", "9557-3.4-023",
                  "9557-4.1-002"):
            self.assertIn("tzdata", by_id[i].get("requires", []), i)
        # any vector whose rfcdt verdict changes without tz data must be marked
        for v in self.vectors:
            opts = dict(v.get("options") or {})
            opts.pop("tzdata", None)
            on = rfcdt.check(v["input"], v["profile"], **opts)
            off = rfcdt.check(v["input"], v["profile"], tzdata="off", **opts)
            if on.ok != off.ok and TZ:
                self.assertIn("tzdata", v.get("requires", []), v["id"])

    def test_rfcdt_passes_all_vectors(self):
        results = run_vectors.run(self.vectors)
        bad = [r for r in results if r["status"] not in ("pass", "skip", "interpretation")]
        self.assertEqual(bad, [])
        for r, v in zip(results, self.vectors):
            self.assertEqual(r["status"] == "interpretation", v["expect"] == "either", v["id"])
        if TZ:
            self.assertFalse(any(r["status"] == "skip" for r in results))

    def _script(self, d, name, body):
        path = os.path.join(d, name)
        with open(path, "w") as fh:
            fh.write(body)
        return f"{sys.executable} {path}"

    def test_interpretation_bucket_never_fails(self):
        with tempfile.TemporaryDirectory() as d:
            rej = self._script(d, "reject_all.py",
                               "import json,sys; sys.stdin.read(); print(json.dumps({'ok': False}))\n")
            either = [v for v in self.vectors if v["expect"] == "either"]
            res = run_vectors.run(either, target=rej)
            self.assertTrue(all(r["status"] == "interpretation" and r["choice"] == "rejected"
                                for r in res))
            groups, tot = run_vectors.summarize(res)
            self.assertEqual(tot["scored"], 0)
            self.assertEqual(tot["interpretation"], len(either))
            buf = io.StringIO()
            run_vectors.print_report(res, "reject_all", out=buf)
            self.assertIn("INTERPRETATION", buf.getvalue())
            self.assertIn("target REJECTED", buf.getvalue())
            self.assertIn("0/0 passed", buf.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                rc = run_vectors.main(["--target", rej, "--vectors", self._subset(d, either)])
            self.assertEqual(rc, 0)

    def _subset(self, d, vecs):
        p = os.path.join(d, "subset.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump({"vectors": vecs}, fh, ensure_ascii=False)
        return p

    def test_resolved_counts_only_on_resolvable(self):
        with tempfile.TemporaryDirectory() as d:
            res_all = self._script(d, "resolve_all.py",
                                   "import json,sys; sys.stdin.read(); "
                                   "print(json.dumps({'ok': True, 'resolved': True}))\n")
            inval = [v for v in self.vectors if v["expect"] == "invalid" and v["profile"] == "ixdtf"]
            res = run_vectors.run(inval, target=res_all)
            for r, v in zip(res, inval):
                want = "interpretation" if v.get("resolvable") else "too-lenient"
                self.assertEqual(r["status"], want, v["id"])

    def test_strict_elective_policy_not_too_strict(self):
        # A target that acts on every elective MAY (rejects elective inconsistencies and
        # duplicates, Z + offset zone, uses the leap table) must not be TOO STRICT.
        body = (
            "import sys, os, json\n"
            f"sys.path.insert(0, {HERE!r}); import rfcdt\n"
            "s = sys.stdin.read(); prof = os.environ['RFCDT_PROFILE']\n"
            "opts = json.loads(os.environ.get('RFCDT_OPTIONS') or '{}')\n"
            "opts.setdefault('leap_seconds', 'table')\n"
            "r = rfcdt.check(s, prof, **opts)\n"
            "ok = r.ok and not set(r.warning_codes) & {'R9557-3.4/elective-inconsistency',"
            " 'R9557-3.3/duplicate-elective-key', 'R9557-3.3/elective-unknown-key',"
            " 'R9557-3.3/elective-unknown-value', 'R9557-4.1/elective-unknown-time-zone',"
            " 'R9557-4.1/time-zone-name-case'}\n"
            "tz = (r.fields or {}).get('time_zone')\n"
            "if ok and tz and tz['kind'] == 'offset' and r.fields['offset_unknown']: ok = False\n"
            "print(json.dumps({'ok': ok}))\n")
        with tempfile.TemporaryDirectory() as d:
            res = run_vectors.run(self.vectors, target=self._script(d, "strict.py", body))
            bad = [(r["id"], r["status"]) for r in res
                   if r["status"] not in ("pass", "interpretation", "skip")]
            self.assertEqual(bad, [])
            self.assertTrue(any(r["status"] == "interpretation" and r["choice"] == "rejected"
                                for r in res))

    def test_target_has_tzdata(self):
        tzv = [v for v in self.vectors if "tzdata" in v.get("requires", [])]
        self.assertTrue(tzv)
        with tempfile.TemporaryDirectory() as d:
            acc = self._script(d, "a.py", "import json,sys; sys.stdin.read(); print(json.dumps({'ok': True}))\n")
            res = run_vectors.run(tzv, target=acc, target_has_tzdata="no")
            self.assertTrue(all(r["status"] == "skip" for r in res))
            res = run_vectors.run(tzv, target=acc, target_has_tzdata="auto")
            self.assertFalse(any(r["status"] == "skip" for r in res))
            res = run_vectors.run(tzv, target=acc, no_tzdata=True)
            self.assertTrue(all(r["status"] == "skip" for r in res))

    def test_argv_mode_uses_double_dash(self):
        sample = [v for v in self.vectors if v["profile"] == "rfc3339" and not v.get("options")]
        self.assertTrue(any(v["input"].startswith("-") for v in sample))
        res = run_vectors.run(sample, target=f"{sys.executable} {RFCDT} check --json",
                              mode="argv")
        bad = [(r["id"], r["status"], r.get("detail")) for r in res
               if r["status"] not in ("pass", "interpretation")
               and not (r["status"] == "skip" and "\x00" in r["input"])]
        self.assertEqual(bad, [])
        self.assertTrue(any(r["status"] == "skip" for r in res))  # NUL vectors

    def test_runner_classifies_lenient_and_strict(self):
        with tempfile.TemporaryDirectory() as d:
            acc = os.path.join(d, "accept_all.py")
            with open(acc, "w") as fh:
                fh.write("import json,sys; sys.stdin.read(); print(json.dumps({'ok': True}))\n")
            sample = [v for v in self.vectors if v["profile"] == "rfc3339"][:40]
            res = run_vectors.run(sample, target=f"{sys.executable} {acc}")
            statuses = {r["status"] for r in res}
            self.assertIn("too-lenient", statuses)
            self.assertNotIn("too-strict", statuses)
            buf = io.StringIO()
            run_vectors.print_report(res, "accept_all", out=buf)
            self.assertIn("TOO LENIENT", buf.getvalue())

    def test_reference_adapter_subset(self):
        sample = self.vectors[::15]
        res = run_vectors.run(sample, target=f"{sys.executable} {RFCDT} adapter")
        self.assertTrue(all(r["status"] in ("pass", "skip", "interpretation") for r in res),
                        [r for r in res if r["status"] not in ("pass", "skip", "interpretation")])
        for r, v in zip(res, sample):
            if r["status"] == "interpretation":
                self.assertEqual(r["choice"], "accepted" if v["rfcdt_default"] == "valid"
                                 else "rejected", v["id"])

    def _fields_adapter(self, d, name, fields_expr):
        """Adapter that accepts everything rfcdt accepts and returns rfcdt's
        fields patched by ``fields_expr`` (a Python expression over f, s)."""
        body = ("import sys, os, json\n"
                f"sys.path.insert(0, {HERE!r}); import rfcdt\n"
                "s = sys.stdin.read(); prof = os.environ['RFCDT_PROFILE']\n"
                "opts = json.loads(os.environ.get('RFCDT_OPTIONS') or '{}')\n"
                "r = rfcdt.check(s, prof, **opts)\n"
                "f = dict(r.fields or {})\n"
                f"f = {fields_expr}\n"
                "print(json.dumps({'ok': r.ok, 'fields': f}))\n")
        return self._script(d, name, body)

    def test_wrong_value_on_either_vector(self):
        # last-wins on a repeated elective key: accepting is permitted, but the
        # effective value must be the first one -> WRONG VALUE (a failure).
        vec = [v for v in self.vectors if v.get("fields", {}).get("effective_tags")
               == {"u-ca": "chinese"} and v["expect"] == "either"]
        self.assertTrue(vec)
        with tempfile.TemporaryDirectory() as d:
            last = self._fields_adapter(
                d, "last.py", "{**f, 'effective_tags': {t['key']: t['value'] "
                              "for t in f.get('tags') or []}}")
            res = run_vectors.run(vec, target=last)
            self.assertEqual([r["status"] for r in res], ["wrong-value"])
            self.assertIn("japanese", res[0]["detail"])
            buf = io.StringIO()
            run_vectors.print_report(res, "last", out=buf)
            self.assertIn("WRONG VALUE", buf.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                rc = run_vectors.main(["--target", last, "--vectors", self._subset(d, vec)])
            self.assertEqual(rc, 1)
            # the same adapter rejecting is a plain interpretation
            rej = self._script(d, "rej.py", "import json,sys; sys.stdin.read(); "
                                            "print(json.dumps({'ok': False}))\n")
            self.assertEqual(run_vectors.run(vec, target=rej)[0]["status"], "interpretation")

    def test_wrong_value_two_digit_year(self):
        vec = [v for v in self.vectors if v["input"] == "0050-06-01T00:00:00Z"]
        self.assertEqual(vec[0]["fields"]["year"], 50)
        with tempfile.TemporaryDirectory() as d:
            remap = self._fields_adapter(
                d, "remap.py", "{**f, 'year': f['year'] + 1900 if f.get('year', 100) < 100 "
                               "else f.get('year')}")
            res = run_vectors.run(vec, target=remap)
            self.assertEqual(res[0]["status"], "wrong-value")
            self.assertIn("year: expected 50, got 1950", res[0]["detail"])
            # only the keys the adapter returns are compared
            yonly = self._fields_adapter(d, "yonly.py", "{'year': f.get('year')}")
            self.assertEqual(run_vectors.run(vec, target=yonly)[0]["status"], "pass")

    def test_rfcdt_adapter_fields_all_match(self):
        fv = [v for v in self.vectors if v.get("fields")]
        self.assertGreaterEqual(len(fv), 25)
        res = run_vectors.run(fv, target=f"{sys.executable} {RFCDT} adapter")
        self.assertEqual([r["id"] for r in res if r["status"] not in ("pass", "interpretation",
                                                                          "skip")], [])
        self.assertTrue(all(r.get("fields_compared") for r in res if r.get("choice") == "accepted"))

    def test_compare_fields_rules(self):
        cf = run_vectors.compare_fields
        self.assertIsNone(cf({"year": 1}, "Stamp(year=1)"))        # not an object
        self.assertIsNone(cf({"year": 1}, {"epochMs": 0}))          # no shared names
        self.assertEqual(cf({"year": 1, "month": 2}, {"year": 1}), [])
        self.assertEqual(cf({"secfrac": "52"}, {"secfrac": "520"}), [])
        self.assertEqual(cf({"secfrac": "000000000001"}, {"secfrac": "000"}), [])  # truncation
        self.assertEqual(cf({"secfrac": "052"}, {"secfrac": "52"}), [("secfrac", "052", "52")])
        self.assertEqual(cf({"secfrac": "123"}, {"secfrac": "124"}), [("secfrac", "123", "124")])
        self.assertEqual(cf({"time_zone": {"kind": "name", "name": "X", "critical": False}},
                            {"time_zone": {"name": "X"}}), [])
        self.assertTrue(cf({"time_zone": {"name": "X"}}, {"time_zone": None}))
        self.assertTrue(cf({"effective_tags": {"u-ca": "hebrew"}}, {"effective_tags": {}}))
        # a list-shaped rfcdt name returned as an object is a name clash, not compared
        self.assertIsNone(cf({"tags": []}, {"tags": {}}))

    def test_offset_with_seconds_reason(self):
        for s, prof in (("2024-01-01T00:00:00-00:44:30", "rfc3339"),
                        ("2024-01-01T12:00:00+01:00:00", "rfc3339"),
                        ("2022-07-08T00:14:07-00:44:30[Europe/Dublin]", "ixdtf")):
            r = rfcdt.check(s, prof)
            self.assertEqual(r.error_codes, ["R3339-5.6/time-numoffset"], s)
            self.assertIn("offset-has-seconds", r.errors[0].message)
        for s in ("2022-07-08T00:14:07Z[+01:00:00]", "2022-07-08T00:14:07Z[!+01:00:00]",
                  "2022-07-08T00:14:07+01:00[!+01:00junk]"):
            self.assertEqual(rfcdt.check(s, "ixdtf").error_codes, ["R9557-4.1/time-zone-offset"])
        self.assertEqual(rfcdt.check("junk2024-01-01T00:00:00Z").error_codes,
                         ["R3339-5.6/date-fullyear"])

    def test_new_vectors_present(self):
        inputs = {(v["input"], v["profile"]) for v in self.vectors}
        for s, p in (("2022-07-08T00:14:07+01:00[!+01:00junk]", "ixdtf"),
                     ("2022-07-08T00:14:07Z[+01:00:00]", "ixdtf"),
                     ("2022-07-08T00:14:07Z[!+01:00:00]", "ixdtf"),
                     ("junk2024-01-01T00:00:00Z", "rfc3339"),
                     ("2024-01-01T00:00:00-00:44:30", "rfc3339"),
                     ("0050-06-01T00:00:00Z", "rfc3339")):
            self.assertIn((s, p), inputs)

    def test_target_kind(self):
        with tempfile.TemporaryDirectory() as d:
            acc = self._script(d, "a.py", "import json,sys; sys.stdin.read(); "
                                          "print(json.dumps({'ok': True}))\n")
            res = run_vectors.run(self.vectors, target=acc, target_kind="rfc3339")
            for r in res:
                if r["profile"] == "ixdtf":
                    self.assertEqual((r["status"], r["skip_kind"]), ("skip", "target-kind"))
            res = {r["id"]: r for r in run_vectors.run(self.vectors, target=acc,
                                                        target_kind="ixdtf")}
            by = {v["id"]: v for v in self.vectors}
            skipped = [i for i, r in res.items() if r["status"] == "skip"]
            self.assertTrue(skipped)
            for i in skipped:
                self.assertEqual(by[i]["profile"], "rfc3339")
                self.assertEqual(by[i]["reason"], "R3339-5.6/trailing-characters")
                self.assertIn("[", by[i]["input"])
            # invalid in both profiles: still run (and fail for accept-all)
            for s in ("2024-01-01T12:00:00+01:00:00", "2024-01-01T12:00:00Z\n",
                      "2023-02-30T00:00:00Zjunk"):
                r = next(r for r in res.values() if r["input"] == s and r["profile"] == "rfc3339")
                self.assertEqual(r["status"], "too-lenient", s)
            # valid rfc3339 vectors run normally
            self.assertTrue(any(r["status"] == "pass" and r["profile"] == "rfc3339"
                                for r in res.values()))
        # built-in engine is clean for every kind
        for kind in run_vectors.TARGET_KINDS:
            bad = [r for r in run_vectors.run(self.vectors, target_kind=kind)
                   if r["status"] not in ("pass", "interpretation", "skip")]
            self.assertEqual(bad, [], kind)

    def test_target_options_fixed(self):
        opt = [v for v in self.vectors if v.get("options")]
        self.assertTrue(opt)
        for kw in ({"target_options": "fixed"}, {"default_options_only": True}):
            res = run_vectors.run(self.vectors, **kw)
            sk = [r for r in res if r["status"] == "skip"]
            self.assertEqual(len(sk), len(opt))
            self.assertTrue(all(r["skip_kind"] == "options" for r in sk))
            _, tot = run_vectors.summarize(res)
            self.assertEqual(tot["skipped_by"], {"options": len(opt)})
            buf = io.StringIO()
            run_vectors.print_report(res, None, out=buf)
            self.assertIn("fixed policy", buf.getvalue())
        with contextlib.redirect_stdout(io.StringIO()) as out:
            rc = run_vectors.main(["--target-options", "fixed"])
        self.assertEqual(rc, 0)
        self.assertIn("non-default options", out.getvalue())
        with self.assertRaises(ValueError):
            run_vectors.run(self.vectors[:1], target_options="bogus")

    def test_adapter_errors_reported(self):
        res = run_vectors.run(self.vectors[:2], target=f"{sys.executable} -c print(1)")
        self.assertTrue(all(r["status"] == "error" for r in res))

    def test_skip_with_error_key_is_skip(self):
        with tempfile.TemporaryDirectory() as d:
            sk = self._script(d, "skip_err.py",
                              "import json,sys; sys.stdin.read(); "
                              "print(json.dumps({'skip': True, 'error': 'unsupported'}))\n")
            res = run_vectors.run(self.vectors[:3], target=sk)
        self.assertTrue(all(r["status"] == "skip" for r in res), res)
        self.assertTrue(all(r["skip_kind"] == "target" for r in res if "skip_kind" in r))
        self.assertTrue(any(r.get("detail") == "unsupported" for r in res))


class TestNonUtf8Stdout(unittest.TestCase):
    """Windows pipes default to the ANSI code page (cp1252). Output must never raise
    UnicodeEncodeError there, and --json must stay valid, lossless JSON."""

    def run_cp1252(self, *args):
        env = dict(os.environ, PYTHONIOENCODING="cp1252")
        env.pop("PYTHONUTF8", None)
        return subprocess.run([sys.executable, RFCDT, *args], capture_output=True, env=env)

    def test_check_json_non_ascii(self):
        s = "2026-09-24T12:00:00\uff0b02:00"  # fullwidth plus sign: not in cp1252
        cp = self.run_cp1252("check", s, "--json")
        self.assertNotIn(b"UnicodeEncodeError", cp.stderr)
        self.assertEqual(cp.returncode, 1)  # INVALID, not a crash
        d = json.loads(cp.stdout.decode("ascii"))  # ASCII-only on a non-UTF-8 stdout
        self.assertEqual(d["input"], s)

    def test_check_text_non_ascii(self):
        cp = self.run_cp1252("check", "2026-09-24T12:00:00\uff0b02:00")
        self.assertNotIn(b"UnicodeEncodeError", cp.stderr)
        self.assertEqual(cp.returncode, 1)
        self.assertIn(b"\\uff0b", cp.stdout)  # backslashreplace

    def test_scan_json_non_ascii_finding(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "a.py"), "w", encoding="utf-8") as fh:
                fh.write("from datetime import datetime\n"
                         "x = datetime.fromisoformat(s)  # \u201cnaive\u201d \u2192 \u65e5\u4ed8\n")
            cp = self.run_cp1252("scan", d, "--json")
            self.assertNotIn(b"UnicodeEncodeError", cp.stderr)
            d2 = json.loads(cp.stdout.decode("ascii"))
            self.assertTrue(d2["findings"])
            cp = self.run_cp1252("scan", d)
            self.assertNotIn(b"UnicodeEncodeError", cp.stderr)
            self.assertIn(b"SCAN-PY-FROMISOFORMAT", cp.stdout)


if __name__ == "__main__":
    unittest.main()
