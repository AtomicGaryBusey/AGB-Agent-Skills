## Answers to the six questions

**Only one of the six is not a clear pass, and it's a technicality: none of the six is a WCAG 2.2 AA failure.** Five are false positives because an exception in the criterion covers them, or the page already meets the requirement. The one part-exception is a Vue component that doesn't ship yet (see 3).

| # | Query | AA failure? | Why |
|---|---|---|---|
| 1 | Fare table scrolls sideways at 320px (SC 1.4.10 Reflow) | **No** | Reflow exempts "parts of the content which require two-dimensional layout", and data tables are the standard example. The scrolling is contained in `.table-scroll` (`css/site.css:118`), so the rest of the page doesn't scroll sideways. The wrapper has `role="region"`, a name and `tabindex="0"` (`fares.html:43`), so keyboard users can scroll it. |
| 2 | Disabled "Submit claim", 2.06:1 (SC 1.4.3 Contrast) | **No** | The button has the `disabled` attribute (`claim-3.html:46`), and 1.4.3 exempts text in an inactive control. `js/claim.js:5-7` enables it when the confirmation box is ticked. It then uses the normal `.btn` style: white on #0b5cad, about 6.6:1. At most an advisory: pale disabled text doesn't tell users why the button is off. |
| 3 | Saved trips reordered by dragging (SC 2.5.7 Dragging Movements) | **No, for planner.html** | Every item has "Move up" and "Move down" buttons (`planner.html:82-97`). They work (`js/planner.js:48-59`), keep focus on the button and announce the new position through `role="status"`. That is a single-pointer alternative to dragging. **However**, `components/SavedTrips.vue` offers the same feature by dragging only, with no buttons. If that component ships, it fails 2.5.7 (**Nonconformity** once rendered; a Deviation while it's unbuilt source). Fix: add the same Move up/down buttons and status message. |
| 4 | Map zoom buttons are 20×20px (SC 2.5.8 Target Size) | **No** | The spacing exception applies. The buttons are stacked with an 8px gap (`site.css:159-161`), so their centres are 28px apart. A 24px circle centred on each button doesn't overlap the other's circle, and the 12px toolbar padding keeps other targets away. On narrow screens they sit in a row with a 12px gap, so the centres are 32px apart. Advisory: 44px buttons would be easier to use. |
| 5 | Survey dialog has no focus-trap or Escape code (SC 2.1.2 No Keyboard Trap) | **No** | `js/site.js:7` uses the browser's own `dialog.showModal()`. The browser handles Escape, keeps focus inside the dialog, and lets Tab reach the browser toolbar. The dialog also has a keyboard-operable Close button (`<form method="dialog">`), and focus goes back to the opener when it closes (`site.js:9-11`). A keyboard trap means focus can't get out, and here it can. Custom trap code would be needed for a `<div>` modal, not for a native `<dialog>`. |
| 6 | Wordmark #9cc3e6 on white, 1.85:1 (SC 1.4.3) | **No** | 1.4.3 exempts logotypes: "Text that is part of a logo or brand name has no contrast requirement." I confirmed the 1.85:1 ratio. Advisory only: the wordmark is the only visible text in the home link (`.logo`), so a darker colour such as `--brand` #0b5cad would help people with low vision. |

## Real failures I found in the files I reviewed

While checking the six questions I found several real failures the checker didn't raise. This isn't a full audit; I only read the files these questions touched.

| Severity | SC | Location | Problem | Fix |
|---|---|---|---|---|
| Nonconformity | 1.4.10 Reflow | `site.css:136`, `alerts.html:53,58` | `.alert-detail { min-width: 880px }` forces plain paragraphs of text wider than a 320px screen. This is the real Reflow failure; text paragraphs have no exception. | Remove the `min-width` rule. |
| Nonconformity | 2.4.7 Focus Visible | `site.css:52` | `.site-nav a:focus { outline: none }` is more specific than the global `:focus-visible` rule (`site.css:31`), so the main-menu links on every page show no focus indicator. | Delete that rule, or add `.site-nav a:focus-visible { outline: 3px solid var(--brand); }`. |
| Nonconformity | 2.1.1 Keyboard | `map.html:43-49`, `js/map.js:15-20` | The map stops are `<g>` elements that only respond to clicks. They can't be focused or opened from the keyboard, so keyboard users can't see stop details. | Add a list of stop buttons that fills the same panel, or make each stop focusable with `tabindex="0"` and `role="button"`, a name, and Enter/Space handlers. |
| Nonconformity | 2.2.2 Pause, Stop, Hide | `index.html:31-49`, `site.css:82-93` | The promo carousel scrolls automatically on an infinite 18-second loop with no pause control. This applies even to content users don't rely on. | Add a pause button, and stop the animation when the user sets `prefers-reduced-motion`. |
| Nonconformity | 1.4.1 Use of Color | `fares.html:42,63-88`, `site.css:122` | Peak fares are marked "shown in red" and nothing else. The red is about 2:1 against the body text, so people who can't see the red can't tell which price is the peak one. | Label them in the text, e.g. `<span class="peak">Peak: $3.25</span>`. |
| Nonconformity | 1.3.1 Info and Relationships | `fares.html:46-92` | The table's headers are `<td class="th">` cells, not `<th>`. Screen readers don't read the column or row headings with each price. | Use `<thead>` with `<th scope="col">` (and `colgroup` for the grouped headings) and `<th scope="row">` for rider types. |
| Nonconformity | 3.1.1 Language of Page | `fares.html:2` | The `<html>` tag has no `lang` attribute; all ten other pages have `lang="en"`. | Add `lang="en"`. |

## Limits of this review

- **Nothing was run.** There was no shell, so I didn't run the audit scripts, render the pages or use a screen reader. Everything above comes from reading the HTML, CSS, JS and Vue files. The contrast ratios and target spacing are calculated from the CSS values.
- **The site does not conform to WCAG 2.2 AA yet.** That's because of the seven failures in the second table, not the six queries.
- **Still to check in a browser:**
  - At 320px, confirm the zoom buttons' layout and that nothing else scrolls sideways.
  - Check the native dialog's Escape and focus behaviour in each browser you support.
  - Do a screen-reader check of the saved-trips status announcements and the fare table once it uses `<th>`.
