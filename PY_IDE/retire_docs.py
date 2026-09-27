# -*- coding: utf-8 -*-
"""VibeDSL.md goes; the -> rule it holds goes with it unless it is kept

The file is stale by the owner's word, but the section written today - `->` as
the constructor - is the only place that rule is written down, and deleting the
file with the rule inside it loses it. So the section moves to RULES.MD, which
is the current document, and the rest of the file goes unremarked.

VibeDSL.md is also listed in the README file map, so that line has to stop
pointing at a file that will not exist.
"""
import io
import re
import sys

SRC = "VibeDSL.md"
DST = "RULES.MD"
README = "README.md"


def main():
    apply = "--apply" in sys.argv
    L = io.open(SRC, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
    a = next(n for n, l in enumerate(L) if l.startswith("## `->`"))
    b = next(n for n, l in enumerate(L[a + 1:], a + 1) if l.startswith("## "))
    block = [l for l in L[a:b] if l.strip()]
    print("  раздел: строки %d..%d, %d непустых" % (a + 1, b, len(block)))

    raw = io.open(DST, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    print("  в %s уже есть раздел про ->: %s" % (DST, "-> " in text and "constructor" in text))

    rraw = io.open(README, encoding="utf-8-sig").read()
    rcrlf = "\r\n" in rraw
    rtext = rraw.replace("\r\n", "\n")
    has_line = "VibeDSL.md            language overview" in rtext
    print("  README ссылается на VibeDSL.md: %s" % has_line)

    if not apply:
        print("\n(только план)")
        return 0

    add = ["", "## `->` - the constructor, and the operator that shortens it", ""]
    add += block[1:]
    add += ["",
            "This section replaces the one that lived in `VibeDSL.md`. That file was",
            "stale as a whole and went with the rest; this rule is not, and it is",
            "here now because it is the only statement of what `->` means.",
            "The named examples come from `PY_IDE/window.vibe`, which is the syntax",
            "that actually compiles.", ""]
    text = text.rstrip("\n") + "\n" + "\n".join(add)
    io.open(DST, "w", encoding="utf-8", newline="").write(
        text.replace("\n", "\r\n") if crlf else text)
    print("  -> раздел перенесён в %s" % DST)

    if has_line:
        rtext = rtext.replace("VibeDSL.md            language overview\n", "")
        io.open(README, "w", encoding="utf-8", newline="").write(
            rtext.replace("\n", "\r\n") if rcrlf else rtext)
        print("  -> ссылка из README убрана")

    for f in (SRC, "plan/UI-plans.md"):
        try:
            os.remove(f)
            print("  удалён %s" % f)
        except OSError as e:
            print("  не удалён %s: %s" % (f, e))
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    import os
    sys.exit(main())
