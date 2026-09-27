import io
import re

P = "validator/validator.py"
s = io.open(P, encoding="utf-8-sig").read()
crlf = "\r\n" in s
t = s.replace("\r\n", "\n")

CHECK = '''
# An id may not take a name the base already explains, and may not repeat.
# 27 declarations in PY_IDE/window.vibe did the first thing - view, theme, text,
# frm, left and 23 more - and it is the same collision as goal and col: the spec
# claims a word that has a mark and a definition, and from then on `theme` means
# two things. It also cost the compiler: a locally claimed name has to be spared
# from compiling, so show(theme) stopped being a mark until the claim went.
RX_ID = re.compile(r'\\bid="([^"]+)"')
RX_PARAM = re.compile(r'->param=([A-Za-z_]\\w*)')
RX_BASIS = re.compile(r'(?<=->(?:prop|item|function|abstract):id=")[A-Za-z_]\\w*')


def check_ids(node, base_words):
    """id must be unique in the spec, and must not be a word the base explains"""
    if node.parent is not None and node.parent.no == -1:
        return
    text = node.text or ""
    for m in re.finditer(r'id="([^"]+)"', text):
        name = m.group(1)
        if name.lower() in base_words:
            OUT.append((node.no, "E", "line %d: id \\"%s\\" is a word the base already explains "
                        "(%s) - a spec may not claim it; use the base word as it is"
                        % (node.no, name, base_words[name.lower()])))
    return


def check_id_unique(root, base_words):
    """every id once per spec; id and param share one namespace"""
    seen = {}
    for ch in _walk_all(root):
        t = ch.text or ""
        for rx, kind in ((RX_ID, "id"), (RX_PARAM, "param")):
            for m in rx.finditer(t):
                nm = m.group(1)
                key = nm.lower()
                prev = seen.get(key)
                if prev and prev[0] != kind:
                    OUT.append((ch.no, "E", "line %d: %s=\\"%s\\" collides with %s on line %d - "
                                "id and param share one namespace" % (ch.no, kind, nm, prev[0], prev[1])))
                elif prev:
                    OUT.append((ch.no, "E", "line %d: %s=\\"%s\\" is already declared on line %d"
                                % (ch.no, kind, nm, prev[1])))
                else:
                    seen[key] = (kind, ch.no)


def _walk_all(node):
    yield node
    for ch in node.children:
        for x in _walk_all(ch):
            yield x

'''

anchor = "def check_pins(node, scan_text):"
assert anchor in t
t = t.replace(anchor, CHECK.lstrip("\n") + "\n" + anchor, 1)
io.open(P, "w", encoding="utf-8", newline="").write(
    t.replace("\n", "\r\n") if crlf else t)
print("  check_ids() и check_id_unique() добавлены")
