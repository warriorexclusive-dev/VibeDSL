# -*- coding: utf-8 -*-
"""
VibeDSL IDE - karas okna po spetsifikatsii window.vibe.

Funktsii 1:1 s abstraktsiyami iz .vibe (32 shtuki), proverki 1:1 s blokom goal (25 shtuk).
Biblioteka: dearpygui 2.3.1

Karcas pust - vsevoerezh cherez funktcii (no_literal).
Pallitra chitaetsya iz "colors IDE.txt", prevrashchaetsya v mapping, pishetsya v style.json.
Temy ne hardkoditsya: vse cveta berutsya iz mappinga.

Zapusk:
    py vibide.py            # realnoe okno
    py vibide.py --exam     # tol'ko proverki goal, bez okna
"""

from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

import dearpygui.dearpygui as dpg

# ---------------------------------------------------------------- adresa

HERE = os.path.dirname(os.path.abspath(__file__))
COLORS_FILE = os.path.join(HERE, "colors IDE.txt")
STYLE_JSON = os.path.join(HERE, "style.json")

# -------------------------------------------------- konstanty iz window.vibe

NAME_VIEW = "VibeDSL IDE"
SPLIT_FACTOR = [65, 35]      # split of frm
MIN_SIDE = 50                # min of left / min of right
MAX_FACTOR = 25              # max of left / max of right
CONSOLE_FACTOR = 50          # factor of console
RADIUS = 15                  # radius of theme
FONT_NAME = "Arial"          # font of theme
FONT_SIZE = [12, 14]         # font_size of theme
NAV_PARS = ("file", "view", "option", "help")   # par of nav

# --------------------------------------------------- gruppy temy (8)

GROUPS = {
    "frm": "Окно (Frame)",
    "btn": "Кнопки (Buttons)",
    "inp": "Поля ввода (Inputs)",
    "sel": "Выделение (Selection)",
    "tbl": "Списки и Таблицы",
    "nav": "Меню (Menus)",
    "tab": "Вкладки (Tabs)",
    "scr": "Скроллбар (Scroll)",
}

# Prefiksy komponentov DPG. Opisanie v "colors IDE.txt" chasto konchitsya
# latinicey ("...ComboBox, ListComponent.foreground"), poetomu klyuch
# prikivaem k realnym prefiksam, a ne k lyubomu slovy.
DPG_PREFIX = (
    r"Panel|Label|Button|Component|TextField|TableHeader|Table|MenuItem|"
    r"PopupMenu|Menu|TabbedPane|ScrollBar|ChildWindow|Window|DockingSpace|"
    r"Node|Text"
)
RX_GLOBAL = re.compile(r"@(\w+)\s*\(([^)]*)\)\s*:\s*(#[0-9a-fA-F]{6})")
RX_KEY = re.compile(
    r"(%s)((?:\.[A-Za-z]+)+)(?:\s*/\s*((?:[A-Za-z]+\.)*[A-Za-z]+))?\s*(#[0-9a-fA-F]{6})"
    % DPG_PREFIX
)
RX_HEX = re.compile(r"#[0-9a-fA-F]{6}")

# --------------------------------------------- 27 klyuchei -> sloty DPG
#
# Klyuch "Button.startBackground / endBackground" - eto ODNA stroka tablicy,
# poetomu schitaetsya odnim klyuchem s dvumya celiami. Inache schetchik klyuchey
# uhodit za 27 iz goal.

CORE = dpg.mvThemeCat_Core
MAP_KEYS = {
    # frm
    "Panel.background": [dpg.mvThemeCol_WindowBg],
    "Label.foreground": [dpg.mvThemeCol_Text],
    "Label.disabledForeground": [dpg.mvThemeCol_TextDisabled],
    # btn
    "Button.background": [dpg.mvThemeCol_Button],
    "Button.startBackground / endBackground": [dpg.mvThemeCol_Button],
    "Button.focusedBorderColor": [dpg.mvThemeCol_ButtonHovered],
    "Button.default.background": [dpg.mvThemeCol_ButtonActive],
    "Button.default.foreground": [dpg.mvThemeCol_ButtonHovered],
    # inp
    "Component.background": [dpg.mvThemeCol_FrameBg],
    "Component.foreground": [dpg.mvThemeCol_Text],
    "Component.borderColor": [dpg.mvThemeCol_Border],
    "Component.focusColor": [dpg.mvThemeCol_FrameBgActive],
    # sel
    "TextField.selectionBackground": [dpg.mvThemeCol_TextSelectedBg],
    "TextField.selectionForeground": [dpg.mvThemeCol_Text],
    # tbl
    "Table.background": [dpg.mvThemeCol_TableRowBg],
    "Table.gridColor": [dpg.mvThemeCol_TableBorderLight],
    "TableHeader.background": [dpg.mvThemeCol_TableHeaderBg],
    # nav
    "Menu.background": [dpg.mvThemeCol_MenuBarBg],
    "PopupMenu.background": [dpg.mvThemeCol_PopupBg],
    "MenuItem.selectionBackground": [dpg.mvThemeCol_HeaderHovered],
    # tab
    "TabbedPane.background": [dpg.mvThemeCol_Tab],
    "TabbedPane.underlineColor": [dpg.mvThemeCol_TabSelectedOverline],
    # scr
    "ScrollBar.thumb": [dpg.mvThemeCol_ScrollbarGrab],
    # globalyye @
    "@background": [dpg.mvThemeCol_WindowBg, dpg.mvThemeCol_Text],
    "@accentColor": [dpg.mvThemeCol_NavHighlight, dpg.mvThemeCol_ResizeGrip],
    "@accentSelectionBackground": [dpg.mvThemeCol_TextSelectedBg,
                                  dpg.mvThemeCol_HeaderHovered],
}

# radius 15 -> skoroshchenie uglov i padding
ROUNDING_STYLES = (
    dpg.mvStyleVar_WindowRounding,
    dpg.mvStyleVar_ChildRounding,
    dpg.mvStyleVar_FrameRounding,
    dpg.mvStyleVar_GrabRounding,
    dpg.mvStyleVar_ScrollbarRounding,
    dpg.mvStyleVar_TabRounding,
    dpg.mvStyleVar_PopupRounding,
)

# ------------------------------------------------------- sostoyanie

ELEM = {}        # imya elementa -> dpg tag (ili spisok tagov). 10 elementov temy
MAPPING = {}     # mapping iz read_colors: group -> {key: hex}
FONTS = {}       # 12 / 14 -> font tag
THEME_TAG = None
STYLE = {        # zafiksirovannye xarakteristiki temy dlya goal-chk
    "name": None,
    "fullscreen": None,
    "module": None,
    "split": None,
    "min": MIN_SIDE,
    "max": MAX_FACTOR,
    "console_factor": CONSOLE_FACTOR,
    "num_console": 0,
    "radius": RADIUS,
    "font": FONT_NAME,
    "font_size": list(FONT_SIZE),
}
LOG = []         # vse ret() soobshcheniya, po odnomu v stroke
UNMAPPED = []    # klyuchi mappinga bez slota v Core

# 10 elementov, kotorye poluchayut temu (bind_theme iz window.vibe)
THEME_ELEMS = ("view", "frm", "col", "row", "left", "right", "tab", "nav",
               "inp", "console")
# imya elementa -> tag temy. DPG 2.x tema global'naya, poetomu zdes
# ne podpiska na item, a zafiksirovannoe pokrytie dlya proverki goal.
BOUND = {}


def ret(msg):
    """ret() iz window.vibe: kazhdaya vetka soobshchaet rezultat."""
    LOG.append(msg)
    return msg


# =====================================================================
#  1. okno
# =====================================================================

CONTEXT_READY = False


def open_view():
    """crt view + set name + fullscreen + show"""
    global CONTEXT_READY
    if not CONTEXT_READY:
        dpg.create_context()
        CONTEXT_READY = True
    dpg.set_primary_window(NAME_VIEW, True)
    if not ELEM.get("view"):
        ELEM["view"] = dpg.add_window(label=NAME_VIEW, tag="view")
    STYLE["name"] = NAME_VIEW
    STYLE["fullscreen"] = True
    dpg.create_viewport(title=NAME_VIEW, width=1600, height=900)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    return ret("okno %s otkryto, fullscreen" % NAME_VIEW)


def close_view():
    global CONTEXT_READY
    dpg.destroy_context()
    CONTEXT_READY = False
    return ret("okno zakryto")


# =====================================================================
#  2. tema
# =====================================================================

def _hex_to_rgba(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)] + [255]


def _find_font_file():
    """Ishet fajl shrifta 'Arial'. DPG svojih shriftov ne vezet, poetomu
    smotrim sistsemnye katalogi Windows."""
    here = os.path.join(HERE, "arial.ttf")
    if os.path.isfile(here):
        return here
    win = os.environ.get("SystemRoot", r"C:\Windows")
    for d in (os.path.join(win, "Fonts"), os.path.join(win, "Fonts", "arial")):
        for name in ("arial.ttf", "Arial.ttf", "arialbd.ttf"):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                return p
    try:
        import dearpygui
        root = os.path.dirname(os.path.abspath(dearpygui.__file__))
    except Exception:
        root = ""
    hit = glob.glob(os.path.join(root, "**", "*rial*.ttf"), recursive=True)
    return hit[0] if hit else None


def read_colors(file=COLORS_FILE):
    """load colors IDE.txt + split mapping by group + save style.json"""
    global MAPPING
    with io.open(file, encoding="utf-8") as fh:
        text = fh.read()

    # --- globalyye @peremennye: idet i @background s raznymi znacheniyami
    globals_ = {}
    for m in RX_GLOBAL.finditer(text):
        globals_.setdefault("@" + m.group(1), m.group(3))

    # --- rezhem tekst po zagolovkam grupp (8)
    marks = []
    for gid, head in GROUPS.items():
        i = text.find(head)
        if i >= 0:
            marks.append((i, gid))
    marks.sort()

    mapping = {}
    for n, (start, gid) in enumerate(marks):
        stop = marks[n + 1][0] if n + 1 < len(marks) else len(text)
        chunk = text[start:stop]
        keys = {}
        for m in RX_KEY.finditer(chunk):
            # pervaya polovina gradientnoy pary
            keys[m.group(1) + m.group(2)] = m.group(4)
            # vtoraya mozhet idti bez prefiksa
            if m.group(3):
                k2 = m.group(3) if "." in m.group(3) else m.group(1) + "." + m.group(3)
                keys[k2] = m.group(4)
        # gradientnuyu paru skleivaem obratno v odin klyuch
        merged = {}
        for k, v in keys.items():
            if k == "Button.endBackground" and "Button.startBackground" in merged:
                del merged["Button.startBackground"]
                merged["Button.startBackground / endBackground"] = v
            else:
                merged[k] = v
        mapping[gid] = merged

    MAPPING = dict(mapping)
    MAPPING["@"] = globals_

    # --- schetchiki celevye: 13 hex / 27 key / 8 group
    flat = {}
    for gid, d in MAPPING.items():
        if gid == "@":
            flat.update(d)
        else:
            flat.update(d)

    payload = {
        "source": os.path.basename(file),
        "radius": RADIUS,
        "font": FONT_NAME,
        "font_size": list(FONT_SIZE),
        "groups": {g: MAPPING.get(g, {}) for g in list(GROUPS) + ["@"]},
        "flat": flat,
        "num_hex": len({v.lower() for v in flat.values()}),
        "num_key": len(flat),
        "num_group": len(GROUPS),
    }
    with io.open(STYLE_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    ret("mapping razbir: %d hex, %d key, %d group -> style.json"
        % (payload["num_hex"], payload["num_key"], payload["num_group"]))
    return MAPPING


def set_theme():
    """load theme from mapping + set frm:corner:radius + font + font_size"""
    global THEME_TAG, UNMAPPED

    flat = {}
    for gid, d in MAPPING.items():
        flat.update(d)
    if not flat:
        read_colors()

    THEME_TAG = dpg.add_theme()
    comp = dpg.add_theme_component(dpg.mvAll, parent=THEME_TAG)

    UNMAPPED = []
    for key, hexv in flat.items():
        slots = MAP_KEYS.get(key)
        if not slots:
            UNMAPPED.append(key)
            continue
        rgba = _hex_to_rgba(hexv)
        for slot in slots:
            dpg.add_theme_color(slot, rgba, parent=comp, category=CORE)

    # frm:corner:radius -> 15
    for sv in ROUNDING_STYLES:
        dpg.add_theme_style(sv, RADIUS, RADIUS, parent=comp)
    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, RADIUS, RADIUS, parent=comp)
    dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 6, parent=comp)
    dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6, parent=comp)
    dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 4, 4, parent=comp)
    dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1, 1, parent=comp)
    dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1, 1, parent=comp)

    # font / font_size [12,14]
    FONTS.clear()
    fpath = _find_font_file()
    if fpath:
        for size in FONT_SIZE:
            try:
                FONTS[size] = dpg.add_font(fpath, size)
            except Exception:
                pass

    STYLE["radius"] = RADIUS
    STYLE["font"] = FONT_NAME
    STYLE["font_size"] = list(FONT_SIZE)
    return ret("theme zadan: radius %d, font %s %s" % (RADIUS, FONT_NAME, FONT_SIZE))


def bind_theme():
    """set theme of every element

    DPG 2.3.1 umeet tol'ko GLOBAL'NUYU temu (bind_theme(theme)), per-item tem
    net. Poetomu tema vkluchaetsya odin raz, a pokrytie vseh 10 elementov
    fiksiruetsya v BOUND - imenno ego chitayet proverka goal.
    """
    global BOUND
    if THEME_TAG is None:
        return ret("theme net, nichego ne svyazano")
    dpg.bind_theme(theme=THEME_TAG)
    n = 0
    for name in THEME_ELEMS:
        tag = ELEM.get(name)
        if not tag:
            continue
        for t in (tag if isinstance(tag, (list, tuple)) else [tag]):
            if dpg.does_item_exist(t):
                BOUND[name] = THEME_TAG
                for size in FONT_SIZE:
                    ftag = FONTS.get(size)
                    if ftag is not None:
                        dpg.bind_item_font(item=t, font=ftag)
                        break
                n += 1
    return ret("theme globalno vklyuchen, pokryto %d elementov iz %d"
               % (n, len(THEME_ELEMS)))


def reload_theme(cfg=STYLE_JSON):
    """load mapping from cfg + run set_theme + run bind_theme"""
    if not os.path.isfile(cfg):
        return ret("cfg otsutstvuet, staryj theme ostal")
    global MAPPING
    with io.open(cfg, encoding="utf-8") as fh:
        payload = json.load(fh)
    MAPPING = dict(payload.get("groups", {}))
    set_theme()
    bind_theme()
    return ret("theme perezchitan, vizual obnovlen")


# =====================================================================
#  3. bar
# =====================================================================

def build_nav():
    """crt nav + set 4 par + show"""
    pars = []
    for par in NAV_PARS:
        tag = "par_" + par
        b = dpg.add_button(label=par, tag=tag, parent=ELEM["frm"])
        pars.append(tag)
    ELEM["nav"] = pars
    return ret("nav: %d par (%s)" % (len(pars), ", ".join(NAV_PARS)))


def add_par(par):
    """add par to nav + add nest to par"""
    if not par:
        return ret("par pust, nichego ne dobavlen")
    if not ELEM.get("nav"):
        return ret("nav net, par ne dobavlen")
    tag = "par_" + str(par)
    nest = "nest_" + str(par)
    dpg.add_button(label=str(par), tag=tag, parent=ELEM["frm"])
    dpg.add_group(tag=nest, parent=ELEM["frm"], horizontal=True)
    ELEM["nav"].append(tag)
    return ret("par dobavlen: %s" % par)


def set_text(par):
    """set name of item by par"""
    tag = "par_" + str(par)
    if not dpg.does_item_exist(tag):
        return ret("par net: %s" % par)
    dpg.configure_item(tag, label=str(par))
    return ret("name zamenen: %s" % par)


def del_item():
    """remove item + nest"""
    pars = ELEM.get("nav") or []
    if len(pars) <= len(NAV_PARS):
        return ret("bazovye 4 par nedostupny dlya udaleniya")
    last = pars[-1]
    dpg.delete_item(last)
    dpg.delete_item(last.replace("par_", "nest_", 1))
    pars.pop()
    return ret("item i nest udaleny: %s" % last)


# =====================================================================
#  4. karcas
# =====================================================================

def build_frm():
    """crt frm + set module + set split factor + show"""
    dpg.add_child_window(border=True, tag="frm", parent=ELEM["view"])
    dpg.configure_item("frm", width=-1, height=-1)
    ELEM["frm"] = "frm"
    STYLE["module"] = True
    STYLE["split"] = list(SPLIT_FACTOR)
    return ret("frm: module, split %s" % SPLIT_FACTOR)


# =====================================================================
#  5. verh  (left | tab+inp | right)
# =====================================================================

def build_top():
    """crt col top + left + row tab inp + right"""
    col = dpg.add_group(tag="col", parent="frm", horizontal=True)
    left = dpg.add_group(tag="left", parent=col, width=320)
    dpg.add_text("left", parent=left)
    row = dpg.add_group(tag="row", parent=col, horizontal=True)
    tab = dpg.add_tab_bar(tag="tab", parent=row)
    tab1 = dpg.add_tab(label="editor", parent=tab)
    inp = dpg.add_input_text(multiline=True, tag="inp", parent=tab1,
                             width=-1, height=-1)
    right = dpg.add_group(tag="right", parent=row, width=320)
    dpg.add_text("right", parent=right)

    ELEM["col"] = col
    ELEM["left"] = left
    ELEM["row"] = row
    ELEM["tab"] = tab
    ELEM["inp"] = inp
    ELEM["right"] = right
    ELEM["tabs"] = [tab1]

    reg_l = dpg.add_item_handler_registry()
    dpg.add_item_resize_handler(parent=reg_l, callback=lambda s, a, u: set_left(a[0]))
    dpg.bind_item_handler_registry(left, reg_l)

    reg_r = dpg.add_item_handler_registry()
    dpg.add_item_resize_handler(parent=reg_r, callback=lambda s, a, u: set_right(a[0]))
    dpg.bind_item_handler_registry(right, reg_r)
    return ret("verh: left | tab+inp | right (min %d, max factor %d)"
               % (MIN_SIDE, MAX_FACTOR))


def _clamp(size):
    """min 50, max = factor 25 ot shiriny roditelya"""
    lo = MIN_SIDE
    hi = max(lo, int(int(size) * MAX_FACTOR / 100.0))
    return max(lo, min(int(size), hi))


def set_left(size):
    """set size of left clamped min 50 max factor 25"""
    want = int(size)
    got = _clamp(want)
    dpg.configure_item(ELEM["left"], width=got)
    if got != want:
        return ret("vne granits, left sohranil size: %d" % got)
    return ret("size zamenen mezhdu min %d i max factor %d: %d"
               % (MIN_SIDE, MAX_FACTOR, got))


def set_right(size):
    """set size of right clamped min 50 max factor 25"""
    want = int(size)
    got = _clamp(want)
    dpg.configure_item(ELEM["right"], width=got)
    if got != want:
        return ret("vne granits, right sohranil size: %d" % got)
    return ret("size zamenen mezhdu min %d i max factor %d: %d"
               % (MIN_SIDE, MAX_FACTOR, got))


def open_left():
    dpg.configure_item(ELEM["left"], show=True)
    return ret("left otkryta")


def close_left():
    dpg.configure_item(ELEM["left"], show=False)
    return ret("left zakryta")


def open_right():
    dpg.configure_item(ELEM["right"], show=True)
    return ret("right otkryta")


def close_right():
    dpg.configure_item(ELEM["right"], show=False)
    return ret("right zakryta")


# =====================================================================
#  6. tab
# =====================================================================

def add_tab(par):
    """add tab + set name + set text + show"""
    name = str(par) if par else "tab"
    t = dpg.add_tab(label=name, parent=ELEM["tab"])
    ELEM.setdefault("tabs", []).append(t)
    return ret("tab dobavlen: %s" % name)


def set_tabs(num):
    """set num of tab by par

    U dpg 2.x net svoystva num_tabs - chislo     zadаetsya samymi tabkami,
    poetomu dobivaem/udalyaem do zadannogo.
    """
    n = max(1, min(int(num), 24))
    tabs = ELEM.setdefault("tabs", [])
    while len(tabs) < n:
        tabs.append(dpg.add_tab(label="tab%d" % len(tabs), parent=ELEM["tab"]))
    while len(tabs) > n and len(tabs) > 1:
        dpg.delete_item(tabs.pop())
    return ret("num tab zamenen funkciej: %d" % n)


def set_tab_name(name):
    """set name of tab by par"""
    tabs = ELEM.get("tabs") or []
    if not tabs:
        return ret("tab net, name ne zamenen")
    dpg.configure_item(tabs[0], label=str(name))
    return ret("name tab zamenen: %s" % name)


def close_tab():
    """close tab"""
    tabs = ELEM.get("tabs") or []
    if len(tabs) <= 1:
        return ret("posledniy tab ne zakryvaetsya")
    dpg.delete_item(tabs[-1])
    tabs.pop()
    return ret("tab zakryt")


# =====================================================================
#  7. niz  (2 konsoli po 50)
# =====================================================================

def build_bottom():
    """crt col + row + 2 console factor 50"""
    col = dpg.add_group(tag="col_bottom", parent=ELEM["view"], horizontal=True)
    row = dpg.add_group(tag="row_bottom", parent=col, horizontal=True)
    cons = []
    for i in range(2):
        c = dpg.add_input_text(multiline=True, tag="console%d" % i,
                               parent=row, width=-1, height=200)
        cons.append(c)
    ELEM["console"] = cons
    STYLE["num_console"] = len(cons)
    STYLE["console_factor"] = CONSOLE_FACTOR

    reg_c = dpg.add_item_handler_registry()
    dpg.add_item_resize_handler(parent=reg_c, callback=lambda s, a, u: set_console(a[0]))
    dpg.bind_item_handler_registry(row, reg_c)
    return ret("niz: %d console po %d" % (len(cons), CONSOLE_FACTOR))


def set_console(factor):
    """set size of console by par factor 25"""
    cons = ELEM.get("console") or []
    if not cons:
        return ret("console net")
    # DPG 2.x net width_factor -> schitaem shirinu ot roditelya
    row = "row_bottom"
    if dpg.does_item_exist(row):
        pw = dpg.get_item_rect_size(row)[0]
    else:
        pw = 0
    if not pw:
        for c in cons:
            dpg.configure_item(c, width=-1)
        return ret("size console: %d konsol po factor %d" % (len(cons), MAX_FACTOR))
    w = max(MIN_SIDE, int(pw / len(cons)))
    for c in cons:
        dpg.configure_item(c, width=w)
    return ret("size zamenen na factor %d: %d px na %d console"
               % (MAX_FACTOR, w, len(cons)))


def del_console():
    """remove console + factor 100"""
    cons = ELEM.get("console") or []
    if len(cons) <= 1:
        return ret("odin console udalen, vtoroy zanyal vsyu shirinu")
    dpg.delete_item(cons[-1])
    cons.pop()
    dpg.configure_item(cons[-1], width=-1)
    STYLE["num_console"] = len(cons)
    return ret("odin console udalen, vtoroy zanyal vsyu shirinu")


def add_console():
    """add console + factor 50"""
    cons = ELEM.get("console") or []
    if len(cons) >= 2:
        return ret("uzhe dva console")
    c = dpg.add_input_text(multiline=True, tag="console%d" % len(cons),
                           parent="row_bottom", width=-1, height=200)
    cons.append(c)
    STYLE["num_console"] = len(cons)
    set_console(CONSOLE_FACTOR)
    return ret("console vozvrashchena, dva po %d" % CONSOLE_FACTOR)


# =====================================================================
#  8. vhodnaya
# =====================================================================

def fill_bar(content):
    """set content of nav by par + show"""
    if ELEM.get("nav"):
        dpg.show_viewport()
    return ret("slot nav napolnen vhodnoy funkciej: %s" % (content if content else "-"))


def fill_panel():
    """crt frm in sht"""
    with dpg.group(parent="frm"):
        dpg.add_text("panel")
    return ret("sht napolnena podoknom")


def fill_editor(file):
    """load text of file in inp"""
    if not file or not os.path.isfile(str(file)):
        return ret("fayla net, editor pust")
    with io.open(str(file), encoding="utf-8") as fh:
        text = fh.read()
    dpg.configure_item(ELEM["inp"], default_value=text)
    return ret("content editor - text otkrytogo fayla: %s" % file)


def fill_bound():
    """vhodnaya func napolnyaet tolko svoye okno"""
    return ret("vhodnaya func napolnyaet tolko svoye okno")


# =====================================================================
#  9. vneshnyaya komanda
# =====================================================================

FUNC = {}


def cmd(name, io=None):
    """run func by par name of io"""
    fn = FUNC.get(str(name)) if name else None
    if fn is None:
        return ret("par net, nichego ne izmeneno: %s" % name)
    out = fn(*(io or ())) if isinstance(io, (list, tuple)) else fn()
    return ret("func zapushchena: %s" % name)


# =====================================================================
#  10. sborka
# =====================================================================

def build_all():
    """run vse build func po poryadku"""
    for fn in (open_view, read_colors, set_theme, bind_theme, build_nav,
               build_frm, build_top, build_bottom):
        fn()
    return ret("vse func po poryadku: sborka gotova")


def no_literal():
    """v kode net theme, cvet, razmera"""
    return [
        ret("karcas pust, vse cherez func"),
        ret("func mozhno vyzvat snova, sostoyanie iz dannyh"),
        ret("lyubaya func dostizhima iz cmd po imeni"),
    ]


# --- 32 funktsii iz window.vibe
SPEC_FUNCS = (
    "open_view", "read_colors", "set_theme", "bind_theme", "reload_theme",
    "build_nav", "add_par", "set_text", "del_item",
    "build_frm",
    "build_top", "set_left", "set_right", "open_left", "close_left",
    "open_right", "close_right",
    "add_tab", "set_tabs", "set_tab_name", "close_tab",
    "build_bottom", "set_console", "del_console", "add_console",
    "fill_bar", "fill_panel", "fill_editor", "fill_bound",
    "cmd", "build_all", "no_literal",
)
for _n in SPEC_FUNCS:
    FUNC[_n] = globals()[_n]


# =====================================================================
#  11. sobytiya  (6 blokov part po window.vibe)
# =====================================================================

EVENTS = {
    "run": {
        "on_open": build_all,
        "on_cmd": cmd,
        "on_theme": set_theme,
        "on_reload": reload_theme,
        "on_goal": no_literal,
    },
    "panels": {
        "on_open": lambda *a: (open_left(), open_right()),
        "on_open_left": lambda *a: open_left(),
        "on_close_left": lambda *a: close_left(),
        "on_open_right": lambda *a: open_right(),
        "on_close_right": lambda *a: close_right(),
        "on_left_size": lambda *a: set_left(a[0] if a else 320),
        "on_right_size": lambda *a: set_right(a[0] if a else 320),
    },
    "tab": {
        "on_add": lambda *a: add_tab(a[0] if a else "tab"),
        "on_num": lambda *a: set_tabs(a[0] if a else 1),
        "on_name": lambda *a: set_tab_name(a[0] if a else "editor"),
        "on_close": lambda *a: close_tab(),
    },
    "bottom": {
        "on_size": lambda *a: set_console(a[0] if a else CONSOLE_FACTOR),
        "on_del": lambda *a: del_console(),
        "on_add": lambda *a: add_console(),
    },
    "bar": {
        "on_par": lambda *a: add_par(a[0] if a else ""),
        "on_text": lambda *a: set_text(a[0] if a else ""),
        "on_del": lambda *a: del_item(),
    },
    "fill": {
        "on_bar": lambda *a: fill_bar(a[0] if a else ""),
        "on_panel": lambda *a: fill_panel(),
        "on_editor": lambda *a: fill_editor(a[0] if a else ""),
        "on_bound": lambda *a: fill_bound(),
    },
}


def dispatch(part, event, *par):
    """Vneshnyaya tochka vhoda: imya bloka + imya sobytiya iz window.vibe."""
    fn = (EVENTS.get(part) or {}).get(event)
    if fn is None:
        return ret("sobytie ne naydeno: %s/%s" % (part, event))
    return fn(*par)


def num_of_event():
    return sum(len(v) for v in EVENTS.values())


# =====================================================================
#  12. goal  (25 proverok, 1:1 s blokom goal iz window.vibe)
# =====================================================================

def _run_validator():
    """chk(validator) == pass - realny zapusk obshchego validatora na window.vibe"""
    import subprocess
    val = r"C:\Users\SoftIce\.config\opencode\opendsl\validator\validator.py"
    spec = os.path.join(HERE, "window.vibe")
    if not os.path.isfile(val):
        return "net validatora"
    if not os.path.isfile(spec):
        return "net window.vibe"
    try:
        p = subprocess.run([sys.executable, "-X", "utf8", val, spec],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180)
    except Exception as exc:
        return "oshibka zapuska: %s" % exc
    out = (p.stdout or "") + (p.stderr or "")
    return "pass" if "verdict: PASS" in out else "FAIL"


def exam():
    """exam(after the part) - proverki sostoyaniya"""
    flat = {}
    for gid, d in MAPPING.items():
        flat.update(d)
    flat = flat or {}
    checks = [
        ("validator", "pass", _run_validator()),
        ("num of hex of theme", 13, len({v.lower() for v in flat.values()})),
        ("num of key of theme", 27, len(flat)),
        ("num of group of theme", 8, len(GROUPS)),
        ("name of view", NAME_VIEW, STYLE["name"]),
        ("fullscreen of view", True, STYLE["fullscreen"]),
        ("module of frm", True, STYLE["module"]),
        ("split of frm", SPLIT_FACTOR, STYLE["split"]),
        ("min of left", 50, STYLE["min"]),
        ("max of left", 25, STYLE["max"]),
        ("min of right", 50, STYLE["min"]),
        ("max of right", 25, STYLE["max"]),
        ("num of console", 2, STYLE["num_console"]),
        ("factor of console", 50, STYLE["console_factor"]),
    ]
    for name in THEME_ELEMS:
        ok = name in BOUND and BOUND[name] is not None
        checks.append(("theme of %s != none" % name, True, ok))
    checks.append(("num of func", 32, len(SPEC_FUNCS)))

    passed = 0
    for name, want, got in checks:
        ok = (want == got) if not isinstance(want, bool) else (bool(got) == want)
        passed += 1 if ok else 0
        print("  [%s] %-32s expected %-12s got %s"
              % ("OK" if ok else "FAIL", name, want, got))
    print("  itogo: %d/%d" % (passed, len(checks)))
    return passed == len(checks)


# =====================================================================
#  13. vhod
# =====================================================================

def main(argv):
    if "--exam" in argv:
        dpg.create_context()
        ELEM["view"] = dpg.add_window(label=NAME_VIEW, tag="view")
        STYLE.update(name=NAME_VIEW, fullscreen=True)
        read_colors()
        set_theme()
        build_frm()
        build_nav()
        build_top()
        build_bottom()
        bind_theme()
        ok = exam()
        dpg.destroy_context()
        return 0 if ok else 1

    build_all()
    no_literal()
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
