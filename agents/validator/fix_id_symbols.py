# -*- coding: utf-8 -*-
"""revert the master, and put the frame and alphabet in symbols_map instead

Adding idopen/idshut/idbase to the dictionary was wrong twice over.

Once: ORDER and SPLITS went red, because the master is one of five copies and a
new concept has to land in all of them atomically. That is the trap this whole
session was about, and I walked into it in the same afternoon I named it.

Twice, and this is the real reason: the frame and the id alphabet are not
concepts. A concept is a thing the language can talk about. These are glyph
level constructs - a bracket and a range of positions - and the file that
holds glyph level facts is symbols_map, the canonical word<->glyph table. The
dictionary stays a list of concepts, and its five copies stay in step.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")
S = os.path.join(ROOT, "compiler", "symbols_map.txt")

ENTRIES = (
    '*-> idopen       - open of the id frame, points INWARD like a bracket. an id is\n'
    '     written between idopen and idshut; outside the frame an alphabet glyph is\n'
    '     not an id, it is a typo with no claim. U+25B9\n'
    '*-> idshut       - close of the id frame, filled where idopen is hollow, so the two\n'
    '     differ by fill as well as by direction in one colour. U+25C2\n'
    '*-> idbase       - the generated id alphabet: sixteen glyphs, U+23BE..U+23CD,\n'
    '     contiguous, fixed, never extended. 16^4 = 2^16 = 65536 ids. a spec-local\n'
    '     id is exactly 4 of them, order significant. DELIBERATELY UNSPELLED - an id\n'
    '     is an address and must not render as text. the base never takes this run,\n'
    '     because the run is defined as everything in this range\n\n'
)

# 1. revert the master
raw = io.open(D, encoding="utf-8-sig").read()
crlf = "\r\n" in raw
t = raw.replace("\r\n", "\n")
i = t.find("*-> idopen")
j = t.find("*-> root")           # the next entry after the block
if i != -1 and j > i:
    t = t[:i] + t[j:]
    io.open(D, "w", encoding="utf-8", newline="").write(
        t.replace("\n", "\r\n") if crlf else t)
    print("  мастер: блок откачен")
else:
    print("  мастер: откачивать нечего (i=%d j=%d)" % (i, j))

# 2. put it in symbols_map, which is the glyph-level carrier
raw = io.open(S, encoding="utf-8-sig").read()
crlf = "\r\n" in raw
t = raw.replace("\r\n", "\n")
if "idopen" not in t:
    lines = t.split("\n")
    at = max(n for n, l in enumerate(lines) if l.startswith("U+"))
    lines.insert(at + 1, "")
    lines.insert(at + 2, "# --- id frame and id alphabet: added for generated ids. ---")
    lines.insert(at + 3, ENTRIES.rstrip())
    io.open(S, "w", encoding="utf-8", newline="").write(
        "\n".join(lines).replace("\n", "\r\n") if crlf else "\n".join(lines))
    print("  symbols_map: рамка и алфавит записаны")
else:
    print("  symbols_map: уже есть")
