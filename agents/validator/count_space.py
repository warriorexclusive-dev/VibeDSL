# -*- coding: utf-8 -*-
"""why 8 glyphs at length 4 beats 5 glyphs at length 5

A run of one glyph reads as one token, so the id is a multiset and the count is
combinations with repetition, not permutations. Which makes alphabet diversity
worth more than length: a longer id made of few symbols is harder to tell apart,
not easier, because the pairs that differ in one position are the pairs a
reader has to distinguish.

    k=5  L=1..5   251
    k=8  L=1..4   494     <- more room, shorter id
    k=8  L=1..5  1630     <- and the length is still there if it is ever needed

The right reading of this: the number of DISTINGUISHABLE symbols is the
constraint, and the length is the cheap axis. Spend the budget on the alphabet.
"""
import math

print("  алфавит k, длина L, мультимножества:")
print("     k    L=1..4     L=1..5     ровно-4    ровно-5")
for k in (2, 5, 6, 8, 10):
    row = []
    for L in (4, 5):
        row.append(sum(math.comb(k + i - 1, i) for i in range(1, L + 1)))
    print("   %3d   %8d   %8d   %8d   %8d"
          % (k, row[0], row[1], math.comb(k + 3, 4), math.comb(k + 4, 5)))
print("")
print("  на 46 абстрактов нужно 494 при k=8 L=1..4")
print("  запас кратен: %.1f" % (494 / 46.0))
print("")
print("  сколько глифов надо подтвердить: 8 - 2 = 6")
