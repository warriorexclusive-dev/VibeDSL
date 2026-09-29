# -*- coding: utf-8 -*-
"""what the state is after 18 batches, and what is still red

The batches held the verdict at 8/13 every time, which is the thing worth
knowing: the rename is reversible and provably so. What is left red was red
before the rename, and none of the 18 steps moved it.
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = io.open(os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt"),
            encoding="utf-8-sig").read()
S = io.open(os.path.join(ROOT, "compiler", "symbols_map.txt"),
            encoding="utf-8-sig").read()

print("  обмен в носителях:")
for w in ("virtual", "abstract", "vrt"):
    inmap = "да" if re.search(r"U\+[0-9A-Fa-f]+\s+\S+\s+\*->\s*%s\b" % re.escape(w), S) else "НЕТ"
    ind = "да" if re.search(r"(?m)^\*->\s*%s\b" % re.escape(w), D) else "НЕТ"
    print("     %-9s карта %-4s словарь %s" % (w, inmap, ind))

print("")
print("  смыслы на своих местах:")
print("     virtual:<тип>:§=...   объявлений в словаре   %d"
      % len(re.findall(r"virtual:(?:prop|function|item)", D)))
print("     abstract=...          пожеланий в словаре     %d"
      % len(re.findall(r'abstract\s*=\s*"', D)))
print("     abstract:<тип>:§=...  осталось старых         %d"
      % len(re.findall(r"abstract:(?:prop|function|item)", D)))

print("")
print("  красные сейчас:")
r = subprocess.run([sys.executable, "-X", "utf8",
                    os.path.join(ROOT, "validator", "spell_checker_v2.py")],
                   capture_output=True, text=True, encoding="utf-8")
for l in r.stdout.split("\n"):
    t = l.strip()
    if t.startswith("FAIL") or t.startswith("failing:"):
        print("     " + t[:82])

r2 = subprocess.run([sys.executable, "-X", "utf8",
                     os.path.join(ROOT, "validator", "glyph_checker.py")],
                    capture_output=True, text=True, encoding="utf-8")
print("")
for l in r2.stdout.split("\n"):
    t = l.strip()
    if t.startswith("ok ") or t.startswith("FAIL") or "VERDICT" in t:
        print("     " + t[:82])
