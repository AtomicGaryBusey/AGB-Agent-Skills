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

- K4: The step-2 object-recognition CAPTCHA on login.html:43-55 (#captcha-form, 'select every picture that shows a book', with an audio alternative button). 3.3.8 (AA) explicitly allows object recognition as an exception, and it meets the 1.1.1 CAPTCHA exception. Reporting the CAPTCHA as a 3.3.8 or 1.1.1 failure is a false positive (noting it would fail AAA 3.3.9 is fine). The paste-blocked PIN at login.html:37 is a separate real defect.
- N2: The confirm-PIN field 'Type your PIN again' at signup.html:66-67. The 3.3.7 security exception applies (Understanding 3.3.7 names password confirmation). Reporting it as a Redundant Entry failure is a false positive. (The re-asked email at signup.html:58-59 is a real defect and does not count.)

How to judge each item:
- Findings about OTHER problems that happen to mention the same file, line or
  success criterion do not count (for example a real defect on a neighbouring
  element, or the same technique used wrongly on a different page).
- Calling the property compliant, passing, excepted or "no finding" is fine.
  So is a best-practice remark, an Advisory or Review note, or a note that it
  matters only at AAA, when it is clearly not presented as a Level A/AA
  violation.

If FAIL, name the decoy.
