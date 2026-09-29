# -*- coding: utf-8 -*-
"""swap abstract and vrt in the map, and the descriptions with them

The two entries already carried each other's senses, only the names were
crossed. That is why this is a swap and not a rename:

    U+2330 abstract  "declaration of a pure concept (idea)"
    U+2216 vrt       "virtual, logical virtual sequence or entity"

A pure idea declared and not executed IS the wish line, and that is what
abstract now is. A declaration that can be applied but does not run by itself IS
virtual, and that is what U+2330 now is. So the glyphs stay where they were and
the names move - which is the cheap direction, and the one that cannot lose a
concept.

The form is unchanged, exactly as it was under abstract:
    virtual:prop:id="color"->frm:prop        parent : type, no id in the tail
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "compiler", "symbols_map.txt")
D = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")

OLD_ABS_MAP = ("U+2330", chr(0x2330), "abstract",
               "the declaration of a pure concept")
OLD_VRT_MAP = ("U+2216", chr(0x2216), "vrt",
               "virtual, logical virtual sequence or entity")

NEW_ABS_MAP = (
    "U+2216", chr(0x2216), "abstract",
    "a WISH, a mapping of idea concepts. an abstract is a statement of intent and"
    " nothing else: no type, no id, nothing to apply and nothing to check."
    " ->(abstract=..) is said before the work, ✓ goal is marked after it. a wish"
    " with an id is a declaration pretending to be a wish"
)
NEW_VRT_MAP = (
    "U+2330", chr(0x2330), "virtual",
    "the declaration of a VIRTUAL entity - one that can be applied and never"
    " executes by itself. :prop / :function / :item say which kind of virtual"
    " entity it is, § is the identifier it is applied by, and the tail is"
    " parent:type. this is what used to be called abstract"
)

s = io.open(S, encoding="utf-8-sig").read()
crlf = "\r\n" in s
t = s.replace("\r\n", "\n")

for old, new in ((OLD_ABS_MAP, NEW_VRT_MAP), (OLD_VRT_MAP, NEW_ABS_MAP)):
    hits = [l for l in t.split("\n") if l.startswith(old[0]) and old[1] in l]
    if not hits:
        print("  не найден в карте: U+%s" % old[0])
        continue
    h = hits[0]
    rest = h.split(" - ", 1)[1] if " - " in h else ""
    newline = "%-11s %s  *-> %-9s - %s" % (new[0], new[1], new[2], new[3] + (
        " " + rest if rest else ""))
    t = t.replace(h, newline)
    print("  U+%s  %s -> %s" % (old[0], old[2], new[2]))

io.open(S, "w", encoding="utf-8", newline="").write(
    t.replace("\n", "\r\n") if crlf else t)

# and the dictionary, same swap
d = io.open(D, encoding="utf-8-sig").read()
crlf = "\r\n" in d
u = d.replace("\r\n", "\n")
lines = u.split("\n")
for i, l in enumerate(lines):
    if l.startswith("*-> abstract"):
        lines[i] = ("*-> virtual       - the declaration of a VIRTUAL entity - one that can be"
                    "\n     applied and never executes by itself. :prop / :function / :item"
                    "\n     say which kind, § is the identifier it is applied by, the tail"
                    "\n     is parent:type. -> virtual:prop:id=\"color\"->frm:prop. this is"
                    "\n     what used to be called abstract")
        print("  словарь: abstract -> virtual")
    elif l.startswith("*-> vrt"):
        lines[i] = ("*-> abstract      - a WISH, a mapping of idea concepts. an abstract is a"
                    "\n     statement of intent and nothing else: no type, no id, nothing to"
                    "\n     apply and nothing to check. -> abstract=\"хочу IDE как Android"
                    "\n     Studio\". said before the work; goal is marked after it")
        print("  словарь: vrt -> abstract")
io.open(D, "w", encoding="utf-8", newline="").write(
    "\n".join(lines).replace("\n", "\r\n") if crlf else "\n".join(lines))
