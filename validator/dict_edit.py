#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dict_edit.py - make one deliberate change to the word dictionary.

Everything the base dictionary is made of lives in two files that must agree:

    DATA/dictionary_sorted_by_type.txt   the master: what the words ARE
    compiler/symbols_map.txt             the mark table: which mark each gets

A concept is one `*-> word, alias, ... - meaning` block. Its mark lives in the
table under ONE of its words, so a rename that forgets the table leaves a
concept nothing can reach, and a split that forgets the master leaves two marks
claiming one meaning. Both happened; that is why this tool exists.

Nothing is guessed and nothing is edited twice:

    py -X utf8 validator\\dict_edit.py show <concept>
    py -X utf8 validator\\dict_edit.py expand <abbr>          # keep the full word
    py -X utf8 validator\\dict_edit.py drop <concept>         # remove it entirely
    py -X utf8 validator\\dict_edit.py split <c> <a> <b>     # one meaning, two marks
    py -X utf8 validator\\dict_edit.py head <c> <word>        # the full word leads
    py -X utf8 validator\\dict_edit.py move-mark <a> <b>      # hand a mark over
    py -X utf8 validator\\dict_edit.py reglyph <c> <U+XXXX>   # a different mark
    py -X utf8 validator\\dict_edit.py add <words> -d <desc> [--mark U+XXXX]
    py -X utf8 validator\\dict_edit.py verify

Every command PRINTS the exact change and writes nothing. Add --apply to commit;
today `reglyph` commits and refuses a codepoint that is already taken.

`drop`, `split`, `head` and `move-mark` are PLAN-ONLY on purpose. Each of them
needs a human-chosen description or a judgement about which meaning leads, and
a tool that guesses that is the tool this repository keeps having to catch.

After any --apply, re-run the gate: it re-sorts, re-splits, regenerates and
verifies the whole base.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
MASTER = os.path.join(ROOT, "DATA", "dictionary_sorted_by_type.txt")
SYM = os.path.join(ROOT, "compiler", "symbols_map.txt")
SPEC_EXT = (".vibe", ".vibedsl", ".spec")
POOL = ("abstracts.txt", "protos.txt", "blueprints.txt", "agents.txt")
SKIP_DIRS = {"temp", "GLOS", "node_modules", "__pycache__", ".git"}

RX_MASTER = re.compile(r"^\*->\s*(.+?)\s+-\s+(.*)$")
RX_WORD_OK = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
RX_SYM = re.compile(
    r"^(U\+\s*[0-9A-Fa-f]{4,6}(?:\+[0-9A-Fa-f]{4,6})*)(\s+)(\S+)(\s+)(\*->\s*)(.+?)(\s+-\s+)(.*)$")


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8", newline="").write(t)


def nl_of(p):
    return "\r\n" if "\r\n" in read(p) else "\n"


def load_master():
    """[(lineno, names, desc, block)] - a block is the entry plus its exm lines."""
    text = read(MASTER).replace("\r\n", "\n")
    lines = text.split("\n")
    blocks, cur = [], None
    for i, l in enumerate(lines):
        m = RX_MASTER.match(l.strip())
        if m:
            names = [x.strip() for x in m.group(1).split(",") if x.strip()]
            if cur:
                blocks.append(cur)
            cur = {"line": i + 1, "names": names, "desc": m.group(2).strip(), "lines": [i]}
        elif cur is not None and (l.strip().startswith("-> exm:") or l.strip() == ""):
            cur["lines"].append(i)
            if l.strip() == "":
                blocks.append(cur)
                cur = None
        else:
            if cur:
                blocks.append(cur)
            cur = None
    if cur:
        blocks.append(cur)
    return lines, blocks


def head_of(lines, blk):
    return RX_MASTER.match(lines[blk["lines"][0]].strip()).group(1).strip()


def write_master(lines, blocks):
    """rebuild the file from blocks, so an entry and its exm lines stay together"""
    out, done = [], set()
    for blk in blocks:
        for i in blk["lines"]:
            if i in done:
                continue
            out.append(lines[i])
            done.add(i)
    for i, l in enumerate(lines):
        if i not in done and l.strip() == "":
            continue
        if i not in done:
            out.append(l)
    return "\n".join(out)


def find(blocks, name):
    for b in blocks:
        if name in b["names"] or b["names"][0] == name:
            return b
    return None


def find_sym(sym_lines, word):
    """-> (index, match, heads). RX_SYM groups: 1 cp, 2 gap, 3 glyph, 4 gap,
    5 '*-> ', 6 heads, 7 separator, 8 meaning."""
    for i, l in enumerate(sym_lines):
        m = RX_SYM.match(l.rstrip())
        if not m:
            continue
        heads = [h.strip() for h in m.group(6).split(",")]
        if word in heads:
            return i, m, heads
    return None, None, None


def segments():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_cc", os.path.join(ROOT, "compiler", "compile.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.segments


def tok(w):
    return re.compile(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(w))


def rename_in_specs(word, new, seg):
    """code position only: quoted payload is never the compiler's business"""
    touched = []
    targets = []
    for base, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in sorted(fs):
            if f.endswith(SPEC_EXT) or (f in POOL and os.path.basename(base) == "DATA"):
                targets.append(os.path.join(base, f))
    rx = tok(word)
    for p in targets:
        t = read(p)
        out = []
        for line in t.split("\n"):
            body = line[:-1] if line.endswith("\r") else line
            trail = "\r" if line.endswith("\r") else ""
            parts = []
            for kind, chunk in seg(body):
                if kind == "code" and rx.search(chunk):
                    chunk = rx.sub(new, chunk)
                parts.append(chunk)
            out.append("".join(parts) + trail)
        nt = "\n".join(out)
        if nt != t:
            touched.append((p, len(rx.findall(t))))
    return touched


# ------------------------------------------------------------------ commands
def cmd_show(name):
    lines, blocks = load_master()
    blk = find(blocks, name)
    if not blk:
        print("нет концепта '%s'" % name)
        return 1
    sym = read(SYM).replace("\r\n", "\n").split("\n")
    print("master:%d  names=%s" % (blk["line"], blk["names"]))
    print("  desc: %s" % blk["desc"][:110])
    for w in blk["names"]:
        i, m, _ = find_sym(sym, w)
        print("  %-14s -> %s" % (w, ("%s %s" % (m.group(1), m.group(3))) if m else "нет своего знака (наследует)"))
    for i in blk["lines"][1:]:
        s = lines[i].strip()
        if s:
            print("  %s" % s[:104])
    return 0


def cmd_expand(abbr):
    """drop the abbreviation; the full word is the one already in the concept"""
    lines, blocks = load_master()
    blk = find(blocks, abbr)
    if not blk or abbr not in blk["names"]:
        print("'%s' не является именем концепта" % abbr)
        return 1
    rest = [n for n in blk["names"] if n != abbr]
    if not rest:
        print("'%s' - единственное имя концепта; используйте drop или rename" % abbr)
        return 1
    keep = max(rest, key=len)
    print("expand: %s -> оставить %s" % (blk["names"], keep))
    sym = read(SYM).replace("\r\n", "\n").split("\n")
    i, m, heads = find_sym(sym, abbr)
    if m:
        print("  таблица: голова %s -> %s (знак %s %s)"
              % (abbr, keep, m.group(1), m.group(3)))
    seg = segments()
    for p, n in rename_in_specs(abbr, keep, seg):
        print("  спеки: %s (%d)" % (os.path.relpath(p, ROOT), n))
    return 0


def cmd_drop(name):
    lines, blocks = load_master()
    blk = find(blocks, name)
    if not blk:
        print("нет концепта '%s'" % name)
        return 1
    print("drop: %s  (master:%d, строк %d)"
          % (blk["names"], blk["line"], len(blk["lines"])))
    sym = read(SYM).replace("\r\n", "\n").split("\n")
    for w in blk["names"]:
        i, m, _ = find_sym(sym, w)
        if m:
            print("  таблица:%d голова %s (знак %s) СТАНЕТ СВОБОДНЫМ"
                  % (i + 1, w, m.group(1)))
    for p, n in rename_in_specs(name, name, segments()):
        pass
    return 0


def cmd_split(concept, a, b):
    """one concept that ended up holding two marks becomes two concepts"""
    lines, blocks = load_master()
    blk = find(blocks, concept)
    if not blk:
        print("нет концепта '%s'" % concept)
        return 1
    sym = read(SYM).replace("\r\n", "\n").split("\n")
    ia, ma, _ = find_sym(sym, a)
    ib, mb, _ = find_sym(sym, b)
    if not ma or not mb:
        print("нужны оба имени в таблице со своими знаками: %s / %s" % (a, b))
        return 1
    print("split: %s -> два концепта" % blk["names"])
    print("  %-12s знак %s %s" % (a, ma.group(1), ma.group(3)))
    print("  %-12s знак %s %s" % (b, mb.group(1), mb.group(3)))
    print("  описания придется развести вручную: одна строка на оба")
    return 0


def cmd_head(concept, word):
    lines, blocks = load_master()
    blk = find(blocks, concept)
    if not blk or word not in blk["names"]:
        print("'%s' не входит в %s" % (word, blk["names"] if blk else concept))
        return 1
    rest = [n for n in blk["names"] if n != word]
    print("head: %s -> %s, %s" % (blk["names"], word, rest))
    print("  ВНИМАНИЕ: сортировка по головному имени может поехать -> sort_dict.py")
    return 0


def cmd_move_mark(frm, to):
    sym = read(SYM).replace("\r\n", "\n").split("\n")
    i, m, _ = find_sym(sym, frm)
    if not m:
        print("'%s' не владеет знаком" % frm)
        return 1
    print("move-mark: %s (%s %s) -> %s" % (frm, m.group(1), m.group(3), to))
    print("  строка таблицы:%d  '%s' больше не будет головой" % (i + 1, frm))
    return 0


def cmd_reglyph(concept, codepoint, apply=False):
    """give a concept a different mark. The mark is what the model reads, so a
    mark that suggests the wrong relation is a defect even with nothing wrong
    with the word - a round-tipped arrow reads as call-and-return, not as the
    point being aimed at."""
    lines, blocks = load_master()
    blk = find(blocks, concept)
    if not blk:
        print("нет концепта '%s'" % concept)
        return 1
    sym = read(SYM).replace("\r\n", "\n").split("\n")
    cp = codepoint.upper().replace("U+", "")
    holder = None
    for i, l in enumerate(sym):
        m = RX_SYM.match(l.rstrip())
        if not m:
            continue
        if m.group(1).upper().replace("U+", "") == cp:
            holder = (i + 1, m.group(6))
    if holder:
        print("  СТОП: U+%s уже занят - строка %d, голова '%s'" % (cp, holder[0], holder[1]))
        return 1
    i, m, _ = find_sym(sym, blk["names"][0])
    if not m:
        for w in blk["names"]:
            i, m, _ = find_sym(sym, w)
            if m:
                break
    if not m:
        print("  '%s' не владеет знаком: сначала move-mark" % concept)
        return 1
    old_cp, old_g = m.group(2), m.group(3)
    try:
        new_g = chr(int(cp, 16))
    except ValueError:
        print("  U+%s не кодовая точка" % cp)
        return 1
    print("reglyph: %s  %s %s -> U+%s %s" % (blk["names"][0], old_cp, old_g, cp, new_g))
    print("  таблица:%d  (%s -> %s, тот же смысл)" % (i + 1, old_g, new_g))
    print("  U+%s станет свободен" % old_cp)
    if not apply:
        print("  (только план; для записи добавьте --apply)")
        return 0
    sym[i] = RX_SYM.sub(lambda mm: "U+%s%s%s%s%s%s%s%s" % (
        cp, mm.group(2), new_g, mm.group(4), mm.group(5), mm.group(6),
        mm.group(7), mm.group(8)),
        sym[i].rstrip(), count=1)
    write(SYM, "\n".join(sym).replace("\n", nl_of(SYM)))
    print("  ЗАПИСАНО")
    return 0


def cmd_add(words, desc, mark=None):
    print("add: %s" % words)
    print("  desc: %s" % desc)
    print("  mark: %s" % (mark or "не задан - concept останется без знака"))
    print("  вставьте в правильную секцию мастера; sort_dict.py проверит порядок")
    return 0


def cmd_verify():
    sys.path.insert(0, os.path.join(ROOT, "compiler"))
    import importlib
    cc = importlib.import_module("compile")
    concepts, w2g, glyphs = cc.load_alias_to_glyph()[1:]
    _s, _n, amb = cc.build_substitution(*cc.load_alias_to_glyph())
    bad = 0
    owner = {}
    for prim, info in concepts.items():
        for n in info["names"]:
            owner.setdefault(n.lower(), []).append(prim)
    for w, prims in sorted(owner.items()):
        if len(prims) > 1:
            bad += 1
            print("  x слово '%s' в %d концептах: %s" % (w, len(prims), sorted(set(prims))))
    for prim, info in sorted(concepts.items()):
        own = {n: w2g[n.lower()] for n in info["names"] if n.lower() in w2g}
        if len(set(own.values())) > 1:
            bad += 1
            print("  x концепт '%s' несет %d знаков: %s"
                  % (prim, len(set(own.values())), own))
    for w in sorted(amb):
        bad += 1
        print("  x знак недостижим или противоречив: '%s'" % w)
    print("инварианты: %s   (%d концептов, %d слов, %d знаков)"
          % ("НАРУШЕНЫ" if bad else "ok", len(concepts), len(owner), len(glyphs)))
    return 1 if bad else 0


GONE = {
    "act": "action", "crt": "create", "chk": "check", "wrt": "write",
    "ret": "return", "req": "request", "rsn": "reason", "src": "source",
    "swt": "switch", "tab": "table", "len": "length", "sys": "system",
    "dir": "directory", "synt": "syntax", "stat": "static",
    "excpt": "exception", "exm": "example", "var": "variable",
    "env": "environment", "unk": "unknown", "targ": "target",
    "cname": "context:name", "basename": "context:name", "architect": "arc",
    "control": "controller", "depend": "dependency", "lower": "lowercase",
    "spec": "specfile", "vis": "graphics", "ch": "change", "inx": "index",
    "endp": "endpoint", "vld": "valid", "uniq": "unique", "thm": "theme",
    "except": None, "syntree": None,
}


def cmd_sweep(apply=False):
    """the master's own examples still teach words the base no longer has.

    Every `-> exm:` line is documentation the model reads, so a dangling word
    there teaches a dead word. Quoted text is left alone, exactly as the
    compiler leaves it alone.
    """
    seg = segments()
    text = read(MASTER).replace("\r\n", "\n")
    lines = text.split("\n")
    hits, changes = 0, 0
    for i, l in enumerate(lines):
        s = l.strip()
        if not s.startswith("-> exm:"):
            continue
        # the `-> exm:` marker is structure, not example text: `exm` is itself a
        # removed word, so segmenting the whole line would rewrite the marker of
        # all 300+ examples into `-> example:`
        indent = l[:len(l) - len(l.lstrip())]
        body = s[len("-> exm:"):]
        found = [w for w in GONE
                 if re.search(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(w), body)]
        if not found:
            continue
        hits += 1
        parts = []
        for kind, chunk in seg(body):
            if kind == "code":
                for w in found:
                    rep = GONE[w]
                    if not rep:
                        continue
                    rx = tok(w)
                    if rx.search(chunk):
                        chunk = rx.sub(rep, chunk)
            parts.append(chunk)
        new = "%s-> exm:%s" % (indent, "".join(parts))
        if new != l:
            changes += 1
            if hits <= 12 or apply:
                print("  %5d| %-12s| %s" % (i + 1, ",".join(found[:3]), new.strip()[:74]))
        if apply:
            lines[i] = new
    print("exm-строк со снятыми словами: %d, изменено: %d" % (hits, changes))
    if not apply:
        print("  (только план; показаны первые 12; для записи добавьте --apply)")
    else:
        write(MASTER, "\n".join(lines).replace("\n", nl_of(MASTER)))
        print("  ЗАПИСАНО")
    return 0


def cmd_merge(a, b, keep=None, apply=False):
    """fold concept A into concept B. One concept ends up with one mark, so the
    other's codepoint goes back on the shelf - and every use of the losing word
    has to move first, which is why the plan counts them."""
    lines, blocks = load_master()
    ba, bb = find(blocks, a), find(blocks, b)
    if not ba or not bb:
        print("нет концепта: %s" % (a if not ba else b))
        return 1
    if ba is bb:
        print("'%s' и '%s' - это уже один концепт" % (a, b))
        return 1
    ia, ma, _ = find_sym(read(SYM).replace("\r\n", "\n").split("\n"), ba["names"][0])
    ib, mb, _ = find_sym(read(SYM).replace("\r\n", "\n").split("\n"), bb["names"][0])
    print("merge: %s (%s) + %s (%s)" % (
        ba["names"], ("%s %s" % (ma.group(1), ma.group(3))) if ma else "без знака",
        bb["names"], ("%s %s" % (mb.group(1), mb.group(3))) if mb else "без знака"))
    print("  победитель: %s, его знак остаётся" % bb["names"][0])
    if ma:
        print("  освободится: U+%s %s" % (ma.group(1).replace("U+", ""), ma.group(3)))
    print("  описания надо слить вручную - это решение о смысле, не о формате")
    names = [x.strip() for x in keep.split(",")] if keep else bb["names"]
    # a word with a space, a slash or a dot in it is a path or a sentence, not a
    # word: ` temperature` would enter the master as its own token and the
    # compiler would never resolve it. Refuse rather than write a broken name.
    bad = [n for n in names if not RX_WORD_OK.match(n)]
    if bad:
        print("  СТОП: не слово: %s" % ", ".join(repr(n) for n in bad))
        return 1
    print("  итоговые слова: %s" % names)
    seg = segments()
    for w in ba["names"]:
        if w in names:
            continue
        hits = rename_in_specs(w, bb["names"][0], seg)
        print("  спеки: %s -> %s : %d файл(ов)" % (w, bb["names"][0], len(hits)))
    if not apply:
        print("  (только план; описание и exm правятся руками)")
        return 0
    return 1


def main(argv):
    a = [x for x in argv[1:] if not x.startswith("--")]
    if not a:
        print(__doc__)
        return 0
    cmd, rest = a[0], a[1:]
    if cmd == "verify":
        return cmd_verify()
    if cmd == "sweep":
        return cmd_sweep("--apply" in argv)
    if cmd == "merge":
        keep = argv[argv.index("--keep") + 1] if "--keep" in argv else None
        return cmd_merge(rest[0], rest[1], keep, "--apply" in argv)
    if cmd == "show":
        return cmd_show(rest[0])
    if cmd == "expand":
        return cmd_expand(rest[0])
    if cmd == "drop":
        return cmd_drop(rest[0])
    if cmd == "split":
        return cmd_split(rest[0], rest[1], rest[2])
    if cmd == "head":
        return cmd_head(rest[0], rest[1])
    if cmd == "move-mark":
        return cmd_move_mark(rest[0], rest[1])
    if cmd == "reglyph":
        return cmd_reglyph(rest[0], rest[1], "--apply" in argv)
    if cmd == "verify":
        return cmd_verify()
    print("неизвестная команда: %s" % cmd)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
