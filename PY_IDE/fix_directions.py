# -*- coding: utf-8 -*-
"""up down left right get the big block arrows, like a remote control

Three of the four directions had no mark at all, and the reason was structural:
their natural glyphs were already spoken for. down wanted U+2193, held by
column. left wanted U+2190, held by <-. right wanted U+2192, held by ->. Only
up had a mark, a thin one, and the set was incoherent.

row had already solved this for itself by taking a block arrow rather than the
thin -> it wanted. column did not, and that is what blocked down. So:

    up      U+2B06  ⬆    free
    down    U+2B07  ⬇    was save
    left    U+2B05  ⬅    free
    right   U+27A1  ➡    was row
    row     U+2B0B  ⬋    free - still a block arrow, so the axes stay a family
    save    U+2B0A  ⬊    was holding the down arrow

Untouched, as asked: -> keeps U+2192, column keeps U+2193.

save giving up U+2193 is the one real loss here - a down arrow into a tray is
exactly what saving is. U+2B0A is the same shape in outline, so the reading
survives the move.

In the spec, left and right are declared as items, because that is what they
are: docked panels with min, max, size and theme. A direction is not a thing
that has a theme.
"""
import io
import re
import sys

S = "compiler/symbols_map.txt"
W = "PY_IDE/window.vibe"
DIR = "direction sign: "
MOVES = [
    (S, "U+2B06", "up", DIR),
    (S, "U+2B07", "save", None),
    (S, "U+2B05", "left", DIR),
    (S, "U+27A1", "row", "composition: linear horizontal axis of children"),
    (S, "U+2B0B", "row", "composition: linear horizontal axis of children"),
    (S, "U+2B0A", "save", None),
    (S, "U+2191", None, None),
]
DES = {
    "up": "direction sign: up",
    "down": "direction sign: down",
    "left": "direction sign: left",
    "right": "direction sign: right",
    "row": "composition: linear horizontal axis of children",
}
OLD_DESC = {
    "up": "direction sign: up",
    "save": None,
    "row": "composition: linear horizontal axis of children",
}
NEWGLYPH = {
    "up": ("U+2B06", "⬆", "up"),
    "down": ("U+2B07", "⬇", "down"),
    "left": ("U+2B05", "⬅", "left"),
    "right": ("U+27A1", "➡", "right"),
    "row": ("U+2B0B", "⬋", "row"),
    "save": ("U+2B0A", "⬊", "save"),
}
DROP = ["U+2B07", "U+2B05", "U+2B06", "U+27A1", "U+2B0B", "U+2B0A", "U+2191"]


def main():
    apply = "--apply" in sys.argv
    raw = io.open(S, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")

    # drop every row we are about to re-issue, so nothing duplicates a codepoint
    kept = []
    dropped = []
    for l in lines:
        st = l.strip()
        hit = next((c for c in DROP if st.startswith(c + " ") or st.startswith(c + " ")), None)
        if hit:
            dropped.append(st.split("*->")[0].strip())
            continue
        kept.append(l)
    # descriptions must be read BEFORE the rows are dropped - save's row is one
    # of the rows being dropped, so looking afterwards finds nothing
    print("  снято строк: %d  (%s)" % (len(dropped), ", ".join(dropped)))
    for l in lines:
        m = re.match(r"\s*U\+[0-9A-Fa-f]{4,6}\s+\S+\s+\*->\s+([\w, ()]+?)\s+-\s+(.*)$", l)
        if not m:
            continue
        for w in [x.strip() for x in m.group(1).split(",")]:
            DES[w] = m.group(2).strip()
    for w in ("up", "down", "left", "right", "row", "save"):
        print("  %-6s описание: %r" % (w, DES.get(w, "ОТСУТСТВУЕТ")[:56]))

    if apply:
        for w in ("up", "down", "left", "right", "row", "save"):
            if w not in DES:
                print("  НЕТ ОПИСАНИЯ для %s - пропускаю" % w)
                continue
            cp, g, word = NEWGLYPH[w]
            kept.append("%-7s %s  *-> %-6s - %s" % (cp, g, word, DES[w]))
            print("  + %s %s *-> %s" % (cp, g, word))
        out = "\n".join(kept)
        io.open(S, "w", encoding="utf-8", newline="").write(
            out.replace("\n", "\r\n") if crlf else out)

    # the spec: left and right are items, they have a theme and a size
    wr = io.open(W, encoding="utf-8-sig").read()
    wcrlf = "\r\n" in wr
    wt = wr.replace("\r\n", "\n")
    for side in ("left", "right"):
        old = '&-> abstract:prop:id="%s"->frm:"%s"' % (side, side)
        new = '&-> abstract:item:id="%s"->frm:"%s"' % (side, side)
        n = wt.count(old)
        print("  window.vibe %-6s %dx" % (side, n))
        if n and apply:
            wt = wt.replace(old, new)
    if apply:
        io.open(W, "w", encoding="utf-8", newline="").write(
            wt.replace("\n", "\r\n") if wcrlf else wt)
    print("ЗАПИСАНО" if apply else "(только план)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
