# -*- coding: utf-8 -*-
"""pick 3 more, for a green-on-black single-colour display

Mono means colour is gone, so shape is the only channel left. Anything that
differs from its neighbour only by weight or line count is out: at terminal
size, heavy and light rules of the same outline blur into one another, and a
wrong id read as a right id is worse than an unreadable one.

So the pick is by SILHOUETTE - arrow, cross, enclosure, star - and from the two
blocks already proven to render on the owner's machine. Box Drawing alone is not
enough: nearly all of it is ruled lines, and ruled lines are exactly the family
that collapses in single colour.
"""
import collections
import importlib.util as u
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()
used = set(g for g in w2g.values() if g)
rev = {}
for w, g in w2g.items():
    rev.setdefault(g, w)

PROVEN = [("Box Drawing", 0x2500, 0x257F), ("Misc Technical", 0x2300, 0x23FF)]

# silhouette families, chosen so no two candidates share an outline
FAMILIES = {
    "стрелка/угол": {0x2571, 0x2572, 0x2574, 0x2576, 0x2578, 0x257A},
    "решётка/крест": set(0x2533, 0x2536, 0x2537, 0x2538, 0x2539, 0x253A,
                          0x253B, 0x253C, 0x253D, 0x254B, 0x254E, 0x254F,
                          0x2550, 0x2553, 0x2556, 0x2559, 0x255C, 0x255F,
                          0x2562, 0x2565, 0x2568, 0x256B, 0x256E, 0x2573),
    "скобки": set(0x239B, 0x239C, 0x239D, 0x239E, 0x239F, 0x23A0, 0x23A1,
                  0x23A2, 0x23A3, 0x23A4, 0x23A5, 0x23A6, 0x23A7, 0x23A8,
                  0x23A9, 0x23AA, 0x23AB, 0x23AC, 0x23AD, 0x23AE, 0x23AF,
                  0x23B0, 0x23B1),
    "управление": set(0x2380, 0x2381, 0x2382, 0x2383, 0x2384, 0x2385, 0x2386,
                       0x2388, 0x2389, 0x238A, 0x238B, 0x238C, 0x238D, 0x238E,
                       0x238F, 0x2390, 0x2391, 0x2392, 0x2393, 0x2394, 0x2395),
    "окружность": {0x2299, 0x229A, 0x2312, 0x2313, 0x2314, 0x238D, 0x238E, 0x23F0, 0x23F1, 0x23F2, 0x23F3},
}

free = {}
for name, lo, hi in PROVEN:
    for cp in range(lo, hi + 1):
        ch = chr(cp)
        if ch in used or ch.isalnum():
            continue
        free[cp] = (ch, name)

print("  свободных в доказанных блоках: %d" % len(free))
print("")
picked = []
for fam, cps in FAMILIES.items():
    avail = [cp for cp in sorted(cps) if cp in free]
    if not avail:
        print("  %-16s нет свободных" % fam)
        continue
    cp = avail[len(avail) // 2]
    ch, name = free[cp]
    picked.append((fam, cp, ch, name))
    print("  %-16s U+%04X  %s  %s" % (fam, cp, ch, name))

print("")
have = [("уже подтверждены", 0x2387, "⎇"), ("уже подтвержден", 0x253F, "┿")]
five = have + [(f, cp, ch) for f, cp, ch, _ in picked][:3]
print("  ПЯТЬ ГЛИФОВ ДЛЯ ID:")
for f, cp, ch in five:
    print("     U+%04X  %s   %s" % (cp, ch, f))
print("")
print("  комбинаций при длине 5: %d" % (5 ** 5))
