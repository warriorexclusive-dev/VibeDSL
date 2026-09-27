# -*- coding: utf-8 -*-
"""the spec's third requirement: a controller per element, interchangeable

The task says every element is filled by a function, and each has its own
interchangeable controller. The mechanism is already in the language and I was
about to invent one: `incld` is defined as

    attribute incld="<id>": what is included here. NOT an import - a belonging
    mark, not an action

So an element says which controller belongs to it, and swapping one value
swaps the behaviour. No import, no dispatch table, nothing new.

Each ctl_* is an abstract, so it is interchangeable with any other abstract
of the same shape - that is what makes them swappable rather than merely
present. The build functions point at them with incld.
"""
import io
import sys

P = "PY_IDE/window.vibe"

CTLS = '''// ---- abstract func: kontrollery
//   incld - atribut prinadlezhnosti, NE import. Element obyavlyaet, kakoy
//   kontroller emu prinadlezhit; smena znacheniya menyayet povedenie, poetomu
//   kontrollery vzaimozamenyaemy. Kazhdyy ctl_* - abstract, to est ego mozhno
//   pomenyat na lyuboy drugoy takoy zhe formy.

&-> abstract:"ctl_bar"->action="bar:incld:set(\\"ctl_bar\\") + add(bar:btn name=\\"minimayz\\") + add(bar:btn name=\\"maksimayz\\") + action=show(bar)":
      bar:incld:set("ctl_bar")->add(bar:btn name="minimayz")->add(bar:btn name="maksimayz")->action=show(bar)

&-> abstract:"ctl_menu"->action="menu:incld:set(\\"ctl_menu\\") + add(menu:item) x4 + action=show(menu)":
      menu:incld:set("ctl_menu")->add(menu:item name="file")->add(menu:item name="edit")->add(menu:item name="run")->add(menu:item name="help")->action=show(menu)

&-> abstract:"ctl_frm"->action="frm:incld:set(\\"ctl_frm\\") + frm:module:set(true) + frm:split:set(factor [65,35]) + action=show(frm)":
      frm:incld:set("ctl_frm")->frm:module:set(true)->frm:split:set(factor [65,35])->action=show(frm)

&-> abstract:"ctl_left"->action="left:incld:set(\\"ctl_left\\") + left:min:set(50) + left:max:set(factor 25) + action=show(left)":
      left:incld:set("ctl_left")->left:min:set(50)->left:max:set(factor 25)->action=show(left)

&-> abstract:"ctl_right"->action="right:incld:set(\\"ctl_right\\") + right:min:set(50) + right:max:set(factor 25) + action=show(right)":
      right:incld:set("ctl_right")->right:min:set(50)->right:max:set(factor 25)->action=show(right)

&-> abstract:"ctl_tab"->action="tab_view:incld:set(\\"ctl_tab\\") + add(tab_view:inp type=\\"text\\") + action=show(tab_view)":
      tab_view:incld:set("ctl_tab")->add(tab_view:inp type="text")->action=show(tab_view)

&-> abstract:"ctl_editor"->action="inp:incld:set(\\"ctl_editor\\") + load(inp:text) + action=show(inp)":
      inp:incld:set("ctl_editor")->load(inp:text)->action=show(inp)

&-> abstract:"ctl_console"->action="console:incld:set(\\"ctl_console\\") + console:factor:set(50) + action=show(console)":
      console:incld:set("ctl_console")->console:factor:set(50)->action=show(console)

&-> abstract:"ctl_nav"->action="nav:incld:set(\\"ctl_nav\\") + nav:par:set(...) + add(nav:par ...) x4 + action=show(nav)":
      nav:incld:set("ctl_nav")->nav:par:set(...)->add(nav:par ...) x4->action=show(nav)

&-> abstract:"swap_ctl"->param=element->param=ctl->action="element:incld:set(ctl) + return(\\"kontroller pomenyan\\")":
      element:incld:set(ctl)

'''


def main():
    apply = "--apply" in sys.argv
    raw = io.open(P, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    L = raw.replace("\r\n", "\n").split("\n")
    i = next(n for n, l in enumerate(L) if "abstract func: karcas" in l)
    L[i:i] = CTLS.rstrip("\n").split("\n") + [""]
    print("  добавлено абстрактов: %d" % CTLS.count("&-> abstract"))
    if not apply:
        print("(только план)")
        return 0
    io.open(P, "w", encoding="utf-8", newline="").write(
        "\n".join(L).replace("\n", "\r\n") if crlf else "\n".join(L))
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
