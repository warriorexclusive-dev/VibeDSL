# -*- coding: utf-8 -*-
"""is item actually in the ABSTRACT_TYPE check, or did the output eat it

The user read the verdict line and saw function and prop but not item. Two
possibilities and they need different answers: the check is missing a type, or
the check is right and the glyph does not render in the terminal they are
reading on. The second one matters more - a glyph the owner cannot see is a
glyph that cannot be in a rule they are meant to follow.
"""
import importlib.util as u
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()
rev = {}
for w, g in w2g.items():
    rev.setdefault(g, w)

src = io.open(os.path.join(ROOT, "validator", "glyph_checker.py"),
              encoding="utf-8-sig").read()
seg = src[src.find("ABSTRACT_TYPE") - 40:]
seg = seg[:seg.find("# GLYPH_COVER")]

seen = []
for m in re.finditer(r"\\u([0-9A-Fa-f]{4})", seg):
    cp = int(m.group(1), 16)
    ch = chr(cp)
    if cp >= 0x80 and ch not in seen:
        seen.append(ch)
print("  глифы в теле проверки ABSTRACT_TYPE:")
for ch in seen:
    print("     U+%04X  %s  ->  %s" % (ord(ch), ch, rev.get(ch, "НЕ В БАЗЕ")))

TYPES = [chr(0x2B1D), chr(0x02A9), chr(0x2317)]
absent = [t for t in TYPES if t not in seen]
print("  три типа в проверке: %s" % ("все на месте" if not absent else "НЕТ %s" % absent))
print("  имя типа в описании: %s" % "".join(
    ch for ch in seen if ch in TYPES))
