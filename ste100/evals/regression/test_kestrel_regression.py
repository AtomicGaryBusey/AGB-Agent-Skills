#!/usr/bin/env python3
"""Regression checks for ste_check.py on the Kestrel eval project.

These tests live outside the skill so that the skill files never refer to the
eval fixture. They check checker behavior only (no answer key is read), and
they skip when the dictionary cache (.cache/) is absent.

Run: python3 -m unittest evals/regression/test_kestrel_regression.py
"""

import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CHECKER = os.path.join(ROOT, "scripts", "ste_check.py")
PROJECT = os.path.join(ROOT, "evals", "fixtures", "kestrel", "project")
CACHE = os.path.join(ROOT, ".cache", "ste100-dictionary.json")


def run(*extra):
    p = subprocess.run([sys.executable, CHECKER, "--json"] + list(extra) + [PROJECT],
                       cwd=ROOT, capture_output=True, text=True)
    return json.loads(p.stdout)


@unittest.skipUnless(os.path.isfile(CACHE), "dictionary cache not built")
class KestrelRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = run()
        cls.flat = [(os.path.relpath(loc["file"], PROJECT), loc["line"], f["rule"],
                     f["message"])
                    for f in cls.data["findings"] for loc in f["locations"]]

    def at(self, name, line=None, rule=None):
        return [x for x in self.flat if x[0] == name and (line is None or x[1] == line) and
                (rule is None or x[2] == rule)]

    def test_term_list_is_read_and_not_linted(self):
        meta = self.data["meta"]
        self.assertGreaterEqual(meta["terms"]["count"], 20)
        self.assertEqual([os.path.basename(f) for f in meta["skipped"]], ["DOCS_TERMS.md"])
        self.assertEqual(self.at("DOCS_TERMS.md"), [])

    def test_technical_verb_from_the_verb_table(self):
        self.assertEqual([x for x in self.flat if x[2] in ("STE-1.7", "STE-1.13")], [])

    def test_do_not_use_word_gives_1_11(self):
        # Checker 2.2.0 adds a second kind of STE-1.11 finding (INFO: a variant
        # of a multi-word term). The do-not-use findings still say "instead".
        f = [x for x in self.flat if x[2] == "STE-1.11" and "variant" not in x[3]]
        self.assertTrue(f)
        self.assertTrue(all("instead" in x[3] for x in f))

    def test_abbreviation_before_definition_in_overview(self):
        f = self.at(os.path.join("docs", "overview.md"), rule="STE-2.2")
        self.assertTrue(any("before its definition" in x[3] for x in f), f)

    def test_bare_noun_after_command_gives_article_not_1_1(self):
        # A work step of the form "<verb> <noun> from <noun>." with no articles.
        rows = self.at(os.path.join("docs", "install.md"), 15)
        self.assertTrue([x for x in rows if x[2] == "STE-4.5"], rows)
        self.assertEqual([x for x in rows if x[2] == "STE-1.1"], [])

    def test_one_vocabulary_finding_per_location(self):
        vocab = {"STE-1.1", "STE-1.2", "STE-1.4", "STE-1.6", "STE-1.11"}
        seen = {}
        for f in self.data["findings"]:
            if f["rule"] in vocab:
                for loc in f["locations"]:
                    seen.setdefault((loc["file"], loc["line"], loc["col"]), set()).add(
                        f["rule"])
        self.assertEqual([k for k, v in seen.items() if len(v) > 1], [])

    # -- audit fixes in checker 2.2.0 (false positives)
    def rules_at(self, name, line):
        return [x[2] for x in self.at(name, line)]

    def test_product_name_with_article_is_not_4_5(self):
        self.assertNotIn("STE-4.5", self.rules_at("README.md", 3))
        self.assertNotIn("STE-4.5", self.rules_at(os.path.join("docs", "overview.md"), 5))

    def test_tn_alternative_heading_and_link_text(self):
        for name, line in (("README.md", 10), (os.path.join("docs", "troubleshooting.md"), 1)):
            rules = self.rules_at(name, line)
            self.assertNotIn("STE-1.1", rules)
            self.assertNotIn("STE-3.5", rules)

    def test_no_4_5_in_tools_list(self):
        self.assertNotIn("STE-4.5", self.rules_at(os.path.join("docs", "install.md"), 8))

    def test_direction_is_not_phrasal(self):
        self.assertEqual([x for x in self.flat if x[2] == "STE-9.3"], [])

    def test_leading_adjective_and_expansion_not_in_2_1(self):
        f = [x[3] for x in self.flat if x[2] == "STE-2.1"]
        self.assertFalse([m for m in f if "new outlet" in m or "maximum allowable" in m], f)

    def test_expansion_of_abbreviation_is_not_unapproved(self):
        rules = self.rules_at(os.path.join("docs", "overview.md"), 24)
        self.assertNotIn("STE-1.1", rules)
        self.assertNotIn("STE-3.5", rules)

    def test_stative_closed_and_ing_noun(self):
        name = os.path.join("docs", "troubleshooting.md")
        self.assertNotIn("STE-3.6", self.rules_at(name, 8))
        self.assertNotIn("STE-3.5", self.rules_at(name, 9))
        # The action passive "is then removed" is still reported.
        self.assertIn("STE-3.6", self.rules_at(os.path.join("docs", "maintenance.md"), 16))

    def test_1_6_message_for_unapproved_verb_noun(self):
        f = [x[3] for x in self.flat if x[2] == "STE-1.6" and "as a noun" in x[3]]
        self.assertTrue(f)
        self.assertTrue(all("not approved" in m and "possible technical noun" in m for m in f))

    # -- audit fixes in checker 2.2.0 (false negatives)
    def test_must_in_step_and_safety_obligation(self):
        name = os.path.join("docs", "maintenance.md")
        self.assertIn("STE-5.3", self.rules_at(name, 18))
        self.assertIn("STE-7.1", self.rules_at(name, 9))
        # "because the pump must start": a reason clause, not a step statement.
        self.assertNotIn("STE-5.3", self.rules_at(os.path.join("docs", "install.md"), 29))

    def test_variant_of_term(self):
        f = [x for x in self.flat if x[2] == "STE-1.11" and "variant" in x[3]]
        self.assertEqual([(x[0], x[1]) for x in f], [(os.path.join("docs", "maintenance.md"), 27)])

    def test_unknown_words_has_hyphenated_letter_word(self):
        self.assertIn("O-ring", [r["word"] for r in run("--unknown-words")])

    def test_british_spelling_suggests_approved_word(self):
        f = [x for x in self.data["findings"] if x["rule"] == "STE-1.14"]
        self.assertTrue(f)
        self.assertNotEqual(f[0]["suggestion"], "Write 'center'.")

    def test_unknown_words_list(self):
        rows = run("--unknown-words")
        self.assertTrue(rows)
        self.assertTrue(all(r["tag"] in ("TN", "TV") and r["count"] >= 1 for r in rows))


if __name__ == "__main__":
    unittest.main()
