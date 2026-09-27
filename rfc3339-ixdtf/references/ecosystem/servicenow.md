# ServiceNow (Glide, REST, Flow, Fluent SDK): pointer

ServiceNow has its own reference: [`../servicenow.md`](../servicenow.md). It covers the native
`yyyy-MM-dd HH:mm:ss` UTC profile and how to grade it, the GlideDateTime / GlideDate / REST / Flow / import API
table, the Fluent SDK 4.13.0 findings (probed offline), grep patterns and audit steps, and the claims that need a
live instance ("unverified (needs instance)").

Probe harnesses: `probes/servicenow/` (see its `README.md`).

`rfcdt.py scan` has 10 ServiceNow rules (`SCAN-SN-*`) for Glide, Flow and Fluent code in JS/TS files (two of them,
`SCAN-SN-SYSPARM-DISPLAY` and `SCAN-SN-FLOW-Z-FORMAT`, run on every text file). Verdict words are those of [`README.md`](README.md#how-to-read-the-verdicts).
