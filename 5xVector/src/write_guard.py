# -*- coding: utf-8 -*-
"""the only way a file gets written in this folder

The rule is that a check stands BEFORE the write, not after it. I broke that
once today and it cost the embedding file: 3650 entries, rebuilt from source in
under a minute because the source was deterministic, and it should not have cost
even that.

So the rule is not in a file to be remembered. It is here, and every write goes
through it:

    guard(path, content, check)

check returns (ok, report). If ok is false nothing is written, and the failure
is printed. There is no code path that writes before checking, because the write
is the last statement and it is unreachable until check returns true.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "write_log.jsonl")

_written = 0
_refused = 0


def guard(path, content, check):
    """check(content) -> (ok, report). The file is written only if ok."""
    global _written, _refused
    ok, report = check(content)
    name = os.path.basename(path)
    if not ok:
        _refused += 1
        print("  ОТКАЗАНО  %s" % name)
        for line in str(report).split("\n"):
            if line.strip():
                print("            %s" % line)
        return False
    io.open(path, "wb").write(content)
    _written += 1
    print("  записано  %-24s %d Б" % (name, len(content)))
    for line in str(report).split("\n"):
        if line.strip():
            print("            %s" % line)
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as f:
        f.write('{"file":"%s","bytes":%d,"ok":true}\n' % (name, len(content)))
    return True


def count():
    print("")
    print("  записано %d   отказано %d" % (_written, _refused))
    return _written


# ---------------------------------------------------------------- the rebuild
def rebuild_embedding():
    """the deterministic rebuild, with the check in front of the write"""
    import re
    SEP = "\u25cf"
    src = os.path.join(HERE, "chunks3.txt")
    dst = os.path.join(HERE, "englang.embedding")
    NULL = 0xF00

    def check(content):
        txt = content.decode("utf-8")
        parts = txt.split(SEP)
        bad = [p for p in parts if any(ord(c) >= 128 for c in p)]
        lines = []
        lines.append("записей %d" % len(parts))
        lines.append("разделителей %d" % txt.count(SEP))
        if len(parts) != 3650:
            lines.append("ОШИБКА: записей должно быть 3650, получено %d" % len(parts))
        if len(parts) - 1 != txt.count(SEP):
            lines.append("ОШИБКА: разделителей на один меньше, чем записей")
        if bad:
            lines.append("ОШИБКА: не-английских записей %d: %s"
                         % (len(bad), " ".join(repr(b) for b in bad[:3])))
        if len(parts) >= NULL:
            lines.append("ОШИБКА: записей %d, а резерв пропуска на %d" % (len(parts), NULL))
        if not parts[0] or not parts[-1]:
            lines.append("ОШИБКА: пустая запись на краю")
        lines.append("свободно до 0xF00: %d" % (NULL - len(parts)))
        return (not any(l.startswith("ОШИБКА") for l in lines)), "\n".join(lines)

    lines = [l.strip() for l in io.open(src, encoding="utf-8")
             if l.strip() and not l.strip().startswith("#")]
    uniq = sorted(set(lines))
    return guard(dst, SEP.join(uniq).encode("utf-8"), check)


if __name__ == "__main__":
    print("")
    print("  ПИСАТЬ ЧЕРЕЗ ГЕЙТ, НЕ ИНАЧЕ")
    rebuild_embedding()
    count()
    print("")
    print("  ЗАПИСИ, КОТОРЫЕ НЕ ДОЛЖНЫ ПРОЙТИ ГЕЙТ:")
    print("     текст без разделителей и не-английская запись")
    print("     неверное число записей   проверяется")
    print("     разделителей не на один меньше   проверяется")
    print("     выход за предел 0xF00   проверяется")
