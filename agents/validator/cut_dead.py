# -*- coding: utf-8 -*-
"""cut the five dead instruments out of glyph_checker.py

Scored against the reference corpus, these five found nothing on any of the
eighteen classes - not a partial miss, zero. An instrument that has never
caught anything is not a safety net, it is a line of output that reads like
one, and it cost the whole day: a report that says 9 checks run implies the
other four were worth reading.

Kept, and this is what the corpus actually says:

    ABSTRACT_SLOT   6/6 planted, no misses
    ID_FRAME        6/6 planted, no misses

Half-measure, and recorded rather than deleted, because the one number against
it is real: GLYPH_CIRCLE flagged all three clean control files, so its red on
the live spec is not evidence about the spec.

Removed bottom-up so the line numbers of the earlier blocks stay valid.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "validator", "glyph_checker.py")
lines = io.open(P, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")

# (last line of block, inclusive) 1-based, from the file as read
BLOCKS = [
    (174, "ABSTRACT_TYPE"),
    (142, "GLYPH_HOLE"),
    (124, "GLYPH_KNOWN"),
    (104, "GLYPH_ALIAS"),
    (96, "GLYPH_ONE"),
]

for last, name in BLOCKS:
    i = last - 1
    blk = "\n".join(lines[i - 12:i + 1])
    assert name in blk, "блок %s не на своём месте, строка сдвинулась" % name
    start = i
    while start > 0 and not lines[start - 1].strip().startswith("#"):
        start -= 1
    start -= 1                       # take the comment header too
    while start > 0 and not lines[start].strip():
        start -= 1
    if start > 0:
        start += 1
    del lines[start:i + 1]
    print("  вырезан %-14s строк %d..%d" % (name, start + 1, last))

io.open(P, "w", encoding="utf-8", newline="\n").write("\n".join(lines))

s = "\n".join(lines)
print("")
print("  осталось проверок: %d" % s.count("    check(\""))
for n in ("GLYPH_ONE", "GLYPH_ALIAS", "GLYPH_KNOWN", "GLYPH_HOLE", "ABSTRACT_TYPE"):
    print("  %-14s %s" % (n, "ОСТАЛСЯ" if n in s else "вырезан"))
