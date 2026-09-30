# WCAG 2.2 Level AA audit: Larkspur Library static front end, Principle 1 (Perceivable) only

**Scope:** `index.html`, `catalog.html`, `events.html`, `login.html`, `signup.html`, `styles.css`, `app.js` and `src/components/*.jsx` (the JSX files are unbuilt sources for the HTML pages). Processes: sign-in (login steps 1–2), card sign-up (steps 1–2) and event reservation (the dialog). Level AA, limited to the 20 Principle 1 criteria (1.1.1–1.4.13). The criteria version is WCAG 2.2 (W3C Recommendation, 12 Dec 2024). Tools: none. I reviewed the code by reading it, with no rendering, browser or assistive technology.

**Summary:** 11 nonconformities, 3 deviations, 2 advisories and 9 review notes. Of the 20 criteria, 7 fail, 4 pass (static review only), 7 don't apply (N/A) and 2 were not evaluated. **Result: the site does not conform.** The failing criteria are 1.1.1, 1.3.1, 1.3.5, 1.4.3, 1.4.10, 1.4.11 and 1.4.12.

**Evidence:** I read all 5 pages, `styles.css`, `app.js`, the 5 components and the SVG assets. I worked out contrast ratios by hand from the CSS hex values using the WCAG relative-luminance formula. The scanner (`wcag_scan`), page runner (`wcag_page`) and screen-reader test were not run because no shell was available.

## Findings

Severity terms: a **nonconformity** is a confirmed failure. A **deviation** is a likely failure that still needs a rendered test to confirm. An **advisory** is best practice, not a failure.

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page, component | catalog.html:38, :46, :54, :62; src/components/BookCard.jsx:7 | Book cover images have no `alt` attribute. Screen readers may announce the file name (e.g. "cover-orchard.svg"). | `<img src="images/cover-orchard.svg">` has no `alt`. The SVG shows only the title, which the `<h2>` link right next to it already gives. | Add `alt=""` (the heading already gives the title). In BookCard: `<img src={book.coverUrl} alt="" />`. |
| 2 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A); also breaks 4.1.2 | page, component | catalog.html:29; src/components/SearchBar.jsx:20-21 | The search button's only content is an image with `alt=""`, so the button has no text alternative or name. | The button has no text and no `aria-label`. `icon-search.svg` is a magnifier glyph. | `<img src="images/icon-search.svg" alt="Search">`, or put `aria-label="Search"` on the `<button>`. |
| 3 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A), failure technique F38 | page | index.html:30 | A purely decorative divider has alt text, so screen readers announce "Purple decorative flourish divider" and can't skip it. | `flourish.svg` is a single wavy stroke with no information. The similar divider at index.html:52 is correctly hidden. | `alt=""` (optionally `role="presentation"`), matching index.html:52. |
| 4 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A), CAPTCHA exception | page, script | login.html:52-53; app.js:114-120 | The CAPTCHA exception requires the CAPTCHA in another sensory mode. The "audio check" button only reveals a line of text; no audio is ever loaded or played, so the image puzzle has no working non-visual alternative. | The click handler only sets `#audio-instructions.hidden = false`. There is no `<audio>` element or audio source anywhere in the front end. The image alts ("CAPTCHA picture 1"…) are enough under the exception. | Provide a working audio CAPTCHA (an `<audio controls>` element per clip plus answer controls). Better: replace the puzzle with a check that needs no perception, or a human-assisted fallback. |
| 5 | Nonconformity | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (Level A), failure technique F2 | page, stylesheet | events.html:36, :43, :50; styles.css:185-189 | Event names look like headings (1.4rem bold) but are marked up as `<p>`. The three event sections have no heading structure for screen readers. | `<p class="event-title">Toddler Rhyme Time</p>`. The only headings under the `<h1>` are the later `<h2 id="access">` and the dialog's `<h2>`. | Use `<h2 class="event-title">…</h2>`. Optionally make each `.event` an `<article>` (or `<section aria-labelledby>`). |
| 6 | Nonconformity | WCAG-1.3.5 | WCAG 2.2 SC 1.3.5 (Level AA) | page | signup.html:34, :38, :42, :46, :50, :59 | Sign-up fields that collect the user's own details don't declare their purpose, so browsers can't autofill them. | These inputs have no `autocomplete`: `#full-name`, `#email`, `#phone`, `#street`, `#postcode`, `#card-email`. (login.html:33 and events.html:93/97 do set it.) | Add `autocomplete="name"`, `"email"`, `"tel"`, `"street-address"` (or `address-line1`), `"postal-code"` and `"email"` respectively. |
| 7 | Nonconformity | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (Level AA) | stylesheet, page | styles.css:190; events.html:37, :44, :51 | The event date, time and room text has too little contrast. | `#999999` on `#ffffff` = **2.85:1** (4.5:1 required; the text is 16px, normal weight). | `.event-meta { color: #595959; }` (7.0:1) or any colour of at least `#767676` darkness (4.54:1). |
| 8 | Nonconformity | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (Level AA) | stylesheet, page | styles.css:249; signup.html:34 | Placeholder text has too little contrast. On the Full name field it is the only label, so users must be able to read it. | `::placeholder #aaaaaa` on `#ffffff` = **2.32:1**. Placeholder text has no contrast exemption. | Give the field a visible `<label for="full-name">Full name (required)</label>` and drop the placeholder. If you keep a placeholder, use `#767676` or darker. (Missing label: see review note R8.) |
| 9 | Nonconformity | WCAG-1.4.10 | WCAG 2.2 SC 1.4.10 (Level AA) | stylesheet, page | styles.css:105-109; index.html:56 | The Staff picks grid has fixed-width columns, so the home page scrolls sideways at a 320 CSS px viewport (400% zoom). | `grid-template-columns: repeat(4, 240px)` plus 3 × 1.25rem gaps = 1020px minimum width. There is no media query and no `max-width`. | `grid-template-columns: repeat(auto-fill, minmax(min(15rem, 100%), 1fr));` |
| 10 | Nonconformity | WCAG-1.4.11 | WCAG 2.2 SC 1.4.11 (Level AA) | stylesheet, page | styles.css:246-248; signup.html:34-67 | Sign-up inputs are white boxes on a white page. Their 1px border is the only thing that shows where each field is, and it is too faint. | `#d6d6d6` border against `#ffffff` = **1.45:1** (3:1 required). This rule overrides the compliant `#767676` border (4.54:1) set at styles.css:243. | Delete the `.signup-form input { border… }` rule, or use `border: 1px solid #767676`. |
| 11 | Nonconformity | WCAG-1.4.12 | WCAG 2.2 SC 1.4.12 (Level AA) | stylesheet, page | styles.css:191-199; events.html:39, :46, :53 | The "Reserve a seat" buttons cut off their text when users apply the text-spacing overrides the criterion requires. | The button is a fixed `112px × 32px` box with `overflow: hidden` and `white-space: nowrap`. With letter-spacing 0.12em and word-spacing 0.16em at 15px, the label gains about 30px and no longer fits the 104px content box. | Remove the fixed `width`, `height` and `overflow`. Use `min-height: 2rem; padding: 0.25rem 0.75rem;` and let the text wrap. |
| 12 | Deviation | WCAG-1.4.1 | WCAG 2.2 SC 1.4.1 (Level A), failure technique F81 | stylesheet, script | styles.css:250; app.js:102-104 | An empty required field is shown as an error only by its border turning red. There is no icon, text or other visual change. | The only change is `.invalid { border-color: #c62828 }` (from `#d6d6d6`). The two colours differ in lightness by 3.86:1, so some users may notice. I graded this as a deviation rather than a nonconformity because a lightness difference can arguably count as more than colour alone. | Add an inline text message ("Enter your full name") linked with `aria-describedby`, and an error icon or thicker border. Set `aria-invalid="true"`. |
| 13 | Deviation | WCAG-1.4.4 | WCAG 2.2 SC 1.4.4 (Level AA) | stylesheet | styles.css:191-199; styles.css:159-169 | Text in fixed-pixel boxes may clip or overflow when only the text is enlarged. Full-page zoom scales the boxes too and should pass. | The `.btn-fixed` text (15px) doubles to about 30px in a 112px box with `overflow: hidden`. The pager links are 16×16px boxes whose 11px digits spill out at 200%. | Same fix as #11. For the pager, use `min-width: 2.75rem; min-height: 2.75rem; font-size: 1rem;` in rem units. |
| 14 | Deviation | WCAG-1.4.10 | WCAG 2.2 SC 1.4.10 (Level AA) | stylesheet, page | styles.css:206-222; events.html:86-101 | The reservation dialog is vertically centred in a fixed-position backdrop that can't scroll. At 320×256 CSS px (1280×1024 at 400%), the top and bottom of the dialog are likely out of reach, including the Confirm button. | `.modal-backdrop { position: fixed; inset: 0; display: flex; align-items: center; }` has no `overflow-y`. The dialog's estimated height (title, text, 2 fields and a button, plus 3rem of padding) is over 256px. | `.modal-backdrop { overflow-y: auto; align-items: flex-start; padding: 1rem; }` or `.modal { max-height: calc(100vh - 2rem); overflow-y: auto; }` |
| 15 | Advisory | WCAG-BP-logotype-contrast | WCAG 2.2 SC 1.4.3 (Level AA), logotype exception | stylesheet | styles.css:40-41; index.html:12, catalog.html:11, events.html:13, login.html:12, signup.html:12 | The "Larkspur Library" wordmark is hard to read. It is exempt from 1.4.3 because it is a logotype, so this is not a failure. | `#c9b6ef` on `#ffffff` = **1.84:1**. | Use the brand purple `#4b2a7b` for `.logo-word` (about 11:1). |
| 16 | Advisory | WCAG-BP-heading-order | WCAG 2.2 SC 1.3.1 (Level A), best practice | page | index.html:77-78 | The heading level jumps from `<h2>` "Visit us" to `<h4>` "Opening hours". | h2 → h4. No criterion requires headings in sequence. | Change it to `<h3>`. |

## SC coverage

| SC | Level | Status | Notes |
|---|---|---|---|
| 1.1.1 Non-text Content | A | **Fail** | #1–#4 |
| 1.2.1 Audio-only and Video-only (Prerecorded) | A | N/A | No media on any page |
| 1.2.2 Captions (Prerecorded) | A | N/A | No media |
| 1.2.3 Audio Description or Media Alternative (Prerecorded) | A | N/A | No media |
| 1.2.4 Captions (Live) | AA | N/A | No media |
| 1.2.5 Audio Description (Prerecorded) | AA | N/A | No media |
| 1.3.1 Info and Relationships | A | **Fail** | #5 (plus advisory #16; R8) |
| 1.3.2 Meaningful Sequence | A | Pass (static) | Source order matches visual order. Re-sorting reorders the DOM too. |
| 1.3.3 Sensory Characteristics | A | Pass (static) | No shape, location or sound-only instructions outside the CAPTCHA |
| 1.3.4 Orientation | AA | Pass (static) | No orientation media queries or locks in the CSS or JS |
| 1.3.5 Identify Input Purpose | AA | **Fail** | #6 |
| 1.4.1 Use of Color | A | Not evaluated | Deviation #12 is still open |
| 1.4.2 Audio Control | A | N/A | No audio, not even for the "audio check" |
| 1.4.3 Contrast (Minimum) | AA | **Fail** | #7, #8 (#15 exempt) |
| 1.4.4 Resize Text | AA | Not evaluated | Deviation #13 is still open |
| 1.4.5 Images of Text | AA | Pass (static) | See R1 |
| 1.4.10 Reflow | AA | **Fail** | #9 (plus deviation #14) |
| 1.4.11 Non-text Contrast | AA | **Fail** | #10 |
| 1.4.12 Text Spacing | AA | **Fail** | #11 |
| 1.4.13 Content on Hover or Focus | AA | N/A | No content appears on hover or focus (no tooltips, `title` popups or menus) |

## Review notes

- **R1 (1.4.5):** The cover SVGs put the book title in SVG `<text>` inside an `<img>`, which counts as an image of text. A book cover is a presentation where that text is essential, so this is exempt. The real text is in the adjacent `<h2>` anyway.
- **R2 (1.1.1):** Some images are correctly handled and not findings. The leaf divider (index.html:52, `alt="" role="presentation"`) and the logo dots (`aria-hidden`) are correctly hidden. The CAPTCHA images' alts plus the `<legend>` meet the "identify and describe the purpose" half of the CAPTCHA exception. Only the alternative-mode half fails (#4).
- **R3 (1.4.3 / 1.4.11):** The other colour pairs pass:
  - White text on `.btn` / `.icon-btn` purple `#5b3a9b`: 8.35:1.
  - Links `#4b2a7b` on white: about 11:1.
  - Footer `#f0eaf8` on `#2d1a4a`: about 14:1.
  - `#767676` borders on white: 4.54:1.
  - The red error border `#c62828` on white: 5.6:1.
- **R4 (1.4.10):** The schedule table's horizontal scroll area (events.html:57, `.table-scroll`) is exempt because data tables need two-dimensional layout. The sticky header switches to `position: static` at ≤640px (styles.css:66-68), so it doesn't take up the screen at 400% zoom.
- **R5 (1.4.11 vs 2.4.7):** `.site-nav a:focus { outline: none; }` (styles.css:59) removes the focus indicator entirely. That fails 2.4.7, which is outside this Principle 1 scope. Because no author-drawn indicator is left, there is nothing to measure under 1.4.11. Other controls use the browser's default focus ring, which 1.4.11 exempts.
- **R6 (1.3.2):** The carousel's off-screen slides (index.html:34-49) stay in reading order and in the accessibility tree. That is fine for 1.3.2. The auto-rotation is a 2.2.2 matter and outside this scope.
- **R7 (components):** The JSX components copy the HTML defects: BookCard → #1, SearchBar → #2, Modal → same markup as events.html. Carousel.jsx and ReadingList.jsx have no Perceivable-specific defects beyond the HTML ones.
- **R8 (1.3.1 / 3.3.2):** `#full-name` (signup.html:34) is labelled only by its placeholder. The placeholder gives it an accessible name, so I did not fail it under 1.3.1. The missing visible label belongs to 3.3.2, which is outside this scope. The catalog search input (catalog.html:28, SearchBar.jsx:14) has no label at all (3.3.2 / 4.1.2, also outside scope).
- **R9 (1.3.1):** The social links in `<div class="social" aria-hidden="true">` (index.html:85-88) can be focused but are hidden from assistive technology. I graded this under 4.1.2 (outside scope) rather than 1.3.1.

## Manual checks required

- **1.4.1:** Confirm #12 visually, with a colour-blindness simulation and in greyscale, after triggering the step-1 validation on signup.html.
- **1.4.4:** Confirm #13 at 200% with text-only zoom (Firefox "Zoom text only", Safari) and with full-page zoom on events.html and catalog.html.
- **1.4.10:** Confirm deviation #14 at 320×256 CSS px with the reservation dialog open. Re-check #9 once fixed.
- **Rendered confirmation of the static passes:** 1.3.2, 1.3.3, 1.3.4 and 1.4.5 are graded from source only. Confirm them in a browser.
- **Screen-reader smoke test (not done):** confirm the search button name (#2), cover image announcements (#1), event headings (#5) and the CAPTCHA alternative (#4). Use NVDA + Firefox and VoiceOver + Safari.

## Not run / not applicable

- `wcag_scan.py`, `wcag_page.mjs` (axe-core) and `wcag_audit.py` were not run because no shell was available. Everything above comes from reading the source.
- There was no rendering, so there are no screenshots, measured glyph widths or pixel-sampled contrast. Clipping widths in #11 and #13 and the dialog height in #14 are estimates.
- Principles 2–4 are out of scope. Issues I noticed but did not grade (for a follow-up audit):
  - catalog.html has no `<title>` (2.4.2).
  - events.html has no `lang` (3.1.1) and a `meta refresh` of 120s (2.2.1).
  - The carousel has no pause control (2.2.2).
  - Controls built from `div`/`span`: catalog.html:42 etc., events.html:88, and `role="buton"` at catalog.html:32 (2.1.1, 4.1.2).
  - The dialog traps Tab and ignores Escape, app.js:83-92 (2.1.2).
  - Positive `tabindex` at login.html:37 and :40 (2.4.3).
  - Paste is blocked on the PIN field, login.html:37 (3.3.8).
  - Email is asked for again at signup.html:59 (3.3.7).
  - The reading list can only be reordered by dragging (2.5.7).
  - Pager targets are 16px (2.5.8).
  - `#list-status` is not a live region (4.1.3).
  - "Click here" link text at events.html:32 (2.4.4).
  - No error text is shown (3.3.1).
  - The help link moves to the footer on catalog.html:93 (3.2.6).
  - The sticky header on catalog.html has no `scroll-padding`, so it may cover focused elements (2.4.11).

## Assumptions

- The report uses WCAG 2.2. The HTML files are what users receive, and the `src/components` files are unbuilt equivalents audited for parity.
- No assistive technology or browser was used.
- The audio CAPTCHA is judged as delivered: if a server-side audio flow exists, it is not in this front end, and #4 should be re-tested.
- Contrast was calculated from the declared CSS colours against the declared or default white backgrounds.

## Reproduction

1. **Contrast:** check any colour-contrast checker against styles.css:40, :190, :247 and :249.
2. **Reflow:** set the viewport to 320px wide on index.html and scroll horizontally to the Staff picks section.
3. **Text spacing:** apply the WCAG text-spacing bookmarklet (line-height 1.5, paragraph spacing 2em, letter-spacing 0.12em, word-spacing 0.16em) on events.html and look at "Reserve a seat".
4. **Missing alts:** inspect the `<img>` elements at catalog.html:29 and :38 in the accessibility tree.
5. **Error colour:** on signup.html, click Next with the fields empty and note that only the border colour changes.
6. **Audio CAPTCHA:** on login.html, click "Use an audio check instead" and note that no audio control appears.
