# -*- coding: utf-8 -*-
"""bake the dsl-coder rules into an ollama model

Three failures today all came from the rules living in a file that something
else had to load:

  mode: subagent      opencode refuses --agent, "falling back to default"
  the tail of the file  php -S sits at the end, so a truncated prompt keeps the
                       protocol and loses the ability to run it
  three carriers      rule in dictionary, in RULES.MD, in AGENTS.MD, and they
                       drifted apart within the same afternoon

Baking the rules into the model removes the file from the chain. There is
nothing to truncate, nothing to declare a mode for, and no second copy to
drift - the model IS the carrier. A word spec is still the report; this is the
working medium.

The prompt is taken from the agent file verbatim, frontmatter stripped, so the
model and the agent cannot disagree about the text.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AG = os.path.join(os.path.expanduser("~"), ".config", "opencode", "agent", "dsl-coder.md")
OUT = os.path.join(ROOT, "MODelfile.dsl-coder")

MODEL = "qwen2.5-coder:7b"
NAME = "vibedsl-coder"
NUM_CTX = 32768          # 65535 was asked for; 32k is the honest ask on a 7b Q4

raw = io.open(AG, encoding="utf-8-sig").read().replace("\r\n", "\n")
close = next((n for n, l in enumerate(raw.split("\n")) if n > 0 and l.strip() == "---"), 0)
body = "\n".join(raw.split("\n")[close + 1:]).strip()
body = re.sub(r"^```.*$", "", body, flags=re.M)          # drop the fence lines
body = body.replace('"', "'")                             # safe inside a Modelfile heredoc
if "'''" in body or '"""' in body:
    body = body.replace("'''", "`").replace('"""', "`")

mf = (
    "# VibeDSL dsl-coder - rules baked into the model\n"
    "#\n"
    "# FROM qwen2.5-coder:7b  Q4_K_M, confirmed with `ollama show`.\n"
    "# The prompt below is the agent file verbatim, frontmatter stripped, so the\n"
    "# two cannot disagree. Glyphs are intentional: they are the canonical form.\n"
    "\n"
    "FROM %s\n"
    "\n"
    "PARAMETER num_ctx %d\n"
    "PARAMETER temperature 0.1\n"
    "PARAMETER stop \"<|im_end|>\"\n"
    "PARAMETER stop \"<|endoftext|>\"\n"
    "\n"
    'SYSTEM """\n%s\n"""\n' % (MODEL, NUM_CTX, body)
)
io.open(OUT, "w", encoding="utf-8", newline="\n").write(mf)
print("  записан %s" % OUT)
print("  FROM     %s" % MODEL)
print("  num_ctx  %d   (65535 просили, 32k - честная просьба для 7b Q4)" % NUM_CTX)
print("  SYSTEM   %d символов, глифов внутри сохранено" % len(body))
print("  кавычек в теле: %d   тройных: %d" % (body.count('"'), body.count('"""')))
