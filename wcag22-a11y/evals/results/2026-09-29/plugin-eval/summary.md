# wcag22-a11y plugin eval summary

Total cost (agent + judge): $5.17
Partial: False 

| Case | Run | Skill used | Recall | Missed | Severity match | Mismatched | Decoy rows flagged (regex) | Decoy judge | Decoy verdicts | No peek | Cost | Turns | Error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bw-decoys | 1 | True | - | - | - | - | HK3 | True | True | True | $0.44 | 17 | - |
| bw-operable | 1 | True | 7/8 | H15 | 7/8 | - | HK3, HK5 | True | - | True | $0.78 | 29 | - |
| bw-perceivable | 1 | True | 8/9 | H26 | 8/9 | - | none | False | - | True | $0.86 | 30 | - |
| bw-understandable-robust | 1 | True | 9/9 | - | 9/9 | - | none | - | - | True | $0.61 | 28 | - |
| wcag-decoys | 1 | True | - | - | - | - | none | True | True | True | $0.36 | 10 | - |
| wcag-operable | 1 | True | 10/11 | D19 | 10/11 | - | K3, K6 | True | - | True | $0.76 | 19 | - |
| wcag-perceivable | 1 | True | 10/10 | - | 10/10 | - | K1 | True | - | True | $0.72 | 21 | - |
| wcag-refusal-caption-poem | 1 | not used: True | - | - | - | - | none | - | - | - | $0.04 | 1 | - |
| wcag-refusal-sql-perf | 1 | not used: True | - | - | - | - | none | - | - | - | $0.08 | 1 | - |
| wcag-understandable-robust | 1 | True | 9/9 | - | 9/9 | - | none | False | - | True | $0.52 | 16 | - |

Overall recall, larkspur (run 1): 29/30 (manual 10/10, rendered 6/7, static 13/13)
Overall recall, brightwater (run 1): 24/26 (manual 9/10, rendered 4/5, static 11/11)
