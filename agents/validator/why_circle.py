# -*- coding: utf-8 -*-
"""find the real cause of GLYPH_CIRCLE on win.vglyph

The standing hypothesis: a glyph is missing from the map the renderer reads, so
it never renders back and the circle cannot close. That is testable and cheap -
ask the renderer which glyphs in the file it does not know.

If they all know their glyphs, the hypothesis is wrong and the divergence is
something else, so print the first diverging line as well. Doing both at once
stops another round of guessing at a cause nobody has looked at.
"""
import collections
import importlib.util as u
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = u.spec_from_file_location("_r", os.path.join(ROOT, "PY_IDE", "render.py"))
r = u.module_from_spec(sp)
sp.loader.exec_module(r)
cc, by = r.glyph_to_word()

P = os.path.join(ROOT, "PY_IDE", "win.vglyph")
g = io.open(P, encoding="utf-8-sig").read().replace("\r\n", "\n")

UNKNOWN = [c for c in dict.fromkeys(g) if ord(c) > 0x2000 and c not in by]
print("  глифов в файле, которых НЕТ в карте рендера: %d" % len(UNKNOWN))
for c in UNKNOWN:
    print("     U+%04X  %s" % (ord(c), c))
print("  слов в карте рендера: %d" % len(by))

w = r.render(g, by, cc)
co, cs, w2g, gl = cc.load_alias_to_glyph()
sub, _, _ = cc.build_substitution(co, cs, w2g, gl)
rx = cc.make_token_rx(sub)
L = w.split("\n")
st = {"replaced": 0, "words": collections.Counter(), "unmapped": set(),
      "undefined": set(), "missing_use": [], "glyphs_used": [], "noteq": set()}
back = [cc.compile_line(l, sub, rx, st, None, cc.local_names(L)) for l in L]
o = g.split("\n")
print("")
n = 0
for i, (a, b) in enumerate(zip(o, back)):
    if re.sub(r"[ \t]+", "", a) != re.sub(r"[ \t]+", "", b):
        n += 1
        if n <= 4:
            print("  строка %d" % (i + 1))
            print("     глифы  : %r" % a.strip()[:100])
            print("     обратно: %r" % b.strip()[:100])
            # which glyphs in that line are unknown to the renderer
            bad = [c for c in a if ord(c) > 0x2000 and c not in by]
            if bad:
                print("     В НЕИЗВЕСТНЫХ: %s" % "".join(bad))
print("  расхождящихся строк: %d из %d" % (n, len(o)))
