# -*- coding: utf-8 -*-
"""dictionary examples taken from the spec that actually compiles

Every function example was an abbreviation - fun:, func:, scop=, par= - the
same crt/wrt/varn disease the base was cleaned of, sitting in the master file.
The replacement is PY_IDE/window.vibe verbatim, including its scop=, because an
example that differs from the spec teaches the wrong form and hides the real
inconsistency instead of showing it.

condition pointed at prototype:id="if", deleted in 741fd49.
"""
import io
import sys

PATH = "DATA/dictionary_sorted_by_type.txt"
REAL_FN = ('-> exm:function type="root" name="vibide" id="vibide" scop="root"'
           '->action == create [spec] lng="VibeDSL"')
PAIRS = [
    # three abbreviations -> one line that is really in the spec
    ('-> exm:fun:type=rule:scop=root\n-> exm:fun:name="load":par="val1"\n-> exm:func:name="load"',
     REAL_FN),
    ('-> exm: prototype:id="if":required:type[item,function,prop]:required:condition',
     '-> exm: prototype:id="abstract":required:type[item,function,prop]:required:condition'),
]


def main():
    raw = io.open(PATH, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    n = 0
    for old, new in PAIRS:
        c = text.count(old)
        print("  %dx  %s" % (c, old.replace("\n", " / ")[:62]))
        if not c:
            print("     MISS")
            continue
        n += c
        if "--apply" in sys.argv:
            text = text.replace(old, new)
    print("\nзаменено: %d" % n)
    if "--apply" not in sys.argv:
        print("(только план)")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="").write(
        text.replace("\n", "\r\n") if crlf else text)
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
