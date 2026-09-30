I reviewed all nine queries against the source files. I couldn't run a shell, the scan tools, a browser or a screen reader, so rendered measurements are worked out from the CSS and should be confirmed in a browser.

# WCAG 2.2 Level AA review: Larkspur Library, nine queried items

**Scope:** index, catalog, events, login and signup HTML pages, plus `styles.css` and `app.js`. The target is Level AA under WCAG 2.2 (W3C Recommendation, 12 Dec 2024).

**Summary:** None of the nine queried items is itself an AA failure. Seven of them do not fail any success criterion (SC). Item 2 is a checker false positive; the table's markup is correct. Item 7 is an Advisory only. Item 6 probably passes but needs a quick check in a browser. While checking items 4, 6, 8 and 9, I found real failures next to what was flagged. They are listed after the table.

## The nine queries

| # | Query | AA failure? | Severity | Why |
|---|---|---|---|---|
| 1 | Leaf divider, `index.html:52`, `alt=""` with `role="presentation"` | **No** | None (false positive) | The image is decorative, and `alt=""` is the correct way to hide it (1.1.1). The `role` is redundant but harmless. The real text-alternative problem is the other divider at `index.html:30`, which reads "Purple decorative flourish divider" aloud. That adds noise but isn't an AA failure; it's an Advisory, and the fix is `alt=""`. |
| 2 | Schedule table uses `scope` on `th` (`events.html:58-82`) | **No** | None (checker false positive) | This is a data table with a caption, column headers and row headers. Using `scope="col"` and `scope="row"` is the correct technique (H63) and meets 1.3.1. The layout-table rule doesn't apply. |
| 3 | "access guide" link about 16px tall (`events.html:29`) | **No** | None | 2.5.8 exempts links inside a sentence (the Inline exception). The line height is 20px (`styles.css:200`), and the link sits in running text. |
| 4 | Image CAPTCHA "select every picture that shows a book" (`login.html:45-51`) | **No, not under 3.3.8** | None for 3.3.8 | 3.3.8 has an **Object Recognition** exception at AA, and picking out books is object recognition. It would fail 3.3.9, but that's AAA. The login process still fails for other reasons; see A and B below. |
| 5 | Logo text `#c9b6ef` on white, 1.84:1 (`styles.css:40`) | **No** | None | I confirmed the ratio: luminance 0.521 gives 1.84:1. 1.4.3 exempts **logotypes**, meaning text that is part of a logo or brand name. The circle next to it is `aria-hidden` and decorative, so 1.4.11 doesn't apply. It's fine to raise this as a readability point for the brand, but it isn't a finding. |
| 6 | Sticky header on index: can it hide the focused element? | **Probably not** | Review note (confirm in a browser) | By my estimate, the header is about 167px tall at desktop widths and about 190px if the help line wraps. `html.pad-for-header { scroll-padding-top: 14rem }` (224px, `styles.css:5`) is larger than both, so focused elements get scrolled clear of the header. Both values are in rem, so they scale together with text zoom. Below 640px the header stops being sticky (`styles.css:66-68`). 2.4.11 fails only if the element is *entirely* hidden. To confirm, tab through `index.html` at 1280px and at 200% zoom. The header does have a real, separate problem; see C below. |
| 7 | `h2` "Visit us" followed directly by `h4` (`index.html:77-78`) | **No** | Advisory (best practice) | 1.3.1 and 2.4.6 don't require heading levels to go in order. The heading is still exposed as a heading and describes its content. Changing it to `<h3>` would still be better. |
| 8 | "Type your PIN again" on signup (`signup.html:66`) | **No** | None | 3.3.7 exempts re-entry that is essential or needed for security. Confirming a new PIN is exactly that case. The same form step does fail 3.3.7 elsewhere; see D below. |
| 9 | Schedule table wider than a 320px viewport | **No** | None | 1.4.10 exempts content that needs a two-dimensional layout, and data tables are the standard example. The table is also inside a scroll region that has a name and can be reached by keyboard (`events.html:57`, `tabindex="0"`, `aria-labelledby`), so only the table scrolls, not the page. The home page does have a real reflow failure; see E below. |

## Real failures found while checking the queries

| # | Severity | SC | Location | Finding | Fix |
|---|---|---|---|---|---|
| A | Nonconformity | 3.3.8 (AA); fails the whole login process | `login.html:37` | The PIN field blocks pasting with `onpaste="return false;"`. A user who can't paste from a password manager has to recall and retype the PIN, which is a cognitive function test with no alternative. | Remove `onpaste` and `ondrop`. |
| B | Nonconformity | 1.1.1 (A), CAPTCHA clause | `login.html:52-53`, `app.js:114-120` | The "Use an audio check instead" button only reveals some instruction text. No audio exists anywhere, so there is no working CAPTCHA in another sense. | Provide a working audio CAPTCHA, or better, a non-CAPTCHA check. Offering a way that doesn't rely on recognition at all would also meet 3.3.9. |
| C | Nonconformity | 2.4.7 (AA), every page | `styles.css:59` | `.site-nav a:focus { outline: none; }` removes the focus indicator from the main navigation, and nothing replaces it. | Remove the rule, or add something like `.site-nav a:focus-visible { outline: 3px solid #fff; outline-offset: -3px; }`. |
| D | Nonconformity | 3.3.7 (A) | `signup.html:58-59`, `app.js:109` | Step 2 asks for "Email address for card notices" after the email was already given in step 1. It isn't filled in automatically and the user can't choose the earlier answer. | Pre-fill it from `#email`, or offer a "same as above" option. |
| E | Nonconformity | 1.4.10 (AA) | `styles.css:107` | `.featured-row` uses a fixed `repeat(4, 240px)` grid, which is over 1000px wide. At 320px the whole page scrolls sideways. | Use `repeat(auto-fill, minmax(min(240px, 100%), 1fr))`. |
| F | Advisory | Best practice (headings), 1.1.1 noise | `index.html:78`, `index.html:30` | These are the item 7 heading and the item 1 flourish alt text. | Use `<h3>` and set `alt=""`. |

I also noticed other likely failures outside the nine queries but didn't look into them closely:

- On `events.html`:
  - The page has no `lang` attribute (3.1.1).
  - A 120-second `meta refresh` reloads the page (2.2.1).
  - The modal is a keyboard trap: Tab is forced back into the dialog and Escape is swallowed (2.1.2).
  - The modal's close control is a `<span>` that can't be reached by keyboard (2.1.1).
  - The link text is "Click here" (2.4.4).
  - `.event-meta` text is `#999` on white, about 2.85:1 (1.4.3).
- On the home page, the carousel moves automatically with no way to pause it (2.2.2).
- On the home page, the footer social links are focusable but inside `aria-hidden` (4.1.2).
- On signup, the full-name field has only placeholder text and no label (3.3.2 / 4.1.2).

These need a full audit pass. Several of them fail regardless of the nine queries, so the site does **not conform** to WCAG 2.2 AA as it stands.

## Assumptions
- Heights and widths are worked out from `styles.css` with default browser styles (16px root, Georgia), not measured in a rendered page.
- I didn't review the React components in `src/components/` or `catalog.html`, because none of the nine queries involve them.
