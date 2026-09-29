# -*- coding: utf-8 -*-
"""the reference corpus, on the settled format

The format is three movements, and only three:

    down            :        a node owns what follows
    continue down   ->       the next line, indented deeper, same node
    sideways        indent   a neighbour at the same level, no operator at all

The sideways movement having no operator is why it was read wrong three times:
there was nothing to look for, so a parse that keys on symbols cannot see it and
a parse that keys on indentation sees nothing else. Both are needed, and they
are not alternatives.

The corpus is a file per defect class with a KNOWN number of each. Without a
denominator, a finding is not a measurement: 261 means nothing until you know
how many were planted, and shrinking 261 to 78 by excluding a folder is not a
fix, it is a different measurement of a different input.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "PY_IDE", "_ref")

# our vocabulary, one glyph each
A = chr(0x2330)      # virtual
ITEM, FUNC, PROP = chr(0x2B1D), chr(0x02A9), chr(0x2317)
ID, AS = chr(0x00A7), chr(0x2A72)
Q = chr(0x22)
FO, FS = chr(0x25B9), chr(0x25C2)
IDN = FO + chr(0x23BF) + chr(0x23C1) + chr(0x23C3) + chr(0x23CD) + FS   # 4-glyph id

# a well-formed node, in the three renderings that must mean the same thing
DENSE = A + ":" + PROP + ":" + ID + AS + Q + "size" + Q + ":" + PROP + "->" + FUNC + "()"
INDENTED = (
    A + ":" + PROP + ":" + ID + AS + Q + "size" + Q + ":" + PROP + "\n"
    + "  ->" + FUNC + "()"
)
BRANCH = (
    A + ":" + PROP + ":" + ID + AS + Q + "size" + Q + ":" + PROP + "\n"
    + "  ->" + FUNC + "()\n"
    + "  " + A + ":" + ITEM + ":" + ID + AS + Q + "img" + Q
)

CLASSES = {
    # ---------------- structure: the sideways movement ----------------
    "ok_dense":        (0, lambda i: DENSE),
    "ok_indented":     (0, lambda i: INDENTED),
    "ok_branch":       (0, lambda i: BRANCH),
    "ok_empty":        (0, lambda i: A + ":" + PROP + ":" + ID + AS + Q + "a" + Q),

    # ---------------- the three axes, broken separately ----------------
    "colon_no_down":   (2, lambda i: A + ":" + PROP + ":" + ID + AS + Q + "a" + Q
                              + "->" + FUNC + "()"),
    "arrow_no_down":   (2, lambda i: A + ":" + PROP + ":" + ID + AS + Q + "a" + Q
                              + "\n" + "  " + FUNC + "()"),
    "lone_arrow":      (2, lambda i: "  ->" + FUNC + "()"),
    "orphan_indent":   (2, lambda i: " " * 6 + A + ":" + PROP + ":" + ID + AS + Q + "a" + Q),

    # ---------------- declarations, against our own base ----------------
    "no_type":         (3, lambda i: A + ":" + ID + AS + Q + "a" + Q + ":" + PROP),
    "type_as_id":      (2, lambda i: A + ":" + ID + AS + Q + A + ITEM + Q + ":" + PROP),
    "empty_id":        (2, lambda i: A + ":" + PROP + ":" + ID + AS + Q + Q),

    # ---------------- the frame and the id ---------------------------
    "unclosed_frame":  (2, lambda i: A + ":" + PROP + ":" + ID + AS + FO + chr(0x23BF)),
    "unopened_frame":  (2, lambda i: A + ":" + PROP + ":" + ID + AS + chr(0x23BF) + FS),
    "id_len":          (2, lambda i: A + ":" + PROP + ":" + ID + AS + FO + chr(0x23BF) + chr(0x23C1) + FS),
    "alphabet_bare":   (2, lambda i: chr(0x23BF) + chr(0x23C1) + ":" + PROP),

    # ---------------- glyphs and holes --------------------------------
    "unknown_glyph":   (2, lambda i: A + ":" + PROP + ":" + ID + AS + Q + "a" + Q
                              + ":" + chr(0x25B2) + PROP),
    "hole_name":       (2, lambda i: A + ":" + PROP + ":" + ID + AS + Q + "minimayz" + Q),

    # ---------------- identity: one id, several objects ---------------
    "id_two_defs":     (2, lambda i: A + ":" + PROP + ":" + ID + AS + Q + "a" + Q
                              + "\n" + "  " + A + ":" + PROP + ":" + ID + AS + Q + "b" + Q),
}

os.makedirs(OUT, exist_ok=True)
planted = []
for name, (cnt, make) in CLASSES.items():
    body = [make(i) for i in range(cnt)] or [make(0)]
    txt = "\n".join(body) + "\n"
    io.open(os.path.join(OUT, name + ".vglyph"), "w", encoding="utf-8", newline="\n").write(txt)
    planted.append((name, cnt))

print("  эталон: %s, файлов %d" % (OUT.replace(ROOT + os.sep, ""), len(CLASSES)))
clean = sum(1 for n, c in planted if c == 0)
print("  классов дефектов %d, чистых контрольных %d" % (len(planted) - clean, clean))
print("  посажено всего дефектов: %d" % sum(c for n, c in planted))
for n, c in planted:
    print("     %-18s %d" % (n, c))
io.open(os.path.join(OUT, "PLANTED.txt"), "w", encoding="utf-8", newline="\n").write(
    "\n".join("%s %d" % (n, c) for n, c in planted) + "\n")
