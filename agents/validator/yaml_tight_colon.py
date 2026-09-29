# -*- coding: utf-8 -*-
"""the decisive test: does the line parse as a YAML plain scalar with a TIGHT colon

The last test failed 7 of 8, and the reason is visible in the output: 'mapping
values are not allowed here'. That is ': ' - colon and space. A YAML plain
scalar may not contain ': ', so every line of the spec is rejected.

But ': ' is the RENDERER's spacing, not the source. The source is tight -
'⌰:ʩ:§' - and the render adds air. So the test that matters is the tight form,
and if the tight form parses then the structure is free exactly as hoped, and
the ': ' is a cosmetic choice on our side that we can simply not make.

Two forms, same file, one parser.
"""
import io
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("  PyYAML нет, установить: pip install pyyaml")
    sys.exit(0)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "PY_IDE", "win.vglyph")
raw = io.open(SPEC, encoding="utf-8").read()
lines = [l for l in raw.replace("\r\n", "\n").split("\n") if l.strip()]

# our own operator punctuation, spaced out the way the renderer writes it
SPACED = [(r"\s+:\s+", ":"),        # ⌰ : ʩ :   ->   ⌰:ʩ:
          (r"\s*->\s*", "->"),        # spaced arrows back to tight
          (r"\s*\+\s*", "+")]         # spaced plus back to tight


def tighten(s):
    for pat, rep in SPACED:
        s = re.sub(pat, rep, s)
    return s


print("  файл %s   непустых строк %d" % (os.path.basename(SPEC), len(lines)))
print("")
print("  форма          разобралось   не разобралось   как dict")
print("  -------------  -----------   --------------   -------")
res = {}
for label, fn in (("как записано", lambda s: s.strip()),
                  ("плотная ':'", tighten)):
    ok = bad = dic = 0
    first = None
    for l in lines:
        body = fn(l)
        if not body:
            continue
        try:
            v = yaml.safe_load(body)
            ok += 1
            if isinstance(v, dict):
                dic += 1
                if first is None:
                    first = (v, body)
        except Exception as e:
            bad += 1
            if first is None and bad == 1:
                first = (e, body)
    res[label] = ok
    print("  %-13s  %11d   %14d   %7d" % (label, ok, bad, dic))
    if first is not None:
        v, b = first
        if isinstance(v, Exception):
            print("       первая ошибка: %s" % str(v).split("\n")[0][:70])
            print("       на строке:     %s" % b[:70])
        else:
            print("       пример значения: %s" % repr(list(v.items())[:3])[:70])

print("")
if res.get("плотная ':'", 0) == len([l for l in lines if l.strip()]):
    print("  ВЫВОД: плотная ':' проходит весь файл. Структура достается бесплатно,")
    print("         а ': ' - это наш выбор косметики, и его можно просто не делать.")
else:
    print("  ВЫВОД: плотная ':' НЕ проходит весь файл. Искать причину построчно.")
    for l in lines:
        b = tighten(l)
        try:
            v = yaml.safe_load(b.strip())
            if not isinstance(v, str):
                print("     не строка: %s" % repr(v)[:70])
        except Exception as e:
            print("     %s" % str(e).split("\n")[0][:70])
            print("        %s" % b.strip()[:70])
            break
