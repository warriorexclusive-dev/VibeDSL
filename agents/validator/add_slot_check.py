# -*- coding: utf-8 -*-
"""ABSTRACT_SLOT and ABSTRACT_TYPE into glyph_checker.py

The abstract head is one of two legal shapes and nothing else:

    §⩲"x"      a literal - a name I chose
    §⩲❂:≕      a slot   - the name is derived from the unique name

Mixing them is the error I made twice: a literal named after a role word, in a
place that is supposed to be a slot. A human sees the shape instantly. I see a
sequence of tokens and I put a value where a slot goes, because I do not
distinguish a slot from a value.

So it is a check, not a warning. "Be careful" demonstrably does not work - five
inventions this session. GLYPH_HOLE caught those in a second, because a check
does not require attention.

ABSTRACT_TYPE is the second half: ⌰ with no type used to be read as ⬝ silently,
and that is how a third of a spec went unreadable while the gate stayed green.
"""
import io
import re

P = "validator/glyph_checker.py"

CHECKS = '''    # ABSTRACT_TYPE - the type is mandatory, there is no default
    e = []
    for p in REFS:
        s = read(p)
        if not s:
            continue
        for m in re.finditer(r"\\u2310(?![:\\u2317\\u2B1D])([^\\n]*)", s):
            tail = m.group(1)[:24]
            if not re.match(r"^:(?:\\u2B1D|\\u02A9|\\u2317)", tail):
                ln = s[:m.start()].count("\\n") + 1
                e.append("%s:%d abstract \\u2310 with no type, read as \\u2B1D" % (p, ln))
    check("ABSTRACT_TYPE", e, "\\u2310 always carries \\u2B1D, \\u02A9 or \\u2317")

    # ABSTRACT_SLOT - after \\u00A7\\u2A72 only a literal or the slot pattern
    e = []
    ROLE = ("any", "unique", "alias", "condition", "prop", "item", "function",
            "name", "id", "abstract")
    for p in REFS:
        s = read(p)
        if not s:
            continue
        for m in re.finditer(r"\\u00A7\\u2A72([^\\n]{0,24})", s):
            what = m.group(1)
            ln = s[:m.start()].count("\\n") + 1
            quoted = re.match(r'^"([A-Za-z_]\\w*)"', what)
            if re.match(r"^\\u2742:\\u2255", what):
                continue                      # the slot, legal
            if quoted:
                if quoted.group(1).lower() in ROLE:
                    e.append("%s:%d id is a LITERAL named after a role word %r -"
                             " a role is a glyph, a name is a string" %
                             (p, ln, quoted.group(1)))
                continue
            e.append("%s:%d after \\u00A7\\u2A72 neither a string nor \\u2742:\\u2255"
                     " -> %r" % (p, ln, what[:16]))
    check("ABSTRACT_SLOT", e, "id is a literal or the slot, never a role word")

'''

MARK = "    # GLYPH_COVER"

s = io.open(P, encoding="utf-8-sig").read()
if "ABSTRACT_SLOT" in s:
    print("  уже есть")
else:
    s = s.replace(MARK, CHECKS + MARK)
    io.open(P, "w", encoding="utf-8", newline="").write(s)
    print("  ABSTRACT_SLOT и ABSTRACT_TYPE добавлены")
