# WCAG 2.2 success criteria — Principle 3: Understandable

> **Source and licence.** Normative text quoted in this file (marked as block quotes, including SC text, notes and guideline statements) is copied verbatim from
> *Web Content Accessibility Guidelines (WCAG) 2.2*, W3C Recommendation, 12 December 2024 edition,
> <https://www.w3.org/TR/WCAG22/>. Copyright © 2024 World Wide Web Consortium.
> <https://www.w3.org/copyright/document-license-2023/>. Status: W3C Recommendation.
> Technique and failure IDs/titles and ACT rule names are taken from *Understanding WCAG 2.2* and
> *Techniques for WCAG 2.2* (W3C Group Notes, informative), <https://www.w3.org/WAI/WCAG22/Understanding/>,
> <https://www.w3.org/WAI/WCAG22/Techniques/>, Copyright © 2024 World Wide Web Consortium, under the same licence.
> All other text (summaries, testability, procedures, code patterns and examples) is original to this skill.
> See `NOTICE` at the skill root.

Principle 3 has 21 success-criterion sections. Each entry uses the check ID `WCAG-<sc>` (see `check-index.md`). Testability: **automated** = a tool can decide the core requirement for most content; **assisted** = tools find candidates or partial failures and a human confirms; **manual** = human judgement dominates. "Static scanner" means the skill's source-code scanner; "page runner" means the live-page runner (axe-core 4.13.0 plus custom checks).

## Contents

- Guideline 3.1 Readable
  - [WCAG-3.1.1 Language of Page](#wcag-3-1-1) (A)
  - [WCAG-3.1.2 Language of Parts](#wcag-3-1-2) (AA)
  - [WCAG-3.1.3 Unusual Words](#wcag-3-1-3) (AAA)
  - [WCAG-3.1.4 Abbreviations](#wcag-3-1-4) (AAA)
  - [WCAG-3.1.5 Reading Level](#wcag-3-1-5) (AAA)
  - [WCAG-3.1.6 Pronunciation](#wcag-3-1-6) (AAA)
- Guideline 3.2 Predictable
  - [WCAG-3.2.1 On Focus](#wcag-3-2-1) (A)
  - [WCAG-3.2.2 On Input](#wcag-3-2-2) (A)
  - [WCAG-3.2.3 Consistent Navigation](#wcag-3-2-3) (AA)
  - [WCAG-3.2.4 Consistent Identification](#wcag-3-2-4) (AA)
  - [WCAG-3.2.5 Change on Request](#wcag-3-2-5) (AAA)
  - [WCAG-3.2.6 Consistent Help](#wcag-3-2-6) (A, new in 2.2)
- Guideline 3.3 Input Assistance
  - [WCAG-3.3.1 Error Identification](#wcag-3-3-1) (A)
  - [WCAG-3.3.2 Labels or Instructions](#wcag-3-3-2) (A)
  - [WCAG-3.3.3 Error Suggestion](#wcag-3-3-3) (AA)
  - [WCAG-3.3.4 Error Prevention (Legal, Financial, Data)](#wcag-3-3-4) (AA)
  - [WCAG-3.3.5 Help](#wcag-3-3-5) (AAA)
  - [WCAG-3.3.6 Error Prevention (All)](#wcag-3-3-6) (AAA)
  - [WCAG-3.3.7 Redundant Entry](#wcag-3-3-7) (A, new in 2.2)
  - [WCAG-3.3.8 Accessible Authentication (Minimum)](#wcag-3-3-8) (AA, new in 2.2)
  - [WCAG-3.3.9 Accessible Authentication (Enhanced)](#wcag-3-3-9) (AAA, new in 2.2)

## Guideline 3.1 — Readable

> Make text content readable and understandable.

<a id="wcag-3-1-1"></a>
### WCAG-3.1.1 — Language of Page (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#language-of-page> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/language-of-page.html>

- **Text:**

  > The default human language of each web page can be programmatically determined.

- **Applies to:** language, page metadata, documents
- **Testability:** automated — axe-core `html-has-lang`, `html-lang-valid` and `html-xml-lang-mismatch` decide presence and validity of the page language; the static scanner flags `<html>` without `lang` in templates and layout components. A human only confirms the declared language matches the main content.
  - **axe-core rules (4.13.0):** `html-has-lang`, `html-lang-valid`, `html-xml-lang-mismatch`
- **Test procedure:**
  1. Inspect the root `<html>` element (or the document language setting for PDF/Office).
  2. Confirm a `lang` attribute exists with a valid BCP 47 tag.
  3. Compare the tag with the predominant language of the content; a valid but wrong tag still fails.
  4. Repeat for each template, SPA route shell and iframe document in scope.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: `<html>` with no `lang` attribute (common in hand-written templates and some SSR shells).
  - Pattern: Invalid or empty values such as `lang=""`, `lang="english"` or `lang="en_US"`.
  - Pattern: Framework default left in place, e.g. `lang="en"` on a site whose content is German.
  - Pattern: `lang` and `xml:lang` that disagree on XHTML documents.
- **Sufficient techniques:**
  - H57 — Using the language attribute on the HTML element
  - PDF16 — Setting the default language using the /Lang entry in the document catalog of a PDF document
  - PDF19 — Specifying the language for a passage or phrase with the Lang entry in PDF documents
- **ACT test rules:** [HTML page has lang attribute](https://www.w3.org/WAI/standards-guidelines/act/rules/b5c3f8/); [HTML page lang attribute has valid language tag](https://www.w3.org/WAI/standards-guidelines/act/rules/bf051a/); [HTML page lang and xml:lang attributes have matching values](https://www.w3.org/WAI/standards-guidelines/act/rules/5b7ae0/proposed/); [HTML page language subtag matches default language](https://www.w3.org/WAI/standards-guidelines/act/rules/ucwvc8/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <!doctype html>
  <html lang="fr">
    <head><title>Accueil</title></head>
  ```

  Fail:

  ```html
  <!doctype html>
  <html>
    <head><title>Accueil</title></head>
  ```

<a id="wcag-3-1-2"></a>
### WCAG-3.1.2 — Language of Parts (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#language-of-parts> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/language-of-parts.html>

- **Text:**

  > The human language of each passage or phrase in the content can be programmatically determined except for proper names, technical terms, words of indeterminate language, and words or phrases that have become part of the vernacular of the immediately surrounding text.

- **Applies to:** language, inline passages, quotations, multilingual content, language switchers
- **Testability:** assisted — axe-core `valid-lang` only checks that `lang` values on descendants are valid; it cannot find untagged foreign passages. A static scanner can flag language-switcher links (e.g. text `Deutsch`, `Español`) without `lang`; a human must identify passages in another language.
  - **axe-core rules (4.13.0):** `valid-lang`
- **Test procedure:**
  1. Read the page and list passages, quotes, names of languages and UI labels written in a language other than the page default.
  2. Check each passage (or its nearest container) carries a correct `lang` attribute.
  3. Ignore proper names, technical terms, words of indeterminate language and words that have become part of the surrounding language.
  4. Verify any `lang` values used are valid BCP 47 tags.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Language-picker links like `<a href="/de">Deutsch</a>` without `lang="de"`.
  - Pattern: Block quotes or testimonials in another language without `lang` on the `<blockquote>`.
  - Pattern: React i18n components rendering fallback strings in the default language inside a translated page without marking them.
  - Pattern: Invalid values such as `lang="sp"`.
- **Sufficient techniques:**
  - H58 — Using language attributes to identify changes in the human language
  - PDF19 — Specifying the language for a passage or phrase with the Lang entry in PDF documents
- **ACT test rules:** [Element with lang attribute has valid language tag](https://www.w3.org/WAI/standards-guidelines/act/rules/de46e4/); [HTML element language subtag matches language](https://www.w3.org/WAI/standards-guidelines/act/rules/off6ek/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <p>Our partner writes:</p>
  <blockquote lang="es">Más vale tarde que nunca.</blockquote>
  <a href="/de/" lang="de" hreflang="de">Deutsch</a>
  ```

  Fail:

  ```html
  <p>Our partner writes:</p>
  <blockquote>Más vale tarde que nunca.</blockquote>
  ```

<a id="wcag-3-1-3"></a>
### WCAG-3.1.3 — Unusual Words (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#unusual-words> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/unusual-words.html>

- **Text:**

  > A mechanism is available for identifying specific definitions of words or phrases used in an unusual or restricted way, including idioms and jargon.

- **Applies to:** text content, jargon, idioms, technical terms
- **Testability:** manual — No axe-core rule applies. A static scanner can list `<abbr>`, `<dfn>` and glossary links as evidence of a mechanism; identifying unusual words is human judgement.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify idioms, jargon and words used in an unusual or restricted way.
  2. For each, check a mechanism gives the specific definition: inline definition, `<dfn>`, link to a glossary, or a definition list.
  3. Confirm the mechanism is reachable from each use (or the glossary is linked consistently).
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Domain jargon (e.g. "amortize", "idempotent") with no definition or glossary link.
  - Pattern: Idioms such as "ballpark figure" left unexplained.
  - Pattern: A glossary page exists but is not linked from the terms that need it.
- **Sufficient techniques:**
  - G101 — Providing the definition of a word or phrase used in an unusual or restricted way
  - G55 — Linking to definitions
  - H40 — Using description lists
  - G112 — Using inline definitions
  - H54 — Using the dfn element to identify the defining instance of a word or phrase
  - G62 — Providing a glossary
  - G70 — Providing a function to search an online dictionary
- **Pass/fail example:**

  Pass:

  ```html
  <p>Each request is <a href="/glossary#idempotent">idempotent</a>.</p>
  ```

  Fail:

  ```html
  <p>Each request is idempotent.</p>
  ```

<a id="wcag-3-1-4"></a>
### WCAG-3.1.4 — Abbreviations (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#abbreviations> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/abbreviations.html>

- **Text:**

  > A mechanism for identifying the expanded form or meaning of abbreviations is available.

- **Applies to:** abbreviations, acronyms, initialisms
- **Testability:** manual — No axe-core rule applies. A static scanner can find all-caps tokens and `<abbr>` elements lacking an expansion; a human decides which are abbreviations needing expansion.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. List abbreviations, acronyms and initialisms on the page.
  2. Check each is expanded on first use, via `<abbr title>` plus visible expansion, a glossary link, or a consistent definition mechanism.
  3. Confirm the expansion is available to all users (not only a mouse-hover `title`).
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Acronyms such as `SLA` or `WCAG` used with no expansion anywhere.
  - Pattern: Expansion only in a `title` tooltip that keyboard and touch users cannot reach.
  - Pattern: Same abbreviation with different meanings on one page and no disambiguation.
- **Sufficient techniques:**
  - G102 — Providing the expansion or explanation of an abbreviation
  - G97 — Providing the first use of an abbreviation immediately before or after the expanded form
  - G55 — Linking to definitions
  - PDF8 — Providing definitions for abbreviations via an E entry for a structure element
  - G62 — Providing a glossary
  - G70 — Providing a function to search an online dictionary
- **Pass/fail example:**

  Pass:

  ```html
  <p>We meet our <abbr title="service level agreement">SLA</abbr>
    (service level agreement) for all plans.</p>
  ```

  Fail:

  ```html
  <p>We meet our SLA for all plans.</p>
  ```

<a id="wcag-3-1-5"></a>
### WCAG-3.1.5 — Reading Level (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#reading-level> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/reading-level.html>

- **Text:**

  > When text requires reading ability more advanced than the lower secondary education level after removal of proper names and titles, supplemental content, or a version that does not require reading ability more advanced than the lower secondary education level, is available.

- **Applies to:** text content, instructions, articles
- **Testability:** manual — No axe-core rule applies. A readability formula (e.g. Flesch-Kincaid) run by the page runner or a script gives an estimate; a human confirms whether a supplemental version or simpler text is needed.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Excluding proper names and titles, estimate the reading level of the main text.
  2. If it needs more than lower secondary education, check for supplemental content (summary, illustrations, audio) or a simpler version.
  3. Confirm the supplement conveys the key information.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Dense legal or academic prose with no plain-language summary.
  - Pattern: Long sentences with nested clauses and passive voice in task instructions.
- **Sufficient techniques:**
  - G86 — Providing a text summary that can be understood by people with lower secondary education level reading ability
  - G103 — Providing visual illustrations, pictures, and symbols to help explain ideas, events, and processes
  - G79 — Providing a spoken version of the text
  - G153 — Making the text easier to read
  - G160 — Providing sign language versions of information, ideas, and processes that must be understood in order to use the content
- **Pass/fail example:**

  Pass:

  ```html
  <section aria-labelledby="sum"><h2 id="sum">Summary in plain words</h2>
    <p>You can cancel within 14 days and get all your money back.</p></section>
  ```

  Fail:

  ```html
  <p>Notwithstanding the foregoing, rescission shall be effectuated within fourteen days...</p>
  ```

<a id="wcag-3-1-6"></a>
### WCAG-3.1.6 — Pronunciation (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#pronunciation> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/pronunciation.html>

- **Text:**

  > A mechanism is available for identifying specific pronunciation of words where meaning of the words, in context, is ambiguous without knowing the pronunciation.

- **Applies to:** text content, heteronyms, languages with ambiguous pronunciation
- **Testability:** manual — No axe-core rule applies. Detecting words whose meaning depends on pronunciation is human judgement; a scanner can only check that `<ruby>` markup is well formed.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Find words whose meaning is ambiguous without knowing the pronunciation (heteronyms, kanji readings, unvowelled Hebrew/Arabic).
  2. Check a mechanism gives the pronunciation: inline, `<ruby>`, glossary or audio.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Heteronyms such as "read" or "lead" in contexts where both meanings fit and no clarification is given.
  - Pattern: Japanese names with non-standard readings and no furigana.
- **Sufficient techniques:**
  - G120 — Providing the pronunciation immediately following the word
  - G121 — Linking to pronunciations
  - G62 — Providing a glossary
  - G163 — Using standard diacritical marks that can be turned off
  - H62 — Using the ruby element
- **Pass/fail example:**

  Pass:

  ```html
  <ruby>東京<rp>(</rp><rt>とうきょう</rt><rp>)</rp></ruby>
  ```

  Fail:

  ```html
  <p>東京</p>
  ```

## Guideline 3.2 — Predictable

> Make web pages appear and operate in predictable ways.

<a id="wcag-3-2-1"></a>
### WCAG-3.2.1 — On Focus (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#on-focus> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/on-focus.html>

- **Text:**

  > When any user interface component receives focus, it does not initiate a change of context.

- **Applies to:** focus, forms, custom widgets, navigation
- **Testability:** assisted — No axe-core rule applies. A static scanner can flag `onFocus`/`focus` handlers that call `submit()`, change `location`, open windows or move focus; a page runner can tab through every focusable element and detect URL changes, new windows or focus jumps. A human confirms whether a change is a change of context.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Tab (and Shift+Tab) through every focusable component without activating anything.
  2. Watch for new windows, navigation, form submission, large content rearrangement or focus being moved elsewhere.
  3. Repeat with a screen reader's virtual cursor for elements that receive focus programmatically.
  4. Record each component whose focus alone causes a change of context.
- **Common failures:**
  - F55 — Failure of Success Criteria 2.1.1, 2.4.7, 2.4.13, and 3.2.1 due to using script to remove focus when focus is received
  - Pattern: `<select onfocus="this.form.submit()">` or a React `onFocus` that calls `navigate()`.
  - Pattern: Focusing a field opens a modal or pop-up window automatically.
  - Pattern: `onFocus={() => nextRef.current.focus()}` that throws focus away from the element.
- **Sufficient techniques:**
  - G107 — Using "activate" rather than "focus" as a trigger for changes of context
- **Pass/fail example:**

  Pass:

  ```jsx
  <input onFocus={() => setHint(true)} aria-describedby="hint" />
  {hint && <p id="hint">Use your work email.</p>}
  ```

  Fail:

  ```jsx
  <input onFocus={() => window.open("/help")} />
  ```

<a id="wcag-3-2-2"></a>
### WCAG-3.2.2 — On Input (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#on-input> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/on-input.html>

- **Text:**

  > Changing the setting of any user interface component does not automatically cause a change of context unless the user has been advised of the behavior before using the component.

- **Applies to:** forms, select menus, radio buttons, checkboxes, custom widgets
- **Testability:** assisted — No axe-core rule applies. A static scanner can flag `onchange`/`onChange`/`input` handlers that submit forms, navigate or move focus; a page runner can change each control value and detect navigation or focus jumps. A human confirms whether users were advised beforehand.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Change the setting of every input (type, select an option, toggle a checkbox or radio) without pressing a submit button.
  2. Note any navigation, form submission, new window or unexpected focus move.
  3. For each change of context found, check whether instructions before the component warn about the behaviour.
  4. Check keyboard selection in `<select>` does not trigger navigation on each arrow key.
- **Common failures:**
  - F36 — Failure of Success Criterion 3.2.2 due to automatically submitting a form and … given a value
  - F37 — Failure of Success Criterion 3.2.2 due to launching a new window without prior warning when the selection of a radio button, check box or select list is changed
  - Pattern: `<select onchange="location=this.value">` jump menus without a Go button.
  - Pattern: React `onChange={e => router.push(e.target.value)}` on a dropdown.
  - Pattern: Checkbox that auto-submits the form (`onChange={() => form.submit()}`).
  - Pattern: Filling the last digit of a code field auto-submits and navigates without warning.
- **Sufficient techniques:**
  - G80 — Providing a submit button to initiate a change of context
  - H32 — Providing submit buttons
  - H84 — Using a button with a select element to perform an action
  - PDF15 — Providing submit buttons with the submit-form action in PDF forms
  - G13 — Describing what will happen before a change to a form control that causes a change of context to occur is made
  - SCR19 — Using an onchange event on a select element without causing a change of context
- **Pass/fail example:**

  Pass:

  ```html
  <form action="/lang"><label for="l">Language</label>
    <select id="l" name="l"><option>English</option><option>Français</option></select>
    <button>Go</button></form>
  ```

  Fail:

  ```html
  <select onchange="location.href=this.value">
    <option value="/en">English</option><option value="/fr">Français</option>
  </select>
  ```

<a id="wcag-3-2-3"></a>
### WCAG-3.2.3 — Consistent Navigation (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#consistent-navigation> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/consistent-navigation.html>

- **Text:**

  > Navigational mechanisms that are repeated on multiple web pages within a set of web pages occur in the same relative order each time they are repeated, unless a change is initiated by the user.

- **Applies to:** navigation, headers, footers, menus, skip links, sets of pages
- **Testability:** assisted — No axe-core rule applies. A page runner can crawl several pages and compare the order of landmark and navigation link lists; a human confirms differences are not user-initiated.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Pick a representative set of pages that share navigation (header, sidebar, footer, breadcrumbs, search).
  2. Compare the relative order of repeated navigation items across the pages.
  3. Accept added or removed items as long as the remaining items keep the same relative order.
  4. Exclude changes the user initiated (e.g. personalising a menu).
- **Common failures:**
  - F66 — Failure of Success Criterion 3.2.3 due to presenting navigation links in a different relative order on different pages
  - Pattern: Main menu items reordered on different page templates (e.g. marketing vs. account layouts).
  - Pattern: Search box before navigation on some pages and after it on others.
  - Pattern: React layout variants that render nav links from different, unsorted arrays.
- **Sufficient techniques:**
  - G61 — Presenting repeated components in the same relative order each time they appear
- **Pass/fail example:**

  Pass:

  ```html
  <!-- every page -->
  <nav aria-label="Main"><a href="/">Home</a> <a href="/shop">Shop</a> <a href="/help">Help</a></nav>
  ```

  Fail:

  ```html
  <!-- page A --><nav><a href="/">Home</a><a href="/shop">Shop</a><a href="/help">Help</a></nav>
  <!-- page B --><nav><a href="/help">Help</a><a href="/">Home</a><a href="/shop">Shop</a></nav>
  ```

<a id="wcag-3-2-4"></a>
### WCAG-3.2.4 — Consistent Identification (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#consistent-identification> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/consistent-identification.html>

- **Text:**

  > Components that have the same functionality within a set of web pages are identified consistently.

- **Applies to:** icons, buttons, links, components repeated across pages
- **Testability:** assisted — No axe-core rule applies. A page runner can collect accessible names of components with the same function (same `href`, same icon, same handler) across pages and flag inconsistent names; a human confirms same functionality.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify components with the same function across the set of pages (search, print, download, home icon, cart).
  2. Compare their visible labels, accessible names and text alternatives.
  3. Flag components with the same function but different identification.
- **Common failures:**
  - F31 — Failure of Success Criterion 3.2.4 due to using two different labels for the same function on different web pages within a set of web pages
  - Pattern: Search button labelled "Search" on one page and "Find" on another.
  - Pattern: The same download icon with `alt="Download"` in one place and `alt="Save file"` elsewhere.
  - Pattern: Shared React component used with different `aria-label` props for the same action.
- **Sufficient techniques:**
  - G197 — Using labels, names, and text alternatives consistently for content that has the same functionality
- **Pass/fail example:**

  Pass:

  ```html
  <button aria-label="Search"><svg aria-hidden="true">…</svg></button> <!-- same on all pages -->
  ```

  Fail:

  ```html
  <!-- page A --><button aria-label="Search">…</button>
  <!-- page B --><button aria-label="Look up">…</button>
  ```

<a id="wcag-3-2-5"></a>
### WCAG-3.2.5 — Change on Request (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#change-on-request> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/change-on-request.html>

- **Text:**

  > Changes of context are initiated only by user request or a mechanism is available to turn off such changes.

- **Applies to:** navigation, pop-ups, new windows, automatic updates, redirects, forms
- **Testability:** assisted — axe-core `meta-refresh-no-exceptions` flags `<meta http-equiv=refresh>` with a delay; a static scanner can flag `target="_blank"` without a warning, `window.open` on load, and `setInterval` reloads; a human confirms that changes happen only on user request or can be turned off.
  - **axe-core rules (4.13.0):** `meta-refresh-no-exceptions`
- **Test procedure:**
  1. Load each page and wait: note any automatic redirect, refresh or content replacement.
  2. Check links and buttons that open new windows warn the user beforehand.
  3. Check any automatic update has a mechanism to turn it off.
  4. Verify redirects are done server-side instead of timed client redirects.
- **Common failures:**
  - F60 — Failure of Success Criterion 3.2.5 due to launching a new window when a user enters text into an input field
  - F61 — Failure of Success Criterion 3.2.5 due to complete change of main content through an automatic update that the user cannot disable from within the content
  - F9 — Failure of Success Criterion 3.2.5 due to changing the context when the user removes focus from a form element
  - F22 — Failure of Success Criterion 3.2.5 due to opening windows that are not requested by the user
  - F52 — Failure of Success Criterion 3.2.5 due to opening a new window as soon as a new page is loaded
  - F40 — Failure due to using meta redirect with a time limit
  - F41 — Failure of Success Criterion 2.2.1, 2.2.4, and 3.2.5 due to using meta refresh to reload the page
  - Pattern: `<meta http-equiv="refresh" content="5; url=/new">`.
  - Pattern: `target="_blank"` links with no text or icon indicating a new window.
  - Pattern: `window.open()` fired on page load or on focus.
  - Pattern: Carousel or feed that replaces content automatically with no way to stop it.
- **Sufficient techniques:**
  - G76 — Providing a mechanism to request an update of the content instead of updating automatically
  - SVR1 — Implementing automatic redirects on the server side instead of on the client side
  - G110 — Using an instant client-side redirect
  - H76 — Using meta refresh to create an instant client-side redirect
  - H83 — Using the target attribute to open a new window on user request and indicating this in link text
  - SCR24 — Using progressive enhancement to open new windows on user request
  - SCR19 — Using an onchange event on a select element without causing a change of context
- **ACT test rules:** [Meta element has no refresh delay](https://www.w3.org/WAI/standards-guidelines/act/rules/bc659a/); [Meta element has no refresh delay (no exception)](https://www.w3.org/WAI/standards-guidelines/act/rules/bisz58/)
- **Pass/fail example:**

  Pass:

  ```html
  <a href="/terms" target="_blank">Terms (opens in new window)</a>
  ```

  Fail:

  ```html
  <meta http-equiv="refresh" content="10; url=/home">
  ```

<a id="wcag-3-2-6"></a>
### WCAG-3.2.6 — Consistent Help (Level A) — new in 2.2

Spec: <https://www.w3.org/TR/WCAG22/#consistent-help> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html>

- **Text:**

  > If a web page contains any of the following help mechanisms, and those mechanisms are repeated on multiple web pages within a set of web pages, they occur in the same order relative to other page content, unless a change is initiated by the user:
  >
  > - Human contact details;
  > - Human contact mechanism;
  > - Self-help option;
  > - A fully automated contact mechanism.
  >
  > *Note 1:* Help mechanisms may be provided directly on the page, or may be provided via a direct link to a different page containing the information.
  >
  > *Note 2:* For this success criterion, "the same order relative to other page content" can be thought of as how the content is ordered when the page is serialized. The visual position of a help mechanism is likely to be consistent across pages for the same page variation (e.g., CSS break-point). The user can initiate a change, such as changing the page's zoom or orientation, which may trigger a different page variation. This criterion is concerned with relative order across pages displayed in the same page variation (e.g., same zoom level and orientation).

- **Applies to:** help, contact details, chat, FAQ links, sets of pages
- **Testability:** assisted — No axe-core rule applies. A page runner can crawl a set of pages and record the DOM order position of help mechanisms (contact links, `mailto:`/`tel:` links, chat widget, FAQ link) relative to other content; a human confirms they appear in the same relative order and identifies which help mechanisms exist.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify the help mechanisms offered (human contact details, contact mechanism, self-help option, automated contact such as a chatbot).
  2. Open several pages in the set that contain them (same page variation / breakpoint).
  3. Check each mechanism appears in the same order relative to other page content on every page.
  4. Remember the SC does not require help to be provided; it requires consistency where it is repeated.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Contact link in the header on some pages and moved to the footer on others.
  - Pattern: Chat widget injected only on some templates, or before main content on some and after it on others.
  - Pattern: Checkout templates that drop the help link used everywhere else, then re-add it in a different position.
- **Sufficient techniques:**
  - G220 — Provide a contact-us link in a consistent location
- **Pass/fail example:**

  Pass:

  ```html
  <footer><a href="/help">Help centre</a> · <a href="tel:+15550100">Call 555-0100</a></footer> <!-- same order on every page -->
  ```

  Fail:

  ```html
  <!-- page A --><header><a href="/help">Help</a></header>
  <!-- page B --><footer><a href="/help">Help</a></footer>
  ```

## Guideline 3.3 — Input Assistance

> Help users avoid and correct mistakes.

<a id="wcag-3-3-1"></a>
### WCAG-3.3.1 — Error Identification (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#error-identification> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html>

- **Text:**

  > If an input error is automatically detected, the item that is in error is identified and the error is described to the user in text.

- **Applies to:** forms, error messages, validation, required fields
- **Testability:** assisted — No axe-core rule directly tests error messages. A static scanner can flag inputs with `aria-invalid` but no `aria-describedby`/`aria-errormessage`, and error messages styled only by colour; a page runner can submit forms with empty/invalid data and dump the accessibility tree for errors. A human confirms the error text identifies the item and describes the problem.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Submit each form empty and with invalid data.
  2. Check each detected error identifies the item in error and describes the problem in text.
  3. Check the error is programmatically associated (`aria-describedby`/`aria-errormessage`, `aria-invalid`) or announced.
  4. Confirm errors are not conveyed only by colour, border or icon.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Field turns red with no text message.
  - Pattern: Generic "There was an error" banner not naming the field.
  - Pattern: Error text placed near the field but not associated, e.g. `<span class="error">` without `aria-describedby`.
  - Pattern: Client validation prevents submission silently.
- **Sufficient techniques:**
  - G83 — Providing text descriptions to identify required fields that were not completed
  - ARIA21 — Using aria-invalid to Indicate An Error Field
  - SCR18 — Providing client-side validation and alert
  - PDF5 — Indicating required form controls in PDF forms
  - ARIA18 — Using aria-alertdialog to Identify Errors
  - ARIA19 — Using ARIA role=alert or Live Regions to Identify Errors
  - G84 — Providing a text description when the user provides information that is not in the list of allowed values
  - G85 — Providing a text description when user input falls outside the required format or values
  - SCR32 — Providing client-side validation and adding error text via the DOM
  - PDF22 — Indicating when user input falls outside the required format or values in PDF forms
- **ACT test rules:** [Error message describes invalid form field value](https://www.w3.org/WAI/standards-guidelines/act/rules/36b590/proposed/)
- **Pass/fail example:**

  Pass:

  ```html
  <label for="em">Email</label>
  <input id="em" aria-invalid="true" aria-describedby="em-err">
  <p id="em-err">Email: enter an address like name@example.com.</p>
  ```

  Fail:

  ```html
  <label for="em">Email</label>
  <input id="em" style="border-color:red">
  ```

<a id="wcag-3-3-2"></a>
### WCAG-3.3.2 — Labels or Instructions (Level A)

Spec: <https://www.w3.org/TR/WCAG22/#labels-or-instructions> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions.html>

- **Text:**

  > Labels or instructions are provided when content requires user input.

- **Applies to:** forms, inputs, required fields, format hints, custom widgets
- **Testability:** assisted — axe-core `form-field-multiple-labels` catches one labelling problem; `label` (tagged 4.1.2) finds unlabelled inputs. A static scanner can flag inputs relying only on `placeholder`; a human confirms the visible labels/instructions are sufficient (required fields, formats).
  - **axe-core rules (4.13.0):** `form-field-multiple-labels`
- **Test procedure:**
  1. Find every input that needs user entry.
  2. Check each has a visible label or instructions when the content requires input.
  3. Check required fields and expected formats (dates, passwords) are indicated before submission.
  4. Check grouped controls (radio sets, date parts) have a group label (e.g. `<fieldset>`/`<legend>`).
- **Common failures:**
  - F82 — Failure of Success Criterion 3.3.2 by visually formatting a set of phone number fields but not including a text label
  - Pattern: `placeholder` used as the only label and disappearing on input.
  - Pattern: Required fields marked only with colour or an unexplained asterisk.
  - Pattern: Date field with no indication of the expected format.
  - Pattern: Radio buttons with no question/legend.
- **Sufficient techniques:**
  - G131 — Providing descriptive labels
  - ARIA1 — Using the aria-describedby property to provide a descriptive label for user interface controls
  - ARIA9 — Using aria-labelledby to concatenate a label from several text nodes
  - ARIA17 — Using grouping roles to identify related form controls
  - G89 — Providing expected data format and example
  - G184 — Providing text instructions at the beginning of a form or set of fields that describes the necessary input
  - G162 — Positioning labels to maximize predictability of relationships
  - G83 — Providing text descriptions to identify required fields that were not completed
  - H90 — Indicating required form controls using label or legend
  - PDF5 — Indicating required form controls in PDF forms
  - H44 — Using label elements to associate text labels with form controls
  - PDF10 — Providing labels for interactive form controls in PDF documents
  - H71 — Providing a description for groups of form controls using fieldset and legend elements
  - G167 — Using an adjacent button to label the purpose of a field
- **Pass/fail example:**

  Pass:

  ```html
  <label for="dob">Date of birth (DD/MM/YYYY, required)</label>
  <input id="dob" required>
  ```

  Fail:

  ```html
  <input placeholder="Date of birth">
  ```

<a id="wcag-3-3-3"></a>
### WCAG-3.3.3 — Error Suggestion (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#error-suggestion> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion.html>

- **Text:**

  > If an input error is automatically detected and suggestions for correction are known, then the suggestions are provided to the user, unless it would jeopardize the security or purpose of the content.

- **Applies to:** forms, validation, error messages
- **Testability:** manual — No axe-core rule applies. A page runner can submit invalid values and capture the resulting messages; a human judges whether suggestions are given where known and safe.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Enter invalid values for each field with a known correct format or range.
  2. Check the error message suggests how to correct it (format, allowed values, closest match).
  3. Accept omission only where a suggestion would jeopardise security or the purpose (e.g. a password).
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: "Invalid input" without saying what is expected.
  - Pattern: Date rejected without stating the format.
  - Pattern: Unrecognised city not followed by likely matches.
- **Sufficient techniques:**
  - ARIA18 — Using aria-alertdialog to Identify Errors
  - G85 — Providing a text description when user input falls outside the required format or values
  - G177 — Providing suggested correction text
  - PDF22 — Indicating when user input falls outside the required format or values in PDF forms
  - G84 — Providing a text description when the user provides information that is not in the list of allowed values
- **Pass/fail example:**

  Pass:

  ```html
  <p id="d-err">Date not recognised. Use the format DD/MM/YYYY, for example 07/03/2026.</p>
  ```

  Fail:

  ```html
  <p id="d-err">Invalid date.</p>
  ```

<a id="wcag-3-3-4"></a>
### WCAG-3.3.4 — Error Prevention (Legal, Financial, Data) (Level AA)

Spec: <https://www.w3.org/TR/WCAG22/#error-prevention-legal-financial-data> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data.html>

- **Text:**

  > For web pages that cause legal commitments or financial transactions for the user to occur, that modify or delete user-controllable data in data storage systems, or that submit user test responses, at least one of the following is true:
  >
  > - **Reversible:** Submissions are reversible.
  > - **Checked:** Data entered by the user is checked for input errors and the user is provided an opportunity to correct them.
  > - **Confirmed:** A mechanism is available for reviewing, confirming, and correcting information before finalizing the submission.

- **Applies to:** forms, checkout, legal commitments, financial transactions, data deletion, test submissions
- **Testability:** manual — No axe-core rule applies. A static scanner can find destructive or payment forms; a human must walk the flow to confirm submissions are reversible, checked, or confirmed.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify pages that cause legal commitments, financial transactions, modification/deletion of user data, or submit test responses.
  2. Complete each flow and check at least one of: reversible, data checked with a chance to correct, or a review/confirm step.
  3. Verify the confirm/review step really lets users correct information before final submission.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: One-click "Delete account" with no confirmation or undo.
  - Pattern: Payment submitted directly from the card form with no review page.
  - Pattern: Exam answers submitted immediately on selection.
- **Sufficient techniques:**
  - G164 — Providing a stated time within which an online request (or transaction) may be amended or canceled by the user after making the request
  - G98 — Providing the ability for the user to review and correct answers before submitting
  - G155 — Providing a checkbox in addition to a submit button
  - G99 — Providing the ability to recover deleted information
  - G168 — Requesting confirmation to continue with selected action
- **Pass/fail example:**

  Pass:

  ```html
  <h2>Review your order</h2><dl>…</dl>
  <a href="/checkout/edit">Change details</a> <button>Confirm and pay</button>
  ```

  Fail:

  ```html
  <button onclick="deleteAccount()">Delete account</button>
  ```

<a id="wcag-3-3-5"></a>
### WCAG-3.3.5 — Help (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#help> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/help.html>

- **Text:**

  > Context-sensitive help is available.

- **Applies to:** forms, help, instructions, complex inputs
- **Testability:** manual — No axe-core rule applies. Whether context-sensitive help is available is human judgement.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Identify inputs whose purpose or format might not be obvious.
  2. Check context-sensitive help is available (instructions, examples, help links, tooltips reachable by keyboard).
  3. Confirm the help is specific to the field or task.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Complex form (tax ID, IBAN) with no examples or help link.
  - Pattern: Help only in a hover `title` attribute not reachable by keyboard or touch.
- **Sufficient techniques:**
  - G71 — Providing a help link on every web page
  - G193 — Providing help by an assistant in the web page
  - G194 — Providing spell checking and suggestions for text input
  - G184 — Providing text instructions at the beginning of a form or set of fields that describes the necessary input
  - G89 — Providing expected data format and example
- **Pass/fail example:**

  Pass:

  ```html
  <label for="iban">IBAN</label> <input id="iban" aria-describedby="iban-h">
  <p id="iban-h">Starts with 2 letters, e.g. GB29 NWBK 6016 1331 9268 19.</p>
  ```

  Fail:

  ```html
  <label for="iban">IBAN</label> <input id="iban">
  ```

<a id="wcag-3-3-6"></a>
### WCAG-3.3.6 — Error Prevention (All) (Level AAA)

Spec: <https://www.w3.org/TR/WCAG22/#error-prevention-all> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-all.html>

- **Text:**

  > For web pages that require the user to submit information, at least one of the following is true:
  >
  > - **Reversible:** Submissions are reversible.
  > - **Checked:** Data entered by the user is checked for input errors and the user is provided an opportunity to correct them.
  > - **Confirmed:** A mechanism is available for reviewing, confirming, and correcting information before finalizing the submission.

- **Applies to:** forms, all submissions
- **Testability:** manual — No axe-core rule applies. Requires walking every submission flow.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. For every form that submits information, check the submission is reversible, checked for errors with a chance to correct, or confirmed/reviewed.
  2. Verify confirm steps allow correction before final submission.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Contact or survey form posts immediately with no review or undo.
  - Pattern: Settings saved instantly with no way to revert.
- **Sufficient techniques:** Following the sufficient techniques for Success Criterion 3.3.4 for all forms that require the user to submit information
- **Pass/fail example:**

  Pass:

  ```html
  <p>Message sent. <button>Undo</button></p>
  ```

  Fail:

  ```html
  <form action="/survey"><button>Submit</button></form> <!-- no review, no undo -->
  ```

<a id="wcag-3-3-7"></a>
### WCAG-3.3.7 — Redundant Entry (Level A) — new in 2.2

Spec: <https://www.w3.org/TR/WCAG22/#redundant-entry> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry.html>

- **Text:**

  > Information previously entered by or provided to the user that is required to be entered again in the same process is either:
  >
  > - auto-populated, or
  > - available for the user to select.
  >
  > Except when:
  >
  > - re-entering the information is essential,
  > - the information is required to ensure the security of the content, or
  > - previously entered information is no longer valid.

- **Applies to:** forms, multi-step processes, checkout, registration
- **Testability:** manual — No axe-core rule applies. A static scanner can spot duplicated fields (same `name`/`autocomplete` token across steps) as candidates; a human walks the process to confirm previously entered data is auto-populated or selectable.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Walk each multi-step process in one session.
  2. List information the user is asked for more than once.
  3. Check repeated information is auto-populated or available to select (e.g. "same as billing address").
  4. Accept exceptions: re-entry essential (memory game), needed for security (password confirmation), or the earlier data is no longer valid.
- **Common failures:**
  - No W3C failure techniques are documented for this SC.
  - Pattern: Shipping and billing address both typed from scratch with no "same as" option.
  - Pattern: Step 3 asks again for the email entered in step 1.
  - Pattern: Going back in a wizard clears previously entered fields.
- **Sufficient techniques:**
  - G221 — Provide data from a previous step in a process
- **Pass/fail example:**

  Pass:

  ```html
  <label><input type="checkbox" checked> Billing address same as shipping</label>
  ```

  Fail:

  ```html
  <h2>Step 3: Billing</h2>
  <label for="b1">Address line 1</label><input id="b1"> <!-- shipping address already given in step 2 -->
  ```

<a id="wcag-3-3-8"></a>
### WCAG-3.3.8 — Accessible Authentication (Minimum) (Level AA) — new in 2.2

Spec: <https://www.w3.org/TR/WCAG22/#accessible-authentication-minimum> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html>

- **Text:**

  > A cognitive function test (such as remembering a password or solving a puzzle) is not required for any step in an authentication process unless that step provides at least one of the following:
  >
  > - **Alternative:** Another authentication method that does not rely on a cognitive function test.
  > - **Mechanism:** A mechanism is available to assist the user in completing the cognitive function test.
  > - **Object Recognition:** The cognitive function test is to recognize objects.
  > - **Personal Content:** The cognitive function test is to identify non-text content the user provided to the website.
  >
  > *Note 1:* "Object recognition" and "Personal content" may be represented by images, video, or audio.
  >
  > *Note 2:* Examples of mechanisms that satisfy this criterion include:
  >
  > - support for password entry by password managers to reduce memory need, and
  > - copy and paste to reduce the cognitive burden of re-typing.

- **Applies to:** authentication, login, password fields, CAPTCHA, one-time codes
- **Testability:** assisted — No axe-core rule applies. A static scanner can flag `onpaste` / `onPaste` handlers that `preventDefault`, `autocomplete="off"` on username/password fields, and split one-time-code inputs; a page runner can test paste and password-manager autofill. A human confirms whether any cognitive function test is used without an alternative, mechanism, or allowed exception (object/personal content recognition).
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Walk every login, sign-up, step-up and password-reset step.
  2. Identify any cognitive function test (remember a password, transcribe a code, solve a puzzle).
  3. Check an alternative method exists or a mechanism assists (paste allowed, password manager autofill, copy-paste of codes, email link, passkey).
  4. Accept object recognition or recognising user-supplied personal content (AA only).
  5. Check CAPTCHA types used and that a non-cognitive alternative is available.
- **Common failures:**
  - F109 — Failure of Success Criterion 3.3.8 and 3.3.9 due to preventing password or code re-entry in the same format
  - Pattern: Password field that blocks paste: `onPaste={e => e.preventDefault()}`.
  - Pattern: `autocomplete="off"` or non-standard field names that stop password managers.
  - Pattern: OTP split into 6 inputs that break paste.
  - Pattern: Text-transcription CAPTCHA with no alternative.
- **Sufficient techniques:**
  - G218 — Email link authentication
  - H100 — Providing properly marked up email and password inputs
- **Pass/fail example:**

  Pass:

  ```html
  <label for="u">Email</label><input id="u" type="email" autocomplete="username">
  <label for="p">Password</label><input id="p" type="password" autocomplete="current-password">
  ```

  Fail:

  ```jsx
  <input type="password" autoComplete="off" onPaste={e => e.preventDefault()} />
  ```

<a id="wcag-3-3-9"></a>
### WCAG-3.3.9 — Accessible Authentication (Enhanced) (Level AAA) — new in 2.2

Spec: <https://www.w3.org/TR/WCAG22/#accessible-authentication-enhanced> · Understanding: <https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-enhanced.html>

- **Text:**

  > A cognitive function test (such as remembering a password or solving a puzzle) is not required for any step in an authentication process unless that step provides at least one of the following:
  >
  > - **Alternative:** Another authentication method that does not rely on a cognitive function test.
  > - **Mechanism:** A mechanism is available to assist the user in completing the cognitive function test.

- **Applies to:** authentication, login, CAPTCHA, image-recognition challenges
- **Testability:** assisted — Same tool support as 3.3.8 (paste-blocking and autocomplete heuristics, autofill tests); a human confirms that no cognitive function test remains, including object or personal-content recognition, unless an alternative or mechanism is available.
  - **axe-core rules (4.13.0):** none
- **Test procedure:**
  1. Apply the 3.3.8 procedure.
  2. Additionally treat object recognition ("select all traffic lights") and personal-content recognition ("pick your photo") as failures unless an alternative or mechanism is provided.
  3. Confirm an alternative such as passkey, email magic link or OAuth is offered.
- **Common failures:**
  - F109 — Failure of Success Criterion 3.3.8 and 3.3.9 due to preventing password or code re-entry in the same format
  - Pattern: Image-recognition CAPTCHA as the only way through login.
  - Pattern: "Choose the picture you uploaded" as a security step with no alternative.
  - Pattern: Any 3.3.8 failure pattern.
- **Sufficient techniques:**
  - G218 — Email link authentication
  - H100 — Providing properly marked up email and password inputs
- **Pass/fail example:**

  Pass:

  ```html
  <button type="button" id="passkey">Sign in with a passkey</button>
  <a href="/login/email-link">Email me a sign-in link</a>
  ```

  Fail:

  ```html
  <p>Select all images with bicycles to continue.</p><div class="captcha-grid">…</div>
  ```
