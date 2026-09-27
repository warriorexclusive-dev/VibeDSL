# -*- coding: utf-8 -*-
"""RULES.MD: the proto listing showed seven protos in a syntax that no longer
exists. Six of them are deleted; the seventh, abstract, is the one that stays
and it is written in the current form. The `fun:type="rule"` line below it
imported if, goal and fail by name, so it imports abstract."""
import io
import sys

PATH = "RULES.MD"
OLD_START = "-> proto(any) is node:act=[crt,exam]:type=rule:"
OLD_END = "   show(varn:max(3)&&req) ret=usr:sel1:->"
NEW = "prototype:id=\"abstract\":required:type[item,function,prop]:required:condition"
OLD_IMPORT = "use(VibeDSL:proto[if,goal,fail])"
NEW_IMPORT = "use(prototype:id=\"abstract\")"


def main():
    raw = io.open(PATH, encoding="utf-8-sig").read()
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    lines = text.split("\n")
    a = lines.index(OLD_START)
    b = lines.index(OLD_END)
    print("   заменяю строки %d..%d (%d строк) -> 1" % (a + 1, b + 1, b - a + 1))
    lines[a:b + 1] = [NEW]
    n_imp = sum(1 for l in lines if OLD_IMPORT in l)
    print("   %s: %d вхождение -> %s" % (OLD_IMPORT, n_imp, NEW_IMPORT))
    text = "\n".join(l.replace(OLD_IMPORT, NEW_IMPORT) for l in lines)
    if "--apply" not in sys.argv:
        print("(только план)")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="").write(
        text.replace("\n", "\r\n") if crlf else text)
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
