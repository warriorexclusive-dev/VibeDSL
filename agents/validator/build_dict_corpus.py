#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_dict_corpus.py - the whole dictionary, as training records.

The lessons file holds what went wrong. This holds what IS: every concept the
base has, with its names, its mark and its declared meaning, generated from the
live master and the live table so it cannot drift from them.

A 0.5B advisor is not a second compiler. It is asked short questions by a
person and answers with a concept. So each record is shaped as an ask and an
answer, not as a spec to reproduce:

    ask    "what marks a direct indication of a goal"
    answer "target - ⌾ - direct logical indication of a goal: ..."

Three fields carry the weight:

  trigger   the surface forms a person is likely to reach for, so the embedding
            has to pull from the word and not only from the mark
  mark      the one token, for a model whose weights know it
  refuse    the readings this word invites, when the base declared them. This
            is the part that cannot be inferred: `except` means exclusion to
            every model, and the base said so out loud.

Records whose meaning names another concept get a `distinct_from` field, so
the pairs that the embedding is most likely to collapse - environment/os,
none/unknown, incld/import, goal/target - are stated as pairs rather than as
two separate facts.

    py -X utf8 validator\\build_dict_corpus.py            # report
    py -X utf8 validator\\build_dict_corpus.py --write
"""
import importlib.util
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "DATA", "dict_corpus.jsonl")
MASTER = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")

RX = re.compile(r"^\*->\s*(.+?)\s+-\s+(.*)$")
RX_NOT = re.compile(r"\bNOT\b\s*([^.;:]+)")


def compiler():
    spec = importlib.util.spec_from_file_location(
        "_cc", os.path.join(ROOT, "compiler", "compile.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv):
    cc = compiler()
    co, concepts, w2g, glyphs = cc.load_alias_to_glyph()
    # mark filed under any name of the concept
    mark_of = {}
    for prim, info in concepts.items():
        for n in info["names"]:
            if n.lower() in w2g:
                mark_of[prim] = (w2g[n.lower()], w2g[n.lower()])
                break

    rows = []
    for prim, info in sorted(concepts.items()):
        names = info["names"]
        desc = (info.get("desc") or "").strip()
        g = mark_of.get(prim, (None, None))[0]
        rec = {
            "concept": prim,
            "names": names,
            "mark": g,
            "meaning": desc,
            "trigger": names,
        }
        refuses = [m.group(1).strip() for m in RX_NOT.finditer(desc)]
        if refuses:
            rec["refuse"] = refuses
        # a described contrast is the pair an embedding is most likely to collapse
        for other in re.findall(r"NOT (\w+)", desc):
            if other in concepts and other != prim:
                rec.setdefault("distinct_from", []).append(other)
        if g is None:
            rec["no_mark"] = True
        rows.append(rec)

    print("концептов: %d" % len(rows))
    print("со знаком  : %d" % sum(1 for r in rows if r.get("mark")))
    print("без знака  : %d" % sum(1 for r in rows if r.get("no_mark")))
    print("с refuse   : %d" % sum(1 for r in rows if r.get("refuse")))
    print("с contrast : %d" % sum(1 for r in rows if r.get("distinct_from")))

    if "--write" not in argv:
        print("(только отчёт; для записи добавьте --write)")
        return 0
    with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\r\n")
    print("ЗАПИСАНО: %s" % os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
