// Vibe Panel. Six buttons, and every one of them goes through the proxy.
//
// A proxy and not Ollama, on purpose: an answer that left nothing in the log is
// an answer nobody can trace, and the log is the whole reason the proxy exists.
// A button that reached Ollama directly would be one click and no record.
//
// No dependencies. VS Code gives this process node, and http and child_process
// are what is needed; a panel that pulled a library to read a JSON file would
// be a panel with a version to keep in step with the editor.

const vscode = require('vscode');
const http = require('http');
const https = require('https');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const HERE = __dirname;
const VS = path.dirname(HERE);
const REPO = path.dirname(VS);
const ROOT = path.join(REPO, '5xVector');
const BRIDGE = path.join(VS, 'tools', 'compile_bridge.py');
const MODELS_JSON = path.join(VS, 'config', 'models.json');
const LOGDIR = path.join(VS, 'log');

let view = null;
let model = '';          // the model the buttons act on
let compiled = '';       // what run sends, so a compile is not repeated
let compiledFrom = '';   // the file it came from, so it is never stale silently

// ---------------------------------------------------------------- the config
function cfg() {
  let c = { port: 11435, ollama: 'http://127.0.0.1:11434' };
  try {
    const raw = JSON.parse(fs.readFileSync(path.join(VS, 'config', 'proxy.json'), 'utf8'));
    if (raw.port) c.port = raw.port;
    if (raw.ollama) c.ollama = raw.ollama;
  } catch (e) { /* no config, the defaults are the conventions */ }
  return c;
}

// ---------------------------------------------------------------- the proxy
function ask(method, p, body, cb) {
  const c = cfg();
  const data = body ? Buffer.from(JSON.stringify(body), 'utf8') : null;
  const lib = c.ollama.startsWith('https') ? https : http;
  const req = lib.request({
    hostname: '127.0.0.1',
    port: c.port,
    path: p,
    method: method,
    headers: Object.assign(
      { 'Content-Type': 'application/json; charset=utf-8' },
      data ? { 'Content-Length': data.length } : {}),
  }, res => {
    const chunks = [];
    res.on('data', d => chunks.push(d));
    res.on('end', () => {
      const text = Buffer.concat(chunks).toString('utf8');
      let parsed = null;
      try { parsed = JSON.parse(text); } catch (e) { /* not json, show it raw */ }
      cb(null, parsed, text, res.statusCode);
    });
  });
  req.on('error', e => cb(e, null, '', 0));
  if (data) req.write(data);
  req.end();
}

// ---------------------------------------------------------------- the bridge
function python() {
  const set = vscode.workspace.getConfiguration('vibe.panel').get('python');
  if (set) return set.split(' ');
  return os.platform() === 'win32' ? ['py', '-3'] : ['python3'];
}

function bridge(args, cb) {
  const cmd = python();
  const p = spawn(cmd[0], cmd.slice(1).concat([BRIDGE].concat(args)),
    { cwd: VS, windowsHide: true });
  const out = [];
  const err = [];
  p.stdout.on('data', d => out.push(d));
  p.stderr.on('data', d => err.push(d));
  p.on('error', e => cb(e, null));
  p.on('close', code => {
    // the bridge answers in UTF-8 and says so itself; the buffer is decoded
    // here rather than left to the pipe, which on Windows would be cp1251 and
    // would turn every glyph into a question mark
    const text = Buffer.concat(out).toString('utf8');
    if (!text.trim()) {
      return cb(new Error(Buffer.concat(err).toString('utf8') || 'мост молчит'), null);
    }
    let parsed = null;
    try { parsed = JSON.parse(text); } catch (e) { /* reported below */ }
    if (parsed) return cb(null, parsed);
    cb(new Error('мост ответил не JSON: ' + text.slice(0, 120)), null);
  });
}

// ---------------------------------------------------------------- the answer
function say(html, cls) {
  if (view) view.webview.postMessage({ type: 'say', html: html, cls: cls || '' });
}

function log(line) {
  console.log('[vibe] ' + line);
  say('<div class="line">' + esc(line) + '</div>', 'plain');
}

function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function newPanel() {
  const models = modelOptions();
  return `<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body { font: 12px var(--vscode-font-family); color: var(--vscode-foreground);
         padding: 8px; }
  select, textarea, button, input { width: 100%; box-sizing: border-box;
         margin: 3px 0 7px; font-family: inherit; font-size: 12px;
         color: var(--vscode-input-foreground);
         background: var(--vscode-input-background);
         border: 1px solid var(--vscode-panel-border); padding: 4px; }
  textarea { min-height: 74px; resize: vertical; }
  .row { display: flex; gap: 5px; }
  .row button { margin: 3px 0; }
  button { cursor: pointer; background: var(--vscode-button-background);
           color: var(--vscode-button-foreground); border: none; padding: 5px; }
  button:hover { background: var(--vscode-button-hoverBackground); }
  #out { border-top: 1px solid var(--vscode-panel-border);
         margin-top: 8px; padding-top: 7px; max-height: 46vh; overflow: auto; }
  .line { white-space: pre-wrap; word-break: break-word; margin: 2px 0;
          font-family: var(--vscode-editor-font-family); }
  .bad { color: var(--vscode-errorForeground); }
  .good { color: var(--vscode-testing-iconPassed, #4ec9b0); }
  h4 { margin: 10px 0 4px; font-size: 11px; text-transform: uppercase;
       opacity: .7; }
</style></head><body>
  <h4>model</h4>
  <select id="model">${models}</select>
  <h4>prompt</h4>
  <textarea id="prompt" placeholder="что спросить у модели"></textarea>
  <h4>buttons</h4>
  <div class="row">
    <button id="models">models</button>
    <button id="model">model</button>
  </div>
  <div class="row">
    <button id="compile">compile</button>
    <button id="run">run</button>
  </div>
  <div class="row">
    <button id="settings">settings</button>
    <button id="log">log</button>
  </div>
  <div id="out"></div>
<script>
const vscode = acquireVsCodeApi();
let current = null;
document.getElementById('model').addEventListener('change', e => {
  current = e.target.value;
  vscode.postMessage({ type: 'pick', model: current });
});
for (const id of ['models','model','compile','run','settings','log']) {
  document.getElementById(id).addEventListener('click', () => {
    vscode.postMessage({ type: id, model: current });
  });
}
document.getElementById('prompt').addEventListener('input', e => {
  vscode.postMessage({ type: 'prompt', text: e.target.value });
});
window.addEventListener('message', ev => {
  const m = ev.data;
  if (m.type === 'say') {
    const d = document.createElement('div');
    d.className = 'line ' + (m.cls || '');
    d.innerHTML = m.html;
    document.getElementById('out').appendChild(d);
    document.getElementById('out').scrollTop = 1e9;
  } else if (m.type === 'model') {
    document.getElementById('model').value = m.model;
  }
});
</script></body></html>`;
}

function modelOptions() {
  let opts = '';
  try {
    const raw = JSON.parse(fs.readFileSync(MODELS_JSON, 'utf8'));
    const names = Object.keys((raw && raw.models) || {});
    for (const n of names) {
      opts += `<option value="${esc(n)}"${n === model ? ' selected' : ''}>` +
        `${esc(n)}</option>`;
    }
  } catch (e) { /* no config yet, the models button will fill it */ }
  if (!opts) opts = '<option value="">— нажми models —</option>';
  return opts;
}

// ---------------------------------------------------------------- the buttons
function bModels() {
  ask('GET', '/api/tags', null, (err, j) => {
    if (err) return log('models: прокси не отвечает, ' + err.message);
    if (!j || !j.models) return log('models: ответ без списка');
    const mine = [];
    let conf = {};
    try { conf = (JSON.parse(fs.readFileSync(MODELS_JSON, 'utf8')).models) || {}; }
    catch (e) { /* no config, all of them are plain */ }
    say('<b>' + j.models.length + ' моделей</b>');
    for (const m of j.models) {
      const c = conf[m.name];
      mine.push((c ? '<span class="good">✓</span>' : '·') + ' ' +
        esc(m.name) + ' <span style="opacity:.6">' +
        (m.size ? (m.size / 1e9).toFixed(1) + ' GB' : '') +
        (c ? ' · ' + esc(Object.keys(c).join(',')) : '') + '</span>');
    }
    say(mine.join('<br>'));
  });
}

function bModel() {
  if (!model) return log('model: модель не выбрана');
  ask('POST', '/api/show', { name: model }, (err, j, text) => {
    if (err) return log('model: ' + err.message);
    if (!j) return log('model: ответ не разобран');
    const sys = j.system || '';
    const tpl = j.template || '';
    say('<b>' + esc(model) + '</b>');
    say('размер   ' + ((j.details && j.details.parameter_size) || '?') +
      ' · семейство ' + ((j.details && j.details.family) || '?'));
    say('system   ' + (sys ? sys.length + ' символов' : 'пусто'));
    say('template ' + (tpl ? tpl.length + ' символов' : 'пусто'));
    if (sys) say('<span style="opacity:.8">' + esc(sys.slice(0, 400)) + '</span>');
    if (j.capabilities) say('умеет    ' + esc(j.capabilities.join(', ')));
  });
}

// ---------------------------------------------------------------- compile
// one place, because two places that compile are two compilers. The button
// calls it and run calls it, and both get the same answer or the same refusal.
// Two levels of spell check, and the person chooses which one. The local one
// asks nothing of the network and the live one asks datamuse about the words
// that are not in the project's table. The button is a person pressing it, so
// the button turns the network on; the plugin, which runs on every keystroke,
// never does.
function compileFile(f, cb, live) {
  bridge([f].concat(live ? ['--spell'] : []), (err, j) => {
    if (err) return cb(err);
    if (!j || !j.ok) {
      const bad = (j && j.bad) || [];
      return cb(new Error(bad.length
        ? bad.map(b => 'строка ' + b.line + ': ' + b.error).join('; ')
        : 'не разобралось'));
    }
    cb(null, j);
  });
}

function bCompile() {
  const ed = vscode.window.activeTextEditor;
  if (!ed) return log('compile: нечего компилировать, файл не открыт');
  const f = ed.document.fileName;
  if (!/\.vibe$/i.test(f)) return log('compile: это не .vibe, а ' + path.basename(f));
  log('compile: ' + path.basename(f) + ', проверка слов с сетью');
  compileFile(f, (err, j) => {
    if (err) return say('compile: ' + esc(err.message), 'bad');
    compiled = (j.lines || []).join('\n');
    compiledFrom = f;
    say('<span class="good">✓</span> скомпилировано строк: ' + (j.lines || []).length);
    if ((j.unknown_words || []).length) {
      say('слов нет в таблице: ' + esc(j.unknown_words.slice(0, 8).join(', ')));
    }
    const sp = j.missing || [];
    if (!sp.length) return say('<span class="good">✓</span> слова на месте');
    say('<span class="bad">' + sp.length + ' слово не прошло</span>');
    for (const s of sp.slice(0, 10)) {
      say('строка ' + s.line + ': ' + esc(s.word) + ' — ' + esc(s.why));
    }
  }, true);
}

// which rules file this model will get, read the same way the proxy reads it,
// so the panel can say what is going to be sent without asking the model
function ruleFor(m) {
  try {
    const c = (JSON.parse(fs.readFileSync(MODELS_JSON, 'utf8')).models || {})[m];
    return c && c.system ? c.system : null;
  } catch (e) { return null; }
}

function bRun() {
  const ed = vscode.window.activeTextEditor;
  if (!ed) return log('run: файл не открыт');
  if (!model) return log('run: модель не выбрана');
  const f = ed.document.fileName;
  const rule = ruleFor(model);

  const send = (payload, what) => {
    say('<b>' + esc(model) + '</b> · ' + esc(what) +
      (rule ? ' · правила ' + esc(rule) : ' · правил нет'));
    const t0 = Date.now();
    ask('POST', '/api/chat',
      { model: model, messages: [{ role: 'user', content: payload }],
        stream: false, options: { num_predict: 800 } },
      (err, j) => {
        if (err) return say('run: ' + esc(err.message), 'bad');
        const ans = (j && j.message && j.message.content) || '';
        say('<span style="opacity:.6">' + ((Date.now() - t0) / 1000).toFixed(1) +
          ' с</span>');
        say(esc(ans) || '<span style="opacity:.6">(пусто)</span>');
      });
  };

  // The model is sent the compiled text and nothing else, always. There used
  // to be a branch that sent the source of a file that was not a .vibe, and it
  // was wrong twice over: the model got words where it should get addresses,
  // and the difference between the two was invisible in the request. A refusal
  // is a better answer than a request the model will read the wrong way.
  log('run: компилирую ' + path.basename(f) + ' и отправляю');
  if (compiled && compiledFrom === f) {
    return send(compiled, 'скомпилированный текст, уже был');
  }
  compileFile(f, (err, j) => {
    if (err) return say('compile: ' + esc(err.message), 'bad');
    compiled = (j.lines || []).join('\n');
    compiledFrom = f;
    say('<span class="good">✓</span> скомпилировано строк: ' +
      (j.lines || []).length);
    if ((j.unknown_words || []).length) {
      say('слов нет в таблице: ' + esc(j.unknown_words.slice(0, 8).join(', ')));
    }
    send(compiled, 'скомпилированный текст');
  });
}

function bSettings() {
  // one thing, one place: the file that holds the settings. A button that
  // opened a different file depending on what was in the editor would be a
  // button with two jobs, and the second one is always a guess.
  vscode.window.showTextDocument(vscode.Uri.file(MODELS_JSON), { preview: false });
  log('settings: ' + path.relative(REPO, MODELS_JSON) +
    ', правила лежат в VSCode\\rules\\');
}

function bLog() {
  let files = [];
  try {
    files = fs.readdirSync(LOGDIR).filter(f => f.endsWith('.jsonl'))
      .map(f => path.join(LOGDIR, f))
      .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
  } catch (e) { return log('log: папки логов нет, ' + path.join('VSCode', 'log')); }
  if (!files.length) return log('log: логов нет, прокси ещё не работал');
  const lines = fs.readFileSync(files[0], 'utf8').split('\n').filter(Boolean);
  const rows = lines.slice(-12).reverse().map(l => {
    try {
      const e = JSON.parse(l);
      return `${e.ts.slice(11)} ${e.path} ${e.model || '-'} ${e.status} ` +
        `${e.total_ms}ms${(e.added && e.added.length) ? ' +' + e.added.length : ''}`;
    } catch (err) { return l.slice(0, 60); }
  });
  say('<b>' + path.basename(files[0]) + ', последние ' + rows.length + '</b>');
  say(esc(rows.join('\n')));
}

// ---------------------------------------------------------------- the view
class PanelView {
  resolveWebviewView(v) {
    view = v;
    v.webview.options = { enableScripts: true };
    v.webview.html = newPanel();
    v.webview.onDidReceiveMessage(msg => {
      switch (msg.type) {
        case 'pick': model = msg.model; break;
        case 'prompt': break;
        case 'models': bModels(); break;
        case 'model': bModel(); break;
        case 'compile': bCompile(); break;
        case 'run': bRun(); break;
        case 'settings': bSettings(); break;
        case 'log': bLog(); break;
      }
    });
    log('панель открыта, прокси ' + cfg().port);
  }
}

function activate(context) {
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider('vibe.panel', new PanelView()));
  const cmds = {
    'vibe.models': bModels, 'vibe.model': bModel, 'vibe.compile': bCompile,
    'vibe.run': bRun, 'vibe.settings': bSettings, 'vibe.log': bLog,
  };
  for (const id of Object.keys(cmds)) {
    context.subscriptions.push(vscode.commands.registerCommand(id, cmds[id]));
  }
  console.log('[vibe] panel up, root %s', ROOT);
}

function deactivate() {}

module.exports = { activate, deactivate };
