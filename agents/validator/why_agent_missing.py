# -*- coding: utf-8 -*-
"""why dsl-coder is not picked up when opencode runs on ollama

Ordered by how likely each cause is, cheapest first.

1. the frontmatter does not parse. The description is one long unquoted YAML
   plain scalar, and a plain scalar dies on the first ": " or the first "#".
   If yaml is unavailable here, the fallback parses the same rules by hand.
2. the agent is mode: subagent, so it is NOT listed as a selectable agent - it
   is reachable only through the task tool. That is by design and would look
   exactly like "not picked up".
3. the prompt is long and the model is local. num_ctx is set in opencode.jsonc;
   if the agent prompt plus the system prompt exceeds it, the tail - which is
   where the RAG bootstrap lives - is the first thing to go.
"""
import io
import os
import re

AG = os.path.join(os.path.expanduser("~"), ".config", "opencode", "agent", "dsl-coder.md")
raw = io.open(AG, encoding="utf-8-sig").read()
lines = raw.replace("\r\n", "\n").split("\n")

print("  файл: %s" % AG)
print("  байт: %d   строк: %d" % (len(raw), len(lines)))
print("  первая строка: %r" % lines[0])
close = next((n for n, l in enumerate(lines) if n > 0 and l.strip() == "---"), None)
print("  закрывающий ---: строка %s" % (close + 1 if close else "НЕ НАЙДЕН"))
if close is None:
    raise SystemExit(0)

fm = lines[1:close]
print("")
print("  поля фронтматтера:")
bad = []
for l in fm:
    if not l.strip():
        continue
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s?(.*)$", l)
    if not m:
        bad.append(("НЕПОЛЕВАЯ СТРОКА", l))
        continue
    k, v = m.group(1), m.group(2)
    flag = ""
    if k == "description":
        if ": " in v:
            flag = "  <-- СОДЕРЖИТ ': ' - YAML plain scalar сломается"
            bad.append((": в description", v[:60]))
        if "#" in v:
            flag = "  <-- СОДЕРЖИТ '#' - это комментарий в YAML"
            bad.append(("# в description", v[:60]))
    print("     %-12s %s%s" % (k, (v[:58] + "...") if len(v) > 58 else v, flag))

print("")
if bad:
    print("  ПРОБЛЕМЫ (%d):" % len(bad))
    for w, s in bad:
        print("     %s: %s" % (w, s))
else:
    print("  синтаксис фронтматтера: подозрительных мест нет")

# yaml, if present
try:
    import yaml
    d = yaml.safe_load("\n".join(["---"] + fm + ["---"]))
    print("  yaml.safe_load: ключи %s" % sorted(d.keys()))
except ImportError:
    print("  yaml: нет в системе, разбирано вручную по правилам YAML")
except Exception as e:
    print("  yaml.safeLoad УПАЛ: %s" % e)

m = re.search(r"(?m)^mode:\s*(\S+)", raw)
print("  mode: %s   <- subagent не появляется в списке, только через task"
      % (m.group(1) if m else "?"))
cfg = os.path.join(os.path.expanduser("~"), ".config", "opencode", "opencode.jsonc")
c = io.open(cfg, encoding="utf-8-sig").read()
n = re.search(r'"num_ctx"\s*:\s*(\d+)', c)
print("  num_ctx в opencode.jsonc: %s   промпт агента: %d символов"
      % (n.group(1) if n else "не задан", len(raw)))
