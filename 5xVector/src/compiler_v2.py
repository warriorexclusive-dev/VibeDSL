# -*- coding: utf-8 -*-
"""compiler for the spec form, byte offsets, nothing invented

    what a human prints        what the compiler emits
    --------------------------  ----------------------------------------
    words                      ASCII, unchanged
    the indent, as a space     U+25A1, at the start of a line
    the marks                  24 glyphs
    nothing else               addresses

    record   (object):property->result[hint]<form>\\r\\n
    parent   FRAME_R name FRAME_L, at the head of the next line

The address is a byte offset, not a place in a list, so a record points at one
piece and the file never has to be read whole. The file grows only at the end,
so an offset, once handed out, stays correct for the life of the table.

Nothing here is guessed. Every sign below was found in RULES.md, and the run at
the bottom refuses to start if one of them is missing.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

EMB = os.path.join(ROOT, "englang.embedding")
RULES = os.path.join(ROOT, "RULES.md")

# ---------------------------------------------------------------- the signs
SEP = "\u25cf"          # the separator in the address layer, one role
SP = "\u25a1"
# The separator in the source, on the input side, taken away by parsing in the
# same class as CR LF and the dash. The file separator is U+25CF and the two are
# on two sides of the compiler, so they are two signs and not one.
SEP_TEXT = "\u2055"
           # the visible space, an output, never an input
FRAME_R = "\u25b6"      # opens the parent
FRAME_L = "\u25c0"      # closes the parent
NULL = 0xF00            # a field with no address

# The width is derived, never written down. A width kept as a number goes stale
# the moment the table grows, and the stale number is invisible: it still
# compiles, it is just wrong. Derived from the source word list, so growing the
# table does not change the width, because the source is what fixes it.
SOURCE = os.path.join(ROOT, "english_words.txt")


def source_entries():
    """the word list the width is fixed by, read, never written"""
    if not os.path.exists(SOURCE):
        return []
    words = [l.strip() for l in io.open(SOURCE, encoding="utf-8")
             if l.strip() and not l.lstrip().startswith("#")]
    return sorted(set(words))


def width_for(entries):
    """the fewest glyphs that hold the last offset of this many entries"""
    if not entries:
        return 4
    need = offsets(entries)[-1] + 1
    w = 4
    while 16 ** w <= need:
        w += 1
    return w


WIDTH = None             # derived on first use, because it needs offsets()


def width():
    """the width is a function of the source word list, not a number kept here"""
    global WIDTH
    if WIDTH is None:
        WIDTH = width_for(source_entries())
    return WIDTH


def encode(value, w=None):
    w = w or width()
    out = []
    for k in range(w):
        out.append(G[(value >> (4 * (w - 1 - k))) & 0xF])
    return "".join(out)

G = "▦▣▭▬▯▮▢⇲⇱⇵⇶▤▰▱▲◉"   # the sixteen, 0..F
assert len(G) == 16, "the sixteen must be sixteen"

# ---------------------------------------------------------------------------
# Constants of the program. Not data. Not in the file.
#
#   the sixteen   bits of an address
#   the marks     formatting, used only when a word is replaced by glyphs
#   the one space  the visible space, an output of the compiler
#   the four tags  the parent tags, and the separator
#
# The file holds ASCII letters and one separator and nothing else. A mark has
# no place in it, so none of these may be written there, and check_embedding
# refuses the file if one appears.
# ---------------------------------------------------------------------------
CONSTANTS_NOT_DATA = True

MARK_GLYPH = {
    "\\": "╲",
    "0": "\u24ea",
    "1": "\u2460",
    "2": "\u2461",
    "3": "\u2462",
    "4": "\u2463",
    "5": "\u2464",
    "6": "\u2465",
    "7": "\u2466",
    "8": "\u2467",
    "9": "\u2468",
    ";": "\u2662",
    ",": "\u2669",
    ".": "\u2668",
    ":": "\u2663",
    "(": "\u25f0", ")": "\u25f1", "[": "\u25f2", "]": "\u25f3",
    "{": "\u25f4", "}": "\u25f5", "=": "\u25f6", "-": "\u25f7",
    "<": "\u25fa", ">": "\u25fc", "~": "\u2600", "|": "\u2605",
    "/": "\u2606", "?": "\u2610", "^": "\u2611", "&": "\u2612",
    "%": "\u261b", "$": "\u2620", "#": "\u2622", "@": "\u2630",
    "!": "\u263c", "*": "\u2660", "_": "\u2665", "+": "\u2666",
}


# ---------------------------------------------------------------- the table
def norm(word):
    """A-Z folds to a-z, and folding happens once so the file cannot hold both

    A word is stored lower, looked up lower, and written lower. Without this
    'Root' and 'root' are two entries and one word, and the table grows a
    duplicate for every capital letter anybody types.
    """
    return word.strip().lower()


def load():
    """entries in file order, folded, so the offsets are the file's own"""
    raw = io.open(EMB, "rb").read()
    return [norm(x) for x in raw.decode("utf-8").split(SEP)]


def offsets(entries):
    """a byte offset per entry; the separator is three bytes"""
    out = []
    at = 0
    for e in entries:
        out.append(at)
        at += len(e.encode("utf-8")) + len(SEP.encode("utf-8"))
    return out


def addr_of(word, table, added):
    """the offset of a word, appended if it is not there yet

    The table is keyed by words. The 3-3-tail layout is assembly and it lives in
    assemble(); it never becomes an address, and a tail never becomes a word.
    """
    word = norm(word)
    if word in table:
        return table[word]
    entries = sorted(set(list(table.keys()) + [word]))
    if len(entries) >= NULL:
        raise SystemExit("  ТАБЛИЦА ПЕРЕПОЛНЕНА: %d" % len(entries))
    off = offsets(entries)[-1]
    table[word] = off
    added.append(word)
    return off


def pieces(s):
    """3-3-tail, and this is the assembly only, never the reading

    Assembly lays bytes out. Reading asks for a word. A word is a vector, it has
    no visible parts, and the tail is a letter, which is a different vector with
    its own address in the alphabet. So neither the tail nor the pieces of a
    word ever appear in a record.
    """
    return [s[i:i + 3] for i in range(0, len(s), 3)]


def assemble(word):
    """the word -> the bytes it occupies, the write side, never the read side"""
    return len(word.lower().encode("utf-8"))


def read_at(off, table):
    """one offset -> one word, the read side, never the assembly"""
    for word, at in table.items():
        if at == off:
            return word
    return None


def field(text, table):
    """LAYER ONE. Convert only, and it writes nothing.

    A word becomes its address if it has one, and it stays itself if it has
    none, because a word that is not English is not in the table and never will
    be. The word that is missing comes back with the result, and writing it is
    the second layer's work and not this one's.

    Returns (glyph, missing) where missing is None when the word is known.
    """
    word = norm(text)
    if not word:
        return "", None
    if not addressable(word):
        return word, None                  # not a word the table will ever hold
    if word in table:
        return encode(table[word]), None
    return "", word                        # unknown, and layer two will write it


def commit(words, table):
    """LAYER TWO. Write what layer one could not resolve, once each.

    This is the only place the table grows. Layer one cannot, and that is the
    whole of the isolation: conversion and writing do not know about each other.

    The language is asked here and not in the conversion, because a word that is
    already in the table was asked when it arrived and there is nothing to ask
    twice. Only what is new goes to the source, so the first run asks a few and
    the rest of the run asks none.
    """
    import language_check as L
    cache = L.load_cache()
    written = []
    for w in dict.fromkeys(words):
        if w in table or not addressable(w):
            continue
        why = L.check(w, cache)
        if why:
            raise SystemExit("  СЛОЙ ТРИ, %s" % why)
        entries = sorted(set(list(table.keys()) + [w]))
        if len(entries) >= NULL:
            raise SystemExit("  ТАБЛИЦА ПЕРЕПОЛНЕНА: %d" % len(entries))
        table[w] = offsets(entries)[-1]
        written.append(w)
    L.save_cache(cache)
    return written


def encode(value):
    out = []
    for k in range(width()):
        out.append(G[(value >> (4 * (width() - 1 - k))) & 0xF])
    return "".join(out)


MARKS_BLOCK = "()"   # a block is shown by its own signs, and its content is
ARROW_GLYPH = "\u2192"   # the arrow, one sign, and the writer types it
ARROW = None        # a reference names something, a place names a place, and
                    # neither is a value to be turned into glyphs


def arrow():
    """the arrow, one sign and therefore one glyph

    It used to be the two signs -> and it became two glyphs, and then the two
    signs pulled apart: the dash is a child marker and the bracket closes the
    area, so neither of them belonged to the arrow. One sign carries the load on
    both sides and the writer has one thing to type instead of two.
    """
    global ARROW
    if ARROW is None:
        ARROW = ARROW_GLYPH
    return ARROW


def format_marks(s):
    return "".join(MARK_GLYPH.get(ch, ch) for ch in s)


# ---------------------------------------------------------------- the record
# the spell checker's role is now the sequence, not the spelling. The record has
# one order, and the compiler reports which order it found, so a wrong order is
# visible instead of silently accepted.
ORDER = ("object", "property", "function", "hint", "state")

REC = re.compile(
    r"^\((?P<obj>[^)]*)\)"
    r"(?::(?P<prop>[^:]*):?)*"
    r"(?:\u2192|->)(?P<func>[^\[]*)"     # the arrow, one sign or the old two
    r"\[(?P<hint>[^\]]*)\]"
    r"<(?P<state>[^>]*)>$"
)


def sequence(line):
    """the order of the fields as written, so a wrong one can be reported"""
    s = line.strip()
    seen = []
    i = 0
    if s.startswith("("):
        seen.append("object")
        i = s.find(")")
        i = s.find(")", i) + 1
    rest = s[i:]
    if rest.startswith(":"):
        seen.append("property")
    if ARROW_GLYPH in rest or "->" in rest:
        seen.append("function")
    if "[" in rest and "]" in rest:
        seen.append("hint")
    if "<" in rest and ">" in rest:
        seen.append("state")
    return seen

PARENT = re.compile(
    "^" + FRAME_R + r"(?P<name>[^" + FRAME_L + r"]+)" + FRAME_L
)


# A reader writes English, and English is the canon for every developer, so a
# word that is not English is refused at the input with a message that names it.
# It is not added to the table and nothing is written.
LATIN = set("abcdefghijklmnopqrstuvwxyz")


def addressable(word):
    """layer two, on writing: the table takes letters and nothing else

    Layer one is the substitution of signs into glyphs and it touches no word.
    This is layer two, and it is on the way to the file: a word that fails here
    is not written, whatever the record says. The record is still compiled, so
    the reader sees what came of the line, and the file stays English.
    """
    for w in word.split():
        if set(w) - LATIN:
            return False
    return True


def not_addressable_in(lines):
    """the words in a compiled record that layer two will not take

    Glyphs are taken out first. A glyph is what an address looks like, and an
    address is supposed to be there, so checking it for being English would
    reject every well formed record.
    """
    glyphs = set(G) | set(MARK_GLYPH.values()) | {SEP, SP, FRAME_R, FRAME_L}
    bad = []
    for line in lines:
        # a record ends at >, and the ) before it belongs to the object. Cutting
        # on )-> cuts the tail off the object and calls the field a boundary
        head = line.split(">")[0].replace(")", " ")
        for w in head.replace("(", " ").replace(SEP, " ").split():
            w = "".join(c for c in w if c not in glyphs)
            if w and not addressable(w):
                bad.append(w)
    return bad


# One field is one object. Brackets inside brackets are two objects with two
# sets of properties, and a position that cannot say which property belongs to
# which object is not a position. So it is refused here, at layer one, and not
# later as a language fault.
NESTED = re.compile(r"[()\[\]<>]")


def address_words(text, table, missing):
    """every name in a piece of text becomes its address, and every sign its glyph

    A name is looked up and a sign is substituted, and they are not the same
    action. The underscore of compile_record is a sign and it becomes a mark; the
    word compile_record is a name and it becomes an offset, and a name turned
    into a word with marks in it is not a name any more.
    """
    out, buf = [], []
    for ch in text:
        if ch.isalpha():
            buf.append(ch.lower())
        else:
            if buf:
                out.append(encode_name("".join(buf), table, missing))
                buf = []
            if ch == " ":
                out.append(SP)          # the separator is a sign, not a space
            else:
                g = MARK_GLYPH.get(ch)
                out.append(g if g else ch)
    if buf:
        out.append(encode_name("".join(buf), table, missing))
    return "".join(out)


def encode_name(word, table, missing):
    """a whole name, spaces kept as the visible space, and one address for it"""
    parts = word.split()
    if not parts:
        return word
    got = []
    for p in parts:
        if not addressable(p):
            got.append(p)
            continue
        if p in table:
            got.append(encode(table[p]))
        else:
            glyph, need = field(p, table)
            if need:
                missing.append(need)
                got.append(p)
            else:
                got.append(glyph)
    return SP.join(got)


def one_object(field):
    """the field, or None, and the reason in the reader's terms"""
    if not field:
        return None
    m = NESTED.search(field)
    if m:
        return ("one field is one object, and %r inside it is a second object "
                "with its own properties: %r. Two objects in one field make the "
                "position in the record stop being a position, so this is "
                "refused here and not later as a language fault"
                % (m.group(0), field))
    return None


def compile_record(line, table):
    """one record: an object, a property, a result, a hint, a form"""
    s = line.strip()
    seq = sequence(s)
    m = REC.match(s)
    if not m:
        return None, "не разобралось: %r" % s
    if seq != list(ORDER):
        return None, "порядок полей: %s, ожидалось %s" % (
            " → ".join(seq) or "пусто", " → ".join(ORDER))
    m = REC.match(s)
    if not m:
        return None, "не разобралось: %r" % s
    obj = (m.group("obj") or "").strip()
    _bad = one_object(obj)
    if _bad:
        return None, _bad
    prop = (m.group("prop") or "").strip()
    func = (m.group("func") or "").strip()
    hint = (m.group("hint") or "").strip()
    state = (m.group("state") or "").strip()

    left = []
    missing = []
    for w in (obj, prop):
        if not w:
            continue
        glyph, need = field(w, table)
        if need:
            missing.append(need)          # layer two's business, not ours
        elif glyph:
            left.append(glyph)
    body = SEP.join(left) if left else ""

    # The right side is read as three blocks, and each is handled in its own
    # right. A sign becomes a glyph. A name becomes an address, and those are
    # two different actions and doing only the first turns a name into a
    # word with glyphs in it instead of a place in the file.
    func_g = address_words(func, table, missing)
    hint_g = ("\u25f2" + address_words(hint, table, missing) + "\u25f3") if hint else ""
    state_g = ("\u25fa" + address_words(state, table, missing) + "\u25fc") if state else ""
    right = " ".join(x for x in (func_g, hint_g, state_g) if x)
    # the arrow is two signs and it gets two glyphs, and there is no glyph for
    # the pair: - is U+25F7 and > is U+25FC, and the arrow is ◷◼
    return (body, right, missing), None


TAG_DATA = ".data"     # opens the free block
TAG_CODE = ".code"     # closes it, and the records follow


def split_blocks(text):
    """(before, free, code) — the one boundary, and only one

    A file may carry a .data block that holds anything at all: a table, a
    diagram, a note, a fragment of another language. The compiler does not read
    it, does not address it and does not complain about it, so the only thing
    that has to happen is finding where it ends.

        .data    opens the free block
        .code    closes it, and the records follow

    Two rules and both of them are about not inventing a second meaning. The
    split happens once: a .code line inside the free block is the end and not a
    new pair, and a .data after it is a line like any other. And the blocks are
    siblings, both of them root, so nothing in the free block can become a
    parent of a record and nothing in the records can reach up into it.

    A file with no tags returns everything as code, which is what every file
    written before this was, and a file that is only a free block returns
    nothing to compile and is not an error: a file that is a note is a whole
    file, not a broken one.
    """
    before, free, code = [], [], []
    where = "before"
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        s = raw.strip()
        if where == "before" and s == TAG_CODE:
            where = "code"
            continue
        if where == "before" and s == TAG_DATA:
            where = "free"
            continue
        if where == "free":
            # the tag that ends it is a boundary and not a record, and it is
            # the last one: a file has one free block and not a nest of them
            if s == TAG_CODE:
                where = "code"
            else:
                free.append(raw)
            continue
        code.append(raw)
    if where == "free":
        # no .code: the free block runs to the end and is not compiled
        return before, free, []
    return before, free, code


def join_wrapped(code):
    """records that a person wrapped, joined back into one line

    A record is one line. A long one gets wrapped by hand:

        (object):property
                →function[example]<state>

    The test is not a mark, it is the arrow. A line that has no arrow yet and
    is followed by a line that opens with one is half a record, whatever it
    ends with, and the indent under it is the hand saying so. An earlier
    version of this looked for a trailing colon, and a colon is in the middle
    of that line and not at its end, so it never fired and every wrapped
    record stayed broken while the code looked correct.

    One wrap and not several, and only a line that is half a record can be
    joined: joining two whole records would merge them and produce one
    nonsensical record out of two good ones.
    """
    out = []
    i = 0
    while i < len(code):
        raw = code[i]
        body = raw.strip()
        while body.startswith("-"):
            body = body[1:].strip()
        has_arrow = ("→" in body) or ("->" in body)
        nxt = code[i + 1] if i + 1 < len(code) else None
        if not has_arrow and nxt is not None and \
                nxt.strip().startswith(("→", "->")):
            # the indent belonged to the hand, and the record takes the first
            # line's: the two halves are one thing and one thing has one indent
            out.append(raw.rstrip() + nxt.strip())
            i += 2
            continue
        out.append(raw)
        i += 1
    return out


def compile_text(text, table, added):
    """the whole source, line by line; a leading space names the parent"""
    out = []
    parent = None
    before, free, code = split_blocks(text)
    # the free block is not read. It is not counted, not reported and not
    # written anywhere, and the only trace of it is that the file still has it.
    for raw in join_wrapped(code):
        if not raw.strip():
            continue
        leading = len(raw) - len(raw.lstrip(" "))
        body = raw.strip()

        pm = PARENT.match(body)
        if pm:
            parent = pm.group("name").strip()
            body = body[pm.end():].strip()

        # the dash is a separator, like -> and \\r\\n, and is dropped here
        while body.startswith("-"):
            body = body[1:].strip()
        if not body:
            continue

        rec, err = compile_record(body, table)
        if err:
            return None, err
        left, right, need = rec
        parts = [left] if left else []
        if parent:
            glyph, need2 = field(parent, table)
            if need2:
                need.append(need2)
            if glyph:
                parts.append(glyph)
        prefix = (SP * leading + SEP) if leading else ""
        out.append("%s(%s)->%s" % (prefix, SEP.join(parts), right))
        added.extend(need)
        parent = None
    return out, None


# ---------------------------------------------------------------- the write
def check_embedding(content):
    txt = content.decode("utf-8")
    parts = txt.split(SEP)
    r = []
    bad = [p for p in parts if any(ord(c) >= 128 for c in p)]
    letters = set("abcdefghijklmnopqrstuvwxyz ")
    stray = [p for p in parts if set(p) - letters]
    r.append("записей %d" % len(parts))
    r.append("разделителей %d" % txt.count(SEP))
    ok = True
    if bad:
        ok = False
        r.append("ОШИБКА: не-английских %d: %s" % (len(bad), bad[:3]))
    if stray:
        ok = False
        r.append("ОШИБКА: в файле не буквы: %s" % " ".join(repr(s) for s in stray[:3]))
    if txt.count(SEP) + 1 != len(parts):
        ok = False
        r.append("ОШИБКА: разделителей не на один меньше")
    if len(parts) >= NULL:
        ok = False
        r.append("ОШИБКА: за пределом 0x%X" % NULL)
    if not parts[0] or not parts[-1]:
        ok = False
        r.append("ОШИБКА: пустая запись на краю")
    last = offsets(parts)[-1]
    if last >= 0x10000:
        ok = False
        r.append("ОШИБКА: последнее смещение %d не влезает в 4 глифа" % last)
    else:
        r.append("смещения в 4 глифах, максимум %d" % last)
    return ok, "\n".join(r)


def save(table):
    import write_guard as Gd
    entries = sorted(table.keys())
    return Gd.guard(EMB, SEP.join(entries).encode("utf-8"), check_embedding)


# ---------------------------------------------------------------- self test
def main():
    txt = io.open(RULES, encoding="utf-8").read()
    missing = [n for n, g in (("разделитель", SEP), ("пробел", SP),
                              ("открывающий тег", FRAME_R),
                              ("закрывающий тег", FRAME_L))
               if g not in txt]
    if missing:
        print("")
        print("  ОТКАЗ: в RULES.md нет %s" % ", ".join(missing))
        return 1
    for m, g in MARK_GLYPH.items():
        if g not in txt:
            print("")
            print("  ОТКАЗ: глиф маркера %r U+%04X не записан в RULES.md" % (m, ord(g)))
            return 1

    entries = load()
    table = {e: o for e, o in zip(entries, offsets(entries))}
    print("")
    print("  КОМПИЛЯТОР")
    print("  записей %d, поле = %d глифа = %d бит, пропуск 0x%X"
          % (len(entries), width(), width() * 4, NULL))
    print("  свободно %d" % (NULL - len(entries)))
    print("  первое смещение %d, последнее %d" % (table[entries[0]], table[entries[-1]]))
    print("  знаки и маркеры найдены в RULES.md, все 24")

    src = ("(root element):element->example[to model]<view>\n"
           + FRAME_R + "root element" + FRAME_L + "\n"
           + "  - (child element):element or other->example[toModel]<view>\n")
    added = []
    lines, err = compile_text(src, table, added)
    print("")
    print("  ВХОД")
    for l in src.strip().split("\n"):
        print("    %s" % l)
    if err:
        print("  ОШИБКА: %s" % err)
        return 1
    print("  ВЫХОД")
    for l in lines:
        print("    %s" % l)
    print("  добавлено в таблицу: %d   %s" % (len(added), " ".join(added) or "-"))

    written = commit(added, table)
    print("")
    print("  СЛОЙ ДВА, записано: %d   %s" % (len(written), " ".join(written) or "-"))
    bad = not_addressable_in(lines)
    if bad:
        print("")
        print("  СЛОЙ ДВА, НЕ ПРОХОДИТ, СЛОВО НЕ АНГЛИЙСКОЕ")
        for w in sorted(set(bad)):
            print("    %r   в таблицу не пишется" % w)
        print("  таблица не тронута")
        return 1

    ok = save(table)
    print("")
    print("  таблица: %s" % ("записана" if ok else "НЕ записана, проверка не прошла"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
