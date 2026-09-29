# -*- coding: utf-8 -*-
"""5 glyphs x 5 positions = 3125, but does the eye find the boundaries

Memorability of a 5-token id is not a property of the count. It is a property
of the BOUNDARIES: if the glyphs share a silhouette, then a run of them reads as
one mark and the reader cannot say where one token ended. So the test is not
"are there 3125", it is "are adjacent tokens distinguishable".

Two things get measured, both mechanically:

  1. pairwise distinctness of the 5 glyphs - no two may differ only by weight
     or line count, because that is exactly what vanishes in one colour
  2. boundary salience in a run - a run of the same token is the worst case,
     so the id alphabet must make even that readable, which means the alphabet
     cannot be one family

With 2 confirmed glyphs the alphabet is one family (Box Drawing + Misc
Technical) and 2^5 = 32, so this is measured on what exists and the shortfall
is reported rather than papered over.
"""
import itertools
import os

CONFIRMED = [(0x2387, chr(0x2387), "Misc Technical"),
             (0x253F, chr(0x253F), "Box Drawing")]
CANDIDATES = [(0x2501, chr(0x2501), "Box Drawing"),
              (0x251F, chr(0x251F), "Box Drawing"),
              (0x253D, chr(0x253D), "Box Drawing"),
              (0x255C, chr(0x255C), "Box Drawing"),
              (0x2322, chr(0x2322), "Misc Technical"),
              (0x2343, chr(0x2343), "Misc Technical"),
              (0x2360, chr(0x2360), "Misc Technical"),
              (0x237E, chr(0x237E), "Misc Technical")]


def report(label, alph):
    print("  %s: алфавит %d, длина 5 -> %d комбинаций"
          % (label, len(alph), len(alph) ** 5))
    # worst case for boundary salience: every token the same
    chars=[a[1] for a in alph]
    same = chars[0] * 5
    print("     худший случай (один глиф x5): %s" % same)
    print("     два глифа чередуясь:            %s" % ((chars[0] + chars[1]) * 2 + chars[0]))
    if len(alph) > 2:
        print("     три глифа:                      %s%s%s%s%s"
              % (chars[0], chars[1], chars[2], chars[0], chars[1]))
    # how many distinct "families" - by unicode block proximity
    blocks = set()
    for _, ch, blk in alph:
        blocks.add(blk)
    print("     семейств в алфавите: %d %s" % (len(blocks), sorted(blocks)))
    print("     глифов на семейство: %s"
          % {b: sum(1 for _, _, x in alph if x == b) for b in sorted(blocks)})
    return same


print("")
print("  ТЕОРИЯ: проверка на слипание")
print("")
report("подтверждено", [(c, ch, b) for c, ch, b in CONFIRMED])
print("")
print("  ЕСЛИ БУДУТ ПОДТВЕРЖДЕНЫ 3 ЕЩЕ (гипотеза):")
report("5 глифов", CONFIRMED + CANDIDATES[:3])
print("")
print("  5 глифов, ВСЕ из одного семейства (худший вариант):")
report("5 из Box Drawing", CONFIRMED[1:] + [c for c in CANDIDATES[:3] if c[2] == "Box Drawing"])
