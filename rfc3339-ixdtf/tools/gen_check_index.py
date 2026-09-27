import re,glob,os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'draft','references'))
rows=[]
for f in ['rfc3339-checks.md','rfc9557-checks.md']:
    for b in re.split(r'(?m)^### ',open(f).read())[1:]:
        head=b.splitlines()[0]
        if not re.match(r'R(3339|9557)-',head): continue
        get=lambda k:(re.search(r'\*\*'+k+r':\*\*\s*(.+)',b) or [None,''])[1].strip()
        cid,_,title=head.partition(' — ')
        lvl=get('Level'); lvl=re.sub(r'\s*\(.*','',lvl) if len(lvl)>40 else lvl
        j=re.match(r'[a-z]+',get('Judgment'))
        rows.append((cid.strip(),title.strip(),lvl,get('Roles'),j.group(0) if j else '',f))
out=["# Check index","","Generated from the two check catalogs. Filter by Roles (producer / consumer / schema), then open the catalog for Detect tactics and test inputs.","","| ID | Check | Level | Roles | Judgment | File |","|---|---|---|---|---|---|"]
out+=["| "+" | ".join(x.replace('|','/') for x in r)+" |" for r in rows]
open('check-index.md','w').write("\n".join(out)+"\n"); print(len(rows))
