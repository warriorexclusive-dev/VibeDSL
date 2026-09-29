# -*- coding: utf-8 -*-
"""what compile.py already loads, so a consistency block can reuse it and not
re-parse the dictionary a second time

The point of the check is that it runs at COMPILE time. Every consistency check
that lives in a separate validator is a thing someone forgets to run, and a
thing that cannot fire while a spec is being compiled is a thing that will be
outlived by a spec written wrong.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = io.open(os.path.join(ROOT, "compiler", "compile.py"),
              encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")

for key in ("POOL_FILES", "FALLBACK_FILES", "DATA =", "def rules_block",
            "def main", "RULES_BLOCK", "print("):
    hits = [n for n, l in enumerate(src) if key in l]
    if hits:
        print("  %-18s строки %s" % (key, hits[:6]))
print("")
i = next((n for n, l in enumerate(src) if l.startswith("def main")), None)
if i is not None:
    for k in range(i, min(i + 40, len(src))):
        if "rules_block" in src[k] or "RULES" in src[k] or "stats" in src[k]:
            print("   %4d| %s" % (k + 1, src[k][:86]))
