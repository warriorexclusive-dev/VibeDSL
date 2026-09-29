# -*- coding: utf-8 -*-
"""the four checks that keyed on the WORD, rebound to the GLYPH

Renaming abstract to virtual moved the name, not the concept, and four checks
fell over. All four were reading the spelling: ABSTRACT_TYPE, ABSTRACT_SLOT,
ID_FRAME, ID_UNIQUE. That is the defect this whole session was about - an
instrument pointed at the label instead of the thing - and it is why a rename
they had every right to make broke the measurement.

U+2330 is the concept. It was called abstract and is now called virtual and will
be called something else next year, and the check must not notice. So the glyph
goes in and the word comes out, including in the messages.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "validator", "glyph_checker.py")
A = chr(0x2330)

s = io.open(P, encoding="utf-8-sig").read()
before = s

# the check id and every message that names the old word
s = s.replace("ABSTRACT_TYPE", "ABSTRACT_TYPE")          # keep the id: it is about the type rule
s = re.sub(r'"(\\u2310|U\+2310)', lambda m: '"\\u2330', s)
s = s.replace("abstract \\u2310 with no type", "declaration U+2330 with no type")
s = s.replace("\\u2310 always carries", "U+2330 always carries")
s = s.replace("head is one of two legal shapes", "head is one of two legal shapes")

if s != before:
    io.open(P, "w", encoding="utf-8", newline="").write(s)
    print("  глиф_чекер: привязан к глифу вместо слова")

n = sum(1 for l in s.replace("\r\n", "\n").split("\n") if "2310" in l)
print("  осталось упоминаний U+2310: %d   (это отрицание, а не абстракт)" % n)
for l in s.replace("\r\n", "\n").split("\n"):
    if "2310" in l:
        print("     %s" % l.strip()[:86])
