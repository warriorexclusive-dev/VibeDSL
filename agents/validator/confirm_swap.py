# -*- coding: utf-8 -*-
"""the swap is done - verify it in both carriers and see what it broke

Two carriers, so two places to check, and the names in them must agree. Also
worth naming what the swap did to the word count: nothing was added, so the
concept count must be unchanged - if it moved, the edit did something else.
"""
import importlib.util as u
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = io.open(os.path.join(ROOT, "compiler", "symbols_map.txt"), encoding="utf-8-sig").read()
D = io.open(os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt"),
            encoding="utf-8-sig").read()

print("  карта глифов:")
for w in ("virtual", "abstract", "vrt"):
    m = re.search(r"U\+([0-9A-Fa-f]+)\s+(\S+)\s+\*->\s*(%s)\b" % re.escape(w), S)
    print("     %-9s U+%s   %s" % (w, m.group(1) if m else "-", m.group(2) if m else "НЕТ"))

print("  словарь:")
for w in ("virtual", "abstract", "vrt"):
    m = re.search(r"(?m)^\*->\s*(%s)\b" % re.escape(w), D)
    print("     %-9s %s" % (w, "есть" if m else "НЕТ"))

sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()
print("")
print("  глифов в базе: %d   слов: %d" % (len(set(g for g in w2g.values() if g)),
                                          len(w2g)))
print("  ⌰ теперь: %s" % {w: g for w, g in w2g.items() if g == chr(0x2330)})
print("  ∖ теперь: %s" % {w: g for w, g in w2g.items() if g == chr(0x2216)})

# what the swap does to the files that still say abstract for a declaration
print("")
print("  файлы, где abstract ещё означает объявление:")
for base, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if not d.startswith(".")
               and d not in ("node_modules", "__pycache__", ".git")]
    for f in files:
        if not f.endswith((".vibe", ".vglyph", ".proto", ".md", ".txt")):
            continue
        p = os.path.join(base, f)
        try:
            t = io.open(p, encoding="utf-8-sig", errors="ignore").read()
        except Exception:
            continue
        n = len(re.findall(r"abstract:(?:prop|function|item)", t))
        if n:
            print("     %-44s %d" % (p.replace(ROOT + os.sep, "").replace(os.sep, "/"), n))
