# WCAG 2.2 Level AA audit, Principle 1 (Perceivable): Larkspur Library static front end

**Scope:** `index.html`, `catalog.html`, `events.html`, `login.html`, `signup.html`, `styles.css`, `app.js` and `src/components/*.jsx` (SearchBar, BookCard, Modal, Carousel, ReadingList). I also read the referenced SVGs in `images/` to judge their text alternatives.
- **Processes covered:** sign-in (2 steps), card sign-up (2 steps) and event reservation (modal).
- **Level:** AA, limited to the 20 Principle 1 success criteria (1.1.1–1.4.13 at A/AA).
- **Tools:** none. There was no shell, so `wcag_scan` and `wcag_page` did not run. This is a static review of the source only.
- **Assistive technology and browsers:** none.

**Summary:** 12 nonconformities, 4 deviations, 3 advisories, 6 review notes. Of the 20 success criteria: 8 fail, 4 pass (static review, provisional), 7 N/A, 1 not evaluated.

**Evidence:** I read all 5 HTML pages, the CSS, the JS and the 5 JSX files line by line. I worked out contrast ratios by hand from the hex values using the WCAG relative-luminance formula. I estimated reflow and text-spacing results from the CSS box sizes. Nothing was rendered.

**Verdict:** For Principle 1, the site does **not conform** to WCAG 2.2 AA. It fails SC 1.1.1, 1.3.1, 1.3.5, 1.4.1, 1.4.3, 1.4.10, 1.4.11 and 1.4.12.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (A) | page, component | `catalog.html:38`, `catalog.html:46`, `catalog.html:54`, `catalog.html:62`; `src/components/BookCard.jsx:7` | The book-cover `<img>` elements have no `alt` attribute. | There is no `alt` at all, so screen readers fall back to the file name (for example "cover-orchard.svg"). | The title is already in the `<h2>` next to each cover, so use `alt=""`. In BookCard use `<img src={book.coverUrl} alt="" />`. |
| 2 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (A); also breaks 4.1.2 | page, component | `catalog.html:29`; `src/components/SearchBar.jsx:21` | The search button contains only an icon image with `alt=""`, so the button has no text alternative. | This is a functional image and the button's only content. `icon-search.svg` is a white magnifier. | Use `alt="Search"` on the image, or add `aria-label="Search"` to the `<button>`. |
| 3 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (A), CAPTCHA exception | page | `login.html:52-53`; `app.js:117-119` | The picture CAPTCHA is meant to have an alternative in another sense ("Use an audio check instead"), but no audio exists. The button only reveals a line of text telling users to "Listen to four short sounds". | None of the files contains an `<audio>` element or any audio source. `initCaptcha` only sets `hidden = false` on `#audio-instructions`. Blind users cannot complete sign-in step 2, so the whole sign-in process fails. | Provide a working audio challenge, or better, replace the CAPTCHA with a non-visual check such as a honeypot or rate limiting. (3.3.8, outside this audit's scope, points the same way.) |
| 4 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (A) | page | `index.html:30` | A decorative flourish has the alt text "Purple decorative flourish divider", so assistive technology announces it. | `flourish.svg` is a single curved stroke and carries no information. Compare `index.html:52`, which is done correctly. | Use `alt=""`, or use a CSS background image. |
| 5 | Nonconformity | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (A) | page, stylesheet | `events.html:36`, `events.html:43`, `events.html:50`; `styles.css:185-189` | Event names look like headings (1.4rem, bold) but are marked up as `<p class="event-title">`. | The page outline goes straight from the `<h1>` at line 28 to the `<h2>` at line 56. Screen-reader users cannot navigate between events by heading. | Use `<h2 class="event-title">`. Consider wrapping each event in `<article>` or `<li>`. |
| 6 | Nonconformity | WCAG-1.3.5 | WCAG 2.2 SC 1.3.5 (AA) | page | `signup.html:34`, `:38`, `:42`, `:46`, `:50`, `:59` | Fields that collect the user's own details have no `autocomplete` token. | This affects full name, email, phone, street, postcode and card email. The login and modal fields do have tokens, so those are fine. | Add `autocomplete="name"`, `"email"`, `"tel"`, `"street-address"` and `"postal-code"` to the first five fields, and `"email"` to card email. |
| 7 | Nonconformity | WCAG-1.4.1 | WCAG 2.2 SC 1.4.1 (A); also breaks 1.3.1 (and 3.3.1, out of scope) | stylesheet, script | `app.js:103`; `styles.css:250` (the base style is at `styles.css:247`) | A required field left empty is shown only by its border changing colour from grey (#d6d6d6) to red (#c62828). | The border width stays at 1px and no text or icon appears. There is no `aria-invalid` and no error message, so the state is not exposed to assistive technology either. | Show a text error for each field, linked with `aria-describedby`, and set `aria-invalid="true"`. Also add a non-colour cue such as a thicker border or an icon. |
| 8 | Nonconformity | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (AA) | stylesheet | `styles.css:190`; used at `events.html:37`, `:44`, `:51` | The event date, time and room text is `#999999` on `#ffffff`. | The ratio is 2.85:1 against a required 4.5:1 (the text is 16px regular). This is essential information. | Use `#595959` or darker (7:1), or at minimum `#767676` (4.54:1). |
| 9 | Nonconformity | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (AA) (placeholder-as-label is also a 3.3.2 problem, out of scope) | page, stylesheet | `signup.html:34`; `styles.css:249` | The Full name field has no `<label>`. Its only label is placeholder text in `#aaaaaa` on white. | The ratio is 2.32:1 against 4.5:1. The label also disappears once the user starts typing. | Add `<label for="full-name">Full name (required)</label>`, remove the placeholder, and if placeholders are used anywhere, make them `#767676` or darker. |
| 10 | Nonconformity | WCAG-1.4.10 | WCAG 2.2 SC 1.4.10 (AA) | stylesheet | `styles.css:107`; `index.html:56` | The Staff picks grid has fixed columns: `repeat(4, 240px)` plus 3 × 1.25rem gaps comes to about 1020px. | At 320 CSS px (400% zoom) this forces about 700px of horizontal scrolling for ordinary text content. | Use `grid-template-columns: repeat(auto-fit, minmax(min(15rem, 100%), 1fr));`. |
| 11 | Nonconformity | WCAG-1.4.11 | WCAG 2.2 SC 1.4.11 (AA) | stylesheet | `styles.css:246-248`; affects every input at `signup.html:34-67` | The sign-up input borders are `#d6d6d6` on `#ffffff`. | The ratio is 1.45:1 against a required 3:1. The border is the only visual cue that marks out the text field. | Use `#767676` (4.54:1), which is the style the other forms already use at `styles.css:243`. |
| 12 | Nonconformity | WCAG-1.4.12 | WCAG 2.2 SC 1.4.12 (AA) | stylesheet | `styles.css:191-199`; used at `events.html:39`, `:46`, `:53` | The "Reserve a seat" buttons are fixed at 112×32px with `overflow:hidden` and `white-space:nowrap`. | The text box is 104px wide. The label is about 100px at 15px Georgia. The 1.4.12 letter spacing (0.12em = 1.8px × 14 characters ≈ 25px) plus word spacing (0.16em × 2 ≈ 5px) brings it to about 130px, so the label gets clipped. | Remove the fixed `width`, `height` and `overflow`. Use `min-height:2rem`, padding, and `line-height:1.5`. |
| 13 | Deviation | WCAG-1.4.10 | WCAG 2.2 SC 1.4.10 (AA) | stylesheet, component | `styles.css:206-222`; `events.html:86-101`; `src/components/Modal.jsx:28` | The reservation dialog sits in a `position:fixed` backdrop, centred with flexbox and with no `overflow-y:auto`. | The dialog content is about 22rem (roughly 350px) tall. At 320×256 CSS px (400% zoom of 1280×1024), the top and bottom, including the Confirm button, would be cut off and could not be scrolled into view. This needs confirming in a rendered page. | Add `overflow-y:auto` to `.modal-backdrop` and `max-height:100%` (or `align-items:flex-start` on short viewports) to `.modal`. |
| 14 | Deviation | WCAG-1.4.4 | WCAG 2.2 SC 1.4.4 (AA) | stylesheet | `styles.css:191-199`, `styles.css:200` | Fixed pixel boxes and line heights don't grow when only the text is zoomed. | With text-only zoom at 200%: the 15px button label grows to 30px inside a fixed 112×32px box and gets clipped. `.fine-print` text grows to 28px but its `line-height` stays at 20px, so the lines overlap. Whole-page zoom is not affected. This needs a browser check. | Use unitless line heights and rem/em sizes. Applying the fix for finding 12 also fixes the button. |
| 15 | Deviation | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (A) (mainly 4.1.2 and 3.3.2, which are out of scope) | page, component | `catalog.html:28`; `src/components/SearchBar.jsx:14-19` | The search field has no label of any kind, visible or programmatic. | There is no `<label>`, `aria-label` or placeholder. The field's purpose is shown only by the icon on the next button, which itself has no text (finding 2). | Add `<label for="q">Search the catalog</label>` (it can be visually hidden, since the page's `<h1>` already says this). |
| 16 | Deviation | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (A) (mainly 4.1.2, out of scope) | page | `index.html:85-88` | The footer social links are visible and focusable but sit inside a container with `aria-hidden="true"`. | Screen readers cannot see the Mastodon and Photos links, but keyboard focus still lands on them. | Remove `aria-hidden` from `.social`. |
| 17 | Advisory | WCAG-BP-heading-order | Best practice (related to 1.3.1) | page | `index.html:78` | The heading level skips from `<h2>` straight to `<h4>` ("Opening hours"). | The structure still works, but the skipped level can confuse screen-reader users. | Use `<h3>`. |
| 18 | Advisory | WCAG-BP-current-state | Best practice | stylesheet | `styles.css:52-59`, `styles.css:160-169` (the markup at, for example, `index.html:15` and `catalog.html:72`) | `aria-current="page"` has no visual style, so sighted users can't see which nav item or results page is current. | This is not a 1.3.1 failure: the information is exposed programmatically but not shown visually. | Add `[aria-current="page"] { font-weight:bold; text-decoration:underline; }` or similar. |
| 19 | Advisory | WCAG-BP-min-text | Best practice | stylesheet | `styles.css:160-167` | The pager uses 11px text in 16×16px boxes. | This is readable at 200% zoom, so it is not a 1.4.4 failure, but it is very small. (The target size, 2.5.8, is out of scope.) | Use at least `font-size: 1rem` and `min-width/min-height: 2.75rem`. |

## SC coverage (Principle 1, Level A and AA)

| SC | Level | Status | Basis |
|---|---|---|---|
| 1.1.1 Non-text Content | A | **Fail** | Findings #1–4 |
| 1.2.1 Audio-only and Video-only (Prerecorded) | A | N/A | There is no audio or video. The audio CAPTCHA does not exist (#3). |
| 1.2.2 Captions (Prerecorded) | A | N/A | No media |
| 1.2.3 Audio Description or Media Alternative | A | N/A | No media |
| 1.2.4 Captions (Live) | AA | N/A | No media |
| 1.2.5 Audio Description (Prerecorded) | AA | N/A | No media |
| 1.3.1 Info and Relationships | A | **Fail** | #5 and #7. Deviations #15 and #16 |
| 1.3.2 Meaningful Sequence | A | Pass (static, provisional) | The DOM order matches the visual order. The events table has a `<caption>` and uses `scope` correctly. |
| 1.3.3 Sensory Characteristics | A | Pass (static, provisional) | No instructions rely only on shape, position or sound. "Drag titles…" (`catalog.html:81`) is a question for 2.5.7/2.1.1, not 1.3.3. |
| 1.3.4 Orientation | AA | Pass (static, provisional) | No orientation lock in CSS or JS |
| 1.3.5 Identify Input Purpose | AA | **Fail** | #6 |
| 1.4.1 Use of Color | A | **Fail** | #7 |
| 1.4.2 Audio Control | A | N/A | No audio |
| 1.4.3 Contrast (Minimum) | AA | **Fail** | #8 and #9 |
| 1.4.4 Resize Text | AA | Not evaluated | Deviation #14 needs a rendered check |
| 1.4.5 Images of Text | AA | Pass (static, provisional) | The only text inside images is book titles on cover art, which is part of the picture (review note 2). |
| 1.4.10 Reflow | AA | **Fail** | #10, plus deviation #13 |
| 1.4.11 Non-text Contrast | AA | **Fail** | #11 |
| 1.4.12 Text Spacing | AA | **Fail** | #12 |
| 1.4.13 Content on Hover or Focus | AA | N/A | No tooltips, popovers or other content triggered by hover or focus |

## Review notes
1. **Logotype contrast is exempt.** `.logo-word` is `#c9b6ef` on white (`styles.css:40`), which is 1.84:1. It is exempt from 1.4.3 as part of a logo or brand name, and `.logo-mark` is correctly hidden with `aria-hidden`. It is still very faint; darkening it is recommended.
2. **Cover SVGs.** Files such as `images/cover-orchard.svg` render the book title as SVG text. I treated this as part of a picture of the product, not an image of text under 1.4.5. With `alt=""` (finding 1), the title is still available from the `<h2>` next to it.
3. **CAPTCHA text alternatives.** The CAPTCHA images' alt text ("CAPTCHA picture N", `login.html:47-50`) together with the `<legend>` does identify the content and describe its purpose, which the 1.1.1 CAPTCHA exception requires. The failure is only the missing alternative in another modality (finding 3).
4. **`rule-leaves.svg` is fine.** It uses `alt="" role="presentation"` (`index.html:52`), which is correct for decoration.
5. **Carousel.** The slides hidden with `overflow:hidden` stay in the DOM in reading order, so there is no 1.3.2 problem. The auto-rotation every 4 seconds with no pause (`app.js:14-17`, `Carousel.jsx:8-11`) falls under 2.2.2, which is out of scope. See the list below.
6. **React sources.** The JSX components are marked "not built". I reported them with the matching HTML because they carry the same defects into any future build. `Carousel.jsx` and `ReadingList.jsx` have no Principle 1 issues of their own.

## Manual checks required (before any conformance claim)
- **1.4.4:** In Firefox with "Zoom text only" at 200%, check the Events buttons and the `.fine-print` paragraph (#14).
- **1.4.10:** At 320×256 CSS px, check the reservation modal (#13) and confirm #10 on the home page.
- **1.4.12:** Apply the text-spacing bookmarklet on all 5 pages to confirm #12 and find any other clipping.
- **1.4.3 and 1.4.11:** Check contrast with a rendered colour picker, including hover and focus states and the checkbox and CAPTCHA tile borders.
- **1.3.1 and 1.1.1:** Do a screen-reader smoke test (NVDA with Firefox, or VoiceOver with Safari). Confirm the names of the search button and cover images, the event headings, the footer links, and that the sign-up error state is announced.
- **1.3.2, 1.3.3, 1.3.4, 1.4.5:** Confirm the provisional passes in rendered pages.

## Outside scope (not graded here; noted so they are not lost)
The brief limited this audit to Principle 1, but the review also turned up these issues:
- `catalog.html` has no `<title>` (2.4.2).
- `events.html` has no `lang` attribute (3.1.1).
- `events.html:6` refreshes the page every 120 seconds (2.2.1).
- The carousel auto-advances with no pause control (2.2.2).
- `.site-nav a:focus { outline:none }` removes the focus indicator (2.4.7).
- The header is sticky with `min-height: 8rem` and there is no `scroll-padding` on the catalog page (2.4.11).
- `role="buton"` is misspelled (`catalog.html:32`) (4.1.2).
- "Add to reading list" buttons are `<div onclick>`, reachable by mouse only (2.1.1, 4.1.2).
- The modal's close control is an `<span>×</span>`; Escape doesn't close the dialog and Tab is trapped on the first field (2.1.1, 2.1.2, 4.1.2).
- Reading-list reordering is drag-only (2.5.7, 2.1.1).
- `#list-status` has no live-region role (4.1.3).
- The login form uses positive `tabindex` (2.4.3), and the PIN field blocks pasting and the picture CAPTCHA is required (3.3.8).
- Signup asks for the email address twice (3.3.7).
- The events link text is "Click here" (2.4.4).
- Help links are not in a consistent place: the help bar is in the header on most pages but in the footer on catalog and missing from events' footer (3.2.6).
- The pager links are 16×16px (2.5.8).

## Assumptions
- No assistive technology or browser was used, and neither audit tool ran. Every status comes from reading the source.
- Contrast ratios come from the hex values in `styles.css`, assuming the default `#ffffff` page background.
- Text-width estimates assume Georgia at about 0.5em per character on average.
- I treated the JSX files as the planned source for the HTML pages, as their header comments say.

## Reproduction
To get tool evidence where a shell is available:
```
python3 ~/.claude/skills/wcag22-a11y/scripts/wcag_audit.py . --url . --pages 5 --out report.md
```
Then work through the manual checks above.
