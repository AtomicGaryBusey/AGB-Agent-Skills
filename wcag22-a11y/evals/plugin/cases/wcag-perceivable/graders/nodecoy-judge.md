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

- K1: The leaf divider image at index.html:52 (img.divider, rule-leaves.svg) with alt="" and role="presentation". Pure decoration hidden from assistive technology is exactly what 1.1.1 requires (H67); role=presentation is redundant but valid. Reporting it as missing a text alternative, or calling the redundant role a defect, is a false positive. (The OTHER divider at index.html:30, flourish.svg, with a descriptive alt, is a real defect and does not count.)
- K2: The events schedule data table (events.html:57-82, table.schedule) with <caption>, <th scope="col"> and <th scope="row">. It is genuine tabular data and scope/caption make header relationships programmatic (1.3.1, H63, H39). Calling it layout-table misuse or a 1.3.1 failure is a false positive.
- K5: The low-contrast logotype text 'Larkspur Library' (.logo-word, #c9b6ef on white, styles.css:40; markup at line 12 of each page). The 1.4.3 Logotypes exception applies (text that is part of a logo or brand name has no contrast requirement), and the logo is not a link or control. Reporting it as a contrast failure is a false positive.
- N1: The heading-level skip at index.html:77-78 (h2 'Visit us' followed by h4 'Opening hours'). WCAG 2.2 has no SC requiring sequential heading levels; the heading is marked up as a heading so 1.3.1 is met. At most a best-practice remark; reporting it as a Nonconformity or Deviation is a false positive.
- N3: The events schedule table at 320px (events.html:57, div.table-scroll; styles.css:202). It scrolls inside its own labelled, focusable region and the page itself does not scroll sideways; 1.4.10 Note 2 lets data tables use two-dimensional layout. Reporting it as a reflow failure is a false positive. (The featured-row grid on index.html, styles.css:105-107, is a real reflow defect and does not count.)

How to judge each item:
- Findings about OTHER problems that happen to mention the same file, line or
  success criterion do not count (for example a real defect on a neighbouring
  element, or the same technique used wrongly on a different page).
- Calling the property compliant, passing, excepted or "no finding" is fine.
  So is a best-practice remark, an Advisory or Review note, or a note that it
  matters only at AAA, when it is clearly not presented as a Level A/AA
  violation.

If FAIL, name the decoy.
