# ISO 999:1996 adherence — Go documentation indexes (go/doc + pkgsite "Index")

**Output audited:** the pkgsite per-package "Index" and "Examples" lists for 8 std packages (1,002 index entries and 148 example entries), plus the go/doc data model rendered for all 177 public std packages (6,078 entries).
**Code audited:** `$GOROOT/src/go/doc` (Go 1.27.1) and the rendering code in `golang.org/x/pkgsite@v0.5.0`: `internal/godoc/dochtml`, `internal/natural`, `static/doc/body.tmpl` and `_doc.css`.
**Markup:** not applicable.
**Locale:** en.
**Declared conventions:** none found.
**Summary:** 0 nonconformities, 7 deviations, 3 advisories, 7 editorial review items.

## Scope decision

| Artifact | Classification | Reason |
|---|---|---|
| **pkgsite per-package "Index"** | **Partial: in scope, with caveats** | It has headings (signatures), subheadings (constructors and methods), anchor locators, and an order (by kind, then name) that is independent of the source files. But pkgsite generates the page body in the same order, so it also works as a contents list. It includes the TOC rows "Constants", "Variables" and "Bugs". Audited as an index because readers use it as the finding list for an API. |
| **pkgsite "Examples" list** | **In scope** (a second index, §7.1.4) | A flat alphabetical list with qualifiers in parentheses and anchor locators. |
| **go/doc data model** | **Code in scope** | It decides the grouping and base order used by every Go doc renderer. |
| `go doc <pkg>` | Out (listing) | No locators. The D6 evidence comes from it. |
| `go doc -all` | Out | The documentation itself. |
| pkgsite `/std` table | Out (collection directory) | Linted for information only (`utf16` < `utf8`, `sha256` < `sha3`). |
| Sidebar outline, Source Files | Out | A contents list and a listing. |
| Jump-to dialog | Out (search) | Counted as a mitigation for D3 and D4. |
| x/tools godoc | Not audited | Deprecated and not installed. |

## Findings

| # | Severity | Check ID | Clause | Location | Finding | Evidence | Fix |
|---|---|---|---|---|---|---|---|
| D1 | Deviation | ISO999-8.4-04 (also 8.6-02, 7.1.3-01, 9.2-01) | §8.4, §8.6, §7.1.3, §9.2 | `body.tmpl:17-62`; `dochtml.go:147-170`; `reader.go:863-913`, `doc.go:60-63` | The arrangement is not self-evident and is never declared. Under each type, constructors A–Z come before methods A–Z, in two unlabelled lists. At the top level, entries are grouped by kind and the alphabet restarts at each group. The order is deterministic, so this is not a §8.4 nonconformity. | `time.Time` (54 subheadings), `reflect.Value` (93), `math/big.Int` (62). Std-wide: **203 subheading restarts** and **97 packages** where the alphabet restarts between functions and types. | Add an index legend, or label or merge the two runs. |
| D2 | Deviation | ISO999-8.1-01 (also 8.1-02, 8.1-04, 8.1-06) | §8.1 | pkgsite `natural/compare.go:55-58`, `dochtml.go:172-174`; go/doc `reader.go:853, 880, 910` (`strings.Compare`) | Case-sensitive, byte-wise filing that cannot be tailored. Acronyms, `_` and non-ASCII names misfile. | Under the camelCase-word assumption: **24 misfiled pairs** std-wide (`HTTP2Config` < `Handler`; `ISOWeek` < `In`; `UTC` < `Unix`). With whole-identifier folding: 83. Probe: `Élan` files after `Zeta`. | Casefold, segment identifiers, compare numbers by value, and break ties on raw bytes. |
| D3 | Deviation (heuristic) | ISO999-6-01 (also 7.5-01, 4-07) | §6.1, §7.5, §4 | `reader.go:434-470` (`readFunc` factory association) | A function that returns a package type is filed only under that type, with no entry among the functions and no *see* reference. | **617 functions** std-wide. Director confirmed that `time.Now` appears only under `type Time`. Mitigated by jump-to. | Add a *see* line or a double entry, or at least mention it in the legend. |
| D4 | Deviation (heuristic) | ISO999-7.1.1-01 (also 7.1.1-02) | §7.1.1 | `body.tmpl:20-21` | Exported constants and variables are not indexed, and nothing says so. They are reachable only through the single "Constants" and "Variables" rows. | **4,503 constants and 487 variables** (`net/http` has 85 and 28). The body anchors already exist. | Index them, or state the exclusion. |
| D5 | Deviation | ISO999-9.4.1.4-01 | §9.1.2.4, §9.4.1.4 | `_doc.css:95-103` | No hanging indent for continuation lines: a wrapped signature starts again at the item's left edge. | Signatures up to 102 characters (`go/ast` `NewPackage`). | Use `padding-left: X; text-indent: -X`. |
| D6 | Deviation | ISO999-8.3-04 | §8.3 d) | `reader.go:852-858, 879-881, 909-911`; `example.go:680-681` | go/doc compares digits character by character. pkgsite corrects this, but `go doc`, x/tools godoc and IDEs inherit it. | Director reproduced: `go doc math/bits` → `Len, Len16, Len32, Len64, Len8`. 15 std-wide 8.3-ORDER hits in go/doc order, 0 in pkgsite order. | Move pkgsite's `natural.Compare` into go/doc. |
| D7 | Deviation (heuristic, low) | ISO999-8.4-04 | §8.4 | `dochtml.go:413-427` | Package-level examples file first under the label "Package", without explanation. | `math/big`: `Package (Sqrt2)` comes before `Float (Shift)`. | File them under P, or add a group heading. |
| A1 | Advisory | ISO999-7.2.3.3-01 | §7.2.3.3 | `body.tmpl:41, 49` | The hierarchy is visual only: the subheading lists are siblings of the type's `<li>`, not nested inside it. | Markup | Nest the lists. |
| A2 | Advisory | ISO999-9.1.2.2-01 | §9.4.1.2 | `body.tmpl:19-61` | No letter-group separation. | `go/ast` 224 entries; `reflect.Value` 93 subheadings. | Optional breaks or a jump bar. |
| A3 | Advisory (inferred) | ISO999-8.4-02 | §8.4 | `dochtml.go:157-158, 172-174` | Value groups are sorted with a comparator that treats them all as equal, using an unstable sort. The output currently keeps the order (177 of 177), but relies on unspecified behaviour. | Probe | Skip the sort, or use a stable sort. |

## Confirmed passing

- **7.4-01:** all 1,026 index anchors and 148 example anchors resolve.
- **8.4-02:** output is deterministic across runs and after shuffling files and declarations (177 of 177).
- **8.3-04 (pkgsite):** numbers file by value.
- **8.5-01:** bare term, then qualified forms, then longer names.
- **3-01:** one locator per entry.
- **Layout (9.1.2.3/4, 9.5-01):** set-out.
- **8.2:** no evidence of letter-by-letter filing.

## Editorial review items

1. Is it an index or a contents list? The pkgsite Index has the same order as the page body.
2. Is the grouping by kind self-evident?
3. The title "Index".
4. Headings are full signatures, not noun phrases.
5. Homographs distinguished by a leading receiver (23 pairs).
6. Singular/plural pairs are distinct API members, so they were dismissed.
7. In the Examples list, the sort key's case can differ from the displayed title case.

## Not applicable

- Ranges and multiple locators.
- Cross-references (none are emitted; see D3).
- Leading numerals and roman numerals.
- Names and titles.
- Leading prepositions.
- Paged presentation.
- Serial indexes.
- Lower-case initials: in Go, case decides whether a name is exported.
- Markup.

## Where ISO 999 is a stretch, and how it was graded

- **Locators:** anchors were accepted as locators (§7.4.2.3), so the range checks were not applicable.
- **Index vs contents list:** because of that ambiguity, the §7.1 and §9.2 findings are heuristic Deviations.
- **Case:** folding affects sort values only, with a raw-byte tie-break.
- **camelCase:** declared as the word-by-word segmentation, with both readings reported.
- **Signature headings:** left as an editorial item.
- **Grouping by kind:** graded only on whether it is declared.

## Assumptions

- **Filing:** identifiers are compound terms, segmented at camelCase humps, acronyms, digit runs and `_`. Filing is word-by-word and case-folded, with numbers by value.
- **Subheadings:** constructors and methods are treated as one sibling set.
- **Locators:** anchors were replaced with the line number of their target `id`. Std-wide locators are declaration ordinals.
- **Linter flags:** `--roman off --no-auto-preamble`.
- **Heuristic limit:** hump segmentation mis-splits some acronyms (`IPv6MTUInfo`), so one pair was excluded.

## Reproduction

In `scratchpad/iso-eval/go/`:
```bash
GOBIN=$PWD/bin go install golang.org/x/pkgsite/cmd/pkgsite@latest          # v0.5.0
./bin/pkgsite -gorepo $(go env GOROOT) -http localhost:8765 $(go env GOROOT)/src &
for p in time strings net/http reflect go/ast math/big math/bits sync/atomic; do
  curl -s localhost:8765/$p > html/$(echo $p | tr / _).html; done
for f in html/*.html; do b=$(basename $f .html); [ $b = std ] && continue
  python3 convert.py display $f > txt/$b.display.txt
  python3 convert.py ident   $f > txt/$b.ident.txt
  python3 convert_examples.py $f > txt/$b.examples.txt; done
for f in txt/*.txt; do python3 ~/.claude/skills/iso999/scripts/iso999_lint.py --filing word --roman off --no-auto-preamble $f; done
(cd dumpdoc && go build -o dumpdoc . && ./dumpdoc > ../std_index.json && SHUFFLE=1 ./dumpdoc > ../std_index.shuf.json)
python3 analyze.py std_index.json
go doc math/bits | grep -n 'func Len'
```
Folders: `html/`, `txt/`, `lint/`, `godoc/`, `probe/`, `dumpdoc/` (with a BSD-licensed copy of pkgsite's `natural.Compare`).
