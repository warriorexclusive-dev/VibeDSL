#!/usr/bin/env python3
"""validator.py - search-command validator (v2, main).

Scans a VibeDSL spec as a 2D indentation tree (deeper indent = step down,
same indent = step sideways / scope end) and validates by command constructors:
- action(...): the opening ( must be closed before the indent returns to the
  command start level,
- <>: variant: following child lines must each carry -> ahead,
- \\( change operator must carry act="...",
- symbols: abstract id="..." builds objects you can extend with prop/fun,
  crt/.../as binds variables, fun name="..." declares functions; a name is
  flagged only when its declaration is not visible in the scope chain.
- use(...): keeps protos/blueprints loaded by id in memory as higher-level
  code chunks - their ids and declared symbols resolve in the importing scope.

Usage: py -X utf8 validator\\validator.py file.vibe [file2.vibe ...]
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "DATA"))

OUT = []


class Node:
    __slots__ = ("text", "no", "indent", "children", "parent", "symbols", "block_syms", "missing_use")

    def __init__(self, text, no, indent):
        self.text = text
        self.no = no
        self.indent = indent
        self.children = []
        self.parent = None
        self.symbols = set()
        self.block_syms = set()
        self.missing_use = set()


def build_tree(lines):
    root = Node(None, 0, -1)
    stack = [root]
    for no, raw in enumerate(lines, 1):
        norm = raw.replace("\t", "    ")
        text = norm.strip()
        if not text or text.startswith("#"):
            continue
        indent = len(norm) - len(norm.lstrip())
        node = Node(text, no, indent)
        while stack[-1].indent >= node.indent:
            stack.pop()
        node.parent = stack[-1]
        stack[-1].children.append(node)
        stack.append(node)
    return root


def entry_aliases(path):
    words = set()
    with io.open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.lstrip()
            if not ln.startswith("*->"):
                continue
            rest = re.sub(r"^\*->\s*", "", ln)
            head = rest.split(" - ", 1)[0] if " - " in rest else rest
            for part in head.split(","):
                part = part.strip()
                if part:
                    words.add(part)
                    words.add(part.lower())
    return words


KNOWN = set()
for fn in ("dictionary.txt", "syntax.txt"):
    KNOWN |= entry_aliases(os.path.join(DATA, fn))
KNOWN |= {"stage", "scop", "srch", "mix"}

ENTRIES = None
USE_CALL = re.compile(r"\buse\(([^)]*)\)")

_SKIP_USE = {
    "agent", "use", "proto", "blueprint", "rule", "type", "scop",
    "root", "src", "as", "dict", "name", "id", "incld", "act", "desc",
}


def load_entries():
    global ENTRIES
    if ENTRIES is None:
        ENTRIES = {}
        for fn in ("protos.txt", "blueprints.txt"):
            path = os.path.join(DATA, fn)
            try:
                lines = io.open(path, encoding="utf-8").read().splitlines()
            except IOError:
                continue
            cur, buf = None, []
            for ln in lines:
                if ln.lstrip().startswith("*->"):
                    if cur is not None:
                        ENTRIES[cur] = "\n".join(buf)
                    m = re.search(r'\bid="([^"]+)"', ln)
                    cur = m.group(1) if m else None
                    buf = [ln]
                elif cur is not None:
                    buf.append(ln)
            if cur is not None:
                ENTRIES[cur] = "\n".join(buf)
    return ENTRIES


def use_targets(inner):
    inner = inner.strip()
    if not inner or "agent" in inner.lower() or re.match(r"\buse\s+\w+\s+(?:src|name)=", inner):
        return ()
    m = re.match(r"VibeDSL:proto\[([^\]]*)\]", inner)
    if m:
        return tuple(t.strip() for t in m.group(1).split(",") if t.strip())
    mid = re.search(r'\bid="([^"]+)"', inner)
    if mid:
        return (mid.group(1),)
    return tuple(
        t for t in re.findall(r"[A-Za-z_]\w*", inner)
        if t.lower() not in _SKIP_USE
    )


def blueprint_symbols(entry_text, seen, out):
    out.update(collect_decls(entry_text))
    for inner in USE_CALL.findall(entry_text):
        for t in use_targets(inner):
            if t in seen:
                continue
            seen.add(t)
            if t in load_entries():
                out.add(t)
                blueprint_symbols(load_entries()[t], seen, out)

RE_ABSTRACT = re.compile(r"\babstract\b[^\n]*?\bid=\"([^\"]+)\"|\babstract\b\s+\"([^\"]+)\"")
RE_AS = re.compile(r"\b(?:[,\s:(]as|:as|\bas)\s+([A-Za-z_]\w*)")
RE_FUN = re.compile(r"\bfun(?:ction)?\s+(?:id|name)=\"([^\"]+)\"")
RE_ENTITY_ACT = re.compile(r"^\s*(\w+):act=\"[^\"]*\"\s*(?::\s*name=\"([^\"]+)\")?")
RE_COLON_BRANCH = re.compile(r"<>:|<>:\s*$")
RE_CMD_WORD = re.compile(r"(?:->|<->|<>:|&->|:|\\)\s*([A-Za-z_]\w*)|^\s*([A-Za-z_]\w*)\s*(?:\(|:|\\|$)")


def collect_decls(text):
    syms = set()
    for m in RE_ABSTRACT.finditer(text):
        if m.group(1):
            syms.add(m.group(1))
        if m.group(2):
            syms.add(m.group(2))
    for m in RE_AS.finditer(text):
        syms.add(m.group(1))
    for m in RE_FUN.finditer(text):
        syms.add(m.group(1))
    m = RE_ENTITY_ACT.match(text)
    if m:
        name = m.group(2) or m.group(1)
        syms.add(m.group(1) + ":" + name)
        syms.add(m.group(1))
    return syms


def children_chain(node, fn=None):
    chain = []
    for ch in node.children:
        chain.append(ch)
        if fn:
            fn(ch)
        chain.extend(children_chain(ch, fn))
    return chain


def block_lines(node):
    yield node, node.text
    for ch in children_chain(node):
        yield ch, ch.text


def compute_blocks(node):
    for ch in node.children:
        compute_blocks(ch)
    node.block_syms = set(node.symbols)
    for ch in node.children:
        node.block_syms |= ch.block_syms
    return node.block_syms


def resolve_uses(node):
    entries = load_entries()
    seen = set()
    for inner in USE_CALL.findall(node.text or ""):
        for t in use_targets(inner):
            if t in seen:
                continue
            seen.add(t)
            if t in entries:
                node.symbols.add(t)
                blueprint_symbols(entries[t], seen, node.symbols)
            else:
                node.missing_use.add(t)
    for ch in node.children:
        resolve_uses(ch)


def collect_all(node):
    node.symbols = collect_decls(node.text or "")
    resolve_uses(node)
    for ch in node.children:
        collect_all(ch)


def is_visible(node, sym):
    cur = node
    while cur is not None:
        if sym in cur.block_syms:
            return True
        cur = cur.parent
    return False


def command_words(text):
    text = re.sub(r'"[^"]*"', '""', text)
    used = set()
    for m in RE_CMD_WORD.finditer(text):
        if m.group(1):
            w = m.group(1)
            before = text[m.start() - 1] if m.start() > 0 else ""
            if before and (before.isalnum() or before in "_)]"):
                continue
        else:
            w = m.group(2)
        if w:
            used.add(w)
    return used


def check(node):
    text = node.text or ""

    if RE_COLON_BRANCH.search(text):
        kids = [ch.text for ch in node.children]
        if not kids:
            OUT.append((node.no, "E", "line %d: <>: must have indented variant lines below" % node.no))
        for ch in node.children:
            if not re.search(r"^\s*->", ch.text):
                OUT.append((ch.no, "E", "line %d: <>: variant child must start with -> ahead" % ch.no))
    if "\\(" in text and "act=" not in text and "action=" not in text:
        OUT.append((node.no, "E", "line %d: change operator \\( needs act= or action= inside" % node.no))

    if RE_COLON_BRANCH.search(node.parent.text or ""):
        scan_text = re.sub(r"^\s*->\s*\w+", "", text, count=1)
    else:
        scan_text = text

    for w in command_words(scan_text):
        if len(w) < 2 or w in KNOWN or w == "stage":
            continue
        if is_visible(node, w):
            continue
        OUT.append((node.no, "E", "line %d: unknown command word '%s' not declared in visible scope" % (node.no, w)))

    depth = 0
    for ch, ch_line in block_lines(node):
        depth += ch_line.count("(") - ch_line.count(")")
        if depth < 0:
            OUT.append((ch.no, "E", "line %d: extra ) before its ( scope" % ch.no))
            depth = 0
    for t in node.missing_use:
        OUT.append((node.no, "E", "line %d: use(...) target %s not in base (protos.txt/blueprints.txt)" % (node.no, t)))
    if depth:
        OUT.append((node.no, "E", "line %d: unclosed ( ... ) - scope must close before indent returns to command level" % node.no))


def walk(node):
    for ch in node.children:
        walk(ch)
    if node.parent is not None:
        check(node)


def main():
    if len(sys.argv) < 2:
        print("usage: py -X utf8 validator\\validator.py file.vibe")
        return 1
    total_e = 0
    for path in sys.argv[1:]:
        if os.path.exists(path):
            text = io.open(path, encoding="utf-8").read()
            src = os.path.basename(path)
        else:
            text = path
            src = "<line>"
        del OUT[:]
        root = build_tree(text.splitlines())
        collect_all(root)
        for ch in root.children:
            compute_blocks(ch)
        walk(root)
        print("== %s" % src)
        seen = set()
        for no, kind, msg in sorted(OUT):
            if msg in seen:
                continue
            seen.add(msg)
            print("  %s %s" % (kind, msg))
        errs = len(seen)
        total_e += errs
        print("# verdict: %s (errors=%d)" % ("PASS" if errs == 0 else "FAIL", errs))
    return 0 if total_e == 0 else 1


if __name__ == "__main__":
    sys.exit(main())