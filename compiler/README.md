# compiler/ — the text → symbol compiler

The upper layer of VibeDSL is written in words. A model that reasons well on
words reads it directly. A **weak model** — a 4-8B local sub-agent, a quantized
22-64B — loses the structure inside the prose, so the same logic is compiled into
the lowercase layer: one mark per word **and one mark per grammar operator**, so the
frame of the tree is symbolic too and the model never has to read two notations
at once.

```
py -X utf8 compiler\compile.py plan\ide-specfile.vibe -o out.txt
py -X utf8 compiler\compile.py plan\ide-specfile.vibe --all-glyphs
php -S 127.0.0.1:8000 router     # then GET /API/compile?file=plan/ide-specfile.vibe
```

## Files

| File | Role |
|---|---|
| `compile.py` | the compiler. Reads everything read-only, writes nothing back |
| `symbols_map.txt` | the mark table: `U+XXXX  mark  *-> word - meaning`. Policed by `py -X utf8 validator\glyphs.py` |
| `header.txt` | the `include.h` of the compiled output — see below |

`DATA/` keeps the word dictionary and the `use()` pool. The two **symbol**
dictionaries live here, beside the compiler that reads them, because nothing
else needs them: the mark table is only consumed by the compiler and the
`/API/symbol` lookup, and the header only by the compiler. The word dictionary
stays in `DATA/` because six other things read it (RAG search, the IDE dictionary
editor, `sort_dict.py`, `spellcheck.py`, `glyphs.py`, `validator.py`) — a second
copy here would be a second source of truth.

## Output — three blocks

```
-----RULES-----   header.txt inlined + the marks this file actually uses
-----DATA-----    every abstract / proto / blueprint / agent that use() pulled
                  out of the base, each marked with an anchor • U+2022
-----CODE-----    the specification. Execution starts here and nowhere else
```

## The rules it applies

| What | Rule |
|---|---|
| words | replaced by the mark of their concept, whole-token only, so `lang` never eats `language` |
| operators | `->` `<-` `<->` `=` `==` `<=` `>=` `<>` `?` `!` `&&` `\|` `\` `/` `*` `+` `-` are marks too, matched longest-first so `<->` never degrades to `<-` |
| `&->` | emitted as the anchor `•` U+2022; `-[N]>` as `⪪` U+2AAA. Lifted out in `segments()` before the bracket rule, otherwise `-[3]>` would open a `[]` scope and never compile |
| indentation | preserved byte for byte; only tokens are swapped, the tree is never reflowed |
| `""` `{}` `()` `[]` | **never** rewritten. A quoted run is a literal, `{}` is the free-form block, `()` is action scope — that boundary is how the model tells logic from payload |
| `//` `/* */` | human comments, kept verbatim |
| `use(...)` | the only import. All four written forms resolve: `use(id)`, `use(a,b)`, `use(VibeDSL:proto[if,goal])`, `use(agent:name="coder")`. Nested `use()` inside a pulled body is followed |
| `incld="id"` | **not** an import — a mapping attribute declared on the entity |
| reserved ASCII | `%` `;` `{}` `//` `-(id)>` `<(source)-` keep their ASCII on purpose, declared in `header.txt`. `%` is a value suffix (`50%` is not modulo), `{}` must keep a visible boundary |

## The mark lookup — by concept, in two passes

The master dictionary declares one concept as several words —
`*-> create, create`, `*-> length, size, length`, `*-> location, location` — while
`symbols_map.txt` files the mark under **one** of them, usually the short
phonetic one the language prefers. A reader that looks up by the concept's own
name misses entirely and rescues only the single alias that happened to match:
that is how `create` compiled and `create` did not, leaving 74 words across 64
concepts with a mark in the table that no input could ever reach.

- **pass 1** — a word with a mark of its own keeps it. Always.
- **pass 2** — a word with no mark of its own inherits from its siblings, but
  only when they all agree on **one** mark. Where siblings disagree the
  dictionary contradicts itself — it did, once: `include, import, incld` shared
  one head while the table gave ⊃ to one and ⊂ to another, and `unknown, none,
  unknown` filed an absence under an unknown. Both are fixed: `incld` ⊂ is its own
  concept, `import` ⊃ is its own, `none` ∄ and `unknown` ⁂ are separate. A
  contradiction is never resolved by guessing: the word is left as text and
  reported. **A wrong mark is worse than no mark** — one makes the model action on
  a meaning nobody declared.

Nothing is invented. Every pairing is one the master itself states.

## `header.txt` — the include.h

One hand-written file with every invariant sentence: the base task in English,
what the three blocks are, how to read a mark, which ASCII is reserved. The
compiler inlines it into the RULES block of every specfile, as a C preprocessor
inlines `#include <...>`.

It is a file and not a Python string literal for three reasons: prose inside
code cannot be proofread, diffed or translated; it is served by the RAG API
(`GET /API/get?dict=header`) and embedded into the IDE (`py ide/gen_data.py`)
like any base file; and it is **the same bytes on every compile**, which is what
makes it cheap for a small model — a stable prefix that stays in the KV cache
instead of being regenerated per specfile.

Slots the compiler fills: `@SOURCE@` `@COUNT_MARKS@` `@COUNT_TOTAL@`
`@COUNT_CONCEPTS@` `@COUNT_DATA@` `@ANCHOR@` `@BLOCK_RULES@` `@BLOCK_DATA@`
`@BLOCK_CODE@`. A slot the header asks for and the compiler does not know is a
**hard error**, so a typo can never reach a model as a hole in its instructions.

Only the per-file part is generated: the GLYPHS table under the header lists just
the marks that file uses, in order of first use.

## The report is part of the contract

```
words replaced    : 212 occurrences, 35 distinct
distinct marks    : 35 emitted, 317 in the base table
use() resolved    : 2 entr(ies)
tokens with no mark left as text : 3
words the base does not define  : 48 (identifiers, kept as text)
concepts with no mark at all     : 20  &->, ()->, *?, //, ;, <, ...
the dictionary contradicts itself : 2 mark(s) unreachable: import, unknown
```

The last line is a **hard failure (exit 1)** if a mark is emitted that is not in
`symbols_map.txt`. A compile of an already-compiled file is effectively a no-op,
so the transform is safe to re-run.

## Known open defects

Two are not fixed here, and both are recorded so nobody re-derives them:

1. **`y` compiles to `⊤` ("true").** The master declares `Y` an alias of the
   boolean literal `true, yes, Y`, so the key of an axis — `y=40%` — becomes
   "true assign 40%". `n` → `⊥` is the same trap. This is a dictionary
   decision, not a code fix: either drop the one-letter aliases, or declare that
   on the left of `=` the word is a name and is not substituted.
2. **`[]` protection is too broad.** `size=[min=5%,max=25%]` protects the values
   correctly (`5%` must not compile) but also the keys, and `min`→`▾` `max`→`▴`
   already have marks. Telling a list-of-values from a list-of-keys is a grammar
   distinction, and a scanner does not know the grammar — this needs a compiler
   that walks the tree `validator/validator.py` already builds.
