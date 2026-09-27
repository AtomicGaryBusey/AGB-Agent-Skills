# rfc3339-ixdtf plugin eval summary

Total cost (agent + judge): $2.23
Partial: False 

| Case | Run | Skill used | Recall | Missed | Severity match | Mismatched | Decoy rows flagged (regex) | Decoy judge | Decoy verdicts | No peek | Cost | Turns | Error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rfc-consumer | 1 | True | 9/9 | - | 9/9 | - | D2, D3 | False | - | True | $0.63 | 11 | - |
| rfc-decoys | 1 | True | - | - | - | - | D2 | False | False | True | $0.51 | 11 | - |
| rfc-producer | 1 | True | 6/6 | - | 5/6 | P5 | D1 | False | - | True | $0.50 | 11 | - |
| rfc-refusal-duration | 1 | not used: True | - | - | - | - | none | - | - | - | $0.07 | 1 | - |
| rfc-refusal-httpdate | 1 | not used: True | - | - | - | - | none | - | - | - | $0.05 | 1 | - |
| rfc-schema | 1 | True | 3/3 | - | 3/3 | - | D1 | False | - | True | $0.47 | 11 | - |
