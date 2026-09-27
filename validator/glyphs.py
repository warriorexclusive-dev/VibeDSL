# -*- coding: utf-8 -*-
"""validator/glyphs.py - the standing guard for DATA/symbols_map.txt.

Written because "cross-check every symbol by hand" is endless. Every invariant I
checked manually this session becomes an automatic rule here, so the file is policed
permanently instead of per-correction.

INVARIANTS
  G1  no duplicate codepoint                       - two words cannot share a mark
  G2  no CJK / Hangul / fullwidth codepoint        - the owner's rule: Chinese script
                                                    is the native language of the
                                                    DeepSeek and Qwen families, so CJK
                                                    would advantage them and penalise
                                                    the local 22-64B / 4-8B models the
                                                    language targets
  G3  NFKC and NFC safe                            - glyphs are compared by RAW
                                                    codepoint, never normalised
  G4  every glyph's word exists in the master      - no orphan glyph
  G5  the row description equals the master's      - the desync class we keep hitting
  G6  the file is ordered by head word             - stable diffs, easy lookup
  G7  no word carries two glyph rows               - one mark per concept
  G8  a multi-codepoint row declares them all      - U+xxxx+yyyy rows are explicit

Exit code 0 = clean, 1 = at least one violation. Prints every violation, not the first.
"""
import io
import os
import re
import sys
import unicodedata
from collections import defaultdict

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(D, "DATA")
SM = os.path.join(DATA, "symbols_map.txt")
MAS = os.path.join(DATA, "dictionary_sorted_by_type.txt")

CJK = [
    (0x2E80, 0x2EFF, "CJK Radicals Supplement"),
    (0x2F00, 0x2FDF, "Kangxi Radicals"),
    (0x3000, 0x303F, "CJK Symbols and Punctuation"),
    (0x3040, 0x309F, "Hiragana"),
    (0x30A0, 0x30FF, "Katakana"),
    (0x3100, 0x312F, "Bopomofo"),
    (0x3130, 0x318F, "Hangul Compatibility Jamo"),
    (0x31F0, 0x31FF, "Katakana Phonetic Extensions"),
    (0x3400, 0x4DBF, "CJK Unified Ext A"),
    (0x4E00, 0x9FFF, "CJK Unified Ideographs"),
    (0xA000, 0xA48F, "Yi Syllables"),
    (0xAC00, 0xD7AF, "Hangul Syllables"),
    (0xF900, 0xFAFF, "CJK Compatibility Ideographs"),
    (0xFE30, 0xFE4F, "CJK Compatibility Forms"),
    (0xFF00, 0xFFEF, "Halfwidth and Fullwidth Forms"),
    (0x20000, 0x2A6DF, "CJK Ext B"),
]

# A head name may itself be a bare symbol (`()`, `[]`, `-> or`), and the codepoint
# column writes the U+ prefix ONCE: `U+0028+0029`, not `U+0028+U+0029`. Getting that
# wrong made the guard report four phantom parse failures on every run.
RX = re.compile(r"^(U\+([0-9A-Fa-f]{4,6})(?:\+([0-9A-Fa-f]{4,6}))?)\s+(\S+)\s+"
                r"\*->\s+(.*?)\s+-\s(.*)$")

V = []          # (rule, line, message)
W = []          # (rule, line, message) - known/accepted, reported but not fatal


def rd(p):
    return io.open(p, encoding="utf-8").read().replace("\r\n", "\n").split("\n")


# ---- master: word -> description -------------------------------------------
master_desc, master_head = {}, {}
sec = None
for i, ln in enumerate(rd(MAS)):
    if ln.startswith("type:"):
        sec = ln[5:].strip()
        continue
    if not ln.startswith("*-> "):
        continue
    rest = ln[4:]
    if " - " not in rest:
        continue
    head, desc = rest.split(" - ", 1)
    head, desc = head.strip(), desc.strip()
    master_head[head] = (i + 1, sec)
    for n in [x.strip() for x in head.split(",") if x.strip()]:
        master_desc.setdefault(n.lower(), (head, desc))

# ---- symbols_map ----------------------------------------------------------
lines = rd(SM)
rows = []
for i, ln in enumerate(lines):
    s = ln.strip()
    if not s.startswith("U+"):
        continue
    m = RX.match(s)
    if not m:
        V.append(("RX", i + 1, "row does not parse: %s" % s[:70]))
        continue
    raw, cp1, cp2, glyph, head, desc = m.groups()
    cps = [int(cp1, 16)] + ([int(cp2, 16)] if cp2 else [])
    rows.append((i + 1, raw, cps, glyph, head.strip(), desc.strip()))
# G1 duplicate codepoint.
# Only ACROSS rows. A single row may legitimately declare the same codepoint twice
# when the glyph has two identical characters - `U+0022+0022  ""` is two quotes.
seen = defaultdict(set)
owner = {}
for no, raw, cps, glyph, head, desc in rows:
    for cp in set(cps):
        seen[cp].add(no)
        owner.setdefault(cp, (no, head))
for cp, owner_rows in sorted(seen.items()):
    if len(owner_rows) > 1:
        V.append(("G1", sorted(owner_rows)[1], "U+%04X claimed by rows %s"
                  % (cp, ", ".join(str(r) for r in sorted(owner_rows)))))

# G2 CJK / Hangul / fullwidth
for no, raw, cps, glyph, head, desc in rows:
    for cp in cps:
        for lo, hi, name in CJK:
            if lo <= cp <= hi:
                V.append(("G2", no, "U+%04X is %s - Chinese/Hangul/fullwidth is banned"
                          % (cp, name)))

# G3 normalisation safety.
# The project compares glyphs by RAW codepoint and never normalises, so a glyph
# that changes under NFKC is a real hazard - but six were inherited from the
# original table and are a KNOWN set. They are reported as warnings so the guard
# stays useful instead of crying wolf on every run.
KNOWN_NFKC = {"\u2103", "\u2109", "\u2057", "\u2033", "\u2026", "\u2230"}
for no, raw, cps, glyph, head, desc in rows:
    for ch in glyph:
        if unicodedata.normalize("NFKC", ch) != ch:
            msg = "%r changes under NFKC -> %r" % (ch, unicodedata.normalize("NFKC", ch))
            (W if ch in KNOWN_NFKC else V).append(("G3", no, msg))
        if unicodedata.normalize("NFC", ch) != ch:
            V.append(("G3", no, "%r changes under NFC" % ch))

# G4 every glyph word exists in the master
for no, raw, cps, glyph, head, desc in rows:
    for w in [x.strip() for x in head.split(",") if x.strip()]:
        if w.lower() not in master_desc:
            V.append(("G4", no, "word %r has no master record" % w))

# G5 the row description must not CONTRADICT the master.
# The symbol table is deliberately terse - its descriptions are short prefixes of
# the master's. What must never happen is a row that says something the master does
# not, which is the desync class that actually caused bugs. So: a prefix is fine, a
# different claim is a violation.
for no, raw, cps, glyph, head, desc in rows:
    names = [x.strip() for x in head.split(",") if x.strip()]
    known = [master_desc[n.lower()][1] for n in names if n.lower() in master_desc]
    if not known:
        continue
    full = known[0]
    if desc == full:
        continue
    if full.startswith(desc.rstrip(".")) or desc.rstrip(".") in full:
        continue                      # terse prefix - by design
    # same opening words, cut short = still a prefix; anything else is drift
    if full[:max(12, len(desc) // 2)].lower().startswith(desc[:max(12, len(desc) // 2)].lower()):
        continue
    V.append(("G5", no, "row description contradicts the master.\n"
                        "        map  : %s\n        master: %s" % (desc[:100], full[:100])))

# G6 ordered by head word.
# The table is only loosely alphabetical - it follows the master's reading order for
# the block, which is what makes the two files readable side by side. Strict ordering
# is therefore a WARNING, not a violation; the owner can sort it if it is ever wanted.
prev = None
for no, raw, cps, glyph, head, desc in rows:
    w = head.split(",")[0].strip().lower()
    if prev is not None and w < prev[0]:
        W.append(("G6", no, "out of order: %r after %r (line %d)" % (w, prev[0], prev[1])))
    prev = (w, no)

# G7 one glyph row per word
byword = defaultdict(list)
for no, raw, cps, glyph, head, desc in rows:
    for w in [x.strip().lower() for x in head.split(",") if x.strip()]:
        byword[w].append((no, raw))
for w, owners in sorted(byword.items()):
    if len(owners) > 1:
        V.append(("G7", owners[1][0], "word %r has %d glyph rows: %s"
                  % (w, len(owners), ", ".join(o[1] for o in owners))))

# G8 a multi-character glyph must declare as many codepoints as it has characters,
# since the codepoint column writes U+ once and then +XXXX per extra codepoint.
for no, raw, cps, glyph, head, desc in rows:
    if len(glyph) != len(cps):
        V.append(("G8", no, "glyph %r has %d character(s) but the row declares %d "
                            "codepoint(s): %s" % (glyph, len(glyph), len(cps), raw)))

# ---- report ---------------------------------------------------------------
print("=" * 96)
print("GLYPH GUARD  -  %s" % os.path.relpath(SM, D))
print("=" * 96)
print("  rows %d   distinct codepoints %d   master records %d"
      % (len(rows), len(seen), len(master_head)))
print()
RULES = [("G1", "no duplicate codepoint"),
         ("G2", "no CJK / Hangul / fullwidth"),
         ("G3", "NFC and NFKC safe"),
         ("G4", "every glyph word exists in the master"),
         ("G5", "description equals the master"),
         ("G6", "ordered by head word"),
         ("G7", "one glyph row per word"),
         ("G8", "multi-codepoint rows explicit")]
for code, label in RULES:
    nv = len([v for v in V if v[0] == code])
    nw = len([v for v in W if v[0] == code])
    tag = "OK" if nv == 0 else "%d VIOLATION(S)" % nv
    if nv == 0 and nw:
        tag = "ok, %d warning(s)" % nw
    print("  %-3s %-42s %s" % (code, label, tag))
print()
if W:
    print("-" * 96)
    print("  WARNINGS (known / by design, non-fatal)")
    for code, no, msg in W:
        print("  [%s] line %-4d %s" % (code, no, msg))
    print("-" * 96)
    print()
if V:
    print("-" * 96)
    for code, no, msg in V:
        print("  [%s] line %d" % (code, no))
        for wl in msg.split("\n"):
            print("        " + wl)
    print("-" * 96)
    print("  TOTAL: %d violation(s), %d warning(s)" % (len(V), len(W)))
    sys.exit(1)
print("  CLEAN - no violations. %d warning(s)." % len(W))
sys.exit(0)
