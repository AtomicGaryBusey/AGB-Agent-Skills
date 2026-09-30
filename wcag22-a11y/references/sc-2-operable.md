# WCAG 2.2 success criteria — Principle 2: Operable

> **Source and licence.** Normative text quoted in this file (marked as block quotes, including SC text, notes and guideline statements) is copied verbatim from
> *Web Content Accessibility Guidelines (WCAG) 2.2*, W3C Recommendation, 12 December 2024 edition,
> <https://www.w3.org/TR/WCAG22/>. Copyright © 2024 World Wide Web Consortium.
> <https://www.w3.org/copyright/document-license-2023/>. Status: W3C Recommendation.
> Technique and failure IDs/titles and ACT rule names are taken from *Understanding WCAG 2.2* and
> *Techniques for WCAG 2.2* (W3C Group Notes, informative), <https://www.w3.org/WAI/WCAG22/Understanding/>,
> <https://www.w3.org/WAI/WCAG22/Techniques/>, Copyright © 2024 World Wide Web Consortium, under the same licence.
> All other text (summaries, testability, procedures, code patterns and examples) is original to this skill.
> See `NOTICE` at the skill root.

Principle 2 has 34 success-criterion sections. Each entry uses the check ID `WCAG-<sc>` (see `check-index.md`). Testability: **automated** = a tool can decide the core requirement for most content; **assisted** = tools find candidates or partial failures and a human confirms; **manual** = human judgement dominates. "Static scanner" means the skill's source-code scanner; "page runner" means the live-page runner (axe-core 4.13.0 plus custom checks).

## Contents

- Guideline 2.1 Keyboard Accessible
  - [WCAG-2.1.1 Keyboard](#wcag-2-1-1) (A)
  - [WCAG-2.1.2 No Keyboard Trap](#wcag-2-1-2) (A)
  - [WCAG-2.1.3 Keyboard (No Exception)](#wcag-2-1-3) (AAA)
  - [WCAG-2.1.4 Character Key Shortcuts](#wcag-2-1-4) (A)
- Guideline 2.2 Enough Time
  - [WCAG-2.2.1 Timing Adjustable](#wcag-2-2-1) (A)
  - [WCAG-2.2.2 Pause, Stop, Hide](#wcag-2-2-2) (A)
  - [WCAG-2.2.3 No Timing](#wcag-2-2-3) (AAA)
  - [WCAG-2.2.4 Interruptions](#wcag-2-2-4) (AAA)
  - [WCAG-2.2.5 Re-authenticating](#wcag-2-2-5) (AAA)
  - [WCAG-2.2.6 Timeouts](#wcag-2-2-6) (AAA)
- Guideline 2.3 Seizures and Physical Reactions
  - [WCAG-2.3.1 Three Flashes or Below Threshold](#wcag-2-3-1) (A)
  - [WCAG-2.3.2 Three Flashes](#wcag-2-3-2) (AAA)
  - [WCAG-2.3.3 Animation from Interactions](#wcag-2-3-3) (AAA)
- Guideline 2.4 Navigable
  - [WCAG-2.4.1 Bypass Blocks](#wcag-2-4-1) (A)
  - [WCAG-2.4.2 Page Titled](#wcag-2-4-2) (A)
  - [WCAG-2.4.3 Focus Order](#wcag-2-4-3) (A)
  - [WCAG-2.4.4 Link Purpose (In Context)](#wcag-2-4-4) (A)
  - [WCAG-2.4.5 Multiple Ways](#wcag-2-4-5) (AA)
  - [WCAG-2.4.6 Headings and Labels](#wcag-2-4-6) (AA)
  - [WCAG-2.4.7 Focus Visible](#wcag-2-4-7) (AA)
  - [WCAG-2.4.8 Location](#wcag-2-4-8) (AAA)
  - [WCAG-2.4.9 Link Purpose (Link Only)](#wcag-2-4-9) (AAA)
  - [WCAG-2.4.10 Section Headings](#wcag-2-4-10) (AAA)
  - [WCAG-2.4.11 Focus Not Obscured (Minimum)](#wcag-2-4-11) (AA, new in 2.2)
  - [WCAG-2.4.12 Focus Not Obscured (Enhanced)](#wcag-2-4-12) (AAA, new in 2.2)
  - [WCAG-2.4.13 Focus Appearance](#wcag-2-4-13) (AAA, new in 2.2)
- Guideline 2.5 Input Modalities
  - [WCAG-2.5.1 Pointer Gestures](#wcag-2-5-1) (A)
  - [WCAG-2.5.2 Pointer Cancellation](#wcag-2-5-2) (A)
  - [WCAG-2.5.3 Label in Name](#wcag-2-5-3) (A)
  - [WCAG-2.5.4 Motion Actuation](#wcag-2-5-4) (A)
  - [WCAG-2.5.5 Target Size (Enhanced)](#wcag-2-5-5) (AAA)
  - [WCAG-2.5.6 Concurrent Input Mechanisms](#wcag-2-5-6) (AAA)
  - [WCAG-2.5.7 Dragging Movements](#wcag-2-5-7) (AA, new in 2.2)
  - [WCAG-2.5.8 Target Size (Minimum)](#wcag-2-5-8) (AA, new in 2.2)

## Guideline 2.1 — Keyboard Accessible

> Make all functionality available from a keyboard.

<a id="wcag-2-1-1"></a>
### WCAG-2.1.1 — Keyboard (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#keyboard> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html>

- **Text:**

  > All functionality of the content is operable through a keyboard interface without requiring specific timings for individual keystrokes, except where the underlying function requires input that depends on the path of the user's movement and not just the endpoints.
  >
  > *Note 1:* This exception relates to the underlying function, not the input technique. For example, if using handwriting to enter text, the input technique (handwriting) requires path-dependent input but the underlying function (text input) does not.
  >
  > *Note 2:* This does not forbid and should not discourage providing mouse input or other input methods in addition to keyboard operation.

- **Applies to:** keyboard, interactive controls, custom widgets, navigation, forms, media players
- **Testability:** assisted — axe-core flags `scrollable-region-focusable`, `frame-focusable-content` and `server-side-image-map`, but cannot tell whether a custom widget really responds to keys. A static scanner can flag click handlers on non-focusable elements (`<div onClick>` without `tabindex`/`onKeyDown`), `tabindex="-1"` on controls and mouse-only events; a page runner can walk the Tab order and compare it with the set of clickable elements. A human must operate every function with the keyboard alone.
  - **axe-core rules (4.13.0):** `frame-focusable-content`, `scrollable-region-focusable`, `server-side-image-map`
- **Test procedure:**
  1. Unplug or ignore the mouse and reach every interactive element with Tab/Shift+Tab.
  2. Activate each control with the keys its role implies (Enter, Space, arrow keys, Esc).
  3. Complete every task end to end (menus, dialogs, drag-and-drop, sliders, carousels, forms) with the keyboard only.
  4. Confirm that a keyboard alternative exists for any path-dependent or mouse-only interaction, and that no function needs specific keystroke timing.
  5. Record each function that is unreachable or not operable as a failure.
- **Common failures:**
  - F54 — Failure of Success Criterion 2.1.1 due to using only pointing-device-specific event handlers (including gesture) for a function
  - F55 — Failure of Success Criteria 2.1.1, 2.4.7, 2.4.13, and 3.2.1 due to using script to remove focus when focus is received
  - F42 — Failure of Success Criteria 1.3.1, 2.1.1, 2.1.3, or 4.1.2 when emulating links
  - Pattern: Clickable `<div>`/`<span>` with an `onclick` handler and no `tabindex="0"` or key handler.
  - Pattern: `<a>` without `href` used as a button, so it is not in the Tab order.
  - Pattern: Functions exposed only on `mouseover`/`hover` (for example, row actions that appear only on hover).
  - Pattern: Drag-and-drop reordering or map panning with no keyboard equivalent.
  - Pattern: React component that calls `e.preventDefault()` on `keydown` for all keys, blocking native activation.
- **Sufficient techniques:**
  - G202 — Ensuring keyboard control for all functionality
  - H91 — Using HTML form controls and links
  - PDF3 — Ensuring correct tab and reading order in PDF documents
  - PDF11 — Providing links and link text using the Link annotation and the /Link structure element in PDF documents
  - PDF23 — Providing interactive form controls in PDF documents
  - G90 — Providing keyboard-triggered event handlers
  - SCR20 — Using both keyboard and other device-specific functions
  - SCR35 — Making actions keyboard accessible by using the onclick event of anchors and buttons
  - SCR2 — Using redundant keyboard and mouse event handlers
- **ACT test rules:** [Iframe with interactive elements is not excluded from tab-order](https://www.w3.org/WAI/standards-guidelines/act/rules/akn7bn/); [Scrollable content can be reached with sequential focus navigation](https://www.w3.org/WAI/standards-guidelines/act/rules/0ssw9k/)
- **Pass/fail example:**

  Pass:

  ```html
  <button type="button" class="card-action" onclick="openDetails()">
    View details
  </button>
  ```

  Fail:

  ```html
  <div class="card-action" onclick="openDetails()">
    View details
  </div>
  ```

<a id="wcag-2-1-2"></a>
### WCAG-2.1.2 — No Keyboard Trap (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#no-keyboard-trap> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/no-keyboard-trap.html>

- **Text:**

  > If keyboard focus can be moved to a component of the page using a keyboard interface, then focus can be moved away from that component using only a keyboard interface, and, if it requires more than unmodified arrow or tab keys or other standard exit methods, the user is advised of the method for moving focus away.
  >
  > *Note:* Since any content that does not meet this success criterion can interfere with a user's ability to use the whole page, all content on the web page (whether it is used to meet other success criteria or not) must meet this success criterion. See Conformance Requirement 5: Non-Interference.

- **Applies to:** keyboard, focus, modals and dialogs, embedded content (iframes, plugins, editors), custom widgets
- **Testability:** assisted — No axe-core rule decides this. A page runner can press Tab repeatedly and detect focus cycling inside a small set of elements or never leaving an iframe or editor; a static scanner can flag `keydown` handlers that call `preventDefault()` on Tab. A human confirms whether any documented non-standard exit method is announced to users.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Tab into every component, including embedded frames, rich-text editors, video players and dialogs.
  2. Try to move focus out with Tab, Shift+Tab and, for dialogs, Esc.
  3. If only a non-standard key sequence exits, check that the page tells users about it before they enter.
  4. Record any component that holds focus with no advised way out as a failure.
- **Common failures:**
  - F10 — Failure of Success Criterion 2.1.2 and Conformance Requirement 5 due to combining multiple content formats in a way that traps users inside one format type
  - Pattern: Custom focus-trap code in a non-modal widget that wraps Tab back to its first element forever.
  - Pattern: Rich-text editor or code editor that consumes Tab with no documented escape key (for example, Esc then Tab).
  - Pattern: Third-party `<iframe>` or plugin that captures keyboard focus.
  - Pattern: Modal dialog that traps focus and has no close button reachable by keyboard or Esc handling.
- **Sufficient techniques:**
  - G21 — Ensuring that users are not trapped in content
- **ACT test rules:** [Focusable element has no keyboard trap](https://www.w3.org/WAI/standards-guidelines/act/rules/80af7b/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <textarea id="code" aria-describedby="code-help"></textarea>
  <p id="code-help">Tab inserts an indent. Press Esc, then Tab, to leave the editor.</p>
  ```

  Fail:

  ```js
  editor.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') { e.preventDefault(); insertIndent(); }
    // no key is provided to leave the editor
  });
  ```

<a id="wcag-2-1-3"></a>
### WCAG-2.1.3 — Keyboard (No Exception) (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#keyboard-no-exception> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/keyboard-no-exception.html>

- **Text:**

  > All functionality of the content is operable through a keyboard interface without requiring specific timings for individual keystrokes.

- **Applies to:** keyboard, all functionality including path-dependent input
- **Testability:** manual — axe-core maps `scrollable-region-focusable` here, which covers only one symptom. Static and runner checks are the same as for 2.1.1, but without the path-dependent exception a human must confirm every function (including freehand drawing or gesture paths) has a keyboard method.
  - **axe-core rules (4.13.0):** `scrollable-region-focusable`
- **Test procedure:**
  1. Perform the full 2.1.1 keyboard test.
  2. List any function that 2.1.1 excused because it depends on the path of the user's movement.
  3. Check that each such function also has a keyboard method (for example, nudging with arrow keys or entering coordinates).
  4. Fail any function with no keyboard method, with no exception.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Freehand drawing canvas with no keyboard way to create shapes or strokes.
  - Pattern: Signature pad that accepts only pointer input with no typed-signature alternative.
  - Pattern: Game or map that needs continuous pointer movement.
- **Sufficient techniques:** No additional techniques exist for this success criterion. Follow techniques for Success Criterion 2.1.1. If that is not possible because there is a requirement for path-dependent input, then it is not possible to meet this Level AAA success criterion.
- **ACT test rules:** [Iframe with interactive elements is not excluded from tab-order](https://www.w3.org/WAI/standards-guidelines/act/rules/akn7bn/); [Scrollable content can be reached with sequential focus navigation](https://www.w3.org/WAI/standards-guidelines/act/rules/0ssw9k/)
- **Pass/fail example:**

  Pass:

  ```html
  <canvas id="sketch" aria-label="Drawing area"></canvas>
  <p>Use arrow keys to move the pen, Space to toggle drawing.</p>
  ```

  Fail:

  ```html
  <canvas id="sketch" onpointermove="draw(event)"></canvas>
  <!-- no keyboard method to draw -->
  ```

<a id="wcag-2-1-4"></a>
### WCAG-2.1.4 — Character Key Shortcuts (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#character-key-shortcuts> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/character-key-shortcuts.html>

- **Text:**

  > If a keyboard shortcut is implemented in content using only letter (including upper- and lower-case letters), punctuation, number, or symbol characters, then at least one of the following is true:
  >
  > - **Turn off:** A mechanism is available to turn the shortcut off;
  > - **Remap:** A mechanism is available to remap the shortcut to include one or more non-printable keyboard keys (e.g., Ctrl, Alt);
  > - **Active only on focus:** The keyboard shortcut for a user interface component is only active when that component has focus.

- **Applies to:** keyboard shortcuts, single-character key bindings, web apps with hotkeys
- **Testability:** assisted — No axe-core rule. A static scanner can find `keydown`/`keypress` listeners that react to a single printable character with no modifier check (for example, `if (e.key === 's')`); a page runner can type single letters with focus on the body and watch for actions. A human confirms whether a setting exists to turn off or remap the shortcut, or that it is active only when the component has focus.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Find every keyboard shortcut in the content (documentation, help menus, source).
  2. Identify shortcuts that use only a letter, number, punctuation or symbol key, without Ctrl/Alt/Cmd.
  3. Check that each such shortcut can be turned off, can be remapped to include a modifier, or works only while its component has focus.
  4. Test with speech input or by typing text elsewhere on the page to confirm no unintended actions fire.
- **Common failures:**
  - F99 — Failure of Success Criterion 2.1.4 due to implementing character key shortcuts that cannot be turned off or remapped
  - Pattern: Global `document.addEventListener('keydown', ...)` that triggers delete, archive or send on a single letter.
  - Pattern: React `useHotkeys('j', next)` bound at app level with no settings toggle.
  - Pattern: Shortcut handler that does not check `e.ctrlKey`/`e.metaKey`/`e.altKey`.
- **Sufficient techniques:**
  - G217 — Providing a mechanism to allow users to remap or turn off character key shortcuts
- **ACT test rules:** [No keyboard shortcut uses only printable characters](https://www.w3.org/WAI/standards-guidelines/act/rules/ffbc54/proposed/)
- **Pass/fail example:**

  Pass:

  ```js
  document.addEventListener('keydown', (e) => {
    if (settings.shortcutsEnabled && e.altKey && e.key === 'a') archive();
  });
  ```

  Fail:

  ```js
  document.addEventListener('keydown', (e) => {
    if (e.key === 'a') archive(); // fires while dictating or typing
  });
  ```

## Guideline 2.2 — Enough Time

> Provide users enough time to read and use content.

<a id="wcag-2-2-1"></a>
### WCAG-2.2.1 — Timing Adjustable (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#timing-adjustable> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable.html>

- **Text:**

  > For each time limit that is set by the content, at least one of the following is true:
  >
  > - **Turn off:** The user is allowed to turn off the time limit before encountering it; or
  > - **Adjust:** The user is allowed to adjust the time limit before encountering it over a wide range that is at least ten times the length of the default setting; or
  > - **Extend:** The user is warned before time expires and given at least 20 seconds to extend the time limit with a simple action (for example, "press the space bar"), and the user is allowed to extend the time limit at least ten times; or
  > - **Real-time Exception:** The time limit is a required part of a real-time event (for example, an auction), and no alternative to the time limit is possible; or
  > - **Essential Exception:** The time limit is essential and extending it would invalidate the activity; or
  > - **20 Hour Exception:** The time limit is longer than 20 hours.
  >
  > *Note:* This success criterion helps ensure that users can complete tasks without unexpected changes in content or context that are a result of a time limit. This success criterion should be considered in conjunction with Success Criterion 3.2.1, which puts limits on changes of content or context as a result of user action.

- **Applies to:** timing, session timeouts, auto-advancing content, redirects, timed forms
- **Testability:** assisted — axe-core `meta-refresh` flags `<meta http-equiv="refresh">` with a delay. A static scanner can flag `setTimeout` redirects, session-expiry code and short `meta refresh` values; a page runner can wait on the page and detect navigation or expiry dialogs. A human confirms whether users can turn off, adjust or extend each limit (at least 10 times the default or with a 20-second warning).
  - **axe-core rules (4.13.0):** `meta-refresh`
- **Test procedure:**
  1. List every time limit set by the content: session timeouts, auto-redirects, timed questions, auto-advancing slides.
  2. For each, check that the user can turn it off, adjust it to at least ten times the default, or is warned and can extend it with a simple action (at least 20 seconds to respond, at least ten times).
  3. Confirm whether a real-time event, an essential limit or a limit over 20 hours applies instead.
  4. Record any limit with none of these options as a failure.
- **Common failures:**
  - F40 — Failure due to using meta redirect with a time limit
  - F41 — Failure of Success Criterion 2.2.1, 2.2.4, and 3.2.5 due to using meta refresh to reload the page
  - F58 — Failure of Success Criterion 2.2.1 due to using server-side techniques to automatically redirect pages after a time-out
  - Pattern: `<meta http-equiv="refresh" content="30; url=/logout">` with no user control.
  - Pattern: Session expiry that logs the user out silently with no warning dialog.
  - Pattern: Carousel that auto-advances content the user needs to read, with no pause control (also 2.2.2).
  - Pattern: Checkout that times out in a few minutes and cannot be extended.
- **Sufficient techniques:**
  - G133 — Providing a checkbox on the first page of a multipart form that allows users to ask for longer session time limit or no session time limit
  - G198 — Providing a way for the user to turn the time limit off
  - G180 — Providing the user with a means to set the time limit to 10 times the default time limit
  - SCR16 — Providing a script that warns the user a time limit is about to expire
  - SCR1 — Allowing the user to extend the default time limit
  - G4 — Allowing the content to be paused and restarted from where it was paused
  - SCR33 — Using script to scroll content, and providing a mechanism to pause it
  - SCR36 — Providing a mechanism to allow users to display moving, scrolling, or auto-updating text in a static window or area
- **ACT test rules:** [Meta element has no refresh delay](https://www.w3.org/WAI/standards-guidelines/act/rules/bc659a/); [Meta element has no refresh delay (no exception)](https://www.w3.org/WAI/standards-guidelines/act/rules/bisz58/)
- **Pass/fail example:**

  Pass:

  ```html
  <div role="alertdialog" aria-labelledby="t">
    <p id="t">Your session ends in 2 minutes.</p>
    <button onclick="extendSession()">Stay signed in</button>
  </div>
  ```

  Fail:

  ```html
  <meta http-equiv="refresh" content="60; url=/session-expired">
  ```

<a id="wcag-2-2-2"></a>
### WCAG-2.2.2 — Pause, Stop, Hide (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#pause-stop-hide> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html>

- **Text:**

  > For moving, blinking, scrolling, or auto-updating information, all of the following are true:
  >
  > - **Moving, blinking, scrolling:** For any moving, blinking or scrolling information that (1) starts automatically, (2) lasts more than five seconds, and (3) is presented in parallel with other content, there is a mechanism for the user to pause, stop, or hide it unless the movement, blinking, or scrolling is part of an activity where it is essential; and
  > - **Auto-updating:** For any auto-updating information that (1) starts automatically and (2) is presented in parallel with other content, there is a mechanism for the user to pause, stop, or hide it or to control the frequency of the update unless the auto-updating is part of an activity where it is essential.
  >
  > *Note 1:* For requirements related to flickering or flashing content, refer to Guideline 2.3.
  >
  > *Note 2:* Since any content that does not meet this success criterion can interfere with a user's ability to use the whole page, all content on the web page (whether it is used to meet other success criteria or not) must meet this success criterion. See Conformance Requirement 5: Non-Interference.
  >
  > *Note 3:* Content that is updated periodically by software or that is streamed to the user agent is not required to preserve or present information that is generated or received between the initiation of the pause and resuming presentation, as this may not be technically possible, and in many situations could be misleading to do so.
  >
  > *Note 4:* An animation that occurs as part of a preload phase or similar situation can be considered essential if interaction cannot occur during that phase for all users and if not indicating progress could confuse users or cause them to think that content was frozen or broken.

- **Applies to:** motion and animation, auto-updating content, carousels, marquees, blinking text, video backgrounds, tickers
- **Testability:** assisted — axe-core `blink` and `marquee` catch the obsolete elements. A static scanner can flag `autoplay` video, CSS `animation: ... infinite`, and `setInterval` updaters; a page runner can observe DOM or pixel changes over 5 seconds. A human checks each moving, blinking, scrolling or auto-updating item for a pause, stop or hide mechanism.
  - **axe-core rules (4.13.0):** `blink`, `marquee`
- **Test procedure:**
  1. Load the page and watch it for at least 5 seconds; list anything that moves, blinks, scrolls or updates on its own.
  2. For moving/blinking/scrolling content that starts automatically, lasts more than 5 seconds and is shown with other content, confirm a pause, stop or hide mechanism.
  3. For auto-updating content that starts automatically and is shown with other content, confirm a pause, stop, hide or update-frequency control.
  4. Check that the controls are keyboard operable and have accessible names.
  5. Exclude only movement that is essential to the activity.
- **Common failures:**
  - F16 — Failure of Success Criterion 2.2.2 due to including scrolling content where movement is not essential to the activity without also including a mechanism to pause and restart the content
  - F112 — Failure of Success Criterion 2.2.2 due to using blinking content that lasts for more than five seconds without a mechanism to stop it
  - F50 — Failure of Success Criterion 2.2.2 due to a script that causes a blink effect without a mechanism to stop the blinking at 5 seconds or less
  - F7 — Failure of Success Criterion 2.2.2 due to an object or applet … for more than five seconds
  - Pattern: `<marquee>` or `<blink>` elements.
  - Pattern: Autoplaying looping `<video autoplay loop muted>` hero banner with no pause button.
  - Pattern: Auto-rotating carousel (`setInterval(next, 4000)`) with no pause control.
  - Pattern: Live news ticker updated by script with no way to stop it.
  - Pattern: Infinite CSS animation on decorative elements alongside page content.
- **Sufficient techniques:**
  - G4 — Allowing the content to be paused and restarted from where it was paused
  - SCR33 — Using script to scroll content, and providing a mechanism to pause it
  - G11 — Creating content that blinks for less than 5 seconds
  - G152 — Setting animated gif images to stop blinking after n cycles (within 5 seconds)
  - SCR22 — Using scripts to control blinking and stop it in five seconds or less
  - G186 — Using a control in the web page that stops moving, blinking, or auto-updating content
  - G191 — Providing a link, button, or other mechanism that reloads the page without any blinking content
- **ACT test rules:** [Text content that changes automatically can be paused, stopped or hidden](https://www.w3.org/WAI/standards-guidelines/act/rules/efbfc7/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <div class="carousel">
    <button aria-pressed="false" onclick="toggleRotation(this)">Pause slides</button>
    <!-- slides -->
  </div>
  ```

  Fail:

  ```html
  <video autoplay loop muted src="hero.mp4"></video>
  <!-- no pause control; plays indefinitely -->
  ```

<a id="wcag-2-2-3"></a>
### WCAG-2.2.3 — No Timing (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#no-timing> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/no-timing.html>

- **Text:**

  > Timing is not an essential part of the event or activity presented by the content, except for non-interactive synchronized media and real-time events.

- **Applies to:** timing, all time limits, timed tests and forms
- **Testability:** manual — No axe-core rule. A static scanner can find timers and `meta refresh`; a page runner can detect timed behaviour. A human confirms that timing is not an essential part of any event or activity except non-interactive synchronized media and real-time events.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. List every time limit in the content.
  2. Confirm each is removed, or that the only remaining limits belong to non-interactive synchronized media or real-time events.
  3. Fail any other time limit, even if it is adjustable.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Quiz that gives a fixed time per question.
  - Pattern: Reservation hold that releases seats after a countdown.
  - Pattern: Form that expires even though the user can extend it.
- **Sufficient techniques:**
  - G5 — Allowing users to complete an activity without any time limit
- **Pass/fail example:**

  Pass:

  ```html
  <form action="/quiz">
    <!-- no timer; users answer at their own pace -->
  </form>
  ```

  Fail:

  ```html
  <p>Time left: <span id="timer">60</span>s</p>
  <script>startCountdown(60, submitQuiz)</script>
  ```

<a id="wcag-2-2-4"></a>
### WCAG-2.2.4 — Interruptions (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#interruptions> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/interruptions.html>

- **Text:**

  > Interruptions can be postponed or suppressed by the user, except interruptions involving an emergency.

- **Applies to:** interruptions, notifications, alerts, auto-updates, chat and push messages
- **Testability:** assisted — axe-core `meta-refresh-no-exceptions` flags any timed refresh. A static scanner can find `role="alert"`, toast libraries and refresh timers; a page runner can observe unrequested interruptions. A human confirms that users can postpone or suppress interruptions except emergencies.
  - **axe-core rules (4.13.0):** `meta-refresh-no-exceptions`
- **Test procedure:**
  1. Identify everything that interrupts the user without being requested: pop-ups, toasts, live alerts, auto-refreshes, promotional overlays.
  2. Check that a setting or control lets the user postpone or turn off each, except emergencies.
  3. Confirm that suppressing interruptions does not lose data the user needs.
- **Common failures:**
  - F40 — Failure due to using meta redirect with a time limit
  - F41 — Failure of Success Criterion 2.2.1, 2.2.4, and 3.2.5 due to using meta refresh to reload the page
  - Pattern: Chat widget that pops open with a message on a timer and cannot be muted.
  - Pattern: `<meta http-equiv="refresh" content="300">` that reloads news pages.
  - Pattern: Frequent non-emergency `role="alert"` toasts with no preference to silence them.
- **Sufficient techniques:**
  - G75 — Providing a mechanism to postpone any updating of content
  - G76 — Providing a mechanism to request an update of the content instead of updating automatically
  - SCR14 — Using scripts to make nonessential alerts optional
- **ACT test rules:** [Meta element has no refresh delay](https://www.w3.org/WAI/standards-guidelines/act/rules/bc659a/); [Meta element has no refresh delay (no exception)](https://www.w3.org/WAI/standards-guidelines/act/rules/bisz58/)
- **Pass/fail example:**

  Pass:

  ```html
  <label><input type="checkbox" id="quiet"> Pause notifications</label>
  ```

  Fail:

  ```html
  <meta http-equiv="refresh" content="120">
  ```

<a id="wcag-2-2-5"></a>
### WCAG-2.2.5 — Re-authenticating (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#re-authenticating> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/re-authenticating.html>

- **Text:**

  > When an authenticated session expires, the user can continue the activity without loss of data after re-authenticating.

- **Applies to:** authentication, sessions, multi-step forms, data preservation
- **Testability:** manual — No axe-core rule. A page runner can expire a session (clearing cookies) mid-task and resubmit to see whether data persists. A human confirms the user can continue the activity without data loss after re-authenticating.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Start a multi-step or data-entry task while signed in.
  2. Let the session expire (or force it) before submitting.
  3. Re-authenticate and confirm that the task continues with all entered data kept.
- **Common failures:**
  - F12 — Failure of Success Criterion 2.2.5 due to having a session time limit without a mechanism … re-authentication
  - Pattern: Session expiry that redirects to login and then to the home page, losing the form.
  - Pattern: Server discards POST data received with an expired token instead of saving it for after sign-in.
- **Sufficient techniques:**
  - G105 — Saving data so that it can be used after a user re-authenticates
  - G181 — Encoding user data as hidden or encrypted data in a re-authorization page
- **Pass/fail example:**

  Pass:

  ```js
  onSessionExpired(() => {
    sessionStorage.setItem('draft', JSON.stringify(formData()));
    showLogin({ returnTo: location.href });
  });
  ```

  Fail:

  ```js
  onSessionExpired(() => { location.href = '/login'; }); // draft lost
  ```

<a id="wcag-2-2-6"></a>
### WCAG-2.2.6 — Timeouts (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#timeouts> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/timeouts.html>

- **Text:**

  > Users are warned of the duration of any user inactivity that could cause data loss, unless the data is preserved for more than 20 hours when the user does not take any actions.
  >
  > *Note:* Privacy regulations may require explicit user consent before user identification has been authenticated and before user data is preserved. In cases where the user is a minor, explicit consent may not be solicited in most jurisdictions, countries or regions. Consultation with privacy professionals and legal counsel is advised when considering data preservation as an approach to satisfy this success criterion.

- **Applies to:** timing, session timeouts, data loss, forms
- **Testability:** manual — No axe-core rule. A static scanner may find timeout configuration; a human confirms that users are told how long inactivity may last before data loss, unless data is kept for more than 20 hours.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify any user inactivity that could cause data loss.
  2. Check that users are warned of the inactivity duration (for example, at the start of the process).
  3. Or confirm that data is kept for more than 20 hours of inactivity.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Application form that silently discards progress after 30 minutes of inactivity with no warning.
  - Pattern: Shopping cart cleared after an unstated idle period.
- **Sufficient techniques** (no numbered techniques; Understanding lists):
  - Setting a session timeout to occur following at least 20 hours of inactivity
  - Storing user data for more than 20 hours
  - Providing a warning of the duration of user inactivity at the start of a process
- **Pass/fail example:**

  Pass:

  ```html
  <p>Your answers are saved for 7 days, even if you leave this page.</p>
  ```

  Fail:

  ```html
  <!-- form discards data after 15 minutes idle; users are not told -->
  <form id="application">...</form>
  ```

## Guideline 2.3 — Seizures and Physical Reactions

> Do not design content in a way that is known to cause seizures or physical reactions.

<a id="wcag-2-3-1"></a>
### WCAG-2.3.1 — Three Flashes or Below Threshold (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#three-flashes-or-below-threshold> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html>

- **Text:**

  > Web pages do not contain anything that flashes more than three times in any one second period, or the flash is below the general flash and red flash thresholds.
  >
  > *Note:* Since any content that does not meet this success criterion can interfere with a user's ability to use the whole page, all content on the web page (whether it is used to meet other success criteria or not) must meet this success criterion. See Conformance Requirement 5: Non-Interference.

- **Applies to:** flashing content, video, animation, games, canvas and WebGL
- **Testability:** assisted — No axe-core rule. A static scanner can flag rapid CSS/JS animation (short `animation-duration` with high-contrast changes) and media; frame analysis tools (for example, PEAT or similar photosensitivity analysers) measure general and red flash thresholds on recorded video. A human confirms flash area and frequency for anything that flashes.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Find any content that flashes (video, animation, games, blinking effects).
  2. Check whether it flashes more than three times in any one-second period.
  3. If it does, measure whether flashes stay below the general and red flash thresholds (for example, with a photosensitive epilepsy analysis tool).
  4. Fail content that flashes more than three times per second above threshold.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: CSS `@keyframes` toggling a large area between black and white with `animation-duration: 0.1s`.
  - Pattern: Promotional video with strobe effects.
  - Pattern: Game that flashes a full-screen red hit effect several times per second.
- **Sufficient techniques:**
  - G19 — Ensuring that no component of the content flashes more than three times in any 1-second period
  - G176 — Keeping the flashing area small enough
  - G15 — Using a tool to ensure that content does not violate the general flash threshold or red flash threshold
- **Pass/fail example:**

  Pass:

  ```css
  .alert { animation: pulse 2s ease-in-out 3; } /* slow, limited */
  ```

  Fail:

  ```css
  .hero { animation: strobe 0.1s steps(2) infinite; }
  @keyframes strobe { 50% { background: #fff; } }
  ```

<a id="wcag-2-3-2"></a>
### WCAG-2.3.2 — Three Flashes (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#three-flashes> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/three-flashes.html>

- **Text:**

  > Web pages do not contain anything that flashes more than three times in any one second period.

- **Applies to:** flashing content, video, animation
- **Testability:** assisted — No axe-core rule. Static and frame-analysis checks as for 2.3.1, but no threshold exception applies: any content flashing more than three times per second fails. A human confirms on the rendered content.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Find all flashing content.
  2. Count flashes in any one-second period.
  3. Fail anything that flashes more than three times per second, regardless of size or contrast.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Small blinking status light at 5 Hz, which passes 2.3.1 by area but fails here.
  - Pattern: Loading spinner that flashes rapidly.
- **Sufficient techniques:**
  - G19 — Ensuring that no component of the content flashes more than three times in any 1-second period
- **Pass/fail example:**

  Pass:

  ```css
  .status { animation: fade 1s ease-in-out infinite; } /* 1 flash per second */
  ```

  Fail:

  ```css
  .status { animation: blink 0.2s steps(2) infinite; } /* 5 flashes per second */
  ```

<a id="wcag-2-3-3"></a>
### WCAG-2.3.3 — Animation from Interactions (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#animation-from-interactions> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html>

- **Text:**

  > Motion animation triggered by interaction can be disabled, unless the animation is essential to the functionality or the information being conveyed.

- **Applies to:** motion animation triggered by interaction, parallax, scroll effects, transitions
- **Testability:** assisted — No axe-core rule. A static scanner can find animations and check whether CSS/JS respects `prefers-reduced-motion`; a page runner can emulate `prefers-reduced-motion: reduce` and compare motion. A human decides whether any remaining motion is essential.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Interact with the page (scroll, click, hover) and note motion animation it triggers.
  2. Check that the user can turn off non-essential motion, via a site setting or by honouring `prefers-reduced-motion`.
  3. Enable reduced motion and confirm the animations stop or are replaced by non-motion effects.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Parallax scrolling with no `@media (prefers-reduced-motion: reduce)` override.
  - Pattern: Page transitions that zoom or slide the whole viewport on every link click.
  - Pattern: JS scroll-triggered animation libraries initialised without checking `matchMedia('(prefers-reduced-motion: reduce)')`.
- **Sufficient techniques:**
  - C39 — Using the CSS prefers-reduced-motion query to prevent motion
  - SCR40 — Using the CSS prefers-reduced-motion query in JavaScript to prevent motion
- **Pass/fail example:**

  Pass:

  ```css
  .panel { transition: transform .4s; }
  @media (prefers-reduced-motion: reduce) {
    .panel { transition: none; }
  }
  ```

  Fail:

  ```css
  .bg { background-attachment: fixed; } /* parallax, no reduced-motion override */
  .panel { transition: transform 1s; }
  ```

## Guideline 2.4 — Navigable

> Provide ways to help users navigate, find content, and determine where they are.

<a id="wcag-2-4-1"></a>
### WCAG-2.4.1 — Bypass Blocks (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#bypass-blocks> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/bypass-blocks.html>

- **Text:**

  > A mechanism is available to bypass blocks of content that are repeated on multiple web pages.

- **Applies to:** navigation, repeated blocks, landmarks, headings, skip links
- **Testability:** assisted — axe-core `bypass` checks that a page has a skip link, a heading or a landmark, but not that it bypasses the right block. A static scanner can check for `<main>` and a skip link whose target exists; a page runner can activate the skip link and confirm focus moves. A human confirms repeated blocks can actually be bypassed.
  - **axe-core rules (4.13.0):** `bypass`
- **Test procedure:**
  1. Identify blocks repeated across pages (header, navigation, sidebars).
  2. Check for a mechanism to skip them: a working skip link, landmarks (`<main>`, `<nav>`), or headings at the start of each section.
  3. Activate the skip link with the keyboard and confirm focus and reading position move past the block.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Skip link `href="#main"` pointing to an id that does not exist.
  - Pattern: Skip link hidden with `display:none` so it never receives focus.
  - Pattern: Pages built only from `<div>` elements with no landmarks or headings.
- **Sufficient techniques:**
  - G1 — Adding a link at the top of each page that goes directly to the main content area
  - G123 — Adding a link at the beginning of a block of repeated content to go to the end of the block
  - G124 — Adding links at the top of the page to each area of the content
  - ARIA11 — Using ARIA landmarks to identify regions of a page
  - H69 — Providing heading elements at the beginning of each section of content
  - PDF9 — Providing headings by marking content with heading tags in PDF documents
  - H64 — Using the title attribute of the iframe element
  - SCR28 — Using an expandable and collapsible menu to bypass block of content
- **ACT test rules:** [Bypass Blocks of Repeated Content](https://www.w3.org/WAI/standards-guidelines/act/rules/cf77f2/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <a class="skip" href="#main">Skip to main content</a>
  <nav>...</nav>
  <main id="main" tabindex="-1">...</main>
  ```

  Fail:

  ```html
  <a href="#content" style="display:none">Skip</a>
  <div class="nav">...</div>
  <div class="content">...</div>
  ```

<a id="wcag-2-4-2"></a>
### WCAG-2.4.2 — Page Titled (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#page-titled> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/page-titled.html>

- **Text:**

  > Web pages have titles that describe topic or purpose.

- **Applies to:** page title, documents, single-page app route changes
- **Testability:** assisted — axe-core `document-title` fails a missing or empty `<title>`; it cannot judge whether the title describes the page. A static scanner can flag duplicate or placeholder titles across templates ("Untitled", "React App"); a page runner can check that the title changes on SPA route changes. A human confirms the title describes topic or purpose.
  - **axe-core rules (4.13.0):** `document-title`
- **Test procedure:**
  1. Check that each page has a `<title>`.
  2. Confirm the title identifies the topic or purpose of the page (unique content first is helpful).
  3. In single-page apps, navigate between views and confirm `document.title` updates.
- **Common failures:**
  - F25 — Failure of Success Criterion 2.4.2 due to the title of a web page not identifying the contents
  - Pattern: Missing or empty `<title>`.
  - Pattern: Every page titled with the site name only, or a framework default such as "React App".
  - Pattern: SPA router that never updates `document.title`.
- **Sufficient techniques:**
  - G88 — Providing descriptive titles for web pages
  - H25 — Providing a title using the title element
  - PDF18 — Specifying the document title using the Title entry in the document information dictionary of a PDF document
- **ACT test rules:** [HTML page has non-empty title](https://www.w3.org/WAI/standards-guidelines/act/rules/2779a5/); [HTML page title is descriptive](https://www.w3.org/WAI/standards-guidelines/act/rules/c4a8a4/)
- **Pass/fail example:**

  Pass:

  ```html
  <title>Shipping address - Checkout - Example Store</title>
  ```

  Fail:

  ```html
  <title>React App</title>
  ```

<a id="wcag-2-4-3"></a>
### WCAG-2.4.3 — Focus Order (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#focus-order> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html>

- **Text:**

  > If a web page can be navigated sequentially and the navigation sequences affect meaning or operation, focusable components receive focus in an order that preserves meaning and operability.

- **Applies to:** focus order, keyboard, dialogs, dynamic content, layout reordering
- **Testability:** assisted — No axe-core rule for order (the `tabindex` best-practice rule is not mapped to this SC). A static scanner can flag positive `tabindex` and CSS reordering (`order`, `flex-direction: row-reverse`, absolute positioning); a page runner can record the Tab sequence and compare it with visual position. A human decides whether the order preserves meaning and operability.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Tab through the page and note the order in which elements receive focus.
  2. Compare it with the visual and logical reading order.
  3. Open dialogs, menus and disclosures and confirm focus moves into them and returns sensibly when closed.
  4. Fail any sequence that changes meaning or makes operation confusing.
- **Common failures:**
  - F44 — Failure of Success Criterion 2.4.3 due to using tabindex to create a tab order that does not preserve meaning and operability
  - F85 — Failure of Success Criterion 2.4.3 due to using dialogs or menus that are not adjacent to their trigger control in the sequential navigation order
  - Pattern: Positive `tabindex` values (`tabindex="3"`) that create an order unrelated to the layout.
  - Pattern: CSS `order` or `flex-direction: row-reverse` making visual order differ from DOM order.
  - Pattern: Modal dialog opened at the end of the DOM with focus left on the trigger behind it.
  - Pattern: Focus sent to the top of the page after closing a dialog or deleting a list item.
- **Sufficient techniques:**
  - G59 — Placing the interactive elements in an order that follows sequences and relationships within the content
  - C27 — Making the DOM order match the visual order
  - PDF3 — Ensuring correct tab and reading order in PDF documents
  - SCR26 — Inserting dynamic content into the Document Object Model immediately following its trigger element
  - H102 — Creating modal dialogs with the HTML dialog element
  - SCR27 — Reordering page sections using the Document Object Model
- **Pass/fail example:**

  Pass:

  ```html
  <label for="first">First name</label><input id="first">
  <label for="last">Last name</label><input id="last">
  ```

  Fail:

  ```html
  <input id="last" tabindex="1">
  <input id="first" tabindex="2">
  <button tabindex="3">Submit</button>
  ```

<a id="wcag-2-4-4"></a>
### WCAG-2.4.4 — Link Purpose (In Context) (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#link-purpose-in-context> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html>

- **Text:**

  > The purpose of each link can be determined from the link text alone or from the link text together with its programmatically determined link context, except where the purpose of the link would be ambiguous to users in general.

- **Applies to:** links, image links, navigation
- **Testability:** assisted — axe-core `link-name` and `area-alt` fail links with no accessible name, but cannot judge purpose. A static scanner can flag vague link text ("click here", "read more", "more") and repeated identical text with different `href`; a page runner can compute accessible names with their programmatic context. A human confirms the purpose is clear from the link text plus its context.
  - **axe-core rules (4.13.0):** `area-alt`, `link-name`
- **Test procedure:**
  1. List all links with their accessible names (for example, with a link list in a screen reader).
  2. For each, check that the purpose is clear from the text alone or with its programmatic context (sentence, paragraph, list item, table cell or header, `aria-describedby`).
  3. Check image links have a text alternative describing the destination.
  4. Fail links whose purpose cannot be worked out, unless it would be ambiguous to all users.
- **Common failures:**
  - F63 — Failure of Success Criterion 2.4.4 due to providing link context only in content that is not related to the link
  - F89 — Failure of Success Criteria 2.4.4, 2.4.9 and 4.1.2 due to not providing an accessible name for an image which is the only content in a link
  - Pattern: Icon-only link `<a href="/cart"><svg>...</svg></a>` with no accessible name.
  - Pattern: Many "Read more" links whose context is not programmatically associated.
  - Pattern: Image link whose `alt` describes the image rather than the destination.
  - Pattern: `<a href="...">here</a>` in a paragraph that does not explain the target.
- **Sufficient techniques:**
  - G91 — Providing link text that describes the purpose of a link
  - H30 — Providing link text that describes the purpose of a link for anchor elements
  - H24 — Providing text alternatives for the area elements of image maps
  - G189 — Providing a control near the beginning of the web page that changes the link text
  - SCR30 — Using scripts to change the link text
  - G53 — Identifying the purpose of a link using link text combined with the text of the enclosing sentence
  - H33 — Supplementing link text with the title attribute
  - C7 — Using CSS to hide a portion of the link text
  - ARIA7 — Using aria-labelledby for link purpose
  - ARIA8 — Using aria-label for link purpose
  - H77 — Identifying the purpose of a link using link text combined with its enclosing list item
  - H78 — Identifying the purpose of a link using link text combined with its enclosing paragraph
  - H79 — Identifying the purpose of a link in a data table using the link text combined with its enclosing table cell and associated table header cells
  - H81 — Identifying the purpose of a link in a nested list using link text combined with the parent list item under which the list is nested
  - PDF11 — Providing links and link text using the Link annotation and the /Link structure element in PDF documents
  - PDF13 — Providing replacement text using the /Alt entry for links in PDF documents
- **ACT test rules:** [Link has non-empty accessible name](https://www.w3.org/WAI/standards-guidelines/act/rules/c487ae/); [Link in context is descriptive](https://www.w3.org/WAI/standards-guidelines/act/rules/5effbb/proposed/); [Links with identical accessible names and same context serve equivalent purpose](https://www.w3.org/WAI/standards-guidelines/act/rules/fd3a94/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <h3 id="a1">Budget report 2025</h3>
  <a href="/r/2025" aria-describedby="a1">Read more</a>
  ```

  Fail:

  ```html
  <a href="/cart"><svg aria-hidden="true">...</svg></a>
  ```

<a id="wcag-2-4-5"></a>
### WCAG-2.4.5 — Multiple Ways (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#multiple-ways> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/multiple-ways.html>

- **Text:**

  > More than one way is available to locate a web page within a set of web pages except where the web page is the result of, or a step in, a process.

- **Applies to:** navigation, site structure, search, sitemaps
- **Testability:** manual — No axe-core rule. A crawler can check that pages are reachable from more than one path (navigation, search, sitemap). A human confirms at least two ways exist to locate each page that is not a step in a process.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify the set of pages in scope.
  2. Check that at least two ways exist to find each page: site navigation, search, site map, table of contents, related links, or links from home.
  3. Exclude pages that are the result of, or a step in, a process.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Content reachable only by following a single path of links, with no search or site map.
  - Pattern: Help articles reachable only through one nested menu.
- **Sufficient techniques:**
  - G125 — Providing links to navigate to related web pages
  - G64 — Providing a Table of Contents
  - G63 — Providing a site map
  - G161 — Providing a search function to help users find content
  - G126 — Providing a list of links to all other web pages
  - G185 — Linking to all of the pages on the site from the home page
- **Pass/fail example:**

  Pass:

  ```html
  <nav aria-label="Main">...</nav>
  <form role="search"><label for="q">Search</label><input id="q" type="search"></form>
  ```

  Fail:

  ```html
  <nav>...</nav>
  <!-- no search, site map or other way to find pages -->
  ```

<a id="wcag-2-4-6"></a>
### WCAG-2.4.6 — Headings and Labels (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#headings-and-labels> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels.html>

- **Text:**

  > Headings and labels describe topic or purpose.

- **Applies to:** headings, labels, forms, page structure
- **Testability:** manual — No axe-core rule decides whether text is descriptive. A static scanner can flag empty headings, generic labels ("Field 1") and duplicate headings; a page runner can list headings and labels. A human judges whether each heading and label describes its topic or purpose.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. List headings on the page and read them out of context.
  2. Check each describes the section that follows.
  3. List visible labels on form fields and controls and check each describes the purpose of the field.
  4. Note: this SC does not require headings or labels to exist, only that those present are descriptive.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Headings such as "Section 1" or "More" that do not describe content.
  - Pattern: Several fields labelled "Name" on one form without distinguishing context.
  - Pattern: Labels that are placeholders such as "Enter text".
- **Sufficient techniques:**
  - G130 — Providing descriptive headings
  - G131 — Providing descriptive labels
- **ACT test rules:** [Form field label is descriptive](https://www.w3.org/WAI/standards-guidelines/act/rules/cc0f0a/proposed/); [Heading is descriptive](https://www.w3.org/WAI/standards-guidelines/act/rules/b49b2e/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <h2>Delivery options</h2>
  <label for="pc">Postcode</label><input id="pc">
  ```

  Fail:

  ```html
  <h2>Section 2</h2>
  <label for="pc">Field</label><input id="pc">
  ```

<a id="wcag-2-4-7"></a>
### WCAG-2.4.7 — Focus Visible (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#focus-visible> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html>

- **Text:**

  > Any keyboard operable user interface has a mode of operation where the keyboard focus indicator is visible.

- **Applies to:** focus, keyboard, focus indicators, CSS styling
- **Testability:** assisted — No axe-core rule. A static scanner can flag `outline: none`/`outline: 0` or `:focus { outline: none }` with no replacement style; a page runner can Tab through the page and compare screenshots or computed styles of each element with and without focus. A human confirms the indicator is visible on every focusable element.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Tab through all interactive elements.
  2. Confirm each shows a visible indicator when it receives keyboard focus.
  3. Check custom components and components inside iframes, and check across themes (for example, dark mode).
- **Common failures:**
  - F55 — Failure of Success Criteria 2.1.1, 2.4.7, 2.4.13, and 3.2.1 due to using script to remove focus when focus is received
  - F78 — Failure of Success Criterion 1.4.11, 2.4.7 and 2.4.13 due to styling element outlines and borders in a way that removes or renders non-visible the visual focus indicator
  - Pattern: Global `*:focus { outline: none; }` reset with no replacement.
  - Pattern: `button:focus { outline: 0 }` in a CSS framework override.
  - Pattern: Focus style only on `:hover`, not `:focus`/`:focus-visible`.
  - Pattern: Focus ring same colour as the background so it cannot be seen.
- **Sufficient techniques:**
  - G149 — Using user interface components that are highlighted by the user agent when they receive focus
  - C15 — Using CSS to change the presentation of a user interface component when it receives focus
  - G165 — Using the default focus indicator for the platform so that high visibility default focus indicators will carry over
  - G195 — Using an author-supplied, visible focus indicator
  - C40 — Creating a two-color focus indicator to ensure sufficient contrast with all components
  - C45 — Using CSS :focus-visible to provide keyboard focus indication
  - SCR31 — Using script to change the background color or border of the element with focus
- **ACT test rules:** [Element in sequential focus order has visible focus](https://www.w3.org/WAI/standards-guidelines/act/rules/oj04fd/)
- **Pass/fail example:**

  Pass:

  ```css
  button:focus-visible {
    outline: 3px solid #1a5fb4;
    outline-offset: 2px;
  }
  ```

  Fail:

  ```css
  *:focus { outline: none; }
  ```

<a id="wcag-2-4-8"></a>
### WCAG-2.4.8 — Location (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#location> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/location.html>

- **Text:**

  > Information about the user's location within a set of web pages is available.

- **Applies to:** navigation, breadcrumbs, site structure, multi-step processes
- **Testability:** manual — No axe-core rule. A static scanner can check for breadcrumbs or `aria-current` in navigation. A human confirms that information about the user's location within a set of pages is available.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Check whether the page shows where the user is within the site or process.
  2. Look for breadcrumbs, a site map, `aria-current` on the current navigation item, or a step indicator.
  3. Confirm the information is available on every page in the set.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Deep content pages with no breadcrumb and no current-item indication in the navigation.
  - Pattern: Multi-step form without a "Step 2 of 4" indicator.
- **Sufficient techniques:**
  - G65 — Providing a breadcrumb trail
  - G63 — Providing a site map
  - G128 — Indicating current location within navigation bars
  - ARIA26 — Using aria-current to identify the current item in a set
  - G127 — Identifying a web page's relationship to a larger collection of web pages
- **Pass/fail example:**

  Pass:

  ```html
  <nav aria-label="Breadcrumb"><ol>
    <li><a href="/">Home</a></li>
    <li><a href="/help">Help</a></li>
    <li aria-current="page">Returns</li>
  </ol></nav>
  ```

  Fail:

  ```html
  <nav><a href="/">Home</a> <a href="/help">Help</a></nav>
  <!-- no indication of current location -->
  ```

<a id="wcag-2-4-9"></a>
### WCAG-2.4.9 — Link Purpose (Link Only) (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#link-purpose-link-only> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-link-only.html>

- **Text:**

  > A mechanism is available to allow the purpose of each link to be identified from link text alone, except where the purpose of the link would be ambiguous to users in general.

- **Applies to:** links, navigation
- **Testability:** assisted — axe-core `identical-links-same-purpose` flags links with the same name but different destinations for review. A static scanner can flag vague link text; a page runner can list link names without context. A human confirms that the purpose of each link is clear from its link text alone.
  - **axe-core rules (4.13.0):** `identical-links-same-purpose`
- **Test procedure:**
  1. List all links by their accessible names only (without surrounding context).
  2. Check each identifies its purpose from the link text alone.
  3. Allow exceptions only where the purpose would be ambiguous to users in general.
- **Common failures:**
  - F84 — Failure of Success Criterion 2.4.9 due to using a non-specific link such as "click here" or "more" without a mechanism to change the link text to specific text.
  - F89 — Failure of Success Criteria 2.4.4, 2.4.9 and 4.1.2 due to not providing an accessible name for an image which is the only content in a link
  - Pattern: "Read more" links that rely on nearby text or `aria-describedby`, which passes 2.4.4 but fails here.
  - Pattern: Identical link text "Download" for different files.
- **Sufficient techniques:**
  - ARIA8 — Using aria-label for link purpose
  - G91 — Providing link text that describes the purpose of a link
  - H30 — Providing link text that describes the purpose of a link for anchor elements
  - H24 — Providing text alternatives for the area elements of image maps
  - G189 — Providing a control near the beginning of the web page that changes the link text
  - SCR30 — Using scripts to change the link text
  - C7 — Using CSS to hide a portion of the link text
  - PDF11 — Providing links and link text using the Link annotation and the /Link structure element in PDF documents
  - PDF13 — Providing replacement text using the /Alt entry for links in PDF documents
- **ACT test rules:** [Link has non-empty accessible name](https://www.w3.org/WAI/standards-guidelines/act/rules/c487ae/); [Link in context is descriptive](https://www.w3.org/WAI/standards-guidelines/act/rules/5effbb/proposed/); [Link is descriptive](https://www.w3.org/WAI/standards-guidelines/act/rules/aizyf1/proposed/); [Links with identical accessible names and same context serve equivalent purpose](https://www.w3.org/WAI/standards-guidelines/act/rules/fd3a94/proposed/); [Links with identical accessible names have equivalent purpose](https://www.w3.org/WAI/standards-guidelines/act/rules/b20e66/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <a href="/r/2025">Read the 2025 budget report</a>
  ```

  Fail:

  ```html
  <p>The 2025 budget report is ready. <a href="/r/2025">Read more</a></p>
  ```

<a id="wcag-2-4-10"></a>
### WCAG-2.4.10 — Section Headings (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#section-headings> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/section-headings.html>

- **Text:**

  > Section headings are used to organize the content.
  >
  > *Note 1:* "Heading" is used in its general sense and includes titles and other ways to add a heading to different types of content.
  >
  > *Note 2:* This success criterion covers sections within writing, not user interface components. User interface components are covered under Success Criterion 4.1.2.

- **Applies to:** headings, page structure, long content
- **Testability:** manual — No axe-core rule. A static scanner can flag long blocks of text with no headings; a page runner can list the heading outline. A human confirms that content is organised under section headings.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Review the content for distinct sections.
  2. Check each section is introduced by a heading.
  3. Confirm the headings are marked up correctly (see 1.3.1).
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Long article with bold paragraphs as visual headings but no heading structure.
  - Pattern: Terms and conditions page with dozens of sections and no headings.
- **Sufficient techniques:**
  - G141 — Organizing a page using headings
  - H69 — Providing heading elements at the beginning of each section of content
- **Pass/fail example:**

  Pass:

  ```html
  <h2>Refunds</h2><p>...</p>
  <h2>Exchanges</h2><p>...</p>
  ```

  Fail:

  ```html
  <p>...refund policy text...</p>
  <p>...exchange policy text...</p>
  <!-- no section headings -->
  ```

<a id="wcag-2-4-11"></a>
### WCAG-2.4.11 — Focus Not Obscured (Minimum) (Level AA) — new in 2.2

Spec: <https://www.w3.org/TR/WCAG22/#focus-not-obscured-minimum> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html>

- **Text:**

  > When a user interface component receives keyboard focus, the component is not entirely hidden due to author-created content.
  >
  > *Note 1:* Where content in a configurable interface can be repositioned by the user, then only the initial positions of user-movable content are considered for testing and conformance of this success criterion.
  >
  > *Note 2:* Content opened by the *user* may obscure the component receiving focus. If the user can reveal the focused component without advancing the keyboard focus, the component with focus is not considered visually hidden due to author-created content.

- **Applies to:** focus, sticky headers and footers, cookie banners, overlays, chat widgets
- **Testability:** assisted — No axe-core rule. A page runner can Tab through the page and, for each focused element, test whether its bounding box is entirely covered by author content (for example, `position: fixed/sticky` headers or banners) using `elementsFromPoint`. A static scanner can flag fixed/sticky elements with no matching `scroll-padding`. A human confirms results, including for user-movable content in its initial position.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Open the page with any sticky header, footer, cookie banner or non-modal dialog in its initial state.
  2. Tab through all interactive elements, scrolling as the browser does.
  3. Check that each focused element is at least partly visible, not entirely hidden by author-created content.
  4. Treat content the user opened and can dismiss without moving focus (for example, with Esc) as not obscuring.
- **Common failures:**
  - F110 — Failure of Success Criterion 2.4.11 Focus Not Obscured (Minimum) due to a sticky footer or header completely hiding focused elements
  - Pattern: `position: sticky` header with no `scroll-padding-top`, so focused links scroll underneath it.
  - Pattern: Cookie consent bar fixed at the bottom covering focused footer links.
  - Pattern: Floating chat widget covering the submit button when it receives focus.
- **Sufficient techniques:**
  - C43 — Using CSS scroll-padding to un-obscure content
- **Pass/fail example:**

  Pass:

  ```css
  header { position: sticky; top: 0; height: 4rem; }
  html { scroll-padding-top: 5rem; }
  ```

  Fail:

  ```css
  header { position: fixed; top: 0; height: 6rem; }
  /* no scroll-padding; focused items scroll under the header */
  ```

<a id="wcag-2-4-12"></a>
### WCAG-2.4.12 — Focus Not Obscured (Enhanced) (Level AAA) — new in 2.2

Spec: <https://www.w3.org/TR/WCAG22/#focus-not-obscured-enhanced> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-enhanced.html>

- **Text:**

  > When a user interface component receives keyboard focus, no part of the component is hidden by author-created content.

- **Applies to:** focus, sticky headers and footers, overlays
- **Testability:** assisted — No axe-core rule. The same page-runner check as 2.4.11, but failing any overlap with author content rather than only total coverage. A human confirms results.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Tab through all interactive elements with sticky and overlay content in place.
  2. Check that no part of each focused component is hidden by author-created content.
  3. Record partial overlaps as failures (they pass 2.4.11 but fail here).
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Sticky header that hides the top half of focused links.
  - Pattern: Fixed footer overlapping the bottom edge of the focused button.
- **Sufficient techniques:**
  - C43 — Using CSS scroll-padding to un-obscure content
- **Pass/fail example:**

  Pass:

  ```css
  html { scroll-padding-top: 5rem; scroll-padding-bottom: 4rem; }
  ```

  Fail:

  ```css
  footer { position: fixed; bottom: 0; height: 3rem; }
  /* focused items near the bottom are partly covered */
  ```

<a id="wcag-2-4-13"></a>
### WCAG-2.4.13 — Focus Appearance (Level AAA) — new in 2.2

Spec: <https://www.w3.org/TR/WCAG22/#focus-appearance> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html>

- **Text:**

  > When the keyboard focus indicator is visible, an area of the focus indicator meets all the following:
  >
  > - is at least as large as the area of a 2 CSS pixel thick perimeter of the unfocused component or sub-component, and
  > - has a contrast ratio of at least 3:1 between the same pixels in the focused and unfocused states.
  >
  > Exceptions:
  >
  > - The focus indicator is determined by the user agent and cannot be adjusted by the author, or
  > - The focus indicator and the indicator's background color are not modified by the author.
  >
  > *Note 1:* What is perceived as the user interface component or sub-component (to determine the perimeter) depends on its visual presentation. The visual presentation includes the component's visible content, border, and component-specific background. It does not include shadow and glow effects outside the component's content, background, or border.
  >
  > *Note 2:* Examples of sub-components that may receive a focus indicator are menu items in an opened drop-down menu, or focusable cells in a grid.
  >
  > *Note 3:* Contrast calculations can be based on colors defined within the technology (such as HTML, CSS, and SVG). Pixels modified by user agent resolution enhancements and anti-aliasing can be ignored.

- **Applies to:** focus indicators, CSS styling, colour contrast
- **Testability:** assisted — No axe-core rule. A page runner can screenshot each element focused and unfocused, and measure the changed-pixel area and its contrast (at least a 2 CSS pixel thick perimeter area, 3:1 between focused and unfocused states). A static scanner can flag thin (`1px`) or low-contrast outlines. A human confirms edge cases such as indicators altered by the author versus the browser default.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Tab to each interactive element.
  2. Measure the focus indicator: its area must be at least as large as a 2 CSS pixel thick perimeter of the unfocused component.
  3. Measure the contrast between the same pixels in focused and unfocused states: at least 3:1.
  4. Exclude indicators determined by the user agent and not changed by the author, and components whose appearance is set by the user agent.
- **Common failures:**
  - F55 — Failure of Success Criteria 2.1.1, 2.4.7, 2.4.13, and 3.2.1 due to using script to remove focus when focus is received
  - F78 — Failure of Success Criterion 1.4.11, 2.4.7 and 2.4.13 due to styling element outlines and borders in a way that removes or renders non-visible the visual focus indicator
  - Pattern: `outline: 1px dotted #999` focus style: too thin and low contrast.
  - Pattern: Focus shown only by a subtle background colour change with less than 3:1 change.
  - Pattern: `box-shadow` focus ring that is clipped by `overflow: hidden` on the parent.
- **Sufficient techniques:**
  - G195 — Using an author-supplied, visible focus indicator
  - C40 — Creating a two-color focus indicator to ensure sufficient contrast with all components
  - C41 — Creating a strong focus indicator within the component
- **Pass/fail example:**

  Pass:

  ```css
  a:focus-visible {
    outline: 2px solid #000;
    outline-offset: 2px;
  }
  ```

  Fail:

  ```css
  a:focus-visible { outline: 1px dotted #bbb; }
  ```

## Guideline 2.5 — Input Modalities

> Make it easier for users to operate functionality through various inputs beyond keyboard.

<a id="wcag-2-5-1"></a>
### WCAG-2.5.1 — Pointer Gestures (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#pointer-gestures> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/pointer-gestures.html>

- **Text:**

  > All functionality that uses multipoint or path-based gestures for operation can be operated with a single pointer without a path-based gesture, unless a multipoint or path-based gesture is essential.
  >
  > *Note:* This requirement applies to web content that interprets pointer actions (i.e., this does not apply to actions that are required to operate the user agent or assistive technology).

- **Applies to:** pointer gestures, touch interfaces, maps, sliders, carousels, custom widgets
- **Testability:** assisted — No axe-core rule. A static scanner can find multi-touch and swipe handlers (`touchstart` with `touches.length > 1`, gesture libraries, `pinch`, `swipe`) and check for sibling buttons; a page runner can list widgets with gesture handlers. A human confirms every multipoint or path-based gesture has a single-pointer alternative.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify functions that use multipoint gestures (pinch, two-finger swipe) or path-based gestures (swipe, drawing a pattern).
  2. Check that each can also be done with a single pointer without a path (tap, click, double-tap, long press), such as buttons.
  3. Confirm any exception is essential (for example, signature capture).
- **Common failures:**
  - F105 — Failure of Success Criterion 2.5.1 due to providing functionality via a path-based gesture without simple pointer alternative
  - Pattern: Map zoom only by pinch, with no + / - buttons.
  - Pattern: Carousel that changes slide only on swipe, with no previous/next buttons.
  - Pattern: Unlock or confirm action that needs a swipe path.
- **Sufficient techniques:**
  - G215 — Providing controls to achieve the same result as path based or multipoint gestures
  - G216 — Providing single point activation for a control slider
- **Pass/fail example:**

  Pass:

  ```html
  <div id="map"></div>
  <button onclick="zoom(1)">Zoom in</button>
  <button onclick="zoom(-1)">Zoom out</button>
  ```

  Fail:

  ```js
  map.addEventListener('touchmove', (e) => {
    if (e.touches.length === 2) pinchZoom(e); // only way to zoom
  });
  ```

<a id="wcag-2-5-2"></a>
### WCAG-2.5.2 — Pointer Cancellation (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#pointer-cancellation> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/pointer-cancellation.html>

- **Text:**

  > For functionality that can be operated using a single pointer, at least one of the following is true:
  >
  > - **No Down-Event:** The down-event of the pointer is not used to execute any part of the function;
  > - **Abort or Undo:** Completion of the function is on the up-event, and a mechanism is available to abort the function before completion or to undo the function after completion;
  > - **Up Reversal:** The up-event reverses any outcome of the preceding down-event;
  > - **Essential:** Completing the function on the down-event is essential.
  >
  > *Note 1:* Functions that emulate a keyboard or numeric keypad key press are considered essential.
  >
  > *Note 2:* This requirement applies to web content that interprets pointer actions (i.e., this does not apply to actions that are required to operate the user agent or assistive technology).

- **Applies to:** pointer events, buttons, custom controls, drag and drop
- **Testability:** assisted — No axe-core rule. A static scanner can flag functions triggered on `mousedown`, `pointerdown` or `touchstart` (React `onMouseDown`, `onPointerDown`) rather than click/up events; a page runner can press the pointer on a control, move away and release to see whether the action fires. A human confirms abort/undo or the essential exception.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Find controls whose function runs on the down-event.
  2. For each, press down on the control, move off it and release; confirm nothing happens (or the action is aborted or can be undone).
  3. Accept down-event activation only when an up-event reverses it (for example, press-and-hold) or it is essential (for example, a piano key).
- **Common failures:**
  - F101 — Failure of Success Criterion 2.5.2 due to activating a control on the down-event
  - Pattern: `onMouseDown={submit}` on a submit or delete button.
  - Pattern: `pointerdown` handler that navigates immediately.
  - Pattern: Custom toggle using `touchstart` to change state.
- **Sufficient techniques:**
  - G210 — Ensuring that drag-and-drop actions can be cancelled
  - G212 — Using native controls to ensure functionality is triggered on the up-event.
- **Pass/fail example:**

  Pass:

  ```jsx
  <button type="button" onClick={deleteItem}>Delete</button>
  ```

  Fail:

  ```jsx
  <button type="button" onMouseDown={deleteItem}>Delete</button>
  ```

<a id="wcag-2-5-3"></a>
### WCAG-2.5.3 — Label in Name (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#label-in-name> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/label-in-name.html>

- **Text:**

  > For user interface components with labels that include text or images of text, the name contains the text that is presented visually.
  >
  > *Note:* A best practice is to have the text of the label at the start of the name.

- **Applies to:** labels, accessible names, buttons, links, form controls, speech input
- **Testability:** assisted — axe-core `label-content-name-mismatch` (experimental) flags names that do not contain the visible text. A static scanner can compare `aria-label` values with the element's visible text content; a page runner can compare computed accessible names with rendered text. A human checks images of text and whether the visible label text appears in the name (preferably at the start).
  - **axe-core rules (4.13.0):** `label-content-name-mismatch(experimental)`
- **Test procedure:**
  1. List components that have a visible text label (including text in images of text).
  2. Compare each accessible name with the visible label.
  3. Confirm the name contains the visible label text (best practice: it starts with it).
  4. Test with speech input by saying the visible label and confirming activation.
- **Common failures:**
  - F96 — Failure due to the accessible name not containing the visible label text
  - F111 — Failure of Success Criteria 1.3.1, 2.5.3, and 4.1.2 due to a control with visible label text but no accessible name
  - Pattern: `<button aria-label="Submit form">Send</button>`: visible "Send" is not in the name.
  - Pattern: Link with visible "Read more" and `aria-label="Article details"`.
  - Pattern: Input labelled visibly "Email" but `aria-labelledby` pointing to hint text only.
- **Sufficient techniques:**
  - G208 — Including the text of the visible label as part of the accessible name
  - G211 — Matching the accessible name to the visible label
- **ACT test rules:** [Form field has non-empty accessible name](https://www.w3.org/WAI/standards-guidelines/act/rules/e086e5/); [Visible label is part of accessible name](https://www.w3.org/WAI/standards-guidelines/act/rules/2ee8b8/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <button aria-label="Send message">Send</button>
  ```

  Fail:

  ```html
  <button aria-label="Submit form">Send</button>
  ```

<a id="wcag-2-5-4"></a>
### WCAG-2.5.4 — Motion Actuation (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#motion-actuation> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/motion-actuation.html>

- **Text:**

  > Functionality that can be operated by device motion or user motion can also be operated by user interface components and responding to the motion can be disabled to prevent accidental actuation, except when:
  >
  > - **Supported Interface:** The motion is used to operate functionality through an accessibility supported interface;
  > - **Essential:** The motion is essential for the function and doing so would invalidate the activity.

- **Applies to:** device motion, shake, tilt, gestures toward the camera, mobile web apps
- **Testability:** assisted — No axe-core rule. A static scanner can flag `devicemotion`, `deviceorientation` and accelerometer or gyroscope APIs; a human confirms that each motion-triggered function has a UI alternative and can be turned off to prevent accidental activation.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Find functions operated by moving the device or by user motion (shake to undo, tilt to scroll).
  2. Check that each can also be operated by standard UI controls.
  3. Check that motion response can be disabled.
  4. Allow exceptions only for accessibility-supported interfaces or where motion is essential.
- **Common failures:**
  - F106 — Failure due to inability to deactivate motion actuation
  - Pattern: `window.addEventListener('devicemotion', undoOnShake)` with no undo button.
  - Pattern: Tilt-to-scroll gallery with no scroll controls and no off switch.
- **Sufficient techniques:**
  - G213 — Provide conventional controls and an application setting for motion activated input
- **ACT test rules:** [Device motion based changes to the content can also be created from the user interface](https://www.w3.org/WAI/standards-guidelines/act/rules/7677a9/proposed/); [Device motion based changes to the content can be disabled](https://www.w3.org/WAI/standards-guidelines/act/rules/c249d5/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <button onclick="undo()">Undo</button>
  <label><input type="checkbox" id="shake"> Shake to undo</label>
  ```

  Fail:

  ```js
  window.addEventListener('devicemotion', (e) => {
    if (isShake(e)) undo(); // only way to undo; cannot be turned off
  });
  ```

<a id="wcag-2-5-5"></a>
### WCAG-2.5.5 — Target Size (Enhanced) (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#target-size-enhanced> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html>

- **Text:**

  > The size of the target for pointer inputs is at least 44 by 44 CSS pixels except when:
  >
  > - **Equivalent:** The target is available through an equivalent link or control on the same page that is at least 44 by 44 CSS pixels;
  > - **Inline:** The target is in a sentence or block of text;
  > - **User Agent Control:** The size of the target is determined by the user agent and is not modified by the author;
  > - **Essential:** A particular presentation of the target is essential to the information being conveyed.

- **Applies to:** pointer targets, buttons, links, icons, touch interfaces
- **Testability:** assisted — No axe-core rule for 44 px (axe `target-size` checks the 24 px minimum). A page runner can measure every target's bounding box against 44 by 44 CSS pixels; a human confirms the equivalent, inline, user-agent and essential exceptions.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Measure the size of each pointer target.
  2. Check each is at least 44 by 44 CSS pixels.
  3. Exclude targets with an equivalent large target on the same page, inline targets in sentences or blocks of text, unmodified user-agent controls, and essential presentations.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Icon buttons at 32 by 32 pixels.
  - Pattern: Pagination links at 20 by 20 pixels.
  - Pattern: Close "x" on dialogs sized to the glyph.
- **Sufficient techniques:**
  - C44 — Using CSS to ensure targets are at least 44 by 44 CSS pixels
- **Pass/fail example:**

  Pass:

  ```css
  .icon-btn { min-width: 44px; min-height: 44px; }
  ```

  Fail:

  ```css
  .icon-btn { width: 24px; height: 24px; padding: 0; }
  ```

<a id="wcag-2-5-6"></a>
### WCAG-2.5.6 — Concurrent Input Mechanisms (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#concurrent-input-mechanisms> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/concurrent-input-mechanisms.html>

- **Text:**

  > Web content does not restrict use of input modalities available on a platform except where the restriction is essential, required to ensure the security of the content, or required to respect user settings.

- **Applies to:** input modalities, touch, mouse, keyboard, stylus
- **Testability:** manual — No axe-core rule. A static scanner can flag code that disables input types based on detection (for example, removing mouse handlers when `ontouchstart` exists or using `pointerType` checks to ignore input). A human confirms the content does not restrict input methods available on the platform.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. On a device with several input methods (for example, a touchscreen laptop), use the content with each: touch, mouse, keyboard.
  2. Switch between methods partway through tasks.
  3. Fail content that blocks a method except where essential, needed for security, or needed to respect user settings.
- **Common failures:**
  - F98 — Failure due to interactions being limited to touch-only on touchscreen devices
  - Pattern: `if ('ontouchstart' in window) disableMouseHandlers()`.
  - Pattern: Handler that ignores events with `e.pointerType === 'mouse'` on touch-capable devices.
- **Sufficient techniques** (no numbered techniques; Understanding lists):
  - Only using high-level, input-agnostic event handlers, such as focus, blur, click, in Javascript (Potential future technique)
  - Registering event handlers for keyboard/keyboard-like and pointer inputs simultaneously in Javascript; see Example 1 in Pointer Events Level 2 (Potential future technique)
- **Pass/fail example:**

  Pass:

  ```js
  el.addEventListener('click', activate); // works for mouse, touch, pen and keyboard
  ```

  Fail:

  ```js
  if ('ontouchstart' in window) {
    el.addEventListener('touchend', activate); // mouse and keyboard ignored
  } 
  ```

<a id="wcag-2-5-7"></a>
### WCAG-2.5.7 — Dragging Movements (Level AA) — new in 2.2

Spec: <https://www.w3.org/TR/WCAG22/#dragging-movements> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html>

- **Text:**

  > All functionality that uses a dragging movement for operation can be achieved by a single pointer without dragging, unless dragging is essential or the functionality is determined by the user agent and not modified by the author.
  >
  > *Note:* This requirement applies to web content that interprets pointer actions (i.e., this does not apply to actions that are required to operate the user agent or assistive technology).

- **Applies to:** dragging movements, drag and drop, sortable lists, sliders, maps, kanban boards
- **Testability:** assisted — No axe-core rule. A static scanner can find drag handlers (`draggable="true"`, `dragstart`, drag-and-drop libraries, pointer move handlers) and check whether alternative buttons exist; a page runner can list drag-capable elements. A human confirms every dragging function can be achieved with single-pointer actions without dragging (keyboard alternatives alone do not satisfy this SC).
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Find each function that uses dragging (reorder, move, resize, slide, pan).
  2. Check that each can also be done with single-pointer actions without dragging, such as taps or clicks on buttons, a menu, or clicking a target position.
  3. Confirm a keyboard-only alternative is not being counted as the only alternative.
  4. Allow exceptions only where dragging is essential or the behaviour is set by the user agent and not modified by the author.
- **Common failures:**
  - F108 — Failure of Success Criterion 2.5.7 Dragging Movements due to not providing a single pointer method that does not require a dragging movement
  - Pattern: Sortable list reorderable only by drag, with no move up/down buttons or menu.
  - Pattern: Custom range slider whose thumb must be dragged, and clicking the track does nothing.
  - Pattern: Kanban board moving cards only by drag.
- **Sufficient techniques:**
  - G219 — Ensuring that an alternative is available for dragging movements that operate on content
- **Pass/fail example:**

  Pass:

  ```html
  <li draggable="true">Task A
    <button aria-label="Move Task A up">&#8593;</button>
    <button aria-label="Move Task A down">&#8595;</button>
  </li>
  ```

  Fail:

  ```html
  <li draggable="true" ondragstart="startMove(event)">Task A</li>
  <!-- no single-pointer way to reorder -->
  ```

<a id="wcag-2-5-8"></a>
### WCAG-2.5.8 — Target Size (Minimum) (Level AA) — new in 2.2

Spec: <https://www.w3.org/TR/WCAG22/#target-size-minimum> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html>

- **Text:**

  > The size of the target for pointer inputs is at least 24 by 24 CSS pixels, except when:
  >
  > - **Spacing:** Undersized targets (those less than 24 by 24 CSS pixels) are positioned so that if a 24 CSS pixel diameter circle is centered on the bounding box of each, the circles do not intersect another target or the circle for another undersized target;
  > - **Equivalent:** The function can be achieved through a different control on the same page that meets this criterion;
  > - **Inline:** The target is in a sentence or its size is otherwise constrained by the line-height of non-target text;
  > - **User Agent Control:** The size of the target is determined by the user agent and is not modified by the author;
  > - **Essential:** A particular presentation of the target is essential or is legally required for the information being conveyed.
  >
  > *Note 1:* Targets that allow for values to be selected spatially based on position within the target are considered one target for the purpose of the success criterion. Examples include sliders, color pickers displaying a gradient of colors, or editable areas where you position the cursor.
  >
  > *Note 2:* For inline targets the line-height should be interpreted as perpendicular to the flow of text. For example, in a language displayed vertically, the line-height would be horizontal.

- **Applies to:** pointer targets, buttons, links, icons, form controls, touch interfaces
- **Testability:** assisted — axe-core `target-size` measures targets against 24 by 24 CSS pixels and the spacing offset, but it cannot always judge the equivalent, inline and essential exceptions. A page runner can measure each target's bounding box and apply the 24 CSS pixel diameter circle spacing test; a static scanner can flag small fixed `width`/`height` on buttons and icon links. A human confirms exceptions.
  - **axe-core rules (4.13.0):** `target-size`
- **Test procedure:**
  1. Measure each pointer target's bounding box.
  2. For targets smaller than 24 by 24 CSS pixels, centre a 24 CSS pixel circle on each and check that it does not intersect another target or another undersized target's circle.
  3. Exclude targets that have an equivalent control meeting the SC, inline targets in sentences, unmodified user-agent controls, and essential or legally required presentations.
  4. Record remaining undersized, crowded targets as failures.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Icon buttons at 16 by 16 pixels placed side by side with no gap.
  - Pattern: Pagination or star-rating controls at 18 pixels with 2 pixel gaps.
  - Pattern: Close button sized to the glyph (`width: 12px`).
  - Pattern: Checkbox restyled smaller than the browser default with `appearance: none; width: 14px`.
- **Sufficient techniques:**
  - C42 — Using min-height and min-width on target container to ensure sufficient target spacing
- **Pass/fail example:**

  Pass:

  ```css
  .toolbar button { min-width: 24px; min-height: 24px; }
  .toolbar { display: flex; gap: 8px; }
  ```

  Fail:

  ```css
  .toolbar button { width: 16px; height: 16px; padding: 0; }
  .toolbar { display: flex; gap: 0; }
  ```
