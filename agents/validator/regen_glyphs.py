# -*- coding: utf-8 -*-
"""regenerate the glyph specs from the word specs, then set the frame

Order matters and it is the same order as always: the compiler produces the
canonical glyph form, and only then does the frame go on. Doing the frame first
left words inside the payload, because the compiler had already run before the
frame existed and nothing translated them afterwards.

    word spec --compile--> glyph spec --frame--> glyph spec, canonical

So: compile, then frame. And the frame pass unescapes first, because a spec the
compiler produced has no escapes left to break - it has a glyph where the
backslash was, which is the compiler bug the frame pass exists to absorb.
"""
import collections
import importlib.util as u
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY = "--apply" in sys.argv
Q, BS = chr(0x22), chr(0x5C)
F_OPEN, F_SHUT = chr(0x25B9), chr(0x25C2)

sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)


def frame(line):
    out, esc, opened = [], False, False
    for ch in line:
        if esc:
            out.append(Q if ch == Q else ch)
            esc = False
            continue
        if ch == BS:
            esc = True
            continue
        if ch == Q:
            out.append(F_OPEN if not opened else F_SHUT)
            opened = not opened
            continue
        out.append(ch)
    if esc:
        out.append(BS)
    return "".join(out), opened


for name in ("win", "window"):
    wf = os.path.join(ROOT, "PY_IDE", name + ".vibe")
    gf = os.path.join(ROOT, "PY_IDE", name + ".vglyph")
    if not os.path.exists(wf):
        print("  %-10s нет .vibe" % name)
        continue
    raw = io.open(wf, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")
    co, cs, w2g, gl = cc.load_alias_to_glyph()
    sub, _, _ = cc.build_substitution(co, cs, w2g, gl)
    rx = cc.make_token_rx(sub)
    loc = cc.local_names(lines)
    st = {"replaced": 0, "words": collections.Counter(), "unmapped": set(),
          "undefined": set(), "missing_use": [], "glyphs_used": [], "noteq": set()}
    out, bad, words_left = [], [], 0
    for n, l in enumerate(lines, 1):
        g = cc.compile_line(l, sub, rx, st, None, loc)
        c, unterm = frame(g)
        if unterm:
            bad.append(n)
        out.append(c)
    body = "\n".join(out)
    # what words survived inside the payload - they should be none
    for l in body.split("\n"):
        inside = l.split(F_SHUT)[0].split(F_OPEN)[-1] if F_OPEN in l else ""
        words_left += len(re.findall(r"[A-Za-z]{3,}", inside))
    print("  %-10s строк %4d  слов заменено %4d  заменено в полнозначии %4d  "
          "непарных рамок %d  слов внутри рамок %d"
          % (name, len(lines), st["replaced"],
             sum(l.count(chr(34)) for l in lines) // 2, len(bad), words_left))
    if APPLY and not bad:
        io.open(gf, "w", encoding="utf-8", newline="").write(
            body.replace("\n", "\r\n") if crlf else body)
    elif bad:
        print("     ПРОПУЩЕНО, непарные рамки в строках %s" % bad[:8])
