# wcag22-a11y plugin eval summary

Total cost (agent + judge): $5.53
Partial: False 

| Case | Run | Skill used | Recall | Missed | Severity match | Mismatched | Decoy rows flagged (regex) | Decoy judge | Decoy verdicts | No peek | Cost | Turns | Error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bw-decoys | 1 | True | - | - | - | - | none | True | True | True | $0.40 | 14 | - |
| bw-operable | 1 | True | 8/8 | - | 8/8 | - | none | False | - | True | $1.07 | 31 | - |
| bw-perceivable | 1 | True | 9/9 | - | 0/9 | H01, H02, H03, H04, H05, H06, H07, H08, H26 | none | True | - | True | $0.96 | 31 | - |
| bw-understandable-robust | 1 | True | 9/9 | - | 9/9 | - | none | - | - | True | $0.78 | 31 | - |
| wcag-decoys | 1 | True | - | - | - | - | none | True | True | True | $0.40 | 10 | - |
| wcag-operable | 1 | True | 11/11 | - | 11/11 | - | K6 | False | - | True | $0.64 | 19 | - |
| wcag-perceivable | 1 | True | 10/10 | - | 10/10 | - | none | False | - | True | $0.62 | 20 | - |
| wcag-refusal-caption-poem | 1 | not used: True | - | - | - | - | none | - | - | - | $0.04 | 1 | - |
| wcag-refusal-sql-perf | 1 | not used: True | - | - | - | - | none | - | - | - | $0.08 | 1 | - |
| wcag-understandable-robust | 1 | True | 9/9 | - | 9/9 | - | none | False | - | True | $0.53 | 16 | - |

Overall recall, larkspur (run 1): 30/30 (manual 10/10, rendered 7/7, static 13/13)
Overall recall, brightwater (run 1): 26/26 (manual 10/10, rendered 5/5, static 11/11)
