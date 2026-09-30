#!/usr/bin/env python3
"""wcag_scan.py - static source scanner for WCAG 2.2 accessibility defects.

Scans markup and component source (HTML, JSX/TSX, Vue, Svelte, server
templates, Markdown with HTML) and stylesheets (CSS/SCSS) for defects that
can be decided from source alone, and maps each finding to a WCAG 2.2
success criterion.

Standard: Web Content Accessibility Guidelines (WCAG) 2.2, W3C
Recommendation, 12 December 2024 edition, https://www.w3.org/TR/WCAG22/ .
Success-criterion names and levels are listed as facts; no normative text is
quoted here. See NOTICE for W3C document licence attribution.

Stdlib only, Python 3.9+.  Exit codes: 0 no fail findings, 1 fail findings,
2 usage or I/O error.

Severity semantics:
  fail   objective SC failure decidable from source
  warn   likely failure that needs confirmation
  manual needs a human check (listed, never counted as failed)
  info   advisory
"""

from __future__ import annotations

import argparse
import bisect
import datetime as _dt
import html as _html
import json
import os
import re
import sys
from html.parser import HTMLParser

TOOL = "wcag_scan"
VERSION = "0.1.0"
WCAG_EDITION = "2.2 (2024-12-12)"
UNDERSTANDING = "https://www.w3.org/WAI/WCAG22/Understanding/"

# ---------------------------------------------------------------------------
# WCAG 2.2 success criteria used by this scanner: id -> (name, level, slug)
# ---------------------------------------------------------------------------
SC = {
    "1.1.1": ("Non-text Content", "A", "non-text-content"),
    "1.3.1": ("Info and Relationships", "A", "info-and-relationships"),
    "1.3.5": ("Identify Input Purpose", "AA", "identify-input-purpose"),
    "1.4.1": ("Use of Color", "A", "use-of-color"),
    "1.4.2": ("Audio Control", "A", "audio-control"),
    "1.4.3": ("Contrast (Minimum)", "AA", "contrast-minimum"),
    "1.4.4": ("Resize Text", "AA", "resize-text"),
    "1.4.10": ("Reflow", "AA", "reflow"),
    "1.4.11": ("Non-text Contrast", "AA", "non-text-contrast"),
    "1.4.12": ("Text Spacing", "AA", "text-spacing"),
    "1.4.13": ("Content on Hover or Focus", "AA", "content-on-hover-or-focus"),
    "2.1.1": ("Keyboard", "A", "keyboard"),
    "2.2.1": ("Timing Adjustable", "A", "timing-adjustable"),
    "2.2.2": ("Pause, Stop, Hide", "A", "pause-stop-hide"),
    "2.4.1": ("Bypass Blocks", "A", "bypass-blocks"),
    "2.4.2": ("Page Titled", "A", "page-titled"),
    "2.4.3": ("Focus Order", "A", "focus-order"),
    "2.4.4": ("Link Purpose (In Context)", "A", "link-purpose-in-context"),
    "2.4.6": ("Headings and Labels", "AA", "headings-and-labels"),
    "2.4.7": ("Focus Visible", "AA", "focus-visible"),
    "2.4.11": ("Focus Not Obscured (Minimum)", "AA", "focus-not-obscured-minimum"),
    "2.4.12": ("Focus Not Obscured (Enhanced)", "AAA", "focus-not-obscured-enhanced"),
    "2.4.13": ("Focus Appearance", "AAA", "focus-appearance"),
    "2.5.3": ("Label in Name", "A", "label-in-name"),
    "2.5.7": ("Dragging Movements", "AA", "dragging-movements"),
    "2.5.8": ("Target Size (Minimum)", "AA", "target-size-minimum"),
    "3.1.1": ("Language of Page", "A", "language-of-page"),
    "3.1.2": ("Language of Parts", "AA", "language-of-parts"),
    "3.2.2": ("On Input", "A", "on-input"),
    "3.3.1": ("Error Identification", "A", "error-identification"),
    "3.3.2": ("Labels or Instructions", "A", "labels-or-instructions"),
    "3.3.7": ("Redundant Entry", "A", "redundant-entry"),
    "3.3.8": ("Accessible Authentication (Minimum)", "AA", "accessible-authentication-minimum"),
    "4.1.2": ("Name, Role, Value", "A", "name-role-value"),
    "4.1.3": ("Status Messages", "AA", "status-messages"),
}

LEVEL_RANK = {"A": 1, "AA": 2, "AAA": 3}
SEVERITY_RANK = {"info": 0, "manual": 1, "warn": 2, "fail": 3}

# ---------------------------------------------------------------------------
# Rule registry: rule slug -> (sc, default severity, description)
# ---------------------------------------------------------------------------
RULES = {
    # 1.1.1
    "img-missing-alt": ("1.1.1", "fail", "<img> has no alt attribute and no other accessible name"),
    "img-alt-empty-in-control": ("1.1.1", "fail", "Link or button whose only content is an image with alt=\"\" has no accessible name"),
    "img-alt-suspicious": ("1.1.1", "warn", "alt text is a file name or a placeholder word such as \"image\" or \"photo\""),
    "input-image-missing-alt": ("1.1.1", "fail", "<input type=image> has no text alternative"),
    "area-missing-alt": ("1.1.1", "fail", "<area href> has no alt text"),
    "svg-img-no-name": ("1.1.1", "fail", "<svg role=img> has no accessible name (aria-label, aria-labelledby or <title>)"),
    "button-icon-no-name": ("1.1.1", "fail", "Icon-only button has no accessible name"),
    "icon-button-component-no-name": ("1.1.1", "warn", "Icon-button component with icon-only content and no label prop"),
    "svg-icon-no-alt": ("1.1.1", "warn", "Possibly meaningful inline <svg> icon with no text alternative and no visible text beside it"),
    # 1.3.1
    "control-no-label": ("1.3.1", "fail", "Form control has no associated label (label[for], wrapping label, aria-label, aria-labelledby, title)"),
    "heading-skip": ("1.3.1", "warn", "Heading level skips one or more levels"),
    "table-no-th": ("1.3.1", "warn", "Data table has no header cells (<th>)"),
    "layout-table-with-th": ("1.3.1", "warn", "Layout table (role=presentation/none) contains <th> or <caption>"),
    "radio-group-no-fieldset": ("1.3.1", "warn", "Radio group is not grouped with fieldset/legend or role=radiogroup"),
    "li-outside-list": ("1.3.1", "fail", "<li> is not contained in <ul>, <ol> or <menu>"),
    "required-asterisk-only": ("1.3.1", "warn", "Required state is shown only by an asterisk; control lacks required/aria-required"),
    # 1.3.5
    "autocomplete-missing": ("1.3.5", "warn", "Input collecting personal data has no autocomplete token"),
    "autocomplete-invalid": ("1.3.5", "fail", "autocomplete value is not a valid HTML autofill token list"),
    # 1.4.x
    "color-only-reference": ("1.4.1", "manual", "Text refers to colour (\"shown in red\"); check the information is not conveyed by colour alone"),
    "media-autoplay-audio": ("1.4.2", "warn", "Media autoplays with sound (no muted attribute)"),
    "contrast-text": ("1.4.3", "fail", "Text/background colour contrast below 4.5:1 (3:1 for large text)"),
    "contrast-unresolved": ("1.4.3", "manual", "Text and background colours are declared but cannot be resolved statically"),
    "viewport-zoom-disabled": ("1.4.4", "fail", "Viewport meta disables zoom (user-scalable=no or maximum-scale < 2)"),
    "fixed-width-no-max": ("1.4.10", "warn", "Fixed width wider than 320 CSS px without max-width may prevent reflow"),
    "ui-border-contrast": ("1.4.11", "warn", "UI component border contrast below 3:1 against its background"),
    "focus-indicator-contrast": ("1.4.11", "warn", "Focus indicator colour contrast below 3:1 against the background"),
    "text-spacing-important": ("1.4.12", "warn", "!important on line-height/letter-spacing/word-spacing can block text-spacing overrides"),
    "hover-content-no-dismiss": ("1.4.13", "manual", "Content shown on hover/focus and hidden on mouseleave/blur with no Escape handler (check dismissible, hoverable, persistent)"),
    # 2.x
    "click-no-keyboard": ("2.1.1", "fail", "Click handler (inline, or attached by a project script: warn) on a non-interactive element without focusability and key handler"),
    "meta-refresh-delay": ("2.2.1", "fail", "Meta refresh with a delay redirects or reloads on a time limit"),
    "marquee-blink": ("2.2.2", "fail", "<marquee> or <blink> moving/blinking content cannot be paused"),
    "media-autoplay-no-controls": ("2.2.2", "warn", "Autoplaying video without controls cannot be paused"),
    "bypass-blocks-missing": ("2.4.1", "warn", "Full page has no <main> landmark and no skip link"),
    "page-title-missing": ("2.4.2", "fail", "Full page has no <title> or an empty <title>"),
    "tabindex-positive": ("2.4.3", "warn", "Positive tabindex overrides the natural focus order"),
    "link-empty": ("2.4.4", "fail", "Link has no text and no accessible name"),
    "link-icon-no-name": ("2.4.4", "fail", "Icon-only link has no accessible name"),
    "link-text-generic": ("2.4.4", "warn", "Link text such as \"click here\" or \"read more\" is not descriptive on its own"),
    "heading-empty": ("2.4.6", "fail", "Heading element has no content"),
    "focus-outline-removed": ("2.4.7", "fail", "outline removed on :focus with no alternative focus indicator"),
    "focus-outline-removed-maybe": ("2.4.7", "warn", "outline removed on interactive elements; confirm another focus style exists"),
    "focus-obscured-check": ("2.4.11", "manual", "position: fixed/sticky content can hide the focused element; check focus is not obscured"),
    "focus-obscured-enhanced-check": ("2.4.12", "manual", "position: fixed/sticky content; check no part of the focused element is hidden"),
    "focus-appearance-check": ("2.4.13", "manual", "Custom focus styles; check indicator area and 3:1 change of contrast"),
    "label-in-name": ("2.5.3", "fail", "aria-label does not contain the visible label text"),
    "drag-no-alternative": ("2.5.7", "warn", "Drag interaction without an evident single-pointer alternative"),
    "drag-library-check": ("2.5.7", "manual", "Drag-and-drop library in use; check a single-pointer alternative exists"),
    "target-size-small": ("2.5.8", "warn", "Interactive target smaller than 24x24 CSS px (check the spacing exception)"),
    # 3.x
    "html-lang-missing": ("3.1.1", "fail", "<html> has no lang attribute (or it is empty)"),
    "html-lang-invalid": ("3.1.1", "fail", "<html lang> is not a valid BCP 47 language tag"),
    "lang-invalid": ("3.1.2", "fail", "lang attribute is not a valid BCP 47 language tag"),
    "onchange-navigates": ("3.2.2", "warn", "Change of a select/radio/checkbox/input (inline handler or script listener) submits or navigates"),
    "error-not-described": ("3.3.1", "warn", "Script marks a field invalid (aria-invalid or an error class) but never writes or reveals an error message"),
    "placeholder-only-label": ("3.3.2", "fail", "Placeholder is the only label of a form control"),
    "redundant-entry": ("3.3.7", "warn", "Information already entered in an earlier step/form/page is requested again without auto-populate or a select option"),
    "redundant-entry-same-step": ("3.3.7", "manual", "Same information is requested twice in one step (confirmation field); check an exception applies"),
    "captcha-on-auth": ("3.3.8", "warn", "CAPTCHA in an authentication form; check an alternative or exception applies"),
    "paste-blocked": ("3.3.8", "fail", "Paste is blocked on an authentication field"),
    "paste-blocked-maybe": ("3.3.8", "warn", "Paste is blocked on a field (or via script)"),
    "password-autocomplete-off": ("3.3.8", "warn", "Password field has autocomplete=off, which obstructs password managers"),
    # 4.1.x
    "aria-role-invalid": ("4.1.2", "fail", "role value is not a valid WAI-ARIA 1.2 role (or is abstract)"),
    "aria-attr-invalid": ("4.1.2", "fail", "aria-* attribute is not defined in WAI-ARIA 1.2"),
    "aria-attr-value-invalid": ("4.1.2", "fail", "aria-* attribute has a value outside its allowed type"),
    "aria-required-attr": ("4.1.2", "fail", "Role is missing a required ARIA state/property"),
    "aria-hidden-focusable": ("4.1.2", "fail", "aria-hidden=\"true\" on a focusable element or an ancestor of one"),
    "aria-idref-missing": ("4.1.2", "warn", "ARIA id reference points to an id not present in the page"),
    "custom-control-no-name": ("4.1.2", "fail", "Custom control (role=button/checkbox/...) has no accessible name"),
    "button-empty": ("4.1.2", "fail", "Button has no text and no accessible name"),
    "aria-state-not-updated": ("4.1.2", "warn", "Static aria-checked/aria-pressed/aria-expanded control whose script toggles state but never updates the ARIA attribute"),
    "click-handler-no-role": ("4.1.2", "warn", "Keyboard-operable element with a click handler exposes no role"),
    "focusable-no-role": ("4.1.2", "warn", "tabindex makes a non-interactive element focusable without a role"),
    "iframe-no-title": ("4.1.2", "fail", "<iframe> has no title or accessible name"),
    "duplicate-id-referenced": ("4.1.2", "fail", "Duplicate id is referenced by for/aria-labelledby/aria-describedby (reference breaks)"),
    "status-message-no-live": ("4.1.3", "warn", "Toast/alert/notification pattern without role=status/alert or aria-live"),
    "status-message-js-no-live": ("4.1.3", "warn", "Script writes a success/error/result message into an element that has no role=status/alert/log or aria-live"),
}

# ---------------------------------------------------------------------------
# WAI-ARIA 1.2 data table (written from the W3C WAI-ARIA 1.2 Recommendation)
# ---------------------------------------------------------------------------
ARIA_ROLES = set("""
alert alertdialog application article banner blockquote button caption cell checkbox code
columnheader combobox complementary contentinfo definition deletion dialog directory document
emphasis feed figure form generic grid gridcell group heading img insertion link list listbox
listitem log main marquee math menu menubar menuitem menuitemcheckbox menuitemradio meter
navigation none note option paragraph presentation progressbar radio radiogroup region row
rowgroup rowheader scrollbar search searchbox separator slider spinbutton status strong
subscript superscript switch tab table tablist tabpanel term textbox time timer toolbar tooltip
tree treegrid treeitem
graphics-document graphics-object graphics-symbol
doc-abstract doc-acknowledgments doc-afterword doc-appendix doc-backlink doc-biblioentry
doc-bibliography doc-biblioref doc-chapter doc-colophon doc-conclusion doc-cover doc-credit
doc-credits doc-dedication doc-endnote doc-endnotes doc-epigraph doc-epilogue doc-errata
doc-example doc-footnote doc-foreword doc-glossary doc-glossref doc-index doc-introduction
doc-noteref doc-notice doc-pagebreak doc-pagefooter doc-pageheader doc-pagelist doc-part
doc-preface doc-prologue doc-pullquote doc-qna doc-subtitle doc-tip doc-toc
""".split())
ARIA_ABSTRACT_ROLES = set("command composite input landmark range roletype section sectionhead select structure widget window".split())

# attribute -> value type
#   bool, tristate, true/false/undefined (bool_u), idref, idrefs, integer, number,
#   string, token:<a|b|c>, tokens:<a|b|c>
ARIA_ATTRS = {
    "aria-activedescendant": "idref",
    "aria-atomic": "bool",
    "aria-autocomplete": "token:inline|list|both|none",
    "aria-braillelabel": "string",
    "aria-brailleroledescription": "string",
    "aria-busy": "bool",
    "aria-checked": "tristate",
    "aria-colcount": "integer",
    "aria-colindex": "integer",
    "aria-colindextext": "string",
    "aria-colspan": "integer",
    "aria-controls": "idrefs",
    "aria-current": "token:page|step|location|date|time|true|false",
    "aria-describedby": "idrefs",
    "aria-description": "string",
    "aria-details": "idrefs",
    "aria-disabled": "bool",
    "aria-dropeffect": "tokens:copy|execute|link|move|none|popup",
    "aria-errormessage": "idrefs",
    "aria-expanded": "bool_u",
    "aria-flowto": "idrefs",
    "aria-grabbed": "bool_u",
    "aria-haspopup": "token:false|true|menu|listbox|tree|grid|dialog",
    "aria-hidden": "bool_u",
    "aria-invalid": "token:grammar|false|spelling|true",
    "aria-keyshortcuts": "string",
    "aria-label": "string",
    "aria-labelledby": "idrefs",
    "aria-level": "integer",
    "aria-live": "token:assertive|off|polite",
    "aria-modal": "bool",
    "aria-multiline": "bool",
    "aria-multiselectable": "bool",
    "aria-orientation": "token:horizontal|undefined|vertical",
    "aria-owns": "idrefs",
    "aria-placeholder": "string",
    "aria-posinset": "integer",
    "aria-pressed": "tristate",
    "aria-readonly": "bool",
    "aria-relevant": "tokens:additions|all|removals|text",
    "aria-required": "bool",
    "aria-roledescription": "string",
    "aria-rowcount": "integer",
    "aria-rowindex": "integer",
    "aria-rowindextext": "string",
    "aria-rowspan": "integer",
    "aria-selected": "bool_u",
    "aria-setsize": "integer",
    "aria-sort": "token:ascending|descending|none|other",
    "aria-valuemax": "number",
    "aria-valuemin": "number",
    "aria-valuenow": "number",
    "aria-valuetext": "string",
}
IDREF_ATTRS = [a for a, t in ARIA_ATTRS.items() if t.startswith("idref")]

# Required states and properties per role (WAI-ARIA 1.2), conservative subset.
ARIA_REQUIRED = {
    "checkbox": ["aria-checked"],
    "combobox": ["aria-expanded"],
    "menuitemcheckbox": ["aria-checked"],
    "menuitemradio": ["aria-checked"],
    "meter": ["aria-valuenow"],
    "radio": ["aria-checked"],
    "scrollbar": ["aria-controls", "aria-valuenow"],
    "slider": ["aria-valuenow"],
    "switch": ["aria-checked"],
}
# Roles whose accessible name is required and may come from content.
NAME_FROM_CONTENT_ROLES = {"button", "checkbox", "link", "menuitem", "menuitemcheckbox",
                           "menuitemradio", "option", "radio", "switch", "tab", "treeitem"}
# Roles whose accessible name is required and must come from the author.
NAME_FROM_AUTHOR_ROLES = {"combobox", "searchbox", "slider", "spinbutton", "textbox", "meter", "listbox"}
INTERACTIVE_ROLES = NAME_FROM_CONTENT_ROLES | NAME_FROM_AUTHOR_ROLES | {"gridcell", "row", "scrollbar", "columnheader", "rowheader"}
LIVE_ROLES = {"status", "alert", "log", "alertdialog", "marquee", "timer"}

# ---------------------------------------------------------------------------
# HTML vocabulary
# ---------------------------------------------------------------------------
KNOWN_HTML = set("""
html head body title meta link style script noscript base template slot main header footer nav
section article aside h1 h2 h3 h4 h5 h6 hgroup address p hr pre blockquote ol ul menu li dl dt dd
figure figcaption div a em strong small s cite q dfn abbr ruby rt rp data time code var samp kbd
sub sup i b u mark bdi bdo span br wbr ins del picture source img iframe embed object param video
audio track map area table caption colgroup col tbody thead tfoot tr td th form label input button
select datalist optgroup option textarea output progress meter fieldset legend details summary
dialog canvas svg math search marquee blink center font big strike tt frame frameset noframes
acronym applet basefont dir portal
""".split())
VOID = set("area base br col embed hr img input link meta param source track wbr".split())
RAW_TEXT = {"script", "style"}
LINK_COMPONENTS = {"link", "navlink", "routerlink", "router-link", "nuxtlink", "nuxt-link",
                   "inertialink", "inertia-link", "g-link", "gatsbylink"}
ICON_COMPONENT_RE = re.compile(r"(Icon|^(Fa|Md|Io|Io5|Hi|Hi2|Bi|Ai|Fi|Ri|Tb|Bs|Gi|Gr|Si|Vsc|Lu|Pi|Im|Cg|Ci|Wi|Ti|Go|Di|Sl|Fc|Rx)[A-Z])")
ICON_CLASS_RE = re.compile(r"(^|[\s])(fa|fas|far|fab|fal|fad|fa-[\w-]+|bi|bi-[\w-]+|icon|icon-[\w-]+|[\w-]+-icon|glyphicon[\w-]*|octicon[\w-]*|ti|ti-[\w-]+|ri-[\w-]+|la|la-[\w-]+|lni[\w-]*|feather[\w-]*|codicon[\w-]*)($|[\s])")
CARD_CLASS_RE = re.compile(r"(^|\s)(?:[\w-]*[-_])?(card|tile|result|listing|product|teaser)s?(--[\w-]+)?(?=\s|$)", re.I)
BLOCK_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "ul", "ol", "dl", "table", "section", "article", "header", "footer",
              "figure", "blockquote", "details", "form", "nav", "aside", "address", "pre", "hr"}
SR_ONLY_RE = re.compile(r"(^|\s)(sr-only|visually-hidden|visuallyhidden|screen-reader-text|screenreader|a11y-hidden|assistive-text|u-hidden-visually|element-invisible|offscreen|cdk-visually-hidden)(\s|$)")
TEXT_INPUT_TYPES = {"", "text", "email", "tel", "url", "password", "search", "number", "date",
                    "datetime-local", "month", "week", "time", "color", "file", "range", "checkbox", "radio"}
NO_LABEL_TYPES = {"hidden", "submit", "button", "reset", "image"}

ISO639_1 = set("""
aa ab ae af ak am an ar as av ay az ba be bg bh bi bm bn bo br bs ca ce ch co cr cs cu cv cy da de dv
dz ee el en eo es et eu fa ff fi fj fo fr fy ga gd gl gn gu gv ha he hi ho hr ht hu hy hz ia id ie ig
ii ik io is it iu ja jv ka kg ki kj kk kl km kn ko kr ks ku kv kw ky la lb lg li ln lo lt lu lv mg mh
mi mk ml mn mr ms mt my na nb nd ne ng nl nn no nr nv ny oc oj om or os pa pi pl ps pt qu rm rn ro ru
rw sa sc sd se sg si sk sl sm sn so sq sr ss st su sv sw ta te tg th ti tk tl tn to tr ts tt tw ty ug
uk ur uz ve vi vo wa wo xh yi yo za zh zu in iw ji
""".split())
BCP47_RE = re.compile(
    r"^[a-z]{2,3}(?:-[a-z]{3}){0,3}"
    r"(?:-[a-z]{4})?"
    r"(?:-(?:[a-z]{2}|\d{3}))?"
    r"(?:-(?:[a-z0-9]{5,8}|\d[a-z0-9]{3}))*"
    r"(?:-[0-9a-wy-z](?:-[a-z0-9]{2,8})+)*"
    r"(?:-x(?:-[a-z0-9]{1,8})+)?$|^x(?:-[a-z0-9]{1,8})+$|^i-[a-z]{2,8}$",
    re.I,
)

AUTOFILL_FIELDS = set("""
name honorific-prefix given-name additional-name family-name honorific-suffix nickname username
new-password current-password one-time-code organization-title organization street-address
address-line1 address-line2 address-line3 address-level4 address-level3 address-level2
address-level1 country country-name postal-code cc-name cc-given-name cc-additional-name
cc-family-name cc-number cc-exp cc-exp-month cc-exp-year cc-csc cc-type transaction-currency
transaction-amount language bday bday-day bday-month bday-year sex url photo
""".split())
AUTOFILL_CONTACT = set("tel tel-country-code tel-national tel-area-code tel-local tel-local-prefix tel-local-suffix tel-extension email impp".split())
AUTOFILL_ALL = AUTOFILL_FIELDS | AUTOFILL_CONTACT

# (regex over name/id, suggested token). Order matters: first match wins.
PERSONAL_FIELD_HINTS = [
    (r"(^|[_\-.\[])(e-?mail)($|[_\-.\]])|^e-?mail", "email"),
    (r"(phone|mobile|^tel$|telephone|cell)", "tel"),
    (r"(first.?name|fname|given.?name|forename)", "given-name"),
    (r"(last.?name|lname|surname|family.?name)", "family-name"),
    (r"(full.?name|^name$|your.?name|^fullname$)", "name"),
    (r"(street|address.?line|addr(ess)?1?$|^address$|address1)", "street-address"),
    (r"(postal|zip|post.?code)", "postal-code"),
    (r"(^city$|locality|town)", "address-level2"),
    (r"(^country$|country.?code|country.?name)", "country"),
    (r"(card.?number|cc.?num|cardnumber|cc-number|ccnumber)", "cc-number"),
    (r"(cc.?exp|expiry|exp.?date|expiration)", "cc-exp"),
    (r"(cvc|cvv|csc|security.?code)", "cc-csc"),
    (r"(cc.?name|card.?holder|name.?on.?card)", "cc-name"),
    (r"(^user.?name$|^login$|^userid$|^user$)", "username"),
    (r"(birth|bday|dob)", "bday"),
    (r"(^company$|^organi[sz]ation$|^org$)", "organization"),
]
PERSONAL_TYPE_HINTS = {"email": "email", "tel": "tel", "password": "current-password"}

GENERIC_LINK_TEXT = {"click here", "here", "read more", "more", "learn more", "click", "this",
                     "link", "continue", "details", "more info", "more information", "go",
                     "this link", "click this", "see more", "find out more", "info", "view"}
SUSPICIOUS_ALT = {"image", "photo", "picture", "img", "graphic", "pic", "icon", "logo",
                  "spacer", "placeholder", "untitled", "alt", "thumbnail", "banner"}
FILENAME_RE = re.compile(r"\.(png|jpe?g|gif|svg|webp|avif|bmp|tiff?|ico)$", re.I)

STEP_TOKEN_RE = re.compile(r"(^|[\s_-])(step|wizard|stage)s?([\s_-]?\d+)?($|[\s_-])", re.I)
STEP_FILE_RE = re.compile(r"(step|stage|wizard|checkout|signup|register|apply|application|booking|onboard)", re.I)
STEP_TEXT_RE = re.compile(r"\bstep\s+\d+\s+(of|/)\s+\d+\b|aria-current=[\"']step[\"']", re.I)
REENTRY_SKIP_TYPES = {"hidden", "submit", "button", "reset", "image", "checkbox", "radio", "file", "range", "color", "search"}
REENTRY_CONFIRM_RE = re.compile(r"\b(confirm|repeat|retype|re-?enter|verify)\b", re.I)
REENTRY_OK_RE = re.compile(r"same as|\buse (my |the |this )?(shipping|billing|delivery|home|previous|above|saved)\b|\bcopy (from|my)\b|\bas above\b|same[_-]?as", re.I)
STATUS_CLASS_RE = re.compile(r"^(toast|toasts|toaster|snackbar|notification|notifications|flash|flash-message|flash-messages|alert|status-message|notice)$", re.I)
CAPTCHA_RE = re.compile(r"captcha|recaptcha|hcaptcha|cf-turnstile|turnstile", re.I)
NAVIGATE_RE = re.compile(r"\.submit\s*\(|requestSubmit\s*\(|location(\.href)?\s*=|location\.(assign|replace)\s*\(|window\.open\s*\(|\bnavigate\s*\(|router\.(push|replace)\s*\(|\$router\.(push|replace)|\bgoto\s*\(|\bredirect\s*\(")
DRAG_LIB_RE = re.compile(
    r"""(?:from\s+|require\s*\(\s*|import\s*\(\s*)['"](react-beautiful-dnd|@hello-pangea/dnd|@dnd-kit/[\w-]+|react-dnd|react-draggable|react-sortable-hoc|sortablejs|vuedraggable|vue-draggable-next|vue-draggable-plus|svelte-dnd-action|dragula|react-dragula|interactjs|@shopify/draggable|gridstack|react-grid-layout|react-rnd|@atlaskit/pragmatic-drag-and-drop[\w/-]*|@formkit/drag-and-drop|jquery-ui[\w/-]*)['"]"""
)
SKIP_DIRS = {"node_modules", "dist", "build", ".git", "vendor", ".cache", ".next", ".nuxt",
             ".svelte-kit", "coverage", "__pycache__", ".venv", "venv", "out", "bower_components"}

EXT_KIND = {
    ".html": "html", ".htm": "html", ".xhtml": "html",
    ".jsx": "jsx", ".tsx": "jsx", ".js": "jsx", ".mjs": "jsx",
    ".ts": "js", ".cjs": "js",
    ".vue": "vue", ".svelte": "svelte",
    ".erb": "tpl", ".hbs": "tpl", ".handlebars": "tpl", ".njk": "tpl", ".liquid": "tpl",
    ".mustache": "tpl", ".jinja": "tpl", ".jinja2": "tpl", ".j2": "tpl", ".twig": "tpl",
    ".ejs": "tpl", ".php": "tpl", ".cshtml": "tpl", ".razor": "tpl",
    ".css": "css", ".scss": "scss", ".less": "css",
    ".md": "md", ".markdown": "md", ".mdx": "md",
}

TEMPLATE_FILL = "§"  # section sign stands in for template constructs


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
class LineIndex:
    def __init__(self, text):
        self.starts = [0]
        for m in re.finditer("\n", text):
            self.starts.append(m.end())

    def pos(self, offset):
        ln = bisect.bisect_right(self.starts, offset) - 1
        return ln + 1, offset - self.starts[ln] + 1


def blank(text):
    """Replace text with spaces, keeping newlines so positions stay valid."""
    return re.sub(r"[^\n]", " ", text)


def fill(text):
    return re.sub(r"[^\n]", TEMPLATE_FILL, text)


def norm_space(s):
    return re.sub(r"\s+", " ", s or "").strip()


def norm_words(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\w]+", " ", (s or "").lower())).strip()


def literal_value(expr):
    """Return the static string value of a simple JS literal expression, or None."""
    e = (expr or "").strip()
    if not e:
        return None
    m = re.fullmatch(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'', e, re.S)
    if m:
        v = m.group(1) if m.group(1) is not None else m.group(2)
        return v.encode("utf-8").decode("unicode_escape", "ignore") if "\\" in v else v
    m = re.fullmatch(r"`([^`$\\]*)`", e, re.S)
    if m:
        return m.group(1)
    if re.fullmatch(r"-?\d+(\.\d+)?", e):
        return e
    if e in ("true", "false"):
        return e
    return None


# ---------------------------------------------------------------------------
# Document model
# ---------------------------------------------------------------------------
class Attr:
    __slots__ = ("name", "raw", "value", "dynamic", "expr", "kind")

    def __init__(self, name, raw, value, dynamic=False, expr=None, kind="attr"):
        self.name, self.raw, self.value = name, raw, value
        self.dynamic, self.expr, self.kind = dynamic, expr, kind


class Text:
    __slots__ = ("text", "dynamic", "line", "col", "parent")

    def __init__(self, text, dynamic=False, line=0, col=0):
        self.text, self.dynamic, self.line, self.col = text, dynamic, line, col
        self.parent = None


class Node:
    __slots__ = ("tag", "name", "component", "attrs", "spread", "children", "parent",
                 "line", "col", "raw_text", "raw_pos", "dyn_content", "link_like", "in_svg")

    def __init__(self, tag, line, col, component=False):
        self.tag = tag
        self.name = tag.lower()
        self.component = component
        self.attrs = {}
        self.spread = False
        self.children = []
        self.parent = None
        self.line, self.col = line, col
        self.raw_text = None
        self.raw_pos = None
        self.dyn_content = False
        self.link_like = component and self.name in LINK_COMPONENTS
        self.in_svg = False

    # attribute helpers ------------------------------------------------------
    def a(self, name):
        return self.attrs.get(name)

    def has(self, name):
        return name in self.attrs

    def sval(self, name):
        at = self.attrs.get(name)
        if at is None or at.dynamic:
            return None
        return at.value if at.value is not None else ""

    def dyn(self, name):
        at = self.attrs.get(name)
        return at is not None and at.dynamic

    def bool_attr(self, name):
        """True if a boolean attribute is set (static truthy or dynamic)."""
        at = self.attrs.get(name)
        if at is None:
            return False
        if at.dynamic:
            return True
        return (at.value or "").lower() != "false"

    def role(self):
        v = self.sval("role")
        if v is None:
            return None
        toks = v.strip().lower().split()
        for t in toks:
            if t in ARIA_ROLES:
                return t
        return toks[0] if toks else None

    def classes(self):
        v = self.sval("class")
        return v.split() if v else []

    def ancestors(self):
        p = self.parent
        while p is not None:
            yield p
            p = p.parent

    def selector(self):
        s = self.tag
        idv = self.sval("id")
        if idv and TEMPLATE_FILL not in idv:
            s += "#" + idv
        for c in self.classes()[:2]:
            if TEMPLATE_FILL not in c:
                s += "." + c
        return s


def iter_nodes(items):
    stack = list(reversed(items))
    while stack:
        n = stack.pop()
        if isinstance(n, Node):
            yield n
            stack.extend(reversed(n.children))


def link_parent(node, child):
    child.parent = node
    node.children.append(child)


def normalize_attr(raw, value, value_kind, mode):
    """Map framework attribute syntax to a DOM attribute.

    Returns an Attr or None (ignored). value_kind: 'str', 'expr' or 'none'.
    """
    n = raw
    dynamic = value_kind == "expr"
    kind = "attr"
    if mode == "jsx":
        if n == "className":
            n = "class"
        elif n == "htmlFor":
            n = "for"
        elif n == "dangerouslySetInnerHTML":
            return Attr("__html", raw, None, True, value, "content")
    nl = n.lower()
    if nl in ("v-bind", "x-bind"):
        return Attr("__spread", raw, None, True, value, "spread")
    if nl in ("v-html", "v-text", "x-html", "x-text", "innerhtml", "[innerhtml]", "textcontent", "[textcontent]"):
        return Attr("__html", raw, None, True, value, "content")
    if nl.startswith(("v-bind:", "x-bind:")):
        nl, dynamic = nl.split(":", 1)[1], True
    elif nl.startswith(":") and not nl.startswith("::"):
        nl, dynamic = nl[1:], True
    elif nl.startswith(("v-on:", "x-on:")):
        nl, kind = "on" + nl.split(":", 1)[1].split(".")[0], "handler"
    elif nl.startswith("@"):
        nl, kind = "on" + nl[1:].split(".")[0], "handler"
    elif nl.startswith("on:"):
        nl, kind = "on" + nl[3:].split("|")[0], "handler"
    elif nl.startswith("(") and nl.endswith(")"):
        nl, kind = "on" + nl[1:-1].split(".")[0], "handler"
    elif nl.startswith("[attr.") and nl.endswith("]"):
        nl, dynamic = nl[6:-1], True
    elif nl.startswith("[") and nl.endswith("]"):
        inner = nl[1:-1]
        if inner.startswith(("class.", "style.", "ngclass", "ngstyle")):
            return None
        nl, dynamic = inner, True
    elif nl in ("v-show", "v-if", "v-else-if", "x-show", "x-if"):
        return Attr(nl, raw, value, True, value, "directive")
    elif nl.startswith(("v-", "#", "bind:", "class:", "use:", "transition:", "in:", "out:",
                        "animate:", "style:", "let:", "*", "x-", "slot", "ng-", "sveltekit:")):
        return None
    if nl.startswith("on") and len(nl) > 2 and kind == "attr" and re.fullmatch(r"on[a-z]+", nl):
        kind = "handler"
    if not nl or TEMPLATE_FILL in nl or not re.fullmatch(r"[\w\-.:]+", nl):
        return Attr("__spread", raw, None, True, value, "spread")
    val = value
    if dynamic:
        lit = literal_value(value)
        if lit is not None:
            dynamic, val = False, lit
        elif mode == "jsx" and value_kind == "expr" and (value or "").strip() in ("undefined", "null"):
            return None
    elif value_kind == "none" and mode == "jsx":
        val = "true"
    if isinstance(val, str) and TEMPLATE_FILL in val:
        dynamic = True
    if kind == "handler":
        return Attr(nl, raw, val, True, value, "handler")
    return Attr(nl, raw, val, dynamic, value if dynamic else None, kind)


def add_attr(node, at):
    if at is None:
        return
    if at.kind == "spread":
        node.spread = True
        return
    if at.kind == "content":
        node.dyn_content = True
        return
    node.attrs[at.name] = at


def is_component(tag, mode, in_svg):
    if in_svg:
        return False
    if mode == "jsx":
        return not tag[:1].islower() or "." in tag
    if mode in ("vue", "svelte") and tag[:1].isupper():
        return True
    return tag.lower() not in KNOWN_HTML


IMPLIED_CLOSE = {
    "li": {"li"}, "option": {"option"}, "tr": {"tr", "td", "th"}, "td": {"td", "th"},
    "th": {"td", "th"}, "dt": {"dt", "dd"}, "dd": {"dt", "dd"},
}
P_CLOSERS = set("address article aside blockquote div dl fieldset footer form h1 h2 h3 h4 h5 h6 header hr main nav ol p pre section table ul".split())


# ---------------------------------------------------------------------------
# HTML (html.parser) tree builder
# ---------------------------------------------------------------------------
class HTMLTreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", 1, 1, component=True)
        self.stack = [self.root]

    def _top(self):
        return self.stack[-1]

    def handle_starttag(self, tag, attrs):
        self._start(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self._start(tag, attrs, True)

    def _start(self, tag, attrs, selfclose):
        line, off = self.getpos()
        low = tag.lower()
        # implied end tags
        top = self._top()
        if low in IMPLIED_CLOSE and top.name in IMPLIED_CLOSE[low]:
            self.stack.pop()
        elif low in P_CLOSERS and top.name == "p":
            self.stack.pop()
        parent = self._top()
        in_svg = parent.in_svg or parent.name in ("svg", "math")
        node = Node(tag, line, off + 1, component=is_component(tag, "html", in_svg))
        node.in_svg = in_svg
        for name, value in attrs:
            add_attr(node, normalize_attr(name, value, "none" if value is None else "str", "html"))
        link_parent(parent, node)
        if not selfclose and low not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        low = tag.lower()
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].name == low:
                del self.stack[i:]
                return

    def handle_data(self, data):
        top = self._top()
        line, off = self.getpos()
        if top.name in RAW_TEXT:
            if top.raw_text is None:
                top.raw_text, top.raw_pos = data, (line, off + 1)
            else:
                top.raw_text += data
            return
        if TEMPLATE_FILL in data:
            parts = data.split(TEMPLATE_FILL)
            static = "".join(parts)
            t = Text(static, dynamic=True, line=line, col=off + 1)
        else:
            t = Text(data, False, line, off + 1)
        link_parent(top, t)


# ---------------------------------------------------------------------------
# Tolerant markup parser for JSX / Vue / Svelte
# ---------------------------------------------------------------------------
class ParseFail(Exception):
    pass


class MarkupParser:
    NAME_RE = re.compile(r"[A-Za-z_$][\w$.:\-]*")
    ATTR_NAME_RE = re.compile(r"[^\s\"'>/={}]+")

    def __init__(self, src, mode):
        self.s = src
        self.n = len(src)
        self.mode = mode
        self.li = LineIndex(src)
        self.roots = []   # top-level nodes
        self.scripts = []  # (text, offset) of <script> bodies (vue/svelte)
        self.styles = []   # (text, offset, lang)

    def pos(self, i):
        return self.li.pos(i)

    # --- generic skipping helpers -----------------------------------------
    def skip_string(self, i):
        q = self.s[i]
        i += 1
        while i < self.n:
            c = self.s[i]
            if c == "\\":
                i += 2
                continue
            if c == q:
                return i + 1
            if c == "\n" and q != "`":
                return i + 1
            i += 1
        return self.n

    def skip_balanced(self, i):
        """i points just after an opening '{'. Return index after the matching '}'."""
        depth = 1
        while i < self.n:
            c = self.s[i]
            if c in "\"'`":
                i = self.skip_string(i)
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        raise ParseFail("unbalanced brace")

    # --- JavaScript scanning (JSX host) -----------------------------------
    KW_BEFORE_EXPR = {"return", "yield", "default", "case", "else", "do", "await", "in", "of",
                      "typeof", "void", "delete", "new", "throw"}

    def scan_js(self, i, closer, out):
        """Scan JS from i until the unmatched closer ('}' or None for EOF).

        JSX elements found in expression position are parsed and appended to
        out. Returns the index after the closer.
        """
        s, n = self.s, self.n
        stack = []
        prev = ""
        prev_word = ""
        while i < n:
            c = s[i]
            if c in " \t\r\n":
                i += 1
                continue
            if s.startswith("//", i):
                j = s.find("\n", i)
                i = n if j < 0 else j
                continue
            if s.startswith("/*", i):
                j = s.find("*/", i + 2)
                i = n if j < 0 else j + 2
                continue
            if c in "\"'":
                i = self.skip_string(i)
                prev, prev_word = "a", ""
                continue
            if c == "`":
                i = self.skip_template(i + 1, out)
                prev, prev_word = "a", ""
                continue
            if c in "([{":
                stack.append(c)
                prev, prev_word = c, ""
                i += 1
                continue
            if c in ")]}":
                if not stack:
                    if closer == c:
                        return i + 1
                    i += 1
                    prev = c
                    continue
                stack.pop()
                prev, prev_word = c, ""
                i += 1
                continue
            if c == "/":
                if prev in ("", "(", ",", "=", ":", "[", "!", "&", "|", "?", "{", "}", ";", "+", "-", "*", "%", "<", ">", "~", "^") or prev_word in self.KW_BEFORE_EXPR:
                    i = self.skip_regex(i)
                    prev, prev_word = "a", ""
                    continue
                prev, prev_word = c, ""
                i += 1
                continue
            if c == "<" and i + 1 < n and (s[i + 1].isalpha() or s[i + 1] in "_$>"):
                if prev in ("", "(", ",", "=", ":", "?", "[", "{", "}", ";", "&", "|", ">", "!") or prev_word in self.KW_BEFORE_EXPR:
                    try:
                        node, j = self.parse_jsx(i)
                    except (ParseFail, RecursionError):
                        node = None
                    if node is not None:
                        out.append(node)
                        i = j
                        prev, prev_word = ")", ""
                        continue
            if c.isalnum() or c in "_$":
                m = re.compile(r"[\w$]+").match(s, i)
                prev_word = m.group(0)
                prev = "a"
                i = m.end()
                continue
            prev, prev_word = c, ""
            i += 1
        if closer:
            raise ParseFail("unterminated expression")
        return n

    def skip_template(self, i, out):
        s, n = self.s, self.n
        while i < n:
            c = s[i]
            if c == "\\":
                i += 2
                continue
            if c == "`":
                return i + 1
            if s.startswith("${", i):
                i = self.scan_js(i + 2, "}", out)
                continue
            i += 1
        return n

    def skip_regex(self, i):
        s, n = self.s, self.n
        i += 1
        in_class = False
        while i < n:
            c = s[i]
            if c == "\\":
                i += 2
                continue
            if c == "\n":
                return i
            if in_class:
                if c == "]":
                    in_class = False
            elif c == "[":
                in_class = True
            elif c == "/":
                i += 1
                while i < n and s[i].isalpha():
                    i += 1
                return i
            i += 1
        return n

    def skip_ws_comments(self, i):
        s, n = self.s, self.n
        while i < n:
            if s[i] in " \t\r\n":
                i += 1
            elif s.startswith("/*", i):
                j = s.find("*/", i + 2)
                i = n if j < 0 else j + 2
            elif s.startswith("//", i) and self.mode == "jsx":
                j = s.find("\n", i)
                i = n if j < 0 else j
            else:
                break
        return i

    # --- JSX element --------------------------------------------------------
    def parse_jsx(self, i, parent_svg=False):
        s, n = self.s, self.n
        line, col = self.pos(i)
        j = i + 1
        if j < n and s[j] == ">":  # fragment
            node = Node("", line, col, component=True)
            node.name = "#fragment"
            j += 1
            return node, self.parse_jsx_children(node, j, "")
        m = self.NAME_RE.match(s, j)
        if not m:
            raise ParseFail("bad tag")
        tag = m.group(0)
        j = m.end()
        if j < n and s[j] not in " \t\r\n/>{":
            raise ParseFail("not jsx")
        node = Node(tag, line, col, component=is_component(tag, "jsx", parent_svg))
        node.in_svg = parent_svg
        while True:
            j = self.skip_ws_comments(j)
            if j >= n:
                raise ParseFail("eof in tag")
            c = s[j]
            if s.startswith("/>", j):
                return node, j + 2
            if c == ">":
                j += 1
                break
            if c == "{":
                sub = []
                k = self.scan_js(j + 1, "}", sub)
                node.spread = True
                j = k
                continue
            am = self.ATTR_NAME_RE.match(s, j)
            if not am:
                raise ParseFail("bad attr")
            raw = am.group(0)
            j = self.skip_ws_comments(am.end())
            if j < n and s[j] == "=":
                j = self.skip_ws_comments(j + 1)
                if j >= n:
                    raise ParseFail("eof")
                q = s[j]
                if q in "\"'":
                    k = s.find(q, j + 1)
                    if k < 0:
                        raise ParseFail("eof in attr")
                    add_attr(node, normalize_attr(raw, _html.unescape(s[j + 1:k]), "str", "jsx"))
                    j = k + 1
                elif q == "{":
                    sub = []
                    k = self.scan_js(j + 1, "}", sub)
                    expr = s[j + 1:k - 1]
                    add_attr(node, normalize_attr(raw, expr, "expr", "jsx"))
                    j = k
                elif q == "<":
                    _sub, k = self.parse_jsx(j)
                    add_attr(node, normalize_attr(raw, "<jsx>", "expr", "jsx"))
                    j = k
                else:
                    raise ParseFail("bad attr value")
            else:
                add_attr(node, normalize_attr(raw, None, "none", "jsx"))
        return node, self.parse_jsx_children(node, j, tag)

    def parse_jsx_children(self, node, j, tag):
        s, n = self.s, self.n
        child_svg = node.in_svg or node.name in ("svg", "math")
        while j < n:
            if s.startswith("</", j):
                k = s.find(">", j)
                if k < 0:
                    raise ParseFail("eof in close")
                close = s[j + 2:k].strip()
                if close != tag:
                    raise ParseFail("mismatched close")
                return k + 1
            c = s[j]
            if c == "<":
                child, k = self.parse_jsx(j, child_svg)
                link_parent(node, child)
                j = k
                continue
            if c == "{":
                line, col = self.pos(j)
                sub = []
                k = self.scan_js(j + 1, "}", sub)
                expr = s[j + 1:k - 1]
                stripped = re.sub(r"/\*.*?\*/", "", expr, flags=re.S).strip()
                if stripped:
                    lit = literal_value(stripped)
                    if lit is not None:
                        link_parent(node, Text(lit, False, line, col))
                    else:
                        link_parent(node, Text("", True, line, col))
                        for sn in sub:
                            link_parent(node, sn)
                j = k
                continue
            k = j
            while k < n and s[k] not in "<{":
                k += 1
            line, col = self.pos(j)
            link_parent(node, Text(_html.unescape(s[j:k]), False, line, col))
            j = k
        raise ParseFail("eof in children")

    # --- Vue / Svelte markup ----------------------------------------------
    def parse_markup(self, start=0, end=None):
        s = self.s
        end = self.n if end is None else end
        mode = self.mode
        root = Node("#root", 1, 1, component=True)
        stack = [root]
        i = start
        while i < end:
            top = stack[-1]
            if s.startswith("<!--", i):
                k = s.find("-->", i + 4)
                i = end if k < 0 else k + 3
                continue
            if s.startswith("</", i):
                k = s.find(">", i)
                if k < 0:
                    break
                close = s[i + 2:k].strip().lower()
                for idx in range(len(stack) - 1, 0, -1):
                    if stack[idx].name == close:
                        del stack[idx:]
                        break
                i = k + 1
                continue
            c = s[i]
            if c == "<" and i + 1 < end and (s[i + 1].isalpha()):
                try:
                    node, k, selfclose = self.parse_markup_tag(i, top)
                except ParseFail:
                    link_parent(top, Text("<", False, *self.pos(i)))
                    i += 1
                    continue
                low = node.name
                if low in IMPLIED_CLOSE and top.name in IMPLIED_CLOSE[low]:
                    stack.pop()
                elif low in P_CLOSERS and top.name == "p":
                    stack.pop()
                parent = stack[-1]
                link_parent(parent, node)
                i = k
                if low in RAW_TEXT and not selfclose:
                    m = re.compile(r"</" + re.escape(node.tag) + r"\s*>", re.I).search(s, i)
                    body_end = end if not m else m.start()
                    node.raw_text = s[i:body_end]
                    node.raw_pos = self.pos(i)
                    if low == "script":
                        self.scripts.append((node.raw_text, i))
                    else:
                        self.styles.append((node.raw_text, i, (node.sval("lang") or "css").lower()))
                    i = end if not m else m.end()
                    continue
                if not selfclose and low not in VOID:
                    stack.append(node)
                continue
            if mode == "vue" and s.startswith("{{", i):
                k = s.find("}}", i + 2)
                k = end if k < 0 else k + 2
                link_parent(top, Text("", True, *self.pos(i)))
                i = k
                continue
            if mode == "svelte" and c == "{":
                line, col = self.pos(i)
                try:
                    k = self.skip_balanced(i + 1)
                except ParseFail:
                    k = end
                inner = s[i + 1:k - 1].strip()
                if inner[:1] in ("#", ":", "/"):
                    pass  # block syntax
                else:
                    lit = literal_value(inner)
                    if lit is not None:
                        link_parent(top, Text(lit, False, line, col))
                    else:
                        link_parent(top, Text("", True, line, col))
                i = k
                continue
            k = i + 1
            stops = "<{" if mode in ("vue", "svelte") else "<"
            while k < end and s[k] not in stops:
                k += 1
            line, col = self.pos(i)
            link_parent(top, Text(_html.unescape(s[i:k]), False, line, col))
            i = k
        return root

    def parse_markup_tag(self, i, parent):
        s, n = self.s, self.n
        m = self.NAME_RE.match(s, i + 1)
        if not m:
            raise ParseFail("bad tag")
        tag = m.group(0)
        line, col = self.pos(i)
        in_svg = parent.in_svg or parent.name in ("svg", "math")
        comp = is_component(tag, self.mode, in_svg) or tag.startswith("svelte:")
        node = Node(tag, line, col, component=comp)
        node.in_svg = in_svg
        j = m.end()
        while True:
            while j < n and s[j] in " \t\r\n":
                j += 1
            if j >= n:
                raise ParseFail("eof")
            if s.startswith("/>", j):
                return node, j + 2, True
            if s[j] == ">":
                return node, j + 1, False
            if s[j] == "{" and self.mode == "svelte":
                k = self.skip_balanced(j + 1)
                inner = s[j + 1:k - 1].strip()
                if inner.startswith("..."):
                    node.spread = True
                elif re.fullmatch(r"[\w$]+", inner):
                    add_attr(node, Attr(inner.lower(), inner, None, True, inner))
                j = k
                continue
            am = self.ATTR_NAME_RE.match(s, j)
            if not am:
                j += 1
                continue
            raw = am.group(0)
            j = am.end()
            while j < n and s[j] in " \t\r\n":
                j += 1
            if j < n and s[j] == "=":
                j += 1
                while j < n and s[j] in " \t\r\n":
                    j += 1
                if j >= n:
                    raise ParseFail("eof")
                q = s[j]
                if q in "\"'":
                    k = s.find(q, j + 1)
                    if k < 0:
                        raise ParseFail("eof")
                    val = s[j + 1:k]
                    j = k + 1
                    if self.mode == "svelte" and "{" in val:
                        inner = val.strip()
                        if inner.startswith("{") and inner.endswith("}") and inner.count("{") == 1:
                            add_attr(node, normalize_attr(raw, inner[1:-1], "expr", "svelte"))
                        else:
                            add_attr(node, normalize_attr(raw, val, "expr", "svelte"))
                        continue
                    if self.mode == "vue" and (raw.startswith((":", "@", "v-"))):
                        add_attr(node, normalize_attr(raw, _html.unescape(val), "expr" if not raw.startswith("@") else "str", "vue"))
                        continue
                    add_attr(node, normalize_attr(raw, _html.unescape(val), "str", self.mode))
                elif q == "{" and self.mode == "svelte":
                    k = self.skip_balanced(j + 1)
                    add_attr(node, normalize_attr(raw, s[j + 1:k - 1], "expr", "svelte"))
                    j = k
                else:
                    k = j
                    while k < n and s[k] not in " \t\r\n>":
                        if s.startswith("/>", k):
                            break
                        k += 1
                    add_attr(node, normalize_attr(raw, s[j:k], "str", self.mode))
                    j = k
            else:
                add_attr(node, normalize_attr(raw, None, "none", self.mode))


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
class Decl:
    __slots__ = ("prop", "value", "important", "line", "col")

    def __init__(self, prop, value, important, line, col):
        self.prop, self.value, self.important, self.line, self.col = prop, value, important, line, col


class Rule:
    __slots__ = ("selector", "decls", "line", "col", "media", "file", "order")

    def __init__(self, selector, line, col, media, file):
        self.selector, self.line, self.col, self.media, self.file = selector, line, col, media, file
        self.decls = []
        self.order = 0

    def get(self, prop):
        v = None
        for d in self.decls:
            if d.prop == prop:
                v = d
        return v


def split_top(s, sep=","):
    parts, depth, cur, q = [], 0, [], None
    for ch in s:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch
        elif ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


class CSSParser:
    def __init__(self, text, file, base_line=1, base_col=1, scss=False, global_vars=None):
        self.file = file
        self.global_vars = global_vars or {}
        self.base_line, self.base_col = base_line, base_col
        text = re.sub(r"/\*.*?\*/", lambda m: blank(m.group(0)), text, flags=re.S)
        if scss:
            text = re.sub(r"(?<![:\"'/\w])//[^\n]*", lambda m: blank(m.group(0)), text)
        self.s = text
        self.n = len(text)
        self.li = LineIndex(text)
        self.vars = {}
        self.rules = []
        self.scss = scss

    def pos(self, i):
        ln, col = self.li.pos(i)
        if ln == 1:
            return self.base_line, self.base_col + col - 1
        return self.base_line + ln - 1, col

    def subst_vars(self, val):
        for _ in range(5):
            new = re.sub(r"\$[\w-]+", lambda m: self.vars.get(m.group(0), self.global_vars.get(m.group(0), m.group(0))), val)
            if new == val:
                break
            val = new
        return val

    def read_until(self, i):
        """Read from i until ';', '{' or '}' at depth 0. Return (text, index_of_stop)."""
        s, n = self.s, self.n
        depth, q = 0, None
        j = i
        while j < n:
            c = s[j]
            if q:
                if c == "\\":
                    j += 2
                    continue
                if c == q:
                    q = None
            elif c in "\"'":
                q = c
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif depth <= 0:
                if c == "#" and j + 1 < n and s[j + 1] == "{":  # scss interpolation
                    k = s.find("}", j)
                    j = n if k < 0 else k + 1
                    continue
                if c in ";{}":
                    return s[i:j], j
            j += 1
        return s[i:j], n

    def parse(self):
        self.parse_block(0, [""], None, top=True)
        for idx, r in enumerate(self.rules):
            r.order = idx
        return self.rules

    def skip_block(self, i):
        depth = 1
        s, n = self.s, self.n
        while i < n and depth:
            if s[i] == "{":
                depth += 1
            elif s[i] == "}":
                depth -= 1
            i += 1
        return i

    def parse_block(self, i, parents, media, top=False, rule=None):
        s, n = self.s, self.n
        while i < n:
            while i < n and s[i] in " \t\r\n;":
                i += 1
            if i >= n:
                return n
            if s[i] == "}":
                return i + 1
            start = i
            text, j = self.read_until(i)
            stop = s[j] if j < n else ""
            prelude = text.strip()
            lead = len(text) - len(text.lstrip())
            if stop == "{":
                if prelude.startswith("@"):
                    at = prelude.split(None, 1)[0].lower()
                    if at in ("@media", "@supports", "@layer", "@container", "@document", "@scope"):
                        i = self.parse_block(j + 1, parents, (media + " and " if media else "") + prelude, top=top)
                    else:
                        i = self.skip_block(j + 1)
                    continue
                sels = [p.strip() for p in split_top(prelude) if p.strip()]
                full = []
                for p in parents:
                    for c in sels:
                        if "&" in c:
                            full.append(c.replace("&", p).strip())
                        elif p:
                            full.append((p + " " + c).strip())
                        else:
                            full.append(c)
                line, col = self.pos(start + lead)
                r = Rule(", ".join(full), line, col, media, self.file)
                r_sel = full
                self.rules.append(r)
                i = self.parse_block(j + 1, r_sel, media, rule=r)
                continue
            # declaration or statement
            i = j + 1 if stop == ";" else j
            if not prelude:
                continue
            if prelude.startswith("$") and ":" in prelude and self.scss:
                k, v = prelude.split(":", 1)
                k = k.strip()
                if "!default" in v:
                    # overridable: resolve only when it is the project's single, unconfigured definition
                    v = v.replace("!default", "").replace("!global", "").strip()
                    if self.global_vars.get(k) != v:
                        continue
                v = v.replace("!global", "").strip()
                self.vars[k] = self.subst_vars(v)
                continue
            if prelude.startswith("@"):
                continue
            if ":" in prelude and rule is not None:
                prop, val = prelude.split(":", 1)
                prop = prop.strip().lower()
                val = val.strip()
                imp = bool(re.search(r"!\s*important\s*$", val, re.I))
                val = re.sub(r"!\s*important\s*$", "", val, flags=re.I).strip()
                if self.scss and "$" in val:
                    val = self.subst_vars(val)
                line, col = self.pos(start + lead)
                rule.decls.append(Decl(prop, val, imp, line, col))
        return n


def parse_inline_style(text, line, col):
    decls = []
    for part in split_top(text or "", ";"):
        if ":" not in part:
            continue
        prop, val = part.split(":", 1)
        imp = bool(re.search(r"!\s*important\s*$", val, re.I))
        val = re.sub(r"!\s*important\s*$", "", val, flags=re.I).strip()
        decls.append(Decl(prop.strip().lower(), val, imp, line, col))
    return decls


UNITLESS = {"line-height", "font-weight", "opacity", "z-index", "flex", "flex-grow", "flex-shrink", "order", "zoom"}


def parse_style_object(expr, line, col):
    """Parse a simple JS object literal of styles: {{ color: '#fff', width: 16 }}."""
    e = (expr or "").strip()
    if not (e.startswith("{") and e.endswith("}")):
        return None
    decls = []
    for part in split_top(e[1:-1], ","):
        part = part.strip()
        if not part:
            continue
        if part.startswith("..."):
            return None
        m = re.fullmatch(r"""["']?([\w-]+)["']?\s*:\s*(.+)""", part, re.S)
        if not m:
            continue
        key = re.sub(r"([A-Z])", lambda x: "-" + x.group(1).lower(), m.group(1))
        raw = m.group(2).strip()
        lit = literal_value(raw)
        if lit is None:
            decls.append(Decl(key, "var(--dynamic)", False, line, col))
            continue
        if re.fullmatch(r"-?\d+(\.\d+)?", lit) and key not in UNITLESS and lit != "0":
            lit += "px"
        decls.append(Decl(key, lit, False, line, col))
    return decls


NAMED_COLORS = dict(x.split(":") for x in """
aliceblue:f0f8ff antiquewhite:faebd7 aqua:00ffff aquamarine:7fffd4 azure:f0ffff beige:f5f5dc
bisque:ffe4c4 black:000000 blanchedalmond:ffebcd blue:0000ff blueviolet:8a2be2 brown:a52a2a
burlywood:deb887 cadetblue:5f9ea0 chartreuse:7fff00 chocolate:d2691e coral:ff7f50
cornflowerblue:6495ed cornsilk:fff8dc crimson:dc143c cyan:00ffff darkblue:00008b darkcyan:008b8b
darkgoldenrod:b8860b darkgray:a9a9a9 darkgreen:006400 darkgrey:a9a9a9 darkkhaki:bdb76b
darkmagenta:8b008b darkolivegreen:556b2f darkorange:ff8c00 darkorchid:9932cc darkred:8b0000
darksalmon:e9967a darkseagreen:8fbc8f darkslateblue:483d8b darkslategray:2f4f4f
darkslategrey:2f4f4f darkturquoise:00ced1 darkviolet:9400d3 deeppink:ff1493 deepskyblue:00bfff
dimgray:696969 dimgrey:696969 dodgerblue:1e90ff firebrick:b22222 floralwhite:fffaf0
forestgreen:228b22 fuchsia:ff00ff gainsboro:dcdcdc ghostwhite:f8f8ff gold:ffd700
goldenrod:daa520 gray:808080 green:008000 greenyellow:adff2f grey:808080 honeydew:f0fff0
hotpink:ff69b4 indianred:cd5c5c indigo:4b0082 ivory:fffff0 khaki:f0e68c lavender:e6e6fa
lavenderblush:fff0f5 lawngreen:7cfc00 lemonchiffon:fffacd lightblue:add8e6 lightcoral:f08080
lightcyan:e0ffff lightgoldenrodyellow:fafad2 lightgray:d3d3d3 lightgreen:90ee90 lightgrey:d3d3d3
lightpink:ffb6c1 lightsalmon:ffa07a lightseagreen:20b2aa lightskyblue:87cefa
lightslategray:778899 lightslategrey:778899 lightsteelblue:b0c4de lightyellow:ffffe0 lime:00ff00
limegreen:32cd32 linen:faf0e6 magenta:ff00ff maroon:800000 mediumaquamarine:66cdaa
mediumblue:0000cd mediumorchid:ba55d3 mediumpurple:9370db mediumseagreen:3cb371
mediumslateblue:7b68ee mediumspringgreen:00fa9a mediumturquoise:48d1cc mediumvioletred:c71585
midnightblue:191970 mintcream:f5fffa mistyrose:ffe4e1 moccasin:ffe4b5 navajowhite:ffdead
navy:000080 oldlace:fdf5e6 olive:808000 olivedrab:6b8e23 orange:ffa500 orangered:ff4500
orchid:da70d6 palegoldenrod:eee8aa palegreen:98fb98 paleturquoise:afeeee palevioletred:db7093
papayawhip:ffefd5 peachpuff:ffdab9 peru:cd853f pink:ffc0cb plum:dda0dd powderblue:b0e0e6
purple:800080 rebeccapurple:663399 red:ff0000 rosybrown:bc8f8f royalblue:4169e1
saddlebrown:8b4513 salmon:fa8072 sandybrown:f4a460 seagreen:2e8b57 seashell:fff5ee sienna:a0522d
silver:c0c0c0 skyblue:87ceeb slateblue:6a5acd slategray:708090 slategrey:708090 snow:fffafa
springgreen:00ff7f steelblue:4682b4 tan:d2b48c teal:008080 thistle:d8bfd8 tomato:ff6347
turquoise:40e0d0 violet:ee82ee wheat:f5deb3 white:ffffff whitesmoke:f5f5f5 yellow:ffff00
yellowgreen:9acd32
""".split())

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?"


def _chan(tok, scale):
    tok = tok.strip()
    if tok.endswith("%"):
        return float(tok[:-1]) * scale / 100.0
    return float(tok)


def parse_color(v):
    """Parse a CSS colour to (r, g, b, a) with r,g,b in 0..255 and a in 0..1, or None."""
    if v is None:
        return None
    v = v.strip().lower()
    if not v:
        return None
    if v in NAMED_COLORS:
        h = NAMED_COLORS[v]
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
    if v == "transparent":
        return (0, 0, 0, 0.0)
    m = re.fullmatch(r"#([0-9a-f]{3,8})", v)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) == 6:
            h += "ff"
        if len(h) != 8:
            return None
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16) / 255.0)
    m = re.fullmatch(r"(rgba?|hsla?)\((.*)\)", v)
    if not m:
        return None
    fn, args = m.group(1), m.group(2)
    if "var(" in args or "calc(" in args:
        return None
    parts = [p for p in re.split(r"[\s,/]+", args.strip()) if p]
    try:
        if fn.startswith("rgb"):
            if len(parts) not in (3, 4):
                return None
            r, g, b = (_chan(p, 255) for p in parts[:3])
            a = _chan(parts[3], 1) if len(parts) == 4 else 1.0
            return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)), max(0.0, min(1.0, a)))
        if len(parts) not in (3, 4):
            return None
        hs = parts[0]
        if hs.endswith("deg"):
            hdeg = float(hs[:-3])
        elif hs.endswith("turn"):
            hdeg = float(hs[:-4]) * 360
        elif hs.endswith("rad"):
            hdeg = float(hs[:-3]) * 57.29577951308232
        else:
            hdeg = float(hs)
        sat = float(parts[1].rstrip("%")) / 100.0
        lig = float(parts[2].rstrip("%")) / 100.0
        a = _chan(parts[3], 1) if len(parts) == 4 else 1.0
        hdeg %= 360

        def f(nn):
            k = (nn + hdeg / 30.0) % 12
            return lig - sat * min(lig, 1 - lig) * max(-1, min(k - 3, 9 - k, 1))
        return (f(0) * 255, f(8) * 255, f(4) * 255, max(0.0, min(1.0, a)))
    except ValueError:
        return None


COLOR_TOKEN_RE = re.compile(r"(#[0-9a-fA-F]{3,8}\b|(?:rgba?|hsla?)\([^)]*\)|\b[a-zA-Z]+\b)")


def background_color(value):
    """Extract the colour from a background/background-color value.

    Returns (rgba) | 'none' | None(unknown).
    """
    if value is None:
        return "none"
    v = value.strip().lower()
    if not v:
        return None
    if any(x in v for x in ("url(", "gradient", "var(", "$", "inherit", "currentcolor", "initial", "unset", "revert", "image-set", "{")):
        return None
    if v in ("none", "transparent"):
        return "none"
    if "(" in re.sub(r"(?:rgba?|hsla?)\([^()]*\)", "", v):
        return None  # other functions (darken(), color.mix(), color-mix(), calc()) are not evaluated
    c = parse_color(v)
    if c:
        return c
    found = None
    for tok in COLOR_TOKEN_RE.findall(v):
        c = parse_color(tok)
        if c:
            if found:
                return None
            found = c
    return found if found else "none"


def rel_lum(c):
    def lin(x):
        x = x / 255.0
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2])


def blend(fg, bg):
    a = fg[3]
    return (fg[0] * a + bg[0] * (1 - a), fg[1] * a + bg[1] * (1 - a), fg[2] * a + bg[2] * (1 - a), 1.0)


def contrast(c1, c2):
    l1, l2 = rel_lum(c1), rel_lum(c2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def to_px(v):
    """Convert a CSS length to px. rem/em assume 16px. Returns None when unknown."""
    if v is None:
        return None
    v = v.strip().lower()
    m = re.fullmatch(r"(" + _NUM + r")(px|pt|rem|em)?", v)
    if not m:
        return None
    num = float(m.group(1))
    unit = m.group(2) or ("px" if num == 0 else None)
    if unit is None:
        return None
    return {"px": num, "pt": num * 96 / 72, "rem": num * 16, "em": num * 16}[unit]


def is_bold(weight):
    if weight is None:
        return False
    w = weight.strip().lower()
    if w in ("bold", "bolder"):
        return True
    try:
        return float(w) >= 700
    except ValueError:
        return False


def outline_removed(decls):
    for d in decls:
        v = d.value.strip().lower()
        if d.prop == "outline" and (v in ("none", "0", "0px", "0 none", "none 0", "0 solid transparent") or re.fullmatch(r"(0|none|0px)(\s+\S+)*", v) or "transparent" in v.split()):
            return d
        if d.prop == "outline-style" and v == "none":
            return d
        if d.prop == "outline-width" and v in ("0", "0px"):
            return d
        if d.prop == "outline-color" and v == "transparent":
            return d
    return None


def has_focus_alternative(decls):
    for d in decls:
        v = d.value.strip().lower()
        if d.prop == "box-shadow" and v not in ("none", "0", ""):
            return True
        if d.prop.startswith("border") and v not in ("none", "0", "0px", "", "inherit"):
            return True
        if d.prop in ("background", "background-color") and v not in ("none", "transparent", "inherit"):
            return True
        if d.prop == "text-decoration" or d.prop == "text-decoration-line":
            if "underline" in v or "overline" in v:
                return True
        if d.prop in ("outline", "outline-style") and d.value.strip().lower() not in ("none", "0", "0px") and not v.startswith(("0 ", "none")) and "transparent" not in v:
            return True
        if d.prop == "outline-offset":
            continue
        if d.prop in ("filter", "transform") and v not in ("none", ""):
            return True
    return False


class CSSIndex:
    """Project-wide index of static CSS rules for simple selectors."""
    SIMPLE_RE = re.compile(r"^([a-zA-Z][\w-]*)?((?:[.#][\w-]+)*)$")

    def __init__(self):
        self.rules = []
        self.simple = []  # (tag, classes, id, spec, order, decls)
        self.focus_visible_bases = set()
        self.class_color_rules = 0

    def add(self, rules):
        base = len(self.rules)
        for r in rules:
            r.order += base
            self.rules.append(r)
            if "." in r.selector and any(d.prop in ("color", "background", "background-color", "border-color") for d in r.decls):
                self.class_color_rules += 1
            for sel in split_top(r.selector):
                sel = sel.strip()
                if ":focus-visible" in sel and has_focus_alternative(r.decls):
                    self.focus_visible_bases.add(focus_base(sel))
                if r.media:
                    continue
                m = self.SIMPLE_RE.match(sel)
                if not m or not sel:
                    continue
                tag = (m.group(1) or "").lower() or None
                rest = m.group(2) or ""
                classes = set(re.findall(r"\.([\w-]+)", rest))
                ids = re.findall(r"#([\w-]+)", rest)
                idv = ids[0] if ids else None
                spec = (1 if idv else 0, len(classes), 1 if tag else 0)
                self.simple.append((tag, classes, idv, spec, r.order, r.decls))

    def resolve(self, node):
        cls = set(c for c in node.classes() if TEMPLATE_FILL not in c)
        idv = node.sval("id")
        matches = []
        for tag, classes, i, spec, order, decls in self.simple:
            if tag and tag != node.name:
                continue
            if i and i != idv:
                continue
            if not classes <= cls:
                continue
            matches.append((spec, order, decls))
        matches.sort(key=lambda t: (t[0], t[1]))
        out = {}
        for spec, order, decls in matches:
            for d in decls:
                out[d.prop] = (d, "css:%d" % order)
        return out


def focus_base(sel):
    s = re.sub(r":not\([^)]*\)", "", sel)
    s = re.sub(r":focus(-visible|-within)?", "", s)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------
class Reporter:
    def __init__(self):
        self.findings = []
        self.seen = set()

    def add(self, rule, file, line, col, message, severity=None, selector="", snippet="", evidence=None, sc=None):
        sc = sc or RULES[rule][0]
        sev = severity or RULES[rule][1]
        key = (file, line, col, rule)
        if key in self.seen:
            return
        self.seen.add(key)
        name, level, slug = SC[sc]
        self.findings.append({
            "tool": TOOL,
            "id": "WCAG-" + sc,
            "sc": sc,
            "sc_name": name,
            "level": level,
            "rule": rule,
            "severity": sev,
            "file": file,
            "line": line,
            "col": col,
            "selector": selector,
            "snippet": snippet,
            "message": message,
            "help": UNDERSTANDING + slug + ".html",
            "evidence": evidence or {},
        })


# ---------------------------------------------------------------------------
# Source loading
# ---------------------------------------------------------------------------
TPL_PATTERNS = [
    re.compile(r"\{\{\{.*?\}\}\}", re.S),
    re.compile(r"\{\{.*?\}\}", re.S),
    re.compile(r"\{%.*?%\}", re.S),
    re.compile(r"\{#.*?#\}", re.S),
    re.compile(r"<%.*?%>", re.S),
    re.compile(r"<\?(?:php|=).*?\?>", re.S),
    re.compile(r"@\{.*?\}|@\(.*?\)", re.S),
]


def preprocess_template(text, kind):
    for pat in TPL_PATTERNS:
        if kind != "tpl" and pat.pattern.startswith(("<%", "<\\?", "@")):
            continue
        text = pat.sub(lambda m: fill(m.group(0)), text)
    return text


def preprocess_markdown(text):
    out = []
    in_fence = None
    for line in text.split("\n"):
        m = re.match(r"^\s{0,3}(```+|~~~+)", line)
        if in_fence:
            out.append(blank(line))
            if m and m.group(1)[0] == in_fence[0] and len(m.group(1)) >= len(in_fence):
                in_fence = None
            continue
        if m:
            in_fence = m.group(1)
            out.append(blank(line))
            continue
        line = re.sub(r"(`+)(.+?)\1", lambda mm: blank(mm.group(0)), line)
        out.append(line)
    return "\n".join(out)


class Document:
    def __init__(self, path, display, kind, text):
        self.path = path
        self.file = display
        self.kind = kind
        self.text = text
        self.lines = text.split("\n")
        self.roots = []
        self.scripts = []   # (text, abs_line, abs_col)
        self.styles = []    # (text, line, col, scss)
        self.full_page = False
        self.md_headings = []

    def snippet(self, line):
        if 1 <= line <= len(self.lines):
            s = self.lines[line - 1].strip()
            return s[:160] + ("..." if len(s) > 160 else "")
        return ""


def build_document(path, display, kind, text):
    doc = Document(path, display, kind, text)
    if kind in ("html", "tpl", "md"):
        src = text
        if kind == "md":
            src = preprocess_markdown(src)
            for i, line in enumerate(src.split("\n")):
                m = re.match(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$", line)
                if m:
                    doc.md_headings.append((len(m.group(1)), i + 1, len(line) - len(line.lstrip()) + 1, m.group(2)))
        src = preprocess_template(src, kind)
        b = HTMLTreeBuilder()
        try:
            b.feed(src)
            b.close()
        except Exception:  # html.parser is tolerant, but be safe
            pass
        doc.roots = b.root.children
        for n in b.root.children:
            n.parent = None
        for n in iter_nodes(doc.roots):
            if n.name == "script" and n.raw_text and not (n.sval("type") or "").startswith("text/x-") and TEMPLATE_FILL not in (n.sval("type") or ""):
                doc.scripts.append((n.raw_text, n.raw_pos[0], n.raw_pos[1]))
            if n.name == "style" and n.raw_text:
                doc.styles.append((n.raw_text, n.raw_pos[0], n.raw_pos[1], False))
        doc.full_page = kind != "md" and (bool(re.search(r"<html[\s>]", src, re.I)) or bool(re.search(r"<!doctype\s+html", src, re.I)))
    elif kind in ("vue", "svelte"):
        mp = MarkupParser(text, kind)
        root = mp.parse_markup()
        if kind == "vue":
            roots = []
            for ch in root.children:
                if isinstance(ch, Node) and ch.name == "template":
                    ch.parent = None
                    roots.append(ch)
            doc.roots = roots
        else:
            doc.roots = root.children
            for ch in doc.roots:
                ch.parent = None
        for txt, off in mp.scripts:
            ln, col = mp.pos(off)
            doc.scripts.append((txt, ln, col))
        for txt, off, lang in mp.styles:
            ln, col = mp.pos(off)
            doc.styles.append((txt, ln, col, lang in ("scss", "sass")))
    elif kind == "jsx":
        mp = MarkupParser(text, "jsx")
        out = []
        try:
            mp.scan_js(0, None, out)
        except (ParseFail, RecursionError):
            pass
        doc.roots = out
        doc.scripts.append((text, 1, 1))
        doc.full_page = any(n.name == "html" and not n.component for n in iter_nodes(out))
    elif kind == "js":
        doc.scripts.append((text, 1, 1))
    elif kind in ("css", "scss"):
        doc.styles.append((text, 1, 1, kind == "scss"))
    return doc


COLOR_WORDS = r"(?:red|green|blue|orange|yellow|purple|pink|grey|gray|amber)"
COLOR_REF_RE = re.compile(
    r"\b(?:shown|highlighted|marked|displayed|indicated|coloured|colored|printed|written|outlined|appears?|labell?ed|flagged)\s+in\s+(?:"
    + COLOR_WORDS + r"|colou?r)\b"
    r"|\bin\s+" + COLOR_WORDS + r"\s*(?:[.,;:)!]|$|\b(?:are|is|indicates?|means?|text|below|above)\b)"
    r"|\bcolou?r[- ]coded\b"
    r"|\b" + COLOR_WORDS + r"\s+(?:fields?|items?|rows?|dates?|text|labels?|entries|cells?|dots?|markers?|borders?)\s+(?:are|is|indicates?|means?|shows?)\b",
    re.I)
HOVER_SHOW = ("onmouseenter", "onmouseover", "onfocus", "onfocusin", "onpointerenter")
HOVER_HIDE = ("onmouseleave", "onmouseout", "onblur", "onfocusout", "onpointerleave")
ESC_RE = re.compile(r"""['"`](?:Escape|Esc)['"`]|\.esc\b|keyCode\s*[!=]==?\s*27|which\s*[!=]==?\s*27|\bkey\s*[!=]==?\s*27|\.escape\b|@keydown\.esc""", re.I)


# ---------------------------------------------------------------------------
# Accessible name approximation
# ---------------------------------------------------------------------------
class Content:
    __slots__ = ("text", "visible", "unknown", "icon", "img_empty_alt")

    def __init__(self):
        self.text, self.visible = [], []
        self.unknown = self.icon = self.img_empty_alt = False


def is_hidden(node):
    v = node.sval("aria-hidden")
    return v is not None and v.lower() == "true"


def content_of(node, acc=None, visible=True):
    acc = acc or Content()
    if node.dyn_content:
        acc.unknown = True
    for ch in node.children:
        if isinstance(ch, Text):
            if ch.dynamic:
                acc.unknown = True
            if ch.text.strip():
                acc.text.append(ch.text)
                if visible:
                    acc.visible.append(ch.text)
            continue
        if ch.component:
            if ch.name in ("#fragment",) or ch.tag.startswith("svelte:") or ch.name == "template":
                content_of(ch, acc, visible)
                continue
            if ICON_COMPONENT_RE.search(ch.tag):
                lbl = None
                for k in ("aria-label", "title", "label", "alt"):
                    at = ch.a(k)
                    if at is not None:
                        lbl = at
                        break
                if lbl is not None:
                    if lbl.dynamic:
                        acc.unknown = True
                    elif (lbl.value or "").strip():
                        acc.text.append(lbl.value)
                if is_hidden(ch) or lbl is None:
                    acc.icon = True
                continue
            acc.unknown = True
            continue
        if ch.name in ("script", "style", "template", "noscript"):
            continue
        if ch.name == "slot":
            acc.unknown = True
            continue
        if is_hidden(ch):
            acc.icon = True
            continue
        if ch.name in ("img", "area") or (ch.name == "input" and (ch.sval("type") or "").lower() == "image"):
            alt = ch.a("alt")
            if alt is None:
                if ch.a("aria-label") is not None or ch.a("aria-labelledby") is not None:
                    acc.unknown = acc.unknown or ch.dyn("aria-label")
                    v = ch.sval("aria-label")
                    if v:
                        acc.text.append(v)
                    else:
                        acc.unknown = True
                elif ch.spread:
                    acc.unknown = True
                else:
                    acc.icon = True
            elif alt.dynamic:
                acc.unknown = True
            elif not (alt.value or "").strip():
                acc.img_empty_alt = True
                acc.icon = True
            else:
                acc.text.append(alt.value)
            continue
        if ch.name == "svg":
            lab = ch.a("aria-label")
            if ch.a("aria-labelledby") is not None or (lab is not None and lab.dynamic):
                acc.unknown = True
            elif lab is not None and (lab.value or "").strip():
                acc.text.append(lab.value)
            else:
                titles = [t for t in ch.children if isinstance(t, Node) and t.name == "title"]
                if titles:
                    sub = content_of(titles[0])
                    if sub.unknown:
                        acc.unknown = True
                    acc.text.extend(sub.text)
                else:
                    acc.icon = True
            continue
        if ch.spread and not ch.children:
            acc.unknown = True
        vis = visible and not SR_ONLY_RE.search(" ".join(ch.classes()))
        before = len(acc.text)
        content_of(ch, acc, vis)
        if len(acc.text) == before and not acc.unknown:
            if ch.name in ("i", "span", "em") and (ICON_CLASS_RE.search(ch.sval("class") or "") or ch.name == "i"):
                acc.icon = True
    return acc


def author_name(node):
    """Return 'present', 'unknown' or None for aria-labelledby/aria-label/title."""
    if node.spread:
        return "unknown"
    if node.a("aria-labelledby") is not None:
        v = node.a("aria-labelledby")
        return "present" if v.dynamic or (v.value or "").strip() else None
    for k in ("aria-label", "title"):
        at = node.a(k)
        if at is not None:
            if at.dynamic or (at.value or "").strip():
                return "present"
    return None


# ---------------------------------------------------------------------------
# Markup analysis
# ---------------------------------------------------------------------------
def is_focusable(n):
    if n.component:
        return False
    if n.bool_attr("disabled") and n.name in ("button", "input", "select", "textarea"):
        return False
    ti = n.a("tabindex")
    if ti is not None:
        if ti.dynamic:
            return True
        try:
            return int((ti.value or "").strip()) >= 0
        except ValueError:
            pass
    if n.name == "a" or n.name == "area":
        return n.has("href")
    if n.name in ("button", "select", "textarea", "iframe", "summary"):
        return True
    if n.name == "input":
        return (n.sval("type") or "").lower() != "hidden"
    if n.name in ("audio", "video"):
        return n.has("controls")
    ce = n.sval("contenteditable")
    if ce is not None and ce.lower() in ("", "true", "plaintext-only"):
        return True
    return False


def self_display_none(x):
    """True when the element itself is statically removed from rendering."""
    if x.component:
        return False
    if x.has("hidden") and not x.dyn("hidden") and (x.sval("hidden") or "").lower() not in ("false", "until-found"):
        return True
    if any(c in ("hidden", "d-none", "is-hidden", "u-hidden") for c in x.classes()):
        return True
    st = x.sval("style")
    return bool(st and re.search(r"display\s*:\s*none|visibility\s*:\s*hidden", st, re.I))


def display_none_set(roots):
    """ids of nodes that are display:none themselves or through an ancestor (one pass)."""
    out = set()
    stack = [(n, False) for n in reversed(roots) if isinstance(n, Node)]
    while stack:
        n, inherited = stack.pop()
        hidden = inherited or self_display_none(n)
        if hidden:
            out.add(id(n))
        stack.extend((c, hidden) for c in reversed(n.children) if isinstance(c, Node))
    return out


def is_native_interactive(n):
    if n.name == "a":
        return n.has("href")
    return n.name in ("button", "input", "select", "textarea", "summary", "option", "label",
                      "details", "audio", "video", "iframe", "area", "optgroup", "embed", "object")


def tabindex_value(n):
    ti = n.a("tabindex")
    if ti is None or ti.dynamic:
        return None
    try:
        return int((ti.value or "").strip())
    except ValueError:
        return None


def has_handler(n, *names):
    return any(nm in n.attrs and n.attrs[nm].kind == "handler" for nm in names)


def handler_text(n, name):
    at = n.a(name)
    if at is None:
        return ""
    return at.expr if at.expr is not None else (at.value or "")


def valid_lang(v):
    v = v.strip()
    if not BCP47_RE.match(v):
        return False
    primary = v.split("-")[0].lower()
    if len(primary) == 2 and primary not in ISO639_1:
        return False
    return True


def validate_autocomplete(value):
    toks = value.lower().split()
    if toks in (["on"], ["off"]):
        return True
    if toks and toks[-1] == "webauthn":
        toks = toks[:-1]
    if not toks:
        return False
    field = toks[-1]
    if field not in AUTOFILL_ALL:
        return False
    rest = toks[:-1]
    if rest and rest[-1] in ("home", "work", "mobile", "fax", "pager"):
        if field not in AUTOFILL_CONTACT:
            return False
        rest = rest[:-1]
    if rest and rest[-1] in ("shipping", "billing"):
        rest = rest[:-1]
    if rest and rest[-1].startswith("section-"):
        rest = rest[:-1]
    return not rest


def describe_aria_type(kind):
    if kind.startswith("token:"):
        return "one of: " + ", ".join(kind[6:].split("|"))
    if kind.startswith("tokens:"):
        return "space-separated tokens from: " + ", ".join(kind[7:].split("|"))
    return {"bool": "true or false", "bool_u": "true, false or undefined",
            "tristate": "true, false, mixed or undefined", "integer": "an integer",
            "number": "a number", "idref": "an id", "idrefs": "one or more ids"}.get(kind, kind)


def check_aria_value(kind, value):
    v = value.strip().lower()
    if kind == "bool":
        return v in ("true", "false")
    if kind == "bool_u":
        return v in ("true", "false", "undefined")
    if kind == "tristate":
        return v in ("true", "false", "mixed", "undefined")
    if kind == "integer":
        return bool(re.fullmatch(r"-?\d+", v))
    if kind == "number":
        return bool(re.fullmatch(_NUM, v))
    if kind.startswith("token:"):
        return v in kind[6:].split("|")
    if kind.startswith("tokens:"):
        allowed = kind[7:].split("|")
        return bool(v.split()) and all(t in allowed for t in v.split())
    if kind in ("idref", "idrefs"):
        return bool(v)
    return True


LOGO_WORD_RE = re.compile(r"logo|wordmark|logotype", re.I)
LOGO_MSG = "possible logotype exception (1.4.3) \u2014 confirm"


def logo_reason_selector(sel):
    """Return why a CSS selector looks like it styles a logo / brand name, else None."""
    m = re.search(r"[.#][\w-]*(logo|wordmark|logotype|brand)[\w-]*", sel or "", re.I)
    return ("selector %s" % m.group(0)) if m else None


def logo_reason_node(n):
    """Logo context of a markup node: class/id/alt containing logo on it or a close ancestor,
    role=img labelled as a logo, or the brand (home) link inside <header>/role=banner."""
    chain = [n] + [a for a in n.ancestors()][:4]
    for a in chain:
        if a.component or a.name in ("body", "html", "main"):
            break
        toks = " ".join([a.sval("id") or "", " ".join(a.classes()), a.sval("alt") or ""])
        if LOGO_WORD_RE.search(toks) or re.search(r"(^|[\s_-])(navbar-)?brand([\s_-]|$)", toks, re.I):
            return "<%s> %s" % (a.name, toks.strip())
        if a.role() == "img" and LOGO_WORD_RE.search((a.sval("aria-label") or "") + " " + (a.sval("title") or "")):
            return "role=img labelled as a logo"
    link = next((a for a in [n] + list(n.ancestors()) if a.name == "a" and a.has("href")), None)
    header = next((a for a in n.ancestors() if a.name == "header" or a.role() == "banner"), None)
    if link is not None and header is not None:
        href = (link.sval("href") or "").strip()
        if (link.sval("rel") or "") == "home" or re.fullmatch(r"(\.?/)?(index\.html?)?|#(top)?|~/?", href):
            return "brand (home) link text in <header>"
    return None


def contrast_check(add, where, fgv, bgv, size_decl, weight_decl, logo=None):
    """Report text contrast for a colour pair. add(rule, where, message, severity, evidence).
    logo: reason the text may be a logotype; contrast-text is then downgraded to warn."""
    if logo:
        inner = add

        def add(rule, where_, msg, sev, ev):  # noqa: F811 - wraps the caller's reporter
            if rule == "contrast-text":
                ev = dict(ev or {}, logotype=logo)
                return inner(rule, where_, "%s: %s (%s)" % (LOGO_MSG, msg, logo), "warn", ev)
            return inner(rule, where_, msg, sev, ev)
    fgc = parse_color(fgv)
    bgc = background_color(bgv)
    if bgc == "none":
        return
    if fgc is None or bgc is None or bgc[3] < 1:
        if fgc is None and not isinstance(bgc, tuple):
            return  # nothing known on either side: not worth a manual item
        add("contrast-unresolved", where,
            "Colour pair (color: %s; background: %s) cannot be resolved statically; check contrast in the browser." % (fgv, bgv),
            None, {"color": fgv, "background": bgv})
        return
    if fgc[3] == 0:
        return
    if fgc[3] < 1:
        fgc = blend(fgc, bgc)
    ratio = contrast(fgc, bgc)
    size = to_px(size_decl.value) if size_decl else None
    bold = is_bold(weight_decl.value) if weight_decl else False
    large = size is not None and (size >= 24 or (bold and size >= 18.66))
    ev = {"ratio": round(ratio, 2), "color": fgv, "background": bgv,
          "font_size_px": round(size, 2) if size else None, "bold": bold, "large_text": large}
    if ratio < 3:
        add("contrast-text", where, "Contrast %.2f:1 (%s on %s) is below 3:1, failing even for large text." % (ratio, fgv, bgv), None, ev)
    elif ratio < 4.5:
        if large:
            return
        if size is not None:
            add("contrast-text", where, "Contrast %.2f:1 (%s on %s) is below 4.5:1 for normal-size text (%.1fpx)." % (ratio, fgv, bgv, size), None, ev)
        else:
            add("contrast-text", where,
                "Contrast %.2f:1 (%s on %s) is below 4.5:1; passes only if the text is large (>=24px, or >=18.66px bold)." % (ratio, fgv, bgv),
                "warn", ev)


class Analyzer:
    def __init__(self, reporter, css, global_label_for, global_label_dynamic):
        self.r = reporter
        self.css = css
        self.global_label_for = global_label_for
        self.global_label_dynamic = global_label_dynamic
        self.entry_by_doc = {}

    def add(self, doc, rule, node_or_pos, message, severity=None, evidence=None, sc=None):
        if isinstance(node_or_pos, Node):
            line, col, sel = node_or_pos.line, node_or_pos.col, node_or_pos.selector()
        else:
            line, col = node_or_pos
            sel = ""
        self.r.add(rule, doc.file, line, col, message, severity, sel, doc.snippet(line), evidence, sc)

    # -----------------------------------------------------------------------
    def analyze(self, doc):
        nodes = list(iter_nodes(doc.roots))
        self.ids = {}
        self.refs = set()
        self.label_for = set()
        self.label_for_dynamic = False
        self.label_text = {}
        for n in nodes:
            if n.component and not n.name.endswith("label") and n.name not in ("label",):
                pass
            idv = n.sval("id")
            if idv and not n.component and TEMPLATE_FILL not in idv:
                self.ids.setdefault(idv.strip(), []).append(n)
            if n.name == "label" or (n.component and "label" in n.name):
                if n.a("for") is not None:
                    if n.dyn("for"):
                        self.label_for_dynamic = True
                    else:
                        self.label_for.add((n.sval("for") or "").strip())
                        self.label_text[(n.sval("for") or "").strip()] = " ".join(content_of(n).text)
                        self.refs.add((n.sval("for") or "").strip())
            for a in IDREF_ATTRS + ["headers"]:
                v = n.sval(a)
                if v:
                    self.refs.update(v.split())
        hidden = display_none_set(doc.roots)
        for n in nodes:
            if n.component:
                self.component_rules(doc, n)
                continue
            if id(n) in hidden:
                continue
            self.element_rules(doc, n)
        self.document_rules(doc, nodes)
        self.inline_style_rules(doc, nodes)

    # -----------------------------------------------------------------------
    def component_rules(self, doc, n):
        # icon-button components (e.g. <IconButton><TrashIcon/></IconButton>)
        if re.search(r"IconButton$|^IconButton|ActionIcon$", n.tag) and not n.spread:
            if author_name(n) is None and not any(n.a(k) is not None for k in ("label", "tooltip", "aria-labelledby", "title", "alt")):
                c = content_of(n)
                if not c.unknown and not "".join(c.text).strip() and c.icon:
                    self.add(doc, "icon-button-component-no-name", n,
                             "%s has icon-only content and no aria-label/label prop; confirm the component renders an accessible name." % n.tag,
                             evidence={"related_sc": ["4.1.2"]})
        if n.link_like:
            self.link_rules(doc, n)

    def element_rules(self, doc, n):
        name = n.name
        role = n.role()
        # ----- 1.1.1 images ---------------------------------------------------
        if name == "img":
            alt = n.a("alt")
            if alt is None:
                if not n.spread and author_name(n) is None and role not in ("presentation", "none") and not is_hidden(n):
                    self.add(doc, "img-missing-alt", n, "<img> has no alt attribute. Add alt text, or alt=\"\" if the image is decorative.")
            elif not alt.dynamic:
                v = (alt.value or "").strip()
                src = n.sval("src") or ""
                base = os.path.basename(src.split("?")[0])
                if v and (FILENAME_RE.search(v) or v.lower() in SUSPICIOUS_ALT or (base and v == base)):
                    self.add(doc, "img-alt-suspicious", n, "alt=\"%s\" looks like a file name or placeholder, not a text alternative." % v,
                             evidence={"alt": v})
        elif name == "input" and (n.sval("type") or "").lower() == "image":
            if n.a("alt") is None and author_name(n) is None and not n.spread:
                self.add(doc, "input-image-missing-alt", n, "<input type=image> needs alt text describing its action.")
            elif n.sval("alt") is not None and not n.sval("alt").strip() and author_name(n) is None:
                self.add(doc, "input-image-missing-alt", n, "<input type=image> has empty alt; the button has no name.")
        elif name == "area" and n.has("href"):
            if (n.a("alt") is None or (n.sval("alt") is not None and not n.sval("alt").strip())) and author_name(n) is None and not n.spread:
                self.add(doc, "area-missing-alt", n, "<area href> needs non-empty alt text.")
        elif name == "svg" and role in ("img", "graphics-document", "graphics-symbol"):
            if author_name(n) is None:
                titles = [t for t in n.children if isinstance(t, Node) and t.name == "title"]
                if not titles and not is_hidden(n):
                    self.add(doc, "svg-img-no-name", n, "<svg role=\"img\"> has no aria-label, aria-labelledby or <title>.")

        elif name == "svg" and not n.in_svg:
            self.svg_icon_rule(doc, n, role)

        # ----- links / buttons -------------------------------------------------
        if name == "a" and n.has("href"):
            self.link_rules(doc, n)
        if name == "button" and role not in ("presentation", "none") and not is_hidden(n):
            self.button_rules(doc, n)
        if name == "input" and (n.sval("type") or "").lower() == "button" and not n.spread:
            if not (n.sval("value") or "").strip() and not n.dyn("value") and author_name(n) is None:
                self.add(doc, "button-empty", n, "<input type=button> has no value or accessible name.")

        # ----- 1.3.1 / 3.3.2 form labels ------------------------------------
        if name in ("input", "select", "textarea"):
            self.form_control_rules(doc, n)

        # ----- 1.3.1 headings -------------------------------------------------
        if re.fullmatch(r"h[1-6]", name) and not n.spread and author_name(n) is None and not is_hidden(n):
            c = content_of(n)
            if not c.unknown and not "".join(c.text).strip():
                self.add(doc, "heading-empty", n, "<%s> is empty; headings must describe the section they introduce." % name,
                         evidence={"related_sc": ["1.3.1"]})

        # ----- tables -----------------------------------------------------------
        if name == "table":
            self.table_rules(doc, n, role)

        # ----- li outside list -------------------------------------------------
        if name == "li" and role in (None, "listitem"):
            p = n.parent
            if p is not None and not p.component and p.name not in ("ul", "ol", "menu", "template", "slot") and p.role() not in ("list", "listbox", "menu", "menubar", "tablist", "tree", "group", "directory"):
                self.add(doc, "li-outside-list", n, "<li> is inside <%s>, not <ul>/<ol>/<menu>; list semantics are lost." % p.name,
                         evidence={"parent": p.name})

        # ----- media ------------------------------------------------------------
        if name in ("video", "audio") and n.bool_attr("autoplay"):
            if not n.bool_attr("muted"):
                self.add(doc, "media-autoplay-audio", n,
                         "<%s autoplay> without muted: if audio plays for more than 3 seconds a pause/stop or volume control is needed." % name)
            if name == "video" and not n.has("controls"):
                self.add(doc, "media-autoplay-no-controls", n,
                         "Autoplaying <video> without controls: moving content longer than 5 seconds needs a pause mechanism.")

        if name in ("marquee", "blink"):
            self.add(doc, "marquee-blink", n, "<%s> creates moving/blinking content that users cannot pause." % name)

        # ----- meta -------------------------------------------------------------
        if name == "meta":
            self.meta_rules(doc, n)

        # ----- keyboard ---------------------------------------------------------
        self.keyboard_rules(doc, n, role)

        # ----- 2.5.3 label in name ----------------------------------------------
        self.label_in_name(doc, n, role)

        # ----- 2.5.7 dragging ----------------------------------------------------
        if (n.sval("draggable") or "").lower() == "true" or has_handler(n, "ondragstart", "ondrag"):
            if has_handler(n, "onclick", "onkeydown", "onkeyup", "onpointerup"):
                self.add(doc, "drag-library-check", n,
                         "Draggable element; confirm every drag operation also works with a single pointer (e.g. click to pick and place, move buttons).",
                         severity="manual")
            else:
                self.add(doc, "drag-no-alternative", n,
                         "Draggable element with no click/key handler on it; provide a single-pointer alternative (buttons, menus) unless dragging is essential.")

        # ----- 3.1.x lang ---------------------------------------------------------
        if name == "html":
            if not n.spread:
                lang = n.a("lang") or n.a("xml:lang")
                if lang is None or (not lang.dynamic and not (lang.value or "").strip()):
                    self.add(doc, "html-lang-missing", n, "<html> needs a lang attribute naming the page's default language.")
                elif not lang.dynamic and not valid_lang(lang.value):
                    self.add(doc, "html-lang-invalid", n, "lang=\"%s\" is not a valid BCP 47 language tag." % lang.value,
                             evidence={"lang": lang.value})
        else:
            lang = n.a("lang")
            if lang is not None and not lang.dynamic and (lang.value or "").strip() and not valid_lang(lang.value):
                self.add(doc, "lang-invalid", n, "lang=\"%s\" is not a valid BCP 47 language tag." % lang.value,
                         evidence={"lang": lang.value})

        # ----- 3.2.2 ----------------------------------------------------------------
        itype = (n.sval("type") or "").lower()
        if name == "select" or (name == "input" and itype in ("radio", "checkbox")):
            for h in ("onchange", "oninput"):
                txt = handler_text(n, h)
                if txt and NAVIGATE_RE.search(txt):
                    self.add(doc, "onchange-navigates", n,
                             "Changing this control submits or navigates; warn users beforehand or use an explicit submit button.",
                             evidence={"handler": txt[:120]})

        # ----- 3.3.8 -------------------------------------------------------------------
        if name in ("input", "textarea"):
            txt = handler_text(n, "onpaste")
            if txt and re.search(r"preventDefault|return\s+false|^\s*false\s*$", txt):
                ac = (n.sval("autocomplete") or "").lower()
                ident = " ".join([(n.sval("name") or ""), (n.sval("id") or ""), ac]).lower()
                if itype == "password" or re.search(r"pass|otp|one-time-code|username|login|pin|verification|2fa|mfa", ident):
                    self.add(doc, "paste-blocked", n, "Paste is blocked on an authentication field; users must be able to paste (e.g. from a password manager).")
                else:
                    self.add(doc, "paste-blocked-maybe", n, "Paste is blocked on this field; if it is part of authentication this fails 3.3.8.")
            if itype == "password" and (n.sval("autocomplete") or "").strip().lower() == "off":
                self.add(doc, "password-autocomplete-off", n,
                         "autocomplete=\"off\" on a password field; use current-password/new-password so password managers can fill it.")

        # ----- 4.1.2 ARIA ----------------------------------------------------------------
        self.aria_rules(doc, n, role)

        if name == "iframe" and not n.spread:
            if author_name(n) is None and not is_hidden(n) and role not in ("presentation", "none"):
                self.add(doc, "iframe-no-title", n, "<iframe> needs a title attribute describing its content.")

        # ----- 4.1.3 ----------------------------------------------------------------------
        self.status_rules(doc, n, role)

        # ----- 3.3.8 captcha -------------------------------------------------------------
        if name in ("div", "img", "iframe", "input", "script", "span") and not n.spread:
            ident = " ".join(filter(None, [n.sval("class"), n.sval("id"), n.sval("src"), n.sval("name")]))
            if CAPTCHA_RE.search(ident):
                form = next((a for a in n.ancestors() if a.name == "form"), None)
                in_auth = False
                if form is not None:
                    in_auth = any((x.sval("type") or "").lower() == "password" for x in iter_nodes(form.children))
                if in_auth or re.search(r"login|signin|sign-in|auth|logon", doc.file, re.I):
                    self.add(doc, "captcha-on-auth", n,
                             "CAPTCHA in an authentication step. It passes 3.3.8 only if it is object/user-content recognition or an alternative method exists.")

    # -----------------------------------------------------------------------
    def svg_icon_rule(self, doc, n, role):
        """1.1.1: an inline <svg> that may carry meaning but has no text alternative."""
        if n.spread or role is not None or n.has("role") or author_name(n) is not None:
            return
        if any(is_hidden(a) for a in [n] + list(n.ancestors())):
            return
        kids = [d for d in iter_nodes(n.children)]
        if any(d.name in ("title", "desc", "text", "foreignobject") for d in kids):
            return
        if kids and all(d.name in ("defs", "symbol", "style", "lineargradient", "radialgradient", "stop", "clippath", "mask",
                                   "pattern", "filter", "marker") or any(a.name in ("defs", "symbol") for a in d.ancestors())
                        for d in kids):
            return  # sprite sheet / definitions only
        if not kids:
            return
        st = (n.sval("style") or "").replace(" ", "").lower()
        if "display:none" in st or (n.sval("width") or "").strip() in ("0", "0px") or (n.sval("height") or "").strip() in ("0", "0px"):
            return
        # inside a control: link/button rules own the naming decision
        for a in n.ancestors():
            if a.component:
                return
            if is_native_interactive(a) or a.role() in INTERACTIVE_ROLES or is_focusable(a):
                return
        # visible text in the same cell / list item / paragraph / heading, or the direct parent
        # climb wrappers that hold nothing but the icon (<span class="ic"><svg/></span>)
        container, inner = None, n
        for a in list(n.ancestors())[:4]:
            others = [ch for ch in a.children if ch is not inner and not (isinstance(ch, Text) and not ch.text.strip() and not ch.dynamic)]
            if others or a.name in ("td", "th", "li", "body", "main", "section", "article", "template"):
                container = a
                break
            inner = a
        if container is None:
            return
        item = container.name in ("li", "td", "th") or bool(CARD_CLASS_RE.search(" ".join(container.classes())))
        if container.name in ("body", "main", "section", "article", "template") and not item:
            return  # stand-alone illustration in a large region; too little signal
        inline, block = Content(), Content()
        block_kids = 0
        for ch in container.children:
            if ch is inner:
                continue
            if isinstance(ch, Text):
                if ch.dynamic:
                    inline.unknown = True
                if ch.text.strip():
                    inline.text.append(ch.text)
                continue
            if ch.component:
                inline.unknown = True
                continue
            acc = block if ch.name in BLOCK_TAGS else inline
            if SR_ONLY_RE.search(" ".join(ch.classes())):
                acc.text.append("sr")
                continue
            before = len(acc.text)
            content_of(ch, acc)
            if ch.name == "img" and (ch.sval("alt") or "").strip():
                acc.text.append(ch.sval("alt"))
            if acc is block and re.search(r"\w", "".join(acc.text[before:])):
                block_kids += 1
        if inline.unknown or block.unknown or re.search(r"\w", "".join(inline.text)):
            return  # label pattern: the icon sits inline beside its text
        use = next((d for d in kids if d.name == "use"), None)
        href = (use.sval("href") or use.sval("xlink:href") or "") if use is not None else ""
        where = "<%s>" % container.name
        ev = {"container": container.selector(), "use_href": href or None}
        if re.search(r"\w", "".join(block.text)):
            if not item:
                return
            repeat = self.icon_repeat(n, kids, container)
            if repeat is not None and repeat[0] == repeat[1] and block_kids <= 1:
                return  # the same icon on every item beside one line of text: a list bullet
            msg = ("Icon stands apart from the text in this item; if it conveys information (status, feature, warning), give it a text alternative: "
                   "<svg>%s in %s sits beside block text (%s) that may not say what the icon means. Add role=\"img\" with a name, or visible text, if it "
                   "carries meaning; add aria-hidden=\"true\" if it is decorative." % (
                       (" <use href=\"%s\">" % href) if href else "", where,
                       ", ".join(sorted({"<%s>" % ch.name for ch in container.children if isinstance(ch, Node) and ch is not inner and ch.name in BLOCK_TAGS}))))
            if repeat is not None and 0 < repeat[0] < repeat[1]:
                msg += " The same icon appears in only %d of %d items in this list, which suggests it marks a property of those items." % repeat
                ev["icon_in_items"] = "%d/%d" % repeat
            ev["stands_apart"] = True
            self.add(doc, "svg-icon-no-alt", n, msg, evidence=ev)
            return
        self.add(doc, "svg-icon-no-alt", n,
                 "Possibly meaningful icon with no text alternative: <svg>%s in %s has no role=\"img\", aria-label/aria-labelledby, <title> or aria-hidden=\"true\", and no visible text beside it. "
                 "Add role=\"img\" with a name (or visible text) if it conveys information; add aria-hidden=\"true\" if it is decorative." % (
                     (" <use href=\"%s\">" % href) if href else "", where),
                 evidence=ev)

    @staticmethod
    def icon_key(svg, kids=None):
        kids = kids if kids is not None else list(iter_nodes(svg.children))
        use = next((d for d in kids if d.name == "use"), None)
        if use is not None:
            h = use.sval("href") or use.sval("xlink:href")
            if h:
                return "use:" + h.strip()
        cls = " ".join(sorted(c for c in svg.classes() if TEMPLATE_FILL not in c))
        if cls:
            return "class:" + cls
        path = next((d for d in kids if d.name == "path" and d.sval("d")), None)
        return "path:" + path.sval("d").strip() if path is not None else None

    def icon_repeat(self, svg, kids, container):
        """(items holding the same icon, items) among the container's sibling items, or None."""
        key = self.icon_key(svg, kids)
        if key is None or container.parent is None:
            return None
        if container.name == "li":
            items = [c for c in container.parent.children if isinstance(c, Node) and c.name == "li"]
        elif container.name in ("td", "th"):
            return None
        else:
            cls = container.classes()[:1]
            items = [c for c in container.parent.children if isinstance(c, Node) and c.name == container.name and c.classes()[:1] == cls]
        if len(items) < 2:
            return None
        hits = 0
        for it in items:
            if any(d.name == "svg" and not is_hidden(d) and self.icon_key(d) == key for d in iter_nodes(it.children)):
                hits += 1
        return hits, len(items)

    # -----------------------------------------------------------------------
    def link_rules(self, doc, n):
        if n.spread or is_hidden(n):
            return
        an = author_name(n)
        c = content_of(n)
        text = norm_space(" ".join(c.text))
        if an is None:
            if c.unknown:
                return
            if not text:
                if c.img_empty_alt:
                    self.add(doc, "img-alt-empty-in-control", n,
                             "Link contains only an image with alt=\"\"; give the image alt text describing the link destination.",
                             evidence={"related_sc": ["2.4.4", "4.1.2"]})
                elif c.icon:
                    self.add(doc, "link-icon-no-name", n,
                             "Icon-only link has no accessible name; add aria-label or visually hidden text.",
                             evidence={"related_sc": ["1.1.1", "4.1.2"]})
                else:
                    self.add(doc, "link-empty", n, "Link has no text or accessible name.", evidence={"related_sc": ["4.1.2"]})
                return
        # generic text
        name_text = text
        if n.a("aria-label") is not None:
            name_text = n.sval("aria-label") or ""
            if n.dyn("aria-label"):
                return
        if n.a("aria-labelledby") is not None or n.a("aria-describedby") is not None:
            return
        if n.sval("title") and norm_words(n.sval("title")) not in GENERIC_LINK_TEXT:
            return
        if norm_words(name_text) in GENERIC_LINK_TEXT and not c.unknown:
            self.add(doc, "link-text-generic", n,
                     "Link text \"%s\" does not describe its purpose; make it descriptive or ensure the surrounding sentence/list item does." % norm_space(name_text),
                     evidence={"text": norm_space(name_text)})

    def button_rules(self, doc, n):
        if n.spread:
            return
        if author_name(n) is not None:
            return
        c = content_of(n)
        if c.unknown or "".join(c.text).strip():
            return
        if c.img_empty_alt:
            self.add(doc, "img-alt-empty-in-control", n,
                     "Button contains only an image with alt=\"\"; give the image alt text describing the action.",
                     evidence={"related_sc": ["4.1.2"]})
        elif c.icon:
            self.add(doc, "button-icon-no-name", n,
                     "Icon-only button has no accessible name; add aria-label or visually hidden text.",
                     evidence={"related_sc": ["4.1.2"]})
        else:
            self.add(doc, "button-empty", n, "Button has no text or accessible name.")

    def form_control_rules(self, doc, n):
        itype = (n.sval("type") or "").lower() if n.name == "input" else ""
        if n.name == "input" and n.dyn("type"):
            return
        if n.spread:
            return
        if n.name == "input" and itype in NO_LABEL_TYPES:
            pass
        else:
            labelled = author_name(n) is not None
            if not labelled:
                for a in n.ancestors():
                    if a.name == "label" or (a.component and ("label" in a.name or "field" in a.name or any("label" in k for k in a.attrs))):
                        labelled = True
                        break
            idv = n.a("id")
            if not labelled and idv is not None:
                if idv.dynamic:
                    labelled = True
                else:
                    key = (idv.value or "").strip()
                    if key in self.label_for or key in self.global_label_for:
                        labelled = True
                    elif self.label_for_dynamic or self.global_label_dynamic:
                        labelled = True  # cannot resolve dynamic label targets
            if not labelled and is_hidden(n):
                labelled = True
            if not labelled:
                if n.a("placeholder") is not None:
                    self.add(doc, "placeholder-only-label", n,
                             "Placeholder is the only label; it disappears on input and is not a reliable accessible name. Add a <label>.",
                             evidence={"related_sc": ["1.3.1", "4.1.2"], "placeholder": n.sval("placeholder")})
                else:
                    self.add(doc, "control-no-label", n,
                             "<%s%s> has no programmatically associated label." % (n.name, (" type=" + itype) if itype else ""),
                             evidence={"related_sc": ["3.3.2", "4.1.2"]})
        # 1.3.5 autocomplete
        if n.name in ("input", "select", "textarea") and itype not in ("hidden", "submit", "button", "reset", "image", "checkbox", "radio", "file", "range", "color"):
            ac = n.a("autocomplete")
            if ac is not None and not ac.dynamic:
                v = (ac.value or "").strip()
                if v and not validate_autocomplete(v):
                    self.add(doc, "autocomplete-invalid", n, "autocomplete=\"%s\" is not a valid autofill token list." % v,
                             evidence={"autocomplete": v})
            if ac is None or (not ac.dynamic and (ac.value or "").strip().lower() == "off"):
                hint = PERSONAL_TYPE_HINTS.get(itype)
                ident = [(n.sval("name") or "").lower(), (n.sval("id") or "").lower()]
                if hint is None:
                    for pat, tok in PERSONAL_FIELD_HINTS:
                        if any(x and re.search(pat, x) for x in ident):
                            hint = tok
                            break
                if hint and itype != "search" and not (itype == "password" and ac is not None):
                    if itype == "password":
                        hint = "current-password or new-password"
                    self.add(doc, "autocomplete-missing", n,
                             "Field appears to collect personal data (%s) but has %s; add autocomplete=\"%s\" if it is about the user." % (
                                 hint, "autocomplete=\"off\"" if ac is not None else "no autocomplete", hint),
                             evidence={"suggested": hint})

    def table_rules(self, doc, n, role):
        rows = []
        has_th = has_caption = False
        stack = list(n.children)
        while stack:
            x = stack.pop()
            if not isinstance(x, Node):
                continue
            if x.name == "table":
                continue
            if x.name == "tr":
                rows.append(x)
            if x.name == "th" or x.role() in ("columnheader", "rowheader"):
                has_th = True
            if x.name == "caption":
                has_caption = True
            if x.component:
                return
            stack.extend(x.children)
        if role in ("presentation", "none"):
            if has_th or has_caption:
                self.add(doc, "layout-table-with-th", n, "Table has role=\"%s\" but contains header/caption markup; decide whether it is data or layout." % role)
            return
        cells = [sum(1 for c in r.children if isinstance(c, Node) and c.name in ("td", "th")) for r in rows]
        if len(rows) >= 2 and cells and max(cells) >= 2 and not has_th:
            self.add(doc, "table-no-th", n, "Table with %d rows has no <th> header cells; mark up headers or use CSS layout." % len(rows))

    def meta_rules(self, doc, n):
        nm = (n.sval("name") or "").lower()
        content = n.sval("content")
        if nm == "viewport" and content:
            kv = {}
            for part in re.split(r"[,;]", content):
                if "=" in part:
                    k, v = part.split("=", 1)
                    kv[k.strip().lower()] = v.strip().lower()
            us = kv.get("user-scalable")
            ms = kv.get("maximum-scale")
            bad = []
            if us in ("no", "0"):
                bad.append("user-scalable=" + us)
            if ms:
                try:
                    if float(ms) < 2:
                        bad.append("maximum-scale=" + ms)
                except ValueError:
                    pass
            if bad:
                self.add(doc, "viewport-zoom-disabled", n,
                         "Viewport meta blocks zoom (%s); users must be able to resize text to 200%%." % ", ".join(bad),
                         evidence={"content": content})
        he = (n.sval("http-equiv") or "").lower()
        if he == "refresh" and content:
            m = re.match(r"\s*(\d+(?:\.\d+)?)", content)
            if m:
                secs = float(m.group(1))
                if 0 < secs <= 72000:
                    self.add(doc, "meta-refresh-delay", n,
                             "<meta http-equiv=refresh> after %g s imposes a time limit users cannot adjust." % secs,
                             evidence={"content": content, "related_sc": ["3.2.5"]})

    def keyboard_rules(self, doc, n, role):
        tv = tabindex_value(n)
        if tv is not None and tv > 0:
            self.add(doc, "tabindex-positive", n, "tabindex=\"%d\" forces a focus order that rarely matches the visual order; use 0 or -1." % tv)
        if n.spread or is_native_interactive(n) or n.name in ("html", "body", "svg", "form", "label"):
            return
        clickable = has_handler(n, "onclick", "onmousedown", "onmouseup", "onpointerdown", "onpointerup", "ondblclick")
        has_role = role in INTERACTIVE_ROLES or n.dyn("role")
        focusable = is_focusable(n) or n.dyn("tabindex")
        has_key = has_handler(n, "onkeydown", "onkeyup", "onkeypress")
        if clickable:
            if is_hidden(n) or role in ("presentation", "none"):
                return
            # event delegation: a real control inside handles the keyboard
            if any(is_focusable(d) or d.component for d in iter_nodes(n.children)):
                return
            missing = []
            if not focusable:
                missing.append("tabindex=\"0\"")
            if not has_key:
                missing.append("a keydown handler (Enter/Space)")
            if missing:
                c = content_of(n)
                has_content = n.name in ("img", "svg") or c.unknown or c.icon or bool("".join(c.text).strip())
                self.add(doc, "click-no-keyboard", n,
                         "<%s> has a click handler but no %s; keyboard users cannot activate it. Prefer a <button>." % (n.name, " or ".join(missing)),
                         severity="fail" if has_content else "warn",
                         evidence={"missing": missing, "role": role})
            elif not has_role:
                self.add(doc, "click-handler-no-role", n,
                         "<%s> is keyboard-operable but exposes no role; add role=\"button\" (or use <button>)." % n.name)
        elif tv is not None and tv >= 0 and role is None and not n.has("role"):
            self.add(doc, "focusable-no-role", n,
                     "tabindex makes <%s> focusable but it has no role; screen readers announce nothing meaningful (fine for scrollable regions with an accessible name)." % n.name)

    def label_in_name(self, doc, n, role):
        interactive = (n.name == "a" and n.has("href")) or n.name == "button" or role in NAME_FROM_CONTENT_ROLES
        if not interactive or n.spread:
            return
        lab = n.sval("aria-label")
        if not lab or not lab.strip() or n.a("aria-labelledby") is not None:
            return
        c = content_of(n)
        if c.unknown:
            return
        vis = norm_words(" ".join(c.visible))
        if len(vis.replace(" ", "")) < 2:
            return
        if vis not in norm_words(lab):
            self.add(doc, "label-in-name", n,
                     "Visible label \"%s\" is not contained in aria-label \"%s\"; speech-input users say what they see." % (norm_space(" ".join(c.visible)), lab),
                     evidence={"visible": norm_space(" ".join(c.visible)), "aria_label": lab})

    def aria_rules(self, doc, n, role):
        rv = n.sval("role")
        if rv is not None and rv.strip():
            toks = rv.strip().lower().split()
            valid = [t for t in toks if t in ARIA_ROLES]
            abstract = [t for t in toks if t in ARIA_ABSTRACT_ROLES]
            if not valid:
                msg = "role=\"%s\" is not a valid WAI-ARIA role" % rv
                if abstract:
                    msg += " (abstract roles must not be used in content)"
                self.add(doc, "aria-role-invalid", n, msg + ".", evidence={"role": rv})
            elif toks[0] not in ARIA_ROLES:
                self.add(doc, "aria-role-invalid", n, "role=\"%s\": first token is invalid; the fallback role will be used." % rv,
                         severity="warn", evidence={"role": rv})
        for name, at in n.attrs.items():
            if not name.startswith("aria-"):
                continue
            kind = ARIA_ATTRS.get(name)
            if kind is None:
                self.add(doc, "aria-attr-invalid", n, "%s is not a WAI-ARIA 1.2 attribute." % name, evidence={"attribute": name})
                continue
            if at.dynamic or at.value is None:
                continue
            if not check_aria_value(kind, at.value):
                sev = "warn" if name == "aria-invalid" else None
                self.add(doc, "aria-attr-value-invalid", n, "%s=\"%s\" is not an allowed value (expected %s)." % (name, at.value, describe_aria_type(kind)),
                         severity=sev, evidence={"attribute": name, "value": at.value})
            if kind.startswith("idref") and doc.full_page and doc.kind in ("html", "tpl") and not n.spread:
                missing = [t for t in at.value.split() if t not in self.ids]
                if missing:
                    self.add(doc, "aria-idref-missing", n, "%s references id(s) not found in this page: %s." % (name, ", ".join(missing)),
                             evidence={"attribute": name, "missing": missing})
        # required attributes
        if role in ARIA_REQUIRED and not n.spread:
            itype = (n.sval("type") or "").lower()
            native = (n.name == "input" and itype in ("checkbox", "radio") and role in ("checkbox", "switch", "radio", "menuitemcheckbox", "menuitemradio")) \
                or (n.name == "input" and itype in ("range", "number") and role in ("slider", "spinbutton", "scrollbar")) \
                or (n.name == "meter" and role == "meter") \
                or (n.name == "select" and role == "combobox") \
                or (n.name == "input" and role == "combobox" and n.has("list"))
            if not native:
                missing = [a for a in ARIA_REQUIRED[role] if a not in n.attrs]
                if missing:
                    self.add(doc, "aria-required-attr", n, "role=\"%s\" requires %s." % (role, ", ".join(missing)),
                             evidence={"role": role, "missing": missing})
        # custom control name
        if role in (NAME_FROM_CONTENT_ROLES | NAME_FROM_AUTHOR_ROLES) and not n.spread and not is_native_interactive(n) and not is_hidden(n):
            if author_name(n) is None:
                idv = n.sval("id")
                labelled = bool(idv and (idv in self.label_for or idv in self.global_label_for))
                if not labelled:
                    if role in NAME_FROM_AUTHOR_ROLES:
                        self.add(doc, "custom-control-no-name", n, "role=\"%s\" needs aria-label or aria-labelledby." % role, evidence={"role": role})
                    else:
                        c = content_of(n)
                        if not c.unknown and not "".join(c.text).strip():
                            self.add(doc, "custom-control-no-name", n, "role=\"%s\" has no accessible name (no text, aria-label or aria-labelledby)." % role,
                                     evidence={"role": role, "icon_only": c.icon})
        # aria-hidden on focusable
        if is_hidden(n):
            if is_focusable(n):
                self.add(doc, "aria-hidden-focusable", n, "aria-hidden=\"true\" on a focusable element: keyboard focus lands on something screen readers cannot perceive.")
            else:
                for d in iter_nodes(n.children):
                    if is_focusable(d) and tabindex_value(d) != -1 and not d.bool_attr("inert"):
                        self.add(doc, "aria-hidden-focusable", n,
                                 "aria-hidden=\"true\" container has a focusable descendant <%s> (line %d); add tabindex=\"-1\"/inert or remove aria-hidden." % (d.name, d.line),
                                 evidence={"descendant": d.selector(), "descendant_line": d.line})
                        break

    def status_rules(self, doc, n, role):
        toks = [c for c in n.classes() if STATUS_CLASS_RE.match(c)]
        idv = (n.sval("id") or "")
        if not toks and not STATUS_CLASS_RE.match(idv or "-"):
            return
        if n.spread or role in LIVE_ROLES or n.has("aria-live") or n.dyn("role"):
            return
        for a in n.ancestors():
            if a.role() in LIVE_ROLES or a.has("aria-live") or any(STATUS_CLASS_RE.match(c) for c in a.classes()):
                return
        for d in iter_nodes(n.children):
            if d.role() in LIVE_ROLES or d.has("aria-live"):
                return
        self.add(doc, "status-message-no-live", n,
                 "Looks like a status/notification container (%s) with no role=\"status\"/\"alert\" or aria-live; if it is injected or updated dynamically, screen readers will not announce it." % ", ".join(toks or [idv]))

    # -----------------------------------------------------------------------
    def document_rules(self, doc, nodes):
        # headings order
        heads = []
        for n in nodes:
            if n.component:
                continue
            m = re.fullmatch(r"h([1-6])", n.name)
            lvl = None
            if m and n.role() in (None, "heading"):
                lvl = int(m.group(1))
                al = n.sval("aria-level")
                if al and al.isdigit():
                    lvl = int(al)
            elif n.role() == "heading":
                al = n.sval("aria-level")
                if al and al.isdigit():
                    lvl = int(al)
            if lvl:
                heads.append((n.line, n.col, lvl, n))
        for lvl, line, col, _t in doc.md_headings:
            heads.append((line, col, lvl, None))
        heads.sort(key=lambda t: (t[0], t[1]))
        prev = None
        for line, col, lvl, node in heads:
            if prev is not None and lvl > prev + 1:
                self.add(doc, "heading-skip", node if node is not None else (line, col),
                         "Heading level jumps from h%d to h%d; skipped levels break the document outline." % (prev, lvl),
                         evidence={"from": prev, "to": lvl})
            prev = lvl
        # radio groups
        groups = {}
        for n in nodes:
            if n.name == "input" and not n.component and (n.sval("type") or "").lower() == "radio":
                nm = n.sval("name")
                if nm and TEMPLATE_FILL not in nm:
                    groups.setdefault(nm, []).append(n)
        for nm, radios in groups.items():
            if len(radios) < 2:
                continue
            grouped = False
            for a in radios[0].ancestors():
                if a.name == "fieldset" or a.role() in ("radiogroup", "group") or a.component:
                    grouped = True
                    break
            if not grouped:
                self.add(doc, "radio-group-no-fieldset", radios[0],
                         "Radio buttons name=\"%s\" are not grouped; wrap them in <fieldset> with a <legend> (or role=radiogroup with a name)." % nm)
        # duplicate ids referenced
        for idv, lst in self.ids.items():
            if len(lst) > 1 and idv in self.refs:
                sev = "fail" if doc.kind in ("html", "tpl", "md") else "warn"
                self.add(doc, "duplicate-id-referenced", lst[1],
                         "id=\"%s\" is used %d times and is referenced by a label/ARIA attribute; the reference resolves to the first only." % (idv, len(lst)),
                         severity=sev, evidence={"id": idv, "lines": [x.line for x in lst], "related_sc": ["1.3.1"], "note": "4.1.1 Parsing is obsolete in WCAG 2.2; broken references still fail 1.3.1/4.1.2"})
        # required asterisk
        for n in nodes:
            if n.name != "label" or n.component:
                continue
            c = content_of(n)
            txt = " ".join(c.text)
            if "*" not in txt or re.search(r"required", txt, re.I):
                continue
            ctl = None
            f = n.sval("for")
            if f and f in self.ids:
                ctl = self.ids[f][0]
            else:
                for d in iter_nodes(n.children):
                    if d.name in ("input", "select", "textarea"):
                        ctl = d
                        break
            if ctl is not None and not ctl.spread and not ctl.has("required") and not ctl.has("aria-required"):
                self.add(doc, "required-asterisk-only", ctl,
                         "Label marks the field required with \"*\" but the control has no required/aria-required attribute.")
        # 3.3.7 redundant entry across forms / step sections in a file
        self.redundant_entry(doc, nodes)
        # 1.4.1 text that points at colour ("fields shown in red")
        self.color_reference(doc, nodes)
        # 1.4.13 hover/focus content in component markup (Vue @mouseenter, inline onmouseover)
        self.hover_markup(doc, nodes)
        # full page rules
        if doc.full_page and doc.kind in ("html", "tpl"):
            titles = [n for n in nodes if n.name == "title" and not n.in_svg and not n.component]
            html_node = next((n for n in nodes if n.name == "html"), None)
            anchor = html_node or (nodes[0] if nodes else (1, 1))
            if not titles:
                self.add(doc, "page-title-missing", anchor, "Page has no <title> element.")
            else:
                c = content_of(titles[0])
                if not c.unknown and not "".join(c.text).strip():
                    self.add(doc, "page-title-missing", titles[0], "<title> is empty.")
            has_main = any(n.name == "main" or n.role() == "main" for n in nodes)
            links = [n for n in nodes if n.name == "a" and n.has("href")]
            skip = False
            for i, a in enumerate(links):
                href = a.sval("href") or ""
                txt = " ".join(content_of(a).text)
                if (href.startswith("#") and len(href) > 1 and i < 3) or re.search(r"skip|jump to|main content", txt, re.I):
                    skip = True
                    break
            navigable = links or any(n.name in ("nav", "header") for n in nodes)
            if not has_main and not skip and navigable:
                body = next((n for n in nodes if n.name == "body"), anchor)
                self.add(doc, "bypass-blocks-missing", body, "No <main> landmark and no skip link; keyboard users cannot bypass repeated blocks.")

    # -----------------------------------------------------------------------
    def color_reference(self, doc, nodes):
        if not self.css or not self.css.class_color_rules:
            return
        done = set()
        for n in nodes:
            if n.component or n.name in ("script", "style", "code", "pre", "kbd", "samp", "template") or n.in_svg:
                continue
            if any(a.name in ("code", "pre") for a in n.ancestors()):
                continue
            for ch in n.children:
                if not isinstance(ch, Text) or not ch.text.strip():
                    continue
                m = COLOR_REF_RE.search(ch.text)
                if not m or ch.line in done:
                    continue
                done.add(ch.line)
                phrase = norm_space(m.group(0)).strip(" .,;:!)")
                self.add(doc, "color-only-reference", (ch.line, ch.col),
                         "Text refers to colour (\"%s\") and the page styles states with classes; check the same information is also given by text, an icon/shape or a pattern, not by colour alone." % phrase,
                         evidence={"phrase": phrase, "element": n.selector()})

    def hover_markup(self, doc, nodes):
        """1.4.13 for handler attributes: show on mouseenter/focus, hide on mouseleave/blur, no Escape."""
        if doc.kind not in ("vue", "svelte", "jsx", "html", "tpl"):
            return
        scripts = " ".join(t for t, _l, _c in doc.scripts)
        for n in nodes:
            if n.component and not n.link_like:
                continue
            show = [h for h in HOVER_SHOW if has_handler(n, h)]
            hide = [h for h in HOVER_HIDE if has_handler(n, h)]
            if not show or not hide:
                continue
            if ESC_RE.search(scripts):
                continue
            # popup toggled by the handler: v-show/v-if on an element whose expression uses the same variable
            names = set()
            for h in show:
                names.update(re.findall(r"([A-Za-z_$][\w$.]*)\s*=(?!=)", handler_text(n, h)))
                names.update(re.findall(r"^\s*([A-Za-z_$][\w$]*)\s*\(", handler_text(n, h)))
            popup = None
            for d in nodes:
                for k in ("v-show", "v-if", "x-show"):
                    at = d.a(k)
                    if at is not None and any(re.search(r"(^|[^\w$.])" + re.escape(nm.split(".")[-1]) + r"\b", at.value or "") for nm in names):
                        popup = d
                        break
                if popup is not None:
                    break
            chain = [n] + list(n.ancestors()) + list(iter_nodes(n.children))
            if popup is not None:
                chain += [popup] + list(iter_nodes(popup.children))
            if any(ESC_RE.search(" ".join((at.raw or "") + " " + (at.expr or at.value or "") for at in a.attrs.values() if at.kind == "handler")) for a in chain):
                continue
            hover_note = ""
            if any(h in ("onmouseleave", "onmouseout") for h in hide):
                if popup is not None and n not in popup.ancestors() and popup not in list(iter_nodes(n.children)):
                    hover_note = " The mouseleave handler is on the trigger only and the popup (line %d) is outside it, so the pointer cannot move onto the popup without it closing (not hoverable)." % popup.line
                elif popup is None:
                    hover_note = " Check the popup stays open while the pointer moves onto it (hoverable)."
            self.add(doc, "hover-content-no-dismiss", n,
                     "Content appears on %s and disappears on %s, but there is no Escape key handler to dismiss it without moving pointer or focus.%s Check dismissible, hoverable and persistent." % (
                         "/".join(h[2:] for h in show), "/".join(h[2:] for h in hide), hover_note),
                     evidence={"show": show, "hide": hide, "popup_line": popup.line if popup is not None else None})

    # -----------------------------------------------------------------------
    # 3.3.7 Redundant Entry
    def label_of(self, n):
        v = n.sval("aria-label")
        if v and v.strip():
            return v
        idv = (n.sval("id") or "").strip()
        if idv and idv in self.label_text:
            return self.label_text[idv]
        for a in n.ancestors():
            if a.name == "label":
                return " ".join(content_of(a).text)
        return n.sval("placeholder") or ""

    def step_section(self, n):
        """Nearest ancestor that delimits a step of a process (form, fieldset, step/wizard container)."""
        for a in n.ancestors():
            if a.component:
                continue
            ident = " ".join([a.sval("id") or "", " ".join(a.classes())])
            if a.name in ("form", "fieldset") or a.has("data-step") or STEP_TOKEN_RE.search(ident):
                return a
        return None

    def entry_fields(self, nodes):
        fields = []
        for n in nodes:
            if n.component or n.name not in ("input", "select", "textarea") or n.spread:
                continue
            itype = (n.sval("type") or "text").lower() if n.name == "input" else ""
            if n.dyn("type") or itype in REENTRY_SKIP_TYPES:
                continue
            ac = [t for t in (n.sval("autocomplete") or "").lower().split()
                  if not t.startswith("section-") and t not in ("shipping", "billing", "on", "off")]
            label = norm_space(self.label_of(n)).lower()
            lkey = re.sub(r"[^a-z0-9 ]+", "", re.sub(r"\((required|optional)\)|\brequired\b|\*", "", label)).strip()
            keys = []
            if ac and ac[-1] in AUTOFILL_ALL:
                keys.append("autocomplete " + " ".join(ac))
            if lkey and not REENTRY_CONFIRM_RE.search(lkey):
                keys.append("label \"%s\"" % lkey)
            if not keys and not REENTRY_CONFIRM_RE.search(lkey):
                continue
            exempt = None
            if itype == "password" or (ac and ac[-1] in ("new-password", "current-password", "one-time-code")):
                exempt = "security"
            elif n.sval("data-reentry"):
                exempt = n.sval("data-reentry")
            elif n.name == "select" or n.has("list"):
                exempt = "select option"
            elif (n.sval("value") or "").strip() or n.dyn("value") or n.has("v-model") or n.has("bind:value"):
                exempt = "auto-populated"
            elif re.search(r"\bnew\b", lkey):
                exempt = "previous value no longer valid"
            fields.append({"node": n, "keys": keys, "section": self.step_section(n), "exempt": exempt,
                           "label": lkey, "confirm": bool(REENTRY_CONFIRM_RE.search(lkey))})
        return fields

    @staticmethod
    def section_offers_copy(section):
        if section is None:
            return False
        for d in iter_nodes(section.children):
            if d.component:
                continue
            if d.name in ("input", "button", "select", "label", "a") or d.role() in ("checkbox", "button", "switch"):
                if REENTRY_OK_RE.search(" ".join(content_of(d).text) + " " + (d.sval("aria-label") or "") + " " + (d.sval("name") or "") + " " + (d.sval("id") or "")):
                    return True
        return False

    def redundant_entry(self, doc, nodes):
        fields = self.entry_fields(nodes)
        self.entry_by_doc[doc.file] = (doc, fields)
        seen = {}
        for f in fields:
            n = f["node"]
            if f["confirm"] and f["exempt"] != "security":
                self.add(doc, "redundant-entry-same-step", n,
                         "Field \"%s\" asks the user to repeat information in the same step. Confirmation re-entry is allowed only when essential or for security; otherwise remove it or pre-fill it." % f["label"],
                         evidence={"label": f["label"]})
                continue
            first = None
            for k in f["keys"]:
                if k in seen:
                    first = (k, seen[k])
                    break
            for k in f["keys"]:
                seen.setdefault(k, f)
            if first is None:
                continue
            k, prev = first
            if prev["section"] is f["section"]:
                if k.startswith("autocomplete"):
                    self.add(doc, "redundant-entry-same-step", n,
                             "%s is requested twice in the same step (first at line %d); check the repetition is essential or for security." % (k, prev["node"].line),
                             evidence={"key": k, "first_line": prev["node"].line})
                continue
            if f["exempt"] or self.section_offers_copy(f["section"]):
                continue
            self.add(doc, "redundant-entry", n,
                     "%s was already requested in an earlier step (line %d) and is asked again with no auto-populated value or option to select it (e.g. a \"same as\" checkbox). Exceptions: re-entry is essential, needed for security, or the earlier value is no longer valid." % (k, prev["node"].line),
                     evidence={"key": k, "first_line": prev["node"].line, "first_selector": prev["node"].selector()})

    def redundant_entry_across_files(self):
        """Steps of a process split across files (step1.html, step2.html ... or 'Step 2 of 3')."""
        groups = {}
        for file, (doc, fields) in self.entry_by_doc.items():
            if not fields or doc.kind in ("css", "scss", "js", "md"):
                continue
            base = os.path.basename(file)
            if STEP_FILE_RE.search(base) or STEP_TEXT_RE.search(doc.text):
                groups.setdefault(os.path.dirname(file), []).append((base, doc, fields))
        for _d, members in groups.items():
            if len(members) < 2:
                continue
            members.sort(key=lambda m: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", m[0])])
            seen = {}
            for base, doc, fields in members:
                local = {}
                for f in fields:
                    if f["confirm"]:
                        continue
                    hit = next(((k, seen[k]) for k in f["keys"] if k in seen), None)
                    if hit and not f["exempt"] and not self.section_offers_copy(f["section"]):
                        k, (pfile, pnode) = hit
                        self.add(doc, "redundant-entry", f["node"],
                                 "%s was already requested on an earlier step page (%s line %d) and is asked again with no auto-populated value or option to select it. Exceptions: essential, security, or the earlier value is no longer valid." % (k, pfile, pnode.line),
                                 evidence={"key": k, "first_file": pfile, "first_line": pnode.line})
                    for k in f["keys"]:
                        local.setdefault(k, (doc.file, f["node"]))
                for k, v in local.items():
                    seen.setdefault(k, v)

    # -----------------------------------------------------------------------
    def inline_style_rules(self, doc, nodes):
        sticky_reported = False
        for n in nodes:
            if n.component:
                continue
            decls = None
            at = n.a("style")
            if at is not None:
                if at.dynamic:
                    decls = parse_style_object(at.expr, n.line, n.col)
                else:
                    decls = parse_inline_style(at.value, n.line, n.col)
            decls = decls or []
            classes = n.classes()
            # 1.4.12 inline !important
            for d in decls:
                if d.important and d.prop in ("line-height", "letter-spacing", "word-spacing"):
                    self.add(doc, "text-spacing-important", n,
                             "Inline %s with !important cannot be overridden by user text-spacing styles." % d.prop)
            # 2.4.7 inline outline none on focusable
            if decls and outline_removed(decls) and (is_focusable(n) or n.role() in INTERACTIVE_ROLES):
                self.add(doc, "focus-outline-removed-maybe", n,
                         "Inline outline removal on a focusable element; :focus rules cannot override it without !important.")
            # tailwind outline-none
            cls_text = " ".join(classes)
            if re.search(r"(^|\s)(focus:|focus-visible:)?outline-none(\s|$)", cls_text) and (is_focusable(n) or n.role() in INTERACTIVE_ROLES):
                if not re.search(r"(^|\s)(focus|focus-visible|focus-within)(:|:[\w-]+:)(ring|outline|border|shadow|bg|underline|decoration)", cls_text) and not re.search(r"(^|\s)ring-", cls_text):
                    self.add(doc, "focus-outline-removed-maybe", n,
                             "outline-none without a focus:/focus-visible: ring/border/shadow utility; confirm a visible focus indicator exists.")
            # 2.4.11 sticky/fixed
            pos = next((d.value.strip().lower() for d in decls if d.prop == "position"), None)
            if not sticky_reported and (pos in ("fixed", "sticky") or re.search(r"(^|\s)(fixed|sticky)(\s|$)", cls_text)):
                sticky_reported = True
                self.add(doc, "focus-obscured-check", n,
                         "Fixed/sticky element: check that focused controls are not entirely hidden behind it (and scroll-padding is set).")
                self.add(doc, "focus-obscured-enhanced-check", n,
                         "Fixed/sticky element: at AAA no part of the focused control may be hidden.")
            # resolved styles for contrast and target size
            resolved = self.css.resolve(n) if self.css else {}
            sources = {}
            for p, (d, src) in resolved.items():
                sources[p] = (d, src)
            for d in decls:
                sources[d.prop] = (d, "inline")
            self.element_contrast(doc, n, sources)
            self.element_target_size(doc, n, sources, classes)

    def element_contrast(self, doc, n, sources):
        fg = sources.get("color")
        bg = sources.get("background-color") or sources.get("background")
        if not fg or not bg:
            return
        if fg[1] == bg[1] and fg[1] != "inline":
            return  # same rule: reported by the stylesheet check
        c = content_of(n)
        if not "".join(c.text).strip():
            return
        if n.bool_attr("disabled") or n.has("aria-disabled"):
            return
        contrast_check(lambda rule, where, msg, sev, ev: self.add(doc, rule, where, msg, sev, ev), n,
                       fg[0].value, bg[0].value, sources.get("font-size", (None,))[0], sources.get("font-weight", (None,))[0],
                       logo=logo_reason_node(n))

    def element_target_size(self, doc, n, sources, classes):
        role = n.role()
        interactive = n.name in ("button", "select") or (n.name == "input" and (n.sval("type") or "").lower() not in ("hidden",)) \
            or (n.name == "a" and n.has("href")) or role in ("button", "link", "checkbox", "radio", "switch", "tab", "menuitem", "option")
        if not interactive or n.spread:
            return
        if n.name == "input" and (n.sval("type") or "").lower() in ("checkbox", "radio") and \
                hides_visually([v[0] for v in sources.values()]):
            return  # visually hidden native input: the pointer target is its label / drawn sibling
        w = to_px(sources["width"][0].value) if "width" in sources else None
        h = to_px(sources["height"][0].value) if "height" in sources else None
        tw = th = None
        for c in classes:
            m = re.fullmatch(r"(w|h|size)-(\d+(?:\.5)?)", c)
            if m:
                v = float(m.group(2)) * 4
                if m.group(1) in ("w", "size"):
                    tw = v
                if m.group(1) in ("h", "size"):
                    th = v
            m = re.fullmatch(r"(w|h|size)-\[(\d+(?:\.\d+)?)px\]", c)
            if m:
                v = float(m.group(2))
                if m.group(1) in ("w", "size"):
                    tw = v
                if m.group(1) in ("h", "size"):
                    th = v
            if re.match(r"(min-w|min-h|p|px|py)-", c):
                return
        w = w if w is not None else tw
        h = h if h is not None else th
        if w is None or h is None:
            return
        for k in ("min-width", "min-height"):
            if k in sources:
                v = to_px(sources[k][0].value)
                if v is not None and v >= 24:
                    return
        if any(k.startswith("padding") for k in sources) and (sources.get("box-sizing", (None,))[0] is None or sources["box-sizing"][0].value.strip() != "border-box"):
            return
        disp = sources.get("display", (None,))[0]
        if n.name == "a" and tw is None and (disp is None or disp.value.strip() == "inline"):
            return  # width/height do not apply to inline links
        if min(w, h) < 24:
            self.add(doc, "target-size-small", n,
                     "Target is %gx%g CSS px (< 24x24). Passes only if a 24px circle centred on it does not overlap other targets, or an exception applies (inline, equivalent control, essential)." % (w, h),
                     evidence={"width": w, "height": h})


# ---------------------------------------------------------------------------
# CSS rule analysis
# ---------------------------------------------------------------------------
INTERACTIVE_SEL_RE = re.compile(r"(^|[\s>+~,(])(a|button|input|select|textarea|summary)(?=$|[\s.#:\[>+~,)])|\[role=['\"]?(button|link|checkbox|tab|switch|radio|menuitem)|\.(btn|button)\b|-btn\b|icon-button|\[tabindex|(^|\s)\*(?=$|[\s:])|(^|\s|,):focus")
TARGET_SEL_RE = re.compile(r"(^)(button|input|select)(?=$|[.#:\[])|\[role=['\"]?(button|link|checkbox|switch|radio|tab|menuitem)|\.(btn|button|icon-btn|icon-button|close|close-button|toggle)\b|-btn\b|-button\b")
UI_SEL_RE = re.compile(r"(^)(button|input|select|textarea)(?=$|[.#:\[])|\.(btn|button|form-control|input)\b")
EXEMPT_SEL_RE = re.compile(r":disabled|\[disabled|\.disabled\b|\[aria-disabled|:placeholder-shown")
TWO_D_RE = re.compile(r"(^|[\s>+~,])(table|pre|code|canvas|video|iframe|map|svg)(?=$|[\s.#:\[>+~,])|\.(table|carousel|slider|chart|map|code|highlight)\b")


def selector_subject(sel):
    """Last compound selector (the element the rule styles)."""
    parts = [p for p in re.split(r"\s*[>+~]\s*|\s+", sel.strip()) if p]
    return parts[-1] if parts else ""


class UIContext:
    """Which class selectors style form controls, and what background sits behind them."""

    def __init__(self, docs, index):
        self.index = index
        self.docs = {d.file: d for d in docs}
        self.markup = [d for d in docs if d.roots]
        self.by_doc, self.all = {}, set()
        for d in self.markup:
            cls = set()
            for n in iter_nodes(d.roots):
                if n.component:
                    continue
                ctl = n.name in ("input", "select", "textarea", "button") and (n.sval("type") or "").lower() != "hidden"
                if ctl or n.role() in ("textbox", "combobox", "searchbox", "checkbox", "switch", "radio", "button", "spinbutton"):
                    cls.update(c for c in n.classes() if TEMPLATE_FILL not in c)
            self.by_doc[d.file] = cls
            self.all |= cls

    def scope(self, file):
        d = self.docs.get(file)
        if d is not None and d.kind in ("vue", "svelte") and d.roots:
            return [d], self.by_doc.get(file, set())
        return self.markup, self.all

    def class_ui(self, subject, file):
        comp = parse_css_compound(subject)
        if comp is None or not comp["classes"]:
            return False
        _docs, cls = self.scope(file)
        return any(c in cls for c in comp["classes"])

    def own_bg(self, n):
        res = self.index.resolve(n)
        d = res.get("background-color") or res.get("background")
        v = d[0].value if d else None
        st = n.a("style")
        if st is not None:
            if st.dynamic:
                return None
            for dd in parse_inline_style(st.value, n.line, n.col):
                if dd.prop in ("background", "background-color"):
                    v = dd.value
        return background_color(v)

    def page_bg(self):
        for tag in ("body", "html"):
            for t, classes, idv, _spec, _o, decls in reversed(self.index.simple):
                if t == tag and not classes and not idv:
                    for d in reversed(decls):
                        if d.prop in ("background", "background-color"):
                            c = background_color(d.value)
                            if isinstance(c, tuple) and c[3] == 1:
                                return c, "%s background %s" % (tag, d.value)
                            if c is None:
                                return None
        return (255, 255, 255, 1.0), "no background declared; assumed white #ffffff"

    def background_for(self, sel, file):
        """(rgba, note) of the first opaque background behind elements matching sel, or None."""
        docs, _cls = self.scope(file)
        hits = select_nodes(docs, sel)[:5]
        if not hits:
            if any(UI_SEL_RE.search(selector_subject(x)) for x in split_top(sel)):
                return self.page_bg()
            return None
        _d, n = hits[0]
        for a in [n] + list(n.ancestors()):
            if a.component:
                return None
            c = self.own_bg(a)
            if c is None:
                return None
            if isinstance(c, tuple):
                if c[3] < 1:
                    return None
                return c, "background of <%s>" % a.selector()
        return self.page_bg()


def analyze_css(reporter, file, lines_of, rules, index, ui_ctx=None):
    def snippet(line):
        lines = lines_of
        if 1 <= line <= len(lines):
            s = lines[line - 1].strip()
            return s[:160] + ("..." if len(s) > 160 else "")
        return ""

    def add(rule, pos, message, severity=None, selector="", evidence=None):
        reporter.add(rule, file, pos[0], pos[1], message, severity, selector, snippet(pos[0]), evidence)

    sticky_done = False
    focus_done = False
    for r in rules:
        sel = r.selector
        decls = r.decls
        if not decls:
            continue
        media = (r.media or "").lower()
        props = {}
        for d in decls:
            props[d.prop] = d
        # 1.4.12
        for d in decls:
            if d.important and d.prop in ("line-height", "letter-spacing", "word-spacing"):
                add("text-spacing-important", (d.line, d.col),
                    "%s: %s !important blocks user text-spacing overrides (unless the value already meets the 1.4.12 metrics)." % (d.prop, d.value),
                    selector=sel)
        # 2.4.7
        od = outline_removed(decls)
        if od is not None:
            sels = [x.strip() for x in split_top(sel) if ":not(:focus-visible)" not in x]
            focus_sels = [x for x in sels if re.search(r":focus(?!-within)", x) and ":not(:focus-visible)" not in x]
            if focus_sels:
                if has_focus_alternative(decls):
                    pass
                elif all(focus_base(x) in index.focus_visible_bases for x in focus_sels):
                    pass
                else:
                    visible_elsewhere = any(":focus-visible" in x for x in focus_sels)
                    add("focus-outline-removed", (od.line, od.col),
                        "Focus outline removed (%s) on \"%s\" with no alternative indicator (box-shadow, border, background, :focus-visible rule)." % (od.value, ", ".join(focus_sels)),
                        severity="fail" if not visible_elsewhere else "warn", selector=sel)
            elif sels and any(INTERACTIVE_SEL_RE.search(selector_subject(x)) for x in sels) and not has_focus_alternative(decls):
                if not any(focus_base(x) in index.focus_visible_bases for x in sels):
                    add("focus-outline-removed-maybe", (od.line, od.col),
                        "outline: %s on interactive elements (%s); confirm a :focus/:focus-visible style restores a visible indicator." % (od.value, sel),
                        selector=sel)
        # 2.4.11 / 2.4.12 / 2.4.13
        pos = props.get("position")
        if pos is not None and pos.value.strip().lower() in ("fixed", "sticky") and not sticky_done and "print" not in media:
            sticky_done = True
            add("focus-obscured-check", (pos.line, pos.col),
                "position: %s on \"%s\": check that focused controls are never entirely hidden behind it (use scroll-padding/scroll-margin)." % (pos.value.strip(), sel),
                selector=sel)
            add("focus-obscured-enhanced-check", (pos.line, pos.col),
                "position: %s on \"%s\": at AAA no part of a focused control may be hidden." % (pos.value.strip(), sel), selector=sel)
        if not focus_done and ":focus" in sel and any(d.prop.startswith(("outline", "box-shadow", "border")) for d in decls):
            focus_done = True
            add("focus-appearance-check", (r.line, r.col),
                "Custom focus style on \"%s\": at AAA the indicator must be at least as large as a 2 CSS px perimeter and have 3:1 change of contrast." % sel,
                selector=sel)
        # 1.4.10
        if "print" not in media and "min-width" not in media and not TWO_D_RE.search(sel):
            for prop in ("width", "min-width"):
                d = props.get(prop)
                if d is None:
                    continue
                px = to_px(d.value) if d.value.strip().endswith("px") else None
                if px is not None and px > 320 and "max-width" not in props:
                    add("fixed-width-no-max", (d.line, d.col),
                        "%s: %s with no max-width can force horizontal scrolling at 320 CSS px (400%% zoom)." % (prop, d.value),
                        selector=sel, evidence={"px": px})
        # 1.4.3 contrast in the same block
        fg = props.get("color")
        bg = props.get("background-color") or props.get("background")
        if fg is not None and bg is not None and not EXEMPT_SEL_RE.search(sel):
            contrast_check(lambda rule, where, msg, sev, ev: add(rule, where, msg, sev, sel, ev),
                           (fg.line, fg.col), fg.value, bg.value, props.get("font-size"), props.get("font-weight"),
                           logo=logo_reason_selector(sel))
        # 1.4.11 UI borders / focus indicators
        bgc = background_color(bg.value) if bg is not None else None
        if isinstance(bgc, tuple) and bgc[3] == 1:
            if ":focus" in sel:
                oc = None
                od2 = props.get("outline-color") or props.get("outline")
                if od2 is not None:
                    for tok in COLOR_TOKEN_RE.findall(od2.value):
                        c = parse_color(tok)
                        if c:
                            oc = (c, od2)
                            break
                if oc and oc[0][3] == 1:
                    ratio = contrast(oc[0], bgc)
                    if ratio < 3:
                        add("focus-indicator-contrast", (oc[1].line, oc[1].col),
                            "Focus outline colour contrast %.2f:1 against the element background is below 3:1 (also check against the page background)." % ratio,
                            selector=sel, evidence={"ratio": round(ratio, 2)})
        if ":focus" not in sel and not EXEMPT_SEL_RE.search(sel) and "::" not in sel and (
                any(UI_SEL_RE.search(selector_subject(x)) for x in split_top(sel))
                or (ui_ctx is not None and any(ui_ctx.class_ui(selector_subject(x), file) for x in split_top(sel)))):
            bd = props.get("border-color") or props.get("border")
            if bd is not None:
                bc = None
                for tok in COLOR_TOKEN_RE.findall(bd.value):
                    c = parse_color(tok)
                    if c:
                        bc = c
                        break
                bg_eff, bg_note = None, None
                if isinstance(bgc, tuple) and bgc[3] == 1:
                    bg_eff, bg_note = bgc, "same rule"
                elif (bg is None or bgc == "none") and ui_ctx is not None:
                    got = ui_ctx.background_for(sel, file)
                    if got:
                        bg_eff, bg_note = got
                if bc and bc[3] == 1 and bg_eff is not None:
                    ratio = contrast(bc, bg_eff)
                    if ratio < 3:
                        where = "the component background" if bg_note == "same rule" else "the background behind it (%s)" % bg_note
                        add("ui-border-contrast", (bd.line, bd.col),
                            "Border contrast %.2f:1 against %s; if the border is what identifies the control, it needs 3:1 against adjacent colours." % (ratio, where),
                            selector=sel, evidence={"ratio": round(ratio, 2), "background_source": bg_note})
        # 2.5.8 target size
        subjects = [selector_subject(x) for x in split_top(sel)]
        if subjects and all(TARGET_SEL_RE.search(x) and "::" not in x for x in subjects) and not EXEMPT_SEL_RE.search(sel):
            w = to_px(props["width"].value) if "width" in props else None
            h = to_px(props["height"].value) if "height" in props else None
            if w is not None and h is not None:
                ok = False
                for k in ("min-width", "min-height"):
                    if k in props:
                        v = to_px(props[k].value)
                        if v is not None and v >= 24:
                            ok = True
                if any(k.startswith("padding") for k in props) and not ("box-sizing" in props and props["box-sizing"].value.strip() == "border-box"):
                    ok = True
                if not ok and min(w, h) < 24:
                    d = props["width"]
                    add("target-size-small", (d.line, d.col),
                        "Target \"%s\" is %gx%g CSS px (< 24x24); passes only with enough spacing or an exception." % (sel, w, h),
                        selector=sel, evidence={"width": w, "height": h})


# ---------------------------------------------------------------------------
# 1.4.11 custom checkbox / radio / switch drawn by a sibling of a hidden input
# ---------------------------------------------------------------------------
PSEUDO_ELEM_RE = re.compile(r"::?(before|after)\b", re.I)
SEL_STATE_RE = re.compile(r":(checked|hover|focus|focus-visible|focus-within|active|disabled|indeterminate|invalid|user-invalid)\b|"
                          r"\[(aria-checked|aria-pressed|checked|disabled|aria-disabled)\b|"
                          r"\.(is-)?(checked|active|on|selected|disabled)\b|--(checked|active|on|selected|disabled)\b", re.I)


def split_selector(part):
    """'a > b + .c' -> (['a', 'b', '.c'], [None, '>', '+']) respecting () and []."""
    comps, combs, cur, depth, pending, gap = [], [], [], 0, None, False
    for ch in part.strip():
        if depth == 0 and ch in " \t\r\n>+~":
            if cur:
                comps.append("".join(cur))
                cur = []
            if ch in ">+~":
                pending = ch
            else:
                gap = True
            continue
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if not cur and comps:
            combs.append(pending or (" " if gap else None))
        elif not cur:
            combs.append(None)
        pending, gap = None, False
        cur.append(ch)
    if cur:
        comps.append("".join(cur))
    return comps, combs


def sel_specificity(part):
    p = re.sub(r"::?(before|after)\b", "", part)
    ids = len(re.findall(r"#[\w-]+", p))
    cls = len(re.findall(r"\.[\w-]+|\[[^\]]*\]|:(?!not\b|is\b|where\b)[\w-]+", p))
    tags = len(re.findall(r"(?:^|[\s>+~])[a-zA-Z][\w-]*", p))
    return (ids, cls, tags)


def _prev_siblings(n):
    if n.parent is None:
        return []
    sibs = [c for c in n.parent.children if isinstance(c, Node)]
    for i, c in enumerate(sibs):
        if c is n:
            return list(reversed(sibs[:i]))
    return []


def node_matches(n, comps, combs, parsed=None):
    parsed = parsed or [parse_css_compound(c) for c in comps]
    if any(p is None for p in parsed):
        return False

    def m(node, i):
        if node is None or not _compound_match(node, parsed[i]):
            return False
        if i == 0:
            return True
        comb = combs[i]
        if comb == ">":
            return m(node.parent, i - 1)
        if comb == " ":
            return any(m(a, i - 1) for a in node.ancestors())
        prev = _prev_siblings(node)
        if comb == "+":
            return bool(prev) and m(prev[0], i - 1)
        return any(m(s, i - 1) for s in prev)
    return m(n, len(comps) - 1)




def hides_visually(decls):
    p = {}
    for d in decls:
        p[d.prop] = d.value.strip().lower()
    if p.get("opacity") in ("0", "0.0", "0%"):
        return True
    w, h = to_px(p.get("width")), to_px(p.get("height"))
    if w is not None and h is not None and w <= 1 and h <= 1:
        return True
    if re.search(r"rect\(\s*0", p.get("clip", "")) or re.search(r"inset\(\s*50%|circle\(\s*0", p.get("clip-path", "")):
        return True
    for k in ("left", "top", "margin-left"):
        v = to_px(p.get(k))
        if v is not None and v <= -999:
            return True
    if re.search(r"scale\(\s*0\s*\)", p.get("transform", "")):
        return True
    return False


class ToggleStyles:
    """Default-state styles of markup nodes, from the rules that can reach them."""

    def __init__(self, docs, css_by_doc):
        self.sheet_rules = []
        self.doc_rules = {}
        for doc, rules in zip(docs, css_by_doc):
            rules = [r for r in rules if not r.media]  # media-conditional styling is not the default state
            if doc.kind in ("css", "scss"):
                self.sheet_rules.extend(rules)
            else:
                self.doc_rules[doc.file] = rules
        self.cache = {}

    def rules_for(self, doc):
        return self.doc_rules.get(doc.file, []) + self.sheet_rules

    def parts(self, doc):
        key = ("parts", doc.file)
        if key not in self.cache:
            out = []
            for r in self.rules_for(doc):
                for part in split_top(r.selector):
                    part = part.strip()
                    if not part or ":deep" in part or ">>>" in part:
                        continue
                    pe = PSEUDO_ELEM_RE.search(part)
                    pseudo = pe.group(1).lower() if pe else None
                    base = PSEUDO_ELEM_RE.sub("", part)
                    state = bool(SEL_STATE_RE.search(re.sub(r":not\([^)]*\)", "", base)))
                    comps, combs = split_selector(base)
                    if not comps:
                        continue
                    parsed = [parse_css_compound(c) for c in comps]
                    if any(p is None for p in parsed):
                        continue
                    out.append((r, part, pseudo, state, comps, combs, parsed, sel_specificity(part)))
            self.cache[key] = out
        return self.cache[key]

    def computed(self, doc, n, pseudo=None):
        """{prop: (Decl, rule, selector_part)} for the default (unchecked, idle) state."""
        key = (id(n), pseudo)
        if key in self.cache:
            return self.cache[key]
        hits = []
        for r, part, ps, state, comps, combs, parsed, spec in self.parts(doc):
            if ps != pseudo or state:
                continue
            if node_matches(n, comps, combs, parsed):
                hits.append((spec, r.order, r, part))
        hits.sort(key=lambda t: (t[0], t[1]))
        out = {}
        for _s, _o, r, part in hits:
            for d in r.decls:
                if d.prop == "background":
                    out.pop("background-color", None)
                elif d.prop == "border":
                    for k in ("border-color", "border-width", "border-style"):
                        out.pop(k, None)
                out[d.prop] = (d, r, part)
        if pseudo is None:
            st = n.a("style")
            if st is not None and not st.dynamic:
                for d in parse_inline_style(st.value, n.line, n.col):
                    if d.prop == "background":
                        out.pop("background-color", None)
                    elif d.prop == "border":
                        for k in ("border-color", "border-width", "border-style"):
                            out.pop(k, None)
                    out[d.prop] = (d, None, "style")
        self.cache[key] = out
        return out


def _paint(props):
    """Background colour of a computed style: (rgba | 'none' | None unknown, decl)."""
    d = props.get("background-color") or props.get("background")
    return background_color(d[0].value if d else None), (d[0] if d else None)


def _first_color(value):
    for tok in COLOR_TOKEN_RE.findall(value or ""):
        c = parse_color(tok)
        if c:
            return c
    return None


def _border(props):
    """(rgba | None unknown | 'none', decl) for the element's border."""
    d = props.get("border")
    bc = props.get("border-color")
    bw = props.get("border-width")
    bs = props.get("border-style")
    if d is None and bc is None:
        return "none", None
    if d is not None:
        v = d[0].value.strip().lower()
        if v in ("none", "0", "0px", "hidden") or re.search(r"\bnone\b", v):
            if bc is None:
                return "none", None
    if bw is not None and to_px(bw[0].value) == 0:
        return "none", None
    if bs is not None and bs[0].value.strip().lower() in ("none", "hidden"):
        return "none", None
    src = bc if bc is not None else d
    if "var(" in src[0].value or "$" in src[0].value:
        return None, src[0]
    c = _first_color(src[0].value)
    if c is None:
        return (None, src[0]) if bc is not None else ("none", None)
    return c, src[0]


RING_RE = re.compile(r"^(inset\s+)?0(?:px)?\s+0(?:px)?\s+0(?:px)?\s+(" + _NUM + r")px\s+(.+)$|^(.+?)\s+(inset\s+)?0(?:px)?\s+0(?:px)?\s+0(?:px)?\s+(" + _NUM + r")px$")


def _ring(props):
    """Colour of a 'box-shadow: 0 0 0 Npx COLOR' ring: rgba | 'none' | None (unknown)."""
    d = props.get("box-shadow")
    if d is None:
        return "none", None
    v = d[0].value.strip().lower()
    if v == "none":
        return "none", None
    parts = split_top(v)
    if len(parts) != 1:
        return None, d[0]
    m = RING_RE.match(parts[0].strip())
    if not m:
        return "none", None  # blurred shadows are not a boundary
    width = float(m.group(2) or m.group(6))
    col = (m.group(3) or m.group(4) or "").strip()
    if width <= 0:
        return "none", None
    c = parse_color(col)
    return (c, d[0]) if c else (None, d[0])


def _hex(c):
    return "#%02x%02x%02x" % tuple(int(round(x)) for x in c[:3])


def analyze_custom_toggles(reporter, docs, css_by_doc):
    """1.4.11: a visually hidden checkbox/radio whose visible control is a sibling element."""
    styles = ToggleStyles(docs, css_by_doc)
    docs_by_file = {d.file: d for d in docs}
    done = set()

    root_vars_cache = {}

    def root_vars(doc):
        # Custom properties declared on :root/html/body (later rules win); enough to resolve a
        # page background such as `background: var(--surface)`.
        key = id(doc)
        if key not in root_vars_cache:
            vals = {}
            for d in styles.rules_for(doc):
                if any(p.strip() in ("body", "html", ":root") for p in split_top(d.selector)):
                    for decl in d.decls:
                        if decl.prop.startswith("--"):
                            vals[decl.prop] = decl.value.strip()
            root_vars_cache[key] = vals
        return root_vars_cache[key]

    def sub_vars(doc, value):
        vals = root_vars(doc)
        for _ in range(5):
            new = re.sub(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*))?\)",
                         lambda m: vals.get(m.group(1), (m.group(2) or m.group(0)).strip()), value)
            if new == value:
                break
            value = new
        return value

    def paint(doc, props):
        d = props.get("background-color") or props.get("background")
        return background_color(sub_vars(doc, d[0].value) if d else None)

    def surround(doc, node):
        for a in node.ancestors():
            if a.component:
                return None, None
            bg = paint(doc, styles.computed(doc, a))
            if bg is None:
                return None, None
            if isinstance(bg, tuple):
                if bg[3] < 1:
                    return None, None
                return bg, "background of <%s>" % a.selector()
        for d in reversed(styles.rules_for(doc)):
            for part in split_top(d.selector):
                if part.strip() in ("body", "html", ":root"):
                    bgd = d.get("background-color") or d.get("background")
                    if bgd is not None:
                        resolved = sub_vars(doc, bgd.value)
                        c = background_color(resolved)
                        if isinstance(c, tuple) and c[3] == 1:
                            shown = bgd.value if resolved == bgd.value else "%s = %s" % (bgd.value, resolved)
                            return c, "%s background %s" % (part.strip(), shown)
                        return None, None
        return (255, 255, 255, 1.0), "no background declared; assumed white #ffffff"

    for doc in docs:
        if not doc.roots:
            continue
        for inp in iter_nodes(doc.roots):
            if inp.name != "input" or inp.component or inp.spread:
                continue
            itype = (inp.sval("type") or "").lower()
            if itype not in ("checkbox", "radio"):
                continue
            if not (hides_visually([v[0] for v in styles.computed(doc, inp).values()])
                    or SR_ONLY_RE.search(" ".join(inp.classes()))):
                continue
            # siblings that draw the control: reached by a + / ~ rule, or empty styled siblings in the same <label>
            after = []
            if inp.parent is not None:
                sibs = [c for c in inp.parent.children if isinstance(c, Node)]
                after = sibs[sibs.index(inp) + 1:]
            cands = []
            for sib in after:
                if sib.component:
                    break
                via = None
                for r, part, ps, state, comps, combs, parsed, spec in styles.parts(doc):
                    if "+" not in combs and "~" not in combs:
                        continue
                    k = max(i for i, c in enumerate(combs) if c in ("+", "~"))
                    if k != len(comps) - 1:
                        continue  # a descendant of the sibling (thumb) is judged with its track
                    if node_matches(sib, comps, combs, parsed) and node_matches(inp, comps[:k], combs[:k], parsed[:k]):
                        # a state rule (:checked, :focus-visible, ...) still proves the relationship; its colours are not used
                        if not state:
                            via = part
                            break
                        via = via or re.sub(r":(checked|hover|focus-visible|focus-within|focus|active|indeterminate)\b", "", part)
                in_label = inp.parent.name == "label" or any(a.name == "label" for a in list(inp.ancestors())[:2])
                if via is None and in_label and not re.search(r"\w", " ".join(content_of(sib).text)) and not content_of(sib).unknown:
                    via = "%s (in the same <label>)" % sib.selector()
                if via is not None:
                    cands.append((sib, via))
            for sib, via in cands[:2]:
                props = styles.computed(doc, sib)
                track_pseudo = None
                bg, bgd = _paint(props)
                bc, bcd = _border(props)
                rc, rcd = _ring(props)
                if bg == "none" and bc == "none" and rc == "none":
                    pb = styles.computed(doc, sib, "before")
                    if pb:
                        track_pseudo = "before"
                        props = pb
                        bg, bgd = _paint(props)
                        bc, bcd = _border(props)
                        rc, rcd = _ring(props)
                if bg == "none" and bc == "none" and rc == "none":
                    continue
                if bg is None or bc is None or rc is None:
                    continue  # an unresolved colour might be the one that reaches 3:1
                if isinstance(bg, tuple) and bg[3] < 1:
                    continue
                outer, outer_note = surround(doc, sib if track_pseudo is None else _Pseudo(sib))
                if outer is None:
                    continue
                ratios, detail = {}, []
                fill = bg if isinstance(bg, tuple) else outer
                if isinstance(bg, tuple):
                    ratios["track_vs_surrounding"] = contrast(bg, outer)
                    detail.append("background %s vs surrounding %s %.2f:1" % (_hex(bg), _hex(outer), ratios["track_vs_surrounding"]))
                for label, c in (("border", bc), ("ring", rc)):
                    if isinstance(c, tuple):
                        c2 = blend(c, outer) if c[3] < 1 else c
                        ratios[label + "_vs_surrounding"] = contrast(c2, outer)
                        detail.append("%s %s vs surrounding %s %.2f:1" % (label, _hex(c2), _hex(outer), ratios[label + "_vs_surrounding"]))
                # thumb / knob: ::before/::after of the track (when the track is the element) or a child element
                thumbs = []
                if track_pseudo is None:
                    for ps in ("before", "after"):
                        tp = styles.computed(doc, sib, ps)
                        if tp:
                            thumbs.append(("::" + ps, tp))
                    for ch in sib.children:
                        if isinstance(ch, Node) and not ch.component and ch.name != "svg":
                            tp = styles.computed(doc, ch)
                            if tp:
                                thumbs.append((ch.selector(), tp))
                unknown = False
                for tname, tp in thumbs:
                    tbg, _x = _paint(tp)
                    tbc, _y = _border(tp)
                    trc, _z = _ring(tp)
                    if tbg is None or tbc is None or trc is None:
                        unknown = True
                        break
                    for label, c in (("thumb", tbg), ("thumb border", tbc), ("thumb ring", trc)):
                        if isinstance(c, tuple):
                            c2 = blend(c, fill) if c[3] < 1 else c
                            key = "%s_%s_vs_track" % (tname.strip(":"), label.replace(" ", "_"))
                            ratios[key] = contrast(c2, fill)
                            detail.append("%s %s %s vs track %.2f:1" % (label, tname, _hex(c2), ratios[key]))
                if unknown or not ratios or max(ratios.values()) >= 3:
                    continue
                d0 = bcd if isinstance(bc, tuple) else (bgd if isinstance(bg, tuple) else rcd)
                rule_obj = next((v[1] for v in props.values() if v[0] is d0), None)
                if rule_obj is not None:
                    fdoc = docs_by_file.get(rule_obj.file, doc)
                    where = (fdoc.file, d0.line, d0.col)
                else:
                    fdoc, where = doc, (doc.file, sib.line, sib.col)
                if where in done:
                    continue
                done.add(where)
                role = (inp.sval("role") or "").lower()
                kind = "switch" if role == "switch" else itype
                sel_name = via + ("::before" if track_pseudo and not PSEUDO_ELEM_RE.search(via) else "")
                reporter.add("ui-border-contrast", where[0], where[1], where[2],
                             "Custom %s drawn by sibling \"%s\" of a visually hidden <input type=\"%s\">: in its default state no part that "
                             "identifies the control reaches 3:1 (%s; surrounding colour from %s). Give the track border, track fill or thumb "
                             "3:1 against its adjacent colour." % (kind, sel_name, itype, "; ".join(detail), outer_note),
                             selector=sel_name, snippet=fdoc.snippet(where[1]),
                             evidence={"sibling_selector": sel_name, "input": inp.selector(),
                                       "ratios": {k: round(v, 2) for k, v in ratios.items()},
                                       "ratio": round(max(ratios.values()), 2), "background_source": outer_note})


class _Pseudo:
    """Stand-in whose ancestors start at the element itself (a ::before sits on its host's background)."""

    def __init__(self, host):
        self.host = host

    def ancestors(self):
        yield self.host
        for a in self.host.ancestors():
            yield a


# ---------------------------------------------------------------------------
# Script-level heuristics
# ---------------------------------------------------------------------------
def analyze_scripts(reporter, doc):
    for text, line0, col0 in doc.scripts:
        li = LineIndex(text)

        def at(off):
            ln, col = li.pos(off)
            if ln == 1:
                return line0, col0 + col - 1
            return line0 + ln - 1, col

        def add(rule, off, msg, severity=None, evidence=None):
            ln, col = at(off)
            reporter.add(rule, doc.file, ln, col, msg, severity, "", doc.snippet(ln), evidence)

        m = DRAG_LIB_RE.search(text)
        if m:
            add("drag-library-check", m.start(), "Drag-and-drop library \"%s\" in use; check every drag action has a single-pointer alternative." % m.group(1),
                evidence={"library": m.group(1)})
        for m in re.finditer(r"addEventListener\(\s*['\"]paste['\"]", text):
            window = text[m.start(): m.start() + 400]
            if re.search(r"preventDefault\s*\(|return\s+false", window):
                add("paste-blocked-maybe", m.start(), "Script blocks the paste event; if it applies to login/password/OTP fields this fails 3.3.8.")
        for m in re.finditer(r"user-scalable\s*=\s*(no|0)\b|maximum-scale\s*=\s*(0?\.\d+|1(\.0+)?)\b", text):
            add("viewport-zoom-disabled", m.start(), "Script sets a viewport that disables zoom (%s)." % m.group(0))
        if doc.kind in ("jsx", "js") and re.search(r"\bviewport\b", text):
            for m in re.finditer(r"\buserScalable\s*:\s*false\b|\bmaximumScale\s*:\s*(0?\.\d+|1(\.0+)?)\b", text):
                add("viewport-zoom-disabled", m.start(), "Viewport config disables zoom (%s)." % m.group(0))


# 4.1.3: scripts that write a status/result message into an element that is not a live region
MSG_NAME_RE = re.compile(r"msg|message|status|result|feedback|notice|notif|alert|error|success|toast|confirm|flash|output|announce", re.I)
MSG_TEXT_RE = re.compile(r"\b(success(ful(ly)?)?|saved|added|submitted|thank(s| you)|error|invalid|fail(ed|ure)?|updated|removed|deleted|found|sent|complete(d)?|results?|in your (cart|basket|bag|list))\b", re.I)
ACTION_RE = re.compile(r"addEventListener\(\s*['\"](submit|click)['\"]|\bon(submit|click)\s*=|\.on\(\s*['\"](submit|click)['\"]|\.(submit|click)\(\s*(function|\(|\w+\s*=>)")
_DOM_Q = r"document\s*\.\s*(getElementById|querySelector)\(\s*['\"]([^'\"]+)['\"]\s*\)"
VAR_DOM_RE = re.compile(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(document\s*\.\s*(getElementById|querySelector)\(\s*['\"]([^'\"]+)['\"]\s*\))")
WRITE_RE = re.compile(r"(" + _DOM_Q + r"|[A-Za-z_$][\w$]*)\s*\.\s*(textContent|innerText|innerHTML)\s*\+?=(?!=)\s*([^;\n]{0,200})")
APPEND_RE = re.compile(r"(" + _DOM_Q + r"|[A-Za-z_$][\w$]*)\s*\.\s*(appendChild|append|prepend|insertAdjacentHTML|replaceChildren)\s*\(")
JQ_WRITE_RE = re.compile(r"\$\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\.\s*(text|html|append)\(\s*([^)\s][^;\n]{0,200})")


def _markup_lookup(docs, selector):
    """Find nodes for a simple '#id', '.class' or 'tag#id' selector across markup documents."""
    m = re.fullmatch(r"([a-z][\w-]*)?(?:#([\w-]+)|\.([\w-]+))", selector.strip(), re.I)
    if not m:
        return []
    tag, idv, cls = m.groups()
    out = []
    for doc in docs:
        for n in iter_nodes(doc.roots):
            if n.component or (tag and n.name != tag.lower()):
                continue
            if (idv and (n.sval("id") or "").strip() == idv) or (cls and cls in n.classes()):
                out.append((doc, n))
    return out


def _is_live(n):
    for a in [n] + list(n.ancestors()):
        if a.role() in LIVE_ROLES or a.dyn("role") or a.dyn("aria-live"):
            return True
        v = a.sval("aria-live")
        if v is not None and v.strip().lower() != "off":
            return True
    return any(d.role() in LIVE_ROLES or (d.sval("aria-live") or "off").lower() != "off" for d in iter_nodes(n.children))


def analyze_status_scripts(reporter, docs):
    for doc in docs:
        for text, line0, col0 in doc.scripts:
            if not ACTION_RE.search(text):
                continue
            li = LineIndex(text)
            code = text
            def css_sel(method, arg):
                return ("#" + arg) if method == "getElementById" else arg
            variables = [(m.start(), m.group(1), css_sel(m.group(3), m.group(4))) for m in VAR_DOM_RE.finditer(code)]
            writes = []
            for m in WRITE_RE.finditer(code):
                writes.append((m.start(), m.group(1), m.group(3) and css_sel(m.group(2), m.group(3)), m.group(4), m.group(5)))
            for m in APPEND_RE.finditer(code):
                writes.append((m.start(), m.group(1), m.group(3) and css_sel(m.group(2), m.group(3)), m.group(4), ""))
            for m in JQ_WRITE_RE.finditer(code):
                writes.append((m.start(), m.group(0), m.group(1), m.group(2), m.group(3)))
            done = set()
            for off, target, direct_sel, how, rhs in sorted(writes):
                sel = direct_sel
                name = target
                if not sel:
                    prior = [v for v in variables if v[1] == target and v[0] < off]
                    if not prior:
                        continue
                    sel = prior[-1][2]
                if sel in done:
                    continue
                named = MSG_NAME_RE.search(name if not direct_sel else "") or MSG_NAME_RE.search(sel)
                texty = how in ("textContent", "innerText", "innerHTML", "text", "html") and MSG_TEXT_RE.search(rhs or "")
                if not (named or texty):
                    continue
                if re.search(r"setAttribute\(\s*['\"](role|aria-live)['\"]", code) and (
                        re.search(re.escape(target) + r"\s*\.\s*setAttribute\(\s*['\"](role|aria-live)", code) or
                        re.search(re.escape(sel.lstrip("#.")) + r"[^;\n]*setAttribute\(\s*['\"](role|aria-live)", code)):
                    continue
                hits = _markup_lookup(docs, sel)
                if not hits or any(_is_live(n) for _d, n in hits):
                    continue
                done.add(sel)
                tdoc, tnode = hits[0]
                ln, col = li.pos(off)
                ln, col = (line0, col0 + col - 1) if ln == 1 else (line0 + ln - 1, col)
                reporter.add("status-message-js-no-live", doc.file, ln, col,
                             "Script writes a message into %s (%s) after a submit/click action, but %s at %s:%d has no role=\"status\"/\"alert\"/\"log\" or aria-live, so screen readers will not announce it." % (
                                 sel, how, tnode.selector(), tdoc.file, tnode.line),
                             None, sel, doc.snippet(ln),
                             {"target": sel, "write": how, "target_file": tdoc.file, "target_line": tnode.line,
                              "message_text": (rhs or "").strip()[:80] or None})


# ---------------------------------------------------------------------------
# Cross-file script linking: listeners attached in .js files resolved to markup
# ---------------------------------------------------------------------------
def js_strip_comments(text):
    """Blank // and /* */ comments outside strings, keeping offsets."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "\"'`":
            q = c
            i += 1
            while i < n and text[i] != q:
                if text[i] == "\\":
                    i += 1
                elif text[i] == "\n" and q != "`":
                    break
                i += 1
            i += 1
            continue
        if text.startswith("//", i) and (i == 0 or text[i - 1] != ":"):
            j = text.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = " "
            i = j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
            continue
        i += 1
    return "".join(out)


def js_balanced_end(text, i, stops=")"):
    """Index of the first unmatched closer (or a stop char at depth 0) from i."""
    depth, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "\"'`":
            q = c
            i += 1
            while i < n and text[i] != q:
                if text[i] == "\\":
                    i += 1
                i += 1
            i += 1
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                return i
            depth -= 1
        elif depth == 0 and c in stops:
            return i
        i += 1
    return n


_JS_ID = r"[A-Za-z_$][\w$]*"
_JS_QUERY = (r"(?:document|" + _JS_ID + r")\s*\.\s*(getElementById|querySelectorAll|querySelector|getElementsByClassName|getElementsByTagName)"
             r"\(\s*(['\"`])([^'\"`$]+)['\"`]\s*\)(?:\s*\[\s*0\s*\])?")
_JQ_QUERY = r"(?:\$|jQuery)\(\s*(['\"])([^'\"]+)['\"]\s*\)"
JS_VAR_RE = re.compile(r"(?:\b(?:const|let|var)\s+)?(" + _JS_ID + r"(?:\.[A-Za-z_$][\w$]*)*)\s*=(?![=>])\s*(?:" + _JS_QUERY + "|" + _JQ_QUERY + ")")
JS_FOREACH_RE = re.compile(r"(?:Array\.from\(\s*)?(" + _JS_QUERY + "|" + _JS_ID + r")\s*\)?\s*\.forEach\(\s*(?:function\s*\w*\s*\(\s*(" + _JS_ID + r")|\(?\s*(" + _JS_ID + r")\s*[,)]?[^=]{0,40}?=>)")
JS_FORCALL_RE = re.compile(r"(?:Array\.prototype|\[\s*\])\.forEach\.call\(\s*(" + _JS_QUERY + "|" + _JS_ID + r")\s*,\s*(?:function\s*\w*\s*\(\s*(" + _JS_ID + r")|\(?\s*(" + _JS_ID + r")\s*[,)]?[^=]{0,40}?=>)")
JS_FOROF_RE = re.compile(r"for\s*\(\s*(?:const|let|var)\s+(" + _JS_ID + r")\s+of\s+(" + _JS_QUERY + "|" + _JS_ID + r")\s*\)")
JS_LISTEN_RE = re.compile(r"(" + _JS_QUERY + "|" + _JS_ID + r"(?:\.[A-Za-z_$][\w$]*)*)\s*\.\s*addEventListener\(\s*['\"](\w+)['\"]\s*,\s*")
JS_PROP_RE = re.compile(r"(" + _JS_QUERY + "|" + _JS_ID + r"(?:\.[A-Za-z_$][\w$]*)*)\s*\.\s*on([a-z]+)\s*=(?!=)\s*")
JQ_ON_RE = re.compile(r"(" + _JQ_QUERY + "|" + _JS_ID + r")\s*\.\s*on\(\s*['\"]([\w\s.]+)['\"]\s*,\s*(?:['\"]([^'\"]+)['\"]\s*,\s*)?")
JQ_SHORT_RE = re.compile(r"(" + _JQ_QUERY + r")\s*\.\s*(click|change|keydown|keyup|mouseenter|mouseleave|mouseover|mouseout|focus|blur|hover)\(\s*(?=function|\(|" + _JS_ID + r"\s*=>)")
JS_DELEGATE_RE = re.compile(r"\.\s*(?:closest|matches)\(\s*['\"]([^'\"]+)['\"]\s*\)")
JS_FUNC_RE = re.compile(r"(?:\bfunction\s+(" + _JS_ID + r")\s*\([^)]*\)\s*\{|\b(?:const|let|var)\s+(" + _JS_ID + r")\s*=\s*(?:async\s+)?(?:function\b[^{]*\{|\([^)]*\)\s*=>\s*\{?|" + _JS_ID + r"\s*=>\s*\{?))")
CLICK_EVENTS = {"click", "mousedown", "mouseup", "pointerdown", "pointerup", "dblclick", "touchstart", "touchend"}
KEY_EVENTS = {"keydown", "keyup", "keypress"}
JS_SHOW_EVENTS = {"mouseenter", "mouseover", "focus", "focusin", "pointerenter"}
JS_HIDE_EVENTS = {"mouseleave", "mouseout", "blur", "focusout", "pointerleave"}
TOGGLE_RE = re.compile(r"classList\s*\.\s*(toggle|add|remove)\s*\(|\.className\s*\+?=(?!=)|\.checked\s*=(?!=)|\.hidden\s*=(?!=)|\.style\.(display|visibility)\s*=|dataset\.\w+\s*=(?!=)|toggleClass\(|addClass\(|removeClass\(|\.(slideToggle|toggle)\(|setAttribute\(\s*['\"](data-[\w-]+|class|hidden)['\"]")
SHOW_ACTION_RE = re.compile(r"classList\s*\.\s*(add|remove|toggle)|\.hidden\s*=|removeAttribute\(\s*['\"]hidden|setAttribute\(\s*['\"](hidden|aria-hidden|aria-expanded|class)|style\.(display|visibility|opacity)|\.(show|hide|fadeIn|fadeOut|toggle)\(|showPopover|hidePopover|\.innerHTML\s*=|\.textContent\s*=|appendChild|\.remove\(\)")
ARIA_STATE_JS = {"aria-checked": "ariaChecked", "aria-pressed": "ariaPressed", "aria-expanded": "ariaExpanded"}


class JSListener:
    __slots__ = ("event", "body", "doc", "line", "col", "sel", "via")

    def __init__(self, event, body, doc, line, col, sel, via):
        self.event, self.body, self.doc, self.line, self.col, self.sel, self.via = event, body, doc, line, col, sel, via


def _query_sel(method, arg):
    arg = arg.strip()
    if method == "getElementById":
        return "#" + arg
    if method == "getElementsByClassName":
        return ".".join([""] + arg.split())
    return arg


def parse_css_compound(comp):
    """Parse 'tag#id.cls[attr=v]' (pseudo-classes dropped) to a matcher dict or None."""
    comp = re.sub(r"::?[\w-]+(\([^)]*\))?", "", comp)
    m = re.fullmatch(r"(\*|[a-zA-Z][\w-]*)?((?:[#.][\w-]+|\[[^\]]+\])*)", comp)
    if not m or not comp:
        return None
    tag = m.group(1) if m.group(1) and m.group(1) != "*" else None
    rest = m.group(2) or ""
    attrs = []
    for am in re.finditer(r"\[\s*([\w:-]+)\s*(?:([~|^$*]?=)\s*['\"]?([^'\"\]]*)['\"]?)?\s*\]", rest):
        attrs.append((am.group(1).lower(), am.group(2), am.group(3)))
    return {"tag": tag.lower() if tag else None, "ids": re.findall(r"#([\w-]+)", rest),
            "classes": re.findall(r"\.([\w-]+)", re.sub(r"\[[^\]]*\]", "", rest)), "attrs": attrs}


def _compound_match(n, cm):
    if n.component:
        return False
    if cm["tag"] and n.name != cm["tag"]:
        return False
    if cm["ids"] and (n.sval("id") or "").strip() not in cm["ids"]:
        return False
    cls = n.classes()
    if any(c not in cls for c in cm["classes"]):
        return False
    for name, op, val in cm["attrs"]:
        at = n.a(name)
        if at is None:
            return False
        if op and not at.dynamic:
            v = at.value or ""
            if op == "=" and v != val:
                return False
            if op == "~=" and val not in v.split():
                return False
    return True


def select_nodes(docs, selector):
    """Nodes in markup docs matching a simple CSS selector list (descendant combinators only)."""
    out = []
    for part in split_top(selector or ""):
        comps = [c for c in re.split(r"\s*[>+~]\s*|\s+", part.strip()) if c]
        if not comps:
            continue
        parsed = [parse_css_compound(c) for c in comps]
        if any(p is None for p in parsed) or not any(p["tag"] or p["ids"] or p["classes"] or p["attrs"] for p in parsed[-1:]):
            continue
        for doc in docs:
            for n in iter_nodes(doc.roots):
                if not _compound_match(n, parsed[-1]):
                    continue
                need = list(reversed(parsed[:-1]))
                for a in n.ancestors():
                    if need and _compound_match(a, need[0]):
                        need.pop(0)
                if not need:
                    out.append((doc, n))
    seen, uniq = set(), []
    for d, n in out:
        if id(n) not in seen:
            seen.add(id(n))
            uniq.append((d, n))
    return uniq


class ScriptLinks:
    """Listeners from scripts resolved to markup nodes across the project."""

    def __init__(self, docs):
        self.docs = docs
        self.markup = [d for d in docs if d.roots and d.kind in ("html", "tpl", "vue", "svelte", "jsx", "md")]
        self.pages = [d for d in self.markup if d.kind in ("html", "tpl")]
        self.by_node = {}        # id(node) -> (node, doc, [JSListener])
        self.doc_scripts = {}    # markup doc file -> [stripped script text]
        self.doc_global = {}     # markup doc file -> [JSListener on document/window]
        self.blocks = []         # (script doc, text, line0, col0, targets, funcs, vars)
        src_refs = {}
        for d in self.pages:
            for n in iter_nodes(d.roots):
                if n.name == "script" and n.sval("src"):
                    src_refs.setdefault(os.path.basename(n.sval("src").split("?")[0]), []).append(d)
        for sdoc in docs:
            if not sdoc.scripts:
                continue
            if sdoc.kind in ("js", "jsx") and not sdoc.roots:
                targets = src_refs.get(os.path.basename(sdoc.path)) or self.pages
            elif sdoc.kind in ("html", "tpl", "vue", "svelte", "jsx"):
                targets = [sdoc]
            else:
                continue
            for text, line0, col0 in sdoc.scripts:
                code = js_strip_comments(text)
                self.parse_block(sdoc, code, line0, col0, targets)

    # --- parsing -------------------------------------------------------------
    @staticmethod
    def functions(code):
        funcs = {}
        for m in JS_FUNC_RE.finditer(code):
            name = m.group(1) or m.group(2)
            start = m.end()
            if code[m.end() - 1] == "{":
                end = js_balanced_end(code, start, "")
            else:
                end = js_balanced_end(code, start, ";\n")
            funcs.setdefault(name, code[start:end])
        return funcs

    def parse_block(self, sdoc, code, line0, col0, targets):
        li = LineIndex(code)

        def at(off):
            ln, col = li.pos(off)
            return (line0, col0 + col - 1) if ln == 1 else (line0 + ln - 1, col)

        funcs = self.functions(code)
        variables = []  # (offset, name, selector)
        for m in JS_VAR_RE.finditer(code):
            sel = _query_sel(m.group(2), m.group(4)) if m.group(2) else m.group(6)
            variables.append((m.start(), m.group(1), sel))

        def resolve(expr, off):
            expr = expr.strip()
            qm = re.fullmatch(_JS_QUERY, expr)
            if qm:
                return _query_sel(qm.group(1), qm.group(3))
            qm = re.fullmatch(_JQ_QUERY, expr)
            if qm:
                return qm.group(2)
            if expr in ("document", "window", "document.body", "document.documentElement"):
                return "#global"
            prior = [v for v in variables if v[1] == expr and v[0] <= off]
            if not prior:
                prior = [v for v in variables if v[1] == expr]
            return prior[-1][2] if prior else None

        for rx in (JS_FOREACH_RE, JS_FORCALL_RE, JS_FOROF_RE):
            for m in rx.finditer(code):
                if rx is not JS_FOROF_RE:
                    src, alias = m.group(1), m.group(5) or m.group(6)
                else:
                    alias, src = m.group(1), m.group(2)
                sel = resolve(src, m.start())
                if sel and alias and sel != "#global":
                    variables.append((m.start(), alias, sel))
        variables.sort()

        def body_with_calls(body):
            extra = []
            for name in set(re.findall(r"(?<![\w$.])(" + _JS_ID + r")\s*\(", body)):
                if name in funcs:
                    extra.append(funcs[name])
            ref = body.strip().rstrip(",").strip()
            ref = re.sub(r"^(this|self|\w+)\.(?=\w+$)", "", ref)
            if re.fullmatch(_JS_ID, ref) and ref in funcs:
                extra.append(funcs[ref])
                for name in set(re.findall(r"(?<![\w$.])(" + _JS_ID + r")\s*\(", funcs[ref])):
                    if name in funcs and name != ref:
                        extra.append(funcs[name])
            return body + "\n" + "\n".join(extra)

        found = []  # (offset, target expr or selector, is_selector, event, body)
        for m in JS_LISTEN_RE.finditer(code):
            end = js_balanced_end(code, m.end())
            found.append((m.start(), m.group(1), False, m.group(5).lower(), code[m.end():end]))
        for m in JS_PROP_RE.finditer(code):
            end = js_balanced_end(code, m.end(), ";\n")
            found.append((m.start(), m.group(1), False, m.group(5).lower(), code[m.end():end]))
        for m in JQ_ON_RE.finditer(code):
            end = js_balanced_end(code, m.end())
            body = code[m.end():end]
            for ev in m.group(4).split():
                ev = ev.split(".")[0].lower()
                if m.group(5):
                    found.append((m.start(), m.group(5), True, ev, body))
                else:
                    found.append((m.start(), m.group(1), False, ev, body))
        for m in JQ_SHORT_RE.finditer(code):
            end = js_balanced_end(code, m.end())
            ev = m.group(4).lower()
            evs = ["mouseenter", "mouseleave"] if ev == "hover" else [ev]
            for e in evs:
                found.append((m.start(), m.group(1), False, e, code[m.end():end]))
        for off, target, is_sel, ev, body in found:
            sel = target if is_sel else resolve(target, off)
            if not sel:
                continue
            full = body_with_calls(body)
            ln, col = at(off)
            if sel == "#global":
                lst = JSListener(ev, full, sdoc, ln, col, None, "delegated")
                for t in targets:
                    self.doc_global.setdefault(t.file, []).append(lst)
                # delegated handlers: e.target.closest('.x') / matches('.x')
                for dm in JS_DELEGATE_RE.finditer(body):
                    self.attach(targets, dm.group(1), JSListener(ev, full, sdoc, ln, col, dm.group(1), "delegated"))
                continue
            self.attach(targets, sel, JSListener(ev, full, sdoc, ln, col, sel, "listener"))
        for t in targets:
            self.doc_scripts.setdefault(t.file, []).append(code)
        self.blocks.append((sdoc, code, line0, col0, targets, funcs, variables))

    def attach(self, targets, sel, lst):
        for d, n in select_nodes(targets, sel):
            self.by_node.setdefault(id(n), (n, d, []))[2].append(lst)

    # --- queries -------------------------------------------------------------
    def events(self, n):
        rec = self.by_node.get(id(n))
        return rec[2] if rec else []

    def scripts_for(self, doc):
        return self.doc_scripts.get(doc.file, [])


def _loc(lst):
    return "%s:%d" % (lst.doc.file, lst.line)


def analyze_js_links(reporter, links):
    """Rules that need listeners attached in scripts (often external .js files)."""
    def add(rule, doc, n, msg, severity=None, evidence=None):
        reporter.add(rule, doc.file, n.line, n.col, msg, severity, n.selector(), doc.snippet(n.line), evidence)

    for n, doc, lsts in list(links.by_node.values()):
        evs = {}
        for lst in lsts:
            evs.setdefault(lst.event, []).append(lst)
        scripts = links.scripts_for(doc)
        # ----- 2.1.1 click listener on a non-focusable, non-interactive element
        clicks = [l for e in CLICK_EVENTS for l in evs.get(e, [])]
        if clicks and not n.component and not n.spread and n.name not in ("html", "body", "form", "label", "document", "option", "optgroup"):
            ok = is_native_interactive(n) or is_focusable(n) or n.dyn("tabindex") or n.dyn("role") or is_hidden(n)
            if not ok:
                for a in n.ancestors():
                    if a.component or is_native_interactive(a) or is_focusable(a) or a.role() in INTERACTIVE_ROLES:
                        ok = True
                        break
            if not ok and any(is_focusable(d) or d.component for d in iter_nodes(n.children)):
                ok = True  # a real control inside handles the keyboard
            if not ok:
                has_key = has_handler(n, "onkeydown", "onkeyup", "onkeypress") or any(evs.get(e) for e in KEY_EVENTS)
                tokens = [t for t in [n.sval("id")] + n.classes() if t]
                js_focus = any(re.search(r"tabIndex\s*=\s*0|setAttribute\(\s*['\"]tabindex['\"]", sc) and any(t in sc for t in tokens) for sc in scripts)
                missing = []
                if not js_focus:
                    missing.append("tabindex=\"0\"")
                if not has_key:
                    missing.append("a keydown handler (Enter/Space)")
                if missing:
                    l0 = clicks[0]
                    add("click-no-keyboard", doc, n,
                        "<%s> gets a %s listener in %s (via \"%s\") but has no %s; keyboard users cannot activate it. Use a <button> (or add tabindex=\"0\", a role and Enter/Space handling)." % (
                            n.name, l0.event, _loc(l0), l0.sel, " or ".join(missing)),
                        severity="warn", evidence={"missing": missing, "listener": _loc(l0), "selector": l0.sel, "via": l0.via})
        # ----- 3.2.2 change listener on a select/input that navigates or submits
        itype = (n.sval("type") or "").lower()
        if n.name == "select" or (n.name == "input" and itype not in ("button", "submit", "reset", "image", "hidden")):
            for lst in evs.get("change", []) + evs.get("input", []):
                m = NAVIGATE_RE.search(lst.body)
                if m:
                    add("onchange-navigates", doc, n,
                        "A %s listener in %s changes context (%s) when this <%s> changes; warn users beforehand or use an explicit submit button." % (
                            lst.event, _loc(lst), m.group(0).strip(), n.name),
                        evidence={"listener": _loc(lst), "selector": lst.sel, "action": m.group(0).strip()})
                    break
        # ----- 4.1.2 static ARIA state that the script never updates
        aria_state_check(add, doc, n, lsts, scripts)
        # ----- 1.4.13 hover/focus content with no Escape
        shows = [l for e in JS_SHOW_EVENTS for l in evs.get(e, []) if SHOW_ACTION_RE.search(l.body)]
        hides = [l for e in JS_HIDE_EVENTS for l in evs.get(e, [])]
        if shows and hides and not any(ESC_RE.search(sc) for sc in scripts) and not n.component:
            note = ""
            if any(l.event in ("mouseleave", "mouseout") for l in hides):
                popup = None
                for l in shows:
                    for qm in re.finditer(_JS_QUERY, l.body):
                        hits = select_nodes([doc], _query_sel(qm.group(1), qm.group(3)))
                        if hits:
                            popup = hits[0][1]
                            break
                    if popup is not None:
                        break
                if popup is not None and n not in popup.ancestors() and popup is not n:
                    note = " mouseleave is on the trigger only and the popup (%s, line %d) is outside it, so moving the pointer onto the popup closes it (not hoverable)." % (popup.selector(), popup.line)
                else:
                    note = " Check the popup stays open while the pointer moves onto it (hoverable)."
            add("hover-content-no-dismiss", doc, n,
                "Content is shown on %s and hidden on %s (%s) with no Escape key handler to dismiss it.%s Check dismissible, hoverable and persistent." % (
                    "/".join(sorted({l.event for l in shows})), "/".join(sorted({l.event for l in hides})), _loc(shows[0]), note),
                evidence={"listener": _loc(shows[0]), "selector": shows[0].sel})
    # inline handler attributes for ARIA state checks (no script listener needed)
    for doc in links.markup:
        for n in iter_nodes(doc.roots):
            if id(n) in links.by_node or n.component:
                continue
            if any(at.kind == "handler" for at in n.attrs.values()):
                aria_state_check(add, doc, n, [], links.scripts_for(doc) + [t for t, _l, _c in doc.scripts])
    analyze_error_scripts(reporter, links)


def aria_state_check(add, doc, n, lsts, scripts):
    role = n.role()
    wanted = []
    if role in ("switch", "checkbox", "menuitemcheckbox", "radio", "menuitemradio") and n.a("aria-checked") is not None and not n.dyn("aria-checked"):
        wanted.append("aria-checked")
    for a in ("aria-pressed", "aria-expanded"):
        if n.a(a) is not None and not n.dyn(a):
            wanted.append(a)
    if not wanted or n.spread:
        return
    if n.name == "input" and (n.sval("type") or "").lower() in ("checkbox", "radio") and wanted == ["aria-checked"]:
        return
    bodies = [l.body for l in lsts if l.event in CLICK_EVENTS | KEY_EVENTS | {"change", "input"}]
    bodies += [handler_text(n, h) for h in ("onclick", "onkeydown", "onkeyup", "onchange", "oninput") if has_handler(n, h)]
    toggling = [b for b in bodies if TOGGLE_RE.search(b)]
    if not toggling:
        return
    alltext = "\n".join(scripts + bodies)
    if re.search(r"(setAttribute|toggleAttribute)\(\s*(?![\"'`])", alltext):
        return  # attribute name computed at run time
    for a in wanted:
        if a in alltext or ARIA_STATE_JS[a] in alltext:
            continue
        where = next((_loc(l) for l in lsts if l.body in toggling), "an inline handler")
        add("aria-state-not-updated", doc, n,
            "%s=\"%s\" is set in markup, and the handler in %s toggles a class or state, but no script ever updates %s (setAttribute('%s', ...)); assistive technology keeps announcing the initial state." % (
                a, n.sval(a), where, a, a),
            evidence={"attribute": a, "initial": n.sval(a), "handler": where})


INVALID_SET_RE = re.compile(
    r"(" + _JS_QUERY + "|" + _JQ_QUERY + "|" + _JS_ID + r"(?:\.[A-Za-z_$][\w$]*)*)\s*\.\s*(?:"
    r"setAttribute\(\s*['\"]aria-invalid['\"]\s*,\s*(?!['\"]false['\"]|false\b)"
    r"|ariaInvalid\s*=(?!=)\s*(?!['\"]false['\"]|false\b)"
    r"|classList\s*\.\s*(?:add|toggle)\(\s*['\"](?:invalid|error|is-invalid|has-error|input-error|field-error|is-error|errored|form-error|input--error|field--error)['\"]"
    r"|addClass\(\s*['\"](?:invalid|error|is-invalid|has-error|input-error|field-error)['\"])")
ERR_WRITE_RE = re.compile(
    r"(" + _JS_QUERY + "|" + _JS_ID + r"(?:\.[A-Za-z_$][\w$]*)*)\s*\.\s*(?:textContent|innerText|innerHTML)\s*\+?=(?!=)"
    r"|(" + _JS_QUERY + "|" + _JS_ID + r"(?:\.[A-Za-z_$][\w$]*)*)\s*\.\s*(?:hidden\s*=\s*false|removeAttribute\(\s*['\"]hidden['\"]|style\.display\s*=\s*['\"](?!none))"
    r"|(" + _JS_QUERY + "|" + _JS_ID + r"(?:\.[A-Za-z_$][\w$]*)*)\s*\.\s*classList\s*\.\s*remove\(\s*['\"](?:hidden|d-none|is-hidden|visually-hidden|sr-only)['\"]")
ERR_OTHER_RE = re.compile(r"setCustomValidity\(|reportValidity\(|\balert\(|insertAdjacent(?:HTML|Text)\(|createTextNode\(|\.(?:text|html|show)\(|\.append\(|appendChild\(|replaceChildren\(|"
                          r"(?:error|err|message|msg)\w*\s*(?:\.\w+|\[[^\]]+\])?\s*=(?!=)\s*['\"`]")
ERR_NAME_RE = re.compile(r"err|error|msg|message|feedback|invalid|alert|hint|help", re.I)


def analyze_error_scripts(reporter, links):
    """3.3.1: a field is marked invalid but no error text is written or revealed."""
    for sdoc, code, line0, col0, targets, _funcs, variables in links.blocks:
        sets = list(INVALID_SET_RE.finditer(code))
        if not sets:
            continue
        li = LineIndex(code)

        def resolve(expr):
            expr = expr.strip()
            qm = re.fullmatch(_JS_QUERY, expr)
            if qm:
                return _query_sel(qm.group(1), qm.group(3))
            prior = [v for v in variables if v[1] == expr]
            return prior[-1][2] if prior else None

        writes = [m for m in ERR_WRITE_RE.finditer(code)]
        other = ERR_OTHER_RE.search(code)
        linked_ok = bool(other)
        if not linked_ok and writes:
            # a write to an unresolvable or error-looking target counts as describing the error
            for w in writes:
                expr = w.group(1) or w.group(5) or w.group(9) or ""
                sel = resolve(expr)
                if sel is None or ERR_NAME_RE.search(expr) or ERR_NAME_RE.search(sel):
                    linked_ok = True
                    break
                for _d, node in select_nodes(targets, sel):
                    idv = node.sval("id") or ""
                    for fm in sets:
                        fsel = resolve(fm.group(1))
                        for _d2, field in select_nodes(targets, fsel or ""):
                            refs = ((field.sval("aria-describedby") or "") + " " + (field.sval("aria-errormessage") or "")).split()
                            if idv and idv in refs:
                                linked_ok = True
                if linked_ok:
                    break
        if linked_ok:
            continue
        done = set()
        for fm in sets:
            target = fm.group(1)
            if target in done:
                continue
            done.add(target)
            ln, col = li.pos(fm.start())
            ln, col = (line0, col0 + col - 1) if ln == 1 else (line0 + ln - 1, col)
            sel = resolve(target) or target
            reporter.add("error-not-described", sdoc.file, ln, col,
                         "Script marks %s invalid (sets %s) but never writes an error message or reveals an error container (textContent/innerText/innerHTML, hidden=false, removeAttribute('hidden')) linked by aria-describedby/aria-errormessage; the error is identified by colour or state alone." % (
                             sel, "aria-invalid" if re.search(r"aria-invalid|ariaInvalid", fm.group(0)) else "an error class"),
                         None, sel, sdoc.snippet(ln), {"target": sel, "writes": len(writes)})


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def collect_files(paths):
    out = []
    for p in paths:
        if os.path.isfile(p):
            out.append(p)
            continue
        for dirpath, dirnames, filenames in os.walk(p):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not (d.startswith(".") and d not in (".",)))
            for fn in sorted(filenames):
                ext = os.path.splitext(fn)[1].lower()
                if ext in EXT_KIND and not fn.endswith((".min.js", ".min.css", ".d.ts", ".bundle.js")):
                    out.append(os.path.join(dirpath, fn))
    return out


def file_kind(path):
    return EXT_KIND.get(os.path.splitext(path)[1].lower())


def scan(paths, level="AA", min_severity="info"):
    reporter = Reporter()
    files = collect_files(paths)
    docs = []
    errors = []
    for f in files:
        kind = file_kind(f)
        if kind is None:
            continue
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as e:
            errors.append("%s: %s" % (f, e))
            continue
        display = os.path.relpath(f) if not os.path.isabs(f) or f.startswith(os.getcwd()) else f
        try:
            docs.append(build_document(f, display, kind, text))
        except RecursionError:
            errors.append("%s: nesting too deep; skipped" % f)
    # project-wide SCSS variables: keep those with exactly one literal definition
    defs = {}
    for doc in docs:
        for txt, _l, _c, scss in doc.styles:
            if scss or doc.kind == "scss":
                for m in re.finditer(r"(?m)^\s*(\$[\w-]+)\s*:\s*([^;{}]+?)\s*;", txt):
                    defs.setdefault(m.group(1), set()).add(re.sub(r"!default|!global", "", m.group(2)).strip())
                for m in re.finditer(r"(\$[\w-]+)\s*:\s*[^,;()]+[,)]", txt):  # @use ... with ($x: v, ...)
                    defs.setdefault(m.group(1), set()).add("<configured>")
    global_vars = {k: next(iter(v)) for k, v in defs.items() if len(v) == 1 and "<configured>" not in v}
    # CSS index (project-wide)
    index = CSSIndex()
    css_by_doc = []
    for doc in docs:
        rules_all = []
        for txt, line, col, scss in doc.styles:
            parser = CSSParser(txt, doc.file, line, col, scss=scss or doc.kind == "scss", global_vars=global_vars)
            try:
                rules = parser.parse()
            except RecursionError:
                continue
            index.add(rules)
            rules_all.extend(rules)
        css_by_doc.append(rules_all)
    # global label[for]
    gl_for, gl_dyn = set(), False
    for doc in docs:
        for n in iter_nodes(doc.roots):
            if n.name == "label" or (n.component and "label" in n.name):
                at = n.a("for")
                if at is not None:
                    if at.dynamic:
                        gl_dyn = gl_dyn or doc.kind in ("html", "tpl")
                    else:
                        gl_for.add((at.value or "").strip())
    analyzer = Analyzer(reporter, index, gl_for, gl_dyn)
    ui_ctx = UIContext(docs, index)
    for doc, rules in zip(docs, css_by_doc):
        analyzer.analyze(doc)
        analyze_css(reporter, doc.file, doc.lines, rules, index, ui_ctx)
        analyze_scripts(reporter, doc)
    analyze_custom_toggles(reporter, docs, css_by_doc)
    analyzer.redundant_entry_across_files()
    analyze_status_scripts(reporter, docs)
    analyze_js_links(reporter, ScriptLinks(docs))
    lvl = LEVEL_RANK[level]
    minsev = SEVERITY_RANK[min_severity]
    findings = [f for f in reporter.findings
                if f["level"] and LEVEL_RANK[f["level"]] <= lvl and SEVERITY_RANK[f["severity"]] >= minsev]
    findings.sort(key=lambda f: (f["file"], f["line"], f["col"], f["sc"], f["rule"]))
    return findings, files, errors


def summarize(findings):
    """Summary block shared with wcag_page: by_sc = {sc: {fail, warn, manual, info}}."""
    by_sc, by_sev = {}, {"fail": 0, "warn": 0, "manual": 0, "info": 0}
    for f in findings:
        row = by_sc.setdefault(f["sc"], {"fail": 0, "warn": 0, "manual": 0, "info": 0})
        row[f["severity"]] += 1
        by_sev[f["severity"]] = by_sev.get(f["severity"], 0) + 1

    def sc_key(k):
        return tuple(int(x) for x in k.split("."))
    return {"by_sc": {k: by_sc[k] for k in sorted(by_sc, key=sc_key)}, "by_severity": by_sev}


def list_rules(out):
    rows = []
    for slug, (sc, sev, desc) in RULES.items():
        rows.append((tuple(int(x) for x in sc.split(".")), slug, sc, SC[sc][1], sev, desc))
    rows.sort()
    out.write("%-32s %-8s %-5s %-7s %s\n" % ("RULE", "SC", "LEVEL", "SEV", "DESCRIPTION"))
    for _k, slug, sc, lvl, sev, desc in rows:
        out.write("%-32s %-8s %-5s %-7s %s\n" % (slug, sc, lvl, sev, desc))


def print_text(findings, files, errors, out):
    for f in findings:
        out.write("%s:%d:%d: %s %s (%s) [%s] %s\n" % (f["file"], f["line"], f["col"], f["severity"].upper(), f["id"], f["level"], f["rule"], f["message"]))
        if f["snippet"]:
            out.write("    %s\n" % f["snippet"])
    s = summarize(findings)["by_severity"]
    out.write("\n%d file(s) scanned: %d fail, %d warn, %d manual, %d info\n" % (len(files), s["fail"], s["warn"], s["manual"], s["info"]))
    for e in errors:
        out.write("error: %s\n" % e)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="wcag_scan.py",
        description="Static WCAG 2.2 scanner for HTML, JSX/TSX, Vue, Svelte, templates, Markdown and CSS/SCSS.",
        epilog="Exit codes: 0 = no fail findings, 1 = fail findings, 2 = usage or I/O error.")
    ap.add_argument("paths", nargs="*", metavar="PATH", help="files or directories to scan")
    ap.add_argument("--json", action="store_true", help="emit the JSON envelope")
    ap.add_argument("--level", choices=["A", "AA", "AAA"], default="AA", help="highest conformance level to report (default AA)")
    ap.add_argument("--min-severity", choices=["info", "manual", "warn", "fail"], default="info",
                    help="lowest severity to report (order: info < manual < warn < fail; default info)")
    ap.add_argument("--list-rules", action="store_true", help="list rules and exit")
    ap.add_argument("--version", action="version", version="%s %s (WCAG %s)" % (TOOL, VERSION, WCAG_EDITION))
    args = ap.parse_args(argv)
    if args.list_rules:
        list_rules(sys.stdout)
        return 0
    if not args.paths:
        ap.print_usage(sys.stderr)
        sys.stderr.write("wcag_scan.py: error: at least one PATH is required\n")
        return 2
    missing = [p for p in args.paths if not os.path.exists(p)]
    if missing:
        sys.stderr.write("wcag_scan.py: error: path not found: %s\n" % ", ".join(missing))
        return 2
    findings, files, errors = scan(args.paths, args.level, args.min_severity)
    if args.json:
        env = {
            "meta": {
                "tool": TOOL,
                "version": VERSION,
                "wcag": WCAG_EDITION,
                "target": args.paths[0] if len(args.paths) == 1 else args.paths,
                "date": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "level": args.level,
                "files_scanned": len(files),
                "errors": errors,
            },
            "summary": summarize(findings),
            "findings": findings,
        }
        json.dump(env, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print_text(findings, files, errors, sys.stdout)
    if errors and not findings and not files:
        return 2
    return 1 if any(f["severity"] == "fail" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
