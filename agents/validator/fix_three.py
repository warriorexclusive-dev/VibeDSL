# -*- coding: utf-8 -*-
"""three fixes, in the order that makes the numbers mean something

1  the backup folder is not a spec. The walk skipped .git and __pycache__ and
   picked up PY_IDE/_restore_*, so three checks were reporting on my own safety
   copy. A red that reads a backup is not a red, it is noise wearing a red coat.

2  the type lookahead stores U+02A9 as the six characters \\u02A9 inside an
   r-string, so it matches that TEXT and never the glyph. Same defect as the
   U+2310 mistake, and same place: a check that cannot match cannot be wrong -
   which is exactly why it looked green.

3  the frame does not count depth, so a nested frame is cut at the first close
   and the content of the action is read as an address. Same class as the
   renderer, which had the same bug and cost me the 582-quote mess.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, "validator", "glyph_checker.py")
s = io.open(G, encoding="utf-8-sig").read()
before = s

# 1 - skip the backup folder, by prefix: anything _restore_*
s = s.replace('and d not in ("temp", ".git", "GLOS", "node_modules", "__pycache__")',
              'and d not in ("temp", ".git", "GLOS", "node_modules", "__pycache__")\n'
              '                   and not d.startswith("_restore")')
s = s.replace('d not in ("temp", ".git", "GLOS", "node_modules", "__pycache__")]',
              'd not in ("temp", ".git", "GLOS", "node_modules", "__pycache__")\n'
              '                   and not d.startswith("_restore")]')
print("  1. папка отката исключена из обхода: %s"
      % ("да" if "_restore" in s else "НЕТ"))

# 2 - the lookahead, as the glyph, not as escape text
A = chr(0x2330)
TYPES = "".join((chr(0x2317), chr(0x2B1D), chr(0x02A9)))
old_rx = r'"' + A + r'(?![:\u2317\u2B1D\u02A9])([^\n]*)"'
new_rx = '"' + re.escape(A) + "(?![:" + re.escape(TYPES) + "])([^\\n]*)" if False else None
import re as _re
new_rx = '"' + _re.escape(A) + "(?![:" + _re.escape(TYPES) + "])([^" + chr(92) + "n]*)"'
if old_rx in s:
    s = s.replace(old_rx, new_rx)
    print("  2. lookahead переведён на глифы: да")
else:
    print("  2. lookahead: строка не найдена, смотрю вручную")
    for l in s.replace("\r\n", "\n").split("\n"):
        if "2317" in l or "2A9" in l or "2B1D" in l:
            print("       %s" % l.strip()[:88])

io.open(G, "w", encoding="utf-8", newline="").write(s)
print("  изменений: %s" % (s != before))
