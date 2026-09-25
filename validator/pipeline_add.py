#!/usr/bin/env python3
"""pipeline_add.py - append a single dictionary entry to the master and rebuild.

    py -X utf8 validator\\pipeline_add.py <input.json>

input.json: {"section": "action|mapping|operators|abstracts",
             "value": "alias, alias2", "desc": "...", "exm": "..."}

Reads the master (DATA/dictionary_sorted_by_type.txt), composes a `*->` entry
block, rejects duplicate aliases, inserts the block into the requested
`type:<section>` block, then rebuilds the canon split files and ide/data.js
via the same scripts used by hand (sort_dict --write, spellcheck.py,
gen_data.py). Prints a single JSON line to stdout.
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir))
MASTER = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")

SECTION_HEADER = {
    "action": "type:action",
    "mapping": "type:mapping",
    "operators": "type:logical operators",
    "abstracts": "type:abstracts",
}

HEADER_RE = re.compile(r"^type:\S.*$", re.MULTILINE)
ENTRY_RE = re.compile(r"^(\*-> )(.*)$")


def read(path):
    return io.open(path, encoding="utf-8").read()


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="").write(text)


def compose_block(value, desc, exm):
    lines = ["*-> %s - %s" % (value, desc)]
    if exm:
        lines.append("    -> exm: %s" % exm)
    return "\n".join(lines)


def existing_aliases(text):
    aliases = set()
    for line in text.splitlines():
        m = ENTRY_RE.match(line)
        if not m:
            continue
        head = m.group(2).split(" - ", 1)[0].strip()
        for part in head.split(","):
            part = part.strip()
            if part:
                aliases.add(part.lower())
    return aliases


def insert_block(text, header, block):
    bounds = [m.start() for m in HEADER_RE.finditer(text)]
    dst = None
    nxt = None
    for i, pos in enumerate(bounds):
        line = text[pos:text.find("\n", pos)].strip()
        if line == header:
            dst = pos
            nxt = bounds[i + 1] if i + 1 < len(bounds) else len(text)
            break
    if dst is None:
        raise ValueError("no section header %r in master" % header)
    if nxt >= len(text) or not text[nxt:]:
        tail = "" if text.endswith("\n") else "\n"
        out = text + tail + "\n" + block + "\n"
    else:
        out = text[:nxt] + block + "\n\n" + text[nxt:]
    return out


def run_pipeline():
    py = sys.executable
    jobs = [
        [os.path.join("validator", "sort_dict.py"), "--write"],
        [os.path.join("validator", "spellcheck.py")],
        [os.path.join("ide", "gen_data.py")],
    ]
    logs = []
    for args in jobs:
        proc = subprocess.run([py, "-X", "utf8"] + args, cwd=ROOT,
                              capture_output=True, text=True, encoding="utf-8")
        merged = (proc.stdout or "").strip()
        if proc.returncode != 0:
            raise RuntimeError("%s failed:\n%s" % (args[0], merged or proc.stderr))
        if merged:
            logs.append(merged.splitlines())
    return logs


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: pipeline_add.py <input.json>\n")
        return 2
    payload = json.loads(read(sys.argv[1]))
    section = str(payload.get("section", ""))
    value = str(payload.get("value", "")).strip()
    desc = str(payload.get("desc", "")).strip()
    exm = str(payload.get("exm", "")).strip()

    if section not in SECTION_HEADER:
        print(json.dumps({"ok": False, "error": "unknown section %r" % section}))
        return 0
    if not value:
        print(json.dumps({"ok": False, "error": "value is required"}))
        return 0
    if " - " in value:
        print(json.dumps({"ok": False, "error": "value must not contain ' - '"}))
        return 0
    if not desc:
        print(json.dumps({"ok": False, "error": "description is required"}))
        return 0

    master = read(MASTER)
    known = existing_aliases(master)
    dup = [a for a in re.split(r"\s*,\s*", value) if a.lower() in known]
    if dup:
        print(json.dumps({"ok": False, "error": "duplicate alias: %s" % ", ".join(dup)}))
        return 0

    block = compose_block(value, desc, exm)
    updated = insert_block(master, SECTION_HEADER[section], block)
    write(MASTER, updated)

    logs = run_pipeline()
    print(json.dumps({
        "ok": True,
        "section": section,
        "value": value,
        "master": MASTER,
        "logs": logs,
    }, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())