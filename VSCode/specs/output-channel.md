# Output channel, the plugin's second half

A working spec, English, mine. Not VibeDSL, not a .vibe record. It is here
because the rule is that the spec comes before the file, and this is the spec
for one function.

## The hole

The plugin watches frames and says nothing. `frameFaults()` returns a list of
faults, `layers()` returns the ranges, `paint()` puts the ranges on the screen
and drops the faults on the floor. The only way a person learns that a frame is
broken is the yellow fill, and a fill has no sentence in it.

`(spell):report->a squiggle and a word[the word in the message, and where it is]`
— that record already asks for the word and the place. The report has no
carrier. This is the carrier.

## What the channel is for

One channel, named `vibe`, and it carries four things and nothing else.

```
1  what the plugin is serving      once, at startup
2  a fault                         line number and the sentence
3  a file that was checked         line count, fault count
4  a write gate                    size before, size after, equal or not
```

No log of keystrokes. The plugin is a watcher, not a recorder, and a log that
carries every keystroke is a log nobody reads. A fault is worth a line because
it is rare. A keystroke is not, because it is not news.

## The rules

**The channel is decoration and never an edit.** It appends to VS Code's
buffer and to nothing else. The file on disk keeps the two ASCII signs, and the
glyph stays in the editor. This is the same rule the arrow already follows and
it is the reason the plugin is safe.

**A line is written only when the answer changes.** `paint()` runs on every
keystroke, so writing on every call fills the channel with the same sentence.
Keep the last answer per file, compare, write on a difference. Three lines in
the file, and the answer is the same, means nothing is written.

**The file name is in every fault line.** A fault without a place is a
sentence about nothing. The place is `basename`, and the line is 1-based,
because that is what the person sees and what the editor's own gutter shows.

**A fault is reported where it is found and is not counted twice.** One pass
walks the lines, collects the faults, writes the fault lines, writes the
summary. Two passes would write every fault twice and there is no reason.

**The gate is reported, not enforced.** The plugin does not write to disk at
all, so there is no write to guard. The gate line states the size before and
the size after, and if they differ the file changed without the plugin, and
that is worth a line and nothing more.

**One role, one sign.** The channel name is one string in one place. It is not
also the command argument, and the command name is a different string.

## The commands

```
vibe.checkFrames   already there, and it gains the channel: faults go to both
vibe.showOutput    new, opens the channel and gives it the focus
```

`checkFrames` keeps its message box. A message box is a glance and a channel is
a reading, and a person who wants the whole list asks for it.

## What this does not touch

```
englang.embedding      the table, and the width, and the 3-3-tail
specs/compiler.vibe    the other spec
RULES.md               the rules of the language
AGENT_RULES.md         the reading side
```

The tail and the stale figures are a separate finding and a separate job. This
channel does not depend on any of them and fixing them does not touch it.

## The check, before the write

```
1  the new spec compiles, and it decodes back to the same words
2  the new JS parses, node --check
3  the new JSON parses, and no key is a second copy of a key above it
4  the plugin's own test: frameFaults and layers still hold on the old cases
5  the file on disk is byte-identical to what was there before
```

All five stand before the write. If one fails, nothing is written and the
failure is printed. That is the gate the project already uses, in
`write_guard.py`, and this is the first thing that goes through it outside the
`src/` folder.
