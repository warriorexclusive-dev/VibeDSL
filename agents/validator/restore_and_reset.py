# -*- coding: utf-8 -*-
"""restore from the repository, wipe the ledger, regenerate in the only order
that works

The order is the lesson of today, and getting it wrong is what made the last
pass unrecoverable:

    restore -> compile -> frame -> issue ids

Each step consumes the previous one's output, and the LAST one consumes the
readable names. So the names are the fragile part, and they are backed up before
anything touches them. Wiping the ledger is safe only AFTER the restore,
because a ledger that remembers addresses whose names are gone cannot be
reconciled - it can only be thrown away, and that is cheaper now than later.
"""
import io
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
BAK = os.path.join(ROOT, "PY_IDE", "_restore_" + time.strftime("%Y%m%d-%H%M%S"))
os.makedirs(BAK, exist_ok=True)
print("  бэкап текущих спек: %s" % os.path.relpath(BAK, ROOT))

for n in ("win.vibe", "window.vibe", "win.vglyph", "window.vglyph"):
    p = os.path.join(ROOT, "PY_IDE", n)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(BAK, n))

# 1. restore the word specs from the repository
for n in ("win.vibe", "window.vibe"):
    r = subprocess.run(["git", "show", "HEAD:PY_IDE/" + n], cwd=ROOT,
                       capture_output=True)
    if r.returncode == 0 and r.stdout:
        p = os.path.join(ROOT, "PY_IDE", n)
        with io.open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(r.stdout.decode("utf-8", "replace"))
        print("  восстановлен из репозитория: %s" % n)

# 2. report what the restore actually gave, before anything consumes it
import re
for n in ("win.vibe", "window.vibe"):
    p = os.path.join(ROOT, "PY_IDE", n)
    if not os.path.exists(p):
        continue
    t = io.open(p, encoding="utf-8-sig").read()
    ids = sorted(set(re.findall(r'id="([^"]+)"', t)))
    print("     %-12s строк %3d   id: %3d   %s"
          % (n, len(t.split("\n")), len(ids), ", ".join(ids[:5])))

# 3. wipe the ledger - safe now, the names are back
led = os.path.join(ROOT, "compiler", "ids.txt")
if os.path.exists(led):
    shutil.copy2(led, os.path.join(BAK, "ids.txt"))
    io.open(led, "w", encoding="utf-8", newline="\n").write("")
    print("  реестр обнулён: %s" % os.path.relpath(led, ROOT))
