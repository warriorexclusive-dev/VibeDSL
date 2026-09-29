# -*- coding: utf-8 -*-
"""prove ID_FRAME in both directions, on a file that does not exist yet

ID_FRAME passed with nothing to read, which is the same defect as ABSTRACT_SLOT
and GLYPH_ONE: green for the wrong reason. A framed id has never been written
into a spec, so both directions are untested.

So: take a real glyph spec, frame a real id correctly, confirm the check stays
quiet, then break it two ways - put a concept glyph inside the frame, and leave
an alphabet glyph bare - and confirm it speaks both times.
"""
import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F_OPEN, F_SHUT = chr(0x25B9), chr(0x25C2)
A1 = chr(0x23BE) + chr(0x23C0) + chr(0x23C6) + chr(0x23CC)
CONCEPT = chr(0x25B6)          # run
SPEC = os.path.join(ROOT, "PY_IDE", "win.vglyph")

orig = io.open(SPEC, encoding="utf-8-sig").read()
anchor = chr(0x2330)           # first abstract line


def run(label):
    r = subprocess.run([sys.executable, "-X", "utf8",
                        os.path.join(ROOT, "validator", "glyph_checker.py")],
                       capture_output=True, text=True, encoding="utf-8")
    hit = [l.strip() for l in r.stdout.split("\n")
           if "ID_FRAME" in l or ("win.vglyph" in l and "alphabet" in l)
           or "framed" in l]
    print("  %-28s %s" % (label, hit[0] if hit else "НЕТ ВЫВОДА"))


try:
    # 1. a correct framed id - the check must stay quiet
    io.open(SPEC, "w", encoding="utf-8", newline="").write(
        orig.replace(anchor, "%s%s%s\n%s" % (F_OPEN, A1, F_SHUT, anchor), 1))
    run("корректная рамка")

    # 2. a concept glyph inside the frame
    io.open(SPEC, "w", encoding="utf-8", newline="").write(
        orig.replace(anchor, "%s%s%s%s\n%s" % (F_OPEN, A1, CONCEPT, F_SHUT, anchor), 1))
    run("внутри рамки концепт")

    # 3. a bare alphabet glyph outside the frame
    io.open(SPEC, "w", encoding="utf-8", newline="").write(
        orig.replace(anchor, "%s\n%s" % (A1, anchor), 1))
    run("алфавит без рамки")
finally:
    io.open(SPEC, "w", encoding="utf-8", newline="").write(orig)
    print("  восстановлено")
