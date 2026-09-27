#!/usr/bin/env python3
"""Turn results/consumers.jsonl into GO.md §1 matrix rows and §2 tables (writes results/tables.md)."""
import json, subprocess, os, datetime as D
from collections import defaultdict, OrderedDict
RFCDT = os.path.expanduser('~/.claude/skills/rfc3339-ixdtf/scripts/rfcdt.py')
rows = [json.loads(l) for l in open('results/consumers.jsonl') if '"kind": "parse"' in l or '"kind":"parse"' in l]
apis = list(OrderedDict.fromkeys(r['api'] for r in rows))
cache = {}
def expected_utc(s):
    if s in cache: return cache[s]
    c = json.loads(subprocess.run(['python3', RFCDT, 'check', '--json', '--', s], capture_output=True, text=True).stdout)
    f = c.get('fields', {})
    try:
        sec = min(f['second'], 59)
        dt = D.datetime(f['year'], f['month'], f['day'], f['hour'], f['minute'], sec) - D.timedelta(minutes=f['offset_minutes'])
        full = (f.get('secfrac') or '')
        frac = full[:9].ljust(9, '0')
        v = dt.strftime('%Y-%m-%dT%H:%M:%S') + '.' + frac + 'Z'
        if full[9:].strip('0'):
            v += '+sub-ns'
    except Exception:
        v = None
    cache[s] = (c['ok'], v)
    return cache[s]

def verdict(r):
    cat, ok, s = r['cat'], r['ok'], r['input']
    # probes/inputs.json schema 2 categories (tools/gen_probe_inputs.py)
    if cat == 'option':
        return 'n/a (non-default option: grade with run_vectors.py)'
    if cat == 'either':
        return 'interpretation (' + ('accepted' if ok else 'rejected') + ')'
    if cat.startswith('ixdtf') or cat == 'invalid' and s.endswith(']'):
        return 'conforming' if not ok else 'lenient (accepts suffix)'
    if cat in ('valid', 'range', 'leap-real'):
        if not ok:
            if cat == 'leap-real': return 'too strict (no leap second)'
            if cat == 'range': return 'too strict (range limit)'
            return '**TOO STRICT**'
        rv, exp = expected_utc(s)
        if exp is None and s.startswith('0000'):
            return 'conforming'
        if exp and exp.endswith('+sub-ns') and exp[:-7] == r['utc']:
            return 'conforming (lossy: fraction truncated to 9 digits)'
        if exp and exp != r['utc']:
            if exp[:19] == r['utc'][:19]:
                return 'conforming (lossy: fraction truncated to 9 digits)'
            return f'**WRONG VALUE** (expected {exp})'
        return 'conforming'
    if cat == 'ext':
        return 'lenient (allowed local ext.)' if ok else 'conforming'
    if cat == 'leap-fake':
        return '**TOO LENIENT**' if ok else 'conforming'
    # invalid
    return '**TOO LENIENT**' if ok else 'conforming'

def result_text(r):
    if r['ok']:
        off = r['offset'].split(' ')[0]
        return f"accepted → UTC {r['utc'][:-1]} (offset {off})"
    e = r['err'].replace('json: unable to unmarshal JSON string into Go time.Time within "/T": ', 'json: ').replace('|', '\\|')
    return 'rejected: ' + (e[:90])

out = []
by = defaultdict(dict)
for r in rows: by[r['api']][r['id']] = r
for a in apis:
    rs = list(by[a].values())
    base = [r for r in rs if not r['id'].startswith('x1-')]
    extra = [r for r in rs if r['id'].startswith('x1-')]
    vs = [(r, verdict(r)) for r in base]
    good = sum(1 for r, v in vs if v == 'conforming')
    out.append(f"#### go — `{a}`\n")
    out.append(f"{good} of {len(base)} probe inputs behaved as the RFCs require (not listed). Deviations and notable behaviour:\n")
    out.append("| Input | Result | RFC verdict |\n|---|---|---|")
    for r, v in vs:
        if v != 'conforming':
            out.append(f"| `{json.dumps(r['input'], ensure_ascii=False)[1:-1].replace('\u00a0', '\\u00a0')}` | {result_text(r)} | {v} |")
    out.append("\nExtra inputs (not in `inputs.json`):\n")
    out.append("| Input | Result | RFC verdict |\n|---|---|---|")
    for r in extra:
        v = verdict(r)
        out.append(f"| `{json.dumps(r['input'], ensure_ascii=False)[1:-1].replace('\u00a0', '\\u00a0')}` | {result_text(r)} | {v} |")
    out.append("")
open('results/tables.md', 'w').write('\n'.join(out) + '\n')

# matrix
cols = ['lc-z','space','off-minus0','off-nocolon','no-sec','no-off','comma','h24','leap-real','leap-fake','feb30-2024','frac12','trail-ws','y+10000','x-tz','x-unk!','x-incons!']
sym = {'conforming':'✓','**TOO STRICT**':'**S**','**TOO LENIENT**':'**L**','lenient (allowed local ext.)':'L','too strict (no leap second)':'s','too strict (range limit)':'s','lenient (accepts suffix)':'L'}
mat = []
for a in apis:
    cells = []
    for c in cols:
        v = verdict(by[a][c])
        cells.append(sym.get(v, '✓~' if v.startswith('conforming (lossy') else ('**W**' if 'WRONG' in v else v)))
    mat.append(f"| go: `{a}` | " + ' | '.join(cells) + ' |')
open('results/matrix.md', 'w').write('\n'.join(mat) + '\n')
print('\n'.join(mat))
