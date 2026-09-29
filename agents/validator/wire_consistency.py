# -*- coding: utf-8 -*-
"""wire the consistency check into compile.py's main, right where the pool loads

Placed next to load_pool because that is where the compiler commits to reading
these files. A check that runs on a schedule is a check that eventually does not
run; this one runs every compile.

Contradictions block. Being behind does not. mapping.dict carries no entries of
its own and that is a fact about the repository, not a fault - a check that
demanded equality had me ready to run --fix and "repair" a file that was never
broken.
"""
import io
import os

P = "compiler/compile.py"
s = io.open(P, encoding="utf-8-sig").read()

NEEDLE = "    pool, _ = load_pool()"
if "consistency" in s:
    print("  уже подключено")
    raise SystemExit(0)

BLOCK = '''    # Consistency of the compiler's own inputs, before a single line is read.
    # A contradiction between the map and the dictionary is a token this
    # compiler can resolve and the language cannot name, so it stops the build.
    # A split file being behind is stated and left alone - see consistency.py.
    import consistency as _cons
    _cerr, _cnote = _cons.check(DATA, SYM, SPLIT_FILES, FALLBACK_FILES)
    if "--quiet" not in sys.argv:
        print(_cons.report(_cerr, _cnote))
    if _cerr:
        return 2

    pool = load_pool()'''

if NEEDLE not in s:
    print("  НЕ НАЙДЕНО место для вставки: %r" % NEEDLE)
    raise SystemExit(1)

s = s.replace(NEEDLE, BLOCK, 1)
# make the module importable from the compiler directory
if "sys.path.insert(0, HERE)" not in s:
    s = s.replace("HERE = os.path.dirname(os.path.abspath(__file__))",
                  "HERE = os.path.dirname(os.path.abspath(__file__))\n"
                  "if HERE not in sys.path:\n    sys.path.insert(0, HERE)", 1)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("  блок CONSISTENCY вставлен в compile.py")
