// RFC 3339 / RFC 9557 conformance probe for JavaScript (Node >= 26, native Temporal).
// Usage: TZ=America/New_York node probe_js.mjs [probe] > results/js.jsonl
//        node probe_js.mjs list            # adapter keys: <key>\t<target-kind>
//        node probe_js.mjs adapter <key>   # scripts/run_vectors.py adapter (per-process + batch)
//   run_vectors.py --target 'node probes/probe_js.mjs adapter temporal-zdt' --batch \
//       --target-kind ixdtf --target-options fixed --target-has-tzdata yes
// Optional: ajv + ajv-formats resolved from NODE_PATH or AJV_DIR (npm i ajv ajv-formats);
// their adapter keys are listed only when they resolve.
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
const HERE = new URL(".", import.meta.url).pathname;
const LANG = "javascript";
const emit = (o) => console.log(JSON.stringify({ lang: LANG, ...o }));

// probes/inputs.json schema 2 (inputs + legacy) or the old list form.
function loadInputs() {
  const doc = JSON.parse(readFileSync(HERE + "inputs.json", "utf8"));
  return Array.isArray(doc) ? doc : [...doc.inputs, ...(doc.legacy || [])];
}

function parseProbe(api, fn, mode, inputs) {
  for (const rec of inputs) {
    try {
      const [out, utc] = fn(rec.s);
      emit({ kind: "parse", api, mode, id: rec.id, input: rec.s, ok: true, out, utc });
    } catch (e) {
      emit({ kind: "parse", api, mode, id: rec.id, input: rec.s, ok: false, err: `${e.name}: ${e.message}`.slice(0, 160) });
    }
  }
}
const dateResult = (d) => {
  if (Number.isNaN(d.getTime())) throw new RangeError("Invalid Date (NaN)");
  return [d.toISOString(), d.toISOString()];
};

// Adapter fields: only what the result object exposes.
const frac = (x) => {
  const n = x.millisecond * 1e6 + x.microsecond * 1e3 + x.nanosecond;
  return n ? String(n).padStart(9, "0") : null;
};
function wallFields(x) {
  const iso = x.withCalendar("iso8601");
  const f = { year: iso.year, month: iso.month, day: iso.day, hour: iso.hour, minute: iso.minute, second: iso.second, leap_second: false };
  const fr = frac(iso);
  if (fr) f.secfrac = fr;
  f.effective_tags = { "u-ca": x.calendarId };
  return f;
}
const zdtFields = (z) => ({ ...wallFields(z), offset_minutes: Math.trunc(z.offsetNanoseconds / 6e10), time_zone: { name: z.timeZoneId } });

const RESOLVED = Symbol("resolved");  // not serialized: moves to the answer's "resolved" key

// key, probe API name, probe mode, target kind, probe fn (-> [out, utc]), adapter fn (-> fields | null)
const APIS = [
  ["date", "Date.parse / new Date(s)", "3339", "rfc3339", (s) => dateResult(new Date(s)),
    (s) => { dateResult(new Date(s)); return null; }],
  ["temporal-instant", "Temporal.Instant.from", "ixdtf", "ixdtf",
    (s) => { const i = Temporal.Instant.from(s); return [i.toString(), i.toString()]; },
    (s) => { Temporal.Instant.from(s); return null; }],
  ["temporal-zdt", "Temporal.ZonedDateTime.from", "ixdtf-zoned", "ixdtf",
    (s) => { const z = Temporal.ZonedDateTime.from(s); return [z.toString(), z.toInstant().toString()]; },
    (s) => zdtFields(Temporal.ZonedDateTime.from(s))],
  ["temporal-zdt-reject", "Temporal.ZonedDateTime.from({offset:'reject'}) [default]", "ixdtf-zoned", "ixdtf",
    (s) => { const z = Temporal.ZonedDateTime.from(s, { offset: "reject" }); return [z.toString(), z.toInstant().toString()]; },
    (s) => zdtFields(Temporal.ZonedDateTime.from(s, { offset: "reject" }))],
  ["temporal-zdt-use", "Temporal.ZonedDateTime.from({offset:'use'})", "ixdtf-zoned", "ixdtf",
    (s) => { const z = Temporal.ZonedDateTime.from(s, { offset: "use" }); return [z.toString(), z.toInstant().toString()]; },
    (s) => {
      // offset:'use' is programmed resolution (§3.4): report resolved when the default
      // offset:'reject' parse of the same string refuses it (the target itself saw the conflict).
      const f = zdtFields(Temporal.ZonedDateTime.from(s, { offset: "use" }));
      try { Temporal.ZonedDateTime.from(s, { offset: "reject" }); } catch { f[RESOLVED] = true; }
      return f;
    }],
  ["temporal-plaindatetime", "Temporal.PlainDateTime.from", "ixdtf", "ixdtf",
    (s) => { const p = Temporal.PlainDateTime.from(s); return [p.toString(), "naive:" + p.toString()]; },
    (s) => wallFields(Temporal.PlainDateTime.from(s))],
];

let ajvNote = null;
try {
  const require = createRequire(process.env.AJV_DIR ? new URL("file://" + process.env.AJV_DIR.replace(/\/?$/, "/")) : import.meta.url);
  const Ajv = require("ajv"); const addFormats = require("ajv-formats");
  const ajv = new Ajv(); addFormats(ajv);
  const v = ajv.compile({ type: "string", format: "date-time" });
  const ajvf = new Ajv(); addFormats(ajvf, { mode: "fast" });
  const vf = ajvf.compile({ type: "string", format: "date-time" });
  const chk = (fn) => (s) => { if (!fn(s)) throw new Error("invalid"); return ["valid", null]; };
  APIS.push(["ajv-full", "ajv-formats format:date-time (full)", "3339", "rfc3339", chk(v), (s) => { chk(v)(s); return null; }]);
  APIS.push(["ajv-fast", "ajv-formats format:date-time (mode:'fast')", "3339", "rfc3339", chk(vf), (s) => { chk(vf)(s); return null; }]);
} catch (e) { ajvNote = String(e).slice(0, 120); }

function answer(fn, s) {
  try {
    const f = fn(s);
    if (!f) return { ok: true };
    return f[RESOLVED] ? { ok: true, resolved: true, fields: f } : { ok: true, fields: f };
  } catch (e) {
    return { ok: false, error: `${e.name}: ${e.message}`.slice(0, 200) };
  }
}

const argv = process.argv.slice(2);
if (argv[0] === "list") {
  for (const a of APIS) console.log(`${a[0]}\t${a[3]}`);
  process.exit(0);
}
if (argv[0] === "adapter") {
  const api = APIS.find((a) => a[0] === argv[1]);
  if (!api) { console.error(`unknown adapter key ${argv[1]}; see: probe_js.mjs list`); process.exit(2); }
  const all = readFileSync(0, "utf8");
  if (process.env.RFCDT_BATCH === "1") {
    const out = all.split("\n").filter((l) => l.trim()).map((l) => {
      const req = JSON.parse(l);
      return JSON.stringify({ id: req.id, ...answer(api[5], req.input) });
    });
    process.stdout.write(out.join("\n") + "\n");
  } else console.log(JSON.stringify(answer(api[5], all)));
  process.exit(0);
}
if (argv[0] && argv[0] !== "probe") { console.error("usage: probe_js.mjs [probe] | list | adapter <key>"); process.exit(2); }

const INPUTS = loadInputs();
for (const [, api, mode, , fn] of APIS) parseProbe(api, fn, mode, INPUTS);
if (ajvNote) emit({ kind: "note", api: "ajv", err: ajvNote });

// ---------------- formatter probes ----------------
const F = (api, thunk) => { try { emit({ kind: "format", api, out: thunk() }); } catch (e) { emit({ kind: "format", api, out: null, err: `${e.name}: ${e.message}` }); } };
const d = new Date(Date.UTC(2026, 8, 24, 12, 0, 0));
F("new Date(...).toISOString()", () => d.toISOString());
F("JSON.stringify(new Date(...))", () => JSON.parse(JSON.stringify(d)));
F("Date#toString()", () => d.toString());
F("Date#toUTCString()", () => d.toUTCString());
F("new Date('+010000-01-01T00:00:00Z').toISOString()", () => new Date("+010000-01-01T00:00:00Z").toISOString());
F("new Date(Date.UTC(-1,0,1)).toISOString()", () => { const x = new Date(0); x.setUTCFullYear(-1, 0, 1); return x.toISOString(); });
F("new Date(Date.UTC(99,0,1)).toISOString()  [2-digit year → 1999]", () => new Date(Date.UTC(99, 0, 1)).toISOString());
F("toLocaleString('sv-SE')  [common 'ISO-ish' hack]", () => d.toLocaleString("sv-SE", { timeZone: "UTC" }));
F("Temporal.Instant#toString()", () => Temporal.Instant.from("2026-09-24T12:00:00Z").toString());
F("Temporal.Instant#toString({timeZone:'Europe/Paris'})", () => Temporal.Instant.from("2026-09-24T12:00:00Z").toString({ timeZone: "Europe/Paris" }));
F("Temporal.ZonedDateTime#toString()", () => Temporal.ZonedDateTime.from("2026-09-24T14:00:00+02:00[Europe/Paris]").toString());
F("Temporal.ZonedDateTime#toString() [non-ISO calendar]", () => Temporal.ZonedDateTime.from("2026-09-24T14:00:00+02:00[Europe/Paris][u-ca=hebrew]").toString());
F("Temporal.ZonedDateTime#toString({timeZoneName:'critical'})", () => Temporal.ZonedDateTime.from("2026-09-24T14:00:00+02:00[Europe/Paris]").toString({ timeZoneName: "critical" }));
F("Temporal.ZonedDateTime (UTC zone) #toString()", () => Temporal.Instant.from("2026-09-24T12:00:00Z").toZonedDateTimeISO("UTC").toString());
F("Temporal.ZonedDateTime (1850 Europe/Paris, LMT) #toString()", () => Temporal.ZonedDateTime.from({ year: 1850, month: 1, day: 1, timeZone: "Europe/Paris" }).toString());
F("Temporal.Instant (year 10000) #toString()", () => Temporal.Instant.from("+010000-01-01T00:00:00Z").toString());
F("Temporal.PlainDateTime#toString()  [no offset]", () => Temporal.PlainDateTime.from("2026-09-24T12:00:00").toString());
F("Temporal.ZonedDateTime#toString({smallestUnit:'minute'})", () => Temporal.ZonedDateTime.from("2026-09-24T14:00:00+02:00[Europe/Paris]").toString({ smallestUnit: "minute" }));
