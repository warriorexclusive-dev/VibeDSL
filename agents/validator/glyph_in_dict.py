# -*- coding: utf-8 -*-
"""put a glyph where a concept is named, inside the English description

"action: action=\"desc\" declares any function" - reading that, there is no way
to tell whether the two `action` are the concept or English prose. They are the
concept, and the entry name above is also the concept, and `->` is also a word
in this dictionary, and `and` and `or` and `not` are words too. A glyph is
unambiguous, a word is not - that is the whole confusion this removes.

Conservative on purpose. The descriptions are English, and English is full of
words that happen to be concept names: file, name, data, type, set, get, list,
map, rule, time, code, text, date. Substituting those would not clarify, it would
destroy. So a word becomes a glyph only where it is in a syntactic position -
followed by :, ( or =, or preceded by one, or inside quotes. Free prose is left
alone and stays English.
"""
import collections
import importlib.util as u
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["DATA/dictionary_sorted_by_type.txt", "DATA/action.dict",
         "DATA/mapping.dict", "DATA/operators.dict", "DATA/abstracts.txt"]

# a concept word is replaced only next to these, or inside quotes
AFTER = (":", "(", "=", "\u2a72", "\"", ">", "[")
BEFORE = (":", ")", "\"", "<", "\u2a72", " ")


def main():
    apply = "--apply" in sys.argv
    sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
    cc = u.module_from_spec(sp)
    sp.loader.exec_module(cc)
    _, _, w2g, _ = cc.load_alias_to_glyph()
    # the entry name itself must stay a word - it is the key
    skip = set()

    def swap(text):
        hit = [0]

        def one(m):
            w = m.group(0)
            i = m.start()
            prev = text[i - 1] if i else " "
            nxt = text[m.end()] if m.end() < len(text) else " "
            quoted = '"' in text[max(0, i - 40):i]
            if not (nxt in AFTER or prev in BEFORE or quoted):
                return w
            g = w2g.get(w.lower())
            if not g:
                return w
            hit[0] += 1
            return g

        out = re.sub(r"[A-Za-z_]\w*", one, text)
        return out, hit[0]

    total = 0
    for f in FILES:
        p = os.path.join(ROOT, f)
        raw = io.open(p, encoding="utf-8-sig").read()
        crlf = "\r\n" in raw
        lines = raw.replace("\r\n", "\n").split("\n")
        n = 0
        for i, l in enumerate(lines):
            if l.lstrip().startswith("#") or "-> exm:" in l:
                continue
            m = re.match(r"^(\*->\s*[^-\n]*?)\s+-\s+(.*)$", l)
            if not m:
                continue
            head, desc = m.group(1), m.group(2)
            new, cnt = swap(desc)
            if cnt and new != desc:
                lines[i] = head + " - " + new
                n += cnt
        if n:
            io.open(p, "w", encoding="utf-8", newline="").write(
                "\n".join(lines).replace("\n", "\r\n") if crlf else "\n".join(lines))
        print("  %-38s подставлено глифов: %d" % (f, n))
        total += n
    print("  всего: %d" % total)
    if not apply:
        print("(только план)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
