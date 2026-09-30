import os
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
import json, re, html, os
d = json.load(open(os.path.join(CACHE,'wcag.json')))
def slice_sec(h, sid):
    m = re.search(r'<section id="%s"' % sid, h)
    if not m: return ''
    # find matching end by counting section tags
    i = m.start(); depth = 0
    for t in re.finditer(r'<(/?)section\b', h[i:]):
        depth += -1 if t.group(1) else 1
        if depth == 0: return h[i:i+t.end()]
    return h[i:]
def links(s):
    out = {}
    for m in re.finditer(r'<a href="https://www\.w3\.org/WAI/WCAG22/Techniques/([a-z-]+)/([A-Z]+\d+)"[^>]*>(.*?)</a>', s, re.S):
        tid = m.group(2); title = html.unescape(re.sub(r'<[^>]+>', '', m.group(3)))
        title = re.sub(r'\s+', ' ', title).strip()
        out.setdefault(tid, title)
    return out
def brief(h):
    s = slice_sec(h, 'brief')
    items = re.findall(r'<dt>(.*?)</dt>\s*<dd>(.*?)</dd>', s, re.S)
    return {re.sub(r'<[^>]+>|\s+',' ',a).strip(): html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',b))).strip() for a,b in items}
def act(h):
    s = slice_sec(h, 'test-rules')
    return [(html.unescape(re.sub(r'<[^>]+>','',t)).strip(), u) for u,t in re.findall(r'<a href="((?:https://www\.w3\.org)?/WAI/standards-guidelines/act/rules/[^"]+)"[^>]*>(.*?)</a>', s, re.S)]
res = {}
for s in d['scs']:
    h = open(os.path.join(CACHE,'understanding')+'/' + os.path.basename(s['understanding'])).read()
    suf=slice_sec(h,'sufficient'); note=[] if links(suf) else [html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',li))).strip() for li in re.findall(r'<li>(.*?)</li>', suf, re.S)]
    res[s['id']] = dict(suf_note=note, sufficient=links(slice_sec(h,'sufficient')), advisory=links(slice_sec(h,'advisory')), failure=links(slice_sec(h,'failure')), brief=brief(h), act=act(h))
json.dump(res, open(os.path.join(CACHE,'techs.json'),'w'), indent=1, ensure_ascii=False)
for k in ['1.1.1','2.5.8','1.4.3','4.1.1','3.3.8']:
    print(k, json.dumps(res[k], ensure_ascii=False)[:1500])
print([k for k,v in res.items() if not v['sufficient']])
