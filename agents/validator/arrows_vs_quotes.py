# -*- coding: utf-8 -*-
"""were the quotes replaced by the inward arrows, or is that an intent

The claim is that the inward arrows ARE the replacement for the symmetric
quotes. That matters more than it looks: quotes PROTECT their content from the
compiler, and that protection is the reason GLYPH_CIRCLE can never close. If
the arrows take over as the frame, the payload stops being protected, the round
trip becomes a fixed point, and the check stops being nonsense.

So: find out whether it has been done, and where the arrows currently appear.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F_OPEN, F_SHUT = chr(0x25B9), chr(0x25C2)
Q = chr(0x22)

print("  спеки: кавычки против стрелок")
for n in ("win.vglyph", "window.vglyph", "win.vibe", "window.vibe"):
    p = os.path.join(ROOT, "PY_IDE", n)
    if not os.path.exists(p):
        continue
    t = io.open(p, encoding="utf-8-sig").read()
    print("     %-16s кавычек %4d   стрелок %d"
          % (n, t.count(Q), t.count(F_OPEN) + t.count(F_SHUT)))

print("")
print("  где стрелки-рамка встречаются вообще:")
hits = 0
for base, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if not d.startswith(".")
               and d not in ("node_modules", "__pycache__", ".git")]
    for f in sorted(files):
        if not f.endswith((".vglyph", ".vibe", ".txt", ".md", ".py")):
            continue
        p = os.path.join(base, f)
        try:
            t = io.open(p, encoding="utf-8-sig", errors="ignore").read()
        except Exception:
            continue
        if F_OPEN in t:
            hits += 1
            print("     %-52s %d"
                  % (p.replace(ROOT + os.sep, "").replace(os.sep, "/"),
                     t.count(F_OPEN) + t.count(F_SHUT)))
print("     всего файлов: %d" % hits)
