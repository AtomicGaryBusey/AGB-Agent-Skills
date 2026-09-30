#!/usr/bin/env node
// wcag_page.mjs - rendered-page WCAG 2.2 auditor (axe-core + custom checks in headless Chromium).
//
// Dependencies (playwright, axe-core, Chromium) live in the skill's gitignored .cache/;
// install them with scripts/setup_page_runner.sh. Run with --help for usage.
//
// Output follows the wcag22-a11y finding contract:
//   {"meta":{...}, "summary":{"by_sc":{...},"by_severity":{...}}, "findings":[...]}
// Exit codes: 0 no fail findings, 1 fail findings, 2 usage/runtime error.

import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const TOOL = 'wcag_page';
export const VERSION = '0.1.0';
const WCAG = '2.2 (2024-12-12)';
const SKILL_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const CACHE_DIR = process.env.WCAG22_CACHE_DIR ? path.resolve(process.env.WCAG22_CACHE_DIR) : path.join(SKILL_DIR, '.cache');
const UNDERSTANDING = 'https://www.w3.org/WAI/WCAG22/Understanding/';

// WCAG 2.2 success criteria: id -> [level, Understanding slug]. 4.1.1 is obsolete in 2.2.
export const SC = {
  '1.1.1':['A','non-text-content'], '1.2.1':['A','audio-only-and-video-only-prerecorded'], '1.2.2':['A','captions-prerecorded'], '1.2.3':['A','audio-description-or-media-alternative-prerecorded'],
  '1.2.4':['AA','captions-live'], '1.2.5':['AA','audio-description-prerecorded'], '1.2.6':['AAA','sign-language-prerecorded'], '1.2.7':['AAA','extended-audio-description-prerecorded'],
  '1.2.8':['AAA','media-alternative-prerecorded'], '1.2.9':['AAA','audio-only-live'], '1.3.1':['A','info-and-relationships'], '1.3.2':['A','meaningful-sequence'],
  '1.3.3':['A','sensory-characteristics'], '1.3.4':['AA','orientation'], '1.3.5':['AA','identify-input-purpose'], '1.3.6':['AAA','identify-purpose'],
  '1.4.1':['A','use-of-color'], '1.4.2':['A','audio-control'], '1.4.3':['AA','contrast-minimum'], '1.4.4':['AA','resize-text'],
  '1.4.5':['AA','images-of-text'], '1.4.6':['AAA','contrast-enhanced'], '1.4.7':['AAA','low-or-no-background-audio'], '1.4.8':['AAA','visual-presentation'],
  '1.4.9':['AAA','images-of-text-no-exception'], '1.4.10':['AA','reflow'], '1.4.11':['AA','non-text-contrast'], '1.4.12':['AA','text-spacing'],
  '1.4.13':['AA','content-on-hover-or-focus'], '2.1.1':['A','keyboard'], '2.1.2':['A','no-keyboard-trap'], '2.1.3':['AAA','keyboard-no-exception'],
  '2.1.4':['A','character-key-shortcuts'], '2.2.1':['A','timing-adjustable'], '2.2.2':['A','pause-stop-hide'], '2.2.3':['AAA','no-timing'],
  '2.2.4':['AAA','interruptions'], '2.2.5':['AAA','re-authenticating'], '2.2.6':['AAA','timeouts'], '2.3.1':['A','three-flashes-or-below-threshold'],
  '2.3.2':['AAA','three-flashes'], '2.3.3':['AAA','animation-from-interactions'], '2.4.1':['A','bypass-blocks'], '2.4.2':['A','page-titled'],
  '2.4.3':['A','focus-order'], '2.4.4':['A','link-purpose-in-context'], '2.4.5':['AA','multiple-ways'], '2.4.6':['AA','headings-and-labels'],
  '2.4.7':['AA','focus-visible'], '2.4.8':['AAA','location'], '2.4.9':['AAA','link-purpose-link-only'], '2.4.10':['AAA','section-headings'],
  '2.4.11':['AA','focus-not-obscured-minimum'], '2.4.12':['AAA','focus-not-obscured-enhanced'], '2.4.13':['AAA','focus-appearance'], '2.5.1':['A','pointer-gestures'],
  '2.5.2':['A','pointer-cancellation'], '2.5.3':['A','label-in-name'], '2.5.4':['A','motion-actuation'], '2.5.5':['AAA','target-size-enhanced'],
  '2.5.6':['AAA','concurrent-input-mechanisms'], '2.5.7':['AA','dragging-movements'], '2.5.8':['AA','target-size-minimum'], '3.1.1':['A','language-of-page'],
  '3.1.2':['AA','language-of-parts'], '3.1.3':['AAA','unusual-words'], '3.1.4':['AAA','abbreviations'], '3.1.5':['AAA','reading-level'],
  '3.1.6':['AAA','pronunciation'], '3.2.1':['A','on-focus'], '3.2.2':['A','on-input'], '3.2.3':['AA','consistent-navigation'],
  '3.2.4':['AA','consistent-identification'], '3.2.5':['AAA','change-on-request'], '3.2.6':['A','consistent-help'], '3.3.1':['A','error-identification'],
  '3.3.2':['A','labels-or-instructions'], '3.3.3':['AA','error-suggestion'], '3.3.4':['AA','error-prevention-legal-financial-data'], '3.3.5':['AAA','help'],
  '3.3.6':['AAA','error-prevention-all'], '3.3.7':['A','redundant-entry'], '3.3.8':['AA','accessible-authentication-minimum'], '3.3.9':['AAA','accessible-authentication-enhanced'],
  '4.1.1':['','parsing'], '4.1.2':['A','name-role-value'], '4.1.3':['AA','status-messages'],
};

// Custom check groups and the SCs they report on. "axe" reports whatever axe maps.
export const CHECKS = {
  'axe': null,
  'contrast-sample': ['1.4.3', '1.4.6'],
  'non-text-contrast': ['1.4.11'],
  'target-size': ['2.5.8'],
  'auto-update': ['2.2.2'],
  'status-messages': ['4.1.3'],
  'focus': ['2.4.7', '2.4.11', '2.4.12', '2.1.2', '2.4.3', '1.4.11'],
  'dialogs': ['2.1.2'],
  'reflow': ['1.4.10'],
  'text-spacing': ['1.4.12'],
  'resize-text': ['1.4.4'],
  'consistent-help': ['3.2.6'],
  'auth': ['3.3.7', '3.3.8', '3.3.9'],
};

const LEVEL_RANK = { A: 1, AA: 2, AAA: 3 };

// Debug logging: WCAG22_DEBUG=1 (all) or a comma list of check names (e.g. "focus,dialogs") writes
// JSON lines describing what each check saw to stderr. Never affects findings or stdout.
const DEBUG = (process.env.WCAG22_DEBUG || '').trim();
const DEBUG_SET = DEBUG && !/^(1|true|all|\*)$/i.test(DEBUG) ? new Set(DEBUG.split(',').map((x) => x.trim())) : null;
export function debugOn(check) { return !!DEBUG && (!DEBUG_SET || DEBUG_SET.has(check)); }
function dbg(check, msg, data) {
  if (!debugOn(check)) return;
  let d = ''; try { d = data === undefined ? '' : ' ' + JSON.stringify(data); } catch { d = ' [unserialisable]'; }
  process.stderr.write(`[wcag_page:${check}] ${msg}${d}\n`);
}
export const LOGO_MSG = 'possible logotype exception (1.4.3) \u2014 confirm';
const SEVERITIES = ['fail', 'warn', 'manual', 'info'];

const HELP_TEXT = `wcag_page ${VERSION} - audit rendered pages against WCAG ${WCAG}

Usage: node wcag_page.mjs <url|file.html|dir> [options]

Options:
  --json              print the JSON envelope instead of the text report
  --level A|AA|AAA    conformance level to test (default AA)
  --viewport WxH      viewport in CSS px (default 1280x800)
  --pages N           crawl same-origin links, audit up to N pages (default 1)
  --screenshots DIR   save page, reflow and failing-focus screenshots to DIR
  --timeout MS        navigation timeout in ms (default 30000)
  --max-tabs N        Tab presses in the keyboard walk (default 60)
  --observe MS        how long to watch carousels/marquees for 2.2.2 (default 6000)
  --check-timeout MS  time budget per check per page (default 120000); a check that overruns is
                      reported as an error and the rest of that page is skipped
  --rules LIST        comma list of checks and/or SC ids to run, e.g.
                      "focus,reflow" or "2.5.8,1.4.12". Checks: ${Object.keys(CHECKS).join(', ')}
  --no-axe            skip axe-core (custom checks only)
  --probe-actions     allow activating ordinary buttons on http(s) targets (4.1.3 status probe,
                      2.1.2 dialogs opened by plain buttons). Always on for local files/dirs;
                      off by default for remote URLs, where those checks become manual notes
  --help              show this help

Local files and directories are served by a built-in static server on 127.0.0.1.
For a directory, index.html is the start page (else every *.html file is a seed).
Install dependencies first: scripts/setup_page_runner.sh
Debug: WCAG22_DEBUG=1 (or a comma list of checks, e.g. focus,dialogs) logs what checks saw to stderr.
Exit codes: 0 no fail findings, 1 fail findings, 2 usage or runtime error.`;

class UsageError extends Error {}

// ---------------------------------------------------------------- argument parsing
export function parseArgs(argv) {
  const o = { target: null, json: false, level: 'AA', viewport: { width: 1280, height: 800 }, pages: 1,
    screenshots: null, timeout: 30000, maxTabs: 60, observe: 6000, checkTimeout: 120000, rules: null, axe: true, help: false, probeActions: false };
  const need = (i, name) => { if (i + 1 >= argv.length) throw new UsageError(`${name} needs a value`); return argv[i + 1]; };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const [flag, inline] = a.startsWith('--') && a.includes('=') ? [a.slice(0, a.indexOf('=')), a.slice(a.indexOf('=') + 1)] : [a, undefined];
    const val = () => { if (inline !== undefined) return inline; const v = need(i, flag); i++; return v; };
    switch (flag) {
      case '-h': case '--help': o.help = true; break;
      case '--json': o.json = true; break;
      case '--no-axe': o.axe = false; break;
      case '--probe-actions': o.probeActions = true; break;
      case '--level': { const v = val().toUpperCase(); if (!LEVEL_RANK[v]) throw new UsageError('--level must be A, AA or AAA'); o.level = v; break; }
      case '--viewport': { const m = /^(\d+)x(\d+)$/i.exec(val()); if (!m) throw new UsageError('--viewport must be WIDTHxHEIGHT'); o.viewport = { width: +m[1], height: +m[2] }; break; }
      case '--pages': { const n = parseInt(val(), 10); if (!(n >= 1)) throw new UsageError('--pages must be >= 1'); o.pages = n; break; }
      case '--screenshots': o.screenshots = val(); break;
      case '--timeout': { const n = parseInt(val(), 10); if (!(n > 0)) throw new UsageError('--timeout must be > 0'); o.timeout = n; break; }
      case '--max-tabs': { const n = parseInt(val(), 10); if (!(n >= 1)) throw new UsageError('--max-tabs must be >= 1'); o.maxTabs = n; break; }
      case '--observe': { const n = parseInt(val(), 10); if (!(n >= 500)) throw new UsageError('--observe must be >= 500 (ms)'); o.observe = n; break; }
      case '--check-timeout': { const n = parseInt(val(), 10); if (!(n >= 1000)) throw new UsageError('--check-timeout must be >= 1000 (ms)'); o.checkTimeout = n; break; }
      case '--rules': o.rules = val(); break;
      default:
        if (a.startsWith('-')) throw new UsageError(`unknown option ${a}`);
        if (o.target) throw new UsageError('only one target is allowed');
        o.target = a;
    }
  }
  if (!o.help && !o.target) throw new UsageError('missing target (url, file or directory)');
  o.selection = selectChecks(o.rules, o.axe);
  return o;
}

// Resolve --rules into {checks:Set, scs:Set|null}.
export function selectChecks(rules, axeEnabled = true) {
  const checks = new Set(); let scs = null;
  if (!rules) { for (const c of Object.keys(CHECKS)) checks.add(c); }
  else {
    for (const raw of rules.split(',').map((s) => s.trim()).filter(Boolean)) {
      const tok = raw.replace(/^WCAG-/i, '');
      if (CHECKS[tok] !== undefined) { checks.add(tok); continue; }
      if (SC[tok]) {
        scs ??= new Set(); scs.add(tok);
        let custom = false;
        for (const [c, list] of Object.entries(CHECKS)) if (list && list.includes(tok)) { checks.add(c); custom = true; }
        if (!custom || tok === '1.4.3' || tok === '2.2.2') checks.add('axe');
        continue;
      }
      throw new UsageError(`unknown rule "${raw}" (checks: ${Object.keys(CHECKS).join(', ')}; or an SC id like 2.5.8)`);
    }
  }
  if (!axeEnabled) checks.delete('axe');
  return { checks, scs };
}

// ---------------------------------------------------------------- helpers (pure)
export function scFromAxeTag(tag) {
  const m = /^wcag(\d)(\d)(\d{1,2})$/.exec(tag);
  return m ? `${m[1]}.${m[2]}.${m[3]}` : null;
}
export function axeTagsForLevel(level) {
  const tags = ['wcag2a', 'wcag21a', 'wcag22a'];
  if (LEVEL_RANK[level] >= 2) tags.push('wcag2aa', 'wcag21aa', 'wcag22aa');
  if (LEVEL_RANK[level] >= 3) tags.push('wcag2aaa', 'wcag21aaa', 'wcag22aaa');
  return tags;
}
export function understandingUrl(sc) { return SC[sc] ? UNDERSTANDING + SC[sc][1] + '.html' : null; }
export function scCompare(a, b) {
  const pa = String(a).split('.').map(Number), pb = String(b).split('.').map(Number);
  for (let i = 0; i < 3; i++) if ((pa[i] || 0) !== (pb[i] || 0)) return (pa[i] || 0) - (pb[i] || 0);
  return 0;
}
// Target-size spacing test (SC 2.5.8): does a 24px-diameter circle centred on `c` intersect rect `r`?
export function circleIntersectsRect(c, radius, r) {
  const nx = Math.max(r.x, Math.min(c.x, r.x + r.w));
  const ny = Math.max(r.y, Math.min(c.y, r.y + r.h));
  return Math.hypot(c.x - nx, c.y - ny) < radius - 1e-6;
}
export function relLuminance([r, g, b]) {
  const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
export function contrastRatio(a, b) {
  const la = relLuminance(a), lb = relLuminance(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}
// Compare relative order of help-mechanism kinds between pages (SC 3.2.6).
// Two kinds of conflict: the help kinds appear in a different relative order ("order"), or the same kind sits on a
// different side of the main content, e.g. header on one page and footer on another ("position"; needs `zones`).
export function helpOrderConflicts(pages) {
  const out = [];
  for (let i = 0; i < pages.length; i++) for (let j = i + 1; j < pages.length; j++) {
    const a = pages[i].order, b = pages[j].order;
    const common = a.filter((k) => b.includes(k));
    const ba = b.filter((k) => common.includes(k));
    if (common.join('|') !== ba.join('|')) { out.push({ a: pages[i], b: pages[j], orderA: common, orderB: ba, kind: 'order' }); continue; }
    const za = pages[i].zones || {}, zb = pages[j].zones || {};
    const moved = common.filter((k) => za[k] && zb[k] && za[k] !== zb[k]);
    if (moved.length) out.push({ a: pages[i], b: pages[j], orderA: common, orderB: ba, kind: 'position', moved, zonesA: Object.fromEntries(moved.map((k) => [k, za[k]])), zonesB: Object.fromEntries(moved.map((k) => [k, zb[k]])) });
  }
  return out;
}

// Baseline comparison for 3.2.6: each page is compared once with the first page that has help
// mechanisms, so one odd page yields one finding (not one per pair).
export function helpOrderFindings(pages) {
  if (pages.length < 2) return [];
  const base = pages[0]; const out = [];
  for (const p of pages.slice(1)) { const c = helpOrderConflicts([base, p]); if (c.length) out.push(c[0]); }
  return out;
}
// Parse a computed CSS colour ("rgb()", "rgba()", "color(srgb ...)") into [r,g,b,a] (0-255, alpha 0-1).
export function parseCssColor(s) {
  if (!s) return null;
  let m = /^rgba?\(([^)]+)\)/i.exec(s.trim());
  if (m) { const p = m[1].split(/[\s,/]+/).filter(Boolean).map((v) => (v.endsWith('%') ? parseFloat(v) * 2.55 : parseFloat(v))); if (p.length < 3 || p.some(Number.isNaN)) return null; return [p[0], p[1], p[2], p.length > 3 ? (String(m[1]).includes('%') && p[3] > 1 ? p[3] / 255 : p[3]) : 1]; }
  m = /^color\(srgb\s+([^)]+)\)/i.exec(s.trim());
  if (m) { const p = m[1].split(/[\s/]+/).filter(Boolean).map(parseFloat); if (p.length < 3) return null; return [p[0] * 255, p[1] * 255, p[2] * 255, p.length > 3 ? p[3] : 1]; }
  if (/^transparent$/i.test(s.trim())) return [0, 0, 0, 0];
  return null;
}
export function compositeOver(top, bottom) {
  const a = top[3] === undefined ? 1 : top[3];
  return [top[0] * a + bottom[0] * (1 - a), top[1] * a + bottom[1] * (1 - a), top[2] * a + bottom[2] * (1 - a), 1];
}
// 1.4.11 verdict for a form control's boundary. Ratios are against the adjacent (outer) background.
//   pass  - border, box-shadow or the control's own background reaches 3:1
//   fail  - nothing distinguishes the control: weak border (or none) and the same background as its surroundings
//   warn  - the control has a visibly distinct background (boundary may not be needed to identify it) but < 3:1
export function controlBoundaryVerdict({ borderRatio = null, shadowRatio = null, bgRatio = 1 }) {
  const best = Math.max(borderRatio || 0, shadowRatio || 0, bgRatio || 0);
  if (best >= 3) return 'pass';
  if (bgRatio >= 1.1) return 'warn';
  return 'fail';
}
// 1.4.11 verdict for a focus indicator: ring = {color:[r,g,b,a], outer, own, offset, otherChange}.
export function focusIndicatorVerdict({ color, outer, own, offset = 0, otherChange = false }) {
  if (!color || !outer) return null;
  const c = compositeOver(color, outer);
  const vsOuter = contrastRatio(c, outer);
  const vsOwn = own && offset <= 0 ? contrastRatio(compositeOver(color, own), own) : 0;
  const ratio = Math.max(vsOuter, vsOwn);
  if (ratio >= 3) return { verdict: 'pass', ratio };
  return { verdict: otherChange ? 'warn' : 'fail', ratio, vsOuter, vsOwn: vsOwn || null };
}

// ---------------------------------------------------------------- in-page library
// Serialized into the page with page.evaluate(); must not reference module scope.
function pageLib() {
  if (window.__w22) return;
  const esc = (s) => (window.CSS && CSS.escape ? CSS.escape(s) : String(s).replace(/[^\w-]/g, '\\$&'));
  const csCache = new Map();
  const W = {
    cs(el) { let c = csCache.get(el); if (!c) { c = getComputedStyle(el); csCache.set(el, c); } return c; },
    clearCache() { csCache.clear(); },
    sel(el) {
      if (!el || el.nodeType !== 1) return '';
      const parts = [];
      let node = el;
      while (node && node.nodeType === 1) {
        const root = node.getRootNode();
        if (node.id) {
          const s = '#' + esc(node.id);
          try { if (root.querySelectorAll(s).length === 1) { parts.unshift(s); break; } } catch (e) { /* ignore */ }
        }
        let part = node.localName;
        const parent = node.parentElement;
        if (parent) {
          const same = Array.from(parent.children).filter((c) => c.localName === node.localName);
          if (same.length > 1) part += `:nth-of-type(${same.indexOf(node) + 1})`;
        }
        parts.unshift(part);
        if (!parent && root instanceof ShadowRoot) { parts.unshift(W.sel(root.host) + ' >>>'); break; }
        node = parent;
      }
      return parts.join(' > ').replace('>>> >', '>>>');
    },
    snippet(el) {
      if (!el || !el.outerHTML) return null;
      let h = el.outerHTML.replace(/\s+/g, ' ');
      if (h.length > 240) { const open = h.slice(0, h.indexOf('>') + 1); h = (open.length < 237 ? open : h.slice(0, 237)) + '...'; }
      return h;
    },
    visible(el) {
      if (!el.isConnected) return false;
      if (el.checkVisibility && !el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) return false;
      const r = el.getBoundingClientRect();
      return r.width > 1 && r.height > 1;
    },
    box(el) { const r = el.getBoundingClientRect(); return { x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height }; },
    vbox(el) { const r = el.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; },
    raf2() { return new Promise((res) => requestAnimationFrame(() => requestAnimationFrame(res))); },
    freezeMotion() {
      if (document.getElementById('__w22-freeze')) return;
      const s = document.createElement('style'); s.id = '__w22-freeze';
      s.textContent = '*,*::before,*::after{transition:none!important;animation:none!important;scroll-behavior:auto!important;caret-color:transparent!important}';
      (document.head || document.documentElement).appendChild(s);
    },
    fixedAncestor(el, stopAt) {
      for (let n = el; n && n !== stopAt && n.nodeType === 1; n = n.parentElement || (n.getRootNode() instanceof ShadowRoot ? n.getRootNode().host : null)) {
        const p = W.cs(n).position; if (p === 'fixed' || p === 'sticky') return n;
      }
      return null;
    },

    // ---- 2.5.8 target size
    uaDefaults: new Map(),
    uaDefaultSize(el) {
      const key = el.localName + ':' + (el.type || '');
      if (W.uaDefaults.has(key)) return W.uaDefaults.get(key);
      let size = null;
      try {
        const f = document.createElement('iframe');
        f.style.cssText = 'position:absolute;left:-9999px;top:0;width:300px;height:100px;border:0';
        document.documentElement.appendChild(f);
        const d = f.contentDocument; d.open(); d.write('<!doctype html><body></body>'); d.close();
        const c = d.createElement(el.localName); if (el.type) c.setAttribute('type', el.type);
        d.body.appendChild(c); const r = c.getBoundingClientRect(); size = { w: r.width, h: r.height };
        f.remove();
      } catch (e) { size = null; }
      W.uaDefaults.set(key, size);
      return size;
    },
    targetSize() {
      const SEL = 'a[href],area[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=link],[role=checkbox],[role=radio],[role=switch],[role=tab],[role=menuitem],[role=menuitemcheckbox],[role=menuitemradio],[role=option],[role=slider],[role=spinbutton],[role=combobox],[role=treeitem],[onclick],[tabindex]:not([tabindex="-1"]),[contenteditable=""],[contenteditable=true]';
      const els = Array.from(document.querySelectorAll(SEL)).filter((el) => !el.disabled && W.visible(el) && el.localName !== 'area');
      const targets = els.map((el) => {
        let b = W.box(el);
        // A visible label adjacent to / wrapping a native control extends its target.
        if (el.labels && el.labels.length) {
          for (const l of el.labels) {
            if (!W.visible(l)) continue;
            const lb = W.box(l);
            const gapX = Math.max(0, Math.max(lb.x, b.x) - Math.min(lb.x + lb.w, b.x + b.w));
            const gapY = Math.max(0, Math.max(lb.y, b.y) - Math.min(lb.y + lb.h, b.y + b.h));
            if (gapX <= 1 && gapY <= 1) {
              const x = Math.min(b.x, lb.x), y = Math.min(b.y, lb.y);
              b = { x, y, w: Math.max(b.x + b.w, lb.x + lb.w) - x, h: Math.max(b.y + b.h, lb.y + lb.h) - y };
            }
          }
        }
        return { el, b, raw: W.box(el) };
      });
      const results = [];
      const under = targets.filter((t) => t.b.w < 24 - 0.01 || t.b.h < 24 - 0.01);
      const related = (a, b) => a.contains(b) || b.contains(a) || (a.labels && Array.from(a.labels).some((l) => l.contains(b))) || (b.labels && Array.from(b.labels).some((l) => l.contains(a)));
      for (const u of under) {
        const cs = W.cs(u.el);
        let exception = null;
        // Inline exception: target is in a sentence or its size is constrained by the line-height of non-target text.
        if (cs.display === 'inline') {
          let block = u.el.parentElement;
          while (block && W.cs(block).display.startsWith('inline')) block = block.parentElement;
          if (block) {
            const all = (block.textContent || '').replace(/\s+/g, ' ').trim();
            const own = (u.el.textContent || '').replace(/\s+/g, ' ').trim();
            if (all.length > own.length + 1) exception = 'inline';
          }
        }
        // User-agent control exception: native control at its unmodified UA size.
        if (!exception && /^(input|select)$/.test(u.el.localName) && cs.appearance !== 'none' && cs.getPropertyValue('-webkit-appearance') !== 'none') {
          const d = W.uaDefaultSize(u.el);
          if (d && Math.abs(d.w - u.raw.w) < 0.5 && Math.abs(d.h - u.raw.h) < 0.5) exception = 'user-agent';
        }
        const c = { x: u.b.x + u.b.w / 2, y: u.b.y + u.b.h / 2 };
        let conflict = null;
        for (const o of targets) {
          if (o === u || related(o.el, u.el)) continue;
          const oUnder = o.b.w < 24 - 0.01 || o.b.h < 24 - 0.01;
          const nx = Math.max(o.b.x, Math.min(c.x, o.b.x + o.b.w)), ny = Math.max(o.b.y, Math.min(c.y, o.b.y + o.b.h));
          const dRect = Math.hypot(c.x - nx, c.y - ny);
          let hit = null;
          if (dRect < 12 - 1e-6) hit = { kind: 'circle-hits-target', distance: +dRect.toFixed(2) };
          else if (oUnder) {
            const oc = { x: o.b.x + o.b.w / 2, y: o.b.y + o.b.h / 2 };
            const dc = Math.hypot(c.x - oc.x, c.y - oc.y);
            if (dc < 24 - 1e-6) hit = { kind: 'circles-overlap', distance: +dc.toFixed(2) };
          }
          if (hit && (!conflict || hit.distance < conflict.distance)) conflict = { ...hit, selector: W.sel(o.el) };
        }
        if (!conflict) continue; // passes via the spacing exception
        results.push({ selector: W.sel(u.el), snippet: W.snippet(u.el), w: +u.b.w.toFixed(2), h: +u.b.h.toFixed(2), exception, conflict });
      }
      return { count: targets.length, undersized: under.length, results };
    },

    // ---- keyboard walk (2.4.7 / 2.4.11 / 2.1.2 / 2.4.3)
    walk: [],
    domOrder: null,
    indexDom() {
      W.domOrder = new Map(); let i = 0;
      const w = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_ELEMENT);
      while (w.nextNode()) W.domOrder.set(w.currentNode, i++);
      W.walk = [];
    },
    tabbables() {
      return Array.from(document.querySelectorAll('a[href],area[href],button,input,select,textarea,summary,iframe,[tabindex],[contenteditable=""],[contenteditable=true]'))
        .filter((el) => el.tabIndex >= 0 && !el.disabled && !(el.type === 'hidden') && W.visible(el) && !el.closest('[inert]'));
    },
    positiveTabindex() {
      return Array.from(document.querySelectorAll('[tabindex]')).filter((el) => parseInt(el.getAttribute('tabindex'), 10) > 0)
        .map((el) => ({ selector: W.sel(el), snippet: W.snippet(el), tabindex: el.getAttribute('tabindex') }));
    },
    focusStyle(el) {
      const c = getComputedStyle(el);
      return { outline: `${c.outlineStyle} ${c.outlineWidth} ${c.outlineColor}`, boxShadow: c.boxShadow, border: c.borderColor + ' ' + c.borderWidth, background: c.backgroundColor, color: c.color, textDecoration: c.textDecorationLine };
    },
    focusInfo() {
      let el = document.activeElement;
      while (el && el.shadowRoot && el.shadowRoot.activeElement) el = el.shadowRoot.activeElement;
      if (!el || el === document.body || el === document.documentElement) return { key: 'BODY', idx: -1 };
      let inner = '';
      const isFrame = el.localName === 'iframe' || el.localName === 'frame';
      if (isFrame) { try { const d = el.contentDocument; inner = !d ? '?cross-origin' : (d.activeElement && d.activeElement !== d.body ? W.sel(d.activeElement) : ''); } catch (e) { inner = '?cross-origin'; } }
      const selector = W.sel(el);
      const r = el.getBoundingClientRect();
      const { offscreen, samples, covered, coveredBy } = W.coverage(el);
      W.walk.push(el);
      return {
        key: selector + (isFrame ? '|' + inner : ''), idx: W.walk.length - 1, selector, snippet: W.snippet(el), tag: el.localName, isFrame, inner,
        rect: { x: r.left, y: r.top, w: r.width, h: r.height }, page: { x: r.left + scrollX, y: r.top + scrollY },
        offscreen, samples, covered, coveredBy,
        domIndex: W.domOrder && W.domOrder.has(el) ? W.domOrder.get(el) : -1,
        modal: !!el.closest('dialog[open], [aria-modal="true"]'), style: W.focusStyle(el), url: location.href, ring: isFrame ? null : W.ring(el),
        multi: W.multiStop(el),
      };
    },
    // Controls where Tab moves between internal parts while document.activeElement stays the same element:
    // native date/time inputs step through their segments, media controls through their buttons, and custom
    // elements may hold focus inside a closed shadow root. Returns a label for the kind, or null.
    multiStop(el) {
      if (el.localName === 'input' && /^(date|time|datetime-local|month|week)$/.test((el.getAttribute('type') || '').toLowerCase())) return 'input[type=' + el.type + ']';
      if ((el.localName === 'video' || el.localName === 'audio') && el.hasAttribute('controls')) return el.localName + '[controls]';
      if (el.localName.includes('-') && !el.shadowRoot) return 'custom element (closed shadow root?)';
      return null;
    },
    // Sample points of `el` inside the viewport; count those painted over by author fixed/sticky content.
    coverage(el) {
      const r = el.getBoundingClientRect();
      const vw = document.documentElement.clientWidth, vh = document.documentElement.clientHeight;
      const vis = { x0: Math.max(0, r.left), y0: Math.max(0, r.top), x1: Math.min(vw, r.right), y1: Math.min(vh, r.bottom) };
      const offscreen = r.width < 1 || r.height < 1 || vis.x1 - vis.x0 < 1 || vis.y1 - vis.y0 < 1;
      let samples = 0, covered = 0; const coveredBy = new Set();
      if (!offscreen) {
        // Hit-test with pointer-events forced on: pointer-events:none headers still paint over the focused element.
        const pe = document.createElement('style'); pe.id = '__w22-pe'; pe.textContent = '*,*::before,*::after{pointer-events:auto!important}';
        (document.head || document.documentElement).appendChild(pe);
        try {
          const nx = Math.min(5, Math.max(2, Math.round((vis.x1 - vis.x0) / 8))), ny = Math.min(5, Math.max(2, Math.round((vis.y1 - vis.y0) / 8)));
          const root = el.getRootNode();
          const hit = root.elementsFromPoint ? root : document;
          for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) {
            const x = vis.x0 + 1 + ((vis.x1 - vis.x0 - 2) * i) / (nx - 1), y = vis.y0 + 1 + ((vis.y1 - vis.y0 - 2) * j) / (ny - 1);
            const stack = hit.elementsFromPoint(x, y);
            if (!stack.length) continue;
            samples++;
            // Elements painted above the focused element at this point (stack is topmost first).
            for (const top of stack) {
              if (top === el || el.contains(top) || top.contains(el)) break;
              const fixed = W.fixedAncestor(top, null);
              if (fixed && !fixed.contains(el) && W.paints(top, fixed)) { covered++; coveredBy.add(W.sel(fixed)); break; }
            }
          }
        } finally { pe.remove(); }
      }
      return { offscreen, samples, covered, coveredBy: Array.from(coveredBy) };
    },
    // 2.4.11 mid-scroll probe: does the page have painting fixed/sticky content at all?
    hasFixedContent() {
      if (!document.body) return false;
      for (const n of document.body.querySelectorAll('*')) {
        const p = W.cs(n).position;
        if ((p === 'fixed' || p === 'sticky') && W.visible(n)) return true;
      }
      return false;
    },
    // Scroll so walk element i sits flush with the top (edge 'top') or bottom edge of the viewport, focus
    // walk element `prevIdx` without scrolling; returns the pre-Tab coverage of element i at that scroll.
    obscureSetup(i, prevIdx, edge) {
      const el = W.walk[i], prev = W.walk[prevIdx];
      if (!el || !el.isConnected || !prev || !prev.isConnected || W.fixedAncestor(el, null)) return null;
      W.clearCache();
      const r0 = el.getBoundingClientRect();
      const vh = document.documentElement.clientHeight;
      if (r0.height < 1 || r0.height > vh / 2) return null;
      const want = edge === 'top' ? 1 : vh - 1 - r0.height;
      window.scrollTo(scrollX, scrollY + r0.top - want);
      const r = el.getBoundingClientRect();
      if (Math.abs(r.top - want) > 2) return null; // the page cannot scroll that far
      const cov = W.coverage(el);
      if (!cov.samples || cov.covered < cov.samples) return null; // nothing hides it at this position
      const sy = scrollY;
      prev.focus({ preventScroll: true });
      if (scrollY !== sy) window.scrollTo(scrollX, sy);
      return { scrollY: sy, top: +r.top.toFixed(1), coveredBy: cov.coveredBy };
    },
    walkIndexOf(i) { return W.walk.indexOf(document.activeElement) === i; },
    walkRect(i) { const el = W.walk[i]; if (!el || !el.isConnected) return null; const r = el.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height, style: W.focusStyle(el) }; },

    // ---- text integrity (1.4.12 / 1.4.4)
    textBase: null,
    textLeaves() {
      const out = []; const seen = new Set();
      if (!document.body) return out;
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (w.nextNode()) {
        const t = w.currentNode; if (!t.nodeValue.trim()) continue;
        const el = t.parentElement; if (!el || seen.has(el)) continue;
        if (/^(script|style|noscript|template|title|option|textarea)$/.test(el.localName) || el.closest('svg, math')) continue;
        seen.add(el); out.push(el); if (out.length >= 3000) break;
      }
      return out;
    },
    lineRects(el) {
      const rects = [];
      for (const n of el.childNodes) {
        if (n.nodeType !== 3 || !n.nodeValue.trim()) continue;
        const rg = document.createRange(); rg.selectNodeContents(n);
        for (const r of rg.getClientRects()) if (r.width > 0.5 && r.height > 0.5) rects.push({ x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height });
        if (rects.length > 60) break;
      }
      return rects;
    },
    clipOf(el, rects) {
      if (!rects.length) return null;
      const u = { x0: Math.min(...rects.map((r) => r.x)), y0: Math.min(...rects.map((r) => r.y)), x1: Math.max(...rects.map((r) => r.x + r.w)), y1: Math.max(...rects.map((r) => r.y + r.h)) };
      const hid = (v) => v === 'hidden' || v === 'clip';
      for (let a = el; a && a !== document.body && a !== document.documentElement; a = a.parentElement) {
        const c = W.cs(a);
        if (!hid(c.overflowX) && !hid(c.overflowY) && c.textOverflow !== 'ellipsis') continue;
        const ar = a.getBoundingClientRect();
        if (ar.width <= 2 || ar.height <= 2) return { hidden: true };
        const left = ar.left + scrollX + a.clientLeft, top = ar.top + scrollY + a.clientTop;
        const over = { bottom: u.y1 - (top + a.clientHeight), right: u.x1 - (left + a.clientWidth), left: left - u.x0, top: top - u.y0 };
        if (hid(c.overflowY) && (over.bottom > 1 || over.top > 1)) return { by: W.sel(a), axis: 'y', px: +Math.max(over.bottom, over.top).toFixed(1), box: { w: +ar.width.toFixed(1), h: +ar.height.toFixed(1) } };
        if (hid(c.overflowX) && (over.right > 1 || over.left > 1)) return { by: W.sel(a), axis: 'x', px: +Math.max(over.right, over.left).toFixed(1), box: { w: +ar.width.toFixed(1), h: +ar.height.toFixed(1) } };
      }
      return null;
    },
    overlapPairs(entries) {
      const pairs = [];
      const flat = [];
      entries.forEach((e, i) => e.rects.forEach((r) => flat.push({ i, r })));
      flat.sort((a, b) => a.r.y - b.r.y);
      for (let p = 0; p < flat.length; p++) {
        const A = flat[p];
        for (let q = p + 1; q < flat.length && flat[q].r.y < A.r.y + A.r.h; q++) {
          const B = flat[q]; if (A.i === B.i) continue;
          const ix = Math.min(A.r.x + A.r.w, B.r.x + B.r.w) - Math.max(A.r.x, B.r.x);
          const iy = Math.min(A.r.y + A.r.h, B.r.y + B.r.h) - Math.max(A.r.y, B.r.y);
          if (ix > 2 && iy > Math.max(2, 0.35 * Math.min(A.r.h, B.r.h))) pairs.push(A.i < B.i ? A.i + ':' + B.i : B.i + ':' + A.i);
        }
      }
      return new Set(pairs);
    },
    textSnapshot() {
      W.clearCache();
      const leaves = W.textLeaves().filter((el) => W.visible(el));
      const entries = leaves.map((el) => { const rects = W.lineRects(el); return { el, rects, clip: W.clipOf(el, rects) }; });
      W.textBase = { entries, pairs: W.overlapPairs(entries) };
      return entries.length;
    },
    textCompare() {
      W.clearCache();
      const base = W.textBase; if (!base) return null;
      const now = base.entries.map((e) => { const vis = W.visible(e.el); const rects = vis ? W.lineRects(e.el) : []; return { el: e.el, rects, clip: vis ? W.clipOf(e.el, rects) : null }; });
      const clipped = [];
      now.forEach((e, i) => {
        const b = base.entries[i];
        if (e.clip && !e.clip.hidden && !b.clip) clipped.push({ selector: W.sel(e.el), snippet: W.snippet(e.el), text: (e.el.textContent || '').trim().slice(0, 80), clip: e.clip });
      });
      const overlaps = [];
      const related = (a, b) => a.contains(b) || b.contains(a);
      for (const key of W.overlapPairs(now)) {
        if (base.pairs.has(key)) continue;
        const [i, j] = key.split(':').map(Number);
        if (related(now[i].el, now[j].el) || W.fixedAncestor(now[i].el, null) || W.fixedAncestor(now[j].el, null)) continue;
        overlaps.push({ a: W.sel(now[i].el), b: W.sel(now[j].el), snippet: W.snippet(now[i].el), textA: (now[i].el.textContent || '').trim().slice(0, 60), textB: (now[j].el.textContent || '').trim().slice(0, 60) });
        if (overlaps.length >= 50) break;
      }
      return { leaves: now.length, clipped, overlaps };
    },
    applyTextSpacing() {
      const s = document.createElement('style'); s.id = '__w22-spacing';
      s.textContent = '*{line-height:1.5!important;letter-spacing:0.12em!important;word-spacing:0.16em!important}p{margin-bottom:2em!important}';
      (document.head || document.documentElement).appendChild(s);
    },
    removeTextSpacing() { const s = document.getElementById('__w22-spacing'); if (s) s.remove(); },
    applyTextResize(factor) {
      const els = Array.from(document.querySelectorAll('body, body *'));
      const cur = els.map((el) => { const c = getComputedStyle(el); return [parseFloat(c.fontSize), c.lineHeight]; });
      els.forEach((el, i) => {
        const [fs, lh] = cur[i];
        if (fs > 0) el.style.setProperty('font-size', fs * factor + 'px', 'important');
        if (lh && lh !== 'normal' && parseFloat(lh) > 0) el.style.setProperty('line-height', parseFloat(lh) * factor + 'px', 'important');
      });
    },

    // ---- 1.4.10 reflow
    reflow() {
      const de = document.documentElement;
      const cw = de.clientWidth;
      const sw = Math.max(de.scrollWidth, document.body ? document.body.scrollWidth : 0);
      const scrolls = sw > cw + 1;
      const clipsX = (el) => { const v = W.cs(el).overflowX; return v !== 'visible'; };
      const EXEMPT = 'table, pre, code, canvas, video, audio, iframe, svg, img, picture, math, [role="application"], [role="img"], [role="grid"], [role="treegrid"], figure, object, embed, map';
      const offenders = new Set(); const out = [];
      const all = document.body ? document.body.querySelectorAll('*') : [];
      for (const el of all) {
        if (!W.visible(el)) continue;
        const r = el.getBoundingClientRect();
        const right = r.right + scrollX;
        if (right <= cw + 1) continue;
        // contained by a horizontally scrolling/clipping ancestor below <body>: does not scroll the page
        let contained = false; let parentOff = false;
        for (let a = el.parentElement; a && a !== document.body && a !== de; a = a.parentElement) {
          if (offenders.has(a)) { parentOff = true; break; }
          if (clipsX(a)) { const ar = a.getBoundingClientRect(); if (ar.right + scrollX <= cw + 1) { contained = true; break; } }
        }
        if (contained) continue;
        offenders.add(el);
        if (parentOff) continue;
        const straddles = r.left + scrollX < cw;
        const pos = W.cs(el).position;
        const exempt = el.matches(EXEMPT) ? el.localName : (el.closest(EXEMPT) ? el.closest(EXEMPT).localName : null);
        out.push({ selector: W.sel(el), snippet: W.snippet(el), left: +(r.left + scrollX).toFixed(1), right: +right.toFixed(1), width: +r.width.toFixed(1), straddles, position: pos, exempt });
        if (out.length >= 40) break;
      }
      return { clientWidth: cw, scrollWidth: sw, scrolls, offenders: out };
    },

    // ---- 1.4.3 contrast sampling support
    // Text colour, font and line box of `selector` (scrolled into view). Call hideText() afterwards to sample
    // the background with the glyphs removed; comparing both frames locates the pixels behind the glyphs.
    textInfo(selector) {
      let el = null; try { el = document.querySelector(selector); } catch (e) { el = null; }
      if (!el) return null;
      el.scrollIntoView({ block: 'center', inline: 'center' });
      const c = getComputedStyle(el);
      // SVG text paints with `fill`, not `color`: use a solid fill (times fill-opacity) as the text colour.
      const svgText = el instanceof SVGElement && /^(text|tspan|textPath)$/.test(el.localName);
      const fillM = svgText ? (c.fill || '').match(/^rgba?\(([^)]*)\)$/) : null;
      let m = (fillM ? fillM[1] : c.color).match(/[\d.]+/g) || ['0', '0', '0'];
      if (fillM) { const fo = parseFloat(c.fillOpacity); if (fo >= 0 && fo < 1) m = [m[0], m[1], m[2], String((m[3] === undefined ? 1 : +m[3]) * fo)]; }
      const rects = W.lineRects(el).map((r) => ({ x: r.x - scrollX, y: r.y - scrollY, w: r.w, h: r.h }));
      const r = rects.length ? { x: Math.min(...rects.map((q) => q.x)), y: Math.min(...rects.map((q) => q.y)), x1: Math.max(...rects.map((q) => q.x + q.w)), y1: Math.max(...rects.map((q) => q.y + q.h)) } : null;
      const vr = el.getBoundingClientRect();
      const box = r ? { x: r.x, y: r.y, w: r.x1 - r.x, h: r.y1 - r.y } : { x: vr.left, y: vr.top, w: vr.width, h: vr.height };
      return { fg: m.slice(0, 4).map(Number), fontSize: parseFloat(c.fontSize), fontWeight: parseInt(c.fontWeight, 10) || 400, box, svg: svgText };
    },
    hideText(selector) {
      let el = null; try { el = document.querySelector(selector); } catch (e) { el = null; }
      if (!el) return false;
      el.setAttribute('data-w22-hidetext', '');
      if (!document.getElementById('__w22-hidetext')) {
        const s = document.createElement('style'); s.id = '__w22-hidetext';
        s.textContent = '[data-w22-hidetext],[data-w22-hidetext] *{color:transparent!important;-webkit-text-fill-color:transparent!important;text-shadow:none!important;text-decoration-color:transparent!important}'
          + ':is(text,tspan,textPath)[data-w22-hidetext],[data-w22-hidetext] :is(text,tspan,textPath){fill:transparent!important;stroke:transparent!important}';
        (document.head || document.documentElement).appendChild(s);
      }
      return true;
    },
    unhideText() { document.querySelectorAll('[data-w22-hidetext]').forEach((e) => e.removeAttribute('data-w22-hidetext')); },

    // ---- 3.2.6 help mechanisms
    helpMechanisms() {
      const found = [];
      const REGION = 'header, footer, nav, aside, [role=banner], [role=contentinfo], [role=navigation], [role=complementary]';
      const inRegion = (el) => !!el.closest(REGION) || !!W.fixedAncestor(el, null);
      const cands = Array.from(document.querySelectorAll('a[href], button, [role=button], [role=link], iframe, [id*="chat" i], [class*="chat" i], [aria-label*="chat" i]'));
      for (const el of cands) {
        if (!W.visible(el) && el.localName !== 'iframe') continue;
        const text = ((el.getAttribute('aria-label') || '') + ' ' + (el.textContent || '') + ' ' + (el.getAttribute('title') || '')).replace(/\s+/g, ' ').trim().toLowerCase();
        const href = (el.getAttribute('href') || el.getAttribute('src') || '').toLowerCase();
        let kind = null;
        if (/^tel:|^sms:/.test(href)) kind = 'phone';
        else if (/^mailto:/.test(href)) kind = 'email';
        else if (/\b(contact( us)?|call us|email us|phone us|get in touch)\b/.test(text) || /\/contact/.test(href)) kind = 'contact';
        else if (/\b(live chat|chat( with us| now)?|chatbot|messenger)\b/.test(text) || /(intercom|drift|zendesk|livechat|tawk|crisp|hs-scripts|chat)/.test(href) || /chat/i.test((el.id || '') + ' ' + (typeof el.className === 'string' ? el.className : ''))) kind = 'chat';
        else if (/\b(help( cent(er|re))?|faqs?|support|knowledge ?base|how[- ]to)\b/.test(text) || /\/(help|faq|faqs|support)(\/|$|\.|\?|#)/.test(href)) kind = 'self-help';
        if (!kind) continue;
        found.push({ el, kind, selector: W.sel(el), text: text.slice(0, 60), region: inRegion(el) });
      }
      // Phone numbers and e-mail addresses written as plain text in header/footer regions.
      for (const reg of document.querySelectorAll(REGION)) {
        const w = document.createTreeWalker(reg, NodeFilter.SHOW_TEXT);
        while (w.nextNode()) {
          const t = w.currentNode; const p = t.parentElement;
          if (!p || p.closest('a[href], button, script, style') || !W.visible(p)) continue;
          const v = t.nodeValue;
          let kind = null;
          if (/(\+?\d[\d\s().-]{7,}\d)/.test(v) && (/\b(phone|tel|call|ring)\b/i.test(v + ' ' + (p.textContent || '')) || (v.match(/\d/g) || []).length >= 9)) kind = 'phone';
          else if (/[\w.+-]+@[\w-]+\.[\w.-]+/.test(v)) kind = 'email';
          // `node` (the text node) positions it: "Email us or call 555..." lists email before phone.
          if (kind && !found.some((f) => f.el === p && f.kind === kind)) found.push({ el: p, node: t, kind, selector: W.sel(p), text: v.replace(/\s+/g, ' ').trim().slice(0, 60), region: true });
        }
      }
      const regional = found.filter((f) => f.region);
      const pos = (f) => f.node || f.el;
      const use = (regional.length ? regional : found).sort((a, b) => (pos(a) === pos(b) ? 0 : pos(a).compareDocumentPosition(pos(b)) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1));
      const order = [];
      for (const f of use) if (!order.includes(f.kind)) order.push(f.kind);
      // Position relative to the main content (3.2.6 is about order relative to other page content): a help link
      // in the header on one page and in the footer on another keeps its order among help items but not on the page.
      const main = document.querySelector('main, [role=main]');
      const zoneOf = (f) => { const n = pos(f); if (!main) return null; if (main.contains(n)) return 'main'; return main.compareDocumentPosition(n) & Node.DOCUMENT_POSITION_PRECEDING ? 'before-main' : 'after-main'; };
      const zones = {};
      for (const f of use) { f.zone = zoneOf(f); if (!(f.kind in zones)) zones[f.kind] = f.zone; }
      return { order, zones, scope: regional.length ? 'header/footer/nav' : 'page', items: use.slice(0, 20).map(({ el, node, ...rest }) => rest) };
    },

    // ---- 3.3.7 / 3.3.8 / 3.3.9 authentication and redundant entry
    auth() {
      const out = { password: [], otp: [], captcha: [], redundant: [] };
      const pasteBlocked = (el) => {
        try {
          const dt = new DataTransfer(); dt.setData('text/plain', 'W22-paste-probe');
          const ev = new ClipboardEvent('paste', { bubbles: true, cancelable: true, composed: true, clipboardData: dt });
          return !el.dispatchEvent(ev);
        } catch (e) { return null; }
      };
      for (const el of document.querySelectorAll('input[type=password]')) {
        const form = el.form;
        const ac = (el.getAttribute('autocomplete') || '').trim().toLowerCase();
        const formAc = form ? (form.getAttribute('autocomplete') || '').trim().toLowerCase() : '';
        out.password.push({ selector: W.sel(el), snippet: W.snippet(el), autocomplete: ac, formAutocomplete: formAc, autocompleteOff: ac === 'off' || (!ac && formAc === 'off'), pasteBlocked: pasteBlocked(el) });
      }
      for (const el of document.querySelectorAll('input:not([type=hidden]):not([type=password])')) {
        const ac = (el.getAttribute('autocomplete') || '').toLowerCase();
        const id = ((el.name || '') + ' ' + (el.id || '')).toLowerCase();
        if (ac.includes('one-time-code') || /\b(otp|one.?time|verification.?code|2fa|mfa|totp)\b/.test(id.replace(/[_-]/g, ' '))) {
          out.otp.push({ selector: W.sel(el), snippet: W.snippet(el), autocomplete: ac, pasteBlocked: pasteBlocked(el) });
        }
      }
      const capSel = 'iframe[src*="recaptcha" i], iframe[src*="hcaptcha" i], iframe[src*="challenges.cloudflare" i], iframe[src*="captcha" i], iframe[title*="captcha" i], .g-recaptcha, .h-captcha, .cf-turnstile, [id*="captcha" i], [class*="captcha" i], img[alt*="captcha" i], img[src*="captcha" i], input[name*="captcha" i]';
      const caps = Array.from(document.querySelectorAll(capSel)).filter((el) => !Array.from(document.querySelectorAll(capSel)).some((o) => o !== el && o.contains(el)));
      for (const el of caps.slice(0, 5)) out.captcha.push({ selector: W.sel(el), snippet: W.snippet(el) });
      const RE = /(confirm|repeat|retype|re-?enter|verify|again|2$)/;
      for (const form of document.querySelectorAll('form')) {
        const seen = new Map();
        for (const el of form.querySelectorAll('input:not([type=hidden]):not([type=password]), select, textarea')) {
          const ac = (el.getAttribute('autocomplete') || '').toLowerCase().split(/\s+/).filter((t) => t && !/^(section-|shipping|billing|on|off|home|work|mobile|fax|pager)/.test(t)).pop();
          const nm = ((el.name || '') + ' ' + (el.id || '')).toLowerCase();
          if (ac) { if (seen.has(ac)) out.redundant.push({ selector: W.sel(el), snippet: W.snippet(el), reason: `autocomplete "${ac}" repeated in the same form (first: ${seen.get(ac)})` }); else seen.set(ac, W.sel(el)); }
          else if (/e-?mail|address|phone/.test(nm) && RE.test(nm.replace(/[_\s-]+/g, ''))) out.redundant.push({ selector: W.sel(el), snippet: W.snippet(el), reason: `field "${el.name || el.id}" looks like a re-entry of information` });
        }
      }
      return out;
    },
    // ---- colour helpers (in page)
    color(s) {
      if (!s) return null;
      let m = /^rgba?\(([^)]+)\)/i.exec(s.trim());
      if (m) { const p = m[1].split(/[\s,/]+/).filter(Boolean).map(parseFloat); return p.length >= 3 ? [p[0], p[1], p[2], p.length > 3 ? p[3] : 1] : null; }
      m = /^color\(srgb\s+([^)]+)\)/i.exec(s.trim());
      if (m) { const p = m[1].split(/[\s/]+/).filter(Boolean).map(parseFloat); return p.length >= 3 ? [p[0] * 255, p[1] * 255, p[2] * 255, p.length > 3 ? p[3] : 1] : null; }
      if (s.trim() === 'transparent') return [0, 0, 0, 0];
      return null;
    },
    over(t, b) { const a = t[3]; return [t[0] * a + b[0] * (1 - a), t[1] * a + b[1] * (1 - a), t[2] * a + b[2] * (1 - a), 1]; },
    ratio(a, b) {
      const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
      const L = (c) => 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
      const x = L(a), y = L(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
    },
    // Effective background colour painted behind `el` (null when an image/gradient or unparsable colour is involved).
    effBg(el) {
      const layers = [];
      for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
        const c = W.cs(n);
        if (c.backgroundImage && c.backgroundImage !== 'none') return null;
        const col = W.color(c.backgroundColor);
        if (!col) return null;
        if (col[3] > 0) { layers.push(col); if (col[3] >= 1) break; }
      }
      let base = [255, 255, 255, 1];
      for (let i = layers.length - 1; i >= 0; i--) base = W.over(layers[i], base);
      return base;
    },
    shadowColor(bs) { if (!bs || bs === 'none') return null; const m = /(rgba?\([^)]*\)|color\([^)]*\))/.exec(bs); return m ? W.color(m[1]) : null; },
    ring(el) {
      const c = getComputedStyle(el);
      return { outlineStyle: c.outlineStyle, outlineWidth: parseFloat(c.outlineWidth) || 0, outlineColor: c.outlineColor, outlineOffset: parseFloat(c.outlineOffset) || 0,
        boxShadow: c.boxShadow, borderColor: c.borderColor, borderWidth: c.borderWidth, background: c.backgroundColor,
        outer: W.effBg(el.parentElement || el), own: W.effBg(el) };
    },
    walkRing(i) { const el = W.walk[i]; return el && el.isConnected ? W.ring(el) : null; },

    // ---- 1.4.11 form-control boundaries
    nonTextContrast() {
      const SEL = 'input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]):not([type=image]):not([type=range]):not([type=color]):not([type=file]), select, textarea, [role=textbox], [role=searchbox], [role=combobox], [role=spinbutton], [role=checkbox], [role=radio], [role=switch]';
      const out = []; let unknown = 0, checked = 0;
      for (const el of document.querySelectorAll(SEL)) {
        if (!W.visible(el) || el.disabled || el.closest('[inert], fieldset[disabled], [aria-disabled="true"]')) continue;
        const cs = W.cs(el);
        const type = (el.getAttribute('type') || '').toLowerCase();
        const role = (el.getAttribute('role') || '').toLowerCase();
        const toggle = /^(checkbox|radio)$/.test(type) || /^(checkbox|radio|switch)$/.test(role);
        const native = /^(input|select|textarea)$/.test(el.localName);
        const noAppearance = cs.appearance === 'none' || cs.getPropertyValue('-webkit-appearance') === 'none';
        if (native && toggle && !noAppearance) continue; // rendered by the user agent: 1.4.11 exception
        const outer = W.effBg(el.parentElement);
        if (!outer) { unknown++; continue; }
        checked++;
        const parts = [cs];
        for (const pe of ['::before', '::after']) { const p = getComputedStyle(el, pe); if (p.content && p.content !== 'none' && p.display !== 'none') parts.push(p); }
        let borderRatio = null, shadowRatio = null, bgRatio = 1; const colours = {};
        parts.forEach((p, i) => {
          for (const side of ['top', 'right', 'bottom', 'left']) {
            const w = parseFloat(p.getPropertyValue(`border-${side}-width`)) || 0; const st = p.getPropertyValue(`border-${side}-style`);
            const col = W.color(p.getPropertyValue(`border-${side}-color`));
            if (w < 0.5 || st === 'none' || st === 'hidden' || !col || col[3] === 0) continue;
            const r = W.ratio(W.over(col, outer), outer);
            if (borderRatio === null || r > borderRatio) { borderRatio = r; colours.border = p.getPropertyValue(`border-${side}-color`); }
          }
          const sc = W.shadowColor(p.boxShadow);
          if (sc && sc[3] > 0) { const r = W.ratio(W.over(sc, outer), outer); if (shadowRatio === null || r > shadowRatio) { shadowRatio = r; colours.shadow = p.boxShadow; } }
          const bg = W.color(p.backgroundColor);
          if (bg && bg[3] > 0 && (!p.backgroundImage || p.backgroundImage === 'none')) { const r = W.ratio(W.over(bg, outer), outer); if (r > bgRatio) { bgRatio = r; colours.background = p.backgroundColor; } }
          else if (p.backgroundImage && p.backgroundImage !== 'none' && i === 0) bgRatio = Math.max(bgRatio, 1.1);
        });
        const best = Math.max(borderRatio || 0, shadowRatio || 0, bgRatio);
        if (best >= 3) continue;
        out.push({ selector: W.sel(el), snippet: W.snippet(el), kind: toggle ? (role || type) : (el.localName === 'select' || role === 'combobox' ? 'select' : 'text input'),
          borderRatio: borderRatio && +borderRatio.toFixed(2), shadowRatio: shadowRatio && +shadowRatio.toFixed(2), bgRatio: +bgRatio.toFixed(2), colours,
          adjacent: `rgb(${outer.slice(0, 3).map(Math.round).join(', ')})` });
        if (out.length >= 30) break;
      }
      return { checked, unknown, results: out };
    },

    // ---- 1.4.3 logotype context
    logoContext(selector) {
      let el = null; try { el = document.querySelector(selector); } catch (e) { el = null; }
      if (!el) return null;
      let n = el;
      for (let d = 0; n && d < 5 && n.nodeType === 1 && !/^(body|html|main)$/.test(n.localName); d++, n = n.parentElement) {
        const toks = [n.id || '', typeof n.className === 'string' ? n.className : '', n.getAttribute('alt') || ''].join(' ');
        if (/logo|wordmark|logotype/i.test(toks) || /(^|[\s_-])(navbar-)?brand([\s_-]|$)/i.test(toks)) return `<${n.localName}> ${toks.trim()}`.slice(0, 80);
        if ((n.getAttribute('role') || '') === 'img' && /logo|wordmark/i.test((n.getAttribute('aria-label') || '') + ' ' + (n.getAttribute('title') || ''))) return 'role=img labelled as a logo';
        if (n.localName === 'svg' && /logo/i.test((n.getAttribute('aria-label') || '') + ' ' + ((n.querySelector('title') || {}).textContent || ''))) return 'svg logo';
      }
      const a = el.closest('a[href]'), hdr = el.closest('header, [role=banner]');
      if (a && hdr) {
        const href = a.getAttribute('href').trim();
        if (a.rel === 'home' || /^(\.?\/)?(index\.html?)?$|^#(top)?$/.test(href) || new URL(a.href, location.href).pathname === '/') return 'brand (home) link text in <header>';
      }
      return null;
    },

    // ---- 2.4.11 scroll settle + author-painted coverage
    async settleScroll() {
      let el = document.activeElement; while (el && el.shadowRoot && el.shadowRoot.activeElement) el = el.shadowRoot.activeElement;
      let last = '', same = 0;
      for (let i = 0; i < 90 && same < 3; i++) {
        await new Promise((r) => requestAnimationFrame(r));
        const r = el && el.getBoundingClientRect ? el.getBoundingClientRect() : { top: 0, left: 0 };
        const k = [scrollX, scrollY, Math.round(r.top), Math.round(r.left)].join(',');
        same = k === last ? same + 1 : 0; last = k;
      }
      return true;
    },
    paints(top, fixed) {
      for (let n = top; n && n.nodeType === 1; n = n.parentElement) {
        const c = W.cs(n);
        if (parseFloat(c.opacity) === 0 || c.visibility === 'hidden') return false;
        if (/^(img|svg|video|canvas|iframe|input|button|select|textarea|picture|object|embed)$/.test(n.localName)) return true;
        const bg = W.color(c.backgroundColor);
        if ((bg && bg[3] > 0.05) || (c.backgroundImage && c.backgroundImage !== 'none')) return true;
        if (n === fixed) break;
      }
      // transparent layer: covered only where it draws its own text
      return Array.from(top.childNodes).some((t) => t.nodeType === 3 && t.nodeValue.trim());
    },

    // ---- 2.1.2 dialog triggers and probing
    dialogTrigger(el) {
      const hp = (el.getAttribute('aria-haspopup') || '').toLowerCase();
      if (hp === 'dialog') return 'aria-haspopup="dialog"';
      for (const id of (el.getAttribute('aria-controls') || '').split(/\s+/).filter(Boolean)) {
        const t = document.getElementById(id);
        if (t && (t.localName === 'dialog' || /\b(alert)?dialog\b/.test(t.getAttribute('role') || '') || t.getAttribute('aria-modal') === 'true')) return `aria-controls="${id}" (dialog)`;
      }
      for (const a of el.attributes) if (/^data-.*toggle/i.test(a.name) && /modal|dialog|lightbox|popup|overlay/i.test(a.value)) return `${a.name}="${a.value}"`;
      if ((el.getAttribute('command') || '') === 'show-modal') return 'command="show-modal"';
      return null;
    },
    DESTRUCTIVE: /\b(delete|remove|pay|buy|purchase|order|checkout|log ?out|sign ?out|unsubscribe|cancel (my )?(account|subscription)|submit|send|post|publish|confirm)\b/i,
    ctlName(e) { return ((e.getAttribute('aria-label') || '') + ' ' + (e.textContent || '') + ' ' + (e.getAttribute('title') || '') + ' ' + (e.value || '')).replace(/\s+/g, ' ').trim(); },
    // Dialog-like containers present in the DOM but not shown: a page with one of these probably opens it from script.
    hiddenDialogs() {
      return Array.from(document.querySelectorAll('dialog:not([open]), [role=dialog], [role=alertdialog], [aria-modal="true"], [class*="modal" i], [class*="dialog" i], [class*="lightbox" i]'))
        .filter((d) => !/^(html|body)$/.test(d.localName) && !W.visible(d) && d.querySelector('input, select, textarea, button, a[href], [tabindex]'));
    },
    // Explicit dialog triggers (aria-haspopup, aria-controls, data-toggle, command) plus, when `heuristic` and the page
    // holds a hidden dialog, plain buttons wired up by onclick/addEventListener (nothing in the markup says they open it).
    dialogTriggers(heuristic) {
      const tabs = W.tabbables();
      const explicit = tabs.map((el) => ({ el, why: W.dialogTrigger(el) })).filter((t) => t.why).slice(0, 5);
      // Hidden dialogs an explicit trigger already points at (aria-controls, data-*target, href="#id") need no guessing.
      const refs = new Set();
      for (const t of explicit) for (const a of t.el.attributes) if (/^(aria-controls|href|data-[\w-]*target)$/i.test(a.name)) a.value.split(/\s+/).forEach((v) => refs.add(v.replace(/^#/, '')));
      const hidden = W.hiddenDialogs().filter((d) => !refs.has(d.id) && !Array.from(refs).some((id) => { const r = id && document.getElementById(id); return r && (r.contains(d) || d.contains(r)); }));
      const out = explicit.slice(); let skipped = 0;
      if (hidden.length && out.length < 5) {
        const ids = hidden.map((d) => d.id).filter(Boolean);
        const seen = new Set();
        const cands = tabs.filter((el) => !explicit.some((t) => t.el === el)
          && (el.localName === 'button' || (el.getAttribute('role') || '') === 'button' || el.hasAttribute('onclick') || (el.localName === 'a' && /^(#|javascript:)/i.test(el.getAttribute('href') || '')))
          && !(el.localName === 'button' && (el.type === 'submit' || el.type === 'reset') && el.form)
          && !el.closest('dialog, [role=dialog], [role=alertdialog], [aria-modal="true"]') && !el.hasAttribute('aria-expanded')
          && !W.DESTRUCTIVE.test(W.ctlName(el)));
        const score = (el) => {
          const attrs = Array.from(el.attributes).map((a) => a.name + '=' + a.value).join(' ');
          let n = 0;
          if (/modal|dialog|popup|lightbox|overlay|open|show/i.test(attrs + ' ' + W.ctlName(el))) n += 2;
          if (ids.some((id) => attrs.includes(id))) n += 3;
          if (/\bdata-[\w-]+=|onclick=/i.test(attrs)) n += 1;
          return n;
        };
        const ranked = cands.map((el) => ({ el, n: score(el) })).sort((a, b) => b.n - a.n);
        for (const { el } of ranked) {
          if (out.length >= 5) break;
          const k = W.ctlName(el).toLowerCase() + '|' + (typeof el.className === 'string' ? el.className : '');
          if (seen.has(k)) continue; seen.add(k); // same label and class: very likely the same handler
          if (!heuristic) { skipped++; continue; }
          out.push({ el, why: `plain ${el.localName === 'button' ? 'button' : 'control'} probed because the page holds a hidden dialog (${W.sel(hidden[0])})` });
        }
      }
      return { triggers: out.map((t) => ({ selector: W.sel(t.el), snippet: W.snippet(t.el), why: t.why })), hidden: hidden.slice(0, 5).map((d) => W.sel(d)), skipped };
    },
    openDialogs() {
      return Array.from(document.querySelectorAll('dialog[open], [role=dialog], [role=alertdialog], [aria-modal="true"], [data-w22-ctl], [class*="modal" i], [class*="dialog" i], [class*="lightbox" i]'))
        .filter((d) => !/^(html|body)$/.test(d.localName) && W.visible(d));
    },
    focusSel(sel) { let el = null; try { el = document.querySelector(sel); } catch (e) { el = null; } if (!el) return false; el.focus(); return document.activeElement === el; },
    markDialog(triggerSel, before) {
      let trig = null; try { trig = document.querySelector(triggerSel); } catch (e) { trig = null; }
      for (const id of ((trig && trig.getAttribute('aria-controls')) || '').split(/\s+/).filter(Boolean)) { const t = document.getElementById(id); if (t) t.setAttribute('data-w22-ctl', ''); }
      const now = W.openDialogs().filter((d) => !before.includes(W.sel(d)));
      const dlg = now.find((d) => !now.some((o) => o !== d && o.contains(d)));
      if (!dlg) return null;
      document.querySelectorAll('[data-w22-dlg]').forEach((e) => e.removeAttribute('data-w22-dlg'));
      dlg.setAttribute('data-w22-dlg', '');
      const tabs = W.tabbables().filter((e) => dlg.contains(e));
      const name = (e) => ((e.getAttribute('aria-label') || '') + ' ' + (e.textContent || '') + ' ' + (e.getAttribute('title') || '') + ' ' + (e.value || '')).replace(/\s+/g, ' ').trim();
      const closers = tabs.filter((e) => /\b(close|cancel|dismiss|done|ok|okay|got it|no thanks|back|exit)\b|^[×✕✖xX]$/i.test(name(e))).map((e) => ({ selector: W.sel(e), name: name(e).slice(0, 40) }));
      const text = (dlg.textContent || '').replace(/\s+/g, ' ');
      const documented = /\b(press|use)\b[^.]{0,40}\b(to|will)\s+(close|exit|leave|dismiss|return)/i.exec(text);
      return { selector: W.sel(dlg), snippet: W.snippet(dlg), tabbables: tabs.length, closers, documented: documented ? documented[0] : null };
    },
    dialogState() {
      const dlg = document.querySelector('[data-w22-dlg]');
      let el = document.activeElement; while (el && el.shadowRoot && el.shadowRoot.activeElement) el = el.shadowRoot.activeElement;
      const open = !!dlg && dlg.isConnected && W.visible(dlg) && !(dlg.localName === 'dialog' && !dlg.open);
      return { open, inside: open && !!el && dlg.contains(el), active: el ? W.sel(el) : null };
    },

    // ---- 2.2.2 auto-updating content
    // Named candidates (carousel/slider/marquee/ticker classes, aria-roledescription, sections of slides) are snapshotted
    // every 250 ms (catches transforms and transitions); every other mutation on the page is grouped by its region
    // (section/aside/figure/role=region/aria-live..., else the changed element's parent), which catches rotators that
    // swap hidden/class/src/innerHTML on a timer without carousel-like names. Infinite CSS animations are read at stop.
    auto: null,
    AUTO_NAMED: '[aria-roledescription*="carousel" i], [class*="carousel" i], [class*="slider" i], [class*="slideshow" i], [class*="marquee" i], [class*="ticker" i], [class*="rotator" i], marquee, [role=marquee]',
    AUTO_REGION: 'section, aside, article, figure, [role=region], [role=marquee], [role=timer], [role=log], [aria-roledescription], [aria-live]',
    autoStart() {
      let c = Array.from(document.querySelectorAll(W.AUTO_NAMED));
      for (const r of document.querySelectorAll('[role=region], section')) if (r.querySelectorAll('[aria-roledescription*="slide" i], [class*="slide" i]').length >= 2) c.push(r);
      c = c.filter((el) => W.visible(el) && !/^(input)$/.test(el.localName) && el.getAttribute('role') !== 'slider');
      c = c.filter((el, i) => c.indexOf(el) === i && !c.some((o) => o !== el && o.contains(el)));
      const t0 = performance.now();
      const snap = (el) => {
        const parts = [el.scrollLeft, el.scrollTop, (el.textContent || '').length, (el.textContent || '').slice(0, 200)];
        const kids = el.querySelectorAll('*');
        for (let i = 0; i < kids.length && i < 40; i++) { const r = kids[i].getBoundingClientRect(); const cs = getComputedStyle(kids[i]); parts.push(Math.round(r.left), Math.round(r.top), cs.opacity, cs.visibility, cs.transform); }
        return parts.join('|');
      };
      const st = c.map((el) => ({ el, times: [], last: snap(el), named: true }));
      const groups = new Map();
      const groupOf = (node) => {
        const el = node.nodeType === 1 ? node : node.parentElement;
        if (!el || !el.isConnected || !document.body.contains(el) || el === document.body) return null;
        for (const s of st) if (s.el.contains(el)) return s;
        let g = el.closest(W.AUTO_REGION) || el.parentElement || el;
        if (g === document.body || g === document.documentElement) g = el;
        if (!groups.has(g)) groups.set(g, { el: g, times: [], named: false });
        return groups.get(g);
      };
      const obs = new MutationObserver((recs) => {
        const now = performance.now() - t0;
        for (const r of recs) {
          if (r.type === 'attributes' && /^data-w22/.test(r.attributeName || '')) continue;
          const g = groupOf(r.target);
          if (g && (!g.times.length || g.times[g.times.length - 1] !== now)) g.times.push(now);
        }
      });
      if (document.body) obs.observe(document.body, { subtree: true, childList: true, attributes: true, characterData: true });
      const timer = setInterval(() => { for (const s of st) { const k = snap(s.el); if (k !== s.last) { s.times.push(performance.now() - t0); s.last = k; } } }, 250);
      W.auto = { st, groups, obs, timer, t0 };
      return { named: st.length };
    },
    // Split change times (ms) into episodes separated by quiet gaps; a transition or a burst of mutations is one episode.
    autoEpisodes(times) {
      const t = times.slice().sort((a, b) => a - b); const eps = [];
      for (const x of t) { const e = eps[eps.length - 1]; if (e && x - e.end <= 700) e.end = x; else eps.push({ start: x, end: x }); }
      return eps;
    },
    autoVerdict(times) {
      const eps = W.autoEpisodes(times);
      const span = eps.length ? (eps[eps.length - 1].end - eps[0].start) / 1000 : 0;
      const longest = eps.reduce((m, e) => Math.max(m, (e.end - e.start) / 1000), 0);
      const qualifies = (eps.length >= 2 && span >= 1.5) || longest >= 3;
      return { episodes: eps.length, span, longest, qualifies, pending: !qualifies && eps.length === 1 };
    },
    autoAll() { return W.auto ? [...W.auto.st, ...W.auto.groups.values()] : []; },
    // Groups that changed exactly once so far: a slow rotator (e.g. every 4-5 s) needs a longer look.
    autoPeek() {
      const pend = W.autoAll().filter((g) => W.visible(g.el) && W.autoVerdict(g.times).pending && (g.named || g.times[0] > 400));
      return pend.map((g) => W.sel(g.el));
    },
    autoPause(el, ids) {
      const scope = [el, el.parentElement].filter(Boolean);
      const ctrls = new Set();
      for (const root of scope) root.querySelectorAll('button, [role=button], input[type=button], input[type=checkbox], a[href]').forEach((b) => ctrls.add(b));
      for (const id of ids) document.querySelectorAll(`[aria-controls~="${CSS.escape(id)}"]`).forEach((b) => ctrls.add(b));
      const nm = (b) => ((b.getAttribute('aria-label') || '') + ' ' + (b.textContent || '') + ' ' + (b.getAttribute('title') || '') + ' ' + (b.value || '')).toLowerCase();
      const pause = Array.from(ctrls).find((b) => /\b(pause|stop)\b/.test(nm(b)));
      return pause ? { selector: W.sel(pause), name: nm(pause).replace(/\s+/g, ' ').trim().slice(0, 40) } : null;
    },
    autoStop() {
      if (!W.auto) return [];
      clearInterval(W.auto.timer); W.auto.obs.disconnect();
      const out = [];
      const all = W.autoAll().filter((g) => g.el.isConnected && W.visible(g.el) && g.times.length);
      for (const s of all) {
        const v = W.autoVerdict(s.times);
        const buckets = [...new Set(s.times.map((t) => Math.floor(t / 400)))];
        const ids = [s.el.id, ...Array.from(s.el.querySelectorAll('[id]')).map((e) => e.id)].filter(Boolean);
        out.push({ selector: W.sel(s.el), snippet: W.snippet(s.el), changes: buckets.length, episodes: v.episodes, span: +v.span.toFixed(1), qualifies: v.qualifies,
          source: s.named ? 'named-region' : 'mutations', role: s.el.getAttribute('aria-roledescription') || s.el.getAttribute('role') || null, live: s.el.getAttribute('aria-live'),
          pause: W.autoPause(s.el, ids) });
      }
      // Infinite (or > 5 s) CSS / Web animations on sizeable content (not spinners): moving content.
      const seen = new Set(all.map((g) => g.el));
      for (const a of (document.getAnimations ? document.getAnimations() : [])) {
        const el = a.effect && a.effect.target; if (!el || el.nodeType !== 1 || a.playState !== 'running') continue;
        const t = a.effect.getComputedTiming ? a.effect.getComputedTiming() : {};
        const total = t.iterations === Infinity ? Infinity : (t.activeDuration || 0) + (t.delay || 0);
        if (total <= 5000) continue;
        const r = el.getBoundingClientRect();
        if (!W.visible(el) || (r.width <= 64 && r.height <= 64) || !((el.textContent || '').trim() || el.querySelector('img, svg, video, canvas') || /^(img|svg|video|canvas)$/.test(el.localName))) continue;
        const owner = Array.from(seen).find((g) => g.contains(el) || el.contains(g));
        if (owner) continue;
        seen.add(el);
        const ids = [el.id, ...Array.from(el.querySelectorAll('[id]')).map((e) => e.id)].filter(Boolean);
        out.push({ selector: W.sel(el), snippet: W.snippet(el), changes: null, episodes: null, span: null, qualifies: true, source: 'css-animation',
          animation: a.animationName || a.id || 'animation', duration_ms: t.duration, iterations: t.iterations === Infinity ? 'infinite' : t.iterations,
          role: el.getAttribute('aria-roledescription') || el.getAttribute('role') || null, live: el.getAttribute('aria-live'), pause: W.autoPause(el, ids) });
      }
      W.auto = null;
      return out;
    },

    // ---- 4.1.3 status messages after activating buttons
    statusCandidates() {
      const bad = /\b(delete|remove|pay|buy|purchase|order|checkout|log ?out|sign ?out|unsubscribe|cancel (my )?(account|subscription))\b/i;
      if (!document.body) return [];
      return Array.from(document.querySelectorAll('button, [role=button], input[type=submit], input[type=button]'))
        .filter((b) => W.visible(b) && !b.disabled && !b.closest('a[href], [inert], dialog:not([open])') && !b.hasAttribute('aria-expanded') && !b.hasAttribute('aria-haspopup') && !b.hasAttribute('aria-controls') && !W.dialogTrigger(b))
        .filter((b) => !bad.test((b.getAttribute('aria-label') || '') + ' ' + (b.textContent || '') + ' ' + (b.value || '')))
        .slice(0, 8).map((b) => W.sel(b));
    },
    statusArm() {
      if (!window.__w22StatusArmed) {
        window.__w22StatusArmed = true;
        window.addEventListener('submit', (e) => e.preventDefault(), true);
      }
      document.querySelectorAll('form').forEach((f) => { f.noValidate = true; });
      W.statusBefore = new Map();
      for (const el of document.body.querySelectorAll('*')) { const t = el.textContent; if (t.length < 600) W.statusBefore.set(el, t.replace(/\s+/g, ' ').trim()); }
      W.statusChanged = new Set();
      if (W.statusObs) W.statusObs.disconnect();
      W.statusObs = new MutationObserver((recs) => {
        for (const r of recs) {
          if (r.type === 'characterData') { if (r.target.parentElement) W.statusChanged.add(r.target.parentElement); }
          else if (r.type === 'childList') W.statusChanged.add(r.target);
          else if (r.type === 'attributes' && r.target.nodeType === 1) W.statusChanged.add(r.target); // hidden/class toggles reveal messages
        }
      });
      W.statusObs.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ['hidden', 'class', 'style'] });
    },
    statusClick(sel) { let b = null; try { b = document.querySelector(sel); } catch (e) { b = null; } if (!b) return false; b.focus(); b.click(); return true; },
    statusCollect(buttonSel) {
      if (W.statusObs) W.statusObs.disconnect();
      let btn = null; try { btn = document.querySelector(buttonSel); } catch (e) { btn = null; }
      let active = document.activeElement;
      const isLive = (el) => { for (let n = el; n && n.nodeType === 1; n = n.parentElement) { const r = (n.getAttribute('role') || '').toLowerCase(); const l = (n.getAttribute('aria-live') || '').toLowerCase(); if (/^(status|alert|log|marquee|timer|alertdialog)$/.test(r) || (l && l !== 'off')) return true; } return false; };
      const out = [];
      const changed = Array.from(W.statusChanged).filter((el) => el.isConnected && el !== document.body && W.visible(el));
      const texts = changed.map((el) => ({ el, now: (el.textContent || '').replace(/\s+/g, ' ').trim(), before: W.statusBefore.has(el) ? W.statusBefore.get(el) : null }));
      const real = texts.filter((t) => t.now && t.now !== t.before && t.now.length <= 300);
      for (const t of real) {
        const el = t.el;
        if (real.some((o) => o !== t && el.contains(o.el) && o.el !== el)) continue; // report the innermost changed element
        if (btn && (el.contains(btn) || btn.contains(el))) continue;
        if (el.closest('dialog, [role=dialog], [role=alertdialog], [aria-modal="true"]')) continue;
        if (active && el.contains(active) && active !== document.body) continue; // focus moved to it: not a status message
        if (/^(ul|ol|table|tbody|thead|select|datalist)$/.test(el.localName) || /^(list|grid|table|listbox|tree)$/.test(el.getAttribute('role') || '')) continue;
        if (isLive(el) || el.querySelector('[role=status], [role=alert], [role=log], [aria-live]:not([aria-live="off"])')) continue;
        // Content the user asked for is not a status message: the control names the region it drives
        // (aria-controls), or it is a prev/next/more-style control that swapped the item shown in its own component.
        const req = btn ? W.requestedContent(btn, el, t.before) : null;
        if (req === 'controls' || req === 'navigated') { W.statusSkipped = (W.statusSkipped || []).concat([{ selector: W.sel(el), reason: req }]); continue; }
        out.push({ selector: W.sel(el), snippet: W.snippet(el), text: t.now.slice(0, 120), before: t.before === null ? null : t.before.slice(0, 60), ...(req ? { requested: req, label: W.controlLabel(btn) } : {}) });
        if (out.length >= 3) break;
      }
      W.statusChanged = new Set();
      return out;
    },

    controlLabel(b) {
      const ids = (b.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean);
      const byId = ids.map((i) => (document.getElementById(i) || {}).textContent || '').join(' ');
      return (b.getAttribute('aria-label') || byId || b.textContent || b.value || b.getAttribute('title') || '').replace(/\s+/g, ' ').trim();
    },
    // Is `el` (changed after activating `b`) the content `b` navigates rather than a status message?
    // 'controls': b's aria-controls names el or an ancestor/descendant of it. 'navigated': b is a prev/next/
    // slide/show-more control, el already held other content (swapped, not a message appearing), and b and el
    // share a small enclosing component. 'nav-label': swapped content with a navigation label, but outside a small
    // shared component (review). null: anything else, including a message appearing where there was none.
    requestedContent(b, el, before) {
      for (const id of (b.getAttribute('aria-controls') || '').split(/\s+/).filter(Boolean)) {
        const c = document.getElementById(id);
        if (c && (c === el || c.contains(el) || el.contains(c))) return 'controls';
      }
      const label = W.controlLabel(b);
      const nav = /^(?:[\u2039\u203a\u00ab\u00bb\u2190\u2192\u276e\u276f<>\s]+|(?:go to |show |view |see |load |display )?(?:the )?(?:prev(?:ious)?|next|more|fewer|less|older|newer|first|last|forward)\b.*|(?:go to |show )?(?:slide|item|page|story|image|photo|picture|banner|tab|card)\s*\d+.*)$/i;
      if (!label || !nav.test(label)) return null;
      const submit = b.form && ((b.localName === 'button' && (b.getAttribute('type') || 'submit').toLowerCase() === 'submit') || (b.localName === 'input' && b.type === 'submit'));
      if (submit || !before) return null; // a message appearing from nothing, or a form step: still a status message candidate
      let lca = b.parentElement;
      while (lca && !lca.contains(el)) lca = lca.parentElement;
      if (!lca || /^(html|body|main|form)$/.test(lca.localName) || lca.querySelectorAll('*').length > 200) return 'nav-label';
      return 'navigated';
    },

    // ---- 3.3.7 fields for redundant-entry comparison (within and across pages)
    entryFields() {
      const skip = /^(hidden|submit|button|reset|image|checkbox|radio|file|range|color|search)$/;
      const confirmRe = /\b(confirm|repeat|retype|re-?enter|verify)\b/i;
      const okRe = /same as|\buse (my |the |this )?(shipping|billing|delivery|home|previous|above|saved)\b|\bcopy (from|my)\b|\bas above\b|same[_-]?as/i;
      const labelOf = (el) => {
        let t = el.getAttribute('aria-label') || '';
        if (!t && el.labels && el.labels.length) t = Array.from(el.labels).map((l) => l.textContent).join(' ');
        if (!t) { const ids = (el.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean); t = ids.map((i) => (document.getElementById(i) || {}).textContent || '').join(' '); }
        return (t || el.getAttribute('placeholder') || '').replace(/\((required|optional)\)|\brequired\b|\*/gi, '').replace(/[^a-z0-9 ]+/gi, ' ').replace(/\s+/g, ' ').trim().toLowerCase();
      };
      // A step section: fieldset/form, data-step, step-like id/class, or a container whose own heading/legend says "Step N".
      const stepHead = (n) => Array.from(n.children).some((c) => /^(h[1-6]|legend|p)$/.test(c.localName) && /\bstep\s+\d/i.test(c.textContent || ''));
      const section = (el) => { for (let n = el.parentElement; n; n = n.parentElement) { const id = (n.id || '') + ' ' + (typeof n.className === 'string' ? n.className : ''); if (/^(form|fieldset)$/.test(n.localName) || n.hasAttribute('data-step') || /(^|[\s_-])(step|wizard|stage)s?([\s_-]?\d+)?($|[\s_-])/i.test(id) || stepHead(n)) return n; } return null; };
      const offersCopy = (sec) => !!sec && Array.from(sec.querySelectorAll('input, button, select, label, a, [role=checkbox], [role=button], [role=switch]')).some((d) => okRe.test((d.textContent || '') + ' ' + (d.getAttribute('aria-label') || '') + ' ' + (d.name || '') + ' ' + (d.id || '')));
      const secs = []; const fields = []; const forms = [];
      for (const el of document.querySelectorAll('input, select, textarea')) {
        const type = (el.getAttribute('type') || 'text').toLowerCase();
        if (el.localName === 'input' && skip.test(type)) continue;
        const ac = (el.getAttribute('autocomplete') || '').toLowerCase().split(/\s+/).filter((t) => t && !t.startsWith('section-') && !/^(shipping|billing|on|off)$/.test(t));
        const label = labelOf(el);
        const confirm = confirmRe.test(label) || confirmRe.test((el.name || '') + ' ' + (el.id || '')) && /e-?mail|address|phone/i.test((el.name || '') + ' ' + (el.id || ''));
        const keys = [];
        if (ac.length && !/^(new-password|current-password|one-time-code)$/.test(ac[ac.length - 1])) keys.push('autocomplete ' + ac.join(' '));
        if (label && !confirm) keys.push(`label "${label}"`);
        // Purpose inferred from autocomplete, input type, or name/id/label words, so "Email address" and
        // "Email for card notices" (neither with autocomplete) are recognised as the same information.
        const purpose = W.fieldPurpose(el, type, ac, label);
        if (purpose && !confirm) keys.push('purpose ' + purpose);
        let exempt = null;
        if (type === 'password' || /password|one-time-code/.test(ac.join(' '))) exempt = 'security';
        else if (el.getAttribute('data-reentry')) exempt = el.getAttribute('data-reentry');
        else if (el.localName === 'select' || el.hasAttribute('list')) exempt = 'select option';
        else if ((el.value || '').trim()) exempt = 'auto-populated';
        else if (/\bnew\b/.test(label)) exempt = 'previous value no longer valid';
        const sec = section(el); let si = secs.indexOf(sec); if (si < 0) { secs.push(sec); si = secs.length - 1; }
        let fi = el.form ? forms.indexOf(el.form) : -1; if (el.form && fi < 0) { forms.push(el.form); fi = forms.length - 1; }
        fields.push({ selector: W.sel(el), snippet: W.snippet(el), keys, exempt, confirm, section: si, form: fi, copyOption: offersCopy(sec), label });
      }
      const text = document.body ? document.body.innerText || '' : '';
      const isStep = /\bstep\s+\d+\s+(of|\/)\s+\d+\b/i.test(text) || !!document.querySelector('[aria-current="step"]') || /(step|checkout|wizard|signup|register|apply|booking|onboard)/i.test(location.pathname);
      return { fields, isStep };
    },
    fieldPurpose(el, type, ac, label) {
      const last = ac.length ? ac[ac.length - 1] : '';
      const ACMAP = { email: 'email', tel: 'tel', 'tel-national': 'tel', name: 'name', 'given-name': 'given-name', 'family-name': 'family-name', 'street-address': 'street-address',
        'address-line1': 'street-address', 'postal-code': 'postal-code', 'address-level2': 'city', bday: 'bday', organization: 'organization' };
      if (ACMAP[last]) return ACMAP[last];
      if (type === 'email') return 'email';
      if (type === 'tel') return 'tel';
      const words = ((el.name || '') + ' ' + (el.id || '') + ' ' + label).toLowerCase().replace(/[_-]+/g, ' ');
      if (/\be ?mail\b/.test(words)) return 'email';
      if (/\b(phone|telephone|mobile|tel)\b/.test(words)) return 'tel';
      if (/\b(post ?code|postal code|zip( code)?)\b/.test(words)) return 'postal-code';
      if (/\b(street|address line ?1|street address|home address)\b/.test(words)) return 'street-address';
      if (/\b(town|city)\b/.test(words)) return 'city';
      if (/\b(first name|given name|forename)\b/.test(words)) return 'given-name';
      if (/\b(last name|family name|surname)\b/.test(words)) return 'family-name';
      if (/\b(full name|your name)\b/.test(words) || /^name$/.test(label)) return 'name';
      if (/\b(date of birth|birth ?date|dob)\b/.test(words)) return 'bday';
      return null;
    },
    // Crawl targets: links, plus same-page form actions and simple scripted navigation (multi-step flows often
    // move to the next step with a form submit or location.href, never an <a>).
    links() {
      const out = Array.from(document.querySelectorAll('a[href], area[href]')).map((a) => a.href);
      // GET forms only: fetching a POST endpoint's URL is not what the form does and may have side effects.
      for (const f of document.querySelectorAll('form[action]')) { const a = f.getAttribute('action'); if ((f.getAttribute('method') || 'get').toLowerCase() === 'get' && a && !/^(javascript:|#)/i.test(a.trim()) && !/log-?out|sign-?out|delete|unsubscribe/i.test(a)) { try { out.push(new URL(a, location.href).href); } catch (e) { /* ignore */ } } }
      for (const b of document.querySelectorAll('[formaction]:not([formmethod="post" i])')) { try { out.push(new URL(b.getAttribute('formaction'), location.href).href); } catch (e) { /* ignore */ } }
      for (const el of document.querySelectorAll('[onclick], [data-href], [data-url]')) {
        const src = (el.getAttribute('onclick') || '') + ' ';
        const m = /location(?:\.href)?\s*=\s*['"]([^'"]+)['"]|location\.(?:assign|replace)\(\s*['"]([^'"]+)['"]/.exec(src);
        const u = m ? (m[1] || m[2]) : (el.getAttribute('data-href') || el.getAttribute('data-url'));
        if (u) { try { out.push(new URL(u, location.href).href); } catch (e) { /* ignore */ } }
      }
      return out;
    },
  };
  window.__w22 = W;
}
const PAGE_LIB = `(${pageLib.toString()})()`;

// Pixel helpers, run in a blank helper page (OffscreenCanvas decodes the PNG screenshots).
function helperLib() {
  if (window.__px) return;
  const P = {
    prev: null,
    async decode(b64) {
      const bin = atob(b64); const u = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
      const bm = await createImageBitmap(new Blob([u], { type: 'image/png' }));
      const c = new OffscreenCanvas(bm.width, bm.height); const x = c.getContext('2d', { willReadFrequently: true });
      x.drawImage(bm, 0, 0); return x.getImageData(0, 0, bm.width, bm.height);
    },
    // Compare a crop of the previous frame with a crop of the current frame (same size), ignoring `mask` (current-frame coords).
    async step({ b64, compare }) {
      const img = await P.decode(b64);
      let res = null;
      if (compare && P.prev) {
        const { then: ra, now: rb, mask } = compare; const A = P.prev, B = img;
        let changed = 0, total = 0, minx = 1e9, miny = 1e9, maxx = -1, maxy = -1;
        for (let yy = 0; yy < ra.h; yy++) for (let xx = 0; xx < ra.w; xx++) {
          const bx = rb.x + xx, by = rb.y + yy, ax = ra.x + xx, ay = ra.y + yy;
          if (ax < 0 || ay < 0 || bx < 0 || by < 0 || ax >= A.width || ay >= A.height || bx >= B.width || by >= B.height) continue;
          if (mask && bx >= mask.x && bx < mask.x + mask.w && by >= mask.y && by < mask.y + mask.h) continue;
          const ia = (ay * A.width + ax) * 4, ib = (by * B.width + bx) * 4;
          const d = Math.max(Math.abs(A.data[ia] - B.data[ib]), Math.abs(A.data[ia + 1] - B.data[ib + 1]), Math.abs(A.data[ia + 2] - B.data[ib + 2]));
          total++;
          if (d > 24) { changed++; minx = Math.min(minx, xx); miny = Math.min(miny, yy); maxx = Math.max(maxx, xx); maxy = Math.max(maxy, yy); }
        }
        res = { changed, total, bbox: changed ? { x: minx, y: miny, w: maxx - minx + 1, h: maxy - miny + 1 } : null };
      }
      P.prev = img;
      return res;
    },
    // Contrast of `fg` against the background frame `b64` (text hidden). With `shown` (the same clip with the text
    // visible), pixels that differ between the frames locate the glyphs; `glyph` stats cover only the background
    // behind the glyphs (dilated by 1px), so lines, icons or chart shapes elsewhere in the text box do not count.
    async contrast({ b64, fg, shown }) {
      const img = await P.decode(b64);
      const vis = shown ? await P.decode(shown) : null;
      const lin = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
      const lum = (r, g, b) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
      const a = fg[3] === undefined ? 1 : fg[3];
      const W = img.width, H = img.height, n = W * H;
      const ratio = new Float64Array(n);
      for (let p = 0; p < n; p++) {
        const i = p * 4, br = img.data[i], bg = img.data[i + 1], bb = img.data[i + 2];
        const fr = fg[0] * a + br * (1 - a), fgc = fg[1] * a + bg * (1 - a), fb = fg[2] * a + bb * (1 - a);
        const l1 = lum(fr, fgc, fb), l2 = lum(br, bg, bb);
        ratio[p] = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
      }
      if (!n) return null;
      const stats = (arr) => {
        if (!arr.length) return null;
        arr.sort((x, y) => x - y);
        const q = (p) => arr[Math.min(arr.length - 1, Math.floor(p * arr.length))];
        return { min: arr[0], p5: q(0.05), median: q(0.5), max: arr[arr.length - 1], pixels: arr.length };
      };
      const box = stats(Array.from(ratio));
      let glyph = null;
      if (vis && vis.width === W && vis.height === H) {
        const ink = new Uint8Array(n);
        for (let p = 0; p < n; p++) {
          const i = p * 4;
          if (Math.max(Math.abs(img.data[i] - vis.data[i]), Math.abs(img.data[i + 1] - vis.data[i + 1]), Math.abs(img.data[i + 2] - vis.data[i + 2])) > 16) ink[p] = 1;
        }
        const sel = [];
        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
          let hit = 0;
          for (let dy = -1; dy <= 1 && !hit; dy++) for (let dx = -1; dx <= 1 && !hit; dx++) {
            const xx = x + dx, yy = y + dy;
            if (xx >= 0 && yy >= 0 && xx < W && yy < H && ink[yy * W + xx]) hit = 1;
          }
          if (hit) sel.push(ratio[y * W + x]);
        }
        glyph = sel.length >= 12 ? stats(sel) : null;
      }
      return { ...box, box, glyph };
    },
  };
  window.__px = P;
}
const HELPER_LIB = `(${helperLib.toString()})()`;

// ---------------------------------------------------------------- dependency loading
export function depsInstalled() {
  return fs.existsSync(path.join(CACHE_DIR, 'node', 'node_modules', 'playwright', 'package.json'))
    && fs.existsSync(path.join(CACHE_DIR, 'node', 'node_modules', 'axe-core', 'axe.min.js'));
}
function loadDeps() {
  if (!depsInstalled()) {
    const e = new Error(`page runner not installed (missing ${path.join(CACHE_DIR, 'node')}). Run: ${path.join(SKILL_DIR, 'scripts', 'setup_page_runner.sh')}`);
    e.code = 'DEPS'; throw e;
  }
  process.env.PLAYWRIGHT_BROWSERS_PATH ??= path.join(CACHE_DIR, 'ms-playwright');
  const req = createRequire(path.join(CACHE_DIR, 'node', 'package.json'));
  const playwright = req('playwright');
  const axePath = req.resolve('axe-core/axe.min.js');
  return {
    chromium: playwright.chromium,
    axeSource: fs.readFileSync(axePath, 'utf8'),
    versions: { playwright: req('playwright/package.json').version, axe: req('axe-core/package.json').version },
  };
}

// ---------------------------------------------------------------- static server
const MIME = { '.html': 'text/html; charset=utf-8', '.htm': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp',
  '.ico': 'image/x-icon', '.woff': 'font/woff', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.txt': 'text/plain; charset=utf-8', '.mp4': 'video/mp4', '.webm': 'video/webm', '.pdf': 'application/pdf' };
export function startServer(root) {
  const rootAbs = path.resolve(root);
  const server = http.createServer((req, res) => {
    let p;
    try { p = decodeURIComponent(new URL(req.url, 'http://x').pathname); } catch { res.writeHead(400).end(); return; }
    let file = path.join(rootAbs, p);
    if (file !== rootAbs && !file.startsWith(rootAbs + path.sep)) { res.writeHead(403).end(); return; }
    try { if (fs.statSync(file).isDirectory()) file = path.join(file, 'index.html'); } catch { /* 404 below */ }
    fs.readFile(file, (err, data) => {
      if (err) { res.writeHead(404, { 'content-type': 'text/plain' }).end('not found'); return; }
      res.writeHead(200, { 'content-type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream', 'cache-control': 'no-store' }).end(data);
    });
  });
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => resolve({ server, origin: `http://127.0.0.1:${server.address().port}` }));
  });
}

// Resolve the CLI target into seed URLs plus a location mapper.
async function resolveTarget(target) {
  if (/^https?:\/\//i.test(target)) {
    return { seeds: [new URL(target).href], loc: (u) => ({ url: u }), close: async () => {} };
  }
  const fsPath = target.startsWith('file:') ? fileURLToPath(target) : target;
  let st;
  try { st = fs.statSync(fsPath); } catch { throw new UsageError(`target not found: ${target}`); }
  const rootGiven = st.isDirectory() ? fsPath : path.dirname(fsPath);
  const { server, origin } = await startServer(rootGiven);
  let seeds;
  if (st.isDirectory()) {
    if (fs.existsSync(path.join(fsPath, 'index.html'))) seeds = [origin + '/index.html'];
    else seeds = fs.readdirSync(fsPath).filter((f) => /\.html?$/i.test(f)).sort().map((f) => origin + '/' + encodeURIComponent(f));
    if (!seeds.length) { server.close(); throw new UsageError(`no .html files in ${target}`); }
  } else seeds = [origin + '/' + encodeURIComponent(path.basename(fsPath))];
  const loc = (u) => {
    if (!u.startsWith(origin)) return { url: u };
    const p = decodeURIComponent(new URL(u).pathname).replace(/^\//, '');
    return { file: path.join(rootGiven, p || 'index.html') };
  };
  return { seeds, loc, close: () => new Promise((r) => server.close(() => r())), origin };
}

// ---------------------------------------------------------------- findings
function mk(sc, rule, severity, loc, { selector = null, snippet = null, message, help = null, evidence = null } = {}) {
  return { tool: TOOL, sc, level: SC[sc] ? SC[sc][0] || null : null, rule, severity, ...loc, line: null, col: null, selector, snippet, message, help: help || understandingUrl(sc), evidence };
}

// ---------------------------------------------------------------- checks
async function runAxe(page, deps, opts, loc, ctx) {
  await page.evaluate(deps.axeSource);
  const tags = axeTagsForLevel(opts.level);
  const disable = opts.selection.checks.has('target-size') ? ['target-size'] : [];
  const res = await page.evaluate(async ({ tags, disable }) => {
    const rules = window.axe.getRules();
    const known = new Set(rules.flatMap((r) => r.tags));
    const values = tags.filter((t) => known.has(t));
    const known2 = new Set(rules.map((x) => x.ruleId));
    const rulesOpt = Object.fromEntries(disable.filter((id) => known2.has(id)).map((id) => [id, { enabled: false }]));
    const r = await window.axe.run(document, { runOnly: { type: 'tag', values }, rules: rulesOpt, resultTypes: ['violations', 'incomplete'] });
    const slim = (list) => list.map((v) => ({ id: v.id, impact: v.impact, tags: v.tags, help: v.help, helpUrl: v.helpUrl, description: v.description,
      nodes: v.nodes.slice(0, 50).map((n) => ({ target: n.target, html: n.html, failureSummary: n.failureSummary, impact: n.impact,
        messages: [...(n.any || []), ...(n.all || []), ...(n.none || [])].map((c) => c.message).filter(Boolean) })), total: v.nodes.length }));
    const covered = [...new Set(rules.filter((x) => !x.tags.includes('experimental') && !x.tags.includes('deprecated')).flatMap((x) => x.tags).filter((t) => /^wcag\d{3,4}$/.test(t)))];
    return { violations: slim(r.violations), incomplete: slim(r.incomplete), version: window.axe.version, covered };
  }, { tags, disable });
  ctx.axeVersion = res.version; ctx.axeCovered = res.covered.map(scFromAxeTag).filter(Boolean);
  const findings = []; const contrastQueue = [];
  // 1.4.3 logotype exception: text that is part of a logo or brand name is downgraded to warn.
  const logos = new Map();
  for (const v of res.violations) if (/^color-contrast/.test(v.id)) for (const n of v.nodes) {
    if (n.target.length === 1 && typeof n.target[0] === 'string') logos.set(n, await page.evaluate((s) => window.__w22.logoContext(s), n.target[0]).catch(() => null));
  }
  const emit = (v, n, severity) => {
    const scs = v.tags.map(scFromAxeTag).filter(Boolean).sort(scCompare);
    const sc = scs[0] || null;
    let msg = severity === 'fail' ? `${v.help}. ${(n.failureSummary || '').replace(/\s+/g, ' ').trim()}` : `Needs review: ${v.help}. ${n.messages.join(' ')}`.trim();
    const logo = logos.get(n);
    if (logo && severity === 'fail') { severity = 'warn'; msg = `${LOGO_MSG}: ${msg}`; }
    findings.push(mk(sc, 'axe:' + v.id, severity, loc, { selector: n.target.flat().join(' >>> '), snippet: n.html, message: msg.slice(0, 600), help: v.helpUrl,
      evidence: { engine: 'axe-core ' + res.version, impact: n.impact || v.impact, related_sc: scs.slice(1), nodes_total: v.total, ...(logo ? { logotype: logo } : {}) } }));
  };
  for (const v of res.violations) for (const n of v.nodes) emit(v, n, 'fail');
  for (const v of res.incomplete) for (const n of v.nodes) {
    if ((v.id === 'color-contrast' || v.id === 'color-contrast-enhanced') && opts.selection.checks.has('contrast-sample') && n.target.length === 1 && typeof n.target[0] === 'string') {
      contrastQueue.push({ rule: v, node: n });
    } else emit(v, n, 'manual');
  }
  return { findings, contrastQueue };
}

async function runContrastSample(page, helper, queue, opts, loc) {
  const findings = [];
  for (const { rule, node } of queue.slice(0, 30)) {
    const sc = rule.id === 'color-contrast-enhanced' ? '1.4.6' : '1.4.3';
    const info = await page.evaluate((s) => window.__w22.textInfo(s), node.target[0]);
    if (!info) continue;
    try {
      const vp = page.viewportSize();
      const x = Math.max(0, Math.floor(info.box.x)), y = Math.max(0, Math.floor(info.box.y));
      const w = Math.min(vp.width, Math.ceil(info.box.x + info.box.w)) - x, h = Math.min(vp.height, Math.ceil(info.box.y + info.box.h)) - y;
      if (w < 1 || h < 1) continue;
      const clip = { x, y, width: w, height: h };
      const shown = await page.screenshot({ clip, animations: 'disabled', caret: 'hide' });
      if (!(await page.evaluate((s) => window.__w22.hideText(s), node.target[0]))) continue;
      const shot = await page.screenshot({ clip, animations: 'disabled', caret: 'hide' });
      const stats = await helper.evaluate((a) => window.__px.contrast(a), { b64: shot.toString('base64'), shown: shown.toString('base64'), fg: info.fg });
      if (!stats) continue;
      const large = info.fontSize >= 24 || (info.fontSize >= 18.66 && info.fontWeight >= 700);
      const need = sc === '1.4.6' ? (large ? 4.5 : 7) : (large ? 3 : 4.5);
      const r2 = (v) => +v.toFixed(2);
      const pick4 = (q) => ({ min: r2(q.min), p5: r2(q.p5), median: r2(q.median), max: r2(q.max) });
      // Judge on the background behind the glyphs when they could be located; else on the whole text box.
      const judged = stats.glyph || stats.box;
      const ok = judged.p5 >= need;
      const shapesIgnored = ok && stats.glyph && stats.box.p5 < need;
      const region = stats.glyph ? 'behind glyphs' : 'text box';
      const logo = ok ? null : await page.evaluate((s) => window.__w22.logoContext(s), node.target[0]).catch(() => null);
      findings.push(mk(sc, 'contrast-sampled-background', ok ? 'info' : 'warn', loc, {
        selector: node.target[0], snippet: node.html,
        message: ok ? `Text over a complex background: sampled background ${region} gives >= ${need}:1 for 95% of pixels (worst ${r2(judged.min)}:1)${shapesIgnored ? `; darker/lighter shapes elsewhere in the text box (5th percentile ${r2(stats.box.p5)}:1) are not behind the glyphs and were ignored` : ''}. Confirm visually.`
          : `${logo ? LOGO_MSG + ': ' : ''}Text over a complex background likely below ${need}:1: 5th-percentile contrast ${r2(judged.p5)}:1, median ${r2(judged.median)}:1 against the sampled background ${region}.`,
        evidence: { method: 'pixel sample of background with text hidden', sample_region: stats.glyph ? 'background behind the glyphs (pixels that change when the text is hidden, dilated 1px)' : 'whole text box (glyph pixels not located)',
          fg_rgba: info.fg, ...(info.svg ? { fg_source: 'SVG fill' } : {}), font_size_px: info.fontSize, font_weight: info.fontWeight, large_text: large,
          required: need, contrast: pick4(judged), pixels: judged.pixels, ...(stats.glyph ? { box_contrast: { ...pick4(stats.box), pixels: stats.box.pixels } } : {}),
          ...(shapesIgnored ? { low_pixels_ignored: 'Pixels below the required ratio lie outside the glyph area (other shapes such as lines, markers or icons inside the sample box), not behind the text; judged on the background behind the glyphs.' } : {}),
          axe: node.messages.join(' '), ...(logo ? { logotype: logo } : {}) },
      }));
    } finally {
      await page.evaluate(() => window.__w22.unhideText());
    }
  }
  for (const { rule, node } of queue.slice(30)) findings.push(mk(rule.id === 'color-contrast-enhanced' ? '1.4.6' : '1.4.3', 'axe:' + rule.id, 'manual', loc, { selector: node.target[0], snippet: node.html, message: 'Needs review: ' + rule.help + ' (sampling limit reached)' }));
  return findings;
}

async function runTargetSize(page, loc) {
  const r = await page.evaluate(() => window.__w22.targetSize());
  const findings = []; const exempt = { inline: [], 'user-agent': [] };
  for (const t of r.results) {
    if (t.exception) { exempt[t.exception].push(t.selector); continue; }
    findings.push(mk('2.5.8', 'target-size-undersized', 'warn', loc, { selector: t.selector, snippet: t.snippet,
      message: `Target is ${t.w}x${t.h} CSS px (< 24x24) and fails the spacing test: its 24px circle ${t.conflict.kind === 'circles-overlap' ? 'overlaps the circle of undersized target' : 'intersects target'} ${t.conflict.selector} (${t.conflict.distance}px). Confirm no equivalent-control or essential exception applies.`,
      evidence: { width: t.w, height: t.h, conflict: t.conflict } }));
  }
  const ex = Object.entries(exempt).filter(([, v]) => v.length);
  if (ex.length) findings.push(mk('2.5.8', 'target-size-exception', 'info', loc, {
    message: 'Undersized targets that fail spacing but meet an exception: ' + ex.map(([k, v]) => `${v.length} ${k}`).join(', ') + '.',
    evidence: Object.fromEntries(ex.map(([k, v]) => [k, v.slice(0, 10)])) }));
  return findings;
}

async function runAuth(page, loc) {
  const a = await page.evaluate(() => window.__w22.auth());
  const f = [];
  for (const p of a.password) {
    if (p.pasteBlocked) f.push(mk('3.3.8', 'password-paste-blocked', 'fail', loc, { selector: p.selector, snippet: p.snippet, message: 'Password field cancels paste events, which blocks password managers and copy-paste (a cognitive function test without a supported mechanism), unless another authentication method is offered.', evidence: { probe: 'synthetic ClipboardEvent("paste") was cancelled' } }));
    if (p.autocompleteOff) f.push(mk('3.3.8', 'password-autocomplete-off', 'warn', loc, { selector: p.selector, snippet: p.snippet, message: `Password field disables autocomplete (${p.autocomplete ? 'autocomplete="off"' : 'form autocomplete="off"'}); use "current-password" or "new-password" so password managers can fill it.`, evidence: { autocomplete: p.autocomplete, form_autocomplete: p.formAutocomplete } }));
  }
  for (const o of a.otp) if (o.pasteBlocked) f.push(mk('3.3.8', 'otp-paste-blocked', 'fail', loc, { selector: o.selector, snippet: o.snippet, message: 'One-time-code field cancels paste events; users must transcribe the code.', evidence: { autocomplete: o.autocomplete } }));
  for (const c of a.captcha) {
    f.push(mk('3.3.8', 'captcha-cognitive-test', 'manual', loc, { selector: c.selector, snippet: c.snippet, message: 'CAPTCHA or challenge detected. Verify an alternative method, a mechanism to assist, or the object/personal-content recognition exception applies.' }));
    f.push(mk('3.3.9', 'captcha-cognitive-test', 'manual', loc, { selector: c.selector, snippet: c.snippet, message: 'CAPTCHA or challenge detected. At AAA, object and personal-content recognition are not exceptions.' }));
  }
  for (const r of a.redundant) f.push(mk('3.3.7', 'possible-redundant-entry', 'manual', loc, { selector: r.selector, snippet: r.snippet, message: `Possible redundant entry: ${r.reason}. Verify previously entered information is auto-populated or selectable (re-entry is allowed only when essential, for security, or when the earlier data is no longer valid).` }));
  return f;
}

// Current focus, resolving focus inside (possibly cross-origin) iframes through Playwright frames.
async function getFocus(page) {
  const info = await page.evaluate(() => window.__w22.focusInfo());
  if (info.isFrame) {
    try {
      const h = await page.evaluateHandle(() => { let el = document.activeElement; while (el && el.shadowRoot && el.shadowRoot.activeElement) el = el.shadowRoot.activeElement; return el; });
      const fr = h.asElement() ? await h.asElement().contentFrame() : null;
      await h.dispose();
      if (fr) {
        info.inner = await fr.evaluate(() => {
          const a = document.activeElement; if (!a || a === document.body || a === document.documentElement) return '';
          const parts = []; for (let n = a; n && n.nodeType === 1; n = n.parentElement) {
            if (n.id) { parts.unshift('#' + n.id); break; }
            const sib = n.parentElement ? Array.from(n.parentElement.children).filter((c) => c.localName === n.localName) : [n];
            parts.unshift(n.localName + (sib.length > 1 ? `:nth-of-type(${sib.indexOf(n) + 1})` : ''));
          }
          return parts.join(' > ');
        });
        info.key = info.selector + '|' + info.inner;
      }
    } catch { /* keep in-page fallback */ }
  }
  return info;
}

async function viewportShot(page) { return page.screenshot({ animations: 'disabled', caret: 'hide' }); }

const MULTI_STOP_LIMIT = 16; // Tab presses tolerated on one multi-part control (datetime-local has ~6 segments)
async function runFocusWalk(page, helper, opts, loc, shotDir, tag) {
  const f = [];
  await page.evaluate(() => { window.__w22.freezeMotion(); window.__w22.indexDom(); if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); window.scrollTo(0, 0); });
  await helper.evaluate(() => { window.__px.prev = null; });
  const total = await page.evaluate(() => window.__w22.tabbables().length);
  const startUrl = page.url();
  const seq = []; const vp = page.viewportSize(); const PAD = 8;
  let stuck = 0, stopReason = 'max-tabs', trap = null; let checked = 0;
  const clamp = (r) => {
    const x = Math.floor(r.x - PAD), y = Math.floor(r.y - PAD), w = Math.ceil(r.w + 2 * PAD), h = Math.ceil(r.h + 2 * PAD);
    return { x, y, w, h, inside: x >= 0 && y >= 0 && x + w <= vp.width && y + h <= vp.height };
  };
  const saveShot = (buf, name) => { if (!shotDir) return null; const p = path.join(shotDir, name); fs.writeFileSync(p, buf); return p; };
  let prevShot = null;
  // Extra presses spent stepping through the parts of multi-part controls do not use up the walk budget.
  let bonus = 0;
  for (let i = 0; i < opts.maxTabs + bonus; i++) {
    await page.keyboard.press('Tab');
    if (page.url() !== startUrl) { stopReason = 'navigated'; break; }
    // Sample only after the browser's focus scrolling (and any scripted smooth scroll) has settled.
    await page.evaluate(() => window.__w22.settleScroll()).catch(() => {});
    const info = await getFocus(page);
    dbg('focus', 'tab', { i, sel: info.selector, rect: info.rect, samples: info.samples, covered: info.covered, by: info.coveredBy, offscreen: info.offscreen });
    const prev = seq[seq.length - 1];
    // --- 2.4.7: compare previous element focused (prev frame) vs unfocused (this frame)
    let compare = null;
    if (prev && prev.key !== 'BODY' && !prev.isFrame && prev.key !== info.key && !prev.offscreen && !(prev.samples > 0 && prev.covered === prev.samples)) {
      const now = await page.evaluate((i) => window.__w22.walkRect(i), prev.idx);
      const then = clamp(prev.rect);
      if (now && then.inside) {
        const nowBox = { x: Math.floor(now.x - PAD), y: Math.floor(now.y - PAD), w: then.w, h: then.h };
        if (nowBox.x >= 0 && nowBox.y >= 0 && nowBox.x + nowBox.w <= vp.width && nowBox.y + nowBox.h <= vp.height) {
          const mask = info.key !== 'BODY' && !info.offscreen ? clamp(info.rect) : null;
          compare = { then, now: nowBox, mask, unfocusedStyle: now.style };
        }
      }
    }
    const buf = await viewportShot(page);
    const diff = await helper.evaluate((a) => window.__px.step(a), { b64: buf.toString('base64'), compare: compare ? { then: compare.then, now: compare.now, mask: compare.mask } : null });
    if (compare && diff && diff.total >= 0.3 * compare.then.w * compare.then.h) {
      checked++;
      if (diff.changed < 20) {
        const maskedShare = 1 - diff.total / (compare.then.w * compare.then.h);
        const noChange = diff.changed < 4 && maskedShare < 0.15;
        const shot = saveShot(prevShot, `${tag}-focus-${prev.idx}.png`);
        f.push(mk('2.4.7', noChange ? 'focus-not-visible' : 'focus-indicator-faint', noChange ? 'fail' : 'warn', loc, { selector: prev.selector, snippet: prev.snippet,
          message: noChange ? 'Keyboard focus produces no visible change around the element (focused vs unfocused screenshots are identical within 8px).'
            : `Keyboard focus changes only ${diff.changed} pixels around the element${maskedShare >= 0.15 ? ` (${Math.round(maskedShare * 100)}% of the area was masked by the next focused element)` : ''}; the indicator may be missing or too faint. Confirm visually.`,
          evidence: { changed_pixels: diff.changed, compared_pixels: diff.total, masked_share: +maskedShare.toFixed(2), focused_style: prev.style, unfocused_style: compare.unfocusedStyle, screenshot: shot || undefined } }));
      }
    }
    prevShot = buf;
    seq.push(info);
    if (info.key === 'BODY') {
      if (seq.some((s) => s.key !== 'BODY')) { stopReason = 'wrapped'; break; }
      if (seq.length >= 2) { stopReason = 'no-focusable'; break; }
      continue;
    }
    // --- 2.4.7 offscreen / 2.4.11 / 2.4.12
    if (info.offscreen && !info.isFrame) {
      f.push(mk('2.4.7', 'focus-offscreen', 'warn', loc, { selector: info.selector, snippet: info.snippet, message: 'Focused element is not rendered inside the viewport (zero size or positioned off-screen), so the focus indicator cannot be seen.', evidence: { rect: info.rect } }));
    } else if (info.samples > 0 && info.covered > 0) {
      const full = info.covered === info.samples;
      const shot = saveShot(buf, `${tag}-obscured-${info.idx}.png`);
      const ev = { sampled_points: info.samples, covered_points: info.covered, covered_by: info.coveredBy, rect: info.rect, screenshot: shot || undefined };
      if (full) f.push(mk('2.4.11', 'focus-obscured-fully', 'fail', loc, { selector: info.selector, snippet: info.snippet, message: `Focused element is entirely hidden by author-created fixed/sticky content (${info.coveredBy.join(', ')}). Exception: content the user opened.`, evidence: ev }));
      f.push(mk('2.4.12', full ? 'focus-obscured-fully' : 'focus-obscured-partially', 'warn', loc, { selector: info.selector, snippet: info.snippet, message: `Focused element is ${full ? 'entirely' : 'partly'} hidden by fixed/sticky content (${info.covered}/${info.samples} sample points covered by ${info.coveredBy.join(', ')}).`, evidence: ev }));
    }
    // --- 2.1.2 trap detection
    if (prev && prev.key === info.key) {
      stuck++;
      if (info.multi && bonus < opts.maxTabs) bonus++;
      // Repeated Tabs on one element are normal inside multi-part native controls (date/time segments, media
      // buttons) and cross-origin frames: only a trap if focus never leaves within a generous bound.
      const limit = info.isFrame && (info.inner === '?cross-origin') ? 40 : info.multi ? MULTI_STOP_LIMIT : 2;
      if (stuck >= limit) { trap = { kind: 'stuck', keys: new Set([info.key]), at: info, modal: info.modal }; stopReason = 'trap'; break; }
    } else stuck = 0;
    if (!(prev && prev.key === info.key)) {
      const firstIdx = seq.findIndex((s) => s.key === info.key);
      if (firstIdx < seq.length - 1) {
        const loop = seq.slice(firstIdx, seq.length - 1);
        if (!loop.some((s) => s.key === 'BODY')) {
          const keys = new Set(loop.map((s) => s.key));
          if (keys.size < total) { trap = { kind: 'cycle', keys, at: info, modal: loop.every((s) => s.modal) }; stopReason = 'trap'; }
          else stopReason = 'wrapped-in-document';
          break;
        }
      }
    }
  }
  if (trap) {
    const leave = async () => !trap.keys.has((await getFocus(page)).key);
    let released = null;
    const extra = trap.at.multi ? MULTI_STOP_LIMIT : 0; // a multi-part control needs more presses to step past its parts
    await page.keyboard.press('Escape');
    for (let j = 0; j < trap.keys.size + 1 + extra && !released; j++) { await page.keyboard.press('Tab'); if (await leave()) released = 'Escape then Tab'; }
    if (!released) {
      for (let j = 0; j < trap.keys.size + 2 + extra && !released; j++) { await page.keyboard.press('Shift+Tab'); if (await leave()) released = 'Shift+Tab'; }
    }
    const members = [...trap.keys].slice(0, 10);
    const ev = { kind: trap.kind, elements: members, tabbable_on_page: total, released_by: released, ...(trap.at.multi ? { multi_part_control: trap.at.multi, tab_presses_on_element: stuck + 1 } : {}) };
    if (released) f.push(mk('2.1.2', 'focus-contained', 'manual', loc, { selector: trap.at.selector, snippet: trap.at.snippet, message: `Tab keeps focus inside a group of ${trap.keys.size} element(s); focus left with ${released}. Verify users are told how to move focus away (required when a non-standard method is needed).`, evidence: ev }));
    else if (trap.modal) f.push(mk('2.1.2', 'modal-focus-containment', 'warn', loc, { selector: trap.at.selector, snippet: trap.at.snippet, message: `Focus is contained in a modal dialog (${trap.keys.size} element(s)) and neither Escape nor Shift+Tab released it. Verify a keyboard-operable close control exists.`, evidence: ev }));
    else f.push(mk('2.1.2', 'keyboard-trap', 'fail', loc, { selector: trap.at.selector, snippet: trap.at.snippet, message: `Keyboard trap: focus ${trap.kind === 'stuck' ? 'stays on this element' : `cycles among ${trap.keys.size} element(s)`} and cannot reach the other ${total - trap.keys.size} tabbable element(s); Escape and Shift+Tab did not release it.`, evidence: ev }));
  }
  // --- 2.4.11 / 2.4.12 at mid-page scroll positions (sticky headers/footers)
  const obscured = new Set(f.filter((x) => x.sc === '2.4.11' || x.sc === '2.4.12').map((x) => x.selector));
  f.push(...await runObscureSweep(page, seq, loc, shotDir, tag, obscured));
  // --- 1.4.11 focus indicator contrast (outline / box-shadow ring vs adjacent colours)
  await page.evaluate(() => { const a = document.activeElement; if (a && a.blur) a.blur(); }).catch(() => {});
  const ringSeen = new Set();
  for (const s of seq) {
    if (s.key === 'BODY' || s.isFrame || !s.ring || ringSeen.has(s.key)) continue;
    ringSeen.add(s.key);
    const un = await page.evaluate((i) => window.__w22.walkRing(i), s.idx).catch(() => null);
    if (!un) continue;
    const r = s.ring;
    // outline-style:auto is the browser's own two-tone ring (appearance set by the user agent): not assessed.
    const outlineOn = r.outlineStyle !== 'none' && r.outlineStyle !== 'auto' && r.outlineWidth >= 1 && (parseCssColor(r.outlineColor) || [0, 0, 0, 0])[3] > 0;
    const outlineChanged = outlineOn && (un.outlineStyle !== r.outlineStyle || un.outlineWidth !== r.outlineWidth || un.outlineColor !== r.outlineColor);
    const shadowChanged = r.boxShadow !== 'none' && r.boxShadow !== un.boxShadow;
    let color = null, via = null;
    if (outlineChanged) { color = parseCssColor(r.outlineColor); via = 'outline'; }
    else if (shadowChanged) { const m = /(rgba?\([^)]*\)|color\([^)]*\))/.exec(r.boxShadow); color = m ? parseCssColor(m[1]) : null; via = 'box-shadow'; }
    if (!color) continue;
    const otherChange = (via === 'outline' && shadowChanged) || un.borderColor !== r.borderColor || un.background !== r.background;
    const v = focusIndicatorVerdict({ color, outer: r.outer, own: r.own, offset: via === 'outline' ? r.outlineOffset : 0, otherChange });
    if (!v || v.verdict === 'pass') continue;
    f.push(mk('1.4.11', 'focus-indicator-contrast', v.verdict, loc, { selector: s.selector, snippet: s.snippet,
      message: `Focus indicator (${via} ${via === 'outline' ? r.outlineColor : r.boxShadow}) has ${v.ratio.toFixed(2)}:1 contrast against the adjacent colours (< 3:1)${otherChange ? '; other focus styling also changes, so confirm the indicator is still perceivable' : ' and it is the only visible focus change'}.`,
      evidence: { via, ratio: +v.ratio.toFixed(2), vs_background: +v.vsOuter.toFixed(2), vs_element: v.vsOwn && +v.vsOwn.toFixed(2), outline_offset: r.outlineOffset, other_change: otherChange,
        focused: { outline: `${r.outlineStyle} ${r.outlineWidth}px ${r.outlineColor}`, box_shadow: r.boxShadow }, unfocused: { outline: `${un.outlineStyle} ${un.outlineWidth}px ${un.outlineColor}`, box_shadow: un.boxShadow } } }));
  }
  // --- 2.4.3 focus order anomalies
  const posTab = await page.evaluate(() => window.__w22.positiveTabindex());
  for (const p of posTab.slice(0, 10)) f.push(mk('2.4.3', 'positive-tabindex', 'warn', loc, { selector: p.selector, snippet: p.snippet, message: `tabindex="${p.tabindex}" moves this element ahead of the DOM order in the focus sequence; confirm the resulting order preserves meaning and operability.` }));
  const els = seq.filter((s) => s.key !== 'BODY' && !s.isFrame);
  const anomalies = [];
  for (let i = 1; i < els.length; i++) {
    const a = els[i - 1], b = els[i];
    if (a.key === b.key) continue;
    if (a.domIndex >= 0 && b.domIndex >= 0 && b.domIndex < a.domIndex) anomalies.push({ type: 'dom-order', from: a.selector, to: b.selector });
    else if (b.page.y + b.rect.h <= a.page.y - 4 && b.page.x + b.rect.w <= a.page.x - 4 && !b.modal) anomalies.push({ type: 'visual-backwards', from: a.selector, to: b.selector, from_xy: [Math.round(a.page.x), Math.round(a.page.y)], to_xy: [Math.round(b.page.x), Math.round(b.page.y)] });
  }
  if (anomalies.length) f.push(mk('2.4.3', 'focus-order-anomaly', 'manual', loc, { selector: anomalies[0].to, message: `${anomalies.length} focus-order step(s) move backwards in DOM order or jump up-and-left visually. Verify the sequence preserves meaning.`, evidence: { anomalies: anomalies.slice(0, 10) } }));
  const walk = { presses: seq.length, focused: new Set(els.map((s) => s.key)).size, tabbable_on_page: total, stop: stopReason, focus_visible_checked: checked };
  return { findings: f, walk };
}

// 2.4.11 / 2.4.12 mid-scroll sweep. Tabbing straight down a page rarely lands a target under a sticky
// header, because the browser only scrolls when the target is outside the viewport. A user who has
// scrolled (mouse wheel, find-in-page, a skip link) and then presses Tab can land focus on an element that
// is "in view" but painted over by the sticky header or footer. For each step of the recorded tab order,
// scroll so the target sits flush with the top (then bottom) edge where fixed/sticky content covers it,
// focus the previous stop without scrolling, press Tab, and measure what is visible once scrolling settles.
// scroll-padding (C43) or scripted scroll correction moves the target clear and passes.
const OBSCURE_SWEEP_MAX = 40, OBSCURE_SWEEP_FAILS = 5;
async function runObscureSweep(page, seq, loc, shotDir, tag, already) {
  const f = [];
  if (!(await page.evaluate(() => window.__w22.hasFixedContent()).catch(() => false))) { dbg('focus', 'sweep skipped: no fixed/sticky content'); return f; }
  const done = new Set(); let probes = 0, fails = 0;
  for (let k = 1; k < seq.length && probes < OBSCURE_SWEEP_MAX; k++) {
    if (fails >= OBSCURE_SWEEP_FAILS) {
      f.push(mk('2.4.11', 'focus-obscured-sweep-truncated', 'info', loc, { message: `Mid-scroll focus sweep stopped after ${fails} fully obscured elements; later focus stops were not probed and are likely affected the same way.` }));
      break;
    }
    const a = seq[k - 1], b = seq[k];
    if (a.key === 'BODY' || b.key === 'BODY' || a.isFrame || b.isFrame || a.key === b.key || done.has(b.key) || already.has(b.selector)) continue;
    done.add(b.key);
    for (const edge of ['top', 'bottom']) {
      const setup = await page.evaluate(({ i, p, e }) => window.__w22.obscureSetup(i, p, e), { i: b.idx, p: a.idx, e: edge }).catch(() => null);
      if (!setup) continue;
      probes++;
      await page.keyboard.press('Tab');
      await page.evaluate(() => window.__w22.settleScroll()).catch(() => {});
      const info = await getFocus(page);
      dbg('focus', 'sweep', { target: b.selector, edge, setup, landed: info.selector, samples: info.samples, covered: info.covered, by: info.coveredBy });
      if (info.key !== b.key || !info.samples || !info.covered) continue;
      const full = info.covered === info.samples;
      let shot = null;
      if (shotDir) { shot = path.join(shotDir, `${tag}-obscured-scroll-${info.idx}.png`); await page.screenshot({ path: shot }).catch(() => { shot = null; }); }
      const ev = { method: `page scrolled so the element sat at the ${edge} edge of the viewport, then Tab from the previous focus stop`, scroll_y: setup.scrollY,
        sampled_points: info.samples, covered_points: info.covered, covered_by: info.coveredBy, rect: info.rect, screenshot: shot || undefined };
      if (full) fails++;
      if (full) f.push(mk('2.4.11', 'focus-obscured-fully', 'fail', loc, { selector: info.selector, snippet: info.snippet,
        message: `Focused element is entirely hidden by author-created fixed/sticky content (${info.coveredBy.join(', ')}) when the page is scrolled so the element is at the ${edge} of the viewport and the user tabs to it; the browser does not scroll it clear. Add scroll-padding (C43) or offset the scroll. Exception: content the user opened.`, evidence: ev }));
      f.push(mk('2.4.12', full ? 'focus-obscured-fully' : 'focus-obscured-partially', 'warn', loc, { selector: info.selector, snippet: info.snippet,
        message: `Focused element is ${full ? 'entirely' : 'partly'} hidden by fixed/sticky content (${info.covered}/${info.samples} sample points covered by ${info.coveredBy.join(', ')}) after scrolling it to the ${edge} edge and tabbing to it.`, evidence: ev }));
      break;
    }
  }
  await page.evaluate(() => window.scrollTo(0, 0)).catch(() => {});
  return f;
}

async function runTextIntegrity(page, kind, loc) {
  const f = [];
  await page.evaluate(() => { window.__w22.freezeMotion(); window.scrollTo(0, 0); });
  await page.evaluate(() => window.__w22.textSnapshot());
  if (kind === 'text-spacing') await page.evaluate(() => window.__w22.applyTextSpacing());
  else await page.evaluate(() => window.__w22.applyTextResize(2));
  await page.evaluate(() => window.__w22.raf2());
  const r = await page.evaluate(() => window.__w22.textCompare());
  if (kind === 'text-spacing') await page.evaluate(() => { window.__w22.removeTextSpacing(); });
  if (!r) return f;
  const sc = kind === 'text-spacing' ? '1.4.12' : '1.4.4';
  const what = kind === 'text-spacing' ? 'With WCAG text-spacing overrides (line-height 1.5, paragraph spacing 2em, letter 0.12em, word 0.16em)' : 'With text resized to 200%';
  for (const c of r.clipped.slice(0, 25)) {
    f.push(mk(sc, kind === 'text-spacing' ? 'text-spacing-clipped' : 'resize-text-clipped', kind === 'text-spacing' ? 'fail' : 'warn', loc, { selector: c.selector, snippet: c.snippet,
      message: `${what}, text "${c.text}" is clipped by ${c.clip.by} (overflow ${c.clip.axis === 'y' ? 'vertical' : 'horizontal'} hidden, ${c.clip.px}px cut off).`,
      evidence: { clipped_by: c.clip.by, axis: c.clip.axis, overflow_px: c.clip.px, container_box: c.clip.box } }));
  }
  if (r.clipped.length > 25) f.push(mk(sc, kind + '-more', 'info', loc, { message: `${r.clipped.length - 25} more clipped text element(s) not listed.` }));
  for (const o of r.overlaps.slice(0, 15)) {
    f.push(mk(sc, kind === 'text-spacing' ? 'text-spacing-overlap' : 'resize-text-overlap', 'warn', loc, { selector: o.a, snippet: o.snippet,
      message: `${what}, text "${o.textA}" overlaps text "${o.textB}" (${o.b}); overlapping text is usually unreadable.`, evidence: { other: o.b } }));
  }
  return f;
}

async function runReflow(context, url, opts, loc, shotDir, tag) {
  const page = await context.newPage();
  const f = [];
  try {
    await page.setViewportSize({ width: 320, height: 256 });
    await page.goto(url, { waitUntil: 'load', timeout: opts.timeout });
    await settle(page);
    const r = await page.evaluate(() => window.__w22.reflow());
    let shot = null;
    if (shotDir) { shot = path.join(shotDir, `${tag}-reflow-320.png`); await page.screenshot({ path: shot, fullPage: true }); }
    const nonExempt = r.offenders.filter((o) => !o.exempt);
    const exempt = r.offenders.filter((o) => o.exempt);
    const ev = (o) => ({ viewport: '320x256', client_width: r.clientWidth, scroll_width: r.scrollWidth, left: o.left, right: o.right, width: o.width, screenshot: shot || undefined });
    if (r.scrolls) {
      for (const o of nonExempt.slice(0, 10)) f.push(mk('1.4.10', 'reflow-horizontal-scroll', 'fail', loc, { selector: o.selector, snippet: o.snippet,
        message: `At 320 CSS px wide the page scrolls horizontally (${r.scrollWidth}px content); this element extends to x=${o.right}px.`, evidence: ev(o) }));
      if (!nonExempt.length && exempt.length) f.push(mk('1.4.10', 'reflow-exempt-content', 'manual', loc, { selector: exempt[0].selector, snippet: exempt[0].snippet,
        message: `At 320 CSS px the page scrolls horizontally only because of ${[...new Set(exempt.map((o) => o.exempt))].join(', ')} content. Confirm it needs two-dimensional layout (data table, map, diagram, video...).`, evidence: ev(exempt[0]) }));
      if (!r.offenders.length) f.push(mk('1.4.10', 'reflow-horizontal-scroll', 'fail', loc, { message: `At 320 CSS px wide the page scrolls horizontally (${r.scrollWidth}px > ${r.clientWidth}px).`, evidence: { client_width: r.clientWidth, scroll_width: r.scrollWidth, screenshot: shot || undefined } }));
    } else {
      for (const o of nonExempt.filter((x) => x.straddles).slice(0, 10)) f.push(mk('1.4.10', 'reflow-content-clipped', 'warn', loc, { selector: o.selector, snippet: o.snippet,
        message: `At 320 CSS px this element runs past the right edge (to x=${o.right}px) but horizontal scrolling is suppressed, so content may be cut off.`, evidence: ev(o) }));
    }
  } finally { await page.close(); }
  return f;
}

// 1.4.11: form-control boundaries against the adjacent background.
async function runNonTextContrast(page, loc) {
  const r = await page.evaluate(() => window.__w22.nonTextContrast());
  const f = [];
  for (const c of r.results) {
    const v = controlBoundaryVerdict({ borderRatio: c.borderRatio, shadowRatio: c.shadowRatio, bgRatio: c.bgRatio });
    if (v === 'pass') continue;
    const parts = [];
    parts.push(c.borderRatio !== null ? `border ${c.borderRatio}:1` : 'no border');
    if (c.shadowRatio !== null) parts.push(`box-shadow ${c.shadowRatio}:1`);
    parts.push(`own background ${c.bgRatio}:1`);
    f.push(mk('1.4.11', v === 'fail' ? 'ui-boundary-contrast' : 'ui-boundary-contrast-maybe', v, loc, { selector: c.selector, snippet: c.snippet,
      message: v === 'fail'
        ? `The ${c.kind}'s visual boundary is below 3:1 against the adjacent background ${c.adjacent} (${parts.join(', ')}), so the control cannot be identified by its shape.`
        : `The ${c.kind} has a distinct background but nothing reaches 3:1 against the adjacent background ${c.adjacent} (${parts.join(', ')}). If the boundary is not needed to identify the control this passes; confirm.`,
      evidence: { border_ratio: c.borderRatio, shadow_ratio: c.shadowRatio, background_ratio: c.bgRatio, adjacent: c.adjacent, colours: c.colours, kind: c.kind } }));
  }
  if (r.unknown) f.push(mk('1.4.11', 'ui-boundary-unresolved', 'manual', loc, { message: `${r.unknown} form control(s) sit on an image or gradient background; check their boundaries have 3:1 contrast against it.` }));
  return f;
}

// 2.1.2: open each dialog trigger with Enter/Space and try to leave the dialog by standard means.
async function runDialogProbes(page, url, opts, loc) {
  const f = []; const probes = [];
  const found = await page.evaluate((h) => window.__w22.dialogTriggers(h), !!opts.actionsAllowed);
  const triggers = found.triggers;
  dbg('dialogs', 'triggers', found);
  if (found.skipped) f.push(mk('2.1.2', 'dialog-probe-skipped', 'manual', loc, { selector: found.hidden[0] || null,
    message: `The page holds a hidden dialog (${found.hidden.join(', ')}) and ${found.skipped} plain button(s) that may open it, but buttons are not activated on remote sites without --probe-actions. Open the dialog manually and check that Tab, Shift+Tab and Escape (or a keyboard-reachable close control) can move focus out of it.`,
    evidence: { hidden_dialogs: found.hidden, candidate_buttons: found.skipped } }));
  const reload = async () => { await page.goto(url, { waitUntil: 'load', timeout: opts.timeout }); await settle(page); await page.evaluate(() => window.__w22.freezeMotion()); };
  const state = () => page.evaluate(() => window.__w22.dialogState());
  const pause = () => page.evaluate(() => window.__w22.raf2()).then(() => page.waitForTimeout(120));
  for (const t of triggers) {
    await reload();
    const before = await page.evaluate(() => window.__w22.openDialogs().map((d) => window.__w22.sel(d)));
    let dlg = null;
    for (const key of ['Enter', ' ']) {
      if (!(await page.evaluate((s) => window.__w22.focusSel(s), t.selector))) break;
      await page.keyboard.press(key === ' ' ? 'Space' : key);
      await pause();
      if (page.url().split('#')[0] !== url.split('#')[0]) { await reload(); break; }
      dlg = await page.evaluate(({ s, b }) => window.__w22.markDialog(s, b), { s: t.selector, b: before });
      if (dlg) break;
    }
    if (!dlg) { probes.push({ trigger: t.selector, opened: false }); continue; }
    let st = await state();
    // Move focus into the dialog if the script did not.
    for (let i = 0; i < 10 && st.open && !st.inside; i++) { await page.keyboard.press('Tab'); st = await state(); }
    if (!st.open || !st.inside) { probes.push({ trigger: t.selector, opened: true, entered: false }); continue; }
    const n = dlg.tabbables + 3; let released = null;
    for (let i = 0; i < n && !released; i++) { await page.keyboard.press('Tab'); st = await state(); if (!st.open || !st.inside) released = 'Tab'; }
    if (!released) { await page.keyboard.press('Escape'); await pause(); st = await state(); if (!st.open || !st.inside) released = 'Escape'; }
    if (!released) for (let i = 0; i < n && !released; i++) { await page.keyboard.press('Shift+Tab'); st = await state(); if (!st.open || !st.inside) released = 'Shift+Tab'; }
    if (!released) {
      for (const c of dlg.closers) {
        await page.evaluate((s) => window.__w22.focusSel(s), c.selector);
        await page.keyboard.press('Enter'); await pause(); st = await state();
        if (!st.open || !st.inside) { released = `Enter on "${c.name}"`; break; }
      }
    }
    probes.push({ trigger: t.selector, opened: true, entered: true, dialog: dlg.selector, released });
    dbg('dialogs', 'probe', probes[probes.length - 1]);
    const ev = { trigger: t.selector, trigger_reason: t.why, dialog: dlg.selector, tabbable_in_dialog: dlg.tabbables, tried: ['Tab', 'Escape', 'Shift+Tab', 'Enter on close/cancel controls'], close_controls: dlg.closers.map((c) => c.name), released_by: released, instructions: dlg.documented };
    if (released) continue;
    if (dlg.documented) f.push(mk('2.1.2', 'dialog-focus-contained-documented', 'manual', loc, { selector: dlg.selector, snippet: dlg.snippet,
      message: `Dialog opened by ${t.selector} keeps focus against Tab, Escape, Shift+Tab and its close controls, but it documents a way out ("${dlg.documented}"). Verify that method works.`, evidence: ev }));
    else f.push(mk('2.1.2', 'keyboard-trap-dialog', 'fail', loc, { selector: dlg.selector, snippet: dlg.snippet,
      message: `Keyboard trap in the dialog opened by ${t.selector} (${t.why}): focus cannot leave by Tab, Escape, Shift+Tab${dlg.closers.length ? ' or its close controls' : ' and it has no keyboard-reachable close control'}, and no alternative is documented.`, evidence: ev }));
  }
  if (triggers.length) await reload(); // restore page state for later checks
  return { findings: f, probes };
}

// 2.2.2: watch the page without interacting. Slow rotators (one change inside the window) get a longer look,
// up to max(2 x --observe, 12 s), so a 4-5 s interval is seen at least twice.
async function runAutoUpdate(page, opts, loc) {
  const n = await page.evaluate(() => window.__w22.autoStart());
  dbg('auto-update', 'start', n);
  await page.waitForTimeout(opts.observe);
  const cap = Math.max(opts.observe * 2, 12000); let waited = opts.observe;
  while (waited < cap) {
    const pend = await page.evaluate(() => window.__w22.autoPeek());
    if (!pend.length) break;
    dbg('auto-update', 'extending observation', { waited, pending: pend });
    const step = Math.min(1000, cap - waited);
    await page.waitForTimeout(step); waited += step;
  }
  const res = await page.evaluate(() => window.__w22.autoStop());
  dbg('auto-update', 'observed', { waited, res });
  const f = [];
  for (const r of res) {
    if (!r.qualifies || r.pause) continue;
    const what = r.source === 'css-animation'
      ? `This element runs a ${r.iterations === 'infinite' ? 'looping' : 'long'} CSS animation ("${r.animation}")`
      : `Content in this ${r.role || (r.source === 'named-region' ? 'carousel/marquee' : 'page')} region changed on its own ${r.episodes} time(s) over ${r.span}s`;
    f.push(mk('2.2.2', 'auto-update-no-pause', 'warn', loc, { selector: r.selector, snippet: r.snippet,
      message: `${what} with no interaction, and no pause/stop control was found. Moving or auto-updating content that starts automatically and lasts more than 5 seconds needs a mechanism to pause, stop or hide it.`,
      evidence: { observed_ms: waited, detected_by: r.source, change_windows: r.changes, episodes: r.episodes, span_s: r.span, aria_live: r.live,
        ...(r.source === 'css-animation' ? { animation: r.animation, duration_ms: r.duration_ms, iterations: r.iterations } : {}) } }));
  }
  return f;
}

// 4.1.3: activate buttons (no navigation, non-GET requests blocked) and look for new text outside live regions.
async function runStatusProbe(page, url, opts, loc) {
  const f = [];
  const cands = await page.evaluate(() => window.__w22.statusCandidates());
  dbg('status-messages', 'candidates', { cands, actionsAllowed: !!opts.actionsAllowed });
  if (!cands.length) return f;
  if (!opts.actionsAllowed) {
    f.push(mk('4.1.3', 'status-messages-not-probed', 'manual', loc, { selector: cands[0],
      message: `${cands.length} button(s) were not activated because the target is a remote site (activation is opt-in with --probe-actions). Activate them manually and check that any status message they produce is in a role="status"/"alert"/"log" or aria-live region.`,
      evidence: { buttons: cands, note: 'rerun with --probe-actions only where clicking these buttons is safe' } }));
    return f;
  }
  const block = (route) => (['GET', 'HEAD', 'OPTIONS'].includes(route.request().method()) ? route.continue() : route.abort());
  const onDialog = (d) => d.dismiss().catch(() => {});
  await page.route('**/*', block); page.on('dialog', onDialog);
  const reported = new Set();
  const reload = async () => { await page.goto(url, { waitUntil: 'load', timeout: opts.timeout }); await settle(page); };
  try {
    for (const sel of cands) {
      await page.evaluate(() => window.__w22.statusArm());
      const ok = await page.evaluate((s) => window.__w22.statusClick(s), sel);
      if (!ok) continue;
      await page.waitForTimeout(600);
      if (page.url().split('#')[0] !== url.split('#')[0]) { await reload(); continue; }
      await page.evaluate(PAGE_LIB);
      const changes = await page.evaluate((s) => window.__w22.statusCollect(s), sel);
      dbg('status-messages', 'requested content skipped', await page.evaluate(() => { const x = window.__w22.statusSkipped || []; window.__w22.statusSkipped = []; return x; }));
      for (const c of changes) {
        if (reported.has(c.selector)) continue;
        reported.add(c.selector);
        const nav = c.requested === 'nav-label';
        f.push(mk('4.1.3', 'status-message-not-announced', nav ? 'manual' : 'warn', loc, { selector: c.selector, snippet: c.snippet,
          message: nav ? `Activating ${sel} ("${c.label}") changed the text of this element to "${c.text}" without moving focus. The control looks like navigation (previous/next/more), so this may be the content the user requested rather than a status message; if it reports a result (e.g. "Saved", "3 results", an error), put it in a role="status"/"alert"/"log" or aria-live region.`
            : `Activating ${sel} changed the text of this element to "${c.text}" without moving focus, but it is not in a role="status"/"alert"/"log" or aria-live region, so screen readers will not announce the message.`,
          evidence: { trigger: sel, text: c.text, previous_text: c.before, note: 'simulated activation; form submission and non-GET requests were blocked', ...(nav ? { trigger_label: c.label, downgraded: 'navigation-style control swapped existing content outside its own component' } : {}) } }));
      }
    }
  } finally {
    page.off('dialog', onDialog);
    await page.unroute('**/*', block).catch(() => {});
    await reload().catch(() => {});
  }
  return f;
}

// 3.3.7 within one page: same data asked again in a different step section.
const keyText = (k) => (k.startsWith('purpose ') ? `The same information (${k.slice(8)}, inferred from the field's type, name or label)` : k);
export function redundantEntryFindings(pages, mkf = mk) {
  // pages: [{loc, url, fields, isStep}] in visit order. Within-page comparisons use sections; across pages only step pages.
  const out = [];
  const seenPages = {};
  for (const p of pages) {
    const seen = {};
    for (const fld of p.fields) {
      if (fld.confirm) continue;
      // Inferred-purpose keys only link fields in the same <form> (or on a step page): a newsletter e-mail box in
      // the footer and a contact form's e-mail field are separate processes.
      const linked = (k, v) => v && (!k.startsWith('purpose ') || v.form === fld.form);
      let hit = null;
      for (const k of fld.keys) { const v = (seen[k] || []).find((x) => linked(k, x)); if (v) { hit = [k, v]; break; } }
      for (const k of fld.keys) (seen[k] ??= []).push(fld);
      if (hit && hit[1].section !== fld.section && !fld.exempt && !fld.copyOption) {
        out.push(mkf('3.3.7', 'redundant-entry', 'warn', p.loc, { selector: fld.selector, snippet: fld.snippet,
          message: `${keyText(hit[0])} was already requested in an earlier step on this page (${hit[1].selector}) and is asked again with no auto-populated value or option to select it. Exceptions: re-entry is essential, needed for security, or the earlier value is no longer valid.`,
          evidence: { key: hit[0], first: hit[1].selector } }));
        continue;
      }
      if (p.isStep && !hit) {
        const prev = fld.keys.map((k) => [k, seenPages[k]]).find(([, v]) => v && v.page !== p);
        if (prev && !fld.exempt && !fld.copyOption) {
          out.push(mkf('3.3.7', 'redundant-entry', 'warn', p.loc, { selector: fld.selector, snippet: fld.snippet,
            message: `${keyText(prev[0])} was already requested on an earlier step page (${prev[1].where}) and is asked again with no auto-populated value or option to select it. Exceptions: re-entry is essential, needed for security, or the earlier value is no longer valid.`,
            evidence: { key: prev[0], first_page: prev[1].where, first: prev[1].selector } }));
        }
      }
    }
    if (p.isStep) for (const fld of p.fields) if (!fld.confirm) for (const k of fld.keys) seenPages[k] ??= { page: p, where: p.loc.file || p.url, selector: fld.selector };
  }
  return out;
}

// ---------------------------------------------------------------- orchestration
// Let late redirects, client rendering and web fonts finish (bounded), then install the page library.
async function settle(page) {
  await page.waitForLoadState('networkidle', { timeout: 4000 }).catch(() => {});
  await page.evaluate(() => document.fonts && document.fonts.ready).catch(() => {});
  await page.evaluate(PAGE_LIB);
}

async function auditPage(context, helper, deps, url, opts, loc, shotDir, tag, ctx) {
  const t0 = Date.now();
  const page = await context.newPage();
  const findings = []; const errors = []; let help = null; let links = []; let title = ''; let walk = null; let entry = null; let dialogs = null;
  const has = (c) => opts.selection.checks.has(c);
  // Each check runs under a time budget (--check-timeout). A check that overruns has usually wedged the
  // page (a pending evaluate never settles), so the page is closed and its remaining checks are skipped.
  const timings = {}; let stalled = null;
  const guard = async (name, fn) => {
    if (stalled) { errors.push({ check: name, error: `skipped: page abandoned after ${stalled} timed out` }); return null; }
    const c0 = Date.now(); let timer;
    if (debugOn('crawl')) dbg('crawl', 'check start', { check: name, visibility: await page.evaluate(() => document.visibilityState).catch((e) => 'eval-error: ' + String(e.message).slice(0, 60)) });
    const budget = new Promise((_, rej) => { timer = setTimeout(() => rej(Object.assign(new Error(`timed out after ${Math.round(opts.checkTimeout / 1000)}s`), { stall: true })), opts.checkTimeout); });
    try { const r = await Promise.race([(async () => { await page.evaluate(PAGE_LIB); return fn(); })(), budget]); if (Array.isArray(r)) findings.push(...r); return r; }
    catch (e) {
      errors.push({ check: name, error: String(e && e.message || e).split('\n')[0] });
      if (e && e.stall) { stalled = name; dbg('crawl', 'check timed out', { url, check: name }); await page.close().catch(() => {}); }
      return null;
    } finally { clearTimeout(timer); timings[name] = (timings[name] || 0) + Date.now() - c0; }
  };
  try {
    const resp = await page.goto(url, { waitUntil: 'load', timeout: opts.timeout });
    if (resp && resp.status() >= 400) throw new Error(`HTTP ${resp.status()} for ${url}`);
    await settle(page);
    title = await page.title();
    await page.evaluate(PAGE_LIB);
    links = await page.evaluate(() => window.__w22.links()).catch(() => []);
    if (shotDir) await page.screenshot({ path: path.join(shotDir, `${tag}-page.png`), fullPage: true }).catch(() => {});
    let contrastQueue = [];
    if (has('axe')) await guard('axe', async () => { const r = await runAxe(page, deps, opts, loc, ctx); contrastQueue = r.contrastQueue; return r.findings; });
    if (has('contrast-sample') && contrastQueue.length) await guard('contrast-sample', () => runContrastSample(page, helper, contrastQueue, opts, loc));
    if (has('auto-update')) await guard('auto-update', () => runAutoUpdate(page, opts, loc));
    if (has('target-size')) await guard('target-size', () => runTargetSize(page, loc));
    if (has('non-text-contrast')) await guard('non-text-contrast', () => runNonTextContrast(page, loc));
    if (has('auth')) {
      await guard('auth', () => runAuth(page, loc));
      entry = await guard('auth', () => page.evaluate(() => window.__w22.entryFields()));
      dbg('auth', 'entry fields ' + url, entry);
    }
    if (has('consistent-help')) { help = await guard('consistent-help', () => page.evaluate(() => window.__w22.helpMechanisms())); dbg('consistent-help', url, help); }
    if (has('status-messages')) await guard('status-messages', () => runStatusProbe(page, url, opts, loc));
    if (has('focus')) await guard('focus', async () => { const r = await runFocusWalk(page, helper, opts, loc, shotDir, tag); walk = r.walk; return r.findings; });
    if (has('dialogs')) await guard('dialogs', async () => { const r = await runDialogProbes(page, url, opts, loc); dialogs = r.probes; return r.findings; });
    if ((has('text-spacing') || has('resize-text')) && !stalled) {
      await page.goto(url, { waitUntil: 'load', timeout: opts.timeout });
      await settle(page);
      if (has('text-spacing')) await guard('text-spacing', () => runTextIntegrity(page, 'text-spacing', loc));
      if (has('resize-text')) await guard('resize-text', () => runTextIntegrity(page, 'resize-text', loc));
    }
    if (has('reflow')) await guard('reflow', () => runReflow(context, url, opts, loc, shotDir, tag));
  } finally { await page.close().catch(() => {}); }
  if (walk && dialogs && dialogs.length) walk.dialog_probes = dialogs;
  return { url, title, findings, errors, help, links, walk, entry, runtime_ms: Date.now() - t0, check_ms: timings };
}

// Crawl de-duplication key: no fragment; for the local static server also no query string and
// "/dir/" == "/dir/index.html".
export function crawlKey(href, local) {
  const u = new URL(href); u.hash = '';
  if (local) { u.search = ''; if (u.pathname.endsWith('/')) u.pathname += 'index.html'; }
  return u.href;
}
const SKIP_EXT = /\.(pdf|zip|gz|tgz|png|jpe?g|gif|webp|svg|ico|mp[34]|webm|mov|avi|docx?|xlsx?|pptx?|csv|json|xml|txt|css|js|woff2?|ttf|dmg|exe)$/i;

export async function audit(opts) {
  const deps = loadDeps();
  const target = await resolveTarget(opts.target);
  // Button activation: always for local files/dirs (served on 127.0.0.1), opt-in for remote targets.
  opts.actionsAllowed = !!opts.probeActions || !!target.origin;
  const browser = await deps.chromium.launch({ headless: true });
  const ctx = { axeVersion: null, axeCovered: null };
  const pages = []; const findings = [];
  try {
    const context = await browser.newContext({ viewport: opts.viewport, deviceScaleFactor: 1, bypassCSP: true, ignoreHTTPSErrors: false });
    context.setDefaultTimeout(opts.timeout);
    const helper = await context.newPage();
    await helper.evaluate(HELPER_LIB);
    if (opts.screenshots) fs.mkdirSync(opts.screenshots, { recursive: true });
    const queue = [...target.seeds]; const seen = new Set(queue.map((u) => crawlKey(u, !!target.origin)));
    const origin = new URL(queue[0]).origin;
    let ok = 0, attempts = 0;
    while (queue.length && ok < opts.pages && attempts < opts.pages * 4 + 4) {
      attempts++;
      const url = queue.shift();
      const loc = target.loc(url);
      let res;
      try {
        res = await auditPage(context, helper, deps, url, opts, loc, opts.screenshots, `p${pages.length + 1}`, ctx);
      } catch (e) {
        res = { url, title: '', findings: [], errors: [{ check: 'navigation', error: String(e.message || e).split('\n')[0] }], help: null, links: [], walk: null, entry: null, runtime_ms: 0 };
      }
      pages.push({ ...res, loc });
      dbg('crawl', 'audited ' + url, { links: res.links.length, errors: res.errors });
      if (!res.errors.some((e) => e.check === 'navigation')) ok++;
      findings.push(...res.findings);
      for (const l of res.links) {
        let u; try { u = new URL(l); } catch { continue; }
        if (u.origin !== origin || !/^https?:$/.test(u.protocol) || SKIP_EXT.test(u.pathname)) continue;
        u.hash = ''; const k = crawlKey(u.href, !!target.origin);
        if (!seen.has(k)) { seen.add(k); queue.push(target.origin ? k : u.href); }
      }
    }
    // 3.2.6 across pages
    if (opts.selection.checks.has('consistent-help')) {
      const hp = pages.filter((p) => p.help && p.help.order.length).map((p) => ({ loc: p.loc, url: p.url, order: p.help.order, zones: p.help.zones, items: p.help.items }));
      const zoneName = { 'before-main': 'before the main content', main: 'inside the main content', 'after-main': 'after the main content' };
      for (const c of helpOrderFindings(hp)) {
        const pa = c.a.loc.file || c.a.url, pb = c.b.loc.file || c.b.url;
        const first = c.kind === 'position' ? c.moved[0] : c.orderB[0];
        findings.push(mk('3.2.6', 'help-order-inconsistent', 'warn', c.b.loc, { selector: (c.b.items.find((i) => i.kind === first) || {}).selector || null,
          message: c.kind === 'position'
            ? `Help mechanisms (${c.moved.join(', ')}) are in a different place relative to the other page content than on ${pa}: ${zoneName[c.zonesA[c.moved[0]]]} there, ${zoneName[c.zonesB[c.moved[0]]]} here.`
            : `Help mechanisms appear in a different relative order than on ${pa}: [${c.orderA.join(', ')}] vs [${c.orderB.join(', ')}].`,
          evidence: { page_a: pa, order_a: c.orderA, page_b: pb, order_b: c.orderB, conflict: c.kind, ...(c.kind === 'position' ? { zones_a: c.zonesA, zones_b: c.zonesB } : {}) } }));
      }
      if (pages.length === 1 && hp.length === 1) findings.push(mk('3.2.6', 'help-single-page', 'manual', pages[0].loc, { message: `Help mechanisms found (${hp[0].order.join(', ')}); 3.2.6 needs a comparison across pages (use --pages N).`, evidence: { items: hp[0].items } }));
    }
    // 3.3.7 within pages (step sections) and across step pages, in crawl order
    if (opts.selection.checks.has('auth')) {
      const ep = pages.filter((p) => p.entry).map((p) => ({ loc: p.loc, url: p.url, fields: p.entry.fields, isStep: p.entry.isStep }));
      const red = redundantEntryFindings(ep);
      const warned = new Set(red.map((r) => (r.file || r.url) + '\u0000' + r.selector));
      // fields that are pre-filled, selectable, security-related or offer "same as" do not need a manual re-entry check either
      for (const p of ep) for (const fl of p.fields) if (fl.exempt || fl.copyOption) warned.add((p.loc.file || p.loc.url) + '\u0000' + fl.selector);
      for (let i = findings.length - 1; i >= 0; i--) {
        const x = findings[i];
        if (x.rule === 'possible-redundant-entry' && warned.has((x.file || x.url) + '\u0000' + x.selector)) findings.splice(i, 1);
      }
      findings.push(...red);
    }
    const browserVersion = browser.version();
    await context.close();
    return { pages, findings: finalize(findings, opts), versions: { ...deps.versions, chromium: browserVersion, axe_runtime: ctx.axeVersion }, axeCovered: ctx.axeCovered };
  } finally {
    await browser.close().catch(() => {});
    await target.close();
  }
}

function finalize(findings, opts) {
  const rank = LEVEL_RANK[opts.level];
  const seen = new Map(); const uniq = [];
  for (const f of findings) {
    if (f.rule.startsWith('axe:') || !f.selector) { uniq.push(f); continue; }
    const k = [f.file || f.url, f.sc, f.rule, f.selector].join('\u0000');
    const first = seen.get(k);
    if (first) { first.evidence = { ...(first.evidence || {}), occurrences: ((first.evidence && first.evidence.occurrences) || 1) + 1 }; continue; }
    seen.set(k, f); uniq.push(f);
  }
  let out = uniq.filter((f) => !f.level || LEVEL_RANK[f.level] <= rank);
  if (opts.selection.scs) out = out.filter((f) => f.sc && opts.selection.scs.has(f.sc));
  const sev = { fail: 0, warn: 1, manual: 2, info: 3 };
  return out.sort((a, b) => (sev[a.severity] - sev[b.severity]) || scCompare(a.sc || '9', b.sc || '9'));
}

// SC coverage of this run: {checks_sc: {check: [sc...]}, sc_covered: [sc...]} limited to the tested level and --rules SCs.
export function coverage(opts, axeCovered = null) {
  const rank = LEVEL_RANK[opts.level];
  const keep = (sc) => SC[sc] && SC[sc][0] && LEVEL_RANK[SC[sc][0]] <= rank && (!opts.selection.scs || opts.selection.scs.has(sc));
  const checks_sc = {};
  for (const c of opts.selection.checks) {
    const list = c === 'axe' ? [...new Set(axeCovered || [])] : CHECKS[c] || [];
    checks_sc[c] = list.filter(keep).sort(scCompare);
  }
  const sc_covered = [...new Set(Object.values(checks_sc).flat())].sort(scCompare);
  return { checks_sc, sc_covered };
}

export function envelope(opts, result, startedAt) {
  const by_sc = {}; const by_severity = { fail: 0, warn: 0, manual: 0, info: 0 };
  for (const f of result.findings) {
    by_severity[f.severity]++;
    const k = f.sc || 'none';
    by_sc[k] ??= { fail: 0, warn: 0, manual: 0, info: 0 }; by_sc[k][f.severity]++;
  }
  const sortedSc = Object.fromEntries(Object.keys(by_sc).sort(scCompare).map((k) => [k, by_sc[k]]));
  return {
    meta: { tool: TOOL, version: VERSION, wcag: WCAG, target: opts.target, date: startedAt.toISOString(), level: opts.level,
      viewport: `${opts.viewport.width}x${opts.viewport.height}`, checks: [...opts.selection.checks],
      engine: result.versions, axe_sc_covered: result.axeCovered ? [...new Set(result.axeCovered)].sort(scCompare) : null,
      ...coverage(opts, result.axeCovered),
      pages: result.pages.map((p) => ({ ...p.loc, title: p.title, runtime_ms: p.runtime_ms, check_ms: p.check_ms, keyboard_walk: p.walk || undefined, errors: p.errors.length ? p.errors : undefined })) },
    summary: { by_sc: sortedSc, by_severity },
    findings: result.findings,
  };
}

export function textReport(env) {
  const L = [];
  const m = env.meta;
  L.push(`${m.tool} ${m.version} - WCAG ${m.wcag}, level ${m.level}, viewport ${m.viewport}`);
  L.push(`Engine: Chromium ${m.engine.chromium}, Playwright ${m.engine.playwright}, axe-core ${m.engine.axe}`);
  L.push(`Checks: ${m.checks.join(', ')}`);
  for (const p of m.pages) {
    const where = p.file || p.url;
    L.push('');
    L.push(`== ${where}${p.title ? `  "${p.title}"` : ''}  (${(p.runtime_ms / 1000).toFixed(1)}s)`);
    if (p.keyboard_walk) L.push(`   keyboard walk: ${p.keyboard_walk.presses} Tab presses, ${p.keyboard_walk.focused} distinct stops of ${p.keyboard_walk.tabbable_on_page} tabbable, stop=${p.keyboard_walk.stop}`);
    for (const e of p.errors || []) L.push(`   ERROR in ${e.check}: ${e.error}`);
    const fs_ = env.findings.filter((f) => (f.file || f.url) === where);
    for (const f of fs_) {
      L.push(`   ${f.severity.toUpperCase().padEnd(6)} ${String(f.sc || '-').padEnd(6)} ${f.rule}${f.selector ? `  ${f.selector}` : ''}`);
      L.push(`          ${f.message}`);
    }
    if (!fs_.length) L.push('   no findings');
  }
  const s = env.summary.by_severity;
  L.push('');
  L.push(`Summary: ${s.fail} fail, ${s.warn} warn, ${s.manual} manual, ${s.info} info across ${m.pages.length} page(s).`);
  L.push('Automated checks cover only part of WCAG 2.2; a clean run is not a conformance claim.');
  return L.join('\n');
}

export async function main(argv) {
  let opts;
  try { opts = parseArgs(argv); } catch (e) {
    if (e instanceof UsageError) { process.stderr.write(`error: ${e.message}\n\n${HELP_TEXT}\n`); return 2; }
    throw e;
  }
  if (opts.help) { process.stdout.write(HELP_TEXT + '\n'); return 0; }
  const started = new Date();
  let result;
  try { result = await audit(opts); } catch (e) {
    if (e instanceof UsageError) { process.stderr.write(`error: ${e.message}\n`); return 2; }
    process.stderr.write(`error: ${e.message}\n`); return 2;
  }
  const env = envelope(opts, result, started);
  if (result.pages.every((p) => p.errors.some((x) => x.check === 'navigation'))) {
    process.stderr.write(`error: could not load any page: ${result.pages.map((p) => p.errors[0].error).join('; ')}\n`);
    if (opts.json) process.stdout.write(JSON.stringify(env, null, 2) + '\n');
    return 2;
  }
  process.stdout.write((opts.json ? JSON.stringify(env, null, 2) : textReport(env)) + '\n');
  return env.summary.by_severity.fail > 0 ? 1 : 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(fs.realpathSync(process.argv[1])).href) {
  main(process.argv.slice(2)).then((code) => { process.exitCode = code; }, (e) => { process.stderr.write(`error: ${e.stack || e}\n`); process.exitCode = 2; });
}
