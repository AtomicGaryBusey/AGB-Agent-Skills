# WCAG 2.2 Level AA audit: Brightwater Transit static front end (Principles 3 and 4)

**Scope:** 11 pages (index, planner, fares, alerts, map, claim-1, claim-2, claim-3, login, feedback, help), `css/site.css`, `js/*.js`, `img/*.svg` and 4 Vue source components (not built).
**Processes:** Lost-item claim (claim-1 → claim-2 → claim-3), sign-in with a one-time code, feedback form, email-alert signup.
**Level:** AA, limited to Principles 3 and 4. That is 15 success criteria; 4.1.1 is obsolete and not graded.
**Tools and assistive tech:** None. This was a static review only.

**Result:** The site does not conform. 10 of the 15 criteria fail: 3.1.1, 3.2.2, 3.2.3, 3.2.6, 3.3.1, 3.3.3, 3.3.7, 3.3.8, 4.1.2 and 4.1.3. A failure in any claim step fails the whole claim process, so claim-1, claim-2 and claim-3 all fail.

**Counts:** 11 nonconformities, 2 deviations, 2 advisories, 5 review notes. Criteria: 10 fail, 5 pass (static review only), 0 N/A.

**Evidence:** I read every file in scope by hand. The skill's scanners (`wcag_scan.py`, `wcag_page.mjs` with axe-core) were not run because there is no shell. Nothing was rendered, tested with a keyboard or tested with a screen reader.

## Findings

| # | Severity | Criterion | Location | Finding | Fix |
|---|---|---|---|---|---|
| 1 | Nonconformity | 3.1.1 Language of Page (A) | `fares.html:2` | The fares page has `<html>` with no `lang`. The other 10 pages all have `lang="en"`. | Use `<html lang="en">`. |
| 2 | Nonconformity | 3.2.2 On Input (A) | `fares.html:34`, `js/fares.js:7-9` | Changing the "Show fares for" select loads a new page straight away (`change` sets `window.location.href`). There's no submit button and no warning. Arrowing through the options with a keyboard reloads the page on each option. | Add `<button type="submit">Show fares</button>` to the form at `fares.html:31` and remove the `change` listener. The form already uses GET with `name="zone"`. |
| 3 | Nonconformity | 3.2.6 Consistent Help (A) and 3.2.3 Consistent Navigation (AA) | `claim-2.html:11-27`, `claim-2.html:63` | On 10 pages the "Help & contact" link is in the header, straight after the main nav (e.g. `index.html:27`). On claim-2 it is missing from the header and appears only at the end of the footer links. That changes its position relative to the other page content in the middle of the claim process. | Restore `<a class="help-link" href="help.html">…Help &amp; contact</a>` after `</nav>` in claim-2's header. The footer copy can stay or go, as long as it's consistent. |
| 4 | Nonconformity | 3.3.1 Error Identification (A) and 3.3.3 Error Suggestion (AA) | `js/feedback.js:8-12`, `js/feedback.js:14-18`, `feedback.html:40`, `feedback.html:53` | When the feedback form fails validation, the script only adds a red border (`.is-invalid`) and `aria-invalid`. The error paragraphs `#fb-email-error` and `#fb-message-error` stay `hidden` and empty, so there's no text saying what went wrong or how to fix it (for example, a malformed email). | In `check()`, set the error text (e.g. "Enter an email address in the format name@example.com", "Enter your message"), set `hidden = false` when invalid, and clear it when valid. Move focus to the first invalid field. |
| 5 | Nonconformity | 3.3.7 Redundant Entry (A) | `claim-3.html:36`, `claim-3.html:40` (repeats `claim-1.html:40`, `claim-1.html:44`) | Step 3 asks again for the email address and phone number already entered in step 1. They aren't pre-filled and can't be picked from a list. Claim-1's email field also has `autocomplete="off"`. Browser autofill isn't a mechanism the site provides. | Carry the step-1 values forward (hidden fields or a server session) and pre-fill `c3-email` and `c3-phone`, or offer a "Use the contact details from step 1" option. |
| 6 | Nonconformity | 3.3.8 Accessible Authentication (Minimum) (AA) | `js/login.js:8-12`, `js/login.js:22`, `login.html:38`, `login.html:50-55` | `blockPaste` stops pasting into the password field and into all 6 code fields. Users have to remember or retype the password and copy the SMS code by hand, which is a cognitive function test. None of the exceptions (alternative method, helper mechanism, object recognition, personal content) applies. | Remove the `paste` listeners. On the code fields, use `autocomplete="one-time-code"` and accept a pasted 6-digit code (or use a single `inputmode="numeric"` field). |
| 7 | Nonconformity | 4.1.2 Name, Role, Value (A) | `planner.html:36` (`css/site.css:103-106`) | The "locate me" button (`#locate-me`) is empty. Its only content is a CSS background image (`img/locate.svg`), so it has no accessible name and is announced as just "button". | Add `aria-label="Use my current location"`, or visually hidden text. |
| 8 | Nonconformity | 4.1.2 Name, Role, Value (A) | `alerts.html:41`, `js/alerts.js:26-28` | The custom notification switch has `role="switch" aria-checked="false"`. `toggle()` only toggles the `is-on` class, so assistive tech always reports it as "off". | In `toggle()`, also set `aria-checked` to match the new state. Or use the native checkbox pattern from `components/ToggleSwitch.vue`. |
| 9 | Nonconformity | 4.1.2 Name, Role, Value (A) | `alerts.html:68`, `js/alerts.js:64` | The email-alert modal's close control is a `<span>&times;</span>` with a click handler. It has no role, no accessible name and can't receive focus. The focus trap (`js/alerts.js:74-86`) also leaves it out, and Escape is blocked, which adds keyboard problems outside this audit's scope (2.1.1, 2.1.2). | Use `<button type="button" class="modal__close" aria-label="Close">&times;</button>`, include it in the focus trap, and let Escape call `closeModal()`. |
| 10 | Nonconformity | 4.1.2 Name, Role, Value (A) | `map.html:43-49`, `js/map.js:15-19` | The map stops (`<g class="stop">`) respond to clicks but have no role and no `tabindex`, so they aren't exposed as controls. This is also a 2.1.1 problem, outside this audit's scope. | Wrap each stop in `<a href="#" role="button">` or give the `<g>` `role="button" tabindex="0" aria-label="Market Square"`. Handle Enter and Space. Alternatively, add a list of stop buttons next to the map. |
| 11 | Nonconformity | 4.1.3 Status Messages (AA) | `alerts.html:51`, `js/alerts.js:38-46` | "Checking..." and "Updated at HH:MM. No new alerts." are written into `<span id="refresh-result">`, which isn't a live region. Screen reader users aren't told the result, and focus stays on the Refresh button. | Add `role="status"` to `#refresh-result`. |
| 12 | Deviation | 3.2.2 On Input (A) | `js/login.js:23-26`, `login.html:47` | Typing a digit moves focus to the next code box, which is a change of context triggered by input. The instructions ("Type the code below") don't mention it. Needs confirmation with a screen reader. | Use a single 6-character code field, or say in `#twofa-hint` that focus moves on automatically. |
| 13 | Deviation | 4.1.2 Name, Role, Value (A) | `components/ZoneInfoTooltip.vue:7`, `:15`, `:32-34` | The tooltip id is built only from the zone (`zone-tip-${zone}`). If the same zone appears twice on a page, the ids collide and `aria-describedby` points to the wrong tooltip. | Build a unique id per instance, e.g. with Vue 3.5 `useId()` or a module counter. |
| 14 | Advisory | Best practice related to 3.3.2 | `claim-3.html:46`, `js/claim.js:5-7` | "Submit claim" stays disabled until the confirmation box is ticked, and nothing explains why. Disabled buttons also can't be focused, so keyboard users may not find them. | Keep the button enabled and validate on submit with a text error, or add a hint linked with `aria-describedby`. |
| 15 | Advisory | Best practice related to 3.3.1 | `js/alerts.js:69-71`, `alerts.html:72` | The "Enter an email address." message is announced but isn't linked to the field (no `aria-invalid` or `aria-describedby`), and the address format isn't checked. | Set `aria-invalid="true"`, reference the message with `aria-describedby`, and check the format. |

## Coverage of the 15 criteria

| Criterion | Level | Status | Basis |
|---|---|---|---|
| 3.1.1 Language of Page | A | Fail | #1 |
| 3.1.2 Language of Parts | AA | Pass (static) | No passages in another language found |
| 3.2.1 On Focus | A | Pass (static) | The tooltip that opens on focus isn't a change of context. Nothing navigates on focus. |
| 3.2.2 On Input | A | Fail | #2, plus #12 |
| 3.2.3 Consistent Navigation | AA | Fail | #3. The main nav itself is the same on all 11 pages. |
| 3.2.4 Consistent Identification | AA | Pass (static) | "Help & contact", Skip link and nav labels are the same everywhere |
| 3.2.6 Consistent Help | A | Fail | #3 |
| 3.3.1 Error Identification | A | Fail | #4 |
| 3.3.2 Labels or Instructions | A | Pass (static) | Every form field has a `<label>`, `aria-label` or `legend`. Required fields on the feedback form are marked. See advisory #14. |
| 3.3.3 Error Suggestion | AA | Fail | #4 |
| 3.3.4 Error Prevention (Legal, Financial, Data) | AA | Pass (static) | Claim submission requires ticking a confirmation box (the "confirmed" option). See review note 4. |
| 3.3.7 Redundant Entry | A | Fail | #5 |
| 3.3.8 Accessible Authentication (Minimum) | AA | Fail | #6 |
| 4.1.2 Name, Role, Value | A | Fail | #7–#10, plus #13 |
| 4.1.3 Status Messages | AA | Fail | #11. These already work: `planner.html:101`, `feedback.html:62`, `components/StopSearch.vue:6`. |
| 4.1.1 Parsing | — | Obsolete | Not graded |

## Review notes

1. **Email-signup message (`alerts.html:75`).** The `role="status"` element sits inside a modal that is `hidden` when the page loads. Some screen readers don't announce live regions that only become visible later. Confirm with NVDA and VoiceOver, or keep the live region outside the modal.
2. **Stop details panel (`map.html:53`, `js/map.js:18`).** The panel's contents change but nothing announces it. That's acceptable for a result the user asked for, but once #10 is fixed, check that screen reader users can find the new details (for example with `aria-controls` or by moving focus to the panel heading).
3. **Rotating alert banner (`alerts.html:30`).** Leaving it out of a live region is right, since announcing it every 20 seconds would be disruptive. Its auto-rotation is a 2.2.2 question, outside this audit.
4. **Claim submission and 3.3.4.** It's debatable whether a lost-item claim counts as "legal, financial or data" at all. It passes either way because of the confirmation checkbox. Showing a summary of steps 1–2 on step 3 would make it stronger.
5. **Hidden login steps (`login.html:31-58`).** Showing and hiding the password form and the code section is triggered by the user, so it isn't a 3.2.x issue. `digits[0].focus()` handles focus.

## Still needs checking

Every "Pass (static)" above still needs checking in a real browser and screen reader before any conformance claim:
- A keyboard and screen reader smoke test of 3.2.1, 3.2.2 and 4.1.2 on all 11 pages.
- Announcements for 4.1.3 on alerts, planner and feedback.
- 3.3.1 and 3.3.3 on the rendered error states.

## Not run or outside scope

- **Automated tools:** `wcag_scan.py`, `wcag_page.mjs` and axe-core weren't run (no shell).
- **Vue components:** Reviewed as source only. None of the 11 pages uses them.
- **Principles 1 and 2:** Outside scope and not evaluated. Problems I noticed in passing, for a later audit:
  - Carousel animates with no pause control (`css/site.css:84`); the banner auto-rotates (`js/alerts.js:16`).
  - Positive `tabindex` values (`login.html:41-42`).
  - Focus outline removed on nav links (`css/site.css:52`).
  - Small targets: 16px mini buttons (`css/site.css:133`), 20px zoom buttons (`css/site.css:161`).
  - Peak fares shown only in red (`fares.html:42`), and table headers marked up as `<td>` (`fares.html:48-60`).
  - `min-width: 880px` on alert details (`css/site.css:136`).
  - Fixed footer covers content (`css/site.css:189`).
  - Low-contrast wordmark and floating labels (`css/site.css:48`, `:180`).
  - Drag-only reordering (`components/SavedTrips.vue:7-15`).
  - Tooltip can't be dismissed (`ZoneInfoTooltip.vue`).
  - `autocomplete="off"` on the claim-1 email field (`claim-1.html:40`).
  - Step-free icons have no text alternative (`planner.html:61`, `:70`).

## Assumptions

- **WCAG version:** WCAG 2.2 (W3C Recommendation, 12 December 2024). 4.1.1 is treated as obsolete; policies that cite WCAG 2.0 or 2.1 may still require it.
- **Validation:** Pages are assumed to have no server-side validation beyond what's in the source.
- **Rendering:** Behaviour was worked out from the source code; nothing was rendered.

## To reproduce

With a shell, run `python3 ~/.claude/skills/wcag22-a11y/scripts/wcag_audit.py . --url . --level AA --out report.md`. Then check each finding above with a keyboard and NVDA+Firefox or VoiceOver+Safari.
