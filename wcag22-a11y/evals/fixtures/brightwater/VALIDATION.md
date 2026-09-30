# Brightwater Transit: blind validation record

This is the one blind use of this fixture, while it was still held out (outside the repository, never used for tuning). It is kept here as the fixture's history. Later results on this fixture are **not blind**. Record them under `evals/results/<date>/` like any other eval run.

The key at the time listed 25 defects (H01-H25) and 6 decoys (HK1-HK6). The run's "Extra #7" below was confirmed and has since been added to `answer-key.md` as **H26**.

---

## Held-out validation, 2026-09-29 (skill at wcag22-a11y 26d4811)

### Tools only (`wcag_audit.py --pages 20`, 2 min 16 s)
Recall 17/25 (SC + file match). Decoys: no fail-level finding within 2 lines of HK1-HK6.
Misses: H01, H04, H07, H08, H09, H18, H20, H23.

### Blind audit with the full skill (one agent, no key access)
Recall 25/25 (every H01-H25 reported with matching SC and file).
Decoys 6/6 clean at Nonconformity level. HK1, HK3, HK4 were raised by the tools and correctly dropped or
passed by the auditor. HK6 was kept as an Advisory citing the logotype exception.
Extra: #7, footer focus ring #0b5cad on #12324f, 1.97:1 (1.4.11). Verified real; the key is missing it (now H26).
Process note: the auditor ran `ls -R` on the skill and saw evals/ file names (not contents) before the warning.
Cost: about 164k subagent tokens, 10.4 min.

### Tool false positives the auditor dropped (repair input)
- keyboard-trap FAIL on native date/datetime-local inputs (segment Tabs)
- contrast-sampled-background on SVG map labels (stroke pixels in the sample box)
- status-message-not-announced on user-requested content (banner prev/next)
- drag-no-alternative on planner rows that have Move up/down buttons
