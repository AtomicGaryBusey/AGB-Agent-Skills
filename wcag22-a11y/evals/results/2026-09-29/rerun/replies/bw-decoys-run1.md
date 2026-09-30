# WCAG 2.2 Level AA review: Brightwater Transit static front end

**Short answer:** none of the six flagged items fails WCAG 2.2 AA. Each one either meets the criterion or falls under an exception written into the criterion itself. While checking them, though, I found **eight real failures** in the same files. Several of them are more serious than anything the checker flagged.

Scope: I read index, planner, fares, map and claim-3 (.html), `css/site.css`, and `js/site.js`, `planner.js`, `map.js` and `claim.js`. Level AA (55 criteria; 4.1.1 is obsolete). No shell was available, so nothing was rendered, no automated tools ran and no screen reader was used. Everything below comes from reading the code. I did not review alerts, login, feedback, help, claim-1, claim-2, `components/*.vue` or the other scripts, and this is **not a full audit or a conformance claim**.

## The six queries

| # | Query | Fails AA? | Why |
|---|---|---|---|
| 1 | Fare table scrolls sideways at 320px (SC 1.4.10 Reflow) | **No.** Drop the flag. | 1.4.10 exempts "parts of the content which require two-dimensional layout", and data tables are the standard example. Only the table scrolls, inside its own container: `.table-scroll { overflow-x: auto }` at `css/site.css:118`. That container is a labelled region that keyboard users can reach (`fares.html:43`: `role="region" aria-labelledby="fare-caption" tabindex="0"`), so they can scroll it too. The rest of the page still reflows. |
| 2 | "Submit claim" at 2.06:1 (SC 1.4.3 Contrast) | **No.** At most an advisory. | This is the disabled style (`css/site.css:68`, `.btn[disabled]`). The button starts `disabled` (`claim-3.html:46`) until the confirmation box is ticked (`js/claim.js:5-7`). Text in an inactive component is exempt from 1.4.3. Once enabled, it's white on #0b5cad, which passes easily. Advisory: nothing tells users why the button is unavailable. A short hint next to the checkbox would help. |
| 3 | Saved trips reordered by dragging (SC 2.5.7 Dragging Movements) | **No.** Pass. | Each item has "Move up" and "Move down" buttons, which work with a single click and need no dragging (`planner.html:82-97`, `js/planner.js:48-59`). The on-screen instructions mention them (`planner.html:77`). Moves are announced in a `role="status"` region (`planner.html:101`), and the buttons are 32px or more. |
| 4 | Map zoom buttons are 20×20px (SC 2.5.8 Target Size) | **No.** Passes under the spacing exception. | Smaller targets pass if 24px circles centred on each target don't overlap another target or its circle. The buttons are 20px with an 8px gap (`css/site.css:159-161`), so their centres are 28px apart. That's more than the 24px needed, and each circle stays 18px from the other button's edge. On narrow screens the gap is 12px, so the centres are 32px apart (`:172`). Advisory: 24px or larger would be easier to hit. |
| 5 | Survey dialog has no Escape or focus code (SC 2.1.2 No Keyboard Trap) | **No.** Pass. | It's a native `<dialog>` opened with `showModal()` (`js/site.js:7`). The browser closes it on Escape, and the Close button works too (`index.html:68-70`: `method="dialog"`). Focus goes back to the opener (`site.js:9-11`). Keeping focus inside a modal is how modals are meant to behave, and users can always leave, so it isn't a trap. The checker was looking for custom JS that the native element makes unnecessary. |
| 6 | Wordmark #9cc3e6 on white at 1.85:1 (SC 1.4.3) | **No.** Advisory only. | 1.4.3 says: "Text that is part of a logo or brand name has no minimum contrast requirement." `.logo .wordmark` (`css/site.css:48`) is the brand name. Advisory: it's also the home link on every page, and at 1.85:1 many users won't see it. Consider a darker brand shade. |

## Real failures found while checking

All eight are **nonconformities**: clear failures confirmed in the source, ranked in criterion order. The heading-markup failure on fares.html affects screen-reader users most. The missing focus outline on the nav links affects every page.

| # | Criterion (Level) | Location | Finding | Fix |
|---|---|---|---|---|
| 1 | 1.1.1 Non-text Content (A) | `planner.html:61,70` | The step-free icons (`<svg class="ico">`) are the only thing that says a trip is step-free. They have no text alternative, so screen readers skip them. | Add `role="img" aria-label="Step-free"` or visible text such as "Step-free". |
| 2 | 1.3.1 Info and Relationships (A) | `fares.html:47-92` | Header cells are `<td class="th">`, so a screen reader can't tell which rider type and zone go with each price. | Use `<thead>`, `<th scope="col">` (with `colspan` for the group headings) and `<th scope="row">` for rider types. |
| 3 | 1.4.1 Use of Color (A) | `fares.html:42,63-88`; `css/site.css:122` | "Peak fares are shown in red." Colour is the only thing marking the second price as the peak fare. | Add text, e.g. `<span class="peak">Peak $3.25</span>`, or use separate peak and off-peak columns. |
| 4 | 2.1.1 Keyboard (A), also 4.1.2 (A) | `map.html:43-49`; `js/map.js:15-20` | Map stops are `<g>` elements with click handlers only. They can't be focused, have no role, and ignore the keyboard, so keyboard users can't get stop details, including step-free information. | Make each stop a button, or give it `tabindex="0"`, `role="button"`, an accessible name and Enter/Space handlers. Or add a list of stops as buttons alongside the map. |
| 5 | 2.2.2 Pause, Stop, Hide (A) | `index.html:31-49`; `css/site.css:82-93` | The promo carousel moves by itself for ever (`animation: … infinite`) and can't be paused. Under WCAG's non-interference rule this criterion applies even to content users don't need. | Add a pause button that sets `animation-play-state: paused`. Also stop the animation under `@media (prefers-reduced-motion: reduce)`. |
| 6 | 2.4.7 Focus Visible (AA) | `css/site.css:52` | `.site-nav a:focus { outline: none; }` overrides the general `:focus-visible` outline on line 31 because it's the more specific rule. Keyboard focus on the main nav links is invisible **on every page**. | Delete line 52, or give nav links their own `:focus-visible` style. |
| 7 | 3.1.1 Language of Page (A) | `fares.html:2` | `<html>` has no `lang`. The other pages I read have `lang="en"`. | `<html lang="en">`. |
| 8 | 4.1.2 Name, Role, Value (A) | `planner.html:36` | The "locate me" button has no accessible name. Its icon is a CSS background image (`css/site.css:103-105`). | `aria-label="Use my current location"`. |

## Notes and limits
- **Verdict:** because of the nonconformities above, the pages I reviewed **do not conform** to WCAG 2.2 AA. The pages I didn't read also need checking before anyone makes a conformance statement.
- **Things to confirm in a browser, because I couldn't render anything:**
  - the reflow of each page at 320px
  - the nav focus outline (item 6)
  - Escape on the dialog in the browsers you support
  - a screen-reader pass on the fare table and saved-trips announcements.
- **Seen in passing, not assessed:**
  - `css/site.css` suggests other issues on pages I didn't read: 16px `.mini-btn` controls on alerts (`:132-135`), `min-width: 880px` alert panels (`:136`), a low-contrast #a0a0a0 floating label on feedback (`:180`) and a fixed 12rem-tall footer (`:189`).
  - The icon font `fonts/bwicons.woff2` isn't in the folder. The icons are `aria-hidden`, so that isn't a WCAG issue, but they won't show up.
  - All of these belong in the full audit.
