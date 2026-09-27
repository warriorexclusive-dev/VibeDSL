# -*- coding: utf-8 -*-
"""column everywhere, col gone

The base's own DICT check settled this: 'col' is an abbreviation of 'column' in
{column, col}: keep the full word. So when the full form exists as the same
concept, the abbreviation is redundant and the check refuses the pair. That is
stricter than what RULES.MD said a commit ago, and the check is right - an
alias that sits next to its own full word teaches nothing that the full word did
not already say.

`col` was anchored by definition, which is legal for a short form that is the
only spelling. Once `column` entered the base there were two spellings and one
of them had to go. It is not `column` that goes.

window.vibe is a real spec, so this is a real change in it: the object is
column in the declaration, in the placement, in create() and in every check.
dict-ui.txt is a second category file that is not one of the four canonical
splits but carries the same row, and is updated so the two do not drift.
"""
import io
import sys

JOBS = [
    ("DATA/dictionary_sorted_by_type.txt", [
        ("*-> column, col    - ", "*-> column        - "),
    ]),
    ("temp/dict-ui.txt", [
        ("*-> col          - ", "*-> column       - "),
    ]),
    ("compiler/symbols_map.txt", [
        ("*-> column, col  - ", "*-> column      - "),
    ]),
    ("PY_IDE/window.vibe", [
        ('&-> abstract:prop:id="col"->frm:"col"', '&-> abstract:prop:id="column"->frm:"column"'),
        ("col:theme:set()", "column:theme:set()"),
        ("create(col)", "create(column)"),
        ("create(col top)", "create(column)"),
        ("create(col bottom)", "create(column)"),
        ("check(col:theme)", "check(column:theme)"),
    ]),
    ("README.md", [
        ("`row col grd", "`row column grd"),
        ("-> col: -> sec:name", "-> column: -> sec:name"),
    ]),
    ("VibeDSL.md", [
        ("`row col grd", "`row column grd"),
        ("-> col: -> sec:name", "-> column: -> sec:name"),
    ]),
    ("plan/UI-plans.md", [
        ("- col   - linear vertical axis", "- column   - linear vertical axis"),
        ("-> col: -> sec:name", "-> column: -> sec:name"),
        ("(`col`/`frm`/`ovl`)", "(`column`/`frm`/`ovl`)"),
    ]),
]


def main():
    apply = "--apply" in sys.argv
    total = 0
    for path, pairs in JOBS:
        raw = io.open(path, encoding="utf-8-sig").read()
        crlf = "\r\n" in raw
        text = raw.replace("\r\n", "\n")
        got = False
        for old, new in pairs:
            n = text.count(old)
            if not n:
                print("  %-30s MISS  %s" % (path.split("\\")[-1], old[:46]))
                continue
            got = True
            total += n
            print("  %-30s %dx  %s" % (path.split("\\")[-1], n, old[:46]))
            if apply:
                text = text.replace(old, new)
        if apply and got:
            io.open(path, "w", encoding="utf-8", newline="").write(
                text.replace("\n", "\r\n") if crlf else text)
    print("\nзаменено: %d" % total)
    if not apply:
        print("(только план)")
    else:
        print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
