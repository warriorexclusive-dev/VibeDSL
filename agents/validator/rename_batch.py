# -*- coding: utf-8 -*-
"""rename abstract -> virtual, ten declarations at a time, with a check after each

Two mass edits already wrecked a spec today - 582 quotes and 101 ids - because I
ran them whole and looked afterwards. So this one runs in batches of ten and
each batch is followed by the checkers, and the count is printed so it is
visible that it is ten and not "the rest".

The rename is unambiguous: only abstract:prop, abstract:function and
abstract:item are declarations. An abstract that is a WISH has no type at all -
it is abstract="..." - so there is nothing here that could be a wish by mistake.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
RX = re.compile(r"abstract:(prop|function|item)")

TARGETS = [
    "DATA/blueprint/base_window.proto",
    "DATA/blueprint/ide_window.proto",
    "DATA/blueprint/palette.proto",
    "PY_IDE/window.vibe",
    "PY_IDE/window.render.vibe",
    "DATA/protos.txt",
    "plan/exit-on-clean.vibe",
    "plan/object-spellcheck.vibe",
    "plan/spellcheck-stage1.vibe",
    "DATA/create_speck_check.md",
]

# find where the next unrenamed declaration is, then take N from there
pending = []
for rel in TARGETS:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        continue
    t = io.open(p, encoding="utf-8-sig").read()
    pending.append((rel, p, len(RX.findall(t)), t))

total = sum(n for _, _, n, _ in pending)
done = total - sum(n for _, _, n, _ in pending)
print("  всего объявлений abstract: %d   осталось: %d" % (total, sum(n for _, _, n, _ in pending)))

# a file whose count is <= N gets finished; otherwise take a slice
batch = 0
for rel, p, n, t in pending:
    if n == 0 or batch >= N:
        continue
    crlf = "\r\n" in t
    lines = t.replace("\r\n", "\n").split("\n")
    taken = 0
    for i, l in enumerate(lines):
        if batch >= N:
            break
        if RX.search(l):
            lines[i] = RX.sub(lambda m: "virtual:" + m.group(1), l)
            taken += 1
            batch += 1
    if taken:
        io.open(p, "w", encoding="utf-8", newline="").write(
            "\n".join(lines).replace("\n", "\r\n") if crlf else "\n".join(lines))
        print("  %-34s переименовано %2d   осталось в файле %2d"
              % (rel.replace(os.sep, "/"), taken, n - taken))
    if batch >= N:
        break
print("  партия: %d объявлений" % batch)
