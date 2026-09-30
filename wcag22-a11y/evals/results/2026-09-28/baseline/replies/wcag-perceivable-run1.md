# WCAG 2.2 Level AA audit: Larkspur Library static front end, Principle 1 (Perceivable) only

The pages fail Principle 1. I found 11 confirmed failures across 7 of the 20 Perceivable success criteria. Two more criteria (1.4.4 and 1.4.12) are likely failures that need a rendered check.

**Scope:** `index.html`, `catalog.html`, `events.html`, `login.html`, `signup.html`, `styles.css`, `app.js`, `src/components/*.jsx`, and the SVGs in `images/` for context.
- **Processes covered:** sign in (2 steps), get a card (2 steps), reserving an event seat (dialog), adding to the reading list.
- **Level:** WCAG 2.2 AA, limited to the 20 Principle 1 criteria that are Level A or AA. AAA items are advisory only.
- **Method:** I read every file. No tools ran and nothing was rendered, and no screen reader or browser was used.

**Summary:** 11 nonconformities, 4 deviations, 2 advisories, 8 review notes.
- **Criteria:** 7 fail, 4 pass (from the code only), 7 not applicable, 2 not evaluated (likely fail).
- **Evidence:** a manual read of 5 HTML pages, 1 stylesheet, 1 script, 5 JSX components and 11 SVGs. Contrast ratios are calculated with the WCAG relative-luminance formula from the CSS colour values.

**Severity terms:**
- **Nonconformity:** a confirmed failure.
- **Deviation:** a likely failure that needs confirming in a real browser.
- **Advisory:** best practice only, not a failure.
- **Review note:** something worth recording that isn't a finding.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page, component | `catalog.html:29`, `src/components/SearchBar.jsx:20-21` | The search submit button's only content is an image with `alt=""`, so the button has no name. | `<button class="icon-btn"><img src="images/icon-search.svg" alt=""></button>`. There's no text, `aria-label` or `title`, so a screen reader says just "button". | Use `alt="Search"` on the image, or put `aria-label="Search"` on the button. |
| 2 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page, component | `catalog.html:38`, `:46`, `:54`, `:62`; `src/components/BookCard.jsx:7` | Book cover images have no `alt` attribute at all. | `<img src="images/cover-orchard.svg">`. Screen readers may read out the file name ("cover-orchard.svg"). Each cover shows the title as text (`images/cover-orchard.svg:1`). | The title is already the `<h2>` next to it, so use `alt=""`. Otherwise use `alt="Cover of The Orchard"`. In JSX: `<img src={book.coverUrl} alt="" />`. |
| 3 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page | `index.html:30` | A purely decorative divider has a text alternative that screen readers will read aloud (known failure F38). | `alt="Purple decorative flourish divider"`. `images/flourish.svg` is a single decorative curve. Compare `index.html:52`, which does this correctly. | `alt=""` |
| 4 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A), CAPTCHA clause | page, script | `login.html:45-53`; `app.js:114-120` | The CAPTCHA offers no working alternative in another sense. The "Use an audio check instead" button only shows a line of text. No audio is ever played, so a blind user cannot finish step 2 of sign-in. Because the sign-in process fails, every step of it fails. | The `#captcha-audio` click handler only sets `#audio-instructions.hidden = false`. There is no `<audio>` element and no audio source anywhere. The image alts ("CAPTCHA picture 1") do identify the purpose, which is fine. | Provide a real audio CAPTCHA, or better, drop the image CAPTCHA and use a non-interactive check (a honeypot field, rate limiting). That also fixes 3.3.8, which is outside this audit's scope. |
| 5 | Nonconformity | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (Level A) | page | `events.html:36`, `:43`, `:50`; `styles.css:185-189` | Event names look like headings but are marked up as `<p>` (known failure F2). Screen reader users can't jump between events, and the events sit under the `<h1>` without their own headings. | `<p class="event-title">`, styled at `font-size: 1.4rem; font-weight: bold`. | `<h2 class="event-title">Toddler Rhyme Time</h2>`. Keep "Room schedule" as `h2`, or make the events `h3` under an "Upcoming events" `h2`. |
| 6 | Nonconformity | WCAG-1.3.5 | WCAG 2.2 SC 1.3.5 (Level AA) | page | `signup.html:34`, `:38`, `:42`, `:46`, `:50`, `:59` | Sign-up fields that collect the user's own details have no `autocomplete` token, so browsers and assistive tools can't identify or autofill them. | These inputs have no `autocomplete`: `full-name`, `email`, `phone`, `street`, `postcode`, `card-email`. The PIN fields (`:63`, `:67`) and the login and dialog fields are correct. | Add `autocomplete="name"`, `"email"`, `"tel"`, `"street-address"` (or `"address-line1"`), `"postal-code"` and `"email"` respectively. |
| 7 | Nonconformity | WCAG-1.4.1 | WCAG 2.2 SC 1.4.1 (Level A) | script, stylesheet | `app.js:103`; `styles.css:250` | The only sign of an empty required field in step 1 is a border colour change (light grey to red). There's no text, icon or other cue. | The script adds `.invalid`, which only sets `border-color: #c62828`. There is no message and no `aria-invalid`. | Add a visible text error for each field (for example "Enter your full name") and an icon or thicker border. Link the message with `aria-describedby` and set `aria-invalid="true"`. |
| 8 | Nonconformity | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (Level AA) | stylesheet | `styles.css:190` (used at `events.html:37`, `:44`, `:51`) | The event date, time and room text has too little contrast. | `#999999` on `#ffffff` is **2.85:1**, below the 4.5:1 needed for 16 px normal text. | Use `color: #595959` (7.0:1) or `#767676` (4.54:1). |
| 9 | Nonconformity | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (Level AA) | stylesheet | `styles.css:249`; `signup.html:34` | Placeholder text has too little contrast, and on the Full name field it's the only label. | `#aaaaaa` on `#ffffff` is **2.32:1**, where 4.5:1 is required. | Add a real `<label>` (see #13). If placeholders stay, use `#767676` or darker. |
| 10 | Nonconformity | WCAG-1.4.10 | WCAG 2.2 SC 1.4.10 (Level AA) | stylesheet | `styles.css:107` (used at `index.html:56`) | The Staff picks grid has fixed column widths. At 320 CSS px wide (400% zoom) the page scrolls sideways. | `grid-template-columns: repeat(4, 240px)` gives 4 × 240 + 3 × 20 = **1020 px** minimum width. This isn't a data table, so no exception applies. | `grid-template-columns: repeat(auto-fill, minmax(min(15rem, 100%), 1fr));` |
| 11 | Nonconformity | WCAG-1.4.11 | WCAG 2.2 SC 1.4.11 (Level AA) | stylesheet | `styles.css:246-248` (all inputs in `signup.html`) | Sign-up text field borders are almost invisible. The border is the only thing that shows where a field is (white field on a white page). | `.signup-form input { border: 1px solid #d6d6d6 }` overrides `.form-field input`: same specificity, but it comes later in the file. `#d6d6d6` vs `#ffffff` is **1.45:1**, where 3:1 is required. | Delete the override so the shared `#767676` border (4.54:1) applies. |
| 12 | Deviation | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page, component | `events.html:88`; `src/components/Modal.jsx:30` | The dialog's close control is a `<span>` holding the "×" symbol. It has no text alternative, so it's announced as "times" or "multiplication sign", if at all. | `<span class="close" onclick="closeModal()">&times;</span>`. It also fails 4.1.2 and 2.1.1, which are outside this audit's scope. | `<button type="button" class="close" aria-label="Close">×</button>` |
| 13 | Deviation | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (Level A) | page | `signup.html:33-35` | The Full name field has no `<label>`. Its only label is placeholder text, which disappears once the user types, so the label isn't reliably tied to the field. Every other field on the form has a label. | `<input id="full-name" … placeholder="Full name (required)">`. The main failure is 3.3.2, outside this audit's scope. | `<label for="full-name">Full name (required)</label>`, and remove the placeholder. |
| 14 | Deviation | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (Level A) | page | `index.html:85-88` | The visible, focusable social links are hidden from screen readers with `aria-hidden="true"`. Keyboard users can tab to them, but screen readers announce nothing. | `<div class="social" aria-hidden="true"><a href=…>Mastodon</a>…`. This is mainly 4.1.2 (axe rule `aria-hidden-focus`). | Remove `aria-hidden`, and wrap the links in `<nav aria-label="Social media">` or a list. |
| 15 | Deviation | WCAG-1.4.12 | WCAG 2.2 SC 1.4.12 (Level AA); also SC 1.4.4 (Level AA) | stylesheet | `styles.css:191-199` (used at `events.html:39`, `:46`, `:53`) | The "Reserve a seat" buttons have a fixed pixel size and clip overflow. Extra letter and word spacing (1.4.12), or text-only zoom to 200% (1.4.4), will likely cut off the label. | `width: 112px; height: 32px; padding: 0 4px; overflow: hidden; white-space: nowrap; font-size: 15px` leaves 104 px for about 14 characters of 15 px Georgia (roughly 100 px). Adding 0.12em letter spacing adds about 25 px, so the text overflows. This needs a rendered test. | Remove the fixed `width`, `height` and `line-height` and the `overflow: hidden`. Use padding and `min-height: 2rem`. |
| 16 | Advisory | WCAG-BP-heading-order | Best practice (related to SC 1.3.1) | page | `index.html:78` | The heading level jumps from `h2` straight to `h4`. | `<h2>Visit us</h2>` is followed by `<h4>Opening hours</h4>`. | Use `<h3>`. |
| 17 | Advisory | WCAG-BP-current-page-visual | Best practice | stylesheet | `styles.css:52-58`, `:160-169` | `aria-current="page"` on the nav and pager links has no visual style, so sighted users can't see which page they're on. | There's no `[aria-current]` rule in `styles.css`. | Add, for example, `.site-nav a[aria-current], .pager a[aria-current] { text-decoration: underline; font-weight: bold; }`. |

## SC coverage (Principle 1, A + AA: 20 criteria)

| SC | Level | Status | Notes |
|---|---|---|---|
| 1.1.1 Non-text Content | A | **Fail** | #1–4, #12 |
| 1.2.1 Audio-only and Video-only (Prerecorded) | A | N/A | No media. The "audio check" has no audio (#4). |
| 1.2.2 Captions (Prerecorded) | A | N/A | No media |
| 1.2.3 Audio Description or Media Alternative (Prerecorded) | A | N/A | No media |
| 1.2.4 Captions (Live) | AA | N/A | No media |
| 1.2.5 Audio Description (Prerecorded) | AA | N/A | No media |
| 1.3.1 Info and Relationships | A | **Fail** | #5 (plus deviations #13, #14). The table (`events.html:58-82`) has a caption and `th` with `scope`, which passes. The fieldsets and legends pass. |
| 1.3.2 Meaningful Sequence | A | Pass (from the code only) | The DOM order matches the visual order, and CSS doesn't reorder anything. |
| 1.3.3 Sensory Characteristics | A | Pass (from the code only) | "Required" is shown as text. The CAPTCHA's visual instruction is the test itself. |
| 1.3.4 Orientation | AA | Pass (from the code only) | No orientation lock in the CSS or JS. |
| 1.3.5 Identify Input Purpose | AA | **Fail** | #6 |
| 1.4.1 Use of Color | A | **Fail** | #7 |
| 1.4.2 Audio Control | A | N/A | No audio |
| 1.4.3 Contrast (Minimum) | AA | **Fail** | #8, #9. Body text `#222` on white is 15.9:1. Links `#4b2a7b` on white are about 11:1. Nav text is white on `#4b2a7b`. `.btn` is white on `#5b3a9b`, 8.3:1. The footer is `#f0eaf8` on `#2d1a4a`. All of these pass. |
| 1.4.4 Resize Text | AA | Not evaluated (likely fail) | #15. Needs a 200% text-only zoom test. |
| 1.4.5 Images of Text | AA | Pass (from the code only) | The title text on the covers is part of cover art, which counts as essential. See review notes. |
| 1.4.10 Reflow | AA | **Fail** | #10 |
| 1.4.11 Non-text Contrast | AA | **Fail** | #11. Other borders (`#767676`, 4.54:1), the search icon (white on `#5b3a9b`) and the buttons pass. |
| 1.4.12 Text Spacing | AA | Not evaluated (likely fail) | #15 |
| 1.4.13 Content on Hover or Focus | AA | N/A | No tooltips, popovers or hover-revealed content. |

## Review notes

- **Logotype contrast (1.4.3 exception):** `.logo-word` `#c9b6ef` on white (`styles.css:40`) is 1.84:1. This is a logotype, so it's exempt. It's still hard to read and worth darkening.
- **Covers (1.4.5):** `images/cover-*.svg` have the title drawn in as `<text>`. This counts as essential cover art, and the same title is real text in the `<h2>`, so it passes. Finding #2 covers their missing `alt`.
- **Hidden divider done correctly:** `index.html:52` (`alt="" role="presentation"`) is implemented correctly.
- **Carousel (`index.html:34-49`, `app.js:8-18`, `Carousel.jsx`):** slides that are off-screen stay in the DOM and screen readers can reach them. That doesn't fail 1.3.x. The automatic rotation belongs to 2.2.2, which is outside this audit's scope.
- **Sticky header and reflow:** `styles.css:66-67` turns off the sticky header at 640 px wide or less. At 320 × 256 (a 1280 × 1024 screen at 400% zoom) it doesn't take up the viewport, so there's no 1.4.10 problem.
- **Wide table:** the `.table-scroll` region (`events.html:57`, `styles.css:202`) scrolls sideways, which is allowed for data tables under 1.4.10.
- **Small text:** `.fine-print` (`styles.css:200`) uses a fixed 20 px `line-height`. A user style with `!important` still overrides it, so that alone doesn't fail 1.4.12. The pager's 11 px text (`styles.css:164`) is small, but no Principle 1 criterion sets a minimum size.
- **React components:** the JSX in `src/components/` says it's the source for the HTML pages but isn't built. I reported its problems next to the HTML equivalents (#1, #2, #12).

## Outside Principle 1 (not audited)

I noticed these but didn't audit them:
- 2.4.7: `.site-nav a:focus { outline: none }` at `styles.css:59`.
- 2.4.3: positive `tabindex` at `login.html:37` and `login.html:40`.
- 3.3.8: pasting is blocked in the PIN field at `login.html:37`, and the image CAPTCHA also matters here.
- 2.2.1: `<meta http-equiv="refresh" content="120">` at `events.html:6`.
- 3.1.1: missing `lang` at `events.html:2`.
- 2.4.2: missing `<title>` in `catalog.html`.
- 4.1.2: `role="buton"` (typo) at `catalog.html:32`; `div` buttons at `catalog.html:42` and similar.
- 3.3.2 / 4.1.2: unlabelled search input at `catalog.html:28` and `SearchBar.jsx:14`.
- 4.1.3: `#list-status` has no live region.
- 2.1.2: the dialog traps focus and Escape does nothing, at `app.js:83-92` and `Modal.jsx:12-20`.
- 2.5.7: the reading list can only be reordered by dragging.
- 2.2.2: the carousel rotates automatically.
- 2.4.4: "Click here" link at `events.html:32`.
- 2.5.8: 16 × 16 px pager targets at `styles.css:160-169`.

## Manual checks required

These need checking in a real browser before any conformance statement:
- **1.4.4:** 200% text-only zoom on `events.html`.
- **1.4.12:** apply a text-spacing bookmarklet on all 5 pages, especially `.btn-fixed`.
- **1.4.10:** 320 px reflow check on all 5 pages, including the open reservation dialog and signup step 2.
- **1.3.2 / 1.1.1:** screen reader smoke test (for example NVDA + Firefox) to confirm reading order and image announcements.
- **1.4.3 / 1.4.11:** rendered check of any contrast not visible in the static CSS (browser default checkbox and focus styles).

## Not run / not applicable

- No shell was available, so neither the audit tools nor axe-core ran. There were no rendered screenshots and no screen reader or browser testing.
- Every status above comes from reading the code only. None of this is a conformance claim.

## Conformance

The site **does not conform** to WCAG 2.2 Level AA for Principle 1. Failing criteria: 1.1.1, 1.3.1, 1.3.5, 1.4.1, 1.4.3, 1.4.10, 1.4.11. 1.4.4 and 1.4.12 are likely failures. Because the CAPTCHA fails 1.1.1, every step of the sign-in process fails.

## Assumptions

- The five HTML files are the deployed pages, and the JSX mirrors them.
- Default browser styles apply wherever `styles.css` sets nothing (links are underlined; system focus ring).
- The CAPTCHA has no server-side audio beyond what's in the code.

## Reproduction

- Open each HTML file in a browser at 320 px width and at 200% zoom.
- Check the contrast figures with any WCAG contrast checker using the hex values quoted above.
- Inspect the accessibility tree (DevTools, Accessibility pane) for items #1, #2, #3, #12 and #14.
