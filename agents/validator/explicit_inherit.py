#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validator/explicit_inherit.py - rewrite space-separated mappings as `:`.

The language allows `frm name="x"` but calls it an antipattern
(DATA/create_speck_check.md:91 "Наследование через `:` обязательно - ради
KV-кэша", :252 "`item name="x"` вместо `item:name="x"`"). The validator was
reworked on 2026-09-25 to STOP ERRORING on the space form
(DATA/create-specs-manual.txt:563), so both stay legal - this tool only makes
the corpus use the explicit one, uniformly.

    py -X utf8 validator\\explicit_inherit.py --dry     # report, change nothing
    py -X utf8 validator\\explicit_inherit.py --write   # rewrite in place
    py -X utf8 validator\\explicit_inherit.py --write --fold-english
    py -X utf8 validator\\explicit_inherit.py --diff    # show every rewrite

WHAT COUNTS AS A MAPPING
  A space becomes `:` only when the right-hand side is an ATTRIBUTE:
    `word =`     `frm name="x"`      -> `frm:name="x"`
    `word :`     `frm styp:text`     (already explicit, left alone)
    a bare noun  `abstract prop id=` -> `abstract:prop:id=`
  and the left-hand side ends in a structure token, not in prose.

WHY THIS REUSES compiler/compile.py
  The first version of this file had its own scanner and corrupted English:
  `the structure: a deeper` became `the:structure: a deeper`, and it ate
  `desc="... template: lang ..."`. Both are the same class of bug the compiler
  already solved - a payload string and a prose colon are indistinguishable from
  a mapping without a real scanner. So the scanner is IMPORTED, not rewritten.

WHAT IS DELIBERATELY NOT TOUCHED
  - DATA/create-specs-manual.txt and DATA/create_speck_check.md. They QUOTE the
    antipattern (`item name="x"` instead of `item:name="x"`), and the manual
    documents the validator rule using the space form. Rewriting those lines
    would destroy the very text that documents the rule.
  - the ` - description` tail of a master-dictionary row: that is prose.
  - prose lines of a .md file. Only fenced code and VibeDSL-looking lines count.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir))
sys.path.insert(0, os.path.join(ROOT, "compiler"))

import compile as CC          # noqa: E402  the scanner, imported not copied

# Files whose job is to DOCUMENT the rule, including the counter-example.
DOCS_ABOUT_THE_RULE = (
    "DATA/create-specs-manual.txt",
    "DATA/create_speck_check.md",
    # the compiler's own RULES template. It is inlined into every compiled
    # spec, and its HOW TO READ AN ACTION SCOPE section documents the very
    # shapes - `owner:property   the owner LEADS` - that the space rule would
    # otherwise rewrite into nonsense. It documents the rule; it is not subject
    # to it.
    "compiler/header.txt",
)

# bare noun keys: no `=`, still a mapping attribute
BARE_KEYS = ("prop", "props", "fun", "func", "function", "frm", "frmwrk",
             "obj", "ent", "val")

LEFT = r'(?:[A-Za-z_][A-Za-z0-9_]*|[)\]"\x01])'
# The left token must START where a token can start - not mid-word, and not
# inside a payload string. It may follow a space OR a colon, because
# `exm:abstract prop id="X"` is exactly the shape we have to fix.
BOUND = r'(?<![A-Za-z0-9_"])'
RX_ASSIGN = re.compile(BOUND + LEFT + r'[ \t]+([A-Za-z_][A-Za-z0-9_]*[ \t]*=)')
RX_BARE = re.compile(BOUND + LEFT + r'[ \t]+(' +
                     r'(?:' + '|'.join(BARE_KEYS) + r')(?=[ \t]|$))')

# `var i=0` is a declaration AND it is implicit inheritance: the space between
# the keyword and the name it declares carries the containment without an anchor.
# The anchor rule does not care which category the word is in - a declaration
# needs its `:` exactly as an attribute does, otherwise the model reads
# `var i` as two free words and has to guess that `i` belongs to `var`.
# The master lists this shape among the `:` payload-separator cases
# (RULES.MD:60 "payload separator: key:value"), which is the same role the
# space was playing, only with the anchor attached.
#
# Earlier this tool protected `var` on the grounds that master:1078 calls it a
# declaration. That was the wrong reason: it defended the KEYWORD, not the
# SEPARATOR. The separator is what the rule is about.

# `;` is a CONTEXT CUT, not a step separator (master:947 "end of current
# function/layer/context ... marker of end context and clean token memory", and
# "do not use in prototypes or rules" - yet `for(var i=0;i<5;i=incr(1))` sits in
# DATA/protos.txt:27, which IS a prototype). A model that obeys it cuts the loop
# context at every `;` and the loop cannot run. Inside a `for(` scope the clause
# separator is therefore `:`, which descends instead of cutting.
RX_FOR = re.compile(r'\bfor\s*\(')


def _colonise(run):
    """space-separated mapping -> `:` inside one already-verified code run"""
    run = RX_BARE.sub(lambda m: m.group(0).replace(" ", ":", 1), run)
    return RX_ASSIGN.sub(lambda m: m.group(0).replace(" ", ":", 1), run)


def fix_for_scope(text):
    """reach into a for(...) clause list, where two things need fixing:

      1. `;` is a CONTEXT CUT (master:947 "end of current function/layer/context
         ... marker of end context and clean token memory", and "do not use in
         prototypes or rules" - yet the loop sat in DATA/protos.txt:27, which IS
         a prototype). A model that obeys it cuts the loop context at every `;`
         and the loop cannot run. The clause separator is `:` instead, which
         descends rather than cutting.
      2. the same clause list is implicit inheritance: `var i=0` carries the
         containment with a space and loses the anchor.

    It has to run on the RAW line, before segmentation, because the clause list
    lives inside an action scope which segmentation protects. Safe to run early:
    it only fires inside a `for(` span, and the interior is still run through the
    same scanner, so a quoted string in there stays untouched.
    """
    m = RX_FOR.search(text)
    if not m:
        return text
    start = m.end() - 1
    depth = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end < 0:
        return text
    inner = text[start + 1:end]
    inner = inner.replace(";", ":")
    fixed = []
    for kind, run in CC.segments(inner):
        fixed.append(_colonise(run) if kind == "code" else run)
    return text[:start + 1] + "".join(fixed) + text[end:]

RX_OBJ = re.compile(r'^\s*\*->\s')
DATA_EXT = (".txt", ".md")
SKIP_DIRS = ("temp", "GLOS", "node_modules", "__pycache__")


def is_data_file(name):
    """.MD must count - RULES.MD is a base reference, and a case-sensitive
    endswith() skipped it silently, which is how the chain rewrite was thought
    to be finished while 14 lines of RULES.MD still used a space."""
    return name.lower().endswith(DATA_EXT)


def iter_targets():
    """every reference file in the repo, one definition of scope.

    Both this tool and validator/spell_checker_v2.py must see the SAME set. Two
    tools with two notions of scope is how a file ends up checked by one and
    fixed by neither.
    """
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in sorted(names):
            if is_data_file(f):
                p = os.path.join(base, f)
                rel_ = os.path.relpath(p, ROOT).replace("\\", "/")
                if rel_ not in DOCS_ABOUT_THE_RULE:
                    yield rel_, p
RX_EXM = re.compile(r'^\s*(?:->\s*)?exm\s*:', re.IGNORECASE)
RX_FENCE = re.compile(r'^\s*```')
# a .md line only counts if it actually looks like VibeDSL. A markdown bullet
# (`* ` or `- `) never does, even when it quotes code - rewriting
# `* USERDEFS register: abstract id="X"` would corrupt the prose that documents
# the very rule this tool enforces.
RX_BULLET = re.compile(r'^\s*[*-]\s')
# A markdown table row is not code either. This one was learned the hard way:
# the row documenting the CUT check contained `for(` and a `;`, and the CUT check
# flagged its own documentation.
RX_TABLE = re.compile(r'^\s*\|')
VIBE_HEADS = (r'\*->|fun|proto|blplan|abstract|use|for|prj|crt|exam|show|ret|val|frm|item'
              r'|part|stage|evt|event|flow|sort|sel|rcl|view|inp|btn|col|row|card|sec|pag|msg')
RX_VIBE = re.compile(r'(?:->|<->)|^\s*(?:' + VIBE_HEADS + r')\b')


SENT = "\x01"

# `X of Y` / `X from Y` inside an action scope is an anchor the author could not
# find, written in the register the model is most fluent in. English prepositions
# are near-deterministic continuations, so they are the cheapest thing a model can
# emit - and a rare mark is not. Under load it drifts to English, and the drift
# is invisible because the words are not in the base: the report said
# "tokens with no glyph left as text: 0" with 63 of them in the file.
#
# So the relation gets its anchor back: X <prep> Y  ->  Y:X. One rule for both
# prepositions, because `name of view` and `theme from mapping` are the same
# relation - that is one drift class instead of two.
#
# REACH IS DELIBERATE AND LIMITED. It goes inside `()` - that is where the drifted
# logic lives, e.g. `set(name of view "X")`. It never goes inside `""` or `{}`:
#   act="load theme from mapping"   a description, English is CORRECT there
#   show("free of comments")        English prose; a word list would eat it
# Folding those would be vandalism, so the scanner tracks both.
def reachable_code(text):
    """the code runs INSIDE an action scope: inside `()`, outside `""` and `{}`.

    Both the english fold and the ENGLISH check need exactly this view, and both
    were wrong before it existed: CC.segments() marks `(...)` as protected, so a
    scan that used it reported "0 english words in code" with 63 of them sitting
    in `set(...)`. Protection is right for COMPILING - the compiler must not
    rewrite an action's arguments - and wrong for CHECKING drift, because the
    drift lands precisely there.
    """
    out = []
    i, n = 0, len(text)
    depth = 0
    buf = []
    while i < n:
        ch = text[i]
        if ch == '"':
            j = text.find('"', i + 1)
            j = n if j < 0 else j + 1
            if depth > 0 and buf:
                out.append("".join(buf))
                buf = []
            i = j
            continue
        if ch == "{":
            j = text.find("}", i + 1)
            j = n if j < 0 else j + 1
            if depth > 0 and buf:
                out.append("".join(buf))
                buf = []
            i = j
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth > 0 and buf:
                out.append("".join(buf))
                buf = []
            depth = max(0, depth - 1)
        elif depth > 0:
            buf.append(ch)
        i += 1
    if depth > 0 and buf:
        out.append("".join(buf))
    return out


RX_REL_OF = re.compile(r"([A-Za-z_]\w*)[ \t]+of[ \t]+([A-Za-z_]\w*)")
RX_REL_FROM = re.compile(r"([A-Za-z_]\w*)[ \t]+from[ \t]+([A-Za-z_]\w*)")


def fold_english_in_scope(text, report=None):
    """inside `()` and outside `""`/`{}`.

    Two relations, two different repairs - they are NOT the same thing:

      `name of view`      = OWNERSHIP. The field belongs to the object, so it
                            gets the anchor, with the order the language uses:
                            `view:name`.
      `theme from mapping` = PROVENANCE. Where it was read from is description,
                            not logic - and the description is already there,
                            two tokens to the left in `act="..."`. So the source
                            is dropped from the CODE, not turned into a pin:
                            `load(theme)`. Making it `mapping:theme` would assert
                            that the mapping owns the theme, which nobody claimed.

    The drop is counted into `report` rather than done silently.
    """
    out = []
    i, n = 0, len(text)
    depth = 0
    while i < n:
        ch = text[i]
        if ch == '"':
            j = text.find('"', i + 1)
            j = n if j < 0 else j + 1
            out.append(text[i:j])
            i = j
            continue
        if ch == "{":
            j = text.find("}", i + 1)
            j = n if j < 0 else j + 1
            out.append(text[i:j])
            i = j
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth > 0:
            m = RX_REL_OF.match(text, i)
            if m:
                out.append(m.group(2) + ":" + m.group(1))
                if report is not None:
                    report["of"] += 1
                i = m.end()
                continue
            m = RX_REL_FROM.match(text, i)
            if m:
                out.append(m.group(1))
                if report is not None:
                    report["from"] += 1
                    report["from_src"].add(m.group(2))
                i = m.end()
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def convert_code(text):
    """the two passes are structure-aware, and a chain survives a payload.

      1. the for() clause list is reached into first - `;` there is a context cut,
         and `var i=0` in it is implicit inheritance
      2. space-separated mappings become `:` in CODE runs only

    A naive per-run rewrite got chains WRONG, and this was caught by looking at
    what the tool had already written: segmentation splits at the payload string,
    so `fun type="rule" scop="root"` came out as `fun:type="rule" scop="root"` -
    the second attribute had no left token left inside its own run. So every
    protected run is first collapsed to ONE sentinel, the rewrite runs over the
    whole line with that sentinel acting as a left token, and the protected runs
    are put back afterwards in order. The payload is never inspected.
    """
    segs = CC.segments(fix_for_scope(text))
    s = "".join(run if kind == "code" else SENT for kind, run in segs)
    s = _colonise(s)
    back = [run for kind, run in segs if kind != "code"]
    out, i = [], 0
    for ch in s:
        if ch == SENT:
            out.append(back[i])
            i += 1
        else:
            out.append(ch)
    return "".join(out)


def split_head_desc(line):
    """a master row is `*-> head - desc`; only the head is code"""
    if not RX_OBJ.match(line):
        return line, False
    m = re.match(r'^(\s*\*->\s*.+?)\s+-\s+(.*)$', line)
    return (m.group(1), True) if m else (line, False)


def is_code_line(path, ln, fenced):
    if RX_FENCE.match(ln):
        return False
    if fenced:
        return True
    if path.endswith((".md", ".MD")):
        if (RX_BULLET.match(ln) or RX_TABLE.match(ln)) and not RX_OBJ.match(ln):
            return False
        return bool(RX_VIBE.search(ln))
    return bool(RX_EXM.match(ln) or RX_OBJ.match(ln) or ln.startswith((" ", "\t")))


def rewrite(rel, show):
    path = os.path.join(ROOT, rel)
    raw = io.open(path, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    lines = raw.replace("\r\n", "\n").split("\n")
    fenced = False
    changed = []
    for i, ln in enumerate(lines):
        if RX_FENCE.match(ln):
            fenced = not fenced
            continue
        if not is_code_line(rel, ln, fenced):
            continue
        head, is_obj = split_head_desc(ln)
        body = head if is_obj else ln
        new = convert_code(body)
        if new == body:
            continue
        lines[i] = (new + ln[len(head):]) if is_obj else new
        changed.append(i)
    if changed and show:
        print("=" * 100)
        print(rel)
        print("=" * 100)
        for i in changed:
            print("  БЫЛО : %s" % lines[i].replace(
                ln_cache[(rel, i)], "@@", 1) if False else "")
        print()
    return raw, crlf, lines, changed


ln_cache = {}


def main(argv):
    write = "--write" in argv
    fold_en = "--fold-english" in argv
    diff = "--diff" in argv
    # ONE definition of scope, shared with validator/spell_checker_v2.py. This
    # script used to carry its own list - DATA/, compiler/ and four root .md
    # files - which is how PY_IDE/window.vibe went unvisited while the gate,
    # reading the same rule through iter_targets(), reported 63 unfixed lines.
    # Two tools with two notions of scope is a silent hole.
    explicit = [a for a in argv[1:] if not a.startswith("-")]
    if explicit:
        targets = [a.replace("\\", "/") for a in explicit]
    else:
        targets = [rel_ for rel_, _p in iter_targets()]

    nfiles = nlines = 0
    rep_en = {"of": 0, "from": 0, "from_src": set()}
    for rel in targets:
        path = os.path.join(ROOT, rel)
        raw = io.open(path, encoding="utf-8-sig").read()
        before = raw.replace("\r\n", "\n").split("\n")
        crlf = "\r\n" in raw
        lines = list(before)
        fenced = False
        changed = []
        folded = 0
        for i, ln in enumerate(lines):
            if RX_FENCE.match(ln):
                fenced = not fenced
                continue
            if not is_code_line(rel, ln, fenced):
                continue
            head, is_obj = split_head_desc(ln)
            body = head if is_obj else ln
            new = convert_code(body)
            if fold_en:
                new2 = fold_english_in_scope(new, rep_en)
                if new2 != new:
                    folded += 1
                new = new2
            if new == body:
                continue
            lines[i] = (new + ln[len(head):]) if is_obj else new
            changed.append(i)
        if not changed:
            continue
        nfiles += 1
        nlines += len(changed)
        print("  %-34s %3d line(s)" % (rel, len(changed)))
        if diff:
            for i in changed:
                print("      БЫЛО : %s" % before[i].strip()[:92])
                print("      СТАЛО: %s" % lines[i].strip()[:92])
        if write:
            out = "\n".join(lines)
            io.open(path, "w", encoding="utf-8", newline="").write(
                out.replace("\n", "\r\n") if crlf else out)
    print()
    print("%s: %d file(s), %d line(s)"
          % ("WROTE" if write else ("DIFF" if diff else "DRY RUN"), nfiles, nlines))
    if fold_en:
        print("english fold: of=%d  from=%d  dropped sources: %s"
              % (rep_en["of"], rep_en["from"],
                 ", ".join(sorted(rep_en["from_src"])) or "none"))
    print("skipped (they document the rule, incl. the counter-example): %s"
          % ", ".join(DOCS_ABOUT_THE_RULE))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
