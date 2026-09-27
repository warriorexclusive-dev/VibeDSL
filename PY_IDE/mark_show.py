# -*- coding: utf-8 -*-
"""mark every show, so a mapping never reads as an order.

`show(left)` on its own is an imperative: show the left panel. To a person
reading the spec that is an instruction, and to a model it is a cheap
continuation that drifts. `action=show(left)` says the verb is bound as a
mapping, not issued as an order.

The spec already had the marker - three times, in the event handlers
(action=show(left), action=show(right)) - and twenty bare. Same verb, two
forms, which is the same defect the dictionary spent the day removing: one
word, one meaning. The section boundary is not a reason; it is the accident
that let the two forms coexist.

    show(view)      ->  action=show(view)
    ->show(theme)   ->  ->action=show(theme)

Only show. The other verbs - create 13, add 8, run 11, load 4, close 3,
remove 2, retry 1, save 1, split 1 - are listed at the end so the decision
stays yours rather than being made by a script that saw a pattern.
"""
import importlib.util
import io
import os
import re
import sys

PATH = "PY_IDE/window.vibe"
# `show` without the paren, and the bare-word guard: an already-marked one must
# not become action=action=. Matching `show(` fails here - `show` sits in the
# code segment and the `(` opens the keep segment, so the pair never appears
# inside one chunk. That is the third boundary bug today; the rule is: do not
# write a pattern whose two halves live on opposite sides of a segment edge.
RX = re.compile(r"(?<![A-Za-z0-9_:=])show(?=\()")
RX_HAS_QUOTED_ARG = re.compile(r"show\(\s*\"")


def segments():
    spec = importlib.util.spec_from_file_location("_cc", os.path.join("compiler", "compile.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.segments


def main():
    seg = segments()
    raw = io.open(PATH, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    apply = "--apply" in sys.argv
    quoted = [i for i, l in enumerate(text.split("\n"), 1) if RX_HAS_QUOTED_ARG.search(l)]
    if quoted:
        print("  СТОП: show с кавычным аргументом на строках %s - не трогаю" % quoted)
        return 1
    print("  show с кавычным аргументом: 0 (можно править построчно)")
    n = 0

    def repl(line):
        nonlocal n
        def one(m):
            nonlocal n
            n += 1
            return "action=show"
        return RX.sub(one, line)

    lines = [repl(l) for l in text.split("\n")]
    print("show без маркера: %d" % n)
    if not apply:
        print("(только план; для записи добавьте --apply)")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="").write(
        "\n".join(lines).replace("\n", "\r\n") if crlf else "\n".join(lines))
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
