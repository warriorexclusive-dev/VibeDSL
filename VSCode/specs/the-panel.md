# the panel, in the editor, and not in a browser

A working spec, English, mine. It is here because the spec comes before the
file, and this is the spec for six buttons.

## What it is

A second extension, beside the first one, in the sidebar.

```
Vibe Writer   watches the frames, decorates the arrow, writes what it finds
Vibe Panel    six buttons, and the answer from a model
```

Two extensions and not one, because one role and one thing. The first is a
watcher and it never talks to a model. The second talks to models and it never
looks at frames. Merged, the second one inherits an activation on every
`vibe` file, and a model call from a keystroke is a model call per keystroke.

## The buttons

```
models      what is installed, from the proxy
model       what is inside one: system, template, modelfile
compile     a .vibe source, through the project compiler
run         the compiled text to the model, and the answer on screen
settings    the rules file and the parameters for one model
log         the last exchanges, from the proxy log
```

**Every one of them goes through the proxy.** Not Ollama, the proxy. A button
that reaches Ollama directly leaves nothing in the log, and the log is the only
thing that says what the model was asked.

**`compile` runs the project's compiler, not a copy of it.** The compiler is
Python and a JavaScript extension cannot import it, so the panel calls a thin
command line bridge that imports the real one. A second implementation of the
compiler is a second set of bugs, and this one already has a gate.

**`run` sends the compiled text, not the source.** The source is what a person
writes and the compiled text is what the model reads. Sending the source makes
the model do a compile the button has already done, and it is the worse of the
two compilers.

**`settings` edits a file and does not rebuild a model.** A model is 7 GB and a
`ollama create` is minutes; a panel that rebuilds one because a number changed
is a trap. The button opens the file, the proxy re-reads it, the next request
uses it.

## What it does not do

```
it does not hold a model in memory    a model is a process, not a value
it does not edit the spec files       the panel reads them and never writes
it does not run without the proxy    an answer with no log is not an answer
```

## The order

```
1  the bridge, called and answered, on a .vibe the compiler already accepts
2  models, from the proxy, on a live Ollama
3  model, /api/show, and the real system prompt of a real model
4  run, end to end, with the answer in the proxy log
5  compile, then run on a compiled file
6  settings, a temperature changed and seen on the next request
```

Bridge first, because every other button that reads a file goes through it, and
a panel that cannot read a file cannot do the half of the work that matters.

## The check, before the write

```
1  the JS parses
2  the JSON parses and no key is declared twice
3  the bridge answers on a .vibe that the compiler already accepts
4  the buttons are declared in the manifest, once each
```
