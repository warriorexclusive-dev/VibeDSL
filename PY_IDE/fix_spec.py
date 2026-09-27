# -*- coding: utf-8 -*-
"""fix the English in window.vibe's action scopes, one reviewed pair at a time.

Rule, and it is one rule: an action scope must say which object a thing
belongs to, using obj:prop. English used a preposition for that, and a
preposition is the cheap continuation: `set(radius of theme 15)` drifts into
prose because "of" carries no anchor.

  X of Y        ->  Y:X          the property belongs to the object
  add(A to B)   ->  add(B:A)     A is added to B, so B is the object
  load(A from B)->  load(B:A)    A comes out of B
  split(A by B) ->  split(A:B)   NOT reversed: B is the criterion, not the owner

`by` is the one that does not reverse, and the three grouped checks need the
group in the middle: `hex:num of theme` is the num of theme inside the hex
group, so it is theme:hex:num - not hex:theme:num, which would read as the
theme of hex.

Every pair below is printed before and after. Nothing is inferred.
"""
import io
import sys

PATH = "PY_IDE/window.vibe"

PAIRS = [
    # ---- line 52: read_colors
    ("split(mapping by group)", "split(mapping:group)"),
    ("set(num of mapping 13)", "set(mapping:num 13)"),
    ('save(mapping to cfg "PY_IDE/style.json")', 'save(cfg:mapping "PY_IDE/style.json")'),
    # ---- line 54: set_theme
    ("load(theme from mapping)", "load(mapping:theme)"),
    ("set(radius of theme 15)", "set(theme:radius 15)"),
    ('set(font of theme "Arial")', 'set(theme:font "Arial")'),
    ("set(font_size of theme [12,14])", "set(theme:font_size [12,14])"),
    # ---- line 59: reload_theme
    ("load(mapping from cfg)", "load(cfg:mapping)"),
    # ---- line 64: build_nav
    ('add(par to nav "file")', 'add(nav:par "file")'),
    ('add(par to nav "view")', 'add(nav:par "view")'),
    ('add(par to nav "option")', 'add(nav:par "option")'),
    ('add(par to nav "help")', 'add(nav:par "help")'),
    # ---- line 66: add_par
    ("add(par to nav par)", "add(nav:par par)"),
    ("add(nest to par par)", "add(par:nest par)"),
    # ---- line 68: set_text
    ("set(name of item par)", "set(item:name par)"),
    # ---- line 81: build_top
    ('add(inp to tab type="text")', 'add(tab:inp type="text")'),
    # ---- line 83 / 85: set_left / set_right
    ("set(size of left par)", "set(left:size par)"),
    ("set(size of right par)", "set(right:size par)"),
    # ---- line 99: add_tab
    ("set(name of tab par)", "set(tab:name par)"),
    ("set(text of tab par)", "set(tab:text par)"),
    # ---- line 101: set_tabs
    ("set(num of tab par)", "set(tab:num par)"),
    # ---- line 103: set_tab_name
    ("set(name of tab par)", "set(tab:name par)"),
    # ---- line 113: set_console
    ("set(size of console par)", "set(console:size par)"),
    # ---- line 123: fill_bar
    ("set(content of nav par)", "set(nav:content par)"),
    # ---- line 128: fill_editor
    ("load(text of file par in inp)", "load(inp:text par)"),
    # ---- line 135: cmd
    ("run(func par of io)", "run(io:func par)"),
    # ---- lines 240-242: the grouped checks, group in the middle
    ("check(hex:num of theme)", "check(theme:hex:num)"),
    ("check(key:num of theme)", "check(theme:key:num)"),
    ("check(group:num of theme)", "check(theme:group:num)"),
]


def main():
    raw = io.open(PATH, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    apply = "--apply" in sys.argv
    hits = 0
    for old, new in PAIRS:
        n = text.count(old)
        if not n:
            print("  MISS  %s" % old)
            continue
        hits += n
        print("  %dx  %-34s -> %s" % (n, old, new))
        if apply:
            text = text.replace(old, new)
    print("вхождений: %d из %d пар" % (hits, len(PAIRS)))
    if not apply:
        print("(только план; для записи добавьте --apply)")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="").write(
        text.replace("\n", "\r\n") if crlf else text)
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
