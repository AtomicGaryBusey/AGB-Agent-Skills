# ISO 999:1996 adherence — rustdoc item indexes (Rust 1.98.1)

**Output audited:** `all.html` for the `tricky` probe crate, chrono 0.4.45, time 0.3.55 and jiff 0.2.37, plus std 1.98.1 (fetched from doc.rust-lang.org; generator `1.98.1 (48a229cea)`).
**Code audited:** rustdoc source at tag 1.98.1 (48a229cea), the same version as the installed rustdoc. Module pages and `sidebar-items.js` were checked only as partial targets (filing).
**Locale:** en.
**Declared conventions:** none found.
**Summary:** 0 nonconformities, 5 deviations, 3 advisories, 6 editorial review items.

## Scope classification

| Artifact | Class | Why |
|---|---|---|
| `all.html` | **Index (in scope)** | Alphabetical, and not in source order (a shuffled rebuild gave identical output). Each entry is a path with a hyperlink locator. The page holds up to 13 separate sequences, one per item kind. |
| Module / crate-root `index.html` item tables | **Partial** | A contents list of one module's children, sorted by default. Filing checks only. |
| `sidebar-items.js` | **Partial** | Navigation list. Filing checks only. |
| `search.index` + search JS | **Out** | A search engine. Relevant only because it holds the aliases and re-export names that `all.html` lacks. |
| `crates.js`, `src-files.js`, help, settings, impl lists | **Out** | Navigation or relationship lists. |
| Crate index at the doc root | **Not produced** | Needs the unstable `--enable-index-page`. |
| Local std docs | **Not available** | Homebrew ships no docs, so the web copy was used. |

## Findings

| # | Severity | Check ID | Clause | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|
| 1 | Deviation | ISO999-8.1-01 (also 8.1-02, 8.1-04, 8.2-01/02, 8.3-04, 4-08) | §8.1, §8.2, §8.3 d), §4 j) | `librustdoc/html/render/mod.rs:492-493` `impl Ord for ItemEntry` → `self.name.cmp(&other.name)`, sorted by `e.sort()` in `print_entries` | **Sorted by raw code point.** (a) Two alphabets: `Zebra` < `mod::…`, and `BTreeSet` < `BinaryHeap`. (b) Numbers sorted digit by digit: `f128, f16, f32, f64`; `i128 … i8`; `LN_10` < `LN_2`; `Foo10` < `Foo2`. (c) Accented names after z. (d) Underscore handled inconsistently: `foo_bar` < `foobar`, but `FooBar` < `Foo_Bar`. | Out of place: **std 239 of 1,942** (88 from case, 148 from numbers); **chrono 14/62, time 20/136, jiff 28/102**, all from case. Director reproduced the std primitive order and the comparator at `mod.rs:492-493`. | Build a key per path segment: fold case and accents, treat `_` as a word break, compare numbers by value, and break ties on the raw bytes. Rustdoc's existing `compare_names` (`print_item.rs:2193`) on a folded key would do it. |
| 2 | Deviation | ISO999-8.4-04 (also 7.1.3-01, 9.2-01) | §8.4, §7.1.3, §9.2 | `AllTypes::print` | Nothing explains the arrangement: code-point order, grouping by kind, path headings, which re-exports are listed, and the silent exclusion of `doc(hidden)` items. | `all.html` starts directly with `<h3 id="structs">`. | Add a one-line note, or fix #1. |
| 3 | Deviation (heuristic) | ISO999-7.5-01 (also 4-07, 6-07) | §4 i), §7.5.1, §6.3 | `AllTypes::append` records only canonical or inlined paths | Plain and renamed re-exports and `#[doc(alias)]` names get no entry and no *see* reference. `#[doc(inline)]` re-exports get double entries. | chrono: **16 of 16** plain crate-root re-exports are missing (`ParseError` appears only as `format::ParseError`), while `NaiveDate` and `naive::NaiveDate` are both listed. The probe's `AlphaWidget` is present in `search.index` but absent from `all.html`. | Add a *see* line for each public re-export and alias. |
| 4 | Deviation | ISO999-6-10 (also 7.4-01) | §6.3, §7.4 | `clean/types.rs:803` `html_filename()` = `format!("{type_}.{name}.html")` | On a case-insensitive filesystem, items that differ only by case share one file, so one entry's link opens the other item's page. | Director reproduced: `struct.APPLE.html` and `struct.Apple.html` are inode 344064627, and the page renders "Struct APPLE". 0 cases in std, chrono, time or jiff. Linux is unaffected. | Give colliding files distinct names, or warn. |
| 5 | Deviation (partial scope) | ISO999-6-06 (also 8.4-01, 8.6-01) | §6.3, §8.4 | Module body: `print_item.rs:266-290` (`compare_names`). Sidebar: `context.rs:340-372` (`a.name.cmp`). | Two sort orders on one page. The body lists `Foo1, Foo2, Foo9, Foo10, Foo100`; the sidebar lists `Foo1, Foo10, Foo100, Foo2, Foo9`. | Lint outputs `tricky-mod` vs `tricky-sidebar` / `tricky-all`. | Use one comparator. |
| 6 | Advisory | ISO999-7.1.4-01 | §7.1.4 | `all.html` | Up to 13 separate kind sequences, so readers need to know an item's kind. Defensible because Rust has separate namespaces. | std Types has 220 entries; Structs 542. | Optional combined A–Z view, or kind qualifiers. |
| 7 | Advisory | ISO999-9.1.2.2-01 | §9.4.1.2 | `all.html` | No letter groups or A–Z bar. | std Functions: 583 entries in one `<ul>`. | Add letter anchors. |
| 8 | Advisory (partial) | ISO999-8.4-04 / 8.6-02 | §8.4, §8.6 | `print_item.rs:266-275` | Module tables list stable items before unstable ones without saying so. | Code | Declare it, or add group subheadings. |

**Why no nonconformity:** §8.4 is the only mandatory provision that applies, and code-point order is one consistent, total, deterministic rule. A rebuild with 77 top-level items shuffled gave identical `all.html` and `sidebar-items.js`.

## Linter results rejected or reclassified

- **8.1-DUPLICATE** (`APPLE`/`Apple`, `FooBar`/`Foo_Bar`): rejected, because these are distinct case-significant identifiers. Moved to E2.
- **8.5-ORDER (33):** 32 are case effects of #1. One was rejected: an artifact of flattening `::`.
- **8.2-ORDER:** reclassified to #1.
- **Pairs that depend on the assumption** (misfiled only if CamelCase counts as one word) were kept and flagged. The totals are stable under both readings.

## Editorial review items

- **E1:** deprecation is not shown in `all.html`.
- **E2:** identifiers that differ only by case in the same section.
- **E3:** flat `::` paths vs nested subheadings.
- **E4:** `doc(hidden)` and private items are excluded without notice.
- **E5:** the §7.2.2 heading-form checks do not fit identifiers, so they were marked not applicable.
- **E6:** the double entries for inlined re-exports are acceptable under §7.5.

## Not applicable

- **Not applicable:**
  - Ranges, elision and passim (one hyperlink locator per entry).
  - Cross-reference integrity (none exist; see #3).
  - Names and titles.
  - §8.3 a)–c): identifiers cannot start with a digit.
  - Subheadings.
  - Checks for paged print.
- **Passed:** 9.3.1-01 by analogy, 7.1.4-02 and 3-01.

## Where ISO 999 fits API docs poorly

- **Case:** the case of an identifier is part of its identity but should not affect filing. §8.1 folding was applied to ordering only.
- **Word breaks:** §8.2 was mapped onto `_` and `::` as a declared assumption, cross-checked with CamelCase split into words.
- **Kind partition:** treated as separate indexes (Advisory).
- **Hyperlink locators:** here the §6.3 locator-accuracy check means "does the link open the right item".
- **Re-exports and aliases:** treated as unchosen terms that need *see* references (heuristic).

## Assumptions

- **Filing key:** case-insensitive, accents folded, `::` and `_` runs as word breaks, a leading `_` ignored, CamelCase as one word (with a run that splits it, as a sensitivity check), numbers by value, ties broken on the original string. Filing is word-by-word.
- **Sequences:** each kind section was linted separately.
- **"Out of place":** entries minus the longest run already in order.

## Reproduction

```bash
W=scratchpad/iso-eval/rust
cd $W/ws && CARGO_TARGET_DIR=$W/ws/target cargo doc --offline
cd $W/ws-shuf && CARGO_TARGET_DIR=$W/ws-shuf/target cargo doc --offline --no-deps
curl -sSL -o $W/std-web/all.html https://doc.rust-lang.org/1.98.1/std/all.html
python3 $W/tools/rustdoc2idx.py $W/ws/target/doc/tricky/all.html $W/lint/tricky-all words,raw,camel
python3 ~/.claude/skills/iso999/scripts/iso999_lint.py $W/lint/std-all/primitives.words.txt --format text --filing word --no-auto-preamble
python3 $W/tools/displaced.py $W/lint/std-all/*.words.txt
ls -i $W/ws/target/doc/tricky/struct.Apple.html $W/ws/target/doc/tricky/struct.APPLE.html
```
The converter exports each section in its original order, maps `::` and `_` to spaces, appends ordinal stand-in locators, and writes `map.tsv` with the original names and hrefs.
