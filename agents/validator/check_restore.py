# -*- coding: utf-8 -*-
"""confirm the restore worked, then reissue every id from the ledger

The word spec is back from git with its readable ids intact, which is the only
state from which a fresh issue is possible - the names are the only input, and
the last pass replaced them with glyphs, so reissuing needs them back.

Then the sequence that works, and only in this order:
    word spec -> compile -> frame -> issue ids from compiler/ids.txt
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "PY_IDE", "window.vibe")
t = io.open(P, encoding="utf-8-sig").read()
ids = sorted(set(re.findall(r'id="([^"]+)"', t)))
print("  window.vibe восстановлен из git")
print("  строк: %d   различных id: %d" % (len(t.split("\n")), len(ids)))
print("  первые: %s" % ", ".join(ids[:8]))
print()
print("  бэкап с глифными id на месте: %s"
      % os.path.exists(os.path.join(ROOT, "PY_IDE", "window.vibe.glyphids.bak")))
