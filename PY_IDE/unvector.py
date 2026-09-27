# -*- coding: utf-8 -*-
"""five vectors on a word, renamed apart

A word bound twice has two meanings and the base allows one word one concept.
My first attempt relaxed the check because param=file in two functions looked
harmless - and that relaxation was the bug, not the finding: binding it twice
IS the vector.

    25  read_colors   param=file     the colors file
    101 fill_editor   param=file     the text put in the editor   -> content
    39  add_par       param=param    a nav parameter             -> par_nav
    41  set_text      param=param    a text parameter            -> par_text
    72  add_tab       param=param    a tab parameter             -> par_tab
    56  set_left      param=size     the left panel size         -> size_left
    58  set_right     param=size     the right panel size        -> size_right
    76  set_tab_name  param=name     the tab name                -> name_tab
    108 cmd           param=name     the command name            -> name_cmd
"""
import io
import re
import sys

P = "PY_IDE/window.vibe"
RENAMES = {
    "fill_editor": ("file", "content"),
    "add_par": ("param", "par_nav"),
    "set_text": ("param", "par_text"),
    "add_tab": ("param", "par_tab"),
    "set_left": ("size", "size_left"),
    "set_right": ("size", "size_right"),
    "set_tab_name": ("name", "name_tab"),
    "cmd": ("name", "name_cmd"),
}


def main():
    apply = "--apply" in sys.argv
    raw = io.open(P, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    t = raw.replace("\r\n", "\n")
    n = 0
    for fn, (old, new) in RENAMES.items():
        # the declaration line and the action line that follows it
        m = re.search(r'(&-> abstract:id="%s"->param=)%s(->action=")([^"]*)"' % (fn, old), t)
        if not m:
            print("  MISS %s param=%s" % (fn, old))
            continue
        act = m.group(3)
        newact = re.sub(r'(?<![A-Za-z_])%s(?![A-Za-z_])' % old, new, act)
        rep = m.group(1) + new + m.group(2) + newact + '"'
        t = t[:m.start()] + rep + t[m.end():]
        n += 1
        print("  %-13s param=%-6s -> %-9s" % (fn, old, new))
        if newact != act:
            print("       action: %s" % act[:66])
            print("            -> %s" % newact[:66])
    print("\nпереименовано: %d" % n)
    if not apply:
        print("(только план)")
        return 0
    io.open(P, "w", encoding="utf-8", newline="").write(
        t.replace("\n", "\r\n") if crlf else t)
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
