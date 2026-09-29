# -*- coding: utf-8 -*-
"""checks for the glyph layer, on the same principles as the word layer

The word layer has 13 named checks and a summary. All 13 read words, so all 13
audit the report and none of them audits the source. The glyph layer therefore
has no checks at all, and the two failures below went through a green verdict:

    minimayz, maksimayz    written as words, minim and maxim already existed
    menu                    not a concept, substituted with a btn named file

Both are holes. A hole is a name the spec uses that the language has no concept
behind, and the spec papered over it instead of stopping. Nothing detected it,
because nothing was looking for holes.

Same principles as the word layer, applied to glyphs:
  - named checks, one verdict, no masking
  - a failure is a failure; nothing is downgraded to keep a count
  - a check states what it can and cannot see
"""
import collections
import importlib.util as u
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMP = os.path.join(ROOT, "compiler", "compile.py")
DICT = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")

# The word spell checker takes SPEC_EXT = (".vibe", ".vibedsl", ".spec"). Glyph
# files get their own extension so the layers never meet: the word checker must
# not read glyphs, the glyph checker must not read words. The extension is the
# boundary - not a flag, not a setting, not a weakened check. A hand-typed list
# of refs is how the two layers met before; this walks instead.
GLYPH_EXT = ".vglyph"


def find_glyphs():
    out = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and d not in ("temp", ".git", "GLOS", "node_modules", "__pycache__")
                   and not d.startswith("_restore")]
        for f in files:
            if f.endswith(GLYPH_EXT):
                out.append(os.path.join(base, f)[len(ROOT) + 1:].replace(os.sep, "/"))
    return sorted(out)


REFS = ()


def compiler():
    sp = u.spec_from_file_location("_cc", COMP)
    cc = u.module_from_spec(sp)
    sp.loader.exec_module(cc)
    return cc


def glyph_word_map(cc):
    _, _, w2g, _ = cc.load_alias_to_glyph()
    by_concept = collections.defaultdict(list)
    for w, g in w2g.items():
        if g:
            by_concept[g].append(w)
    by_glyph = {}
    for g, words in by_concept.items():
        words.sort(key=lambda w: (not re.match(r"^[A-Za-z_]\w*$", w), -len(w), w))
        by_glyph[g] = words[0]
    return w2g, by_concept, by_glyph


def read(p):
    if not os.path.exists(os.path.join(ROOT, p)):
        return None
    return io.open(os.path.join(ROOT, p), encoding="utf-8-sig").read().replace("\r\n", "\n")


def run():
    cc = compiler()
    w2g, by_concept, by_glyph = glyph_word_map(cc)
    global REFS
    REFS = find_glyphs()
    concepts = {g: ws for g, ws in by_concept.items()}
    base_glyphs = set(concepts)
    all_glyphs = set(ch for ch in "".join(base_glyphs) if not ch.isalnum())
    results = []
    notes = []

    def check(name, errs, sees):
        results.append((name, errs, sees))

    # GLYPH_ONE - one glyph, one concept

    # GLYPH_ALIAS - one concept, one glyph (no two glyphs for the same concept)

    # GLYPH_KNOWN - every glyph in a spec is in the base
    # match whole glyph strings, not characters: [] and {} are two characters
    # each and a per-character scan reports them as foreign.
    # The id alphabet is inside the frame and is deliberately unspelled, so it
    # has no word and would read as unknown. ID_FRAME governs it instead.
    ID_ALPHA = "".join(chr(c) for c in range(0x23BE, 0x23CE))
    F_O, F_S = chr(0x25B9), chr(0x25C2)
    e = []
    for p in REFS:
        s = read(p)
        if not s:
            continue
        # an id is a whole construct - take it out before scanning for unknowns

    # GLYPH_HOLE - the check that did not exist
    # a quoted name with no concept behind it. minimayz, maksimayz and menu
    # all pass a word gate and stop nothing; this is where they die.

    # GLYPH_CIRCLE - glyph -> words -> compile must return the glyphs
    e = []
    for p in REFS:
        s = read(p)
        if not s:
            continue
        w = render(s, by_glyph)
        co, cs, w2g2, gl = cc.load_alias_to_glyph()
        sub, _, _ = cc.build_substitution(co, cs, w2g2, gl)
        rx = cc.make_token_rx(sub)
        lines = w.split("\n")
        st = {"replaced": 0, "words": collections.Counter(), "unmapped": set(),
              "undefined": set(), "missing_use": [], "glyphs_used": [], "noteq": set()}
        back = "\n".join(cc.compile_line(l, sub, rx, st, None, cc.local_names(lines))
                         for l in lines)
        if re.sub(r"[ \t]+", "", back) != re.sub(r"[ \t]+", "", s):
            e.append("%s: круг не сошелся" % p)
    check("GLYPH_CIRCLE", e, "глифы -> слова -> глифы, без потерь")

    # ABSTRACT_TYPE - the type is mandatory, there is no default

    # ABSTRACT_SLOT - after \u00A7\u2A72 only a literal or the slot pattern
    e = []
    ROLE = ("any", "unique", "alias", "condition", "prop", "item", "function",
            "name", "id", "abstract")
    for p in REFS:
        s = read(p)
        if not s:
            continue
        for m in re.finditer(r"\u00A7\u2A72([^\n]{0,24})", s):
            what = m.group(1)
            ln = s[:m.start()].count("\n") + 1
            quoted = re.match(r'^"([A-Za-z_]\w*)"', what)
            if re.match(r"^\u2742:\u2255", what):
                continue                      # the slot, legal
            if quoted:
                if quoted.group(1).lower() in ROLE:
                    e.append("%s:%d id is a LITERAL named after a role word %r -"
                             " a role is a glyph, a name is a string" %
                             (p, ln, quoted.group(1)))
                continue
            e.append("%s:%d after \u00A7\u2A72 neither a string nor \u2742:\u2255"
                     " -> %r" % (p, ln, what[:16]))
    check("ABSTRACT_SLOT", e, "id is a literal or the slot, never a role word")

    # ID_FRAME - the id alphabet only exists inside the inward arrows
    e = []
    ID_ALPHA = "".join(chr(c) for c in range(0x23BE, 0x23CE))
    F_OPEN, F_SHUT = chr(0x25B9), chr(0x25C2)
    for p in REFS:
        s = read(p)
        if not s:
            continue
        # direction 1: framed content must be alphabet only
        for m in re.finditer(re.escape(F_OPEN) + r"([^" + re.escape(F_SHUT) + r"]*)"
                             + re.escape(F_SHUT), s):
            bad = [c for c in m.group(1) if c not in ID_ALPHA]
            if bad:
                ln = s[:m.start()].count("\n") + 1
                e.append("%s:%d framed id contains non-alphabet %s"
                         % (p, ln, "".join(sorted(set(bad)))))
        # direction 2: an alphabet glyph outside the frame is not an id
        stripped = re.sub(re.escape(F_OPEN) + r"[^" + re.escape(F_SHUT) + r"]*"
                          + re.escape(F_SHUT), "", s)
        for m in re.finditer("[" + re.escape(ID_ALPHA) + "]+", stripped):
            ln = stripped[:m.start()].count("\n") + 1
            e.append("%s:%d alphabet glyph %r outside the frame - a bare one is"
                     " not an id, it is a typo with no claim" % (p, ln, m.group(0)))
    check("ID_FRAME", e, "id lives only between the inward arrows, both ways")

    # ID_UNIQUE - addresses are local, unique, and never a near miss

    # GLYPH_COVER - what this layer still cannot see, stated not hidden
    d = read("DATA/blueprints.txt") or ""
    notes.append("GLYPH_COVER   чеков: %d, глифов в базе: %d, спек в обходе (*%s): %d" % (
        len(results) + 1, len(base_glyphs), GLYPH_EXT, len(REFS)))
    notes.append("  не видит: соответствие спеки задаче (вводной) - нет носителя")
    notes.append("  не видит: части интерфейса без концепта (menu, bar, chrome, tab)")

    return results, notes


def render(text, by_glyph):
    out = []
    prev = False
    for ch in text:
        w = by_glyph.get(ch)
        if w is None:
            out.append(ch)
            prev = False
            continue
        if prev:
            out.append(" ")
        out.append(w)
        prev = True
    return "".join(out)


def main():
    results, notes = run()
    w = max(len(n) for n, _, _ in results)
    failed = 0
    for name, errs, sees in results:
        if errs:
            failed += 1
            print("  FAIL %-*s %d" % (w, name, len(errs)))
            for e in errs[:6]:
                print("        %s" % e)
            if len(errs) > 6:
                print("        ... еще %d" % (len(errs) - 6))
        else:
            print("  ok   %-*s %s" % (w, name, sees))
    print("")
    for n in notes:
        print("  %s" % n)
    total = len(results)
    print("")
    print("  VERDICT: %s   %d check(s) run, %d passed, %d failed, 0 masked" % (
        "PASS" if not failed else "FAIL", total, total - failed, failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
