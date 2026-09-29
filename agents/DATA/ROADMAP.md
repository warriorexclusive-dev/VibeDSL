# Roadmap - stages and epics

The dictionary has `part` (a partition of a spec) and `stage` (a separation
with progress). It has no `epic`, and it does not need one: an epic here is a
`part`, a stage is a `stage`. Adding a third word for the same thing is the
defect this repository spent a day removing.

Status vocabulary is the one in the base, not invented here:
`pass` / `fail` for a check, `open` for what is not decided yet.

## stage 1 - the base is aligned  (part 1, DONE)

Align the dictionary and the syntax. Find the mapping defects. Record what is
missing.

Done, and the proof is mechanical rather than asserted:

- 334 concepts, 367 words, 315 marks, 0 self-contradictions.
- 40 abbreviations expanded; 6 concepts dropped; 2 split; 1 merged.
- The gate went from 12 checks to 13. The thirteenth, DICT, exists because the
  first twelve passed 12/12 straight through four mutually exclusive defects.
- 1 592 replacements across one spec, 0 words left stranded as text, 0
  collisions across 1 859 compiled lines.

## stage 2 - the IDE, used with an agent  (part 2, OPEN)

The IDE, for working alongside a local or a remote AI agent.

`PY_IDE/vibide.py` runs headless today: `py PY_IDE\vibide.py --exam` builds the
window and passes 25 of 25. It is a dearpygui application against
dearpygui 2.3.1, which is what the spec names.

Still open, and these are the real work of this stage:

- the spec declares 32 functions and the exam asserts that count, so adding or
  splitting a function breaks the check until spec, code and expectation move
  together
- 10 soft warnings: `cfg:mapping`, `mapping:group`, `frm:corner`, `frm:font`,
  `font:font_size`, `par:nest`, `io:func`, `theme:hex`, `theme:group` are used
  as fields and not declared as pins. One of them, `cfg:mapping`, is a direct
  consequence of `mapping` no longer being a dictionary word
- `add_tab` inlines `tab_view:name:set(par)` while `set_tab_name` does exactly
  that: two sources of truth for one operation
- the compiled output has a reader, and the reader is not always strong: the
  RULES template and the GLYPHS legend are 20% of the output and are switchable
  with `--no-rules` / `--no-legend` for a small model that holds the knowledge
  in its weights

## stage 3 - the local assistant learns the syntax  (part 3, OPEN)

Train the local helper on the syntax, and autocomplete, to raise the speed of a
person working in this language.

Two corpora exist and both are generated from the live base, so they cannot
drift from it:

- `DATA/lessons.jsonl` - 43 records over 9 topics: what was wrong, what is
  right, the rule, and why. Six are marked as blind spots, meaning no existing
  check would have caught them.
- `DATA/dict_corpus.jsonl` - 334 concepts with names, mark, meaning, and the
  readings the base refuses.

Honest limits, stated now rather than discovered at training time:

- 334 records will not move any weights. These are specifications. Training
  needs thousands of questions, mutated out of real specs.
- Isolated (wrong, right) pairs teach a model to spot the correction, not to
  hold the convention. The pairs have to appear inside whole specs, in context.
- The `refuse` field is a heuristic: of its nine hits, two are noise
  ("a name of this concept", "ask again"). It has to be hand-kept.
- The advisor is for a person, not an autonomous executor. The human is in the
  loop, so a wrong hint is visible rather than acted on, and short precise
  answers beat long reproductions.

## stage 4 - the web IDE  (part 4, OPEN)

Take the IDE to the web.

## stage 5 - the mobile IDE  (part 5, OPEN)

The IDE on mobile.

## stage 6 - real cases, local and remote models  (part 6, OPEN)

Work through real cases on local and remote models.

This is the stage that needs the real specs the earlier stages were for, which
is why the old low-quality ones were removed: four of them were byte-identical
or near-identical copies of one 267-line IDE spec, and three of those carried
20 validator errors each. A benchmark built on those measures the copy, not the
language.

## stage 7 - specs as OOP  (part 7, OPEN, deliberate)

A prototype is what a spec needs to become real OOP. Who writes that generator
and when is not decided, so the stage is empty on purpose - but the mechanism
is a conscious extension of the language, not a leftover, and that distinction
is the whole point of writing it down here.

One prototype exists, bstract, and it is permanent:

    prototype:id="abstract":required:type[item,function,prop]:required:condition

It is the reference example of the syntax and the yardstick for any prototype
added later. The other seven that stood beside it were scaffolding from before
the syntax rules existed; a model reading them learned the wrong form, and one
of them collided with a prop of the same name in the IDE spec.

A proto declares; the blueprint with the same id implements. That is the whole
of the current mechanism: the interface half and the code half, kept apart, the
way class IEntity and its implementation are kept apart in C++.
