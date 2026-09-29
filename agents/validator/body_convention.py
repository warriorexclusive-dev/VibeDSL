# -*- coding: utf-8 -*-
"""two conventions for the body of a declaration, and I used both

A declaration is two lines: the head carries the type, the id and the action;
the body says what the action is. The question is whether the body repeats the
head or only spells out the action - and I answered it differently in three
places, which means the same file read three ways depending on who wrote it.
"""
import glob
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = "&->"                      # the source spells the constructor this way
                                # U+2022 only appears after compilation, so a
                                # scan for it finds nothing in a source file and
                                # reports a clean file as empty
FILES = ["PY_IDE/window.vibe", "PY_IDE/ide.vglyph"] + sorted(
    glob.glob(os.path.join(ROOT, "DATA", "blueprint", "*.proto")))

print("  %-38s %6s %10s %12s" % ("файл", "декл", "тело полное", "тело-цепочка"))
for p in FILES:
    L = io.open(p, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
    idx = [i for i, l in enumerate(L) if l.lstrip().startswith(KEY)]
    bodies = [L[i + 1].strip() for i in idx if i + 1 < len(L)]
    full = sum(1 for b in bodies if b.startswith(KEY))
    print("  %-38s %6d %10d %12d"
          % (p.replace(ROOT + os.sep, "").replace(os.sep, "/"), len(idx), full,
             len(bodies) - full))
