# -*- coding: utf-8 -*-
"""id = <filename>.<kind>, for prototypes and blueprints

The readable id was a rule with no shape. This gives it one:

    prototype   id=<filename>.proto
    blueprint   id=<filename>.blueprint

which is checkable, and the check is worth having because the alternative is an
id that only means something to whoever typed it. The id IS the file, so the
artifact is findable by grep, the kind is visible in the id itself, and
use(win.proto) says what it pulls without a second lookup.

Never glyphs here - that part already stands. The id is the interface to
something, and glyphs are not an interface.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print("  что сейчас в DATA/protos.txt:")
p = os.path.join(ROOT, "DATA", "protos.txt")
if os.path.exists(p):
    for n, l in enumerate(io.open(p, encoding="utf-8-sig").read()
                           .replace("\r\n", "\n").split("\n"), 1):
        m = re.search(r'id\s*=\s*"?([\w.\-]+)"?', l)
        if m:
            ok = m.group(1).endswith(".proto")
            print("     %-22s %s" % (m.group(1), "ok" if ok else "НЕ .proto"))
else:
    print("     файла нет")

print("")
print("  blueprints.txt:")
b = os.path.join(ROOT, "DATA", "blueprints.txt")
if os.path.exists(b):
    ids = re.findall(r'id\s*=\s*"?([\w.\-]+)"?',
                     io.open(b, encoding="utf-8-sig").read())
    print("     id: %s" % (ids or "пусто, как и задумано"))
