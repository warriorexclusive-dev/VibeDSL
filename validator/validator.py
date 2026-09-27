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
    __slots__ = ("text", "raw", "no", "indent", "children", "parent", "symbols", "block_syms", "missing_use", "abs_ids", "dup_ids")

    def __init__(self, text, no, indent, raw=None):
        self.text = text
        self.raw = raw if raw is not None else text
        self.no = no
        self.indent = indent
        self.children = []
        self.parent = None
        self.symbols = set()
        self.block_syms = set()
        self.missing_use = set()
        self.abs_ids = set()
        self.dup_ids = set()


def mask_lines(lines):
    """Blank out AI custom blocks { ... }, block comments /* ... */ and line
    comments // (quoted string contents are preserved). Content inside them must
    never be validated: {} = AI custom block, /* */ and // = human comments."""
    out = []
    in_custom = 0
    in_comment = False
    for raw in lines:
        s = raw
        n = len(s)
        i = 0
        res = []
        in_str = False
        while i < n:
            c = s[i]
            if in_comment:
                if c == "*" and i + 1 < n and s[i + 1] == "/":
                    in_comment = False
                    res.append("  ")
                    i += 2
                    continue
                res.append(" ")
                i += 1
                continue
            if in_custom:
                if c == "{":
                    in_custom += 1
                elif c == "}":
                    in_custom -= 1
                    if in_custom < 0:
                        in_custom = 0
                res.append(" ")
                i += 1
                continue
            if not in_str:
                if c == '"':
                    in_str = True
                    res.append(c)
                    i += 1
                    continue
                if c == "/" and i + 1 < n and s[i + 1] == "/":
                    break
                if c == "/" and i + 1 < n and s[i + 1] == "*":
                    in_comment = True
                    res.append("  ")
                    i += 2
                    continue
                if c == "{":
                    in_custom = 1
                    res.append(" ")
                    i += 1
                    continue
            else:
                if c == "\\" and i + 1 < n:
                    res.append(s[i])
                    res.append(s[i + 1])
                    i += 2
                    continue
                if c == '"':
                    in_str = False
                res.append(c)
                i += 1
                continue
            res.append(c)
            i += 1
        out.append("".join(res))
    return out


def build_tree(lines, raw_lines=None):
    root = Node(None, 0, -1)
    stack = [root]
    for no, raw in enumerate(lines, 1):
        norm = raw.replace("\t", "    ")
        text = norm.strip()
        if not text or text.startswith("#"):
            continue
        indent = len(norm) - len(norm.lstrip())
        src = raw_lines[no - 1] if raw_lines else raw
        node = Node(text, no, indent, src)
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
for fn in ("dictionary_sorted_by_type.txt", "syntax.txt"):
    KNOWN |= entry_aliases(os.path.join(DATA, fn))
KNOWN |= {"stage", "scop", "srch", "mix"}

# Words that are real functions (type:action). The `act=<verb>(...)` call slot
# must name one of these - being merely "known" is not enough, because `act=`
# declares a function, not a mapping, a field or an operator.
ACTIONS = set()
_cur = None
for _ln in io.open(os.path.join(DATA, "dictionary_sorted_by_type.txt"), encoding="utf-8").read().splitlines():
    if _ln.startswith("type:"):
        _cur = _ln[5:].strip().lower()
        continue
    if _cur == "action" and _ln.startswith("*-> "):
        for _n in _ln[4:].split(" - ", 1)[0].split(","):
            _n = _n.strip().lower()
            if _n:
                ACTIONS.add(_n)

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
    parse_abstract(entry_text, TYPE_SYMS, out)
    for inner in USE_CALL.findall(entry_text):
        for t in use_targets(inner):
            if t in seen:
                continue
            seen.add(t)
            if t in load_entries():
                USE_REACH.add(t)
                out.add(t)
                blueprint_symbols(load_entries()[t], seen, out)

RE_ABSTRACT = re.compile(r"\babstract\b[^\n]*?\bid=\"([^\"]+)\"|\babstract\b\s+\"([^\"]+)\"")
RE_AS = re.compile(r"\b(?:[,\s:(]as|:as|\bas)\s+([A-Za-z_]\w*)")
RE_FUN = re.compile(r"\bfun(?:ction)?\s+(?:id|name)=\"([^\"]+)\"")
RE_ENTITY_ACT = re.compile(r"^\s*(?:->|&->|<-|<->)?\s*(\w+):act(?:ion)?=\"[^\"]*\"\s*(?::\s*name=\"([^\"]+)\")?")
RE_COLON_BRANCH = re.compile(r"<>:|<>:\s*$")
RE_CMD_WORD = re.compile(r"(?:->|<->|<>:|&->|:|\\)\s*([A-Za-z_]\w*)|^\s*([A-Za-z_]\w*)\s*(?:\(|:|\\|$)")

ABSTRACT_TYPES = ("function", "prop", "item")
TYPE_SYMS = {}
USE_REACH = set()
DOC_SYMS = set()
RE_ACT_CALL = re.compile(r"\bact(?:ion)?\s*=\s*([A-Za-z_]\w*)\s*\(")
STD_FIELDS = {"name", "id", "desc", "value", "key", "src", "par", "text", "path", "data", "type"}


def parse_abstract(raw, typed, out):
    """Full abstract syntax (object spell-checker):
    abstract{description} function{type function,prop,item} id="X" {init in quotes} -> {logic}
    The type (a bare word function|prop|item and/or a comma list inside the brace
    block after 'function') names the in-memory dictionaries the checker must
    register into; quoted init registers compound pins id:name into the same
    dictionaries. Returns the declared id (or None) for uniqueness tracking."""
    m = re.search(r"\babstract\b", raw or "")
    if not m:
        return None
    seg = raw[m.start():]
    mid = re.search(r'\bid="([^"]+)"', seg)
    if not mid:
        return None
    aid = mid.group(1)
    types = []
    tm = re.search(r"\bfunction\b\s*\{([^}]*)\}", seg)
    if tm:
        for t in re.split(r"[\s,]+", tm.group(1).strip()):
            t = t.lower()
            if t in ABSTRACT_TYPES:
                types.append(t)
    for t in re.findall(r"\b(?:function|prop|item)\b", seg):
        types.append(t)
    if not types:
        types = ["item"]
    subs = []
    mim = re.search(r'\bid="[^"]+"\s*\{([^}]*)\}', seg)
    if mim:
        subs = re.findall(r'"([^"]+)"', mim.group(1))
    for t in types:
        d = typed.setdefault(t, set())
        d.add(aid)
        for s in subs:
            d.add(aid + ":" + s)
    out.add(aid)
    for s in subs:
        out.add(aid + ":" + s)
    return aid


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
                USE_REACH.add(t)
                node.symbols.add(t)
                blueprint_symbols(entries[t], seen, node.symbols)
            else:
                node.missing_use.add(t)
    for ch in node.children:
        resolve_uses(ch)


def collect_all(node):
    node.symbols = collect_decls(node.text or "")
    node.abs_ids = set()
    raw = node.raw or ""
    for mm in RE_ABSTRACT.finditer(raw):
        if mm.group(1):
            node.abs_ids.add(mm.group(1))
        if mm.group(2):
            node.abs_ids.add(mm.group(2))
    aid = parse_abstract(raw, TYPE_SYMS, node.symbols)
    if aid:
        node.abs_ids.add(aid)
    if re.match(r"^\s*&->", raw or ""):
        DOC_SYMS.update(node.symbols)
    resolve_uses(node)
    for ch in node.children:
        collect_all(ch)


def dup_check(root):
    """The spell-checker sees ids everywhere in files connected via use():
    an abstract id must not duplicate an id declared in the reachable base
    (or another line of the same spec) - the re-declaration is an error."""
    base = set(USE_REACH)
    for rid in USE_REACH:
        txt = ENTRIES.get(rid)
        if not txt:
            continue
        for mm in RE_ABSTRACT.finditer(txt):
            if mm.group(1):
                base.add(mm.group(1))
            if mm.group(2):
                base.add(mm.group(2))
        for mm in RE_FUN.finditer(txt):
            base.add(mm.group(1))
    visited = set()
    for nd in children_chain(root):
        for aid in nd.abs_ids:
            if aid in base or aid in visited:
                nd.dup_ids.add(aid)
            else:
                visited.add(aid)


def is_visible(node, sym):
    cur = node
    while cur is not None:
        if sym in cur.block_syms:
            return True
        cur = cur.parent
    return sym in DOC_SYMS


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


def object_sets():
    """Declared abstract ids and their owned compound pins, from the typed
    in-memory dictionaries (spec + reachable use() base)."""
    declared = set()
    owned = set()
    for d in TYPE_SYMS.values():
        for v in d:
            if ":" in v:
                owned.add(v)
            else:
                declared.add(v)
    return declared, owned


DECL_WORDS = ("prop", "function", "item")
RE_PIN = re.compile(r"(?<![:\w])([A-Za-z_]\w*):([A-Za-z_]\w*)")
# the placement chain of a declaration: -> obj : prop [: obj : prop ...]
RX_DECL_CHAIN = re.compile(
    r"->\s*[A-Za-z_]\w*(?::[A-Za-z_]\w*)*:(?:%s)(?::[A-Za-z_]\w*)*"
    % "|".join(DECL_WORDS))

# `- >` is not the arrow. The console lexer folds `->` into a single symbol, so
# this form is not something a person can type at all - which is exactly why it
# is a WARNING and not an error. Nobody commits it by hand, so if it is in a
# file, the text arrived from outside: a paste, a model, a generator. A lexer
# that only knows `->` will read `- >` as two legal tokens and continue
# nothing, and the chain quietly stops being a chain.
RE_BAD_ARROW = re.compile(r"-(?:\s+)>")
# `abstract function id="x"` - a type word joined by a SPACE where the grammar
# joins by a colon. `prop`, `function` and `item` are type markers, not
# objects: `abstract:prop:id="x"` is a declaration, `abstract function id="x"`
# is two bare words that happen to sit next to each other. A model writes both
# and the second one looks finished, so nothing complains and nothing is
# declared.
RE_TYPE_SPACE = re.compile(
    r"\b(abstract|use|root)\s+(prop|function|item)\b(?!\s*:)")
# `->` with nothing usable after it. After the arrow there must be an object or
# a condition; a dangling arrow is a chain that stops for no stated reason.
RE_DANGLING = re.compile(r"->\s*(?=$|[ \t]*(?:#|//|$))")
# a declared object immediately followed by a bare word, with no `:`. The
# author almost always meant obj:field; what they wrote may be two objects.
RE_NO_COLON = re.compile(r"\b([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\b")
RE_ACTION = re.compile(r'action="([^"]*)"')


def _keep_actions(text):
    """Blank every quoted span EXCEPT the payload of action="...".

    The checker used to blank all of them, which erased the one place obj:pin
    actually appears. What it was really reading was the incidental unquoted
    tail after the payload - a second copy of the same pins - so it passed for
    the wrong reason, and a typo written inside the action was invisible.
    """
    return RE_ACTION.sub(lambda m: " " + m.group(1) + " ", text)


def _code_text(text):
    """The code of a line: structure + action payload, prose blanked.

    Everything that checks the CONTENT of a line must scan this and not
    `text`. Two separate mistakes came from forgetting that: the pin checker
    blanked the action and read a copy of it, and the arrow check fired on
    `note="a - > b"`, a person writing a comparison in prose. One helper, so
    the two steps cannot be taken apart again.
    """
    return re.sub(r'"[^"]*"', '""', _keep_actions(text or ""))


def check_shape(node, text):
    """Three things a token-level grammar cannot see.

    A lexer that knows `->` will never notice `- >`: both are legal tokens. A
    grammar that reads `obj:field` will never notice `obj field`, because
    those are two ordinary words. And nothing at all notices a spec line that
    was never nested under an abstract - it parses fine as a top-level line
    and simply does nothing. All three are soft: each has a legitimate reading.
    """
    # Shape must be read on the RAW line. node.text arrives already masked:
    # mask_lines blanks whatever follows `->` inside a {...} payload, padding
    # it with spaces, so a shape check reading node.text sees every arrow
    # standing at the end of the line and calls all of them dangling. The rule
    # was firing on a truncation, not on a spec. build_tree kept the original
    # in node.raw; that is the line the author wrote.
    raw = getattr(node, "raw", None) or node.text or ""

    # Only where code is: the structural part of the line and the action
    # payload. `note="a - > b"` is a person writing a comparison in prose, and
    # a check that fires on it is worse than no check - the same mistake the
    # colon check made over `do:` blocks, 29 false positives at a time.
    code = _code_text(raw)
    for m in RE_BAD_ARROW.finditer(code):
        OUT.append((node.no, "W", "line %d: '%s' is not the arrow - the console folds `->` into one "
                    "symbol, so this line did not come from your keyboard: it was pasted or "
                    "generated, and here `->` reads as `-` then `>` and continues nothing"
                    % (node.no, m.group(0))))

    for m in RE_TYPE_SPACE.finditer(code):
        OUT.append((node.no, "E", "line %d: '%s %s' - a type word goes only after a colon: "
                    "write %s:%s: - a space here reads as two bare words and declares nothing"
                    % (node.no, m.group(1), m.group(2), m.group(1), m.group(2))))

    for m in RE_DANGLING.finditer(code):
        OUT.append((node.no, "E", "line %d: `->` with nothing after it - after the arrow there "
                    "must be an object or a condition" % node.no))

    body = RX_DECL_CHAIN.sub(" ", _code_text(text))
    # root is Node(None, 0, -1): its .no is 0 and the -1 is its indent, so
    # asking "is this a top-level line" is `parent.parent is None` and nothing
    # else. Reading the wrong field made the whole check unreachable.
    if (node.parent is not None and node.parent.parent is None
            and RE_PIN.search(body) and "&->" not in text
            and not text.lstrip().startswith(("use(", "import("))):
        OUT.append((node.no, "W", "line %d: obj:pin at top level - it is parsed but belongs "
                    "under an abstract (no nesting, so it never runs)" % node.no))

    declared, _owned = object_sets()
    if not declared:
        return
    # Only the action payload is code. A `do:` block is prose, and prose is
    # full of word pairs - "left otkryta", "theme zadan" - that look exactly
    # like an object followed by a field and mean nothing of the kind.
    code = " ".join(RE_ACTION.findall(text))
    if not code:
        return
    for m in RE_NO_COLON.finditer(code):
        o, w = m.group(1), m.group(2)
        if (o in declared and w not in KNOWN and w not in STD_FIELDS
                and w not in declared and len(w) >= 3):
            OUT.append((node.no, "W", "line %d: '%s %s' has no `:` - this may be two different "
                        "objects; if you meant one, write %s:%s" % (node.no, o, w, o, w)))
            break



def check_pins(node, scan_text):
    """Object spell-checker: a compound obj:pin is allowed if the pin was
    declared for the object (abstract{...} init or obj:act name="...") or is a
    standard/dictionary field of the object (frm:name="x", frm name="x").
    Object-field association: standard fields never fire; a genuinely
    undeclared field on a declared object is a SOFT WARNING, not an error.

    The right-hand side of `->` in a declaration is the PLACEMENT chain, not a
    pin assignment:

        &-> abstract:prop:id="radius"->frm:prop:corner:prop

    `frm:prop` there means "a prop, placed on frm, inside corner" - it is not a
    field named `prop` on `frm`, so it must not be spell-checked as one. The
    chain is stripped before the pin scan, the same way quoted payload is, and
    only chains that end in a declaration word are stripped - a real pin after a
    declaration is still checked.
    """
    declared, owned = object_sets()
    if not declared:
        return
    text = scan_text or ""
    text = RX_DECL_CHAIN.sub(" ", text)
    sparse = _code_text(text)
    for m in RE_PIN.finditer(sparse):
        obj, pin = m.group(1), m.group(2)
        if pin in ("act", "action"):
            continue
        if pin in STD_FIELDS or pin in KNOWN or len(pin) < 2:
            continue
        if obj not in declared:
            continue
        # A pin that is ITSELF a declared abstract is a real name, not a typo.
        # `frm:corner` and `io:func` were being reported as undeclared fields
        # when corner and func are declared two lines above with id="corner" -
        # the checker could see the compound `frm:corner` in owned, but never
        # looked at the object vocabulary the spec had built for itself. Ten
        # warnings, one cause: it did not know what the spec had declared.
        if pin in declared:
            continue
        comp = obj + ":" + pin
        if comp in owned or is_visible(node, comp):
            continue
        OUT.append((node.no, "W", "line %d: field '%s' not declared for object '%s' (abstract init or %s:act name=...)" % (node.no, comp, obj, obj)))


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

    for _m in RE_ACT_CALL.finditer(re.sub(r'"[^"]*"', '""', text)):
        _v = _m.group(1).lower()
        if _v not in ACTIONS:
            OUT.append((node.no, "E", "line %d: action= verb '%s' is not a declared type:action word"
                        % (node.no, _v)))

    check_pins(node, scan_text)
    check_shape(node, text)

    depth = 0
    for ch, ch_line in block_lines(node):
        depth += ch_line.count("(") - ch_line.count(")")
        if depth < 0:
            OUT.append((ch.no, "E", "line %d: extra ) before its ( scope" % ch.no))
            depth = 0
    for t in node.missing_use:
        OUT.append((node.no, "E", "line %d: use(...) target %s not in base (protos.txt/blueprints.txt)" % (node.no, t)))
    for aid in node.dup_ids:
        OUT.append((node.no, "E", "line %d: id '%s' already defined (use base or duplicated)" % (node.no, aid)))
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
        TYPE_SYMS.clear()
        USE_REACH.clear()
        DOC_SYMS.clear()
        root = build_tree(mask_lines(text.splitlines()), text.splitlines())
        collect_all(root)
        dup_check(root)
        for ch in root.children:
            compute_blocks(ch)
        walk(root)
        print("== %s" % src)
        seen = set()
        errs = 0
        warns = 0
        for no, kind, msg in sorted(OUT):
            if msg in seen:
                continue
            seen.add(msg)
            print("  %s %s" % (kind, msg))
            if kind == "W":
                warns += 1
            else:
                errs += 1
        total_e += errs
        warn_txt = ", warnings=%d" % warns if warns else ""
        print("# verdict: %s (errors=%d%s)" % ("PASS" if errs == 0 else "FAIL", errs, warn_txt))
    return 0 if total_e == 0 else 1


if __name__ == "__main__":
    sys.exit(main())