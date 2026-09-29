# -*- coding: utf-8 -*-
"""fix 1 only: the backup folder is not a spec

Three checks were reading PY_IDE/_restore_*, my own safety copy, because the
walk skipped .git and __pycache__ and nothing else. A red that reads a backup
is not a red, it is noise wearing a red coat. This is the cheapest of the three
and it should turn three of them green on its own, which is the test of whether
my diagnosis was right.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, "validator", "glyph_checker.py")
s = io.open(G, encoding="utf-8-sig").read()
before = s
s = s.replace('and d not in ("temp", ".git", "GLOS", "node_modules", "__pycache__")',
              'and d not in ("temp", ".git", "GLOS", "node_modules", "__pycache__")\n'
              '                   and not d.startswith("_restore")')
s = s.replace('d not in ("temp", ".git", "GLOS", "node_modules", "__pycache__")]',
              'd not in ("temp", ".git", "GLOS", "node_modules", "__pycache__")\n'
              '                   and not d.startswith("_restore")]')
io.open(G, "w", encoding="utf-8", newline="").write(s)
print("  правка внесена: %s" % (s != before))
