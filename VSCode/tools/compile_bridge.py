# -*- coding: utf-8 -*-
"""the project compiler behind a command line, for the panel

A JavaScript extension cannot import a Python module, and the panel has to
compile with the project's own compiler rather than with a second copy of it.
So this is the thin line between them: it reads a .vibe, it calls
compiler_v2.compile_record, and it prints JSON and nothing else.

It writes nothing. A compile that failed must not leave a half result, so there
is no write here at all: the table is only ever read, and only through the
loaders the project already has.

    py -3 compile_bridge.py <file.vibe>          -> one line of JSON
    py -3 compile_bridge.py --table              -> what is in the table now
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VS = os.path.dirname(HERE)
REPO = os.path.dirname(VS)
# the project the compiler lives in, named and not counted
ROOT = os.path.join(REPO, "5xVector")
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)

# Windows gives Python the console's code page, which is cp1251 on a Russian
# machine and cp866 on another, and a glyph run is not valid in either. The
# output is JSON in UTF-8 and the panel reads it as UTF-8, so the encoding is
# set here rather than left to the environment: a bridge that is correct only
# when a variable happens to be set is a bridge that one day is not.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def out(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    return 0


def addressed(text, table, live):
    """the words that are not English, and where they are

    Two levels, and the second one is asked for only when a person asks:

        local   letters and the project's own table. No network, no wait, and
                it is the same rule the compiler writes with, because it is the
                same table.
        live    datamuse, for a word that is not in the table at all. A word
                outside the table is the only case where the outside is worth
                asking, and asking on every keystroke is a request per letter.

    A word in the table is not asked anything. The table is the project's own
    decision that it is a word, and a second opinion from the internet about a
    word the project already accepted would be a slower way to doubt it.
    """
    import re
    import language_check as L
    cache = L.load_cache()
    out = []
    seen = set()
    for n, raw in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        # only the parts that are words: the marks, the glyphs and the spacing
        for part in re.findall(r"[^\W\d_]+", raw, re.UNICODE):
            w = part.lower()
            if w in seen:
                continue
            seen.add(w)
            if not L.LATIN.match(part):
                out.append({"line": n, "word": part, "why": "не латиница"})
                continue
            if w in table:
                continue
            if not live:
                out.append({"line": n, "word": part,
                            "why": "нет в таблице"})
                continue
            hit = L.known(w, cache, live=True)
            if hit is False:
                out.append({"line": n, "word": part, "why": "datamuse не знает"})
            elif hit is None:
                out.append({"line": n, "word": part,
                            "why": "datamuse не ответил, а молчание это не да"})
    if live:
        L.save_cache(cache)
    return out


def compile_file(path, live=False):
    import compiler_v2 as K
    entries = K.load()
    offs = K.offsets(entries)
    table = {e: o for e, o in zip(entries, offs)}
    try:
        # utf-8-sig and not utf-8: a file saved with a BOM opens as a line that
        # starts with an invisible mark, and every record in it is then refused
        # for a reason nobody can see. The editor writes BOMs, so the reader
        # takes them off rather than blaming the person for a character that
        # was not in what they wrote.
        text = io.open(path, encoding="utf-8-sig").read()
    except (IOError, OSError) as e:
        return out({"ok": False, "error": "не прочитан: %s" % e, "lines": []})

    # The project's own walk, not a second one. This used to loop over the
    # lines here and call compile_record on each, and that made the bridge the
    # second compiler: it did not know about the .data block, so every file
    # that carried one failed with one error per line of a block that is not
    # compiled at all. The block is the compiler's business and the compiler is
    # one thing.
    before, free, code = K.split_blocks(text)
    if not code and free:
        return out({"ok": True, "lines": [], "bad": [],
                    "unknown_words": [],
                    "free_lines": len([l for l in free if l.strip()]),
                    "missing": addressed(text, table, live)})

    missing = []
    lines, err = K.compile_text(text, table, missing)
    if err is not None:
        # The number a person reads is the number in the file, not the number
        # inside the .code block. They are different once a file has a .data
        # block, and a fault reported at line 2 of a file whose line 2 is a
        # theme sends the reader to the wrong place with no way to tell.
        raw_lines = text.replace("\r\n", "\n").split("\n")
        offset = 0
        for i, l in enumerate(raw_lines):
            if l.strip() == ".code":
                offset = i + 1          # count the tag itself
                break
        for n, raw in enumerate(code, 1):
            s = raw.strip()
            while s.startswith("-"):
                s = s[1:].strip()
            if not s:
                continue
            if K.compile_record(s, table)[1] is not None:
                return out({"ok": False, "lines": [], "bad": [{"line": n + offset,
                        "error": err}], "unknown_words": [],
                        "missing": addressed(text, table, live)})
        return out({"ok": False, "lines": [], "bad": [{"line": 0,
                "error": err}], "unknown_words": [],
                "missing": addressed(text, table, live)})
    return out({"ok": True, "lines": lines or [], "bad": [],
                "unknown_words": sorted(set(missing)),
                "free_lines": len([l for l in free if l.strip()]),
                "missing": addressed(text, table, live)})


def table_now():
    import compiler_v2 as K
    entries = K.load()
    return out({"ok": True, "entries": len(entries), "width": K.width(),
                "null_at": K.NULL, "free": K.NULL - len(entries),
                "bytes": os.path.getsize(K.EMB)})


def main():
    if len(sys.argv) < 2:
        return out({"ok": False, "error": "нет файла", "lines": []})
    if sys.argv[1] == "--table":
        return table_now()
    # The outside is asked unless --offline says otherwise, which is the same
    # rule the compiler follows and one switch for both. An earlier version had
    # it the other way round, with a flag that turned the network on, and then
    # the check silently did nothing unless somebody knew to ask for it.
    import language_check as L
    live = "--offline" not in sys.argv[2:] and L.live()
    args = [a for a in sys.argv[1:] if a != "--offline"]
    return compile_file(args[0], live=live)


if __name__ == "__main__":
    sys.exit(main())
