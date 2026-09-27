# ServiceNow probes

Findings and the audit procedure: `references/servicenow.md`. Every file here runs **offline** except
`instance_probe.js`, which is optional and needs an instance that you own.

| File | Runs on | What it shows |
|---|---|---|
| `fluent-build-diff/` | Node + `@servicenow/sdk` (no instance, no login) | Build output that changes with the build host's time zone, and records dropped while the build exits 0 |
| `fluent-build-diff/helpers_probe.cjs` | Node + SDK | Calls the SDK date helpers directly (F1–F4, F6, F7, F10 in `servicenow.md` §3) |
| `glide_rfc3339.js` | Script Include (ES5) | `toRfc3339(gdt)` / `fromRfc3339(s)` helpers |
| `glide_adapter.cjs` | Node | `run_vectors.py` adapter for Glide helper code, with a **stand-in** `GlideDateTime` (epoch ms only; not Rhino) |
| `instance_probe.js` | Background script on an instance | Read-only Glide probes P-ENV … P-DB (`servicenow.md` §6) |

## 1. Fluent build diff (offline)

```sh
cd probes/servicenow/fluent-build-diff
npm install                       # installs @servicenow/sdk 4.13.0 only; no instance contact
./build_diff.sh                   # the fixture app, TZ = UTC, America/New_York, Asia/Kolkata
./build_diff.sh /path/to/your/app # your app (its dist/ is deleted and rebuilt once per zone)
./build_diff.sh ./app UTC Europe/Paris Pacific/Kiritimati   # other zones
```

- It sets `NO_TELEMETRY=1`. Set `NOW_SDK=/…/node_modules/@servicenow/sdk/bin/index.js` if the SDK is elsewhere.
- Output goes to `./out/`: `build-<TZ>.log`, `dist-<TZ>/`, `diff-<TZ>.txt`. The script ignores the
  `serialNumber` and `timestamp` lines of the embedded `bom.json`; they change on every build by design.
- Any diff line is host-TZ-dependent build output: a **WRONG VALUE** unless the host zone equals the zone the
  author meant. `exit=0` with `ERROR_lines>0` means a plugin threw and the record was left out (F12).
- The first build writes `src/fluent/generated/keys.ts` (sys_ids). Later builds reuse it, so file names match.

Expected result with SDK 4.13.0 (checked 2026-09-25, Node 26.8.1): all three builds print
`exit=0 … ERROR_lines=1` (`sched_bad` dropped). `diff UTC vs America/New_York` shows `time_nozone`
`12:00:00 → 17:00:00` and `sched_gap` `run_start 21:00:00 → 22:00:00`. `diff UTC vs Asia/Kolkata` shows
`time_nozone` `→ 06:30:00`. In every build, `time_kolkata` is `1969-12-31 18:30:00` (correct: 19:30), the default
`run_time` of `sched_gap` is `1969-12-31 17:30:00` (correct: 18:30) and `dt_cast` is the verbatim string
`2024-01-01T12:00:00Z`.

Helper probe (no build):

```sh
for z in UTC America/New_York Asia/Kolkata; do TZ=$z node helpers_probe.cjs; done
```

Each line has its expected value in the label.

## 2. Glide helper code under Node (offline)

For Script Include code that uses only `GlideDateTime` epoch-ms methods (`setNumericValue`,
`getNumericValue`, `getValue`), run the vectors with the stand-in:

```sh
python3 scripts/run_vectors.py --target "node probes/servicenow/glide_adapter.cjs [your_script.js] [fnName]" \
    --target-kind rfc3339 --target-options fixed --target-has-tzdata no
```

`fnName` takes a string and returns a `GlideDateTime` (default `fromRfc3339` in `glide_rfc3339.js`). The
adapter scores the returned instant against the offset written in the input. Result for `glide_rfc3339.js`:
128/130; the 2 WRONG VALUE rows are real leap seconds stored as `:59` (the stated policy). Also run it with
`TZ=America/New_York`: host-local `Date` use shows up as a difference.

Limits: the stand-in does not reproduce Java parsing (`new GlideDateTime(s)`, `setDisplayValue`, user
formats). Code that relies on those needs `instance_probe.js`.

## 3. Instance probe (optional, needs an instance)

`instance_probe.js` is **read-only** by default: it creates Glide objects and one uninserted `GlideRecord`.
It writes only if you set `WRITE_TABLE` and `WRITE_FIELD` (P-DB: one insert, then a delete). Use a personal
developer or sub-production instance.

1. System Definition > Scripts - Background, scope `global`.
2. Paste the file, run it as a user whose time zone is UTC, then again as a user in `America/New_York`.
3. Keep the JSON lines: `sed -n 's/^\*\*\* Script: //p' out.txt | grep '^{' > probe-<tz>.jsonl`.
4. Compare with the claims in `references/servicenow.md` §6. Record the instance build tag (P-ENV line).

The REST and Flow probes (REST-R, REST-W, REST-S, FLOW) are commands in `servicenow.md` §6. They write to a
throwaway table, so run them only on an instance you own.
