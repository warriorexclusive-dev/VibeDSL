# VibeDSL validator v1 - structure + entity categories
import re, sys, io, os, argparse

BASE = os.path.dirname(os.path.abspath(__file__))
DICTSORTED = os.path.join(BASE, "..", "DATA", "dictionary_sorted_by_type.txt")
DICTRAW = os.path.join(BASE, "..", "DATA", "dictionary.txt")
BASE_PROTOS = os.path.join(BASE, "..", "DATA", "protos.txt")
BASE_BLUEPRINTS = os.path.join(BASE, "..", "DATA", "blueprints.txt")

MULTI_OP = ["<>:", "<-()", "()->", "<->", "&->", "<>=", "::point:", "<=>",
            "<=<", "|>", ":?", ":=", "<=", ">=", "!=", "==", "+=", "-=",
            "->", "<-", "<>", "||", "&&", "*?", "//"]
SINGLE_PUNCT = set(":;,()[]{}@~")
DECL = {"fun", "func", "function"}


class Category:
    def __init__(self):
        self.alias2cat = {}
        self.cat_names = []

    def load(self, path):
        lines = io.open(path, encoding="utf-8").read().splitlines()
        cur = None
        for ln in lines:
            s = ln.strip()
            if s.startswith("type:"):
                cur = s[len("type:"):].strip()
                if cur not in self.cat_names:
                    self.cat_names.append(cur)
            elif s.startswith("*->") and cur:
                head = s[3:].strip()
                m = re.match(r"^(.*?)\s+-\s?(.*)$", head, re.S)
                kws = (m.group(1) if m else head).strip()
                for a in re.split(r"[,\s]", kws):
                    a = a.strip().lower()
                    if a:
                        if a not in self.alias2cat:
                            self.alias2cat[a] = cur
        return len(self.alias2cat)

    def cat_of(self, tok):
        return self.alias2cat.get(tok.lower())


class Token:
    def __init__(self, kind, val, pos, line):
        self.kind = kind
        self.val = val
        self.pos = pos
        self.line = line
        self.cat = None
        self.issue = None


def tokenize(text):
    toks = []
    i, n = 0, len(text)
    line = 1
    while i < n:
        c = text[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if c in " \t\r":
            i += 1
            continue
        if c == "/" and text[i:i + 2] == "//":
            j = text.find("\n", i)
            toks.append(Token("hcomment", text[i:j if j != -1 else n], i, line))
            i = j if j != -1 else n
            continue
        if c == "/" and text[i:i + 2] == "/*":
            j = text.find("*/", i + 2)
            if j == -1:
                toks.append(Token("hcomment", text[i:n], i, line))
                toks[-1].issue = "error"
                i = n
            else:
                toks.append(Token("hcomment", text[i:j + 2], i, line))
                i = j + 2
            continue
        if c == "#":
            j = text.find("\n", i)
            toks.append(Token("hcomment", text[i:j if j != -1 else n], i, line))
            i = j if j != -1 else n
            continue
        if c == "{":
            j, depth = i + 1, 1
            while j < n and depth:
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                elif text[j] == "\n":
                    line += 1
                j += 1
            if depth:
                toks.append(Token("custom", text[i + 1:n], i, line))
                toks[-1].issue = "error"
            else:
                toks.append(Token("custom", text[i + 1:j - 1], i, line))
            i = j
            continue
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                if text[j] == "\n":
                    line += 1
                j += 1
            if j >= n:
                toks.append(Token("str", text[i + 1:j], i, line))
                toks[-1].issue = "error"
                i = j
            else:
                toks.append(Token("str", text[i + 1:j], i, line))
                i = j + 1
            continue
        if c.isdigit():
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] in "._"):
                if text[j] == "\n":
                    line += 1
                j += 1
            num = text[i:j].rstrip("._")
            toks.append(Token("num", num, i, line))
            i = j
            continue
        hit = None
        if c == "-" and text.startswith("-[", i):
            br = text.find("]", i + 2)
            if br != -1 and br + 1 < n and text[br + 1] == ">":
                op = text[i:br + 2]
                toks.append(Token("op", op, i, line))
                line += op.count("\n")
                i = br + 2
                continue
        for op in sorted(MULTI_OP, key=len, reverse=True):
            if text.startswith(op, i):
                hit = op
                break
        if hit:
            toks.append(Token("op", hit, i, line))
            i += len(hit)
            continue
        if c.isalpha() or c == "_":
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] in "_."):
                j += 1
            toks.append(Token("word", text[i:j], i, line))
            i = j
            continue
        if c in "+-*/%!|?~<>=&^\\":
            j = i + 1
            while j < n and text[j] in "+-*/%!|?~<>=&^":
                j += 1
            toks.append(Token("op", text[i:j], i, line))
            i = j
            continue
        if c in SINGLE_PUNCT:
            toks.append(Token("punct", c, i, line))
            i += 1
            continue
        toks.append(Token("other", c, i, line))
        toks[-1].issue = "error"
        i += 1
    return toks


def check_structure(toks):
    errors = []
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for t in toks:
        if t.kind == "punct" and t.val in "([{":
            stack.append((t, t.val))
        elif t.kind == "punct" and t.val in ")]}":
            if not stack or stack[-1][1] != pairs[t.val]:
                errors.append((t, t.val))
            else:
                stack.pop()
    for t, v in stack:
        errors.append((t, v))
    return errors


def scan_userdefs(toks):
    userdefs = {}
    body = set()
    sig = toks
    n = len(sig)
    i = 0
    while i < n:
        t = sig[i]
        if t.kind == "word" and t.val.lower() == "alias":
            j = i + 1
            while j < n and not (sig[j].kind == "punct" and sig[j].val == "]"):
                j += 1
            j += 1
            while j < n and not (sig[j].kind == "word" and sig[j].val.lower() == "as"):
                j += 1
            if j + 1 < n and sig[j + 1].kind == "word":
                userdefs[sig[j + 1].val.lower()] = "useralias"
        elif t.kind == "word" and t.val.lower() == "abstract":
            j = i + 1
            if (j + 2 < n and sig[j].kind == "word" and sig[j].val.lower() == "name"
                    and sig[j + 1].kind == "op" and sig[j + 1].val == "="
                    and sig[j + 2].kind == "str"):
                nm = sig[j + 2].val
                userdefs[nm.lower()] = "userabstract"
                for k in range(j + 3, n):
                    if sig[k].kind == "word" and sig[k].line == sig[j + 2].line:
                        body.add((sig[k].line, sig[k].pos))
        i += 1
    return userdefs, body


def rule_checks(toks, text, cat):
    out = []
    sig = [t for t in toks if t.kind != "hcomment"]
    depth_p = depth_b = 0
    header_lines = set()
    for li, ln in enumerate(text.splitlines()):
        if ln.strip().startswith("*->"):
            header_lines.add(li)
    for idx, t in enumerate(sig):
        if t.kind == "punct":
            if t.val == "(":
                depth_p += 1
            elif t.val == ")":
                depth_p = max(0, depth_p - 1)
            elif t.val == "[":
                depth_b += 1
            elif t.val == "]":
                depth_b = max(0, depth_b - 1)
        if t.kind != "word":
            continue
        if t.line - 1 in header_lines:
            continue
        low = t.val.lower()
        c = cat.cat_of(low)
        if low in DECL:
            if idx + 1 >= len(sig):
                out.append("declaration '%s' has no target after it" % t.val)
                continue
            nx = sig[idx + 1]
            gap = text[t.pos + len(t.val): nx.pos]
            if nx.kind == "other":
                continue
            if not re.search(r"\s", gap):
                out.append("declaration '%s' must be followed by a space" % t.val)
            continue
        if c == "action" and depth_p == 0 and depth_b == 0:
            nx = sig[idx + 1] if idx + 1 < len(sig) else None
            prev = sig[idx - 1] if idx > 0 else None
            vn = nx.val if nx else None
            vp = prev.val if prev else None
            # attribute form:  action = value  (metadata, not a call)
            if vn in ("=", "=="):
                continue
            # filter composition:  crt\show(...)  /  list\users  (logic filter operator)
            if vn == "\\":
                continue
            # scope form:  action(...)
            if vn == "(":
                continue
            # compact mapping form:  action:value   (property operator)
            if vn == ":":
                continue
            # value/argument list position
            if prev is not None and prev.kind in ("punct", "op") and vp in ("(", "[", ",", "]", "=", ":", ")"):
                continue
            # property-key position: preceded by a word (usr apr, file save)
            if prev is not None and prev.kind == "word":
                continue
            # after a quoted value / number: a fresh expression starts (prose follows examples)
            if prev is not None and prev.kind in ("str", "num"):
                continue
            if vp in ("->", "<-", "<->", "|", "!", "<>", "<>:", ";"):
                pass
            out.append("action '%s' must declare scope '()'" % t.val)
        if c is None and depth_p == 0 and depth_b == 0:
            nx = sig[idx + 1] if idx + 1 < len(sig) else None
            prev = sig[idx - 1] if idx > 0 else None
            vn = nx.val if nx else None
            vp = prev.val if prev else None
            # unknown word in step position (after an arrow) is a call missing scope
            if prev is not None and prev.kind == "op" and vp in ("->", "<-", "<->", "<>:", "&->"):
                if vn in ("(", "[", "=", ":", "\\", "{", ";", ")", "]"):
                    continue
                if nx is not None and nx.kind == "word":
                    after = sig[idx + 2] if idx + 2 < len(sig) else None
                    # variable assignment form:  word word = ...   is not a call
                    if after is not None and after.val == "=":
                        continue
                    # prose annotation (one common logic, paths depend...) has no
                    # property tail; real broken form is  load view name="main"
                    eol = text.find("\n", t.pos)
                    tail = text[t.pos:eol if eol != -1 else len(text)]
                    if "=" not in tail:
                        continue
                    out.append("unknown word '%s' in step position looks like a call without scope: use %s(...)" % (t.val, t.val))
    return out


def load_base(path):
    """Parse DATA/protos.txt / DATA/blueprints.txt: return {id: full entry text}."""
    entries = {}
    cur_id = None
    buf = []
    for ln in io.open(path, encoding="utf-8").read().splitlines():
        if ln.strip().startswith("*->"):
            if cur_id is not None:
                entries[cur_id] = "\n".join(buf)
            m = re.search(r'\bid="([^"]+)"', ln)
            cur_id = m.group(1) if m else None
            buf = [ln]
        else:
            buf.append(ln)
    if cur_id is not None:
        entries[cur_id] = "\n".join(buf)
    return entries


def scan_acts(toks):
    """Collect declared functions from the two canonical act forms:
    A: abstract "name" -> act="..."   (registers: name)
    B: entity:act="...":name="alias"  (registers: entity:alias)
    """
    acts = {}
    sig = [t for t in toks if t.kind != "hcomment"]
    n = len(sig)
    i = 0
    while i < n:
        t = sig[i]
        if t.kind == "word" and t.val.lower() == "abstract" and i + 1 < n:
            nx = sig[i + 1]
            name = None
            j = i + 2
            if nx.kind == "str":
                name = nx.val
            elif nx.kind == "word":
                name = nx.val
            if name:
                k = j
                while k + 2 < n and sig[k].line - t.line <= 4:
                    if (sig[k].kind == "op" and sig[k].val == "->" and
                            sig[k + 1].kind == "word" and sig[k + 1].val.lower() == "act" and
                            sig[k + 2].kind == "op" and sig[k + 2].val == "="):
                        acts[name.lower()] = "abstract act: %s" % name
                        break
                    k += 1
        if (t.kind == "word" and i + 3 < n and
                sig[i + 1].kind == "punct" and sig[i + 1].val == ":" and
                sig[i + 2].kind == "word" and sig[i + 2].val.lower() == "act" and
                sig[i + 3].kind == "op" and sig[i + 3].val == "="):
            entity = t.val.lower()
            alias = "act"
            k = i + 4
            if k < n and sig[k].kind == "str":
                k += 1
            if (k + 3 < n and sig[k].kind == "punct" and sig[k].val == ":" and
                    sig[k + 1].kind == "word" and sig[k + 1].val.lower() == "name" and
                    sig[k + 2].kind == "op" and sig[k + 2].val == "=" and
                    sig[k + 3].kind == "str"):
                alias = sig[k + 3].val.lower()
            acts[entity + ":" + alias] = "entity act: %s:%s" % (entity, alias)
        i += 1
    return acts


def asset_checks(toks, text, cat, userdefs, acts, abody, proto_ids, bp_ids):
    """Asset rules: every function call must be declared (dictionary / aliases /
    user abstract / act), and use(...) must resolve to a prototype/blueprint id.
    Only real code positions are checked: on `*-> KEY - description` entry lines
    the part after ` - ` is prose, not code."""
    out = []
    used = []
    sig = [t for t in toks if t.kind != "hcomment"]
    n = len(sig)
    line_zone = {}
    li = 0
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("*->"):
            i = ln.find(" - ")
            line_zone[li] = i if i >= 0 else None
        li += 1

    for idx, t in enumerate(sig):
        if t.kind != "word":
            continue
        low = t.val.lower()
        # tokens in the prose description of an entry line are not code
        z = line_zone.get(t.line - 1)
        if z is not None and t.pos >= z:
            continue
        nx = sig[idx + 1] if idx + 1 < n else None
        is_call = nx is not None and nx.kind == "punct" and nx.val == "("
        pv = sig[idx - 1] if idx > 0 else None
        bnd = (pv is None or (pv.kind == "op" and pv.val in ("->", "<-", "<->", ":-"))
               or (pv.kind == "punct" and pv.val in (":", ",", "(", ")", "{", ";", "]")))
        # locate the closing paren of this paren group (must close before EOL)
        close = None
        depth = 0
        for k in range(idx + 2, n):
            if sig[k].line > t.line:
                break
            if sig[k].kind == "punct" and sig[k].val == "(":
                depth += 1
            elif sig[k].kind == "punct" and sig[k].val == ")":
                if depth == 0:
                    close = k
                    break
                depth -= 1
        prose_trail = (close is not None and close + 1 < n and sig[close + 1].line == t.line
                       and sig[close + 1].kind == "word")
        code_site = bnd and close is not None and not prose_trail
        if is_call and low == "use":
            if not code_site:
                continue
            depth = 1
            j = idx + 2
            inner = []
            while j < n and depth:
                if sig[j].kind == "punct":
                    if sig[j].val == "(":
                        depth += 1
                    elif sig[j].val == ")":
                        depth -= 1
                        if depth == 0:
                            break
                if sig[j].kind == "word":
                    inner.append(sig[j].val.lower())
                j += 1
            hit = next((w for w in inner if w in proto_ids or w in bp_ids), None)
            if hit is None and not any(cat.cat_of(w) for w in inner):
                out.append("use(...) target %s not in base (DATA/protos.txt / DATA/blueprints.txt) "
                           "nor in dictionary" % inner)
            elif hit is not None:
                used.append(hit)
            continue
        if not is_call or not code_site:
            continue
        if low in DECL:
            continue
        if (t.line, t.pos) in abody:
            continue
        cat_ok = cat.cat_of(low) is not None
        if not cat_ok and idx >= 2 and sig[idx - 1].kind == "punct" and sig[idx - 1].val == ":" \
                and sig[idx - 2].kind == "word":
            composite = sig[idx - 2].val.lower() + ":" + low
            if composite in acts:
                continue
        if cat_ok or low in userdefs or low in acts:
            continue
        out.append("call to undeclared function '%s()' - declare it: "
                   "abstract \"%s\" -> act=\"...\" ; or %s:act=\"...\":name=\"%s\"; "
                   "or add the word to the base" % (t.val, low, low, low))
    return out, used


def main(argv):
    ap = argparse.ArgumentParser(description="VibeDSL validator v1")
    ap.add_argument("input", nargs="?",
                    help='inline VibeDSL line, or ".vibe"/".txt" file path; without arg reads stdin')
    ap.add_argument("--dict", default=None, help="path to dictionary (sorted) file")
    args = ap.parse_args(argv)

    cat = Category()
    dpath = args.dict or DICTSORTED
    if not os.path.exists(dpath):
        dpath = DICTRAW
    n = cat.load(dpath)
    print("# dictionary: %s (%d aliases; cats: %s)"
          % (os.path.basename(dpath), n, ", ".join(cat.cat_names)))

    protos = load_base(BASE_PROTOS) if os.path.exists(BASE_PROTOS) else {}
    blueprints = load_base(BASE_BLUEPRINTS) if os.path.exists(BASE_BLUEPRINTS) else {}
    print("# base: protos=%d blueprints=%d" % (len(protos), len(blueprints)))

    if args.input is None:
        text = sys.stdin.read()
        src = "<stdin>"
    elif os.path.exists(args.input):
        text = io.open(args.input, encoding="utf-8").read()
        src = args.input
    else:
        text = args.input
        src = "<line>"
    print("# source: %s" % src)

    toks = tokenize(text)
    errors = check_structure(toks)
    userdefs, abody = scan_userdefs(toks)
    for nm, kind in userdefs.items():
        print("  [user %s] %s (declared)" % (kind, nm))
    acts = scan_acts(toks)
    for nm, desc in acts.items():
        print("  [act] %s  (%s)" % (nm, desc))
    rerrs = rule_checks(toks, text, cat)
    proto_ids = set(protos)
    bp_ids = set(blueprints)
    aerrs, used = asset_checks(toks, text, cat, userdefs, acts, abody, proto_ids, bp_ids)

    base_errs = []
    visited = set()

    def check_base(name):
        if name in visited:
            return 0
        visited.add(name)
        block = protos.get(name) or blueprints.get(name)
        if block is None:
            return 0
        kind = "proto" if name in proto_ids else "blueprint"
        btoks = tokenize(block)
        berr = check_structure(btoks)
        bud, bab = scan_userdefs(btoks)
        bact = scan_acts(btoks)
        br = rule_checks(btoks, block, cat)
        be, bused = asset_checks(btoks, block, cat, bud, bact, bab, proto_ids, bp_ids)
        ne = (len(berr) + len(br) + len(be)
              + sum(1 for x in btoks if x.issue == "error"))
        for tt, v in berr:
            base_errs.append("  E [%s %s] unbalanced %r" % (kind, name, v))
        for m in br:
            base_errs.append("  E [%s %s] %s" % (kind, name, m))
        for m in be:
            base_errs.append("  E [%s %s] %s" % (kind, name, m))
        for u in bused:
            check_base(u)
        return ne

    used_base = 0
    for u in used:
        used_base += check_base(u)

    prev = None
    for t in toks:
        if t.issue == "error":
            if t.kind == "str":
                print("  E line %d pos %d: unterminated string literal" % (t.line, t.pos))
            elif t.kind == "custom":
                print("  E line %d pos %d: unbalanced custom block { ..." % (t.line, t.pos))
            elif t.kind == "hcomment":
                print("  E line %d pos %d: unterminated block comment /*" % (t.line, t.pos))
            else:
                print("  E line %d pos %d: unexpected char %r" % (t.line, t.pos, t.val))
            continue
        if t.kind == "hcomment":
            continue
        if t.kind == "custom":
            snippet = " ".join(t.val.split())
            print("  [AI custom] { %s }" % snippet[:80])
            continue
        if t.kind == "word":
            sl = t.val.lower()
            c = cat.cat_of(t.val)
            inbody = (t.line, t.pos) in abody
            ukind = userdefs.get(sl)
            if inbody:
                print("  [abstract body] %s" % t.val)
            elif c and sl in DECL:
                print("  [declaration] %s" % t.val)
            elif c:
                print("  [%s] %s" % (c, t.val))
            elif ukind:
                print("  [%s] %s" % (ukind, t.val))
            elif sl == "as":
                t.issue = "grammar"
                print("  [grammar] as")
            elif prev is not None and (prev.kind in ("op", "punct")) and prev.val == "=":
                t.issue = "warn:%s" % t.val
                print("  [?] %s   <- proper name: wrap value in quotes, e.g. name=\"%s\"" % (t.val, t.val))
            else:
                t.issue = "warn:%s" % t.val
                print("  [?] %s   <- not in dictionary (extension/property?)" % t.val)
        prev = t
    for t, v in errors:
        print("  E line %d pos %d: unbalanced %r" % (t.line, t.pos, v))
    for msg in rerrs:
        print("  E rule: %s" % msg)
    for msg in aerrs:
        print("  E asset: %s" % msg)
    for msg in base_errs:
        print(msg)
    if used:
        print("  [use] reads base entries: %s" % ", ".join(sorted(set(used))))

    nerr = (sum(1 for t in toks if t.issue == "error") + len(errors) + len(rerrs)
            + len(aerrs) + used_base)
    nwarn = sum(1 for t in toks if t.issue and t.issue.startswith("warn:"))
    verdict = "FAIL" if nerr else "PASS"
    print("# verdict: %s (errors=%d warnings=%d)" % (verdict, nerr, nwarn))
    return 1 if nerr else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))