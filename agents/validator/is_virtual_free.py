# -*- coding: utf-8 -*-
"""is there already a virtual in the base

Renaming abstract to virtual reads better, so it is worth doing - but only if
the word is free. vrt exists in the map, and if it means "virtual" then the
rename does not add a concept, it collides with one. Two concepts cannot share a
word: that is the rule the whole id-and-alphabet work rests on.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = io.open(os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt"),
            encoding="utf-8-sig").read()
S = io.open(os.path.join(ROOT, "compiler", "symbols_map.txt"),
            encoding="utf-8-sig").read()

print("  в словаре:")
for w in ("abstract", "virtual", "vrt", "proto", "prototype", "apply", "real"):
    m = re.search(r"(?m)^\*->\s*(\S+)\s+-\s+(.*)$", D)
    hits = re.findall(r"(?m)^\*->\s*(\S+)\s+-\s+(.*)$", D)
    got = [h for h in hits if h[0].split(",")[0].strip() == w]
    print("     %-10s %s" % (w, got[0][1][:70] if got else "НЕТ"))

print("")
print("  в карте глифов:")
for w in ("abstract", "vrt", "use", "real"):
    m = re.search(r"U\+[0-9A-Fa-f]+\s+(\S+)\s+\*->\s*(%s)\b" % re.escape(w), S)
    print("     %-10s глиф %s" % (w, m.group(1) if m else "НЕТ"))
