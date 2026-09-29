# -*- coding: utf-8 -*-
"""the project AGENTS.md is not old, it is EARLY - and that is worse

It was written at 12:32 today. The two-layer split, the .vglyph extension, the
id frame and the consistency check all came after that. So it is not a stale
copy of an older idea, it is a file that stopped being true halfway through the
afternoon, and it points only at .vibe in eleven places.

Timestamps settle this. No judgement needed.
"""
import io
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["AGENTS.md", "compiler/compile.py", "compiler/consistency.py",
         "compiler/symbols_map.txt", "DATA/dictionary_sorted_by_type.txt",
         "PY_IDE/window.vglyph", "PY_IDE/win.vglyph"]
today = time.strftime("%Y-%m-%d")
rows = []
for f in FILES:
    p = os.path.join(ROOT, f)
    if os.path.exists(p):
        rows.append((os.path.getmtime(p), f))
rows.sort()
base = rows[0][0] if rows else 0
print("  файлы по времени изменения сегодня:")
for m, f in rows:
    mark = "  <- база" if m == base else ""
    print("     %s  %-40s +%3d мин%s"
          % (time.strftime("%H:%M", time.localtime(m)), f, int((m - base) / 60), mark))

t = io.open(os.path.join(ROOT, "AGENTS.md"), encoding="utf-8-sig").read()
print("")
print("  AGENTS.md о глифном слое:")
for k in (".vglyph", "glyph_checker", "ID_FRAME", "idopen", "idshut", "idbase",
          "рамк", "consistency", "POOL_FILES"):
    print("     %-16s %s" % (k, ("x%d" % t.count(k)) if k in t else "НЕТ ЗНАЕТ"))
print("     .vibe            %d раз" % t.count(".vibe"))
