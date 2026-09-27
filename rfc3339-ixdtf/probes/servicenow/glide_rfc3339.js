/*
 * glide_rfc3339.js - RFC 3339 helpers for ServiceNow server scripts (global or scoped, ES5).
 * Paste into a Script Include. Evidence: tested under Node against a stand-in GlideDateTime
 * (glide_adapter.cjs); NOT run in real Rhino. Date.prototype.toISOString and setUTCFullYear
 * on the instance are unverified (needs instance, probe P-RFC).
 */
// Producer: GlideDateTime -> RFC 3339 (UTC, milliseconds). Years 0000-9999 only.
function toRfc3339(gdt) {
  var ms = Number(String(gdt.getNumericValue()));
  var d = new Date(ms);
  var y = d.getUTCFullYear();
  if (isNaN(ms) || y < 0 || y > 9999) { throw 'toRfc3339: out of range'; }
  return d.toISOString();                         // 2026-09-24T12:34:56.789Z
}

// Consumer: strict RFC 3339 date-time -> GlideDateTime. Rejects everything else.
var RFC3339 = /^([0-9]{4})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9]|60)(\.[0-9]+)?([Zz]|([+-])([01][0-9]|2[0-3]):([0-5][0-9]))$/;
function fromRfc3339(s) {
  var m = RFC3339.exec(String(s));
  if (!m) { throw 'fromRfc3339: not RFC 3339: ' + s; }
  var y = +m[1], mo = +m[2], d = +m[3], h = +m[4], mi = +m[5], se = +m[6];
  var dim = [31, (y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mo - 1];
  if (d > dim) { throw 'fromRfc3339: day out of range: ' + s; }
  var frac = m[7] ? Math.floor(Number('0' + m[7]) * 1000) : 0;   // truncate to ms (lossy, allowed)
  var off = 0;
  if (m[9]) { off = (m[9] === '-' ? -1 : 1) * (+m[10] * 60 + +m[11]); }
  var leap = (se === 60);
  if (leap) { se = 59; }                                      // policy: a valid leap second is stored as :59 (lossy)
  var t = new Date(0);                                        // not Date.UTC(): it maps years 0-99 to 19xx
  t.setUTCFullYear(y, mo - 1, d);
  t.setUTCHours(h, mi, se, frac);
  var ms = t.getTime() - off * 60000;                         // SUBTRACT the offset to get UTC
  if (leap) {                                                 // RFC 3339 §5.7: 23:59:60 UTC on a month's last day
    var u = new Date(ms), nx = new Date(ms + 1000);
    if (u.getUTCHours() !== 23 || u.getUTCMinutes() !== 59 || nx.getUTCDate() !== 1) {
      throw 'fromRfc3339: leap second not at the end of a UTC month: ' + s;
    }
  }
  var gdt = new GlideDateTime();
  gdt.setNumericValue(ms);
  return gdt;
}
