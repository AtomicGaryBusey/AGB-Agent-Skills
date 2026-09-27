#!/usr/bin/env python3
"""Count entries out of place relative to the declared filing key.
Uses iso999_lint.sort_key (word-by-word, case fold, basic diacritic fold, numerals by value)
on the converted headings. displaced = n - LIS(positions under the ideal order).
Usage: displaced.py <converted .txt files...>"""
import sys, os, bisect, re
sys.path.insert(0, os.path.expanduser("~/.claude/skills/iso999/scripts"))
import iso999_lint as L
tot_n = tot_d = 0
for p in sys.argv[1:]:
    names = [re.sub(r", \d+$", "", l.rstrip("\n")) for l in open(p, encoding="utf-8") if l.strip()]
    keys = [(L.sort_key(n, "word", roman="off"), n.casefold(), n) for n in names]
    ideal = sorted(range(len(names)), key=lambda i: keys[i])
    rank = {i: r for r, i in enumerate(ideal)}
    seq = [rank[i] for i in range(len(names))]
    tails = []
    for x in seq:
        k = bisect.bisect_left(tails, x)
        if k == len(tails): tails.append(x)
        else: tails[k] = x
    d = len(names) - len(tails)
    tot_n += len(names); tot_d += d
    print(f"{os.path.relpath(p, os.path.dirname(os.path.dirname(p)))}\tentries={len(names)}\tdisplaced={d}")
print(f"TOTAL\tentries={tot_n}\tdisplaced={tot_d}")
