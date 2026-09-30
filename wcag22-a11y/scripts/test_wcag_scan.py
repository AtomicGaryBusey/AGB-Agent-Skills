#!/usr/bin/env python3
"""Tests for wcag_scan.py (stdlib unittest). Run: python3 scripts/test_wcag_scan.py"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wcag_scan as ws  # noqa: E402

SCRIPT = os.path.join(HERE, "wcag_scan.py")
FIX = os.path.join(HERE, "fixtures")


def scan_text(text, ext=".html", level="AAA", extra=None):
    """Write text to a temp file (plus optional extra files) and scan the directory."""
    d = tempfile.mkdtemp(prefix="wcagscan")
    try:
        with open(os.path.join(d, "t" + ext), "w", encoding="utf-8") as fh:
            fh.write(text)
        for name, body in (extra or {}).items():
            with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        findings, _files, _errors = ws.scan([d], level=level)
        return findings
    finally:
        shutil.rmtree(d)


def rules_of(findings):
    return {f["rule"] for f in findings}


def page(body, head="<title>T</title>", lang=' lang="en"'):
    return "<!DOCTYPE html>\n<html%s>\n<head>%s</head>\n<body>\n<main>\n%s\n</main>\n</body>\n</html>\n" % (lang, head, body)


def jsx(markup):
    return "export default function C() {\n  return (\n    <div>\n%s\n    </div>\n  );\n}\n" % markup


# (rule, ext, bad source, good source)
CASES = [
    # 1.1.1
    ("img-missing-alt", ".html", '<img src="a.png">', '<img src="a.png" alt="">'),
    ("img-alt-empty-in-control", ".html", '<a href="/"><img src="home.png" alt=""></a>', '<a href="/"><img src="home.png" alt="Home"></a>'),
    ("img-alt-suspicious", ".html", '<img src="a.png" alt="image">', '<img src="a.png" alt="Sunset over the bay">'),
    ("input-image-missing-alt", ".html", '<input type="image" src="go.png">', '<input type="image" src="go.png" alt="Search">'),
    ("area-missing-alt", ".html", '<map name="m"><area href="/a" shape="rect" coords="0,0,9,9"></map>', '<map name="m"><area href="/a" alt="About" shape="rect" coords="0,0,9,9"></map>'),
    ("svg-img-no-name", ".html", '<svg role="img"><path d="M0 0"/></svg>', '<svg role="img"><title>Sales chart</title><path d="M0 0"/></svg>'),
    ("button-icon-no-name", ".html", '<button><svg><path d="M0 0"/></svg></button>', '<button aria-label="Close"><svg aria-hidden="true"><path d="M0 0"/></svg></button>'),
    ("icon-button-component-no-name", ".jsx", jsx("<IconButton><DeleteIcon /></IconButton>"), jsx('<IconButton aria-label="Delete"><DeleteIcon /></IconButton>')),
    # 1.3.1
    ("control-no-label", ".html", '<input type="text" name="q">', '<label>Query <input type="text" name="q"></label>'),
    ("heading-skip", ".html", "<h1>A</h1><h3>B</h3>", "<h1>A</h1><h2>B</h2><h3>C</h3><h2>D</h2>"),
    ("table-no-th", ".html", "<table><tr><td>a</td><td>b</td></tr><tr><td>c</td><td>d</td></tr></table>",
     "<table><tr><th>a</th><th>b</th></tr><tr><td>c</td><td>d</td></tr></table>"),
    ("layout-table-with-th", ".html", '<table role="presentation"><tr><th>a</th></tr></table>', '<table role="presentation"><tr><td>a</td></tr></table>'),
    ("radio-group-no-fieldset", ".html",
     '<label><input type="radio" name="p" value="1"> A</label><label><input type="radio" name="p" value="2"> B</label>',
     '<fieldset><legend>Plan</legend><label><input type="radio" name="p" value="1"> A</label><label><input type="radio" name="p" value="2"> B</label></fieldset>'),
    ("li-outside-list", ".html", "<div><li>x</li></div>", "<ul><li>x</li></ul>"),
    ("required-asterisk-only", ".html", '<label for="a">Name *</label><input id="a">', '<label for="a">Name *</label><input id="a" required>'),
    # 1.3.5
    ("autocomplete-missing", ".html", '<label for="e">Email</label><input id="e" type="email">', '<label for="e">Email</label><input id="e" type="email" autocomplete="email">'),
    ("autocomplete-invalid", ".html", '<label for="e">Email</label><input id="e" autocomplete="emial">',
     '<label for="e">Email</label><input id="e" autocomplete="section-a shipping work email">'),
    # 1.4.x
    ("media-autoplay-audio", ".html", '<audio autoplay src="a.mp3"></audio>', '<video autoplay muted controls src="a.mp4"></video>'),
    ("contrast-text", ".css", ".a { color: #aaaaaa; background: #ffffff; }", ".a { color: #333333; background: #ffffff; }"),
    ("contrast-unresolved", ".css", ".a { color: var(--fg); background: #fff; }", ".a { color: var(--fg); }"),
    ("viewport-zoom-disabled", ".html", '<meta name="viewport" content="width=device-width, user-scalable=no">', '<meta name="viewport" content="width=device-width, initial-scale=1">'),
    ("fixed-width-no-max", ".css", ".a { width: 500px; }", ".a { width: 500px; max-width: 100%; }"),
    ("ui-border-contrast", ".css", "input { border: 1px solid #eeeeee; background-color: #ffffff; }", "input { border: 1px solid #767676; background-color: #ffffff; }"),
    ("focus-indicator-contrast", ".css", ".b:focus-visible { outline: 2px solid #eeeeee; background-color: #fff; }", ".b:focus-visible { outline: 2px solid #000000; background-color: #fff; }"),
    ("text-spacing-important", ".css", "p { line-height: 1 !important; }", "p { line-height: 1.5; }"),
    # 2.x
    ("click-no-keyboard", ".html", '<div onclick="go()">Go</div>', '<button type="button" onclick="go()">Go</button>'),
    ("meta-refresh-delay", ".html", '<meta http-equiv="refresh" content="5">', '<meta http-equiv="refresh" content="0; url=/new">'),
    ("marquee-blink", ".html", "<marquee>News</marquee>", "<p>News</p>"),
    ("media-autoplay-no-controls", ".html", '<video autoplay muted src="a.mp4"></video>', '<video autoplay muted controls src="a.mp4"></video>'),
    ("bypass-blocks-missing", ".html",
     '<!DOCTYPE html><html lang="en"><head><title>T</title></head><body><nav><a href="/">Home</a></nav><div>x</div></body></html>',
     '<!DOCTYPE html><html lang="en"><head><title>T</title></head><body><a href="#c">Skip to content</a><div id="c">x</div></body></html>'),
    ("page-title-missing", ".html", '<!DOCTYPE html><html lang="en"><head></head><body><main>x</main></body></html>', page("x")),
    ("tabindex-positive", ".html", '<button tabindex="2">A</button>', '<button tabindex="0">A</button>'),
    ("link-empty", ".html", '<a href="/x"></a>', '<a href="/x">Docs</a>'),
    ("link-icon-no-name", ".html", '<a href="/x"><svg><path d="M0 0"/></svg></a>', '<a href="/x" aria-label="Settings"><svg><path d="M0 0"/></svg></a>'),
    ("link-text-generic", ".html", '<a href="/x">Click here</a>', '<a href="/x">Pricing plans</a>'),
    ("heading-empty", ".html", "<h2></h2>", "<h2>Section</h2>"),
    ("focus-outline-removed", ".css", "a:focus { outline: none; }", "a:focus { outline: none; box-shadow: 0 0 0 3px #000; }"),
    ("focus-outline-removed-maybe", ".css", "button { outline: 0; }", ".card { outline: 0; }"),
    ("focus-obscured-check", ".css", ".h { position: sticky; top: 0; }", ".h { position: relative; }"),
    ("focus-obscured-enhanced-check", ".css", ".h { position: fixed; top: 0; }", ".h { position: static; }"),
    ("focus-appearance-check", ".css", "a:focus-visible { outline: 2px solid #000; }", "a { color: #000; }"),
    ("label-in-name", ".html", '<button aria-label="Close dialog">Cancel</button>', '<button aria-label="Cancel booking">Cancel</button>'),
    ("drag-no-alternative", ".html", '<div draggable="true">Card</div>', "<div>Card</div>"),
    ("drag-library-check", ".js", "import Sortable from 'sortablejs';\n", "import debounce from 'lodash/debounce';\n"),
    ("target-size-small", ".css", ".icon-btn { width: 16px; height: 16px; }", ".icon-btn { width: 24px; height: 24px; }"),
    # 3.x
    ("html-lang-missing", ".html", '<!DOCTYPE html><html><head><title>T</title></head><body><main>x</main></body></html>', page("x")),
    ("html-lang-invalid", ".html", page("x", lang=' lang="english"'), page("x", lang=' lang="en-GB"')),
    ("lang-invalid", ".html", '<p lang="en_US">Hi</p>', '<p lang="zh-Hant-TW">Hi</p>'),
    ("onchange-navigates", ".html", '<select aria-label="Page" onchange="this.form.submit()"><option>1</option></select>',
     '<select aria-label="Page" onchange="update(this.value)"><option>1</option></select>'),
    ("placeholder-only-label", ".html", '<input type="text" placeholder="Name">', '<input type="text" placeholder="Name" aria-label="Name">'),
    ("redundant-entry", ".html",
     '<form><input aria-label="E" autocomplete="email"></form><form><input aria-label="E2" autocomplete="email"></form>',
     '<form><input aria-label="E" autocomplete="email"></form><form><input aria-label="T" autocomplete="tel"></form>'),
    ("captcha-on-auth", ".html",
     '<form><input type="password" aria-label="Password" autocomplete="current-password"><div class="g-recaptcha"></div></form>',
     '<form><input type="search" aria-label="Search"><div class="g-recaptcha"></div></form>'),
    ("paste-blocked", ".html", '<input type="password" aria-label="Password" autocomplete="current-password" onpaste="return false">',
     '<input type="password" aria-label="Password" autocomplete="current-password">'),
    ("paste-blocked-maybe", ".html", '<input aria-label="Confirm e-mail" name="confirm" onpaste="return false">', '<input aria-label="Confirm e-mail" name="confirm">'),
    ("password-autocomplete-off", ".html", '<input type="password" aria-label="Password" autocomplete="off">', '<input type="password" aria-label="Password" autocomplete="new-password">'),
    # 4.1.x
    ("aria-role-invalid", ".html", '<div role="buton">x</div>', '<div role="button" tabindex="0" onkeydown="k()" onclick="c()">x</div>'),
    ("aria-attr-invalid", ".html", '<div aria-labeledby="x">y</div><p id="x">z</p>', '<div aria-labelledby="x">y</div><p id="x">z</p>'),
    ("aria-attr-value-invalid", ".html", '<div aria-hidden="yes">x</div>', '<div aria-hidden="true">x</div>'),
    ("aria-required-attr", ".html", '<div role="checkbox" tabindex="0" aria-label="A">x</div>', '<div role="checkbox" aria-checked="false" tabindex="0" aria-label="A">x</div>'),
    ("aria-hidden-focusable", ".html", '<a href="/" aria-hidden="true">x</a>', '<a href="/" aria-hidden="true" tabindex="-1">x</a>'),
    ("aria-idref-missing", ".html", page('<input aria-label="A" aria-describedby="nope">'), page('<input aria-label="A" aria-describedby="h"><p id="h">Hint</p>')),
    ("custom-control-no-name", ".html", '<div role="button" tabindex="0" onclick="c()" onkeydown="k()"></div>', '<div role="button" tabindex="0" onclick="c()" onkeydown="k()">Save</div>'),
    ("button-empty", ".html", "<button></button>", "<button>Save</button>"),
    ("click-handler-no-role", ".html", '<div tabindex="0" onclick="c()" onkeydown="k()">Go</div>', '<div role="button" tabindex="0" onclick="c()" onkeydown="k()">Go</div>'),
    ("focusable-no-role", ".html", '<div tabindex="0">x</div>', '<div tabindex="0" role="region" aria-label="Log">x</div>'),
    ("iframe-no-title", ".html", '<iframe src="/m"></iframe>', '<iframe src="/m" title="Map"></iframe>'),
    ("duplicate-id-referenced", ".html", '<label for="a">A</label><input id="a"><input id="a" aria-label="B">', '<label for="a">A</label><input id="a"><input id="b" aria-label="B">'),
    ("status-message-no-live", ".html", '<div class="toast">Saved</div>', '<div class="toast" role="status">Saved</div>'),
    ("status-message-js-no-live", ".html",
     page('<form id="f"><button>Add</button></form><p id="note"></p><script>document.getElementById("f").addEventListener("submit", function (e) {'
          ' e.preventDefault(); document.getElementById("note").textContent = "Item added to your list"; });</script>'),
     page('<form id="f"><button>Add</button></form><p id="note" role="status"></p><script>document.getElementById("f").addEventListener("submit", function (e) {'
          ' e.preventDefault(); document.getElementById("note").textContent = "Item added to your list"; });</script>')),
    # cross-file / script heuristics
    ("svg-icon-no-alt", ".html",
     '<table><tr><th>Wi-Fi</th></tr><tr><td><svg width="16" height="16"><path d="M0 0"/></svg></td></tr></table>',
     '<table><tr><th>Wi-Fi</th></tr><tr><td><svg width="16" height="16" aria-hidden="true"><path d="M0 0"/></svg> Yes</td></tr></table>'),
    ("color-only-reference", ".html",
     '<style>.late { color: #b00020; }</style><p>Overdue loans are shown in red.</p>',
     '<style>.late { color: #b00020; }</style><p>Overdue loans are marked "Overdue".</p>'),
    ("hover-content-no-dismiss", ".vue",
     '<template><div><span tabindex="0" role="button" aria-label="Info" @mouseenter="tip = true" @mouseleave="tip = false">i</span>'
     '<p v-show="tip">Prices include tax.</p></div></template>',
     '<template><div @mouseenter="tip = true" @mouseleave="tip = false" @keydown.esc="tip = false">'
     '<button type="button" aria-label="Info">i</button><p v-show="tip">Prices include tax.</p></div></template>'),
    ("error-not-described", ".html",
     '<label for="e">Email</label><input id="e" type="email"><script>document.getElementById("e").addEventListener("blur", function (ev) {'
     ' if (!ev.target.value) { ev.target.setAttribute("aria-invalid", "true"); } });</script>',
     '<label for="e">Email</label><input id="e" type="email" aria-describedby="e-err"><p id="e-err"></p><script>document.getElementById("e").addEventListener("blur", function (ev) {'
     ' if (!ev.target.value) { ev.target.setAttribute("aria-invalid", "true"); document.getElementById("e-err").textContent = "Enter an email address"; } });</script>'),
    ("aria-state-not-updated", ".html",
     '<button type="button" id="b" aria-pressed="false">Bold</button><script>document.getElementById("b").addEventListener("click", function () {'
     ' this.classList.toggle("on"); });</script>',
     '<button type="button" id="b" aria-pressed="false">Bold</button><script>document.getElementById("b").addEventListener("click", function () {'
     ' var on = this.classList.toggle("on"); this.setAttribute("aria-pressed", String(on)); });</script>'),
    ("redundant-entry-same-step", ".html",
     '<form><label for="e">Email</label><input id="e" autocomplete="email"><label for="c">Confirm email</label><input id="c"></form>',
     '<form><label for="e">Email</label><input id="e" autocomplete="email"><label for="p">Password</label><input id="p" type="password"></form>'),
]


class RuleCases(unittest.TestCase):
    def test_every_rule_has_a_case(self):
        covered = {c[0] for c in CASES}
        self.assertEqual(set(ws.RULES) - covered, set(), "rules without a positive/negative test case")

    def test_rule_registry_consistency(self):
        for slug, (sc, sev, desc) in ws.RULES.items():
            self.assertIn(sc, ws.SC, slug)
            self.assertIn(sev, ws.SEVERITY_RANK, slug)
            self.assertTrue(desc)

    def test_cases(self):
        for rule, ext, bad, good in CASES:
            with self.subTest(rule=rule, kind="positive"):
                found = scan_text(bad, ext)
                self.assertIn(rule, rules_of(found), "expected %s in %r; got %s" % (rule, bad, sorted(rules_of(found))))
                f = next(x for x in found if x["rule"] == rule)
                self.assertEqual(f["sc"], ws.RULES[rule][0])
                self.assertEqual(f["id"], "WCAG-" + ws.RULES[rule][0])
                self.assertGreaterEqual(f["line"], 1)
                self.assertGreaterEqual(f["col"], 1)
            with self.subTest(rule=rule, kind="negative"):
                found = scan_text(good, ext)
                self.assertNotIn(rule, rules_of(found), "unexpected %s in %r" % (rule, good))


class FindingShape(unittest.TestCase):
    KEYS = {"tool", "sc", "level", "rule", "severity", "file", "line", "col", "selector",
            "snippet", "message", "help", "evidence"}

    def test_contract_keys(self):
        found = scan_text('<img src="a.png">')
        self.assertTrue(found)
        f = found[0]
        self.assertTrue(self.KEYS <= set(f), self.KEYS - set(f))
        self.assertEqual(f["tool"], "wcag_scan")
        self.assertEqual(f["level"], "A")
        self.assertEqual(f["severity"], "fail")
        self.assertTrue(f["help"].startswith("https://www.w3.org/WAI/WCAG22/Understanding/non-text-content"))
        self.assertEqual(f["selector"], "img")
        self.assertIn("<img", f["snippet"])

    def test_position_is_exact(self):
        found = scan_text('<p>x</p>\n  <p>\n    <img src="a.png"></p>')
        f = [x for x in found if x["rule"] == "img-missing-alt"][0]
        self.assertEqual((f["line"], f["col"]), (3, 5))


class JSXParsing(unittest.TestCase):
    def test_generic_arrow_and_comparisons_are_not_jsx(self):
        src = ("const id = <T,>(x: T) => x;\n"
               "function f<T>(a: number, b: number) { return a < b && b > 0; }\n"
               "const s = useState<boolean>(false);\n"
               "export const C = () => <img src=\"x.png\" />;\n")
        found = scan_text(src, ".tsx")
        imgs = [f for f in found if f["rule"] == "img-missing-alt"]
        self.assertEqual(len(imgs), 1)
        self.assertEqual(imgs[0]["line"], 4)

    def test_strings_regex_and_comments_hide_markup(self):
        src = ("const a = '<img src=\"a.png\">';\n"
               "const b = /<img src=\"b.png\">/g;\n"
               "// <img src=\"c.png\">\n"
               "/* <img src=\"d.png\"> */\n"
               "const t = `<img src=\"e.png\">`;\n")
        self.assertNotIn("img-missing-alt", rules_of(scan_text(src, ".jsx")))

    def test_template_literal_expression_can_hold_jsx(self):
        src = "const t = `${<img src=\"a.png\" />}`;\n"
        self.assertIn("img-missing-alt", rules_of(scan_text(src, ".jsx")))

    def test_classname_htmlfor_and_handlers_normalise(self):
        src = jsx('<label htmlFor="n">Name</label><input id="n" autoComplete="name" />\n'
                  '<span className="toast" onClick={() => go()}>Hi</span>')
        found = scan_text(src, ".jsx")
        r = rules_of(found)
        self.assertNotIn("control-no-label", r)
        self.assertIn("status-message-no-live", r)
        self.assertIn("click-no-keyboard", r)

    def test_spread_props_suppress_missing_name_findings(self):
        src = jsx("<img {...props} />\n<button {...rest} />\n<a href=\"/x\" {...p}></a>")
        r = rules_of(scan_text(src, ".jsx"))
        self.assertFalse(r & {"img-missing-alt", "button-empty", "link-empty"}, r)

    def test_dynamic_values_are_not_guessed(self):
        src = jsx("<img src={src} alt={alt} />\n<button>{label}</button>\n<a href={url}>{text}</a>\n"
                  "<h2>{title}</h2>\n<html lang={locale}></html>")
        r = rules_of(scan_text(src, ".jsx"))
        self.assertFalse(r & {"img-missing-alt", "button-empty", "link-empty", "heading-empty", "html-lang-missing"}, r)

    def test_literal_expressions_are_static(self):
        src = jsx('<img src="a.png" alt={""} />\n<a href="/" aria-hidden={true}>x</a>\n<div tabIndex={3}>x</div>')
        r = rules_of(scan_text(src, ".jsx"))
        self.assertIn("aria-hidden-focusable", r)
        self.assertIn("tabindex-positive", r)
        self.assertNotIn("img-missing-alt", r)

    def test_fragments_members_and_attr_jsx(self):
        src = ("export const C = () => (\n  <>\n    <Foo.Bar icon={<svg />}>\n      <img src=\"a.png\" />\n"
               "    </Foo.Bar>\n  </>\n);\n")
        found = scan_text(src, ".tsx")
        self.assertIn("img-missing-alt", rules_of(found))
        self.assertEqual([f["line"] for f in found if f["rule"] == "img-missing-alt"], [4])

    def test_conditional_and_map(self):
        src = jsx("{open && <img src=\"a.png\" />}\n<ul>{items.map(i => <li key={i}>{i}</li>)}</ul>")
        r = rules_of(scan_text(src, ".jsx"))
        self.assertIn("img-missing-alt", r)
        self.assertNotIn("li-outside-list", r)

    def test_component_root_li_is_not_flagged(self):
        src = "export const Item = ({ t }) => <li>{t}</li>;\n"
        self.assertNotIn("li-outside-list", rules_of(scan_text(src, ".jsx")))

    def test_link_components_are_links(self):
        src = jsx("<Link href=\"/x\"><SettingsIcon /></Link>")
        self.assertIn("link-icon-no-name", rules_of(scan_text(src, ".jsx")))

    def test_unknown_components_hide_content(self):
        src = jsx("<button><Trans id=\"save\" /></button>")
        self.assertNotIn("button-empty", rules_of(scan_text(src, ".jsx")))

    def test_style_object_contrast(self):
        src = jsx("<p style={{ color: '#aaa', backgroundColor: '#fff', fontSize: 14 }}>x</p>")
        f = [x for x in scan_text(src, ".jsx") if x["rule"] == "contrast-text"]
        self.assertTrue(f)
        self.assertEqual(f[0]["severity"], "fail")

    def test_next_viewport_export(self):
        src = "export const viewport = { width: 'device-width', maximumScale: 1, userScalable: false };\n"
        self.assertIn("viewport-zoom-disabled", rules_of(scan_text(src, ".tsx")))

    def test_paste_blocked_via_script(self):
        src = "el.addEventListener('paste', (e) => { e.preventDefault(); });\n"
        self.assertIn("paste-blocked-maybe", rules_of(scan_text(src, ".ts")))

    def test_malformed_jsx_does_not_crash(self):
        src = "export const C = () => (<div><span>unclosed</div>);\nconst x = <img src=\"a.png\" />;\n"
        found = scan_text(src, ".jsx")
        self.assertIsInstance(found, list)


class VueSvelteParsing(unittest.TestCase):
    def test_vue_bindings(self):
        src = ('<template>\n  <div>\n    <img :src="u" :alt="a">\n    <img :src="u" alt="">\n'
               '    <div @click="go">x</div>\n    <p>{{ msg }}</p>\n    <Comp v-bind="attrs" />\n  </div>\n</template>\n'
               '<script>\nconst s = \'<img src="x.png">\';\n</script>\n')
        found = scan_text(src, ".vue")
        r = rules_of(found)
        self.assertNotIn("img-missing-alt", r)
        self.assertIn("click-no-keyboard", r)

    def test_vue_literal_bound_values(self):
        src = '<template><a href="/" :aria-hidden="true" :tabindex="0">x</a></template>'
        self.assertIn("aria-hidden-focusable", rules_of(scan_text(src, ".vue")))

    def test_vue_style_scss_parsed(self):
        src = '<template><p class="m">x</p></template>\n<style lang="scss">\n$c: #bbb;\n.m { color: $c; background: #fff; }\n</style>\n'
        f = [x for x in scan_text(src, ".vue") if x["rule"] == "contrast-text"]
        self.assertTrue(f)
        self.assertEqual(f[0]["line"], 4)

    def test_svelte_shorthand_spread_and_blocks(self):
        src = ('<script>export let src; export let alt;</script>\n<img {src} {alt}>\n<img {...$$props}>\n'
               '{#each items as item}\n  <li>{item}</li>\n{/each}\n<img src={src}>\n')
        found = scan_text(src, ".svelte")
        self.assertEqual([f["line"] for f in found if f["rule"] == "img-missing-alt"], [7])

    def test_svelte_event_modifiers(self):
        src = '<div on:click|preventDefault={go}>Go</div>\n'
        self.assertIn("click-no-keyboard", rules_of(scan_text(src, ".svelte")))

    def test_svelte_quoted_interpolation_is_dynamic(self):
        src = '<img src="a.png" alt="{name} avatar">\n'
        self.assertNotIn("img-missing-alt", rules_of(scan_text(src, ".svelte")))


class HTMLParsing(unittest.TestCase):
    def test_template_placeholders_are_dynamic(self):
        src = '<a href="{{ u }}">{{ t }}</a>\n<img src="{{ s }}" alt="{{ a }}">\n<input {% if r %}required{% endif %} name="q">\n'
        r = rules_of(scan_text(src, ".njk"))
        self.assertFalse(r & {"link-empty", "img-missing-alt", "control-no-label"}, r)

    def test_erb_placeholders(self):
        src = '<img src="<%= logo %>" alt="<%= t(:logo) %>">\n<a href="<%= p %>"><%= name %></a>\n'
        r = rules_of(scan_text(src, ".erb"))
        self.assertFalse(r & {"img-missing-alt", "link-empty"}, r)

    def test_angular_bindings(self):
        src = '<button (click)="x()" [attr.aria-label]="label"></button>\n<div (click)="y()">Go</div>\n'
        r = rules_of(scan_text(src, ".html"))
        self.assertNotIn("button-empty", r)
        self.assertIn("click-no-keyboard", r)

    def test_implied_li_close(self):
        self.assertNotIn("li-outside-list", rules_of(scan_text("<ul><li>a<li>b<li>c</ul>")))

    def test_script_body_not_markup(self):
        src = '<script>document.body.innerHTML = "<img src=x.png>";</script>'
        self.assertNotIn("img-missing-alt", rules_of(scan_text(src)))

    def test_fragment_is_not_full_page(self):
        r = rules_of(scan_text("<p>partial</p>"))
        self.assertFalse(r & {"page-title-missing", "html-lang-missing", "bypass-blocks-missing"}, r)

    def test_markdown_fences_and_code_spans_ignored(self):
        src = '# T\n\n```html\n<img src="a.png">\n```\n\nUse `<img src="b.png">` here.\n\n<img src="c.png">\n'
        found = scan_text(src, ".md")
        self.assertEqual([f["line"] for f in found if f["rule"] == "img-missing-alt"], [9])

    def test_markdown_heading_skip(self):
        self.assertIn("heading-skip", rules_of(scan_text("# A\n\n### C\n", ".md")))

    def test_delegated_click_not_flagged(self):
        src = '<div onclick="route(event)"><button>A</button><a href="/b">B</a></div>'
        self.assertNotIn("click-no-keyboard", rules_of(scan_text(src)))

    def test_empty_backdrop_click_is_warn(self):
        f = [x for x in scan_text('<div class="backdrop" onclick="close()"></div>') if x["rule"] == "click-no-keyboard"]
        self.assertEqual(f[0]["severity"], "warn")

    def test_role_fallback_list(self):
        f = [x for x in scan_text('<div role="foo region" aria-label="R">x</div>') if x["rule"] == "aria-role-invalid"]
        self.assertEqual(f[0]["severity"], "warn")

    def test_abstract_role_fails(self):
        f = [x for x in scan_text('<div role="widget">x</div>') if x["rule"] == "aria-role-invalid"]
        self.assertEqual(f[0]["severity"], "fail")
        self.assertIn("abstract", f[0]["message"])

    def test_native_checkbox_role_switch_needs_no_aria_checked(self):
        r = rules_of(scan_text('<input type="checkbox" role="switch" aria-label="Wi-Fi">'))
        self.assertNotIn("aria-required-attr", r)

    def test_hidden_input_needs_no_label(self):
        self.assertNotIn("control-no-label", rules_of(scan_text('<input type="hidden" name="csrf" value="x">')))

    def test_label_in_other_file_counts(self):
        found = scan_text('<input id="shared">', ".html", extra={"other.html": '<label for="shared">Shared</label>'})
        self.assertNotIn("control-no-label", rules_of(found))

    def test_sr_only_text_names_icon_link(self):
        src = '<a href="/cart"><svg aria-hidden="true"></svg><span class="sr-only">Cart</span></a>'
        self.assertFalse(rules_of(scan_text(src)) & {"link-icon-no-name", "link-empty"})

    def test_display_none_controls_skipped(self):
        src = ('<input type="file" class="hidden">\n<input type="file" hidden>\n'
               '<div style="display:none"><input type="text"></div>\n<input type="file" class="d-none">\n')
        self.assertNotIn("control-no-label", rules_of(scan_text(src)))

    def test_spa_shell_needs_no_bypass(self):
        src = '<!doctype html><html lang="en"><head><title>App</title></head><body><div id="root"></div><script src="/m.js"></script></body></html>'
        self.assertEqual(rules_of(scan_text(src)), set())

    def test_label_in_name_ignores_single_symbol(self):
        self.assertNotIn("label-in-name", rules_of(scan_text('<button aria-label="Close">X</button>')))


class CSSChecks(unittest.TestCase):
    def test_contrast_math(self):
        white, black = ws.parse_color("#fff"), ws.parse_color("black")
        self.assertAlmostEqual(ws.contrast(white, black), 21.0, places=3)
        self.assertAlmostEqual(ws.contrast(ws.parse_color("#767676"), white), 4.54, places=2)
        self.assertAlmostEqual(ws.contrast(ws.parse_color("#949494"), white), 3.03, places=2)

    def test_color_parsing(self):
        self.assertEqual(ws.parse_color("rgb(255 0 0 / 50%)"), (255.0, 0.0, 0.0, 0.5))
        self.assertEqual(ws.parse_color("#0f08"), (0, 255, 0, 0x88 / 255.0))
        r, g, b, a = ws.parse_color("hsl(120, 100%, 25%)")
        self.assertEqual((round(r), round(g), round(b), a), (0, 128, 0, 1.0))
        self.assertIsNone(ws.parse_color("var(--x)"))
        self.assertEqual(ws.background_color("url(a.png) no-repeat"), None)
        self.assertEqual(ws.background_color("#fff url(a.png)"), None)
        self.assertEqual(ws.background_color("none"), "none")
        self.assertEqual(ws.background_color("#fff no-repeat")[:3], (255, 255, 255))

    def test_large_text_threshold(self):
        r = scan_text(".a { color: #888; background: #fff; font-size: 24px; }\n"
                      ".b { color: #888; background: #fff; font-size: 14pt; font-weight: bold; }\n", ".css")
        self.assertNotIn("contrast-text", rules_of(r))
        r = scan_text(".a { color: #888; background: #fff; font-size: 18px; font-weight: bold; }\n", ".css")
        self.assertIn("contrast-text", rules_of(r))

    def test_alpha_foreground_is_blended(self):
        f = [x for x in scan_text(".a { color: rgba(0,0,0,.87); background: #fff; }", ".css") if x["rule"].startswith("contrast")]
        self.assertEqual(f, [])
        f = [x for x in scan_text(".a { color: rgba(0,0,0,.2); background: #fff; }", ".css") if x["rule"] == "contrast-text"]
        self.assertTrue(f)

    def test_translucent_background_is_manual(self):
        f = [x for x in scan_text(".a { color: #000; background: rgba(255,255,255,.5); }", ".css")]
        self.assertEqual([x["severity"] for x in f if x["sc"] == "1.4.3"], ["manual"])

    def test_disabled_selectors_exempt(self):
        self.assertNotIn("contrast-text", rules_of(scan_text("button:disabled { color: #ccc; background: #fff; }", ".css")))

    def test_comments_and_strings_with_braces(self):
        src = '/* } { */\n.a::before { content: "{"; }\n.b { color: #aaa; background: #fff; }\n'
        f = [x for x in scan_text(src, ".css") if x["rule"] == "contrast-text"]
        self.assertEqual([x["line"] for x in f], [3])

    def test_scss_nesting_and_parent_selector(self):
        src = ".card {\n  &:focus { outline: none; }\n  .inner { width: 600px; }\n}\n"
        found = scan_text(src, ".scss")
        sels = {x["rule"]: x["selector"] for x in found}
        self.assertEqual(sels.get("focus-outline-removed"), ".card:focus")
        self.assertEqual(sels.get("fixed-width-no-max"), ".card .inner")

    def test_focus_visible_rule_elsewhere_rescues_focus(self):
        found = scan_text(".x:focus { outline: none; }", ".css", extra={"b.css": ".x:focus-visible { outline: 2px solid #000; }"})
        self.assertNotIn("focus-outline-removed", rules_of(found))

    def test_media_min_width_and_print_skip_reflow(self):
        src = "@media (min-width: 900px) { .a { width: 860px; } }\n@media print { .b { width: 700px; } }\n"
        self.assertNotIn("fixed-width-no-max", rules_of(scan_text(src, ".css")))

    def test_element_resolution_combines_class_rules(self):
        found = scan_text('<p class="muted on-white">Terms</p>', ".html",
                          extra={"s.css": ".muted { color: #aaa; }\n.on-white { background-color: #fff; }\n"})
        f = [x for x in found if x["rule"] == "contrast-text" and x["file"].endswith(".html")]
        self.assertTrue(f)

    def test_inline_style_contrast_and_spacing(self):
        r = rules_of(scan_text('<p style="color:#aaa;background-color:#fff;line-height:1 !important">x</p>'))
        self.assertIn("contrast-text", r)
        self.assertIn("text-spacing-important", r)

    def test_tailwind_target_size_and_outline(self):
        r = rules_of(scan_text('<button class="w-4 h-4 outline-none" aria-label="Close"></button>'))
        self.assertIn("target-size-small", r)
        self.assertIn("focus-outline-removed-maybe", r)
        r = rules_of(scan_text('<button class="w-6 h-6 outline-none focus-visible:ring-2" aria-label="Close"></button>'))
        self.assertFalse(r & {"target-size-small", "focus-outline-removed-maybe"}, r)

    def test_inline_link_target_size_exempt(self):
        self.assertNotIn("target-size-small", rules_of(scan_text('<a href="/x" style="width:10px;height:10px">x</a>')))


class Validators(unittest.TestCase):
    def test_lang(self):
        for ok in ("en", "en-US", "zh-Hant-TW", "sr-Latn", "es-419", "de-CH-1996", "x-klingon", "haw", "mi"):
            self.assertTrue(ws.valid_lang(ok), ok)
        for bad in ("en_US", "english", "e", "zz", "en-", "123"):
            self.assertFalse(ws.valid_lang(bad), bad)

    def test_autocomplete(self):
        for ok in ("on", "off", "email", "shipping street-address", "section-x billing work tel", "username webauthn"):
            self.assertTrue(ws.validate_autocomplete(ok), ok)
        for bad in ("emial", "work name", "billing", "nope", "email shipping"):
            self.assertFalse(ws.validate_autocomplete(bad), bad)

    def test_aria_values(self):
        self.assertTrue(ws.check_aria_value("tristate", "mixed"))
        self.assertFalse(ws.check_aria_value("bool", "mixed"))
        self.assertTrue(ws.check_aria_value("tokens:additions|all|removals|text", "additions text"))
        self.assertFalse(ws.check_aria_value("token:page|step|location|date|time|true|false", "yes"))
        self.assertTrue(ws.check_aria_value("integer", "-2"))
        self.assertFalse(ws.check_aria_value("number", "abc"))

    def test_aria_tables(self):
        self.assertIn("switch", ws.ARIA_ROLES)
        self.assertNotIn("widget", ws.ARIA_ROLES)
        self.assertIn("widget", ws.ARIA_ABSTRACT_ROLES)
        self.assertEqual(ws.ARIA_REQUIRED["slider"], ["aria-valuenow"])


class Fixtures(unittest.TestCase):
    GOOD = ["html/good_page.html", "jsx/GoodCard.tsx", "vue/Good.vue", "svelte/Good.svelte",
            "css/good.css", "tpl/good.erb", "jslinks/ok", "vue/HoverTipOk.vue",
            "toggles/switch-ok.html", "toggles/TickOk.vue", "toggles/FlipOk.vue", "icons/venues-ok.html"]
    BAD = {
        "html/bad_page.html": {"page-title-missing", "html-lang-missing", "viewport-zoom-disabled", "meta-refresh-delay",
                               "focus-outline-removed", "contrast-text", "bypass-blocks-missing", "marquee-blink",
                               "img-missing-alt", "img-alt-empty-in-control", "link-text-generic", "button-icon-no-name",
                               "placeholder-only-label", "click-no-keyboard", "iframe-no-title", "heading-skip",
                               "aria-role-invalid", "aria-hidden-focusable", "lang-invalid"},
        "jsx/BadCard.tsx": {"drag-library-check", "img-missing-alt", "click-no-keyboard", "link-icon-no-name",
                            "label-in-name", "autocomplete-missing", "placeholder-only-label", "aria-required-attr",
                            "contrast-text", "paste-blocked", "onchange-navigates", "li-outside-list",
                            "status-message-no-live"},
        "vue/Bad.vue": {"img-missing-alt", "button-icon-no-name", "click-no-keyboard", "control-no-label",
                        "onchange-navigates", "heading-empty", "heading-skip", "link-icon-no-name",
                        "aria-hidden-focusable", "autocomplete-missing", "drag-library-check", "contrast-text",
                        "focus-outline-removed", "target-size-small"},
        "svelte/Bad.svelte": {"img-missing-alt", "img-alt-suspicious", "click-no-keyboard", "status-message-no-live",
                              "link-empty", "lang-invalid", "aria-required-attr", "custom-control-no-name",
                              "focus-outline-removed", "fixed-width-no-max", "text-spacing-important", "contrast-text"},
        "css/bad.css": {"focus-outline-removed", "contrast-text", "fixed-width-no-max", "text-spacing-important",
                        "focus-obscured-check", "ui-border-contrast", "focus-indicator-contrast", "target-size-small",
                        "contrast-unresolved"},
        "css/nested.scss": {"contrast-text", "focus-outline-removed", "text-spacing-important", "fixed-width-no-max"},
        "tpl/bad.njk": {"img-missing-alt", "link-text-generic"},
        "md/guide.md": {"heading-skip", "img-missing-alt", "link-text-generic"},
        "jslinks/bad": {"click-no-keyboard", "onchange-navigates", "aria-state-not-updated", "svg-icon-no-alt",
                        "hover-content-no-dismiss", "error-not-described", "color-only-reference"},
        "vue/HoverTip.vue": {"hover-content-no-dismiss", "ui-border-contrast"},
        "svelte/Field.svelte": {"ui-border-contrast"},
        "toggles/switch-bad.html": {"ui-border-contrast"},
        "toggles/Tick.vue": {"ui-border-contrast"},
        "toggles/Flip.vue": {"ui-border-contrast"},
        "icons/venues-bad.html": {"svg-icon-no-alt"},
    }

    def scan_file(self, rel, level="AAA"):
        findings, _f, _e = ws.scan([os.path.join(FIX, rel)], level=level)
        return findings

    def test_good_fixtures_have_no_fail_or_warn(self):
        for rel in self.GOOD:
            with self.subTest(rel=rel):
                bad = [(f["line"], f["rule"]) for f in self.scan_file(rel) if f["severity"] in ("fail", "warn")]
                self.assertEqual(bad, [])

    def test_bad_fixtures_expected_rules(self):
        for rel, expected in self.BAD.items():
            with self.subTest(rel=rel):
                got = rules_of(self.scan_file(rel))
                self.assertEqual(expected - got, set(), "missing in %s" % rel)

    def test_md_fence_lines(self):
        lines = [f["line"] for f in self.scan_file("md/guide.md") if f["rule"] == "img-missing-alt"]
        self.assertEqual(lines, [11])

    def test_directory_walk_skips_vendor_dirs(self):
        d = tempfile.mkdtemp(prefix="wcagwalk")
        try:
            for sub in ("node_modules/pkg", "dist", "build", ".git", "vendor", ".cache", "src"):
                os.makedirs(os.path.join(d, sub))
                with open(os.path.join(d, sub, "x.html"), "w") as fh:
                    fh.write('<img src="a.png">')
            with open(os.path.join(d, "src", "app.min.js"), "w") as fh:
                fh.write('const a = <img src="a.png" />;')
            findings, files, _e = ws.scan([d])
            self.assertEqual([os.path.relpath(f, d) for f in files], [os.path.join("src", "x.html")])
            self.assertEqual(len(findings), 1)
        finally:
            shutil.rmtree(d)
        _findings, files, _e = ws.scan([FIX])
        self.assertTrue(any(f.endswith("Bad.vue") for f in files))
        self.assertFalse(any(f.endswith(".txt") for f in files))


class RedundantEntry(unittest.TestCase):
    """3.3.7: data entered in an earlier step requested again without auto-populate/select."""

    def warns(self, body, ext=".html", extra=None):
        return [f for f in scan_text(body, ext, extra=extra) if f["rule"] == "redundant-entry"]

    def test_step_sections_in_one_form(self):
        bad = ('<form><div class="step step-1"><label for="a">Email address</label><input id="a" type="email"></div>'
               '<div class="step step-2"><label for="b">Email address</label><input id="b" type="email"></div></form>')
        f = self.warns(bad)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["severity"], "warn")
        self.assertIn('label "email address"', f[0]["message"])

    def test_shipping_then_billing_needs_same_as_option(self):
        bad = ('<form><fieldset><legend>Shipping</legend><label for="s">Street</label><input id="s" autocomplete="shipping street-address"></fieldset>'
               '<fieldset><legend>Billing</legend><label for="b">Billing street</label><input id="b" autocomplete="billing street-address"></fieldset></form>')
        self.assertEqual(len(self.warns(bad)), 1)
        good = bad.replace('<legend>Billing</legend>', '<legend>Billing</legend><label><input type="checkbox" name="same"> Same as shipping address</label>')
        self.assertEqual(self.warns(good), [])

    def test_exceptions(self):
        first = '<form><label for="a">Email</label><input id="a" autocomplete="email"></form>'
        cases = {
            "prefilled": '<form><label for="b">Email</label><input id="b" autocomplete="email" value="x@example.org"></form>',
            "select": '<form><label for="b">Email</label><select id="b" autocomplete="email"><option>x@example.org</option></select></form>',
            "no longer valid": '<form><label for="b">New email</label><input id="b" type="email"></form>',
            "documented essential": '<form><label for="b">Email</label><input id="b" autocomplete="email" data-reentry="essential"></form>',
        }
        for why, second in cases.items():
            with self.subTest(why=why):
                self.assertEqual(self.warns(first + second), [])
        pw = '<form><label for="p">Password</label><input id="p" type="password"></form>'
        self.assertEqual(self.warns(pw + pw.replace('"p"', '"q"')), [], "security re-entry")

    def test_steps_across_pages_fixture(self):
        findings, _f, _e = ws.scan([os.path.join(FIX, "steps")])
        red = [f for f in findings if f["rule"] == "redundant-entry"]
        self.assertEqual([(os.path.basename(f["file"]), f["selector"]) for f in red], [("step2-plot.html", "input#mail2")])
        self.assertEqual(red[0]["severity"], "warn")
        self.assertTrue(red[0]["evidence"]["first_file"].endswith("step1-details.html"))

    def test_unrelated_pages_are_not_compared(self):
        f1 = '<form><label for="a">Email</label><input id="a" autocomplete="email"></form>'
        findings = scan_text(f1, extra={"other.html": f1.replace('"a"', '"b"')})
        self.assertNotIn("redundant-entry", rules_of(findings))


class StatusMessageScripts(unittest.TestCase):
    """4.1.3: script writes success/error/result text into a non-live element."""

    def test_fixture_cross_file_script(self):
        findings, _f, _e = ws.scan([os.path.join(FIX, "status")])
        f = [x for x in findings if x["rule"] == "status-message-js-no-live"]
        self.assertEqual([x["selector"] for x in f], ["#wish-feedback"])
        self.assertTrue(f[0]["file"].endswith("wishlist.js"))
        self.assertEqual(f[0]["severity"], "warn")
        self.assertEqual(f[0]["evidence"]["target_line"], 11)

    def test_non_message_writes_and_live_regions_ignored(self):
        js = ('<script>document.querySelector("#f").addEventListener("click", function () {'
              ' var list = document.getElementById("items"); list.appendChild(document.createElement("li"));'
              ' document.getElementById("count").textContent = String(list.children.length); });</script>')
        self.assertNotIn("status-message-js-no-live", rules_of(scan_text(page('<button id="f">Add</button><ul id="items"></ul><span id="count"></span>' + js))))
        js2 = ('<script>const out = document.getElementById("msg"); document.getElementById("f").addEventListener("submit", (e) => {'
               ' out.setAttribute("role", "status"); out.textContent = "Saved"; });</script>')
        self.assertNotIn("status-message-js-no-live", rules_of(scan_text(page('<form id="f"></form><div id="msg"></div>' + js2))))
        js3 = js2.replace('out.setAttribute("role", "status"); ', "")
        self.assertIn("status-message-js-no-live", rules_of(scan_text(page('<form id="f"></form><div id="msg"></div>' + js3))))
        live_parent = page('<form id="f"></form><div aria-live="polite"><div id="msg"></div></div>' + js3)
        self.assertNotIn("status-message-js-no-live", rules_of(scan_text(live_parent)))

    def test_no_action_handler_no_finding(self):
        js = '<script>document.getElementById("msg").textContent = "Saved";</script>'
        self.assertNotIn("status-message-js-no-live", rules_of(scan_text(page('<div id="msg"></div>' + js))))


class ScriptLinking(unittest.TestCase):
    """Listeners attached in external .js files, resolved to elements in the project's pages."""

    def scan_dir(self, rel):
        findings, _f, _e = ws.scan([os.path.join(FIX, rel)])
        return findings

    def by_rule(self, findings, rule):
        return [f for f in findings if f["rule"] == rule]

    def test_bad_fixture_findings(self):
        found = self.scan_dir("jslinks/bad")
        clicks = self.by_rule(found, "click-no-keyboard")
        self.assertEqual(sorted(f["selector"] for f in clicks), ["circle#water-point", "g.plot", "span.dialog-close"])
        for f in clicks:
            self.assertEqual(f["severity"], "warn")
            self.assertTrue(f["file"].endswith("garden.html"), "reported at the element")
            self.assertIn("garden.js:", f["evidence"]["listener"])
        nav = self.by_rule(found, "onchange-navigates")
        self.assertEqual([f["selector"] for f in nav], ["select#season"])
        self.assertEqual(nav[0]["evidence"]["action"], "location.href =")
        aria = {f["evidence"]["attribute"]: f for f in self.by_rule(found, "aria-state-not-updated")}
        self.assertEqual(set(aria), {"aria-checked", "aria-expanded"})
        self.assertTrue(all(f["severity"] == "warn" and f["sc"] == "4.1.2" for f in aria.values()))
        hover = self.by_rule(found, "hover-content-no-dismiss")
        self.assertEqual([f["selector"] for f in hover], ["span#rota-help"])
        self.assertEqual((hover[0]["sc"], hover[0]["severity"]), ("1.4.13", "manual"))
        self.assertIn("not hoverable", hover[0]["message"])
        err = self.by_rule(found, "error-not-described")
        self.assertEqual(len(err), 1)
        self.assertTrue(err[0]["file"].endswith("garden.js"))
        self.assertEqual((err[0]["sc"], err[0]["severity"]), ("3.3.1", "warn"))
        svg = self.by_rule(found, "svg-icon-no-alt")
        self.assertEqual(len(svg), 2)
        self.assertEqual(sorted(f["evidence"]["use_href"] or "" for f in svg), ["", "sprites.svg#icon-cross"])
        color = self.by_rule(found, "color-only-reference")
        self.assertEqual([(f["sc"], f["severity"], f["evidence"]["phrase"]) for f in color], [("1.4.1", "manual", "shown in red")])
        self.assertFalse([f for f in found if f["severity"] == "fail"], "script-linked findings are never fail")

    def test_ok_fixture_is_clean(self):
        found = self.scan_dir("jslinks/ok")
        self.assertEqual([(f["line"], f["rule"]) for f in found if f["severity"] in ("fail", "warn", "manual")], [])

    def test_script_links_only_to_pages_that_load_it(self):
        js = 'document.getElementById("x").addEventListener("click", function () { go(); });'
        loads = page('<span id="x">Go</span><script src="app.js"></script>')
        other = page('<span id="x">Go</span>')
        d = tempfile.mkdtemp(prefix="wcaglink")
        try:
            for name, body in (("a.html", loads), ("b.html", other), ("app.js", js)):
                with open(os.path.join(d, name), "w") as fh:
                    fh.write(body)
            f = [x for x in ws.scan([d])[0] if x["rule"] == "click-no-keyboard"]
            self.assertEqual([os.path.basename(x["file"]) for x in f], ["a.html"])
            os.remove(os.path.join(d, "a.html"))  # no page loads app.js: link to every page
            f = [x for x in ws.scan([d])[0] if x["rule"] == "click-no-keyboard"]
            self.assertEqual([os.path.basename(x["file"]) for x in f], ["b.html"])
        finally:
            shutil.rmtree(d)

    def test_click_linking_variants(self):
        body = page('<ul class="tags"><li class="tag">Rust</li></ul><div id="w"><button type="button" class="in">X</button></div>'
                    '<span id="k" tabindex="0">K</span><script src="app.js"></script>')
        js = ("const tags = document.querySelectorAll('ul.tags .tag');\n"
              "for (const t of tags) { t.addEventListener('click', pick); }\n"
              "function pick() {}\n"
              "document.getElementById('w').addEventListener('click', () => {});\n"  # delegates to a real button
              "const k = document.getElementById('k'); k.onclick = pick; k.onkeydown = pick;\n")
        f = [x for x in scan_text(body, extra={"app.js": js}) if x["rule"] == "click-no-keyboard"]
        self.assertEqual([x["selector"] for x in f], ["li.tag"])
        deleg = page('<div class="card">Open</div><script src="app.js"></script>')
        js2 = "document.addEventListener('click', function (e) { var c = e.target.closest('.card'); if (c) open(c); });"
        f = [x for x in scan_text(deleg, extra={"app.js": js2}) if x["rule"] == "click-no-keyboard"]
        self.assertEqual([x["evidence"]["via"] for x in f], ["delegated"])

    def test_jquery_and_named_function_navigation(self):
        body = page('<label for="s">Sort</label><select id="s"><option>A</option></select><script src="app.js"></script>')
        js = "function go(v) { window.location.assign('/sort/' + v); }\n$('#s').on('change', function () { go(this.value); });\n"
        f = [x for x in scan_text(body, extra={"app.js": js}) if x["rule"] == "onchange-navigates"]
        self.assertEqual(len(f), 1)
        js_ok = "$('#s').on('change', function () { render(this.value); });\n"
        self.assertNotIn("onchange-navigates", rules_of(scan_text(body, extra={"app.js": js_ok})))

    def test_aria_state_suppressed_by_computed_attribute_or_native_input(self):
        dyn = ('<button type="button" id="b" aria-expanded="false">Menu</button><script>var b = document.getElementById("b");'
               ' b.addEventListener("click", function () { b.classList.toggle("open"); sync(b, "aria-expanded"); });'
               ' function sync(el, attr) { el.setAttribute(attr, el.classList.contains("open")); }</script>')
        self.assertNotIn("aria-state-not-updated", rules_of(scan_text(dyn)))
        inline = '<div role="checkbox" aria-checked="false" tabindex="0" onclick="this.classList.toggle(\'on\')" onkeydown="k()">Opt in</div>'
        self.assertIn("aria-state-not-updated", rules_of(scan_text(inline)))

    def test_error_linked_by_describedby_is_ok(self):
        body = ('<label for="e">Email</label><input id="e" aria-describedby="e-note"><p id="e-note" hidden></p>'
                '<script>var e = document.getElementById("e"); var n = document.getElementById("e-note");'
                ' e.addEventListener("blur", function () { e.classList.add("is-invalid"); n.hidden = false; });</script>')
        self.assertNotIn("error-not-described", rules_of(scan_text(body)))
        unrelated = body.replace("n.hidden = false", 'document.getElementById("banner").hidden = false').replace(
            '<p id="e-note" hidden></p>', '<p id="e-note">Work address</p><div id="banner" hidden>Hi</div>')
        self.assertIn("error-not-described", rules_of(scan_text(unrelated)))


class HeuristicRules(unittest.TestCase):
    def test_svg_icon_contexts(self):
        ok = {
            "next to text": '<ul><li><svg width="9" height="9"><path d="M0 0"/></svg> Free delivery</li></ul>',
            "wrapper next to text": '<p><span class="ic"><svg width="9" height="9"><path d="M0 0"/></svg></span> Open daily</p>',
            "inside button": '<button type="button"><svg width="9" height="9"><path d="M0 0"/></svg> Save</button>',
            "aria-hidden ancestor": '<table><tr><td><span aria-hidden="true"><svg><path d="M0 0"/></svg></span></td></tr></table>',
            "titled": '<table><tr><td><svg><title>Yes</title><path d="M0 0"/></svg></td></tr></table>',
            "sprite sheet": '<div><svg style="display: none"><symbol id="i"><path d="M0 0"/></symbol></svg></div>',
            "stand-alone illustration": '<section><div><svg width="400" height="300"><path d="M0 0"/></svg></div></section>',
        }
        for why, body in ok.items():
            with self.subTest(why=why):
                self.assertNotIn("svg-icon-no-alt", rules_of(scan_text(body)))
        bad = '<ul><li><svg width="9" height="9"><use href="#i-check"/></svg></li></ul>'
        f = [x for x in scan_text(bad) if x["rule"] == "svg-icon-no-alt"]
        self.assertEqual([(x["severity"], x["evidence"]["use_href"]) for x in f], [("warn", "#i-check")])

    def test_color_reference_phrases(self):
        style = "<style>.hl { background-color: #fff3a0; }</style>"
        for text in ("Changes are highlighted in green.", "Mandatory fields are marked in colour.", "Errors in red.",
                     "Red fields are required.", "The schedule is colour-coded."):
            with self.subTest(text=text):
                self.assertIn("color-only-reference", rules_of(scan_text(style + "<p>%s</p>" % text)))
        for text in ("She lives in Redmond.", "The red wine list is below.", "Set in green hills near the coast."):
            with self.subTest(text=text):
                self.assertNotIn("color-only-reference", rules_of(scan_text(style + "<p>%s</p>" % text)))
        self.assertNotIn("color-only-reference", rules_of(scan_text("<p>Errors are shown in red.</p>")), "no class colour styling")
        self.assertNotIn("color-only-reference", rules_of(scan_text(style + "<pre>shown in red</pre>")))

    def test_hover_inline_html_and_escape(self):
        bad = ('<span tabindex="0" role="button" aria-label="Help" onmouseover="tip.hidden=false" onmouseout="tip.hidden=true">?</span>'
               '<div id="tip" hidden>Help text</div>')
        self.assertIn("hover-content-no-dismiss", rules_of(scan_text(bad)))
        esc = bad + "<script>document.addEventListener('keydown', function (e) { if (e.key === 'Escape') tip.hidden = true; });</script>"
        self.assertNotIn("hover-content-no-dismiss", rules_of(scan_text(esc)))
        show_only = '<span tabindex="0" role="button" aria-label="Help" onmouseover="tip.hidden=false">?</span>'
        self.assertNotIn("hover-content-no-dismiss", rules_of(scan_text(show_only)))

    def test_border_contrast_in_component_styles(self):
        f = [x for x in self_scan("vue/HoverTip.vue") if x["rule"] == "ui-border-contrast"]
        self.assertEqual([(x["line"], x["evidence"]["ratio"]) for x in f], [(19, 1.36)])
        self.assertIn("assumed white", f[0]["message"])
        f = [x for x in self_scan("svelte/Field.svelte") if x["rule"] == "ui-border-contrast"]
        self.assertEqual([(x["line"], x["evidence"]["ratio"]) for x in f], [(12, 1.36)])
        self.assertIn("div.panel", f[0]["message"])
        # a class that styles no form control is not a UI component
        vue = '<template><div class="box">x</div></template>\n<style scoped>\n.box { border: 1px solid #dddddd; }\n</style>\n'
        self.assertNotIn("ui-border-contrast", rules_of(scan_text(vue, ".vue")))
        # the page background is used when declared
        dark = '<template><input class="f" aria-label="Q"></template>\n<style>\nbody { background: #111111; }\n.f { border: 1px solid #dddddd; }\n</style>\n'
        self.assertNotIn("ui-border-contrast", rules_of(scan_text(dark, ".vue")))


    def test_svg_icon_standing_apart_in_items(self):
        f = [x for x in self_scan("icons/venues-bad.html") if x["rule"] == "svg-icon-no-alt"]
        self.assertEqual([x["line"] for x in f], [12, 21, 26])
        for x in f:
            self.assertEqual(x["severity"], "warn")
            self.assertTrue(x["message"].startswith("Icon stands apart from the text in this item; if it conveys information"))
            self.assertTrue(x["evidence"]["stands_apart"])
        self.assertEqual([x["evidence"].get("icon_in_items") for x in f], ["2/3", "2/3", None])
        self.assertIn("only 2 of 3 items", f[0]["message"])
        self.assertEqual(f[2]["evidence"]["container"], "div.offer-card")
        self.assertEqual([x for x in self_scan("icons/venues-ok.html") if x["rule"] == "svg-icon-no-alt"], [])

    def test_svg_icon_label_patterns_stay_silent(self):
        icon = '<svg width="9" height="9"><use href="#i-a"/></svg>'
        ok = {
            "inline label in item": '<ul><li><span>%s Step-free</span><h3>Hall</h3></li></ul>' % icon,
            "paragraph label": '<ul><li><h3>Hall</h3><p>%s Step-free</p></li></ul>' % icon,
            "heading": '<article class="card"><h3>%s Hall</h3><p>Seats 40</p></article>' % icon,
            "text beside icon in item": '<ul><li>%s Step-free<p>More</p></li></ul>' % icon,
            "plain wrapper with block text": '<div class="row">%s<h3>Hall</h3><p>Seats 40</p></div>' % icon,
            "bullet on every item": '<ul><li>%s<p>Tea</p></li><li>%s<p>Keys</p></li></ul>' % (icon, icon),
            "nav link": '<nav><ul><li><a href="/a">%s About</a></li></ul></nav>' % icon,
        }
        for why, body in ok.items():
            with self.subTest(why=why):
                self.assertNotIn("svg-icon-no-alt", rules_of(scan_text(body)))
        bad = {
            "list item": '<ul><li>%s<h3>Hall</h3><p>Seats 40</p></li></ul>' % icon,
            "card": '<article class="venue-card"><span class="ic">%s</span><h3>Hall</h3><p>Seats 40</p></article>' % icon,
            "table cell": '<table><tr><th>Room</th></tr><tr><td>%s<p>Hall</p></td></tr></table>' % icon,
        }
        for why, body in bad.items():
            with self.subTest(why=why):
                f = [x for x in scan_text(body) if x["rule"] == "svg-icon-no-alt"]
                self.assertEqual(len(f), 1)
                self.assertTrue(f[0]["evidence"].get("stands_apart"))


class CustomToggleContrast(unittest.TestCase):
    """1.4.11: checkbox / radio / switch drawn by a sibling of a visually hidden native input."""

    def toggle_findings(self, rel_or_findings):
        found = self_scan(rel_or_findings) if isinstance(rel_or_findings, str) else rel_or_findings
        return [x for x in found if x["rule"] == "ui-border-contrast"]

    def test_switch_fixture(self):
        f = self.toggle_findings("toggles/switch-bad.html")
        self.assertEqual([(x["line"], x["severity"], x["selector"]) for x in f], [(15, "warn", ".pref__input + .pref__track")])
        r = f[0]["evidence"]["ratios"]
        self.assertEqual(r["track_vs_surrounding"], 1.14)
        self.assertEqual(r["border_vs_surrounding"], 1.43)
        self.assertEqual(r["span.pref__knob_thumb_vs_track"], 1.14)
        self.assertEqual(r["span.pref__knob_thumb_ring_vs_track"], 1.16)
        self.assertIn("Custom switch", f[0]["message"])
        self.assertIn(".pref__input + .pref__track", f[0]["message"])
        self.assertEqual(self.toggle_findings("toggles/switch-ok.html"), [])

    def test_vue_checkbox_fixture(self):
        f = self.toggle_findings("toggles/Tick.vue")
        self.assertEqual([(x["line"], x["evidence"]["ratio"]) for x in f], [(18, 1.49)])
        self.assertIn("div.opts", f[0]["message"])
        self.assertNotIn(":checked", f[0]["selector"])
        # checked-only pale state, an unhidden native checkbox and a dark ring are all fine
        self.assertEqual(self.toggle_findings("toggles/TickOk.vue"), [])

    def test_state_only_sibling_rules_identify_the_track(self):
        f = self.toggle_findings("toggles/Flip.vue")
        self.assertEqual([(x["line"], x["selector"]) for x in f], [(15, ".flip__in + .flip__track")])
        r = f[0]["evidence"]["ratios"]
        self.assertEqual((r["track_vs_surrounding"], r["border_vs_surrounding"], r["span.flip__knob_thumb_ring_vs_track"]), (1.13, 1.36, 1.15))
        self.assertEqual(self.toggle_findings("toggles/FlipOk.vue"), [])
        # no sibling rules at all: the same-<label> fallback accepts a track that holds only an empty knob
        with open(os.path.join(FIX, "toggles", "Flip.vue"), encoding="utf-8") as fh:
            src = "".join(ln for ln in fh.read().splitlines(True) if "+ .flip__track" not in ln)
        f = self.toggle_findings(scan_text(src, ".vue"))
        self.assertEqual([x["selector"] for x in f], ["span.flip__track (in the same <label>)"])
        self.assertNotIn("flip__text", " ".join(x["selector"] for x in f))

    def test_page_background_from_custom_property(self):
        slider = '<label class="switch"><input type="checkbox"><span class="slider"></span></label>'
        track = (".switch input { opacity: 0; width: 1px; height: 1px; }\n"
                 ".slider { background-color: #f1f1f1; border: 1px solid #dddddd; }\n")
        css = ":root { --page: #ffffff; --surface: var(--page); }\nbody { background: var(--surface); }\n" + track
        f = self.toggle_findings(scan_text(page(slider), extra={"s.css": css}))
        self.assertEqual(len(f), 1)
        self.assertIn("vs surrounding #ffffff", f[0]["message"])  # body background resolved through two var() levels
        # an undefined custom property stays unresolved, so the check stays silent
        css = "body { background: var(--nowhere); }\n" + track
        self.assertEqual(self.toggle_findings(scan_text(page(slider), extra={"s.css": css})), [])

    def test_hidden_input_is_not_a_small_target(self):
        found = self_scan("toggles/switch-ok.html") + self_scan("toggles/TickOk.vue")
        self.assertNotIn("target-size-small", rules_of(found))

    def test_variants(self):
        slider = '<label class="switch"><input type="checkbox"><span class="slider"></span></label>'
        base = ".switch input { opacity: 0; width: 0; height: 0; }\n.slider { background-color: #eeeeee; }\n"
        bad = base + ".slider::before { content: ''; background-color: #ffffff; }\ninput:checked + .slider { background-color: #1a5fb4; }\n"
        f = self.toggle_findings(scan_text(page(slider), extra={"s.css": bad}))
        self.assertEqual(len(f), 1)
        self.assertTrue(f[0]["file"].endswith("s.css"))
        self.assertEqual(f[0]["selector"], "input + .slider")
        ok = base + ".slider::before { content: ''; background-color: #555555; }\n"
        self.assertEqual(self.toggle_findings(scan_text(page(slider), extra={"s.css": ok})), [])
        box = '<label><input type="checkbox" class="sr-only"><i class="box"></i> Agree</label>'
        f = self.toggle_findings(scan_text(page(box), extra={"s.css": ".box { border: 1px solid #dddddd; }\n"}))
        self.assertEqual([x["selector"] for x in f], ["i.box (in the same <label>)"])
        self.assertEqual(self.toggle_findings(scan_text(page(box), extra={"s.css": ".box { border: 1px solid var(--line); }\n"})), [],
                         "unresolved colour: no guess")
        native = box.replace(' class="sr-only"', "")
        self.assertEqual(self.toggle_findings(scan_text(page(native), extra={"s.css": ".box { border: 1px solid #dddddd; }\n"})), [])
        pseudo = '<input type="checkbox" id="c" class="cb"><label for="c">Agree</label>'
        css = ".cb { position: absolute; opacity: 0; }\n.cb + label::before { content: ''; border: 1px solid #e5e5e5; }\n"
        f = self.toggle_findings(scan_text(page(pseudo), extra={"s.css": css}))
        self.assertEqual([x["selector"] for x in f], [".cb + label::before"])
        css_ok = css.replace("#e5e5e5", "#707070")
        self.assertEqual(self.toggle_findings(scan_text(page(pseudo), extra={"s.css": css_ok})), [])

    def test_selector_split(self):
        self.assertEqual(ws.split_selector("label > input:checked~.t .k"),
                         (["label", "input:checked", ".t", ".k"], [None, ">", "~", " "]))
        self.assertEqual(ws.split_selector(".x:not(.y .z) + span"), ([".x:not(.y .z)", "span"], [None, "+"]))


def self_scan(rel):
    findings, _f, _e = ws.scan([os.path.join(FIX, rel)])
    return findings


class LogotypeContrast(unittest.TestCase):
    """1.4.3 logotype exception: low contrast on logo / brand text is warn, not fail."""

    def test_css_fixture(self):
        findings, _f, _e = ws.scan([os.path.join(FIX, "css", "brand.css")])
        by_sel = {f["selector"]: f for f in findings if f["rule"] == "contrast-text"}
        self.assertEqual(by_sel[".site-logo"]["severity"], "warn")
        self.assertTrue(by_sel[".site-logo"]["message"].startswith("possible logotype exception (1.4.3) \u2014 confirm"))
        self.assertEqual(by_sel[".intro-note"]["severity"], "fail")

    def test_markup_contexts(self):
        muted = '<span style="color: #b0b0b0; background-color: #fff">%s</span>'
        cases = {
            "logo class": '<div class="site-logo">%s</div>' % (muted % "Fernbrook"),
            "header brand link": '<header><a href="/">%s</a></header>' % (muted % "Fernbrook"),
            "role img logo": '<div role="img" aria-label="Fernbrook logo">%s</div>' % (muted % "FB"),
        }
        for why, body in cases.items():
            with self.subTest(why=why):
                f = [x for x in scan_text(page(body)) if x["rule"] == "contrast-text"]
                self.assertEqual([x["severity"] for x in f], ["warn"])
                self.assertIn("logotype", f[0]["evidence"])
        plain = [x for x in scan_text(page('<p>%s</p>' % (muted % "Opening hours"))) if x["rule"] == "contrast-text"]
        self.assertEqual([x["severity"] for x in plain], ["fail"])
        nav = [x for x in scan_text(page('<header><a href="/about">%s</a></header>' % (muted % "About"))) if x["rule"] == "contrast-text"]
        self.assertEqual([x["severity"] for x in nav], ["fail"], "non-home header link is not a brand link")


class CLI(unittest.TestCase):
    def run_cli(self, *args):
        p = subprocess.run([sys.executable, SCRIPT] + list(args), capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr

    def test_list_rules(self):
        code, out, _ = self.run_cli("--list-rules")
        self.assertEqual(code, 0)
        for slug in ws.RULES:
            self.assertIn(slug, out)
        self.assertIn("SC", out.splitlines()[0])

    def test_version(self):
        code, out, _ = self.run_cli("--version")
        self.assertEqual(code, 0)
        self.assertIn(ws.VERSION, out)

    def test_help(self):
        code, out, _ = self.run_cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("--min-severity", out)

    def test_usage_errors(self):
        self.assertEqual(self.run_cli()[0], 2)
        self.assertEqual(self.run_cli("/nonexistent/path/xyz")[0], 2)
        self.assertEqual(self.run_cli("--level", "B", FIX)[0], 2)

    def test_json_envelope_and_exit_1(self):
        code, out, _ = self.run_cli("--json", os.path.join(FIX, "html", "bad_page.html"))
        self.assertEqual(code, 1)
        env = json.loads(out)
        self.assertEqual(set(env), {"meta", "summary", "findings"})
        self.assertEqual(env["meta"]["tool"], "wcag_scan")
        self.assertEqual(env["meta"]["wcag"], "2.2 (2024-12-12)")
        self.assertTrue(env["meta"]["date"].endswith("Z"))
        self.assertIn("target", env["meta"])
        self.assertEqual(sum(env["summary"]["by_severity"].values()), len(env["findings"]))
        self.assertEqual(sum(sum(v.values()) for v in env["summary"]["by_sc"].values()), len(env["findings"]))
        for sc, row in env["summary"]["by_sc"].items():
            self.assertEqual(set(row), {"fail", "warn", "manual", "info"}, sc)
            self.assertEqual(row["fail"], sum(1 for f in env["findings"] if f["sc"] == sc and f["severity"] == "fail"))
        self.assertTrue(all(f["severity"] in ("fail", "warn", "manual", "info") for f in env["findings"]))

    def test_exit_0_for_clean_and_warn_only(self):
        self.assertEqual(self.run_cli(os.path.join(FIX, "html", "good_page.html"))[0], 0)
        self.assertEqual(self.run_cli("--min-severity", "warn", os.path.join(FIX, "tpl", "good.erb"))[0], 0)

    def test_level_filter(self):
        code, out, _ = self.run_cli("--json", "--level", "A", os.path.join(FIX, "css", "bad.css"))
        env = json.loads(out)
        self.assertTrue(all(f["level"] == "A" for f in env["findings"]))
        self.assertFalse(any(f["sc"] == "1.4.3" for f in env["findings"]))
        code, out, _ = self.run_cli("--json", os.path.join(FIX, "css", "bad.css"))
        levels = {f["level"] for f in json.loads(out)["findings"]}
        self.assertNotIn("AAA", levels)
        code, out, _ = self.run_cli("--json", "--level", "AAA", os.path.join(FIX, "css", "bad.css"))
        self.assertIn("2.4.13", {f["sc"] for f in json.loads(out)["findings"]})

    def test_min_severity(self):
        code, out, _ = self.run_cli("--json", "--min-severity", "fail", os.path.join(FIX, "css", "bad.css"))
        env = json.loads(out)
        self.assertTrue(env["findings"])
        self.assertTrue(all(f["severity"] == "fail" for f in env["findings"]))

    def test_text_output(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = ws.main([os.path.join(FIX, "tpl", "bad.njk")])
        out = buf.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("FAIL WCAG-1.1.1 (A) [img-missing-alt]", out)
        self.assertIn("file(s) scanned", out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
