# -*- coding: utf-8 -*-
"""unbreak the two word-keyed instruments: the check's lookahead, and validator

Both looked at the name and not the concept, and both fell over on a rename
nobody had any business being afraid of.

  glyph_checker  the type lookahead listed prop and item and forgot FUNCTION,
                 so every declaration of a function read as "no type" - 4 false
  validator.py   RE_ABSTRACT matched the word abstract, so after the rename it
                 matched nothing at all and parse_abstract saw an empty spec.
                 That is why SPELL and SYMBOLS failed: not a broken spec, a
                 blind validator.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- 1. the lookahead, missing U+02A9 function ----------------------------
G = os.path.join(ROOT, "validator", "glyph_checker.py")
s = io.open(G, encoding="utf-8-sig").read()
old = "(?![:" + chr(0x2317) + chr(0x2B1D) + "])"
new = "(?![:" + chr(0x2317) + chr(0x2B1D) + chr(0x02A9) + "])"
n = s.count(old)
io.open(G, "w", encoding="utf-8", newline="").write(s.replace(old, new))
print("  glyph_checker: в lookahead добавлен ʩ (function), мест: %d" % n)

# --- 2. validator.py, word -> concept -------------------------------------
V = os.path.join(ROOT, "validator", "validator.py")
t = io.open(V, encoding="utf-8-sig").read()
before = t
# the compiled form carries the glyph, so accept the glyph as well as the word
t = t.replace(r'\babstract\b[^\n]*?\bid="([^"]+)"|\babstract\b\s+"([^"]+)"',
              '(?:%s|\\babstract\\b)[^\\n]*?\\bid="([^"]+)"|'
              '(?:%s|\\babstract\\b)\\s+"([^"]+)"' % (chr(0x2330), chr(0x2330)))
io.open(V, "w", encoding="utf-8", newline="").write(t)
print("  validator.py: RE_ABSTRACT принимает глиф, изменено: %s"
      % (t != before))

# and the word forms that follow it, so a word spec still parses
t2 = io.open(V, encoding="utf-8-sig").read()
for name in ("TYPE_SYMS",):
    m = re.search(r"(?m)^%s\s*=\s*(.+)$" % name, t2)
    if m:
        print("  %s = %s" % (name, m.group(1)[:70]))
