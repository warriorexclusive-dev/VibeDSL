# -*- coding: utf-8 -*-
"""cut the last two entries and their continuation lines

idbase and idshut survived because each cut stopped at the NEXT "*-> " line, so
the continuation lines of the last entry of each cut stayed behind as loose
text. Cut by line, not by character offset: keep a line if it starts with "*-> "
and is one of the id entries, drop it, and drop the indented continuation lines
that belong to it.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")
raw = io.open(D, encoding="utf-8-sig").read()
crlf = "\r\n" in raw
lines = raw.replace("\r\n", "\n").split("\n")

GONE = ("idopen", "idshut", "idbase")
out = []
dropping = False
removed = 0
for l in lines:
    if l.startswith("*-> "):
        word = l[4:].split()[0] if len(l) > 4 else ""
        dropping = word in GONE
    elif not l.strip():
        dropping = False
    if dropping:
        removed += 1
        continue
    out.append(l)

text = "\n".join(out)
while "\n\n\n" in text:
    text = text.replace("\n\n\n", "\n\n")
io.open(D, "w", encoding="utf-8", newline="").write(
    text.replace("\n", "\r\n") if crlf else text)
print("  удалено строк: %d" % removed)
print("  осталось упоминаний: %s"
      % {w: text.count(w) for w in GONE if w in text} or "нет")
