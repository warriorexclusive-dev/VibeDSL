# -*- coding: utf-8 -*-
"""is the frame missing from the base, or only from the dictionary

The check reports ▹ and ◂ as unknown. They are in symbols_map as idopen and
idshut - that is where they were put, because putting them in the dictionary
broke ORDER and SPLITS. So the frame may be half-registered: a glyph with a
word in the map and no concept in the dictionary. That is a real gap, not a
check artefact, and it is the same shape as the id alphabet - a construct that
exists as a glyph but has no place where concepts live.
"""
import importlib.util as u
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = io.open(os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt"),
            encoding="utf-8-sig").read()
S = io.open(os.path.join(ROOT, "compiler", "symbols_map.txt"), encoding="utf-8-sig").read()

sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()
resolved = set(g for g in w2g.values() if g)

for name, cp in (("idopen", 0x25B9), ("idshut", 0x25C2)):
    ch = chr(cp)
    in_map = re.search(r"U\+%04X\s+%s\s+\*->\s*(\S+)" % (cp, re.escape(ch)), S)
    in_dict = bool(re.search(r"(?m)^\*->\s*%s\b" % name, D))
    in_res = ch in resolved
    print("  %-8s глиф %s" % (name, ch))
    print("     карта глифов   %s" % ("есть, слово " + in_map.group(1) if in_map else "НЕТ"))
    print("     словарь         %s" % ("есть" if in_dict else "НЕТ"))
    print("     резолвится      %s" % ("да" if in_res else "нет"))
    if in_map and not in_dict:
        print("     ВЫВОД: глиф есть, слова нет -概念 живёт только в карте")
