# -*- coding: utf-8 -*-
"""the code's docstrings become the spec's action, one to one

The spec was converted out of the old prose and the code was not, so 26
docstrings in vibide.py still teach `crt frm + set module`, which is the form
the language stopped using. That is the same failure the prototypes had: text a
model reads and learns the wrong shape from.

The authority is window.vibe. Each function's docstring becomes the action= of
its abstract, verbatim, so the code documents itself in the language it
implements instead of in a dialect of it.
"""
import io
import re
import sys

SPEC = "PY_IDE/window.vibe"
CODE = "PY_IDE/vibide.py"


def spec_actions(path):
    t = io.open(path, encoding="utf-8-sig").read().replace("\r\n", "\n")
    out = {}
    for m in re.finditer(r'&->\s*abstract(?::(\w+))?:id="([^"]+)"[^\n]*?action="([^"]*)"', t):
        out[m.group(2)] = m.group(3)
    for m in re.finditer(r'&->\s*abstract(?::(\w+))?:"([^"]+)"->action="([^"]*)"', t):
        out.setdefault(m.group(2), m.group(3))
    return out


def main():
    apply = "--apply" in sys.argv
    acts = spec_actions(SPEC)
    print("  action= в спеке: %d" % len(acts))

    raw = io.open(CODE, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")

    done = 0
    missing = []
    for i, l in enumerate(lines):
        m = re.match(r"^def (\w+)\(", l)
        if not m:
            continue
        fn = m.group(1)
        # the docstring line right after the def, possibly after a blank
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j >= len(lines):
            continue
        d = re.match(r'^(\s*)"""(.*)"""$', lines[j])
        if not d:
            continue
        indent, old = d.group(1), d.group(2)
        if old in acts:
            continue
        if fn in acts:
            new = acts[fn]
            print("  %-14s %s" % (fn, new[:74]))
            lines[j] = '%s"""%s"""' % (indent, new)
            done += 1
        elif old.strip():
            missing.append((fn, old[:52]))

    print("\n  заменено: %d" % done)
    if missing:
        print("  остались без action в спеке: %d" % len(missing))
        for fn, o in missing:
            print("     %-14s %s" % (fn, o))
    if not apply:
        print("(только план)")
        return 0
    out = "\n".join(lines)
    io.open(CODE, "w", encoding="utf-8", newline="").write(
        out.replace("\n", "\r\n") if crlf else out)
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
