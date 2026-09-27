"""Compare go/doc and pkgsite sibling order against declared ISO 999 filing keys.

K_fold : whole identifier, case-folded, digit runs by numeric value, '_' null
         (identifier = one word; word-by-word == letter-by-letter here)
K_hump : identifier split at camelCase humps, acronym boundaries, digit runs
         and '_' into words; filed word-by-word, case-folded, numbers by value
         and before letters (8.2, 8.3 d)
Only adjacent pairs are tested (an inversion anywhere implies one adjacent).
"""
import json, re, sys
from collections import Counter, defaultdict

def fold_key(s):
    parts = re.findall(r'\d+|[^\d_]+', s)
    return tuple((0, int(p), '') if p.isdigit() else (1, 0, p.casefold()) for p in parts)

HUMP = re.compile(r'[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+')
def hump_words(s):
    return HUMP.findall(s)
def hump_key(s):
    return tuple((0, int(w), '') if w.isdigit() else (1, 0, w.casefold()) for w in hump_words(s))

def cause(a, b):
    if re.search(r'\d', a + b) and fold_key(a)[:1] == fold_key(b)[:1]:
        pass
    ca, cb = a.casefold(), b.casefold()
    if '_' in a + b: return 'underscore'
    # strip digits' effect: compare with digits padded
    pad = lambda s: re.sub(r'\d+', lambda m: m.group().zfill(8), s)
    if pad(a) <= pad(b) and not a <= b: return 'digits'
    if a < b and ca > cb: return 'case (upper before lower)'
    if pad(ca) > pad(cb) and pad(a) < pad(b): return 'case (upper before lower)'
    return 'other'

def sibling_sets(entries):
    top_f = [e['name'] for e in entries if e['level'] == 0 and e['kind'] == 'func']
    top_t = [e['name'] for e in entries if e['level'] == 0 and e['kind'] == 'type']
    sets = [('funcs', top_f), ('types', top_t)]
    cur = None
    for e in entries:
        if e['level'] == 0 and e['kind'] == 'type':
            cur = {'type': e['name'], 'ctor': [], 'method': []}
            sets.append(('ctor+method@' + e['name'], cur))
        elif e['level'] == 1:
            cur[e['kind']].append(e['name'])
    out = []
    for label, s in sets:
        if isinstance(s, dict):
            out.append(('ctors@' + s['type'], s['ctor']))
            out.append(('methods@' + s['type'], s['method']))
            out.append(('presented-subheadings@' + s['type'], s['ctor'] + s['method']))
        else:
            out.append((label, s))
    return out

data = [p for p in json.load(open(sys.argv[1])) if p['godoc']]
for order in ('godoc', 'pkgsite'):
    for kname, key in (('K_fold', fold_key), ('K_hump', hump_key)):
        inv = Counter(); ex = defaultdict(list); npairs = Counter()
        for p in data:
            for label, names in sibling_sets(p[order]):
                kind = label.split('@')[0]
                for a, b in zip(names, names[1:]):
                    npairs[kind] += 1
                    if key(a) > key(b):
                        c = 'two-run restart' if kind == 'presented-subheadings' and a in [x['name'] for x in p[order] if x['kind']=='ctor'] and b in [x['name'] for x in p[order] if x['kind']=='method'] else cause(a, b)
                        inv[(kind, c)] += 1
                        if len(ex[(kind, c)]) < 6:
                            ex[(kind, c)].append(f"{p['path']}: {a} > {b}" + (f" [{label.split('@')[1]}]" if '@' in label else ''))
        print(f"\n## order={order} key={kname}")
        print("adjacent pairs tested:", dict(npairs))
        for k, v in sorted(inv.items(), key=lambda kv: -kv[1]):
            print(f"  {v:5d}  {k[0]:24s} {k[1]}")
            for x in ex[k]: print("         e.g.", x)
