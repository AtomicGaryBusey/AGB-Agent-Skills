"""Convert `now-sdk explain --list --format raw` output to iso999_lint text input.
- Keeps the listing's line order exactly.
- Drops the '# ...' header/hint lines (CLI chrome, not entries).
- Drops the bracketed tag list (displayed like a scope note; not part of the heading/sort key).
- Appends a surrogate numeric locator = 1-based position of the topic's file in source order
  (docs/ relative paths sorted, i.e. the docs folder's own arrangement), because the linter
  only parses numeric/roman locators; the real locator is the topic name itself.
"""
import json,sys,re
topics=json.load(open('explain_topics.json'))
order={t['name']:i+1 for i,t in enumerate(sorted(topics,key=lambda t:t['file']))}
out=[]
for ln in open(sys.argv[1]):
    ln=ln.rstrip('\n')
    if not ln or ln.startswith('#'): continue
    name=re.sub(r'\s*\[.*\]$','',ln)
    out.append(f"{name}, {order[name]}")
open(sys.argv[2],'w').write('\n'.join(out)+'\n')
print(len(out))
