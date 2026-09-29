# -*- coding: utf-8 -*-
"""triangles, filled and hollow, pointing in and out - which are free

The geometric shapes block is already proven on the owner machine: the base
draws from it heavily, so whatever else failed to render, this block did not.
So a triangle reservation costs nothing in render risk.

Asking specifically about the FILLED ones, because filled and hollow differ by
fill rather than by outline, and that is the distinction that survives a
monochrome display better than weight does.
"""
import importlib.util as u
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()
rev = {}
for w, g in w2g.items():
    rev.setdefault(g, w)

TRI = {
    "up    filled": 0x25B2, "up    hollow": 0x25B3,
    "up s  filled": 0x25B4, "up s  hollow": 0x25B5,
    "right filled": 0x25B6, "right hollow": 0x25B7,
    "rght s filled": 0x25B8, "rght s hollow": 0x25B9,
    "rght p filled": 0x25BA, "rght p hollow": 0x25BB,
    "down  filled": 0x25BC, "down  hollow": 0x25BD,
    "down s filled": 0x25BE, "down s hollow": 0x25BF,
    "left  filled": 0x25C0, "left  hollow": 0x25C1,
    "left s filled": 0x25C2, "left s hollow": 0x25C3,
    "left  dbl   ": 0x25C6, "left  sq  ": 0x25C7,
    "rght  dbl   ": 0x25C8, "rght  sq  ": 0x25C9,
}
print("  треугольники Geometric Shapes (блок уже рисуется у вас):")
free, taken = [], []
for name, cp in sorted(TRI.items()):
    ch = chr(cp)
    if ch in w2g.values() or ch in rev:
        owner = rev.get(ch, "?")
        taken.append((name, cp, ch, owner))
        print("     U+%04X  %s  %-12s  ЗАНЯТ: %s" % (cp, ch, name, owner))
    else:
        free.append((name, cp, ch))
        print("     U+%04X  %s  %-12s  свободен" % (cp, ch, name))
print("")
print("  свободных: %d   занято: %d" % (len(free), len(taken)))
filled_free = [f for f in free if "filled" in f[0]]
print("  из них ЗАКРАШЕННЫХ свободно: %d" % len(filled_free))
for name, cp, ch in filled_free:
    print("     U+%04X  %s  %s" % (cp, ch, name.strip()))
