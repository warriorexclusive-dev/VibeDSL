# ROUTING TRACE - format for the platform's own decisions

A trace records what the router did with a task: which expert it picked, how
far away the others were, and how sure it was. It is written per task and kept
in a folder of its own, apart from the language, apart from the specs, apart
from the model.

## Why it is written at all

Apache 2.0 ships AS IS, with no warranty and no liability. Nobody else's claim
that the router picks correctly can be relied on, so correctness has to be shown
from the outside. A trace is that evidence.

It is also the answer to a question that cannot be settled by argument: whether
splitting a task across experts is worth it. That question was asked and could
not be answered - the task was never actually delegated once, so there was
nothing to measure. A trace is what makes it measurable next time, and a public
folder of traces makes it measurable by anyone rather than by one person.

## One line per decision

```
session  task        chosen       distances (all, sorted)      margin  temp  ms
------   ----------  -----------  ---------------------------  ------  ----  ---
s-1f3    ide-window  dsl-coder    0.31 0.58 0.62 0.88         0.27    0.7   140
s-1f4    theme       coder        0.44 0.47 0.91 0.93         0.03    0.7    96
```

## Tokens, on both sides

```
tok_in   tokens the model was given        the prompt, the session, the tools
tok_out  tokens the model produced         what it wrote back
```

| field | why it is here |
|---|---|
| tok_in | the whole cost of a session is here, not in one line of a spec |
| tok_out | the answer, and with tok_in it gives the ratio that decides caching |

**This is the field that settles the argument about glyphs.** A glyph is more
characters and possibly more tokens than a word, and it was said that this does
not matter for a local model. That is true, and it is also unmeasured. With
tok_in and tok_out written per task, the cost of a glyph spec against a word spec
stops being an opinion and becomes a number in this folder, accumulated over
real work.

Read the two separately, not as a pair:

```
tok_in   grows with the session, so a long conversation is the expensive thing
tok_out  grows with how much was rewritten, so a task that needed many passes
         shows up here first
```

## Fields

| field | what it is | why it is here |
|---|---|---|
| session | id of the task | ties the line to the work |
| task | short label, not the text | says what was asked without carrying the code |
| chosen | the expert that ran | the decision itself |
| distances | every expert, sorted, ascending | the alternatives, so the choice can be re-derived |
| margin | chosen minus the nearest other | **how sure it was**; a small margin is a coin toss |
| temp | temperature in force | the setting that produced the above |
| ms | wall time for the routing call | latency, and a large jump means something else was wrong |

`margin` is the field worth reading first. A margin above about 0.15 is a
decision. Below it is a guess between two neighbours, and the result should be
read as "one of these two", not "this one".

## What is not in the trace

```
the text of the task        may be someone else's code
the embedding itself        it is the task, in another form
exact per-layer vectors     these reconstruct the router itself
```

Distances, winner and margin are enough to re-derive the decision and to see the
uncertainty. They do not carry the code. That is the line: **the reasoning is
public, the input is not.**

## Reading a folder

```
many small margins      routing is guessing; split tasks differently or merge
chosen one expert often the router is confident the task is single; that is
                        information about the task, not about the router
one expert never chosen either it is dead, or the router cannot see its niche
```

## And what a trace is for, in one line

It turns "the router picked the right one" from a claim into a line you can read,
and it accumulates — so the question of whether to delegate is answered by
counting, over time, instead of by opinion on the day.
