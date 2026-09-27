# ISO 999:1996 audit of Go, Rust and ServiceNow documentation indexes

Audited 2026-09-25 with the `iso999` skill. Each target was audited independently by a separate agent. The director reproduced the key claims (marked ✔ below). Findings cite clause numbers only. The licensed standard was not opened.

## Scope: what is actually an index

ISO 999 applies to indexes as defined in §3.5. It does not apply to code in general, or to tables of contents.

| Target | In scope | Out of scope (and why) |
|---|---|---|
| **Go 1.27.1** | pkgsite per-package **"Index"**: partial, because the page body is generated in the same order. pkgsite **"Examples"** list. The `go/doc` sorting and grouping code. | `go doc` (no locators), `go doc -all` (the docs themselves), the `/std` directory, the sidebar, the jump-to dialog (search) |
| **Rust 1.98.1** | rustdoc **`all.html`** ("All items"). Module item tables and `sidebar-items.js` (partial, filing checks only). rustdoc source at tag 1.98.1. | `search.index` (search), `crates.js`, source-file lists, help and settings pages |
| **ServiceNow SDK 4.13.0** | **`now-sdk explain --list`** topic list (260 entries): partial, because the heading is also the locator | Docs-site API lists (identical to the TOC order); two PDF books, which have **no back-of-book index**; `.d.ts` barrels; search facets; glossary |

## Results

| Target | Nonconformities | Deviations | Advisories | Editorial |
|---|---|---|---|---|
| Go | 0 | 7 | 3 | 7 |
| Rust | 0 | 5 | 3 | 6 |
| ServiceNow | 0 | 6 | 1 | 5 |

**Why there are no nonconformities.** The only mandatory provision that applies is §8.4. All three generators are deterministic, and each uses one consistent rule. Shuffled-input rebuilds gave identical output for Go (177 packages), Rust and ServiceNow (20 of 20). The rules are just never declared, which makes them Deviations under §8.4, §7.1.3 and §9.2.

## Headline findings

- **Go (D2/D6):** filing is case-sensitive and byte-wise, and `go/doc` compares digits one character at a time. ✔ `go doc math/bits` lists `Len16, Len32, Len64, Len8` (`reader.go:853, 880, 910`, `strings.Compare`). pkgsite corrects the digit order but keeps the case sensitivity.
- **Go (D3):** 617 standard-library functions are filed only under their result type, with no *see* reference. ✔ `time.Now` appears only under `type Time`.
- **Go (D1/D4):** the arrangement by kind, then constructors, then methods is never explained. 4,503 exported constants and 487 variables have no index entry.
- **Rust (1):** `all.html` sorts by raw bytes. ✔ `mod.rs:492-493`: `self.name.cmp(&other.name)`. ✔ The live std page lists `f128, f16, f32, f64, i128 … i8`. Entries out of place: std 239 of 1,942; chrono 14 of 62; time 20 of 136; jiff 28 of 102.
- **Rust (4):** on macOS, ✔ `struct.Apple.html` and `struct.APPLE.html` are the same file (inode 344064627), so the `Apple` link opens "Struct APPLE". This was seen only in the probe crate.
- **Rust (3, 5):** re-exports that are not inlined, and doc aliases, get no entry. Module pages use a natural sort, but the sidebar and `all.html` use byte order.
- **ServiceNow (1):** ✔ `printTopicList` sorts with a bare `localeCompare()` (`explain/index.js:215`), so the order depends on the reader's machine. ✔ Under a Czech locale, `checkboxvariable-api` and `choicecolumn-api` move from positions 35–36 to 99–100.
- **ServiceNow (3–6):** the folder hierarchy is discarded, and related topics are scattered by inconsistent slug forms (`flow-api` vs `wfa-flow-guide`). `playbook-guide` files after the longer `playbook-*-guide` topics. There are no *see* references for abbreviations (`acl`, `atf`, `wfa` …).

## Gaps in the iso999 skill (all three audits)

1. **Numeric locators only.** The linter accepts only numeric locators, so anchor and CLI-key locators needed stand-in numbers (Go, Rust, ServiceNow).
2. **HTML parser.** The linter's HTML reader failed on pkgsite's sibling `<li><ul>` nesting and ignores `<h2>`/`<h3>` section boundaries. On minified HTML every finding is reported as line 1 (Go, Rust).
3. **No filing mode for code identifiers.** There is no camelCase or acronym segmentation. `_` is always treated as a null value, which files identifiers letter-by-letter. There is no way to express "identity depends on case, filing does not" (Go, Rust).
4. **Misattributed rules.** Case-sort errors are reported as 8.2-ORDER or 8.5-ORDER. PAGEORDER fires on deliberate orders by kind. 8.1-DUPLICATE flags case-distinct identifiers. The qualifier logic misses suffix qualifiers (`-api`, `-guide`) and leading ones (`func (recv)`). Displaced blocks are undercounted, because only the first entry of a block is reported.
5. **No classification guidance** for API indexes vs contents lists, kind-partitioned indexes, headings that are their own locator, CLI list+search hybrids, re-exports and aliases as *see* references, or entries that can only be reached through a parent group.
6. **Locale-dependent collation** has no guidance on whether it counts under §8.4 (ServiceNow).

## Files

- `go/REPORT.md`, `rust/REPORT.md`, `servicenow/REPORT.md`: the full reports.
- Evidence, converters, linter inputs and outputs, and probes are in each target folder. See the Reproduction section of each report.
