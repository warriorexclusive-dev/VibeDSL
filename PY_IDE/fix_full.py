# -*- coding: utf-8 -*-
"""full words in the dictionary examples

fun/func -> function, par -> param, err -> error, scop -> scope, syn -> syntax,
ret -> return. All seven have a full form in the base, so there is a choice and
the full one is it.

val stays. The base has no `value` and no `val` - content, data and text are
different meanings and borrowing one of them would be a false claim. Same
verdict as arc: no alias exists, so nothing to expand into. num and msg are
already full words, they are not abbreviations at all.

One special case. Line 77 read "often used with the par key (parameter) and ret
(return)" - the description was explaining the abbreviations it used. Expanding
the words leaves "the param key (parameter)", so the parenthetical goes: the
word is now the word.
"""
import io
import re
import sys

PATH = "DATA/dictionary_sorted_by_type.txt"
SPECIAL = ("often used with the par key (parameter) and ret (return)",
           "often used with the param key and the return key")
# longest first so func is never eaten by a partial fun
RULES = [("func", "function"), ("fun", "function"), ("par", "param"),
         ("err", "error"), ("scop", "scope"), ("syn", "syntax"), ("ret", "return")]


def main():
    raw = io.open(PATH, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    apply = "--apply" in sys.argv

    n0 = text.count(SPECIAL[0])
    print("  частный случай (строка 77): %d" % n0)
    text = text.replace(*SPECIAL)

    total = 0
    for short, full in RULES:
        pat = re.compile(r"\b%s\b" % short)
        lines = [i + 1 for i, l in enumerate(text.split("\n")) if pat.search(l)]
        n = len(pat.findall(text))
        total += n
        print("  %-5s -> %-9s %2d  строки %s" % (short, full, n, lines[:8]))
        if apply:
            text = pat.sub(full, text)

    print("\nзаменено: %d" % total)
    if not apply:
        print("(только план)")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="").write(
        text.replace("\n", "\r\n") if crlf else text)
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
