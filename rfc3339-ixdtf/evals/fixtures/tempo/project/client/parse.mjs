// Tempo web client: parse timestamps returned by the Tempo API.
//
//   node client/parse.mjs '2026-03-14T09:30:00-04:00[America/New_York]'

import { fileURLToPath } from 'node:url';

const KNOWN_KEYS = new Set(['u-ca']);

const DATE = '(\\d{4})-(\\d{2})-(\\d{2})';
const TIME = 'T(\\d{2}):(\\d{2}):(\\d{2})(?:\\.(\\d+))?';
const OFFSET = '(Z|[+-]\\d{2}:\\d{2})';
const SUFFIX = '((?:\\[[^\\[\\]]+\\])*)';
const STAMP_RE = new RegExp(DATE + TIME + OFFSET + SUFFIX + '$');

const KEY_RE = /^[a-z_][a-z0-9_-]*$/;
const VALUES_RE = /^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$/;
const MAX_MDAY = 31;

function parseOffset(off) {
  if (off === 'Z') return 0;
  const sign = off[0] === '-' ? -1 : 1;
  const hh = Number(off.slice(1, 3));
  const mm = Number(off.slice(4, 6));
  if (hh > 23 || mm > 59) throw new RangeError(`offset out of range: ${off}`);
  return sign * (hh * 60 + mm);
}

export function parseSuffix(suffix) {
  const out = { timeZone: null, timeZoneCritical: false, calendar: null, tags: {} };
  const parts = suffix.match(/\[[^\[\]]+\]/g) ?? [];
  for (const [i, raw] of parts.entries()) {
    let body = raw.slice(1, -1);
    const critical = body.startsWith('!');
    if (critical) body = body.slice(1);

    const eq = body.indexOf('=');
    if (eq < 0) {
      if (i !== 0) throw new RangeError(`time zone must be the first suffix: ${raw}`);
      out.timeZone = body;
      out.timeZoneCritical = critical;
      continue;
    }

    const key = body.slice(0, eq);
    const value = body.slice(eq + 1);
    if (!KEY_RE.test(key) || !VALUES_RE.test(value)) {
      throw new RangeError(`malformed suffix tag: ${raw}`);
    }
    if (key.startsWith('_')) throw new RangeError(`experimental key not accepted: ${key}`);
    if (!KNOWN_KEYS.has(key)) continue;
    out.tags[key] = value;
  }
  out.calendar = out.tags['u-ca'] ?? null;
  return out;
}

function zoneOffsetMinutes(epochMs, timeZone) {
  const zdt = Temporal.Instant.fromEpochMilliseconds(epochMs).toZonedDateTimeISO(timeZone);
  return zdt.offsetNanoseconds / 60e9;
}

export function parseTimestamp(text) {
  const m = STAMP_RE.exec(text);
  if (!m) throw new RangeError(`invalid timestamp: ${JSON.stringify(text)}`);
  const [, y, mo, d, h, mi, s, frac = '', off, suffix] = m;
  const [year, month, day, hour, minute, second] = [y, mo, d, h, mi, s].map(Number);

  if (month < 1 || month > 12 || day < 1 || day > MAX_MDAY) {
    throw new RangeError(`date out of range: ${text}`);
  }
  if (hour > 23 || minute > 59 || second > 60) {
    throw new RangeError(`time out of range: ${text}`);
  }

  const offsetMinutes = parseOffset(off);
  const millis = Number((frac + '000').slice(0, 3));
  const wall = Date.UTC(year, month - 1, day, hour, minute, Math.min(second, 59), millis);
  const epochMs = wall - offsetMinutes * 60_000;

  const ext = parseSuffix(suffix);
  if (ext.timeZone) {
    let zoneOffset = null;
    try {
      zoneOffset = zoneOffsetMinutes(epochMs, ext.timeZone);
    } catch (err) {
      if (ext.timeZoneCritical) throw new RangeError(`unknown time zone: ${ext.timeZone}`);
      ext.timeZone = null;
    }
    const offsetKnown = off !== 'Z' && off !== '-00:00';
    if (ext.timeZoneCritical && offsetKnown && zoneOffset !== offsetMinutes) {
      throw new RangeError(`offset ${off} inconsistent with [!${ext.timeZone}]`);
    }
  }

  return {
    epochMs,
    iso: new Date(epochMs).toISOString(),
    offsetMinutes,
    leapSecond: second === 60,
    timeZone: ext.timeZone,
    calendar: ext.calendar,
    tags: ext.tags,
  };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  for (const arg of process.argv.slice(2)) {
    try {
      console.log(JSON.stringify(parseTimestamp(arg)));
    } catch (err) {
      console.log(JSON.stringify({ input: arg, error: err.message }));
    }
  }
}
