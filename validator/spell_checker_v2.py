#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validator/spell_checker_v2.py - one gate for the whole language base.

Every check here was, at some point, a thing that had to be run by hand and
whose failure was only found by reading output. This file makes them one
command with one verdict and one exit code.

    py -X utf8 validator\\spell_checker_v2.py            # check everything
    py -X utf8 validator\\spell_checker_v2.py --list     # what it checks
    py -X utf8 validator\\spell_checker_v2.py --fix      # apply safe fixes, then check
    py -X utf8 validator\\spell_checker_v2.py --only GLYPHS,SPELL
    py -X utf8 validator\\spell_checker_v2.py plan\\ide-spec.vibe   # limit to these

Exit 0 = every check passed. Exit 1 = at least one failed.

THE CHECKS
  ORDER      the master dictionary is in alias order          (sort_dict.py)
  SPLITS     the four category files match the master        (spellcheck.py)
  GLYPHS     G1-G8 on the mark table                         (glyphs.py, subprocess)
  HEADER     every slot compiler/header.txt asks for is known
  INHERIT    no implicit inheritance left in a code line      (explicit_inherit.py)
  CUT        no `;` inside `for(...)` - `;` cuts the context and the loop dies
  PROSE      the rewrite tool still leaves prose and payload alone
  SPELL      every spec passes the grammar                    (validator.py)
  SYMBOLS    every spec compiles, emits only known marks,
             and keeps its indentation byte for byte          (compiler/compile.py)
  TWICE      compiling an already-compiled file changes nothing

WHY IT IMPORTS AND DOES NOT REIMPLEMENT
  The first version of explicit_inherit.py had its own line scanner and turned
  `the structure: a deeper` into `the:structure: a deeper`. A second
  implementation of "what is code and what is payload" is a second chance at that
  bug. So every check here calls the module that already does the work. The only
  subprocess is glyphs.py, which executes at import and cannot be imported.
"""
import fnmatch
import io
import os
import re
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, os.pardir))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "compiler"))
sys.path.insert(0, os.path.join(ROOT, "ide"))

DATA = os.path.join(ROOT, "DATA")
COMPILER = os.path.join(ROOT, "compiler")
MASTER = os.path.join(DATA, "dictionary_sorted_by_type.txt")
SPLITS = ("action.dict", "mapping.dict", "operators.dict", "abstracts.txt")
SPEC_EXT = (".vibe", ".vibedsl", ".spec")
SKIP_DIRS = ("temp", ".git", "GLOS", "node_modules", "__pycache__", "temp")


class Result(object):
    def __init__(self, code, title):
        self.code = code
        self.title = title
        self.bad = []
        self.warn = []
        self.note = ""
        self.skipped = False

    @property
    def ok(self):
        return not self.bad and not self.skipped

    def fail(self, msg):
        self.bad.append(msg)

    def soft(self, msg):
        self.warn.append(msg)


def age_of(path):
    """seconds since the file was last written, or None"""
    try:
        return time.time() - os.path.getmtime(path)
    except OSError:
        return None


# Several models work on this repository at once and the work is partitioned
# between them. That is the POINT, not a problem to defend against: each model
# runs this gate over the WHOLE repository, so it finds the other models' errors
# too. An earlier version refused to touch a "hot" file younger than 180 s - that
# was protection, and it was wrong here, because it would have hidden exactly the
# in-flight work a cross-check is supposed to catch.
#
# What replaced it is INFORMATION, not a lock: every failure carries the age of
# its file, so a five-minute-old spec that is still being written reads differently
# from yesterday's spec nobody has touched. Judging that is the reader's job.
#
# --scope stays, but as a FOCUS flag for a quick targeted run - not as a safety
# boundary. Leaving it off is the normal, correct way to run this.
SCOPES = None


def scope_ok(relp, scopes):
    if not scopes:
        return True
    r = relp.replace("\\", "/")
    for s in scopes:
        s = s.replace("\\", "/").rstrip("/")
        if r == s or r.startswith(s + "/") or fnmatch.fnmatch(r, s):
            return True
    return False


def stamp(relp):
    """`path (4m ago)` - lets a reader tell in-flight work from abandoned work"""
    a = age_of(os.path.join(ROOT, relp))
    if a is None:
        return relp
    if a < 90:
        return "%s (%ds ago - likely still in progress)" % (relp, a)
    if a < 5400:
        return "%s (%dm ago)" % (relp, a // 60)
    if a < 172800:
        return "%s (%dh ago)" % (relp, a // 3600)
    return "%s (%dd ago)" % (relp, a // 86400)


def find_specs(only=None, scopes=None):
    out = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if f.endswith(SPEC_EXT):
                p = os.path.join(base, f)
                if not scope_ok(rel(p), scopes):
                    continue
                out.append(p)
    out.sort()
    if only:
        wanted = {os.path.normcase(os.path.abspath(p)) for p in only}
        out = [p for p in out if os.path.normcase(p) in wanted]
    return out


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


# ---------------------------------------------------------------- 1. ORDER
def chk_order(specs, fix):
    import sort_dict
    r = Result("ORDER", "master dictionary is in alias order")
    secs = sort_dict.split_sections(io.open(MASTER, encoding="utf-8").read())
    for header, pos, key, prev in sort_dict.report(secs):
        r.fail("%s at #%d: '%s' must come after '%s'" % (header, pos, key, prev))
    if r.ok:
        r.note = "%d sections" % len(secs)
    return r


# ---------------------------------------------------------------- 2. SPLITS
def chk_splits(specs, fix=False, scopes=None):
    """the four category files must be what spellcheck.py would write"""
    import spellcheck
    r = Result("SPLITS", "category splits match the master")
    text = io.open(MASTER, encoding="utf-8").read()
    blocks = spellcheck.split_blocks(text)
    merged = {}
    for name, filename in spellcheck.CASES:
        if name not in blocks:
            r.fail("no section '%s' in the master" % name)
            return r
        merged.setdefault(filename, []).append((name, blocks[name]))
    for filename, parts in merged.items():
        want = spellcheck.DICT_PREFIX + "".join(b for _, b in parts)
        path = os.path.join(DATA, filename)
        if fix:
            io.open(path, "w", encoding="utf-8", newline="").write(want)
        if not os.path.isfile(path):
            r.fail("%s missing" % filename)
            continue
        got = io.open(path, encoding="utf-8").read()
        if got.replace("\r\n", "\n") != want.replace("\r\n", "\n"):
            n = spellcheck.count_entries(want)
            r.fail("%s is stale (%d entries in the master, run --fix)" % (stamp("DATA/" + filename), n))
    if r.ok:
        r.note = "%d files, %d entries" % (len(merged), spellcheck.count_entries(text))
    return r


# ---------------------------------------------------------------- 3. GLYPHS
def chk_glyphs(specs, fix):
    r = Result("GLYPHS", "mark table invariants G1-G8")
    p = subprocess.run([sys.executable, "-X", "utf8",
                        os.path.join(HERE, "glyphs.py")],
                       capture_output=True, cwd=ROOT)
    out = p.stdout.decode("utf-8", "replace")
    for ln in out.splitlines():
        if "VIOLATION" in ln:
            code = ln.strip().split()[0]
            r.fail("%s violation(s) - run validator/glyphs.py" % code)
        if "rows " in ln and "distinct codepoints" in ln:
            r.note = ln.strip()
        if "warning(s)" in ln and ("CLEAN" in ln or "TOTAL" in ln):
            r.soft(ln.strip())
    if p.returncode not in (0, 1):
        r.fail("glyphs.py crashed: %s" % p.stderr.decode("utf-8", "replace")[:200])
    return r


# ---------------------------------------------------------------- DICT
# The gate proved order, splits, marks, prose and spelling, and still shipped a
# dictionary that contradicted itself four ways in one afternoon:
#   include,import,incld  -> the table gave one concept both U+2283 and U+2282
#   unknown,none,unk      -> the table gave one concept both U+2204 and U+2042
#   vis,UI in two concepts-> the second owned no mark and only added ambiguity
#   map,mapping           -> the abbreviation sat in the head, the full word behind it
# None of those is a formatting problem, so none of the twelve checks could see
# them. This one asks a different question: is the base consistent with ITSELF.
def _cons(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def _subseq(short, long):
    it = iter(long)
    return all(c in it for c in short)


def chk_dict(specs, fix):
    r = Result("DICT", "the dictionary does not contradict itself")
    sys.path.insert(0, os.path.join(ROOT, "compiler"))
    import importlib
    cc = importlib.import_module("compile")
    concepts, word_to_glyph, glyphs = cc.load_alias_to_glyph()[1:]
    _sub, _noglyph, ambiguous = cc.build_substitution(*cc.load_alias_to_glyph())

    # a) one word, one concept
    owner = {}
    for prim, info in concepts.items():
        for n in info["names"]:
            owner.setdefault(n.lower(), []).append(prim)
    for w, prims in sorted(owner.items()):
        if len(prims) > 1:
            r.fail("word '%s' is declared in %d concepts: %s"
                   % (w, len(prims), ", ".join(sorted(set(prims)))))

    # b) one concept, one mark - otherwise the mark is a coin flip
    for prim, info in sorted(concepts.items()):
        own = {n: word_to_glyph[n.lower()] for n in info["names"]
               if n.lower() in word_to_glyph}
        if len(set(own.values())) > 1:
            r.fail("concept '%s' carries %d marks: %s"
                   % (prim, len(set(own.values())),
                      ", ".join("%s=%s" % kv for kv in sorted(own.items()))))

    # c) no mark is unreachable
    for w in sorted(ambiguous):
        r.fail("mark unreachable or contradictory at '%s'" % w)

    # d) the head names the concept; an abbreviation never leads. `os, platform`
    #    is NOT this case: neither word is short for the other, `os` is simply
    #    the canonical name and `platform` a full-word synonym.
    for prim, info in sorted(concepts.items()):
        names = info["names"]
        if len(names) < 2:
            continue
        head = names[0]
        ch = _cons(head)
        for n in names[1:]:
            cn = _cons(n)
            if (len(n) > len(head) and len(ch) >= 2 and len(ch) < len(cn)
                    and _subseq(ch, cn)):
                r.fail("head '%s' abbreviates '%s' in {%s}: the full word leads"
                       % (head, n, ", ".join(names)))
                break

    # e) one word per concept: an abbreviation is a consonant skeleton of a
    #    longer word in the same concept, and the embedding reads it as the
    #    short one even when the mark says otherwise.
    for prim, info in sorted(concepts.items()):
        names = info["names"]
        for a in names:
            for w in names:
                if a == w:
                    continue
                ca, cw = _cons(a), _cons(w)
                if len(ca) >= 2 and len(ca) < len(cw) and _subseq(ca, cw):
                    r.fail("'%s' is an abbreviation of '%s' in {%s}: keep the full word"
                           % (a, w, ", ".join(names)))
                    break
            else:
                continue
            break

    # f) the head must not lie about what follows it. `*-> insert, - ...` reads
    #    as "and here is another alias" and then there is none: harmless to a
    #    reader who has the dictionary in context, a false signal to a fresh
    #    one, which is the only reader the base is written for.
    mpath = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")
    with io.open(mpath, encoding="utf-8-sig") as fh:
        for no, raw in enumerate(fh.read().replace("\r\n", "\n").split("\n"), 1):
            mm = re.match(r"^\*->\s*(.+?)\s+-\s+", raw.strip())
            if not mm:
                continue
            head = mm.group(1)
            why = []
            if head.rstrip().endswith(","):
                why.append("trailing comma promises an alias that is not there")
            if ",," in head:
                why.append("empty name between commas")
            elif any(p.strip() == "" for p in head.split(",")):
                why.append("empty name in the alias list")
            for w in why:
                r.fail("master:%d %s -> %s" % (no, w, head.strip()[:44]))

    # g) a punctuation name must be the ASCII spelling of the word it sits
    #    beside. RX_WORD only ever matches a leading letter, so `...` as a name
    #    of `any` was a promise the tokenizer cannot keep: the dictionary said
    #    `...` means the mark, the compiler could never produce it, and 0 specs
    #    used it. The ASCII forms below are the ones deliberately kept.
    PUNCT_OF_WORD = {"&&", "|", "!", ":point:"}
    RX_TOKENIZER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
    for prim, info in sorted(concepts.items()):
        names = info["names"]
        words = [n for n in names if RX_TOKENIZER.fullmatch(n)]
        punct = [n for n in names if not RX_TOKENIZER.fullmatch(n)]
        if not (words and punct):
            continue
        for p in punct:
            if p not in PUNCT_OF_WORD:
                r.fail("'%s' sits beside the word(s) %s but is not an ASCII form "
                       "of any of them, and the tokenizer can never match it"
                       % (p, "/".join(words)))

    r.note = "%d concept(s), %d word(s), %d mark(s)" % (
        len(concepts), len(owner), len(glyphs))
    return r

# ---------------------------------------------------------------- 4. HEADER
def chk_header(specs, fix):
    import compile as CC
    r = Result("HEADER", "header slots are all known")
    probe = {"BLOCK_RULES": "R", "BLOCK_DATA": "D", "BLOCK_CODE": "C",
             "ANCHOR": "A", "SOURCE": "S", "COUNT_MARKS": "0",
             "COUNT_TOTAL": "0", "COUNT_CONCEPTS": "0", "COUNT_DATA": "0"}
    try:
        lines = CC.load_header(probe)
    except SystemExit as e:
        r.fail(str(e))
        return r
    left = [s for s in CC.RX_SLOT.findall("\n".join(lines))]
    if left:
        r.fail("unfilled slot(s): %s" % ", ".join("@%s@" % s for s in left))
    if r.ok:
        r.note = "%d lines, %d slots" % (len(lines), len(probe))
    return r


# ---------------------------------------------------------------- 5. INHERIT
def chk_inherit(specs, fix=False, scopes=None):
    import explicit_inherit as EI
    r = Result("INHERIT", "no implicit inheritance in a code line")
    total = 0
    for rp, path in EI.iter_targets():
        raw = io.open(path, encoding="utf-8-sig").read()
        crlf = "\r\n" in raw
        lines = raw.replace("\r\n", "\n").split("\n")
        fenced = False
        dirty = 0
        for i, ln in enumerate(lines):
            if EI.RX_FENCE.match(ln):
                fenced = not fenced
                continue
            if not EI.is_code_line(rp, ln, fenced):
                continue
            head, is_obj = EI.split_head_desc(ln)
            body = head if is_obj else ln
            new = EI.convert_code(body)
            if new == body:
                continue
            dirty += 1
            if fix:
                lines[i] = (new + ln[len(head):]) if is_obj else new
        if dirty:
            total += dirty
            r.fail("%s: %d line(s) still use a space - run --fix" % (stamp(rp), dirty))
            if fix:
                out = "\n".join(lines)
                io.open(path, "w", encoding="utf-8", newline="").write(
                    out.replace("\n", "\r\n") if crlf else out)
    if r.ok:
        r.note = "0 of %d file(s)" % len(list(EI.iter_targets()))
    return r


# ---------------------------------------------------------------- 6. CUT
def chk_cut(specs, fix):
    r = Result("CUT", "no context cut `;` inside a for(...) clause list")
    import explicit_inherit as EI
    hits = []
    seen = set()
    pools = [(rel(p), p) for _rp, p in EI.iter_targets()]
    pools += [(rel(p), p) for p in find_specs()]
    for rp, p in pools:
        if p in seen:
            continue
        seen.add(p)
        fenced = False
        for i, ln in enumerate(io.open(p, encoding="utf-8-sig"), 1):
            if EI.RX_FENCE.match(ln):
                fenced = not fenced
                continue
            if "for(" not in ln or ";" not in ln:
                continue
            if p.lower().endswith((".md",)) and not EI.is_code_line(rp, ln, fenced):
                continue
            hits.append("%s:%d  %s" % (rp, i, ln.strip()[:70]))
    for h in hits:
        r.fail("`;` cuts the loop context: " + h)
    if r.ok:
        r.note = "0 occurrences in %d file(s)" % len(seen)
    return r


# ---------------------------------------------------------------- 6b. ENGLISH
# A model that cannot find the anchor writes the relation in English, because an
# English preposition after a noun is the most predictable continuation it has and
# a rare mark is not. Under load it drifts. So English in CODE position is a drift
# signal, not a style: it means an anchor is missing.
#
# This is a check, not a dictionary entry, and that is the whole point. A row in
# the master would make `of` LEGAL - and a legal `of` is free, so the model would
# use it forever. The words are absent from the base on purpose, so they stay
# visible here instead of becoming silently accepted.
#
# `act="..."` and `""` and `{}` are exempt: English is CORRECT in a description.
DRIFT = ("of", "from", "by", "at", "then", "are", "be", "with", "into")


def chk_english(specs, fix=False, scopes=None):
    import explicit_inherit as EI
    import compile as CC
    r = Result("ENGLISH", "no English relation words in code position")
    if not specs:
        r.skipped = True
        r.note = "no specs found"
        return r
    RX = {w: re.compile(r"(?<![A-Za-z0-9_:])" + w + r"(?![A-Za-z0-9_:])")
          for w in DRIFT}
    counts = {}
    for path in specs:
        for i, ln in enumerate(io.open(path, encoding="utf-8-sig"), 1):
            body = ln.split("//")[0]
            for run in EI.reachable_code(body):
                for w in DRIFT:
                    m = RX[w].search(run)
                    if m:
                        counts[w] = counts.get(w, 0) + 1
                        r.soft("%s: %d  `%s` in an action scope - the anchor is "
                               "missing (english is the cheap continuation, so it "
                               "drifts)" % (stamp(rel(path)), i, w))
                        break
    if counts:
        r.note = ", ".join("%s=%d" % (w, c) for w, c in sorted(counts.items()))
    elif r.ok:
        r.note = "0 in %d spec(s)" % len(specs)
    return r


# ---------------------------------------------------------------- 6c. BINDING
# The language binds to nothing, and TARGETING is not binding. Saying which
# platform you mean is a concept - `os, platform` both mean it, one mark - and
# belongs in the base. What must never enter the base is a platform MECHANISM:
# a bus, a runtime, an instruction set, a vendor part. Those are what the
# advanced interpreter binds, and the moment one becomes a concept the spec has
# to change when the target changes.
#
# A NOTE ON HONESTY, because this check got it wrong first: it was written as a
# denylist and then reported "0 platform-bound" as if the list were exhaustive.
# It was not. Asked about the word `platform`, I checked, and found `os` and
# `target` already in the base - both with marks - which the list had omitted
# because nobody thought of them. A denylist is incomplete by construction.
#
# So: this catches the obvious (a vendor, a bus, an API) and it is a TRAP, not a
# proof. It cannot tell you the base is free of platform detail. That is a review
# of all 337 concepts, not a regex.
PLATFORM_MECHANISM = re.compile(r"""(?i)\b(?:
    windows|linux|android|ios|macos|webos|qt|tkinter|pygame|electron
  | serial|usb|bluetooth|gpio|i2c|spi|uart|canbus|modbus|opcua|hmi|plc
  | printf|println|stdout|stderr|stdio
  | hbm|gpu|npu|vram|sram|ddr|simd|opencl|cuda|rocm
  | avr|esp32|esp8266|raspberry|arduino|microcontroller
  | golang|kotlin|swift|perl|ruby
)\b""", re.X)


def chk_binding(specs, fix=False, scopes=None):
    import compile as C
    r = Result("BINDING", "no platform MECHANISM became a base concept")
    _co, concepts, _w2g, glyphs = C.load_alias_to_glyph()
    for k, v in sorted(concepts.items()):
        if PLATFORM_MECHANISM.search(k):
            r.fail("'%s' is a platform mechanism and it is a dictionary concept "
                   "(section %s) - the target is the interpreter's business"
                   % (k, v["sec"]))
    for g, (word, _d) in sorted(glyphs.items()):
        if PLATFORM_MECHANISM.search(word):
            r.fail("mark %r is filed under '%s' - a spec must not have to change "
                   "when the target does" % (g, word))
    if r.ok:
        r.note = ("%d concept(s), %d mark(s); os/platform/target allowed as "
                  "targeting, not as mechanism" % (len(concepts), len(glyphs)))
        r.soft("this is a trap for the obvious, NOT a proof the base is clean - "
               "a denylist cannot be exhaustive. Review the concepts by eye.")
    return r


# ---------------------------------------------------------------- 7. PROSE
def chk_prose(specs, fix):
    """regression guard: the rewrite tool must not touch prose or payload.

    Both of these shipped as bugs once, in this order:
      `the structure: a deeper`   -> `the:structure: a deeper`
      `desc="... template: lang"`  -> the `:` inside the payload was consumed
    """
    import explicit_inherit as EI
    r = Result("PROSE", "the rewrite leaves prose, payload and blocks alone")
    cases = [
        ("  Indentation is the structure: a deeper indent is a child",
         "  Indentation is the structure: a deeper indent is a child",
         "english prose with a colon"),
        ('   desc="ready blueprint: lang, type and name" act=[crt]',
         '   desc="ready blueprint: lang, type and name":act=[crt]',
         'quoted payload byte-identical, chain after it made explicit'),
        ("-> exm: crt site lang=php logc={Mag, sklad 5}",
         "-> exm: crt site:lang=php:logc={Mag, sklad 5}",
         "free-form block kept, both attributes before it made explicit"),
        ('for(var i="a b";i<5;i=incr(1))',
         'for(var:i="a b":i<5:i=incr(1))',
         "quoted payload inside a for() clause list"),
    ]
    for src, want, why in cases:
        got = EI.convert_code(src)
        if got != want:
            r.fail("%s\n        want %r\n        got  %r" % (why, want, got))
    if r.ok:
        r.note = "%d regression cases" % len(cases)
    return r


# ---------------------------------------------------------------- 8. SPELL
def chk_spell(specs, fix):
    import validator as V
    r = Result("SPELL", "every spec passes the grammar")
    if not specs:
        r.skipped = True
        r.note = "no specs found"
        return r
    for path in specs:
        text = io.open(path, encoding="utf-8-sig").read()
        lines = text.replace("\r\n", "\n").split("\n")
        del V.OUT[:]
        V.TYPE_SYMS.clear()
        V.USE_REACH.clear()
        V.DOC_SYMS.clear()
        try:
            root = V.build_tree(V.mask_lines(lines), lines)
            V.collect_all(root)
            V.dup_check(root)
            for ch in root.children:
                V.compute_blocks(ch)
            V.walk(root)
        except Exception as e:                      # a crash is a failure, not a traceback
            r.fail("%s: validator crashed: %s: %s" % (rel(path), type(e).__name__, e))
            continue
        seen = set()
        for no, kind, msg in sorted(V.OUT):
            if msg in seen:
                continue
            seen.add(msg)
            # The validator emits kind "W" as a SOFT warning on purpose: an
            # undeclared field on a declared object is "W", and the verdict stays
            # PASS (errors=0, warnings=N) - see
            # DATA/create-specs-manual.txt:566 "МЯГКОЕ ПРЕДУПРЕЖДЕНИЕ (W), не
            # ошибка: verdict остаётся PASS при warnings>0". Counting those as
            # failures made this gate red on a file the language calls correct,
            # and put five warnings into the blessed baseline that never
            # belonged there.
            if kind == "W":
                r.soft("%s: %s" % (rel(path), msg))
            else:
                r.fail("%s: %s" % (rel(path), msg))
    if r.ok:
        r.note = "%d spec(s) PASS" % len(specs)
        if r.warn:
            r.note += ", %d warning(s)" % len(r.warn)
    return r


# ---------------------------------------------------------------- 9. SYMBOLS
def compile_to(path, out):
    p = subprocess.run([sys.executable, "-X", "utf8",
                        os.path.join(COMPILER, "compile.py"), path, "-o", out],
                       capture_output=True, cwd=ROOT)
    return p.stdout.decode("utf-8", "replace"), p.returncode


RX_LEAD = re.compile(r"^[ \t]*")


def split_blocks(path):
    L = io.open(path, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    ci = L.index("-----CODE-----")
    di = L.index("-----DATA-----")
    code = L[ci + 1:]
    if code and code[-1] == "":
        code = code[:-1]
    return L[:di], code


def chk_symbols(specs, fix):
    r = Result("SYMBOLS", "every spec compiles to known marks, tree intact")
    if not specs:
        r.skipped = True
        r.note = "no specs found"
        return r
    import compile as CC
    _co, _concepts, _w2g, glyphs = CC.load_alias_to_glyph()
    known = set(glyphs) | {CC.ANCHOR, CC.MULTIVEC}
    tmp = os.path.join(tempfile.gettempdir(), "sc2_sym.txt")
    for path in specs:
        out, code = compile_to(path, tmp)
        if code != 0:
            r.fail("%s: compile exit=%d\n        %s"
                   % (rel(path), code, out.strip().splitlines()[-1] if out.strip() else ""))
            continue
        if "FAIL: emitted a glyph that is not in" in out:
            r.fail("%s: %s" % (rel(path), [l for l in out.splitlines()
                                            if l.startswith("  FAIL")][0]))
        _rules, code_lines = split_blocks(tmp)
        for i, ln in enumerate(code_lines):
            for ch in ln:
                if ord(ch) > 0x2000 and ch not in known and not ch.isspace():
                    r.fail("%s line %d: unknown mark %r" % (rel(path), i + 1, ch))
                    break
        src = io.open(path, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
        if src and src[-1] == "":
            src = src[:-1]
        if len(src) != len(code_lines):
            r.fail("%s: %d lines in, %d lines out" % (rel(path), len(src), len(code_lines)))
            continue
        for i, (a, b) in enumerate(zip(src, code_lines)):
            if RX_LEAD.match(a).group(0) != RX_LEAD.match(b).group(0):
                r.fail("%s line %d: indentation changed %r -> %r"
                       % (rel(path), i + 1, RX_LEAD.match(a).group(0),
                          RX_LEAD.match(b).group(0)))
                break
    if os.path.exists(tmp):
        os.remove(tmp)
    if r.ok:
        r.note = "%d spec(s), tree and marks intact" % len(specs)
    return r


# ---------------------------------------------------------------- 10. TWICE
def chk_twice(specs, fix):
    """compiling an already-compiled file must change nothing"""
    r = Result("TWICE", "a compile is idempotent")
    pool = specs[:3] or find_specs()[:3]
    if not pool:
        r.skipped = True
        return r
    a = os.path.join(tempfile.gettempdir(), "sc2_a.txt")
    b = os.path.join(tempfile.gettempdir(), "sc2_b.txt")
    m = os.path.join(tempfile.gettempdir(), "sc2_mid.txt")
    for path in pool:
        compile_to(path, a)
        _rules, first = split_blocks(a)
        # feed the compiled tree back in as if it were the source
        io.open(m, "w", encoding="utf-8", newline="").write("\n".join(first) + "\n")
        compile_to(m, b)
        _r2, second = split_blocks(b)
        if len(first) != len(second):
            r.fail("%s: %d lines -> %d on recompile"
                   % (rel(path), len(first), len(second)))
            continue
        for i, (x, y) in enumerate(zip(first, second)):
            if x != y:
                r.fail("%s line %d changed on recompile:\n        %r\n        %r"
                       % (rel(path), i + 1, x.strip()[:70], y.strip()[:70]))
                break
    for f in (a, b, m):
        if os.path.exists(f):
            os.remove(f)
    if r.ok:
        r.note = "%d spec(s) stable" % len(pool)
    return r


def _call(fn, specs, fix, scopes):
    """INHERIT and SPLITS also take a scope; the rest do not."""
    import inspect
    if len(inspect.signature(fn).parameters) >= 3:
        return fn(specs, fix, scopes)
    return fn(specs, fix)


# ---------------------------------------------------------------- baseline
# The repo arrived with real debt: example/IDE/* uses action words that were
# never added to the master, PY_IDE/window.vibe uses fields nobody declared.
# A gate that is red on day one gets ignored, so known failures are BLESSED into
# a baseline file and only NEW ones fail the run. `--bless` rewrites it.
BASELINE = os.path.join(HERE, "spell_checker_v2.baseline.txt")


def load_baseline():
    if not os.path.isfile(BASELINE):
        return set()
    return {ln.strip() for ln in io.open(BASELINE, encoding="utf-8")
            if ln.strip() and not ln.startswith("#")}


def save_baseline(failures):
    io.open(BASELINE, "w", encoding="utf-8", newline="").write(
        "# known-failure baseline - regenerate with:\n"
        "#   py -X utf8 validator\\spell_checker_v2.py --bless\n"
        "# one failure per line; anything NOT listed here fails the run.\n"
        + "".join(f + "\n" for f in sorted(failures)))


# ---------------------------------------------------------------- report
CHECKS = [
    ("ORDER", "the master dictionary is in alias order", chk_order, False),
    ("SPLITS", "the four category files match the master", chk_splits, True),
    ("GLYPHS", "the mark table satisfies G1-G8", chk_glyphs, False),
    ("DICT", "the dictionary does not contradict itself", chk_dict, False),
    ("HEADER", "every slot header.txt asks for is known", chk_header, False),
    ("PROSE", "the rewrite tool still leaves prose and payload alone", chk_prose, False),
    ("INHERIT", "no implicit inheritance in a code line", chk_inherit, True),
    ("CUT", "no context cut `;` inside a for(...) clause list", chk_cut, False),
    ("ENGLISH", "no English relation words in code position", chk_english, False),
    ("BINDING", "no platform MECHANISM became a base concept", chk_binding, False),
    ("SPELL", "every spec passes the grammar", chk_spell, False),
    ("SYMBOLS", "every spec compiles to known marks, tree intact", chk_symbols, False),
    ("TWICE", "compiling an already-compiled file changes nothing", chk_twice, False),
]


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("-")]
    flags = {a for a in argv if a.startswith("-")}
    if "--list" in flags:
        print("checks in spell_checker_v2:")
        for code, title, _fn, fixable in CHECKS:
            print("  %-8s %-56s %s" % (code, title, "[--fix]" if fixable else ""))
        print()
        print("  --fix        apply the safe rewrites (SPLITS, INHERIT) then check")
        print("  --scope=A,B  only consider these paths - use it to stay inside your")
        print("               own area when several models work in parallel")
        print("  cross-model: the gate runs over the WHOLE repo on purpose, so it")
        print("              finds the other models' errors too. Each failure")
        print("              carries its file age, so in-flight work is visible.")
        print("  --bless      record current failures as the known baseline")
        print("  --only=A,B   run only these checks")
        return 0

    only = None
    scopes = None
    min_age = None
    for a in flags:
        if a.startswith("--only="):
            only = set(a.split("=", 1)[1].split(","))
        elif a.startswith("--scope="):
            scopes = [s for s in a.split("=", 1)[1].split(",") if s]

    fix = "--fix" in flags
    specs = find_specs(args or None)
    base = load_baseline()

    print("=" * 100)
    print("SPELL CHECKER V2   %s   %d spec(s) in scope   baseline: %d known failure(s)"
          % ("--fix" if fix else "check only", len(specs), len(base)))
    if scopes:
        print("scope: %s   (a FOCUS flag, not a boundary - omit it to cross-check)"
              % ", ".join(scopes))
    print("=" * 100)

    results = []
    for code, title, fn, _fixable in CHECKS:
        if only and code not in only:
            continue
        res = Result(code, title)
        try:
            res = _call(fn, specs, fix, scopes)
        except SystemExit as e:
            res = Result(code, title)
            res.fail("aborted: SystemExit(%s)" % e.code)
        except Exception as e:
            res = Result(code, title)
            res.fail("crashed: %s: %s" % (type(e).__name__, e))
        results.append(res)

    # In --fix mode the report must show the state AFTER the rewrite, not the
    # state that was found - otherwise a fixed run still prints FAIL and the
    # exit code lies. Only the fixable checks are re-run; they are the cheap ones.
    if fix:
        by_code = {c: f for c, _t, f, _x in CHECKS}
        for idx, res in enumerate(results):
            if res.bad and res.code in by_code:
                again = _call(by_code[res.code], specs, False, scopes)
                again.note = (again.note + "  [after --fix]").strip()
                results[idx] = again

    # split each result into known and new
    fresh, known = [], []
    for res in results:
        new = [b for b in res.bad if b not in base]
        kn = [b for b in res.bad if b in base]
        res.bad = new
        known.extend(kn)
    all_new = [b for r in results for b in r.bad]
    all_known = sorted(set(known))

    if "--bless" in flags:
        save_baseline(set(all_new) | set(all_known))
        print("  baseline written: %d known failure(s)" % len(set(all_new) | set(all_known)))
        print()
        return 0

    for res in results:
        mark = "SKIP" if res.skipped else ("PASS" if res.ok else "FAIL")
        print("  %-4s %-8s %-56s %s" % (mark, res.code, res.title, res.note))
        for w in res.warn:
            print("         ~ %s" % w)
        for b in res.bad[:10]:
            print("         x %s" % b)
        if len(res.bad) > 10:
            print("         x ... and %d more" % (len(res.bad) - 10))

    failed = [r for r in results if not r.ok and not r.skipped]
    print("-" * 100)
    print("VERDICT: %s   %d check(s) run, %d passed, %d failed, %d known failure(s) masked"
          % ("FAIL" if failed else "PASS",
             len([r for r in results if not r.skipped]),
             len([r for r in results if r.ok]),
             len(failed), len(all_known)))
    if failed:
        print("  failing: %s" % ", ".join(r.code for r in failed))
        print("  %d new failure(s). Fix, or --bless if they are pre-existing debt."
              % len(all_new))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
