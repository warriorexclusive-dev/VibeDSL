# -*- coding: utf-8 -*-
"""unescape first, then swap the frame - in that order, and the order is the fix

The compiler turns a backslash into its glyph and puts it AFTER the quote it was
escaping:

    \"   ->   "⧵

which closes the string early. So escaping is broken in the glyph layer, and the
broken lines are exactly the ones holding the invented names. Two defects, one
cause, and the frame change dissolves both: with ▹ ◂ the quote no longer needs
escaping at all, because it is no longer the delimiter.

So the order is not cosmetic:

    1  \"  ->  "        the escape is now unnecessary, drop it
    2  "  ->  ▹ ... ◂   the quote pairs become the frame
    3  the backslash glyph ⧵ in already-compiled files is an orphan, left alone
       and reported, because removing it by hand would be editing compiled output
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = chr(0x22)
BS = chr(0x5C)
F_OPEN, F_SHUT = chr(0x25B9), chr(0x25C2)
APPLY = "--apply" in sys.argv


def convert(line):
    out = []
    esc = False
    for ch in line:
        if esc:                      # the escaped char, delivered literally
            if ch == Q:
                out.append(Q)        # keep the quote, drop the backslash
            elif ch == BS:
                out.append(BS)
            else:
                out.append(BS)
                out.append(ch)
            esc = False
            continue
        if ch == BS:
            esc = True
            continue
        out.append(ch)
    if esc:
        out.append(BS)                # a trailing lone backslash is kept

    # now the remaining quotes become the frame
    res, opened = [], False
    for ch in out:
        if ch == Q:
            res.append(F_OPEN if not opened else F_SHUT)
            opened = not opened
        else:
            res.append(ch)
    return "".join(res), opened


for name in ("win.vglyph", "window.vglyph", "win.vibe", "window.vibe"):
    p = os.path.join(ROOT, "PY_IDE", name)
    if not os.path.exists(p):
        continue
    raw = io.open(p, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")
    bad, new, unesc = [], [], 0
    for n, l in enumerate(lines, 1):
        c, unterminated = convert(l)
        unesc += l.count(BS + Q)
        if unterminated:
            bad.append(n)
        new.append(c)
    body = "\n".join(new)
    print("  %-16s кавычек %4d -> стрелок %4d   снято экранирований %3d   непарных: %s"
          % (name, raw.count(Q), body.count(F_OPEN) + body.count(F_SHUT), unesc, bad or "нет"))
    if APPLY and not bad:
        io.open(p, "w", encoding="utf-8", newline="").write(
            body.replace("\n", "\r\n") if crlf else body)
    elif bad:
        print("     ПРОПУЩЕНО: непарные в строках %s" % bad)
