# -*- coding: utf-8 -*-
"""run the instruments over the reference corpus and score found against planted

A finding with no denominator is not a measurement. The corpus says how many of
each defect class were planted, so the only question left is how many came back -
and an instrument that finds 0 of 5 is not green, it is dead, which is a very
different thing and the only way to tell them apart.
"""
import collections
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "PY_IDE", "_ref")

planted = {}
for l in io.open(os.path.join(REF, "PLANTED.txt"), encoding="utf-8").read().split("\n"):
    if l.strip():
        k, v = l.split()
        planted[k] = int(v)

r = subprocess.run([sys.executable, "-X", "utf8",
                    os.path.join(ROOT, "validator", "glyph_checker.py")],
                   capture_output=True, text=True, encoding="utf-8")
out = r.stdout
cur = None
per = collections.defaultdict(lambda: collections.Counter())
for l in out.split("\n"):
    t = l.strip()
    m = re.match(r"(?:ok|FAIL)\s+(\S+)", t)
    if m:
        cur = m.group(1)
        continue
    if not cur or not t:
        continue
    if "_ref" not in t:
        continue
    cls = re.search(r"_ref/(\w+)\.vglyph", t)
    if cls:
        per[cur][cls.group(1)] += 1

print("  чек                    класс дефекта      посажено  найдено")
print("  ---------------------  -----------------  --------  -------")
score = 0
for name in sorted(per):
    for cls, n in sorted(per[name].items()):
        p = planted.get(cls, 0)
        mark = "" if p else "  (чистый файл)"
        print("  %-21s  %-17s  %8d  %7d%s" % (name, cls, p, n, mark))
        if p and n:
            score += 1
print("")
print("  классов, где прибор что-то нашёл: %d" % score)
print("  приборов, которые НИЧЕГО не нашли на эталоне:")
dead = []
for name in ("GLYPH_ONE", "GLYPH_ALIAS", "GLYPH_KNOWN", "GLYPH_HOLE",
             "GLYPH_CIRCLE", "ABSTRACT_TYPE", "ABSTRACT_SLOT", "ID_FRAME",
             "ID_UNIQUE"):
    if not per.get(name):
        dead.append(name)
for d in dead:
    print("     %s" % d)
