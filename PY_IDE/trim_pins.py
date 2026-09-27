# -*- coding: utf-8 -*-
"""cut the init blocks back to the names that are genuinely new

The blocks I added cleared all ten warnings, and that was treating the symptom:
corner, font, font_size, cfg, par, frm, io, mapping and func are all declared
as abstracts with id="", and check_pins simply did not look at the spec's own
object vocabulary. It does now, so every block that only re-declared an
existing abstract is redundant and says nothing.

What is left is the three names the spec invents and no abstract covers:

  theme  {hex, group}   the eight theme groups, reached as theme:hex:num
  mapping {group}       a mapping is split by group
  par     {nest}        a parameter holds its nest

Those are real declarations: a name that exists nowhere else has to be
declared once, and an init block is where a spec says so.
"""
import io
import sys

PATH = "PY_IDE/window.vibe"

PAIRS = [
    ('&-> abstract:prop:id="theme"{"hex" "group" "num"}->frm:prop',
     '&-> abstract:prop:id="theme"{"hex" "group"}->frm:prop'),
    ('&-> abstract:prop:id="font"{"font_size"}->frm:prop',
     '&-> abstract:prop:id="font"->frm:prop'),
    ('&-> abstract:prop:id="cfg"{"mapping"}->frm:"cfg"',
     '&-> abstract:prop:id="cfg"->frm:"cfg"'),
    ('&-> abstract:prop:id="par"{"nest" "par"}->frm:"par"',
     '&-> abstract:prop:id="par"{"nest"}->frm:"par"'),
    ('&-> abstract:prop:id="frm"{"corner" "font" "module" "split" "theme"}->frm:"frm"',
     '&-> abstract:prop:id="frm"->frm:"frm"'),
    ('&-> abstract:prop:id="io"{"func"}->frm:"io"',
     '&-> abstract:prop:id="io"->frm:"io"'),
    ('&-> abstract:prop:id="mapping"{"group" "num"}->frm:"mapping"',
     '&-> abstract:prop:id="mapping"{"group"}->frm:"mapping"'),
]


def main():
    raw = io.open(PATH, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    apply = "--apply" in sys.argv
    n = 0
    for old, new in PAIRS:
        hit = text.count(old)
        if not hit:
            print("  MISS %s" % old[:56])
            continue
        n += hit
        print("  %s" % new[:62])
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
