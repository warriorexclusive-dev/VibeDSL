#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""expand_words.py - remove abbreviated aliases, keep the full word.

The language keeps ONE word per concept. Short forms (`crt`, `chk`, `excpt`)
are not free: two of them (`in`, `n`) open nine other concepts as a prefix,
and one (`except`) collides with a meaning every model already holds. The
dictionary therefore carries the full word only.

What changes per removed alias A of the full word F:

  master  `*-> F, A - desc`            -> `*-> F - desc`
  table   `U+XXXX g *-> A - desc`       -> `U+XXXX g *-> F - desc`   (same mark)
  specs   standalone A in code position -> F
  docs    standalone A in prose        -> F

Quoted payload is NEVER touched: the compiler does not resolve it, so neither
do we. `mapping` was removed the same way and moved 0 bytes of compiled text.

The map is FROZEN below. It is the source of truth, not the run order: the
same input always yields the same output, and a chunk can be replayed.

    py -X utf8 validator\\expand_words.py --plan          # report, change nothing
    py -X utf8 validator\\expand_words.py --apply         # rewrite
    py -X utf8 validator\\expand_words.py --verify        # assert the invariants
"""
import importlib.util
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
MASTER = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")
SYM = os.path.join(ROOT, "compiler", "symbols_map.txt")


def _compiler_segments():
    """the compiler's own code/keep splitter.

    Quoted payload is never rewritten, so the rename must not rewrite it
    either. Reusing compile.segments() keeps that promise mechanical instead
    of a second regex that would drift from the first.
    """
    spec = importlib.util.spec_from_file_location(
        "_cc", os.path.join(ROOT, "compiler", "compile.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.segments
SPEC_EXT = (".vibe", ".vibedsl", ".spec")
SKIP_DIRS = {"temp", "GLOS", "node_modules", "__pycache__", ".git"}

# FROZEN: abbreviation -> full word. Nothing enters this table at run time.
MAP = {
    "allw": "allow", "answ": "answer", "apr": "approve", "arc": "architecture",
    "arch": "architecture", "bhvr": "behavior", "brk": "break", "bsns": "business",
    "cch": "catch", "chk": "check", "cnv": "convert", "conf": "config",
    "cos": "cosine", "crit": "critical", "crt": "create", "ctx": "context",
    "del": "delete", "descr": "description", "dir": "directory", "els": "else",
    "endp": "endpoint", "env": "environment", "err": "error", "evt": "event",
    "excpt": "exception", "examp": "example", "exm": "example", "extn": "extension",
    "fbd": "forbidden", "fin": "finally", "fmt": "format", "frmwrk": "framework",
    "func": "function", "fun": "function", "inx": "index", "isol": "isolate",
    "landscp": "landscape", "len": "length", "locat": "location", "lst": "list",
    "mem": "memory", "mk": "make", "par": "param", "proc": "procedure",
    "req": "request", "reqred": "required", "respn": "response", "ret": "return",
    "rm": "remove", "rsn": "reason", "rvw": "review", "sin": "sinus",
    "skl": "skill", "src": "source", "stat": "static", "svc": "service",
    "swt": "switch", "synt": "syntax", "sys": "system", "tab": "table",
    "thm": "theme", "uniq": "unique", "unk": "unknown", "uper": "upercase",
    "var": "variable", "varn": "variant", "vld": "valid", "wrt": "write",
    "vis": "graphics", "map": None, "mapping": None, "except": None,
    "act": "action", "ch": "change", "control": "controller",
    "depend": "dependency", "lower": "lowercase", "spec": "specfile",
    "targ": "target", "architect": "arc",
}
# `map`, `mapping`, `except` were decided by hand and are already applied.

RX_MASTER = re.compile(r"^\*->\s*(.+?)\s+-\s+(.*)$")
RX_ENTRY = re.compile(r"^(\*->\s*)(.+?)(\s+-\s+)(.*)$")
RX_SYM = re.compile(r"^(U\+[0-9A-Fa-f]{4,6}(?:\+[0-9A-Fa-f]{4,6})*)\s+(\S+)\s+(\*->\s*)(\S+)(\s+-\s+)(.*)$")
def tok(word):
    """a standalone-token pattern: not glued to a letter, digit or underscore"""
    return re.compile(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(word))


def read(path):
    return io.open(path, encoding="utf-8").read()


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="").write(text)


def spec_files():
    for base, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in sorted(fs):
            if f.endswith(SPEC_EXT):
                yield os.path.join(base, f)


POOL = ("abstracts.txt", "protos.txt", "blueprints.txt", "agents.txt")


def doc_files():
    """prose only: .md. The .dict splits are generated from the master and the
    DATA/*.txt pool is compiled, so neither belongs here."""
    for base, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in sorted(fs):
            if f.endswith(".md"):
                yield os.path.join(base, f)


def pool_files():
    for f in POOL:
        p = os.path.join(ROOT, "DATA", f)
        if os.path.exists(p):
            yield p


def code_only(text, segments):
    """the CODE runs of a file, unchanged - counting must see the word as it is
    written today, not the word it is about to become."""
    out = []
    for line in text.split("\n"):
        for kind, chunk in segments(line.rstrip("\r")):
            if kind == "code":
                out.append(chunk)
    return "\n".join(out)


def plan():
    segments = _compiler_segments()
    master = read(MASTER).replace("\r\n", "\n").split("\n")
    sym = read(SYM).replace("\r\n", "\n").split("\n")
    specs = {p: code_only(read(p), segments)
             for p in list(spec_files()) + list(pool_files())}
    rows = []
    for a, f in sorted(MAP.items()):
        if f is None:
            continue
        rx = tok(a)
        m_hits = [i + 1 for i, l in enumerate(master) if RX_MASTER.match(l.strip())
                  and a in [x.strip() for x in RX_MASTER.match(l.strip()).group(1).split(",")]]
        t_hits = [i + 1 for i, l in enumerate(sym)
                  if RX_SYM.match(l) and a in [h.strip() for h in RX_SYM.match(l).group(4).split(",")]]
        s_hits = {p: len(rx.findall(t)) for p, t in specs.items() if rx.search(t)}
        d_hits = {p: len(rx.findall(t)) for p, t in docs_plain().items() if rx.search(t)}
        rows.append((a, f, m_hits, t_hits, s_hits, d_hits))
    return rows


def docs_plain():
    return {p: read(p) for p in doc_files()}


def show(rows):
    tm = tt = ts = td = 0
    print("%-9s -> %-13s %4s %4s %5s %5s" % ("abbr", "full", "mast", "tabl", "spec", "docs"))
    for a, f, m, t, s, d in rows:
        ns = sum(s.values()); nd = sum(d.values())
        tm += len(m); tt += len(t); ts += ns; td += nd
        print("%-9s -> %-13s %4d %4d %5d %5d  %s" % (
            a, f, len(m), len(t), ns, nd,
            ", ".join("%s:%d" % (os.path.basename(p), c) for p, c in sorted(s.items())) or "-"))
    print("-" * 74)
    print("ИТОГО: concepts=%d table=%d spec=%d docs=%d" % (tm, tt, ts, td))
    return ts


def rename_code(text, segments):
    """expand abbreviations in CODE position only, leaving payload alone."""
    nl = "\r\n" if "\r\n" in text else "\n"
    out = []
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        parts = []
        for kind, chunk in segments(line):
            if kind == "code":
                for a, f in sorted(MAP.items()):
                    if f is None:
                        continue
                    rx = tok(a)
                    if rx.search(chunk):
                        chunk = rx.sub(f, chunk)
            parts.append(chunk)
        out.append("".join(parts))
    return nl.join(out)


def rename_prose(text):
    """docs describe the language, so their word list must follow the rename."""
    for a, f in sorted(MAP.items()):
        if f is None:
            continue
        rx = tok(a)
        if rx.search(text):
            text = rx.sub(f, text)
    return text


def apply():
    segments = _compiler_segments()
    master = read(MASTER).replace("\r\n", "\n").split("\n")
    sym = read(SYM).replace("\r\n", "\n").split("\n")
    changed_m = changed_t = 0
    for a, f in sorted(MAP.items()):
        if f is None:
            continue
        for i, l in enumerate(master):
            m = RX_MASTER.match(l.strip())
            if not m:
                continue
            names = [x.strip() for x in m.group(1).split(",")]
            if a not in names or f not in names:
                continue
            keep = [n for n in names if n != a]
            head = keep[0]
            master[i] = "*-> %s - %s" % (", ".join(keep), m.group(2)) if len(keep) > 1 \
                else "*-> %s - %s" % (head, m.group(2))
            changed_m += 1
        for i, l in enumerate(sym):
            m = RX_SYM.match(l)
            if not m:
                continue
            # a table head may list several words: `landscp, landscape`
            heads = [h.strip() for h in m.group(4).split(",")]
            if a not in heads:
                continue
            rest = [h for h in heads if h != a]
            head = rest[0] if rest else f
            pad = m.group(5)
            sym[i] = "%s %s %s%s%s%s" % (m.group(1), m.group(2), m.group(3),
                                         head.ljust(len(pad) - 3), pad, m.group(6))
            changed_t += 1
    write(MASTER, "\n".join(master).replace("\n", "\r\n"))
    write(SYM, "\n".join(sym).replace("\n", "\r\n"))
    ns = nd = np = 0
    for p in list(spec_files()) + list(pool_files()):
        t = read(p)
        o = t
        t = rename_code(t, segments)
        if t != o:
            write(p, t)
            if p.endswith(".md"):
                nd += 1
            elif os.path.basename(p) in POOL:
                np += 1
            else:
                ns += 1
    for p in doc_files():
        t = read(p)
        o = t
        t = rename_prose(t)
        if t != o:
            write(p, t)
            nd += 1
    print("master=%d table=%d specs=%d pool=%d docs=%d" % (changed_m, changed_t, ns, np, nd))


def verify():
    master = read(MASTER)
    sym = read(SYM)
    bad = []
    for a, f in sorted(MAP.items()):
        if f is None:
            continue
        for i, l in enumerate(master.replace("\r\n", "\n").split("\n"), 1):
            m = RX_MASTER.match(l.strip())
            if m and a in [x.strip() for x in m.group(1).split(",")]:
                bad.append("master:%d still lists %s" % (i, a))
        for i, l in enumerate(sym.replace("\r\n", "\n").split("\n"), 1):
            m = RX_SYM.match(l)
            if m and a in [h.strip() for h in m.group(4).split(",")]:
                bad.append("table:%d still filed under %s" % (i, a))
    for b in bad:
        print("  x " + b)
    print("инварианты: %s" % ("НАРУШЕНЫ" if bad else "ok"))
    return 1 if bad else 0


if __name__ == "__main__":
    if "--plan" in sys.argv:
        show(plan())
    elif "--apply" in sys.argv:
        apply()
    elif "--verify" in sys.argv:
        sys.exit(verify())
    else:
        print(__doc__)
