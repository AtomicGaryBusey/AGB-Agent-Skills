None of the nine items is a WCAG 2.2 Level AA failure. Each one is either allowed by an exception in the success criterion or is a false positive from the checker. While checking them, though, I found real failures next to three of them (items 4, 6 and 8) and several others elsewhere; they're listed below.

I reviewed the files by reading them only. Nothing was rendered or run, and no screen reader was used.

## Verdict on the nine items

| # | Item | AA failure? | Severity | Why |
|---|---|---|---|---|
| 1 | Leaf divider, `index.html:52`, `alt="" role="presentation"` | **No** | None (pass, 1.1.1) | The image is only decoration, so empty alt is the correct way to hide it from screen readers. `role="presentation"` repeats what `alt=""` already does, which is harmless. |
| 2 | `scope` on the `th` cells of the events schedule | **No** | Checker false positive (pass, 1.3.1) | `events.html:58-82` is a real data table: it has a `<caption>`, column headers with `scope="col"` and row headers with `scope="row"`. That is correct data-table markup, not layout-table misuse. |
| 3 | 'access guide' link, about 16px tall | **No** | None (pass, 2.5.8) | The link is inside a sentence in the fine print (`events.html:29`). SC 2.5.8 exempts targets whose size is set by the surrounding line of text. |
| 4 | Image CAPTCHA, "select every picture that shows a book" | **No** for the CAPTCHA itself | None (3.3.8) | SC 3.3.8 has an **Object Recognition** exception at Level AA, and choosing pictures of books is object recognition. The audio option ("select every sound made by an animal") is also recognition. **But the login process fails 3.3.8 anyway**; see finding A below. |
| 5 | Logo text `#c9b6ef` on white, about 1.84:1 | **No** | None (Advisory) | SC 1.4.3 says "Text that is part of a logo or brand name has no contrast requirement." The site name inside `.logo` is the brand logotype. You may still want to darken it for readability. |
| 6 | Sticky header on index.html hiding focus | **No** (static review; confirm in a browser) | Review note (2.4.11) | `html.pad-for-header { scroll-padding-top: 14rem }` (`styles.css:5`) reserves more space than the header needs: its minimum height is 8rem and it measures roughly 9rem with one row of links. At 640px and narrower the header stops being sticky (`styles.css:66-68`). Both values are in rem, so they scale together when zoomed. A quick keyboard test should still confirm this. There is a separate focus problem on every page; see finding B. |
| 7 | h2 'Visit us' followed by h4 'Opening hours' | **No** | Advisory (best practice) | SC 1.3.1 requires headings to be marked up, not numbered in sequence. "Opening hours" is marked up as a heading, so it passes. Changing it to `<h3>` (`index.html:78`) is still better. |
| 8 | 'Type your PIN again' on signup | **No** | None (3.3.7) | SC 3.3.7 allows re-entry when "the information is required to ensure the security of the content," and confirming a new PIN is that case. **But the same step asks for the email address again, which does fail**; see finding C. |
| 9 | Schedule table wider than a 320px screen | **No** | None (pass, 1.4.10) | SC 1.4.10 exempts content that needs a two-dimensional layout, and data tables are the standard example. The table is also in a `.table-scroll` wrapper with `overflow-x: auto`, `role="region"`, a label and `tabindex="0"` (`events.html:57`), so keyboard users can scroll it. |

## Failures found next to the queried items

| # | Severity | Check ID | Location | Finding | Fix |
|---|---|---|---|---|---|
| A | Nonconformity | WCAG-3.3.8 | `login.html:37` | The PIN field has `onpaste="return false;" ondrop="return false;"`, so password managers and copy-paste can't fill it. Users then have to remember and type the PIN themselves, which counts as a cognitive function test. Because login is one process, this fails both steps. | Remove `onpaste` and `ondrop`. |
| B | Nonconformity | WCAG-2.4.7 | `styles.css:59` | `.site-nav a:focus { outline: none; }` removes the focus indicator from the main navigation on every page. | Delete the rule, or replace it with `.site-nav a:focus-visible { outline: 3px solid #fff; outline-offset: -3px; }`. |
| C | Nonconformity | WCAG-3.3.7 | `signup.html:58-59`, `app.js:109` | Step 2 asks for "Email address for card notices" even though the email was entered in step 1. The field is not filled in automatically, and there is no way to choose the earlier address. | Pre-fill `#card-email` from `#email` in the step-2 handler, or add a "Use the same email" checkbox. |

## Other issues seen while reading (not fully audited)

I didn't test these fully, so confirm them in a full audit:

- **Colour contrast (1.4.3):** `.event-meta` is `#999999` on white, about 2.8:1 (`styles.css:190`).
- **Language (3.1.1):** `events.html` has no `lang` attribute.
- **Timing:**
  - `events.html:6` reloads the page every 120 seconds with `<meta http-equiv="refresh">` (2.2.1).
  - The home carousel advances automatically with no pause control (2.2.2, `app.js:14`).
- **Events reservation dialog:**
  - The Tab key always sends focus back to the name field, so Confirm can't be reached by keyboard (2.1.1).
  - Escape is blocked, and the close "×" is a `<span>` that keyboard users can't reach (`events.html:88`, `app.js:83-91`).
- **Reflow (1.4.10):** `.featured-row` has four fixed columns of 240px (`styles.css:107`), so the home page won't fit a narrow screen.
- **Hidden links (4.1.2):** `aria-hidden="true"` hides the footer social links from screen readers, but they can still be focused (`index.html:85`).
- **Labels (3.3.2 / 4.1.2):** "Full name" on signup has only placeholder text and no label (`signup.html:34`).
- **Focus order (2.4.3):** the login form uses positive `tabindex` values (`login.html:37, 40`).
- **Link purpose (2.4.4):** "Click here" is the only text for the calendar link (`events.html:32`).

## Summary

- **Queried items:** none of the nine is an AA failure. Items 5 and 7 are advisories, and item 6 needs a browser check.
- **Confirmed failures:** 3 (A–C above).
- **Other suspected failures:** about 9 from the reading pass.
- **Not done:** a keyboard walk-through, a screen-reader check, a zoom/reflow check, and the audit scripts (no shell was available). The catalog page and the React components weren't reviewed beyond this, so this is not a full conformance result. With findings A–C open, the site does not conform to WCAG 2.2 AA as it stands.
