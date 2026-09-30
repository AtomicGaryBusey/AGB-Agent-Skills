# WCAG 2.2 Level AA audit: Larkspur Library static front end (Principle 1, Perceivable)

**Scope:** `index.html`, `catalog.html`, `events.html`, `login.html`, `signup.html`, `styles.css`, `app.js`, `src/components/*.jsx` and the SVGs they reference. I covered all states I could find: the carousel, the reservation modal, both signup steps, both login steps and the signup error state. Level AA, limited to Principle 1. That is 20 success criteria: 1.1.1, 1.2.1–1.2.5, 1.3.1–1.3.5, 1.4.1–1.4.5 and 1.4.10–1.4.13. Criteria in Principles 2–4 and AAA criteria were not assessed. **Method:** I read the source files only. The skill's scanners (`wcag_scan`, `wcag_page`) were **not run**, because there is no shell. No browser rendering was done and no assistive technology (AT) was used.

**Summary:** 13 nonconformities, 2 deviations, 4 advisories, 7 review notes.
- **Criteria results:** 8 fail, 4 pass, 7 not applicable, 1 not evaluated.

**Evidence:** I reviewed all 23 source files and SVGs by hand. Contrast ratios were calculated with the WCAG relative-luminance formula from the hex values in the CSS.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page, component | `catalog.html:29`, `src/components/SearchBar.jsx:20-22` | The search button's only content is an icon with `alt=""`, so the button has no text alternative. Also breaks 4.1.2. | `<button class="icon-btn"><img src="images/icon-search.svg" alt=""></button>`. There is no text node, `aria-label` or `title`, so a screen reader announces just "button". | `<img … alt="Search">`, or keep `alt=""` and add `aria-label="Search"` to the button. |
| 2 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page, component | `catalog.html:38`, `:46`, `:54`, `:62`; `src/components/BookCard.jsx:7` | Book cover images have no `alt` attribute. | `<img src="images/cover-orchard.svg">`. Without `alt`, screen readers fall back to the file name ("cover-orchard.svg"). | The title is already in the adjacent `<h2>`, so use `alt=""`. In JSX: `<img src={book.coverUrl} alt="" />`. |
| 3 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A), CAPTCHA clause | page | `login.html:52-53`, `app.js:114-120` | The CAPTCHA says it has an audio alternative, but none exists. The "Use an audio check instead" button only reveals some instructions. The CAPTCHA exception requires alternatives in other sensory modes. Also relevant to 3.3.8 (out of scope). | The click handler (`app.js:118`) only sets `#audio-instructions.hidden = false`. There is no `<audio>` element, no audio source and no audio inputs. A blind user cannot complete sign-in, and sign-in is a process that must work end to end. | Build a real audio CAPTCHA with accessible controls and answer inputs. Better: replace the CAPTCHA with a non-interactive check (honeypot or rate-limiting) so no one has to pass a sensory test. |
| 4 | Nonconformity | WCAG-1.1.1 | WCAG 2.2 SC 1.1.1 (Level A) | page | `index.html:30` | A decorative divider has descriptive alt text, so screen readers can't skip it (WCAG failure technique F39). | `alt="Purple decorative flourish divider"`. `flourish.svg` is a single decorative curve. The matching divider at `index.html:52` is handled correctly. | `alt=""`, or use a CSS background. |
| 5 | Nonconformity | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (Level A) | page, component | `catalog.html:28`, `src/components/SearchBar.jsx:14-19` | The search field has no label: no `<label>`, `aria-label`, `title` or placeholder. Also breaks 3.3.2 and 4.1.2 (out of scope). | `<input type="search" id="q" name="q">`. Only the nearby icon suggests its purpose. | `<label for="q">Search the catalog</label>`. It can be visually hidden, but a visible label is better. |
| 6 | Nonconformity | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (Level A) | page, stylesheet | `events.html:36`, `:43`, `:50`; `styles.css:185-189` | Event names look like headings but are `<p>` elements (failure technique F2). Screen-reader users can't jump between events. | `<p class="event-title">` is styled `font-size:1.4rem; font-weight:bold`. The page has only an `<h1>` and one `<h2>` at line 56. | `<h2 class="event-title">Toddler Rhyme Time</h2>`, and group each event in an `<article>`. |
| 7 | Nonconformity | WCAG-1.3.5 | WCAG 2.2 SC 1.3.5 (Level AA) | page | `signup.html:34`, `:38`, `:42`, `:46`, `:50`, `:59` | The signup fields ask for the user's own details but have no `autocomplete` tokens. | Missing on full-name, email, phone, street, postcode and card-email. The login form (`login.html:33,37`) and the modal (`events.html:93,97`) do this correctly. | Add `autocomplete="name"`, `"email"`, `"tel"`, `"street-address"`, `"postal-code"` and `"email"` respectively. |
| 8 | Nonconformity | WCAG-1.4.1 | WCAG 2.2 SC 1.4.1 (Level A) | page, stylesheet | `app.js:103`, `styles.css:250` | A required field left empty is marked only by its border turning red. There is no text, icon or change in border width. Also breaks 3.3.1 (out of scope). | `f.classList.add('invalid')` changes the border from `#d6d6d6` to `#c62828`, and nothing else changes. Clicking Next just appears to do nothing. | Add an error message next to each field and link it with `aria-describedby`. Set `aria-invalid="true"`. Optionally add an icon or a thicker border. |
| 9 | Nonconformity | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (Level AA) | stylesheet | `styles.css:190` (used at `events.html:37`, `:44`, `:51`) | Event date, time and room text is too low-contrast. | `#999999` on `#ffffff` = **2.85:1** at 16px normal weight. 4.5:1 is required. | `color:#595959` (7.0:1) or at least `#767676` (4.54:1). |
| 10 | Nonconformity | WCAG-1.4.3 | WCAG 2.2 SC 1.4.3 (Level AA) | stylesheet | `styles.css:249` (used at `signup.html:34`) | The placeholder text is too low-contrast. It is also the only label for the Full name field (see #14). | `#aaaaaa` on `#ffffff` = **2.32:1**. | Use a real `<label>` (see #14). If a placeholder stays, use a colour of at least `#767676`. |
| 11 | Nonconformity | WCAG-1.4.10 | WCAG 2.2 SC 1.4.10 (Level AA) | stylesheet | `styles.css:107` (used at `index.html:56`) | Staff picks have fixed column widths, so the page scrolls sideways at 320 CSS px. | `grid-template-columns: repeat(4, 240px)` plus 3 × 1.25rem gaps = **1020px** minimum width, and no media query overrides it. | `grid-template-columns: repeat(auto-fit, minmax(min(15rem, 100%), 1fr));` |
| 12 | Nonconformity | WCAG-1.4.11 | WCAG 2.2 SC 1.4.11 (Level AA) | stylesheet | `styles.css:246-248` (used at `signup.html:34-67`) | Signup text fields have a very faint border, which is the only thing showing where each field is. | `#d6d6d6` on `#ffffff` = **1.45:1**. 3:1 is required. Other forms use `#767676` (4.54:1). | Delete the `.signup-form input` override so the shared `#767676` border applies. |
| 13 | Nonconformity | WCAG-1.4.12 | WCAG 2.2 SC 1.4.12 (Level AA) | stylesheet | `styles.css:191-199` (used at `events.html:39`, `:46`, `:53`) | "Reserve a seat" buttons have a fixed size and hide overflow, so text is cut off when users increase text spacing. | Content box is 112 − 8 = **104px**. "Reserve a seat" at 15px Georgia is about 92px wide. The 1.4.12 spacing test (letter-spacing 0.12em, word-spacing 0.16em) adds about 30px, to roughly 122px, so the end of "seat" is clipped. This is estimated from font metrics and should be confirmed in a browser. | Remove `width`, `height`, `overflow:hidden` and `line-height:32px`. Use `min-height: 2rem; padding: 0.25rem 0.75rem;` instead. |
| 14 | Deviation | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (Level A) | page | `signup.html:34` | The Full name field has no `<label>`, only a placeholder. Browsers do use the placeholder as a fallback accessible name, but the visible label disappears as soon as the user types. The main failure is 3.3.2 (out of scope). | `<input id="full-name" … placeholder="Full name (required)">`. Every other field on the form has a `<label for>`. | `<label for="full-name">Full name (required)</label>`, and remove the placeholder. |
| 15 | Deviation | WCAG-1.3.1 | WCAG 2.2 SC 1.3.1 (Level A) | page | `index.html:85-88` | Visible, focusable social links are wrapped in `aria-hidden="true"`, so they are hidden from screen readers. The main failure is 4.1.2 (out of scope). | `<div class="social" aria-hidden="true"><a href=…>Mastodon</a>…`. Keyboard users reach links that screen readers never announce. | Remove `aria-hidden`, and wrap the links in `<nav aria-label="Social media">` or a list. |
| 16 | Advisory | WCAG-BP-heading-order | Best practice (related to 1.3.1) | page | `index.html:78` | The heading levels jump from `<h2>` to `<h4>`. | `<h2 id="hours-heading">` → `<h4>Opening hours</h4>` | Use `<h3>`. |
| 17 | Advisory | WCAG-BP-logo-contrast | Related to 1.4.3 (logotype exception) | stylesheet | `styles.css:40` (used at `index.html:12` and line 11–13 of each page) | The wordmark is **1.84:1** (`#c9b6ef` on `#fff`). Logotypes are exempt from 1.4.3, but it is still hard to read. | Brand name text in `.logo-word` | Consider `#4b2a7b` (10.9:1). |
| 18 | Advisory | WCAG-BP-fixed-size-text-boxes | Related to 1.4.4 and 1.4.12 | stylesheet | `styles.css:160-169` (used at `catalog.html:71-77`) | Page-number links use 11px text in fixed 16×16px boxes. When text is enlarged it spills over the borders, though the digits stay readable. The small targets also matter for 2.5.8 (out of scope). | `width:16px; height:16px; font-size:11px; line-height:16px` | Use `min-width: 2.75rem; min-height: 2.75rem; font-size: 1rem;` with padding. |
| 19 | Advisory | WCAG-BP-current-state-visual | Related to 1.3.1 | stylesheet | `styles.css:52-58`, `:160-169` | The current page in the main navigation and the pager is marked only with `aria-current`. Sighted users see no difference. | There is no `[aria-current]` style rule. | `.site-nav a[aria-current], .pager a[aria-current] { font-weight: bold; text-decoration: underline; }` plus a background change. |

## Success-criteria coverage (1.x, Level AA)

| SC | Level | Status | Basis |
|---|---|---|---|
| 1.1.1 Non-text Content | A | **Fail** | #1–#4 |
| 1.2.1 Audio-only and Video-only (Prerecorded) | A | N/A | No media (the "audio check" has no audio, see #3) |
| 1.2.2 Captions (Prerecorded) | A | N/A | No media |
| 1.2.3 Audio Description or Media Alternative | A | N/A | No media |
| 1.2.4 Captions (Live) | AA | N/A | No media |
| 1.2.5 Audio Description (Prerecorded) | AA | N/A | No media |
| 1.3.1 Info and Relationships | A | **Fail** | #5, #6 (plus deviations #14, #15) |
| 1.3.2 Meaningful Sequence | A | Pass (static review) | Source order matches visual order. The modal comes after `<main>` in the DOM, which is fine. The CSS doesn't reorder content. |
| 1.3.3 Sensory Characteristics | A | Pass (static review) | Instructions ("select every picture that shows a book", "Drag titles…") don't rely on shape, position or sound alone. |
| 1.3.4 Orientation | AA | Pass (static review) | No orientation media queries and no `screen.orientation.lock`. |
| 1.3.5 Identify Input Purpose | AA | **Fail** | #7 |
| 1.4.1 Use of Color | A | **Fail** | #8. Body links keep their default underline. |
| 1.4.2 Audio Control | A | N/A | No audio |
| 1.4.3 Contrast (Minimum) | AA | **Fail** | #9, #10. Other text passes: body `#222` 15.9:1; links `#4b2a7b` 10.9:1; nav and footer text 10.9:1 or better; `.btn` white on `#5b3a9b` 8.3:1. |
| 1.4.4 Resize Text | AA | Not evaluated | Needs a rendered 200% test (see Review notes). |
| 1.4.5 Images of Text | AA | Pass (static review) | Titles on the cover art are part of a picture (see Review notes). The search icon is a symbol, not text. |
| 1.4.10 Reflow | AA | **Fail** | #11 |
| 1.4.11 Non-text Contrast | AA | **Fail** | #12. Other components pass: `#767676` borders 4.54:1; `.icon-btn` 8.3:1; pager border 10.9:1. |
| 1.4.12 Text Spacing | AA | **Fail** | #13 |
| 1.4.13 Content on Hover or Focus | AA | N/A | No content appears on hover or focus (no tooltips, `title` popups or menus). |

## Review notes

1. **1.4.4:** `.btn-fixed` and `.pager` are sized in px. Full-page browser zoom scales them, which is enough to meet 1.4.4, so I expect a pass. Text-only zoom (Firefox "Zoom text only") would clip `.btn-fixed` the same way as #13. Please confirm at 200% in a browser.
2. **1.4.5 and cover SVGs:** `images/cover-*.svg` put the book title in an SVG `<text>` element. Text in a picture with other significant visual content is exempt. The fix in #2 (`alt=""`) holds because the title is also real text in the `<h2>` next to each cover.
3. **CAPTCHA alt text:** "CAPTCHA picture 1–4" (`login.html:47-50`) meets the first part of the 1.1.1 CAPTCHA exception, because it names the purpose without giving the answer away. The failure in #3 is the missing alternative modality.
4. **Events table:** `events.html:57-83` scrolls sideways inside `.table-scroll`. Data tables are exempt from 1.4.10. The table structure (`<caption>`, `th scope="col"` and `scope="row"`) passes 1.3.1.
5. **Sticky header:** The sticky header (`styles.css:25-28`, `min-height: 8rem`) switches to static at 640px or narrower (`styles.css:66-68`). So at 320 CSS px it doesn't cut down the reading area, and there is no 1.4.10 issue.
6. **Modal close "×":** `events.html:88` and `Modal.jsx:30` use a text character, not an image, so 1.1.1 doesn't apply. The missing name, role and focusability are 4.1.2 and 2.1.1 problems (see below).
7. **React sources vs. HTML:** The JSX files say they are "not built". The same markup problems appear in both the HTML and the JSX, so both locations are cited.

## Manual checks required (before any conformance statement)

- **1.4.4:** Rendered test at 200% zoom on all five pages, including the open modal and signup step 2.
- **1.4.10, 1.4.12, 1.4.11:** Confirm #11–#13 in a browser: 320 CSS px viewport and the text-spacing bookmarklet on every page and state.
- **Screen reader smoke test (e.g. NVDA + Firefox, VoiceOver + Safari).** No AT was used. Confirm:
  - what the search button and search field announce (#1, #5);
  - that covers are silent after the fix (#2);
  - the name announced for the Full name field (#14);
  - that the social links are exposed after the fix (#15).
- Re-check 1.3.2, 1.3.3, 1.3.4 and 1.4.5 in a rendered page. They currently pass on static review only.

## Not run / not applicable

- `wcag_scan.py`, `wcag_page.mjs` (axe-core) and `wcag_audit.py` were not run because there is no shell. Nothing here comes from a tool, and passing results don't mean the tools would find nothing.
- **Outside the requested scope, but seen while reading.** These matter for conformance and are not assessed further:
  - **Non-interference criteria.** Any failure here stops the whole page from conforming:
    - 2.2.2: the carousel auto-advances every 4s with no pause (`app.js:14-17`, `Carousel.jsx:7-12`).
    - 2.1.2: Tab is locked to one field in the modal and Escape is suppressed (`app.js:83-92`, `Modal.jsx:12-20`).
  - 2.2.1: `<meta http-equiv="refresh" content="120">` (`events.html:6`) reloads the page and wipes an open reservation.
  - 3.1.1: no `lang` attribute (`events.html:2`). 2.4.2: no `<title>` (`catalog.html:3-7`).
  - 2.1.1 and 4.1.2:
    - `div` "buttons" with `onclick` (`catalog.html:42` etc., `BookCard.jsx:15`);
    - `role="buton"` typo (`catalog.html:32`);
    - a close `<span>` you can't reach by keyboard (`events.html:88`).
  - 2.1.1 and 2.5.7: the reading list can only be reordered by dragging (`app.js:49-60`, `ReadingList.jsx`).
  - 2.4.7: `.site-nav a:focus { outline: none; }` (`styles.css:59`). 2.4.3: `tabindex="1"` and `"2"` (`login.html:37,40`).
  - 3.3.8: pasting into the PIN is blocked (`login.html:37`). 3.3.7: email is asked for twice (`signup.html:38,59`).
  - 3.2.6: the help bar moves to the footer on the catalog page (`catalog.html:93`) and is missing from the footer on other pages.
  - 4.1.3: `#list-status` is not a live region (`catalog.html:34`). 2.4.4: "Click here" (`events.html:32`). 2.5.8: 16px pager targets.
- AAA criteria in Principle 1 (1.2.6–1.2.9, 1.3.6, 1.4.6–1.4.9) were not assessed.

## Assumptions

- The audit is against WCAG 2.2 (W3C Recommendation, 12 December 2024). 4.1.1 is not in scope.
- Contrast was calculated from the hex values declared in `styles.css`, against the element's actual background (white unless stated). Text sizes come from the CSS: 1rem = 16px, so none of the flagged text counts as "large text".
- The text-spacing width in #13 is an estimate from Georgia and Times New Roman character widths. It clips with either font.
- The site is plain HTML/CSS/JS. The React components are treated as the source for the same markup.
- No assistive technology or browser was used.

## Conformance

The pages **do not conform** to WCAG 2.2 Level AA, based on Principle 1 alone. Failing criteria: 1.1.1, 1.3.1, 1.3.5, 1.4.1, 1.4.3, 1.4.10, 1.4.11 and 1.4.12. Separately, the non-interference failures listed above (2.2.2 and 2.1.2) would block conformance at any level, whatever the Principle 1 results.

## Reproduction

1. Open each HTML file with `styles.css` and `app.js` loaded.
2. **Contrast (#9, #10, #12):** check `.event-meta` (`#999`), the signup placeholder (`#aaa`) and signup field borders (`#d6d6d6`), each against `#fff`, in any contrast checker.
3. **Reflow (#11):** set the viewport to 320×256 on `index.html` and scroll to "Staff picks". The page scrolls sideways.
4. **Text spacing (#13):** on `events.html`, apply `* { letter-spacing: .12em !important; word-spacing: .16em !important; line-height: 1.5 !important; }`. The "Reserve a seat" labels are cut off.
5. **Colour-only error (#8):** on `signup.html`, click Next with the fields empty. The only change is a red border.
6. **Audio CAPTCHA (#3):** on `login.html`, click "Use an audio check instead". A sentence appears, but there is no audio to play.
7. **Missing names (#1, #2, #5):** open the browser's accessibility tree on `catalog.html`. The search button and search field have no accessible name, and each cover image is named from its file path.
