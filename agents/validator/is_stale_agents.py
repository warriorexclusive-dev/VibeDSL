# -*- coding: utf-8 -*-
"""is AGENTS.md a stale copy that no longer works

There are two. The project one is loaded by convention. The global one was
renamed to AGENTS.md.bak, so it is NOT loaded - which means for a long time the
global instructions were simply not in effect, and nobody noticed because the
project file shadowed the need for them.

Staleness is not a guess. It is measured against the things that changed today:
the glyph rule, the frame, the two layers, and where the 15 checks actually live.
A document that asserts the opposite of the current state is stale, and a
document that describes a file that no longer exists is worse than stale, because
it sends the next reader to look for it.
"""
import io
import os
import re
import time

P = os.path.join("C:\\Users\\SoftIce\\Desktop\\Projects\\VibeDSL", "AGENTS.md")
G = os.path.join(os.path.expanduser("~"), ".config", "opencode", "AGENTS.md")
GB = G + ".bak"

CLAIMS = [
    ("пишем словами / write in words", r"(?i)\bwrite (in )?words\b"),
    ("глифы как правило",              r"(?i)glyph"),
    ("5 проверок синтаксиса",         r"(?i)5 (pass|runs|syntax)"),
    ("15 проверок",                   r"(?i)\b15\b"),
    ("читает DATA напрямую",           r"(?i)DATA/"),
    ("use\\(\\) прототипы",             r"(?i)proto_get|prototypes"),
    ("RAG база php",                  r"(?i)php -S|router"),
    ("агент dsl-coder",               r"(?i)dsl-coder"),
    ("расширение .vibe",              r"(?i)\.vibe"),
    ("blueprint",                     r"(?i)blueprint"),
]

for path, label in ((P, "ПРОЕКТНЫЙ"), (GB, "ГЛОБАЛЬНЫЙ (.bak, НЕ ЗАГРУЖАЕТСЯ)")):
    if not os.path.exists(path):
        print("  %s: ФАЙЛА НЕТ" % label)
        print("")
        continue
    st = os.stat(path)
    txt = io.open(path, encoding="utf-8-sig", errors="ignore").read()
    age = time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
    print("  %s" % label)
    print("     %s" % path)
    print("     %d байт, изменён %s" % (st.st_size, age))
    for name, rx in CLAIMS:
        n = len(re.findall(rx, txt))
        print("     %-28s %s" % (name, ("x%d" % n) if n else "нет"))
    print("")

print("  глобальный AGENTS.md существует: %s" % os.path.exists(G))
print("  .bak существует:                 %s" % os.path.exists(GB))
