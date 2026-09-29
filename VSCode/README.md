# VSCode

Everything that runs in or beside VS Code, in one folder, with no path in it
that names a machine.

```
VSCode\
  README.md            this
  requirements.txt     what to install
  .gitignore           the built file and the backups are not source
  config\
    proxy.json         the only machine-specific values there are
    models.json        per-model settings, and the rules file each one uses
  rules\               the rules themselves, one file per model
  plugin\              the extension that watches a file
    package.json  extension.js  language-configuration.json  specs\writer.vibe
  panel\               the extension with the buttons
    package.json  extension.js  icon.svg
  tools\
    gate_plugin.py     checks the plugin, writes only if every check passed
    pack_vsix.py       builds the writer vsix and installs it
    pack_panel.py      builds the panel vsix and installs it
    compile_bridge.py  the project compiler behind a command line, for the panel
    ollama_proxy.py    the proxy in front of Ollama, and the log
  specs\               what each of them is for, written before the code
  log\                 one jsonl per proxy run
```

The gate writes a `.before` next to every file it touches, and a `.before` of
the same size as the file it sits next to is not a backup: the gate overwrites
it with the current state on the next run. They are in `.gitignore` for that
reason and not because a backup is worthless.

## The two extensions

```
Vibe Writer   5xvector.vibe-writer    watches a file, decorates it, checks it
Vibe Panel    5xvector.vibe-panel     six buttons, and the model
```

Two and not one, because one role and one thing. The writer never talks to a
model. The panel never looks at frames.

### Vibe Writer — the watcher

What it does to a `.vibe` file:

```
-> and →      the arrow, violet and bold. The only glyph it ever writes, and
              only into the editor: the file on disk keeps the two ASCII signs
< >           the pointed frames, a yellow fill
words         a word the project has not accepted, a red squiggle under it
```

What it checks, and what it does not:

```
brackets and blocks    it checks, and a frame inside a frame is a fault
words                  it checks, letters and the project's own table
the role of a word     it does not check, and never will
```

The last one is a decision and not an unfinished job. A person tells a verb from
a noun without a list, and a model knows it by having been trained on the
language. A dictionary cannot answer it: `state` is a noun and a verb and an
adjective, and so is every English verb, because `make` is also a thing and
`run` is also a trip. A check that decided for the operator would be a different
check from the one that was written, and nobody would be able to tell.

**The word check is local, on purpose.** The plugin asks two questions that both
have an answer on this machine: are the letters Latin, and is the word in
`5xVector\englang.embedding`. It never asks the network, because it runs on
every keystroke and one request per word is one request per letter. The network
half is the panel's `compile`, where a person is the one pressing the button.

**The table is read, never copied.** `englang.embedding` stays in the project
and the plugin reads it from `VSCode\..\5xVector\`, or from `vibe.table` if you
point it somewhere else. A copy inside the extension would be a second table
and would drift from the first.

### Vibe Panel — the buttons

It opens on the **Vibe** icon in the activity bar, and every button is also a
command in the palette and a key.

| key | command | what it does |
|---|---|---|
| `Ctrl+Alt+B` | `vibe.compile` | compiles the open `.vibe` through the project compiler |
| `Ctrl+Alt+R` | `vibe.run` | sends the compiled text to the model, with the rules |
| `Ctrl+Alt+M` | `vibe.models` | what is installed, and which have settings |
| `Ctrl+Alt+I` | `vibe.model` | what is inside one: system, template, modelfile |
| `Ctrl+Alt+L` | `vibe.log` | the last exchanges, from the proxy log |
| — | `vibe.settings` | opens `config\models.json` |

```
compile and run fire only when the open file is a .vibe
everything else fires anywhere
```

That is not "it does not work on other files". It is the point: the keys are
taken in this project and free in every other one, so nothing is intercepted
from a person who is not working on this language.

To move or remove a key: `Ctrl+K Ctrl+S`, then search `@command:vibe.` A key
that is already taken is marked there, which the manifest cannot know.

### What `run` actually sends

```
the rules     from config\models.json, by the proxy, as the system message
the spec      the COMPILED text, always, compiled on the way
```

Not the source. Ever. An earlier version sent the source of a file that was not
a `.vibe`, and it was wrong twice over: the model got words where it should get
addresses, and the difference between the two requests is invisible in the log.
A refusal is a better answer than a request the model will read the wrong way.

The rules are not sent by the panel. They are read by the proxy from the same
file the panel just read, and every line it added is written to the log beside
what the client sent. So a wrong answer can be traced to a setting rather than
blamed on the model.

**The proxy has to be running**, and that is the price of the rules:

```
py -3 tools\ollama_proxy.py
```

Without it the buttons say `прокси не отвечает`, and that is the whole of the
failure.

## This folder is the one copy, and it is beside the project

This folder is at the root of the repository, and it is the only copy of these
files. `plugin\`, `tools\` and `specs\` used to sit inside `5xVector\` beside the
same files in `plugins\`, `test\` and `src\`, and two copies of one file is one
copy too many: they agree on the day they are written and they do not agree on
the day someone edits one of them.

So there are three names, and every path is built from them:

```
REPO = dirname(abspath(tools/..))       ->  VibeDSL       this folder's parent
VS   = dirname(abspath(tools/..))       ->  VibeDSL\VSCode this folder
ROOT = REPO\5xVector                    ->  named, not counted
```

**`ROOT` is written down on purpose.** The gate guards the compiler and the
table, which live in `5xVector\`, and while this folder was inside it they were
one level up. A folder that moves silently changes what it was pointing at, and
that is the failure this project keeps paying for: a path that used to be right
and is now wrong, with nothing to say so. So the project is named, and if it
is ever renamed the gate stops at once instead of guarding nothing.

A second plugin from an older version goes beside this one, as `plugin-old\`
with its own `tools\`, and the two do not meet.

## Paths you can change without editing code

Only these, and only in `config\proxy.json`:

```
host  port  ollama  log_dir
```

`--config` prints what is actually in force, which is the way to tell what a
file that was never edited is doing.


## On a new machine

Four steps, and the order matters: nothing is written before a check passed.

```
1  python -m pip install -r requirements.txt
2  edit config\proxy.json if Ollama is not on 127.0.0.1:11434
3  py -3 tools\gate_plugin.py          <- five checks, writes only if all pass
4  py -3 tools\pack_vsix.py            <- builds the vsix, installs it
```

Step 3 does not need VS Code. Step 4 needs it only to install; if `code` is not
found it says so and leaves the built file where it is, and installing by hand
is Extensions -> ... -> Install from VSIX.

## On Linux and macOS

Same three commands, and the folder paths with slashes. The only thing that was
Windows-only was the path to `code`, and it is looked for now in this order:

```
$CODE_CMD        a full path, if you want to be certain
code on PATH     the ordinary way
the usual places per system
```

So on a machine with no VS Code in the usual place, either put `code` on PATH or
set `CODE_CMD`, and the difference between the two is one variable.

## What the proxy is for, in one line

A model can be asked something and there is no record that it was. The proxy is
the record.

It does not buffer, so a stream stays a stream and the first token arrives when
it arrives. It does not translate between `/api/chat` and `/v1/chat/completions`,
because a translation drops the fields the other dialect has. It does not edit
prompts on the way through, because a log that does not describe the request is
worse than no log.

```
py -3 tools\ollama_proxy.py            <- serves
py -3 tools\ollama_proxy.py --config   <- what settings are in force, then stops
```

A client that goes to Ollama's own port does not pass the proxy and is not
logged. That is the one thing to know before trusting a gap in the log.

## What is not here, and why

```
the record form      not checked, on purpose, and the reason is above
the frame check      it reads one line at a time, so a frame across two lines
                     gives two false faults. Known, written down as plugin-01,
                     not fixed.
the bridge network   off with VIBE_OFFLINE=1
```

That last one is a switch and not a flag, because the default has to be the one
that works. A switch that is off until a person turns it on is a switch most
people never touch, and then the check does not run and the file looks clean
because nobody looked.

```
VIBE_OFFLINE=1   no network, letters and the table only
unset            the outside is asked, which is the default
```
