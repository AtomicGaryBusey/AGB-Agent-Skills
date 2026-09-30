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

- K3: The small inline 'access guide' link in the fine print at events.html:29 (CSS styles.css:200, 14px text, about 98.5 x 16 CSS px). The 2.5.8 Inline exception applies (target in a sentence, size constrained by line-height), it is underlined, and it has ample contrast. Reporting it as a 2.5.8 target-size failure is a false positive.
- K6: The sticky header on index.html (html.pad-for-header at index.html:2, styles.css:5 scroll-padding-top: 14rem). scroll-padding keeps focused elements clear of the header (technique C43), so 2.4.11 is met on index.html. Reporting the index page's sticky header as obscuring focus is a false positive. The SAME sticky rule on catalog.html (no scroll-padding) is a real defect and does not count.

How to judge each item:
- Findings about OTHER problems that happen to mention the same file, line or
  success criterion do not count (for example a real defect on a neighbouring
  element, or the same technique used wrongly on a different page).
- Calling the property compliant, passing, excepted or "no finding" is fine.
  So is a best-practice remark, an Advisory or Review note, or a note that it
  matters only at AAA, when it is clearly not presented as a Level A/AA
  violation.

If FAIL, name the decoy.
