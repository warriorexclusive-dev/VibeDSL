# -*- coding: utf-8 -*-
"""compiler/ids.txt - the ledger of issued addresses, owned by the compiler

Six duplicates today came from two mistakes of mine in one place: the seed was
a constant, so both specs drew the same first address, and nothing checked
cand in used at all, so an address already taken was drawn again.

A ledger fixes both, and it is not the unowned second copy that worried me
earlier. It has an owner: the compiler. The compiler draws from it, appends to
it with write, and ID_UNIQUE can compare it against the specs. A file that
nobody maintains is a second truth; a file the compiler maintains is a
counter.

Format: one address per line, nothing else. No ids, no timestamps, no names -
those live in the specs, and a ledger that duplicated them would be a copy
waiting to drift.
"""
import io
import os
import random
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "compiler", "ids.txt")
F_OPEN, F_SHUT = chr(0x25B9), chr(0x25C2)
ALPHA = [chr(c) for c in range(0x23BE, 0x23CE)]
LEN = 4
SEED = 0x23BE


def read_ledger():
    if not os.path.exists(LEDGER):
        return []
    out = []
    for l in io.open(LEDGER, encoding="utf-8").read().replace("\r\n", "\n").split("\n"):
        l = l.strip()
        if l and set(l) <= set(ALPHA):
            out.append(l)
    return out


def near(a, b):
    return len(a) == len(b) and sum(1 for x, y in zip(a, b) if x != y) == 1


def draw(n, issued):
    rng = random.Random(SEED)
    used = set(issued)
    out = []
    while len(out) < n:
        cand = "".join(rng.choice(ALPHA) for _ in range(LEN))
        if cand in used:                      # <- the check that was missing
            continue
        if any(near(cand, k) for k in used):
            continue
        used.add(cand)
        out.append(cand)
    return out


if not os.path.exists(LEDGER):
    io.open(LEDGER, "w", encoding="utf-8", newline="\n").write("")
    print("  создан %s" % LEDGER)

issued = read_ledger()
print("  реестр: %s   уже выдано: %d" % (LEDGER, len(issued)))

for name in ("win", "window"):
    # the GLYPH form, not the word one. The word spec keeps its readable names
    # for the human - id="controller_bar" - and that is where they live for
    # good. The address exists only in the canonical glyph form. This is the two
    # ends of one thing, and it is why the names are not destroyed by issuing:
    # they were never in the file being rewritten.
    p = os.path.join(ROOT, "PY_IDE", name + ".vglyph")
    if not os.path.exists(p):
        continue
    raw = io.open(p, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")
    RX = re.compile(re.escape(F_OPEN) + r"([A-Za-z_]\w*)" + re.escape(F_SHUT))
    ids, seen = [], set()
    for l in lines:
        for m in RX.finditer(l):
            if m.group(1) not in seen:
                seen.add(m.group(1))
                ids.append(m.group(1))
    mapping = {i: d for i, d in zip(ids, draw(len(ids), issued))}
    body, bad = [], 0
    for l in lines:
        l = RX.sub(lambda m: F_OPEN + mapping.get(m.group(1), m.group(1)) + F_SHUT, l)
        d = l.count(F_OPEN) - l.count(F_SHUT)
        if d:
            bad += 1
        body.append(l)
    if bad:
        print("  %-8s ПРОПУЩЕНО, дисбаланс рамок в %d строк" % (name, bad))
        continue
    io.open(p, "w", encoding="utf-8", newline="").write(
        ("\n".join(body).replace("\n", "\r\n")) if crlf else "\n".join(body))
    fresh = list(mapping.values())
    with io.open(LEDGER, "a", encoding="utf-8", newline="\n") as fh:
        for a in fresh:
            fh.write(a + "\n")
    print("  %-8s id %3d   выдано %3d   пример %s = %s%s%s   в реестр записано"
          % (name, len(ids), len(fresh), ids[0] if ids else "-",
             F_OPEN, mapping[ids[0]] if ids else "-", F_SHUT))
