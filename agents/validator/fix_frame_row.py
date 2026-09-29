# -*- coding: utf-8 -*-
"""the map row for the frame is in dictionary format, so nothing parses it

symbols_map.txt rows are:  U+XXXX  glyph  *-> word - description

What my earlier edit wrote was the DICTIONARY form:  *-> idopen - description
and a name. load_alias_to_glyph found no U+ field, so the row was invisible, so
idopen and idshut did not resolve, so the agent-glyph check called them unknown
- and all three facts were the same fact, seen three times and none of them
locating the cause.
"""
import importlib.util as u
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "compiler", "symbols_map.txt")
s = io.open(S, encoding="utf-8-sig").read()
crlf = "\r\n" in s
lines = s.replace("\r\n", "\n").split("\n")

out, removed = [], 0
for l in lines:
    if ("idopen" in l or "idshut" in l) and not re.match(r"^U\+", l.strip()):
        removed += 1
        continue
    out.append(l)

rows = [
    "U+25B9   %s  *-> idopen - open of the frame, points INWARD like a bracket, hollow"
    % chr(0x25B9),
    "U+25C2   %s  *-> idshut - close of the frame, filled, so the pair differs by fill"
    % chr(0x25C2),
]
text = "\n".join(out).rstrip("\n") + "\n" + "\n".join(rows) + "\n"
io.open(S, "w", encoding="utf-8", newline="").write(
    text.replace("\n", "\r\n") if crlf else text)
print("  неверных строк удалено: %d   добавлено строк карты: %d" % (removed, len(rows)))

sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()
for nm, cp in (("idopen", 0x25B9), ("idshut", 0x25C2)):
    print("  %-8s глиф %s   в карте слов: %s"
          % (nm, chr(cp), "да" if w2g.get(nm) == chr(cp) else "НЕТ"))
print("  глифов в базе: %d" % len(set(g for g in w2g.values() if g)))
