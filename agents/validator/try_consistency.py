# -*- coding: utf-8 -*-
"""run the consistency module against the real inputs, read POOL_FILES from compile

PowerShell keeps mangling the inline python, so the read happens here. The point
is to see the actual output before wiring it into compile.py, because a check
that has never printed anything is the class of thing this session was about.
"""
import importlib.util as u
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = u.spec_from_file_location("_c", os.path.join(ROOT, "compiler", "consistency.py"))
c = u.module_from_spec(sp)
sp.loader.exec_module(c)

src = io.open(os.path.join(ROOT, "compiler", "compile.py"),
              encoding="utf-8-sig").read().replace("\r\n", "\n")
pool = re.findall(r"^\s*\"([^\"]+\.(?:txt|dict))\"\s*,?\s*$", src, re.M)
print("  POOL/FALLBACK found in compile.py: %s" % (pool or "не распознан"))

errs, notes = c.check(os.path.join(ROOT, "DATA"),
                      os.path.join(ROOT, "compiler", "symbols_map.txt"),
                      pool[:4], pool[4:])
print("")
print(c.report(errs, notes))
print("")
print("  ИТОГ: ошибок-противоречий %d, замечаний %d" % (len(errs), len(notes)))
print("  -> компиляцию блокировать следует только по ошибкам, не по замечаниям")
