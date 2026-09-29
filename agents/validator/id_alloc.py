# -*- coding: utf-8 -*-
"""random id allocator with uniqueness confirmation

Sequential allocation is the wrong shape. Take ids in order and neighbours in
the list differ in ONE position - which is exactly the pair a human has to tell
apart, so the list becomes unreadable precisely where it is read. Random
allocation puts a run of ids in different parts of the space, so neighbours
differ in composition.

Three rules, all mechanical:

  1. the space is MULTISETS of length 1..5, not permutations. A run reads as
     one token, so ┿┿┿┿┿ means "five of ┿" and order carries no information.
     With k=5 that is 251, not 3125. 251 is plenty for a spec, so readability
     costs nothing here.
  2. ids are emitted in CANONICAL order, fixed by the ranking of the glyph in
     the base. ┿┿⇗ and ⇗┿┿ are the same id, so an ordering slip would change
     meaning silently - the reverscheck failure, but on order.
  3. uniqueness is confirmed, not assumed: against every id in every spec, and
     within the drawn set, and no two drawn ids may differ in a single
     position, because that is the pair that reads worst.
"""
import itertools
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = ".vglyph"
ID = chr(0x00A7)
ASSIGN = chr(0x2A72)
Q = chr(0x22)

# 2 confirmed on the owner machine. The remaining three must be confirmed before
# this has room: with k=2 the space is 2+3+4+5+6 = 20, which does not cover 46.
FRAME_OPEN = chr(0x25B9)   # renders confirmed; points INTO the content
FRAME_SHUT = chr(0x25C2)   # renders confirmed; points INTO the content
# Swapped from the first proposal. A bracket points inward, a guillemet points
# outward, and inward reads as a bracket - so the record inside is bracketed
# rather than quoted. Open is hollow, close is filled, so in one colour the two
# still differ by fill as well as by direction.

# The id alphabet is one CONTIGUOUS run, U+23BE..U+23CD, sixteen glyphs, all
# confirmed on the owner machine. Contiguous is the whole point: an id is
# recognisable by shape, and the dictionary can never take this piece because
# the piece is defined as "everything in this range". The two glyphs confirmed
# earlier, U+2387 and U+253F, are outside the run and are dropped in favour of
# a single block - a set of scattered glyphs has no checkable property, a
# range does.
ALPHABET = [chr(c) for c in range(0x23BE, 0x23CE)]
CANON = {g: i for i, g in enumerate(sorted(ALPHABET))}
MAXLEN = 5


def space(alpha):
    out = []
    for n in range(1, MAXLEN + 1):
        for combo in itertools.combinations_with_replacement(alpha, n):
            out.append("".join(sorted(combo, key=lambda g: CANON[g])))
    return out


def existing_ids():
    """ids per SPEC, not across all specs

    An id exists only inside its own spec. Two specs may both carry the same id
    and that is not a collision, so pooling every id from the whole repository
    and calling it a conflict was checking something that does not exist as a
    rule. Which is also why no registry is needed: uniqueness is read off the
    spec, there is no second copy to drift, and the "duplicates across files"
    worry was mine, not the language's.
    """
    per = {}
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and d not in ("temp", ".git", "GLOS", "node_modules", "__pycache__")]
        for f in sorted(files):
            if f.endswith(EXT):
                p = os.path.join(base, f)
                txt = io.open(p, encoding="utf-8-sig").read()
                pat = re.escape(ID) + re.escape(ASSIGN) + Q + "([^" + Q + "]+)" + Q
                per[p.replace(ROOT + os.sep, "").replace(os.sep, "/")] = set(
                    re.findall(pat, txt))
    return per


def near(a, b):
    """one position apart - the pair that reads worst"""
    if len(a) != len(b):
        return False
    return sum(1 for x, y in zip(a, b) if x != y) == 1


def draw(n, alpha, taken):
    pool = [s for s in space(alpha) if s not in taken]
    if not pool:
        return []
    rng = random.Random()
    rng.shuffle(pool)
    out = []
    for cand in pool:
        if any(near(cand, k) for k in out):
            continue
        out.append(cand)
        if len(out) >= n:
            break
    return out


def main():
    want = 8
    if "--n" in sys.argv:
        want = int(sys.argv[sys.argv.index("--n") + 1])
    alpha = list(ALPHABET)
    sp = space(alpha)
    per = existing_ids()
    taken = set()
    for v in per.values():
        taken |= v
    print("  алфавит      : %s   (k=%d, подтверждено на машине владельца: 2)"
          % ("".join(alpha), len(alpha)))
    print("  длина        : 1..%d, мультимножества" % MAXLEN)
    print("  пространство : %d" % len(sp))
    print("  занято по спекам: %s"
          % (", ".join("%s=%d" % (k, len(v)) for k, v in per.items()) or "-"))
    print("  всего занято: %d" % len(taken))
    print("  свободно     : %d" % len([s for s in sp if s not in taken]))
    got = draw(want, alpha, taken)
    print("")
    print("  выдано %d (без соседних отличий в одну позицию):" % len(got))
    for g in got:
        mark = " (форма слова, в глифах: %s)" % "".join(
            CANON and "?" for _ in g) if False else ""
        print("     %s" % g)
    print("")
    if len(alpha) < 5:
        print("  ВНИМАНИЕ: при k=%d пространство %d - на 46 абстрактов не хватает."
              % (len(alpha), len(sp)))
        print("  Нужно подтвердить ещё %d глифа из Misc Technical." % (5 - len(alpha)))
    return 0


if __name__ == "__main__":
    import io
    sys.exit(main())
