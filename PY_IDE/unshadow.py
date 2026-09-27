# -*- coding: utf-8 -*-
"""the 27 declarations that took a name the base already explains

view, theme, text, frm, left and 24 more. The base has a mark and a definition
for every one of them, and the spec re-declared them as its own - which is the
same collision as goal and col, and it is what forced the compiler to protect
locally-declared names from compiling: show(theme) was staying text because the
spec had claimed `theme` for itself, not because theme is not a word.

Removing the claims is the right way round. After this the spec just uses the
base words, local_names() shrinks from 96 to the 23 that are genuinely local,
and a word inside a paren compiles like a word anywhere else.
"""
import io
import re
import sys

SPEC = "PY_IDE/window.vibe"
SHADOW = ["view", "name", "fullscreen", "theme", "cfg", "file", "text", "nav",
          "frm", "module", "split", "factor", "column", "row", "left", "right",
          "min", "max", "size", "num", "inp", "console", "sht", "content",
          "io", "none", "goal"]


def main():
    apply = "--apply" in sys.argv
    raw = io.open(SPEC, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")
    drop = []
    for i, l in enumerate(lines):
        m = re.match(r'^\s*&->\s*abstract:(prop|item):id="([^"]+)"', l)
        if m and m.group(2) in SHADOW:
            drop.append((i, m.group(2), m.group(1)))
    print("  строк к удалению: %d" % len(drop))
    for i, name, kind in drop:
        print("   %4d  %-6s %-5s  %s" % (i + 1, name, kind, lines[i].strip()[:58]))
    keep = [l for n, l in enumerate(lines) if n not in {d[0] for d in drop}]
    print("\n  строк: %d -> %d" % (len(lines), len(keep)))
    if not apply:
        print("(только план)")
        return 0
    io.open(SPEC, "w", encoding="utf-8", newline="").write(
        "\n".join(keep).replace("\n", "\r\n") if crlf else "\n".join(keep))
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
