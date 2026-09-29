# -*- coding: utf-8 -*-
"""where the rule actually landed, and whether the file survived it

A rule in a new file is a second carrier, which is the thing this whole session
was about, so the file was folded into the dictionary header and deleted. Verify
that: the rule is present, the extra file is gone, and the invariants are intact.
"""
import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")
STRAY = os.path.join(ROOT, "DATA", "id_rule.txt")

txt = io.open(D, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
print("  строка 1: %s" % txt[0])
marks = [n for n, l in enumerate(txt, 1)
         if "TWO KINDS OF id" in l or "NEVER name a prototype" in l
         or "ALPHABET AND FRAME" in l or "THE CANONICAL FORM" in l]
for n in marks:
    print("  строка %4d: %s" % (n, txt[n - 1].strip()[:62]))
print("  всего строк: %d" % len(txt))
print("  отдельный файл правила удален: %s" % (not os.path.exists(STRAY)))

for chk in ("dict_edit.py verify", "spell_checker_v2.py", "glyph_checker.py"):
    r = subprocess.run([sys.executable, "-X", "utf8",
                        os.path.join(ROOT, "validator", chk)],
                       capture_output=True, text=True, encoding="utf-8")
    line = [l.strip() for l in r.stdout.split("\n")
            if "инварианты" in l or "VERDICT" in l]
    for l in line:
        print("  %-22s %s" % (chk.split()[0], l))
