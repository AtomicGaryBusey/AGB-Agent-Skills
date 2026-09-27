"""Tests for iso999_markup.py. All fixtures are invented for this suite,
except the end-to-end run over the repo's own pellow-valley eval fixture."""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import iso999_markup as M  # noqa: E402

PELLOW_DOCS = os.path.join(HERE, "..", "evals", "fixtures", "pellow-valley",
                           "project", "docs")
PELLOW_REGEX = r"\{\{\s*(?P<kind>index|see|seealso)\s*:\s*(?P<body>.*?)\s*\}\}"


class TmpDir(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="iso999mk")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def lint(self, files, fmt="auto", custom=None):
        for name, text in files.items():
            self.write(name, text)
        _, entries, findings, errors = M.run([self.dir], fmt, custom)
        return entries, findings

    def rules(self, files, fmt="auto", custom=None):
        return [f.rule for f in self.lint(files, fmt, custom)[1]]


def latex(text, fmt="latex"):
    findings = []
    reader = M.read_latex if fmt == "latex" else M.read_idx
    return reader(text, "t.tex", findings), findings


# ---------------------------------------------------------------------------
# Syntax: LaTeX / makeindex
# ---------------------------------------------------------------------------
class LatexSyntax(unittest.TestCase):
    def test_levels_sortas_encap(self):
        es, _ = latex(r"Text\index{kettles!copper@\textit{copper}|textbf}.")
        e = es[0]
        self.assertEqual(e.path, ("kettles", "copper"))
        self.assertEqual(e.levels[1][1], "copper")
        self.assertEqual(e.encap, "textbf")
        self.assertEqual(e.kind, "index")

    def test_see_and_seealso(self):
        es, _ = latex(r"\index{teapots|see{kettles}} \index{urns|seealso{kettles}}")
        self.assertEqual((es[0].kind, es[0].targets), ("see", ["kettles"]))
        self.assertEqual((es[1].kind, es[1].targets), ("seealso", ["kettles"]))

    def test_ranges(self):
        es, _ = latex("\\index{steam|(}\nmore\n\\index{steam|)}")
        self.assertEqual([e.range for e in es], ["open", "close"])
        self.assertEqual([e.line for e in es], [1, 3])

    def test_quoting(self):
        es, _ = latex(r'\index{exclamation "!"@ marks"|x}\index{say ""hi""}')
        self.assertEqual(len(es[0].levels), 1)
        self.assertEqual(es[0].levels[0][0], 'exclamation !@ marks|x')
        self.assertIsNone(es[0].levels[0][1])
        self.assertEqual(es[0].encap, "")
        self.assertEqual(es[1].heading, 'say "hi"')

    def test_escaped_quote_is_accent(self):
        es, _ = latex(r'\index{M\"uller, Anna}')
        self.assertEqual(es[0].heading, "M\u00fcller, Anna")

    def test_optional_arg_comment_and_not_indexentry(self):
        es, _ = latex("\\index[names]{Brun, Ida}\n% \\index{hidden}\n"
                      "\\indexspace \\indexname")
        self.assertEqual([e.heading for e in es], ["Brun, Ida"])

    def test_unbalanced(self):
        es, fs = latex("\\index{broken")
        self.assertEqual(es, [])
        self.assertEqual(fs[0].rule, "MARKUP-PARSE")

    def test_braces_protect_specials(self):
        es, _ = latex(r"\index{{a!b}@x}")
        self.assertEqual(len(es[0].levels), 1)

    def test_idx_file(self):
        es, _ = latex("\\indexentry{gears!spur|hyperpage}{12}\n"
                      "\\indexentry{gears|see{cogs}}{3}\n", fmt="idx")
        self.assertEqual(es[0].path, ("gears", "spur"))
        self.assertEqual(es[0].locator, "12")
        self.assertEqual(es[1].kind, "see")
        self.assertEqual(es[1].line, 2)


# ---------------------------------------------------------------------------
# Syntax: reST / Sphinx
# ---------------------------------------------------------------------------
RST = """\
Title
=====

.. index::
   single: kilns; firing
   pair: glaze; ash
   triple: wood; fired; kiln
   see: ovens; kilns
   seealso: clay; kilns
   !pottery
   :name: idx-one

.. index:: saggars, wadding

Body text with :index:`slip` and :index:`a note <single: slip; trailing>`.
"""


class RstSyntax(unittest.TestCase):
    def setUp(self):
        self.f = []
        self.es = M.read_rst(RST, "t.rst", self.f)

    def paths(self):
        return [(e.kind, e.path, tuple(e.targets)) for e in self.es]

    def test_single_pair_triple(self):
        p = self.paths()
        self.assertIn(("index", ("kilns", "firing"), ()), p)
        self.assertIn(("index", ("glaze", "ash"), ()), p)
        self.assertIn(("index", ("ash", "glaze"), ()), p)
        self.assertIn(("index", ("wood", "fired kiln"), ()), p)
        self.assertIn(("index", ("fired", "kiln, wood"), ()), p)
        self.assertIn(("index", ("kiln", "wood fired"), ()), p)

    def test_see_seealso_main_plain_role(self):
        p = self.paths()
        self.assertIn(("see", ("ovens",), ("kilns",)), p)
        self.assertIn(("seealso", ("clay",), ("kilns",)), p)
        self.assertIn(("index", ("pottery",), ()), p)
        self.assertIn(("index", ("saggars",), ()), p)
        self.assertIn(("index", ("wadding",), ()), p)
        self.assertIn(("index", ("slip",), ()), p)
        self.assertIn(("index", ("slip", "trailing"), ()), p)
        self.assertFalse(any("idx-one" in " ".join(e.path) for e in self.es))

    def test_line_numbers(self):
        by = {e.path: e.line for e in self.es}
        self.assertEqual(by[("kilns", "firing")], 5)
        self.assertEqual(by[("saggars",)], 13)
        self.assertEqual(by[("slip",)], 15)

    def test_malformed_see(self):
        f = []
        M.read_rst(".. index:: see: lonely\n", "x.rst", f)
        self.assertEqual(f[0].rule, "MARKUP-PARSE")

    def test_old_pair_types(self):
        es = M.read_rst(".. index:: module: kilnlib\n", "x.rst", [])
        self.assertEqual({e.path for e in es},
                         {("module", "kilnlib"), ("kilnlib", "module")})


# ---------------------------------------------------------------------------
# Syntax: DITA
# ---------------------------------------------------------------------------
DITA = """\
<topic id="t"><title>Looms</title><body>
<p>Weaving<indexterm>looms<indexterm>treadle</indexterm></indexterm>.</p>
<!-- <indexterm>commented out</indexterm> -->
<p><indexterm><ph>"Jenny"</ph> spinning<index-sort-as>jenny spinning</index-sort-as></indexterm></p>
<p><indexterm>heddles<index-see>looms<indexterm>treadle</indexterm></index-see></indexterm>
<indexterm>shuttles<index-see-also>looms</index-see-also></indexterm></p>
<p><indexterm start="r1">warping</indexterm> ... <indexterm end="r1"/>
&nbsp;<indexterm start="r2">sizing</indexterm></p>
</body></topic>
"""


class DitaSyntax(unittest.TestCase):
    def setUp(self):
        self.f = []
        self.es = M.read_dita(DITA, "t.dita", self.f)

    def test_nested_and_comment(self):
        paths = [e.path for e in self.es if e.kind == "index"]
        self.assertIn(("looms", "treadle"), paths)
        self.assertNotIn(("looms",), paths)
        self.assertFalse(any("commented" in p[0] for p in paths))

    def test_sort_as(self):
        e = [e for e in self.es if e.heading.startswith('"Jenny"')][0]
        self.assertEqual(e.levels[0][1], "jenny spinning")
        self.assertEqual(e.line, 4)

    def test_see_targets(self):
        see = [e for e in self.es if e.kind == "see"][0]
        self.assertEqual(see.targets, ["looms, treadle"])
        also = [e for e in self.es if e.kind == "seealso"][0]
        self.assertEqual(also.targets, ["looms"])

    def test_ranges(self):
        rng = [(e.range, e.range_key) for e in self.es if e.range]
        self.assertEqual(rng, [("open", "r1"), ("close", "r1"),
                               ("open", "r2")])

    def test_malformed(self):
        f = []
        M.read_dita("<p><indexterm>a<b></indexterm></p>", "x.dita", f)
        self.assertEqual(f[0].rule, "MARKUP-PARSE")


# ---------------------------------------------------------------------------
# Syntax: custom
# ---------------------------------------------------------------------------
class CustomSyntax(unittest.TestCase):
    def test_kinds(self):
        rx = M.re.compile(r"\[\[(?P<kind>ix|see|see also):(?P<body>[^\]]+)\]\]",
                          M.re.S)
        syn = M.CustomSyntax(rx, xref_sep="=>", target_sep=";")
        txt = ("a [[ix:mills!water|(]] b\n[[ix:mills!water|)]]\n"
               "[[see:watermills=>mills; water]] [[see also:dams=>weirs]]")
        es = M.read_custom(txt, "x.txt", [], syn)
        self.assertEqual(es[0].path, ("mills", "water"))
        self.assertEqual(es[0].range, "open")
        self.assertEqual(es[1].line, 2)
        self.assertEqual(es[2].targets, ["mills", "water"])
        self.assertEqual(es[3].kind, "seealso")

    def test_quotes_not_special(self):
        rx = M.re.compile(r"<<(?P<body>.*?)>>")
        es = M.read_custom('<<"Big Bertha" (crane)>>', "x", [],
                           M.CustomSyntax(rx))
        self.assertEqual(es[0].heading, '"Big Bertha" (crane)')


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
class ConsistencyRules(TmpDir):
    def test_number(self):
        r = self.rules({"a.tex": r"\index{lighthouse}", "b.tex":
                        r"\index{lighthouses}\index{lighthouse}"})
        self.assertEqual(r.count("ISO999-7.2.2.2-NUMBER"), 1)

    def test_number_distinct_qualifiers_not_flagged(self):
        r = self.rules({"a.tex": r"\index{spring (season)}"
                                 r"\index{springs (coils)}"})
        self.assertNotIn("ISO999-7.2.2.2-NUMBER", r)

    def test_number_linked_by_see_not_flagged(self):
        r = self.rules({"a.tex": r"\index{ferries}\index{ferry|see{ferries}}"})
        self.assertNotIn("ISO999-7.2.2.2-NUMBER", r)

    def test_number_in_subentries(self):
        r = self.rules({"a.tex": r"\index{ports!crane}\index{ports!cranes}"})
        self.assertIn("ISO999-7.2.2.2-NUMBER", r)

    def test_name_variants(self):
        _, f = self.lint({"a.rst": ".. index:: single: Okafor, Ngozi Ada\n",
                          "b.rst": ".. index:: single: Okafor, N. A.\n"})
        v = [x for x in f if x.rule == "ISO999-7.3.1.1-VARIANT"]
        self.assertEqual(len(v), 1)
        self.assertTrue(v[0].file.endswith("b.rst"))

    def test_name_different_people_not_flagged(self):
        r = self.rules({"a.rst": ".. index:: single: Okafor, Ngozi\n"
                                 "   single: Okafor, Tunde\n"})
        self.assertNotIn("ISO999-7.3.1.1-VARIANT", r)

    def test_name_distinct_dates_not_flagged(self):
        r = self.rules({"a.tex": r"\index{Varga, P. (1820-1880)}"
                                 r"\index{Varga, Piroska (1901-1970)}"})
        self.assertNotIn("ISO999-7.3.1.1-VARIANT", r)

    def test_inversion_same_words(self):
        r = self.rules({"a.tex": r"\index{Gaunt, Rosalind de}"
                                 r"\index{de Gaunt, Rosalind}"})
        self.assertIn("ISO999-6.3-INVERSION", r)

    def test_inversion_same_words_linked_ok(self):
        r = self.rules({"a.tex": r"\index{de Gaunt, Rosalind}"
                        r"\index{Gaunt, Rosalind de|see{de Gaunt, Rosalind}}"})
        self.assertNotIn("ISO999-6.3-INVERSION", r)

    def test_inversion_sibling_style(self):
        _, f = self.lint({"a.tex": r"\index{kilns, bottle}\index{tunnel kilns}"
                                   r"\index{kilns}"})
        v = [x for x in f if x.rule == "ISO999-6.3-INVERSION"]
        self.assertEqual(len(v), 1)
        self.assertIn("tunnel kilns", v[0].message)

    def test_inversion_names_and_proper_nouns_ignored(self):
        r = self.rules({"a.tex": r"\index{Gaunt, Rosalind}\index{John of Gaunt}"
                                 r"\index{railways, narrow gauge}"
                                 r"\index{Great Northern Railways}"})
        self.assertNotIn("ISO999-6.3-INVERSION", r)

    def test_case_variant(self):
        _, f = self.lint({"a.tex": r"\index{Tide tables}\index{tide tables}"
                                   r"\index{tide tables}"})
        v = [x for x in f if x.rule == "ISO999-6.3-CASE"]
        self.assertEqual(len(v), 1)
        self.assertIn('"Tide tables"', v[0].message)
        self.assertNotIn("ISO999-7.2.2.2-NUMBER", [x.rule for x in f])


class SortAsRules(TmpDir):
    def test_symbol_quote_markup(self):
        r = self.rules({"a.tex": "\\index{\\emph{Argo}}\\index{`Nell'}"
                                 "\\index{Argo@\\emph{Argo}}"})
        self.assertEqual(r.count("ISO999-8.1-SORTAS"), 2)

    def test_numeral_is_info(self):
        _, f = self.lint({"a.dita": "<p><indexterm>1918 armistice</indexterm>"
                          "<indexterm>1920s<index-sort-as>nineteen twenties"
                          "</index-sort-as></indexterm></p>"})
        v = [x for x in f if x.rule == "ISO999-8.3-SORTAS"]
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0].severity, "info")

    def test_nonascii_latex_info_only(self):
        _, f = self.lint({"a.tex": "\\index{\u00c5ngstr\u00f6m, A. J.}",
                          "b.rst": ".. index:: \u00c5land\n"})
        v = [x for x in f if x.rule == "ISO999-8.1-SORTAS"]
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0].severity, "info")
        self.assertTrue(v[0].file.endswith("a.tex"))

    def test_accent_macro_flagged(self):
        r = self.rules({"a.tex": r"\index{\'Etienne, Luc}"})
        self.assertIn("ISO999-8.1-SORTAS", r)

    def test_duplicates_reported_once(self):
        _, f = self.lint({"a.rst": ".. index:: #hashtags\n\n.. index:: "
                                   "#hashtags\n"})
        v = [x for x in f if x.rule == "ISO999-8.1-SORTAS"]
        self.assertEqual(len(v), 1)
        self.assertIn("also", v[0].message)


class XrefRules(TmpDir):
    def test_dangling_see_and_seealso(self):
        r = self.rules({"a.tex": r"\index{cogs|see{gears}}"
                                 r"\index{pulleys|seealso{belts}}"
                                 r"\index{pulleys}"})
        self.assertIn("ISO999-7.5.1-DANGLING", r)
        self.assertIn("ISO999-7.5.2-DANGLING", r)

    def test_resolves_subentry_target_and_multi(self):
        r = self.rules({"a.tex": r"\index{gears!spur}\index{belts}"
                                 r"\index{cogs|see{gears, spur}}"
                                 r"\index{pulleys|seealso{belts; gears}}"
                                 r"\index{pulleys}"})
        self.assertFalse([x for x in r if "DANGLING" in x], r)

    def test_chain(self):
        _, f = self.lint({"a.rst": ".. index::\n   see: autos; cars\n"
                          "   see: cars; motor vehicles\n"
                          "   single: motor vehicles\n"})
        v = [x for x in f if x.rule == "ISO999-7.5.1-CHAIN"]
        self.assertEqual(len(v), 1)
        self.assertIn('"autos"', v[0].message)

    def test_cycle(self):
        r = self.rules({"a.tex": r"\index{alpha|see{beta}}"
                                 r"\index{beta|see{gamma}}"
                                 r"\index{gamma|see{alpha}}"})
        self.assertEqual(r.count("ISO999-7.5.1-CYCLE"), 1)
        self.assertNotIn("ISO999-7.5.1-CHAIN", r)

    def test_see_with_locators(self):
        _, f = self.lint({"a.tex": r"\index{cogs|see{gears}}\index{gears}",
                          "b.tex": r"\index{cogs}"})
        v = [x for x in f if x.rule == "ISO999-3.13-LOCATORS"]
        self.assertEqual(len(v), 1)
        self.assertIn("b.tex:1", v[0].message)

    def test_see_with_subentries(self):
        _, f = self.lint({"a.tex": r"\index{cogs|see{gears}}\index{gears}"
                                   r"\index{cogs!wooden}"})
        v = [x for x in f if x.rule == "ISO999-3.13-LOCATORS"]
        self.assertIn("subentries", v[0].message)

    def test_seealso_with_locators_ok(self):
        r = self.rules({"a.tex": r"\index{cogs|seealso{gears}}\index{gears}"
                                 r"\index{cogs}"})
        self.assertEqual([x for x in r if x != "MARKUP-PARSE"], [])

    def test_self(self):
        r = self.rules({"a.tex": r"\index{cogs|see{Cogs}}"})
        self.assertIn("ISO999-7.5-SELF", r)

    def test_repeated_see_reported_once(self):
        _, f = self.lint({"a.tex": r"\index{cogs|see{gears}}" * 3})
        v = [x for x in f if x.rule == "ISO999-7.5.1-DANGLING"]
        self.assertEqual(len(v), 1)


class RangeRules(TmpDir):
    def test_unclosed_and_stray(self):
        _, f = self.lint({"a.tex": "\\index{tides|(}\n\\index{waves|)}\n"})
        r = sorted(x.rule for x in f)
        self.assertEqual(r, ["ISO999-7.4.3.1-STRAY",
                             "ISO999-7.4.3.1-UNCLOSED"])

    def test_across_files_ok(self):
        r = self.rules({"ch1.tex": r"\index{tides|(textbf}",
                        "ch2.tex": r"\index{tides|)textbf}"})
        self.assertEqual(r, [])

    def test_double_open(self):
        r = self.rules({"a.tex": r"\index{tides|(}\index{tides|(}"
                                 r"\index{tides|)}"})
        self.assertEqual(r, ["ISO999-7.4.3.1-UNCLOSED"])

    def test_dita_ids(self):
        r = self.rules({"a.dita": '<p><indexterm start="x">tides</indexterm>'
                                  '<indexterm end="y"/></p>'})
        self.assertEqual(sorted(r), ["ISO999-7.4.3.1-STRAY",
                                     "ISO999-7.4.3.1-UNCLOSED"])

    def test_idx_scoped_per_file(self):
        r = self.rules({"a.idx": "\\indexentry{tides|(}{3}\n",
                        "b.idx": "\\indexentry{tides|)}{9}\n"})
        self.assertEqual(sorted(r), ["ISO999-7.4.3.1-STRAY",
                                     "ISO999-7.4.3.1-UNCLOSED"])


# ---------------------------------------------------------------------------
# CLI, walking, summary
# ---------------------------------------------------------------------------
def cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = M.main(argv)
    return code, out.getvalue(), err.getvalue()


class Cli(TmpDir):
    def test_walk_auto_and_json(self):
        self.write("book/ch1.tex", "\\index{lighthouse}\n\\index{lighthouses}")
        self.write("book/notes.txt", "no markup here")
        self.write("book/img.png", "\0\0binary")
        self.write("book/.git/x.tex", "\\index{hidden}")
        self.write("book/topic.dita", "<indexterm>lighthouse</indexterm>")
        code, out, _ = cli([self.dir, "--json"])
        self.assertEqual(code, 1)
        doc = json.loads(out)
        s = doc["summary"]
        self.assertEqual(sorted(f["format"] for f in s["files"]),
                         ["dita", "latex"])
        self.assertEqual(s["entries"], 3)
        self.assertEqual(s["distinct_headings"], 2)
        self.assertEqual(s["variant_clusters"][0]["forms"],
                         ["lighthouse", "lighthouses"])
        f = doc["findings"][0]
        self.assertEqual(f["rule"], "ISO999-7.2.2.2-NUMBER")
        self.assertEqual(f["clause"], "7.2.2.2")
        self.assertEqual(f["line"], 2)
        self.assertIn("related", f)

    def test_text_output_and_clean_exit(self):
        p = self.write("a.rst", ".. index:: harbours\n")
        code, out, _ = cli([p])
        self.assertEqual(code, 0)
        self.assertIn("1 entries, 1 distinct headings", out)

    def test_forced_format_filters_walk(self):
        self.write("a.tex", "\\index{x|see{nowhere}}")
        self.write("b.rst", ".. index:: see: y; nowhere\n")
        code, out, _ = cli([self.dir, "--format", "rst", "--json"])
        doc = json.loads(out)
        self.assertEqual([f["format"] for f in doc["summary"]["files"]],
                         ["rst"])

    def test_usage_errors(self):
        self.assertEqual(cli([])[0], 2)
        self.assertEqual(cli([self.dir, "--format", "custom"])[0], 2)
        self.assertEqual(cli([self.dir, "--format", "custom",
                              "--entry-regex", "(x"])[0], 2)
        self.assertEqual(cli([self.dir, "--format", "custom",
                              "--entry-regex", "x"])[0], 2)
        self.assertEqual(cli([os.path.join(self.dir, "missing")])[0], 2)

    def test_list_rules(self):
        code, out, _ = cli(["--list-rules"])
        self.assertEqual(code, 0)
        for rid in M.RULES:
            self.assertIn(rid, out)

    def test_custom_ext_filter(self):
        self.write("a.md", "{{index: gears}} {{see: cogs|wheels}}")
        self.write("b.txt", "{{see: cogs|wheels}}")
        code, out, _ = cli([self.dir, "--format", "custom", "--entry-regex",
                            PELLOW_REGEX, "--ext", "md", "--json"])
        doc = json.loads(out)
        self.assertEqual(len(doc["summary"]["files"]), 1)
        self.assertEqual(doc["summary"]["by_rule"],
                         {"ISO999-7.5.1-DANGLING": 1})

    def test_entries_flag(self):
        p = self.write("a.tex", "\\index{gears!spur@\\emph{spur}}")
        code, out, _ = cli([p, "--json", "--entries"])
        e = json.loads(out)["entries"][0]
        self.assertEqual(e["path"], ["gears", "spur"])
        self.assertEqual(e["sort_as"], [None, "spur"])


# ---------------------------------------------------------------------------
# End to end: pellow-valley eval fixture (markup defects M1-M5, decoys D2/D3)
# ---------------------------------------------------------------------------
@unittest.skipUnless(os.path.isdir(PELLOW_DOCS), "pellow-valley fixture absent")
class PellowValley(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        code, out, _ = cli([PELLOW_DOCS, "--format", "custom",
                            "--entry-regex", PELLOW_REGEX, "--json"])
        cls.code = code
        cls.doc = json.loads(out)
        cls.f = cls.doc["findings"]

    def find(self, rule, *needles):
        return [f for f in self.f if f["rule"] == rule and
                all(n in f["message"] for n in needles)]

    def test_m1_singular_plural(self):
        hits = self.find("ISO999-7.2.2.2-NUMBER", '"signal boxes"',
                         '"signal box"')
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0]["file"].endswith("03-operations.md"))
        self.assertEqual(hits[0]["line"], 41)

    def test_m2_name_forms(self):
        hits = self.find("ISO999-7.3.1.1-VARIANT", '"Thomas, J. H."',
                         '"Thomas, John Hywel"')
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["line"], 48)

    def test_m3_inversion(self):
        hits = self.find("ISO999-6.3-INVERSION", '"bridges, iron"',
                         '"timber bridges"')
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0]["file"].endswith("02-construction.md"))
        self.assertEqual(hits[0]["line"], 23)

    def test_m4_blind_see(self):
        hits = self.find("ISO999-7.5.1-DANGLING", '"sheds"', '"engine sheds"')
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0]["file"].endswith("03-operations.md"))
        self.assertEqual(hits[0]["line"], 37)

    def test_m5_see_chain(self):
        hits = self.find("ISO999-7.5.1-CHAIN", '"rails"', '"permanent way"',
                         '"track"')
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0]["file"].endswith("02-construction.md"))
        self.assertEqual(hits[0]["line"], 15)

    def test_no_decoys_and_nothing_else(self):
        text = json.dumps(self.f)
        self.assertNotIn("Iolo", text)          # D2
        self.assertNotIn("gauge", text)         # D3
        self.assertEqual(len(self.f), 5, [f["message"] for f in self.f])
        self.assertEqual(self.code, 1)

    def test_summary(self):
        s = self.doc["summary"]
        self.assertEqual(s["entries"], 77)
        self.assertEqual(len([c for c in s["variant_clusters"]]), 3)
        counts = {os.path.basename(f["file"]): f["entries"]
                  for f in s["files"]}
        self.assertEqual(counts["03-operations.md"], 20)


class TestEvicted(TmpDir):
    """iCloud-evicted (dataless) files and slow reads never stall a walk.
    os.stat and open are faked; no real iCloud file is touched."""

    TEX = "\\index{alpha}\n"

    def setUp(self):
        super().setUp()
        for name in ("ok.tex", "gone.tex", "sparse.tex", "slow.tex",
                     "cloudy/c.tex"):
            self.write(name, self.TEX)
        with open(os.path.join(self.dir, ".notes.tex.icloud"), "wb") as fh:
            fh.write(b"bplist00")

    def fake_stat(self, flags=None, blocks0=()):
        real = os.stat
        flags = flags or {}

        def fake(path, *a, **kw):
            st = real(path, *a, **kw)
            name = os.path.basename(os.fspath(path))
            if name in flags or name in blocks0:
                return type("S", (), {
                    "st_mode": st.st_mode, "st_size": st.st_size,
                    "st_flags": flags.get(name, 0),
                    "st_blocks": 0 if name in blocks0 else st.st_blocks,
                    "st_mtime": st.st_mtime})()
            return st
        patcher = mock.patch.object(M.os, "stat", fake)
        patcher.start()
        self.addCleanup(patcher.stop)

    def names(self, files):
        return sorted(os.path.basename(f) for f, _, _ in files)

    def test_constant(self):
        self.assertEqual(M.SF_DATALESS, 0x40000000)

    def test_dataless_and_placeholders_skipped(self):
        self.fake_stat(flags={"gone.tex": M.SF_DATALESS,
                              "cloudy": M.SF_DATALESS},
                       blocks0=("sparse.tex",))
        skipped = []
        files, _, _, errors = M.run([self.dir], skipped=skipped)
        self.assertEqual(self.names(files), ["ok.tex", "slow.tex"])
        self.assertEqual(errors, [])
        got = sorted((os.path.basename(x["file"]), x["reason"], x["dir"])
                     for x in skipped)
        self.assertEqual(got, [(".notes.tex.icloud", M.NOT_LOCAL, False),
                               ("cloudy", M.NOT_LOCAL, True),
                               ("gone.tex", M.NOT_LOCAL, False),
                               ("sparse.tex", M.NOT_LOCAL, False)])
        s = M.summarise(files, [], [], skipped)
        self.assertEqual(s["skipped"], {M.NOT_LOCAL: 4, M.READ_TIMEOUT: 0})
        # --include-evicted reads them; the .icloud stub stays skipped
        skipped = []
        files, _, _, _ = M.run([self.dir], include_evicted=True,
                               skipped=skipped)
        self.assertEqual(self.names(files), ["c.tex", "gone.tex", "ok.tex",
                                             "slow.tex", "sparse.tex"])
        self.assertEqual([os.path.basename(x["file"]) for x in skipped],
                         [".notes.tex.icloud"])
        # explicit dataless file / root directory are not opened either
        skipped = []
        files, _, _, _ = M.run([os.path.join(self.dir, "gone.tex"),
                                os.path.join(self.dir, "cloudy")],
                               skipped=skipped)
        self.assertEqual(files, [])
        self.assertEqual(len(skipped), 2)

    def test_empty_file_not_placeholder(self):
        p = self.write("empty.tex", "")
        self.fake_stat(blocks0=("empty.tex",))
        self.assertFalse(M.is_dataless(p))
        self.assertFalse(M.is_dataless(os.path.join(self.dir, "nope.tex")))

    def test_read_timeout(self):
        import threading
        import time
        release = threading.Event()
        self.addCleanup(release.set)
        real_open = open

        def slow_open(path, *a, **kw):
            if os.path.basename(os.fspath(path)) == "slow.tex":
                release.wait(10)
            return real_open(path, *a, **kw)
        M.open = slow_open
        self.addCleanup(delattr, M, "open")
        skipped = []
        t0 = time.monotonic()
        files, _, _, _ = M.run([self.dir], file_timeout=0.2, skipped=skipped)
        self.assertLess(time.monotonic() - t0, 5)
        self.assertIn("ok.tex", self.names(files))
        self.assertNotIn("slow.tex", self.names(files))
        self.assertEqual([(os.path.basename(x["file"]), x["reason"])
                          for x in skipped if x["reason"] == M.READ_TIMEOUT],
                         [("slow.tex", M.READ_TIMEOUT)])
        lingering = [t for t in threading.enumerate()
                     if t.name == "iso999-read"]
        self.assertTrue(lingering and all(t.daemon for t in lingering))
        release.set()
        with self.assertRaises(OSError):
            M.read_bytes(os.path.join(self.dir, "missing.tex"), 1)

    def test_cli(self):
        self.fake_stat(flags={"gone.tex": M.SF_DATALESS})
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            M.main([self.dir, "--json", "--file-timeout", "3"])
        doc = json.loads(out.getvalue())
        self.assertEqual(doc["summary"]["skipped"][M.NOT_LOCAL], 2)
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            M.main([self.dir])
        self.assertIn("not-local (iCloud/dataless) 2", out.getvalue())
        self.assertIn("--include-evicted", out.getvalue())
        for bad in ("-1", "x"):
            with redirect_stderr(io.StringIO()), \
                    self.assertRaises(SystemExit) as cm:
                M.main([self.dir, "--file-timeout", bad])
            self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
