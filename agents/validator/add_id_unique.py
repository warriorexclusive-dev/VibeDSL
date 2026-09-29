# -*- coding: utf-8 -*-
"""ID_UNIQUE - the check the generator has no right to skip

The generator picks ids, so the generator is the last party that should be
trusted to pick them well. Uniqueness is checked where the ids actually live, in
the spec, and three things have to hold at once:

  no repeats            two declarations must not share an address
  no near misses        two ids differing in ONE position are the pair a reader
                        has to tell apart, so they are the pair that must never
                        be allocated together
  per spec, not global  ids are local, so the same address in another spec is
                        not a collision and must not be reported as one

A check that reported cross-file duplicates would have been a false red for the
same reason the earlier ones were.
"""
import io
import os
import re

P = "validator/glyph_checker.py"
CHECK = '''    # ID_UNIQUE - addresses are local, unique, and never a near miss
    e = []
    F_O, F_S = chr(0x25B9), chr(0x25C2)
    ALPHA = set(chr(c) for c in range(0x23BE, 0x23CE))
    RX = re.compile(re.escape(F_O) + r"([%s%s]+)" % ("", "") + re.escape(F_S)
    for p in REFS:
        s = read(p)
        if not s:
            continue
        found = re.findall(re.escape(F_O) + r"([^" + re.escape(F_S) + r"]*)"
                           + re.escape(F_S), s)
        addrs = [f for f in found if f and set(f) <= ALPHA]
        seen = {}
        for a in addrs:
            if a in seen:
                e.append("%s: address %r twice, lines %d and %d"
                         % (p, a, seen[a], s[:s.index(a)].count("\\n") + 1))
            else:
                seen[a] = s[:s.index(a)].count("\\n") + 1
        for i, a in enumerate(addrs):
            for b in addrs[i + 1:]:
                if len(a) == len(b) and sum(1 for x, y in zip(a, b) if x != y) == 1:
                    e.append("%s: %r and %r differ in one position - the pair a "
                             "reader must tell apart" % (p, a, b))
    check("ID_UNIQUE", e, "addresses are local, unique, and no near miss")

'''
MARK = "    # GLYPH_COVER"
s = io.open(P, encoding="utf-8-sig").read()
if "ID_UNIQUE" in s:
    print("  уже есть")
else:
    io.open(P, "w", encoding="utf-8", newline="").write(s.replace(MARK, CHECK + MARK))
    print("  ID_UNIQUE добавлен")
