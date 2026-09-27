# -*- coding: utf-8 -*-
"""abstract function id= -> abstract:function:id=

The type word goes only after a colon. `abstract function id="pass"` is two
bare words that happen to sit next to each other: it looks finished, it parses,
and it declares nothing. The three plan specs were all written that way, and
nothing complained until the rule existed to complain with.

One line is not the same kind of thing. In object-spellcheck.vibe:

    abstract{abstract full syntax} function{function,prop,item} id="abs"

that is a spec DESCRIBING the syntax - it quotes the forms on purpose. Quoting
belongs in a payload, where the checker does not read code, so it moves there
and keeps its meaning.
"""
import io
import sys

FIX = {
    "plan/exit-on-clean.vibe": [
        ('abstract function id="pass"', 'abstract:function:id="pass"'),
        ('abstract prop id="loop"', 'abstract:prop:id="loop"'),
        ('abstract prop id="dict"', 'abstract:prop:id="dict"'),
    ],
    "plan/spellcheck-stage1.vibe": [
        ('abstract function id="get_commands"', 'abstract:function:id="get_commands"'),
    ],
    "plan/object-spellcheck.vibe": [
        ('abstract function id="object_checker"',
         'abstract:function:id="object_checker"'),
        ('abstract{abstract full syntax} function{function,prop,item} id="abs" {"type","init"} -> {logic}',
         'abstract:prop:id="abs" {"type","init"} -> {any full syntax: function, prop, item}'),
        ('abstract prop id="object" {"name","track"}', 'abstract:prop:id="object" {"name","track"}'),
        ('abstract item id="line" {"text"}', 'abstract:item:id="line" {"text"}'),
    ],
}


def main():
    apply = "--apply" in sys.argv
    total = 0
    for path, pairs in FIX.items():
        raw = io.open(path, encoding="utf-8-sig").read()
        crlf = "\r\n" in raw
        text = raw.replace("\r\n", "\n")
        print(path)
        for old, new in pairs:
            n = text.count(old)
            if not n:
                print("   MISS  %s" % old[:58])
                continue
            total += n
            print("   %dx %s" % (n, new[:58]))
            if apply:
                text = text.replace(old, new)
        if apply:
            io.open(path, "w", encoding="utf-8", newline="").write(
                text.replace("\n", "\r\n") if crlf else text)
    print("\nзаменено: %d" % total)
    if not apply:
        print("(только план; для записи добавьте --apply)")
    else:
        print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
