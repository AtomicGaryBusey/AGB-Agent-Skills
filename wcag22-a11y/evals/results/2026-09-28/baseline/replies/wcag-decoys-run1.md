I read all four relevant pages plus `styles.css` and `app.js`, and used the wcag22-a11y skill's references. None of the nine items is a WCAG 2.2 AA failure as written. Four of them sit right next to real failures, which are listed after the nine.

# WCAG 2.2 Level AA review — Larkspur Library: the nine queried items

**Scope:** the nine items, reviewed by reading the source only. I didn't run the checker, render the pages or test with a screen reader. Level AA (55 success criteria; 4.1.1 is obsolete). This is not a full audit and doesn't support a conformance claim.
**Summary for the nine:** 0 failures. Two need a quick browser check (items 4 and 6); one has an optional improvement (item 5); one is a best-practice fix (item 7). Four related failures found nearby are listed after the table.

## Verdicts on the nine items

| # | Item | AA failure? | Severity | Why |
|---|---|---|---|---|
| 1 | Leaf divider `index.html:52`, `alt="" role="presentation"` | **No** | None (false positive) | This is the correct way to mark a decorative image under 1.1.1. It's supposed to have no text alternative. The opposite problem is at `index.html:30`: the decorative flourish has `alt="Purple decorative flourish divider"`, which is just noise for screen reader users. Best-practice fix: `alt=""`. |
| 2 | Schedule table uses `scope` on `th` (`events.html:58-82`) | **No** | None (false positive) | It's a real data table with a `<caption>`, column headers (`scope="col"`) and row headers (`scope="row"`). That is correct 1.3.1 markup, not a layout table. |
| 3 | "access guide" link is about 16px tall (`events.html:29`) | **No** | None | 2.5.8 excludes links inside a sentence. This one sits in running text whose `line-height` is 20px, so the exception applies. Separate content bug: `#access` jumps to "Room schedule this week" (`events.html:56`), and there's no access guide on the page. |
| 4 | Image CAPTCHA "select every picture that shows a book" (`login.html:43-55`) | **No, not under 3.3.8** | Review note | 3.3.8 (AA) exempts tests where the task is recognising objects, and this is one. It would fail 3.3.9, but that's AAA. See related failures A and B for the real problems in this login process. |
| 5 | Logo text `#c9b6ef` on white, about 1.84:1 (`styles.css:40`) | **No** | Advisory | 1.4.3 exempts text that is part of a logo or brand name. The ratio is real, so darkening it would help, but it isn't required. |
| 6 | Sticky header on `index.html`: can it hide focus? | **Not as coded** | Review note (check in a browser) | The header is only sticky on index (`.sticky-page`), and it goes static below 640px (`styles.css:66-68`). `html.pad-for-header` sets `scroll-padding-top: 14rem`, and I estimate the header at about 10.2rem (≈167px) tall. So a focused element scrolled into view should land below it. Check with Tab and Shift+Tab in Chrome, Firefox and Safari. The bigger focus problem on this page is related failure C. |
| 7 | h2 "Visit us" then h4 "Opening hours" (`index.html:77-78`) | **No** | Advisory (best practice) | Both are marked up as headings, so 1.3.1 is met. Skipping a level isn't a WCAG failure. Changing it to `<h3>` is still better. |
| 8 | "Type your PIN again" on signup (`signup.html:66`) | **No** | None | 3.3.7 exempts re-entry that's needed for security, and confirming a new password or PIN is the standard example. The real repeat-entry problem on this form is related failure D. |
| 9 | Schedule table wider than a 320px screen | **No** | None | 1.4.10 exempts content that needs a two-dimensional layout, such as data tables. It's also inside `.table-scroll` (`overflow-x:auto`) with `role="region"`, a label and `tabindex="0"`, so keyboard users can scroll it. The whole page doesn't scroll sideways because of it. |

## Related failures found next to these items

| # | Severity | Check ID | Where | Finding | Fix |
|---|---|---|---|---|---|
| A | Nonconformity | WCAG-3.3.8 (AA) | `login.html:37` | The PIN field has `onpaste="return false;" ondrop="return false;"`, so users can't paste their PIN. 3.3.8 needs a way to avoid remembering or retyping it, and blocking paste is a listed failure pattern. Password-manager autofill (`autocomplete="current-password"`) still works, but paste has to work too. Because one failing step fails the whole process, the entire sign-in fails. | Remove `onpaste` and `ondrop`. |
| B | Nonconformity | WCAG-1.1.1 (A) | `login.html:52-53`, `app.js:114-120` | The CAPTCHA exception needs an alternative in a different sense (for example sound instead of sight). "Use an audio check instead" only un-hides a paragraph of instructions. There's no audio element, file or player anywhere, so blind users have no way to pass step 2. | Build a working audio CAPTCHA, or better, use a non-interactive check such as a server-side risk score. |
| C | Nonconformity | WCAG-2.4.7 (AA) | `styles.css:59`, all 5 pages | `.site-nav a:focus { outline: none; }` removes the focus indicator on the main navigation links and adds nothing in its place. | Delete the rule, or use `.site-nav a:focus-visible { outline: 3px solid #fff; outline-offset: -3px; }`. |
| D | Nonconformity | WCAG-3.3.7 (A) | `signup.html:58-59` | Step 2 asks for "Email address for card notices" after step 1 already collected the email (`signup.html:37-38`). It isn't filled in or offered as a choice. | Pre-fill `#card-email` from `#email` when Next is clicked (`app.js:107-109`), or add a "Same as above" checkbox. |

## Other failures I saw while reading (not checked in depth)
- `events.html:2`: the page has no `lang` attribute (3.1.1).
- `events.html:6`: `<meta http-equiv="refresh" content="120">` reloads the page every two minutes and can't be turned off (2.2.1).
- The Reserve-a-seat dialog has three problems:
  - `app.js:83-92` forces every Tab press back to the Name field, so the Email field and Confirm button can't be reached by keyboard (2.1.1).
  - Escape does nothing, so keyboard users can't leave the dialog (2.1.2).
  - The × close control (`events.html:88`) is a `<span>` with a click handler, so it can't be reached or activated by keyboard.
- `login.html:37,40`: `tabindex="1"` and `"2"` make Tab go to Continue, then PIN, then card number (2.4.3).
- `index.html:34` / `app.js:14-17`: the carousel moves every 4 seconds and can't be paused (2.2.2).
- `styles.css:107`: the Staff-picks grid is fixed at `repeat(4, 240px)` (1020px wide), so the home page scrolls sideways at 320px (1.4.10).
- `index.html:85`: the footer social links are inside `aria-hidden="true"` but can still get keyboard focus (4.1.2).
- `signup.html:34` and the signup CSS:
  - The Full name field has only a placeholder and no label (3.3.2).
  - The placeholder `#aaa` on white is about 2.3:1 (1.4.3).
  - The input borders `#d6d6d6` are about 1.5:1 (1.4.11).
  - Errors are shown only by a red border, with no text (3.3.1).
- `events.html:32`: a "Click here" link alone in its paragraph (2.4.4).
- `styles.css:190`: `.event-meta` text `#999` on white is about 2.8:1 (1.4.3).

## Not done / assumptions
- No automated tools, rendered pages, screen reader or zoom tests were run; everything is from reading the source. Item 6 still needs the browser check described above.
- `catalog.html` and `src/components/*.jsx` weren't reviewed because none of the nine items is there. The pager (`styles.css:159-169`, 16×16px links) and the drag-only reading list are worth checking against 2.5.8 and 2.5.7 before release.
- The site isn't ready to claim WCAG 2.2 AA until failures A–D and the others above are fixed and the remaining criteria have been tested.
