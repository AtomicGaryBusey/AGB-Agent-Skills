import json, os

def e(applies, testability, tools, procedure, patterns, pass_, fail):
    return {"applies": applies, "testability": testability, "tools": tools,
            "procedure": procedure, "patterns": patterns,
            "pass": {"lang": pass_[0], "code": pass_[1]},
            "fail": {"lang": fail[0], "code": fail[1]}}

D = {}

D["2.1.1"] = e(
    "keyboard, interactive controls, custom widgets, navigation, forms, media players",
    "assisted",
    "axe-core flags `scrollable-region-focusable`, `frame-focusable-content` and `server-side-image-map`, but cannot tell whether a custom widget really responds to keys. A static scanner can flag click handlers on non-focusable elements (`<div onClick>` without `tabindex`/`onKeyDown`), `tabindex=\"-1\"` on controls and mouse-only events; a page runner can walk the Tab order and compare it with the set of clickable elements. A human must operate every function with the keyboard alone.",
    ["Unplug or ignore the mouse and reach every interactive element with Tab/Shift+Tab.",
     "Activate each control with the keys its role implies (Enter, Space, arrow keys, Esc).",
     "Complete every task end to end (menus, dialogs, drag-and-drop, sliders, carousels, forms) with the keyboard only.",
     "Confirm that a keyboard alternative exists for any path-dependent or mouse-only interaction, and that no function needs specific keystroke timing.",
     "Record each function that is unreachable or not operable as a failure."],
    ["Clickable `<div>`/`<span>` with an `onclick` handler and no `tabindex=\"0\"` or key handler.",
     "`<a>` without `href` used as a button, so it is not in the Tab order.",
     "Functions exposed only on `mouseover`/`hover` (for example, row actions that appear only on hover).",
     "Drag-and-drop reordering or map panning with no keyboard equivalent.",
     "React component that calls `e.preventDefault()` on `keydown` for all keys, blocking native activation."],
    ("html", "<button type=\"button\" class=\"card-action\" onclick=\"openDetails()\">\n  View details\n</button>"),
    ("html", "<div class=\"card-action\" onclick=\"openDetails()\">\n  View details\n</div>"))

D["2.1.2"] = e(
    "keyboard, focus, modals and dialogs, embedded content (iframes, plugins, editors), custom widgets",
    "assisted",
    "No axe-core rule decides this. A page runner can press Tab repeatedly and detect focus cycling inside a small set of elements or never leaving an iframe or editor; a static scanner can flag `keydown` handlers that call `preventDefault()` on Tab. A human confirms whether any documented non-standard exit method is announced to users.",
    ["Tab into every component, including embedded frames, rich-text editors, video players and dialogs.",
     "Try to move focus out with Tab, Shift+Tab and, for dialogs, Esc.",
     "If only a non-standard key sequence exits, check that the page tells users about it before they enter.",
     "Record any component that holds focus with no advised way out as a failure."],
    ["Custom focus-trap code in a non-modal widget that wraps Tab back to its first element forever.",
     "Rich-text editor or code editor that consumes Tab with no documented escape key (for example, Esc then Tab).",
     "Third-party `<iframe>` or plugin that captures keyboard focus.",
     "Modal dialog that traps focus and has no close button reachable by keyboard or Esc handling."],
    ("html", "<textarea id=\"code\" aria-describedby=\"code-help\"></textarea>\n<p id=\"code-help\">Tab inserts an indent. Press Esc, then Tab, to leave the editor.</p>"),
    ("js", "editor.addEventListener('keydown', (e) => {\n  if (e.key === 'Tab') { e.preventDefault(); insertIndent(); }\n  // no key is provided to leave the editor\n});"))

D["2.1.3"] = e(
    "keyboard, all functionality including path-dependent input",
    "manual",
    "axe-core maps `scrollable-region-focusable` here, which covers only one symptom. Static and runner checks are the same as for 2.1.1, but without the path-dependent exception a human must confirm every function (including freehand drawing or gesture paths) has a keyboard method.",
    ["Perform the full 2.1.1 keyboard test.",
     "List any function that 2.1.1 excused because it depends on the path of the user's movement.",
     "Check that each such function also has a keyboard method (for example, nudging with arrow keys or entering coordinates).",
     "Fail any function with no keyboard method, with no exception."],
    ["Freehand drawing canvas with no keyboard way to create shapes or strokes.",
     "Signature pad that accepts only pointer input with no typed-signature alternative.",
     "Game or map that needs continuous pointer movement."],
    ("html", "<canvas id=\"sketch\" aria-label=\"Drawing area\"></canvas>\n<p>Use arrow keys to move the pen, Space to toggle drawing.</p>"),
    ("html", "<canvas id=\"sketch\" onpointermove=\"draw(event)\"></canvas>\n<!-- no keyboard method to draw -->"))

D["2.1.4"] = e(
    "keyboard shortcuts, single-character key bindings, web apps with hotkeys",
    "assisted",
    "No axe-core rule. A static scanner can find `keydown`/`keypress` listeners that react to a single printable character with no modifier check (for example, `if (e.key === 's')`); a page runner can type single letters with focus on the body and watch for actions. A human confirms whether a setting exists to turn off or remap the shortcut, or that it is active only when the component has focus.",
    ["Find every keyboard shortcut in the content (documentation, help menus, source).",
     "Identify shortcuts that use only a letter, number, punctuation or symbol key, without Ctrl/Alt/Cmd.",
     "Check that each such shortcut can be turned off, can be remapped to include a modifier, or works only while its component has focus.",
     "Test with speech input or by typing text elsewhere on the page to confirm no unintended actions fire."],
    ["Global `document.addEventListener('keydown', ...)` that triggers delete, archive or send on a single letter.",
     "React `useHotkeys('j', next)` bound at app level with no settings toggle.",
     "Shortcut handler that does not check `e.ctrlKey`/`e.metaKey`/`e.altKey`."],
    ("js", "document.addEventListener('keydown', (e) => {\n  if (settings.shortcutsEnabled && e.altKey && e.key === 'a') archive();\n});"),
    ("js", "document.addEventListener('keydown', (e) => {\n  if (e.key === 'a') archive(); // fires while dictating or typing\n});"))

D["2.2.1"] = e(
    "timing, session timeouts, auto-advancing content, redirects, timed forms",
    "assisted",
    "axe-core `meta-refresh` flags `<meta http-equiv=\"refresh\">` with a delay. A static scanner can flag `setTimeout` redirects, session-expiry code and short `meta refresh` values; a page runner can wait on the page and detect navigation or expiry dialogs. A human confirms whether users can turn off, adjust or extend each limit (at least 10 times the default or with a 20-second warning).",
    ["List every time limit set by the content: session timeouts, auto-redirects, timed questions, auto-advancing slides.",
     "For each, check that the user can turn it off, adjust it to at least ten times the default, or is warned and can extend it with a simple action (at least 20 seconds to respond, at least ten times).",
     "Confirm whether a real-time event, an essential limit or a limit over 20 hours applies instead.",
     "Record any limit with none of these options as a failure."],
    ["`<meta http-equiv=\"refresh\" content=\"30; url=/logout\">` with no user control.",
     "Session expiry that logs the user out silently with no warning dialog.",
     "Carousel that auto-advances content the user needs to read, with no pause control (also 2.2.2).",
     "Checkout that times out in a few minutes and cannot be extended."],
    ("html", "<div role=\"alertdialog\" aria-labelledby=\"t\">\n  <p id=\"t\">Your session ends in 2 minutes.</p>\n  <button onclick=\"extendSession()\">Stay signed in</button>\n</div>"),
    ("html", "<meta http-equiv=\"refresh\" content=\"60; url=/session-expired\">"))

D["2.2.2"] = e(
    "motion and animation, auto-updating content, carousels, marquees, blinking text, video backgrounds, tickers",
    "assisted",
    "axe-core `blink` and `marquee` catch the obsolete elements. A static scanner can flag `autoplay` video, CSS `animation: ... infinite`, and `setInterval` updaters; a page runner can observe DOM or pixel changes over 5 seconds. A human checks each moving, blinking, scrolling or auto-updating item for a pause, stop or hide mechanism.",
    ["Load the page and watch it for at least 5 seconds; list anything that moves, blinks, scrolls or updates on its own.",
     "For moving/blinking/scrolling content that starts automatically, lasts more than 5 seconds and is shown with other content, confirm a pause, stop or hide mechanism.",
     "For auto-updating content that starts automatically and is shown with other content, confirm a pause, stop, hide or update-frequency control.",
     "Check that the controls are keyboard operable and have accessible names.",
     "Exclude only movement that is essential to the activity."],
    ["`<marquee>` or `<blink>` elements.",
     "Autoplaying looping `<video autoplay loop muted>` hero banner with no pause button.",
     "Auto-rotating carousel (`setInterval(next, 4000)`) with no pause control.",
     "Live news ticker updated by script with no way to stop it.",
     "Infinite CSS animation on decorative elements alongside page content."],
    ("html", "<div class=\"carousel\">\n  <button aria-pressed=\"false\" onclick=\"toggleRotation(this)\">Pause slides</button>\n  <!-- slides -->\n</div>"),
    ("html", "<video autoplay loop muted src=\"hero.mp4\"></video>\n<!-- no pause control; plays indefinitely -->"))

D["2.2.3"] = e(
    "timing, all time limits, timed tests and forms",
    "manual",
    "No axe-core rule. A static scanner can find timers and `meta refresh`; a page runner can detect timed behaviour. A human confirms that timing is not an essential part of any event or activity except non-interactive synchronized media and real-time events.",
    ["List every time limit in the content.",
     "Confirm each is removed, or that the only remaining limits belong to non-interactive synchronized media or real-time events.",
     "Fail any other time limit, even if it is adjustable."],
    ["Quiz that gives a fixed time per question.",
     "Reservation hold that releases seats after a countdown.",
     "Form that expires even though the user can extend it."],
    ("html", "<form action=\"/quiz\">\n  <!-- no timer; users answer at their own pace -->\n</form>"),
    ("html", "<p>Time left: <span id=\"timer\">60</span>s</p>\n<script>startCountdown(60, submitQuiz)</script>"))

D["2.2.4"] = e(
    "interruptions, notifications, alerts, auto-updates, chat and push messages",
    "assisted",
    "axe-core `meta-refresh-no-exceptions` flags any timed refresh. A static scanner can find `role=\"alert\"`, toast libraries and refresh timers; a page runner can observe unrequested interruptions. A human confirms that users can postpone or suppress interruptions except emergencies.",
    ["Identify everything that interrupts the user without being requested: pop-ups, toasts, live alerts, auto-refreshes, promotional overlays.",
     "Check that a setting or control lets the user postpone or turn off each, except emergencies.",
     "Confirm that suppressing interruptions does not lose data the user needs."],
    ["Chat widget that pops open with a message on a timer and cannot be muted.",
     "`<meta http-equiv=\"refresh\" content=\"300\">` that reloads news pages.",
     "Frequent non-emergency `role=\"alert\"` toasts with no preference to silence them."],
    ("html", "<label><input type=\"checkbox\" id=\"quiet\"> Pause notifications</label>"),
    ("html", "<meta http-equiv=\"refresh\" content=\"120\">"))

D["2.2.5"] = e(
    "authentication, sessions, multi-step forms, data preservation",
    "manual",
    "No axe-core rule. A page runner can expire a session (clearing cookies) mid-task and resubmit to see whether data persists. A human confirms the user can continue the activity without data loss after re-authenticating.",
    ["Start a multi-step or data-entry task while signed in.",
     "Let the session expire (or force it) before submitting.",
     "Re-authenticate and confirm that the task continues with all entered data kept."],
    ["Session expiry that redirects to login and then to the home page, losing the form.",
     "Server discards POST data received with an expired token instead of saving it for after sign-in."],
    ("js", "onSessionExpired(() => {\n  sessionStorage.setItem('draft', JSON.stringify(formData()));\n  showLogin({ returnTo: location.href });\n});"),
    ("js", "onSessionExpired(() => { location.href = '/login'; }); // draft lost"))

D["2.2.6"] = e(
    "timing, session timeouts, data loss, forms",
    "manual",
    "No axe-core rule. A static scanner may find timeout configuration; a human confirms that users are told how long inactivity may last before data loss, unless data is kept for more than 20 hours.",
    ["Identify any user inactivity that could cause data loss.",
     "Check that users are warned of the inactivity duration (for example, at the start of the process).",
     "Or confirm that data is kept for more than 20 hours of inactivity."],
    ["Application form that silently discards progress after 30 minutes of inactivity with no warning.",
     "Shopping cart cleared after an unstated idle period."],
    ("html", "<p>Your answers are saved for 7 days, even if you leave this page.</p>"),
    ("html", "<!-- form discards data after 15 minutes idle; users are not told -->\n<form id=\"application\">...</form>"))

D["2.3.1"] = e(
    "flashing content, video, animation, games, canvas and WebGL",
    "assisted",
    "No axe-core rule. A static scanner can flag rapid CSS/JS animation (short `animation-duration` with high-contrast changes) and media; frame analysis tools (for example, PEAT or similar photosensitivity analysers) measure general and red flash thresholds on recorded video. A human confirms flash area and frequency for anything that flashes.",
    ["Find any content that flashes (video, animation, games, blinking effects).",
     "Check whether it flashes more than three times in any one-second period.",
     "If it does, measure whether flashes stay below the general and red flash thresholds (for example, with a photosensitive epilepsy analysis tool).",
     "Fail content that flashes more than three times per second above threshold."],
    ["CSS `@keyframes` toggling a large area between black and white with `animation-duration: 0.1s`.",
     "Promotional video with strobe effects.",
     "Game that flashes a full-screen red hit effect several times per second."],
    ("css", ".alert { animation: pulse 2s ease-in-out 3; } /* slow, limited */"),
    ("css", ".hero { animation: strobe 0.1s steps(2) infinite; }\n@keyframes strobe { 50% { background: #fff; } }"))

D["2.3.2"] = e(
    "flashing content, video, animation",
    "assisted",
    "No axe-core rule. Static and frame-analysis checks as for 2.3.1, but no threshold exception applies: any content flashing more than three times per second fails. A human confirms on the rendered content.",
    ["Find all flashing content.",
     "Count flashes in any one-second period.",
     "Fail anything that flashes more than three times per second, regardless of size or contrast."],
    ["Small blinking status light at 5 Hz, which passes 2.3.1 by area but fails here.",
     "Loading spinner that flashes rapidly."],
    ("css", ".status { animation: fade 1s ease-in-out infinite; } /* 1 flash per second */"),
    ("css", ".status { animation: blink 0.2s steps(2) infinite; } /* 5 flashes per second */"))

D["2.3.3"] = e(
    "motion animation triggered by interaction, parallax, scroll effects, transitions",
    "assisted",
    "No axe-core rule. A static scanner can find animations and check whether CSS/JS respects `prefers-reduced-motion`; a page runner can emulate `prefers-reduced-motion: reduce` and compare motion. A human decides whether any remaining motion is essential.",
    ["Interact with the page (scroll, click, hover) and note motion animation it triggers.",
     "Check that the user can turn off non-essential motion, via a site setting or by honouring `prefers-reduced-motion`.",
     "Enable reduced motion and confirm the animations stop or are replaced by non-motion effects."],
    ["Parallax scrolling with no `@media (prefers-reduced-motion: reduce)` override.",
     "Page transitions that zoom or slide the whole viewport on every link click.",
     "JS scroll-triggered animation libraries initialised without checking `matchMedia('(prefers-reduced-motion: reduce)')`."],
    ("css", ".panel { transition: transform .4s; }\n@media (prefers-reduced-motion: reduce) {\n  .panel { transition: none; }\n}"),
    ("css", ".bg { background-attachment: fixed; } /* parallax, no reduced-motion override */\n.panel { transition: transform 1s; }"))

D["2.4.1"] = e(
    "navigation, repeated blocks, landmarks, headings, skip links",
    "assisted",
    "axe-core `bypass` checks that a page has a skip link, a heading or a landmark, but not that it bypasses the right block. A static scanner can check for `<main>` and a skip link whose target exists; a page runner can activate the skip link and confirm focus moves. A human confirms repeated blocks can actually be bypassed.",
    ["Identify blocks repeated across pages (header, navigation, sidebars).",
     "Check for a mechanism to skip them: a working skip link, landmarks (`<main>`, `<nav>`), or headings at the start of each section.",
     "Activate the skip link with the keyboard and confirm focus and reading position move past the block."],
    ["Skip link `href=\"#main\"` pointing to an id that does not exist.",
     "Skip link hidden with `display:none` so it never receives focus.",
     "Pages built only from `<div>` elements with no landmarks or headings."],
    ("html", "<a class=\"skip\" href=\"#main\">Skip to main content</a>\n<nav>...</nav>\n<main id=\"main\" tabindex=\"-1\">...</main>"),
    ("html", "<a href=\"#content\" style=\"display:none\">Skip</a>\n<div class=\"nav\">...</div>\n<div class=\"content\">...</div>"))

D["2.4.2"] = e(
    "page title, documents, single-page app route changes",
    "assisted",
    "axe-core `document-title` fails a missing or empty `<title>`; it cannot judge whether the title describes the page. A static scanner can flag duplicate or placeholder titles across templates (\"Untitled\", \"React App\"); a page runner can check that the title changes on SPA route changes. A human confirms the title describes topic or purpose.",
    ["Check that each page has a `<title>`.",
     "Confirm the title identifies the topic or purpose of the page (unique content first is helpful).",
     "In single-page apps, navigate between views and confirm `document.title` updates."],
    ["Missing or empty `<title>`.",
     "Every page titled with the site name only, or a framework default such as \"React App\".",
     "SPA router that never updates `document.title`."],
    ("html", "<title>Shipping address - Checkout - Example Store</title>"),
    ("html", "<title>React App</title>"))

D["2.4.3"] = e(
    "focus order, keyboard, dialogs, dynamic content, layout reordering",
    "assisted",
    "No axe-core rule for order (the `tabindex` best-practice rule is not mapped to this SC). A static scanner can flag positive `tabindex` and CSS reordering (`order`, `flex-direction: row-reverse`, absolute positioning); a page runner can record the Tab sequence and compare it with visual position. A human decides whether the order preserves meaning and operability.",
    ["Tab through the page and note the order in which elements receive focus.",
     "Compare it with the visual and logical reading order.",
     "Open dialogs, menus and disclosures and confirm focus moves into them and returns sensibly when closed.",
     "Fail any sequence that changes meaning or makes operation confusing."],
    ["Positive `tabindex` values (`tabindex=\"3\"`) that create an order unrelated to the layout.",
     "CSS `order` or `flex-direction: row-reverse` making visual order differ from DOM order.",
     "Modal dialog opened at the end of the DOM with focus left on the trigger behind it.",
     "Focus sent to the top of the page after closing a dialog or deleting a list item."],
    ("html", "<label for=\"first\">First name</label><input id=\"first\">\n<label for=\"last\">Last name</label><input id=\"last\">"),
    ("html", "<input id=\"last\" tabindex=\"1\">\n<input id=\"first\" tabindex=\"2\">\n<button tabindex=\"3\">Submit</button>"))

D["2.4.4"] = e(
    "links, image links, navigation",
    "assisted",
    "axe-core `link-name` and `area-alt` fail links with no accessible name, but cannot judge purpose. A static scanner can flag vague link text (\"click here\", \"read more\", \"more\") and repeated identical text with different `href`; a page runner can compute accessible names with their programmatic context. A human confirms the purpose is clear from the link text plus its context.",
    ["List all links with their accessible names (for example, with a link list in a screen reader).",
     "For each, check that the purpose is clear from the text alone or with its programmatic context (sentence, paragraph, list item, table cell or header, `aria-describedby`).",
     "Check image links have a text alternative describing the destination.",
     "Fail links whose purpose cannot be worked out, unless it would be ambiguous to all users."],
    ["Icon-only link `<a href=\"/cart\"><svg>...</svg></a>` with no accessible name.",
     "Many \"Read more\" links whose context is not programmatically associated.",
     "Image link whose `alt` describes the image rather than the destination.",
     "`<a href=\"...\">here</a>` in a paragraph that does not explain the target."],
    ("html", "<h3 id=\"a1\">Budget report 2025</h3>\n<a href=\"/r/2025\" aria-describedby=\"a1\">Read more</a>"),
    ("html", "<a href=\"/cart\"><svg aria-hidden=\"true\">...</svg></a>"))

D["2.4.5"] = e(
    "navigation, site structure, search, sitemaps",
    "manual",
    "No axe-core rule. A crawler can check that pages are reachable from more than one path (navigation, search, sitemap). A human confirms at least two ways exist to locate each page that is not a step in a process.",
    ["Identify the set of pages in scope.",
     "Check that at least two ways exist to find each page: site navigation, search, site map, table of contents, related links, or links from home.",
     "Exclude pages that are the result of, or a step in, a process."],
    ["Content reachable only by following a single path of links, with no search or site map.",
     "Help articles reachable only through one nested menu."],
    ("html", "<nav aria-label=\"Main\">...</nav>\n<form role=\"search\"><label for=\"q\">Search</label><input id=\"q\" type=\"search\"></form>"),
    ("html", "<nav>...</nav>\n<!-- no search, site map or other way to find pages -->"))

D["2.4.6"] = e(
    "headings, labels, forms, page structure",
    "manual",
    "No axe-core rule decides whether text is descriptive. A static scanner can flag empty headings, generic labels (\"Field 1\") and duplicate headings; a page runner can list headings and labels. A human judges whether each heading and label describes its topic or purpose.",
    ["List headings on the page and read them out of context.",
     "Check each describes the section that follows.",
     "List visible labels on form fields and controls and check each describes the purpose of the field.",
     "Note: this SC does not require headings or labels to exist, only that those present are descriptive."],
    ["Headings such as \"Section 1\" or \"More\" that do not describe content.",
     "Several fields labelled \"Name\" on one form without distinguishing context.",
     "Labels that are placeholders such as \"Enter text\"."],
    ("html", "<h2>Delivery options</h2>\n<label for=\"pc\">Postcode</label><input id=\"pc\">"),
    ("html", "<h2>Section 2</h2>\n<label for=\"pc\">Field</label><input id=\"pc\">"))

D["2.4.7"] = e(
    "focus, keyboard, focus indicators, CSS styling",
    "assisted",
    "No axe-core rule. A static scanner can flag `outline: none`/`outline: 0` or `:focus { outline: none }` with no replacement style; a page runner can Tab through the page and compare screenshots or computed styles of each element with and without focus. A human confirms the indicator is visible on every focusable element.",
    ["Tab through all interactive elements.",
     "Confirm each shows a visible indicator when it receives keyboard focus.",
     "Check custom components and components inside iframes, and check across themes (for example, dark mode)."],
    ["Global `*:focus { outline: none; }` reset with no replacement.",
     "`button:focus { outline: 0 }` in a CSS framework override.",
     "Focus style only on `:hover`, not `:focus`/`:focus-visible`.",
     "Focus ring same colour as the background so it cannot be seen."],
    ("css", "button:focus-visible {\n  outline: 3px solid #1a5fb4;\n  outline-offset: 2px;\n}"),
    ("css", "*:focus { outline: none; }"))

D["2.4.8"] = e(
    "navigation, breadcrumbs, site structure, multi-step processes",
    "manual",
    "No axe-core rule. A static scanner can check for breadcrumbs or `aria-current` in navigation. A human confirms that information about the user's location within a set of pages is available.",
    ["Check whether the page shows where the user is within the site or process.",
     "Look for breadcrumbs, a site map, `aria-current` on the current navigation item, or a step indicator.",
     "Confirm the information is available on every page in the set."],
    ["Deep content pages with no breadcrumb and no current-item indication in the navigation.",
     "Multi-step form without a \"Step 2 of 4\" indicator."],
    ("html", "<nav aria-label=\"Breadcrumb\"><ol>\n  <li><a href=\"/\">Home</a></li>\n  <li><a href=\"/help\">Help</a></li>\n  <li aria-current=\"page\">Returns</li>\n</ol></nav>"),
    ("html", "<nav><a href=\"/\">Home</a> <a href=\"/help\">Help</a></nav>\n<!-- no indication of current location -->"))

D["2.4.9"] = e(
    "links, navigation",
    "assisted",
    "axe-core `identical-links-same-purpose` flags links with the same name but different destinations for review. A static scanner can flag vague link text; a page runner can list link names without context. A human confirms that the purpose of each link is clear from its link text alone.",
    ["List all links by their accessible names only (without surrounding context).",
     "Check each identifies its purpose from the link text alone.",
     "Allow exceptions only where the purpose would be ambiguous to users in general."],
    ["\"Read more\" links that rely on nearby text or `aria-describedby`, which passes 2.4.4 but fails here.",
     "Identical link text \"Download\" for different files."],
    ("html", "<a href=\"/r/2025\">Read the 2025 budget report</a>"),
    ("html", "<p>The 2025 budget report is ready. <a href=\"/r/2025\">Read more</a></p>"))

D["2.4.10"] = e(
    "headings, page structure, long content",
    "manual",
    "No axe-core rule. A static scanner can flag long blocks of text with no headings; a page runner can list the heading outline. A human confirms that content is organised under section headings.",
    ["Review the content for distinct sections.",
     "Check each section is introduced by a heading.",
     "Confirm the headings are marked up correctly (see 1.3.1)."],
    ["Long article with bold paragraphs as visual headings but no heading structure.",
     "Terms and conditions page with dozens of sections and no headings."],
    ("html", "<h2>Refunds</h2><p>...</p>\n<h2>Exchanges</h2><p>...</p>"),
    ("html", "<p>...refund policy text...</p>\n<p>...exchange policy text...</p>\n<!-- no section headings -->"))

D["2.4.11"] = e(
    "focus, sticky headers and footers, cookie banners, overlays, chat widgets",
    "assisted",
    "No axe-core rule. A page runner can Tab through the page and, for each focused element, test whether its bounding box is entirely covered by author content (for example, `position: fixed/sticky` headers or banners) using `elementsFromPoint`. A static scanner can flag fixed/sticky elements with no matching `scroll-padding`. A human confirms results, including for user-movable content in its initial position.",
    ["Open the page with any sticky header, footer, cookie banner or non-modal dialog in its initial state.",
     "Tab through all interactive elements, scrolling as the browser does.",
     "Check that each focused element is at least partly visible, not entirely hidden by author-created content.",
     "Treat content the user opened and can dismiss without moving focus (for example, with Esc) as not obscuring."],
    ["`position: sticky` header with no `scroll-padding-top`, so focused links scroll underneath it.",
     "Cookie consent bar fixed at the bottom covering focused footer links.",
     "Floating chat widget covering the submit button when it receives focus."],
    ("css", "header { position: sticky; top: 0; height: 4rem; }\nhtml { scroll-padding-top: 5rem; }"),
    ("css", "header { position: fixed; top: 0; height: 6rem; }\n/* no scroll-padding; focused items scroll under the header */"))

D["2.4.12"] = e(
    "focus, sticky headers and footers, overlays",
    "assisted",
    "No axe-core rule. The same page-runner check as 2.4.11, but failing any overlap with author content rather than only total coverage. A human confirms results.",
    ["Tab through all interactive elements with sticky and overlay content in place.",
     "Check that no part of each focused component is hidden by author-created content.",
     "Record partial overlaps as failures (they pass 2.4.11 but fail here)."],
    ["Sticky header that hides the top half of focused links.",
     "Fixed footer overlapping the bottom edge of the focused button."],
    ("css", "html { scroll-padding-top: 5rem; scroll-padding-bottom: 4rem; }"),
    ("css", "footer { position: fixed; bottom: 0; height: 3rem; }\n/* focused items near the bottom are partly covered */"))

D["2.4.13"] = e(
    "focus indicators, CSS styling, colour contrast",
    "assisted",
    "No axe-core rule. A page runner can screenshot each element focused and unfocused, and measure the changed-pixel area and its contrast (at least a 2 CSS pixel thick perimeter area, 3:1 between focused and unfocused states). A static scanner can flag thin (`1px`) or low-contrast outlines. A human confirms edge cases such as indicators altered by the author versus the browser default.",
    ["Tab to each interactive element.",
     "Measure the focus indicator: its area must be at least as large as a 2 CSS pixel thick perimeter of the unfocused component.",
     "Measure the contrast between the same pixels in focused and unfocused states: at least 3:1.",
     "Exclude indicators determined by the user agent and not changed by the author, and components whose appearance is set by the user agent."],
    ["`outline: 1px dotted #999` focus style: too thin and low contrast.",
     "Focus shown only by a subtle background colour change with less than 3:1 change.",
     "`box-shadow` focus ring that is clipped by `overflow: hidden` on the parent."],
    ("css", "a:focus-visible {\n  outline: 2px solid #000;\n  outline-offset: 2px;\n}"),
    ("css", "a:focus-visible { outline: 1px dotted #bbb; }"))

D["2.5.1"] = e(
    "pointer gestures, touch interfaces, maps, sliders, carousels, custom widgets",
    "assisted",
    "No axe-core rule. A static scanner can find multi-touch and swipe handlers (`touchstart` with `touches.length > 1`, gesture libraries, `pinch`, `swipe`) and check for sibling buttons; a page runner can list widgets with gesture handlers. A human confirms every multipoint or path-based gesture has a single-pointer alternative.",
    ["Identify functions that use multipoint gestures (pinch, two-finger swipe) or path-based gestures (swipe, drawing a pattern).",
     "Check that each can also be done with a single pointer without a path (tap, click, double-tap, long press), such as buttons.",
     "Confirm any exception is essential (for example, signature capture)."],
    ["Map zoom only by pinch, with no + / - buttons.",
     "Carousel that changes slide only on swipe, with no previous/next buttons.",
     "Unlock or confirm action that needs a swipe path."],
    ("html", "<div id=\"map\"></div>\n<button onclick=\"zoom(1)\">Zoom in</button>\n<button onclick=\"zoom(-1)\">Zoom out</button>"),
    ("js", "map.addEventListener('touchmove', (e) => {\n  if (e.touches.length === 2) pinchZoom(e); // only way to zoom\n});"))

D["2.5.2"] = e(
    "pointer events, buttons, custom controls, drag and drop",
    "assisted",
    "No axe-core rule. A static scanner can flag functions triggered on `mousedown`, `pointerdown` or `touchstart` (React `onMouseDown`, `onPointerDown`) rather than click/up events; a page runner can press the pointer on a control, move away and release to see whether the action fires. A human confirms abort/undo or the essential exception.",
    ["Find controls whose function runs on the down-event.",
     "For each, press down on the control, move off it and release; confirm nothing happens (or the action is aborted or can be undone).",
     "Accept down-event activation only when an up-event reverses it (for example, press-and-hold) or it is essential (for example, a piano key)."],
    ["`onMouseDown={submit}` on a submit or delete button.",
     "`pointerdown` handler that navigates immediately.",
     "Custom toggle using `touchstart` to change state."],
    ("jsx", "<button type=\"button\" onClick={deleteItem}>Delete</button>"),
    ("jsx", "<button type=\"button\" onMouseDown={deleteItem}>Delete</button>"))

D["2.5.3"] = e(
    "labels, accessible names, buttons, links, form controls, speech input",
    "assisted",
    "axe-core `label-content-name-mismatch` (experimental) flags names that do not contain the visible text. A static scanner can compare `aria-label` values with the element's visible text content; a page runner can compare computed accessible names with rendered text. A human checks images of text and whether the visible label text appears in the name (preferably at the start).",
    ["List components that have a visible text label (including text in images of text).",
     "Compare each accessible name with the visible label.",
     "Confirm the name contains the visible label text (best practice: it starts with it).",
     "Test with speech input by saying the visible label and confirming activation."],
    ["`<button aria-label=\"Submit form\">Send</button>`: visible \"Send\" is not in the name.",
     "Link with visible \"Read more\" and `aria-label=\"Article details\"`.",
     "Input labelled visibly \"Email\" but `aria-labelledby` pointing to hint text only."],
    ("html", "<button aria-label=\"Send message\">Send</button>"),
    ("html", "<button aria-label=\"Submit form\">Send</button>"))

D["2.5.4"] = e(
    "device motion, shake, tilt, gestures toward the camera, mobile web apps",
    "assisted",
    "No axe-core rule. A static scanner can flag `devicemotion`, `deviceorientation` and accelerometer or gyroscope APIs; a human confirms that each motion-triggered function has a UI alternative and can be turned off to prevent accidental activation.",
    ["Find functions operated by moving the device or by user motion (shake to undo, tilt to scroll).",
     "Check that each can also be operated by standard UI controls.",
     "Check that motion response can be disabled.",
     "Allow exceptions only for accessibility-supported interfaces or where motion is essential."],
    ["`window.addEventListener('devicemotion', undoOnShake)` with no undo button.",
     "Tilt-to-scroll gallery with no scroll controls and no off switch."],
    ("html", "<button onclick=\"undo()\">Undo</button>\n<label><input type=\"checkbox\" id=\"shake\"> Shake to undo</label>"),
    ("js", "window.addEventListener('devicemotion', (e) => {\n  if (isShake(e)) undo(); // only way to undo; cannot be turned off\n});"))

D["2.5.5"] = e(
    "pointer targets, buttons, links, icons, touch interfaces",
    "assisted",
    "No axe-core rule for 44 px (axe `target-size` checks the 24 px minimum). A page runner can measure every target's bounding box against 44 by 44 CSS pixels; a human confirms the equivalent, inline, user-agent and essential exceptions.",
    ["Measure the size of each pointer target.",
     "Check each is at least 44 by 44 CSS pixels.",
     "Exclude targets with an equivalent large target on the same page, inline targets in sentences or blocks of text, unmodified user-agent controls, and essential presentations."],
    ["Icon buttons at 32 by 32 pixels.",
     "Pagination links at 20 by 20 pixels.",
     "Close \"x\" on dialogs sized to the glyph."],
    ("css", ".icon-btn { min-width: 44px; min-height: 44px; }"),
    ("css", ".icon-btn { width: 24px; height: 24px; padding: 0; }"))

D["2.5.6"] = e(
    "input modalities, touch, mouse, keyboard, stylus",
    "manual",
    "No axe-core rule. A static scanner can flag code that disables input types based on detection (for example, removing mouse handlers when `ontouchstart` exists or using `pointerType` checks to ignore input). A human confirms the content does not restrict input methods available on the platform.",
    ["On a device with several input methods (for example, a touchscreen laptop), use the content with each: touch, mouse, keyboard.",
     "Switch between methods partway through tasks.",
     "Fail content that blocks a method except where essential, needed for security, or needed to respect user settings."],
    ["`if ('ontouchstart' in window) disableMouseHandlers()`.",
     "Handler that ignores events with `e.pointerType === 'mouse'` on touch-capable devices."],
    ("js", "el.addEventListener('click', activate); // works for mouse, touch, pen and keyboard"),
    ("js", "if ('ontouchstart' in window) {\n  el.addEventListener('touchend', activate); // mouse and keyboard ignored\n} "))

D["2.5.7"] = e(
    "dragging movements, drag and drop, sortable lists, sliders, maps, kanban boards",
    "assisted",
    "No axe-core rule. A static scanner can find drag handlers (`draggable=\"true\"`, `dragstart`, drag-and-drop libraries, pointer move handlers) and check whether alternative buttons exist; a page runner can list drag-capable elements. A human confirms every dragging function can be achieved with single-pointer actions without dragging (keyboard alternatives alone do not satisfy this SC).",
    ["Find each function that uses dragging (reorder, move, resize, slide, pan).",
     "Check that each can also be done with single-pointer actions without dragging, such as taps or clicks on buttons, a menu, or clicking a target position.",
     "Confirm a keyboard-only alternative is not being counted as the only alternative.",
     "Allow exceptions only where dragging is essential or the behaviour is set by the user agent and not modified by the author."],
    ["Sortable list reorderable only by drag, with no move up/down buttons or menu.",
     "Custom range slider whose thumb must be dragged, and clicking the track does nothing.",
     "Kanban board moving cards only by drag."],
    ("html", "<li draggable=\"true\">Task A\n  <button aria-label=\"Move Task A up\">&#8593;</button>\n  <button aria-label=\"Move Task A down\">&#8595;</button>\n</li>"),
    ("html", "<li draggable=\"true\" ondragstart=\"startMove(event)\">Task A</li>\n<!-- no single-pointer way to reorder -->"))

D["2.5.8"] = e(
    "pointer targets, buttons, links, icons, form controls, touch interfaces",
    "assisted",
    "axe-core `target-size` measures targets against 24 by 24 CSS pixels and the spacing offset, but it cannot always judge the equivalent, inline and essential exceptions. A page runner can measure each target's bounding box and apply the 24 CSS pixel diameter circle spacing test; a static scanner can flag small fixed `width`/`height` on buttons and icon links. A human confirms exceptions.",
    ["Measure each pointer target's bounding box.",
     "For targets smaller than 24 by 24 CSS pixels, centre a 24 CSS pixel circle on each and check that it does not intersect another target or another undersized target's circle.",
     "Exclude targets that have an equivalent control meeting the SC, inline targets in sentences, unmodified user-agent controls, and essential or legally required presentations.",
     "Record remaining undersized, crowded targets as failures."],
    ["Icon buttons at 16 by 16 pixels placed side by side with no gap.",
     "Pagination or star-rating controls at 18 pixels with 2 pixel gaps.",
     "Close button sized to the glyph (`width: 12px`).",
     "Checkbox restyled smaller than the browser default with `appearance: none; width: 14px`."],
    ("css", ".toolbar button { min-width: 24px; min-height: 24px; }\n.toolbar { display: flex; gap: 8px; }"),
    ("css", ".toolbar button { width: 16px; height: 16px; padding: 0; }\n.toolbar { display: flex; gap: 0; }"))

out = os.path.join(os.path.dirname(__file__), "p2.json")
json.dump(D, open(out, "w"), indent=1, ensure_ascii=False)
print(len(D))
