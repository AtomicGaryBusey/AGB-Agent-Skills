"""Tests for iso999_lint.py. All fixtures are invented for this suite."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iso999_lint as L  # noqa: E402


def run(text, fmt="text", **kw):
    opts = L.Options(**kw)
    _, findings = L.lint_text(text, fmt, opts)
    return findings


def warns(text, fmt="text", **kw):
    return [f.rule for f in run(text, fmt, **kw) if f.severity == "warn"]


def infos(text, fmt="text", **kw):
    return [f.rule for f in run(text, fmt, **kw) if f.severity == "info"]


def ind(*items):
    return "\\begin{theindex}\n" + "\n".join(items) + "\n\\end{theindex}\n"


CLEAN_TEXT = """\
# Index

A

abacus, 4, 9\u201311
  beads, 12
  wooden frames, 15
  see also counting boards
Aldridge, Petra, 33
counting boards, 14, 30\u201331
harbours see ports
ports, 40, 52
  tidal, 41
tally sticks, 7, 18
"""

CLEAN_IND = ind(
    "  \\item abacus, 4, 9--11, \\seealso{counting boards}{0}",
    "    \\subitem beads, 12",
    "    \\subitem wooden frames, 15",
    "  \\item Aldridge, Petra, 33",
    "  \\indexspace",
    "  \\item counting boards, 14, \\textbf{30--31}",
    "  \\item harbours, \\see{ports}{1}",
    "  \\item ports, 40, 52",
    "    \\subitem tidal, 41",
    "  \\item tally sticks, 7, 18",
)


class TestClean(unittest.TestCase):
    def test_clean_text_has_no_warnings(self):
        self.assertEqual(warns(CLEAN_TEXT), [])

    def test_clean_ind_has_no_warnings(self):
        self.assertEqual(warns(CLEAN_IND, "ind"), [])

    def test_clean_html_has_no_warnings(self):
        html = ("<ul><li>abacus, 4, 9\u201311<ul><li>beads, 12</li>"
                "<li><em>see also</em> counting boards</li></ul></li>"
                "<li>counting boards, 14, 30\u201331</li>"
                "<li>harbours, <em>see</em> ports</li>"
                "<li>ports, 40, 52</li></ul>")
        self.assertEqual(warns(html, "html"), [])


class TestParsing(unittest.TestCase):
    def test_text_structure(self):
        roots = L.build_tree(L.read_text(CLEAN_TEXT))
        heads = [e.heading for e in roots]
        self.assertEqual(heads[:3], ["abacus", "Aldridge, Petra",
                                     "counting boards"])
        abacus = roots[0]
        self.assertEqual([c.heading for c in abacus.children],
                         ["beads", "wooden frames"])
        self.assertEqual(abacus.see_also[0].target, "counting boards")
        self.assertEqual(abacus.see_also_placement, "sub")
        self.assertEqual(len(abacus.locators), 2)
        self.assertEqual(abacus.locators[1].end, 11)

    def test_dash_style_subheadings(self):
        text = "kites, 3\n\u2013 box, 4\n\u2013 delta, 6\nlanterns, 9\n"
        roots = L.build_tree(L.read_text(text))
        self.assertEqual([e.heading for e in roots], ["kites", "lanterns"])
        self.assertEqual(len(roots[0].children), 2)

    def test_italic_see_markdown(self):
        text = "gulls *see* seabirds\nseabirds, 5, 8\n"
        roots = L.build_tree(L.read_text(text))
        self.assertEqual(roots[0].see[0].target, "seabirds")
        self.assertEqual(warns(text), [])

    def test_wrapped_locator_line(self):
        text = "quilting, 3, 5,\n      7, 9\nrugs, 2\n"
        roots = L.build_tree(L.read_text(text))
        self.assertEqual(len(roots[0].locators), 4)

    def test_ind_continuation_and_see(self):
        text = ind("  \\item ports, 40, 52,", "\t\t60",
                   "  \\item wharves, \\see{ports}{3}")
        roots = L.build_tree(L.read_ind(text))
        self.assertEqual(len(roots[0].locators), 3)
        self.assertEqual(roots[1].see[0].target, "ports")
        self.assertEqual(roots[1].locators, [])   # {3} is not a locator

    def test_detect_format(self):
        self.assertEqual(L.detect_format("x.ind", ""), "ind")
        self.assertEqual(L.detect_format("x.html", ""), "html")
        self.assertEqual(L.detect_format("x", "\\item a, 1"), "ind")
        self.assertEqual(L.detect_format("x", "<ul><li>a</li></ul>"), "html")
        self.assertEqual(L.detect_format("x", "a, 1"), "text")

    def test_html_dl(self):
        html = "<dl><dt>otters</dt><dd>7, 8</dd><dt>voles</dt><dd>3</dd></dl>"
        roots = L.build_tree(L.read_html(html))
        self.assertEqual([e.heading for e in roots], ["otters", "voles"])
        self.assertEqual(len(roots[0].locators), 2)


class TestSortKey(unittest.TestCase):
    def k(self, s, mode="word"):
        return L.sort_key(s, mode)

    def test_word_vs_letter(self):
        self.assertLess(self.k("salt marsh"), self.k("saltbox"))
        self.assertGreater(self.k("salt marsh", "letter"),
                           self.k("saltbox", "letter"))

    def test_case_and_diacritics(self):
        self.assertEqual(self.k("\u00c9clair"), self.k("eclair"))
        self.assertEqual(self.k("Mercury"), self.k("mercury"))

    def test_same_term_sequence(self):
        # default --inversion after: inverted heading leads the longer terms
        seq = ["tin", "tin (element)", "tin, cans", "tin mines"]
        keys = [self.k(s) for s in seq]
        self.assertEqual(keys, sorted(keys))
        seq = ["tin", "tin, cans", "tin (element)", "tin mines"]
        keys = [L.sort_key(s, inversion="before") for s in seq]
        self.assertEqual(keys, sorted(keys))

    def test_numerals(self):
        seq = ["3 musketeers", "XII tables", "40 winks", "apple"]
        keys = [L.sort_key(s, roman_list=frozenset({"XII"})) for s in seq]
        self.assertEqual(keys, sorted(keys))
        self.assertLess(self.k("Route 9"), self.k("Route 66"))
        self.assertLess(self.k("Route 66"), self.k("Route one"))


class TestFiling(unittest.TestCase):
    def test_heading_order_text(self):
        self.assertIn("ISO999-8.2-ORDER", warns("walrus, 3\nbadger, 5\n"))

    def test_heading_order_ind(self):
        self.assertIn("ISO999-8.2-ORDER", warns(
            ind("\\item walrus, 3", "\\item badger, 5"), "ind"))

    def test_letter_mode_detected_and_accepted(self):
        text = "saltbox, 2\nsalt marsh, 4\n"
        self.assertIn("ISO999-8.2-ORDER", warns(text))
        self.assertEqual(warns(text, filing="letter"), [])
        mode = [f for f in run(text) if f.rule == "ISO999-8.2-MODE"][0]
        self.assertIn("letter-by-letter", mode.message)

    def test_mixed_methods(self):
        # pair 1 fits word-by-word only; pair 3 fits letter-by-letter only
        text = "salt marsh, 4\nsaltbox, 2\nseabed, 1\nsea wall, 9\n"
        self.assertIn("ISO999-8.2-MIXED", warns(text))
        self.assertIn("ISO999-8.2-MIXED", warns(ind(
            "\\item salt marsh, 4", "\\item saltbox, 2",
            "\\item seabed, 1", "\\item sea wall, 9"), "ind"))

    def test_numerals_after_letters(self):
        text = "apple, 1\n42 steps, 3\n"
        self.assertIn("ISO999-8.3-ORDER", warns(text))
        self.assertIn("ISO999-8.3-ORDER", warns(
            ind("\\item apple, 1", "\\item 42 steps, 3"), "ind"))
        self.assertEqual(warns(text, numerals="ignore"), [])

    def test_same_term_order(self):
        text = "tin mines, 3\ntin (element), 4\n"
        self.assertIn("ISO999-8.5-ORDER", warns(text))
        self.assertIn("ISO999-8.5-ORDER", warns(
            ind("\\item tin mines, 3", "\\item tin (element), 4"), "ind"))

    def test_subheading_order(self):
        text = "gardens, 1\n  roses, 5\n  herbs, 9\n"
        self.assertIn("ISO999-8.6-ORDER", warns(text))
        self.assertIn("ISO999-8.6-ORDER", warns(
            ind("\\item gardens, 1", "\\subitem roses, 5",
                "\\subitem herbs, 9"), "ind"))

    def test_subheading_page_order_warns_unless_declared(self):
        text = "canal, 1\n  surveying, 5\n  opening, 9\n  decline, 12\n"
        self.assertEqual(warns(text), ["ISO999-8.6-PAGEORDER"])
        self.assertEqual(warns(text, subheading_order="page"), [])
        self.assertIn("ISO999-8.6-SYSTEMATIC",
                      infos(text, subheading_order="page"))

    def test_function_words_option(self):
        text = "rivers\n  of dams, 5\n  fishing, 9\n"
        self.assertIn("ISO999-8.6-ORDER", warns(text))
        self.assertEqual(warns(text, func_words=True), [])

    def test_crossref_does_not_affect_position(self):
        text = "peat, 3 see also bogs\npeat cutting, 4\nbogs, 1\n"
        f = [x for x in run(text) if x.rule.endswith("ORDER")]
        self.assertTrue(any("bogs" in x.message for x in f))
        self.assertFalse(any('"peat cutting" files before' in x.message
                             for x in f))


class TestDuplicates(unittest.TestCase):
    def test_case_duplicate_text(self):
        self.assertIn("ISO999-8.1-DUPLICATE",
                      warns("Lantern, 3\nlantern, 7\n"))

    def test_whitespace_duplicate_ind(self):
        self.assertIn("ISO999-8.1-DUPLICATE", warns(
            ind("\\item paper  mills, 3", "\\item paper mills, 7"), "ind"))

    def test_subheading_duplicate(self):
        self.assertIn("ISO999-8.1-DUPLICATE",
                      warns("ink, 1\n  Iron gall, 2\n  iron gall, 3\n"))


class TestLocators(unittest.TestCase):
    CASES = [
        ("ISO999-7.4.3-DUPLICATE", "pewter, 12, 12", "\\item pewter, 12, 12"),
        ("ISO999-7.4.3-OVERLAP", "pewter, 10\u201320, 15",
         "\\item pewter, 10--20, 15"),
        ("ISO999-7.4.3-OVERLAP", "pewter, 10\u201320, 18\u201325",
         "\\item pewter, 10--20, 18--25"),
        ("ISO999-7.4.3.1-REVERSED", "pewter, 30\u201322",
         "\\item pewter, 30--22"),
        ("ISO999-7.4.3.1-OPEN", "pewter, 30ff", "\\item pewter, 30ff"),
        ("ISO999-7.4.3.2-PASSIM", "pewter, 30\u201340 passim",
         "\\item pewter, 30--40 passim"),
        ("ISO999-7.2.3.5-MAXLOC", "pewter, 1, 2, 3, 4, 5, 6, 7",
         "\\item pewter, 1, 2, 3, 4, 5, 6, 7"),
    ]

    def test_each_locator_rule_both_formats(self):
        for rule, text_line, ind_line in self.CASES:
            with self.subTest(rule=rule, fmt="text"):
                self.assertIn(rule, warns(text_line + "\n"))
            with self.subTest(rule=rule, fmt="ind"):
                self.assertIn(rule, warns(ind(ind_line), "ind"))

    def test_max_locators_option(self):
        self.assertEqual(warns("pewter, 1, 2, 3, 4\n", max_locators=4), [])
        self.assertIn("ISO999-7.2.3.5-MAXLOC",
                      warns("pewter, 1, 2, 3, 4\n", max_locators=3))

    def test_mixed_dash(self):
        text = "anvils, 3\u20135\nbellows, 7\u20139\ncoke, 11-14\n"
        self.assertEqual(warns(text), ["ISO999-7.4.3.1-DASH"])
        self.assertEqual(warns(ind("\\item anvils, 3--5",
                                   "\\item bellows, 7--9",
                                   "\\item coke, 11-14"), "ind"),
                         ["ISO999-7.4.3.1-DASH"])

    def test_mixed_elision(self):
        text = ("anvils, 123\u2013125\nbellows, 234\u2013236\n"
                "coke, 345\u20137\n")
        self.assertEqual(warns(text), ["ISO999-7.4.3.1-ELISION"])
        self.assertEqual(warns(ind("\\item anvils, 123--125",
                                   "\\item bellows, 234--236",
                                   "\\item coke, 345--7"), "ind"),
                         ["ISO999-7.4.3.1-ELISION"])

    def test_consistent_elision_is_info_only(self):
        text = "anvils, 123\u20135\nbellows, 234\u20136\n"
        self.assertEqual(warns(text), [])
        self.assertIn("ISO999-7.4.3.1-ELISION", infos(text))

    def test_teens(self):
        self.assertIn("ISO999-7.4.3.1-TEENS", infos("anvils, 212\u20136\n"))

    def test_elided_expansion(self):
        loc = L.parse_locator("345-7", 1)
        self.assertEqual((loc.start, loc.end, loc.elided), (345, 347, True))
        loc = L.parse_locator("345-347", 1)
        self.assertFalse(loc.elided)
        self.assertIsNone(L.parse_locator("98-102", 1).elided)

    def test_roman_before_arabic_is_ascending(self):
        self.assertEqual(warns("preface, iv, vii, 3\n"), [])


class TestCrossRefs(unittest.TestCase):
    CASES = [
        ("ISO999-7.5.1-DANGLING", "moorings see anchorages\n",
         ["\\item moorings, \\see{anchorages}{1}"]),
        ("ISO999-7.5.2-DANGLING", "moorings, 4 see also anchorages\n",
         ["\\item moorings, 4, \\seealso{anchorages}{1}"]),
        ("ISO999-7.5.1-LOCATORS", "berths, 5\nmoorings, 3 see berths\n",
         ["\\item berths, 5", "\\item moorings, 3, \\see{berths}{1}"]),
        ("ISO999-7.5.1-CHAIN",
         "anchorages see berths\nberths see moorings\nmoorings, 3, 8\n",
         ["\\item anchorages, \\see{berths}{1}",
          "\\item berths, \\see{moorings}{1}",
          "\\item moorings, 3, 8"]),
        ("ISO999-7.5.1-CYCLE", "berths see quays\nquays see berths\n",
         ["\\item berths, \\see{quays}{1}", "\\item quays, \\see{berths}{1}"]),
        ("ISO999-7.5-SELF", "quays, 3 see also quays\n",
         ["\\item quays, 3, \\seealso{quays}{1}"]),
        ("ISO999-7.5-TARGETORDER",
         "berths, 2\ndocks, 3\nquays, 4 see also docks; berths\n",
         ["\\item berths, 2", "\\item docks, 3",
          "\\item quays, 4, \\seealso{docks; berths}{1}"]),
        ("ISO999-7.5.2.1-SAMELOC",
         "berths, 2, 9\nquays, 2, 9 see also berths\n",
         ["\\item berths, 2, 9", "\\item quays, 2, 9, \\seealso{berths}{1}"]),
    ]

    def test_each_crossref_rule_both_formats(self):
        for rule, text, ind_items in self.CASES:
            with self.subTest(rule=rule, fmt="text"):
                self.assertIn(rule, warns(text))
            with self.subTest(rule=rule, fmt="ind"):
                self.assertIn(rule, warns(ind(*ind_items), "ind"))

    def test_cycle_not_also_reported_as_chain(self):
        rules = warns("berths see quays\nquays see berths\n")
        self.assertNotIn("ISO999-7.5.1-CHAIN", rules)

    def test_reciprocal_see_also_is_fine(self):
        text = "canoes, 3 see also kayaks\nkayaks, 5 see also canoes\n"
        self.assertEqual(warns(text), [])

    def test_subheading_target_resolves(self):
        text = "boats, 1\n  sails, 4, 6\nrigging see boats: sails\n"
        self.assertNotIn("ISO999-7.5.1-DANGLING", warns(text))

    def test_generic_italic_target_skipped(self):
        text = "birds, 2 see also *individual species*\n"
        self.assertEqual(warns(text), [])

    def test_placement_inconsistent_text(self):
        text = ("berths, 2 see also docks\n"
                "docks, 3 see also quays\n"
                "quays (see also berths) 4\n")
        self.assertEqual(warns(text), ["ISO999-7.5.2.1-PLACEMENT"])

    def test_placement_inconsistent_ind(self):
        text = ind("\\item berths, 2, \\seealso{docks}{0}",
                   "\\item docks, 3, \\seealso{quays}{0}",
                   "\\item quays, \\seealso{berths}{0}, 4")
        self.assertEqual(warns(text, "ind"), ["ISO999-7.5.2.1-PLACEMENT"])

    def test_see_also_only_entry_info(self):
        text = "berths, 2\nquays see also berths\n"
        self.assertIn("ISO999-7.5.2.1-NOREFS", infos(text))

    def test_few_locators_info(self):
        self.assertIn("ISO999-7.5.1-FEW", infos("jetties see piers\npiers, 7\n"))


def heads(text, fmt="text"):
    reader = {"text": L.read_text, "html": L.read_html}[fmt]
    return L.build_tree(reader(text))


class TestSingleSpaceLocators(unittest.TestCase):
    """Item 1: locators joined to the heading by one space."""

    def test_comma_list_after_one_space(self):
        r = heads("quince 12, 3, 30\n")
        self.assertEqual(r[0].heading, "quince")
        self.assertEqual([l.start for l in r[0].locators], [12, 3, 30])

    def test_range_after_one_space(self):
        r = heads("reeds 40–42\n")
        self.assertEqual(r[0].heading, "reeds")
        self.assertEqual(r[0].locators[0].end, 42)

    def test_spaced_range_and_passim(self):
        r = heads("reeds 40 – 42\nsedge 30–40 passim\n")
        self.assertEqual([e.heading for e in r], ["reeds", "sedge"])
        self.assertTrue(r[1].locators[0].passim)

    def test_emphasis_and_prefix_tokens(self):
        r = heads("tundra *14*, 2:30, 31f\n")
        self.assertEqual(r[0].heading, "tundra")
        self.assertEqual(len(r[0].locators), 3)
        self.assertTrue(r[0].locators[0].emphasis)
        self.assertEqual(r[0].locators[1].prefix, 2)

    def test_bare_number_in_one_space_index(self):
        r = heads("almonds 3\nbeets 7\ncress 9\n")
        self.assertEqual([e.heading for e in r], ["almonds", "beets",
                                                  "cress"])
        self.assertTrue(all(len(e.locators) == 1 for e in r))

    def test_comma_index_keeps_number_in_heading(self):
        r = heads("almonds, 3\nHighway 61, 12, 14\nzinnias, 5\n")
        self.assertEqual(r[1].heading, "Highway 61")
        self.assertEqual([l.start for l in r[1].locators], [12, 14])

    def test_place_year_ambiguity_documented(self):
        # 'Place, year' is read as heading + locator; documented limitation
        r = heads("Lisbon, 1755\n")
        self.assertEqual(r[0].heading, "Lisbon")

    def test_roman_after_one_space(self):
        r = heads("foreword ix, xii, 3\nalmonds 2\nbeets 4\n")
        self.assertEqual(r[0].heading, "foreword")
        self.assertEqual(len(r[0].locators), 3)
        r = heads("vitamin c, 12, 14\n")
        self.assertEqual(r[0].heading, "vitamin c")

    def test_numbered_noun_keeps_number(self):
        r = heads("slates in volumes 1–4 see tablets\ntablets, 6\n")
        self.assertEqual(r[0].heading, "slates in volumes 1–4")
        self.assertEqual(r[0].locators, [])

    def test_subheadings_one_space(self):
        r = heads("orchards 5\n  pruning 12, 19\n  grafting 30\n")
        self.assertEqual([c.heading for c in r[0].children],
                         ["pruning", "grafting"])

    def test_html_one_space(self):
        r = heads("<ul><li>quince 12, 30</li></ul>", "html")
        self.assertEqual(r[0].heading, "quince")

    def test_paren_see_line_does_not_vote(self):
        r = heads("quays (see also berths) 4\nberths 2\n")
        self.assertEqual(r[1].heading, "berths")

    def test_one_space_index_is_clean(self):
        self.assertEqual(warns("almonds 3\nbeets 7, 12\ncress 9–11\n"),
                         [])


class TestRomanNumerals(unittest.TestCase):
    """Item 2: acronyms are not roman numerals."""

    ACRONYMS = ("anvils, 3\nCV writing, 8\ncypress, 9\nDIV tags, 12\n"
                "dolphins, 4\nMIX sessions, 5\nmoss, 2\nVI editor, 7\n"
                "violins, 1\n")

    def test_acronyms_file_as_letters(self):
        self.assertEqual(warns(self.ACRONYMS), [])

    def test_context_word_makes_numeral(self):
        text = "2 steps, 1\nXIV dynasty, 3\n40 winks, 5\napples, 9\n"
        self.assertEqual(warns(text), [])
        self.assertIn("ISO999-8.3-ORDER", warns(text, roman="off"))

    def test_roman_list(self):
        text = "3 bears, 1\nXII tables, 3\n40 winks, 5\napples, 9\n"
        self.assertIn("ISO999-8.3-ORDER", warns(text))
        self.assertEqual(warns(text, roman_list=frozenset({"XII"})), [])

    def test_not_whole_first_token(self):
        self.assertIsNone(L._lead_roman("CDs and tapes", "strict",
                                        frozenset({"CD"}))[0])


class TestInversion(unittest.TestCase):
    """Item 3: --inversion before|after."""

    AFTER = "ember, 1\nember (ship), 2\nember, glowing, 3\nember days, 4\n"
    BEFORE = "ember, 1\nember, glowing, 3\nember (ship), 2\nember days, 4\n"

    def test_default_after(self):
        self.assertEqual(warns(self.AFTER), [])
        self.assertIn("ISO999-8.5-ORDER", warns(self.BEFORE))

    def test_before(self):
        self.assertEqual(warns(self.BEFORE, inversion="before"), [])
        self.assertIn("ISO999-8.5-ORDER",
                      warns(self.AFTER, inversion="before"))


class TestPageOrder(unittest.TestCase):
    """Item 4: page-ordered subheadings."""

    TEXT = "docks, 5\n  tolls, 40\n  moorings, 52\n  cranes, 88\n"

    def test_page_order_warns(self):
        self.assertEqual(warns(self.TEXT), ["ISO999-8.6-PAGEORDER"])
        self.assertEqual(warns(ind("\\item docks, 5", "\\subitem tolls, 40",
                                   "\\subitem moorings, 52",
                                   "\\subitem cranes, 88"), "ind"),
                         ["ISO999-8.6-PAGEORDER"])

    def test_declared_page_order_is_info(self):
        self.assertEqual(warns(self.TEXT, subheading_order="page"), [])
        self.assertIn("ISO999-8.6-SYSTEMATIC",
                      infos(self.TEXT, subheading_order="page"))

    def test_two_subheadings_are_plain_order(self):
        text = "docks, 5\n  tolls, 40\n  moorings, 52\n"
        self.assertEqual(warns(text), ["ISO999-8.6-ORDER"])

    def test_numeric_order_stays_info(self):
        roots = L.build_tree(L.read_text(
            "fairs, 1\n  1851, 2\n  1889 exhibition, 3\n  1900, 4\n"))
        self.assertEqual(L._systematic(roots[0].children), "numeric")


class TestQualifiedCrossRefs(unittest.TestCase):
    """Item 5: 7.5.3 qualified cross-references."""

    def test_split_qualifier(self):
        self.assertEqual(L.split_qualifier("styluses for entries up to 1900"),
                         ("styluses", "for entries up to 1900"))
        self.assertEqual(L.split_qualifier("nibs (before 1900)")[0], "nibs")
        self.assertEqual(L.split_qualifier("slates in later issues")[0],
                         "slates")
        self.assertEqual(L.split_qualifier("Mercury (planet)"),
                         ("Mercury (planet)", ""))

    def test_see_also_with_qualifier_resolves(self):
        text = ("nibs, 3, 8 see also styluses for entries up to 1900\n"
                "styluses, 5, 9 see also nibs (for entries from 1900 "
                "onwards)\n")
        self.assertEqual(warns(text), [])

    def test_qualified_heading_pair_no_chain_or_dangling(self):
        text = "pens see quills\nquills in later issues see pens\n"
        self.assertEqual(warns(text), [])

    def test_qualified_see_with_volumes(self):
        text = "slates in volumes 1–4 see tablets\ntablets, 6\n"
        self.assertEqual(warns(text), [])

    def test_ordinary_qualifier_still_checked(self):
        self.assertIn("ISO999-7.5.1-DANGLING",
                      warns("orbs see Mercury (planet)\n"))
        self.assertEqual(warns("Mercury (planet), 4, 7\n"
                               "orbs see Mercury (planet)\n"), [])

    def test_unqualified_chain_still_found(self):
        text = "inks see pens\npens see quills\nquills, 3, 8\n"
        self.assertIn("ISO999-7.5.1-CHAIN", warns(text))


class TestLocaleFold(unittest.TestCase):
    """Item 6: --locale-fold none|basic."""

    def test_duplicates(self):
        text = "Étude, 3\netude, 4\n"
        self.assertIn("ISO999-8.1-DUPLICATE", warns(text))
        self.assertNotIn("ISO999-8.1-DUPLICATE",
                         warns(text, locale_fold="none"))

    def test_order(self):
        text = "zebu, 1\nÖland, 2\n"
        self.assertIn("ISO999-8.2-ORDER", warns(text))
        self.assertEqual(warns(text, locale_fold="none"), [])


class TestFunctionWords(unittest.TestCase):
    """Item 7: articles are not ignorable function words."""

    def test_articles_removed(self):
        for art in ("a", "an", "the"):
            self.assertNotIn(art, L.FUNCTION_WORDS)
        self.assertIn("of", L.FUNCTION_WORDS)
        self.assertIn("and", L.FUNCTION_WORDS)

    def test_article_still_files(self):
        text = "rivers\n  the dams, 5\n  fishing, 9\n"
        self.assertIn("ISO999-8.6-ORDER", warns(text, func_words=True))


class TestLocatorSeverity(unittest.TestCase):
    """Item 8: ASCENDING is info, DUPLICATE stays warn."""

    def test_ascending_info_both_formats(self):
        self.assertEqual(warns("pewter, 40, 12\n"), [])
        self.assertIn("ISO999-7.4.3-ASCENDING", infos("pewter, 40, 12\n"))
        self.assertIn("ISO999-7.4.3-ASCENDING",
                      infos(ind("\\item pewter, 40, 12"), "ind"))

    def test_duplicate_warn(self):
        self.assertEqual(L.RULES["ISO999-7.4.3-DUPLICATE"][1], "warn")
        self.assertIn("ISO999-7.4.3-DUPLICATE", warns("pewter, 12, 12\n"))


class TestCLI(unittest.TestCase):
    def _run(self, content, *args, suffix=".txt"):
        with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False,
                                         encoding="utf-8") as fh:
            fh.write(content)
            path = fh.name
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = L.main([path, *args])
        finally:
            os.unlink(path)
        return code, out.getvalue(), err.getvalue()

    def test_exit_codes(self):
        self.assertEqual(self._run(CLEAN_TEXT)[0], 0)
        self.assertEqual(self._run(CLEAN_IND, suffix=".ind")[0], 0)
        self.assertEqual(self._run("walrus, 3\nbadger, 5\n")[0], 1)

    def test_parse_error_exit_2(self):
        code, _, err = self._run("no items here\n", suffix=".ind")
        self.assertEqual(code, 2)
        self.assertIn("parse error", err)

    def test_missing_file_exit_2(self):
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(L.main(["/nonexistent/idx.txt"]), 2)

    def test_usage_error_exit_2(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                L.main(["x.txt", "--filing", "sideways"])
        self.assertEqual(cm.exception.code, 2)

    def test_json_output(self):
        code, out, _ = self._run("walrus, 3\nbadger, 5\n", "--json")
        data = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual(data["summary"]["warn"], 1)
        f = [x for x in data["findings"] if x["rule"] == "ISO999-8.2-ORDER"]
        self.assertEqual(f[0]["clause"], "8.2")
        self.assertEqual(f[0]["line"], 2)

    def test_format_override(self):
        code, out, _ = self._run(CLEAN_IND, "--format", "ind", "--json")
        self.assertEqual(json.loads(out)["format"], "ind")
        self.assertEqual(code, 0)

    def test_every_finding_rule_is_catalogued(self):
        for rid, (clause, sev, _) in L.RULES.items():
            self.assertTrue(rid.startswith("ISO999-"))
            self.assertIn(sev, ("info", "warn"))

    def test_new_options_cli(self):
        text = "docks, 5\n  tolls, 40\n  moorings, 52\n  cranes, 88\n"
        self.assertEqual(self._run(text)[0], 1)
        self.assertEqual(self._run(text, "--subheading-order", "page")[0], 0)
        code, out, _ = self._run("zebu, 1\nÖland, 2\n", "--locale-fold",
                                 "none", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["locale_fold"], "none")
        self.assertEqual(self._run(TestInversion.BEFORE, "--inversion",
                                   "before")[0], 0)

    def test_roman_list_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                         encoding="utf-8") as fh:
            fh.write("# numerals\nXII\n")
            rl = fh.name
        try:
            text = "3 bears, 1\nXII tables, 3\n40 winks, 5\napples, 9\n"
            self.assertEqual(self._run(text)[0], 1)
            self.assertEqual(self._run(text, "--roman-list", rl)[0], 0)
            self.assertEqual(self._run(text, "--roman", "off")[0], 1)
        finally:
            os.unlink(rl)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(self._run(text, "--roman-list",
                                       "/nonexistent/r.txt")[0], 2)

    def test_list_rules_and_help(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(L.main(["--list-rules"]), 0)
        self.assertIn("ISO999-8.6-PAGEORDER", out.getvalue())
        self.assertRegex(out.getvalue(), r"ISO999-7\.4\.3-ASCENDING\s+\S+\s+info")
        helptext = L._build_argparser().format_help()
        for flag in ("--roman", "--roman-list", "--inversion",
                     "--subheading-order", "--locale-fold", "collator"):
            self.assertIn(flag, helptext)


def rules_of(text, fmt="text", **kw):
    return [f.rule for f in run(text, fmt, **kw)]


class TestPreamble(unittest.TestCase):
    """Audit item 1: a leading introductory note is not a run of headings."""

    NOTE = ("This index covers the chapters on rope making and sail lofts. "
            "Numbers in bold\n"
            "refer to drawings, and a letter n after a number marks a "
            "footnote.\n"
            "\n"
            "cordage, 3, 9\nhemp, 12\nsailcloth, 20\n")

    def test_note_detected_and_skipped(self):
        self.assertEqual(warns(self.NOTE), [])
        self.assertIn("ISO999-7.1.3-NOTE", infos(self.NOTE))
        roots = L.build_tree(L.read_text(self.NOTE))
        self.assertEqual([e.heading for e in roots],
                         ["cordage", "hemp", "sailcloth"])

    def test_no_auto_preamble(self):
        # the unskipped note lines misfile ('This index ...' before
        # 'refer to ...'); v2 attributes that pair to 8.1-CASE-ORDER,
        # since it is in order only under a case-sensitive sort
        self.assertTrue(any(r.endswith("ORDER") for r in
                            warns(self.NOTE, auto_preamble=False)))
        self.assertNotIn("ISO999-7.1.3-NOTE",
                         infos(self.NOTE, auto_preamble=False))

    def test_skip_until(self):
        f = run(self.NOTE, auto_preamble=False, skip_until=r"^cordage")
        self.assertEqual([x.rule for x in f if x.severity == "warn"], [])
        self.assertIn("ISO999-7.1.3-NOTE", [x.rule for x in f])
        with self.assertRaises(L.ParseError):
            run(self.NOTE, skip_until=r"^nothing-matches-this")

    def test_title_line_and_letter_header(self):
        text = ("# Index\n\nAbout this index\n\n"
                "Entries are filed word by word. Subheadings are listed "
                "alphabetically under each main heading.\n\n"
                "C\n\ncordage, 3\n\nH\n\nhemp, 12\n")
        self.assertEqual(warns(text), [])
        roots = L.build_tree(L.read_text(text))
        self.assertEqual([e.heading for e in roots], ["cordage", "hemp"])

    def test_long_see_entry_is_not_a_note(self):
        text = ("harbours see anchorages; berths; docks; moorings; piers; "
                "quays; wharves.\n\nanchorages, 3\n")
        self.assertNotIn("ISO999-7.1.3-NOTE", infos(text))
        self.assertIn("ISO999-8.2-ORDER", warns(text))
        note = ("For abbreviations see the list on page 4. Entries are "
                "filed word by word.\n\nanchorages, 3\nberths, 5\n")
        self.assertIn("ISO999-7.1.3-NOTE", infos(note))

    def test_plain_index_has_no_note(self):
        self.assertNotIn("ISO999-7.1.3-NOTE", infos(CLEAN_TEXT))
        self.assertNotIn("ISO999-7.1.3-NOTE",
                         infos("almonds 3\nbeets 7\ncress 9\n"))


class TestDigitAttribution(unittest.TestCase):
    """Audit item 2: digit-run misorder is 8.3 d, not 8.5."""

    def test_heading_digits(self):
        rules = warns("Route 66  4\nRoute 9  7\n")
        self.assertIn("ISO999-8.3-ORDER", rules)
        self.assertNotIn("ISO999-8.5-ORDER", rules)

    def test_subheading_digits(self):
        rules = warns("roads  1\n  Gate 12  4\n  Gate 3  7\n")
        self.assertIn("ISO999-8.3-ORDER", rules)
        self.assertNotIn("ISO999-8.6-ORDER", rules)

    def test_letters_still_8_5(self):
        self.assertIn("ISO999-8.5-ORDER", warns("tin mines, 3\ntin (x), 4\n"))


class TestSortKeyLeak(unittest.TestCase):
    """Audit item 3: cross-reference text leaked into the sort key."""

    def test_leak_detected(self):
        text = ("cotton gin, 4\ncotton mills, 8\ncotton see textiles\n"
                "textiles, 2, 5\n")
        self.assertEqual(warns(text), ["ISO999-8.7-SORTKEY"])
        self.assertEqual(warns(ind("\\item cotton gin, 4",
                                   "\\item cotton mills, 8",
                                   "\\item cotton, \\see{textiles}{1}",
                                   "\\item textiles, 2, 5"), "ind"),
                         ["ISO999-8.7-SORTKEY"])

    def test_plain_misorder_not_blamed_on_xref(self):
        text = "walrus see seals\nbadger, 5\nseals, 3, 4\n"
        rules = warns(text)
        self.assertIn("ISO999-8.2-ORDER", rules)
        self.assertNotIn("ISO999-8.7-SORTKEY", rules)


class TestTargetSeparator(unittest.TestCase):
    """Audit item 4: comma-separated targets."""

    def test_comma_targets(self):
        text = "berths, 2\ndocks, 3\nquays, 4 see also docks, berths\n"
        rules = warns(text)
        self.assertIn("ISO999-7.5-SEPARATOR", rules)
        self.assertIn("ISO999-7.5-TARGETORDER", rules)
        self.assertNotIn("ISO999-7.5.2-DANGLING", rules)
        rules = warns(ind("\\item berths, 2", "\\item docks, 3",
                          "\\item quays, 4, \\seealso{docks, berths}{1}"),
                      "ind")
        self.assertIn("ISO999-7.5-SEPARATOR", rules)

    def test_comma_targets_in_order(self):
        text = "berths, 2\ndocks, 3\nquays, 4 see also berths, docks\n"
        self.assertEqual(warns(text), ["ISO999-7.5-SEPARATOR"])

    def test_inverted_name_target_is_fine(self):
        text = "Aldridge, Petra, 3, 8\nwriters see Aldridge, Petra\n"
        self.assertEqual(warns(text), [])

    def test_partial_resolution_stays_dangling(self):
        text = "berths, 2\nquays, 4 see also berths, piers\n"
        rules = warns(text)
        self.assertIn("ISO999-7.5.2-DANGLING", rules)
        self.assertNotIn("ISO999-7.5-SEPARATOR", rules)


class TestCaseBlock(unittest.TestCase):
    """Audit item 5: two alphabets from a case-sensitive sort."""

    def test_case_restart(self):
        text = ("Anchors, 1\nBuoys, 2\nCompasses, 3\n"
                "awnings, 4\nbilges, 5\ncleats, 6\n")
        f = [x for x in run(text) if x.severity == "warn"]
        self.assertEqual([x.rule for x in f], ["ISO999-8.1-CASEBLOCK"])
        for letter in ("A", "B", "C"):
            self.assertIn(letter, f[0].message)

    def test_repeated_group_headers(self):
        text = ("A\nAnchors, 1\nB\nBuoys, 2\n"
                "A\nawnings, 4\nB\nbilges, 5\n")
        rules = warns(text)
        self.assertEqual(rules.count("ISO999-8.1-CASEBLOCK"), 1)
        text = "A\nanchors, 1\nB\nbuoys, 2\nB\nbunks, 3\n"
        f = [x for x in run(text) if x.rule == "ISO999-8.1-CASEBLOCK"]
        self.assertEqual(len(f), 1)
        self.assertIn("B", f[0].message)

    def test_mixed_case_index_is_fine(self):
        self.assertNotIn("ISO999-8.1-CASEBLOCK", rules_of(CLEAN_TEXT))


class TestSpaceSeparator(unittest.TestCase):
    """Audit item 6: single-space separator ambiguity (7.4.5)."""

    def test_heading_ending_in_digit_warns(self):
        text = "almonds 3\nPier 4 12\nquinces 9\n"
        self.assertEqual(warns(text), ["ISO999-7.4.5-SEPARATOR"])

    def test_unambiguous_space_style_info_once(self):
        text = "almonds 3\nbeets 7\ncress 9\n"
        self.assertEqual(warns(text), [])
        self.assertEqual(infos(text).count("ISO999-7.4.5-SEPARATOR"), 1)

    def test_comma_style_silent(self):
        self.assertNotIn("ISO999-7.4.5-SEPARATOR",
                         rules_of("almonds, 3\nbeets, 7\n"))


class TestPlacementBefore(unittest.TestCase):
    """Audit item 7: consistent see-also-before-locators is info."""

    def test_consistent_before_is_info(self):
        text = ("berths, 2\ndocks (see also berths) 3\n"
                "quays (see also docks) 4\n")
        self.assertEqual(warns(text), [])
        self.assertIn("ISO999-7.5.2.1-PLACEMENT", infos(text))

    def test_consistent_after_is_silent(self):
        text = "berths, 2 see also docks\ndocks, 3 see also berths\n"
        self.assertNotIn("ISO999-7.5.2.1-PLACEMENT", rules_of(text))


class TestNearDuplicates(unittest.TestCase):
    """Audit item 8: singular/plural and name-form variants (info)."""

    def test_plural_variants(self):
        for text in ("harbour, 3\nharbours, 9\n", "berry, 2\nberries, 5\n",
                     "fox, 1\nfoxes, 4\n", "tidal pool, 3\ntidal pools, 5\n"):
            with self.subTest(text=text):
                self.assertIn("ISO999-7.2.2.2-NUMBER", infos(text))
                self.assertNotIn("ISO999-7.2.2.2-NUMBER", warns(text))

    def test_plural_with_qualifier_ignored(self):
        self.assertNotIn("ISO999-7.2.2.2-NUMBER",
                         infos("glass, 1\nglasses (spectacles), 4\n"))
        self.assertNotIn("ISO999-7.2.2.2-NUMBER",
                         infos("almond, 1\nbeets, 4\n"))

    def test_name_variants(self):
        self.assertIn("ISO999-7.3.1.1-VARIANT",
                      infos("Okafor, N., 8\nOkafor, Ngozi, 3\n"))
        self.assertIn("ISO999-7.3.1.1-VARIANT",
                      infos("Lindqvist, M. E., 7\nLindqvist, Maja Eva, 2\n"))
        self.assertNotIn("ISO999-7.3.1.1-VARIANT",
                         infos("Okafor, Ngozi, 3\nOkafor, T., 8\n"))


class TestNewCLI(unittest.TestCase):
    def test_new_flags_and_rules(self):
        helptext = L._build_argparser().format_help()
        for flag in ("--skip-until", "--no-auto-preamble"):
            self.assertIn(flag, helptext)
        out = io.StringIO()
        with redirect_stdout(out):
            L.main(["--list-rules"])
        for rid in ("ISO999-7.1.3-NOTE", "ISO999-8.7-SORTKEY",
                    "ISO999-7.5-SEPARATOR", "ISO999-8.1-CASEBLOCK",
                    "ISO999-7.4.5-SEPARATOR", "ISO999-7.2.2.2-NUMBER",
                    "ISO999-7.3.1.1-VARIANT"):
            self.assertIn(rid, out.getvalue())

    def test_cli_preamble_flags(self):
        run_cli = TestCLI()._run
        self.assertEqual(run_cli(TestPreamble.NOTE)[0], 0)
        self.assertEqual(run_cli(TestPreamble.NOTE, "--no-auto-preamble")[0],
                         1)
        self.assertEqual(run_cli(TestPreamble.NOTE, "--no-auto-preamble",
                                 "--skip-until", "^cordage")[0], 0)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(run_cli(TestPreamble.NOTE, "--skip-until",
                                     "(")[0], 2)


# ---------------------------------------------------------------------------
# v2: gaps found by the Go / Rust / ServiceNow audits. Invented fixtures.
# ---------------------------------------------------------------------------
class TestLocatorModes(unittest.TestCase):
    """v2 item 1: --locators numeric|anchor|none|auto."""

    def test_anchor_text_tab_lines(self):
        text = "ferns\t#sec-ferns\nmosses\thttps://example.org/mosses\n"
        roots, f = L.lint_text(text, "text", L.Options(locators="anchor"))
        self.assertEqual([e.heading for e in roots], ["ferns", "mosses"])
        self.assertEqual([l.anchor for e in roots for l in e.locators],
                         ["#sec-ferns", "https://example.org/mosses"])
        self.assertEqual([x.rule for x in f if x.severity == "warn"], [])

    def test_anchor_locators_skip_numeric_checks(self):
        text = "heather, #zz, #aa\n"
        rules = rules_of(text, locators="anchor")
        self.assertNotIn("ISO999-7.4.3-ASCENDING", rules)
        self.assertEqual(warns(text, locators="anchor"), [])

    def test_none_keeps_trailing_tokens(self):
        text = "Route 66\nvitamin c\nzone 9 [area, sector, 4]\n"
        roots, _ = L.lint_text(text, "text", L.Options(locators="none"))
        self.assertEqual([e.heading for e in roots],
                         ["Route 66", "vitamin c", "zone 9"])
        self.assertTrue(all(not e.locators for e in roots))

    def test_none_see_also_is_not_norefs(self):
        text = "quartz see also silica\nsilica\n"
        self.assertNotIn("ISO999-7.5.2.1-NOREFS",
                         rules_of(text, locators="none"))

    def test_auto_falls_back_per_entry(self):
        text = "kelp, 12\nlichen\t#lichen\n"
        roots, _ = L.lint_text(text, "text", L.Options())
        self.assertEqual(roots[0].locators[0].start, 12)
        self.assertEqual(roots[1].locators[0].anchor, "#lichen")

    def test_html_anchor_whole_link_heading(self):
        html = ('<ul><li><a href="#alpha">Alpha</a></li>'
                '<li><a href="#beta">Beta</a></li></ul>'
                '<div id="alpha"></div><div id="beta"></div>')
        roots, f = L.lint_text(html, "html", L.Options(locators="anchor"))
        self.assertEqual([e.heading for e in roots], ["Alpha", "Beta"])
        self.assertEqual([e.locators[0].anchor for e in roots],
                         ["#alpha", "#beta"])
        self.assertNotIn("ISO999-7.4-ANCHOR", [x.rule for x in f])

    def test_html_anchor_trailing_link_locators(self):
        html = ('<ul><li>abacus, <a href="#p4">4</a>, <a href="#p9">9</a>'
                '</li></ul><p id="p4"></p><p id="p9"></p>')
        roots, _ = L.lint_text(html, "html", L.Options(locators="anchor"))
        self.assertEqual(roots[0].heading, "abacus")
        self.assertEqual([l.anchor for l in roots[0].locators],
                         ["#p4", "#p9"])

    def test_anchor_integrity(self):
        html = ('<ul><li><a href="#gone">Gamma</a></li>'
                '<li><a href="#here">Here</a></li></ul><b id="here"></b>')
        f = run(html, "html", locators="anchor")
        hits = [x for x in f if x.rule == "ISO999-7.4-ANCHOR"]
        self.assertEqual(len(hits), 1)
        self.assertIn("#gone", hits[0].message)
        self.assertEqual(hits[0].severity, "warn")

    def test_signature_commas_not_locators_in_anchor_mode(self):
        html = ('<ul><li><a href="#Mix">func Mix(a, b, c int) int</a>'
                '</li></ul><h4 id="Mix">x</h4>')
        roots, _ = L.lint_text(html, "html", L.Options(locators="anchor"))
        self.assertEqual(roots[0].heading, "func Mix(a, b, c int) int")
        self.assertEqual(len(roots[0].locators), 1)


# invented pkgsite-like index: a constructor list and a method list sit
# in sibling <li><ul> wrappers after the type they belong to
PKG_LIKE = ('<ul class="idx">'
            '<li><a href="#Anvil">type Anvil</a></li>'
            '<li><ul><li><a href="#NewAnvil">func NewAnvil() Anvil</a></li>'
            '</ul></li>'
            '<li><ul><li><a href="#Anvil.Bend">func (a Anvil) Bend()</a>'
            '</li><li><a href="#Anvil.Clang">func (a Anvil) Clang()</a>'
            '</li><li><a href="#Anvil.Dent">func (a Anvil) Dent(n, m '
            'int)</a></li></ul></li>'
            '<li><a href="#Bellows">type Bellows</a></li></ul>'
            + "".join(f'<h4 id="{i}"></h4>' for i in
                      ("Anvil", "NewAnvil", "Anvil.Bend", "Anvil.Clang",
                       "Anvil.Dent", "Bellows")))


class TestHTMLStructure(unittest.TestCase):
    """v2 item 2: nesting, sections, chrome, positions, --heading-regex."""

    def test_sibling_li_ul_nesting(self):
        roots = L.build_tree(L.read_html(PKG_LIKE, {}, locators="anchor"))
        self.assertEqual([e.heading for e in roots],
                         ["type Anvil", "type Bellows"])
        self.assertEqual(len(roots[0].children), 4)
        self.assertEqual(roots[0].children[3].heading,
                         "func (a Anvil) Dent(n, m int)")

    def test_sections_split_and_labelled(self):
        html = ('<h3 id="structs">Structs</h3><ul><li>Oar</li>'
                '<li>Rudder</li></ul>'
                '<h3 id="functions">Functions</h3><ul><li>cast</li>'
                '<li>bail</li><li>dredge</li></ul>')
        f = [x for x in run(html, "html") if x.severity == "warn"]
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].section, "Functions")
        self.assertTrue(f[0].message.startswith("[Functions]"))
        merged = warns(html, "html", sections="merge")
        self.assertGreater(len(merged), 1)

    def test_section_ids_without_headings(self):
        html = ('<section id="structs"><ul><li>Oar</li><li>Rudder</li>'
                '</ul></section><section id="functions"><ul><li>bail</li>'
                '<li>cast</li></ul></section>')
        self.assertEqual(warns(html, "html"), [])

    def test_letter_headers_do_not_split(self):
        html = ('<h2>A</h2><ul><li>apple</li><li>azalea</li></ul>'
                '<h2>B</h2><ul><li>aardvark</li></ul>')
        self.assertIn("ISO999-8.2-ORDER", warns(html, "html"))

    def test_nav_chrome_skipped(self):
        html = ('<nav><ul><li>Zeta</li><li>Alpha</li></ul></nav>'
                '<ul><li>alpha</li><li>beta</li></ul>'
                '<footer><ul><li>Terms</li><li>About</li></ul></footer>')
        roots, f = L.lint_text(html, "html", L.Options())
        self.assertEqual([e.heading for e in roots], ["alpha", "beta"])
        self.assertEqual([x.rule for x in f if x.severity == "warn"], [])

    def test_only_section(self):
        html = ('<h3>Overview</h3><ul><li>zinc</li><li>arc</li></ul>'
                '<h3>Index</h3><ul><li>arc</li><li>zinc</li></ul>')
        self.assertEqual(warns(html, "html", only_section="^Index$"), [])
        self.assertTrue(warns(html, "html"))
        with self.assertRaises(L.ParseError):
            run(html, "html", only_section="^Nothing$")

    def test_minified_positions(self):
        html = "<ul><li>walrus</li><li>badger</li><li>otter</li></ul>"
        f = [x for x in run(html, "html") if x.rule == "ISO999-8.2-ORDER"]
        self.assertEqual(len(f), 1)
        self.assertRegex(str(f[0].line), r"^1:\d+$")
        self.assertEqual(f[0].as_dict()["col"], f[0].line.col)
        self.assertIn("(line 1:", f[0].message)

    def test_heading_regex_files_on_identifier(self):
        html = ('<ul><li><a href="#Anvil">type Anvil</a></li>'
                '<li><a href="#Bellows">func Bellows(x, y int)</a></li>'
                '</ul><i id="Anvil"></i><i id="Bellows"></i>')
        self.assertTrue(warns(html, "html", locators="anchor"))
        rx = r"^(?:func\s+(?:\([^)]*\)\s*)?|type\s+)?(\w+)"
        self.assertEqual(warns(html, "html", locators="anchor",
                               heading_regex=rx), [])


class TestIdentifierFiling(unittest.TestCase):
    """v2 item 3: --filing identifier and --case-significant."""

    def test_segmentation(self):
        seg = L.segment_identifier
        self.assertEqual(seg("HTTPServer"), "HTTP Server")
        self.assertEqual(seg("parseHTTP2Frame"), "parse HTTP 2 Frame")
        self.assertEqual(seg("io::read_to_end"), "io read to end")
        self.assertEqual(seg("Len16"), "Len 16")
        self.assertEqual(seg("a.b-c"), "a b c")

    def test_digit_runs_by_value(self):
        self.assertEqual(warns("Width8\nWidth16\nWidth64\n",
                               filing="identifier", locators="none"), [])
        self.assertIn("ISO999-8.3-ORDER",
                      warns("Width16\nWidth8\n", filing="identifier",
                            locators="none"))

    def test_underscore_is_a_word_break(self):
        text = "foobar\nfoo_bar\n"
        # word mode: '_' is null, so the two file identically (DUPLICATE)
        self.assertNotIn("ISO999-8.2-ORDER", warns(text, locators="none"))
        self.assertTrue(warns(text, filing="identifier", locators="none"))

    def test_camel_humps_are_word_breaks(self):
        # 'Tide Pool' files before 'Tidewater' word-by-word
        self.assertEqual(warns("TidePool\nTidewater\n", filing="identifier",
                               locators="none"), [])
        self.assertTrue(warns("Tidewater\nTidePool\n", filing="identifier",
                              locators="none"))

    def test_raw_tie_break_makes_order_total(self):
        opts = L.Options(filing="identifier")
        a, b = L.okey("APPLE", opts), L.okey("Apple", opts)
        self.assertEqual(a[:2], b[:2])
        self.assertLess(a, b)

    def test_case_significant_homograph(self):
        text = "Widget\nWIDGET\nWid_get\n"
        f = run(text, filing="identifier", locators="none")
        rules = [x.rule for x in f]
        self.assertNotIn("ISO999-8.1-DUPLICATE", rules)
        self.assertEqual(rules.count("ISO999-3.10-HOMOGRAPH"), 1)
        self.assertIn("ISO999-8.1-DUPLICATE",
                      warns("Widget\nWidget\n", filing="identifier",
                            locators="none"))

    def test_case_significant_flag_in_word_mode(self):
        text = "Lantern, 3\nlantern, 7\n"
        self.assertIn("ISO999-8.1-DUPLICATE", warns(text))
        self.assertEqual(warns(text, case_significant=True), [])
        self.assertIn("ISO999-3.10-HOMOGRAPH",
                      infos(text, case_significant=True))
        self.assertIn("ISO999-8.1-DUPLICATE",
                      warns("Widget\nwidget\n", filing="identifier",
                            locators="none", case_significant=False))


class TestAttributionV2(unittest.TestCase):
    """v2 item 4: CASE-ORDER, genuine 8.5 structure, qualifier suffixes."""

    def test_case_order(self):
        rules = warns("Yarrow, 3\nbasil, 5\n")
        self.assertEqual(rules, ["ISO999-8.1-CASE-ORDER"])

    def test_case_order_in_identifier_mode(self):
        rules = warns("HTTP3Knob\nHatch\n", filing="identifier",
                      locators="none")
        self.assertEqual(rules, ["ISO999-8.1-CASE-ORDER"])

    def test_accents_are_not_case(self):
        self.assertEqual(warns("zebu, 1\nÖland, 2\n"), ["ISO999-8.2-ORDER"])

    def test_digits_still_8_3(self):
        self.assertEqual(warns("Gate 12  1\nGate 3  2\n"),
                         ["ISO999-8.3-ORDER"])

    def test_8_5_needs_qualifier_structure(self):
        self.assertEqual(warns("kelp forests, 3\nkelp beds, 5\n"),
                         ["ISO999-8.2-ORDER"])
        self.assertEqual(warns("kelp beds, 3\nkelp, 5\n"),
                         ["ISO999-8.5-ORDER"])
        self.assertEqual(warns("sea wall defences, 3\nsea wall, 5\n"),
                         ["ISO999-8.5-ORDER"])

    def test_qualifier_suffix(self):
        text = "quilt-binding-guide\nquilt-guide\n"
        self.assertEqual(warns(text, locators="none"), [])
        self.assertEqual(warns(text, locators="none",
                               qualifier_suffixes=("-guide", "-api")),
                         ["ISO999-8.5-ORDER"])
        ok = "quilt-api\nquilt-guide\nquilt-binding-guide\n"
        self.assertEqual(warns(ok, locators="none",
                               qualifier_suffixes=("-guide", "-api")), [])

    def test_heading_regex_leading_qualifier(self):
        rx = r"^(?:\[\w+\]\s*)?(.+)$"
        text = "[beta] anchors\n[alpha] buoys\n"
        self.assertTrue(warns(text, locators="none"))
        self.assertEqual(warns(text, locators="none", heading_regex=rx), [])


class TestDisplaced(unittest.TestCase):
    """v2 item 5: DISPLACED summary and block collapsing."""

    def test_summary_counts_lis(self):
        text = "alder\nbirch\noak\npine\nspruce\ncedar\nelm\nfir\n"
        f = run(text, locators="none")
        d = [x for x in f if x.rule == "ISO999-8-DISPLACED"]
        self.assertEqual(len(d), 1)
        self.assertEqual(d[0].severity, "info")
        self.assertIn("3 of 8", d[0].message)
        for name in ("oak", "pine", "spruce"):
            self.assertIn(f'"{name}"', d[0].message)
        order = [x for x in f if x.rule == "ISO999-8.2-ORDER"]
        self.assertEqual(len(order), 1)
        self.assertIn("block of 3", order[0].message)

    def test_block_collapsed(self):
        text = "alder\nbirch\nyew\noak\ncedar\ndogwood\n"
        order = [x for x in run(text, locators="none")
                 if x.rule == "ISO999-8.2-ORDER"]
        self.assertEqual(len(order), 1)
        self.assertIn("block of 2", order[0].message)

    def test_no_summary_when_in_order(self):
        self.assertNotIn("ISO999-8-DISPLACED", rules_of(CLEAN_TEXT))


class TestRuns(unittest.TestCase):
    """v2 item 6: 8.6-RUNS instead of PAGEORDER for restarted alphabets."""

    def test_two_runs(self):
        text = ("kettle, 1\n  boil, 5\n  pour, 9\n  steep, 12\n"
                "  descale, 20\n  fill, 22\n")
        self.assertEqual(warns(text), ["ISO999-8.6-RUNS"])
        f = [x for x in run(text) if x.rule == "ISO999-8.6-RUNS"][0]
        self.assertIn("2 alphabetical runs", f.message)
        self.assertIn('"descale"', f.message)

    def test_lone_constructor_run(self):
        # NewAnvil | Bend Clang Dent: a lone constructor run + method run
        self.assertEqual(warns(PKG_LIKE, "html", locators="anchor",
                               heading_regex=r"(\w+)(?:\(|$)"),
                         ["ISO999-8.6-RUNS"])

    def test_disorder_is_not_runs(self):
        text = "canal, 1\n  surveying, 5\n  opening, 9\n  decline, 12\n"
        self.assertEqual(warns(text), ["ISO999-8.6-PAGEORDER"])

    def test_case_pairs_inside_runs_still_reported(self):
        # run 1 'grind Zone sift' holds a case-sorted pair; run 2 restarts
        text = ("mill\n  grind\n  Zone\n  sift\n  axle\n  bolt\n"
                "  wheel\n")
        rules = warns(text, locators="none")
        self.assertEqual(sorted(rules), ["ISO999-8.1-CASE-ORDER",
                                         "ISO999-8.6-RUNS"])


class TestCompareLocales(unittest.TestCase):
    """v2 item 7: --compare-locales (8.1-LOCALE)."""

    HEADS = "cedar\nchalk\ndune\nhill\niron\n"

    def _seq(self):
        roots, _ = L.lint_text(self.HEADS, "text",
                               L.Options(locators="none"))
        return [(None, roots)]

    def test_moved_entries_listed(self):
        coll = {"plain": lambda s: s,
                "digraph": lambda s: s.replace("ch", "h￿")}
        opts = L.Options(compare_locales=("plain", "digraph", "zz_NOPE"))
        f = L.check_locales(self._seq(), opts, collators=coll)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, "info")
        self.assertIn('"chalk" (2->4)', f[0].message)
        self.assertIn("zz_NOPE", f[0].message)
        self.assertNotIn('"dune"', f[0].message)

    def test_needs_two_locales(self):
        opts = L.Options(compare_locales=("plain", "zz_NOPE"))
        f = L.check_locales(self._seq(), opts,
                            collators={"plain": lambda s: s})
        self.assertIn("needs two available locales", f[0].message)

    def test_real_setlocale_path(self):
        f = run(self.HEADS, locators="none", compare_locales=("C", "POSIX"))
        loc = [x for x in f if x.rule == "ISO999-8.1-LOCALE"]
        self.assertEqual(len(loc), 1)
        self.assertIn("identically", loc[0].message)


class TestCLIV2(unittest.TestCase):
    def _cli(self, text, *args, suffix=".txt"):
        with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False,
                                         encoding="utf-8") as fh:
            fh.write(text)
            path = fh.name
        try:
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = L.main([path, *args])
            return code, out.getvalue(), err.getvalue()
        finally:
            os.unlink(path)

    def test_help_and_rules(self):
        helptext = L._build_argparser().format_help()
        for flag in ("--locators", "--sections", "--only-section",
                     "--heading-regex", "--qualifier-suffix",
                     "--case-significant", "--compare-locales",
                     "identifier"):
            self.assertIn(flag, helptext)
        out = io.StringIO()
        with redirect_stdout(out):
            L.main(["--list-rules"])
        for rid in ("ISO999-8.1-CASE-ORDER", "ISO999-3.10-HOMOGRAPH",
                    "ISO999-8-DISPLACED", "ISO999-8.6-RUNS",
                    "ISO999-7.4-ANCHOR", "ISO999-8.1-LOCALE"):
            self.assertIn(rid, out.getvalue())

    def test_qualifier_suffix_cli(self):
        code, out, _ = self._cli("quilt-binding-guide\nquilt-guide\n",
                                 "--locators", "none",
                                 "--qualifier-suffix=-guide,-api")
        self.assertEqual(code, 1)
        self.assertIn("ISO999-8.5-ORDER", out)

    def test_bad_heading_regex(self):
        code, _, err = self._cli("a\nb\n", "--heading-regex", r"\w+")
        self.assertEqual(code, 2)
        self.assertIn("capturing group", err)

    def test_json_col_and_section(self):
        html = ('<h3 id="functions">Functions</h3>'
                '<ul><li>cast</li><li>bail</li></ul>')
        code, out, _ = self._cli(html, "--json", suffix=".html")
        data = json.loads(out)
        f = [x for x in data["findings"] if x["rule"].endswith("ORDER")]
        self.assertEqual(f[0]["section"], "Functions")
        self.assertIn("col", f[0])



# ---------------------------------------------------------------------------
# v0.3 work order: parsing fixes (T1), layouts (T3), root causes (T4)
# ---------------------------------------------------------------------------
def tree(text, fmt="text", **kw):
    roots, _ = L.lint_text(text, fmt, L.Options(**kw))
    return roots


def flat(roots):
    return [(e.level, e.heading, [l.raw for l in e.locators])
            for e in L.walk(roots)]


class TestTrailingFullStop(unittest.TestCase):
    """T1-1: a full stop closing an entry is not part of its last locator."""

    def test_locators_kept(self):
        text = "kelp, 3, 3.\nlime, 9, 4.\n"
        self.assertIn("ISO999-7.4.3-DUPLICATE", warns(text))
        self.assertIn("ISO999-7.4.3-ASCENDING", infos(text))
        self.assertEqual([h for _, h, _ in flat(tree(text))],
                         ["kelp", "lime"])

    def test_number_leaves_heading(self):
        roots = tree("Kelp, 367.\nLime, 12.\n")
        self.assertEqual(flat(roots), [(0, "Kelp", ["367"]),
                                       (0, "Lime", ["12"])])
        self.assertNotIn("ISO999-8.3-ORDER", warns("Kelp, 367.\nLime, 12.\n"))

    def test_abbreviation_keeps_its_stop(self):
        roots = tree("Lyell, Sir C., 5.\nquartz, etc.\n")
        self.assertEqual(roots[0].heading, "Lyell, Sir C.")
        self.assertEqual(roots[1].heading, "quartz, etc.")


class TestSymbolHeadings(unittest.TestCase):
    """T1-2: headings made only of symbols file by code point."""

    HTML = ("<ul><li>!=, 3</li><li>%=, 4</li><li>&amp;=, 5</li>"
            "<li>*, 6</li><li>**, 7</li></ul>")

    def test_no_collisions(self):
        rules = rules_of(self.HTML, "html")
        for r in ("ISO999-8.1-DUPLICATE", "ISO999-3.10-HOMOGRAPH",
                  "ISO999-8.2-ORDER"):
            self.assertNotIn(r, rules)
        self.assertNotIn("ISO999-3.10-HOMOGRAPH",
                         rules_of(self.HTML, "html", case_significant=True))

    def test_code_point_order_checked(self):
        html = "<ul><li>**, 7</li><li>*, 6</li></ul>"
        self.assertIn("ISO999-8.2-ORDER", warns(html, "html"))

    def test_keys_distinct(self):
        self.assertNotEqual(L.sort_key("*"), L.sort_key("**"))
        self.assertNotEqual(L.sort_key("!="), L.sort_key("%="))
        self.assertEqual(L.sort_key("*")[0], -1)

    def test_ignorable_marks_still_null(self):
        self.assertEqual(L.sort_key("'Tis"), L.sort_key("Tis"))
        self.assertEqual(L.sort_key("“Quoted”"),
                         L.sort_key("Quoted"))

    def test_symbol_with_gloss(self):
        # the symbol is the subject: '! (bang)' is not filed under B
        a, b = L.sort_key("! (bang)"), L.sort_key("apple")
        self.assertLess(a, b)
        self.assertLess(L.sort_key("! (bang)"), L.sort_key("!="))


class TestLinkTextHeadings(unittest.TestCase):
    """T1-3: a heading that is itself the link text keeps its digits."""

    HTML = ('<ul><li><a href="#r9">Route 9</a></li>'
            '<li><a href="#r66">Route 66</a></li>'
            '<li><a href="#rt">route table</a></li></ul>')

    def test_headings_and_anchors(self):
        roots = tree(self.HTML, "html")
        self.assertEqual([e.heading for e in roots],
                         ["Route 9", "Route 66", "route table"])
        self.assertEqual(roots[1].locators[0].anchor, "#r66")
        self.assertNotIn("ISO999-8.1-DUPLICATE", rules_of(self.HTML, "html"))

    def test_trailing_link_locators(self):
        html = ('<ul><li>kelp<ul><li><a href="#a">in soap</a>, '
                '<a href="#b">[1]</a></li></ul></li></ul>')
        sub = tree(html, "html")[0].children[0]
        self.assertEqual(sub.heading, "in soap")
        self.assertEqual([l.anchor for l in sub.locators], ["#a", "#b"])

    def test_numeric_links_still_numeric(self):
        html = '<ul><li>kelp, <a href="#p4">4</a>, <a href="#p9">9</a></li></ul>'
        e = tree(html, "html")[0]
        self.assertEqual((e.heading, [l.start for l in e.locators]),
                         ("kelp", [4, 9]))


class TestSiteChrome(unittest.TestCase):
    """T1-4: navigation, search and sidebars are not index entries."""

    def test_roles_and_classes_skipped(self):
        html = ('<div class="related" role="navigation"><ul>'
                '<li><a href="#">index</a></li><li>modules |</li></ul></div>'
                '<div class="sphinxsidebar"><ul><li>zeta</li><li>Index</li>'
                '</ul></div><search role="search"><ul><li>quick</li></ul>'
                '</search><div role="search"><ul><li>omega</li></ul></div>'
                '<ul><li>abacus, 4</li><li>kelp, 9</li></ul>')
        self.assertEqual([e.heading for e in tree(html, "html")],
                         ["abacus", "kelp"])
        self.assertEqual(warns(html, "html"), [])

    def test_underscore_group_does_not_bleed(self):
        html = ('<h1>Index</h1><h2 id="Symbols">Symbols</h2>'
                '<ul><li>!=</li></ul><h2 id="_">_</h2>'
                '<ul><li>__init__</li><li>__len__</li></ul>'
                '<h2 id="A">A</h2><ul><li>banana</li><li>apple</li></ul>')
        f = [x for x in run(html, "html", locators="none")
             if x.rule == "ISO999-8.2-ORDER"]
        self.assertEqual(len(f), 1)
        self.assertNotEqual(f[0].section, "_")
        self.assertNotIn("[_]", f[0].message)

    def test_index_caption_not_an_entry(self):
        self.assertEqual([e.heading for e in tree("INDEX.\n\nabacus, 4\n")],
                         ["abacus"])
        self.assertEqual([e.heading for e in tree("Index\n\nabacus, 4\n")],
                         ["abacus"])

    def test_deprecated_badge_stripped(self):
        html = ('<ul><li><a href="#P">type Package</a><span class="'
                'Documentation-indexDeprecated Documentation-deprecatedTag">'
                'deprecated</span></li><li><a href="#Q">type Queue</a></li>'
                '</ul>')
        self.assertEqual([e.heading for e in tree(html, "html",
                                                  locators="anchor")],
                         ["type Package", "type Queue"])


class TestParseHealth(unittest.TestCase):
    """T4-2: parse-health info and --dump-tree."""

    def test_health_reported_for_misparse(self):
        text = "".join(f"heading{c} number {c}{c}.x\n" for c in "abcdefghijkl")
        f = [x for x in run(text) if x.rule == "ISO999-PARSE-HEALTH"]
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, "info")
        self.assertIn("no locators", f[0].message)

    def test_clean_index_has_no_health_note(self):
        self.assertNotIn("ISO999-PARSE-HEALTH", rules_of(CLEAN_TEXT))

    def test_dump_tree(self):
        code, out, _ = TestCLIV2._cli(self, "kelp, 4\n  zinc in, 8\nlime, 5\n",
                                      "--dump-tree")
        self.assertEqual(code, 0)
        data = json.loads(out)
        seq = data["sections"][0]["entries"]
        self.assertEqual(seq[0]["heading"], "kelp")
        self.assertEqual(seq[0]["locators"], ["4"])
        self.assertEqual(seq[0]["children"][0]["heading"], "zinc in")
        self.assertEqual(seq[1]["heading"], "lime")

    _cli = TestCLIV2._cli


class TestDittoDashes(unittest.TestCase):
    """T3-1: repeated-heading dashes and flush-left turnover lines."""

    def test_single_dash(self):
        roots = tree("Affinities, 301.\n—, of organic beings, 378.\n"
                     "Agassiz, 112.\n")
        self.assertEqual(flat(roots), [(0, "Affinities", ["301"]),
                                       (1, "of organic beings", ["378"]),
                                       (0, "Agassiz", ["112"])])

    def test_depth_by_dash_count(self):
        text = ("kelp, 4\n——, drying, 12\n"
                "————, in sheds, 13\n"
                "——, harvest, 30\nlime, 5\n")
        self.assertEqual([(lv, h) for lv, h, _ in flat(tree(text))],
                         [(0, "kelp"), (1, "drying"), (2, "in sheds"),
                          (1, "harvest"), (0, "lime")])

    def test_flush_left_turnover(self):
        text = ("Agassiz, 112.\n"
                "—, on parallelism of development and geological\n"
                "succession, 396.\n—, on prophetic forms, 301.\n"
                "Algae, 338.\n")
        self.assertEqual(flat(tree(text)), [
            (0, "Agassiz", ["112"]),
            (1, "on parallelism of development and geological succession",
             ["396"]),
            (1, "on prophetic forms", ["301"]),
            (0, "Algae", ["338"])])

    def test_bullet_dash_unchanged(self):
        text = "abacus, 4\n— beads, 5\n— — wire, 6\nkelp, 9\n"
        self.assertEqual([(lv, h) for lv, h, _ in flat(tree(text))],
                         [(0, "abacus"), (1, "beads"), (2, "wire"),
                          (0, "kelp")])


class TestRunOnAndTurnover(unittest.TestCase):
    """T3-3: run-on subheadings and deeper-indented turnover lines."""

    def test_run_on(self):
        text = "kelp, 4; drying, 12-14; harvesting, 30; zinc in, 8\nlime, 5\n"
        self.assertEqual(flat(tree(text)), [
            (0, "kelp", ["4"]), (1, "drying", ["12-14"]),
            (1, "harvesting", ["30"]), (1, "zinc in", ["8"]),
            (0, "lime", ["5"])])

    def test_run_on_order_checked(self):
        self.assertIn("ISO999-8.6-ORDER",
                      warns("kelp, 4; zinc in, 8; drying, 12\nlime, 5\n"))

    def test_run_on_see_also(self):
        roots = tree("kelp, 4; drying, 12; see also algae\nalgae, 3\n",
                     )
        kelp = [e for e in roots if e.heading == "kelp"][0]
        self.assertEqual([r.target for r in kelp.see_also], ["algae"])
        self.assertEqual([c.heading for c in kelp.children], ["drying"])

    def test_semicolon_see_targets_not_run_on(self):
        roots = tree("harbours see ports; quays\nports, 3\nquays, 4\n")
        self.assertEqual([r.target for r in roots[0].see], ["ports", "quays"])

    def test_deeper_turnover(self):
        text = ("kelp, 4\n"
                "    drying of the fronds on stony beaches in the western\n"
                "      isles, 12-14\n"
                "    harvesting, 30\n"
                "lime, 5\n")
        self.assertEqual(flat(tree(text)), [
            (0, "kelp", ["4"]),
            (1, "drying of the fronds on stony beaches in the western isles",
             ["12-14"]),
            (1, "harvesting", ["30"]), (0, "lime", ["5"])])

    def test_real_subsubheading_kept(self):
        text = "kelp\n  drying\n    in sheds, 5\n  harvest, 3\nlime, 2\n"
        self.assertEqual([(lv, h) for lv, h, _ in flat(tree(text))],
                         [(0, "kelp"), (1, "drying"), (2, "in sheds"),
                          (1, "harvest"), (0, "lime")])


class TestParagraphHTML(unittest.TestCase):
    """T3-2: <p>/<br> HTML indexes."""

    def test_gutenberg_br(self):
        html = ('<h2>CHAPTER I.</h2><p>Some prose about kelp, 1859.</p>'
                '<h2><a id="p443"></a>INDEX.</h2><p class="noindent"><br>\n'
                'Aberrant groups, <a href="#p379">379</a>.<br>\n<br>\n'
                'Abyssinia, plants of, <a href="#p340">340</a>.<br>\n'
                '—, rivers of, <a href="#p341">341</a>.<br>\n<br>\n'
                'Acclimatisation, <a href="#p112">112</a>.<br>\n</p>')
        self.assertEqual(flat(tree(html, "html")), [
            (0, "Aberrant groups", ["379"]),
            (0, "Abyssinia, plants of", ["340"]),
            (1, "rivers of", ["341"]),
            (0, "Acclimatisation", ["112"])])

    def test_word_msoindex(self):
        html = ('<p class=MsoIndexHeading>K</p>'
                '<p class=MsoIndex1>kelp, 4</p><p class=MsoIndex2>zinc in, 8</p>'
                '<p class=MsoIndex2>drying, 12</p><p class=MsoIndex1>lime, 5</p>'
                '<p class=MsoNormal>Not part of the index.</p>')
        roots = tree(html, "html")
        self.assertEqual([(lv, h) for lv, h, _ in flat(roots)],
                         [(0, "kelp"), (1, "zinc in"), (1, "drying"),
                          (0, "lime")])
        self.assertIn("ISO999-8.6-ORDER", warns(html, "html"))

    def test_libreoffice_margins(self):
        html = ('<p style="margin-left: 0cm">kelp, 4</p>'
                '<p style="margin-left: 0.5cm">drying, 12</p>'
                '<p style="margin-left: 1cm">in sheds, 13</p>'
                '<p style="margin-left: 0.5cm">zinc in, 8</p>'
                '<p style="margin-left: 0cm">lime, 5</p>')
        self.assertEqual([(lv, h) for lv, h, _ in flat(tree(html, "html"))],
                         [(0, "kelp"), (1, "drying"), (2, "in sheds"),
                          (1, "zinc in"), (0, "lime")])


class TestTableHTML(unittest.TestCase):
    """T3-9: basic <table> index: first cell is the heading, links locate."""

    def test_table_rows(self):
        html = ('<table><tr><th>Path</th><th>Synopsis</th></tr>'
                '<tr><td><a href="/beta">beta</a></td><td>Beta tools</td></tr>'
                '<tr><td><div class="sub"><a href="/beta/x">x</a></div>'
                '<div class="mobileSynopsis">X things</div></td><td></td></tr>'
                '<tr><td><a href="/alpha">alpha</a></td><td>Alpha</td></tr>'
                '</table>')
        roots = tree(html, "html", locators="anchor")
        self.assertEqual([(lv, h) for lv, h, _ in flat(roots)],
                         [(0, "beta"), (1, "x"), (0, "alpha")])
        self.assertEqual(roots[0].locators[0].anchor, "/beta")
        self.assertIn("ISO999-8.2-ORDER", warns(html, "html",
                                                locators="anchor"))


class TestLeadingArticles(unittest.TestCase):
    """T3-5: initial articles kept in some headings, inverted in others."""

    def test_mixed_forms_warn(self):
        self.assertIn("ISO999-7.3.4.2-ARTICLE",
                      warns("The Tempest, 7\nWinter's Tale, The, 9\n"))

    def test_one_form_is_fine(self):
        self.assertNotIn("ISO999-7.3.4.2-ARTICLE",
                         rules_of("Tempest, The, 7\nWinter's Tale, The, 9\n"))
        self.assertNotIn("ISO999-7.3.4.2-ARTICLE",
                         rules_of("The Tempest, 7\nThe Winter's Tale, 9\n"))

    def test_lower_case_article_ignored(self):
        self.assertNotIn("ISO999-7.3.4.2-ARTICLE",
                         rules_of("a priori, 3\nTale, A, 9\n"))


class TestAbbreviations(unittest.TestCase):
    """T3-6: abbreviations file as written (7.3.6)."""

    def test_mc_as_mac(self):
        rules = warns("Macaw, 2\nMcDonnell, 4\nMadeira, 3\n")
        self.assertIn("ISO999-7.3.6-ABBREV", rules)
        self.assertNotIn("ISO999-8.2-ORDER", rules)

    def test_st_run_together(self):
        rules = warns("Sterility, 3\nSt. Helena, 4\nStone, 5\n")
        self.assertIn("ISO999-7.3.6-ABBREV", rules)
        self.assertNotIn("ISO999-8.2-ORDER", rules)

    def test_variant_pairs(self):
        text = "Saint Helena, 5\nSt. Helena, 4\n"
        self.assertIn("ISO999-7.3.6-VARIANT", infos(text))
        self.assertIn("ISO999-7.3.6-VARIANT",
                      infos("Smith & Sons, 3\nSmith and Sons, 4\n"))
        self.assertIn("ISO999-7.3.6-VARIANT",
                      infos("MacDonald, Flora, 3\nMcDonald, Flora, 4\n"))

    def test_no_variant_for_distinct_names(self):
        self.assertNotIn("ISO999-7.3.6-VARIANT",
                         rules_of("MacDonald, Flora, 3\nMcDonnell, Ian, 4\n"))


class TestHonorifics(unittest.TestCase):
    """T3-7: honorifics in inverted names."""

    TEXT = "Forbes, Mr. D., 3\nForbes, E., 4\nForbes, Prof. J., 5\n"

    def test_default_is_info(self):
        self.assertNotIn("ISO999-8.5-ORDER", warns(self.TEXT))
        self.assertIn("ISO999-7.3.1-HONORIFIC", infos(self.TEXT))

    def test_flag_suppresses(self):
        rules = rules_of(self.TEXT, ignore_honorifics=True)
        self.assertNotIn("ISO999-7.3.1-HONORIFIC", rules)
        self.assertNotIn("ISO999-8.5-ORDER", rules)

    def test_flag_cli(self):
        code, _, _ = TestCLIV2._cli(self, self.TEXT, "--ignore-honorifics")
        self.assertEqual(code, 0)

    def test_real_misorder_still_warns(self):
        self.assertIn("ISO999-8.5-ORDER",
                      warns("Forbes, Mr. J., 3\nForbes, E., 4\n"))

    _cli = TestCLIV2._cli


class TestRootCause(unittest.TestCase):
    """T4-1: order findings explained by one other sort key."""

    TEXT = "".join(f"{c}.b, 1\n{c}_a, 2\n" for c in "abcdef")

    def test_summary_replaces_pairs(self):
        fs = run(self.TEXT)
        rc = [f for f in fs if f.rule == "ISO999-8-ROOTCAUSE"]
        self.assertEqual(len(rc), 1)
        self.assertEqual(rc[0].severity, "warn")
        self.assertIn("code-point", rc[0].message)
        self.assertIn("6", rc[0].message)
        self.assertEqual(warns(self.TEXT), ["ISO999-8-ROOTCAUSE"])

    def test_verbose_pairs_keeps_them_as_info(self):
        fs = run(self.TEXT, verbose_pairs=True)
        pairs = [f for f in fs if f.rule == "ISO999-8.2-ORDER"]
        self.assertEqual(len(pairs), 6)
        self.assertTrue(all(f.severity == "info" for f in pairs))

    def test_few_pairs_not_collapsed(self):
        self.assertNotIn("ISO999-8-ROOTCAUSE",
                         rules_of("a.b, 1\na_a, 2\nzebra, 3\n"))

    def test_unexplained_pairs_stay(self):
        text = self.TEXT + "zebra, 9\nyak, 10\n"
        w = warns(text)
        self.assertIn("ISO999-8-ROOTCAUSE", w)
        self.assertIn("ISO999-8.2-ORDER", w)

    def test_subheading_order_collapsed_per_group(self):
        text = "kelp, 1\n  zinc, 5\n  drying, 3\n  yam, 7\n  barley, 9\nlime, 2\n"
        f = [x for x in run(text) if x.rule == "ISO999-8.6-ORDER"]
        self.assertEqual(len(f), 1)
        self.assertIn("2 ", f[0].message)


class TestHyperrefInd(unittest.TestCase):
    """hyperref wraps see/seealso and formats in \\hyperindexformat."""

    def test_hyperindexformat(self):
        text = ind("  \\item ash, \\hyperindexformat{\\seealso{kelp ash}}{5}, "
                   "\\hyperpage{21}",
                   "  \\item kelp, \\hyperpage{3}, \\hyperindexformat{\\textbf}{9}",
                   "  \\item kelp ash, \\hyperpage{26}",
                   "  \\item seaweed, \\hyperindexformat{\\see{kelp}}{3}",
                   "  \\item wrack, \\hyperindexformat{\\see{seaweed}}{15}")
        roots = tree(text, "ind")
        ash, kelp, _, sea, _ = roots
        self.assertEqual(ash.heading, "ash")
        self.assertEqual([r.target for r in ash.see_also], ["kelp ash"])
        self.assertEqual([l.start for l in ash.locators], [21])
        self.assertEqual([l.start for l in kelp.locators], [3, 9])
        self.assertTrue(kelp.locators[1].emphasis)
        self.assertEqual([r.target for r in sea.see], ["kelp"])
        self.assertIn("ISO999-7.5.1-CHAIN", warns(text, "ind"))


class TestSummariesV3(unittest.TestCase):
    """Repeated per-entry findings and group findings with one cause."""

    def test_maxloc_collapsed(self):
        text = "".join(f"kelp{c}, 1, 2, 3, 4, 5, 6, 7\n"
                       for c in "abcdefghijkl")
        f = [x for x in run(text) if x.rule == "ISO999-7.2.3.5-MAXLOC"]
        self.assertEqual(len(f), 1)
        self.assertIn("12 entries", f[0].message)
        self.assertEqual(len([x for x in run(text, verbose_pairs=True)
                              if x.rule == "ISO999-7.2.3.5-MAXLOC"]), 12)

    def test_identical_duplicates_not_collapsed(self):
        text = "".join(f"kelp{c}, 1\nkelp{c}, 2\n" for c in "abcdefghijkl")
        f = [x for x in run(text) if x.rule == "ISO999-8.1-DUPLICATE"]
        self.assertEqual(len(f), 12)

    def test_runs_absorbed_by_root_cause(self):
        # sorted by lower-cased code point: '--x' options before '-a'
        subs = "".join(f"  --{w}, 1\n" for w in ("xray", "yank", "zeta"))
        subs += "".join(f"  -{c}, 2\n" for c in "abc")
        text = ("kelp, 1\n" + subs + "lime, 1\n" +
                "".join(f"{c}.b, 1\n{c}_a, 2\n" for c in "mnopq"))
        fs = run(text)
        self.assertIn("ISO999-8-ROOTCAUSE", [f.rule for f in fs])
        self.assertNotIn("ISO999-8.6-RUNS", [f.rule for f in fs])
        rc = [f for f in fs if f.rule == "ISO999-8-ROOTCAUSE"][0]
        self.assertIn("subheading group", rc.message)

    def test_emphasis_ignored_by_alt_keys(self):
        # 'attach_mock' before bold 'attached': in order under a lower()
        # sort of the text; the bold markers must not decide it
        html = "<ul>" + "".join(
            f"<li>{w}_mock</li><li><strong>{w}ed</strong></li>"
            for w in ("attach", "bless", "crash", "dress", "finish")) + \
            "</ul>"
        self.assertEqual(warns(html, "html", locators="none"),
                         ["ISO999-8-ROOTCAUSE"])


class TestParsingExtrasV3(unittest.TestCase):
    def test_pagenum_marker_skipped(self):
        html = ('<h2>INDEX</h2><p>Bees, 4.<br>Beetles, <span class="pagenum">'
                '[492]</span>5.<br>Birds, 6.</p>')
        self.assertEqual([e.heading for e in tree(html, "html")],
                         ["Bees", "Beetles", "Birds"])

    def test_dialog_skipped(self):
        html = ('<table><tr><td><a href="/a">alpha</a></td></tr>'
                '<tr><td><a href="/b">beta</a></td></tr></table>'
                '<dialog><table><tr><td>?</td></tr><tr><td>/</td></tr>'
                '</table></dialog>')
        self.assertEqual([e.heading for e in tree(html, "html",
                                                  locators="anchor")],
                         ["alpha", "beta"])

    def test_locator_only_turnover_after_comma(self):
        text = ("Fries on species in large genera being allied,\n45.\n"
                "Frigate-bird, 142.\n")
        self.assertEqual(flat(tree(text)), [
            (0, "Fries on species in large genera being allied", ["45"]),
            (0, "Frigate-bird", ["142"])])

    def test_ditto_with_doubled_comma(self):
        text = ("Geoffroy, on balancement, 117.\n"
                "\u2014, , Isidore, on repeated parts, 118.\n")
        self.assertEqual(flat(tree(text))[1],
                         (1, "Isidore, on repeated parts", ["118"]))

    def test_parse_health_ignores_identifier_digits(self):
        html = "<ul>" + "".join(f'<li><a href="#v{i}">SockV{i}</a></li>'
                                for i in range(12)) + "</ul>"
        self.assertNotIn("ISO999-PARSE-HEALTH",
                         rules_of(html, "html", locators="anchor",
                                  filing="identifier"))


class TestLocatorSeparators(unittest.TestCase):
    """FIN-ISO 7.4-03: successive locators are separated by commas."""

    def test_spaces_only(self):
        self.assertIn("ISO999-7.4.2-LOCSEP",
                      warns("glaciers 14 22 90\nmoraines, 3, 8\n"))
        self.assertIn("ISO999-7.4.2-LOCSEP",
                      warns("glaciers, 14 22 90\nmoraines, 3, 8\n"))

    def test_semicolons(self):
        self.assertIn("ISO999-7.4.2-LOCSEP",
                      warns("kelp, 4; 12\nmoraines, 3, 8\n"))

    def test_commas_pass(self):
        self.assertNotIn("ISO999-7.4.2-LOCSEP",
                         rules_of("glaciers, 14, 22, 90\nmoraines, 3, 8\n"))

    def test_number_in_heading_is_not_a_list(self):
        # one trailing number, or numbers out of ascending order, stay a
        # heading ('Route 66', 'Boeing 747 400')
        self.assertNotIn("ISO999-7.4.2-LOCSEP",
                         rules_of("Route 66, 12\nTrunk road 9, 3, 4\n"))
        self.assertNotIn("ISO999-7.4.2-LOCSEP",
                         rules_of("Airliner 747 400, 12\nbuses, 3\n"))

    def test_runon_is_not_a_locator_list(self):
        self.assertNotIn("ISO999-7.4.2-LOCSEP",
                         rules_of("kelp, 4; drying, 12; zinc in, 8\n"))


class TestNumberingSequences(unittest.TestCase):
    """FIN-ISO 7.4-04: distinct numbering sequences told apart, one prefix
    scheme."""

    def test_parse_prefix_notations(self):
        self.assertEqual(L.parse_locator("2:45", 1).pstyle, "arabic:")
        loc = L.parse_locator("II.45", 1, ext=True)
        self.assertEqual((loc.prefix, loc.start, loc.pstyle),
                         (2, 45, "roman."))
        self.assertEqual(L.parse_locator("A-3", 1, ext=True).pstyle,
                         "letter-")
        self.assertEqual(L.parse_locator("A3", 1).pstyle, "letter")
        # the separated forms are never peeled off after one space
        self.assertIsNone(L.parse_locator("B-12", 1))
        self.assertEqual(heads("Vitamin B-12, 4\n")[0].heading,
                         "Vitamin B-12")

    def test_bare_numbers_beside_volume_prefixes(self):
        text = "tidal power, 1:88, 2:88\nwave power, 88\nwind, 2:14\n"
        self.assertIn("ISO999-7.4.2-SEQUENCE", warns(text))

    def test_all_prefixed_pass(self):
        text = "tidal power, 1:88, 2:88\nwave power, 1:90\nwind, 2:14\n"
        self.assertNotIn("ISO999-7.4.2-SEQUENCE", rules_of(text))

    def test_appendix_and_front_matter_beside_body_pass(self):
        text = "appendix tables, A3, A7\npreface, iv\nsluices, 12, 40\n"
        self.assertEqual(warns(text), [])

    def test_mixed_volume_notations(self):
        text = "tidal power, 1:88, II.40\nwave power, 2:88\n"
        self.assertIn("ISO999-7.4.2-PREFIX", warns(text))
        self.assertNotIn("ISO999-7.4.2-PREFIX",
                         rules_of("tidal power, 1:88, 2:40\n"
                                  "wave power, 2:88\n"))

    def test_mixed_letter_notations(self):
        self.assertIn("ISO999-7.4.2-PREFIX",
                      warns("appendix, A3, A-4\nbody, 12\n"))
        self.assertNotIn("ISO999-7.4.2-PREFIX",
                         rules_of("appendix, A-3, A-4\nbody, 12\n"))

    def test_roman_after_arabic(self):
        text = "preface, 12, xiv, 40\nzebra, 3\n"
        self.assertIn("ISO999-7.4.2-SEQORDER", infos(text))
        self.assertNotIn("ISO999-7.4.3-ASCENDING", rules_of(text))
        self.assertNotIn("ISO999-7.4.2-SEQORDER",
                         rules_of("preface, xiv, 12, 40\nzebra, 3\n"))

    def test_other_disorder_stays_ascending(self):
        text = "preface, 40, 12\n"
        self.assertIn("ISO999-7.4.3-ASCENDING", infos(text))
        self.assertNotIn("ISO999-7.4.2-SEQORDER", rules_of(text))

    def test_ind_prefixes(self):
        self.assertIn("ISO999-7.4.2-PREFIX", warns(ind(
            "\\item tidal power, 1:88, II.40",
            "\\item wave power, 2:88"), "ind"))


class TestSpecialMatterMarkers(unittest.TestCase):
    """FIN-ISO 7.4-17: one marking scheme for special-matter locators."""

    def test_mixed_scheme(self):
        self.assertIn("ISO999-7.4.4-SPECIAL",
                      infos("tides, 14, *22*, [31], 40m\n"))
        self.assertIn("ISO999-7.4.4-SPECIAL",
                      infos("tides, 14, 22f, 31t, fig. 4\n"))

    def test_one_scheme_passes(self):
        self.assertNotIn("ISO999-7.4.4-SPECIAL",
                         rules_of("tides, 14, 22f, 31t, 40m\n"))

    def test_bold_principal_is_not_special(self):
        self.assertNotIn("ISO999-7.4.4-SPECIAL",
                         rules_of("tides, 14, 22f, 31t\nwaves, 3, **7**\n"))

    def test_notes_and_columns_are_not_special(self):
        self.assertNotIn("ISO999-7.4.4-SPECIAL",
                         rules_of("tides, 14n, 22a, *31*\n"))

    def test_styles_from_html_and_ind(self):
        html = ("<ul><li>tides, 14, <i>22</i>, 31t</li>"
                "<li>waves, 3, <b>7</b></li></ul>")
        self.assertIn("ISO999-7.4.4-SPECIAL", infos(html, "html"))
        self.assertIn("ISO999-7.4.4-SPECIAL", infos(ind(
            "\\item tides, 14, \\textit{22}, 31t"), "ind"))
        self.assertNotIn("ISO999-7.4.4-SPECIAL", rules_of(ind(
            "\\item tides, 14, \\textbf{22}, 31t"), "ind"))

    def test_figure_numbers_are_their_own_sequence(self):
        r = heads("tides, 14, 40, fig. 3\n")
        self.assertEqual(len(r[0].locators), 3)
        self.assertTrue(r[0].locators[2].wprefix)
        self.assertNotIn("ISO999-7.4.3-ASCENDING",
                         rules_of("tides, 14, 40, fig. 3\n"))
        loc = L.parse_locator("12 (map)", 1)
        self.assertEqual((loc.start, loc.marker), (12, "map"))


class TestIndentation(unittest.TestCase):
    """FIN-ISO 9.1.2.4-01 / 9.4.1.4-01: uniform indents per level; turnover
    lines deeper than the deepest subheading (text layouts)."""

    def test_uneven_level(self):
        text = ("harbours, 4\n  berths, 7\n    night, 9\n  cranes, 12\n"
                "quays, 3\n    tolls, 8\n")
        self.assertIn("ISO999-9.1.2.4-INDENT", warns(text))

    def test_uniform_levels_pass(self):
        text = ("harbours, 4\n  berths, 7\n    night, 9\n  cranes, 12\n"
                "quays, 3\n  tolls, 8\n")
        self.assertNotIn("ISO999-9.1.2.4-INDENT", rules_of(text))

    def test_markdown_bullets_not_measured(self):
        text = "- harbours, 4\n  - berths, 7\n- quays, 3\n    - tolls, 8\n"
        self.assertNotIn("ISO999-9.1.2.4-INDENT", rules_of(text))

    LAYOUT = ("Harbours\n  Construction of breakwaters in the northern\n"
              "{t}bays, 12\n  moles, 14\n    rubble, 15\nQuays, 3,\n"
              "{t}18, 22\n")

    def test_shallow_turnover(self):
        # turnovers at the sub-subheading column (4)
        text = self.LAYOUT.format(t="    ")
        self.assertIn("ISO999-9.4.1.4-TURNOVER", warns(text))
        r = heads(text)
        self.assertEqual(r[0].children[0].heading,
                         "Construction of breakwaters in the northern bays")

    def test_deep_turnover_passes(self):
        text = self.LAYOUT.format(t="        ")
        self.assertNotIn("ISO999-9.4.1.4-TURNOVER", rules_of(text))
        r = heads(text)
        self.assertEqual(r[0].children[0].heading,
                         "Construction of breakwaters in the northern bays")
        self.assertEqual(len(r[1].locators), 3)

    def test_flush_left_turnover_in_flat_index(self):
        text = ("Aberrant groups, 379.\nAgassiz on parallelism of "
                "development and geological\nsuccession, 396.\n"
                "Algae, 338.\nAnts, 207.\n")
        self.assertIn("ISO999-9.4.1.4-TURNOVER", warns(text))

    def test_html_not_measured(self):
        html = ("<p>Harbours, 3,<br>18, 22</p><p>Quays, 5</p>")
        self.assertNotIn("ISO999-9.4.1.4-TURNOVER", rules_of(html, "html"))


class TestRunOnPunctuation(unittest.TestCase):
    """FIN-ISO 9.5-02: run-on punctuation conventions."""

    GOOD = ("beacons: coastal 7; inland 9\n"
            "buoys 3; bell 4; whistle 6\n"
            "lighthouses 14, 20; fuel 33, 40 (oil 33; paraffin 40); "
            "keepers 31\n")

    def test_consistent_passes(self):
        self.assertEqual([r for r in rules_of(self.GOOD)
                          if r == "ISO999-9.5-RUNON"], [])

    def test_parse_colon_lead_and_third_level(self):
        r = heads(self.GOOD)
        self.assertEqual([e.heading for e in r],
                         ["beacons", "buoys", "lighthouses"])
        self.assertEqual([c.heading for c in r[0].children],
                         ["coastal", "inland"])
        fuel = r[2].children[0]
        self.assertEqual((fuel.heading, [c.heading for c in fuel.children]),
                         ("fuel", ["oil", "paraffin"]))

    def test_colon_after_locators(self):
        text = ("buoys 3; bell 4; whistle 6\n"
                "lighthouses: 14, 20; keepers 31\n")
        self.assertIn("ISO999-9.5-RUNON", warns(text))

    def test_semicolon_after_bare_lead(self):
        text = "beacons; coastal 7; inland 9\nbuoys 3; bell 4; whistle 6\n"
        self.assertIn("ISO999-9.5-RUNON", warns(text))

    def test_bare_lead_needs_a_runon_index(self):
        # one prose semicolon in a set-out index is not run-on layout
        text = "Animals, domestic; descended from stocks, 14.\nApes, 3.\n"
        self.assertNotIn("ISO999-9.5-RUNON", rules_of(text))

    def test_comma_between_siblings(self):
        text = ("buoys 3; bell 4; whistle 6\n"
                "lighthouses 14, 20; keepers 31, fuel 33, 40\n")
        self.assertIn("ISO999-9.5-RUNON", warns(text))

    def test_unbalanced_parentheses(self):
        text = ("buoys 3; bell 4; whistle 6\n"
                "lighthouses 14; fuel 33 (oil 33; paraffin 40\n")
        self.assertIn("ISO999-9.5-RUNON", warns(text))


class TestTextSections(unittest.TestCase):
    """FIN-ISO T3-9: --only-section and section splitting for text."""

    TEXT = ("INDEX OF NAMES\n\nAdler, Rhea, 4\nBrandt, Oskar, 9\n\n"
            "INDEX OF PLACES\n\nAmberley, 3\nB\nBarrow, 5\nCorran, 12\n")

    def test_sections_split(self):
        # Amberley after Brandt is not a misorder: a new sequence starts
        self.assertEqual(warns(self.TEXT), [])
        self.assertIn("ISO999-8.2-ORDER",
                      warns(self.TEXT, sections="merge"))

    def test_only_section_heading(self):
        seqs, _ = L.parse_index(self.TEXT, "text",
                                L.Options(only_section="places"))
        self.assertEqual([e.heading for _, r in seqs for e in r],
                         ["Amberley", "Barrow", "Corran"])

    def test_only_section_letter_group(self):
        seqs, _ = L.parse_index(self.TEXT, "text",
                                L.Options(only_section="^B$"))
        self.assertEqual([e.heading for _, r in seqs for e in r],
                         ["Barrow", "Corran"])

    def test_markdown_heading_sections(self):
        text = ("## Names\n\nAdler, 4\nBrandt, 9\n\n## Places\n\n"
                "Amberley, 3\n")
        self.assertEqual(warns(text), [])
        seqs, _ = L.parse_index(text, "text",
                                L.Options(only_section="^names$"))
        self.assertEqual([e.heading for _, r in seqs for e in r],
                         ["Adler", "Brandt"])

    def test_single_caption_is_not_a_split(self):
        seqs, _ = L.parse_index("INDEX\n\nabacus, 3\nbeads, 4\n", "text",
                                L.Options())
        self.assertEqual([lab for lab, _ in seqs], [None])

    def test_no_match_is_an_error(self):
        out, err = io.StringIO(), io.StringIO()
        with tempfile.NamedTemporaryFile("w", suffix=".txt",
                                         delete=False) as fh:
            fh.write(self.TEXT)
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = L.main([fh.name, "--only-section", "nowhere"])
        finally:
            os.unlink(fh.name)
        self.assertEqual(code, 2)
        self.assertIn("matched no section", err.getvalue())


class TestArticleAndInitialismFiling(unittest.TestCase):
    """FIN-ISO 7.3.4.2-01 / 7.3.6-02 coverage additions."""

    def test_front_article_filed_both_ways(self):
        text = ("Oak, 3\nThe Orchard, 5\nOrkney, 7\nPine, 9\nTea, 1\n"
                "The Zebra, 2\nTiger, 4\n")
        rules = warns(text)
        self.assertIn("ISO999-7.3.4.2-ARTICLE", rules)
        self.assertNotIn("ISO999-8.2-ORDER", rules)

    def test_front_article_consistently_ignored_is_info(self):
        text = "Oak, 3\nThe Orchard, 5\nOrkney, 7\nPine, 9\n"
        self.assertNotIn("ISO999-7.3.4.2-ARTICLE", warns(text))
        self.assertIn("ISO999-7.3.4.2-ARTICLE", infos(text))

    def test_front_article_under_t_is_fine(self):
        text = "Tea, 1\nThe Orchard, 5\nTiger, 4\n"
        self.assertNotIn("ISO999-7.3.4.2-ARTICLE", rules_of(text))

    def test_dotted_initialism_filed_as_letters(self):
        rules = warns("N.A.T.O., 5\nNairobi, 2\nNASA, 4\nNavy, 7\n")
        self.assertIn("ISO999-7.3.6-ABBREV", rules)
        self.assertNotIn("ISO999-8.2-ORDER", rules)

    def test_initialisms_filed_as_words_pass(self):
        self.assertEqual(warns("Nairobi, 2\nNASA, 4\nN.A.T.O., 5\n"
                               "Navy, 7\n"), [])


GOLDEN_ROOT = os.path.normpath(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), ".."))
GOLDEN_MANIFEST = os.path.join(GOLDEN_ROOT, "evals", "golden", "golden.json")


def golden_counts(case):
    path = os.path.join(GOLDEN_ROOT, case["path"])
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = L.main([path, "--json", *case["args"]])
    if code == 2:
        return {"error": err.getvalue().strip()}
    data = json.loads(out.getvalue())
    counts = {}
    for f in data["findings"]:
        k = f"{f['rule']}/{f['severity']}"
        counts[k] = counts.get(k, 0) + 1
    counts["entries"] = data["entries"]
    return dict(sorted(counts.items()))


@unittest.skipUnless(os.path.exists(GOLDEN_MANIFEST), "no golden corpus")
class TestGolden(unittest.TestCase):
    """T2-5: pinned finding counts on real-world and self-built indexes."""

    def test_golden_counts(self):
        with open(GOLDEN_MANIFEST, encoding="utf-8") as fh:
            man = json.load(fh)
        for case in man["cases"]:
            if not os.path.exists(os.path.join(GOLDEN_ROOT, case["path"])):
                continue
            with self.subTest(case=case["name"]):
                self.assertIn("expect", case, "run --update-golden")
                self.assertEqual(golden_counts(case), case["expect"])


def update_golden():
    with open(GOLDEN_MANIFEST, encoding="utf-8") as fh:
        man = json.load(fh)
    for case in man["cases"]:
        if os.path.exists(os.path.join(GOLDEN_ROOT, case["path"])):
            case["expect"] = golden_counts(case)
    with open(GOLDEN_MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

class TestNonUtf8Stdout(unittest.TestCase):
    """Windows pipes default to cp1252: --json output must not raise and must parse."""

    def test_json_non_ascii(self):
        import subprocess
        env = dict(os.environ, PYTHONIOENCODING="cp1252")
        env.pop("PYTHONUTF8", None)
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "iso999_lint.py")
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "idx.txt")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("Z\u00fcrich, 4\n\u65e5\u672c, 9\n\u00c5ngstr\u00f6m units, 12\u201314\nabacus, 3\n")
            cp = subprocess.run([sys.executable, script, p, "--json"], capture_output=True, env=env)
            self.assertNotIn(b"UnicodeEncodeError", cp.stderr)
            json.loads(cp.stdout.decode("ascii"))



if __name__ == "__main__":
    if "--update-golden" in sys.argv:
        update_golden()
        sys.exit(0)
    unittest.main()
