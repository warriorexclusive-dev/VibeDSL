import io
import re

P = "compiler/compile.py"
s = io.open(P, encoding="utf-8-sig").read()
crlf = "\r\n" in s
t = s.replace("\r\n", "\n")

# ---- 1. segments(): () and [] produce a 'paren' run, not plain code ----------
OLD_STACK = '''        if stack:
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
            continue'''
NEW_STACK = '''        if stack:
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
            continue'''
assert OLD_STACK in t
t = t.replace(OLD_STACK, NEW_STACK, 1)

# the top-level opener: a paren starts a 'paren' run, a brace a 'keep' run
OLD_OPEN = '''        if ch == '"' or ch in OPEN_KEEP:
            flush("code")
            buf.append(ch)
            if ch == '"':
                quote = True
            else:
                stack.append(OPEN_KEEP[ch])
            i += 1
            continue'''
NEW_OPEN = '''        if ch == '"' or ch in OPEN_KEEP or ch in PARENS:
            flush("code")
            buf.append(ch)
            if ch == '"':
                quote = True
            elif ch in PARENS:
                parens.append(PARENS[ch])
            else:
                stack.append(OPEN_KEEP[ch])
            i += 1
            continue'''
assert OLD_OPEN in t
t = t.replace(OLD_OPEN, NEW_OPEN, 1)

# a closing paren ends the 'paren' run
OLD_APPEND = '''        buf.append(ch)
        i += 1
    flush("keep" if (stack or quote) else "code")'''
NEW_APPEND = '''        if parens and ch == parens[-1]:
            parens.pop()
            buf.append(ch)
            flush("paren")
            i += 1
            continue
        buf.append(ch)
        i += 1
    flush("keep" if (stack or quote) else ("paren" if parens else "code"))'''
assert OLD_APPEND in t
t = t.replace(OLD_APPEND, NEW_APPEND, 1)

# the paren stack itself
OLD_INIT = '''    out, buf = [], []
    stack = []
    quote = False'''
NEW_INIT = '''    out, buf = [], []
    stack = []
    parens = []
    quote = False'''
assert OLD_INIT in t
t = t.replace(OLD_INIT, NEW_INIT, 1)

OLD_KEEP = 'OPEN_KEEP = {"{": "}"}'
NEW_KEEP = ('OPEN_KEEP = {"{": "}"}\n'
            '# () and [] are compiled, but a name the spec declared for itself stays text\n'
            '# inside them: show(theme) is a reference to the prop called theme, not to the\n'
            '# word theme. Outside the parens both are the word, and both compile.\n'
            'PARENS = {"(": ")", "[": "]"}')
assert OLD_KEEP in t
t = t.replace(OLD_KEEP, NEW_KEEP, 1)

# ---- 2. compile_line(): a 'paren' run skips the spec's own names -------------
OLD_SIG = 'def compile_line(line, sub, token_rx, stats, known=None):'
NEW_SIG = 'def compile_line(line, sub, token_rx, stats, known=None, local=None):'
assert OLD_SIG in t
t = t.replace(OLD_SIG, NEW_SIG, 1)

OLD_KIND = '''    for kind, text in segments(line):
        if kind == "keep":
            out.append(text)
            continue'''
NEW_KIND = '''    local = local or frozenset()
    for kind, text in segments(line):
        if kind == "keep":
            out.append(text)
            continue
        in_paren = kind == "paren"'''
assert OLD_KIND in t
t = t.replace(OLD_KIND, NEW_KIND, 1)

OLD_REPL = '''        def repl(m):
            w = m.group(0)
            g = sub.get(w.lower())'''
NEW_REPL = '''        def repl(m):
            w = m.group(0)
            if in_paren and w.lower() in local:
                return w
            g = sub.get(w.lower())'''
assert OLD_REPL in t
t = t.replace(OLD_REPL, NEW_REPL, 1)

# an uncompiled local name is not an undefined word either
OLD_UNDEF = '''            if lw in sub:
                continue'''
NEW_UNDEF = '''            if lw in sub or (in_paren and lw in local):
                continue'''
assert OLD_UNDEF in t
t = t.replace(OLD_UNDEF, NEW_UNDEF, 1)

io.open(P, "w", encoding="utf-8", newline="").write(
    t.replace("\n", "\r\n") if crlf else t)
print("  segments(): () и [] дают 'paren'")
print("  compile_line(): 'paren' пропускает локальные имена")
