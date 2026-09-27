#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compile.py - VibeDSL text -> glyph compiler.

Emits ONE file with three blocks, so a weak model can tell at a glance what to
execute and what not to:

    -----RULES-----   the glyph dictionary + what each block is for + the task
    -----DATA-----    abstracts / blueprints / prototypes pulled in by `use`
    -----CODE-----    the specification. Execution starts HERE. The tree is
                      preserved exactly, YAML-style: indentation is never
                      touched, only whole words are swapped for glyphs.

Rules implemented
  1. a dictionary word is replaced by the glyph of its concept
  2. text inside (), [] and {} is never rewritten
  3. indentation is preserved byte for byte
  4. `use(<id>)` pulls the proto/blueprint with that id, compiles it too, and
     places it at the TOP of the file (the DATA block); nested `use(...)` inside
     a pulled body is resolved too. `incld="<id>"` is NOT followed: it is a
     mapping attribute (U+2282 `incld`, an include of code), not an import.

Decisions taken, stated so they can be reversed:
  D1  `[]` and `{}` are protected as well as `()`. The language's own syntax
      file declares {} "intentionally free-form, never rewritten into a rigid
      schema", so rewriting inside it would violate the grammar.
  D2  text inside double quotes is ALSO left alone. desc="..." and name="..."
      are payload, not logic; rewriting them would corrupt the description.
  D3  only whole words are replaced, matched on alias boundaries, so `lang`
      never eats `language` and `crt` never eats `create` inside a longer name.
  D4  a word that has no glyph is left as text and counted in the report, so
      nothing is ever silently dropped.

    py -X utf8 validator\\compile.py <spec.vibe> [-o <out.txt>]
"""
import io
import os
import re
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, os.pardir, "DATA"))
MASTER = os.path.join(DATA, "dictionary_sorted_by_type.txt")
SYM = os.path.join(DATA, "symbols_map.txt")
PROTOS = os.path.join(DATA, "protos.txt")
BLUEPRINTS = os.path.join(DATA, "blueprints.txt")

RX_SYM = re.compile(r"^U\+([0-9A-Fa-f]{4,6}(?:\+[0-9A-Fa-f]{4,6})*)\s+(\S+)\s+\*->\s*(.*)$")
RX_USE = re.compile(r"\buse\s*\(\s*([^)]*?)\s*\)")
RX_ID = re.compile(r'\bid="([^"]*)"')
RX_INCLD = re.compile(r'\bincld="([^"]*)"')
RX_ENTRY = re.compile(r"^\*->\s*(.+?)\s*(?:-\s*(.*))?$")

BLOCK_RULES = "-----RULES-----"
BLOCK_DATA = "-----DATA-----"
BLOCK_CODE = "-----CODE-----"


# ---------------------------------------------------------------- dictionary
def load_alias_to_glyph():
    """master entry block -> concept id; symbols_map word -> glyph; join them."""
    concept_of, concepts = {}, {}
    section = None
    for ln in io.open(MASTER, encoding="utf-8").read().splitlines():
        t = ln.strip()
        if t.startswith("type:"):
            section = t[5:].strip()
            continue
        if not t.startswith("*-> "):
            continue
        m = RX_ENTRY.match(t)
        if not m:
            continue
        names = [x.strip() for x in m.group(1).split(",") if x.strip()]
        if not names:
            continue
        prim = names[0]
        concepts[prim] = {"names": names, "desc": (m.group(2) or "").strip(), "sec": section}
        for n in names:
            concept_of[n.lower()] = prim

    word_to_glyph, glyphs = {}, {}
    for ln in io.open(SYM, encoding="utf-8").read().splitlines():
        t = ln.strip()
        if not t or t.startswith("#"):
            continue
        m = RX_SYM.match(t)
        if not m:
            continue
        g = "".join(chr(int(x, 16)) for x in m.group(1).split("+"))
        rest = m.group(3)
        word, desc = rest.split(" - ", 1) if " - " in rest else (rest, "")
        word, desc = word.strip(), desc.strip()
        glyphs[g] = (word, desc)
        for a in [x.strip() for x in word.split(",") if x.strip()]:
            word_to_glyph[a.lower()] = g
    return concept_of, concepts, word_to_glyph, glyphs


def build_substitution(concept_of, word_to_glyph):
    """alias -> glyph, only for concepts that actually own a glyph"""
    sub, noglyph = {}, set()
    for alias, prim in concept_of.items():
        g = word_to_glyph.get(prim.lower()) or word_to_glyph.get(alias)
        if g:
            sub[alias] = g
        else:
            noglyph.add(prim)
    return sub, noglyph


# ---------------------------------------------------------------- protection
OPEN = {"(": ")", "[": "]", "{": "}"}
CLOSE = {")", "]", "}"}


def segments(line):
    """split a line into (kind, text). kind: 'code' (compilable) or 'keep'."""
    out, buf, i, n = [], [], 0, len(line)
    stack = []
    in_quote = False
    while i < n:
        ch = line[i]
        if in_quote:
            buf.append(ch)
            if ch == '"':
                in_quote = False
            i += 1
            continue
        if ch == '"':
            out.append(("code", "".join(buf)))
            buf = []
            out.append(("keep", ch))
            in_quote = True
            i += 1
            continue
        if ch in OPEN:
            out.append(("code", "".join(buf)))
            buf = []
            out.append(("keep", ch))
            stack.append(OPEN[ch])
            i += 1
            continue
        if stack and ch == stack[-1]:
            buf.append(ch)
            out.append(("keep", "".join(buf)))
            buf = []
            stack.pop()
            i += 1
            continue
        if stack and ch in CLOSE:          # unbalanced closer: keep it literal
            buf.append(ch)
            i += 1
            continue
        buf.append(ch)
        i += 1
    out.append(("code", "".join(buf)))
    return [(k, t) for k, t in out if t != ""]


RX_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def compile_line(line, sub, stats):
    out = []
    for kind, text in segments(line):
        if kind == "keep":
            out.append(text)
            continue

        def repl(m):
            w = m.group(0)
            g = sub.get(w.lower())
            if g:
                stats["replaced"] += 1
                stats["words"][w.lower()] = g
                return g
            stats["unmapped"].add(w.lower())
            return w

        out.append(RX_WORD.sub(repl, text))
    return "".join(out)


# ---------------------------------------------------------------- use/incl
def load_pool():
    pool, order = {}, []
    for path in (BLUEPRINTS, PROTOS):
        if not os.path.exists(path):
            continue
        lines = io.open(path, encoding="utf-8").read().splitlines()
        i = 0
        while i < len(lines):
            t = lines[i].strip()
            if not t.startswith("*-> "):
                i += 1
                continue
            m = RX_ID.search(t)
            if m:
                ident = m.group(1)
                body = [lines[i]]
                j = i + 1
                while j < len(lines):
                    s = lines[j]
                    if s.strip().startswith("*-> ") and not s.startswith((" ", "\t")):
                        break
                    if s.strip() == "" and j + 1 < len(lines) and \
                       not lines[j + 1].startswith((" ", "\t")):
                        break
                    body.append(s)
                    j += 1
                if ident not in pool:
                    pool[ident] = {"header": body[0], "body": body, "src": os.path.basename(path)}
                    order.append(ident)
                i = j
                continue
            i += 1
    return pool, order


def resolve_use(ids, pool, stats):
    """Only the word `use` triggers an import.

    `incld="<id>"` is NOT a dependency to chase here: it is a mapping attribute
    (glyph U+2282, word `incld`, "additional, include") - an include of code
    declared on the entity. The compiler compiles it as an attribute; it does not
    pull the target in. `use(<id>)` is the imperative that imports.
    """
    seen, out = set(), []

    def visit(ident, depth):
        key = ident.strip()
        if key in seen:
            return
        seen.add(key)
        entry = pool.get(key)
        if entry is None:
            stats["missing_use"].append(key)
            return
        # nested use(...) inside the pulled-in body only
        for ln in entry["body"]:
            for m in RX_USE.finditer(ln):
                for d in m.group(1).split(","):
                    if d.strip():
                        visit(d.strip(), depth + 1)
        out.append((key, entry))

    for x in ids:
        visit(x, 0)
    return out


# ---------------------------------------------------------------- emit
def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    src = argv[1]
    dst = None
    if "-o" in argv:
        dst = argv[argv.index("-o") + 1]
    if not os.path.isfile(src):
        print("no such spec: %s" % src)
        return 2

    concept_of, concepts, word_to_glyph, glyphs = load_alias_to_glyph()
    sub, noglyph = build_substitution(concept_of, word_to_glyph)
    pool, _ = load_pool()

    raw = io.open(src, encoding="utf-8").read()
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")

    stats = {"replaced": 0, "words": collections.Counter(), "unmapped": set(),
             "missing_use": []}

    # 1. find use() in the spec
    use_ids = []
    for ln in lines:
        for m in RX_USE.finditer(ln):
            use_ids.extend(x.strip() for x in m.group(1).split(",") if x.strip())
    resolved = resolve_use(use_ids, pool, stats)

    # 2. compile the spec
    code_lines = [compile_line(ln, sub, stats) for ln in lines]

    # 3. compile the pulled-in material
    data_blocks = []
    for ident, entry in resolved:
        block = [compile_line(entry["header"], sub, stats)]
        for ln in entry["body"][1:]:
            block.append(compile_line(ln, sub, stats))
        data_blocks.append((ident, block))

    # 4. assemble
    o = []
    o.append(BLOCK_RULES)
    o.append("glyph dictionary = %d glyphs / %d concepts with a glyph" % (len(glyphs), len(sub)))
    o.append("")
    o.append("what each block is for:")
    o.append("  %s  reference only. Read it, do NOT execute it." % BLOCK_RULES)
    o.append("  %s  already resolved by the compiler. Declarations only, do NOT" % BLOCK_DATA)
    o.append("            execute them separately - they are inlined context.")
    o.append("  %s  the specification. EXECUTION STARTS HERE, top to bottom.")
    o.append("")
    o.append("TASK: Execute the specification in the %s block, in order." % BLOCK_CODE)
    o.append("      Treat %s as already-resolved context, not as new work." % BLOCK_DATA)
    o.append("      Do not translate the glyphs back into words.")
    o.append("")
    o.append("glyphs: glyph = word (meaning)")
    for g in sorted(glyphs, key=lambda x: glyphs[x][0]):
        w, d = glyphs[g]
        o.append("  %-3s = %-12s %s" % (g, w, d))
    o.append("")
    o.append(BLOCK_DATA)
    if not data_blocks:
        o.append("(nothing was pulled in by use)")
    for ident, block in data_blocks:
        o.append("")
        o.append("# resolved from use(): %s" % ident)
        o.extend(block)
    o.append("")
    o.append(BLOCK_CODE)
    o.extend(code_lines)

    text = "\n".join(o)
    if dst:
        io.open(dst, "wb").write((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))
        print("wrote %s" % dst)
    else:
        print(text)

    # 5. report
    print("")
    print("COMPILE REPORT")
    print("  source            : %s (%d lines)" % (src, len(lines)))
    print("  words replaced    : %d occurrences, %d distinct" % (stats["replaced"], len(stats["words"])))
    print("  use() resolved    : %d entr(ies)%s"
          % (len(data_blocks), ("" if not stats["missing_use"]
                                else "  MISSING: " + ",".join(stats["missing_use"]))))
    print("  words with no glyph left as text : %d" % len(stats["unmapped"]))
    if stats["unmapped"]:
        print("     %s" % ", ".join(sorted(stats["unmapped"])[:24]))
    print("  concepts with no glyph at all    : %d%s"
          % (len(noglyph), ("  " + ", ".join(sorted(noglyph)[:16]) if noglyph else "")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
