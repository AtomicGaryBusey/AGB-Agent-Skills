# WCAG 2.2 Level AA audit: Brightwater Transit static front end (Principles 3 and 4 only)

**Scope:** 11 HTML pages (index, planner, fares, alerts, map, claim-1, claim-2, claim-3, login, feedback, help), `css/site.css`, `js/*.js`, `img/*.svg` and 4 Vue source components. I treated the claim process (claim-1 → claim-2 → claim-3) and the sign-in process (password → one-time code) as complete processes. The audit is Level AA, limited to the 15 in-scope Principle 3 and 4 success criteria. 4.1.1 Parsing is obsolete in WCAG 2.2 and was not evaluated.

**How it was checked:** I read every file listed above. No shell was available, so the skill's scanners (`wcag_scan.py`, `wcag_page.mjs`) were not run. No browser, keyboard walkthrough or screen reader was used. I rate a finding a nonconformity when the source alone proves it.

**Summary:** 12 nonconformities, 0 deviations, 3 advisories, 4 review notes. Of the 15 criteria in scope: 9 fail, 4 pass on static evidence, 1 is N/A and 1 is not fully evaluated. The site **does not conform** to WCAG 2.2 AA for Principles 3 and 4. Failing criteria: 3.1.1, 3.2.2, 3.2.3, 3.2.6, 3.3.1, 3.3.3, 3.3.7, 3.3.8, 4.1.2.

## Findings

| # | Severity | Check ID | Ref | Target | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|---|
| 1 | Nonconformity | WCAG-3.1.1 | WCAG 2.2 SC 3.1.1 (A) | page | `fares.html:2` | The page doesn't say what language it's in. | `<html>` has no `lang`; the other 10 pages have `lang="en"`. | `<html lang="en">` |
| 2 | Nonconformity | WCAG-3.2.2 | WCAG 2.2 SC 3.2.2 (A) | page | `js/fares.js:7-9` (control `fares.html:34`) | Changing the "Show fares for" select loads a new page right away. There is no submit button and no warning. | A `change` listener sets `window.location.href`. With the keyboard, arrowing through the options reloads the page on the first key press. | Remove the auto-navigation and add `<button type="submit">Show fares</button>` to the form at `fares.html:31`, or filter the table in place without leaving the page. |
| 3 | Nonconformity | WCAG-3.2.6 (also 3.2.3) | WCAG 2.2 SC 3.2.6 (A); SC 3.2.3 (AA) | page | `claim-2.html:11-27`, `claim-2.html:63` | The "Help & contact" link is in the header on every other page. On claim step 2 it moves to the end of the footer, so its order relative to the rest of the page changes partway through the claim. | The header has no `.help-link`; the link appears as the 4th footer item instead. Compare `claim-1.html:27` and `claim-3.html:27`. | Put back `<a class="help-link" href="help.html">…Help &amp; contact</a>` after `</nav>` in `claim-2.html` and remove the footer copy at line 63. |
| 4 | Nonconformity | WCAG-3.3.7 | WCAG 2.2 SC 3.3.7 (A) | page / process | `claim-3.html:35-40` vs `claim-1.html:38-44` | Step 3 asks again for the email address and phone number the user already gave in step 1. Nothing fills them in and there is no option to choose them. | Step 1 sends `email` and `phone` to claim-2 as GET parameters. The claim-2 form doesn't pass them on, and `js/claim.js` doesn't fill in `#c3-email` or `#c3-phone`. None of the exceptions (essential, security, stale data) applies. | Carry the step 1 values through (hidden fields in claim-2, then fill `value` in claim-3), or show them as a read-only summary with an edit link. |
| 5 | Nonconformity | WCAG-3.3.8 | WCAG 2.2 SC 3.3.8 (AA) | page / process | `js/login.js:8-12`, `js/login.js:22`; `login.html:50-55` | Pasting is blocked in the password field and in every one-time code box. Users must remember and retype the password and copy the SMS code by hand, which are cognitive function tests. Password managers can't help, and the code can't be pasted or autofilled. | `blockPaste` calls `preventDefault()` on `paste` for `#pw` and for each `.otp-digit`. The code inputs have `autocomplete="off"` and are split into six `maxlength="1"` fields. | Remove both paste blockers. Use one code field: `<input autocomplete="one-time-code" inputmode="numeric" pattern="\d{6}">`, or share a pasted 6-digit value across the six boxes. |
| 6 | Nonconformity | WCAG-3.3.1 | WCAG 2.2 SC 3.3.1 (A) | page | `js/feedback.js:8-12,14-22`; `feedback.html:40,53` | When email or message is invalid, submitting does nothing visible except a red border. The error elements are never filled in or shown, so there is no text saying which field is wrong or why. | `check()` only toggles `.is-invalid` and `aria-invalid`. `#fb-email-error` and `#fb-message-error` stay `hidden` and empty. Focus doesn't move. | In `check()`, set the error's `textContent` (for example "Enter your email address"), set `hidden = false` when invalid, and move focus to the first invalid field. |
| 7 | Nonconformity | WCAG-3.3.3 | WCAG 2.2 SC 3.3.3 (AA) | page | `js/feedback.js:16` | The site knows the fix for a badly formatted email but never says it. | Same root cause as #6. The format regex fails silently. | For a format error, show "Enter an email address in the format name@example.com". |
| 8 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (A) | page | `planner.html:36` | The "locate me" button has no accessible name. Screen readers announce just "button". | `<button class="btn-locate" id="locate-me"></button>` is empty. Its icon is a CSS background (`site.css:105`), which gives no name. | Add `aria-label="Use my current location"`, or visually hidden text. |
| 9 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (A) | page | `alerts.html:41`; `js/alerts.js:26-28` | The push-notification switch never reports its state. It always reads "off", even after it's turned on. | The markup starts with `aria-checked="false"`, and `toggle()` only toggles the `is-on` class. | In `toggle()`, add `sw.setAttribute('aria-checked', String(sw.classList.contains('is-on')))`, or use `<input type="checkbox" role="switch">` as `components/ToggleSwitch.vue` does. |
| 10 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (A) | page | `alerts.html:68`; `js/alerts.js:64` | The close control of the email-alerts dialog is a `<span>`. It has no role or name and can't get keyboard focus. Escape is also blocked (`alerts.js:75-77`) and Tab is kept inside the dialog (`alerts.js:79-85`), so keyboard users can't close the dialog. That last part is 2.1.2, outside this audit's scope, but it has the same root cause. | `<span class="modal__close">&times;</span>` has only a click listener. | Use `<button type="button" class="modal__close" aria-label="Close">&times;</button>`, let Escape close the dialog, and include the close button in the focus loop. |
| 11 | Nonconformity | WCAG-4.1.2 | WCAG 2.2 SC 4.1.2 (A) | page | `map.html:43-49`; `js/map.js:15-20` | The map stops respond to clicks but have no role, no accessible name as a control and no `tabindex`. Assistive technology sees them as plain text, not as buttons. This also fails 2.1.1 (outside scope). | `<g class="stop" data-stop="…">` has only a `click` listener. | Give each `<g>` `role="button" tabindex="0" aria-label="Market Square: show stop details"` plus Enter/Space handlers, or wrap each stop in `<a href="#stop-market">`. |
| 12 | Nonconformity | WCAG-4.1.3 | WCAG 2.2 SC 4.1.3 (AA) | page | `alerts.html:51`; `js/alerts.js:40,45` | The "Checking..." and "Updated at HH:MM. No new alerts." messages aren't announced to screen readers. | `#refresh-result` is a plain `<span>` with no `role` or `aria-live`. Focus stays on the button. | `<span id="refresh-result" role="status"></span>` |
| 13 | Advisory | WCAG-BP-disabled-submit | Related to SC 3.3.2 (A) | page | `claim-3.html:46` | "Submit claim" is disabled until the confirmation box is ticked, and nothing explains why. Disabled buttons also can't receive focus. | The `disabled` attribute plus the toggle in `js/claim.js:5-7`. | Keep the button enabled and check the box on submit with an error message, or add a hint linked by `aria-describedby`. |
| 14 | Advisory | WCAG-BP-unique-id | Related to SC 4.1.2 | component | `components/ZoneInfoTooltip.vue:33` | Two tooltips for the same zone on one page would share an `id`, so `aria-describedby` could point to the wrong tooltip. | The id is `zone-tip-${this.zone}`. | Add a per-instance counter or use Vue 3.5 `useId()`. |
| 15 | Advisory | WCAG-BP-error-text | Related to SC 3.3.1 | page | `js/alerts.js:70` | The "Enter an email address." message is announced through `role="status"`, but the field isn't marked invalid or linked to the message. | No `aria-invalid` or `aria-describedby` on `#alert-email`. | On error, set `aria-invalid="true"` and `aria-describedby="alert-subscribe-msg"`. |

## SC coverage (Principles 3 and 4, AA)

| SC | Level | Status | Notes |
|---|---|---|---|
| 3.1.1 Language of Page | A | **Fail** | #1 |
| 3.1.2 Language of Parts | AA | Pass (static) | No text in other languages found. |
| 3.2.1 On Focus | A | Pass (static) | Only `ZoneInfoTooltip` reacts to focus, and a tooltip isn't a change of context. |
| 3.2.2 On Input | A | **Fail** | #2 |
| 3.2.3 Consistent Navigation | AA | **Fail** | #3. The main nav and footer are otherwise the same on every page. |
| 3.2.4 Consistent Identification | AA | Pass (static) | "Help & contact", "Sign in" and "Skip to main content" are labelled the same everywhere. |
| 3.2.6 Consistent Help | A | **Fail** | #3 |
| 3.3.1 Error Identification | A | **Fail** | #6 |
| 3.3.2 Labels or Instructions | A | Pass (static) | All inputs have labels or a legend, and required fields are marked. See advisory #13. |
| 3.3.3 Error Suggestion | AA | **Fail** | #7 |
| 3.3.4 Error Prevention (Legal, Financial, Data) | AA | N/A | No legal commitments, financial transactions, or changes to or deletion of stored data. The claim has a confirmation checkbox anyway. |
| 3.3.7 Redundant Entry | A | **Fail** | #4 |
| 3.3.8 Accessible Authentication (Minimum) | AA | **Fail** | #5 |
| 4.1.2 Name, Role, Value | A | **Fail** | #8–#11 |
| 4.1.3 Status Messages | AA | **Fail** | #12. Handled correctly: `planner.html:101`, `alerts.html:75`, `feedback.html:62`, `StopSearch.vue:6`. |

## Review notes

- **Vue components are source only.** I judged `ToggleSwitch.vue` (a native checkbox with `role="switch"`, which passes 4.1.2) and `StopSearch.vue` (a `role="status"` result count, which passes 4.1.3) from their templates. They need checking again once they are built and mounted.
- **The native `<dialog>` on index** (`index.html:65`, `js/site.js`) looks correct: `showModal()`, a labelled title and focus returned to the opener. Browser and AT support was not confirmed.
- **The rotating alert banner** (`alerts.js:16`) is not a live region. That's correct for 4.1.3: messages that change on a timer shouldn't be announced. The pause/stop requirement for it falls under 2.2.2, which is outside scope.
- **3.3.8 exception check:** the "Object Recognition" and "Personal Content" exceptions don't apply to #5. Blocking paste also removes the "mechanism to assist" the criterion allows.

## Manual checks still required

- **Screen reader smoke test** (NVDA + Firefox, VoiceOver + Safari) of every fix for #8–#12, and of the 4.1.2 name/role/state for `role="switch"`, the SVG map `role="group"` and the `aria-current` nav links.
- **Keyboard walk of both processes:** the claim steps 1–3 and sign-in including the code step.
- **3.3.1 and 3.3.3 on claim-1 and claim-2:** they have no client-side validation, so server-side error responses must be checked.
- **Run the skill's scanners** once a shell is available: `wcag_audit.py . --url . --level AA`.

## Out of scope (seen during review; not assessed)

- 1.1.1 / 1.3.1: step-free icon SVGs with no accessible name (`planner.html:61,70`); fare-table headers marked up as `<td class="th">` (`fares.html:48-59`).
- 1.3.5: `autocomplete="off"` and a missing `autocomplete` on claim-1 fields (`claim-1.html:36-44`).
- 1.4.3 / 1.4.11: floating labels `#a0a0a0` (`site.css:180`); wordmark `#9cc3e6`; peak fares shown only in red (1.4.1).
- 2.1.1 / 2.1.2: the map stops (#11) and the modal trap (#10); the drag-only reordering in `SavedTrips.vue` (also 2.5.7).
- 2.2.2: the auto-playing CSS promo carousel (`site.css:84`) and the rotating banner.
- 2.4.3: positive `tabindex` on the login page (`login.html:41-42`).
- 2.4.7: `.site-nav a:focus { outline: none }` (`site.css:52`).
- 2.4.11: the fixed `.dock-footer` on feedback (`site.css:189`).
- 2.5.8: 16px banner buttons (`site.css:133`) and 20px zoom buttons (`site.css:161`).
- 1.4.10: `min-width: 880px` on alerts (`site.css:136`).

## Assumptions

- WCAG 2.2 (W3C Recommendation, 12 December 2024) is the reference. 4.1.1 is treated as obsolete; a policy tied to WCAG 2.0 or 2.1 (Section 508 or EN 301 549) would still require checking it.
- The pages are served as they are, with no server-side prefill or validation other than what the source shows.
- No assistive technology or browser was used, so each "Pass (static)" means the source shows no failure, not a verified pass.
