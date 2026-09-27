import io
import re

P = "compiler/compile.py"
s = io.open(P, encoding="utf-8-sig").read()
crlf = "\r\n" in s
t = s.replace("\r\n", "\n")

RX_LOCAL = '''
# A name the spec declared for itself. Inside a paren it stays text: show(theme)
# refers to the prop this spec called theme, not to the base word theme, and the
# two are different things that happen to share a spelling. Outside the parens
# the word is the word and compiles, which is why this is scoped to 'paren' runs
# and not to the whole line.
RX_LOCAL_ID = re.compile(r'id="([^"]+)"')
RX_LOCAL_ABS = re.compile(r'abstract(?::\\w+)?"([^"]+)"')
RX_LOCAL_NAME = re.compile(r'\\bname="([^"]+)"')


def local_names(lines):
    """every identifier this spec claims, lowercased"""
    out = set()
    for ln in lines:
        for rx in (RX_LOCAL_ID, RX_LOCAL_ABS, RX_LOCAL_NAME):
            for m in rx.finditer(ln):
                out.add(m.group(1).lower())
    return frozenset(out)

'''

anchor = "def compile_line(line, sub, token_rx, stats, known=None, local=None):"
assert anchor in t
t = t.replace(anchor, RX_LOCAL.lstrip("\n") + "\n" + anchor, 1)

OLD = '''    # 2. compile the spec
    known = set(concept_of)
    code_lines = [compile_line(ln, sub, token_rx, stats, known) for ln in lines]'''
NEW = '''    # 2. compile the spec
    known = set(concept_of)
    local = local_names(lines)
    code_lines = [compile_line(ln, sub, token_rx, stats, known, local)
                  for ln in lines]'''
assert OLD in t
t = t.replace(OLD, NEW, 1)

OLD2 = '            block.append(compile_line(ln, sub, token_rx, stats, known))'
NEW2 = '            block.append(compile_line(ln, sub, token_rx, stats, known, local))'
assert OLD2 in t
t = t.replace(OLD2, NEW2, 1)

io.open(P, "w", encoding="utf-8", newline="").write(
    t.replace("\n", "\r\n") if crlf else t)
print("  local_names() добавлена, оба вызова передают local")
