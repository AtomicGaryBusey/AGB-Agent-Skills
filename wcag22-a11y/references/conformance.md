# WCAG 2.2 conformance

> **Source and licence.** Normative text quoted in this file (marked as block quotes) is copied verbatim from
> *Web Content Accessibility Guidelines (WCAG) 2.2*, W3C Recommendation, 12 December 2024 edition,
> <https://www.w3.org/TR/WCAG22/>. Copyright © 2024 World Wide Web Consortium.
> <https://www.w3.org/copyright/document-license-2023/>. Status: W3C Recommendation.
> All other text (summaries, testability, procedures, code patterns and examples) is original to this skill.
> See `NOTICE` at the skill root.

Part 1 is our own auditor guidance. Part 2 reproduces WCAG 2.2 section 5 (Conformance) verbatim, with notes in *italics* as in the spec. The normative definitions of *conformance*, *accessibility supported*, *web page*, *process* and *conforming alternate version* are in `glossary.md`.

## Part 1 — Auditor guidance (original to this skill)

### The five conformance requirements at a glance

| # | Requirement | What the auditor checks |
|---|---|---|
| 1 | Conformance level (5.2.1) | Every SC at the target level and below is satisfied (or not applicable), or a conforming alternate version exists at that level. |
| 2 | Full pages (5.2.2) | The whole page is in scope — including every responsive variation and content revealed from the page (dialogs, menus, long descriptions). Parts cannot be excluded. |
| 3 | Complete processes (5.2.3) | If a page is one step of a process (sign-up, checkout), every step is in scope; one failing step fails the process at that level. |
| 4 | Accessibility-supported uses only (5.2.4) | Techniques relied on to pass an SC must actually work with the user agents and assistive technology the audience uses (e.g. an ARIA pattern that screen readers do not expose cannot be relied upon). |
| 5 | Non-interference (5.2.5) | Content not relied upon must not block the rest of the page, and 1.4.2, 2.1.2, 2.3.1 and 2.2.2 apply to all content on the page, even content that is not relied upon. |

### Conformance levels and counts

WCAG 2.2 contains 87 success-criterion sections: 31 at Level A, 24 at Level AA, 31 at Level AAA, plus 4.1.1 Parsing, which is obsolete and removed (86 active criteria). Levels are cumulative:

- **Level A** — the 31 Level A criteria.
- **Level AA** — Level A plus the 24 Level AA criteria = **55 criteria**.
- **Level AAA** — all 86 active criteria. W3C does not recommend AAA as a blanket policy for whole sites because some AAA criteria cannot be met for some content.

### What "audit against WCAG 2.2 AA" means

1. Evaluate every page in scope against all 55 Level A and AA criteria. Each criterion ends as **pass**, **fail** or **not applicable** (a criterion with no matching content on the page is satisfied — e.g. 1.2.2 on a page with no video).
2. Do not test 4.1.1 Parsing as a WCAG 2.2 criterion. Route real markup defects (duplicate IDs referenced by `for`/`aria-labelledby`, broken nesting that changes the accessibility tree) to 1.3.1 or 4.1.2. If a contract or policy still names WCAG 2.0/2.1, the spec notes that authors "may need to continue to test and report 4.1.1" (see the quote below).
3. Include the whole page and all its states: responsive breakpoints, open menus and dialogs, error states, and every step of each process (requirements 2 and 3).
4. Automated tools (axe-core, the static scanner) find a subset of failures only. A clean automated run is not a conformance result; each A/AA criterion marked assisted or manual in `check-index.md` needs human review, usually with a keyboard and at least one screen reader.
5. AAA criteria are out of scope for an AA audit. Report any AAA criteria met as optional extra information (5.3.2), never as failures.
6. A conformance claim is optional. If one is made it must have the five required components of 5.3.1 (date; guideline title, version and URI; level; the pages covered; technologies relied upon).

### New at Level A/AA in WCAG 2.2 (delta from 2.1 AA)

- 2.4.11 Focus Not Obscured (Minimum) (Level AA)
- 2.5.7 Dragging Movements (Level AA)
- 2.5.8 Target Size (Minimum) (Level AA)
- 3.2.6 Consistent Help (Level A)
- 3.3.7 Redundant Entry (Level A)
- 3.3.8 Accessible Authentication (Minimum) (Level AA)
- Removed: 4.1.1 Parsing.

New at AAA: 2.4.12 Focus Not Obscured (Enhanced), 2.4.13 Focus Appearance, 3.3.9 Accessible Authentication (Enhanced).

### Partial conformance statements

WCAG 2.2 defines two forms (5.4 and 5.5). Use the third-party form only for content that is genuinely not under the author's control (user comments, injected ads, aggregated feeds), and identify that content concretely. Use the language form only when the failure is caused by missing accessibility support for a language. Neither form turns a failing page into a conforming one; they describe what would conform. "Partially conforms" is not a WCAG conformance level — in an audit report, list each failing criterion instead.

### Accessibility supported, in practice

A technique only counts toward an SC if the audience's user agents and assistive technology support it. Record which browser and AT combinations were tested (an optional claim component in 5.3.2), and treat an ARIA pattern that fails in mainstream screen readers as not relied upon. The full normative definition is in `glossary.md` under *accessibility supported*.

### Relationship to earlier versions (quoted)

> WCAG 2.2 builds on and is backwards compatible with WCAG 2.1, meaning web pages that conform to WCAG 2.2 are at least as accessible as pages that conform to WCAG 2.1. Requirements have been added that build on 2.1 and 2.0. WCAG 2.2 has removed one success criterion, 4.1.1 Parsing. Authors that are required by policy to conform with WCAG 2.0 or 2.1 will be able to update content to WCAG 2.2, but may need to continue to test and report 4.1.1. Authors following more than one version of the guidelines should be aware of the following additions.
>
> WCAG 2.2 uses the same conformance model as WCAG 2.0. It is intended that sites that conform to WCAG 2.2 also conform to WCAG 2.0 and WCAG 2.1, which means they meet the requirements of any policies that reference WCAG 2.0 or WCAG 2.1, while also better meeting the needs of users on the current Web.

— WCAG 2.2, Introduction, Comparison with WCAG 2.1 (<https://www.w3.org/TR/WCAG22/#comparison-with-wcag-2-1>).

## Part 2 — WCAG 2.2 section 5, Conformance (verbatim)

Source: <https://www.w3.org/TR/WCAG22/#conformance>

> This section lists requirements for conformance to WCAG 2.2. It also gives information about how to make conformance claims, which are optional. Finally, it describes what it means to be accessibility supported, since only accessibility-supported ways of using technologies can be relied upon for conformance. Understanding Conformance includes further explanation of the accessibility-supported concept.
>
> ### 5.1 Interpreting Normative Requirements
>
> The main content of WCAG 2.2 is normative and defines requirements that impact conformance claims. Introductory material, appendices, sections marked as "non-normative", diagrams, examples, and notes are informative (non-normative). Non-normative material provides advisory information to help interpret the guidelines but does not create requirements that impact a conformance claim.
>
> The key words *MAY*, *MUST*, *MUST NOT*, *NOT RECOMMENDED*, *RECOMMENDED*, *SHOULD*, and *SHOULD NOT* are to be interpreted as described in [RFC2119].
>
> ### 5.2 Conformance Requirements
>
> In order for a web page to conform to WCAG 2.2, all of the following conformance requirements must be satisfied:
>
> #### 5.2.1 Conformance Level
>
> One of the following levels of conformance is met in full.
>
> - For Level A conformance (the minimum level of conformance), the web page satisfies all the Level A success criteria, or a conforming alternate version is provided.
> - For Level AA conformance, the web page satisfies all the Level A and Level AA success criteria, or a Level AA conforming alternate version is provided.
> - For Level AAA conformance, the web page satisfies all the Level A, Level AA and Level AAA success criteria, or a Level AAA conforming alternate version is provided.
>
> *Note 1:* Although conformance can only be achieved at the stated levels, authors are encouraged to report (in their claim) any progress toward meeting success criteria from all levels beyond the achieved level of conformance.
>
> *Note 2:* It is not recommended that Level AAA conformance be required as a general policy for entire sites because it is not possible to satisfy all Level AAA success criteria for some content.
>
> #### 5.2.2 Full pages
>
> Conformance (and conformance level) is for full web page(s) only, and cannot be achieved if part of a web page is excluded.
>
> *Note 1:* For the purpose of determining conformance, alternatives to part of a page's content are considered part of the page when the alternatives can be obtained directly from the page, e.g., a long description or an alternative presentation of a video.
>
> *Note 2:* Authors of web pages that cannot conform due to content outside of the author's control may consider a Statement of Partial Conformance.
>
> *Note 3:* A full page includes each variation of the page that is automatically presented by the page for various screen sizes (e.g. variations in a responsive web page). Each of these variations needs to conform (or needs to have a conforming alternate version) in order for the entire page to conform.
>
> #### 5.2.3 Complete processes
>
> When a web page is one of a series of web pages presenting a process (i.e., a sequence of steps that need to be completed in order to accomplish an activity), all web pages in the process conform at the specified level or better. (Conformance is not possible at a particular level if any page in the process does not conform at that level or better.)
>
> *Example:* An online store has a series of pages that are used to select and purchase products. All pages in the series from start to finish (checkout) conform in order for any page that is part of the process to conform.
>
> #### 5.2.4 Only Accessibility-Supported Ways of Using Technologies
>
> Only accessibility-supported ways of using technologies are relied upon to satisfy the success criteria. Any information or functionality that is provided in a way that is not accessibility supported is also available in a way that is accessibility supported. (See Understanding accessibility support.)
>
> #### 5.2.5 Non-Interference
>
> If  technologies  are used in a way that is not accessibility supported, or if they are used in a non-conforming way, then they do not block the ability of users to access the rest of the page. In addition, the web page as a whole continues to meet the conformance requirements under each of the following conditions:
>
> 1. when any technology that is not relied upon is turned on in a user agent,
> 2. when any technology that is not relied upon is turned off in a user agent, and
> 3. when any technology that is not relied upon is not supported by a user agent
>
> In addition, the following success criteria apply to all content on the page, including content that is not otherwise relied upon to meet conformance, because failure to meet them could interfere with any use of the page:
>
> - **1.4.2 - Audio Control**,
> - **2.1.2 - No Keyboard Trap**,
> - **2.3.1 - Three Flashes or Below Threshold**, and
> - **2.2.2 - Pause, Stop, Hide**.
>
> *Note:* If a page cannot conform (for example, a conformance test page or an example page), it cannot be included in the scope of conformance or in a conformance claim.
>
> For more information, including examples, see Understanding Conformance Requirements.
>
> ### 5.3 Conformance Claims (Optional)
>
> Conformance is defined only for web pages. However, a conformance claim may be made to cover one page, a series of pages, or multiple related web pages.
>
> #### 5.3.1 Required Components of a Conformance Claim
>
> Conformance claims are **not required**. Authors can conform to WCAG 2.2 without making a claim. However, if a conformance claim is made, then the conformance claim **must** include the following information:
>
> 1. **Date** of the claim
> 2. **Guidelines title, version and URI**  "Web Content Accessibility Guidelines 2.2 at https://www.w3.org/TR/WCAG22/"
> 3. **Conformance level** satisfied: (Level A, AA or AAA)
> 4. **A concise description of the web pages**, such as a list of URIs for which the claim is made, including whether subdomains are included in the claim.
>   *Note 1:* The web pages may be described by list or by an expression that describes all of the URIs included in the claim.
>   *Note 2:* Web-based products that do not have a URI prior to installation on the customer's website may have a statement that the product would conform when installed.
> 5. A list of the  **web content technologies relied upon**.
>
> *Note 3:* If a conformance logo is used, it would constitute a claim and must be accompanied by the required components of a conformance claim listed above.
>
> #### 5.3.2 Optional Components of a Conformance Claim
>
> In addition to the required components of a conformance claim above, consider providing additional information to assist users. Recommended additional information includes:
>
> - A list of success criteria beyond the level of conformance claimed that have been met. This information should be provided in a form that users can use, preferably machine-readable metadata.
> - A list of the specific technologies that are " *used but not relied upon*."
> - A list of user agents, including assistive technologies that were used to test the content.
> - A list of specific accessibility characteristics of the content, provided in machine-readable metadata.
> - Information about any additional steps taken that go beyond the success criteria to enhance accessibility.
> - A machine-readable metadata version of the list of specific technologies that are relied upon.
> - A machine-readable metadata version of the conformance claim.
>
> *Note 1:* Refer to Understanding Conformance Claims for more information and example conformance claims.
>
> *Note 2:* Refer to Understanding Metadata for more information about the use of metadata in conformance claims.
>
> ### 5.4 Statement of Partial Conformance - Third Party Content
>
> Web pages that will later have additional content added can use a 'statement of partial conformance'. For example, an email program, a blog, an article that allows users to add comments, or applications supporting user-contributed content. Another example would be a page, such as a portal or news site, composed of content aggregated from multiple contributors, or sites that automatically insert content from other sources over time, such as when advertisements are inserted dynamically.
>
> In these cases, it is not possible to know at the time of original posting what the uncontrolled content of the pages will be. It is important to note that the uncontrolled content can affect the accessibility of the controlled content as well. Two options are available:
>
> 1. A determination of conformance can be made based on best knowledge. If a page of this type is monitored and repaired (non-conforming content is removed or brought into conformance) within two business days, then a determination or claim of conformance can be made since, except for errors in externally contributed content which are corrected or removed when encountered, the page conforms. No conformance claim can be made if it is not possible to monitor or correct non-conforming content;
>   **OR**
> 2. A "statement of partial conformance" may be made that the page does not conform, but could conform if certain parts were removed. The form of that statement would be, "This page does not conform, but would conform to WCAG 2.2 at level X if the following parts from uncontrolled sources were removed." In addition, the following would also be true of uncontrolled content that is described in the statement of partial conformance:
>   1. It is not content that is under the author's control.
>   2. It is described in a way that users can identify (e.g., they cannot be described as "all parts that we do not control" unless they are clearly marked as such.)
>
> ### 5.5 Statement of Partial Conformance - Language
>
> A "statement of partial conformance due to language" may be made when the page does not conform, but would conform if accessibility support existed for (all of) the language(s) used on the page. The form of that statement would be, "This page does not conform, but would conform to WCAG 2.2 at level X if accessibility support existed for the following language(s):"
>
> ### 5.6 Privacy Considerations
>
> *This section is non-normative.*
>
> Success criteria within this specification which the Working Group has identified possible implications for privacy, either by providing protections for end users or which are important for website providers to take in to consideration when implementing features designed to protect user privacy, are listed below. This list reflects the current understanding of the Working Group but other Success criteria may have privacy implications that the Working Group is not aware of at the time of publishing.
>
> Success criteria within this specification that may relate to privacy are:
>
> - 2.2.6 Timeouts (AAA)
> - 3.3.7 Redundant Entry (A)
>
> ### 5.7 Security Considerations
>
> *This section is non-normative.*
>
> Success criteria within this specification which the Working Group has identified possible implications for security, either by providing protections for end users or which are important for website providers to take in to consideration when implementing features designed to protect user security, are listed below. This list reflects the current understanding of the Working Group but other Success criteria may have security implications that the Working Group is not aware of at the time of publishing.
>
> Success criteria within this specification that may relate to security are:
>
> - 1.1.1 Non-text Content (A)
> - 1.3.5 Identify Input Purpose (AA)
> - 1.4.7 Low or No Background Audio (AAA)
> - 2.2.1 Timing Adjustable (A)
> - 2.2.5 Re-authenticating (AAA)
> - 2.2.6 Timeouts (AAA)
> - 2.5.6 Concurrent Input Mechanisms (AAA)
> - 3.3.3 Error Suggestion (AA)
> - 3.3.7 Redundant Entry (A)
> - 3.3.8 Accessible Authentication (Minimum) (AA)
> - 3.3.9 Accessible Authentication (Enhanced) (AAA)
