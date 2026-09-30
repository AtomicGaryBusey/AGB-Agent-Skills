# Manual checks

> **Attribution.** SC numbers, names and levels are from *Web Content Accessibility Guidelines (WCAG) 2.2*,
> W3C Recommendation, 12 December 2024 edition, <https://www.w3.org/TR/WCAG22/>. Copyright © 2024 World Wide
> Web Consortium, <https://www.w3.org/copyright/document-license-2023/>. No SC text is quoted here; the verbatim
> text is in `sc-1-perceivable.md` … `sc-4-robust.md`. These procedures are original to this skill. See `NOTICE`.

Tools give partial signal on about half of the AA SC and judge none of them fully. Work through each area below
for every page state and process step in scope. Each step names the SC it decides. Record the result per SC
(Pass, Fail, N/A, Not evaluated) and turn failures into Findings rows with the evidence you saw or heard. The
per-SC **Test procedure** in the `sc-*.md` files is the authority when this list is shorter.

Setup: a desktop browser with zoom and dev tools, one screen reader (see the matrix in `workflow.md`), a
contrast checker, and a phone or a narrow window. Turn off any browser extension that changes focus or styles.

## 1. Keyboard-only walkthrough (2.1.1, 2.1.2, 2.1.4, 2.4.3, 2.4.7, 2.4.11, 3.2.1)

1. Put the mouse away. From the address bar, press Tab through the whole page, then Shift+Tab back.
2. Every function you can do with a mouse must be reachable and operable: links (Enter), buttons (Enter and
   Space), checkboxes (Space), radios and tabs (arrow keys), selects, menus, sliders, date pickers, carousels,
   drag-and-drop alternatives, video controls. **2.1.1.**
3. Open every widget: menus, dialogs, accordions, tooltips, comboboxes. Focus must be able to leave each one
   with standard keys (Tab, Shift+Tab, Escape); a non-standard exit must be announced. Test embedded iframes,
   rich-text editors and video players. **2.1.2.** A native date or time input (`type` `date`, `time`,
   `datetime-local`, `month`, `week`) takes one Tab per segment (and sometimes a picker button) before focus
   leaves: that is not a trap. Focus the input and count the Tabs until focus reaches the next control; then
   Shift+Tab back out. A fixed count that ends outside the input passes.
4. Focus order follows the meaning and operation of the page. A dialog moves focus in; closing it returns focus
   to the trigger. Content inserted after a trigger comes next in order. **2.4.3.**
5. A visible focus indicator on every focused element, including custom widgets and links in dark areas.
   **2.4.7.** (Indicator size and 3:1 change are 2.4.13, AAA.)
6. With every sticky header, footer, cookie banner and chat widget in its initial state, no focused element is
   **entirely** hidden. Scroll back to the top and repeat with the banner open. **2.4.11.**
7. Receiving focus alone never submits a form, opens a new window, or moves focus elsewhere. **3.2.1.**
8. Single-character shortcuts (letters, digits, punctuation without Ctrl/Alt/Cmd): each can be turned off,
   remapped, or works only while its component has focus. Test by typing in a text field and on the page body.
   **2.1.4.**
9. Skip link or landmarks/headings let you bypass repeated navigation. **2.4.1.**

## 2. Screen reader smoke test (1.1.1, 1.3.1, 1.3.2, 2.4.2, 2.4.4, 2.4.6, 2.5.3, 3.1.1, 3.1.2, 4.1.2, 4.1.3)

1. Page title is announced and describes the page or step ("Checkout: payment (2 of 4)"). **2.4.2.**
2. Language: text in another language is read with the right voice; the page default is correct. **3.1.1, 3.1.2.**
3. Headings list: all visual headings are present at sensible levels, and they describe their sections.
   **1.3.1, 2.4.6.**
4. Landmarks list: header, nav, main, footer, and named regions match the visual layout. **1.3.1.**
5. Read the page linearly: order makes sense; no hidden or off-screen text reads out of place; decorative
   images are silent; informative images give their meaning; complex images (charts) have a text equivalent.
   **1.1.1, 1.3.2.**
6. Links list: each link's purpose is clear from its name plus context. **2.4.4.**
7. Every control announces a name, a role, and its state or value (expanded/collapsed, checked, selected,
   pressed, current page, invalid, required, value of a slider). Change the state and listen for the new
   state. **4.1.2.**
8. Controls with visible text: the spoken name contains the visible words (voice-control users say what they
   see). **2.5.3.**
9. Tables: headers announced with each data cell. Forms: groups announce their legend. Lists announce item
   counts where they are visual lists. **1.3.1.**
10. Status messages (search results count, "added to cart", "saved", progress, inline form errors after
    submit) are announced without focus moving. **4.1.3.** Content the user asked for (next slide, "Show
    more", a tab panel) is not a status message; check its controls under 4.1.2 instead.

## 3. Forms, labels and errors (1.3.1, 1.3.5, 3.2.2, 3.3.1, 3.3.2, 3.3.3, 3.3.4, 3.3.7)

1. Every field has a visible label or instructions, including required-field and format hints before input.
   **3.3.2.** The label is programmatically linked (click the label: the field gets focus). **1.3.1.**
2. Fields about the user themselves (name, email, phone, address, birthday, credit-card name) carry the right
   `autocomplete` token. **1.3.5.**
3. Changing a select, radio, checkbox or text field does not submit, navigate or move focus unless the user
   was told beforehand. **3.2.2.**
4. Submit empty, then with invalid values. Each error identifies the field and describes the problem in text
   (not colour or an icon only). **3.3.1.** Where a correction is known, the message suggests it ("Use the
   format DD/MM/YYYY") unless that would compromise security. **3.3.3.**
5. Errors are announced (focus moves to an error summary, or a live region speaks), and each invalid field
   exposes `aria-invalid` or equivalent with the message linked by `aria-describedby`. **4.1.2, 4.1.3.**
6. Legal commitments, payments, test answers, and changes or deletions of user data are reversible, checked
   with a chance to correct, or confirmed before final submission. **3.3.4.**
7. In a multi-step process, information entered earlier (shipping address, email) is filled in or offered as
   an option on later steps. Exceptions: essential, security, or the earlier value is no longer valid.
   **3.3.7.**

## 4. Contrast edge cases (1.4.1, 1.4.3, 1.4.11)

1. Text over images, gradients, video and semi-transparent layers: measure the lightest and darkest area
   behind the glyphs. **1.4.3.** When a tool samples a box around the text, pick colours from the pixels
   directly behind and between the letters. Map lines, icons or borders that cross the box are not the text
   background.
2. States: hover, focus, visited, selected, error, and placeholder text. Disabled controls are exempt; logos
   and brand names are exempt (a pale logo can be an Advisory). **1.4.3.**
3. Non-text: input boundaries (when needed to find the field), checkbox and radio marks, toggle positions, icon
   buttons without text, focus indicators, and chart parts needed to understand the chart, each 3:1 against
   adjacent colours. **1.4.11.**
4. Colour is not the only way to show links in text (underline, or 3:1 against surrounding text plus a
   non-colour cue on hover and focus), errors, required fields, or chart series. **1.4.1.**

## 5. Zoom, reflow and text spacing (1.3.4, 1.4.4, 1.4.5, 1.4.10, 1.4.12, 1.4.13)

1. Browser zoom to 200%: all text resizes, and nothing is cut off, overlaps, or loses function. **1.4.4.**
2. Viewport 1280 px wide at 400% zoom (or a 320 CSS px wide window): content reflows into one column with no
   horizontal scrolling, except two-dimensional content (data tables, maps, diagrams, toolbars). Test
   horizontal text at 256 CSS px high as well. Menus, dialogs and sticky elements still work. **1.4.10.**
3. Apply the text-spacing bookmarklet or user style (line height 1.5, paragraph spacing 2× font size, letter
   spacing 0.12×, word spacing 0.16×): no text is clipped or hidden, no buttons lose their labels. **1.4.12.**
4. Content that appears on hover or focus (custom tooltips, menus, popovers): it can be dismissed with Escape
   without moving the pointer or focus, the pointer can move onto it without it vanishing, and it stays until
   dismissed or no longer relevant. **1.4.13.**
5. Rotate a device or emulator: the page works in both portrait and landscape unless one orientation is
   essential. **1.3.4.**
6. Text shown as an image (banners, buttons, headings as images) is real text unless customisable or
   essential (logos). **1.4.5.**

## 6. Media (1.2.1 – 1.2.5, 1.4.2, 2.2.2)

1. Prerecorded video with sound: accurate, synchronised captions, including speaker names and meaningful
   sounds. **1.2.2.** Live video with sound: live captions. **1.2.4.**
2. Prerecorded video: important visual information that the soundtrack does not describe is in an audio
   description track (AA) or a text alternative (A only). **1.2.3, 1.2.5.**
3. Audio-only: a transcript. Video-only: a transcript or an audio track describing it. **1.2.1.**
4. Audio that plays automatically for more than 3 s can be paused or muted independently of system volume.
   **1.4.2.**
5. A media alternative for text (a video that repeats the page text) is labelled as such; it needs no
   captions or description beyond that.

## 7. Motion, timing and auto-updating content (2.2.1, 2.2.2, 2.3.1, 2.5.4)

1. Time limits (session timeouts, timed forms, auto-advancing steps): the user can turn off, adjust (to at
   least 10×), or extend (warned 20 s before, with a simple action, at least 10 times). Exempt: real-time events,
   essential limits, limits over 20 hours. **2.2.1.**
2. Moving, blinking or scrolling content that starts by itself, lasts more than 5 s, and appears beside other
   content (carousels, tickers, animated backgrounds): pause, stop or hide control. Auto-updating content (news
   feeds, stock tickers): pause, stop, hide, or control the frequency. **2.2.2.**
3. Nothing flashes more than three times in any one second, unless below the general and red flash thresholds
   (use a flash analysis tool on video). **2.3.1.**
4. Functions triggered by device motion (shake, tilt) also work with a UI control, and motion can be turned
   off. **2.5.4.**

## 8. Pointer input, dragging and target size (2.5.1, 2.5.2, 2.5.7, 2.5.8)

1. Multipoint gestures (pinch, two-finger swipe) and path-based gestures (swipe a carousel) have a
   single-pointer alternative without a path (buttons). **2.5.1.**
2. Press the pointer on a control, move off it, release: the action does not fire, or it can be undone.
   Actions fire on the up-event by default. **2.5.2.**
3. Every drag action (reorder a list, move a card, resize a panel, a slider thumb, a map pan) has a
   single-pointer alternative: buttons, click-then-click, or a menu. Keyboard support alone does not satisfy
   this. Exempt: essential dragging and user-agent controls. **2.5.7.**
4. Targets under 24×24 CSS px: check the exceptions in order. Spacing: a 24 px circle centred on each
   undersized target touches no other target and no other undersized target's circle. Equivalent: another
   control on the page does the same thing and meets the size. Inline: the link sits in a sentence or its size
   is set by the line height of surrounding text. User agent: native control not restyled. Essential:
   presentation is essential or legally required. Only targets that meet none of these fail. **2.5.8.**

## 9. Authentication (3.3.8; 3.3.9 at AAA)

Walk every login, sign-up, password reset, step-up and re-authentication step.

1. List each cognitive function test: remembering a password or username, transcribing a one-time code,
   solving a puzzle, a text CAPTCHA, typing characters from an image, doing arithmetic.
2. Each test must have at least one of: another method that is not such a test (passkey, email link, SSO), a
   mechanism that helps (password-manager autofill works, paste works in password and code fields, a copy
   button next to the code), object recognition, or recognition of personal content the user provided.
3. Paste into every password and one-time-code field; try a password manager's autofill. Split code boxes
   (one digit per box) must accept a pasted full code.
4. CAPTCHA: note the type and whether an alternative exists. An image-object CAPTCHA passes AA but fails
   3.3.9 (AAA); a distorted-text CAPTCHA with no alternative fails 3.3.8.

## 10. Consistent navigation, identification and help (2.4.5, 3.2.3, 3.2.4, 3.2.6)

Compare at least three pages of the same set (for example home, a content page, a form step).

1. Two or more ways to find each page, except pages that are the result of or a step in a process (checkout
   steps, confirmation pages, search results). Ways: site-wide navigation reaching every page, a home page
   linking to every page, a site map, search, a table of contents, related-page links. A site of three or four
   pages with every page linked to and from the home page can pass. **2.4.5.**
2. Repeated navigation appears in the same relative order on each page (items may be added or hidden, not
   reordered). **3.2.3.**
3. Components with the same function have the same name, icon and text across pages (a search button is not
   "Find" on one page and "Go" on another). **3.2.4.**
4. If a help mechanism (contact details, a contact form or chat, a help page link, a self-help option)
   appears on several pages, it is in the same order relative to other content each time. Help does not have
   to exist. Compare pages at the same breakpoint, zoom and orientation. Include every step of each
   multi-step process: help that moves on one step (header to footer) fails. **3.2.6.**

## 11. Structure and wording (1.3.1, 1.3.3, 2.4.6, 3.3.2)

1. Instructions do not rely only on shape, size, visual position, orientation or sound ("click the round
   button on the right"). **1.3.3.**
2. Visual groups (fieldsets, card lists, data tables, quotes, emphasis that carries meaning) have matching
   markup. **1.3.1.**
3. Headings and labels describe their topic or purpose. **2.4.6.**

## Recording

If no screen reader was used, section 2 stays open: see `workflow.md` Step 6 for the Assumptions wording.

For each area, list the SC it covers with a result. Put open items (no access to a step, no AT available)
under "Manual checks required" with the reason, and never mark them Pass. In the Evidence cell of a finding,
give the observed fact: keystrokes and what happened, the screen reader and browser with the exact
announcement, the measured size or ratio, the zoom level and viewport.
