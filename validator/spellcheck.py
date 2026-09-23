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
import sys

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


# ---------------------------------------------------------------- stage 2
# spec: plan/spellcheck-stage1.vibe (stage 2)
#   open(file:"API/get")   :\(file:name="dictionary.txt" act="delete"):\(stage 1:[...] action="add"):rebuild()
#   open(file:"API/search") :as sc_file: fun name="search": ->\(... delete) ->\(... mix(...) add)  sc_file:rebuild()
# The four split files (action/mapping/operators/abstracts) become THE CANON
# once the spec passes: the parser knows syntax per type.

import html as _html
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:4545"

FILES = [("action", "action.dict"), ("mapping", "mapping.dict"),
         ("logical operators", "operators.dict"),
         ("abstracts", "abstracts.txt"), ("behavior", "abstracts.txt")]


def html_to_text(raw):
    m = re.search(r"<body>(.*)</body>", raw, re.S)
    text = m.group(1) if m else raw
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = text.replace("&nbsp;", " ")
    return _html.unescape(text)


def http_get(path, params=None):
    url = "%s/%s" % (BASE, path)
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=20) as r:
        raw = r.read().decode("utf-8", "replace")
    return html_to_text(raw)


def split_entries(text):
    return [b.strip() for b in re.split(r"(?m)^(?=\*-> )", text) if b.strip()]


def first_key(blk):
    m = re.match(r"\*->\s+([^\s,]+)", blk)
    return m.group(1) if m else None


def load_section_index(source):
    """primary alias -> section name, from the full sorted dictionary."""
    idx = {}
    for sec, blob in split_blocks(source).items():
        for blk in split_entries(blob):
            key = first_key(blk)
            if key:
                idx[key] = sec
    return idx


def act_delete():
    """delete local dictionary.txt (stale splits)."""
    for name, _ in FILES:
        p = os.path.join(OUT, name + ".part")
        if os.path.exists(p):
            os.remove(p)
    for fn in ("dictionary.txt",):
        p = os.path.join(OUT, fn)
        if os.path.exists(p):
            os.remove(p)


def save_parts(buckets, index):
    total = 0
    for sec, fn in FILES:
        blobs = buckets.get(sec, [])
        body = "".join(b + "\n\n" for b in blobs)
        with io.open(os.path.join(OUT, fn), "w", encoding="utf-8") as f:
            f.write(body)
        total += len(blobs)
        print("    %-14s %d entries" % (fn, len(blobs)))
    return total


def act_add(text, index):
    """add: split fetched/combined text into the four category files."""
    buckets = {sec: [] for sec, _ in FILES}
    unknown = []
    for blk in split_entries(text):
        if not re.match(r"\*-> ?", blk):
            continue
        key = first_key(blk)
        sec = index.get(key) if key else None
        if sec is None:
            unknown.append(blk.split("\n", 1)[0][:80])
            sec = "abstracts"
        buckets[sec].append(blk)
    total = save_parts(buckets, index)
    if unknown:
        print("  [!] %d entries NOT found in base (mixed into abstracts.txt):" % len(unknown))
        for u in unknown[:10]:
            print("      %s" % u)
    print("  rebuild total=%d entries" % total)
    return total


def mix(parts):
    """mix: reassemble the four parts into one combined dictionary source."""
    return "\n\n".join(p for p in parts if p.strip())


def rebuild(text, index):
    """stage1:rebuild() - delete stale then add fresh category files."""
    act_delete()
    return act_add(text, index)


def stage2():
    index = load_section_index(read(SRC))
    print("stage 2: channels against %s" % BASE)

    # channel A: open(file:"API/get") -> delete -> add -> rebuild
    src = http_get("API/get", {"dict": "dictionary"})
    print("[API/get] fetched %d chars" % len(src))
    n_get = rebuild(src, index)

    # channel B: open(file:"API/search") :as sc_file -> fun search (delete, mix add) -> rebuild
    parts = []
    for term in ("action", "mapping", "logical operator", "abstract"):
        hit = http_get("API/search", {"in": term})
        parts.append(hit)
        print("[API/search] in=%s -> %d chars" % (term, len(hit)))
    sc_file = mix(parts)
    print("  sc_file=mix(...) %d chars" % len(sc_file))
    n_srch = rebuild(sc_file, index)
    print("stage 2 done: get=%d search=%d entries" % (n_get, n_srch))


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "stage2":
        stage2()
    else:
        main()