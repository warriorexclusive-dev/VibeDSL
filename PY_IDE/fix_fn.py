# -*- coding: utf-8 -*-
"""the function entry's examples, taken verbatim from the spec

Four exm lines, every one an abbreviation: fun:type=rule:scop=root,
fun:name="load":par="val1", func:name="load". The replacement is line 5 of
PY_IDE/window.vibe character for character, scop= and all - an example that
differs from the spec teaches the wrong form, and copying the spec's own
scop= keeps the real inconsistency visible instead of hiding it behind a
tidied-up example.
"""
import io
import sys

PATH = "DATA/dictionary_sorted_by_type.txt"
OLD = ('    -> exm:fun:type=rule:scop=root\n'
       '    -> exm:fun:name="load":par="val1"\n'
       '    -> exm:func:name="load"')
NEW = ('    -> exm:function type="root" name="vibide" id="vibide" scop="root"'
       '->action == create [spec] lng="VibeDSL"')


def main():
    raw = io.open(PATH, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    n = text.count(OLD)
    print("  найдено: %d" % n)
    if not n:
        print("  MISS")
        return 1
    print("  -> %s" % NEW[:88])
    if "--apply" not in sys.argv:
        print("(только план)")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="").write(
        text.replace(OLD, NEW).replace("\n", "\r\n") if crlf else text.replace(OLD, NEW))
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
