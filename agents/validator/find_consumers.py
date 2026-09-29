# -*- coding: utf-8 -*-
"""what reads protos and blueprints, and what moving them into folders breaks

Before creating DATA/proto and DATA/blueprint, find out who loads these files and
by what path. use() resolves through load_pool, and if that pool is keyed on the
old flat filenames then moving the files does not just reorganise a directory -
it silently breaks every use() in every spec, and nothing would say so except a
spec that stops resolving.

That is the lesson of the day: find the consumer before you move the thing.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = io.open(os.path.join(ROOT, "compiler", "compile.py"),
              encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")

i = next(k for k, l in enumerate(src) if l.startswith("def load_pool"))
print("  compiler/compile.py  load_pool:")
for k in range(i, min(i + 26, len(src))):
    print("   %4d| %s" % (k + 1, src[k][:86]))

print("")
print("  кто ещё упоминает protos.txt / blueprints.txt:")
for base, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__")]
    for f in files:
        if not f.endswith((".py", ".md", ".txt", ".json", ".jsonc")):
            continue
        p = os.path.join(base, f)
        try:
            t = io.open(p, encoding="utf-8-sig", errors="ignore").read()
        except Exception:
            continue
        for name in ("protos.txt", "blueprints.txt"):
            if name in t:
                rel = p.replace(ROOT + os.sep, "").replace(os.sep, "/")
                n = t.count(name)
                print("     %-34s %s x%d" % (rel, name, n))
