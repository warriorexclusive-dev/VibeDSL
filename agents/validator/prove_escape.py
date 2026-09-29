# -*- coding: utf-8 -*-
"""prove the escape fix, on the exact shape that broke

A backslash before a quote must keep the string open. Before the fix the \"
closed the string, the backslash fell outside and became a glyph, and the escape
ended up AFTER the quote it was escaping - which is why exactly the lines with
the invented names were the ones with unpaired quotes.
"""
import importlib.util as u
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sp = u.spec_from_file_location("_c", os.path.join(ROOT, "compiler", "compile.py"))
c = u.module_from_spec(sp)
sp.loader.exec_module(c)

Q = chr(0x22)
BS = chr(0x5C)
LINE = ("&-> abstract:item:id=" + Q + "bar" + Q + "->action=" + Q
        + "bar:incld:set(" + BS + Q + "controller_bar" + BS + Q + ")"
        + " + add(bar:btn)" + Q)

segs = c.segments(LINE)
keep = [t for k, t in segs if k == "keep"]
print("  вход:")
print("     %s" % LINE)
print("")
print("  keep-сегменты (%d):" % len(keep))
for t in keep:
    print("     %r" % t)
print("")
# the string must survive whole: one segment holding the inner escaped quotes
ok = any(t.count(Q) == 4 for t in keep)
print("  строка с двумя экранированными кавычками уцелела: %s" % ok)
print("  всего кавычек в keep: %d (ожидается 6: 2 внешние + 4 внутренние)"
      % sum(t.count(Q) for t in keep))
print("  обратных слэшей в keep: %d (ожидается 2, и ни один не должен стать глифом)"
      % sum(t.count(BS) for t in keep))
