// Tests for wcag_page.mjs. Run: node --test scripts/test_wcag_page.mjs
// Browser tests skip cleanly when the page runner is not installed (scripts/setup_page_runner.sh).
import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import path from 'node:path';
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import {
  parseArgs, selectChecks, scFromAxeTag, axeTagsForLevel, circleIntersectsRect, contrastRatio,
  helpOrderConflicts, understandingUrl, startServer, depsInstalled, SC,
  helpOrderFindings, parseCssColor, compositeOver, controlBoundaryVerdict, focusIndicatorVerdict,
  crawlKey, redundantEntryFindings, coverage, LOGO_MSG, CHECKS,
} from './wcag_page.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SCRIPT = path.join(HERE, 'wcag_page.mjs');
const FIX = path.join(HERE, 'page-fixtures');
const SKIP = depsInstalled() ? false : 'page runner not installed (run scripts/setup_page_runner.sh)';

function run(args) {
  return new Promise((resolve) => {
    execFile(process.execPath, [SCRIPT, ...args, '--json'], { cwd: FIX, timeout: 120000, maxBuffer: 32 << 20 }, (err, stdout, stderr) => {
      let json = null; try { json = JSON.parse(stdout); } catch { /* leave null */ }
      resolve({ code: err ? err.code : 0, json, stderr });
    });
  });
}
const pick = (res, sc, rule) => res.json.findings.filter((f) => f.sc === sc && (!rule || f.rule === rule));

// ------------------------------------------------------------------ unit tests (no browser)
describe('pure helpers', () => {
  test('SC table has 87 entries with 2.2 additions', () => {
    assert.equal(Object.keys(SC).length, 87);
    for (const id of ['2.4.11', '2.4.12', '2.4.13', '2.5.7', '2.5.8', '3.2.6', '3.3.7', '3.3.8', '3.3.9']) assert.ok(SC[id], id);
    assert.equal(SC['2.5.8'][0], 'AA');
    assert.equal(understandingUrl('2.5.8'), 'https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html');
  });
  test('axe tag mapping', () => {
    assert.equal(scFromAxeTag('wcag111'), '1.1.1');
    assert.equal(scFromAxeTag('wcag1412'), '1.4.12');
    assert.equal(scFromAxeTag('wcag258'), '2.5.8');
    assert.equal(scFromAxeTag('wcag2aa'), null);
    assert.equal(scFromAxeTag('best-practice'), null);
    assert.ok(axeTagsForLevel('AA').includes('wcag22aa'));
    assert.ok(!axeTagsForLevel('AA').includes('wcag2aaa'));
    assert.ok(axeTagsForLevel('AAA').includes('wcag2aaa'));
    assert.ok(!axeTagsForLevel('A').includes('wcag2aa'));
  });
  test('spacing circle geometry (2.5.8)', () => {
    const c = { x: 8, y: 8 };
    assert.equal(circleIntersectsRect(c, 12, { x: 18, y: 0, w: 16, h: 16 }), true); // 10px away
    assert.equal(circleIntersectsRect(c, 12, { x: 20, y: 0, w: 16, h: 16 }), false); // exactly 12px: touching is allowed
    assert.equal(circleIntersectsRect(c, 12, { x: 17, y: 17, w: 10, h: 10 }), false); // diagonal 12.7px
  });
  test('contrast ratio', () => {
    assert.equal(+contrastRatio([0, 0, 0], [255, 255, 255]).toFixed(2), 21);
    assert.equal(+contrastRatio([118, 118, 118], [255, 255, 255]).toFixed(2), 4.54);
  });
  test('help order comparison (3.2.6)', () => {
    const a = { order: ['contact', 'self-help'] }, b = { order: ['self-help', 'chat', 'contact'] }, c = { order: ['contact', 'chat'] };
    assert.equal(helpOrderConflicts([a, b]).length, 1);
    assert.equal(helpOrderConflicts([a, c]).length, 0);
  });
  test('argument parsing and rule selection', () => {
    const o = parseArgs(['x.html', '--level', 'aaa', '--viewport', '1024x768', '--pages=3', '--rules', 'focus,2.5.8']);
    assert.equal(o.level, 'AAA'); assert.deepEqual(o.viewport, { width: 1024, height: 768 }); assert.equal(o.pages, 3);
    assert.deepEqual([...o.selection.checks].sort(), ['focus', 'target-size']);
    assert.deepEqual([...o.selection.scs], ['2.5.8']);
    assert.ok(selectChecks('1.1.1').checks.has('axe'));
    assert.ok(!selectChecks(null, false).checks.has('axe'));
    assert.throws(() => parseArgs(['x.html', '--rules', 'nope']));
    assert.throws(() => parseArgs(['--json']));
    assert.throws(() => parseArgs(['x.html', '--level', 'B']));
  });
  test('help order baseline: one finding per differing page (3.2.6)', () => {
    const base = { order: ['self-help', 'contact', 'phone'] }, same = { order: ['self-help', 'contact'] }, odd = { order: ['contact', 'self-help', 'phone'] };
    assert.equal(helpOrderConflicts([base, same, same, odd]).length, 3); // pairwise view
    const f = helpOrderFindings([base, same, same, odd]);
    assert.equal(f.length, 1); assert.equal(f[0].b, odd);
  });
  test('crawl key normalisation', () => {
    assert.equal(crawlKey('http://127.0.0.1:1/a.html?from=nav#x', true), 'http://127.0.0.1:1/a.html');
    assert.equal(crawlKey('http://127.0.0.1:1/', true), 'http://127.0.0.1:1/index.html');
    assert.equal(crawlKey('http://127.0.0.1:1/plots/', true), 'http://127.0.0.1:1/plots/index.html');
    assert.equal(crawlKey('https://example.org/a?b=1#c', false), 'https://example.org/a?b=1');
  });
  test('css colour parsing and compositing', () => {
    assert.deepEqual(parseCssColor('rgb(1, 2, 3)'), [1, 2, 3, 1]);
    assert.deepEqual(parseCssColor('rgba(10, 20, 30, 0.5)'), [10, 20, 30, 0.5]);
    assert.deepEqual(parseCssColor('rgb(10 20 30 / 0.25)'), [10, 20, 30, 0.25]);
    assert.deepEqual(parseCssColor('color(srgb 1 0 0)'), [255, 0, 0, 1]);
    assert.deepEqual(parseCssColor('transparent'), [0, 0, 0, 0]);
    assert.equal(parseCssColor('oklch(0.5 0.1 20)'), null);
    assert.deepEqual(compositeOver([0, 0, 0, 0.5], [255, 255, 255, 1]), [127.5, 127.5, 127.5, 1]);
  });
  test('1.4.11 control boundary verdicts', () => {
    assert.equal(controlBoundaryVerdict({ borderRatio: 4.5, bgRatio: 1 }), 'pass');
    assert.equal(controlBoundaryVerdict({ borderRatio: null, bgRatio: 12 }), 'pass'); // dark field on white
    assert.equal(controlBoundaryVerdict({ borderRatio: 1.4, bgRatio: 1 }), 'fail');
    assert.equal(controlBoundaryVerdict({ borderRatio: null, bgRatio: 1 }), 'fail');
    assert.equal(controlBoundaryVerdict({ borderRatio: null, bgRatio: 1.16 }), 'warn'); // distinct background: conservative
    assert.equal(controlBoundaryVerdict({ borderRatio: 1.2, shadowRatio: 3.2, bgRatio: 1 }), 'pass');
  });
  test('1.4.11 focus indicator verdicts', () => {
    const white = [255, 255, 255, 1], navy = [0, 0, 80, 1];
    assert.equal(focusIndicatorVerdict({ color: [26, 77, 191, 1], outer: white, own: white }).verdict, 'pass');
    assert.equal(focusIndicatorVerdict({ color: [255, 214, 214, 1], outer: white, own: white, offset: 2 }).verdict, 'fail');
    assert.equal(focusIndicatorVerdict({ color: [255, 214, 214, 1], outer: white, own: white, otherChange: true }).verdict, 'warn');
    // outline touching a dark button: adjacent to the button colour too
    assert.equal(focusIndicatorVerdict({ color: [255, 214, 214, 1], outer: white, own: navy, offset: 0 }).verdict, 'pass');
    assert.equal(focusIndicatorVerdict({ color: [255, 214, 214, 1], outer: white, own: navy, offset: 3 }).verdict, 'fail');
    assert.equal(focusIndicatorVerdict({ color: [0, 0, 0, 1], outer: null }), null);
  });
  test('3.3.7 redundant entry across sections and step pages', () => {
    const fld = (selector, keys, section, extra = {}) => ({ selector, snippet: '', keys, section, exempt: null, confirm: false, copyOption: false, ...extra });
    const p1 = { loc: { file: 's1.html' }, isStep: true, fields: [fld('#a', ['autocomplete email'], 0), fld('#pc', ['autocomplete postal-code'], 1), fld('#pc2', ['autocomplete postal-code'], 2)] };
    const p2 = { loc: { file: 's2.html' }, isStep: true, fields: [fld('#b', ['autocomplete email'], 0), fld('#pw', ['label "password"'], 0, { exempt: 'security' })] };
    const f = redundantEntryFindings([p1, p2]);
    assert.deepEqual(f.map((x) => [x.file, x.selector, x.severity]), [['s1.html', '#pc2', 'warn'], ['s2.html', '#b', 'warn']]);
    p2.fields[0].exempt = 'auto-populated'; p1.fields[2].copyOption = true;
    assert.equal(redundantEntryFindings([p1, p2]).length, 0);
    p2.fields[0].exempt = null; p2.isStep = false;
    assert.equal(redundantEntryFindings([p1, p2]).length, 0, 'non-step pages are not compared');
  });
  test('coverage: checks_sc and sc_covered follow checks, level and --rules', () => {
    const all = coverage(parseArgs(['x.html']), ['1.1.1', '1.4.3', '1.4.6']);
    assert.deepEqual(all.checks_sc['non-text-contrast'], ['1.4.11']);
    assert.deepEqual(all.checks_sc.axe, ['1.1.1', '1.4.3']);
    for (const sc of ['1.4.11', '2.1.2', '2.2.2', '4.1.3', '3.2.6', '3.3.7', '2.4.11']) assert.ok(all.sc_covered.includes(sc), sc);
    assert.ok(!all.sc_covered.includes('1.4.6') && !all.sc_covered.includes('2.4.12'), 'AAA dropped at AA');
    assert.ok(coverage(parseArgs(['x.html', '--level', 'AAA'])).sc_covered.includes('2.4.12'));
    const one = coverage(parseArgs(['x.html', '--rules', '2.2.2']), ['2.2.2', '1.1.1']);
    assert.deepEqual(one.sc_covered, ['2.2.2']); assert.deepEqual(Object.keys(one.checks_sc).sort(), ['auto-update', 'axe']);
    assert.ok(CHECKS.dialogs.includes('2.1.2') && CHECKS['status-messages'].includes('4.1.3'));
    assert.equal(LOGO_MSG, 'possible logotype exception (1.4.3) \u2014 confirm');
  });
  test('--probe-actions option (default off)', () => {
    assert.equal(parseArgs(['https://example.org/']).probeActions, false);
    assert.equal(parseArgs(['https://example.org/', '--probe-actions']).probeActions, true);
  });
  test('help position relative to main content (3.2.6)', () => {
    const a = { order: ['self-help', 'phone'], zones: { 'self-help': 'before-main', phone: 'before-main' } };
    const b = { order: ['self-help', 'phone'], zones: { 'self-help': 'after-main', phone: 'after-main' } };
    const c = { order: ['self-help', 'phone'], zones: { 'self-help': 'before-main', phone: 'before-main' } };
    const f = helpOrderConflicts([a, b]);
    assert.equal(f.length, 1); assert.equal(f[0].kind, 'position'); assert.deepEqual(f[0].moved, ['self-help', 'phone']);
    assert.equal(helpOrderConflicts([a, c]).length, 0);
    assert.equal(helpOrderConflicts([{ order: ['phone'] }, { order: ['phone'], zones: { phone: 'main' } }]).length, 0, 'unknown zone is not a conflict');
  });
  test('3.3.7 inferred purpose links fields only within the same form', () => {
    const fld = (selector, keys, section, form) => ({ selector, snippet: '', keys, section, form, exempt: null, confirm: false, copyOption: false });
    const page = (fields, isStep = false) => [{ loc: { file: 'p.html' }, isStep, fields }];
    const same = redundantEntryFindings(page([fld('#a', ['purpose email'], 0, 0), fld('#b', ['purpose email'], 1, 0)]));
    assert.deepEqual(same.map((x) => x.selector), ['#b']); assert.match(same[0].message, /same information \(email/);
    assert.equal(redundantEntryFindings(page([fld('#a', ['purpose email'], 0, 0), fld('#n', ['purpose email'], 1, 1)])).length, 0, 'footer newsletter form is a separate process');
    assert.equal(redundantEntryFindings(page([fld('#a', ['purpose email'], 0, 0), fld('#n', ['purpose email'], 1, 1)], true)).length, 0, 'even on a step page');
    assert.equal(redundantEntryFindings(page([fld('#a', ['label "email"'], 0, 0), fld('#n', ['label "email"'], 1, 1)])).length, 1, 'identical labels still match across sections');
  });
  test('--observe option', () => {
    assert.equal(parseArgs(['x.html', '--observe', '2500']).observe, 2500);
    assert.equal(parseArgs(['x.html']).observe, 6000);
    assert.throws(() => parseArgs(['x.html', '--observe', '10']));
  });
  test('static server refuses path traversal', async () => {
    const { server, origin } = await startServer(FIX);
    try {
      const get = (p) => new Promise((res) => http.get(origin + p, (r) => { r.resume(); res(r.statusCode); }));
      assert.equal(await get('/smoke.html'), 200);
      assert.equal(await get('/..%2fwcag_page.mjs'), 403);
      assert.notEqual(await get('/%2e%2e/wcag_page.mjs'), 200);
      assert.equal(await get('/missing.html'), 404);
    } finally { server.close(); }
  });
});

// ------------------------------------------------------------------ CLI tests (browser)
describe('cli', () => {
  test('--help exits 0', async () => {
    const r = await new Promise((res) => execFile(process.execPath, [SCRIPT, '--help'], (e, out) => res({ code: e ? e.code : 0, out })));
    assert.equal(r.code, 0); assert.match(r.out, /--level A\|AA\|AAA/);
  });
  test('setup_page_runner.sh --help prints only the header comment', async () => {
    const r = await new Promise((res) => execFile('bash', [path.join(HERE, 'setup_page_runner.sh'), '--help'], (e, out) => res({ code: e ? e.code : 0, out })));
    assert.equal(r.code, 0);
    const lines = r.out.trimEnd().split('\n');
    assert.match(lines[0], /^Install the rendered-page runner/);
    assert.match(lines[lines.length - 1], /--check\s+verify the install only/);
    assert.ok(!/set -euo|PLAYWRIGHT_VERSION|^#/m.test(r.out));
  });
  test('--help documents --probe-actions and WCAG22_DEBUG', async () => {
    const r = await new Promise((res) => execFile(process.execPath, [SCRIPT, '--help'], (e, out) => res({ out })));
    assert.match(r.out, /--probe-actions/); assert.match(r.out, /WCAG22_DEBUG/);
  });
  test('usage error exits 2', async () => {
    const r = await run(['--level', 'Z', 'x.html']);
    assert.equal(r.code, 2);
  });
  test('missing target exits 2', { skip: SKIP }, async () => {
    const r = await run(['does-not-exist.html']);
    assert.equal(r.code, 2);
  });
});

describe('rendered checks', { concurrency: 4, skip: SKIP }, () => {
  test('axe smoke: violations map to SC and envelope matches contract', async () => {
    const r = await run(['smoke.html', '--rules', 'axe']);
    assert.equal(r.code, 1);
    const { meta, summary, findings } = r.json;
    assert.equal(meta.tool, 'wcag_page'); assert.equal(meta.wcag, '2.2 (2024-12-12)'); assert.ok(meta.date && meta.target);
    assert.ok(meta.axe_sc_covered.includes('1.1.1'));
    const img = findings.find((f) => f.rule === 'axe:image-alt');
    assert.ok(img); assert.equal(img.sc, '1.1.1'); assert.equal(img.severity, 'fail'); assert.equal(img.level, 'A');
    assert.equal(img.file, 'smoke.html'); assert.match(img.help, /dequeuniversity/); assert.match(img.snippet, /<img/);
    for (const k of ['tool', 'sc', 'level', 'rule', 'severity', 'line', 'col', 'selector', 'snippet', 'message', 'help', 'evidence']) assert.ok(k in img, k);
    assert.ok(findings.some((f) => f.rule === 'axe:color-contrast' && f.sc === '1.4.3'));
    assert.ok(summary.by_severity.fail >= 3); assert.ok(summary.by_sc['1.1.1'].fail >= 1);
  });

  test('2.5.8 target size: crowded 16px buttons warn', async () => {
    const r = await run(['target-size-bad.html', '--rules', 'target-size']);
    const f = pick(r, '2.5.8', 'target-size-undersized');
    assert.equal(f.length, 3); assert.equal(f[0].severity, 'warn'); assert.equal(f[0].evidence.width, 16);
  });
  test('2.5.8 target size: spaced, inline and large targets pass', async () => {
    const r = await run(['target-size-ok.html', '--rules', 'target-size']);
    assert.equal(pick(r, '2.5.8', 'target-size-undersized').length, 0);
  });

  test('2.4.7 focus visible: outline:none fails', async () => {
    const r = await run(['focus-visible-bad.html', '--rules', '2.4.7']);
    assert.equal(r.code, 1);
    assert.equal(pick(r, '2.4.7', 'focus-not-visible').length, 2);
  });
  test('--level A drops AA findings; --screenshots writes files', async () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'w22-shots-'));
    try {
      const r = await run(['focus-visible-bad.html', '--rules', 'focus', '--level', 'A', '--screenshots', dir]);
      assert.equal(r.code, 0); assert.equal(pick(r, '2.4.7').length, 0);
      const files = fs.readdirSync(dir);
      assert.ok(files.includes('p1-page.png')); assert.ok(files.some((f) => f.startsWith('p1-focus-')));
    } finally { fs.rmSync(dir, { recursive: true, force: true }); }
  });
  test('2.4.7 focus visible: outline indicator passes', async () => {
    const r = await run(['focus-visible-ok.html', '--rules', '2.4.7']);
    assert.equal(r.code, 0); assert.equal(pick(r, '2.4.7').length, 0);
    assert.equal(r.json.meta.pages[0].keyboard_walk.focus_visible_checked, 2);
  });

  test('2.4.11 focus not obscured: fixed banner hides focus', async () => {
    const r = await run(['focus-obscured-bad.html', '--rules', 'focus']);
    const f = pick(r, '2.4.11', 'focus-obscured-fully');
    assert.ok(f.length >= 1); assert.equal(f[0].severity, 'fail'); assert.ok(f[0].evidence.covered_by.length);
    assert.equal(pick(r, '2.4.12').length, 0, 'AAA findings dropped at AA');
  });
  test('2.4.11 focus not obscured: scroll-padding keeps focus visible; partial reported at AAA only', async () => {
    const aa = await run(['focus-obscured-ok.html', '--rules', 'focus']);
    assert.equal(pick(aa, '2.4.11').length, 0);
    const aaa = await run(['focus-obscured-ok.html', '--rules', 'focus', '--level', 'AAA']);
    assert.equal(pick(aaa, '2.4.11').length, 0);
    assert.ok(pick(aaa, '2.4.12', 'focus-obscured-partially').every((f) => f.severity === 'warn'));
  });

  test('2.1.2 keyboard trap: cycling widget fails', async () => {
    const r = await run(['keyboard-trap-bad.html', '--rules', '2.1.2']);
    const f = pick(r, '2.1.2', 'keyboard-trap');
    assert.equal(f.length, 1); assert.equal(f[0].severity, 'fail'); assert.equal(f[0].evidence.released_by, null);
  });
  test('2.1.2 keyboard trap: Escape releases focus -> manual only', async () => {
    const r = await run(['keyboard-trap-escape.html', '--rules', '2.1.2']);
    assert.equal(pick(r, '2.1.2', 'keyboard-trap').length, 0);
    const f = pick(r, '2.1.2', 'focus-contained');
    assert.equal(f.length, 1); assert.equal(f[0].evidence.released_by, 'Escape then Tab');
  });
  test('2.1.2 native date/time inputs: Tab through their segments is not a trap', async () => {
    const r = await run(['keyboard-datetime-ok.html', '--rules', '2.1.2']);
    assert.equal(pick(r, '2.1.2').length, 0, JSON.stringify(pick(r, '2.1.2')));
    const walk = r.json.meta.pages[0].keyboard_walk;
    assert.equal(walk.stop, 'wrapped'); assert.equal(walk.focused, walk.tabbable_on_page);
    assert.ok(walk.presses > walk.tabbable_on_page); // segments took extra presses
  });
  test('2.1.2 native date input that swallows Tab is still a trap', async () => {
    const r = await run(['keyboard-datetime-bad.html', '--rules', '2.1.2']);
    const f = pick(r, '2.1.2', 'keyboard-trap');
    assert.equal(f.length, 1); assert.equal(f[0].selector, '#d'); assert.equal(f[0].evidence.released_by, null);
    assert.equal(f[0].evidence.multi_part_control, 'input[type=date]'); assert.ok(f[0].evidence.tab_presses_on_element >= 10);
  });
  test('2.1.2 keyboard trap: normal page has none', async () => {
    const r = await run(['focus-order-ok.html', '--rules', '2.1.2']);
    assert.equal(pick(r, '2.1.2').length, 0); assert.equal(r.json.meta.pages[0].keyboard_walk.stop, 'wrapped');
  });

  test('2.4.3 focus order: positive tabindex and visual jumps flagged', async () => {
    const r = await run(['focus-order-bad.html', '--rules', '2.4.3']);
    assert.equal(pick(r, '2.4.3', 'positive-tabindex').length, 2);
    const a = pick(r, '2.4.3', 'focus-order-anomaly');
    assert.equal(a.length, 1); assert.ok(a[0].evidence.anomalies.some((x) => x.type === 'visual-backwards'));
  });
  test('2.4.3 focus order: natural order is clean', async () => {
    const r = await run(['focus-order-ok.html', '--rules', '2.4.3']);
    assert.equal(pick(r, '2.4.3').length, 0);
  });

  test('a check that stalls the page times out, is named, and the run still finishes', async () => {
    const t0 = Date.now();
    const r = await run(['hang-after-load.html', '--rules', 'auto-update,focus', '--check-timeout', '4000']);
    assert.ok(Date.now() - t0 < 60000, 'run should finish well inside the harness timeout');
    assert.ok(r.json, 'JSON report is still written');
    const errs = r.json.meta.pages[0].errors || [];
    assert.ok(errs.some((e) => e.check === 'auto-update' && /timed out after 4s/.test(e.error)), JSON.stringify(errs));
    assert.ok(errs.some((e) => e.check === 'focus' && /skipped: page abandoned after auto-update timed out/.test(e.error)), JSON.stringify(errs));
    assert.ok(r.json.meta.pages[0].check_ms['auto-update'] >= 4000);
  });
  test('1.4.10 reflow: fixed 900px column fails', async () => {
    const r = await run(['reflow-bad.html', '--rules', 'reflow']);
    const f = pick(r, '1.4.10', 'reflow-horizontal-scroll');
    assert.equal(f.length, 1); assert.equal(f[0].severity, 'fail'); assert.ok(f[0].evidence.scroll_width > 320);
  });
  test('1.4.10 reflow: responsive page passes', async () => {
    const r = await run(['reflow-ok.html', '--rules', 'reflow']);
    assert.equal(r.code, 0); assert.equal(pick(r, '1.4.10').length, 0);
  });
  test('1.4.10 reflow: wide data table is exempt -> manual', async () => {
    const r = await run(['reflow-table.html', '--rules', 'reflow']);
    assert.equal(r.code, 0);
    const f = pick(r, '1.4.10');
    assert.equal(f.length, 1); assert.equal(f[0].rule, 'reflow-exempt-content'); assert.equal(f[0].severity, 'manual');
  });

  test('1.4.12 text spacing + 1.4.4 resize: fixed-height box clips', async () => {
    const r = await run(['text-clip.html', '--rules', 'text-spacing,resize-text']);
    assert.equal(pick(r, '1.4.12', 'text-spacing-clipped').length, 1);
    assert.equal(pick(r, '1.4.12', 'text-spacing-clipped')[0].severity, 'fail');
    assert.equal(pick(r, '1.4.4', 'resize-text-clipped').length, 1);
  });
  test('1.4.12 text spacing + 1.4.4 resize: flexible box passes', async () => {
    const r = await run(['text-ok.html', '--rules', 'text-spacing,resize-text']);
    assert.equal(pick(r, '1.4.12').length + pick(r, '1.4.4').length, 0);
  });

  test('1.4.3 contrast sampling on gradients (axe incomplete)', async () => {
    const r = await run(['contrast-gradient.html', '--rules', '1.4.3']);
    const f = pick(r, '1.4.3', 'contrast-sampled-background');
    const faint = f.find((x) => x.selector === '#faint'), strong = f.find((x) => x.selector === '#strong');
    assert.ok(faint && strong);
    assert.equal(faint.severity, 'warn'); assert.ok(faint.evidence.contrast.p5 < 4.5);
    assert.equal(strong.severity, 'info'); assert.ok(strong.evidence.contrast.p5 >= 4.5);
  });

  test('1.4.3 SVG labels: shapes in the sample box but not behind the glyphs are ignored', async () => {
    const r = await run(['contrast-svg-ok.html', '--rules', '1.4.3']);
    const f = pick(r, '1.4.3', 'contrast-sampled-background');
    assert.equal(f.length, 2);
    for (const x of f) {
      assert.equal(x.severity, 'info', JSON.stringify(x.evidence)); assert.ok(x.evidence.contrast.p5 >= 4.5);
      assert.equal(x.evidence.fg_source, 'SVG fill'); assert.deepEqual(x.evidence.fg_rgba.slice(0, 3), [34, 34, 34]);
      assert.match(x.evidence.sample_region, /behind the glyphs/);
    }
    const ignored = f.filter((x) => x.evidence.low_pixels_ignored);
    assert.ok(ignored.length >= 1); assert.ok(ignored.every((x) => x.evidence.box_contrast.p5 < 4.5));
  });
  test('1.4.3 SVG labels: faint fill or dark shape behind the glyphs still warns', async () => {
    const r = await run(['contrast-svg-bad.html', '--rules', '1.4.3']);
    const f = pick(r, '1.4.3', 'contrast-sampled-background');
    const faint = f.find((x) => x.selector === '#lbl-faint'), dark = f.find((x) => x.selector === '#lbl-dark');
    assert.ok(faint && dark);
    assert.equal(faint.severity, 'warn'); assert.deepEqual(faint.evidence.fg_rgba.slice(0, 3), [180, 180, 180]); assert.ok(faint.evidence.contrast.median < 4.5);
    assert.equal(dark.severity, 'warn'); assert.ok(dark.evidence.contrast.p5 < 3);
  });

  test('3.2.6 consistent help: order differs across pages', async () => {
    const r = await run(['help-bad', '--pages', '2', '--rules', 'consistent-help']);
    const f = pick(r, '3.2.6', 'help-order-inconsistent');
    assert.equal(f.length, 1); assert.deepEqual(f[0].evidence.order_a, ['contact', 'self-help']);
  });
  test('3.2.6 consistent help: same order passes', async () => {
    const r = await run(['help-ok', '--pages', '2', '--rules', 'consistent-help']);
    assert.equal(pick(r, '3.2.6', 'help-order-inconsistent').length, 0);
    assert.equal(r.json.meta.pages.filter((p) => !p.errors).length, 2);
  });

  test('3.3.8 / 3.3.7 authentication: paste blocking, autocomplete off, captcha, re-entry', async () => {
    const r = await run(['auth-bad.html', '--rules', 'auth', '--level', 'AAA']);
    assert.equal(r.code, 1);
    assert.equal(pick(r, '3.3.8', 'password-paste-blocked')[0].severity, 'fail');
    assert.equal(pick(r, '3.3.8', 'password-autocomplete-off')[0].severity, 'warn');
    assert.equal(pick(r, '3.3.8', 'captcha-cognitive-test')[0].severity, 'manual');
    assert.equal(pick(r, '3.3.9', 'captcha-cognitive-test').length, 1);
    assert.equal(pick(r, '3.3.7', 'possible-redundant-entry')[0].selector, '#u2');
  });
  test('3.3.8 authentication: well-formed sign-in passes', async () => {
    const r = await run(['auth-ok.html', '--rules', 'auth']);
    assert.equal(r.code, 0); assert.equal(r.json.findings.length, 0);
  });

  test('envelope meta lists checks_sc and sc_covered', async () => {
    const r = await run(['smoke.html', '--rules', 'axe,non-text-contrast']);
    const m = r.json.meta;
    assert.deepEqual(Object.keys(m.checks_sc).sort(), ['axe', 'non-text-contrast']);
    assert.deepEqual(m.checks_sc['non-text-contrast'], ['1.4.11']);
    assert.ok(m.checks_sc.axe.includes('1.1.1'));
    assert.ok(m.sc_covered.includes('1.4.11') && m.sc_covered.includes('1.1.1'));
    assert.deepEqual(m.sc_covered, [...new Set(Object.values(m.checks_sc).flat())].sort((a, b) => a.localeCompare(b, 'en', { numeric: true })));
  });

  test('1.4.11 non-text contrast: pale borders, tinted field, custom checkbox, faint focus ring', async () => {
    const r = await run(['nontext-contrast-bad.html', '--rules', '1.4.11']);
    assert.equal(r.code, 1);
    const fails = pick(r, '1.4.11', 'ui-boundary-contrast').map((f) => f.selector).sort();
    assert.deepEqual(fails, ['#agree', '#pale']);
    const maybe = pick(r, '1.4.11', 'ui-boundary-contrast-maybe');
    assert.deepEqual(maybe.map((f) => [f.selector, f.severity]), [['#tinted', 'warn']]);
    assert.ok(!r.json.findings.some((f) => f.selector === '#off'), 'disabled control excluded');
    const ring = pick(r, '1.4.11', 'focus-indicator-contrast');
    assert.equal(ring.length, 1); assert.equal(ring[0].selector, '#send'); assert.equal(ring[0].severity, 'fail');
    assert.ok(ring[0].evidence.ratio < 3);
  });
  test('1.4.11 non-text contrast: strong borders, dark field, native checkbox, visible ring pass', async () => {
    const r = await run(['nontext-contrast-ok.html', '--rules', '1.4.11']);
    assert.equal(r.code, 0); assert.equal(pick(r, '1.4.11').length, 0);
  });

  test('2.4.11 sticky header (pointer-events:none, smooth scroll) covers a link focused while tabbing down', async () => {
    const r = await run(['focus-obscured-sticky-bad.html', '--rules', 'focus']);
    const all = pick(r, '2.4.11', 'focus-obscured-fully');
    const f = all.filter((x) => !x.evidence.method); // found by the straight Tab walk (the mid-scroll sweep adds evidence.method)
    assert.equal(f.length, 1); assert.equal(f[0].severity, 'fail');
    assert.match(f[0].snippet, /Volunteer rota/);
    assert.deepEqual(f[0].evidence.covered_by, ['html > body > header']);
    assert.equal(pick(r, '1.4.11').length, 0, 'UA auto focus ring is not assessed');
  });
  test('2.4.11 sticky header with scroll-padding-top passes', async () => {
    const r = await run(['focus-obscured-sticky-ok.html', '--rules', 'focus']);
    assert.equal(pick(r, '2.4.11').length, 0);
  });

  test('2.1.2 dialog trap: modal opened by aria-haspopup trigger cannot be left', async () => {
    const r = await run(['dialog-trap-bad.html', '--rules', 'dialogs']);
    assert.equal(r.code, 1);
    const f = pick(r, '2.1.2', 'keyboard-trap-dialog');
    assert.equal(f.length, 1); assert.equal(f[0].selector, '#cookie');
    assert.equal(f[0].evidence.trigger, '#prefs'); assert.equal(f[0].evidence.released_by, null);
  });
  test('2.1.2 dialog trap: native dialog and Escape-closable modal pass; state restored', async () => {
    const r = await run(['dialog-trap-ok.html', '--rules', 'dialogs,focus']);
    assert.equal(pick(r, '2.1.2').length, 0);
    const probes = r.json.meta.pages[0].keyboard_walk.dialog_probes;
    assert.deepEqual(probes.map((p) => [p.trigger, p.opened, !!p.released]), [['#open-native', true, true], ['#open-custom', true, true]]);
    assert.equal(probes[1].released, 'Escape');
  });

  test('2.2.2 auto-rotating carousel without pause control warns', async () => {
    const r = await run(['carousel-bad.html', '--rules', 'auto-update', '--observe', '3000']);
    const f = pick(r, '2.2.2', 'auto-update-no-pause');
    assert.equal(f.length, 1); assert.equal(f[0].severity, 'warn'); assert.ok(f[0].evidence.change_windows >= 2);
    assert.match(f[0].snippet, /carousel/);
  });
  test('2.2.2 carousel with a pause button passes', async () => {
    const r = await run(['carousel-ok.html', '--rules', 'auto-update', '--observe', '3000']);
    assert.equal(pick(r, '2.2.2').length, 0);
  });

  test('4.1.3 status message: text written after submit without a live region warns', async () => {
    const r = await run(['status-bad.html', '--rules', '4.1.3']);
    const f = pick(r, '4.1.3', 'status-message-not-announced');
    assert.deepEqual(f.map((x) => x.selector), ['#wish-note']);
    assert.match(f[0].evidence.text, /added to your wishlist/);
  });
  test('4.1.3 / 2.1.2 remote targets: buttons are not activated without --probe-actions', async () => {
    const { server, origin } = await startServer(FIX);
    try {
      const off = await run([origin + '/status-bad.html', '--rules', '4.1.3']);
      assert.equal(pick(off, '4.1.3', 'status-message-not-announced').length, 0);
      const note = pick(off, '4.1.3', 'status-messages-not-probed');
      assert.equal(note.length, 1); assert.equal(note[0].severity, 'manual'); assert.ok(note[0].evidence.buttons.length >= 1);
      const on = await run([origin + '/status-bad.html', '--rules', '4.1.3', '--probe-actions']);
      assert.deepEqual(pick(on, '4.1.3', 'status-message-not-announced').map((x) => x.selector), ['#wish-note']);
      assert.equal(pick(on, '4.1.3', 'status-messages-not-probed').length, 0);
      const doff = await run([origin + '/dialog-trap-plain-bad.html', '--rules', 'dialogs']);
      assert.equal(pick(doff, '2.1.2', 'keyboard-trap-dialog').length, 0);
      assert.equal(pick(doff, '2.1.2', 'dialog-probe-skipped').length, 1);
      const don = await run([origin + '/dialog-trap-plain-bad.html', '--rules', 'dialogs', '--probe-actions']);
      assert.equal(pick(don, '2.1.2', 'keyboard-trap-dialog').length, 1);
    } finally { server.close(); }
  });
  test('4.1.3 status probe stays on by default for local files', async () => {
    const r = await run(['status-bad.html', '--rules', '4.1.3']);
    assert.equal(pick(r, '4.1.3', 'status-messages-not-probed').length, 0);
    assert.equal(pick(r, '4.1.3', 'status-message-not-announced').length, 1);
  });
  test('4.1.3 status message: role=status region passes', async () => {
    const r = await run(['status-ok.html', '--rules', '4.1.3']);
    assert.equal(pick(r, '4.1.3').length, 0);
  });

  test('4.1.3 requested content: prev/next/show-more swapping their own item is not a status message', async () => {
    const r = await run(['status-requested-ok.html', '--rules', '4.1.3']);
    assert.equal(pick(r, '4.1.3').length, 0, JSON.stringify(pick(r, '4.1.3')));
  });
  test('4.1.3 requested content: Save and form-step messages still warn; distant nav swap is a review note', async () => {
    const r = await run(['status-requested-bad.html', '--rules', '4.1.3']);
    const f = pick(r, '4.1.3', 'status-message-not-announced');
    const warn = f.filter((x) => x.severity === 'warn').map((x) => x.selector).sort();
    assert.deepEqual(warn, ['#save-note', '#step-error']);
    const note = f.filter((x) => x.severity === 'manual');
    assert.deepEqual(note.map((x) => x.selector), ['#far-text']); assert.equal(note[0].evidence.trigger_label, 'Newer');
    assert.ok(!f.some((x) => x.selector === '#notice-text'));
  });

  test('1.4.3 logotype: brand link and logo text downgraded to warn, body text still fails', async () => {
    const r = await run(['logo-contrast.html', '--rules', '1.4.3']);
    const f = pick(r, '1.4.3', 'axe:color-contrast');
    const bySev = (s) => f.filter((x) => x.severity === s);
    assert.equal(bySev('fail').length, 1); assert.match(bySev('fail')[0].snippet, /Gates close/);
    assert.equal(bySev('warn').length, 2);
    for (const w of bySev('warn')) { assert.ok(w.message.startsWith(LOGO_MSG)); assert.ok(w.evidence.logotype); }
  });

  test('3.3.7 redundant entry: step sections and step pages warn', async () => {
    const r = await run(['steps-bad', '--pages', '2', '--rules', '3.3.7']);
    const f = pick(r, '3.3.7', 'redundant-entry');
    assert.deepEqual(f.map((x) => [path.basename(x.file), x.selector, x.severity]).sort(), [['step1.html', '#pc2', 'warn'], ['step2.html', '#em2', 'warn']]);
    assert.equal(pick(r, '3.3.7', 'possible-redundant-entry').length, 0, 'no duplicate manual item for warned fields');
  });
  test('3.3.7 redundant entry: same-as option, pre-filled value and password confirmation pass', async () => {
    const r = await run(['steps-ok', '--pages', '2', '--rules', '3.3.7']);
    assert.equal(pick(r, '3.3.7').length, 0);
  });

  test('3.2.6 crawl loads every linked same-origin page once and flags the page with a different help order', async () => {
    const r = await run(['help-site', '--pages', '10', '--rules', 'consistent-help']);
    const loaded = r.json.meta.pages.filter((p) => !p.errors).map((p) => p.file).sort();
    assert.deepEqual(loaded, ['help-site/about.html', 'help-site/events.html', 'help-site/index.html', 'help-site/plots/index.html', 'help-site/visit.html']);
    assert.equal(new Set(r.json.meta.pages.map((p) => p.file)).size, r.json.meta.pages.length, 'no page audited twice');
    const f = pick(r, '3.2.6', 'help-order-inconsistent');
    assert.equal(f.length, 1); assert.equal(f[0].file, 'help-site/visit.html');
    assert.deepEqual(f[0].evidence.order_a, ['self-help', 'contact', 'phone', 'email']);
    assert.deepEqual(f[0].evidence.order_b, ['contact', 'self-help', 'email', 'phone']);
  });

  // ---- patterns from realistic sites that the first-generation checks missed
  test('2.4.11 sticky banner hides links only at mid-page scroll positions (mid-scroll sweep)', async () => {
    const r = await run(['focus-obscured-midscroll-bad.html', '--rules', '2.4.11']);
    const f = pick(r, '2.4.11', 'focus-obscured-fully');
    assert.ok(f.length >= 3); assert.ok(f.every((x) => x.severity === 'fail' && /Tab from the previous focus stop/.test(x.evidence.method)));
    assert.deepEqual(f[0].evidence.covered_by, ['html > body > div']);
  });
  test('2.4.11 sticky banner with scroll-padding passes the mid-scroll sweep', async () => {
    const r = await run(['focus-obscured-midscroll-ok.html', '--rules', '2.4.11']);
    assert.equal(pick(r, '2.4.11').length, 0);
  });
  test('2.1.2 trap in a div modal opened by a plain button (click listener, no aria-haspopup)', async () => {
    const r = await run(['dialog-trap-plain-bad.html', '--rules', 'dialogs']);
    const f = pick(r, '2.1.2', 'keyboard-trap-dialog');
    assert.equal(f.length, 1); assert.equal(f[0].severity, 'fail'); assert.match(f[0].evidence.trigger_reason, /plain button/);
    assert.match(f[0].snippet, /role="dialog"/);
  });
  test('2.1.2 plain-button modal that Escape closes passes', async () => {
    const r = await run(['dialog-trap-plain-ok.html', '--rules', 'dialogs,focus']);
    assert.equal(pick(r, '2.1.2').length, 0);
    const probes = r.json.meta.pages[0].keyboard_walk.dialog_probes;
    assert.equal(probes.length, 1); assert.equal(probes[0].released, 'Escape');
  });
  test('WCAG22_DEBUG logs check internals to stderr without touching the JSON on stdout', async () => {
    const r = await new Promise((res) => execFile(process.execPath, [SCRIPT, 'dialog-trap-plain-bad.html', '--rules', 'dialogs', '--json'],
      { cwd: FIX, env: { ...process.env, WCAG22_DEBUG: 'dialogs' }, maxBuffer: 32 << 20 }, (e, out, err) => res({ out, err })));
    assert.ok(JSON.parse(r.out).findings.length >= 1);
    assert.match(r.err, /^\[wcag_page:dialogs\] triggers /m); assert.ok(!/\[wcag_page:focus\]/.test(r.err));
  });
  test('2.2.2 slow rotators (hidden toggles, innerHTML) without carousel names warn after extended observation', async () => {
    const r = await run(['rotator-slow-bad.html', '--rules', 'auto-update', '--observe', '3000']);
    const f = pick(r, '2.2.2', 'auto-update-no-pause');
    assert.deepEqual(f.map((x) => x.selector).sort(), ['#notices', 'html > body > main > figure']);
    for (const x of f) { assert.equal(x.evidence.detected_by, 'mutations'); assert.ok(x.evidence.episodes >= 2); assert.ok(x.evidence.observed_ms > 3000); }
  });
  test('2.2.2 looping CSS marquee warns; small spinner ignored', async () => {
    const r = await run(['marquee-css-bad.html', '--rules', 'auto-update', '--observe', '1000']);
    const f = pick(r, '2.2.2', 'auto-update-no-pause');
    assert.equal(f.length, 1); assert.equal(f[0].evidence.detected_by, 'css-animation'); assert.equal(f[0].evidence.animation, 'scroll-left');
  });
  test('2.2.2 slow rotator with a pause control, one-off update and spinner pass', async () => {
    const r = await run(['rotator-slow-ok.html', '--rules', 'auto-update', '--observe', '3000']);
    assert.equal(pick(r, '2.2.2').length, 0);
  });
  test('3.2.6 help block moved from header to footer (same order among help items) warns', async () => {
    const r = await run(['help-moved-bad', '--pages', '2', '--rules', 'consistent-help']);
    const f = pick(r, '3.2.6', 'help-order-inconsistent');
    assert.equal(f.length, 1); assert.equal(f[0].file, 'help-moved-bad/rates.html'); assert.equal(f[0].evidence.conflict, 'position');
    assert.deepEqual(f[0].evidence.zones_a, { 'self-help': 'before-main', phone: 'before-main' });
  });
  test('3.2.6 help in the footer on every page, styled and worded differently, passes', async () => {
    const r = await run(['help-moved-ok', '--pages', '2', '--rules', 'consistent-help']);
    assert.equal(pick(r, '3.2.6').length, 0);
  });
  test('3.3.7 JS-revealed step panels: same data asked again under a different label warns', async () => {
    const r = await run(['steps-inferred-bad.html', '--rules', '3.3.7']);
    assert.deepEqual(pick(r, '3.3.7', 'redundant-entry').map((x) => x.selector).sort(), ['#cb', '#rcpt']);
  });
  test('3.3.7 contact form and footer newsletter form on one page pass', async () => {
    const r = await run(['steps-inferred-ok.html', '--rules', '3.3.7']);
    assert.equal(pick(r, '3.3.7', 'redundant-entry').length, 0);
  });
  test('3.3.7 step 2 reached only through a GET form action is crawled and compared', async () => {
    const r = await run(['steps-action', '--pages', '3', '--rules', '3.3.7']);
    assert.ok(r.json.meta.pages.some((p) => p.file === 'steps-action/plot.html' && !p.errors));
    const f = pick(r, '3.3.7', 'redundant-entry');
    assert.deepEqual(f.map((x) => [x.file, x.selector]), [['steps-action/plot.html', '#em2']]);
  });
});
