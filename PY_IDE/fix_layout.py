import io

P = "PY_IDE/vibide.py"
raw = io.open(P, encoding="utf-8-sig").read()
crlf = "\r\n" in raw
t = raw.replace("\r\n", "\n")

# 1. the column is the VERTICAL axis. horizontal=True makes dearpygui lay its
#    children out in a line, which is what `row` is, not what `column` is.
OLD_COL = 'col = dpg.add_group(tag="col", parent="frm", horizontal=True)'
NEW_COL = ('# column is the vertical axis: left above row. horizontal=True put them\n'
           '    # side by side, which is what row is for.\n'
           '    col = dpg.add_group(tag="col", parent="frm")')
assert OLD_COL in t, "col anchor"
t = t.replace(OLD_COL, NEW_COL, 1)

# 2. build_bottom adds to the SAME column. It used to build a second column
#    parented to the view, so top and bottom never shared the 65/35 split that
#    build_frm declares.
OLD_BOTTOM_CALL = "               build_frm, build_nav, build_top, build_bottom):"
NEW_BOTTOM_CALL = "               build_frm, build_nav, build_top, build_bottom):"
assert OLD_BOTTOM_CALL in t

# replace the whole build_bottom body
i = t.index("def build_bottom():")
j = t.index("\ndef ", i + 10) + 1
NEW_BOTTOM = '''def build_bottom():
    """add(column row) + add(row:console ...) x2 + console:factor:set(50) x2"""
    # the same column build_top made, so build_frm's split factor [65,35]
    # has something to divide. A second column parented to the view put the
    # consoles on top of the frame instead of under it.
    col = ELEM.get("col")
    if not col:
        return ret("net column - snachala build_top")
    if ELEM.get("row_bottom"):
        return ret("niz uzhe sobran")
    row = dpg.add_group(tag="row_bottom", parent=col, horizontal=True)
    con1 = dpg.add_group(tag="console", parent=row)
    con2 = dpg.add_group(tag="console", parent=row)
    for c in (con1, con2):
        dpg.configure_item(c, weight=0.5, horizontal=True)
    dpg.add_text("", parent=con1, tag="console_out")
    dpg.add_text("", parent=con2, tag="console_err")
    ELEM["row_bottom"] = row
    ELEM["console"] = [con1, con2]
    STYLE["factor"] = 50
    dpg.configure_item("frm", vertical=True, height=-1)
    return ret("niz: 2 konsoli popolam, split %s" % SPLIT_FACTOR)

'''
t = t[:i] + NEW_BOTTOM + t[j:]

io.open(P, "w", encoding="utf-8", newline="").write(
    t.replace("\n", "\r\n") if crlf else t)
print("  col - вертикальная ось")
print("  build_bottom - та же колонка, две консоли пополам")
