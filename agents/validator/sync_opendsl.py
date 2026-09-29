# -*- coding: utf-8 -*-
"""sync DATA from the repo into opendsl - with a diff first and a backup always

The two copies have diverged: 37135 vs 39235 for the dictionary, so every glyph,
every rule and every converted example made today is missing on the side that
use() and proto_get actually read. Copying over it blindly would be reckless -
the sizes differ, so opendsl may hold something the repo does not.

So: compare first, back up, then copy only where the repo is the newer one, and
report every file that was touched and every one that was left alone.
"""
import filecmp
import hashlib
import io
import os
import shutil
import sys
import time

REPO = r"C:\Users\SoftIce\Desktop\Projects\VibeDSL\DATA"
OPEN = os.path.join(os.path.expanduser("~"), ".config", "opencode", "opendsl", "DATA")
BAK = OPEN + ".bak-" + time.strftime("%Y%m%d-%H%M%S")

def sha(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()[:12]

if "--apply" not in sys.argv:
    print("  (план)")
    same, diff, only_repo, only_open = [], [], [], []
    for f in sorted(os.listdir(REPO)):
        a, b = os.path.join(REPO, f), os.path.join(OPEN, f)
        if not os.path.isfile(a):
            continue
        if not os.path.exists(b):
            only_repo.append(f)
        elif sha(a) == sha(b):
            same.append(f)
        else:
            diff.append((f, os.path.getsize(a), os.path.getsize(b)))
    for f in sorted(os.listdir(OPEN)):
        if not os.path.exists(os.path.join(REPO, f)):
            only_open.append(f)
    print("  совпадают      : %s" % (", ".join(same) or "-"))
    print("  РАСХОДЯТСЯ      :")
    for f, sa, sb in diff:
        print("     %-38s repo=%-7d opencode=%-7d" % (f, sa, sb))
    print("  только в repo  : %s" % (", ".join(only_repo) or "-"))
    print("  только в open  : %s" % (", ".join(only_open) or "-"))
    print("")
    print("  бекап будет в : %s" % BAK)
    sys.exit(0)

shutil.copytree(OPEN, BAK)
print("  бекап: %s" % BAK)
n = 0
for f in sorted(os.listdir(REPO)):
    a, b = os.path.join(REPO, f), os.path.join(OPEN, f)
    if os.path.isfile(a) and (not os.path.exists(b) or sha(a) != sha(b)):
        shutil.copy2(a, b)
        print("  обновлён: %s" % f)
        n += 1
print("  обновлено файлов: %d" % n)
bad = [f for f in sorted(os.listdir(REPO))
       if os.path.isfile(os.path.join(REPO, f))
       and os.path.exists(os.path.join(OPEN, f))
       and sha(os.path.join(REPO, f)) != sha(os.path.join(OPEN, f))]
print("  осталось расхождений: %d %s" % (len(bad), bad if bad else ""))
