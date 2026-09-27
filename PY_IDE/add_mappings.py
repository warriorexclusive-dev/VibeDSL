# -*- coding: utf-8 -*-
"""process and collision, two mappings the base was missing

process is a mapping of a process name, not a command. That is the C++ sense
of Process - an isolated execution space with its own data - so it intersects
with C++ rather than with the action vocabulary. The name maps, which is why
check(process:collision) reads the process named collision.

collision is a logical mapping operator reachable from a process and from a 3D
vector. It is deliberately left loosely defined: a precise definition would
distort the vector, and the vector is the more general of the two.

Both go into type:mapping, alphabetically - collision between code and column,
process between procedure and prompt - and into symbols_map with descriptions
identical to the master, because G5 compares them.
"""
import io
import sys

D = "DATA/dictionary_sorted_by_type.txt"
S = "compiler/symbols_map.txt"

PROC_DESC = ("mapping of a process name: an isolated execution space with its own data, "
             "the C++ sense of Process; NOT a command, the name maps, so "
             "check(process:collision) reads the process named collision")
COLL_DESC = ("logical mapping collision operator: reachable from a process and from a 3D "
             "vector, and deliberately not defined more precisely - a precise definition "
             "would distort the vector, and the vector is the more general of the two")

PAIRS = [
    (D, "*-> code         - code.\n"
        "    -> exm:code:java\n"
        "\n"
        "*-> column        - composition: linear vertical axis of children",
     "*-> code         - code.\n"
        "    -> exm:code:java\n"
        "\n"
        "*-> collision    - " + COLL_DESC + "\n"
        "    -> exm:process:collision\n"
        "    -> exm:create(model type=cube)-[3]> collision:[1,2,3]\n"
        "\n"
        "*-> column        - composition: linear vertical axis of children"),
    (D, "*-> prompt        - mapping operator of user/human prompt",
     "*-> process       - " + PROC_DESC + "\n"
        "    -> exm:check(process:collision)\n"
        "\n"
        "*-> prompt        - mapping operator of user/human prompt"),
    (S, "U+2B1F   ⬟  *-> syntax", "U+2B1F   ⬟  *-> process - " + PROC_DESC),
    (S, "U+2A1B ⨛ *-> ", "U+2A1B ⨛ *-> collision - " + COLL_DESC),
]


def main():
    apply = "--apply" in sys.argv
    cache = {}
    total = 0
    for path, old, new in PAIRS:
        if path not in cache:
            raw = io.open(path, encoding="utf-8-sig").read()
            cache[path] = [raw, "\r\n" in raw, raw.replace("\r\n", "\n")]
        crlf, text = cache[path][1], cache[path][2]
        n = text.count(old)
        print("  %-30s %d  %s" % (path.split("\\")[-1], n, old.replace("\n", " / ")[:50]))
        if not n:
            print("     MISS")
            continue
        total += n
        if apply:
            cache[path][2] = text.replace(old, new, 1)
    print("\nзаменено: %d" % total)
    if not apply:
        print("(только план)")
        return 0
    for path, (_, crlf, text) in cache.items():
        io.open(path, "w", encoding="utf-8", newline="").write(
            text.replace("\n", "\r\n") if crlf else text)
    print("ЗАПИСАНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
