# Answer key: Larkspur Library

Target: `project/` (this fixture). All paths below are relative to that folder. Standard: WCAG 2.2, W3C Recommendation, 12 December 2024. Short fragments of SC text are quoted from https://www.w3.org/TR/WCAG22/ (Copyright © 2024 World Wide Web Consortium. https://www.w3.org/copyright/document-license-2023/ . Status: W3C Recommendation).

Built independently, without reading the wcag22-a11y skill. Every "rendered" claim below was checked in headless Chromium (playwright-core). The results are listed under "Render verification" at the end.

Detectability labels:
- **static**: can be found from source (HTML/CSS/JS/JSX) without rendering.
- **rendered**: needs computed styles or layout in a real browser (contrast, sizes, overflow, geometry).
- **manual**: needs a human judgment or a scripted interaction (meaning, timing, keyboard or drag behaviour, cross-page comparison).

## Summary

| Principle | Count | IDs |
|---|---|---|
| 1 Perceivable | 10 | D01-D10 |
| 2 Operable | 11 | D11-D21 |
| 3 Understandable | 4 | D22-D25 |
| 4 Robust | 5 | D26-D30 |
| **Total** | **30** | |

| Detectability | Count | IDs |
|---|---|---|
| static | 13 | D01, D04, D11, D13, D15, D16, D18, D22, D25, D26, D27, D28, D29 |
| rendered | 7 | D06, D07, D08, D09, D10, D19, D21 |
| manual | 10 | D02, D03, D05, D12, D14, D17, D20, D23, D24, D30 |

WCAG 2.2 new SC seeded: 2.4.11 (D19), 2.5.7 (D20), 2.5.8 (D21), 3.2.6 (D23), 3.3.7 (D24), 3.3.8 (D25).

Decoys: 6 (K1-K6). Non-scored notes: 3 (N1-N3). A finding on a decoy or a note at "fail" severity is a false positive.

---

## Defects

### Principle 1: Perceivable

**D01: Informative images with no alt attribute**
- Location: `catalog.html:38`, `:46`, `:54`, `:62` (`.book-card img`); source `src/components/BookCard.jsx:7`
- SC: 1.1.1 Non-text Content (A). Failure technique F65.
- Detectability: static
- Code: `<img src="images/cover-orchard.svg">` / `<img src={book.coverUrl} />`
- Fix: Add alt text, such as `alt="Cover of The Orchard"`. The cover sits next to the title link, so `alt=""` is also acceptable. The attribute must be present.

**D02: Decorative image with a non-null text alternative**
- Location: `index.html:30` (`img.divider`, flourish.svg)
- SC: 1.1.1 Non-text Content (A): pure decoration must be "implemented in a way that it can be ignored by assistive technology". Failure technique F39.
- Detectability: manual (a scanner sees a valid alt; a person must judge that the image is pure decoration)
- Code: `<img class="divider" src="images/flourish.svg" alt="Purple decorative flourish divider">`
- Fix: `alt=""`, or use a CSS background. Compare decoy K1 at `index.html:52`.

**D03: Visual headings not marked up as headings**
- Location: `events.html:36`, `:43`, `:50` (`p.event-title`); CSS `styles.css:185` (`.event-title`: 1.4rem, bold)
- SC: 1.3.1 Info and Relationships (A). Failure technique F2: changes in text presentation convey structure without the matching markup.
- Detectability: manual (a heuristic can flag large bold `<p>` text; a person confirms that it acts as a heading)
- Code: `<p class="event-title">Toddler Rhyme Time</p>`
- Fix: `<h2 class="event-title">Toddler Rhyme Time</h2>`. The page has an h1 and a later h2, so h2 is correct.
- See N1: a plain heading-level skip is not scored.

**D04: Personal-data fields have no autocomplete purpose**
- Location: `signup.html:34` (full-name), `:38` (email), `:42` (phone), `:46` (street), `:50` (postcode), `:59` (card-email)
- SC: 1.3.5 Identify Input Purpose (AA). These fields collect the user's own data, and their purposes (name, email, tel, street-address, postal-code) are in the Input Purposes list. Nothing makes the purpose programmatically determinable.
- Detectability: static
- Code: `<input id="email" name="email" type="email" required>`
- Fix: `autocomplete="name"`, `"email"`, `"tel"`, `"street-address"`, `"postal-code"` and `"email"` for these fields in order.

**D05: Errors shown only by colour**
- Location: `app.js:103` (`f.classList.add('invalid')`); CSS `styles.css:250` (`.signup-form input.invalid { border-color: #c62828; }`)
- SC: 1.4.1 Use of Color (A). Failure technique F81. It also fails 3.3.1 Error Identification (A), because the error is never described in text.
- Detectability: manual (click "Next" with empty fields; the only change is the red border, and no text or `aria-invalid` is added)
- Fix: Set `aria-invalid="true"`. Add a text message linked with `aria-describedby`, such as "Enter your street address", and an error icon or text prefix. Move focus to an error summary.

**D06: Low-contrast body text**
- Location: CSS `styles.css:190` (`.event-meta { color: #999999; }`); used at `events.html:37`, `:44`, `:51`
- SC: 1.4.3 Contrast (Minimum) (AA). #999999 on #ffffff is 2.85:1. The minimum is 4.5:1 (16px normal weight text, not large).
- Detectability: rendered
- Fix: `color: #595959` (7.0:1) or `#767676` (4.54:1).

**D07: Placeholder is the only label, and its contrast is low**
- Location: `signup.html:34` (`#full-name`); CSS `styles.css:249` (`.signup-form input::placeholder { color: #aaaaaa; }`)
- SC: 1.4.3 Contrast (Minimum) (AA). Understanding 1.4.3 says the SC "applies to text in the page, including placeholder text". #aaaaaa on #ffffff is 2.32:1, and this is the only visible label text. Secondary: 3.3.2 Labels or Instructions (A) is commonly cited, because the only label and the "(required)" instruction disappear when the user types. Understanding 3.3.2 does not name placeholder-only labels explicitly, so score the 1.4.3 failure as primary and accept 3.3.2 as a match.
- Detectability: rendered
- Code: `<input id="full-name" name="full-name" type="text" placeholder="Full name (required)" required>`
- Fix: Add a visible `<label for="full-name">Full name (required)</label>`. Keep any placeholder at 4.5:1 or better (for example #767676).

**D08: Reflow failure at 320 CSS px**
- Location: CSS `styles.css:105-107` (`.featured-row { grid-template-columns: repeat(4, 240px); }`); used at `index.html:56`
- SC: 1.4.10 Reflow (AA). At a 320px viewport, `document.documentElement.scrollWidth` is 1036, so the user must scroll in two directions. Text cards are not "content which requires two-dimensional layout".
- Detectability: rendered
- Fix: `grid-template-columns: repeat(auto-fill, minmax(min(100%, 15rem), 1fr));`

**D09: Text is clipped when text spacing is increased**
- Location: CSS `styles.css:191-198` (`.btn-fixed { width: 112px; height: 32px; overflow: hidden; white-space: nowrap; }`); used at `events.html:39`, `:46`, `:53`
- SC: 1.4.12 Text Spacing (AA). Failure technique F104. With the SC's spacing values applied (line-height 1.5, letter-spacing 0.12em, word-spacing 0.16em, paragraph spacing 2em), the label needs 132px but the box is 112px. "Reserve a seat" is then cut off. At default spacing the text fits exactly (112/112).
- Detectability: rendered
- Fix: Remove the fixed width, height and `overflow:hidden`. Use `min-width`/`min-height` and padding.

**D10: Form field borders have insufficient non-text contrast**
- Location: CSS `styles.css:246-247` (`.signup-form input { border: 1px solid #d6d6d6; }`); affects every input in `signup.html` (lines 34-67)
- SC: 1.4.11 Non-text Contrast (AA). The border is the only visual cue that identifies the text field (white field on a white page). #d6d6d6 against #ffffff is 1.45:1. The minimum is 3:1.
- Detectability: rendered
- Fix: `border: 1px solid #767676` (4.54:1). The login page already uses this value.

### Principle 2: Operable

**D11: A div acts as a button with no keyboard support**
- Location: `catalog.html:42`, `:50`, `:58`, `:66` (`div.btn.add-btn`); source `src/components/BookCard.jsx:15`
- SC: 2.1.1 Keyboard (A). The element has only an `onclick`, with no `tabindex` and no key handler, so keyboard users cannot reach or activate it. Secondary: 4.1.2 (no button role).
- Detectability: static
- Code: `<div class="btn add-btn" data-title="The Orchard" onclick="addToList(this)">Add to reading list</div>`
- Fix: `<button type="button" class="btn add-btn" data-title="The Orchard">Add to reading list</button>`

**D12: Keyboard trap in the reservation modal**
- Location: `app.js:83-92` (the `keydown` handler: line 85 `if (e.key === 'Tab')` forces focus to `#res-name`; line 89 swallows `Escape`); `events.html:88` (the close control is a non-focusable `<span class="close" onclick=...>`); source `src/components/Modal.jsx:13` and `:30`
- SC: 2.1.2 No Keyboard Trap (A). Failure technique F10. After a user opens "Reserve a seat", Tab, Shift+Tab and Escape all leave focus on `#res-name`. The close control cannot be focused, and "Confirm" cannot be reached. The fields are not in a `<form>`, so Enter does nothing. Focus cannot leave the modal by keyboard. Secondary: 2.1.1 for the close span.
- Detectability: manual (scripted interaction)
- Fix: Cycle focus among the modal's focusable elements instead of pinning it to one field. Close the modal on Escape. Make close a `<button type="button" aria-label="Close">`. Return focus to the button that opened the modal. Alternatively, use `<dialog>` with `showModal()`.

**D13: Meta refresh reloads the page on a timer**
- Location: `events.html:6`
- SC: 2.2.1 Timing Adjustable (A). Failure technique F41. The page reloads every 120 s without warning. The user cannot turn this off, adjust it or extend it, and none of the exceptions applies. A reload also discards anything typed in the modal.
- Detectability: static
- Code: `<meta http-equiv="refresh" content="120">`
- Fix: Remove it. If the data must update, update it in place and give the user control of updates.

**D14: Auto-advancing carousel with no pause control**
- Location: `index.html:34` (`#whats-new`); `app.js:14-17` (`setInterval(..., 4000)`); source `src/components/Carousel.jsx:8`
- SC: 2.2.2 Pause, Stop, Hide (A). Failure technique F16. The content starts to move automatically, continues for more than 5 s (it never stops) and is shown in parallel with other content. There is no pause, stop or hide mechanism.
- Detectability: manual (observe over time; a static heuristic sees `setInterval` with no pause control)
- Fix: Add a visible Pause/Play button. Pause on hover and focus. Honour `prefers-reduced-motion`. Or make the carousel advance only when the user acts.

**D15: Page has no title**
- Location: `catalog.html:3-7` (the `<head>` has no `<title>`)
- SC: 2.4.2 Page Titled (A)
- Detectability: static
- Fix: `<title>Catalog search - Larkspur Library</title>`

**D16: Positive tabindex gives an illogical focus order**
- Location: `login.html:40` (`tabindex="1"` on Continue) and `login.html:37` (`tabindex="2"` on PIN)
- SC: 2.4.3 Focus Order (A). Failure technique F44. The measured order is Continue, then PIN, then the header "Home" link, then the rest of the page, with the card number field near the end. The user reaches the submit button before any field.
- Detectability: static (positive `tabindex`; the illogical order is confirmed by tabbing)
- Fix: Remove both `tabindex` attributes.

**D17: Link purpose cannot be determined ("Click here")**
- Location: `events.html:32` (the link is alone in the `<p>` at lines 31-33)
- SC: 2.4.4 Link Purpose (In Context) (A). Failure technique F63. The link has no context in its sentence, paragraph, list item or table cell, and no preceding heading. It downloads an .ics calendar, which nothing on the page says.
- Detectability: manual (a scanner flags the generic text; a person confirms that no context exists)
- Code: `<p>\n  <a href="calendar.ics">Click here</a>\n</p>`
- Fix: `<a href="calendar.ics">Add all library events to your calendar (.ics)</a>`

**D18: Focus indicator removed from navigation links**
- Location: CSS `styles.css:59` (`.site-nav a:focus { outline: none; }`); affects the nav on all five pages
- SC: 2.4.7 Focus Visible (AA). Failure technique F78. No other focus style replaces the outline, and `:hover` underline does not apply on keyboard focus.
- Detectability: static (CSS)
- Fix: Delete the rule, or use `.site-nav a:focus-visible { outline: 3px solid #ffffff; outline-offset: -3px; }` (white on #4b2a7b is 10.96:1).

**D19: Sticky header hides the focused element (2.2-new)**
- Location: CSS `styles.css:25-26` (`.sticky-page .site-header { position: sticky; top: 0; }`); applied by `catalog.html:8` (`<body class="sticky-page">`). The `<html>` element on catalog.html has no `pad-for-header` class, so there is no `scroll-padding-top`.
- SC: 2.4.11 Focus Not Obscured (Minimum) (AA). Failure technique F110. Verified at 1280x600: when "Tides" has focus and "The Orchard" sits under the 128px header, Shift+Tab moves focus to "The Orchard" at y 88-115. The header bottom is at y 128, so the element is entirely hidden. Chromium does not scroll because the element is already inside the viewport.
- Detectability: rendered
- Fix: Add the same technique as decoy K6 (C43): `html { scroll-padding-top: <header height + margin>; }`. Or do not make the header sticky.

**D20: Reading list can only be reordered by dragging (2.2-new)**
- Location: `catalog.html:83-86` (`<li draggable="true">`); `app.js:49-60` (`bindDrag`: dragstart, dragover, drop); source `src/components/ReadingList.jsx:22`
- SC: 2.5.7 Dragging Movements (AA). The only way to reorder is a drag. There is no single-pointer alternative such as up/down buttons or a "move to position" select. Dragging is not essential, and the author implements the behaviour, not the user agent. Secondary: 2.1.1 (no keyboard way to reorder).
- Detectability: manual (a static heuristic sees `draggable`/drag handlers with no alternative controls)
- Fix: Add a "Move up" and a "Move down" `<button>` to each item, with live-region feedback, or a position `<select>`.

**D21: Pagination targets are too small (2.2-new)**
- Location: CSS `styles.css:160-169` (`.pager a { width: 16px; height: 16px; ... }`); `catalog.html:72-76`
- SC: 2.5.8 Target Size (Minimum) (AA). Measured: 16x16 boxes with centres 20px apart (x = 80, 100, 120, 140, 160). The 24px circles overlap, so the Spacing exception fails. There is no equivalent control, the targets are not inline, the user agent does not set the size, and the presentation is not essential.
- Detectability: rendered
- Fix: `.pager a { min-width: 24px; min-height: 24px; }` (44px is better), or keep 16px and space the centres at least 24px apart.

### Principle 3: Understandable

**D22: Page language missing**
- Location: `events.html:2`
- SC: 3.1.1 Language of Page (A)
- Detectability: static
- Code: `<html>`
- Fix: `<html lang="en">`

**D23: Help link is in a different order on one page (2.2-new)**
- Location: the help mechanism is `<p class="help-bar">Need help? <a href="mailto:...">Ask a Librarian</a> or call (555) 010-2040.</p>`. It is inside the header after the main nav, before `<main>`, at `index.html:22`, `events.html:23`, `login.html:22` and `signup.html:22`. On `catalog.html:93` it is in the footer, after `<main>`.
- SC: 3.2.6 Consistent Help (A). The mechanism gives human contact details and a human contact mechanism. It repeats on multiple pages but does not occur "in the same order relative to other page content" on catalog.html, at the same page variation.
- Detectability: manual (cross-page comparison; can be assisted by a static diff of each page's serialized order)
- Fix: Put the help bar in the same header position on catalog.html (after the nav, inside `.header-inner`).

**D24: Step 2 asks again for data entered in step 1 (2.2-new)**
- Location: `signup.html:58-59` (`#card-email`, "Email address for card notices (required)"); the first entry is `signup.html:38` (`#email`). The step switch at `app.js:99-110` does not copy the value across.
- SC: 3.3.7 Redundant Entry (A). The same process needs the same information (the user's email) again. It is neither auto-populated nor offered for selection. It is not essential, not needed for security, and still valid.
- Detectability: manual (compare fields across steps)
- Fix: Pre-fill `#card-email` from `#email` (G221), offer a "Use the email I entered above" choice, or do not ask again.
- See N2: the confirm-PIN field (`signup.html:67`) is exempt.

**D25: Authentication step blocks paste on the PIN field (2.2-new)**
- Location: `login.html:37`
- SC: 3.3.8 Accessible Authentication (Minimum) (AA). Failure technique F109. Remembering the PIN is a cognitive function test. The step blocks paste and drop, so the "Mechanism" (copy and paste, or a standalone password manager) is defeated. Understanding 3.3.8 says that if "users are prevented from copy and paste operations ... then the page would fail this criterion unless an alternative is provided." Step 1 offers no alternative such as an email link or passkey. The object-recognition CAPTCHA in step 2 is a separate step, so it does not satisfy step 1 (see K4).
- Detectability: static
- Code: `<input id="pin" name="pin" type="password" autocomplete="current-password" tabindex="2" onpaste="return false;" ondrop="return false;">`
- Fix: Remove `onpaste` and `ondrop`, and keep `autocomplete="current-password"`. Optionally offer an email magic link.

### Principle 4: Robust

**D26: Search input has no accessible name or label**
- Location: `catalog.html:28` (`#q`); source `src/components/SearchBar.jsx:14-19`
- SC: 4.1.2 Name, Role, Value (A). Failure technique F68. The input has no label, `aria-label`, `title` or placeholder. Secondary: 1.3.1 and 3.3.2 (no visible label).
- Detectability: static
- Code: `<input type="search" id="q" name="q">`
- Fix: `<label for="q">Search the catalog</label>` (it may be visually hidden, because the h1 gives visible context), or `aria-labelledby` pointing to the h1.

**D27: Icon-only button with no accessible name**
- Location: `catalog.html:29` (`button.icon-btn`); source `src/components/SearchBar.jsx:20-22`
- SC: 4.1.2 Name, Role, Value (A). The button's only content is an image with `alt=""`, so the name is empty. Secondary: 1.1.1 (a functional image needs a text alternative).
- Detectability: static
- Code: `<button type="submit" class="icon-btn"><img src="images/icon-search.svg" alt=""></button>`
- Fix: `<img ... alt="Search">`, or `aria-label="Search"` on the button.

**D28: Custom control with an invalid ARIA role**
- Location: `catalog.html:32` (`span.sort-toggle`); behaviour in `app.js:21-34`
- SC: 4.1.2 Name, Role, Value (A). `role="buton"` is not a valid role, so the focusable, clickable span is exposed as a generic element. Its role cannot be programmatically determined. Keyboard operation works (Enter/Space handler), so only the role and name exposure fail.
- Detectability: static
- Code: `<span class="sort-toggle" role="buton" tabindex="0" id="sort-toggle">Title A&ndash;Z</span>`
- Fix: `<button type="button" class="sort-toggle" id="sort-toggle" aria-label="Sort order: Title A to Z">Title A&ndash;Z</button>`. Or fix the role to `role="button"`.

**D29: Focusable links inside an aria-hidden container**
- Location: `index.html:85` (`div.social[aria-hidden="true"]`) and its links at `:86-87`
- SC: 4.1.2 Name, Role, Value (A). Secondary: 1.3.1. Keyboard users land on the links, but assistive technology gets no name or role for them, so a screen reader user hears nothing on a focus stop.
- Detectability: static
- Code: `<div class="social" aria-hidden="true"><a href="https://social.example/larkspurlib">Mastodon</a> ...`
- Fix: Remove `aria-hidden`. If the links really must be hidden, remove them from the tab order too (`inert` or `tabindex="-1"`).

**D30: Status message is not announced**
- Location: `catalog.html:34` (`<div id="list-status"></div>`); written by `app.js:44`
- SC: 4.1.3 Status Messages (AA). Failure technique F103. "Added 'The Orchard' to your reading list." is inserted without `role="status"` or `aria-live`, and focus does not move. Assistive technology cannot present it. Verified: role=null, aria-live=null.
- Detectability: manual (trigger the action; a static heuristic can flag a `textContent` write to a container with no live role)
- Note: in this static build the triggering div is not keyboard operable (D11). A pointer or screen-reader user still gets no announcement.
- Fix: `<div id="list-status" role="status"></div>`

---

## Decoys (compliant; must NOT be reported as failures)

**K1: Decorative divider correctly hidden**
- Location: `index.html:52`
- Code: `<img class="divider" src="images/rule-leaves.svg" alt="" role="presentation">`
- Why it complies: 1.1.1 says pure decoration is "implemented in a way that it can be ignored by assistive technology". `alt=""` does this (H67), and `role="presentation"` is redundant but valid. It is the correct counterpart of D02.

**K2: Data table with scope attributes**
- Location: `events.html:57-82` (`table.schedule`: `<caption>`, `<th scope="col">` at lines 62-65, `<th scope="row">` at lines 70 and 75)
- Why it complies: This is real tabular data (rooms by weekday). `scope` and `caption` make the header relationships programmatically determinable, which is what 1.3.1 requires (H63, H39). A scanner that flags every `scope` or `<table>` as "layout table misuse" is wrong.
- See N3 for its reflow behaviour.

**K3: Small inline link**
- Location: `events.html:29` (the "access guide" link in `p.fine-print`); CSS `styles.css:200` (`.fine-print { font-size: 14px; line-height: 20px; }`)
- Measured target: 98.5 x 16 CSS px, which is under 24px high.
- Why it complies: The 2.5.8 **Inline** exception applies: "The target is in a sentence or its size is otherwise constrained by the line-height of non-target text." The link is underlined (the default), so 1.4.1 also passes, and #4b2a7b on white is 10.96:1.

**K4: Object-recognition CAPTCHA in authentication step 2**
- Location: `login.html:43-55` (the `#captcha-form` fieldset; legend at line 46; audio alternative at line 52)
- Why it complies with 3.3.8 (AA): The SC allows a cognitive function test in an authentication step if the step provides "**Object Recognition**: The cognitive function test is to recognize objects." "Select every picture that shows a book" is object recognition. Note 1 allows the audio variant too. Understanding 3.3.8 confirms these are "excepted in this criterion at AA level". This would fail 3.3.9 (AAA), which is out of scope.
- It also meets the 1.1.1 CAPTCHA exception: the legend and each image's alt ("CAPTCHA picture 1" etc.) identify and describe the purpose without giving the answer, and an alternative in another modality is offered (the audio button).
- In this static mock-up the audio button only reveals the instructions (`app.js:114-120`), and a production build would supply the sounds. The audio part therefore matters only for 1.1.1, not for the 3.3.8 decoy.
- This is a separate step from D25. Step 1's paste-blocked PIN fails on its own.

**K5: Low-contrast logotype text**
- Location: CSS `styles.css:40` (`.logo-word { color: #c9b6ef; }`, 1.84:1 on white); markup `index.html:12`, and the same line 12 in catalog, events, login and signup
- Why it complies: 1.4.3 exception **Logotypes**: "Text that is part of a logo or brand name has no contrast requirement." The logo is deliberately not a link or control; navigation uses the separate "Home" nav link. This avoids the Understanding 1.4.3 caveat about logos that act as interactive controls. The mark (`.logo-mark`) is `aria-hidden` decoration.

**K6: Sticky header that does not hide focus, thanks to scroll-padding**
- Location: `index.html:2` (`<html lang="en" class="pad-for-header">`), `index.html:9` (`<body class="sticky-page">`); CSS `styles.css:5` (`html.pad-for-header { scroll-padding-top: 14rem; }`, 224px) and `styles.css:25-26` (sticky)
- Why it complies: This is 2.4.11 technique C43. Verified at 1280x600 with the same procedure as D19: the target link starts under the 167px header, and on Shift+Tab the browser scrolls it to y 401-422, fully visible below the header. At widths of 640px or less the header is `position: static` (`styles.css:67`), so no overlap can occur. Same header, same sticky rule as catalog.html, but the result is compliant.

---

## Non-scored notes (neither defect nor decoy; flagging them as "fail" is a false positive)

- **N1**: `index.html:77-78`: h2 "Visit us" is followed by h4 "Opening hours" (a level skip). WCAG 2.2 has no SC that requires sequential heading levels; 1.3.1 is met because the heading is marked up as a heading. This is best practice only (WCAG-BP / info). The genuine heading defect is D03.
- **N2**: `signup.html:66-67`: "Type your PIN again". The 3.3.7 exception applies ("the information is required to ensure the security of the content"), and Understanding 3.3.7 names password confirmation as this case.
- **N3**: `events.html:57` (`div.table-scroll`, CSS `styles.css:202`): at 320px the schedule table is wider than the viewport, but it scrolls inside its own labelled, focusable region, and the page itself does not scroll sideways (scrollWidth 320). 1.4.10 Note 2 lists data tables as content that may need two-dimensional layout.

---

## Render verification (headless Chromium, 2026-09-28)

- `.btn-fixed`: scrollWidth/clientWidth is 112/112 at default and 132/112 with the 1.4.12 spacing values (D09).
- Pager: five 16x16 targets at x = 80, 100, 120, 140, 160 (D21).
- Inline link: 98.5 x 16 (K3).
- Reflow at 320px: index 1036 (D08); catalog, events, login and signup 320.
- 2.4.11: catalog "The Orchard" at y 88-115 under a header ending at 128, entirely hidden (D19). Index "The Orchard" scrolled to y 401-422, below a header ending at 167, visible (K6).
- Modal: Tab, Tab, Shift+Tab, Escape and Tab all leave focus on `#res-name`, and the modal stays open (D12).
- Carousel: the transform changed from none to translateX(-200%) after 8.5 s with no user action (D14).
- Status: text written, role=null, aria-live=null (D30).
- Signup "Next" with empty fields: the `.invalid` class is added to full-name, email, street and postcode, with 0 text error elements (D05).
- Login tab order: Continue, then pin, then Home (D16).
- No JavaScript errors on any page.
