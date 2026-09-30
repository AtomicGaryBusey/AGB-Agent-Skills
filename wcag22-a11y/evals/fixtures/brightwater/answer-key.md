# Answer key: Brightwater Transit

> **Provenance.** Built on 2026-09-28 as a held-out validation set and kept out of the repository. It was used once, for a blind validation run on 2026-09-29 (see `VALIDATION.md`), and was then retired from held-out duty. It is now a regular fixture. Scores on it are **no longer blind**: the skill and its tools may since have been tuned with this site in view.

Target: `project/` (next to this file). All paths below are relative to that folder. Standard: WCAG 2.2, W3C Recommendation, 12 December 2024. Short fragments of SC text are quoted from https://www.w3.org/TR/WCAG22/ (Copyright © 2024 World Wide Web Consortium. https://www.w3.org/copyright/document-license-2023/ . Status: W3C Recommendation).

The site is static HTML, one stylesheet (`css/site.css`) and vanilla JS (`js/`), plus unbuilt Vue single-file components in `components/`. `fonts/` is empty on purpose: the icon font never loads, and every icon that uses it is `aria-hidden`. Built independently of the wcag22-a11y skill. The "Verified" notes were checked in headless Chrome through the DevTools protocol, and contrast was computed with the WCAG relative-luminance formula. They are collected under "Render verification" at the end.

Detectability labels:
- **static**: can be found from source (HTML/CSS/JS/Vue) without rendering.
- **rendered**: needs computed styles or layout in a real browser (contrast, sizes, overflow, geometry).
- **manual**: needs a human judgment or a scripted interaction (meaning, timing, keyboard or pointer behaviour, cross-page or cross-state comparison).

Scoring: a finding matches when it names the same element or pattern and the same SC. Where a secondary SC is listed as "also acceptable", credit either. The eval graders accept a cited line within ±1 of the lines given here (see `evals/graders/specs/brightwater.json`).

## Summary

| Principle | Count | IDs |
|---|---|---|
| 1 Perceivable | 9 | H01-H08, H26 |
| 2 Operable | 8 | H09-H16 |
| 3 Understandable | 6 | H17-H22 |
| 4 Robust | 3 | H23-H25 |
| **Total** | **26** | |

| Detectability | Count | IDs |
|---|---|---|
| static | 11 | H01, H02, H03, H09, H11, H12, H13, H17, H18, H22, H24 |
| rendered | 5 | H05, H06, H07, H16, H26 |
| manual | 10 | H04, H08, H10, H14, H15, H19, H20, H21, H23, H25 |

WCAG 2.2 new SC seeded: 2.4.11 (H14), 2.5.7 (H15), 2.5.8 (H16), 3.2.6 (H19), 3.3.7 (H21), 3.3.8 (H22).

H01-H25 were seeded. **H26 was not seeded: it was found in the blind validation run** (2026-09-29) and confirmed; the original key lacked it.

Decoys: 6 (HK1-HK6). There are no non-scored notes. A finding on a decoy at "fail" severity is a false positive.

---

## Defects

### Principle 1: Perceivable

**H01: Step-free SVG sprite icon has no text alternative**
- Location: `planner.html:61`, `:70`
- SC: 1.1.1 Non-text Content (A)
- Detectability: static
- Code: `<svg class="ico" width="20" height="20"><use href="img/sprite.svg#step-free"></use></svg>`. The icon is the only indication that trips 1 and 3 are step-free (trip 2 lacks it). No `role="img"`, `aria-label`, `<title>` or visible text. Verified: Chrome exposes two `image` nodes with an empty name.
- Fix: `<svg class="ico" role="img" aria-label="Step-free route" ...>`, or add visible text "Step-free" next to the icon and set `aria-hidden="true"` on the SVG.

**H02: Fare table headers are `<td>` cells styled as headers**
- Location: `fares.html:48-59` (header rows), `:62`, `:70`, `:78`, `:86` (row headers); CSS `css/site.css:121` (`.fare-table td.th`)
- SC: 1.3.1 Info and Relationships (A)
- Detectability: static
- Code: `<td class="th" colspan="2">Single ride</td>` ... `<td class="th">Adult</td>`. The table has no `<th>` elements (verified). The two-level column headers (Single ride / Day pass over zones) and the rider-type row headers are only visual (bold and shaded).
- Fix: use `<thead>` with `<th scope="colgroup" colspan="2">` for the top row, `<th scope="col">` for the zone row and `<th scope="row">` for rider types.

**H03: Claim contact fields do not identify their input purpose**
- Location: `claim-1.html:36`, `:40`, `:44`
- SC: 1.3.5 Identify Input Purpose (AA)
- Detectability: static
- Code: `<input id="c-name" name="name" type="text">`, `<input id="c-email" name="email" type="email" autocomplete="off">`, `<input id="c-phone" name="phone" type="tel">`. These collect the user's own name, email and phone, but carry no autocomplete token (email is explicitly `off`).
- Fix: `autocomplete="name"`, `autocomplete="email"`, `autocomplete="tel"`.

**H04: Peak fares are distinguished only by red text**
- Location: `fares.html:42` (legend), `:63-64` (and every `<span class="peak">` in rows 71-72, 79-80, 87-88); CSS `css/site.css:122` (`.fare-table .peak`)
- SC: 1.4.1 Use of Color (A)
- Detectability: manual
- Code: legend "Peak fares are shown in red." and `<td>$2.50 <span class="peak">$3.25</span></td>` with `.fare-table .peak { color: #c0392b; }`. Peak red against the off-peak text colour #1b2a3a is 2.68:1 (below 3:1), and there is no underline, label, weight or symbol difference.
- Fix: add a text label ("$3.25 peak"), or split peak and off-peak into separate labelled columns.

**H05: Floating labels on the feedback form have insufficient text contrast**
- Location: CSS `css/site.css:179-180` (`.float-field label { ... color: #a0a0a0; }`); affects `feedback.html:35`, `:39`, `:52`
- SC: 1.4.3 Contrast (Minimum) (AA)
- Detectability: rendered
- Code: `color: #a0a0a0` on the #ffffff input background = 2.61:1 (verified computed colour rgb(160,160,160)). These are real `<label>` elements (not placeholders), and they stay grey when floated, so they are text that needs 4.5:1.
- Fix: use a label colour of at least #767676 (4.54:1), for example `var(--ink)` or #5a6570.

**H06: Alert details force horizontal scrolling at 320 CSS px**
- Location: CSS `css/site.css:136` (`.alert-detail { min-width: 880px; ... }`); affects `alerts.html:53`, `:58`
- SC: 1.4.10 Reflow (AA)
- Detectability: rendered
- Code: `min-width: 880px` on blocks of plain prose. At a 320px viewport the document `scrollWidth` is 896px (verified), so each line of alert text needs horizontal scrolling. This is running text, not content that needs two-dimensional layout.
- Fix: remove `min-width` (use `max-width: 60rem` if needed) so text wraps.

**H07: Account toggle switch track and thumb have almost no contrast**
- Location: `components/ToggleSwitch.vue:32-38`
- SC: 1.4.11 Non-text Contrast (AA)
- Detectability: rendered
- Code: `.toggle__track { background: #f1f1f1; border: 1px solid #dddddd; }` and a white thumb with a #e2e2e2 ring. Track border against the page is 1.36:1, track fill 1.13:1, and thumb against track 1.13:1. In the off state the control and its state are close to invisible. The on state (#0b5cad) is fine.
- Fix: give the off track a border or fill of at least 3:1 (for example `border: 2px solid #6b7785`) and make the thumb contrast 3:1 with the track.

**H08: Zone tooltip cannot be hovered or dismissed**
- Location: `components/ZoneInfoTooltip.vue:8-11`, `:42-43`
- SC: 1.4.13 Content on Hover or Focus (AA)
- Detectability: manual
- Code: `@mouseenter="open = true" @mouseleave="open = false"` are on the trigger button only, and the tip is placed `top: calc(100% + 10px)`. Moving the pointer toward the tooltip crosses a 10px gap, which fires `mouseleave` and closes it (not hoverable). No Escape handler exists, so you can only dismiss it by moving the pointer or focus (not dismissible).
- Fix: put the mouse handlers on the wrapper `.zone-info` and remove the gap (or bridge it), and add a `keydown.esc` handler at document level that sets `open = false`.

**H26: Footer focus ring has insufficient non-text contrast** (found in blind validation, not seeded)
- Location: CSS `css/site.css:31` (`:focus-visible { outline: 3px solid var(--brand); outline-offset: 2px; }`), `css/site.css:57` (`.site-footer { background: var(--brand-dark); ... }`); tokens at `css/site.css:10-11` (`--brand: #0b5cad`, `--brand-dark: #12324f`). Affects the footer links (`.footer-links a`, and `.chat-cta` on feedback.html) on every page.
- SC: 1.4.11 Non-text Contrast (AA): the focus indicator is a visual cue required to identify the state of a user interface component.
- Detectability: rendered
- Code: the global outline colour #0b5cad drawn, with a 2px offset, on the footer background #12324f is 1.97:1 (below 3:1). The link text (#cfe3f7 on #12324f, 10.0:1) is fine; only the focus ring fails. In the header and main content the same ring is on white (6.67:1) and passes.
- Fix: a footer-specific ring, for example `.site-footer :focus-visible { outline-color: #ffffff; }` (12.9:1 on #12324f), or a two-colour ring.
- Not to be confused with H13 (the ring is removed entirely from `.site-nav` links) or 2.4.13 Focus Appearance (AAA, out of scope).

### Principle 2: Operable

**H09: Route map stops can only be selected with a pointer**
- Location: `map.html:43-49`, `js/map.js:15-19`
- SC: 2.1.1 Keyboard (A)
- Detectability: static
- Code: `<g class="stop" data-stop="market"><circle .../>...</g>` with only `g.addEventListener('click', ...)`. The groups have no tabindex, role or key handler (verified: tabIndex -1 on all 7), and the stop details (lines, step-free status) cannot be reached any other way.
- Fix: make each stop a focusable control (for example `tabindex="0" role="button" aria-label="Market Square"` with Enter and Space handlers), or provide an equivalent keyboard-operable stop list.

**H10: Email-alerts modal is a keyboard trap**
- Location: `alerts.html:66-77` (close control at `:68`), `js/alerts.js:73-86`
- SC: 2.1.2 No Keyboard Trap (A). Also acceptable: 2.1.1 for the unfocusable close control.
- Detectability: manual
- Code: the custom `div` modal's keydown handler cancels Escape (`e.preventDefault(); // avoid losing a half-typed address`) and forces Tab and Shift+Tab to cycle between the email input and Subscribe. The only close control is `<span class="modal__close">&times;</span>` (not focusable). Backdrop-click closing is mouse only. Verified: 6 Tab and Shift+Tab presses stayed on alert-email and alert-subscribe, and Escape left the modal open.
- Fix: make the close control a `<button>`, let Escape close the modal and return focus to the opener (or use `<dialog>.showModal()`).

**H11: Auto-advancing CSS carousel has no pause mechanism**
- Location: CSS `css/site.css:82-85`, `:88-93`; `index.html:34-47`
- SC: 2.2.2 Pause, Stop, Hide (A)
- Detectability: static
- Code: `.promo-track { animation: promo-slide 18s ease-in-out infinite; }`. The slides move automatically forever, beside other content, for more than 5 seconds, with no pause, stop or hide control (no button in the carousel, verified) and no `prefers-reduced-motion` override.
- Fix: add a Pause/Play button that toggles `animation-play-state`, pause on hover and focus, or do not auto-advance.

**H12: Positive tabindex gives an illogical focus order on sign-in**
- Location: `login.html:41`, `:42`
- SC: 2.4.3 Focus Order (A)
- Detectability: static
- Code: `<button type="submit" class="btn" tabindex="2">Sign in</button>` and `<a href="help.html#account" tabindex="1">Create an account</a>`. Verified tab sequence: "Create an account", "Sign in", then the skip link, the logo and so on. The credential fields come after the whole header.
- Fix: remove both tabindex attributes.

**H13: Main navigation links suppress the focus indicator**
- Location: CSS `css/site.css:52`
- SC: 2.4.7 Focus Visible (AA)
- Detectability: static
- Code: `.site-nav a:focus { outline: none; }`. Its specificity (0,2,1) beats the global `:focus-visible` rule (0,1,0), and no replacement style exists (the underline is hover-only). Verified computed `outline-style: none` on focus. This affects every page.
- Fix: delete the rule, or give it a visible replacement (for example `outline: 3px solid var(--brand)`).

**H14: Fixed "dock" footer entirely hides focused form fields**
- Location: CSS `css/site.css:189`; `feedback.html:64-72`
- SC: 2.4.11 Focus Not Obscured (Minimum) (AA)
- Detectability: manual
- Code: `.dock-footer { position: fixed; bottom: 0; min-height: 12rem; z-index: 50; }` with an opaque background, and no `scroll-padding-bottom`. The browser treats an element in the bottom 192px band as already in view and does not scroll. Verified at 1280x800: tabbing to `#fb-message` puts it at top 634, while the footer covers 608 to 800, so the element is entirely behind the footer (`elementFromPoint` at its centre returns the footer). Other controls are hidden the same way at other viewport heights.
- Fix: `html { scroll-padding-bottom: 13rem; }`, or make the footer non-fixed or collapsible.

**H15: Dashboard saved-trips reorder needs dragging**
- Location: `components/SavedTrips.vue:8-17`, `:29-41`
- SC: 2.5.7 Dragging Movements (AA). Also acceptable: 2.1.1 (no keyboard way to reorder).
- Detectability: manual
- Code: `draggable="true" @dragstart=... @drop="onDrop(index)"` is the only way to reorder. There are no Move up and Move down buttons, menu or single-pointer alternative, and the instructions say "Drag a trip to change the order". Compare HK3, which is compliant.
- Fix: add "Move up" and "Move down" buttons (or a position select) per item, as in `planner.html`.

**H16: Alert banner controls are 16x16 px and tightly packed**
- Location: `alerts.html:32-34`; CSS `css/site.css:132-135` (`.mini-btn`)
- SC: 2.5.8 Target Size (Minimum) (AA)
- Detectability: rendered
- Code: `.mini-btn { width: 16px; height: 16px; margin-left: 4px; }`. Verified rects: x = 1208, 1228 and 1248, each 16x16, so centres are 20px apart. 24px circles centred on adjacent targets intersect (20 < 24), so the spacing exception fails. No inline, essential or equivalent exception applies.
- Fix: `min-width: 24px; min-height: 24px` (44px preferred), or at least 8px gaps so the centres are 24px or more apart.

### Principle 3: Understandable

**H17: Fares page has no page language**
- Location: `fares.html:2`
- SC: 3.1.1 Language of Page (A)
- Detectability: static
- Code: `<html>` with no `lang` (verified `document.documentElement.lang === ""`). All other pages use `lang="en"`.
- Fix: `<html lang="en">`.

**H18: Zone select navigates away as soon as its value changes**
- Location: `fares.html:34-39`, `js/fares.js:7-9`
- SC: 3.2.2 On Input (A)
- Detectability: static
- Code: `select.addEventListener('change', function () { window.location.href = 'fares.html?zone=' + ...; });`. Arrowing through the options with the keyboard loads a new page each time, which resets focus to the top. There is no submit button and no advance warning.
- Fix: add a "Show fares" submit button and remove the change handler, or warn users before the control.

**H19: Help link moves to the footer on claim step 2**
- Location: `claim-2.html:24-27` (header has no help link), `claim-2.html:63`; compare `claim-1.html:27`, `claim-3.html:27` and every other page at line 27
- SC: 3.2.6 Consistent Help (A). Also acceptable: 3.2.3 Consistent Navigation.
- Detectability: manual
- Code: on every other page "Help &amp; contact" is the last item in the header, after the main navigation. On `claim-2.html` it is missing from the header and appears as the last footer link, so its order relative to the other page content changes within the same claim process.
- Fix: keep `<a class="help-link" href="help.html">` in the header on claim-2, as on the other pages.

**H20: Feedback form errors are shown only as a red border**
- Location: `js/feedback.js:8-12`, `:16-18`; `feedback.html:40`, `:53`; CSS `css/site.css:187`
- SC: 3.3.1 Error Identification (A)
- Detectability: manual
- Code: `field.classList.toggle('is-invalid', !ok); field.setAttribute('aria-invalid', ...)`. The `aria-describedby` targets `#fb-email-error` and `#fb-message-error` stay `hidden` and empty (verified after an empty submit: `hidden=true`, `textContent=""`). No text says which fields are in error or why, and focus does not move.
- Fix: write messages into the error elements and unhide them (for example "Enter an email address in the format name@example.com"), then move focus to the first invalid field or to an error summary.

**H21: Step 3 asks again for contact details entered in step 1**
- Location: `claim-3.html:32-41` (inputs at `:36` and `:40`); earlier entry at `claim-1.html:40`, `:44`
- SC: 3.3.7 Redundant Entry (A)
- Detectability: manual
- Code: step 1 collects email and phone. Step 3 ("Where should we send updates about this claim?") has empty `#c3-email` and `#c3-phone` fields with no pre-fill and no "use the details from step 1" option. This is not a confirmation, security or no-longer-valid case, so no exception applies.
- Fix: pre-populate from step 1 (hidden fields or session state), offer a "Same as my contact details" checkbox, or drop the duplicate fields.

**H22: Sign-in blocks pasting of the password and the one-time code**
- Location: `js/login.js:8-12`, `:22`; `login.html:50-55`
- SC: 3.3.8 Accessible Authentication (Minimum) (AA)
- Detectability: static
- Code: `function blockPaste(e) { e.preventDefault(); } pw.addEventListener('paste', blockPaste); ... input.addEventListener('paste', blockPaste);`. The OTP is also split into six `maxlength="1"` fields with `autocomplete="off"` (no `one-time-code`). The user must remember the password or transcribe the SMS code digit by digit, which is a cognitive function test with no alternative and no mechanism to help.
- Fix: remove the paste blocking, use one input with `autocomplete="one-time-code"` and allow paste into it (or spread a pasted code across the fields).

### Principle 4: Robust

**H23: Custom notification switch never updates `aria-checked`**
- Location: `alerts.html:41`, `js/alerts.js:26-28`
- SC: 4.1.2 Name, Role, Value (A)
- Detectability: manual
- Code: `function toggle() { sw.classList.toggle('is-on'); }`. After activation the switch looks on, but `aria-checked` stays `"false"` (verified: class `bw-switch is-on`, aria-checked `false`). Assistive technology reports the wrong state.
- Fix: `sw.setAttribute('aria-checked', String(sw.classList.toggle('is-on')));`

**H24: "Locate me" background-image button has no accessible name**
- Location: `planner.html:36`; CSS `css/site.css:103-106`
- SC: 4.1.2 Name, Role, Value (A). Also acceptable: 1.1.1.
- Detectability: static
- Code: `<button type="button" class="btn-locate" id="locate-me"></button>`. The only content is a CSS `background-image: url("../img/locate.svg")`. Verified: the first button in the accessibility tree has name "".
- Fix: `aria-label="Use my current location"`, or visually hidden text inside the button.

**H25: "Refresh alerts" result is not announced**
- Location: `alerts.html:51`, `js/alerts.js:38-46`
- SC: 4.1.3 Status Messages (AA)
- Detectability: manual
- Code: `refreshResult.textContent = 'Checking...'` and then `'Updated at hh:mm. No new alerts.'` into `<span id="refresh-result"></span>`. This element has no `role="status"` or `aria-live` and no live ancestor (verified), and focus stays on the button, so screen reader users are not told the result of their action.
- Fix: `<span id="refresh-result" role="status"></span>` (present in the DOM before it is updated).

---

## Decoys (compliant; must NOT be reported as failures)

**HK1: Fare table scrolls horizontally at narrow widths**
- Location: `fares.html:43`; CSS `css/site.css:118-119` (`.table-scroll { overflow-x: auto; }`, `.fare-table { min-width: 760px; }`)
- SC queried: 1.4.10 Reflow (AA)
- Why it complies: data tables are content that needs a two-dimensional layout for use and meaning, which the SC excepts. Only the table scrolls: the page `scrollWidth` stays 320 at a 320px viewport (verified), and the region is keyboard-scrollable (`tabindex="0"`, `role="region"`, labelled by the caption). The table's real defects are H02 and H04, not reflow.

**HK2: Low-contrast "Submit claim" button**
- Location: `claim-3.html:46`; CSS `css/site.css:68`
- SC queried: 1.4.3 Contrast (Minimum) (AA); also 1.4.11
- Why it complies: the button is `disabled` until the confirmation box is checked. Text or controls "that are part of an inactive user interface component" have no contrast requirement (#9aa3ad on #e4e7ea = 2.06:1 is allowed). When enabled it uses `.btn`, which is white on #0b5cad = 6.67:1.

**HK3: Drag-to-reorder saved trips in the trip planner**
- Location: `planner.html:77-101`, `js/planner.js:19-58`
- SC queried: 2.5.7 Dragging Movements (AA); also 2.1.1
- Why it complies: each item has real "Move up" and "Move down" buttons, a single-pointer (and keyboard) alternative to dragging. Instructions mention both methods, focus stays on the pressed button, and the move is announced through `role="status"`. The visible text starts the accessible name ("Move up Home to Work"), so 2.5.3 also passes. Compare H15.

**HK4: 20x20 px map zoom buttons**
- Location: `map.html:33-36`; CSS `css/site.css:159-163`
- SC queried: 2.5.8 Target Size (Minimum) (AA)
- Why it complies: the targets are below 24x24 but meet the spacing exception. The buttons are stacked with an 8px gap (verified: y = 227.9 and 255.9, so the centres are 28px apart). 24px circles centred on each do not intersect each other (28 > 24) or any other target, because the toolbar has 12px padding and a border and the nearest stop circle is more than 100px away.

**HK5: Native `<dialog>` with no focus-trap or Escape code**
- Location: `index.html:64-71`, `js/site.js:1-12`
- SC queried: 2.1.2 No Keyboard Trap (A); also 2.4.3
- Why it complies: `showModal()` makes the rest of the page inert, moves focus into the dialog (verified: focus goes to "Close"), and closes it natively on Escape (verified: `open=false` after Escape). The close handler returns focus to the opener (verified `activeElement` = `open-survey`). A standard exit method works, so there is no trap, and the focus order is logical.

**HK6: Pale "Brightwater Transit" wordmark in the header**
- Location: CSS `css/site.css:48` (`.logo .wordmark { color: #9cc3e6; }`); markup `index.html:12-15`, and the same lines 12-15 on every page
- SC queried: 1.4.3 Contrast (Minimum) (AA)
- Why it complies: 1.85:1 on white would fail as body text, but this is the agency's logotype (brand name in the logo link, next to the logo mark). "Text that is part of a logo or brand name has no contrast requirement." The link still has an accessible name ("Brightwater Transit") and a focus indicator (the global `:focus-visible`; the `outline: none` in H13 applies only to `.site-nav a`).

---

## Render verification (headless Chrome through CDP, 2026-09-28)

- H01: two `image` nodes with an empty name in the accessibility tree.
- H02: zero `<th>` elements in the fare table.
- H05: label computed colour rgb(160,160,160) on white, 2.61:1.
- H06: document `scrollWidth` 896 at a 320px viewport on alerts.html. HK1: fares.html `scrollWidth` 320.
- H09: `tabIndex` -1 on all 7 stop groups.
- H10: 6 Tab and Shift+Tab presses stay on `alert-email` / `alert-subscribe`; Escape leaves the modal open.
- H12: tab order "Create an account", "Sign in", skip link, logo.
- H13: computed `outline-style: none` on a focused `.site-nav a`.
- H14: at 1280x800, `#fb-message` at top 634 under a footer covering 608-800; `elementFromPoint` returns the footer.
- H16: `.mini-btn` rects at x = 1208, 1228, 1248, each 16x16.
- H17: `document.documentElement.lang === ""`.
- H20: after an empty submit, both error elements `hidden=true`, `textContent=""`.
- H23: after activation, class `bw-switch is-on`, `aria-checked="false"`.
- H24: first button in the accessibility tree has name "".
- H25: `#refresh-result` has no role or `aria-live` and no live ancestor.
- H26 (blind validation, 2026-09-29): #0b5cad on #12324f = 1.97:1.
- HK4: zoom buttons at y = 227.9 and 255.9 (centres 28px apart).
- HK5: focus moves to "Close" on open; `open=false` after Escape; focus returns to `open-survey`.
