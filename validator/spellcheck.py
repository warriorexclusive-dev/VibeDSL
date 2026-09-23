#!/usr/bin/env python3
"""spellcheck.py - stage 1 (get_commands): split the whole dictionary by
category and save each block to its own file.

Spec: plan/spellcheck-stage1.vibe

    stage 1:
       abstract function id="get_commands" -> src:dict
          crt file="action.dict" as file_action
          ...
          get_commands(dict:src):swt:type:
             case "action":      save(file_action)
             case "mapping":     save(file_mapping)
             case "operator":    save(file_operators)
             case "abstracts":   save(file_abstracts)

Category blocks come from the explicit `type:<name>` section headers in
dictionary_sorted_by_type.txt.
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, os.pardir, "DATA")
OUT = os.path.join(HERE, "out")

SRC = os.path.join(DATA, "dictionary_sorted_by_type.txt")

CASES = [
    ("action",           "action.dict"),
    ("mapping",          "mapping.dict"),
    ("logical operators", "operators.dict"),
    ("abstracts",        "abstracts.txt"),
    ("behavior",         "abstracts.txt"),
]


def read(path):
    return io.open(path, encoding="utf-8").read()


def split_blocks(text):
    header_re = re.compile(r"^type:(\S.*)$", re.MULTILINE)
    bounds = [m.start() for m in header_re.finditer(text)]
    blocks = {}
    for i, pos in enumerate(bounds):
        header = header_re.match(text, pos).group(1).strip()
        end = bounds[i + 1] if i + 1 < len(bounds) else len(text)
        blocks[header] = text[pos:end].rstrip("\n") + "\n"
    return blocks


def count_entries(blob):
    return len(re.findall(r"^\*-> ", blob, re.MULTILINE))


def main():
    os.makedirs(OUT, exist_ok=True)
    text = read(SRC)
    blocks = split_blocks(text)
    missing = [name for name, _ in CASES if name not in blocks]
    if missing:
        raise SystemExit("no section for: %s" % ", ".join(missing))

    merged = {}
    for name, filename in CASES:
        merged.setdefault(filename, []).append((name, blocks[name]))

    total = 0
    for filename, parts in merged.items():
        body = "".join(blob for _, blob in parts)
        prefix = "start language dictionary\n\n"
        path = os.path.join(OUT, filename)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(prefix + body)
        n = count_entries(body)
        total += n
        print("  %-14s %s  (%d entries, %s:%s)" % (
            filename, os.path.getsize(path),
            n, parts[0][0], ",".join(p[0] for p in parts)))
    print("total entries=%d" % total)


if __name__ == "__main__":
    main()