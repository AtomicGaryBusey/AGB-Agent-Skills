#!/usr/bin/env python3
"""Emit pkgsite's Examples list (section after the Index) as linter text.
Order unchanged. heading = link text; locator = HTML line of the target id."""
import re, sys
from urllib.parse import unquote
html = open(sys.argv[1], encoding="utf-8").read()
ids = {}
for n, line in enumerate(html.split("\n"), 1):
    for m in re.finditer(r'\bid="([^"]+)"', line):
        ids.setdefault(m.group(1), n)
i = html.find('id="pkg-examples"')
if i < 0:
    sys.exit(0)
seg = html[i:html.find('</section>', i)]
for href, text in re.findall(r'<a href="#([^"]+)"[^>]*>([^<]+)</a>', seg):
    if href == 'pkg-examples':
        continue
    print(f"{' '.join(text.split())}, {ids.get(href) or ids.get(unquote(href)) or 0}")
