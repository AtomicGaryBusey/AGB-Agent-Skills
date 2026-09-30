---
type: llm
---
The user asked about the queried items listed below; all of them are
COMPLIANT with WCAG 2.2 Level AA.

- HK1: The fare table's horizontal scrolling at fares.html:43 (div.table-scroll, role="region", tabindex="0", labelled by the caption) with .fare-table { min-width: 760px } at css/site.css:118-119. Data tables are content that needs two-dimensional layout, which 1.4.10 excepts; only the table region scrolls, the page itself does not (scrollWidth 320 at 320px), and the region is keyboard-scrollable. Reporting the table's scrolling as a Reflow failure is a false positive. (The table's td-as-header markup, H02, and red-only peak fares, H04, are real defects and do not count.)
- HK2: The 'Submit claim' button at claim-3.html:46 (#c3-submit), styled by .btn[disabled] at css/site.css:68 (#9aa3ad on #e4e7ea, 2.06:1). The button is disabled until the confirmation box is ticked; 1.4.3 and 1.4.11 exempt inactive user interface components. Enabled, it is white on #0b5cad (6.67:1). Reporting its disabled-state contrast as a failure is a false positive.
- HK3: Drag-to-reorder of the saved trips on planner.html:77-101 (js/planner.js:19-58). Every item also has real 'Move up' and 'Move down' buttons (a single-pointer and keyboard alternative), the instructions name both methods, focus stays on the pressed button, and moves are announced via role="status". Reporting it under 2.5.7 Dragging Movements or 2.1.1 Keyboard is a false positive. (The dashboard component components/SavedTrips.vue, H15, is drag-only and is a real defect; it does not count.)
- HK4: The 20x20px map zoom buttons at map.html:33-36 (.zoom-btn, css/site.css:159-163). They are under 24x24 but meet the 2.5.8 spacing exception: stacked with an 8px gap (centres 28px apart), so 24px circles centred on them do not intersect each other or any other target. Reporting them as a Target Size failure is a false positive.
- HK5: The rider survey dialog at index.html:64-71, a native <dialog> opened with showModal() in js/site.js:1-12, with no custom focus-trap or Escape code. showModal() makes the page inert, moves focus in, closes natively on Escape, and the close handler returns focus to the opener, so there is no keyboard trap (2.1.2) and the focus order is logical (2.4.3). Reporting it as a trap or focus-order failure is a false positive. (The custom email-alerts modal on alerts.html, H10, is a real trap and does not count.)
- HK6: The pale 'Brightwater Transit' wordmark in the header logo link (.logo .wordmark { color: #9cc3e6 } at css/site.css:48, about 1.85:1 on white; markup at lines 12-15 of every page). 1.4.3 exempts text that is part of a logo or brand name, and the link keeps its accessible name and the global focus indicator. Reporting its contrast as a failure is a false positive.

PASS only if the reply gives an explicit verdict for each queried item and
every verdict is "compliant / passes / exception applies / not a Level AA
failure" (a remark that the item could optionally be improved, is best
practice, or would matter only at AAA is acceptable as long as it is not
presented as a Level A/AA failure, nonconformity or deviation).
FAIL if any item is called a Level A/AA failure, nonconformity, deviation or
defect, or if the reply gives no verdict for an item.
