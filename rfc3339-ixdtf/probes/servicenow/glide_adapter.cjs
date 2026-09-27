// run_vectors adapter for Glide server-script date helpers, run under Node with a STAND-IN GlideDateTime.
// The stand-in stores epoch ms only; it does not reproduce Rhino/Java parsing. Results show whether the
// helper's own logic is right, not what the instance does.
// Usage:
//   python3 scripts/run_vectors.py --target "node probes/servicenow/glide_adapter.cjs [script.js] [fnName]" \
//       --target-kind rfc3339 --target-options fixed --target-has-tzdata no
// Defaults: script = glide_rfc3339.js next to this file, fnName = fromRfc3339 (string -> GlideDateTime).
// A consumer that returns a GlideDateTime is scored by instant: the adapter adds back the offset written in
// the input and reports the local wall fields, so a wrong instant shows as WRONG VALUE.
const fs = require('fs'); const path = require('path'); const vm = require('vm');
const script = process.argv[2] || path.join(__dirname, 'glide_rfc3339.js');
const fnName = process.argv[3] || 'fromRfc3339';
const pad = (n, w) => String(n).padStart(w || 2, '0');
function GlideDateTime(v) { this._ms = Date.now(); this._valid = true; if (v !== undefined) this.setValue(v); }
GlideDateTime.prototype.setNumericValue = function (ms) { this._ms = Number(ms); };
GlideDateTime.prototype.getNumericValue = function () { return this._ms; };
GlideDateTime.prototype.isValid = function () { return this._valid; };
GlideDateTime.prototype.getValue = function () {
  const d = new Date(this._ms);
  return `${pad(d.getUTCFullYear(), 4)}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
};
GlideDateTime.prototype.setValue = function (v) { // internal format only (UTC 'yyyy-MM-dd HH:mm:ss') or epoch ms
  if (typeof v === 'number') { this._ms = v; return; }
  const m = /^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$/.exec(String(v));
  if (!m) { this._valid = false; return; }
  const t = new Date(0); t.setUTCFullYear(+m[1], +m[2] - 1, +m[3]); t.setUTCHours(+m[4], +m[5], +m[6], 0); this._ms = t.getTime();
};
GlideDateTime.prototype.toString = GlideDateTime.prototype.getValue;
const ctx = vm.createContext({ GlideDateTime, gs: { info() {}, print() {} } });
vm.runInContext(fs.readFileSync(script, 'utf8'), ctx, { filename: script });
const s = fs.readFileSync(0, 'utf8');
const out = (o) => process.stdout.write(JSON.stringify(o));
let r;
try { r = ctx[fnName](s); } catch (e) { out({ ok: false, error: String(e) }); process.exit(0); }
if (r === null || r === undefined || (r.isValid && !r.isValid())) { out({ ok: false }); process.exit(0); }
const ms = Number(String(r.getNumericValue ? r.getNumericValue() : r));
const om = /([Zz]|([+-])(\d{2}):(\d{2}))(\[.*)?$/.exec(s);
if (!om || isNaN(ms)) { out({ ok: true }); process.exit(0); }
const off = om[2] ? (om[2] === '-' ? -1 : 1) * (+om[3] * 60 + +om[4]) : 0;
const d = new Date(ms + off * 60000);
out({ ok: true, fields: { year: d.getUTCFullYear(), month: d.getUTCMonth() + 1, day: d.getUTCDate(), hour: d.getUTCHours(), minute: d.getUTCMinutes(), second: d.getUTCSeconds(), offset_minutes: off } });
