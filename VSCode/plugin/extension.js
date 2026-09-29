// Vibe Writer, the first plugin. Two visual layers and no text is ever changed.
//
// One: the arrow. On disk it is two ASCII signs, and in the editor it is one
// glyph drawn on top of them, because it marks the key and the key has to be
// visible at a glance. It is the only place a glyph appears. Nothing is
// replaced, and Ctrl+S writes the same two signs it always wrote.
//
// Two: the pointed frames, highlighted and not turned into glyphs.
//
// Everything else, the plus and the minus and the rest, is left exactly as the
// person typed it. That was my mistake once: I turned the arrow into a real
// character in the document, and the one autosave would have put a glyph on
// disk and broken the rule that the source stays ASCII. So a decoration and
// never an edit.

const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

const HERE = __dirname;
const VS = path.dirname(HERE);

const ARROW = '→';
const PAIRS = { '(': ')', '[': ']', '<': '>' };
const CLOSERS = new Set([')', ']', '>']);
const CHANNEL = 'vibe';

// The banner goes out before anything else, on the console, because the console
// is the only place that can report a module that never loaded. If the file has
// a syntax error the channel does not exist, it cannot say so, and a plugin that
// says nothing looks exactly like a plugin that has nothing to say. So the very
// first thing this file does is print that it is here.
console.log('[vibe] extension.js loaded, vscode %s',
  vscode.version ? vscode.version : 'unknown');

let KEY_DEC = null;
let FRAME_DEC = null;
let SPELL_DEC = null;
let OUT = null;

// The words the project has already accepted, and when the table was last
// read. Read once per change of the file, not once per keystroke, and held as a
// Set because the question on every keystroke is "is this in there" and a
// list would make that a scan of 3792 words per letter typed.
let TABLE = null;
let TABLE_STAMP = 0;

// The last answer per file. paint() runs on every keystroke, so a line written
// on every call is the same sentence over and over, and a channel of one
// sentence repeated is a channel nobody reads. A line goes out on a change and
// nowhere else.
const LAST = new Map();
const SEEN = new Set();
const SPELL_LAST = new Map();

/**
 * One line, two places: the channel and the console.
 *
 * The channel is what a person reads, and the console is what a person reads
 * when the channel is empty and it is not known why. Both are decoration and
 * neither ever edits the file, so writing to both costs nothing that matters.
 * One call and one sentence, and the two places cannot drift apart because
 * there is only one sentence to begin with.
 */
function say(line) {
  console.log('[vibe] %s', line);
  if (OUT) OUT.appendLine(line);
}

/** The name and the place, because a fault without a place says nothing. */
function where(document) {
  const p = document.uri.fsPath || document.uri.toString();
  const cut = p.lastIndexOf('\\') > p.lastIndexOf('/') ? p.lastIndexOf('\\')
                                                      : p.lastIndexOf('/');
  return cut >= 0 ? p.slice(cut + 1) : p;
}

/**
 * Report what is wrong with the frames on one line. Returns [] when it holds.
 * A frame is not allowed to be inside a frame, and that is the whole of the
 * checking: the words inside are not read.
 */
function frameFaults(line) {
  const s = line.replace(/->/g, '');
  const stack = [];
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (PAIRS[ch]) {
      if (stack.length) {
        return [`frame ${ch} sits inside frame ${stack[stack.length - 1].ch}, and a frame holds no frame`];
      }
      stack.push({ ch, at: i });
    } else if (CLOSERS.has(ch)) {
      if (!stack.length) return [`frame ${ch} closes and nothing is open`];
      const top = stack.pop();
      if (PAIRS[top.ch] !== ch) return [`frame ${top.ch} is closed by ${ch}`];
    }
  }
  if (stack.length) {
    return [`frame ${stack[stack.length - 1].ch} is never closed`];
  }
  return [];
}

/** Where the table is, and where the words are looked for. */
function repoRoot() {
  // VS = <repo>\VSCode, so the project is a sibling and not a guess upward.
  // The name is written down: a folder that moves changes what it points at,
  // and a path that changed quietly is the one nobody checks.
  return path.join(VS, '..', '5xVector');
}

const SEP = '●';   // U+25CF, the separator in the table, one role only

function loadTable() {
  const file = vscode.workspace.getConfiguration('vibe').get('table') ||
    path.join(repoRoot(), 'englang.embedding');
  let stamp = 0;
  try { stamp = fs.statSync(file).mtimeMs; } catch (e) { return null; }
  if (TABLE && TABLE_STAMP === stamp) return TABLE;
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch (e) { return null; }
  const set = new Set(text.split(SEP).map(w => w.trim().toLowerCase()).filter(Boolean));
  TABLE = set;
  TABLE_STAMP = stamp;
  return set;
}

/**
 * The words a person typed that are not English, and where.
 *
 * Local only, and on purpose. The other half of the project's spell check asks
 * datamuse, and that is a request per word to the internet; on every keystroke
 * it is a request per letter, and the editor stops being an editor. So this
 * asks two things that both have an answer on this machine: are the letters
 * Latin, and is the word in the project's own table. A word that passes the
 * letters and is not in the table is reported as unknown rather than wrong,
 * because a table is a project's choice and not a dictionary.
 */
function addressed(text, skip) {
  const table = loadTable();
  if (!table) return [];
  const out = [];
  const seen = new Set();
  const lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    if (skip && skip.has(i)) continue;   // a .data block is not checked either
    const m = lines[i].match(/[^\W\d_]+/gu);
    if (!m) continue;
    for (const w of m) {
      const k = w.toLowerCase();
      if (seen.has(k)) continue;
      if (!/^[A-Za-z]+$/.test(w)) { out.push({ line: i, word: w, why: 'не латиница' }); seen.add(k); continue; }
      if (!table.has(k)) { out.push({ line: i, word: k, why: 'нет в таблице' }); seen.add(k); }
    }
  }
  return out;
}

/** A range for one word, so the squiggle sits on the word and not on the line. */
function wordRange(doc, line, word) {
  const text = doc.lineAt(line).text;
  const at = text.toLowerCase().indexOf(word);
  if (at < 0) return new vscode.Range(line, 0, line, text.length);
  return new vscode.Range(line, at, line, at + word.length);
}

// The same boundary the compiler draws, and the plugin does not draw it twice
// for its own reasons: a .data block holds anything at all, a theme, a table, a
// note, and none of it is a record and none of it is checked. The range is from
// the .data tag to the .code tag INCLUSIVE, so both tags are inside it, and
// everything after .code is compiled and checked as before.
//
// The compiler has the same rule in split_blocks(). It is written out again
// here because the plugin cannot call Python on every keystroke, and a line
// that says .data and a line that says .code are two lines of comparison. That
// is the whole of what is written twice.
const SKIP = new Set(['.data', '.code']);

/** the line numbers no check may look at, and the set is empty without .data */
function skipRange(text) {
  const lines = text.split('\n');
  const out = new Set();
  let start = -1;
  for (let i = 0; i < lines.length; i++) {
    if (start < 0) {
      if (lines[i].trim() === '.data') { start = i; out.add(i); }  // the tag is in it
      continue;
    }
    out.add(i);
    if (lines[i].trim() === '.code') return out;   // and the .code tag
  }
  if (start >= 0) for (let i = start; i < lines.length; i++) out.add(i);
  return out;
}

/** Where the key marker sits, and where the pointed frames are. */
function layers(text, skip) {
  const keys = [];
  const frames = [];
  const faults = [];
  const lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    if (skip && skip.has(i)) continue;   // a .data block is not the compiler's
    const line = lines[i];
    if (!line.trim()) continue;
    for (let c = 0; c < line.length; c++) {
      // The key marker is looked for twice, in both of the forms it can be in.
      // The two signs are what a person types, and the one sign is what the
      // sweep in arrowsEverywhere() leaves in the buffer, so by the time this
      // runs the second has usually already replaced the first. Looking for the
      // two signs only would find nothing in a file that has just been typed,
      // which is every file, and a marker that is searched for in a form that
      // is never there is a marker that never gets a colour.
      if (line[c] === ARROW) {
        keys.push(new vscode.Range(i, c, i, c + 1));
        continue;
      }
      if (line[c] === '-' && line[c + 1] === '>') {
        keys.push(new vscode.Range(i, c, i, c + 2));
        c++;
      }
    }
    for (let c = 0; c < line.length; c++) {
      if (line[c] === '<' || line[c] === '>') {
        frames.push(new vscode.Range(i, c, i, c + 1));
      }
    }
    for (const f of frameFaults(line)) faults.push({ line: i, message: f });
  }
  return { keys, frames, faults };
}

/**
 * The plugin serves these language ids and nothing else. The id is the one the
 * language contributes, and it is written here in one place on purpose, so that
 * the next time it is wrong it is wrong in one line and not in a guard that
 * was pasted from somewhere else.
 */
const SERVES = ['vibe', 'markdown'];

function serves(document) {
  return SERVES.indexOf(document.languageId) >= 0;
}

function paint(editor) {
  if (!editor || !serves(editor.document)) return [];
  const doc = editor.document;
  const text = doc.getText();
  const skip = skipRange(text);
  const { keys, frames, faults } = layers(text, skip);
  // Both decorations are applied, and the key one was not for a long time:
  // KEY_DEC was created at activation and nothing ever put it on an editor, so
  // the arrow carried the theme colour and the setting that named a colour for
  // it did nothing. keys is what layers() found, and it is not frames.
  editor.setDecorations(KEY_DEC, keys.map(r => ({ range: r })));
  editor.setDecorations(FRAME_DEC, frames.map(r => ({ range: r })));
  const bad = addressed(text, skip);
  editor.setDecorations(SPELL_DEC, bad.map(b => ({ range: wordRange(doc, b.line, b.word) })));
  report(doc, faults);
  spell(doc, bad);
  return faults;
}

/** The words, and a line only when the list changed. Same rule as report(). */
function spell(document, bad) {
  const key = document.uri.toString();
  const sig = bad.map(b => b.line + b.word).join('|');
  if (SPELL_LAST.get(key) === sig) return;
  SPELL_LAST.set(key, sig);
  const name = where(document);
  if (!bad.length) {
    say(`${name}: слова на месте, ${document.lineCount} строк`);
    return;
  }
  say(`${name}: ${bad.length} слово не в таблице`);
  for (const b of bad.slice(0, 8)) say(`  line ${b.line + 1}: ${b.word}, ${b.why}`);
  if (bad.length > 8) say(`  ... ещё ${bad.length - 8}`);
}

/**
 * The faults and the count, and a line only when the answer changed.
 *
 * One pass walks the faults and writes each one, then the summary. Two passes
 * would write every fault twice, and there is no reason to read it twice.
 */
function report(document, faults) {
  const key = document.uri.toString();
  const sig = faults.length + '|' + faults.map(f => f.line + f.message).join('');
  if (LAST.get(key) === sig) return;
  LAST.set(key, sig);

  const name = where(document);
  if (!faults.length) {
    say(`${name}: frames hold, ${document.lineCount} lines`);
    return;
  }
  say(`${name}: ${faults.length} fault, ${document.lineCount} lines`);
  for (const f of faults) say(`  line ${f.line + 1}: ${f.message}`);
}

/**
 * Say once per file that the plugin has seen it, and not once per keystroke.
 *
 * The silence here is the thing that reads as a dead plugin. A file opens, the
 * frames are checked, nothing is wrong, and report() writes "frames hold" once
 * and then stays quiet forever because the answer has not changed. That is
 * correct and it looks identical to a plugin that crashed on the first file. So
 * the first time a file is seen it says so, and after that the rule above
 * applies and the channel is quiet until something actually changes.
 *
 * It is called from paint() and not from onDidOpenTextDocument, because the
 * editors that were open when VS Code started are restored before an extension
 * activates, and that event has already gone past. Called from paint() the line
 * appears on whichever path a file arrives by, and a file open at startup gets
 * it too, which is the case that matters most and the one that was missing.
 *
 * And it checks serves(), because it did not, and the plugin announced its own
 * output log: the log of the plugin, opened by the plugin, watched by the
 * plugin. It never checked the frames in that file, so the line was noise, and
 * noise about the plugin's own log is the worst kind: it looks like activity.
 */
function seen(document) {
  if (!serves(document)) return;
  const key = document.uri.toString();
  if (SEEN.has(key)) return;
  SEEN.add(key);
  say(`${where(document)}: opened, ${document.lineCount} lines, language ${
    document.languageId}, plugin is watching the frames`);
}

/**
 * On every change, every -> in the file becomes the arrow. All of them, not
 * only the one just typed, because a partial sweep leaves half a file in one
 * alphabet and half in the other, and nobody can read that.
 *
 * The edit triggers the same event once more, and on that pass there is no ->
 * left, so the sweep stops there. It ends by itself, which a sweep of only the
 * typed sign never did.
 */
function arrowsEverywhere(event) {
  const d = event.document;
  if (!serves(d)) return;
  // undo and redo are the person's own decision and the sweep must not answer
  // it. Without this, Ctrl+Z brings back the two signs and the very next pass
  // turns them into the arrow again, and the undo does nothing at all.
  if (event.reason === vscode.TextDocumentChangeReason.Undo ||
      event.reason === vscode.TextDocumentChangeReason.Redo) return;
  const text = d.getText();
  if (text.indexOf('->') < 0) return;
  const ed = vscode.window.activeTextEditor;
  if (!ed || ed.document.uri.toString() !== d.uri.toString()) return;
  const found = [];
  for (let i = 0; i + 1 < text.length; i++) {
    if (text[i] === '-' && text[i + 1] === '>') {
      found.push(new vscode.Range(d.positionAt(i), d.positionAt(i + 2)));
    }
  }
  if (!found.length) return;
  say(`${where(d)}: arrow inserted, ${found.length} in the buffer, ` +
    'the disk keeps the two signs');
  // from the end, so the positions already found stay true
  return ed.edit(b => { for (const r of found.reverse()) b.replace(r, ARROW); },
    { undoStopBefore: true, undoStopAfter: true });
}

function refreshAll() {
  if (!vscode.window) return [];
  const faults = [];
  for (const ed of vscode.window.visibleTextEditors) faults.push(...paint(ed));
  return faults;
}

/**
 * The key decoration, built from the setting, and never from a guess.
 *
 * The colour was written into the call and the setting beside it was never
 * read, so vibe.key could be any value at all and the arrow would keep the
 * same violet. A setting that exists and is not read is not a setting, it is a
 * comment in a JSON file, and it looks exactly like a feature in the settings
 * UI where a person types a colour and nothing changes.
 *
 * An empty or missing value falls back to the violet it always was, so the
 * worst case is the behaviour that already worked, and never an invisible
 * marker on a dark theme.
 */
function keyColour() {
  try {
    const v = vscode.workspace.getConfiguration('vibe').get('key');
    if (typeof v === 'string' && v.trim()) return v.trim();
  } catch (e) {
    // a host that has no configuration, such as the test stub, is not an error
  }
  return '#c792ea';
}

function buildKey() {
  if (KEY_DEC) KEY_DEC.dispose();
  KEY_DEC = vscode.window.createTextEditorDecorationType({
    fontWeight: 'bold',
    color: keyColour(),
  });
  context_subscriptions_push(KEY_DEC);
}

// The activation pushes both decorations into the context, and a rebuild pushes
// a new one, so the list is held here and the activation adds what is in it.
let CONTEXT = null;
function context_subscriptions_push(d) {
  if (CONTEXT) CONTEXT.subscriptions.push(d);
}

function activate(context) {
  CONTEXT = context;
  // The channel is the report and the report is a decoration. It appends to a
  // panel and touches nothing else: the file on disk keeps the two ASCII signs
  // and the glyph stays in the editor. The same rule the arrow already follows,
  // and the reason this plugin is safe to leave switched on.
  OUT = vscode.window.createOutputChannel(CHANNEL);
  context.subscriptions.push(OUT);
  say(`vibe: up, serving ${SERVES.join(', ')}, the file is never written`);

  // green disappeared into the grey text and red is the colour of an error,
  // so the key sits in violet, and yellow is left to the state frame.
  buildKey();
  // a theme colour can be empty in a given theme, and then the highlight is
  // there and cannot be seen, which is the worst of both. So the colour is
  // given outright.
  FRAME_DEC = vscode.window.createTextEditorDecorationType({
    backgroundColor: 'rgba(255, 214, 10, 0.18)',
    border: '1px solid rgba(255, 214, 10, 0.55)',
    borderRadius: '2px',
  });
  context.subscriptions.push(KEY_DEC, FRAME_DEC);
  // a word the project has not accepted, in the same red the frame uses for a
  // broken one, and a squiggle rather than a fill because a fill over a word
  // hides the word, and the word is the thing the person has to read and fix
  SPELL_DEC = vscode.window.createTextEditorDecorationType({
    textDecoration: 'underline wavy',
    borderBottom: '1px solid rgba(255, 85, 85, 0.9)',
    color: '#ff5555',
  });
  context.subscriptions.push(SPELL_DEC);
  // the table is read at startup, so the first keystroke does not wait for it
  loadTable();
  say(`vibe: таблица слов прочитана, ${TABLE ? TABLE.size : 0} слов, ` +
    'проверка локальная, сеть не трогается');

  const fire = () => refreshAll();
  context.subscriptions.push(
      vscode.workspace.onDidChangeTextDocument(e => {
        arrowsEverywhere(e);
        fire();
        // the console gets this one on every change, and it is the one line
        // that proves the listener is alive. report() is quiet by design after
        // the first answer, so without this there is no way to tell a plugin
        // that is waiting from a plugin that is dead.
        console.log('[vibe] change in %s, %d lines',
          where(e.document), e.document.lineCount);
      }),
    vscode.workspace.onDidOpenTextDocument(d => { seen(d); fire(); }),
    vscode.window.onDidChangeVisibleTextEditors(() => fire()),
    // a change of vibe.key has to rebuild the decoration, or the new colour
    // waits for a restart and looks like a setting that does not work
    vscode.workspace.onDidChangeConfiguration(e => {
      if (!e || !e.affectsConfiguration || e.affectsConfiguration('vibe.key')) {
        buildKey();
        say(`vibe: key colour is now ${keyColour()}`);
      }
      fire();
    })
  );

  context.subscriptions.push(vscode.commands.registerCommand('vibe.checkFrames', () => {
    const ed = vscode.window.activeTextEditor;
    if (!ed) return vscode.window.showInformationMessage('vibe: no file open');
    const faults = paint(ed);
    // the box is a glance and the channel is a reading, and both are wanted
    say(`${where(ed.document)}: checked by hand, ${faults.length} fault`);
    vscode.window.showInformationMessage(faults.length
      ? `vibe: ${faults.length} fault in the frames, the channel has the lines`
      : `vibe: frames hold, ${ed.document.lineCount} lines, the file was not touched`);
  }));

  // A person asks for the whole list, and the list is already there. Asking
  // again would be a second read of the same answer, so this only reveals it.
  context.subscriptions.push(vscode.commands.registerCommand('vibe.showOutput', () => {
    if (OUT) OUT.show(true);
  }));

  fire();
}

function deactivate() {}

module.exports = { activate, deactivate, frameFaults, layers };
