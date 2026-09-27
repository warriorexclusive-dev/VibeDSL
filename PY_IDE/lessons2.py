# -*- coding: utf-8 -*-
"""record what this round established, in the format the dataset already uses

The one that matters most is the vector: I relaxed a check because
param=file in two functions looked harmless, and the relaxation was the bug,
not the finding. A word bound twice has two meanings, and the base allows one
word one concept. The check was right and I softened it.
"""
import io
import json
import sys

P = "DATA/lessons.jsonl"
NEW = [
    {
        "id": "binding-01",
        "topic": "binding",
        "wrong": "id and param may repeat in one spec - a param belongs to its function, so param=file twice is harmless",
        "right": "a word bound twice is a VECTOR on that word; id and param are one namespace and each name is bound once per spec",
        "rule": "one word, one binding, one meaning, per spec",
        "why": "I found five real vectors in PY_IDE/window.vibe - file, param x3, size, name - and then relaxed the check "
               "that found them, on the grounds that a param is function-local. That reasoning is exactly the error: "
               "the repetition IS the defect, whether or not each function means something different by it. Softening a "
               "check because a finding looks harmless is how a finding stops being reported, and the finding was right.",
        "check": "validator.check_id_unique",
        "gate": "SPELL",
    },
    {
        "id": "binding-02",
        "topic": "binding",
        "wrong": "a spec may declare id=\"theme\" because in this spec theme is a prop",
        "right": "a spec may not claim a name the base already explains; it uses the base word as it is",
        "rule": "the base owns the word, a spec owns the placement",
        "why": "27 of 50 declarations in window.vibe did this - view, theme, text, frm, left and 23 more, the same "
               "collision as goal and col. It also cost the compiler: a locally claimed name has to be spared from "
               "compiling, so show(theme) stopped being a mark until the claim was removed. The name was never the "
               "spec's to take.",
        "check": "validator.check_ids",
        "gate": "SPELL",
    },
    {
        "id": "paren-01",
        "topic": "compiling",
        "wrong": "a command written as check(x) never compiles, because everything inside () is protected",
        "right": "() and [] are transparent - a word inside them is a word - and {} stays protected because a brace block is a free-form custom block",
        "rule": "quotes and {} protect; () and [] do not",
        "why": "I fixed a non-canonical != by writing !(check(x) == none), which moved check inside a paren and stopped "
               "it compiling - a fix for one word on a line broke a working word on the same line, and the report still "
               "said 9 so it looked finished. The paren was never meant to hide a command.",
        "check": "compiler.segments",
        "gate": "SPELL",
    },
    {
        "id": "report-01",
        "topic": "reporting",
        "wrong": "the compile report says one line has a non-canonical !=",
        "right": "it deduplicates: one message stood for ten occurrences, and both had to be found by grepping",
        "rule": "a deduplicated report counts kinds, not places",
        "why": "scop= and != were reported as one line each. scop= was one. != was ten. Reading the count instead of "
               "grepping would have left nine of them, and I only found them because the number felt too small.",
        "check": "compiler RX_NOTEQ",
        "gate": "SPELL",
    },
    {
        "id": "parens-01",
        "topic": "compiling",
        "wrong": "protecting locally declared names from compiling is how paren transparency can be added safely",
        "right": "the protection was a symptom - the spec had claimed 27 names from the base, and removing the claims removed the need for the exception",
        "rule": "fix the collision, do not shield from it",
        "why": "local_names() covered up exactly what binding-02 describes. Two mechanisms, one cause, and the "
               "covering one is what would have kept the cause alive.",
        "check": "compiler.local_names",
        "gate": "SPELL",
    },
]


def main():
    apply = "--apply" in sys.argv
    raw = io.open(P, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    have = set()
    for l in raw.replace("\r\n", "\n").split("\n"):
        if l.strip():
            have.add(json.loads(l).get("id"))
    add = [r for r in NEW if r["id"] not in have]
    print("  уже есть: %d, добавляю: %d" % (len(have), len(add)))
    for r in add:
        print("   + %-12s %s" % (r["id"], r["topic"]))
    if not apply:
        print("(только план)")
        return 0
    text = raw.replace("\r\n", "\n").rstrip("\n")
    for r in add:
        text += "\n" + json.dumps(r, ensure_ascii=False)
    io.open(P, "w", encoding="utf-8", newline="").write(
        text + "\n" if not crlf else text + "\r\n")
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
