# -*- coding: utf-8 -*-
"""name the two leftover concepts instead of guessing which ones they are

dict_edit reports 340 concepts where HEAD had 338, so two entries from my id
block survived the cuts. Which two is not something to infer from a count - ask
git, which is the only witness that was there before I started.
"""
import io
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cur = io.open(os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt"),
              encoding="utf-8-sig").read()
old = subprocess.run(["git", "show", "HEAD:DATA/dictionary_sorted_by_type.txt"],
                     cwd=ROOT, capture_output=True).stdout.decode("utf-8", "ignore")
rx = re.compile(r"(?m)^\*->\s+(\S+)")
a, b = set(rx.findall(old)), set(rx.findall(cur))
print("  в HEAD: %d   сейчас: %d" % (len(a), len(b)))
print("  ЛИШНИЕ (мои, лишние): %s" % sorted(b - a))
print("  ПОТЕРЯНО:               %s" % sorted(a - b))
for w in sorted(b - a):
    for m in re.finditer(r"(?m)^\*->\s+%s.*(?:\n(?![\s*#\n]).*)*" % re.escape(w), cur):
        print("  ---")
        print("  " + m.group(0).rstrip())
        break
