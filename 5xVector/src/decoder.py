# -*- coding: utf-8 -*-
"""the decipher, moved out of the test and made a thing of its own

The model did not read the glyphs and it will not be asked to again. So the
reading is done here, by code, and the rules are what the code follows. The
difference is one line and it is the whole of the finding: a test proves the
format, and a decipher uses it.

    read_side   a run of signs to the words it stands for
    an address  five of the sixteen, and a sign that is not one of them
                separates, and a sign from an underscore joins
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import compiler_v2 as K

GLYPHS = os.path.join(ROOT, "compiled", "compiler.glyphs")
SPEC = os.path.join(ROOT, "specs", "compiler.vibe")

BACK = {v: k for k, v in K.MARK_GLYPH.items()}
FRAME = {"\u25f2", "\u25f3", "\u25fa", "\u25fc",
         "\u25f0", "\u25f1", "\u25f4", "\u25f5", "\u25f6", "\u25f7",
         K.arrow(), "->", "(", ")", "[", "]", "{", "}", "<", ">", ":"}
CLOSE = {"\u25f2": "\u25f3", "\u25fa": "\u25fc",
         "\u25f0": "\u25f1", "\u25f4": "\u25f5", "\u25f6": "\u25f7"}


def addr(run, entries, offs):
    w = K.width()
    if len(run) % w:
        return None
    v = 0
    for ch in run:
        if ch not in K.G:
            return None
        v = (v << 4) | K.G.index(ch)
    return entries[offs.index(v)] if v in offs else None


def side(run, entries, offs):
    """the words of one run, and the signs that stood between them"""
    out, cur, signs, glue = [], [], [], False
    for ch in run:
        if ch in K.G:
            cur.append(ch)
            continue
        if cur:
            word = addr("".join(cur), entries, offs)
            if word is None:
                return None, signs
            if glue and out:
                out[-1] = out[-1] + "_" + word
            else:
                out.append(word)
            cur = []
        glue = BACK.get(ch) == "_"
        signs.append(ch)
    if cur:
        word = addr("".join(cur), entries, offs)
        if word is None:
            return None, signs
        if glue and out:
            out[-1] = out[-1] + "_" + word
        else:
            out.append(word)
    return out, signs


def line(text, entries, offs):
    """one compiled line, read back to the words it was written from"""
    body = text.strip().lstrip(K.SP)
    left, arrow, right = body.partition(K.arrow())
    if not arrow:
        return None, "no arrow"
    words, marks = [], []
    for part in left.split(K.SEP):
        if not part:
            continue
        w, sg = side(part, entries, offs)
        if w is None:
            return None, "the left side does not decode"
        words.extend(w)
        marks.extend(sg)

    right = right.strip()
    head = right
    for o in CLOSE:
        if o in head:
            head = head.split(o, 1)[0]
            break
    w, sg = side(head, entries, offs)
    if w is None:
        return None, "the function does not decode"
    words.extend(w)
    marks.extend(sg)

    while True:
        o = c = None
        for a, b in CLOSE.items():
            if a in right:
                o, c = a, b
                break
        if not o:
            break
        i = right.index(o)
        j = right.find(c, i)
        if j < 0:
            return None, "a block is not closed"
        w, sg = side(right[i + 1:j], entries, offs)
        if w is None:
            return None, "inside a block it does not decode"
        words.extend(w)
        marks.extend(sg)
        right = right[:i] + " " + " ".join(w) + " " + right[j + 1:]
    return words, None


def main():
    entries = K.load()
    offs = K.offsets(entries)
    compiled = [l for l in io.open(GLYPHS, encoding="utf-8").read().split("\n")
                if l.strip()]
    source = [l for l in io.open(SPEC, encoding="utf-8").read().split("\n")
              if l.strip()]
    print("")
    print("  ДЕШИФРАТОР, КАК КОД, НЕ КАК ТЕСТ")
    print("    вход    %s" % os.path.basename(GLYPHS))
    print("    рядом   %s" % os.path.basename(SPEC))
    print("    ширина  %d глифов" % K.width())
    print("    раздел  %d знаков" % len(FRAME))
    print("")
    ok = bad = 0
    first = None
    for n, (src, comp) in enumerate(zip(source, compiled), 1):
        got, err = line(comp, entries, offs)
        if err:
            bad += 1
            if first is None:
                first = (n, err, src, comp)
            continue
        # the frame and the marks go, the underscore stays: it is part of a
        # name and not a mark, and cleaning it away loses the name
        want = re.sub(r"[()\[\]{}<>:→.\-]", " ", src.strip().lstrip("- ").lower())
        want = " ".join(want.split())
        got_s = " ".join(got).lower()
        if got_s == want:
            ok += 1
        else:
            bad += 1
            if first is None:
                first = (n, "decodes but does not match", want, got_s)
    print("    прочитано %d, отказов %d" % (ok, bad))
    if first:
        n, err, a, b = first
        print("")
        print("  ПЕРВЫЙ ОТКАЗ, СТРОКА %d: %s" % (n, err))
        print("    в исходнике %s" % a[:60])
        print("    прочитано   %s" % b[:60])
        return 1
    print("")
    print("  ДЕШИФРАТОР РАБОТАЕТ, %d ИЗ %d" % (ok, ok + bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
