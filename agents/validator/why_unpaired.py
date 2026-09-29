# -*- coding: utf-8 -*-
"""why the glyph file has unpaired quotes and the word file does not

Same total quote count, different per-line distribution. So the compiler moved
one, and the only way it does that is by treating a backslash as an escape -
which it does, and my converter does too, but the ESCAPE ITSELF became a glyph.

A literal backslash in a word spec is the concept backslash, so the compiler
emits its glyph. That glyph is not a backslash character, so nothing looks like
an escape any more - except that the compiler's own quote scanner may still
honour it, which would put the two readers out of step.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = chr(0x22)
BS = chr(0x5C)
BSGLYPH = chr(0x2B35)          # whatever the map gives for backslash

for name, lines_want in (("window.vibe", [70, 73, 76]), ("window.vglyph", [70, 73, 76])):
    p = os.path.join(ROOT, "PY_IDE", name)
    if not os.path.exists(p):
        continue
    L = io.open(p, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
    print("  %s" % name)
    for n in lines_want:
        if n - 1 < len(L):
            l = L[n - 1]
            print("     %4d  кавычек %d  обратных слэшей %d  глифов-слэшей %d"
                  % (n, l.count(Q), l.count(BS), l.count(BSGLYPH)))
            print("           %s" % l.strip()[:96])
    print("")
