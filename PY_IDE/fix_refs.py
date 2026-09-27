# -*- coding: utf-8 -*-
"""use(...) examples named prototypes that no longer exist.

The four written forms of use() are still four, and the point of these lines is
the FORM, not the name. But an example naming a deleted entry is worse than no
example: use(varn5) does not resolve any more, and a reader will try it.

The multi-id bracket form keeps its shape on the one prototype that stays.
"""
import io
import sys

FIX = [
    ("DATA/dictionary_sorted_by_type.txt",
     "-> exm:use(VibeDSL:proto[if,goal,fail])",
     "-> exm:use(VibeDSL:proto[abstract])"),
    ("DATA/dictionary_sorted_by_type.txt",
     "-> exm:proto(any)",
     '-> exm:prototype:id="abstract":required:type[item,function,prop]:required:condition'),
    ("README.md",
     "(`use(varn5)`, `use(VibeDSL:proto[if,goal,fail])`, `use(agent name=...)`).",
     "(`use(abstract)`, `use(VibeDSL:proto[abstract])`, `use(agent name=...)`)."),
    ("README.md",
     "`use(VibeDSL:proto[if,goal])`",
     "`use(VibeDSL:proto[abstract])`"),
    ("AGENTS.md",
     "`use(VibeDSL:proto[if,goal,fail])`",
     "`use(VibeDSL:proto[abstract])`"),
]


def main():
    apply = "--apply" in sys.argv
    total = 0
    cache = {}
    for path, old, new in FIX:
        if path not in cache:
            raw = io.open(path, encoding="utf-8-sig").read()
            cache[path] = [raw, "\r\n" in raw, raw.replace("\r\n", "\n")]
        _, crlf, text = cache[path]
        n = text.count(old)
        print("  %-32s %dx  %s" % (path.split("\\")[-1], n, old[:44]))
        if not n:
            print("     MISS")
            continue
        total += n
        if apply:
            cache[path][2] = text.replace(old, new)
    print("\nзаменено: %d" % total)
    if not apply:
        print("(только план)")
        return 0
    for path, (raw, crlf, text) in cache.items():
        io.open(path, "w", encoding="utf-8", newline="").write(
            text.replace("\n", "\r\n") if crlf else text)
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
