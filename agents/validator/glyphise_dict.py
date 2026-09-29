# -*- coding: utf-8 -*-
"""the dictionary teaches its syntax in words - put the examples in glyphs

The rule at the top of the dictionary says a spec is written in glyphs, and then
361 examples underneath it were written in words. A language that teaches its
syntax in the wrong form teaches the wrong form, and that is exactly how a spec
came to be authored in words while the compiler emitted glyphs. I wrote that
contradiction myself, in the rule that forbids it.

Only the syntax after "-> exm:" is converted. The marker itself is the
dictionary's own structure and stays, and the // comment stays English, and
the description after the dash stays English - the dictionary describes the
language, it is not written in it.
"""
import collections
import importlib.util as u
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")
ALL = ["DATA/dictionary_sorted_by_type.txt", "DATA/action.dict", "DATA/mapping.dict",
       "DATA/operators.dict", "DATA/abstracts.txt"]
MARK = "-> exm:"
TAIL = "-> exm: "


def main():
    apply = "--apply" in sys.argv
    sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
    cc = u.module_from_spec(sp)
    sp.loader.exec_module(cc)
    co, cs, w2g, gl = cc.load_alias_to_glyph()
    sub, _, _ = cc.build_substitution(co, cs, w2g, gl)
    rx = cc.make_token_rx(sub)
    raw = io.open(D, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")
    st = {"replaced": 0, "words": collections.Counter(), "unmapped": set(),
          "undefined": set(), "missing_use": [], "glyphs_used": [], "noteq": set()}
    n = 0
    for i, l in enumerate(lines):
        if MARK not in l:
            continue
        head, tail = l.split(TAIL, 1) if TAIL in l else l.split(MARK, 1)
        code, sep, comment = tail.partition("//")
        conv = cc.compile_line(code, sub, rx, st, None, set())
        new = head + (TAIL if TAIL in l else MARK) + conv + (sep + comment if sep else "")
        n += 1
        if n <= 4 and apply:
            print("  БЫЛО : %s" % l.strip()[:92])
            print("  СТАЛО: %s" % new.strip()[:92])
            print("")
        lines[i] = new
    print("  строк-примеров переведено в глифы: %d" % n)
    print("  слов заменено: %d   неизвестно: %d" % (st["replaced"], len(st["undefined"])))
    if st["undefined"]:
        for x in sorted(st["undefined"])[:8]:
            print("    НЕТ В БАЗЕ: %s" % x)
    if not apply:
        print("(только план)")
        return 0
    io.open(D, "w", encoding="utf-8", newline="").write(
        "\n".join(lines).replace("\n", "\r\n") if crlf else "\n".join(lines))
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
