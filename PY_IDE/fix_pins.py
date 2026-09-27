# -*- coding: utf-8 -*-
"""declare the ten pins the spec was already using, and stop duplicating set_tab_name.

Ten soft warnings, all one cause: the spec writes obj:pin and never says the
object HAS that pin. A placement chain (->frm:prop) declares where a prop sits;
it does not declare a field, and the validator is right to refuse the claim. The
form that declares a field is a quoted init block right after the id:

    &-> abstract:prop:id="theme"{"hex" "group"}->frm:prop

Every pin below was already in the code, so these are not new claims - they are
the claims the code was already making, written down. Each one is true: cfg
holds a mapping, a mapping has groups, a font has a size, the frame holds a
corner and a font, a parameter has a nest, io has the function to run.

The second fix is duplication. add_tab inlined tab_view:name:set(par) while
set_tab_name did exactly that and nothing else, so one operation had two
sources of truth. add_tab now calls it, the way reload_theme and build_all
already call other abstracts. That is 33 functions, not 32, and the exam's
check(func:num) has to move with it.
"""
import io
import sys

PATH = "PY_IDE/window.vibe"

DECL = [
    # (old declaration line, new one with its pins)
    ('&-> abstract:prop:id="theme"->frm:prop',
     '&-> abstract:prop:id="theme"{"hex" "group" "num"}->frm:prop'),
    ('&-> abstract:prop:id="font"->frm:prop',
     '&-> abstract:prop:id="font"{"font_size"}->frm:prop'),
    ('&-> abstract:prop:id="cfg"->frm:"cfg"',
     '&-> abstract:prop:id="cfg"{"mapping"}->frm:"cfg"'),
    ('&-> abstract:prop:id="par"->frm:"par"',
     '&-> abstract:prop:id="par"{"nest" "par"}->frm:"par"'),
    ('&-> abstract:prop:id="frm"->frm:"frm"',
     '&-> abstract:prop:id="frm"{"corner" "font" "module" "split" "theme"}->frm:"frm"'),
    ('&-> abstract:prop:id="io"->frm:"io"',
     '&-> abstract:prop:id="io"{"func"}->frm:"io"'),
    ('&-> abstract:prop:id="mapping"->frm:"mapping"',
     '&-> abstract:prop:id="mapping"{"group" "num"}->frm:"mapping"'),
]

# add_tab: call set_tab_name instead of repeating it
CALL = [
    ('->add(tab_view)->tab_view:name:set(par)->tab_view:text:set(par)->action=show(tab_view)',
     '->add(tab_view)->run(set_tab_name)->tab_view:text:set(par)->action=show(tab_view)'),
    ('add(tab_view) + tab_view:name:set(par) + tab_view:text:set(par) + action=show(tab_view)',
     'add(tab_view) + run(set_tab_name) + tab_view:text:set(par) + action=show(tab_view)'),
]


def main():
    raw = io.open(PATH, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    apply = "--apply" in sys.argv
    n = 0
    for old, new in DECL + CALL:
        hit = text.count(old)
        if not hit:
            print("  MISS %s" % old[:60])
            continue
        n += hit
        print("  %dx %-58s" % (hit, old[:58]))
        print("      -> %s" % new[:58])
        if apply:
            text = text.replace(old, new)
    print("\nзаменено: %d" % n)
    if not apply:
        print("(только план; для записи добавьте --apply)")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="").write(
        text.replace("\n", "\r\n") if crlf else text)
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
