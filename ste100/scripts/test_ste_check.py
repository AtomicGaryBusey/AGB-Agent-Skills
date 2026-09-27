#!/usr/bin/env python3
"""Tests for ste_check.py.

All example sentences are invented for these tests. The vocabulary tests use
the invented mini dictionary in fixtures/mini_dictionary.json, which has the
same schema as the real cache. Its content words are nonce words (glab, vorsk,
frobnicate, ...) and its not-approved -> alternative pairs are invented; only
generic English function words keep their ordinary use. Sentences checked with
that fixture use the nonce words. English content words that remain in them
are either deliberately unknown to the fixture (gasket) or are triggers that
the checker itself hard-codes (injury, gloves, closed, point). Tests against
the real cache are skipped when .cache/ste100-dictionary.json is absent.

Run: python3 -m unittest scripts/test_ste_check.py   (or run this file)
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import ste_check as sc  # noqa: E402

SCRIPT = os.path.join(HERE, "ste_check.py")
FIXTURE = os.path.join(HERE, "fixtures", "mini_dictionary.json")
REAL_CACHE = os.path.join(os.path.dirname(HERE), ".cache", "ste100-dictionary.json")
LEX = sc.Lexicon.load(FIXTURE)


def check(text, flavor="md", lex=LEX, terms=None, profile="auto"):
    return sc.check_text(text, flavor, "t.md", lex, terms, profile)


def rules(findings):
    return [f.rule for f in findings]


def find(findings, rule, text=None):
    out = [f for f in findings if f.rule == rule and (text is None or text in f.message)]
    return out


def terms(text):
    return sc.TermList().parse(text)


def words(text, flavor="md"):
    b = sc.Block("paragraph")
    b.add(1, 0, text)
    b.build()
    b.masked = sc.mask_block(b.text, flavor)
    b.tokens = sc.tokenize(b.masked)
    s = sc.split_sentences(b)[0]
    return sc.count_words(s.tokens, sc.is_upper_sentence(s.tokens))


def blocks(text, flavor="md"):
    out = sc.Parser(text, flavor).parse()
    for b in out:
        b.build()
    return out


class ExtractionTests(unittest.TestCase):
    def test_code_fence_indented_code_and_front_matter_are_skipped(self):
        text = ("---\ntitle: a; b\n---\n\nThe vorsk glabs.\n\n```\nx = 1; y = 2\n```\n\n"
                "    indented; code\n\n~~~sh\nrm -rf /tmp; ls\n~~~\n")
        fs = check(text)
        self.assertEqual(find(fs, "STE-8.1"), [])
        texts = [b.text for b in blocks(text)]
        self.assertEqual(texts, ["The vorsk glabs."])

    def test_inline_code_urls_paths_and_link_targets_are_masked(self):
        text = ("Glab `a; b` and https://example.com/x;y and the file "
                "src/app/main.py and [the guide](docs/a;b.md) and <b>bold</b>.\n")
        fs = check(text)
        self.assertEqual(find(fs, "STE-8.1"), [])
        self.assertEqual(find(fs, "STE-X-SLASH"), [])
        self.assertEqual(find(fs, "STE-1.6", "guide"), find(fs, "STE-1.6", "guide"))
        self.assertTrue(find(fs, "STE-1.6", "'guide'"))   # link text is prose

    def test_html_comment_and_block_are_skipped(self):
        text = "<!-- a; b -->\n\n<div>\nx; y\n</div>\n\nThe vorsk glabs.\n"
        self.assertEqual(find(check(text), "STE-8.1"), [])

    def test_line_and_column_are_kept(self):
        text = "The vorsk glabs.\n\n  Glab the vorsk; trosk the flarn.\n"
        f = find(check(text), "STE-8.1")[0]
        self.assertEqual((f.line, f.col), (3, 17))

    def test_paragraph_across_lines_keeps_positions(self):
        text = "The vorsk glabs\nslowly; the flarn stays.\n"
        f = find(check(text), "STE-8.1")[0]
        self.assertEqual((f.line, f.col), (2, 7))

    def test_table_cells_are_prose_with_columns(self):
        text = "| Name | Use |\n|---|---|\n| `x` | Glab it; trosk it. |\n"
        bs = blocks(text)
        self.assertEqual([b.kind for b in bs], ["table_cell"] * 4)
        self.assertTrue(bs[0].header)
        f = find(check(text), "STE-8.1")[0]
        self.assertEqual((f.line, f.col), (3, 16))

    def test_headings_and_setext(self):
        bs = blocks("# Snarbing the flarn\n\nText here.\n\nTitle\n=====\n")
        self.assertEqual([b.kind for b in bs], ["heading", "paragraph", "heading"])
        # -ing forms are permitted in headings (procedure titles).
        self.assertEqual(find(check("## Snarbing the flarn\n"), "STE-3.5"), [])

    def test_blockquote_and_alert_label(self):
        text = "> [!WARNING]\n> Do not pront the skeen. It can cause injury.\n"
        bs = blocks(text)
        self.assertEqual(bs[0].label, "WARNING")
        self.assertTrue(bs[0].quote)
        self.assertEqual(bs[0].segs[0][1], 2)

    def test_label_prefix_is_removed(self):
        bs = blocks("**Note:** The vorsk glabs.\n")
        self.assertEqual(bs[0].label, "NOTE")
        self.assertEqual(bs[0].segs[0][2].strip(), "The vorsk glabs.")

    def test_lists(self):
        bs = blocks("Do these steps:\n\n1. Glab the vorsk.\n2. Trosk the vorsk.\n   More text.\n"
                    "   - Nested item\n")
        items = [b for b in bs if b.kind == "list_item"]
        self.assertEqual(len(items), 3)
        self.assertTrue(items[0].ordered)
        self.assertEqual(items[1].text, "Trosk the vorsk. More text.")
        self.assertEqual(items[2].level, 1)

    def test_rst_code_and_admonition(self):
        text = ("Title\n=====\n\n.. code-block:: sh\n\n   a; b\n\n.. note::\n\n"
                "   Glab the vorsk.\n\nThe end::\n\n    x; y\n")
        fs = check(text, "rst")
        self.assertEqual(find(fs, "STE-8.1"), [])
        self.assertTrue(find(fs, "STE-5.5"))

    def test_adoc_listing_and_admonition(self):
        text = "= Title\n\n----\na; b\n----\n\nNOTE: Glab the vorsk.\n"
        fs = check(text, "adoc")
        self.assertEqual(find(fs, "STE-8.1"), [])
        self.assertTrue(find(fs, "STE-5.5"))

    def test_quoted_text_is_not_checked(self):
        fs = check('Select "Colour; frobnicate".\n')
        self.assertEqual(find(fs, "STE-1.14"), [])
        self.assertEqual(find(fs, "STE-1.1"), [])
        self.assertEqual(find(fs, "STE-8.1"), [])


class WordCountTests(unittest.TestCase):
    """Rules 8.4 to 8.7, with invented sentences."""

    def test_plain(self):
        self.assertEqual(words("Open the valve."), 3)

    def test_parentheses_count_as_one(self):
        self.assertEqual(words("Loosen the clamp bolt (7)."), 5)
        self.assertEqual(words("Open the valve (the green lamp comes on)."), 4)

    def test_numbers_and_units(self):
        self.assertEqual(words("The cable weighs 3 kg."), 4)
        self.assertEqual(words("Set the heater to 40 °C."), 5)
        self.assertEqual(words("Wait 30 seconds."), 2)
        self.assertEqual(words("Fill it to 50 %."), 4)

    def test_hyphenated_group_is_one(self):
        self.assertEqual(words("Use a push-fit clamp."), 4)

    def test_quoted_code_abbreviation_identifier(self):
        self.assertEqual(words('Click "Save and close" to continue.'), 4)
        self.assertEqual(words("Run `make test` now."), 3)
        self.assertEqual(words("Connect port J12 to the USB hub."), 7)

    def test_proper_noun_and_label_runs(self):
        self.assertEqual(words("Send the report to the Regional Safety Office today."), 7)
        self.assertEqual(words("Set the MAIN POWER switch to ON."), 6)

    def test_uppercase_sentence_counts_each_word(self):
        self.assertEqual(words("DO NOT TOUCH THE HOT PLATE."), 6)


class VocabularyTests(unittest.TestCase):
    def test_v1_regression_sentence(self):
        fs = check("It is vorbary to frobnicate the plimsade in blurk to zorbulate the "
                   "quiskation.\n")
        msgs = {f.message: f.suggestion for f in find(fs, "STE-1.1")}
        self.assertIn("'frobnicate' is not approved", msgs)
        self.assertIn("'zorbulate' is not approved", msgs)
        self.assertIn("'in blurk to' is not approved", msgs)
        self.assertIn("BRELL (v)", msgs["'frobnicate' is not approved"])
        self.assertIn("QUOMP (v)", msgs["'zorbulate' is not approved"])
        self.assertIn("TO (prep)", msgs["'in blurk to' is not approved"])
        # "blurk" inside the phrase is not reported again.
        self.assertFalse(any("'blurk'" in m for m in msgs))

    def test_inflected_unapproved_word(self):
        fs = check("The dorp frobnicates the glimmet.\n")
        self.assertTrue(find(fs, "STE-1.1", "frobnicates"))

    def test_unapproved_phrase_with_inflection(self):
        fs = check("The blaxor blarried out the tosk.\n")
        self.assertTrue(find(fs, "STE-1.1", "blarried out"))

    def test_part_of_speech_imperative(self):
        f = find(check("Tosk the vorsk.\n"), "STE-1.2")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, "warn")
        self.assertIn("VESK (v)", f[0].suggestion)
        self.assertEqual(find(check("Do the tosk of the vorsk.\n"), "STE-1.2"), [])

    def test_part_of_speech_after_modal(self):
        f = find(check("You must blick the vorsk.\n"), "STE-1.2")
        self.assertEqual(f[0].severity, "warn")
        self.assertIn("noun", f[0].message)

    def test_noun_use_of_verb_only_entry_is_unlisted_not_unapproved(self):
        fs = check("Snarb the blurk.\n")          # blurk: only 'n' not approved
        self.assertTrue(find(fs, "STE-1.1", "'blurk'"))

    def test_unlisted_forms(self):
        fs = check("Brell a grasker glimmet. The vorsk halped.\n")
        self.assertTrue(find(fs, "STE-1.4", "grasker"))
        self.assertTrue(find(fs, "STE-1.4", "halped"))
        self.assertEqual(find(check("Brell the dreelest vonk.\n"), "STE-1.4"), [])

    def test_unknown_word_and_term_list(self):
        fs = check("Snarb the gasket.\n")
        self.assertTrue(find(fs, "STE-1.6", "gasket"))
        fs = check("Snarb the gasket.\n", terms=terms("- gasket (TN): a seal ring\n"))
        self.assertEqual(find(fs, "STE-1.6"), [])

    def test_multi_word_term(self):
        tl = terms("| Term | Kind |\n|---|---|\n| blend mode | TN |\n")
        fs = check("Plim the blend modes.\n", terms=tl)
        self.assertEqual(find(fs, "STE-1.6"), [])

    def test_proper_names_identifiers_numbers_are_ignored(self):
        fs = check("Sprock the dax to Zorblat with `zx_tool` and v2 at 10 kg on J12.\n")
        self.assertEqual(find(fs, "STE-1.6"), [])

    def test_grouping_of_repeated_findings(self):
        fs = sc.group_findings(check("Snarb the gasket. Wemble the gasket.\n\n"
                                     "Quisk the gasket.\n"))
        g = find(fs, "STE-1.6", "gasket")
        self.assertEqual(len(g), 1)
        self.assertEqual(len(g[0].locations), 3)
        self.assertEqual(g[0].as_dict()["count"], 3)
        self.assertIn("3 occurrences", sc.format_text(g[0]))

    def test_technical_noun_used_as_verb(self):
        fs = check("You must tape the glimmet.\n", terms=terms("tape (TN)\n"))
        self.assertTrue(find(fs, "STE-1.7"))

    def test_technical_verb_used_as_noun(self):
        fs = check("Do a reboot of the dorp.\n", terms=terms("reboot (TV)\n"))
        self.assertTrue(find(fs, "STE-1.13"))

    def test_no_dictionary_obligation_fallback(self):
        fs = check("The blaxor should glab the vorsk.\n", lex=None)
        self.assertTrue(find(fs, "STE-X-OBLIGATION"))
        fs = check("The blaxor should glab the vorsk.\n")
        self.assertTrue(find(fs, "STE-1.1", "should"))
        self.assertEqual(find(fs, "STE-X-OBLIGATION"), [])


class SpellingTests(unittest.TestCase):
    def test_british_words(self):
        fs = check("Change the colour of the cable. Organise the centre panel.\n", lex=None)
        sugg = [f.suggestion for f in find(fs, "STE-1.14")]
        self.assertIn("Write 'color'.", sugg)
        self.assertIn("Write 'Organize'.", sugg)
        self.assertIn("Write 'center'.", sugg)

    def test_exceptions(self):
        fs = check("Advise the operator. Exercise care. The noise stops. Four hours. Our "
                   "cover.\n", lex=None)
        self.assertEqual(find(fs, "STE-1.14"), [])


class RuleTests(unittest.TestCase):
    def test_2_1_noun_cluster(self):
        self.assertTrue(find(check("Snarb the pomble motch cooling vonk cobbet.\n"), "STE-2.1"))
        self.assertEqual(find(check("Snarb the vonk cobbet.\n"), "STE-2.1"), [])

    def test_2_2_abbreviation_definition(self):
        self.assertTrue(find(check("Restart the QXR daemon.\n", lex=None), "STE-2.2",
                             "no definition"))
        ok = "The Quick Xfer Relay (QXR) sends data. Restart the QXR.\n"
        self.assertEqual(find(check(ok, lex=None), "STE-2.2"), [])
        late = "Restart the QXR. The Quick Xfer Relay (QXR) sends data.\n"
        self.assertTrue(find(check(late, lex=None), "STE-2.2", "before its definition"))

    def test_3_2_progressive(self):
        self.assertTrue(find(check("The dorp is sprocking dax.\n"), "STE-3.2"))

    def test_3_4_complex_constructions(self):
        self.assertTrue(find(check("The blaxor has snarbed the vorsk.\n"), "STE-3.4"))
        self.assertTrue(find(check("The vorsk can be glabbed.\n"), "STE-3.4"))
        self.assertTrue(find(check("The fribs have been snarbed.\n"), "STE-3.4"))

    def test_3_5_ing(self):
        f = find(check("After snarbing the flarn, wemble the dorp.\n"), "STE-3.5")
        self.assertEqual(f[0].severity, "warn")
        tl = terms("cooling vonk (TN)\n")
        self.assertEqual(find(check("Wemble the cooling vonk.\n", terms=tl), "STE-3.5"), [])

    def test_3_6_passive(self):
        f = find(check("The vorsk is glabbed by the moderon.\n"), "STE-3.6")
        self.assertEqual(f[0].severity, "warn")
        f = find(check("The cache was corrupted.\n", lex=None), "STE-3.6")
        self.assertEqual(f[0].severity, "info")
        f = find(check("1. The cover is removed.\n", lex=None), "STE-3.6")
        self.assertEqual(f[0].severity, "warn")
        # A participle that is an approved adjective shows a condition.
        self.assertEqual(find(check("Fleem kest that the gronk is flonched.\n"), "STE-3.6"), [])

    def test_3_7_nominalization(self):
        fs = check("After the snarbal of the flarn, wemble the vonk.\n")
        self.assertTrue(find(fs, "STE-3.7", "snarbal"))

    def test_4_2_contractions_and_omissions(self):
        self.assertTrue(find(check("Don't glab the flarn.\n"), "STE-4.2", "contraction"))
        self.assertEqual(find(check("Read the blaxor's notes.\n"), "STE-4.2"), [])
        self.assertTrue(find(check("If snibbed, snarb the flarn.\n"), "STE-4.2"))

    def test_4_3_vertical_lists(self):
        fs = check("The kit has these pakes\n\n- the glimmet,\n- A vonk\n  - A skeen\n")
        msgs = [f.message for f in find(fs, "STE-4.3")]
        self.assertTrue(any("colon" in m for m in msgs))
        self.assertTrue(any("comma" in m for m in msgs))
        self.assertTrue(any("lowercase" in m for m in msgs))
        self.assertTrue(any("nested" in m for m in msgs))
        ok = check("The kit has these pakes:\n\n- The glimmet\n- The vonk.\n")
        self.assertEqual(find(ok, "STE-4.3"), [])

    def test_4_3_series(self):
        fs = check("The kit has a glimmet, a vonk, a skeen, a pomble, a motch and a flarn for "
                   "the dorp in the box.\n")
        self.assertTrue(find(fs, "STE-4.3", "series"))

    def test_4_5_articles(self):
        self.assertTrue(find(check("Snarb flarn.\n"), "STE-4.5"))
        self.assertEqual(find(check("Snarb the flarn.\n"), "STE-4.5"), [])
        self.assertTrue(find(check("Glab the vorsk V12.\n"), "STE-4.5", "identifier"))

    def test_5_1_and_6_3_length(self):
        proc = ("Open the cover of the unit and then carefully remove the old cable from "
                "the rear panel of the unit with the tool.\n")
        f = find(check(proc, lex=None), "STE-5.1")
        self.assertEqual(len(f), 1)
        self.assertIn("23 words", f[0].message)
        desc = ("The unit has a cover that protects the cable and the fan from dust and "
                "water, and it keeps the motor cool in hot rooms.\n")
        self.assertEqual(find(check(desc, lex=None), "STE-6.3"), [])
        long_desc = desc.replace("hot rooms", "hot rooms during the long summer months of "
                                              "the year")
        self.assertTrue(find(check(long_desc, lex=None), "STE-6.3"))

    def test_profile_override(self):
        desc = ("The unit has a cover that protects the cable and the fan from dust and "
                "water in the small room at night.\n")          # 22 words
        self.assertEqual(find(check(desc, lex=None), "STE-5.1"), [])
        self.assertTrue(find(check(desc, lex=None, profile="procedure"), "STE-5.1"))

    def test_5_2_one_instruction(self):
        f = find(check("Glab the flarn and snarb the vorsk, then wemble the dorp.\n"),
                 "STE-5.2")
        self.assertEqual(f[0].severity, "warn")
        self.assertIn("3 instructions", f[0].message)
        self.assertEqual(find(check("Snarb and flurge the glimmet.\n"), "STE-5.2"), [])

    def test_5_3_imperative(self):
        self.assertTrue(find(check("1. The blaxor must glab the vorsk.\n"), "STE-5.3"))
        self.assertEqual(find(check("1. Glab the vorsk.\n"), "STE-5.3"), [])

    def test_5_4_condition_first(self):
        self.assertTrue(find(check("Glab the vorsk when the presk is fimp.\n"), "STE-5.4"))
        self.assertEqual(find(check("When the presk is fimp, glab the vorsk.\n"),
                              "STE-5.4"), [])

    def test_5_5_notes(self):
        self.assertTrue(find(check("NOTE: Glab the vorsk.\n"), "STE-5.5"))
        self.assertEqual(find(check("NOTE: The vorsk glabs slowly.\n"), "STE-5.5"), [])

    def test_6_6_paragraph(self):
        para = " ".join(["The vonk wirls."] * 7) + "\n"
        self.assertTrue(find(check(para), "STE-6.6"))
        self.assertEqual(find(check(" ".join(["The vonk wirls."] * 6)), "STE-6.6"), [])

    def test_7_safety(self):
        fs = check("WARNING: The skeen is whask.\n")
        self.assertTrue(find(fs, "STE-7.2"))
        self.assertTrue(find(fs, "STE-7.3"))
        fs = check("WARNING: Do not pront the skeen. The skeen can cause injury.\n")
        self.assertEqual(find(fs, "STE-7.2") + find(fs, "STE-7.3"), [])
        self.assertTrue(find(check("CAUTION: Do not skub the dorp.\n"), "STE-7.3"))
        self.assertTrue(find(check("DANGER: Do not pront the skeen. It can cause injury.\n"),
                             "STE-7.1"))
        self.assertTrue(find(check("CAUTION: Do not pront the skeen. It can cause injury.\n"),
                             "STE-7.1", "persons"))
        self.assertTrue(find(check("Do not pront the skeen because it can cause injury.\n"),
                             "STE-7.1", "without"))
        self.assertTrue(find(check("NOTE: The skeen can cause damage.\n"), "STE-7.1"))

    def test_8_1_semicolon(self):
        self.assertTrue(find(check("Glab the vorsk; trosk the flarn.\n"), "STE-8.1"))

    def test_9_3_phrasal_verbs(self):
        self.assertTrue(find(check("Plim up the dorp.\n"), "STE-9.3"))
        self.assertEqual(find(check("Dap on the gloves.\n"), "STE-9.3"), [])
        self.assertEqual(find(check("Take the part out of the box.\n", lex=None),
                              "STE-9.3"), [])

    def test_gr6_latin(self):
        fs = check("Use a tool, e.g. a clamp, i.e. a small tool, etc.\n", lex=None)
        self.assertEqual(len(find(fs, "STE-GR-6")), 3)

    def test_gr7_gender(self):
        self.assertTrue(find(check("The operator opens his cover.\n", lex=None), "STE-GR-7"))

    def test_first_person(self):
        self.assertTrue(find(check("I open the valve.\n", lex=None), "STE-X-FIRST-PERSON"))
        self.assertEqual(find(check("We supply the cable.\n", lex=None),
                              "STE-X-FIRST-PERSON"), [])

    def test_slash(self):
        self.assertTrue(find(check("Set the switch on/off.\n", lex=None), "STE-X-SLASH"))
        fs = check("Use the A/B switch. The leak is 2 cc/hour.\n", lex=None)
        self.assertEqual(find(fs, "STE-X-SLASH"), [])

    def test_catalogue_ids(self):
        for f in check("Glab the vorsk; trosk it, e.g. now. He did.\n"):
            self.assertIn(f.rule, sc.RULES)
        numbered = [r for r in sc.RULES if r[4:5].isdigit()]
        self.assertEqual(len(numbered), 53)


# An invented term list in the table layout (no content from the specification).
TABLE_TERMS = """# Names for the parts of the Zeta-9 unit

This list gives the names for the parts of the unit. Use only these names.

## Technical nouns

| Technical noun | Definition | Do not use |
|---|---|---|
| sump | The tray below the unit that collects oil | drip tray, basin |
| kronk handle | The handle that turns the shaft | - |
| QXR | Quick xfer relay. The relay that sends the data | — |

## Technical verbs

| Technical verb | Definition |
|---|---|
| reflash | To write new firmware to the controller |
"""


class TermListTableTests(unittest.TestCase):
    def setUp(self):
        self.tl = terms(TABLE_TERMS)

    def test_table_columns_by_header_name(self):
        tl = self.tl
        self.assertEqual(tl.single.get("sump"), "TN")
        self.assertEqual(tl.single.get("qxr"), "TN")
        self.assertEqual(tl.single.get("reflash"), "TV")
        self.assertIn((("kronk", "handle"), "TN"), tl.multi["kronk"])
        self.assertEqual(tl.avoid_single, {"basin": "sump"})
        self.assertEqual(tl.avoid_multi["drip"], [(("drip", "tray"), "sump")])
        # Header cells, "-" cells, and the introduction are not terms.
        for w in ("technical", "definition", "-", "this", "do"):
            self.assertNotIn(w, tl.single)
            self.assertNotIn(w, tl.multi)
        self.assertTrue(tl.definitions["qxr"].startswith("Quick xfer relay"))

    def test_generic_term_header_under_a_verb_heading(self):
        tl = terms("## Technical verbs\n\n| Term | Definition |\n|---|---|\n"
                   "| reflash | To write firmware |\n")
        self.assertEqual(tl.single["reflash"], "TV")

    def test_line_layout_with_do_not_use(self):
        tl = terms("- sump (TN): the oil tray. Do not use: basin, drip tray\n")
        self.assertEqual(tl.single["sump"], "TN")
        self.assertEqual(tl.avoid_single["basin"], "sump")
        self.assertIn((("drip", "tray"), "sump"), tl.avoid_multi["drip"])

    def test_terms_suppress_unlisted_and_part_of_speech_findings(self):
        fs = check("Wemble the sumps. Wirl the kronk handles. You must reflash the moderon.\n",
                   terms=self.tl)
        self.assertEqual([f for f in fs if f.rule in ("STE-1.1", "STE-1.2", "STE-1.6",
                                                      "STE-1.7", "STE-1.13")], [])

    def test_do_not_use_words_give_1_11(self):
        fs = check("Dap the basin below the dorp. Vakk the drip trays.\n", terms=self.tl)
        f = find(fs, "STE-1.11")
        self.assertEqual(len(f), 2)
        self.assertEqual(f[0].severity, "warn")
        self.assertIn("use 'sump' instead", f[0].message)
        self.assertIn("'drip trays'", f[1].message)
        self.assertEqual(find(fs, "STE-1.6"), [])
        self.assertIn("STE-1.11", sc.RULES)
        self.assertTrue(sc.RULES["STE-1.11"]["checked"])


class ProbableNounTests(unittest.TestCase):
    """Unapproved verb (or adjective) entries that are used as nouns."""

    def test_bare_object_of_a_command_is_a_noun_and_needs_an_article(self):
        fs = check("Snarb kronk from the dorp.\n")
        self.assertEqual(find(fs, "STE-1.1"), [])
        self.assertTrue(find(fs, "STE-1.6", "'kronk'"))
        self.assertTrue(find(fs, "STE-4.5", "'kronk'"))

    def test_bare_nouns_after_command_and_preposition(self):
        fs = check("Snarb kronk from sump.\n", terms=terms("sump (TN)\n"))
        self.assertEqual(find(fs, "STE-1.1"), [])
        arts = [f.message for f in find(fs, "STE-4.5")]
        self.assertTrue(any("'kronk'" in m for m in arts))
        self.assertTrue(any("'sump'" in m for m in arts))

    def test_noun_after_adjective_and_determiner(self):
        fs = check("Attach the grask zelk.\n")
        self.assertEqual(find(fs, "STE-1.1"), [])
        self.assertTrue(find(fs, "STE-1.6", "'zelk'"))

    def test_verb_use_stays_unapproved(self):
        self.assertTrue(find(check("Kronk the shaft.\n"), "STE-1.1", "'Kronk'"))
        self.assertTrue(find(check("The blaxor must zelk the dorp.\n"), "STE-1.1",
                             "'zelk'"))

    def test_adjective_entry(self):
        self.assertTrue(find(check("Quisk the spurl glimmet.\n"), "STE-1.1", "'spurl'"))
        fs = check("Snarb the spurl.\n")
        self.assertEqual(find(fs, "STE-1.1"), [])
        self.assertTrue(find(fs, "STE-1.6", "'spurl'"))

    def test_one_vocabulary_finding_per_token(self):
        for text in ("Snarb kronk from the dorp.\n", "Attach the grask zelk.\n",
                     "Tosk the vorsk.\n", "It is vorbary to frobnicate the plimsade.\n"):
            seen = {}
            for f in check(text):
                if f.rule in sc.VOCAB_PRIORITY:
                    seen.setdefault((f.line, f.col), []).append(f.rule)
            for rules_at in seen.values():
                self.assertEqual(len(set(rules_at)), 1, (text, rules_at))
        a = sc.Finding("x", 1, 5, "info", "STE-1.6", "m")
        b = sc.Finding("x", 1, 5, "warn", "STE-1.1", "m")
        c = sc.Finding("x", 1, 5, "info", "STE-4.5", "m")
        self.assertEqual(sc.one_vocabulary_finding_per_token([a, b, c]), [b, c])


class NoiseTests(unittest.TestCase):
    def test_1_6_groups_by_word_across_files_and_plurals(self):
        fs = check("Snarb the gasket. Wemble the gaskets.\n") + \
            sc.check_text("Quisk a gasket.\n\nSnarb the gasket.\n", "md", "u.md", LEX,
                          None)
        fs += sc.check_text(" ".join("Wemble gasket %d." % n for n in range(4)) + "\n", "md",
                            "v.md", LEX, None)
        g = find(sc.group_findings(fs), "STE-1.6", "gasket")
        self.assertEqual(len(g), 1)
        self.assertEqual(len(g[0].locations), 8)
        d = g[0].as_dict()
        self.assertEqual(d["count"], 8)
        self.assertEqual(len(d["locations"]), 5)
        self.assertIn("8 occurrences", sc.format_text(g[0]))
        self.assertIn("+3 more", sc.format_text(g[0]))

    def test_unknown_words_list(self):
        fs = check("Snarb the gasket. Wemble the gaskets. You must defrag the dorp. "
                   "You can defrag it.\n")
        rows = {r["word"]: r for r in sc.unknown_words(sc.group_findings(fs))}
        self.assertEqual(rows["gasket"]["count"], 2)
        self.assertEqual(rows["gasket"]["tag"], "TN")
        self.assertEqual(rows["defrag"]["tag"], "TV")


class AbbreviationTermListTests(unittest.TestCase):
    def setUp(self):
        self.tl = terms(TABLE_TERMS)

    def test_term_list_abbreviation_before_its_definition(self):
        fs = check("Restart the QXR. The quick xfer relay (QXR) sprocks dax.\n",
                   terms=self.tl)
        f = find(fs, "STE-2.2", "before its definition")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, "warn")
        self.assertEqual(f[0].col, 13)

    def test_term_list_is_not_a_definition_in_the_document(self):
        fs = check("Restart the QXR.\n", terms=self.tl)
        f = find(fs, "STE-2.2", "no definition in this document")
        self.assertEqual(len(f), 1)
        self.assertIn("Quick xfer relay", f[0].suggestion)
        ok = "The quick xfer relay (QXR) sprocks dax. Restart the QXR.\n"
        self.assertEqual(find(check(ok, terms=self.tl), "STE-2.2"), [])


class AuditFixTests(unittest.TestCase):
    """False positives and false negatives found by a blind audit (checker 2.2.0).
    All sentences, names, and dictionary rows here are invented."""

    # -- false positives
    def test_product_name_with_article_is_not_4_5(self):
        fs = check("The Zorbex QX-7 is a pomble. Connect the Zorbex QX-7 to the dorp.\n")
        self.assertEqual(find(fs, "STE-4.5"), [])
        # A common noun with an identifier still gets the finding.
        self.assertTrue(find(check("Glab the vorsk V12.\n"), "STE-4.5", "identifier"))

    def test_tn_alternative_in_dictionary_is_not_unapproved(self):
        # 'zeffle' (v) is not approved; its alternative 'zeffling' is a TN.
        for text in ("# Zeffling\n", "- [Zeffling](d.md): The steps for the dorp\n",
                     "Do the zeffling of the dorp.\n"):
            fs = check(text)
            self.assertEqual(find(fs, "STE-1.1") + find(fs, "STE-3.5"), [], text)
        # The verb use stays unapproved.
        self.assertTrue(find(check("Zeffle the dorp.\n"), "STE-1.1", "Zeffle"))
        # A noun that is itself not approved stays STE-1.1, with the approved
        # alternative first.
        f = find(check("Record the blorf.\n"), "STE-1.1")
        self.assertEqual([x.severity for x in f], ["warn"])
        self.assertTrue(f[0].suggestion.startswith("Approved alternatives: IF … NOT"))
        # The -s form of the verb after a noun is a verb, not the TN plural.
        self.assertTrue(find(check("The handle glurps the vonk.\n"), "STE-1.1", "glurps"))
        self.assertEqual(find(check("Dap the glurps in the box.\n"), "STE-1.1"), [])

    def test_4_5_not_in_list_fragments(self):
        text = "Wuggets:\n\n- Hex key, 4 mm to 8 mm\n- Gronk kit, 2 each\n"
        self.assertEqual(find(check(text), "STE-4.5"), [])
        # A step with a verb still gets the finding.
        self.assertTrue(find(check("1. Snarb flarn.\n"), "STE-4.5"))

    def test_point_up_as_direction_is_not_phrasal(self):
        for text in ("Quisk the lid. The tab must point up.\n",
                     "Fleem kest that the tab points down.\n"):
            self.assertEqual(find(check(text), "STE-9.3"), [], text)
        self.assertTrue(find(check("Plim up the dorp.\n"), "STE-9.3"))

    def test_2_1_leading_adjective_is_not_counted(self):
        tl = terms("inlet flow probe (TN)\n")
        fs = check("Quisk a nuv inlet flow probe.\n", terms=tl)
        self.assertEqual(find(fs, "STE-2.1"), [])
        fs = check("Snarb the olp pomble motch vonk cobbet.\n")
        f = find(fs, "STE-2.1")
        self.assertEqual(len(f), 1)
        self.assertIn("'pomble motch vonk cobbet'", f[0].message)

    def test_term_definition_expansion_is_not_reported(self):
        tl = terms("| Technical noun | Definition |\n|---|---|\n"
                   "| SSPP | Spurl starting pomble presk. The presk for a restart |\n")
        text = "The spurl starting pomble presk (SSPP) of the dorp is 20 MPa.\n"
        before = [f.rule for f in check(text)]
        self.assertIn("STE-1.1", before)
        self.assertIn("STE-3.5", before)
        fs = check(text, terms=tl)
        self.assertEqual([f for f in fs if f.rule in ("STE-1.1", "STE-3.5", "STE-2.1",
                                                      "STE-1.6")], [])

    def test_stative_participle_is_not_passive(self):
        for text in ("The vorsk is closed.\n", "| Cause |\n|---|\n| The vorsk is closed. |\n",
                     "The frosh tamb is brimp.\n"):
            self.assertEqual(find(check(text), "STE-3.6"), [], text)
        # An action with 'then', or with an agent, is still passive.
        self.assertTrue(find(check("1. The flarn is then snarbed.\n"), "STE-3.6"))
        self.assertTrue(find(check("The vorsk is closed by the moderon.\n"), "STE-3.6"))

    def test_ing_technical_noun_after_determiner(self):
        for text in ("Replace the flonched snibbing.\n", "Dap a gronk on a snibbing.\n",
                     "Wemble the three snibbings.\n"):
            self.assertEqual(find(check(text), "STE-3.5"), [], text)
        self.assertTrue(find(check("After snibbing the flarn, wemble the dorp.\n"), "STE-3.5"))

    def test_1_6_message_for_unapproved_verb_used_as_noun(self):
        f = find(check("Snarb kronk from the dorp.\n"), "STE-1.6", "'kronk'")
        self.assertEqual(len(f), 1)
        self.assertIn("only as a verb that is not approved", f[0].message)
        self.assertIn("possible technical noun", f[0].message)
        self.assertNotIn("(only as a verb)", f[0].message)

    # -- false negatives
    def test_must_statement_in_a_step_is_5_3(self):
        fs = check("1. Quisk the lid; the tab must point down.\n")
        self.assertTrue(find(fs, "STE-5.3"))
        fs = check("1. The blaxor should glab the vorsk.\n")
        self.assertTrue(find(fs, "STE-5.3"))
        self.assertTrue(find(fs, "STE-1.1", "should"))
        # A reason clause is not a separate instruction.
        fs = check("1. Wirl the knob because the vonk must halp first.\n")
        self.assertEqual(find(fs, "STE-5.3"), [])

    def test_you_should_wear_is_a_safety_hint(self):
        fs = check("You should wear gloves when you pront the skeen.\n")
        f = find(fs, "STE-7.1")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, "info")
        self.assertEqual(find(check("WARNING: WEAR GLOVES. THE SKEEN CAN CAUSE INJURY.\n"),
                              "STE-7.1"), [])

    def test_variant_of_term_list_noun(self):
        tl = terms("inlet flow probe (TN)\n")
        fs = check("Unplob the vonk inlet flow probe.\n", terms=tl)
        f = find(fs, "STE-1.11", "variant")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, "info")
        self.assertIn("'inlet flow probe'", f[0].message)
        fs = check("Unplob the inlet flow probe.\n", terms=tl)
        self.assertEqual(find(fs, "STE-1.11"), [])
        fs = check("Unplob the nuv inlet flow probe.\n", terms=tl)
        self.assertEqual(find(fs, "STE-1.11"), [])

    def test_unknown_words_include_letter_hyphen_words(self):
        fs = sc.group_findings(check("Flurge the brelled O-ring and the V-belt.\n"))
        rows = [r["word"] for r in sc.unknown_words(fs)]
        self.assertIn("O-ring", rows)
        self.assertIn("V-belt", rows)

    def test_last_list_item_without_period(self):
        text = "Do these steps:\n\n1. Glab the vorsk.\n2. Trosk the flarn\n"
        f = find(check(text), "STE-4.3", "last item")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, "info")
        # A list of names (no verbs) needs no period.
        text = "The dorp has these pakes:\n\n- The pomble\n- The motch\n"
        self.assertEqual(find(check(text), "STE-4.3"), [])

    def test_suggestions_prefer_approved_words(self):
        f = find(check("Spirn the knob.\n"), "STE-1.1", "Spirn")
        self.assertTrue(f[0].suggestion.startswith("Approved alternatives: WIRL (v)"),
                        f[0].suggestion)
        # 'zarvolise' is a British-style -ise spelling of the invented 'zarvolize',
        # which the fixture lists only as a verb that is not approved (and a TN).
        f = find(check("Dap the pake in the zarvolise of the dorp.\n"), "STE-1.14")
        self.assertNotIn("Write 'zarvolize'.", f[0].suggestion)
        self.assertIn("QUENNEL (n)", f[0].suggestion)
        # An approved American spelling, or a term-list noun, is still suggested.
        f = find(check("Brell the grovyse glimmet.\n"), "STE-1.14")
        self.assertEqual(f[0].suggestion, "Write 'grovyze'.")
        f = find(check("Dap the pake in the zarvolise.\n",
                       terms=terms("zarvolize (TN)\n")), "STE-1.14")
        self.assertEqual(f[0].suggestion, "Write 'zarvolize'.")


class CLITests(unittest.TestCase):
    def run_cli(self, *args, stdin=None):
        p = subprocess.run([sys.executable, SCRIPT] + list(args), input=stdin,
                           capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def test_help_and_version(self):
        code, out, _ = self.run_cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("usage:", out)
        self.assertIn("--dictionary", out)
        code, out, _ = self.run_cli("--version")
        self.assertEqual(code, 0)
        self.assertIn(sc.VERSION, out)

    def test_no_paths_is_usage_error(self):
        code, _, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("usage", err)

    def test_list_rules(self):
        code, out, _ = self.run_cli("--list-rules")
        self.assertEqual(code, 0)
        self.assertIn("STE-5.1", out)
        self.assertIn("STE-GR-6", out)
        code, out, _ = self.run_cli("--list-rules", "--json")
        data = json.loads(out)
        self.assertEqual(set(data[0]), {"id", "title", "judgment", "needs_dictionary",
                                        "checked"})
        by_id = {r["id"]: r for r in data}
        for rid, judgment, checked in (("STE-1.4", "objective", True),
                                       ("STE-3.1", "objective", False),
                                       ("STE-1.11", "objective", True),
                                       ("STE-1.14", "objective", True),
                                       ("STE-3.3", "heuristic", False)):
            self.assertEqual((by_id[rid]["judgment"], by_id[rid]["checked"]),
                             (judgment, checked), rid)

    def test_text_output_format_and_exit_codes(self):
        bad = self.write("bad.md", "Glab the vorsk; trosk it.\n")
        code, out, _ = self.run_cli("--dictionary", FIXTURE, bad)
        self.assertEqual(code, 1)
        self.assertRegex(out, r"bad\.md:1:15 WARN STE-8\.1 semicolon")
        self.assertIn("    suggestion:", out)
        good = self.write("good.md", "Glab the vorsk.\n")
        code, out, _ = self.run_cli("--dictionary", FIXTURE, good)
        self.assertEqual(code, 0, out)

    def test_json_output(self):
        p = self.write("a.md", "Glab the vorsk; trosk it. Snarb the gasket.\n")
        code, out, _ = self.run_cli("--dictionary", FIXTURE, "--json", p)
        data = json.loads(out)
        self.assertEqual(set(data), {"meta", "summary", "findings"})
        self.assertTrue(data["meta"]["dictionary"]["loaded"])
        self.assertEqual(data["summary"]["files"], 1)
        f = data["findings"][0]
        for key in ("file", "line", "col", "severity", "rule", "message", "suggestion",
                    "count", "locations"):
            self.assertIn(key, f)

    def test_min_severity(self):
        p = self.write("a.md", "Snarb the gasket.\n")
        _, out, _ = self.run_cli("--dictionary", FIXTURE, p)
        self.assertIn("STE-1.6", out)
        code, out, _ = self.run_cli("--dictionary", FIXTURE, "--min-severity", "warn", p)
        self.assertNotIn("STE-1.6", out)
        self.assertEqual(code, 0)

    def test_missing_dictionary_gives_one_info_and_continues(self):
        p = self.write("a.md", "Open the valve; close it.\n")
        env = dict(os.environ, STE100_DICTIONARY=os.path.join(self.dir, "none.json"))
        proc = subprocess.run([sys.executable, SCRIPT, p], capture_output=True, text=True,
                              env=env)
        self.assertEqual(proc.stdout.count("STE-X-NODICT"), 1)
        self.assertIn("run tools/build_dictionary.py", proc.stdout)
        self.assertIn("STE-8.1", proc.stdout)
        self.assertEqual(proc.returncode, 1)

    def test_explicit_bad_dictionary_path_is_error(self):
        p = self.write("a.md", "Open the valve.\n")
        code, _, err = self.run_cli("--dictionary", os.path.join(self.dir, "x.json"), p)
        self.assertEqual(code, 2)
        self.assertIn("not found", err)

    def test_directory_walk_skips_code_and_hidden(self):
        self.write("docs/a.md", "Glab the vorsk; trosk it.\n")
        self.write("docs/b.rst", "Glab the vorsk; trosk it.\n")
        self.write("docs/c.py", "x = 1; y = 2\n")
        self.write("docs/.hidden/d.md", "a; b\n")
        self.write("docs/node_modules/e.md", "a; b\n")
        code, out, _ = self.run_cli("--dictionary", FIXTURE, "--json",
                                    os.path.join(self.dir, "docs"))
        files = [os.path.basename(f) for f in json.loads(out)["meta"]["files"]]
        self.assertEqual(files, ["a.md", "b.rst"])

    def test_explicit_code_file_is_skipped(self):
        p = self.write("c.py", "x = 1; y = 2\n")
        code, _, err = self.run_cli("--dictionary", FIXTURE, p)
        self.assertIn("skipped", err)
        self.assertEqual(code, 2)

    def test_terms_option_and_default_discovery(self):
        p = self.write("proj/a.md", "Snarb the gasket.\n")
        tl = self.write("proj/DOCS_TERMS.md", "gasket (TN) - a seal ring\n")
        _, out, _ = self.run_cli("--dictionary", FIXTURE, "--terms", tl, p)
        self.assertNotIn("gasket", out)
        _, out, _ = self.run_cli("--dictionary", FIXTURE, p)
        self.assertNotIn("gasket", out)

    def test_term_list_file_is_never_checked(self):
        self.write("proj/docs/a.md", "Dap the basin below the dorp.\n")
        self.write("proj/DOCS_TERMS.md", TABLE_TERMS + "\nThis line has a semicolon; here.\n")
        code, out, err = self.run_cli("--dictionary", FIXTURE, "--json",
                                      os.path.join(self.dir, "proj"))
        data = json.loads(out)
        files = [os.path.basename(f) for f in data["meta"]["files"]]
        self.assertNotIn("DOCS_TERMS.md", files)
        self.assertEqual([os.path.basename(f) for f in data["meta"]["skipped"]],
                         ["DOCS_TERMS.md"])
        self.assertIn("not checked (term list", err)
        self.assertNotIn("STE-8.1", data["summary"]["by_rule"])
        self.assertEqual(data["summary"]["by_rule"].get("STE-1.11"), 1)
        # A term list named with --terms is not checked either.
        custom = self.write("proj/names.md", "- sump (TN): the tray. Do not use: basin\n")
        code, out, _ = self.run_cli("--dictionary", FIXTURE, "--json", "--terms", custom,
                                    os.path.join(self.dir, "proj"))
        files = [os.path.basename(f) for f in json.loads(out)["meta"]["files"]]
        self.assertNotIn("names.md", files)
        code, out, _ = self.run_cli("--help")
        self.assertIn("never checked as prose", " ".join(out.split()))
        self.assertIn("Do not use", out)

    def test_unknown_words_option(self):
        p = self.write("a.md", "Snarb the gasket. Wemble the gaskets. Glab the vorsk; trosk "
                               "it.\n")
        code, out, _ = self.run_cli("--dictionary", FIXTURE, "--unknown-words", p)
        self.assertEqual(code, 0)
        self.assertIn("gasket (TN)  # 2 use(s)", out)
        self.assertNotIn("STE-8.1", out)
        code, out, _ = self.run_cli("--dictionary", FIXTURE, "--unknown-words", "--json", p)
        rows = json.loads(out)
        self.assertEqual(rows[0]["word"], "gasket")
        self.assertEqual(rows[0]["count"], 2)
        code, out, _ = self.run_cli("--help")
        self.assertIn("--unknown-words", out)

    def test_stdin(self):
        code, out, _ = self.run_cli("--dictionary", FIXTURE, "-",
                                    stdin="Glab the vorsk; trosk it.\n")
        self.assertIn("-:1:15 WARN STE-8.1", out)


@unittest.skipUnless(os.path.isfile(REAL_CACHE), "real dictionary cache not built")
class ModalQuestionCrashTests(unittest.TestCase):
    """Regression: a sentence starting with a capitalised modal plus a word
    used to raise TypeError (tuple | set) in the -ing/verb heuristics."""

    def test_capitalised_modal_questions_do_not_crash(self):
        import io, contextlib
        for text in ("Can you open it?\n", "Must the lid stay shut?\n",
                     "Will the fan stop?\n", "May we close it?\n",
                     "Should the lamp glow?\n"):
            with self.subTest(text=text):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    old = sys.stdin
                    sys.stdin = io.StringIO(text)
                    try:
                        rc = sc.main(["-", "--min-severity", "info"])
                    finally:
                        sys.stdin = old
                self.assertIn(rc, (0, 1))


@unittest.skipUnless(os.path.isfile(REAL_CACHE), "real dictionary cache not built")
class RealCacheTests(unittest.TestCase):
    def test_real_cache_loads_and_checks(self):
        lex = sc.Lexicon.load(REAL_CACHE)
        self.assertGreater(len(lex.forms), 1000)
        # Take a not-approved one-word verb from the cache itself, so that this
        # file names no word of the real dictionary.
        with open(REAL_CACHE, encoding="utf-8") as fh:
            entries = json.load(fh)["entries"]
        word = next(e["word"] for e in entries
                    if e.get("pos") == "v" and not e.get("approved")
                    and str(e.get("word", "")).isalpha()
                    and not any(r.get("approved") for r in lex.lookup(e["word"])))
        fs = check("You must %s the item.\n" % word, lex=lex)
        self.assertTrue(find(fs, "STE-1.1", "'%s'" % word), word)


if __name__ == "__main__":
    unittest.main()
