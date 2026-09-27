# -*- coding: utf-8 -*-
"""step 1 of the rewrite: the window chrome becomes declared elements

My last commit described the layout in a comment and that is the same mistake
as faking a gate - a sentence claiming the spec does something it does not.
menu, minimize and maximize were written about and never declared, so this
removes the comment and puts them in the tree where build_all can reach them.

The chain the task states, in the language's own notation:

    open_view   fullscreen window
      create(bar)              the chrome: minimize, maximize
      create(menu)             under the chrome
      create(frm)               under the menu
        frm:split:set(factor [65,35])
        column                  vertical axis
          row                   top: left | tab_view | right
          row_bottom            bottom: two consoles, half each

bar, menu and frm are declared as items. Their names are NOT in the base, so
they are exactly the kind of local name a spec is allowed to claim - and
check_id_unique is what stops one spec from binding the same name twice.
"""
import io
import sys

P = "PY_IDE/window.vibe"
CHROME = '''// ---- abstract func: okno

&-> abstract:"build_chrome"->action="create(bar) + add(bar:btn minimayz) + add(bar:btn maksimayz) + create(menu) + add(menu:item) x4 + action=show(bar) + action=show(menu)":
      create(bar)->add(bar:btn name="minimayz")->add(bar:btn name="maksimayz")->create(menu)->add(menu:item name="file")->add(menu:item name="edit")->add(menu:item name="run")->add(menu:item name="help")->action=show(bar)->action=show(menu)

&-> abstract:"click_minimayz"->action="view:fullscreen:set(false) + return("okno svernuto")":
      view:fullscreen:set(false)

&-> abstract:"click_maksimayz"->action="view:fullscreen:set(true) + return("okno razvorotano")":
      view:fullscreen:set(true)

&-> abstract:"build_menu"->action="create(menu) + add(menu:item) x4 + nav:par:set(...) + action=show(menu)":
      create(menu)->add(menu:item name="file")->add(menu:item name="edit")->add(menu:item name="run")->add(menu:item name="help")->nav:par:set("menu")->action=show(menu)

'''


def main():
    apply = "--apply" in sys.argv
    raw = io.open(P, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    L = raw.replace("\r\n", "\n").split("\n")

    # 1. drop the six comment lines that only DESCRIBED the chrome
    dropped = 0
    while len(L) > 1 and L[1].startswith("//") and any(
            k in L[1] for k in ("okno na ves ekran", "pod menyu", "verh:", "niz:",
                                "kazhdyy element", "vzaimozamenyaemyh")):
        del L[1]
        dropped += 1
    print("  удалено строк комментария: %d" % dropped)

    # 2. the chrome goes in before the frame section
    i = next(n for n, l in enumerate(L) if "abstract func: karcas" in l)
    L[i:i] = CHROME.rstrip("\n").split("\n") + [""]
    print("  вставлено: build_chrome, click_minimayz, click_maksimayz, build_menu")

    # 3. build_all calls them
    for n, l in enumerate(L):
        if 'run(build_frm)' in l and 'run(build_chrome)' not in l:
            L[n] = l.replace("run(build_frm)", "run(build_chrome)->run(build_menu)->run(build_frm)")
            print("  build_all: %s" % l.strip()[:96])
            break

    if not apply:
        print("(только план)")
        return 0
    io.open(P, "w", encoding="utf-8", newline="").write(
        "\n".join(L).replace("\n", "\r\n") if crlf else "\n".join(L))
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
