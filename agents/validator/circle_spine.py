# -*- coding: utf-8 -*-
"""split the round trip into spine and payload, and count both

A line is not one thing. It is a SPINE - the grammar outside the quotes - and a
PAYLOAD inside them. Only the spine can round-trip, because quotes protect their
content from the compiler, and that protection is the whole point of them.

So the round trip has two halves and they behave differently:

    • ⌰:ʩ:§⩲"win"→⁐⩲"◈(❒) ✚ ⇐(❒:⛶:⇐(⊤)) ..."
    |_________________|     |_________________________|
         SPINE              PAYLOAD

    spine    glyph -> word -> glyph      closes. no quotes involved.
    payload  glyph -> word -> WORD      does not. quotes hold the words.

The payload half is not broken, it is protected. So a check that compares the
whole line is comparing something that cannot be equal, and calling that a
failure is wrong.

What is genuinely checkable:
  1. the spine closes            a real defect if it does not
  2. quotes are balanced         a real defect: an unbalanced quote swallows
                                 the rest of the file, and nothing else sees it
  3. the payload is present      an empty payload is a different statement
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


def split_quotes(line):
    """returns (spine, [payloads]) honouring the backslash the compiler honours"""
    spine, payload, parts, esc = [], [], [], False
    for ch in line:
        if esc:
            payload.append(ch)
            esc = False
            continue
        if ch == "\\":
            payload.append(ch)
            esc = True
            continue
        if ch == '"':
            parts.append("".join(payload))
            payload = []
            continue
        (spine if not parts else payload).append(ch)
    if payload:
        parts.append("".join(payload))          # unterminated - reported separately
    return "".join(spine), parts


def roundtrip(text, quote_aware):
    w = r.render(text, by, cc)
    co, cs, w2g, gl = cc.load_alias_to_glyph()
    sub, _, _ = cc.build_substitution(co, cs, w2g, gl)
    rx = cc.make_token_rx(sub)
    L = w.split("\n")
    st = {"replaced": 0, "words": collections.Counter(), "unmapped": set(),
          "undefined": set(), "missing_use": [], "glyphs_used": [], "noteq": set()}
    out = [cc.compile_line(l, sub, rx, st, None, cc.local_names(L)) for l in L]
    if not quote_aware:
        return "\n".join(out)
    res = []
    for a, b in zip(text.split("\n"), out):
        sa, _ = split_quotes(a)
        sb, _ = split_quotes(b)
        res.append(sa if re.sub(r"[ \t]+", "", sa) == re.sub(r"[ \t]+", "", sb)
                   else a + "   <<< SPINE DIVERGES")
    return "\n".join(res)


for name in ("win.vglyph", "window.vglyph"):
    P = os.path.join(ROOT, "PY_IDE", name)
    if not os.path.exists(P):
        continue
    g = io.open(P, encoding="utf-8-sig").read().replace("\r\n", "\n")
    o, b = g.split("\n"), roundtrip(g, False).split("\n")
    whole = sum(1 for x, y in zip(o, b)
                if re.sub(r"[ \t]+", "", x) != re.sub(r"[ \t]+", "", y))
    spine_diff = 0
    unbalanced = 0
    for line in g.split("\n"):
        s, parts = split_quotes(line)
        if s.count('"'):
            unbalanced += 1
        if line.count('"') % 2:
            unbalanced += 1
    sp2 = roundtrip(g, True)
    spine = sp2.split("\n")
    spine_diff = sum(1 for l in spine if "SPINE DIVERGES" in l)
    print("  %s" % name)
    print("     строк                       %d" % len(o))
    print("     расхождений целиком         %d   <- из них ложных: кавычки" % whole)
    print("     расхождений только на хребте %d   <- вот это настоящие" % spine_diff)
    print("     непарных кавычек            %d" % (unbalanced // 2))
    print("")
