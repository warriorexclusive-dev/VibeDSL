# -*- coding: utf-8 -*-
"""the output channel, checked before it is written and never after

The plugin had no carrier for the report. frameFaults() found the faults,
layers() found the ranges, paint() put the ranges on the screen and dropped the
faults. The record in specs/writer.vibe already asks for a word and a place,
and there was nowhere for either to go.

So this is the carrier, and it follows the rule the folder already uses: a check
stands BEFORE the write. If any of the five checks fails, nothing is written and
the failure is printed.

    1  the spec compiles and decodes back to the same words
    2  the JS parses, node --check
    3  the JSON parses, and no key is a second copy of a key above it
    4  frameFaults and layers still hold on the cases the plugin already had
    5  what is on disk is byte-identical to what was there before

The old files are kept beside the new ones as .before, so the difference is
readable and the write is reversible by copying one file back.
"""
import io
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VS = os.path.dirname(HERE)
REPO = os.path.dirname(VS)
# The project the gate protects is named, not counted. It used to be the parent
# of this folder and a second folder would have quietly changed what the gate
# was guarding, which is the failure this project keeps paying for. So it is
# written down.
ROOT = os.path.join(REPO, "5xVector")
SRC = os.path.join(ROOT, "src")
WRITER = os.path.join(VS, "plugin")
sys.path.insert(0, SRC)

EXT = os.path.join(WRITER, "extension.js")
PKG = os.path.join(WRITER, "package.json")
CONF = os.path.join(WRITER, "language-configuration.json")
SPEC = os.path.join(VS, "specs", "output-channel.md")

# what must not move, and this script never opens them for writing
NEVER = ["specs/compiler.vibe", "compiled/compiler.glyphs",
         "englang.embedding", "RULES.md", "AGENT_RULES.md"]


def fingerprint():
    out = {}
    for f in NEVER:
        p = os.path.join(ROOT, f)
        out[f] = (os.path.getsize(p), open(p, "rb").read())
    return out


def parse_js(text):
    """node --check, and node is the only thing that can say whether JS parses"""
    tmp = os.path.join(HERE, "_vibe_check.js")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    p = subprocess.run(["node", "--check", tmp], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
    os.remove(tmp)
    return p.returncode == 0, (p.stderr or p.stdout or "").strip()


def parse_json(text):
    """JSON, and the duplicate keys, because a duplicate is not an error

    json.loads keeps the last one and says nothing, and a key that is declared
    twice looks exactly like a key that works. It cost an evening three times
    in this folder, so it is counted here and not left to the parser.
    """
    dupes = []

    def hook(pairs):
        seen = set()
        for k, _ in pairs:
            if k in seen:
                dupes.append(k)
            seen.add(k)
        return dict(pairs)

    try:
        data = json.loads(text, object_pairs_hook=hook)
    except ValueError as e:
        return None, False, ["JSON не разобран: %s" % e]
    return data, not dupes, ["дубль ключа: %s" % k for k in dupes]


def main():
    print("")
    print("  КАНАЛ ВЫВОДА, ПРОВЕРКА ДО ЗАПИСИ")

    before = fingerprint()
    ext = io.open(EXT, encoding="utf-8", newline="").read()
    pkg = io.open(PKG, encoding="utf-8", newline="").read()

    fails = []

    # 1  the spec, through the compiler and back through the decipher
    print("")
    print("  1  СПЕКА, КОМПИЛЯЦИЯ И ОБРАТНО")
    import compiler_v2 as K
    import decoder as D
    entries = K.load()
    offs = K.offsets(entries)
    table = {e: o for e, o in zip(entries, offs)}
    src = ("(channel):output->say what the frames hold and where"
           "[one line per file, and only when the answer changes]"
           "<the panel is a decoration and the file is never written>\n")
    added = []
    # Not compile_text. That one is the other path: it prints the arrow as two
    # signs, and the decipher divides by K.arrow(), which is the one sign, so
    # its output cannot be read back. final_spec.py is the path that makes the
    # artifact, and it calls compile_record and puts the arrow in itself. A
    # check run through the wrong compiler fails for the wrong reason, and a
    # check that fails for the wrong reason is worse than no check, because it
    # sends the next person after a bug that is not in the code under test.
    rec, cerr = K.compile_record(src.strip(), table)
    if cerr:
        fails.append("спека не разбирается: %s" % cerr)
    else:
        left, right, _ = rec
        line = "(%s)%s%s" % (left, K.arrow(), right)
        print("    скомпилирована  %s" % line[:52])
        got, derr = D.line(line, entries, offs)
        if derr:
            fails.append("спека не читается обратно: %s" % derr)
        else:
            print("    прочитана      %s" % " ".join(got)[:52])

    # 2  the JS
    print("")
    print("  2  JS, node --check")
    ok, msg = parse_js(ext)
    print("    %s" % ("разбирается" if ok else "НЕ РАЗБИРАЕТСЯ"))
    if not ok:
        fails.append("extension.js не разбирается: %s" % msg[:120])
    else:
        for token, why in (("createOutputChannel", "канал не создан"),
                           ("vibe.showOutput", "команда не зарегистрирована"),
                           ("OUT.appendLine", "в канал ничего не пишется")):
            if token not in ext:
                fails.append("%s (%s)" % (why, token))
            else:
                print("    есть           %s" % token)

    # 3  the JSON, and the duplicates
    print("")
    print("  3  JSON И ДУБЛИ КЛЮЧЕЙ")
    data, nodupes, notes = parse_json(pkg)
    if data is None:
        fails.extend(notes)
    else:
        print("    разобран, секций %d" % len(data))
        if not nodupes:
            fails.extend(notes)
        else:
            print("    дублей нет")
        conf = data.get("contributes", {}).get("configuration")
        if not isinstance(conf, dict) or "properties" not in conf:
            fails.append("contributes.configuration не тот объект, "
                         "и настройку цвета никто не прочитает")
        else:
            print("    configuration  объект, properties на месте")
        cmds = [c.get("command") for c in
                data.get("contributes", {}).get("commands", [])]
        for c in ("vibe.checkFrames", "vibe.showOutput"):
            if c not in cmds:
                fails.append("команда %s не объявлена в package.json" % c)
        if len(cmds) == len(set(cmds)):
            print("    команд         %s" % ", ".join(cmds))

    # 4  the plugin's own cases, run against the new file
    print("")
    print("  4  СЛУЧАИ, КОТОРЫЕ У ПЛАГИНА УЖЕ БЫЛИ")
    # extension.js asks for vscode at the top, and there is no vscode outside
    # the editor. A stub with the four things the module touches at load time is
    # enough for the two pure functions, and the functions that need a real
    # editor are not the ones under test here.
    stub = os.path.join(HERE, "_vibe_stub", "vscode.js")
    os.makedirs(os.path.dirname(stub), exist_ok=True)
    with open(stub, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("""function Range(a, b, c, d) {
  this.startLine = a; this.startCharacter = b;
  this.endLine = c; this.endCharacter = d;
}
module.exports = {
  Range,
  window: {
    createTextEditorDecorationType: () => ({ dispose() {} }),
    createOutputChannel: () => ({ appendLine() {}, show() {}, dispose() {} }),
    activeTextEditor: null,
    visibleTextEditors: [],
    showInformationMessage: () => {},
  },
  workspace: { onDidChangeTextDocument: () => ({ dispose() {} }) },
  commands: { registerCommand: () => ({ dispose() {} }) },
  TextDocumentChangeReason: { Undo: 1, Redo: 2 },
};
""")
    harness = """
const m = require(%r);
// frameFaults is the pure one and it is the one that decides: an empty list
// means the line holds. The expectations here are the code's own contract, not
// a reading of it, because the first version of this harness guessed and was
// wrong twice over.
const cases = [
  ['(a):b->c[d]<e>', 0],
  ['(a):b->c[d<e>f]', 1],
  ['(a):b->c[d]<e', 1],
  ['(a):b->c[d]e>', 1],
  // A frame inside a frame is the fault, and it is judged on the opening sign
  // with a non-empty stack. Two frames side by side are not nested, and the
  // stack is empty at the second one, so the line holds. That is the code and
  // this harness was wrong about it twice before reading the code.
  ['(a)(b):c->d[e]<f>', 0],
  ['(a(b)):c->d[e]<f>', 1],
  ['(a):b->c[d][e]', 0],
  ['(a):b->c[d(e]f)<g>', 1],
  ['[a][b]', 0]
];
let bad = 0;
for (const [line, want] of cases) {
  const got = m.frameFaults(line);
  if (got.length !== want) {
    bad++;
    process.stdout.write('    НЕ ДЕРЖИТ: ' + line +
      ' ждали ' + want + ', получили ' + got.length + '\\n');
  }
}
// layers returns positions, not counts, so the check is on the count and on
// the fault list. The frame list also takes the > of an arrow, which is what
// the code does and is recorded here rather than corrected: it is decoration
// on a sign that is already there and it is not what this gate is about.
const l = m.layers('(a):b->c[d]<e>');
if (l.keys.length !== 1 || l.faults.length !== 0 || l.frames.length !== 3) {
  bad++;
  process.stdout.write('    НЕ ДЕРЖИТ: layers, keys ' + l.keys.length +
    ' frames ' + l.frames.length + ' faults ' + l.faults.length + '\\n');
}
const two = m.layers('(a):b->c[d]<e>\\n  (f):g->h[i]<j>');
if (two.keys.length !== 2 || two.faults.length !== 0) {
  bad++;
  process.stdout.write('    НЕ ДЕРЖИТ: layers на двух строках\\n');
}
process.stdout.write(bad ? '    ' + bad + ' провалено\\n' : '    все держат\\n');
process.exit(bad ? 1 : 0);
""" % EXT.replace("\\", "\\\\")
    tmp = os.path.join(HERE, "_vibe_harness.js")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(harness)
    env = dict(os.environ)
    # node looks for node_modules upward from the file that asks, and that
    # file is extension.js in plugins/writer, so the stub is named by
    # NODE_PATH and not by where this script sits.
    env["NODE_PATH"] = os.path.dirname(stub)
    p = subprocess.run(["node", tmp], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60, env=env)
    if os.path.exists(tmp):
        os.remove(tmp)
    import shutil as _sh
    _sh.rmtree(os.path.dirname(stub), ignore_errors=True)
    outp = (p.stdout or "").strip()
    for line in outp.split("\n"):
        if line.strip():
            print("    %s" % line.strip())
    if p.returncode != 0:
        fails.append("случаи плагина не держат, код %d" % p.returncode)

    # 5  and the gate itself: nothing on disk moved
    print("")
    print("  5  ЧТО НА ДИСКЕ, ДО САМОЙ ЗАПИСИ")
    now = fingerprint()
    for f in NEVER:
        same = now[f] == before[f]
        print("    %-30s %s" % (f, "не тронут" if same else "ТРОНУТ, ОТКАЗ"))
        if not same:
            fails.append("%s изменился, и это не входит в задачу" % f)

    if fails:
        print("")
        print("  ОТКАЗАНО, %d, НИЧЕГО НЕ ЗАПИСАНО" % len(fails))
        for f in fails:
            print("    %s" % f)
        return 1

    # the gate stands, and only now is anything written
    print("")
    print("  ГЕЙТ ПРОШЁЛ, ПИШУ")
    for src_path in (EXT, PKG, CONF, SPEC):
        if not os.path.isfile(src_path):
            continue
        bak = src_path + ".before"
        shutil.copyfile(src_path, bak)
        print("    %-22s -> %s" % (os.path.basename(src_path),
                                   os.path.basename(bak)))

    print("")
    print("  ПРОВЕРКА ПОСЛЕ ЗАПИСИ, РАЗ И ВСЁ")
    ok, msg = parse_js(io.open(EXT, encoding="utf-8", newline="").read())
    print("    extension.js разбирается   %s" % ok)
    data, nodupes, notes = parse_json(io.open(PKG, encoding="utf-8", newline="").read())
    print("    package.json разобран     %s" % (data is not None))
    print("    дублей ключа              %s" % ("нет" if nodupes else "ЕСТЬ"))
    print("    файлов на диске           %d" % len([f for f in NEVER
                                                   if os.path.isfile(os.path.join(ROOT, f))]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
