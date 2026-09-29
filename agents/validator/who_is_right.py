# -*- coding: utf-8 -*-
"""what each red check is actually looking at, so I stop calling instruments broken

A count of 261 is not a verdict, it is a question. Either the spec is that wrong,
or the check is reading a file it should not, or it is looking for a shape that
the compiler has since changed. All three look identical from the summary line,
and I have twice today decided a check was broken on the strength of that line
alone - once when the check was right and once when it was wrong.

So: name the file, name the first finding, and let the numbers follow.
"""
import collections
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
r = subprocess.run([sys.executable, "-X", "utf8",
                    os.path.join(ROOT, "validator", "glyph_checker.py")],
                   capture_output=True, text=True, encoding="utf-8")
out = r.stdout

cur = None
per = collections.defaultdict(list)
for l in out.split("\n"):
    t = l.strip()
    m = re.match(r"(?:ok|FAIL)\s+(\S+)", t)
    if m:
        cur = m.group(1)
        continue
    if cur and t and "GLYPH_COVER" not in t and not t.startswith("VERDICT"):
        per[cur].append(t)

for name in ("ABSTRACT_TYPE", "ABSTRACT_SLOT", "ID_FRAME", "ID_UNIQUE", "GLYPH_CIRCLE"):
    items = per.get(name, [])
    files = collections.Counter()
    for t in items:
        m = re.match(r"([\w./\-]+\.vglyph)", t)
        if m:
            files[m.group(1)] += 1
    print("  %-14s находок %4d   файлы: %s"
          % (name, len(items),
             ", ".join("%s x%d" % (k, v) for k, v in files.most_common(4)) or "-"))
    for t in items[:1]:
        print("       первая: %s" % t[:88])
    print("")
