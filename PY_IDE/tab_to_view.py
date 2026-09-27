# -*- coding: utf-8 -*-
"""tab is a view onto a tab, so it is an item, and it is called tab_view.

I got the category wrong first. I saw `tab` collide with the table concept and
went looking for a name that would fit, instead of asking what the thing is.
It is not a property - the spec creates it, adds to it, closes it and shows it.
It is an element that happens to carry pins. So:

    prop  ->  item,  because create/add/close/show act on it
    tab   ->  tab_view

The rename is not cosmetics. `tab_view` is nowhere near `table`, so the
collision is gone because the thing is named for what it is, not because a
shorter colliding name was chosen.

Prose and quoted payloads are left alone - they are messages to a person, not
identifiers:

    action="add tab + set name + set text + show"     <- stays
    part 2: "tab"                                     <- stays
    return("tab dobavlen")                            <- stays

Only code position is rewritten, plus the two quoted identifiers that really
are identifiers: the declaration's id, and the part's frm:name.
"""
import importlib.util
import io
import os
import re
import sys

PATH = "PY_IDE/window.vibe"
OLD, NEW = "tab", "tab_view"

# quoted identifiers that must move, because they ARE the identifier
EXPLICIT = [
    ('&-> abstract:prop:id="tab"->frm:"tab"',
     '&-> abstract:item:id="tab_view"->frm:type="tab_view"'),
    ('->frm:name="tab":', '->frm:name="tab_view":'),
]

ONLY = ("create(%s)", "add(%s)", "close(%s)", "show(%s)",
        "add(%s:inp type=\"text\")", "%s:num:set(par)", "%s:name:set(par)",
        "%s:text:set(par)", "%s:theme:set()", "check(%s:theme)")

RX_TOKEN = re.compile(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % OLD)


def paren_pairs():
    out = []
    for t in ONLY:
        out.append((t % OLD, t % NEW))
    return out


def segments():
    spec = importlib.util.spec_from_file_location("_cc", os.path.join("compiler", "compile.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.segments


def main():
    seg = segments()
    raw = io.open(PATH, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    apply = "--apply" in sys.argv
    n = 0

    def repl(line):
        nonlocal n
        if not line.strip():
            return line
        out = []
        for kind, chunk in seg(line):
            if kind == "code" and RX_TOKEN.search(chunk):
                n += len(RX_TOKEN.findall(chunk))
                if apply:
                    chunk = RX_TOKEN.sub(NEW, chunk)
            out.append(chunk)
        return "".join(out)

    lines = [repl(l) for l in text.split("\n")]

    for old, new in EXPLICIT + paren_pairs():
        hit = sum(l.count(old) for l in lines)
        if hit:
            print("  %dx %-40s -> %s" % (hit, old, new))
            n += hit
            if apply:
                lines = [l.replace(old, new) for l in lines]
        else:
            print("  MISS %s" % old)

    print("\nзаменено: %d" % n)
    if not apply:
        print("(только план; для записи добавьте --apply)")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="").write(
        "\n".join(lines).replace("\n", "\r\n") if crlf else "\n".join(lines))
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
