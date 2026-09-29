# -*- coding: utf-8 -*-
"""find 5 free glyphs for generated ids, from blocks that actually render

5 glyphs x 5 places = 3125 ids, which is plenty for a spec. But a glyph the
owner cannot see is no use: U+2B1D is in the base and did not render in the
terminal the owner reads on. So candidates are drawn only from blocks that
fonts ship by default, and anything from an exotic block is rejected on sight
rather than on principle.

Rejected outright: anything already in the base, anything the base already
distinguishes poorly, and anything whose codepoint is outside the ranges
DejaVu / Segoe UI / Consolas actually cover.
"""
import collections
import importlib.util as u
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()
used = set(g for g in w2g.values() if g)
print("  занято глифов: %d" % len(used))

# blocks that render without a symbol font
BLOCKS = [
    ("Letterlike Symbols", 0x2100, 0x214F),
    ("Arrows supplement", 0x27F0, 0x27FF),
    ("Box Drawing", 0x2500, 0x257F),
    ("Block Elements", 0x2580, 0x259F),
    ("Math Operators II", 0x27C0, 0x27EF),
    ("Geometric Shapes II", 0x25A0, 0x25FF),
    ("Misc Technical", 0x2300, 0x23FF),
    ("Control Pictures", 0x2400, 0x243F),
    ("Enclosed Alphanumerics", 0x2460, 0x24FF),
    ("Box Drawing ext", 0x2500, 0x254B),
]

# skip these: they are near-identical to something already used, or they are
# the ASCII-frame characters the language keeps on purpose
SKIP = set("░▒▓█▄▀▌▐░▓▒") | set("╱╲╳═╍╎╏┆┇┊┋") | set("⌀⌁⌂⌃⌄")

found = collections.defaultdict(list)
for name, lo, hi in BLOCKS:
    for cp in range(lo, hi + 1):
        ch = chr(cp)
        if ch in used or ch in SKIP:
            continue
        if ch.isalnum():
            continue
        found[name].append((cp, ch))

for name, items in found.items():
    print("  %-24s свободных: %d" % (name, len(items)))
print("")
print("  кандидаты по одному из каждого блока (визуально разные семейства):")
PICK = ["Box Drawing", "Block Elements", "Letterlike Symbols", "Misc Technical",
        "Control Pictures"]
picked = []
for name in PICK:
    items = found.get(name, [])
    if not items:
        continue
    cp, ch = items[len(items) // 2]
    picked.append((name, cp, ch))
for name, cp, ch in picked:
    print("     U+%04X  %s   %s" % (cp, ch, name))
print("")
print("  комбинаций при длине 5: %d" % (len(picked) ** 5))
