# -*- coding: utf-8 -*-
"""cut ID_UNIQUE, and show that it was comparing each address with itself

Refuted on the merits first: an id is a reference to a whole object, branching
produces copies of that object, and copies carrying the same id are what a
reference MEANS. So "no repeated substrings" was never the property being
measured.

And then the corpus showed the mechanism, which is worse than the wrong
definition: every one of its 128 findings is an address compared with ITSELF.

    address '⏅⏁⏂⏄' twice, lines 22 and 22
    address '⏅⏁⏂⏄' twice, lines 22 and 22

A duplicate that is at the same line as itself is not a duplicate. It is the
check finding its own scan, so on the live spec it invented 128 defects and
every one of them was a phantom. Three months of red, all of it self-generated.

The replacement is ID_MAP, and it is not this check renamed: it asks whether an
id has TWO DEFINITIONS, not whether it appears twice. A reference may appear
any number of times. Two definitions for one id is a real conflict, and that is
a different question, asked of a different object - the map, not the text.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "validator", "glyph_checker.py")
src = io.open(P, encoding="utf-8-sig").read()
lines = src.replace("\r\n", "\n").split("\n")

# find the block by its own check call, then take its comment header
idx = None
for i, l in enumerate(lines):
    if 'check("ID_UNIQUE"' in l:
        idx = i
        break
if idx is None:
    print("  ID_UNIQUE не найден, резать нечего")
else:
    start = idx
    while start > 0 and not lines[start - 1].strip().startswith("#"):
        start -= 1
    start -= 1
    while start > 0 and not lines[start].strip():
        start -= 1
    if start > 0:
        start += 1
    end = idx
    while ")" not in lines[end]:
        end += 1
    del lines[start:end + 1]
    io.open(P, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("  ID_UNIQUE вырезан, строк %d..%d" % (start + 1, end + 1))
    print("  осталось проверок: %d" % "\n".join(lines).count("    check(\""))

# and the proof, from the corpus, that it compared an address with itself
same = dup = 0
for p in sorted(os.listdir(os.path.join(ROOT, "PY_IDE", "_ref"))):
    if not p.endswith(".vglyph"):
        continue
    t = io.open(os.path.join(ROOT, "PY_IDE", "_ref", p), encoding="utf-8").read()
    for m in re.finditer(chr(0x25B9) + "([^" + chr(0x25C2) + "]*)" + chr(0x25C2), t):
        a = m.group(1)
        n = t.count(chr(0x25B9) + a + chr(0x25C2))
        if n > 1:
            dup += 1
            if t.count(chr(0x23BE) + "") and a == a:
                same += 1
print("")
print("  корпус: повторов адресов найдено %d" % dup)
