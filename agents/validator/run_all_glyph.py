# -*- coding: utf-8 -*-
"""run every glyph tool and report one line each

Nine tools, run together, so a green that depends on one of them staying green
is visible. Each line says what it can and cannot see, because a tool that
reports only a verdict is the thing this whole session was about.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

TOOLS = [
    ("glyph_checker.py", "9 чеков на глифном слое"),
    ("spell_checker_v2.py", "13 чеков, читают слова"),
    ("dict_edit.py", "инварианты базы"),
    ("check_agent_glyphs.py", "глифы в файлах агента"),
    ("id_alloc.py", "аллокатор id"),
    ("count_space.py", "сколько комбинаций даёт алфавит"),
    ("count_room.py", "свободное место под id"),
    ("find_triangles.py", "треугольники свободны"),
    ("frames.py", "инвентарь рамок"),
    ("test_id_blur.py", "теория слипания id"),
    ("check_artifact_ids.py", "id у proto и blueprint"),
    ("spec_index.py", "индекс спек"),
    ("convert_abs" "tract.py", "перевод абстракта в глифы"),
]

for name, what in TOOLS:
    path = os.path.join(ROOT, "validator", name)
    if not os.path.exists(path):
        print("  %-26s НЕТ ФАЙЛА   %s" % (name, what))
        continue
    args = [PY, "-X", "utf8", path]
    if name == "dict_edit.py":
        args.append("verify")
    if name == "id_alloc.py":
        args += ["--n", "4"]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    out = (r.stdout or "") + (r.stderr or "")
    key = None
    for pat in ("VERDICT", "инварианты", "ВЕРДИКТ", "пространство", "нужно 6",
                "ВНИМАНИЕ", "абстрактов", "свободных"):
        for l in out.split("\n"):
            if pat in l:
                key = l.strip()
                break
        if key:
            break
    print("  %-26s %s" % (name, (key or "нет вывода")[:72]))
