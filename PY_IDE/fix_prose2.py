# -*- coding: utf-8 -*-
"""the second wave: prose that had no preposition, so the first pass missed it

The first prose pass looked for of/from/by/to/in and rewrote fifteen strings.
Fourteen more were in the old style anyway - "crt view + set name +
fullscreen + show" - with no preposition in them, so nothing flagged them and
they went on describing a form the code had left behind. A check that looks for
one word finds one word; it does not find a style.

Each replacement below is the code that sits under it, abbreviated where the
code repeats itself. No double quotes: the whole string is quoted payload.

build_all is the one that had no action= at all - it was a bare run chain - so
it is given one, and its prose becomes the chain.
"""
import io
import sys

PATH = "PY_IDE/window.vibe"

PAIRS = [
    ('crt view + set name + fullscreen + show',
     'create(view) + view:name:set(...) + view:fullscreen:set(true) + action=show(view)'),
    ('crt nav + set 4 par + show',
     'create(nav) + nav:par:set(...) + add(nav:par ...) x4 + action=show(nav)'),
    ('remove item + nest', 'remove(item)'),
    ('crt frm + set module + set split factor + show',
     'create(frm) + frm:module:set(true) + frm:split:set(factor [65,35]) + action=show(frm)'),
    ('show left', 'action=show(left)'),
    ('close left', 'close(left)'),
    ('show right', 'action=show(right)'),
    ('close right', 'close(right)'),
    ('close tab', 'close(tab_view)'),
    ('crt col + row + 2 console factor 50',
     'create(col bottom) + create(row) + create(console) + console:factor:set(50) x2'),
    ('remove console + factor 100',
     'remove(console) + console:factor:set(100)'),
    ('add console + factor 50',
     'add(console) + console:factor:set(50)'),
    ('create(frm v sht)', 'create(frm v sht)'),
    ('run vse build func po poryadku',
     'run(open_view) -> run(read_colors) -> run(set_theme) -> run(bind_theme) '
     '-> run(build_nav) -> run(build_frm) -> run(build_top) -> run(build_bottom)'),
]


def main():
    raw = io.open(PATH, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    apply = "--apply" in sys.argv
    n = 0
    for old, new in PAIRS:
        # the prose may sit on its own line or in the header: match either
        hit_t = text.count('action="%s"' % old)
        hit_l = sum(1 for l in text.split("\n") if l.strip() == old)
        if not hit_t and not hit_l:
            print("  MISS %s" % old[:50])
            continue
        n += hit_t + hit_l
        print("  %dx %-42s -> %s" % (hit_t + hit_l, old[:42], new[:52]))
        if apply:
            text = text.replace('action="%s"' % old, 'action="%s"' % new)
            text = "\n".join(('    ->action="%s"' % new) if l.strip() == old else l
                             for l in text.split("\n"))
    print("\nзаменено: %d из %d" % (n, len(PAIRS)))
    if not apply:
        print("(только план; для записи добавьте --apply)")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="").write(
        text.replace("\n", "\r\n") if crlf else text)
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
