# -*- coding: utf-8 -*-
"""col expands to column, and column enters the base

`col` is a real short form with a real definition, so it stays - but the
examples teach the full word, and that means the full word has to exist. It did
not: the base had col and row, and no column. So column is added on col's own
glyph, U+2193, which reads as a vertical axis and is what col was already
carrying. row keeps ->, the horizontal one.

`column, col` is the alias shape the base already uses elsewhere (and,&&), so
one concept, one mark, two spellings - and the short spelling stays anchored by
the definition underneath it.
"""
import io
import sys

DESC = "composition: linear vertical axis of children"
DICT = "DATA/dictionary_sorted_by_type.txt"
SYMS = "compiler/symbols_map.txt"
JOBS = [
    (DICT, "*-> col          - " + DESC, "*-> column, col    - " + DESC),
    (DICT, '-> exm:col: inp:name="login" | btn:name="save"',
     '-> exm:column: inp:name="login" | btn:name="save"'),
    (SYMS, "*-> col        - " + DESC, "*-> column, col  - " + DESC),
]


def main():
    apply = "--apply" in sys.argv
    total = 0
    for path, old, new in JOBS:
        raw = io.open(path, encoding="utf-8-sig").read()
        crlf = "\r\n" in raw
        text = raw.replace("\r\n", "\n")
        n = text.count(old)
        print("  %-32s %d  %s" % (path.split("\\")[-1], n, old[:52]))
        if not n:
            print("     MISS")
            continue
        total += n
        if apply:
            io.open(path, "w", encoding="utf-8", newline="").write(
                text.replace(old, new).replace("\n", "\r\n") if crlf else text.replace(old, new))
    print("\nзаменено: %d" % total)
    if not apply:
        print("(только план)")
    else:
        print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
