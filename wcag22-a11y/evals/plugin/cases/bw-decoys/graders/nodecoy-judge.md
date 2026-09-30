---
type: llm
weight: 0.001
---
PASS if none of the properties listed below is reported as a Level A or AA
violation. FAIL if any listed property is itself reported as one: a
findings-table row with severity Nonconformity or Deviation whose subject IS
that property, or a statement that the property violates a Level A or AA
success criterion.

The reply is a WCAG 2.2 Level AA accessibility audit report. Each listed item
is a specific property of the audited project that is known to be COMPLIANT
(a decoy or a non-scored note).

- HK1: The fare table's horizontal scrolling at fares.html:43 (div.table-scroll, role="region", tabindex="0", labelled by the caption) with .fare-table { min-width: 760px } at css/site.css:118-119. Data tables are content that needs two-dimensional layout, which 1.4.10 excepts; only the table region scrolls, the page itself does not (scrollWidth 320 at 320px), and the region is keyboard-scrollable. Reporting the table's scrolling as a Reflow failure is a false positive. (The table's td-as-header markup, H02, and red-only peak fares, H04, are real defects and do not count.)
- HK2: The 'Submit claim' button at claim-3.html:46 (#c3-submit), styled by .btn[disabled] at css/site.css:68 (#9aa3ad on #e4e7ea, 2.06:1). The button is disabled until the confirmation box is ticked; 1.4.3 and 1.4.11 exempt inactive user interface components. Enabled, it is white on #0b5cad (6.67:1). Reporting its disabled-state contrast as a failure is a false positive.
- HK3: Drag-to-reorder of the saved trips on planner.html:77-101 (js/planner.js:19-58). Every item also has real 'Move up' and 'Move down' buttons (a single-pointer and keyboard alternative), the instructions name both methods, focus stays on the pressed button, and moves are announced via role="status". Reporting it under 2.5.7 Dragging Movements or 2.1.1 Keyboard is a false positive. (The dashboard component components/SavedTrips.vue, H15, is drag-only and is a real defect; it does not count.)
- HK4: The 20x20px map zoom buttons at map.html:33-36 (.zoom-btn, css/site.css:159-163). They are under 24x24 but meet the 2.5.8 spacing exception: stacked with an 8px gap (centres 28px apart), so 24px circles centred on them do not intersect each other or any other target. Reporting them as a Target Size failure is a false positive.
- HK5: The rider survey dialog at index.html:64-71, a native <dialog> opened with showModal() in js/site.js:1-12, with no custom focus-trap or Escape code. showModal() makes the page inert, moves focus in, closes natively on Escape, and the close handler returns focus to the opener, so there is no keyboard trap (2.1.2) and the focus order is logical (2.4.3). Reporting it as a trap or focus-order failure is a false positive. (The custom email-alerts modal on alerts.html, H10, is a real trap and does not count.)
- HK6: The pale 'Brightwater Transit' wordmark in the header logo link (.logo .wordmark { color: #9cc3e6 } at css/site.css:48, about 1.85:1 on white; markup at lines 12-15 of every page). 1.4.3 exempts text that is part of a logo or brand name, and the link keeps its accessible name and the global focus indicator. Reporting its contrast as a failure is a false positive.

How to judge each item:
- Findings about OTHER problems that happen to mention the same file, line or
  success criterion do not count (for example a real defect on a neighbouring
  element, or the same technique used wrongly on a different page).
- Calling the property compliant, passing, excepted or "no finding" is fine.
  So is a best-practice remark, an Advisory or Review note, or a note that it
  matters only at AAA, when it is clearly not presented as a Level A/AA
  violation.

If FAIL, name the decoy.
