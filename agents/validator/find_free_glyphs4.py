# -*- coding: utf-8 -*-
"""three more free glyphs, from the two blocks proven to render

Two of five candidates were confirmed on the owner's screen: U+2387 and U+253F.
The other three were not, and the confirmed pair proves the source blocks are
Box Drawing and Misc Technical. So search those and only those. No silhouette
machinery: the green-on-black remark was a joke about a film, and building a
monochrome-contrast filter out of it was mine, not the task.
"""
import importlib.util as u
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()
used = set(g for g in w2g.values() if g)

CONFIRMED = [(0x2387, "Misc Technical"), (0x253F, "Box Drawing")]
taken = set(c for c, _ in CONFIRMED)
PROVEN = [("Box Drawing", 0x2500, 0x257F), ("Misc Technical", 0x2300, 0x23FF)]

free = []
for name, lo, hi in PROVEN:
    for cp in range(lo, hi + 1):
        ch = chr(cp)
        if ch in used or ch in taken or ch.isalnum():
            continue
        free.append((cp, ch, name))

print("  свободных в доказанных блоках: %d" % len(free))
print("")
print("  кандидаты на три оставшихся глифа (обозрите и скажите, какие видны):")
for cp, ch, name in free[::max(1, len(free) // 12)][:12]:
    print("     U+%04X  %s   %s" % (cp, ch, name))
print("")
print("  свободных по блокам:")
for name, lo, hi in PROVEN:
    n = sum(1 for cp, c, nm in free if nm == name)
    print("     %-18s %d" % (name, n))
