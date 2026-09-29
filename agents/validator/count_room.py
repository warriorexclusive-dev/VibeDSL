# -*- coding: utf-8 -*-
"""how much room is there, and does the id range need to be a contiguous block

The concern is not the count. 8 out of a few hundred is nothing. The concern is
SEGMENTATION: if id glyphs sit in the same blocks as concept glyphs, then two
of them read the same as two concept tokens. That is the overload that was
refused for the anchor, and it would be worse here, because a false reading of
an id silently names the wrong thing.

So the id space wants a CONTIGUOUS free run, and the honest question is how many
contiguous free runs exist in the blocks that are proven to render.
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

print("  сколько всего в базе: %d глифов" % len(used))
print("")
for name, lo, hi in PROVEN:
    runs = []
    cur = None
    for cp in range(lo, hi + 1):
        ch = chr(cp)
        free = ch not in used and not ch.isalnum()
        if free and cur is None:
            cur = cp
        elif not free and cur is not None:
            runs.append((cur, cp - 1))
            cur = None
    if cur is not None:
        runs.append((cur, hi))
    longest = max(runs, key=lambda r: r[1] - r[0]) if runs else None
    print("  %s" % name)
    print("     свободных одиночных: %d,  непрерывных серий: %d"
          % (sum(b - a + 1 for a, b in runs), len(runs)))
    print("     самая длинная серия: U+%04X..U+%04X  = %d глифов"
          % (longest[0], longest[1], longest[1] - longest[0] + 1)
          if longest else "     нет")
    for a, b in runs:
        if b - a + 1 >= 8:
            sample = "".join(chr(c) for c in range(a, min(a + 8, b + 1)))
            print("       >=8 подряд: U+%04X..U+%04X (%d)  %s"
                  % (a, b, b - a + 1, sample))
print("")
print("  израсходовано на концепты: %d" % len(used))
print("  нужно на id:               8")
print("  при 8 глифах из непрерывной серии id опознаются по форме,")
print("  и словарь никогда не занимает этот кусок.")
