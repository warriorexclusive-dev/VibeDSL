# -*- coding: utf-8 -*-
"""glyphs -> words, so the word form is a rendering and not a hand-typed artifact

The whole failure this morning was a hand-written word spec. 2220 mechanical
replacements lost nothing; 294 hand-typed lines lost four defects. So the word
form must never be typed - it must be rendered from the glyph form, and then
compared against it.

The reverse map is safe: 322 concepts, and only 5 carry more than one word, all
of them deliberate operator aliases (&& / and, or / |, ! / not / revers). There
is no ambiguity worth a decision.

    glyph spec --render--> word spec --compile--> must equal the glyph spec

If that last equality fails, a word is standing for a concept the author did not
mean, and that is the defect this whole exercise exists to catch.
"""
import collections
import importlib.util as u
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _compiler():
    sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
    cc = u.module_from_spec(sp)
    sp.loader.exec_module(cc)
    return cc


def glyph_to_word():
    cc = _compiler()
    concept_of, _, word_to_glyph, _ = cc.load_alias_to_glyph()
    by_concept = collections.defaultdict(list)
    for w, g in word_to_glyph.items():
        if g:
            by_concept[g].append(w)
    by_glyph = {}
    for g, words in by_concept.items():
        # prefer a readable word over a punctuation alias (and over &&, or over
        # |), and a spelled word over a cryptic one (true over y, set over s).
        # the alias exists for writing, the word for reading, and this is the
        # reading side.
        words.sort(key=lambda w: (not re.match(r"^[A-Za-z_]\w*$", w), -len(w), w))
        by_glyph[g] = words[0]
    return cc, by_glyph


ANCHOR = "•"


def render(text, by_glyph, cc):
    """glyphs -> words, with a space where two words would otherwise glue

    A glyph delimits itself; a word does not. ¬▣ rendered naively is
    "reverscheck", one token, and the meaning of the line is gone. This defect
    exists only in the word layer and cannot exist in the glyph layer.

    U+2022 is deliberately overloaded: the compiler writes it for the "&->"
    constructor AND it is the anchor glyph. There are not enough free glyphs to
    give the constructor its own, and splitting it would mean hunting for spares
    across every abstract. So the position decides: at the head of a line it is
    the constructor, elsewhere it is the word. Rendering it as "anchor" is what
    ate the four id declarations - the line stopped being a declaration.
    """
    out = []
    prev_word = False
    at_head = True
    for ch in text:
        if ch == "\n":
            out.append(ch)
            at_head = True
            prev_word = False
            continue
        if ch == ANCHOR and at_head:
            out.append("&->")
            prev_word = False
            at_head = False
            continue
        w = by_glyph.get(ch)
        if w is None:
            out.append(ch)
            prev_word = False
        else:
            # a space only between two words. = and : are spelled words too,
            # and gluing was only ever needed between two real ones: "id ="
            # breaks the grammar the same way "reverscheck" did.
            if prev_word and re.match(r"^[A-Za-z_]\w*$", w):
                out.append(" ")
            out.append(w)
            prev_word = bool(re.match(r"^[A-Za-z_]\w*$", w))
        if not ch.isspace():
            at_head = False
    return "".join(out)


def main():
    src = os.path.join(ROOT, "PY_IDE", "window.vglyph")
    dst = os.path.join(ROOT, "PY_IDE", "window.render.vibe")
    cc, by_glyph = glyph_to_word()
    g = io.open(src, encoding="utf-8-sig").read()
    w = render(g, by_glyph, cc)
    apply = "--apply" in sys.argv
    # and the check that matters: does the word form compile back to the glyphs
    co, cs, w2g, gl = cc.load_alias_to_glyph()
    sub, _, _ = cc.build_substitution(co, cs, w2g, gl)
    rx = cc.make_token_rx(sub)
    lines = w.replace("\r\n", "\n").split("\n")
    st = {"replaced": 0, "words": collections.Counter(), "unmapped": set(),
          "undefined": set(), "missing_use": [], "glyphs_used": [], "noteq": set()}
    back = "\n".join(cc.compile_line(l, sub, rx, st, None, cc.local_names(lines))
                     for l in lines)
    orig = g.replace("\r\n", "\n")
    print("  глифов отрендерено в слова: %d" % len(by_glyph))
    print("  слов подставлено: %d" % st["replaced"])
    print("  не распознано: %d" % len(st["undefined"]))
    print("  КРУГ СОШЁЛСЯ (рендер -> компиляция == исходные глифы): %s" % (back == orig))
    if not apply:
        print("(только план)")
        return 0 if back == orig else 1
    io.open(dst, "w", encoding="utf-8", newline="\r\n").write(w)
    print("  ЗАПИСАНО %s" % dst)
    return 0 if back == orig else 1


if __name__ == "__main__":
    sys.exit(main())
