# -*- coding: utf-8 -*-
"""a setter is a vector anchored at the end of a path, not a call with arguments.

I got this wrong first. `set(frm:font,"Arial")` passes the pin and the value as
two arguments, which flattens the chain: nothing says the operation belongs to
frm:font rather than to frm. `frm:font:set("Arial")` anchors it - the path
names the object, and `:set` is applied there. That is the whole difference,
and the comma form loses it.

    set(view:name, "VibeDSL IDE")   ->  view:name:set("VibeDSL IDE")
    set(frm:split, factor [65,35])  ->  frm:split:set(factor [65,35])
    set(left:max, factor 25)        ->  left:max:set(factor 25)

The ten in bind_theme carry no value - they propagate the ambient theme down
the tree, which is inheritance, not assignment. They become `x:theme:set()`:
the setter with an empty argument, because what fills it is inherited. That one
is a judgement, and it is the only judgement in this file.
"""
import io
import re
import sys

PATH = "PY_IDE/window.vibe"

# the comma form - an earlier, wrong attempt; absent from the file, matched anyway
RX_COMMA = re.compile(r"\bset\(([A-Za-z_][A-Za-z0-9_]*(?::[A-Za-z_][A-Za-z0-9_]*)+),([^()]*)\)")
# bare with a value: set(pin value). No lookahead on `none`: `set(nav:content
# none)` sets the content to the none marker, and a lookahead meant to skip
# empty forms silently dropped that one real setter. A form with no value has
# nothing after the pin, so it cannot match this pattern at all.
RX_BARE_VAL = re.compile(
    r"\bset\(([A-Za-z_][A-Za-z0-9_]*(?::[A-Za-z_][A-Za-z0-9_]*)+)(\s+[^()]+)\)")
# bare with no value: set(pin)
RX_BARE = re.compile(r"\bset\(([A-Za-z_][A-Za-z0-9_]*(?::[A-Za-z_][A-Za-z0-9_]*)+)\)")


def main():
    raw = io.open(PATH, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    apply = "--apply" in sys.argv
    n = b = 0

    def with_value(m):
        pin, val = m.group(1), m.group(2)
        # print what is ACTUALLY in the file, not a reconstruction: a pretty
        # "before" is how a no-op apply gets mistaken for a successful one
        print("  %-32s -> %s" % (m.group(0), "%s:set(%s)" % (pin, val.strip())))
        return "%s:set(%s)" % (pin, val.strip()) if apply else m.group(0)

    def without_value(m):
        pin = m.group(1)
        print("  %-32s -> %s   (наследование, значение не задано)"
              % (m.group(0), "%s:set()" % pin))
        return "%s:set()" % pin if apply else m.group(0)

    text, n = RX_COMMA.subn(with_value, text)
    text, w = RX_BARE_VAL.subn(with_value, text)
    text, b = RX_BARE.subn(without_value, text)
    print("\nс запятой: %d, без запятой со значением: %d, без значения: %d" % (n, w, b))
    if not apply:
        print("(только план; для записи добавьте --apply)")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="").write(
        text.replace("\n", "\r\n") if crlf else text)
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
