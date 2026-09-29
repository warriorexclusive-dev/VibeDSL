# -*- coding: utf-8 -*-
"""abstract:item:id="any"-> alias  ->  glyphs

The rule for an abstract is id="any" plus a chain saying which real concept the
local name stands for. So every abstract has the same head and differs only in
the tail, which is what makes the three types comparable:

    item      -> alias
    function  -> condition
    prop      -> any:prop

Converted by lookup, never by memory - five inventions this session came from
trusting recall instead of grepping the base.
"""
import importlib.util as u
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()

LINES = [
    'abstract:item:id=unique:name-> alias',
    'abstract:function:id=unique:name-> condition',
    'abstract:prop:id=unique:name-> any:prop',
]
for src in LINES:
    out = []
    i = 0
    while i < len(src):
        if src[i] == '"':
            j = src.index('"', i + 1)
            out.append(src[i:j + 1])
            i = j + 1
            continue
        m = None
        for j in range(len(src), i, -1):
            tok = src[i:j]
            if tok in w2g:
                m = (tok, w2g[tok], j)
                break
        if m:
            out.append(m[1])
            i = m[2]
        else:
            out.append(src[i])
            i += 1
    g = "".join(out)
    missing = [c for c in g if ord(c) > 0x2000 and not c.isalpha()
               and c not in set(x for x in w2g.values() if x)]
    print("  %-40s ->  \u2022 %s%s" % (src, g, "   ПРОБЛЕМА: %s" % missing if missing else ""))
