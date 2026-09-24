#!/usr/bin/env python3
"""sort_dict.py - keep DATA/dictionary_sorted_by_type.txt in order.

Entries are `*-> alias - desc` blocks (with optional indented `-> exm:` lines),
grouped under `type:<name>` section headers. This script sorts the entry
blocks inside each section by their PRIMARY alias (case-insensitive) while
keeping the section header order unchanged.

    py -X utf8 validator\\sort_dict.py            # report out-of-order entries
    py -X utf8 validator\\sort_dict.py --write   # rewrite the master in order

Exit code 1 if any section is out of order (unless --write succeeds).
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.normpath(os.path.join(HERE, "..", "DATA", "dictionary_sorted_by_type.txt"))

HEADER_RE = re.compile(r"^type:\S.*$", re.MULTILINE)
ENTRY_RE = re.compile(r"(?m)^(?=\*-> )")


def primary_alias(blk):
    m = re.match(r"\*->\s+(.+)", blk)
    if not m:
        return ""
    head = m.group(1).split(" - ", 1)[0].strip()
    first = head.split(",")[0].strip()
    return first


def split_sections(text):
    bounds = [m.start() for m in HEADER_RE.finditer(text)]
    sections = []
    for i, pos in enumerate(bounds):
        end = bounds[i + 1] if i + 1 < len(bounds) else len(text)
        sections.append(text[pos:end])
    return sections


def split_entries(blob):
    return [b for b in ENTRY_RE.split(blob) if b.lstrip().startswith("*->")]


def report(sections):
    bad = []
    for sec in sections:
        header = HEADER_RE.match(sec).group(0)
        entries = split_entries(sec)
        keys = [(primary_alias(b), b) for b in entries]
        prev = None
        for i, (k, _b) in enumerate(keys):
            if prev is not None and k.lower() < prev.lower():
                bad.append((header, i + 1, k, prev))
            prev = k
    return bad


def main():
    text = io.open(PATH, encoding="utf-8").read()
    sections = split_sections(text)
    bad = report(sections)
    if "--write" in sys.argv:
        rebuilt = []
        first = HEADER_RE.search(text)
        preamble = text[: first.start()] if first else ""
        for sec in sections:
            header = HEADER_RE.match(sec).group(0)
            entries = sorted(split_entries(sec), key=lambda b: primary_alias(b).lower())
            rebuilt.append(header + "\n\n" + "\n\n".join(e.strip() for e in entries) + "\n")
        out = preamble + "\n".join(rebuilt)
        io.open(PATH, "w", encoding="utf-8", newline="").write(out)
        print("rewrote %s (%d bytes)" % (PATH, len(out)))
        return 0
    if bad:
        for header, pos, key, prev in bad:
            print("  [%s] at #%d: '%s' should come after '%s'" % (header, pos, key, prev))
        print("%d inversion(s); run with --write to fix" % len(bad))
        return 1
    print("sorted OK: %d sections, no out-of-order entries" % len(sections))
    return 0


if __name__ == "__main__":
    sys.exit(main())