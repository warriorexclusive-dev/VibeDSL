# -*- coding: utf-8 -*-
"""ID_FRAME: bind the id alphabet to the inward arrows, both directions

Defining FRAME_OPEN and FRAME_SHUT as constants binds nothing. Binding is two
checks, and both directions, because either alone is a check that can pass for
the wrong reason - which is how GLYPH_ONE passed while looking for U+2310
instead of U+2330, and how ABSTRACT_SLOT passed with nothing to read:

  inside the frame   only alphabet glyphs        ▹ ⎾⏀⏆ ◂  ok
                     ▹ ⎾⏀ ▶ ◂                   not ok - ▶ is a concept
  outside the frame  never an alphabet glyph     ⏆⏀ bare   not ok
                     a bare ⏀ is not an id, it is a typo with no claim

The second direction is the one that matters. A bare alphabet glyph looks
exactly like a concept, which is the whole failure this session: five invented
words that read as real ones. Inside the frame it is declared local; outside it
is not declared at all.
"""
import io
import re

P = "validator/glyph_checker.py"
CHECK = '''    # ID_FRAME - the id alphabet only exists inside the inward arrows
    e = []
    ID_ALPHA = "".join(chr(c) for c in range(0x23BE, 0x23CE))
    F_OPEN, F_SHUT = chr(0x25B9), chr(0x25C2)
    for p in REFS:
        s = read(p)
        if not s:
            continue
        # direction 1: framed content must be alphabet only
        for m in re.finditer(re.escape(F_OPEN) + r"([^" + re.escape(F_SHUT) + r"]*)"
                             + re.escape(F_SHUT), s):
            bad = [c for c in m.group(1) if c not in ID_ALPHA]
            if bad:
                ln = s[:m.start()].count("\\n") + 1
                e.append("%s:%d framed id contains non-alphabet %s"
                         % (p, ln, "".join(sorted(set(bad)))))
        # direction 2: an alphabet glyph outside the frame is not an id
        stripped = re.sub(re.escape(F_OPEN) + r"[^" + re.escape(F_SHUT) + r"]*"
                          + re.escape(F_SHUT), "", s)
        for m in re.finditer("[" + re.escape(ID_ALPHA) + "]+", stripped):
            ln = stripped[:m.start()].count("\\n") + 1
            e.append("%s:%d alphabet glyph %r outside the frame - a bare one is"
                     " not an id, it is a typo with no claim" % (p, ln, m.group(0)))
    check("ID_FRAME", e, "id lives only between the inward arrows, both ways")

'''
MARK = "    # GLYPH_COVER"
s = io.open(P, encoding="utf-8-sig").read()
if "ID_FRAME" in s:
    print("  уже есть")
else:
    io.open(P, "w", encoding="utf-8", newline="").write(s.replace(MARK, CHECK + MARK))
    print("  ID_FRAME добавлен")
