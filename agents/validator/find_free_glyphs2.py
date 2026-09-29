# -*- coding: utf-8 -*-
"""three more, from the two blocks that are PROVEN to render on the owner's machine

Observed, not assumed: of five candidates, U+2387 (Misc Technical) and U+253F
(Box Drawing) render, and U+258F (Block Elements), U+2125 (Letterlike) and
U+241E (Control Pictures) do not. So the search is confined to the two proven
blocks rather than to blocks that are theoretically safe. A glyph the owner
cannot see is a glyph that cannot be in a rule they must follow.

They must also be told apart at a glance, so the pick spans orientations: one
horizontal, one vertical, one diagonal. Box Drawing has 113 free, Misc
Technical 234, so there is room to be picky.
"""
import collections
import importlib.util as u
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()
used = set(g for g in w2g.values() if g)

PROVEN = [("Box Drawing", 0x2500, 0x257F), ("Misc Technical", 0x2300, 0x23FF)]

# orientation buckets, so the three are not three neighbours
def bucket(ch):
    v = ord(ch)
    if v in (0x2571, 0x2572) or 0x2571 <= v <= 0x2573:
        return "diag"
    if v in (0x2500, 0x2501, 0x2504, 0x2505, 0x2508, 0x2509, 0x254C, 0x254D,
             0x2550, 0x2554, 0x2558, 0x255C, 0x2560, 0x2563, 0x2566, 0x2569,
             0x256C, 0x2570, 0x2574):
        return "horiz"
    if 0x2502 <= v <= 0x2503 or 0x2506 <= v <= 0x2507 or 0x250A <= v <= 0x250B \
       or 0x2551 <= v <= 0x2553 or 0x2555 <= v <= 0x2557 or 0x255B <= v <= 0x255D \
       or 0x255F <= v <= 0x2561 or 0x2564 <= v <= 0x2568 or 0x256A <= v <= 0x256B \
       or 0x256D <= v <= 0x256F:
        return "vert"
    return None

free = []
for name, lo, hi in PROVEN:
    for cp in range(lo, hi + 1):
        ch = chr(cp)
        if ch in used or ch.isalnum():
            continue
        free.append((cp, ch, name, bucket(ch)))

by = collections.defaultdict(list)
for cp, ch, name, b in free:
    by[b].append((cp, ch, name))
print("  свободных в доказанных блоках: %d" % len(free))
for b in ("horiz", "vert", "diag", None):
    print("     %-6s %d" % (b or "прочее", len(by[b])))

PICK = []
for b in ("horiz", "vert", "diag"):
    items = by.get(b) or []
    if items:
        cp, ch, name = items[len(items) // 2]
        PICK.append((b, cp, ch, name))
print("")
print("  три кандидата, по одному на ориентацию:")
for b, cp, ch, name in PICK:
    print("     U+%04X  %s  %-8s %s" % (cp, ch, b, name))
allp = [("U+2387", "⎇"), ("U+253F", "┿")] + [("U+%04X" % cp, ch) for _, cp, ch, _ in PICK]
print("")
print("  итого 5 глифов: %s" % " ".join(c for _, c in allp))
print("  комбинаций при длине 5: %d" % (len(allp) ** 5))
