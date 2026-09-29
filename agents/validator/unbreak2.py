# -*- coding: utf-8 -*-
"""the same two fixes, matching the escape TEXT and not the characters

Both instruments store U+2330 as the six-character sequence \\u2330 in their
source, so a search built from the character itself never matches - which is why
the previous attempt reported zero sites and zero changes and looked like it
had worked. A fix that reports "0 places" is a fix that did nothing, and it
said so plainly, which is the only reason this was caught.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

G = os.path.join(ROOT, "validator", "glyph_checker.py")
s = io.open(G, encoding="utf-8-sig").read()
old = r"(?![:" + "\\u2317" + "\\u2B1D" + "])"
new = r"(?![:" + "\\u2317" + "\\u2B1D" + "\\u02A9" + "])"
n = s.count(old)
if n:
    io.open(G, "w", encoding="utf-8", newline="").write(s.replace(old, new))
print("  glyph_checker: ʩ добавлен в lookahead, мест: %d" % n)

V = os.path.join(ROOT, "validator", "validator.py")
t = io.open(V, encoding="utf-8-sig").read()
o1 = r"\babstract\b[^\n]*?\bid="
n1 = t.count(o1)
p1 = "(?:" + chr(0x2330) + "|\\babstract\\b)[^\\n]*?\\bid="
if n1:
    t = t.replace(o1, p1)
o2 = r'\babstract\b\s+"'
n2 = t.count(o2)
p2 = "(?:" + chr(0x2330) + "|\\babstract\\b)\\s+"
if n2:
    t = t.replace(o2, p2)
io.open(V, "w", encoding="utf-8", newline="").write(t)
print("  validator.py: RE_ABSTRACT -> глиф, мест: %d + %d" % (n1, n2))
