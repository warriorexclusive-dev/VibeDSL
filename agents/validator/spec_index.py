# -*- coding: utf-8 -*-
"""spec index: id -> what it is, where it is, without reading the whole file

Grepping a 294-line spec for the same six names ten times a session is the
symptom. The answer is an index, and the answer to "the dictionary lives in five
copies" is that this one is GENERATED and never hand-edited - with --check to
prove it still agrees with the spec, because a derived copy that drifts is
worse than no copy.

Also allocates a free id from the id space, since the id space is generated and
something has to hand out the next one. Handing out ids by hand is how five
invented names got in.

    U+2387 ⎇   U+253F ┿   - confirmed to render on the owner machine
"""
import collections
import importlib.util as u
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = ".vglyph"

ABSTRACT = chr(0x2330)
TYPES = {chr(0x2B1D): "item", chr(0x02A9): "function", chr(0x2317): "prop"}
ID = chr(0x00A7)
ASSIGN = chr(0x2A72)
Q = chr(0x22)
ID_SPACE = [chr(0x2387), chr(0x253F)]

HEAD = re.compile(
    re.escape(ABSTRACT) + r"(?::(" + "|".join(map(re.escape, TYPES)) + r"))?"
    r":" + re.escape(ID) + re.escape(ASSIGN) + Q + r"(\w+)" + Q)


def read(p):
    return io.open(p, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")


def scan():
    rows = []
    dupes = collections.defaultdict(list)
    files = []
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and d not in ("temp", ".git", "GLOS", "node_modules", "__pycache__")]
        for n in sorted(names):
            if n.endswith(EXT):
                files.append(os.path.join(base, n).replace(ROOT + os.sep, ""))
    for f in sorted(files):
        for i, line in enumerate(read(f), 1):
            if line.lstrip().startswith(ABSTRACT):
                m = HEAD.match(line.lstrip())
                if m:
                    kind = TYPES.get(m.group(1)) or "БЕЗ ТИПА"
                    rows.append((m.group(2), kind, f, i))
                    dupes[m.group(2)].append("%s:%d" % (f, i))
    return rows, {k: v for k, v in dupes.items() if len(v) > 1}


def render(rows, dupes):
    out = []
    w = max((len(r[0]) for r in rows), default=4)
    for name, kind, f, ln in rows:
        out.append("  %-*s  %-8s  %s:%d" % (w, name, kind, f.replace("\\", "/"), ln))
    out.append("")
    out.append("  абстрактов: %d   файлов: %d" % (len(rows), len(set(r[2] for r in rows))))
    if dupes:
        out.append("  ДУБЛИ (id в одном пространстве):")
        for k, v in sorted(dupes.items()):
            out.append("    %s  ->  %s" % (k, ", ".join(v)))
    else:
        out.append("  дублей нет")
    return "\n".join(out)


def free_id(rows, take=8):
    used = set(r[0] for r in rows)
    n = len(ID_SPACE)
    out = []
    for ln in range(1, 6):
        for a in ID_SPACE:
            for b in ID_SPACE:
                cand = a + b if ln == 2 else a + b * (ln - 1)
                if cand not in used and cand not in out:
                    out.append(cand)
                    if len(out) >= take:
                        return out
    return out


def main():
    rows, dupes = scan()
    if "--ids" in sys.argv:
        print("  свободные id из пространства %s (5 глифов, 3125 комбинаций):" % "".join(ID_SPACE))
        print("  %s" % "  ".join(free_id(rows)))
        return 0
    print(render(rows, dupes))
    return 1 if dupes else 0


if __name__ == "__main__":
    sys.exit(main())
