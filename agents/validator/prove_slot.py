# -*- coding: utf-8 -*-
"""plant the two errors in text that actually exists, then prove the check

The first attempt planted nothing. `§⩲"file"` does not exist - the name= form
carries file, the id= form carries win/win_min/view - and `⬝:` was replaced
wherever it appeared first, which was not in an abstract head. A proof that
plants nothing proves nothing, which is the same lesson as GLYPH_ONE passing
because it looked for the wrong character.
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "PY_IDE", "win.vglyph")

ID = chr(0x00A7)
ASSIGN = chr(0x2A72)
Q = chr(0x22)
ABSTRACT = chr(0x2330)
ITEM = chr(0x2B1D)

orig = io.open(SPEC, encoding="utf-8-sig").read()
ids = re.findall(ID + ASSIGN + Q + r"(\w+)" + Q, orig)
print("  id= значения в файле: %s" % ids)

# plant 1: an id whose literal is a role word - use a real one
planted = orig.replace(ID + ASSIGN + Q + ids[0] + Q,
                       ID + ASSIGN + Q + "any" + Q, 1)
# plant 2: an abstract with no type - take a real head and drop its type
m = re.search(re.escape(ABSTRACT) + re.escape(ITEM) + ":", planted)
if m:
    planted = planted[:m.start()] + ABSTRACT + planted[m.end():]
print("  подложено: id=%s (имя-роль), abstract без типа" % "any")

io.open(SPEC, "w", encoding="utf-8", newline="").write(planted)
try:
    r = subprocess.run([sys.executable, "-X", "utf8",
                        os.path.join(ROOT, "validator", "glyph_checker.py")],
                       capture_output=True, text=True, encoding="utf-8")
    for l in r.stdout.split("\n"):
        t = l.strip()
        if t.startswith("FAIL ABSTRACT") or "win.vglyph:" in t or "VERDICT" in t \
           or t.startswith("ok   ABSTRACT"):
            print("  " + t)
finally:
    io.open(SPEC, "w", encoding="utf-8", newline="").write(orig)
    print("  восстановлено")
