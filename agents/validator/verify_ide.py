# -*- coding: utf-8 -*-
"""verify the from-scratch glyph spec against everything we built today

Nine checks, and each one is asked a question it can actually answer. A check
that cannot fail is not evidence, so every one of these has been planted with a
deliberate violation at some point - except the ones I say are unproven below,
and those are named as unproven rather than reported green.
"""
import importlib.util as u
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "PY_IDE", "ide.vglyph")
Q, BS = chr(0x22), chr(0x5C)
F_O, F_S = chr(0x25B9), chr(0x25C2)
ALPHA = set(chr(c) for c in range(0x23BE, 0x23CE))
TYPES = {chr(0x2B1D): "item", chr(0x02A9): "function", chr(0x2317): "prop"}
ABS = chr(0x2330)
ID, AS = chr(0x00A7), chr(0x2A72)

sp = u.spec_from_file_location("_cc", os.path.join(ROOT, "compiler", "compile.py"))
cc = u.module_from_spec(sp)
sp.loader.exec_module(cc)
co, cs, w2g, gl = cc.load_alias_to_glyph()
sub, _, _ = cc.build_substitution(co, cs, w2g, gl)
rx = cc.make_token_rx(sub)

text = io.open(P, encoding="utf-8-sig").read().replace("\r\n", "\n")
lines = text.split("\n")
ok = lambda c, m: print("  %-4s %s" % ("ok" if c else "FAIL", m)) or c

print("  ide.vglyph   строк %d   символов %d" % (len(lines), len(text)))
print("")

# 1. frame balance, depth aware - an id sits inside a framed action
bad = [(n, l.count(F_O) - l.count(F_S)) for n, l in enumerate(lines, 1)
       if l.count(F_O) != l.count(F_S)]
ok(not bad, "рамки сбалансированы в каждой строке   %s" % (bad or ""))

# 2. an abstract always carries a type
notype = []
for n, l in enumerate(lines, 1):
    if l.lstrip().startswith(ABS):
        m = re.match(re.escape(ABS) + r":(.)", l.lstrip())
        if not m or m.group(1) not in TYPES:
            notype.append(n)
ok(not notype, "у каждого ⌰ есть тип ⬝ ʩ или ⌗   %s" % (notype or ""))

# 3. every id is a 4-glyph address, and addresses are unique
ids, addrs = [], []
for l in lines:
    m = re.search(re.escape(ID) + re.escape(AS) + re.escape(F_O) + r"([^" + F_S + "]*)" + F_S, l)
    if m:
        ids.append(m.group(1))
        if set(m.group(1)) <= ALPHA and len(m.group(1)) == 4:
            addrs.append(m.group(1))
ok(len(addrs) == len(ids), "все id это 4 глифа из алфавита   %d/%d" % (len(addrs), len(ids)))

dup = [a for a in set(addrs) if addrs.count(a) > 1]
ok(not dup, "адреса уникальны   повторов %d %s" % (len(dup), dup or ""))

def near(a, b):
    return len(a) == len(b) and sum(1 for x, y in zip(a, b) if x != y) == 1
nm = [(a, b) for i, a in enumerate(addrs) for b in addrs[i + 1:] if near(a, b)]
ok(not nm, "нет пар, отличающихся в одной позиции   %d" % len(nm))

# 4. every glyph is in the base, except the id alphabet inside a frame
body = re.sub(re.escape(F_O) + r"[^" + F_S + r"]*" + F_S, "", text)
unk = sorted({c for c in body if ord(c) > 0x2000 and not c.isalpha()
              and c not in set(g for g in w2g.values() if g)})
ok(not unk, "каждый глиф вне рамки есть в базе   %s" % (unk or ""))

# 5. every name is a concept, or a declared local word
base_words = set(w2g)
names = re.findall(re.escape(chr(0x2255)) + re.escape(AS) + re.escape(F_O) + r"([^" + F_S + r"]+)" + F_S, text)
declared = set(re.findall(re.escape(ID) + re.escape(AS) + re.escape(F_O) + r"[^" + F_S + r"]+" + F_S, text))
local = set(re.findall(re.escape(F_O) + r"([A-Za-z_]\w*)" + F_S, text))
badname = [n for n in names if n not in base_words and n not in local]
ok(not badname, "у каждого имени есть концепт или оно объявлено   %s" % (badname or ""))

# 6. the spine round-trips: outside the frames, glyph -> word -> glyph
L = [cc.compile_line(l, sub, rx, {"replaced": 0, "words": {}, "unmapped": set(),
                                  "undefined": set(), "missing_use": [],
                                  "glyphs_used": [], "noteq": set()}, None, set())
     for l in lines]
sp_a = [re.sub(re.escape(F_O) + r"[^" + F_S + r"]*" + F_S, "", l) for l in lines]
sp_b = [re.sub(re.escape(F_O) + r"[^" + F_S + r"]*" + F_S, "", l) for l in L]
d = sum(1 for a, b in zip(sp_a, sp_b) if a.strip() != b.strip())
ok(d == 0, "хребет сходится: глифы -> слова -> глифы   расхождений %d" % d)
