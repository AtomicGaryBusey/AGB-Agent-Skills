#!/usr/bin/env python3
"""Grader self-test, per fixture: one synthetic findings row per defect and
decoy; every generated recall/severity/nodecoy regex must match its own row
only (rows from the same fixture are the cross-talk set), objective severity
graders must reject a Review note, prose must not count, and no-peek must catch
an answer-key or fixture read. Run after gen_suite.py; exits 1 on a mismatch."""
import json, re, glob, os, sys
from pathlib import Path
EV = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, f"{EV}/graders")
import spec as specmod
spec = specmod.load()
# realistic rows, one per defect: (location text, description)
# --- larkspur ---
R = {
"D01": ("`catalog.html:38`, :46, :54, :62", "1.1.1 Non-text Content (A) | Nonconformity | Cover images have no alt attribute"),
"D02": ("index.html:30", "1.1.1 (A) | Review note | Decorative flourish has descriptive alt"),
"D03": ("events.html:36", "1.3.1 Info and Relationships | Deviation | Event titles styled as headings but are <p>"),
"D04": ("signup.html:34-59", "1.3.5 Identify Input Purpose (AA) | Nonconformity | No autocomplete on personal fields"),
"D05": ("app.js:103", "1.4.1 Use of Color | Nonconformity | Errors shown by red border only"),
"D06": ("styles.css:190", "1.4.3 Contrast (Minimum) | Nonconformity | .event-meta #999 on white 2.85:1"),
"D07": ("signup.html:34", "1.4.3 / 3.3.2 | Nonconformity | Placeholder is the only label; #aaa is 2.32:1"),
"D08": ("styles.css:105-107", "1.4.10 Reflow | Deviation | Fixed 4x240px grid scrolls sideways at 320px"),
"D09": ("styles.css:191", "1.4.12 Text Spacing | Deviation | .btn-fixed clips text"),
"D10": ("styles.css:246", "1.4.11 Non-text Contrast | Deviation | Input border #d6d6d6 1.45:1"),
"D11": ("catalog.html:42", "2.1.1 Keyboard | Nonconformity | div with onclick, not focusable"),
"D12": ("app.js:83-92", "2.1.2 No Keyboard Trap | Nonconformity | Tab pinned to #res-name"),
"D13": ("events.html:6", "2.2.1 Timing Adjustable | Nonconformity | meta refresh 120 s"),
"D14": ("app.js:14", "2.2.2 Pause, Stop, Hide | Nonconformity | setInterval carousel with no pause"),
"D15": ("catalog.html", "2.4.2 Page Titled | Nonconformity | No <title> element"),
"D16": ("login.html:40", "2.4.3 Focus Order | Deviation | positive tabindex"),
"D17": ("events.html:32", "2.4.4 Link Purpose | Review note | 'Click here'"),
"D18": ("styles.css:59", "2.4.7 Focus Visible | Nonconformity | outline: none on nav links"),
"D19": ("styles.css:25-26", "2.4.11 Focus Not Obscured | Deviation | sticky header with no scroll-padding on catalog"),
"D20": ("catalog.html:83", "2.5.7 Dragging Movements | Nonconformity | drag-only reorder"),
"D21": ("styles.css:160", "2.5.8 Target Size (Minimum) | Nonconformity | pager 16x16"),
"D22": ("events.html:2", "3.1.1 Language of Page | Nonconformity | <html> has no lang"),
"D23": ("catalog.html:93", "3.2.6 Consistent Help | Nonconformity | help bar moved to footer"),
"D24": ("signup.html:59", "3.3.7 Redundant Entry | Nonconformity | card-email asks for email again"),
"D25": ("login.html:37", "3.3.8 Accessible Authentication (Minimum) | Nonconformity | onpaste blocks password managers"),
"D26": ("catalog.html:28", "4.1.2 Name, Role, Value | Nonconformity | Search input #q has no accessible name"),
"D27": ("catalog.html:29", "4.1.2 Name, Role, Value | Nonconformity | Icon-only submit button, img alt empty"),
"D28": ("catalog.html:32", "4.1.2 Name, Role, Value | Nonconformity | role=\"buton\" is not a valid role"),
"D29": ("index.html:85", "4.1.2 Name, Role, Value | Nonconformity | Focusable links inside aria-hidden container"),
"D30": ("catalog.html:34", "4.1.3 Status Messages | Nonconformity | status text not in a live region"),
}
DECOY = {
"K1": ("index.html:52", "1.1.1 | Nonconformity | divider has empty alt"),
"K2": ("events.html:60", "1.3.1 | Deviation | layout table uses scope"),
"K3": ("events.html:29", "2.5.8 Target Size | Nonconformity | access guide link 16px"),
"K4": ("login.html:46", "3.3.8 | Nonconformity | CAPTCHA is a cognitive function test"),
"K5": ("styles.css:40", "1.4.3 Contrast | Nonconformity | logo-word #c9b6ef"),
"K6": ("index.html:2", "2.4.11 | Deviation | sticky header obscures focus"),
"N1": ("index.html:78", "1.3.1 | Deviation | heading level skip h2 to h4"),
"N2": ("signup.html:67", "3.3.7 Redundant Entry | Deviation | confirm PIN asked again"),
"N3": ("events.html:57", "1.4.10 Reflow | Deviation | table scrolls horizontally at 320"),
}
# --- brightwater --- (some rows deliberately cite a neighbour's line or file
# region: H04 fares.html:63 is inside H02's range, H13 cites site.css:31 (H26),
# H14 names the site-footer (H26 anchor), HK1 fares.html:43 is inside H04's)
RB = {
"H01": ("planner.html:61, :70", "1.1.1 Non-text Content (A) | Nonconformity | Step-free SVG icon has no text alternative"),
"H02": ("fares.html:48-59", "1.3.1 Info and Relationships (A) | Nonconformity | Fare table uses td.th cells, no th elements"),
"H03": ("claim-1.html:40", "1.3.5 Identify Input Purpose (AA) | Nonconformity | c-email has autocomplete=\"off\"; name and phone have no token"),
"H04": ("fares.html:63-64", "1.4.1 Use of Color (A) | Review note | Peak fares shown only in red (#c0392b)"),
"H05": ("css/site.css:179-180", "1.4.3 Contrast (Minimum) (AA) | Deviation | Floating labels #a0a0a0 on white are 2.61:1"),
"H06": ("css/site.css:136", "1.4.10 Reflow (AA) | Deviation | .alert-detail min-width 880px forces horizontal scrolling at 320px"),
"H07": ("components/ToggleSwitch.vue:32-38", "1.4.11 Non-text Contrast (AA) | Deviation | Off track #f1f1f1 with #dddddd border is 1.36:1; thumb 1.13:1"),
"H08": ("components/ZoneInfoTooltip.vue:8-11", "1.4.13 Content on Hover or Focus (AA) | Review note | Tooltip closes when the pointer moves onto it; no Escape"),
"H26": ("css/site.css:31, :57", "1.4.11 Non-text Contrast (AA) | Deviation | Focus ring #0b5cad on #12324f is 1.97:1"),
"H09": ("map.html:43-49", "2.1.1 Keyboard (A) | Nonconformity | SVG stop groups respond to click only; not focusable"),
"H10": ("js/alerts.js:73-86", "2.1.2 No Keyboard Trap (A) | Nonconformity | Email modal cancels Escape and cycles Tab; close is a span"),
"H11": ("css/site.css:84", "2.2.2 Pause, Stop, Hide (A) | Nonconformity | Promo carousel animation runs infinitely with no pause control"),
"H12": ("login.html:41-42", "2.4.3 Focus Order (A) | Deviation | Positive tabindex on Sign in and Create an account"),
"H13": ("css/site.css:52 (beats :focus-visible at site.css:31)", "2.4.7 Focus Visible (AA) | Deviation | .site-nav a:focus { outline: none } with no replacement"),
"H14": ("feedback.html:64-72", "2.4.11 Focus Not Obscured (Minimum) (AA) | Review note | Fixed .site-footer.dock-footer (12rem) hides focused fields"),
"H15": ("components/SavedTrips.vue:8-17", "2.5.7 Dragging Movements (AA) | Deviation | Drag is the only way to reorder saved trips"),
"H16": ("alerts.html:32-34", "2.5.8 Target Size (Minimum) (AA) | Deviation | .mini-btn banner buttons 16x16, centres 20px apart"),
"H17": ("fares.html:2", "3.1.1 Language of Page (A) | Nonconformity | <html> has no lang attribute"),
"H18": ("js/fares.js:7-9", "3.2.2 On Input (A) | Nonconformity | Zone select change handler navigates to a new page"),
"H19": ("claim-2.html:63", "3.2.6 Consistent Help (A) | Review note | Help & contact moved from the header to the footer"),
"H20": ("js/feedback.js:8-12", "3.3.1 Error Identification (A) | Deviation | Invalid fields get a red border only; error text stays hidden"),
"H21": ("claim-3.html:36, :40", "3.3.7 Redundant Entry (A) | Review note | Email and phone from step 1 asked again, no pre-fill"),
"H22": ("js/login.js:8-12", "3.3.8 Accessible Authentication (Minimum) (AA) | Nonconformity | Paste blocked on password and OTP digits"),
"H23": ("js/alerts.js:26-28", "4.1.2 Name, Role, Value (A) | Deviation | Switch toggles class but never updates aria-checked"),
"H24": ("planner.html:36", "4.1.2 Name, Role, Value (A) | Nonconformity | Locate-me button has no accessible name (background image only)"),
"H25": ("alerts.html:51", "4.1.3 Status Messages (AA) | Review note | refresh-result text is not in a live region"),
}
DECOYB = {
"HK1": ("fares.html:43", "1.4.10 Reflow | Deviation | fare table scrolls horizontally at 320px"),
"HK2": ("claim-3.html:46", "1.4.3 Contrast | Nonconformity | Submit claim button #9aa3ad on #e4e7ea 2.06:1"),
"HK3": ("planner.html:79", "2.5.7 Dragging Movements | Deviation | saved trips reorder by drag"),
"HK4": ("map.html:34-35", "2.5.8 Target Size | Nonconformity | zoom buttons 20x20px"),
"HK5": ("index.html:65", "2.1.2 No Keyboard Trap | Nonconformity | survey dialog has no Escape handler"),
"HK6": ("css/site.css:48", "1.4.3 Contrast | Nonconformity | wordmark #9cc3e6 on white 1.85:1"),
}
ROWS = {"larkspur": (R, DECOY), "brightwater": (RB, DECOYB)}
def row(i, loc, desc):
    """The skill's findings-table shape (SKILL.md):
    | # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
    desc is "SC text | Severity | finding"."""
    sc, sev, finding = desc.split(" | ")
    num = re.search(r"\d\.\d\.\d+", sc)
    check = f"WCAG-{num.group(0)}" if num else "WCAG-?"
    return f"| {i} | {sev} | {check} | WCAG 2.2 SC {sc} | page | {loc} | {finding} | - | - |"
def load(p):
    t = open(p).read(); fm, body = t.split("---\n", 2)[1], t.split("---\n", 2)[2].strip()
    meta = {}
    for l in fm.strip().splitlines():
        k, v = l.split(": ", 1)
        try: meta[k] = json.loads(v)
        except ValueError: meta[k] = v
    return meta, body
def flags(m): return (re.M if "m" in m.get("flags","") else 0) | (re.I if "i" in m.get("flags","") else 0)
bad = 0
# every defect and decoy in the spec has a synthetic row, and vice versa
for fx, (rd, rk) in ROWS.items():
    fs = spec["fixture_specs"][fx]
    want = {d["id"] for d in fs["defects"]} | set(fs["decoy_defs"])
    if want != set(rd) | set(rk):
        bad += 1; print(f"{fx}: synthetic rows {sorted(set(rd) | set(rk))} != spec ids {sorted(want)}")
if set(ROWS) != set(spec["fixture_specs"]):
    bad += 1; print("fixtures without synthetic rows:", set(spec["fixture_specs"]) - set(ROWS))
checked = 0
for case in spec["cases"]:
    rd, rk = ROWS[spec["cases"][case]["fixture"]]
    gd = f"{EV}/plugin/cases/{case}/graders"
    for p in sorted(glob.glob(gd + "/*.md")):
        n = os.path.basename(p)[:-3]; m, body = load(p)
        if m["type"] != "regex" or m.get("target") == "trace": continue
        rx = re.compile(body, flags(m))
        kind, id_ = n.split("-", 1)
        checked += 1
        for oid, (loc, desc) in {**rd, **rk}.items():
            hit = bool(rx.search("intro text\n" + row(oid, loc, desc) + "\n"))
            if kind in ("recall", "severity"):
                exp = (oid == id_)
            else:  # nodecoy: should hit only its own decoy row
                exp = (oid == id_)
            if hit != exp:
                bad += 1; print(f"{case}/{n}: row {oid} hit={hit} expected={exp}")
# severity-mismatch check: wrong severity should fail severity grader for objective defects
for d in spec["defects"]:
    if d["sev"] == ["Nonconformity"]:
        m, body = load(f"{EV}/plugin/cases/{d['case']}/graders/severity-{d['id']}.md")
        loc, desc = ROWS[d["fixture"]][0][d["id"]]
        if re.search(body, row(d["id"], loc, desc.replace("Nonconformity", "Review note")), flags(m)):
            bad += 1; print("severity too lax", d["id"])
# prose (no table row) must not count
m, body = load(f"{EV}/plugin/cases/wcag-perceivable/graders/recall-D01.md")
assert not re.search(body, "catalog.html:38 1.1.1 missing alt", flags(m))
# no-peek
m, body = load(f"{EV}/plugin/cases/wcag-perceivable/graders/no-peek.md")
assert re.search(body, '{"file_path":"/x/evals/fixtures/larkspur/answer-key.md"}') and not re.search(body, '"file_path":"/w/catalog.html"')
m, body = load(f"{EV}/plugin/cases/bw-perceivable/graders/recall-H04.md")
assert not re.search(body, "fares.html:63 1.4.1 peak fares only red", flags(m))
# H26 cited on a page's footer links instead of the CSS
m, body = load(f"{EV}/plugin/cases/bw-perceivable/graders/recall-H26.md")
assert re.search(body, "| 9 | index.html:76-78 (footer-links) | 1.4.11 | Deviation | focus ring 1.97:1 |", flags(m))
for case in ("bw-perceivable", "bw-operable", "bw-understandable-robust", "bw-decoys"):
    m, body = load(f"{EV}/plugin/cases/{case}/graders/no-peek.md")
    for peek in ('{"file_path":"/x/evals/fixtures/brightwater/answer-key.md"}',
                 '{"pattern":"**/*","path":"/x/evals/fixtures/brightwater"}',
                 '{"file_path":"/x/evals/fixtures/brightwater/VALIDATION.md"}',
                 '{"file_path":"/x/evals/graders/specs/brightwater.json"}',
                 '{"file_path":"/x/holdout-key.md"}'):
        if not re.search(body, peek):
            bad += 1; print(f"{case}/no-peek misses {peek}")
    for ok in ('"file_path":"/w/alerts.html"', '"file_path":"/w/js/alerts.js"', '"file_path":"/w/css/site.css"'):
        if re.search(body, ok):
            bad += 1; print(f"{case}/no-peek fires on workspace read {ok}")
# Regression rows from the first paid multi-fixture run (2026-09-29), trimmed.
# (case, grader, text, expected hit). For nodecoy graders a hit is a false
# alarm unless expected; for recall/severity a miss is a false miss.
REAL = {
"h15": "| 3 | Nonconformity | WCAG-2.5.7 | WCAG 2.2 SC 2.5.7 (AA); also SC 2.1.1 (A) | component | `components/SavedTrips.vue:5`, `:7-15`, `:31-40` | Saved trips can only be reordered by dragging. There is no single-pointer alternative (such as Move up/down buttons) and no keyboard method. | The template has only `draggable=\"true\"`, `@dragstart` and `@drop`. | Reuse the pattern from `planner.html:77-101`: add \"Move up\"/\"Move down\" buttons that splice `trips`. |",
"d19": "| 13 | Deviation | WCAG-2.4.11 | WCAG 2.2 SC 2.4.11 (AA) | page / stylesheet | `catalog.html:2,8`; `styles.css:19-28` | **On Catalog, focused items may end up completely hidden under the sticky header.** The header is sticky (`body.sticky-page`), but `<html>` lacks the `pad-for-header` class, so there's no `scroll-padding-top`. | Compare `index.html:2` (has `class=\"pad-for-header\"`, `scroll-padding-top:14rem`) with `catalog.html:2` (no class) | Add `class=\"pad-for-header\"` to `catalog.html:2`. |",
"d02": "| 4 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page | `index.html:30` | A decorative divider has descriptive alt text, so screen readers can't skip it (WCAG failure technique F39). | `alt=\"Purple decorative flourish divider\"`. The matching divider at `index.html:52` is handled correctly. | `alt=\"\"`, or use a CSS background. |",
"h10": "| 1 | Nonconformity | WCAG-2.1.2 | WCAG 2.2 SC 2.1.2 (A); also SC 2.1.1 (A) | page | `alerts.html:66-77`, `alerts.html:68`, `js/alerts.js:64-67`, `js/alerts.js:74-86` | A keyboard user can't leave the \"Email alerts\" modal. Escape is cancelled on purpose. | `alerts.js:75-77` cancels Escape. | Let Escape call `closeModal()`. Or replace the whole thing with the native `<dialog>`/`showModal()` pattern already used on index. |",
"bullet": "- **Keyboard walk-through of all 11 pages in a browser:** confirm #1, #2, #5 and #6, and confirm the other 2.4.3/2.4.7 passes, including the native `<dialog>` on index (`site.js`).",
"k3": "| 14 | Deviation | WCAG-2.4.4 | WCAG 2.2 SC 2.4.4 (A) | page | `events.html:29` \u2192 `events.html:56` | **The \"access guide\" link goes to the wrong place.** It promises parking details, but its target `#access` is the heading \"Room schedule this week\". | `href=\"events.html#access\"` | Point the link at a real access-guide section. |",
# synthetic probes of the decoy location rules
"k6-wide": "| 20 | Deviation | WCAG-2.4.11 | WCAG 2.2 SC 2.4.11 (AA) | page | `index.html:1-40` | Sticky header obscures focus on the home page. | - | - |",
"k6-narrow": "| 21 | Deviation | WCAG-2.4.11 | WCAG 2.2 SC 2.4.11 (AA) | page | `index.html:2-9` | Sticky header obscures focus on the home page. | - | - |",
"k6-evidence": "| 22 | Deviation | WCAG-2.4.11 | WCAG 2.2 SC 2.4.11 (AA) | page | `catalog.html:8` | Sticky header obscures focus. | compare `index.html:2` | - |",
"k1-list": "| 23 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (A) | page | `index.html:30`, `:52` | Divider images: text alternatives wrong. | - | - |",
"k1-review": "| 24 | Review note | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (A) | page | `index.html:52` | Divider has empty alt; confirm it is decorative. | - | - |",
}
EXPECT = [
("bw-operable", "recall-H15", "h15", True), ("bw-operable", "severity-H15", "h15", True),
("bw-operable", "nodecoy-HK3", "h15", True),   # not_contains grader: True = row does NOT hit
("wcag-operable", "recall-D19", "d19", True), ("wcag-operable", "severity-D19", "d19", True),
("wcag-operable", "nodecoy-K6", "d19", True),
("wcag-perceivable", "recall-D02", "d02", True), ("wcag-perceivable", "nodecoy-K1", "d02", True),
("bw-operable", "recall-H10", "h10", True), ("bw-operable", "nodecoy-HK5", "h10", True),
("bw-operable", "nodecoy-HK5", "bullet", True),
("wcag-operable", "nodecoy-K3", "k3", True),
("wcag-operable", "nodecoy-K6", "k6-wide", True), ("wcag-operable", "nodecoy-K6", "k6-narrow", False),
("wcag-operable", "nodecoy-K6", "k6-evidence", True),
("wcag-perceivable", "nodecoy-K1", "k1-list", False), ("wcag-perceivable", "nodecoy-K1", "k1-review", True),
]
for case, gname, key, want_pass in EXPECT:
    m, body = load(f"{EV}/plugin/cases/{case}/graders/{gname}.md")
    hit = bool(re.search(body, "intro\n" + REAL[key] + "\n", flags(m)))
    passed = (not hit) if m.get("match") == "not_contains" else hit
    checked += 1
    if passed != want_pass:
        bad += 1; print(f"regression {case}/{gname} on {key}: passed={passed} expected={want_pass}")
print(f"regex graders checked: {checked}")
print("mismatches:", bad)
sys.exit(1 if bad else 0)
