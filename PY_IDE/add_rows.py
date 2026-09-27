# -*- coding: utf-8 -*-
"""insert the two new glyph rows into symbols_map

The table is loosely ordered, not strictly by codepoint, so a new row goes next
to its neighbours rather than at a computed offset. U+2A1B sits among the U+2A1x
rows and U+2B1F among the U+2B1x-2B2x rows.
"""
import io
import sys

S = "compiler/symbols_map.txt"
PROC_DESC = ("mapping of a process name: an isolated execution space with its own data, "
             "the C++ sense of Process; NOT a command, the name maps, so "
             "check(process:collision) reads the process named collision")
COLL_DESC = ("logical mapping collision operator: reachable from a process and from a 3D "
             "vector, and deliberately not defined more precisely - a precise definition "
             "would distort the vector, and the vector is the more general of the two")
NEW = [
    ("U+2A1D   ⨝  *-> grp", "U+2A1B ⨛ *-> collision - " + COLL_DESC),
    ("U+2B20   ⬠  *-> model", "U+2B1F   ⬟  *-> process - " + PROC_DESC),
]


def main():
    apply = "--apply" in sys.argv
    raw = io.open(S, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")
    for anchor, row in NEW:
        hits = [n for n, l in enumerate(lines) if l.strip().startswith(anchor)]
        print("  якорь %-24s найден %d" % (anchor[:24], len(hits)))
        if len(hits) != 1:
            print("     MISS")
            continue
        print("     -> %s" % row[:66])
        if apply:
            lines.insert(hits[0], row)
    if not apply:
        print("(только план)")
        return 0
    io.open(S, "w", encoding="utf-8", newline="").write(
        "\n".join(lines).replace("\n", "\r\n") if crlf else "\n".join(lines))
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
