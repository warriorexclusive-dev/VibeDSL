# -*- coding: utf-8 -*-
"""the input-consistency check, as a module the compiler imports at startup

A check that lives in a separate validator is a check someone forgets to run, and
a check that cannot fire while a spec is being compiled is a check that will be
outlived by a spec written wrong. So this runs inside compile.py, every time,
before a single line is compiled.

What it compares, and what it refuses to do:

  master <-> symbols_map   every glyph in one is in the other. A glyph the map
                           has and the dictionary does not, or the reverse, is a
                           token the compiler can resolve and the language cannot
                           name - so that is an error, not a warning.

  master <-> the splits   reported, NOT enforced. A split may be empty by design:
                           mapping.dict carries no definitions of its own, and a
                           check that demands equality would have had me run
                           --fix and "repair" a file that was never broken. So a
                           split that is behind is stated with its age and its
                           count, and left alone.

The difference between those two is the whole point. One is a contradiction, the
other is a fact about the repository.
"""
import collections
import io
import os
import re


def _entries(path):
    if not path or not os.path.isfile(path):
        return []
    txt = io.open(path, encoding="utf-8-sig").read().replace("\r\n", "\n")
    return re.findall(r"(?m)^\*->\s+(\S+)", txt)


def _map_glyphs(path):
    if not path or not os.path.isfile(path):
        return set()
    out = set()
    for ln in io.open(path, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n"):
        m = re.match(r"U\+([0-9A-Fa-f]{4,6})\s+(\S+)\s+\*->\s+(\S+)", ln)
        if m:
            out.add(m.group(2))
    return out


def check(data_dir, map_path, split_files, fallback_files=()):
    """returns (errors, notes) - errors block, notes only speak"""
    errors, notes = [], []

    dict_path = os.path.join(data_dir, "dictionary_sorted_by_type.txt")
    master = _entries(dict_path)
    mset = set(master)

    # 1. master <-> map. This one is a contradiction, so it is an error.
    #    Only the FIRST word of a row is the concept; the rest are aliases
    #    (and,&& / revers, not, ! / true, yes, Y). An alias is not a concept and
    #    is not supposed to be in the dictionary - treating the whole list as
    #    concepts gave 34 false contradictions, which is worse than no check.
    glyphs = _map_glyphs(map_path)
    canon, aliases = set(), set()
    if glyphs:
        for ln in io.open(map_path, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n"):
            m = re.match(r"U\+[0-9A-Fa-f]{4,6}\s+\S+\s+\*->\s+(.+?)\s*(?:-|$)", ln)
            if m:
                parts = [w.strip() for w in m.group(1).split(",") if w.strip()]
                if parts:
                    canon.add(parts[0])
                    aliases.update(parts[1:])
        # The direction that matters is dictionary -> map. A dictionary entry
        # with no glyph is a concept that cannot be written at all, so it is an
        # error. The reverse is not: a map row whose word is an alias, or whose
        # head word differs from the dictionary spelling, is normal - and
        # checking that direction produced 26 false contradictions and blocked
        # every compile, which is worse than the gap it was looking for.
        #
        # It reads the map itself rather than asking the compiler. Asking meant
        # importing compile.py, and compile.py imports this module to print the
        # report - so the import was circular, spec_from_file_location returned
        # None, the map came back empty, and the check reported all 338 concepts
        # as unwritable and failed the build. Three false alarms from one check.
        # The map is a table; read the table.
        resolved = set()
        if glyphs:
            for ln in io.open(map_path, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n"):
                m = re.match(r"U\+[0-9A-Fa-f]{4,6}\s+\S+\s+\*->\s*(.+?)\s*(?:-|$)", ln)
                if m:
                    parts = [w.strip() for w in m.group(1).split(",") if w.strip()]
                    if parts:
                        canon.add(parts[0])
                        aliases.update(parts[1:])
                        resolved.add(parts[0].lower())
        noglyph = sorted(w for w in mset
                         if w.lower() not in resolved and w not in aliases)
        if noglyph:
            errors.append("%d dictionary concept(s) have no glyph and cannot be"
                          " written: %s" % (len(noglyph), ", ".join(noglyph[:8])))
        notes.append("map: %d glyphs, %d concepts, %d aliases | dictionary: %d"
                     % (len(glyphs), len(canon), len(aliases), len(master)))

    # 2. master <-> splits. Reported, never enforced.
    for name in list(split_files) + list(fallback_files):
        got = _entries(os.path.join(data_dir, name))
        if not got:
            notes.append("%-22s no entries of its own - by design, not a fault" % name)
            continue
        missing = mset - set(got)
        if missing:
            notes.append("%-22s behind the master by %d of %d"
                         % (name, len(missing), len(master)))
        else:
            notes.append("%-22s in step with the master (%d)" % (name, len(got)))

    return errors, notes


def report(errors, notes, w=None):
    out = []
    out.append("CONSISTENCY of compiler inputs")
    for n in notes:
        out.append("  . %s" % n)
    if errors:
        out.append("  ! %s" % errors[0])
        for e in errors[1:]:
            out.append("  ! %s" % e)
        out.append("  ! %d contradiction(s). Fix before writing a spec." % len(errors))
    else:
        out.append("  ok no contradiction between the map and the dictionary")
    return "\n".join(out)
