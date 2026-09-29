#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compiler/compile.py - VibeDSL text -> symbol compiler (for weak models).

Emits ONE file with three blocks, so a weak model can tell at a glance what to
execute and what not to:

    -----RULES-----   the base task in English + the glyph reference
    -----DATA-----    every abstract / proto / blueprint that `use()` pulled in,
                      each marked with an anchor
    -----CODE-----    the specification. Execution starts HERE. The tree is
                      preserved exactly, YAML-style: indentation is never
                      touched, only whole words and operators are swapped.

WHAT "COMPILING" MEANS HERE
  A dictionary word becomes the glyph of its concept, and so does a grammar
  operator. `root == a` becomes two glyphs. The frame of the language is
  therefore symbolic too, not only the vocabulary: a weak model never has to
  read two notations at once.

Rules implemented
  1. a dictionary word OR operator is replaced by the glyph of its concept,
     matched longest-alias-first, so `<->` never loses to `<-` and `<`
  2. text inside (), [] and {} is never rewritten
  3. indentation is preserved byte for byte
  4. `&->` is emitted as the anchor glyph U+2022, which is what
     DATA/abstracts.txt declares it to be
  5. `use(<id>)` pulls the proto/blueprint/abstract with that id out of the RAG
     base (the same DATA/*.txt the API serves), compiles it too, and places it
     in the DATA block marked with an anchor. Nested `use(...)` inside a pulled
     body is resolved too. The originals on disk are opened read-only and are
     never rewritten.
  6. `incld="<id>"` is NOT followed: it is a mapping attribute, an include of
     code declared on the entity. `use()` is the imperative that imports.

Decisions taken, stated so they can be reversed:
  D1  `[]` and `{}` are protected as well as `()`. The language's own syntax
      file declares {} "intentionally free-form, never rewritten into a rigid
      schema", so rewriting inside it would violate the grammar.
  D2  text inside double quotes is ALSO left alone. desc="..." and name="..."
      are payload, not logic; rewriting them would corrupt the description.
      A quoted value is the marker: after compilation a glyph is a keyword and
      a quoted run is a literal.
  D3  only whole tokens are replaced, matched on alias boundaries, so `lang`
      never eats `language` and `crt` never eats `create` inside a longer name.
  D4  a token that has no glyph is left as text and counted in the report, so
      nothing is ever silently dropped.
  D5  `%`, `;`, `{}`, `//`, `-(id)>` and `<(src)-` keep their ASCII form on
      purpose and are declared as reserved in the RULES block. `%` is a percent
      suffix inside values (50%), `{}` is the free-form carrier whose ASCII
      boundary must stay visible, `//` is a human comment, `;` ends a layer.
      Compiling them would change meaning, not shorten it.

    py -X utf8 compiler\\compile.py <spec.vibe> [-o <out.txt>] [--all-glyphs]
"""
import io
import os
import re
import sys
import collections

# The symbol dictionaries live BESIDE this file, in compiler/:
#   symbols_map.txt  the mark table  (U+XXXX  mark  *-> word - meaning)
#   header.txt       the include.h of the compiled output
# The word dictionary stays in DATA/, because six other consumers read it
# (RAG search, the IDE dictionary editor, sort_dict, spellcheck, glyphs guard,
# validator). A second copy of it here would be a second source of truth.
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.normpath(os.path.join(HERE, os.pardir))
DATA = os.path.join(ROOT, "DATA")
MASTER = os.path.join(DATA, "dictionary_sorted_by_type.txt")
SYM = os.path.join(HERE, "symbols_map.txt")
HEADER = os.path.join(HERE, "header.txt")
POOL_FILES = ("abstracts.txt", "protos.txt", "blueprints.txt")
FALLBACK_FILES = ("agents.txt",)
SPLIT_FILES = ("action.dict", "mapping.dict", "operators.dict", "abstracts.txt")

RX_SYM = re.compile(r"^U\+([0-9A-Fa-f]{4,6}(?:\+[0-9A-Fa-f]{4,6})*)\s+(\S+)\s+\*->\s*(.*)$")
RX_ID = re.compile(r'\bid="([^"]*)"')
# The separator must be " - " (space, dash, space). An earlier reader accepted a
# bare "-", which silently truncated every head that contains a dash: the row
# `*-> <-  - left strict link` parsed as head `<` with the description starting
# at "- left strict link", so `<-` and `<->` vanished from the dictionary and
# their marks became unreachable. A head-only row is allowed too.
RX_ENTRY = re.compile(r"^\*->\s*(.+?)\s+-\s+(.*)$")
RX_ENTRY_BARE = re.compile(r"^\*->\s*(\S.*?)\s*$")

BLOCK_RULES = "-----RULES-----"
BLOCK_DATA = "-----DATA-----"
BLOCK_CODE = "-----CODE-----"
ANCHOR = "•"                      # U+2022, the forced-anchor glyph
MULTIVEC = "⪪"                  # U+2AAA, the multivector marker -[N]>

# ---------------------------------------------------------------- dictionary
def split_aliases(head):
    """`-> or` and `->, or` both mean the alias set {`->`, `or`}.

    The old reader took the whole head as ONE alias, so the arrow was stored
    under the two-token key `-> or` and no word matcher could ever produce that
    key - the arrow of the language was uncompilable by construction.
    """
    out = []
    for part in head.split(","):
        for tok in part.split():
            tok = tok.strip()
            if tok and tok not in out:
                out.append(tok)
    return out


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
        m = RX_ENTRY.match(t) or RX_ENTRY_BARE.match(t)
        if not m:
            continue
        names = split_aliases(m.group(1))
        if not names:
            continue
        prim = names[0]
        desc = m.group(2).strip() if m.re is RX_ENTRY else ""
        # A prim can head more than one row (`<` heads four). Merging keeps the
        # aliases; overwriting silently dropped them, which is how `incld`
        # lost the mark filed under it.
        info = concepts.setdefault(prim, {"names": [], "desc": desc, "sec": section})
        for n in names:
            if n not in info["names"]:
                info["names"].append(n)
            concept_of.setdefault(n.lower(), prim)

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
        aliases = split_aliases(word)
        if not aliases:
            continue
        word, desc = ",".join(aliases), desc.strip()
        glyphs[g] = (word, desc)
        for a in aliases:
            word_to_glyph.setdefault(a.lower(), g)
    return concept_of, concepts, word_to_glyph, glyphs


def build_substitution(concept_of, concepts, word_to_glyph, glyphs):
    """alias -> glyph, in two passes so nothing is ever guessed.

    The lookup is by CONCEPT, not by alias. The master declares the words of one
    concept as a list - `create, crt`, `length, size, len`, `location, locat` -
    while symbols_map.txt files the mark under ONE of them, usually the
    short phonetic one the language prefers. The previous reader looked the mark
    up by the concept's own name first, missed, and rescued only the single alias
    that happened to match, so `crt` compiled and `create` did not: 74 words
    across 64 concepts had a mark in the table that no input could reach.

    pass 1  a word that has a mark of its OWN keeps it. Always.
    pass 2  a word with no mark of its own inherits from its siblings - but only
            when they all agree on ONE mark. When the siblings disagree the
            dictionary contradicts itself (`unknown, none, unk` where `none` is
            marked as absence and `unk` as unknown; `include, import, incld`
            where include and incld carry different marks), so the word is left
            as text and reported. A wrong mark is worse than no mark: one makes
            the model act on a meaning nobody declared.

    Nothing is invented. Every pairing is one the master itself states.
    """
    sub, noglyph, ambiguous = {}, set(), set()
    for prim, info in concepts.items():
        own = {}
        for name in info["names"]:
            g = word_to_glyph.get(name.lower())
            if g:
                own[name] = g
        for name, g in own.items():
            sub[name.lower()] = g
        for name in info["names"]:
            if name in own:
                continue
            marks = {g for g in own.values()}
            if len(marks) == 1:
                sub[name.lower()] = next(iter(marks))
            elif len(marks) > 1:
                ambiguous.add(name)
            else:
                noglyph.add(prim)
    for g, (word, _d) in glyphs.items():
        if g not in set(sub.values()):
            ambiguous.add(word)
    return sub, noglyph, ambiguous

# ---------------------------------------------------------------- protection
OPEN = {"(": ")", "[": "]", "{": "}"}
# Only {} opens a protected scope. () and [] are transparent: a word inside
# them is a word, and a command written as check(x) used to sit inside the paren
# and never compile at all. {} stays protected because a brace block is a
# free-form custom block, deliberately unwritten (see the header).
OPEN_KEEP = {"{": "}"}
# () and [] are compiled, but a name the spec declared for itself stays text
# inside them: show(theme) is a reference to the prop called theme, not to the
# word theme. Outside the parens both are the word, and both compile.
PARENS = {"(": ")", "[": "]"}


def segments(line):
    """split a line into (kind, text) runs. kind: 'code' (compilable) or 'keep'.

    The rule is a STACK, not a flag. While a (), [] or {} scope is open,
    everything up to its matching close is 'keep', nested scopes included, and
    a // or /* */ comment is 'keep' to the end of the line or the closing star.

    The previous reader flushed the pending buffer as 'code' every time a NESTED
    bracket or a quote opened, so `use(VibeDSL:proto[if,goal])` and
    `name="main"` were both compiled - the promise that quoted payload and
    action scope are never rewritten was not actually kept.
    """
    out, buf = [], []
    stack = []
    parens = []
    quote = False

    def flush(kind):
        if buf:
            out.append((kind, "".join(buf)))
            del buf[:]

    def comment_end(i):
        """index just past the comment starting at i, or None if not one"""
        if line.startswith("//", i):
            return n
        if line.startswith("/*", i):
            j = line.find("*/", i + 2)
            return n if j < 0 else j + 2
        return None

    i, n = 0, len(line)
    while i < n:
        ch = line[i]
        if quote:
            # A backslash escapes the next character, INCLUDING a quote. Without
            # this, \" closed the string, the backslash landed outside it and was
            # translated to its glyph - so the escape moved to AFTER the quote it
            # was escaping, and every later quote on the line lost its partner.
            # The lines that broke were the ones holding the invented names.
            if ch == "\\" and i + 1 < n:
                buf.append(ch)
                buf.append(line[i + 1])
                i += 2
                continue
            buf.append(ch)
            if ch == '"':
                quote = False
                flush("keep")
            i += 1
            continue
        # The two written spellings that are one glyph each. They are lifted out
        # before the bracket rule runs, otherwise `-[3]>` would open a `[]` scope
        # and the marker would land in a 'keep' run and never compile.
        mv = RX_MULTIVEC.match(line, i)
        if mv:
            buf.append(mv.group(0))
            i = mv.end()
            continue
        if line.startswith("&->", i):
            buf.append("&->")
            i += 3
            continue
        if stack:
            if ch in OPEN_KEEP:
                stack.append(OPEN_KEEP[ch])
                buf.append(ch)
            elif ch == stack[-1]:
                buf.append(ch)
                stack.pop()
                if not stack:
                    flush("keep")
            else:
                buf.append(ch)
            i += 1
            continue
        # top level
        end = comment_end(i)
        if end is not None:
            # flush the code BEFORE the comment first. Appending the comment to
            # a buffer that still holds unflushed code merged the two into one
            # 'keep' run, so `show prj:source:data // note` lost its marks
            # entirely: the line has no bracket, nothing flushed on the way, and
            # the whole thing was handed to the model as payload.
            flush("code")
            buf.append(line[i:end])
            flush("keep")
            i = end
            continue
        if ch == '"' or ch in OPEN_KEEP or ch in PARENS:
            flush("code")
            buf.append(ch)
            if ch == '"':
                quote = True
            elif ch in PARENS:
                parens.append(PARENS[ch])
            else:
                stack.append(OPEN_KEEP[ch])
            i += 1
            continue
        if parens and ch == parens[-1]:
            parens.pop()
            buf.append(ch)
            flush("paren")
            i += 1
            continue
        buf.append(ch)
        i += 1
    flush("keep" if (stack or quote) else ("paren" if parens else "code"))
    return [(k, t) for k, t in out if t]


# ---------------------------------------------------------------- tokenizer
RX_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
WORDCH = "A-Za-z0-9_"
RX_ASSIGN = re.compile(r'\b(?:name|id)\s*=\s*"?([^",\)\]]+)"?')
# -[N]> is the multivector marker; N is a digit count, so the table alias
# `-[]>` never matches the written form. It is emitted as its own glyph first.
RX_MULTIVEC = re.compile(r"-\[\d*\]>")
# `!=` is not a VibeDSL operator: the language writes inequality as `!(a==b)` and
# says outright that `<>` is NOT "not equal" (RULES.MD:49). It is left as text on
# purpose - compiling it would invent an operator - so it must be REPORTED, or a
# model reads it as "not assign" and acts on a meaning nobody declared.
RX_NOTEQ = re.compile(r"!=")
# The base files mark an object with a leading `*->`. That delimiter belongs to
# the storage format, not to the logic: compiled, `*` became the multiplication
# glyph and the entry opened with a multiplication sign glued to an arrow. The
# anchor line already delimits the entry, so the marker is dropped.
RX_OBJMARK = re.compile(r"^\s*\*->\s?")
# The header is the C++ `#include` of this compiler: one hand-written file with
# every invariant sentence, inlined into the RULES block of every compiled spec.
# It lives in DATA/ beside the rest of the base, is opened read-only, and is
# served by the RAG API like any other base file. It is NOT a Python string
# literal, because prose that lives inside code cannot be proofread, diffed or
# translated - and this prose is what a weak model reads on every single task.
RX_SLOT = re.compile(r"@([A-Z_]+)@")


def make_token_rx(sub):
    """one alternation over every alias that owns a glyph, longest alias first.

    Longest-first is what keeps the frame honest: `<->` must be tried before
    `<-`, and `<-` before `<`, or the arrow family silently degrades.

    A word-shaped alias carries its own lookarounds so it can only match a whole
    word - otherwise `styp` would be eaten by a `sty` alias. A punctuation alias
    carries none, because `a->b` must still compile.
    """
    alts = []
    for a in sorted(sub, key=len, reverse=True):
        e = re.escape(a)
        if a[0].isalnum() or a[0] == "_":
            e = r"(?<![%s])%s(?![%s])" % (WORDCH, e, WORDCH)
        if a == "=":
            # `!=` is not a VibeDSL operator: the language says `<>` is NOT
            # "not equal" and inequality is written `!(a==b)` (RULES.MD:49). The
            # guard used to be `(?<!!)`, which is TEXTUAL, so a second pass saw
            # `¬=` - the `!` already a mark - and compiled the `=` after all:
            # `!=` -> `¬=` -> `¬=`, never the same file twice. Blocking on the
            # mark as well as the letter makes the output stable. The form is
            # REPORTED, not silently mangled into "not assign".
            e = r"(?<![!¬])" + e
        alts.append(e)
    return re.compile("|".join(alts)) if alts else None


# A name the spec declared for itself. Inside a paren it stays text: show(theme)
# refers to the prop this spec called theme, not to the base word theme, and the
# two are different things that happen to share a spelling. Outside the parens
# the word is the word and compiles, which is why this is scoped to 'paren' runs
# and not to the whole line.
# The ASSIGN mark is what `=` compiles to, so an already-compiled line carries
# no `=` at all. Matching only the source spelling made local_names() see a
# DIFFERENT set on a second pass - every name it was protecting had vanished -
# so the words it had shielded compiled anyway and the legend grew 62 -> 123.
# Accepting both spellings is what makes a compile idempotent.
ASSIGN = '[=\u2a72]'
RX_LOCAL_ID = re.compile('\bid[=⩲]"([^"]+)"')
RX_LOCAL_ABS = re.compile(r'abstract(?::\w+)?"([^"]+)"')
RX_LOCAL_NAME = re.compile('\bname[=⩲]"([^"]+)"')

def local_names(lines):
    """every identifier this spec claims, lowercased"""
    out = set()
    for ln in lines:
        for rx in (RX_LOCAL_ID, RX_LOCAL_ABS, RX_LOCAL_NAME):
            for m in rx.finditer(ln):
                out.add(m.group(1).lower())
    return frozenset(out)


def compile_line(line, sub, token_rx, stats, known=None, local=None):
    out = []
    local = local or frozenset()
    for kind, text in segments(line):
        if kind == "keep":
            out.append(text)
            continue
        in_paren = kind == "paren"
        # DATA/abstracts.txt declares &-> to be the textual spelling of the
        # anchor glyph U+2022 and says the compiler emits U+2022 in its place.
        if "&->" in text:
            text = text.replace("&->", ANCHOR)
        text = RX_MULTIVEC.sub(MULTIVEC, text)
        if RX_NOTEQ.search(text):
            stats["noteq"].add(text.strip()[:64])
        for g in (ANCHOR, MULTIVEC):
            if g in text and g not in stats["glyphs_used"]:
                stats["glyphs_used"].append(g)

        def repl(m):
            w = m.group(0)
            if in_paren and w.lower() in local:
                return w
            g = sub.get(w.lower())
            if g:
                stats["replaced"] += 1
                stats["words"][w.lower()] = g
                if g not in stats["glyphs_used"]:
                    stats["glyphs_used"].append(g)
            return g

        if token_rx:
            text = token_rx.sub(repl, text)
        # every remaining word: if the base knows it but it owns no glyph, say so
        for w in RX_WORD.findall(text):
            lw = w.lower()
            if lw in sub or (in_paren and lw in local):
                continue
            if known is None or lw in known:
                stats["unmapped"].add(lw)
            else:
                stats["undefined"].add(lw)
        out.append(text)
    return "".join(out)


# ---------------------------------------------------------------- use/incl
def split_use_args(arg):
    """the four forms `use()` is written in, all of which occur in real specs:

        use(id)                    use(a, b)                -> id, id
        use(NS:kind[a, b])         use(VibeDSL:proto[if,goal])
        use(agent name="coder")    use(agent:name="coder")  -> coder
    """
    parts, buf, depth = [], [], 0
    for ch in arg:                      # split on commas OUTSIDE brackets only
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))

    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if "[" in p and p.endswith("]"):
            _head, _, inner = p.partition("[")
            out.extend(x.strip() for x in inner[:-1].split(",") if x.strip())
            continue
        m = RX_ASSIGN.search(p)
        if m:
            out.append(m.group(1).strip())
            continue
        out.append(p.split(":")[-1].strip())
    return [x for x in out if x]


def read_entries(path):
    """split a RAG base file into `*->` objects, keeping the body lines.

    A new object starts at ANY line whose stripped form begins with `*->`, not
    only at column 0: DATA/agents.txt indents its second entry by one space, and
    the old column-0 test swallowed `dsl-plan` into the body of `coder`.
    """
    lines = io.open(path, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    entries, i = [], 0
    while i < len(lines):
        if not lines[i].strip().startswith("*-> "):
            i += 1
            continue
        body = [lines[i]]
        j = i + 1
        while j < len(lines):
            s = lines[j]
            if s.strip().startswith("*-> "):
                break
            if s.strip() == "" and j + 1 < len(lines) and \
               not lines[j + 1].strip().startswith("*-> ") and \
               not lines[j + 1].startswith((" ", "\t")):
                break
            body.append(s)
            j += 1
        entries.append(body)
        i = j
    return entries


def load_pool():
    """id -> entry, over the whole RAG base. Read-only; disk is never written.

    The three kinds the language defines - abstract, proto, blueprint - are the
    pool proper. DATA/agents.txt is a fallback so `use(agent name="coder")`
    resolves instead of reporting MISSING for the rest of time.
    """
    pool, order = {}, []
    for name in POOL_FILES + FALLBACK_FILES:
        path = os.path.join(DATA, name)
        if not os.path.exists(path):
            continue
        for body in read_entries(path):
            ident = ""
            for ln in body[:3]:
                m = RX_ID.search(ln)
                if m:
                    ident = m.group(1).strip()
                    break
            if not ident:
                toks = body[0].strip()[4:].split()
                ident = toks[1].strip("()") if len(toks) > 1 else ""
            if not ident or ident in pool:
                continue
            pool[ident] = {"body": body, "src": name}
            order.append(ident)
    return pool, order


def resolve_use(spec_lines, pool, stats):
    """Only the word `use` triggers an import.

    `incld="<id>"` is NOT a dependency to chase: it is a mapping attribute
    (glyph U+2282 `incld`, "additional, include") - an include of code declared
    on the entity. The compiler compiles it as an attribute; it does not pull
    the target in. `use(<id>)` is the imperative that imports.
    """
    seen, out = set(), []

    def visit(ident):
        if ident in seen:
            return
        seen.add(ident)
        entry = pool.get(ident)
        if entry is None:
            stats["missing_use"].append(ident)
            return
        for ln in entry["body"]:                    # nested use(...) in the body
            for m in RX_USE.finditer(ln):
                for d in split_use_args(m.group(1)):
                    visit(d)
        out.append((ident, entry))

    for ln in spec_lines:
        for m in RX_USE.finditer(ln):
            for d in split_use_args(m.group(1)):
                visit(d)
    return out


RX_USE = re.compile(r"\buse\s*\(([^)]*)\)")


# ---------------------------------------------------------------- header
def load_header(values):
    """read header.txt, substitute the slots, return the lines.

    A slot the header asks for and the compiler does not know is a hard error,
    not a silent blank: a typo in the header must never reach a model as a hole
    in its instructions.
    """
    if not os.path.isfile(HEADER):
        raise SystemExit("no header: %s" % os.path.relpath(HEADER, ROOT))
    raw = io.open(HEADER, encoding="utf-8-sig").read().replace("\r\n", "\n")
    lines = [ln for ln in raw.split("\n")
             if ln.strip() not in ("start compiled header", "end compiled header")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        raise SystemExit("header is empty: %s" % os.path.relpath(HEADER, ROOT))

    unknown = set()

    def sub(m):
        key = m.group(1)
        if key not in values:
            unknown.add(key)
            return m.group(0)
        return str(values[key])

    out = [RX_SLOT.sub(sub, ln) for ln in lines]
    if unknown:
        raise SystemExit("header asks for unknown slot(s): %s"
                         % ", ".join("@%s@" % u for u in sorted(unknown)))
    return out


# ---------------------------------------------------------------- emit
def rules_block(glyphs, stats, all_glyphs, concepts_total, concepts_marked,
                src, data_count, want_rules=True, want_legend=True):
    o = [BLOCK_RULES, ""]
    # The RULES template and the GLYPHS legend are CONTEXT, not payload: they
    # cost 130 lines and ~3500 characters, and on the IDE spec the legend alone
    # is 20% of the whole output and 38% of the spec. A mark is ONE token and
    # its explanation is about sixteen, so the explanation costs sixteen times
    # the fact it explains.
    #
    # That trade is right for a strong reader with attention to spare and wrong
    # for a small one. A 0.5B advisor is given the knowledge in its weights
    # instead, and wants the output short. So both are switchable, and neither is
    # the default for the other: dropping the legend is not a cheaper way to
    # ship the same thing, it is a different reader.
    if not want_rules:
        o = [BLOCK_RULES, ""]
        o.append("  (RULES omitted, and with them the GLYPHS legend: --no-rules")
        o.append("  implies --no-legend. The reader is expected to know both")
        o.append("  already.)")
        o.append("")
        return o
    o.extend(load_header({
        "BLOCK_RULES": BLOCK_RULES,
        "BLOCK_DATA": BLOCK_DATA,
        "BLOCK_CODE": BLOCK_CODE,
        "ANCHOR": ANCHOR,
        "SOURCE": src,
        "COUNT_MARKS": len(stats["glyphs_used"]),
        "COUNT_TOTAL": len(glyphs),
        "COUNT_CONCEPTS": concepts_total,
        "COUNT_DATA": data_count,
    }))

    o.append("")
    o.append("GLYPHS")
    if not want_legend:
        o.append("  (legend omitted: --no-legend. Every mark here is one token and")
        o.append("  its meaning is expected to be known already.)")
        o.append("")
        return o
    if all_glyphs:
        o.append("  the whole base table (%d marks, --all-glyphs):" % len(glyphs))
        for g, (w, d) in sorted(glyphs.items(), key=lambda kv: kv[1][0]):
            o.append("    %-3s = %-14s %s" % (g, w, d))
        o.append("")
        return o

    o.append("  %d of %d dictionary concepts own a mark. %d of them appear in this"
             % (concepts_marked, concepts_total, len(stats["glyphs_used"])))
    o.append("  file, listed in order of first use. A mark that is not listed")
    o.append("  here does not occur in this file.")
    o.append("")
    seen = set()
    for g in stats["glyphs_used"]:
        if g in seen or g not in glyphs:
            continue
        seen.add(g)
        w, d = glyphs[g]
        o.append("    %-3s = %-14s %s" % (g, w, d))
    o.append("")
    return o


def parse_args(argv):
    """-> (src, dst, all_glyphs, want_rules, want_legend)

    A second POSITIONAL argument is taken as the output path. It used to be
    dropped in silence, and that is not a cosmetic bug: a caller who wrote
    `compile.py spec.vibe out.txt` got the compiled text on stdout AND kept
    reading the OLD out.txt, then drew conclusions from a stale file. Someone
    lost two findings that way before this was fixed, so an unknown flag or a
    third positional is now an error rather than a shrug.

    --no-rules drops the RULES template, --no-legend drops the GLYPHS legend.
    Both are CONTEXT rather than payload. --no-rules already implies
    --no-legend: the legend is emitted inside the rules block, and a reader
    with no template has no use for a glossary either. It says so rather than
    making the reader discover it by counting lines. Both exist for a reader
    that already holds the knowledge in its weights; a 0.5B advisor is the case
    they were written for.
    """
    src = dst = None
    all_glyphs = False
    want_rules = want_legend = True
    extra = []
    i = 1
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            return None, None, False, True, True
        if a == "-o":
            i += 1
            dst = argv[i] if i < len(argv) else None
        elif a == "--all-glyphs":
            all_glyphs = True
        elif a == "--no-rules":
            want_rules = False
        elif a == "--no-legend":
            want_legend = False
        elif a.startswith("-"):
            extra.append(a)
        elif src is None:
            src = a
        elif dst is None:
            dst = a
        else:
            extra.append(a)
        i += 1
    if extra:
        raise SystemExit("compile.py: unexpected argument(s): %s\n"
                         "usage: py -X utf8 compiler\\compile.py <spec> "
                         "[-o <out>] [--all-glyphs] [--no-rules] [--no-legend]"
                         % " ".join(extra))
    if dst is not None and not os.path.isabs(dst):
        dst = os.path.abspath(dst)
    return src, dst, all_glyphs, want_rules, want_legend


def main(argv):
    src, dst, all_glyphs, want_rules, want_legend = parse_args(argv)
    if not src:
        print(__doc__)
        return 2
    if not os.path.isfile(src):
        print("no such spec: %s" % src)
        return 2

    concept_of, concepts, word_to_glyph, glyphs = load_alias_to_glyph()
    sub, noglyph, ambiguous = build_substitution(concept_of, concepts,
                                                 word_to_glyph, glyphs)
    token_rx = make_token_rx(sub)
    # Consistency of the compiler's own inputs, before a single line is read.
    # A contradiction between the map and the dictionary is a token this
    # compiler can resolve and the language cannot name, so it stops the build.
    # A split file being behind is stated and left alone - see consistency.py.
    import consistency as _cons
    _cerr, _cnote = _cons.check(DATA, SYM, SPLIT_FILES, FALLBACK_FILES)
    if "--quiet" not in sys.argv:
        print(_cons.report(_cerr, _cnote))
    # advisory: four false alarms so far, so it reports and does not
    # decide. --strict promotes it once it can prove a real one.
    if _cerr and "--strict" in sys.argv:
        return 2

    pool = load_pool()

    raw = io.open(src, encoding="utf-8-sig").read()      # -sig drops a BOM
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")

    stats = {"replaced": 0, "words": collections.Counter(), "unmapped": set(),
             "undefined": set(), "missing_use": [], "glyphs_used": [],
             "noteq": set()}

    # 1. find use() in the spec and pull it out of the RAG base
    resolved = resolve_use(lines, pool, stats)

    # 2. compile the spec
    known = set(concept_of)
    local = local_names(lines)
    code_lines = [compile_line(ln, sub, token_rx, stats, known, local)
                  for ln in lines]

    # 3. compile the pulled-in material
    data_blocks = []
    for ident, entry in resolved:
        block = []
        for n, ln in enumerate(entry["body"]):
            if n == 0:
                ln = RX_OBJMARK.sub("", ln)
            block.append(compile_line(ln, sub, token_rx, stats, known, local))
        data_blocks.append((ident, entry["src"], block))

    # 4. assemble
    concepts_marked = len({concept_of[a] for a in sub if a in concept_of})
    o = rules_block(glyphs, stats, all_glyphs, len(concepts), concepts_marked,
                    os.path.basename(src), len(data_blocks),
                    want_rules, want_legend)

    o.append(BLOCK_DATA)
    o.append("")
    if not data_blocks:
        o.append("(empty - the specification declares no use(); there is nothing")
        o.append(" to resolve. The whole specification is in %s.)" % BLOCK_CODE)
    else:
        o.append("Each entry below was pulled in by use() from the base and is")
        o.append("marked with an anchor. Declarations, not steps.")
        o.append("")
        for ident, srcname, block in data_blocks:
            o.append("%s anchor id=\"%s\"  from DATA/%s" % (ANCHOR, ident, srcname))
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
    unknown = [g for g in stats["glyphs_used"] if g not in glyphs]
    print("")
    print("COMPILE REPORT")
    print("  source            : %s (%d lines)" % (src, len(lines)))
    print("  words replaced    : %d occurrences, %d distinct" % (stats["replaced"], len(stats["words"])))
    print("  distinct glyphs   : %d emitted, %d in the base table"
          % (len(stats["glyphs_used"]), len(glyphs)))
    print("  use() resolved    : %d entr(ies)%s"
          % (len(data_blocks), ("" if not stats["missing_use"]
                                else "  MISSING: " + ",".join(stats["missing_use"]))))
    print("  tokens with no glyph left as text : %d" % len(stats["unmapped"]))
    if stats["unmapped"]:
        print("     %s" % ", ".join(sorted(stats["unmapped"])[:24]))
    print("  words the base does not define   : %d (identifiers, kept as text)" % len(stats["undefined"]))
    print("  concepts with no glyph at all    : %d%s"
          % (len(noglyph), ("  " + ", ".join(sorted(noglyph)[:16]) if noglyph else "")))
    if stats["noteq"]:
        print("  non-canonical `!=` left as text : %d line(s) - the language writes"
              % len(stats["noteq"]))
        print("     inequality as !(a==b); `<>` is NOT not-equal (RULES.MD:49)")
        for n in sorted(stats["noteq"])[:4]:
            print("       %s" % n)
    if ambiguous:
        print("  the dictionary contradicts itself : %d mark(s) unreachable: %s"
              % (len(ambiguous), ", ".join(sorted(ambiguous)[:12])))
        print("     left as text on purpose - a wrong mark is worse than no mark")
    if unknown:
        print("  FAIL: emitted a glyph that is not in %s: %s"
              % (os.path.relpath(SYM, ROOT), " ".join(unknown)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
