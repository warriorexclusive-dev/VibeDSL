# -*- coding: utf-8 -*-
"""put the id frame and the id alphabet into the base, so the base knows them

The source of truth is the repo, and the frame plus the sixteen alphabet glyphs
were living only in a validator and in a rule. GLYPH_KNOWN would have failed any
spec that actually used an id, because an id glyph is not in the base.

Two entries, and the distinction matters:

  the FRAME is a real construct and gets a word - it is written in every id
  the ALPHABET is a generated range and gets NO word, because an id is not
    spelled and must not be renderable as text. So the range is one entry whose
    description names it, and GLYPH_KNOWN is taught that a glyph inside the
    frame is an id rather than an unknown glyph.

If the alphabet got words, the renderer would produce words for an id, the human
report would show a handle where an address belongs, and the whole reason for
the frame would be gone.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")
raw = io.open(D, encoding="utf-8-sig").read()
crlf = "\r\n" in raw
t = raw.replace("\r\n", "\n")

F_OPEN = chr(0x25B9)
F_SHUT = chr(0x25C2)
A_LO, A_HI = 0x23BE, 0x23CD
ALPHA = "".join(chr(c) for c in range(A_LO, A_HI + 1))

ENTRIES = (
    'type:behavior\n\n'
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
MARK = "type:behavior\n\n"

added = 0
if "idopen" not in t:
    t = t.replace(MARK, ENTRIES, 1)
    added = 1
if "idbase" not in t:
    added = 1
if added:
    io.open(D, "w", encoding="utf-8", newline="").write(
        t.replace("\n", "\r\n") if crlf else t)
print("  словарь: frame + alphabet записаны: %s" % bool(added))
print("  рамка   %s U+25B9   %s U+25C2" % (F_OPEN, F_SHUT))
print("  алфавит U+%04X..U+%04X = %d глифов, без слов" % (A_LO, A_HI, len(ALPHA)))
