import io
import re

P = "PY_IDE/vibide.py"
raw = io.open(P, encoding="utf-8-sig").read()
crlf = "\r\n" in raw
t = raw.replace("\r\n", "\n")

# ---- _clamp: the max is a share of the PARENT, not of the argument ----------
OLD = '''def _clamp(size):
    """min 50, max = factor 25 ot shiriny roditelya"""
    lo = MIN_SIDE
    hi = max(lo, int(int(size) * MAX_FACTOR / 100.0))
    return max(lo, min(int(size), hi))'''
NEW = '''def _clamp(size, parent=None):
    """min 50, max = factor 25 of the parent width

    window.vibe says left:max:set(factor 25) and the docstring always said the
    factor was of the parent. The code multiplied the ARGUMENT by the factor, so
    the limit moved with the panel instead of bounding it: a panel at 400 was
    capped at 100, and a panel at 100 was capped at 25 - below its own minimum.
    The parent is the bound; the argument is only the request.
    """
    lo = MIN_SIDE
    want = int(size)
    if parent:
        try:
            pw = dpg.get_item_width(parent)
            if pw and pw > 0:
                want = min(want, int(pw * MAX_FACTOR / 100.0))
        except Exception:
            pass
    return max(lo, min(want, max(lo, int(want))))'''
assert OLD in t, "clamp anchor"
t = t.replace(OLD, NEW, 1)

# ---- set_left / set_right pass the parent ---------------------------------
t = t.replace(
    'dpg.configure_item(ELEM["left"], width=got)',
    'dpg.configure_item(ELEM["left"], width=got)')
for side, other in (("left", "row"), ("right", "row")):
    old = 'want = int(size)\n    got = _clamp(want)\n    dpg.configure_item(ELEM["%s"], width=got)' % side
    new = ('want = int(size)\n'
           '    got = _clamp(want, ELEM.get("%s"))\n'
           '    dpg.configure_item(ELEM["%s"], width=got)' % (other, side))
    if old in t:
        t = t.replace(old, new, 1)

# ---- the resize handlers ask the sender's parent, not the sender -----------
t = t.replace("set_left(dpg.get_item_width(s))",
              "set_left(dpg.get_item_width(s), dpg.get_item_width(dpg.get_item_parent(s)))")
t = t.replace("set_right(dpg.get_item_width(s))",
              "set_right(dpg.get_item_width(s), dpg.get_item_width(dpg.get_item_parent(s)))")

# ---- and set_left / set_right accept the parent as a second argument -------
for side in ("left", "right"):
    t = t.replace("def set_%s(size):" % side, "def set_%s(size, parent=None):" % side, 1)
    t = t.replace("got = _clamp(want, ELEM.get(\"row\"))",
                  "got = _clamp(want, parent or ELEM.get(\"row\"))")

# ---- build_top: initial width from the spec, not a literal 320 -------------
t = t.replace('left = dpg.add_group(tag="left", parent=col, width=320)',
              'left = dpg.add_group(tag="left", parent=col, width=-1)')
t = t.replace('right = dpg.add_group(tag="right", parent=row, width=320)',
              'right = dpg.add_group(tag="right", parent=row, width=-1)')
t = t.replace('''    ELEM["tabs"] = [tab1]''',
              '''    ELEM["tabs"] = [tab1]

    # window.vibe: left:min:set(50) + left:max:set(factor 25), and the three
    # are shown. A literal 320 was neither the minimum nor the factor.
    for side in ("left", "right"):
        try:
            pw = dpg.get_item_width(row)
        except Exception:
            pw = 0
        if pw:
            dpg.configure_item(ELEM[side],
                               width=max(MIN_SIDE, int(pw * MAX_FACTOR / 100.0)))''')

io.open(P, "w", encoding="utf-8", newline="").write(
    t.replace("\n", "\r\n") if crlf else t)
print("  _clamp считает предел от родителя")
print("  set_left/set_right принимают родителя")
print("  обработчики спрашивают родителя отправителя")
print("  build_top берёт ширину из спеки, не 320")
