# -*- coding: utf-8 -*-
"""ctl_ -> controller, which was in the base the whole time

controller is U+2316, 'entity control manager'. I invented ctl_ without
looking, and then spent a question asking whether the language had a word for it
after grepping the dictionary for the wrong strings. Four inventions in one
session - reqr, parametr, proto, sc(oped - and now ctl_ - and every one of them
was avoidable with a grep I did not run.

That is self-11 in the tools dataset, and this is the second time it has cost
something. Recording it is cheap; the habit it points at is: grep the base for
the CONCEPT before writing a word, not after.
"""
import io
import re
import sys

FILES = ["PY_IDE/window.vibe", "DATA/lessons.jsonl", "DATA/tools.jsonl"]


def main():
    apply = "--apply" in sys.argv
    cache = {}
    for p in FILES:
        raw = io.open(p, encoding="utf-8-sig").read()
        cache[p] = [raw, "\r\n" in raw, raw.replace("\r\n", "\n")]
    for p in FILES:
        _, crlf, t = cache[p]
        n_ctl = len(re.findall(r"ctl_", t))
        if not n_ctl:
            continue
        # ctl_left -> controller_left, and the prose that mentions ctl_ too
        t = t.replace("ctl_", "controller_")
        cache[p][2] = t
        print("  %-26s вхождений ctl_: %d" % (p, n_ctl))
    if not apply:
        print("(только план)")
        return 0
    for p, (_, crlf, t) in cache.items():
        io.open(p, "w", encoding="utf-8", newline="").write(
            t.replace("\n", "\r\n") if crlf else t)
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
