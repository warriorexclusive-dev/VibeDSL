# -*- coding: utf-8 -*-
"""the frame inventory, and why "" is the one that has to change

Every delimiter in the language is currently a SYMMETRIC pair, and a symmetric
frame cannot nest and cannot be unbalanced-checked. () is the exception - it is
already two different characters. So the frames are:

    ( )   two chars, asymmetric, nests
    [ ]   symmetric  "block of entity or node"
    { }   symmetric  "start custom logic description"
    " "   symmetric  "included custom string"

The string is the worst of the four, because a string is the one place content
is free text, so it is the one place you actually want to nest and to quote
inside. With " " the only way to put a quote in a string is a backslash, and
the language has no escape rule for it.

So: two distinct glyphs, open and close. That is the same fix as () had already.
"""
import importlib.util as u
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()

FRAMES = ["()", "[]", "{}", '""', "&->", "->", "=>"]
print("  рамки в базе:")
for f in FRAMES:
    g = w2g.get(f)
    sym = "симметричная" if len(f) == 2 and f[0] == f[1] else (
        "асимметричная" if len(f) == 2 else "стрелка")
    print("     %-5s  %-3s  %-14s  %s" % (f, g or "?", sym,
          (cc.load_alias_to_glyph()[0].get(f) or "")))
print("")
for w in ("quote", "string", "char", "in", "out", "escape"):
    print("     %-8s -> %s" % (w, w2g.get(w) or "НЕТ"))
