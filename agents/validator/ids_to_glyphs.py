# -*- coding: utf-8 -*-
"""readable ids -> generated 4-glyph ids, 16 of 16, spec-local

Confirmed: length 4, alphabet U+23BE..U+23CD, order significant, 16^4 = 2^16.
Spec-local, so the same id string in two specs gets two different addresses -
that is what "local" means, and it is why no registry is needed.

The frame has to be NESTED and that is the thing worth getting right. An id sits
inside a framed action:

    action   ⁐⩲▹ ▱:⊂:⇐(▹⎾⏀⏆⏌◂) ◂
                    ^^^^^^^^^^ an id, framed, inside the action's frame

So the frame pass counts DEPTH. A boolean toggle - which is what the previous
pass used - emits the closing arrow at the wrong place the moment there is more
than one level, and it would look correct until the third line.
"""
import collections
import importlib.util as u
import io
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q, BS = chr(0x22), chr(0x5C)
F_OPEN, F_SHUT = chr(0x25B9), chr(0x25C2)
ALPHA = [chr(c) for c in range(0x23BE, 0x23CE)]
LEN = 4
APPLY = "--apply" in sys.argv


def deep_frame(line):
    out, esc, depth = [], False, 0
    for ch in line:
        if esc:
            out.append(Q if ch == Q else ch)
            esc = False
            continue
        if ch == BS:
            esc = True
            continue
        if ch == Q:
            out.append(F_OPEN if depth == 0 else F_SHUT)
            depth += 1 if depth == 0 else -1
            continue
        out.append(ch)
    if esc:
        out.append(BS)
    return "".join(out), depth


def near(a, b):
    return len(a) == len(b) and sum(1 for x, y in zip(a, b) if x != y) == 1


for name in ("win", "window"):
    p = os.path.join(ROOT, "PY_IDE", name + ".vibe")
    if not os.path.exists(p):
        continue
    raw = io.open(p, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")

    # ids are already framed from the previous pass, so look for a frame whose
    # content is purely word characters - that is an id, an action never is.
    # Everything inside the frame is a local declaration and all of it becomes
    # glyphs - an id, a name, a free word. There is no class among them that has
    # to stay readable, because a name may legitimately hold a human word coming
    # in from a blueprint, and a generated id cannot be misspelled. A proto or
    # blueprint id stays readable, and it is OUTSIDE the frame: that is what
    # makes the frame the whole answer rather than half of one.
    RX_ID = re.compile(re.escape(F_OPEN) + r"([A-Za-z_]\w*)" + re.escape(F_SHUT))
    ids, seen = [], set()
    for l in lines:
        for m in RX_ID.finditer(l):
            if m.group(1) not in seen:
                seen.add(m.group(1))
                ids.append(m.group(1))

    rng = random.Random(0x23BE)
    used, mapping = set(), {}
    for i in ids:
        while True:
            cand = "".join(rng.choice(ALPHA) for _ in range(LEN))
            if cand in used:
                continue
            if any(near(cand, u) for u in used):
                continue
            used.add(cand)
            mapping[i] = cand
            break

    out, bad = [], 0
    for l in lines:
        l = RX_ID.sub(lambda m: F_OPEN + mapping.get(m.group(1), m.group(1)) + F_SHUT, l)
        c, depth = deep_frame(l)
        if depth:
            bad += 1
        out.append(c)
    body = "\n".join(out)
    print("  %-8s id %3d -> глифов %3d   пример: %s = %s%s%s   дисбаланс рамок в %d строк"
          % (name, len(ids), len(ALPHA), ids[0] if ids else "-",
             F_OPEN, mapping[ids[0]] if ids else "-", F_SHUT, bad))
    if APPLY and not bad:
        io.open(p, "w", encoding="utf-8", newline="").write(
            body.replace("\n", "\r\n") if crlf else body)
    elif bad:
        print("     ПРОПУЩЕНО")
