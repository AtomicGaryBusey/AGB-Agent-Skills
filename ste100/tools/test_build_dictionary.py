#!/usr/bin/env python3
"""Tests for build_dictionary.py.

All page text in these tests is INVENTED (nonsense words such as "blent" and
"glimmet"). No row of the real ASD-STE100 dictionary appears here. The
synthetic pages copy only the layout facts the parser uses: four column
edges, bold headwords with a short font box, and a running header/footer.

Run: python3 -m unittest tools/test_build_dictionary.py  (or pytest)
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_dictionary as bd  # noqa: E402

REPO = HERE.parent
REAL_CACHE = REPO / ".cache" / "ste100-dictionary.json"
FIXTURE = HERE / "fixtures" / "mini_dictionary.json"

# Column edges and font box heights as the parser expects them.
C0, C1, C2, C3 = 72.0, 180.0, 309.65, 439.27
BOLD_H, BODY_H = 10.2, 15.07
LINE = 12.0


class Page:
    """Build one synthetic ``pdftotext -bbox`` page."""

    def __init__(self, footer="2-1-Z1"):
        self.words = []
        self._w(207, 43.2, "ASD-STE100", BOLD_H)
        self._w(C0, 67.2, "Word", 9.2)
        self._w(C1, 67.2, "Approved", 9.2)
        self._w(C2, 78.9, "STE", 9.2)
        self._w(C3, 78.9, "Non-STE", 9.2)
        self._w(C0, 727.0, "Page", BOLD_H)
        self._w(C0 + 30, 727.0, footer, BOLD_H)

    def _w(self, x, y, text, h):
        self.words.append((x, y, x + 6 * len(text), y + h, text))

    def line(self, col_x, y, text, bold=False, indent=0.0):
        x = col_x + indent
        for tok in text.split():
            self._w(x, y if bold else y - 3.5, tok, BOLD_H if bold else BODY_H)
            x += 6 * len(tok) + 3
        return self

    def cell(self, col_x, y, lines, bold=False, indent=0.0):
        for i, t in enumerate(lines):
            self.line(col_x, y + i * LINE, t, bold, indent)
        return self

    def html(self):
        rows = "".join(
            '<word xMin="%f" yMin="%f" xMax="%f" yMax="%f">%s</word>\n'
            % (x0, y0, x1, y1, t.replace("&", "&amp;").replace("<", "&lt;"))
            for x0, y0, x1, y1, t in self.words
        )
        return '<page width="612" height="792">\n%s</page>\n' % rows


def doc(*pages):
    return "<html><body><doc>\n%s</doc></body></html>" % "".join(p.html() for p in pages)


def sample_page():
    """One invented dictionary page with the tricky cases."""
    p = Page()
    y = 95.0
    # Approved verb, forms one per line, commas missing on some lines.
    p.cell(C0, y, ["BLENT (v)", "BLENTS", "BLENTED,", "BLENTED"], bold=True)
    p.cell(C1, y, ["1. To join two zibs", "into one"])
    p.cell(C1, y + 2 * LINE + 6, ["2. To mix a glim"])
    p.cell(C2, y, ["BLENT THE ZIBS.", "EXAMPLE TEXT HERE", "MORE TEXT", "END."])
    y += 4 * LINE + 20
    # Not-approved verb: TN and TV alternatives, a qualifier in parentheses.
    p.cell(C0, y, ["grallow (v)"], bold=True)
    p.cell(C1, y, ["WOBBLATE (TV)", "BLENT (v)", "(WITH A WOBBIN [TN])", "QUIBBET (TN)"])
    p.cell(C3, y, ["Do not grallow it."])
    y += 4 * LINE + 20
    # Approved adjective with comparative and superlative forms.
    p.cell(C0, y, ["FRUMP (adj)", "(FRUMPER,", "FRUMPEST)"], bold=True)
    p.cell(C1, y, ["Having a high glim", "level"])
    y += 3 * LINE + 20
    # Headword that wraps with a soft hyphen, part of speech on line two.
    p.cell(C0, y, ["SNORKEL-", "WAPPY (adv)"], bold=True)
    p.cell(C1, y, ["In a snorkelwappy way"])
    y += 2 * LINE + 20
    # Headword with the part of speech alone on the next line; phrase alt.
    p.cell(C0, y, ["zantiferously", "(adv)"], bold=True)
    p.cell(C1, y, ["AT THE SAME", "GLIMMET"])
    y += 2 * LINE + 20
    # Several parts of speech: separate rows; help text in column 1 and 2.
    p.cell(C0, y, ["GLIMMET (n)"], bold=True)
    p.cell(C1, y, ["A small part of a zib"])
    p.cell(C1, y + 2 * LINE, ["For other", "meanings, use:"], indent=34)
    p.cell(C1, y + 4 * LINE, ["QUASK (adv)"])
    y += 5 * LINE + 20
    p.cell(C0, y, ["glimmet (v)"], bold=True)
    p.cell(C1, y, ["BLENT (v), BROVE (v)"])
    p.cell(C1, y + 2 * LINE, ["Refer also to", "FRUMP (adj)."], indent=34)
    y += 4 * LINE + 20
    # Headword without a part of speech; verb with "No other verb forms."
    p.cell(C0, y, ["PLUX EXEMPLI"], bold=True)
    p.cell(C1, y, ["Used to introduce a", "sample zib"])
    y += 2 * LINE + 20
    p.cell(C0, y, ["WUB (v),", "WUB, WUBBO", "(also WIBS, WOBS)"], bold=True)
    p.cell(C0, y + 3 * LINE, ["No other verb", "forms."], indent=34)
    p.cell(C1, y, ["Auxiliary word that", "means to glim"])
    y += 5 * LINE + 20
    # Paren headword and a phrase alternative with an ellipsis.
    p.cell(C0, y, ["vorp (as vorp as)", "(conj)"], bold=True)
    p.cell(C1, y, ["TOLLO (prep) … AGAIN"])
    y += 2 * LINE + 20
    p.cell(C0, y, ["drelled (adj)"], bold=True)
    p.cell(C1, y, ["Use a different", "construction."], indent=34)
    return p


def parsed(pages_html):
    pages = bd.parse_bbox_html(pages_html)
    raw, diag = bd.parse_dictionary(pages)
    return {(e["display"], e["pos"]): e for e in raw}, raw, diag


class TestPageModel(unittest.TestCase):
    def test_bbox_parse_and_dictionary_page(self):
        pages = bd.parse_bbox_html(doc(sample_page()))
        self.assertEqual(len(pages), 1)
        self.assertTrue(bd.is_dictionary_page(pages[0]))
        intro = Page(footer="2-0-3")
        self.assertFalse(bd.is_dictionary_page(bd.parse_bbox_html(doc(intro))[0]))

    def test_columns_and_bold(self):
        pages = bd.parse_bbox_html(doc(sample_page()))
        lines = bd.page_lines(pages[0], 1)
        cols = {(ln.text, ln.col, ln.bold) for ln in lines}
        self.assertIn(("BLENT (v)", 0, True), cols)       # headword
        self.assertIn(("BLENT (v)", 1, False), cols)      # an alternative
        self.assertIn(("1. To join two zibs", 1, False), cols)
        self.assertIn(("No other verb", 0, False), cols)  # help in column 1
        cols = {t for t, _c, _b in cols}
        # Columns 3 and 4 (examples) are never read.
        self.assertFalse(any("BLENT THE ZIBS" in t for t in cols))
        self.assertFalse(any("grallow it" in t for t in cols))


class TestHeadwords(unittest.TestCase):
    def setUp(self):
        self.by, self.raw, self.diag = parsed(doc(sample_page()))

    def test_entry_list(self):
        self.assertEqual(
            [(e["display"], e["pos"]) for e in self.raw],
            [("BLENT", "v"), ("grallow", "v"), ("FRUMP", "adj"),
             ("SNORKELWAPPY", "adv"), ("zantiferously", "adv"), ("GLIMMET", "n"),
             ("glimmet", "v"), ("PLUX EXEMPLI", None), ("WUB", "v"),
             ("vorp (as vorp as)", "conj"), ("drelled", "adj")])
        self.assertEqual(self.diag["leftover_text"], [])

    def test_verb_forms_without_commas(self):
        self.assertEqual(self.by[("BLENT", "v")]["forms_listed"], ["BLENTS", "BLENTED", "BLENTED"])

    def test_also_forms_and_no_other_forms(self):
        e = self.by[("WUB", "v")]
        self.assertEqual(e["forms_listed"], ["WUB", "WUBBO", "WIBS", "WOBS"])
        self.assertTrue(e["no_other_forms"])

    def test_adjective_comparatives(self):
        self.assertEqual(self.by[("FRUMP", "adj")]["forms_listed"], ["FRUMPER", "FRUMPEST"])

    def test_approval_from_case(self):
        self.assertTrue(self.by[("GLIMMET", "n")]["approved"])
        self.assertFalse(self.by[("glimmet", "v")]["approved"])
        self.assertFalse(self.by[("vorp (as vorp as)", "conj")]["approved"])


class TestColumnTwo(unittest.TestCase):
    def setUp(self):
        self.by, _raw, _diag = parsed(doc(sample_page()))

    def test_multiline_meaning(self):
        self.assertEqual(self.by[("BLENT", "v")]["meaning"], "To join two zibs into one")
        self.assertEqual(self.by[("FRUMP", "adj")]["meaning"], "Having a high glim level")

    def test_tn_tv_and_context(self):
        alts = self.by[("grallow", "v")]["alternatives"]
        self.assertEqual(alts[0], {"word": "wobblate", "pos": None, "kind": "TV"})
        self.assertEqual(alts[1]["word"], "blent")
        self.assertEqual(alts[1]["pos"], "v")
        self.assertEqual(alts[1]["context"], "with a wobbin")
        self.assertEqual(alts[2], {"word": "quibbet", "pos": None, "kind": "TN"})

    def test_wrapped_phrase_alternative(self):
        self.assertEqual(self.by[("zantiferously", "adv")]["alternatives"],
                         [{"word": "at the same glimmet", "pos": None, "kind": "approved"}])

    def test_list_on_one_line(self):
        alts = self.by[("glimmet", "v")]["alternatives"]
        self.assertEqual([(a["word"], a["pos"]) for a in alts], [("blent", "v"), ("brove", "v")])

    def test_help_and_other_meanings(self):
        e = self.by[("GLIMMET", "n")]
        self.assertEqual(e["meaning"], "A small part of a zib")
        self.assertEqual(e["alternatives"], [{"word": "quask", "pos": "adv", "kind": "approved"}])
        self.assertEqual(self.by[("glimmet", "v")]["refs"], ["frump (adj)"])

    def test_tag_wrapped_to_next_line(self):
        # A long alternative whose tag is alone on the next line keeps the tag.
        self.assertEqual(bd.parse_alternatives("FLOOBERATING\n(TN)"),
                         [{"word": "flooberating", "pos": None, "kind": "TN"}])
        self.assertEqual(bd.parse_alternatives("SNORKILY\n(adv)"),
                         [{"word": "snorkily", "pos": "adv", "kind": "approved"}])
        self.assertEqual(bd.parse_alternatives("GLIM (v), SNORKILY\n(adj),"),
                         [{"word": "glim", "pos": "v", "kind": "approved"},
                          {"word": "snorkily", "pos": "adj", "kind": "approved"}])
        # A phrase whose last tag wraps stays one phrase without a context.
        self.assertEqual(bd.parse_alternatives("ONE (TN) OF THE ZIBS\n(TN)"),
                         [{"word": "one of the zibs", "pos": None, "kind": "approved"}])
        # A qualifier on the next line still attaches as context.
        alts = bd.parse_alternatives("BLENT (v)\n(WITH A WOBBIN [TN])")
        self.assertEqual(alts[0]["context"], "with a wobbin")

    def test_ellipsis_phrase(self):
        self.assertEqual(self.by[("vorp (as vorp as)", "conj")]["alternatives"],
                         [{"word": "tollo … again", "pos": None, "kind": "approved"}])

    def test_help_only_entry_is_a_note(self):
        e = self.by[("drelled", "adj")]
        self.assertEqual(e["alternatives"], [])
        self.assertTrue(e["help"])

    def test_meaning_is_short(self):
        long_text = "one two three four five six seven eight nine ten eleven twelve thirteen"
        self.assertEqual(len(bd.short_meaning("1. " + long_text).split()), 13)  # 12 + "…"
        self.assertTrue(bd.short_meaning(long_text).endswith("…"))


class TestPageBreaks(unittest.TestCase):
    def test_row_split_across_pages(self):
        p1, p2 = Page("2-1-Z1"), Page("2-1-Z2")
        p1.cell(C0, 680.0, ["BROVE (v),", "BROVES,"], bold=True)
        p1.cell(C1, 680.0, ["To move a zib to a new", "place"])
        p2.cell(C0, 95.0, ["BROVE,", "BROVEN"], bold=True)
        p2.cell(C0, 140.0, ["QUASK (adv)"], bold=True)
        p2.cell(C1, 140.0, ["In a frump manner"])
        by, raw, diag = parsed(doc(p1, p2))
        self.assertEqual(by[("BROVE", "v")]["forms_listed"], ["BROVES", "BROVE", "BROVEN"])
        self.assertEqual(by[("BROVE", "v")]["meaning"], "To move a zib to a new place")
        self.assertEqual(len(raw), 2)

    def test_meaning_continues_on_next_page(self):
        p1, p2 = Page("2-1-Z1"), Page("2-1-Z2")
        p1.cell(C0, 690.0, ["TOLLO (prep)"], bold=True)
        p1.cell(C1, 690.0, ["In a position"])
        p2.cell(C1, 95.0, ["QUIBBET (TN)"])
        by, _raw, _diag = parsed(doc(p1, p2))
        self.assertEqual(by[("TOLLO", "prep")]["meaning"], "In a position")
        self.assertEqual(by[("TOLLO", "prep")]["alternatives"][0]["kind"], "TN")


class TestForms(unittest.TestCase):
    def entry(self, display, pos, listed=(), approved=None):
        return {"display": display, "pos": pos, "forms_listed": list(listed),
                "approved": bd.is_approved(display) if approved is None else approved}

    def test_approved_verb_uses_only_listed_forms(self):
        forms, variants = bd.compute_forms(self.entry("BLENT", "v", ["BLENTS", "BLENTED", "BLENTED"]))
        self.assertEqual(forms, ["blent", "blents", "blented"])
        self.assertEqual(variants, [])
        self.assertNotIn("blenting", forms)  # -ing forms are never added

    def test_verb_without_listed_forms(self):
        self.assertEqual(bd.compute_forms(self.entry("WUB", "v"))[0], ["wub"])

    def test_approved_noun_plural(self):
        self.assertEqual(bd.compute_forms(self.entry("GLIMMET", "n"))[0], ["glimmet", "glimmets"])
        self.assertEqual(bd.compute_forms(self.entry("ZIBBY", "n"))[0], ["zibby", "zibbies"])
        self.assertEqual(bd.compute_forms(self.entry("KLOSH", "n"))[0], ["klosh", "kloshes"])

    def test_adjective_forms(self):
        f, _ = bd.compute_forms(self.entry("FRUMP", "adj", ["FRUMPER", "FRUMPEST"]))
        self.assertEqual(f, ["frump", "frumper", "frumpest"])

    def test_not_approved_variants_are_separate(self):
        forms, variants = bd.compute_forms(self.entry("snarfle", "v"))
        self.assertEqual(forms, ["snarfle"])
        self.assertEqual(variants, ["snarfles", "snarfled", "snarfling"])

    def test_paren_headwords(self):
        self.assertEqual(bd.surface_forms_of_headword("vorp (as vorp as)"), ["as vorp as"])
        self.assertEqual(bd.surface_forms_of_headword("zib (that)"), ["zib that"])
        self.assertEqual(bd.surface_forms_of_headword("GLOM (or GLOMME)"), ["glom", "glomme"])

    def test_finalize_index(self):
        by, raw, _ = parsed(doc(sample_page()))
        entries, index = bd.finalize(raw)
        self.assertIn({"word": "blent", "pos": "v", "approved": True}, index["blented"])
        self.assertIn({"word": "frump", "pos": "adj", "approved": True}, index["frumpest"])
        self.assertTrue(all("examples" not in e for e in entries))
        self.assertEqual(set(entries[0]), {"word", "display", "pos", "approved", "meaning",
                                           "forms", "alternatives"})


class TestValidateAndCheck(unittest.TestCase):
    def test_counts_and_problems(self):
        _by, raw, _ = parsed(doc(sample_page()))
        counts, problems, notes = bd.validate(raw, {"approved": 6, "not_approved": 5})
        self.assertEqual(counts, {"approved": 6, "not_approved": 5, "entries": 11})
        self.assertEqual(problems, [])
        self.assertTrue(any("PLUX EXEMPLI" in n for n in notes))
        self.assertTrue(any("drelled" in n for n in notes))
        _c, problems, _n = bd.validate(raw, {"approved": 7, "not_approved": 5})
        self.assertTrue(any("approved count 6 != stated 7" in p for p in problems))

    def test_stated_totals(self):
        words = [(0, 0, 0, 0, t) for t in
                 "The list has words that are approved (12 approved words) and "
                 "words that are not approved (34 words).".split()]
        self.assertEqual(bd.stated_totals([words]), {"approved": 12, "not_approved": 34})
        self.assertEqual(bd.stated_totals([]), bd.DEFAULT_EXPECTED)

    def test_check_sha_mismatch_and_match(self):
        with tempfile.TemporaryDirectory() as d:
            pdf = Path(d, "x.pdf")
            pdf.write_bytes(b"not a real pdf")
            data = json.loads(FIXTURE.read_text(encoding="utf-8"))
            cache = Path(d, "c.json")
            cache.write_text(json.dumps(data), encoding="utf-8")
            with mock.patch("sys.stdout"):
                self.assertEqual(bd.check(cache, pdf, sha_only=True), 1)
            data["meta"]["pdf_sha256"] = hashlib.sha256(b"not a real pdf").hexdigest()
            cache.write_text(json.dumps(data), encoding="utf-8")
            with mock.patch("sys.stdout"):
                self.assertEqual(bd.check(cache, pdf, sha_only=True), 0)
                self.assertEqual(bd.check(Path(d, "missing.json"), pdf, sha_only=True), 1)

    def test_missing_pdftotext_message(self):
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaises(bd.BuildError) as cm:
                bd.require_pdftotext()
        self.assertIn("poppler", str(cm.exception))


class TestFixture(unittest.TestCase):
    def test_fixture_schema(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(set(data), {"meta", "entries", "forms"})
        self.assertIn("INVENTED", data["meta"]["source"])
        for e in data["entries"]:
            for k in ("word", "display", "pos", "approved", "meaning", "forms", "alternatives"):
                self.assertIn(k, e)
            for a in e["alternatives"]:
                self.assertIn(a["kind"], ("approved", "TN", "TV"))
            for f in e["forms"]:
                self.assertIn({"word": e["word"], "pos": e["pos"], "approved": e["approved"]},
                              data["forms"][f])
        c = data["meta"]["counts"]
        self.assertEqual(c["approved"], sum(e["approved"] for e in data["entries"]))


@unittest.skipUnless(REAL_CACHE.exists(), "no local .cache/ste100-dictionary.json (build it first)")
class TestRealCache(unittest.TestCase):
    """Checks on the user's locally built cache. Skipped when it is absent."""

    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(REAL_CACHE.read_text(encoding="utf-8"))

    def test_meta(self):
        m = self.data["meta"]
        self.assertEqual(m["source"], "ASD-STE100 Issue 9")
        self.assertEqual(len(m["pdf_sha256"]), 64)
        self.assertEqual(m["builder_version"], bd.BUILDER_VERSION)

    def test_counts(self):
        e = self.data["entries"]
        approved = sum(1 for x in e if x["approved"])
        self.assertEqual(self.data["meta"]["counts"],
                         {"approved": approved, "not_approved": len(e) - approved, "entries": len(e)})
        # The Issue 9 introduction states 875 / 1274 (the same totals as
        # Issue 8). The table itself has 879 / 1319 rows; see the build notes.
        self.assertEqual(approved, 879)
        self.assertEqual(len(e) - approved, 1319)
        self.assertEqual(self.data["meta"]["expected_counts"], {"approved": 875, "not_approved": 1274})

    def test_no_examples_and_short_meanings(self):
        for e in self.data["entries"]:
            self.assertLessEqual(len((e["meaning"] or "").replace(" …", "").split()), 12)
            self.assertFalse({"example", "examples", "ste_example"} & set(e))

    def test_no_part_of_speech_tag_as_context(self):
        # A wrapped "(TN)" or "(adj)" tag is the kind or part of speech, not a context.
        tags = {"tn", "tv", "n", "v", "adj", "adv", "prep", "conj", "pron"}
        for e in self.data["entries"]:
            for a in e["alternatives"]:
                self.assertNotIn(a.get("context"), tags, (e["word"], a))

    def test_approved_verbs_have_forms_indexed(self):
        verbs = [e for e in self.data["entries"] if e["approved"] and e["pos"] == "v"]
        self.assertEqual(len(verbs), 208)
        with_forms = [e for e in verbs if len(e["forms"]) > 1]
        self.assertGreaterEqual(len(with_forms), 200)
        for e in verbs:
            for f in e["forms"]:
                self.assertTrue(any(x["word"] == e["word"] and x["approved"]
                                    for x in self.data["forms"][f]))


if __name__ == "__main__":
    unittest.main()
