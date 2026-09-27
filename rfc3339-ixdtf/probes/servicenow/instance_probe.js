/*
 * instance_probe.js - RFC 3339 / RFC 9557 probe for ServiceNow Glide date-time APIs.
 *
 * WHAT IT DOES
 *   Runs read-only calls on GlideDateTime, GlideDate, GlideTime, GlideElement and gs.
 *   Prints one JSON object per line. Every line has "probe" (the claim ID in
 *   references/servicenow.md §6) and "api".
 *
 * WHERE TO RUN IT
 *   A sub-production or personal developer instance that you own.
 *   System Definition > Scripts - Background, scope "global". Some rows need global
 *   (setXMLValue, getXMLValue, gs.nowDateTime). In a scoped app, those rows print
 *   {"skipped": "..."}.
 *   The script does not insert, update or delete records, unless you set WRITE_TABLE
 *   below (the P-DB probe). Then it inserts one record and deletes it again.
 *
 * HOW TO READ THE OUTPUT
 *   Background scripts put "*** Script: " in front of each line. Remove it, then:
 *     sed -n 's/^\*\*\* Script: //p' out.txt | grep '^{' > probe.jsonl
 *   Run the script two times: one time as a user with time zone UTC, and one time
 *   as a user with time zone America/New_York. The first line (P-ENV) records the
 *   session time zone and the format properties. Many results depend on them.
 *
 * ES5 ONLY. Rhino in global scope does not support let/const/arrow functions in
 * every compatibility mode.
 */
(function () {
  var WRITE_TABLE = '';        // for example 'u_rfc_probe'. Empty = skip P-DB (no writes).
  var WRITE_FIELD = '';        // a glide_date_time column on WRITE_TABLE

  function out(o) {
    var line;
    try { line = JSON.stringify(o); } catch (e) { line = '{"probe":"JSON","error":"' + String(e) + '"}'; }
    if (typeof gs.print === 'function') { gs.print(line); } else { gs.info(line); }
  }
  function str(x) { return (x === null || x === undefined) ? null : String(x); }
  function num(x) { if (x === null || x === undefined) { return null; } var n = Number(String(x)); return isNaN(n) ? String(x) : n; }
  function has(o, m) { try { return typeof o[m] === 'function' || (o[m] !== undefined && o[m] !== null); } catch (e) { return false; } }
  function snap(g) {
    var r = {};
    try { r.valid = g.isValid(); } catch (e) { r.valid = 'ERR ' + e; }
    try { r.value = str(g.getValue()); } catch (e) { r.value = 'ERR ' + e; }
    try { r.ms = num(g.getNumericValue()); } catch (e) { r.ms = 'ERR ' + e; }
    try { r.err = str(g.getErrorMsg()); } catch (e) { r.err = 'ERR ' + e; }
    return r;
  }
  var SENTINEL = 0; // 1970-01-01 00:00:00. If a setter fails and keeps this, the row shows "kept_sentinel".
  function freshSentinel() { var g = new GlideDateTime(); g.setNumericValue(SENTINEL); return g; }

  // ---------------------------------------------------------------- P-ENV
  var env = { probe: 'P-ENV', api: 'environment' };
  try { env.session_tz = str(gs.getSession().getTimeZoneName()); } catch (e) { env.session_tz = 'ERR ' + e; }
  try { env.user_tz_obj = str(new GlideDateTime().getUserTimeZone()); } catch (e) { env.user_tz_obj = 'ERR ' + e; }
  try { env.sys_tz = str(gs.getSysTimeZone()); } catch (e) { env.sys_tz = 'ERR ' + e; }
  var props = ['glide.sys.date_format', 'glide.sys.time_format', 'glide.sys.default.tz', 'glide.sys.internal.tz'];
  env.props = {};
  for (var p = 0; p < props.length; p++) { try { env.props[props[p]] = str(gs.getProperty(props[p], '(unset)')); } catch (e) { env.props[props[p]] = 'ERR ' + e; } }
  try { env.gs_getDateTimeFormat = str(gs.getDateTimeFormat()); } catch (e) { env.gs_getDateTimeFormat = 'ERR ' + e; }
  try { env.gs_getDateFormat = str(gs.getDateFormat()); } catch (e) { env.gs_getDateFormat = 'ERR ' + e; }
  try { env.gs_getTimeFormat = str(gs.getTimeFormat()); } catch (e) { env.gs_getTimeFormat = 'ERR ' + e; }
  try { env.build = str(gs.getProperty('glide.buildtag')); } catch (e) { env.build = 'ERR ' + e; }
  try { env.scope = str(gs.getCurrentScopeName()); } catch (e) { env.scope = 'ERR ' + e; }
  out(env);

  // ---------------------------------------------------------------- P-OUT: producers
  // Fixed instant 2026-09-24T12:34:56.789Z = 1790253296789 ms.
  var g0 = new GlideDateTime();
  g0.setNumericValue(1790253296789);
  var getters = ['getValue', 'toString', 'getDisplayValue', 'getDisplayValueInternal', 'getDisplayValueWithoutTZ',
    'getXMLValue', 'getUTCValue', 'getInternalFormattedLocalTime', 'getUserFormattedLocalTime', 'getNumericValue',
    'getTZOffset', 'getDSTOffset', 'isDST'];
  for (var i = 0; i < getters.length; i++) {
    var m = getters[i];
    var row = { probe: 'P-OUT', api: 'GlideDateTime.' + m + '()', instant: '2026-09-24T12:34:56.789Z' };
    if (!has(g0, m)) { row.skipped = 'method not present in this scope'; out(row); continue; }
    try { row.out = str(g0[m]()); } catch (e) { row.error = String(e); }
    out(row);
  }
  var styles = ['short', 'medium', 'long', 'full'];
  for (var s = 0; s < styles.length; s++) {
    try { out({ probe: 'P-OUT', api: 'getDisplayValueLang("' + styles[s] + '")', out: str(g0.getDisplayValueLang(styles[s])) }); }
    catch (e) { out({ probe: 'P-OUT', api: 'getDisplayValueLang("' + styles[s] + '")', error: String(e) }); }
  }
  try { out({ probe: 'P-OUT', api: 'String(gdt) / gdt+""', out: '' + g0 }); } catch (e) { out({ probe: 'P-OUT', api: 'String(gdt)', error: String(e) }); }
  try { out({ probe: 'P-JSON', api: 'JSON.stringify({t: gdt})', out: JSON.stringify({ t: g0 }) }); } catch (e) { out({ probe: 'P-JSON', api: 'JSON.stringify({t: gdt})', error: String(e) }); }
  try { out({ probe: 'P-OUT', api: 'GlideDateTime.excludeZFromFormat("yyyy-MM-dd\'T\'HH:mm:ss\'Z\'")', out: str(GlideDateTime.excludeZFromFormat("yyyy-MM-dd'T'HH:mm:ss'Z'")) }); }
  catch (e) { out({ probe: 'P-OUT', api: 'GlideDateTime.excludeZFromFormat', error: String(e) }); }

  // Recommended RFC 3339 producers (see references/servicenow.md §4).
  try {
    var iso1 = str(g0.getValue()).replace(' ', 'T') + 'Z';
    out({ probe: 'P-RFC', api: 'getValue().replace(" ","T")+"Z"', out: iso1, expected: '2026-09-24T12:34:56Z' });
  } catch (e) { out({ probe: 'P-RFC', api: 'getValue()+Z', error: String(e) }); }
  try {
    var d = new Date(num(g0.getNumericValue()));
    out({ probe: 'P-RFC', api: 'new Date(getNumericValue()).toISOString()', out: (typeof d.toISOString === 'function') ? d.toISOString() : 'toISOString missing', expected: '2026-09-24T12:34:56.789Z' });
  } catch (e) { out({ probe: 'P-RFC', api: 'Date.toISOString', error: String(e) }); }
  // Year-range edge for the toISOString route.
  try { var dz = new Date(-62198755200000); out({ probe: 'P-RFC', api: 'toISOString year 0000', out: dz.toISOString() }); } catch (e) { out({ probe: 'P-RFC', api: 'toISOString year 0000', error: String(e) }); }

  // gs "now" family: which are UTC, which are user format and zone.
  var gsNow = ['now', 'nowNoTZ', 'nowDateTime', 'beginningOfToday', 'endOfToday', 'minutesAgo', 'daysAgo'];
  var ref = new GlideDateTime();
  out({ probe: 'P-GS', api: 'reference new GlideDateTime().getValue()', out: str(ref.getValue()), dv: str(ref.getDisplayValue()) });
  for (var k = 0; k < gsNow.length; k++) {
    var f = gsNow[k];
    var r2 = { probe: 'P-GS', api: 'gs.' + f + '()' };
    if (typeof gs[f] !== 'function') { r2.skipped = 'not in this scope'; out(r2); continue; }
    try { r2.out = str((f === 'minutesAgo' || f === 'daysAgo') ? gs[f](0) : gs[f]()); } catch (e) { r2.error = String(e); }
    out(r2);
  }
  try { out({ probe: 'P-GS', api: 'gs.nowGlideDateTime().getValue()', out: str(gs.nowGlideDateTime().getValue()) }); } catch (e) { out({ probe: 'P-GS', api: 'gs.nowGlideDateTime', error: String(e) }); }

  // ---------------------------------------------------------------- P-IN: consumers
  // exp = expected epoch ms if the string is read as RFC 3339 (null = not a valid RFC 3339 date-time).
  var inputs = [
    ['base-space-utc', '2026-09-24 12:34:56', 1790253296000, 'internal format; UTC by docs'],
    ['T-Z', '2026-09-24T12:34:56Z', 1790253296000, 'RFC 3339'],
    ['t-z-lower', '2026-09-24t12:34:56z', 1790253296000, 'RFC 3339 (lower case)'],
    ['T-z', '2026-09-24T12:34:56z', 1790253296000, 'RFC 3339 (lower z)'],
    ['off+02', '2026-09-24T12:34:56+02:00', 1790246096000, 'RFC 3339'],
    ['off-05', '2026-09-24T12:34:56-05:00', 1790271296000, 'RFC 3339'],
    ['off-minus0', '2026-09-24T12:34:56-00:00', 1790253296000, 'RFC 3339 (= Z per RFC 9557 s2)'],
    ['off-nocolon', '2026-09-24T12:34:56+0200', null, 'not RFC 3339'],
    ['frac3-Z', '2026-09-24T12:34:56.789Z', 1790253296789, 'RFC 3339'],
    ['frac9-Z', '2026-09-24T12:34:56.123456789Z', 1790253296123, 'RFC 3339 (ms truncation OK)'],
    ['space-frac', '2026-09-24 12:34:56.789', null, 'not RFC 3339 (no offset)'],
    ['no-off', '2026-09-24T12:34:56', null, 'not RFC 3339 (no offset)'],
    ['space-Z', '2026-09-24 12:34:56Z', 1790253296000, 'space form (erratum 5783, held)'],
    ['leap-real', '2016-12-31T23:59:60Z', 1483228799000, 'RFC 3339 leap second (maps to :59 or rejected)'],
    ['leap-real-space', '2016-12-31 23:59:60', null, 'internal format with :60'],
    ['feb30', '2024-02-30 12:00:00', null, 'invalid date'],
    ['h24', '2026-09-24 24:00:00', null, 'invalid hour'],
    ['m13', '2026-13-01 00:00:00', null, 'invalid month'],
    ['no-sec', '2026-09-24 12:34', null, 'alt format yyyy-MM-dd HH:mm'],
    ['date-only', '2026-09-24', null, 'alt format yyyy-MM-dd'],
    ['ambig-slash', '09/10/2026 12:00:00', null, 'MM/dd or dd/MM?'],
    ['ixdtf-zone', '2026-09-24T12:34:56+02:00[Europe/Paris]', 1790246096000, 'RFC 9557'],
    ['ixdtf-crit-unk', '2026-09-24T12:34:56Z[!x-foo=bar]', null, 'RFC 9557: MUST reject'],
    ['lead-ws', ' 2026-09-24 12:34:56', null, 'leading space'],
    ['trail-nl', '2026-09-24 12:34:56\n', null, 'trailing newline'],
    ['y0000', '0000-01-01 00:00:00', null, 'year 0000'],
    ['y10000', '10000-01-01 00:00:00', null, '5-digit year'],
    ['y2digit', '26-09-24 12:34:56', null, '2-digit year']
  ];

  function probeSetter(label, fn) {
    for (var j = 0; j < inputs.length; j++) {
      var id = inputs[j][0], sIn = inputs[j][1], exp = inputs[j][2];
      var row = { probe: 'P-IN', api: label, id: id, input: sIn, rfc_expected_ms: exp };
      var g = null;
      try { g = fn(sIn); } catch (e) { row.threw = String(e); }
      if (g) {
        var sn = snap(g);
        for (var key in sn) { if (sn.hasOwnProperty(key)) { row[key] = sn[key]; } }
        if (label.indexOf('ctor') < 0 && sn.ms === SENTINEL) { row.kept_sentinel = true; }
        if (exp !== null && typeof sn.ms === 'number') { row.delta_ms = sn.ms - exp; }
      }
      out(row);
    }
  }
  probeSetter('new GlideDateTime(s)', function (x) { return new GlideDateTime(x); });
  probeSetter('setValue(s)', function (x) { var g = freshSentinel(); g.setValue(x); return g; });
  probeSetter('setDisplayValue(s)', function (x) { var g = freshSentinel(); g.setDisplayValue(x); return g; });
  probeSetter('setDisplayValueInternal(s)', function (x) { var g = freshSentinel(); g.setDisplayValueInternal(x); return g; });
  probeSetter('setDisplayValueInternalWithAlternates(s)', function (x) { var g = freshSentinel(); g.setDisplayValueInternalWithAlternates(x); return g; });
  probeSetter('setXMLValue(s)', function (x) { var g = freshSentinel(); if (!has(g, 'setXMLValue')) { throw 'setXMLValue not present'; } g.setXMLValue(x); return g; });
  probeSetter('new GlideDateTime(s, true /*isDisplayValue*/)', function (x) { return new GlideDateTime(x, true); });

  // setValueUTC / setDisplayValue(s, fmt) with ISO-style SimpleDateFormat patterns.
  var fmts = [
    "yyyy-MM-dd'T'HH:mm:ss'Z'",
    "yyyy-MM-dd'T'HH:mm:ssXXX",
    "yyyy-MM-dd'T'HH:mm:ss.SSSXXX",
    "yyyy-MM-dd'T'HH:mm:ssZ",
    "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'",
    "yyyy-MM-dd HH:mm:ss"
  ];
  for (var fi = 0; fi < fmts.length; fi++) {
    (function (fmt) {
      probeSetter('setValueUTC(s, "' + fmt + '")', function (x) { var g = freshSentinel(); g.setValueUTC(x, fmt); return g; });
      probeSetter('setDisplayValue(s, "' + fmt + '")', function (x) { var g = freshSentinel(); g.setDisplayValue(x, fmt); return g; });
    })(fmts[fi]);
  }

  // ---------------------------------------------------------------- P-ELEM: GlideElement (no insert)
  var gr = new GlideRecord('sys_user');
  gr.initialize();
  var field = gr.isValidField('last_login_time') ? 'last_login_time' : null;
  if (!field) { out({ probe: 'P-ELEM', skipped: 'sys_user.last_login_time not found' }); }
  else {
    var elemInputs = ['2026-09-24 12:34:56', '2026-09-24T12:34:56Z', '2026-09-24T12:34:56+02:00', '2026-09-24T12:34:56.789Z'];
    for (var ei = 0; ei < elemInputs.length; ei++) {
      var x = elemInputs[ei];
      var rr = { probe: 'P-ELEM', input: x };
      try { gr.setValue(field, x); rr.setValue_getValue = str(gr.getValue(field)); rr.setValue_dv = str(gr.getDisplayValue(field)); } catch (e) { rr.setValue_err = String(e); }
      try { gr[field] = x; rr.assign_getValue = str(gr.getValue(field)); } catch (e) { rr.assign_err = String(e); }
      try { gr[field].setDisplayValue(x); rr.setDisplayValue_getValue = str(gr.getValue(field)); } catch (e) { rr.setDisplayValue_err = String(e); }
      try { rr.getGlideObject_ms = num(gr[field].getGlideObject().getNumericValue()); } catch (e) { rr.getGlideObject_err = String(e); }
      try { rr.json_elem = JSON.stringify({ t: gr[field] }); } catch (e) { rr.json_elem_err = String(e); }
      out(rr);
    }
  }

  // ---------------------------------------------------------------- P-TZ / P-DST (no writes)
  var tzs = ['America/New_York', 'Asia/Kolkata', 'UTC', 'Not/AZone'];
  for (var t = 0; t < tzs.length; t++) {
    var gtz = new GlideDateTime();
    gtz.setNumericValue(1790253296789);
    var rt = { probe: 'P-TZ', api: 'setTimeZone("' + tzs[t] + '")' };
    try { rt.returned = str(gtz.setTimeZone(tzs[t])); } catch (e) { rt.error = String(e); }
    try { rt.dv = str(gtz.getDisplayValue()); rt.dvi = str(gtz.getDisplayValueInternal()); rt.value = str(gtz.getValue()); rt.tzoffset = num(gtz.getTZOffset()); } catch (e) { rt.read_error = String(e); }
    out(rt);
  }
  // DST gap (02:30 does not exist on 2026-03-08 in New York) and overlap (01:30 twice on 2026-11-01).
  var dst = [
    ['gap', '2026-03-08 02:30:00', [1772955000000, 1772951400000]],
    ['overlap', '2026-11-01 01:30:00', [1793511000000, 1793514600000]]
  ];
  for (var di = 0; di < dst.length; di++) {
    var gd = new GlideDateTime();
    var rd = { probe: 'P-DST', scenario: dst[di][0], local_input: dst[di][1], tz: 'America/New_York', candidates_ms: dst[di][2] };
    try { gd.setTimeZone('America/New_York'); gd.setDisplayValueInternal(dst[di][1]); var sd = snap(gd); for (var kk in sd) { if (sd.hasOwnProperty(kk)) { rd[kk] = sd[kk]; } } } catch (e) { rd.error = String(e); }
    out(rd);
  }
  // addDaysLocalTime vs addDaysUTC across the 2026-03-08 transition (12:00 EST on 03-07 = 17:00Z).
  try {
    var a = new GlideDateTime(); a.setNumericValue(1772902800000); a.setTimeZone('America/New_York'); a.addDaysLocalTime(1);
    var b = new GlideDateTime(); b.setNumericValue(1772902800000); b.addDaysUTC(1);
    out({ probe: 'P-DST', scenario: 'addDays across DST', addDaysLocalTime_value: str(a.getValue()), addDaysUTC_value: str(b.getValue()), note: 'local=2026-03-08 16:00:00 keeps 12:00 wall time; UTC=2026-03-08 17:00:00' });
  } catch (e) { out({ probe: 'P-DST', scenario: 'addDays across DST', error: String(e) }); }

  // ---------------------------------------------------------------- P-PREC: precision in memory
  try {
    var gp = new GlideDateTime(); gp.setNumericValue(1790253296789);
    var gp2 = new GlideDateTime(gp.getValue());
    out({ probe: 'P-PREC', api: 'setNumericValue(...789) -> getNumericValue / via getValue', ms_direct: num(gp.getNumericValue()), ms_after_getValue_roundtrip: num(gp2.getNumericValue()) });
  } catch (e) { out({ probe: 'P-PREC', error: String(e) }); }

  // ---------------------------------------------------------------- P-DATE / P-TIME
  var gdi = ['2026-09-24', '2026-09-24T00:00:00Z', '24/09/2026', '2024-02-30'];
  for (var q = 0; q < gdi.length; q++) {
    var rq = { probe: 'P-DATE', api: 'GlideDate.setValue', input: gdi[q] };
    try { var gdd = new GlideDate(); gdd.setValue(gdi[q]); rq.value = str(gdd.getValue()); rq.dv = str(gdd.getDisplayValue()); } catch (e) { rq.error = String(e); }
    out(rq);
  }
  var gti = ['12:34:56', '12:34:56Z', '12:34:56+02:00', '12:34:56.789', '24:00:00', '23:59:60'];
  for (var w = 0; w < gti.length; w++) {
    var rw = { probe: 'P-TIME', api: 'GlideTime.setValue', input: gti[w] };
    try { var gtt = new GlideTime(); gtt.setValue(gti[w]); rw.value = str(gtt.getValue()); rw.dv = str(gtt.getDisplayValue()); rw.ms = num(gtt.getNumericValue()); } catch (e) { rw.error = String(e); }
    out(rw);
  }

  // ---------------------------------------------------------------- P-DB: stored precision (opt-in write)
  if (!WRITE_TABLE || !WRITE_FIELD) {
    out({ probe: 'P-DB', skipped: 'set WRITE_TABLE and WRITE_FIELD to a scratch table you own' });
  } else {
    var w1 = new GlideRecord(WRITE_TABLE);
    w1.initialize();
    var gw = new GlideDateTime(); gw.setNumericValue(1790253296789);
    w1.setValue(WRITE_FIELD, gw);
    var sid = w1.insert();
    var w2 = new GlideRecord(WRITE_TABLE);
    var row = { probe: 'P-DB', table: WRITE_TABLE, field: WRITE_FIELD, wrote_ms: 1790253296789 };
    if (sid && w2.get(sid)) {
      row.read_value = str(w2.getValue(WRITE_FIELD));
      try { row.read_ms = num(w2[WRITE_FIELD].getGlideObject().getNumericValue()); } catch (e) { row.read_err = String(e); }
      w2.deleteRecord();
      row.cleaned_up = true;
    } else { row.error = 'insert or get failed'; }
    out(row);
  }
  out({ probe: 'DONE' });
})();
