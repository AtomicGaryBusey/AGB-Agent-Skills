# ISO 999:1996 adherence — ServiceNow SDK documentation indexes (SDK 4.13.0, Australia docs)

**Scope:** output and code for the one artifact that counts as an index: the `now-sdk explain --list` topic list, a title index to the SDK's bundled docs collection. The docs' front-matter `tags` (markup) were reviewed only where they feed that list.
**Locale:** English content. The baseline run used en-US collation.
**Declared conventions:** none found. There is no introductory note, no documented filing rule, and no documented heading or qualifier convention.
**Summary:** 0 nonconformities, 6 deviations, 1 advisory, 5 editorial review items.

The report cites clause numbers only (the private clause-by-clause guidance used during the audit is not included in this edition). No ServiceNow instance was contacted.

## Scope decisions

The test is the §3.5 definition of an index.

| Artifact | Classification | Why |
|---|---|---|
| `now-sdk explain --list`: 260 entries (`sdk-cli/dist/command/explain/index.js` `printTopicList`, `sdk-api/dist/docs.js` `scanDocs`) | **Index, partial (in scope)** | Alphabetical (`localeCompare`). It interleaves topics from `api/`, `guides/`, `fluent/` and `configuration/`, so it departs from the source arrangement. Each entry identifies one document (§3.2), so it works as a title index (§5). It is partial because the locator is implicit: the heading is also the retrieval key. It has no subheadings and no cross-references. |
| Front-matter `tags` (260 files) | Markup feeding the list | Printed in brackets as a gloss, like a scope note. Their main purpose is search matching. |
| `now-sdk explain <term>` / `--list <term>` | Out | Ranked search results. |
| SDK `docs/` folder | Out | No index, glossary or A–Z file. Seven files carry Docusaurus `sidebar_*` fields, which are navigation. |
| Docs-site "ServiceNow Fluent API reference" (26 children) and "Server API reference" (446 children) | TOC / navigation (out) | The child lists are in exactly the Fluid Topics TOC order (maps `zUlSbxoxKPAWFDGUdAoSCw`, `eJIqiaxRKVcMaR8XQU6_oA`). For context only: linting the Server API titles gives 15 order breaks. |
| Docs-site TOC, search, "Products" facet | Out | Document order, or a search filter with no locators. |
| PDF books: "Build or modify applications" (2,900 pp.) and Australia release notes (1,741 pp.) | TOC only, **no back-of-book index** (out) | The PDF `Keywords` metadata is a flattened keyword dump with no locators. ISO 999 does not require an index to exist, so this is not a finding. |
| `@servicenow/glide` `.d.ts` barrels | Out | Machine-facing `export *` lists. |
| developer.servicenow.com API reference | Not examined | Its content comes from the portal's instance APIs, which the no-instance rule excludes. The same content was examined on the docs site. |
| Platform glossary | Out | Definitions with no locators. |

## Findings

Positions refer to the order of `explain_list_lint.txt`.

| # | Severity | Check ID | Clause | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|
| 1 | Deviation | ISO999-8.1-06 (also 8.4-01; 8.4-02 considered) | §8.1, §8.4 | `printTopicList`: `[...docs].sort((a,b)=>a.name.localeCompare(b.name))` (`index.js:215`) | The collation is hard-wired to the host's default ICU locale. It takes no locale argument, no options and no sort key, and no filing rule is declared. The same English list files differently on different readers' machines. | cs_CZ and sk_SK move 7 topics: `checkboxvariable-api`, `choicecolumn-api`, `choiceset-api` and `choiceset-guide` move after the h… topics, and 3 `scheduled…` topics move. lt_LT moves 4. en_US, C, da, sv, fi, et and tr give identical output. Each run is deterministic (20 of 20 shuffles identical), so this is not raised to 8.4-02. Director reproduced cs_CZ: positions 35–36 → 99–100. | `localeCompare(b,'en',{sensitivity:'base'})` or `Intl.Collator('en')`; declare the rule. |
| 2 | Deviation | ISO999-7.1.3-01 (also 9.2-01, 7.2.2.4-04, 8.4-04) | §7.1.3, §9.2 | Header `# Available topics:` | No introductory note. Nothing explains the `-api`/`-guide`/`-reference`/`-overview` qualifiers, the bracketed gloss, the abbreviations, or the filing rule. | `explain_list_raw.txt` | Add a 2–3 line note. |
| 3 | Deviation | ISO999-4-04 (also 7.2.3.2-01, 6-03) | §4 f), §7.2.3.2 | `scanDocs` keeps only the basename | The folder hierarchy is lost. 81 related topics are spread across the whole alphabet. | `api/table/columns/`: 50 topics at positions 12–246. `service-catalog/variables/`: 31 topics at 18–260. `api/flow/`: 8 topics at 2–253. | Emit subheadings or group headings. |
| 4 | Deviation | ISO999-4-05 (also 6-07, 7.2.2.1-01) | §4 g), §6.3, §7.2.2 | Basenames used as headings | Inconsistent heading forms scatter one subject (about 42 entries). | `custom-action-api` 50 / `wfa-custom-action-guide` 250; `flow-api` 89 / `wfa-flow-guide` 252; `creating-workspaces-guide` 47 / `workspace-api` 259; `ui-page-guide` 228 / `uipage-api` 233. | One normalised term plus a type qualifier. |
| 5 | Deviation | ISO999-4-07 (also 7.5-01, 7.2.1.3.1-02) | §4 i), §7.5.1 | No *see* facility | 15 headings start with an abbreviation (`acl-api`, `atf-guide`, `sla-api`, `sdlc-guide`, 8 `wfa-*` …) and have no entry under the expanded form. | Front matter | Add a `see:` or alias facility. |
| 6 | Deviation | ISO999-8.5-01 (also 8.5-02, 3-03) | §8.5, §3.10 | `<term>-<type>` convention | The hyphenated qualifier files as if it were a word, so a term's main heading files after longer phrases (12 headings). The linter missed this; it was found manually. | `playbook-guide` 152 files after `playbook-activities-guide` 148, `-anti-patterns-guide` 149 and `-datapills-guide` 151. Also affected: `service-portal-guide`, `service-catalog-guide`, `table-guide`, `list-guide`, `dashboard-guide` … | Sort on (term, qualifier rank, rest). |
| 7 | Advisory | ISO999-9.1.2.2-01 | §9.1.2 | `printTopicList` | A 260-line list with no breaks between letter groups. | — | Add group breaks in pretty mode. |

## Editorial review items

1. Slugs vs the terms users actually use: the docs' H1 titles are not used.
2. The tag vocabulary has case-only duplicates (`Acl`/`acl`) and variant forms (`ai agent`/`ai-agent`/`AiAgent`).
3. Title: "Available topics".
4. Coverage: 260 of 260 bundled docs are listed. Topics that exist only on the docs site are a scope question.
5. Whether the table-name tags should become access points.

## Checks not applicable / not run

- **Locators and ranges:** there is one implicit, non-numeric locator per entry. 7.4-07 passes: `scanDocs` throws on a name collision.
- **Cross-references and subheadings:** none exist (findings 3 and 5).
- **Other:** names and titles, numerals, accents and print layout do not apply.
- **The real CLI** was not run, because it sends telemetry. It was reproduced with the SDK's own `scanDocs`.

## Assumptions

English, word-by-word filing (the linter found 25 pairs consistent with word-by-word, and 0 with letter-by-letter). The hyphen is treated as a word break. "Scattered" means more than 30 positions apart. The type suffix is read as a §3.10 qualifier.

## Reproduction

In `scratchpad/iso-eval/servicenow/`:
```
node explain_list.js list > explain_list_raw.txt
python3 to_lint.py explain_list_raw.txt explain_list_lint.txt
python3 ~/.claude/skills/iso999/scripts/iso999_lint.py explain_list_lint.txt --format text --no-auto-preamble
for L in en_US C cs_CZ sk_SK lt_LT; do LANG=$L.UTF-8 LC_ALL=$L.UTF-8 node explain_list.js list > probes/list_$L.txt; done
node probes/shuffle_probe.js
```
`to_lint.py` keeps the order, drops the header and the tag gloss, and appends a stand-in locator: the entry's 1-based position in source order.
