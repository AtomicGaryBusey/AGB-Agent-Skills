# rfc3339-ixdtf plugin eval summary

Total cost (agent + judge): $2.29
Partial: False 

| Case | Run | Skill used | Recall | Missed | Severity match | Mismatched | Decoy rows flagged (regex) | Decoy judge | Decoy verdicts | No peek | Cost | Turns | Error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rfc-consumer | 1 | True | 9/9 | - | 9/9 | - | none | True | - | True | $0.71 | 10 | - |
| rfc-decoys | 1 | True | - | - | - | - | none | True | True | True | $0.45 | 10 | - |
| rfc-producer | 1 | True | 6/6 | - | 5/6 | P5 | none | True | - | True | $0.45 | 9 | - |
| rfc-refusal-duration | 1 | not used: True | - | - | - | - | none | - | - | - | $0.06 | 1 | - |
| rfc-refusal-httpdate | 1 | not used: True | - | - | - | - | none | - | - | - | $0.05 | 1 | - |
| rfc-schema | 1 | True | 3/3 | - | 3/3 | - | none | False | - | True | $0.56 | 10 | - |
