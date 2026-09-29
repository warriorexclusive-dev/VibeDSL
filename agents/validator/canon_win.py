# -*- coding: utf-8 -*-
"""put win.vglyph in the canonical form, so the checks have something to read

win.vglyph was hand-written with the ASCII spelling where the compiler emits the
glyph: = where the base says ⩲, -> where it says →. GLYPH_CIRCLE has been
failing on it since it was written, and the reason it did not block anything is
worse than the failure: ABSTRACT_SLOT passed with nothing to look at, because
the shape it checks for is not in the file.

A check that passes because there was nothing to read is the same defect as a
check that passes because it looked for the wrong character. Both are green and
neither means anything.

The canonical form is what the compiler emits. So: write the word form, compile
it, and the glyph file is that output. No hand-canonicalising.
"""
import collections
import importlib.util as u
import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(u.module_from_spec(SP) and SP)
SP.loader.exec_module(cc)
co, cs, w2g, gl = cc.load_alias_to_glyph()
sub, _, _ = cc.build_substitution(co, cs, w2g, gl)
rx = cc.make_token_rx(sub)

GF = os.path.join(ROOT, "PY_IDE", "win.vglyph")
WF = os.path.join(ROOT, "PY_IDE", "win.vibe")

raw = io.open(GF, encoding="utf-8-sig").read()
crlf = "\r\n" in raw
lines = raw.replace("\r\n", "\n").split("\n")
st = {"replaced": 0, "words": collections.Counter(), "unmapped": set(),
      "undefined": set(), "missing_use": [], "glyphs_used": [], "noteq": set()}
out = [cc.compile_line(l, sub, rx, st, None, cc.local_names(lines)) for l in lines]
new = "\n".join(out)
n_eq = sum(1 for a, b in zip(lines, out) if a != b)
print("  строк изменено компиляцией: %d   слов заменено: %d" % (n_eq, st["replaced"]))
io.open(GF, "w", encoding="utf-8", newline="\r\n" if crlf else "\n").write(new)
io.open(WF, "w", encoding="utf-8", newline="\r\n" if crlf else "\n").write(new)
print("  ЗАПИСАНО win.vglyph (и win.vibe для сверки)")

r = subprocess.run([sys.executable, "-X", "utf8",
                    os.path.join(ROOT, "validator", "glyph_checker.py")],
                   capture_output=True, text=True, encoding="utf-8")
for l in r.stdout.split("\n"):
    t = l.strip()
    if t and (t.startswith("ok ") or t.startswith("FAIL") or "VERDICT" in t
              or "win.vglyph" in t):
        print("  " + t)
