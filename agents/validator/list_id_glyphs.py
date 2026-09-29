# -*- coding: utf-8 -*-
"""every free glyph in the contiguous Misc Technical run, for the owner to pick

The range U+239A..U+23CD is 52 codepoints and none of them is in the base, which
is the point: a contiguous free run means the id alphabet is recognisable by
shape and the dictionary can never take it. Codepoints are printed alongside
because three candidates have already failed to render, and a codepoint is
still nameable when the glyph is not.
"""
import importlib.util as u
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()
used = set(g for g in w2g.values() if g)

LO, HI = 0x239A, 0x23CD
free = [cp for cp in range(LO, HI + 1)
        if chr(cp) not in used and not chr(cp).isalnum()]
print("  диапазон U+%04X..U+%04X   свободно %d из %d"
      % (LO, HI, len(free), HI - LO + 1))
print("")
for i in range(0, len(free), 8):
    row = free[i:i + 8]
    print("  " + "  ".join("U+%04X %s" % (cp, chr(cp)) for cp in row))
print("")
print("  нужно 6. Назовите шесть кодпоинтов.")
