# -*- coding: utf-8 -*-
"""register the frame, appended LAST and not in alphabetical position

▹ and ◂ were used in specs, written into a rule, given a name, and existed
nowhere. That is the seventh time this week: a symbol in use, absent from the
base, and nothing red because nothing looked. Twice as words (ctl_, ≍), once as
glyphs I invented for the frame itself.

Appended last, deliberately, not sorted into place. The dictionary is
alphabetical and a rename in the middle of it broke ORDER and SPLITS last time.
These two are appended and marked as such, so a later pass can sort the whole
file once, deliberately, instead of two words at a time.

The human cost, stated because it is real: for me ▹ and ◂ are a frame that opens
inward. To a person reading the report they are two near-identical marks from a
strange alphabet, and the frame looks like byte code. That is the price of the
two-ends split, paid on the side where the frame matters least - the report can
be rendered with "" instead, and the glyph form keeps the glyph.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")
S = os.path.join(ROOT, "compiler", "symbols_map.txt")

ENTRIES = (
    "\n# --- APPENDED, not in alphabetical order ---------------------------------\n"
    "# The frame. U+25B9 opens and points INWARD, U+25C2 closes and points\n"
    "# inward too, and is filled where the opener is hollow so the two differ by\n"
    "# fill as well as by direction in one colour. A bracket points inward, a\n"
    "# guillemet points outward, and inward reads as a bracket.\n"
    "#\n"
    "# It replaced the symmetric quotes because quotes PROTECT their content from\n"
    "# the compiler, so a payload written in them never came back and no round trip\n"
    "# could ever close. The frame does not protect, so the spine and the payload\n"
    "# behave the same and the circle becomes a fixed point.\n"
    "#\n"
    "# For a reader of the report these two are visually byte code. That is the\n"
    "# price of the two-ends split, and it is paid where it costs least: the report\n"
    "# may render the frame as quotes, the glyph form keeps the glyph.\n"
    "*-> idopen       - open of the frame, points inward like a bracket. an id is written\n"
    "     between idopen and idshut. outside the frame an alphabet glyph is not an id,\n"
    "     it is a typo with no claim. U+25B9\n"
    "*-> idshut       - close of the frame, filled where idopen is hollow, so the pair\n"
    "     differs by fill as well as by direction in one colour. U+25C2\n"
)

d = io.open(D, encoding="utf-8-sig").read()
crlf = "\r\n" in d
if "idopen" not in d:
    body = d.replace("\r\n", "\n").rstrip("\n")
    io.open(D, "w", encoding="utf-8", newline="").write(
        body + "\n" + ENTRIES.replace("\n", "\r\n") if crlf else body + "\n" + ENTRIES)
    print("  словарь: idopen и idshut добавлены последними")
else:
    print("  словарь: уже есть")

s = io.open(S, encoding="utf-8-sig").read()
crlf2 = "\r\n" in s
if "idopen" not in s:
    t = s.replace("\r\n", "\n").rstrip("\n")
    rows = (chr(0x25B9) + "  *-> idopen - open of the frame, points INWARD, hollow\n"
            + chr(0x25C2) + "  *-> idshut - close of the frame, filled, so the pair differs by fill too")
    t = t.replace("U+%04X" % 0x25B9, "U+25B9   " + chr(0x25B9) + " *-> idopen") if False else t
    io.open(S, "w", encoding="utf-8", newline="").write(
        t + "\n" + rows.replace("\n", "\r\n") if crlf2 else t + "\n" + rows)
    print("  карта: рамка добавлена")
else:
    print("  карта: уже есть")

# and does it resolve now
import importlib.util as u
sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()
res = set(g for g in w2g.values() if g)
for nm, cp in (("idopen", 0x25B9), ("idshut", 0x25C2)):
    print("  %-8s глиф %s   в карте слов: %s"
          % (nm, chr(cp), "да" if chr(cp) in res else "НЕТ"))
