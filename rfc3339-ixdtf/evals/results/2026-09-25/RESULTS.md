# rfc3339-ixdtf eval results, 2026-09-25

Model: claude-opus-5-5 (default). 1 run per case, single arm (`--ablation none`), `--no-publish`, static review only (no Bash; see evals/README.md). Judge: haiku (attempt 1), sonnet (attempt 2).

## Plugin eval: final run (`plugin-eval/`, attempt 2)

| Case | Skill used | Recall (scripted) | Severity match | Decoy FPs (manual adjudication) | Cost |
|---|---|---|---|---|---|
| rfc-producer | yes | 6/6 (P1-P6) | 5/6: P5 reported as Advisory, key says Deviation (RFC 9557 §2 SHOULD) | 0 | $0.45 |
| rfc-consumer | yes | 9/9 (C1-C9) | 9/9 | 0 | $0.71 |
| rfc-schema | yes | 3/3 (S1-S3) | 3/3 | 0 (judge flagged an Advisory that the schema doesn't enforce the documented UTC/millisecond profile of received_at/start_utc; that is about schema enforcement, not a claim that 3 digits + Z is invalid) | $0.56 |
| rfc-decoys | yes | n/a | n/a | 0; all three queried items judged compliant (judge PASS) | $0.45 |
| rfc-refusal-duration | not used (pass) | | | | $0.06 |
| rfc-refusal-httpdate | not used (pass) | | | | $0.05 |

Total: $2.29 (agent + judge). No run read the answer key.
P5 was also Advisory in attempt 1, so it is consistent: SKILL.md rule 1 maps SHOULD to Deviation, but the skill treats the Z/+00:00 choice as Advisory. Either the key or the skill's Z-semantics guidance needs to change.

## Attempt 1 (`plugin-eval-attempt1/`), superseded
Same recall (6/6, 9/9, 3/3), severity 17/18 (P5). Tooling fault: skill references were not readable (fixed with Read grants). The haiku judge failed every case, and the regex decoy graders for D2/D3 fired on real findings (for example C6's fix text contains `[Tt]`). Those two regex graders were removed; decoys are judged by the llm grader plus manual review.

## Trigger eval (`triggers.json`, `triggers.log`)
TP 6, FN 4, FP 0, TN 10: precision 1.0, recall 0.6, accuracy 0.8 (1 run per prompt).
Missed (should trigger): "Parse `…+02:00[Europe/Paris]` in Go", "Handle `[u-ca=hebrew]` suffix tags in our deserializer", "Is a leap second `23:59:60` legal in our log format?", "Should we send `Z` or `+00:00` when the offset is unknown?". The first three went straight to Bash; the last was answered with no tool. That is input for T2-4 (description trigger phrases).
All 6 triggers were the installed skill, not run_eval's temporary copy.
Cost: not metered (see iso999 note).
