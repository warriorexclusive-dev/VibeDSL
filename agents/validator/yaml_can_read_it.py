# -*- coding: utf-8 -*-
"""can the specs survive a real YAML parser, unquoted, with no changes

The plan is to stop parsing text and parse structure, and YAML is structure
with indentation that already exists. Before adopting it, the text has to be
tested against an actual parser rather than against my reading of the spec -
because I have been wrong about the base four times today.

Plain style only. That is the whole point: the glyph line must stay one dense
line with nothing wrapped in quotes, and if it does not survive that then YAML
is the wrong choice and it should be rejected now rather than after 40 files are
migrated.
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "PY_IDE", "win.vglyph")

try:
    import yaml
except ImportError:
    print("  PyYAML нет, установить: pip install pyyaml")
    sys.exit(0)

raw = io.open(SPEC, encoding="utf-8").read()
lines = [l for l in raw.replace("\r\n", "\n").split("\n") if l.strip()]
print("  файл %s   непустых строк %d" % (os.path.basename(SPEC), len(lines)))

ok = bad = 0
kinds = {}
samples = []
for n, l in enumerate(lines, 1):
    ind = len(l) - len(l.lstrip(" "))
    body = l.strip()
    # the real thing: the line as it stands, only indented, unquoted, unmodified
    text = ("  " * (ind // 2)) + body
    try:
        v = yaml.safe_load(text)
        ok += 1
        k = type(v).__name__
        kinds[k] = kinds.get(k, 0) + 1
        if len(samples) < 6 and isinstance(v, str) and len(v) > 40:
            samples.append((n, v))
    except Exception as e:
        bad += 1
        if bad <= 8:
            print("  строка %-4d %s" % (n, str(e).split("\n")[0][:96]))
            print("           %s" % body[:88])

print("")
print("  разобралось как есть: %d    не разобралось: %d" % (ok, bad))
print("  типы: %s" % ", ".join("%s=%d" % (k, v) for k, v in sorted(kinds.items())))
print("")
print("  строков, которые НЕ должны были разбираться: 0 ожидалось")
print("")
print("  и это главное - сколько строк прошло как dict, а не как строка:")
for k, v in sorted(kinds.items()):
    flag = "" if k == "str" else "  <- ВОТ ЭТО: текст оказался СТРУКТУРОЙ"
    print("     %-6s %3d%s" % (k, v, flag))
if samples:
    print("")
    print("  пример того, что YAML считает значением строки:")
    for n, v in samples[:3]:
        print("     строка %-4d %s" % (n, v[:70]))
