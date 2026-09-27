#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lessons.py - DATA/lessons.jsonl must agree with the tree it describes.

A lessons file that drifts is worse than none: it would be training a model on
a dictionary that no longer exists. So every record carries a `check` - a
substring that MUST be gone, or a substring that MUST be there - and this
verifies both against the live files.

    py -X utf8 validator\\lessons.py            # report
    py -X utf8 validator\\lessons.py --topics   # the shape

A record may also carry `gate`: the check in spell_checker_v2 that would catch
its class of defect. Where gate is "none", the defect was invisible to every
check that exists, and that is recorded rather than hidden - those are the
blind spots this file was built out of.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
LESSONS = os.path.join(ROOT, "DATA", "lessons.jsonl")
MASTER = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")
SYM = os.path.join(ROOT, "compiler", "symbols_map.txt")
SPEC = os.path.join(ROOT, "PY_IDE", "window.vibe")

# where a `check` string is looked for. Ordered: first hit wins.
PLACES = [
    ("master", MASTER),
    ("symbols", SYM),
    ("spec", SPEC),
]


def read(p):
    return io.open(p, encoding="utf-8-sig").read()


def load():
    rows = []
    for n, line in enumerate(read(LESSONS).replace("\r\n", "\n").split("\n"), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        try:
            rows.append((n, json.loads(s)))
        except ValueError as e:
            print("  x line %d is not JSON: %s" % (n, e))
    return rows


def blob():
    return "\n".join(read(p) for _n, p in PLACES)


def main(argv):
    rows = load()
    if "--topics" in argv:
        by = {}
        for _n, r in rows:
            by.setdefault(r.get("topic", "?"), []).append(r["id"])
        for t in sorted(by):
            print("  %-9s %2d   %s" % (t, len(by[t]), ", ".join(sorted(by[t]))))
        print("  %-9s %2d" % ("TOTAL", len(rows)))
        return 0

    text = blob()
    bad = nofind = nogate = 0
    for n, r in rows:
        rid = r.get("id", "line%d" % n)
        for field in ("id", "topic", "wrong", "right", "rule", "why", "check"):
            if not r.get(field):
                print("  x %-12s missing field '%s'" % (rid, field))
                bad += 1
        chk = r.get("check", "")
        if chk.startswith("master: ") or chk.startswith("symbols: ") or chk.startswith("PY_IDE"):
            needle = chk.split(" ", 1)[1].strip() if " " in chk else chk
            if needle in ("-", ""):
                nofind += 1
                continue
            if needle in text:
                print("  x %-12s check string is STILL IN THE TREE: %r" % (rid, needle))
                bad += 1
        if r.get("gate", "none") == "none":
            nogate += 1
    print("записей: %d" % len(rows))
    print("нарушений: %d" % bad)
    print("без gate (слепые зоны): %d из %d" % (nogate, len(rows)))
    print("темы: %s" % ", ".join(sorted({r.get("topic", "?") for _n, r in rows})))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
