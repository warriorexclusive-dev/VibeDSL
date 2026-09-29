# Proxy and panel, the two halves of one thing

A working spec, English, mine. It is here because the spec comes before the
file, and this is the spec for what the buttons are going to do.

## The hole

Fourteen models on `127.0.0.1:11434` and no way to see who talks to them. A
model can be asked something and there is no record that it was, what it was
asked, or what it answered. Changing a RULES block means rebuilding a model by
hand, and nobody remembers which model carries which rules.

So two things, and they are one thing:

```
proxy   sits in front of Ollama and writes down everything that passes
panel   the buttons that drive it
```

The panel without the proxy is a toy, because the model call leaves no trace.
The proxy without the panel is a log nobody reads.

## The proxy

```
client  ->  proxy :11435  ->  ollama :11434
               |
               +-- log/NNNN.jsonl, one line per exchange
```

**It does not buffer.** The stream is the feature. If the proxy collects the
whole answer before writing it back, `stream: true` stops being a stream and
every client that depends on the first token arriving early stops working. So
bytes go through as they arrive, and the log is written from the same read.

**It is a proxy and not a library.** `requests` is installed and the OpenAI
layer at `/v1/` is alive, so a client could talk to Ollama directly. It would
also then leave nothing in the log, and the log is the reason this exists.

**Both dialects pass.** `/api/chat` for native callers, `/v1/chat/completions`
for OpenAI-shaped ones. The proxy does not translate between them, because
translation loses the fields the other one has, and the fields are the log.

**Nothing is rewritten on the way through.** Not a prompt, not a parameter.
The proxy is a witness. A proxy that edits is a middleware and needs its own
tests, and there is no way to tell from the log which of the two you were
looking at.

## The log

One JSON object per line, written as the exchange finishes.

```
ts            when it came in
method path   what was asked for
model         the model field, or the path segment
status        the HTTP status that came back
ttfb_ms       first token, the number that says whether the model is fast
total_ms      the whole thing
req           the request body, whole
res           the response, whole, reassembled from the stream
stream        true or false
```

`res` is reassembled because a streamed answer arrives in pieces and a log of
pieces is a log you cannot grep. The pieces still go to the client untouched;
only the copy is joined.

**The log is append only and is never rotated by the proxy.** A file that
rewrites itself loses the entry you were reading. Rotation is a thing a person
does when the disk is full, and the proxy says so rather than doing it.

## The model config

One file, `models.conf`, read per request.

```
vibedsl-rule:1.5b
  system      rules/current.md
  temperature 0.7
```

**Rules live in a file, not in the panel and not in the proxy.** The panel edits
a file, the proxy serves a file, and the file is the thing a person opens when
the model answers wrong. If the rules were in the proxy, fixing a rule would
mean editing code and restarting a server.

**The panel never rebuilds a model on its own.** `ollama create` is slow, and a
panel that rebuilds a 7 GB model because a temperature changed would be a
trap. The button builds a Modelfile, shows it, and asks.

**What it shows comes from the model, not from a cached list.** `/api/show`
returns `system`, `template` and `modelfile` for the model itself. Reading a
file the panel wrote down last week would be reading a lie the moment the model
was rebuilt by hand.

## The buttons

```
models      what is installed, from /api/tags
model       what is inside one, from /api/show
compile     a .vibe source, through the project compiler
run         the compiled text to the model, and the answer to the log
settings    temperature, num_ctx, and the rules file for one model
log         the last exchanges, from the proxy log
```

**Compile goes through the project compiler, not through a copy of it.**
`compiler_v2.compile_text()` is imported. A second implementation of the same
compiler is a second set of bugs, and this one already has a gate.

**Run sends the compiled text, not the source.** The source is what a person
writes and the compiled text is what the model reads. Sending the source would
make the model do the compile that the button has already done, and the model is
the worse compiler of the two.

**One button, one action, and the log says which.** Every button that talks to
Ollama writes one line to the log with the model and the time. A panel that
does something you cannot see afterwards is a panel you cannot trust.

## The order

```
1  the proxy, tested on a real request and a real stream
2  the config file, tested by changing a temperature and seeing it arrive
3  compile, tested against a .vibe that the project compiler already accepts
4  run, tested end to end with the answer in the log
5  the rest of the buttons
```

Compile comes after the proxy because compile without the log is a print, and
the log is the part that cannot be recovered afterwards.

## What this does not do

```
it does not translate dialects      a translator loses fields
it does not edit prompts in flight  then the log is not the request
it does not rotate the log          rotation loses the line you are reading
it does not rebuild models silently a 7 GB rebuild behind a button is a trap
```

## The check, before the write

```
1  a real streamed request through the proxy arrives whole and in order
2  a real non-streamed request arrives whole
3  the log holds one object per exchange and res is the full answer
4  the file on disk is byte-identical to what was there before
```

The proxy is a thing other programs depend on, so a check that only reads the
code proves nothing about it. The four above are run against a live model.
