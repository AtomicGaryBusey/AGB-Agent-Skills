// Call SDK 4.x date helpers directly (no build, no instance) and print JSON.
// Usage: TZ=<zone> node helpers_probe.cjs   (compare output across TZ=UTC / America/New_York / Asia/Kolkata)
// Finds node_modules/@servicenow by walking up from this file and the cwd, then NODE_PATH (npm install first).
// The converter is a deep dist path that "exports" hides, so it is loaded by absolute path.
const fs = require('fs'); const path = require('path');
function findSN() {
  const starts = [__dirname, process.cwd()];
  for (let d of starts) for (;;) { const c = path.join(d, 'node_modules', '@servicenow'); if (fs.existsSync(c)) return c; const up = path.dirname(d); if (up === d) break; d = up; }
  for (const d of (process.env.NODE_PATH || '').split(path.delimiter).filter(Boolean)) { const c = path.join(d, '@servicenow'); if (fs.existsSync(c)) return c; }
  throw new Error('node_modules/@servicenow not found: run npm install here or set NODE_PATH');
}
const SN = findSN();
const core = require(path.join(SN, 'sdk-build-core'));
const tzc = require(path.join(SN, 'sdk-build-plugins', 'dist', 'schedule-script', 'timeZoneConverter.js'));
console.log(JSON.stringify({ sdk_build_core: require(path.join(SN, 'sdk-build-core', 'package.json')).version }));
const fmt = (d) => (d instanceof Date ? d.toISOString() : d);
const run = (label, f) => { let r; try { r = f(); } catch (e) { r = 'THROWS ' + (e && e.message || e); } console.log(JSON.stringify({ label, result: fmt(r) })); };
console.log(JSON.stringify({ host_tz: Intl.DateTimeFormat().resolvedOptions().timeZone, node: process.version }));
run("F1 timeFieldToXML({hours:1},'Asia/Kolkata')  expect 1969-12-31T19:30:00Z", () => core.timeFieldToXML({ hours: 1 }, 'Asia/Kolkata'));
run("F1 timeFieldToXML({hours:0,minutes:30},'Europe/Berlin')  expect 1969-12-31T23:30:00Z", () => core.timeFieldToXML({ hours: 0, minutes: 30 }, 'Europe/Berlin'));
run("F2 timeFieldToXML({hours:12}) (no zone)  host-dependent", () => core.timeFieldToXML({ hours: 12 }));
run("F3 parseGlideDuration('1970-07-20 00:00:00')  expect {days:200}", () => core.parseGlideDuration('1970-07-20 00:00:00'));
run("F4 dateTimeFieldToXML('2026-03-08 02:30:00','Asia/Kolkata')  expect 2026-03-07 21:00:00", () => tzc.dateTimeFieldToXML('2026-03-08 02:30:00', 'Asia/Kolkata'));
run("F6 dateTimeFieldToXML('0050-06-01 00:00:00','America/New_York')  expect a year-0050 value or a clear validation error", () => tzc.dateTimeFieldToXML('0050-06-01 00:00:00', 'America/New_York'));
run("F6 convertXMLToDateTime('0050-06-01 00:00:00','America/New_York')  expect year 0050, not 1950", () => tzc.convertXMLToDateTime('0050-06-01 00:00:00', 'America/New_York'));
run("F7 formatDateToPlatformFormat(year 50)  expect 0050-06-01 00:00:00", () => core.formatDateToPlatformFormat(new Date('0050-06-01T00:00:00Z')));
run("F10 dateTimeFieldToXML('2024-02-30 12:00:00','Europe/Paris')  expect rejection", () => tzc.dateTimeFieldToXML('2024-02-30 12:00:00', 'Europe/Paris'));
