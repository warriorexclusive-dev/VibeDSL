# -*- coding: utf-8 -*-
"""does the agent file obey the rule it states?

The file tells the agent to write glyphs only, and to use no token RAG does not
return. So checking it is the same job as GLYPH_KNOWN: every glyph in the file
must be in the base. A rule that the rule's author breaks is worse than no rule.
"""
import importlib.util as u
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT = os.path.join(os.path.expanduser("~"), ".config", "opencode", "agent",
                     sys.argv[1] if len(sys.argv) > 1 else "dsl-coder.md")

sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
_, _, w2g, _ = cc.load_alias_to_glyph()
base = set(g for g in w2g.values() if g)
# U+23BE..U+23CD is the id alphabet: documented, contiguous, and DELIBERATELY
# unspelled, so it has no word and never will. An id is an address and must
# not render as text, so a check that reads words cannot see it - and must not
# report it as unknown.

lines = io.open(AGENT, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
in_fm = lines[0].strip() == "---"
bad = {}
for n, l in enumerate(lines, 1):
    if n == 1 and in_fm:
        continue
    if in_fm and l.strip() == "---":
        in_fm = False
        continue
    for ch in set(l):
        if ord(ch) > 0x2000 and not ch.isalpha() and ch not in base \
                and not (0x23BE <= ord(ch) <= 0x23CD):
            bad.setdefault(ch, []).append(n)
print("  файл     : %s" % AGENT)
print("  строк    : %d   глифов в базе: %d" % (len(lines), len(base)))
if bad:
    for ch, ns in sorted(bad.items()):
        print("  ПРОБЛЕМА U+%04X %r  строки: %s" % (ord(ch), ch, ",".join(map(str, ns[:6]))))
else:
    print("  ВЕРДИКТ: все глифы файла есть в базе")
