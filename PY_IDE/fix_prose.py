# -*- coding: utf-8 -*-
"""the prose must describe the code that is there now

ENGLISH reported 0 because it scans code position only. The 15 action="..."
strings kept saying "split mapping by group" after the code had become
split(mapping:group) - so the prose, which is the first thing a model reads,
was teaching a form that no longer existed.

Each replacement is the code itself, in the language's own notation, with ...
where a literal value goes. No double quotes: the whole string is quoted
payload, and a quote inside it is a quoting bug, not a value.

No prepositions. The owner leads in obj:prop, a setter is a vector anchored at
the end of the path, and action= marks a binding.
"""
import io
import sys

PATH = "PY_IDE/window.vibe"

PAIRS = [
    # read_colors
    ('load colors IDE.txt + split mapping by group + save style.json',
     'load(file) + split(mapping:group) + mapping:num:set(13) + save(cfg:mapping ...)'),
    # set_theme
    ('load theme from mapping + set frm:corner:radius + font + font_size',
     'load(mapping:theme) + frm:corner:radius:set(15) + frm:font:set(...) '
     '+ font:font_size:set(...) + action=show(theme)'),
    # bind_theme - nothing is given, so it is inheritance
    ('set theme of every element',
     'nasledovanie temy: view:theme:set()..console:theme:set() + action=show(theme)'),
    # reload_theme
    ('load mapping from cfg + run set_theme + run bind_theme',
     'load(cfg:mapping) + run(set_theme) + run(bind_theme)'),
    # add_par
    ('add par to nav + add nest to par',
     'add(nav:par par) + add(par:nest par)'),
    # set_text
    ('set name of item by par', 'item:name:set(par)'),
    # set_left / set_right
    ('set size of left clamped min 50 max factor 25',
     'left:size:set(par), granitsy: min 50, max factor 25'),
    ('set size of right clamped min 50 max factor 25',
     'right:size:set(par), granitsy: min 50, max factor 25'),
    # set_tabs / set_tab_name
    ('set num of tab by par', 'tab_view:num:set(par)'),
    ('set name of tab by par', 'tab_view:name:set(par)'),
    # set_console
    ('set size of console by par factor 25',
     'console:size:set(par), factor 25'),
    # fill_bar
    ('set content of nav by par + show', 'nav:content:set(par) + action=show(nav)'),
    # fill_panel - `in` here is a position, not a preposition
    ('crt frm in sht', 'create(frm v sht)'),
    # fill_editor
    ('load text of file in inp', 'load(inp:text par)'),
    # cmd
    ('run func by par name of io', 'run(io:func par)'),
]


def main():
    raw = io.open(PATH, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    apply = "--apply" in sys.argv
    n = 0
    for old, new in PAIRS:
        hit = text.count('action="%s"' % old)
        if not hit:
            print("  MISS %s" % old)
            continue
        n += hit
        print("  %dx %-44s" % (hit, old[:44]))
        print("      -> %s" % new)
        if apply:
            text = text.replace('action="%s"' % old, 'action="%s"' % new)
    print("\nзаменено: %d из %d" % (n, len(PAIRS)))
    if not apply:
        print("(только план; для записи добавьте --apply)")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="").write(
        text.replace("\n", "\r\n") if crlf else text)
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
