# VibeDSL

**VibeDSL** is a semantic, NLP-based domain-specific language - a **logic constructor**
for tasks, rules and architectures that must be passed clearly to an AI. It is designed
for both AI and humans: a human can write it by hand, and a minimal set of precise
instructions is enough for an AI to assemble the logic.

Version: **v1.0 alfa** - License: **Apache 2.0**.

The language is a **two-dimensional diagram in text**: nodes, arrows and indentation
form two axes (a whiteboard like Miro). The third axis (Z) holds **states** - see
[Z vector](#z-vector--z-) below.

## Why

The goal of the language is **maximum portability of logic**: the ability to hand the
same logic to a different model without rewriting it.

| From | To | What must survive |
|---|---|---|
| cloud model | local model, 22-64B quantization | the exact logic, not a paraphrase of it |
| large model | small sub-agent | logic crammed into small chunks |
| cloud model | a different cloud model | the same specfile, read verbatim |

The target user is **medium and near-large business** - teams that already run
local models alongside cloud ones and cannot afford to maintain two copies of the
same logic.

### The problem it solves

One model does not understand another model's logic when that logic exists only in
code. Three root causes:

1. **Codebase volume.** Even with Jira and Confluence connected, the amount of
   information is too large even for a large cloud model. The context fills with
   everything except the part that actually decides the behaviour.
2. **Prompts aimed at quantized models.** A 22-64B quantized model does not reason
   reliably from human-language prose. An instruction written for a frontier model
   loses its precision on the way down, because it arrives as a paragraph of
   natural language rather than as a structure.
3. **Token and KV-cache cost at 4-8B.** A local sub-agent at 4-8B quantization pays
   twice: for the tokens it consumes, and for reusing a large KV cache. Every
   advantage of running locally is cancelled by that overhead.

### What the language does about it

It gives logic a **compact, canonical, unambiguous form** that any model can be
handed directly - a few hundred tokens instead of a repository, and a specfile that a
22-64B model and a frontier model read the same way.

Unambiguous means unambiguous **for a human reader too**, not only for a model. One
word has one meaning, one meaning has one word, and every line of the base resolves
without guessing. A rule a person can apply is a rule a small model can follow.

## Base syntax

```
[node:name] -> [node:param]     chain: a logical unit delegates to a node

parent:                       parent is the object with a colon at the end of the line
   -> child                   children are indented and begin with an arrow marker
     -> grandchild:           indentation = nesting (Python/YAML style)

:                             logical operator + null-safe presence check (a:b:c);
                              checks the object and marks the condition that the logic
                              is done; can take the <> multi-way prefix
->  <-  <->                   right strict link / inverse / two-way public interface
==  =                         equality (if-then gate) / assignment
<=  >=                        comparison: less-or-equal / greater-or-equal
-(id)>                         link to an internal object of the specfile (by id)
<(source)-                        link to an external source beyond the specfile: one-way departure, may not return
|  &&  !                      logical or / and / reverse
{}  ""                        free-form custom logic / custom value mapping
part N:  stage N:             isolated partition / staged partition with reference
```

Core markers stay stable across the language:

| Marker | Meaning |
|---|---|
| `*->` | object marker - every dictionary/proto/blueprint object starts with it |
| indentation | horizontal vector: nesting / vertical hierarchy |
| `:` | logical operator + null-safe presence check; **with ask** - if the object is absent it halts the logic and asks |
| `<>:` | multi-way logic: several paths by selection; explicit conditions required, without them behaves as plain `:` |
| `&->` | remember/author marker - memorizes the node as an etalon (used by `abstract`: `&-> abstract(action id=...)`) |
| `quote` | verbatim speech marker (mapping to base) - "this was said", not for interpretation |
| `=` `==` | assignment / equality (if-then gate) |
| `->` `<-` `<->` | right strict link / inverse / two-way public interface |
| `id=""` `desc=""` | object identity and description (used by `*_get` / `*_search`) |
| `ask` | resolution cascade (see below) |

Command style uses phonetic abbreviations (`create`, `exam`, `write`, `approve`, `strk`, `valid`,
`exst`, `rollb`, `prnt`, `variant`) - readable without a dictionary.

## Vectors

Logic is built as chains of linked vectors: `[model1]->[model2]` delegates a logical
unit to the next node. Ordered collections are vectors too: `[]` blocks, `list`
(list/array/collection), `table` (in-memory table), `index` (indexed access), `fifo` (queue).

Vertical structure is built like YAML: a colon-parent opens an object, indented
arrow-children nest into it.

```
root:
   -> list:[v1,v2,v3]
      -> table:rows
         -> index:[0,1,2]
   -> sel[val1,val2]->function:data=sel:return
      -> for(i<10,incr(1))
         -> data:index[i]

root:node == a<>:             : two-way logic, Y/N scope
   -> show(ok)                : on YES
   -> show(no)                : on NO
```

Indentation itself is also a vector - **horizontal**: each nesting level chains its
child objects into an ordered hierarchy.

## UI layer (Material Design 3)

The visual/frontend zone is described with Material Design 3 vocabulary — in trend,
and a clear textbook. Tokens are short (3-4 chars) to fit small models, abstract
over precise (precision closes via `styp`/`{}`).

- Composition: `row column grd frm grp ovl pag sec hscroll vscroll spr`
- Recycler (first-class, not composed from abstracts): `rcl`
- Navigation: `nav bct table link`
- Input controls: `inp btn sel tgl slr pic srch`
- Display & feedback: `crd list icn avt bdg dvr prg skn tip msg dlg sht theme`
- User input events: `kdown kpress kup mosup mosdown scrtap enter`
- Entities: `view` (concrete frame/screen - not `graphics`, that is the visual element/type abstraction), `event,event` (lifecycle/callback marker alias, e.g. `event type="onCreate" -> load view`)

Sketch:

```vibedsl
prj:name="settings":theme="m3":
   -> pag:name="main":
      -> column: -> sec:name="profile" | -> frm:name="list_card":
         -> inp:name="login" styp:text
         -> sel:name="theme" styp:switch
         -> btn:name="save" action:approve
   -> rcl:source="msg:list":item="row"
   -> ovl: -> dlg:name="confirm" | -> msg:name="saved" styp:snackbar
```

## Multi vector (`-[]>`)

`-[N]>` marks a **critical branching node of logic**: it lifts an object into N
parallel state dimensions instead of a plain yes/no path. The choice is important -
it splits into N state paths and deserves attention when you read the logic. The
dimensions are **logical (states)**, NOT spatial geometry. Usually written after the
colon (`:-[N]>`) as in `create model:-[3]> type=human`.

`:` between vectors selects one element and flows into one common logic; `<>:` opens
several logic paths depending on the selection and requires explicit conditions.

```
create(model:-[3]> type="human")   // -[3]> = critical branching node: 3 state axes

-[3]> [a,b,c]:[d,e,f]:[x,y,z]:  : selects one element -> one common logic
-[3]> [a,b,c]:[d,e,f]:[x,y,z]<>: paths dependency on the selection
     a,d,z -> val:a = d = z
     b,e,y -> val:b = y / e   // / = division
     ->  show()               // default: every selection except the two above
```

`\` filters logic - exclusion/filtering by condition when used inside brackets or
quotes; `/` is plain mathematical division:

```
create\show(file:name="out.xml")  // create, but do not show (logic filter)
list\users                     // filter: everything except "users"
val:rate = 10 / 2              // / = division
```

## Prototypes, blueprints and scope

`scop` sets the scope of a rule or prototype - `scop=root` means global and always active.

```
function:type="agent":scop="root" -> event:create([code, data, file])
   -> create(specfile:lng="VibeDSL" proto):
   -> exam(specfile:syn==VibeDSL:dict:syn)<>:
      -> exam(!(specfile:logic==?))<>:
         -> show(specfile:lang="VibeDSL":source="orig" with(VibeDSL:prnt:strk:->add(ref:lang="usr:lang"))):
            -> usr approve:
               -> create([code, data, file] lng=specfile:lng:name):
                  -> exam(file:syn==specfile:lng:syn):
                     -> exam(file:logic==specfile:logic)<>:
                        -> write:goal
                        -> retry(5)!:rollb
```

- **Prototypes** (`proto` / `blplan`) are the **abstract** formal plans and execution
  templates, kept in `DATA/protos.txt`. `blplan` is the more formal plan variant.
- **Blueprints** are the **ready** models - physically complete vector rules of a
  project/module, kept in `DATA/blueprints.txt`. `incld="<blueprint-id>"` declares
  on the entity which blueprint its code includes; it is a mapping attribute, not
  an import. The imperative that pulls a prototype or blueprint into a specfile is
  `use(<id>)`, which `compiler/compile.py` resolves into the DATA block and
  `API/blueprint_get` / `API/proto_get` serve one at a time.

```
blplan(plan) id="p_goal":desc="formal plan blueprint":incld="goal,retry":action=[create,exam]:scop="root":
   -> create(plan:lng="VibeDSL")
      -> exam(plan:syn==VibeDSL:dict:syn)<>:
         -> goal
         -> retry(5)!:rollb
```

## `ask` - resolution cascade

`ask` never guesses. Resolution order:

1. **Base first** - query `dictionary` / `syntax` / `protos` / `blueprints` via the RAG
   API (`get` / `search`).
2. If the answer is **already recorded**, it is used and the human is **not** asked again.
3. If the base is **silent**, the **human** is asked.

This keeps small models from having to memorise thousands of sessions.

## Grammar rules (strict)

The **frame** of the language is strict - a small model must never need to guess it.
The `:` operator roles and precedence are defined in RULES.MD §7; the enforced rules
are checked by `validator/validator.py` (v2, search-command; run as
`py -X utf8 validator\validator.py <file>`; the old v1 spell-checker is kept as
`validator/validator_deprecated.py`):

- **2D indentation tree**: deeper indent = step down into a scope, same indent =
  step sideways / scope end. A specfile is validated as a tree, not a flat token list.
- **Action scope `()`**: an `action(` opening paren must be closed before the
  indent returns to the command start level; an `extra ) before its ( scope` and
  an `unclosed ( ... )` are errors.
- **`<>:` variant**: the following child lines must each carry `->` ahead
  (`a, d, z -> value = a = d = z`).
- **`\(` change operator** must carry `action="..."` (or `action="..."`) inside.
- **Symbols**: `abstract id="X"` declares objects you can extend with
  `X:prop`/`X:function name="Y"`; `create ... as v` binds variables; `function name="Z"`
  declares functions; `entity:action="...":name="access"` declares
  `entity:access`. A command word is flagged only when its declaration is not
  visible in the scope chain.
- **`use(...)`**: keeps protos/blueprints loaded by id
  (`PROTO/DATA/protos.txt`, `DATA/blueprints.txt`) in memory as higher-level
  code chunks - their ids and declared symbols resolve in the importing scope
   (`use(abstract)`, `use(VibeDSL:proto[abstract])`, `use(agent name=...)`).
- **`{}` = AI custom block, `/* */` and `//` = human comments** (skipped).

Current base additions: `error, error` is a **logic action** (logic-stop trigger;
`function event:error:-> return:exception:response`); `quote` is a verbatim-speech mapping
marker; `rebuild` is an action; `num` is the unified numeric value with
`format("...")` patterns; `flow` is a behavior, `sort` is a mapping.

## The symbol layer - compiling the text language into symbols

The upper layer above is written in words. A model that reasons well on words
reads it directly. A **weak model** (a 4-8B local sub-agent, a quantized 22-64B)
loses the structure inside the prose, so the same logic is compiled into the
lowercase layer: one glyph per word, **and one glyph per grammar operator**, so the
frame of the tree is symbolic too and the model never has to read two notations
at once.

`compiler/compile.py` is that compiler. It emits ONE file with three blocks:

```
-----RULES-----   the base task in English, what each block is for, and the
                  glyph reference (only the marks this file actually uses)
-----DATA-----    every abstract / proto / blueprint that use() pulled in out
                  of the RAG base, each marked with an anchor
-----CODE-----    the specification. Execution starts here and nowhere else.
```

```
py -X utf8 validator\compile.py plan\ide-specfile.vibe -o out.txt
py -X utf8 validator\compile.py plan\ide-specfile.vibe --all-glyphs
php -S 127.0.0.1:8000 router      # then GET /API/compile?file=plan/ide-specfile.vibe
```

| What it does | Rule |
|---|---|
| words | replaced by the glyph of their concept, whole-token only, so `lang` never eats `language` |
| operators | `->` `<-` `<->` `=` `==` `<=` `>=` `<>` `?` `!` `&&` `\|` `\` `/` `*` `+` `-` are glyphs too, matched longest-first so `<->` never degrades to `<-` |
| `&->` | emitted as the anchor glyph U+2022, and `-[N]>` as U+2AAA - the two written spellings the dictionary declares as single glyphs |
| indentation | preserved byte for byte; only tokens are swapped, the tree is never reflowed |
| `""` `{}` `()` `[]` | **never** rewritten. A quoted run is a literal, `{}` is the free-form block, `()` is action scope - that boundary is what the model uses to tell logic from payload |
| `//` `/* */` | human comments, kept verbatim |
| `use(...)` | the import. Pulls the entry out of `DATA/` and compiles it into the DATA block. All four written forms resolve: `use(id)`, `use(a,b)`, `use(VibeDSL:proto[abstract])`, `use(agent:name="coder")`; nested `use()` inside a pulled body is followed too |
| `incld="id"` | **not** an import - it is a mapping attribute (an include of code declared on the entity). Only `use()` pulls |
| reserved ASCII | `%` `;` `{}` `//` `-(id)>` `<(source)-` keep their ASCII form on purpose and are declared as reserved in the RULES block, because compiling them would change meaning (`50%` is a value, not modulo) |
| the base | `DATA/*.txt` is opened **read-only**. A compile never writes to the base |

The report it prints is part of the contract: how many occurrences were
replaced, which marks were emitted, what `use()` resolved, what is still text
(a word the base knows but that owns no glyph yet), and a hard failure if a
glyph was emitted that is not in `compiler/symbols_map.txt`.

`compiler/symbols_map.txt` is policed by `validator/glyphs.py` (G1-G8: no duplicate
codepoint, no CJK/Hangul/fullwidth, NFC and NFKC safe, every glyph word exists
in the master, no description contradicts the master, one mark per concept).
`validator/sort_dict.py` keeps the master dictionary in order; re-run it after
any manual insert, then `validator/spellcheck.py` to rebuild the category splits
and `py ide/gen_data.py` for the IDE.



### The header — the `include.h` of the compiler

`compiler/header.txt` is the one hand-written file with every invariant sentence: the
base task in English, what the three blocks are, how to read a mark, and which
ASCII is reserved on purpose. The compiler inlines it into the RULES block of
every compiled specfile, exactly as a C preprocessor inlines `#include <...>`.

It is a file, not a Python string literal, for three reasons: prose buried in
code cannot be proofread, diffed or translated; it belongs to the base, so it is
served by the RAG API like every other base file (`GET /API/get?dict=header`)
and embedded in the IDE by `py ide/gen_data.py`; and it is **the same bytes on
every compile**, which is what makes it cheap for a small model — the rules text
is a stable prefix that stays in the KV cache instead of being regenerated.

Slots the compiler fills: `@SOURCE@`, `@COUNT_MARKS@`, `@COUNT_TOTAL@`,
`@COUNT_CONCEPTS@`, `@COUNT_DATA@`, `@ANCHOR@`, `@BLOCK_RULES@`, `@BLOCK_DATA@`,
`@BLOCK_CODE@`. A slot the header asks for and the compiler does not know is a
**hard error**, not a blank — a typo in the header must never reach a model as a
hole in its instructions.

Only the per-file part is generated: the GLYPHS table under the header lists only
the marks that file actually uses, in order of first use. `--all-glyphs` prints
the whole table instead.

## The gate

```
py -X utf8 validator\spell_checker_v2.py
```

Ten checks, one verdict, one exit code — dictionary order, category splits, the
mark table invariants, the header slots, no implicit inheritance left in any
code line, no context cut inside a loop, every specfile passing the grammar, every
specfile compiling to known marks with its indentation byte-identical, and a compile
being idempotent. `--fix` applies the safe rewrites and re-verifies before it
reports; `--bless` records pre-existing debt as a baseline so only new failures
are red. See `AGENTS.md` for the table.

## Project layout

```
index            landing page (concepts, syntax, Z vector, prototypes, API table)
router           dev-server router - REQUIRED to execute the extensionless app files
compiler/        the text -> symbol compiler and its two symbol dictionaries
API/get          whole source by:dict=header|dictionary|syntax|blueprints|protos|agents|symbols_map
API/search       RAG search across dictionary/syntax/agents/symbols
API/proto_search search abstract prototypes by id / desc
API/proto_get    exact abstract prototype by id
API/blueprint_search  search ready blueprints by id / desc
API/blueprint_get     exact ready blueprint by id
API/compile      text specfile -> symbol specfile (RULES / DATA / CODE), wraps compiler/compile.py
API/lib          shared helpers (vibedslPage, vibedslToHtml, vibedslSources)
DATA/dictionary_sorted_by_type.txt  master dictionary entries (type sections)
DATA/action.dict, DATA/mapping.dict, DATA/operators.dict, DATA/abstracts.txt  category split canon (validator/spellcheck.py)
DATA/syntax.txt       base syntax symbols
DATA/protos.txt       abstract prototypes (proto / blplan)
DATA/blueprints.txt   ready architectural models (blueprint)
DATA/agents.txt       agent rules
compiler/compile.py       the text -> symbol compiler (RULES / DATA / CODE)
compiler/symbols_map.txt  canonical word <-> glyph table (U+XXXX glyph *-> word - meaning)
compiler/header.txt       the include.h of the compiled output: task, block guide, reserved ASCII
validator/glyphs.py   guard for compiler/symbols_map.txt (G1-G8)
validator/sort_dict.py, validator/spellcheck.py  dictionary order + category splits
validator/spell_checker_v2.py  the single gate: 10 checks, one verdict
validator/explicit_inherit.py  rewrite space-separated mappings as explicit ':'
agents/coder.md       the coder agent (specfile -> exam -> usr approve -> create -> exam -> goal|retry/rollback)
RULES.MD              working rules / protocol
AGENTS.md             repo guide for agents
LICENSE               Apache License 2.0
```

## Run locally

Application files carry **no `.php` extension**; the dev server executes them through
the router, so the router argument is required:

```
php -S 127.0.0.1:8000 router
```

Then open <http://127.0.0.1:8000/>.

## IDE

`ide/` is a browser IDE (Monaco) with live VibeDSL validation (JS port of
`validator/validator.py` (v2), byte-parity checked by `node ide/test_parity.js`).
It loads a vendored Monaco from `temp/package/min/vs`, which is **not** part of
this repository (~70 MB build artifact) - vendors it yourself, e.g. the official
`monaco-editor/min/vs` zip extracted to `temp/package/min/vs`, then:

```
php -S 127.0.0.1:8000 router
```

and open <http://127.0.0.1:8000/ide/>. Regenerate the embedded data after
editing `DATA/`: `py ide/gen_data.py`.

Verify endpoints headless (no PHPUnit; the repo is script-testable):

```
php -l <file>
php API/search
php API/get
php API/proto_get
```

## API endpoints

Domain-relative paths - they resolve under any host, reverse proxy or internal
corporate domain, e.g. `GET <base>/API/get?dict=dictionary`.

| Endpoint | Params | Returns |
|---|---|---|
| `GET /API/get` | `dict=header\|dictionary\|action\|mapping\|operators\|abstracts\|syntax\|blueprints\|protos\|agents\|symbols_map` | Whole requested source as HTML; unknown `dict` -> 404 page |
| `GET /API/search` | `in=<term>` | RAG search across dictionary/syntax/agents; no match -> `[no match ...]` |
| `GET /API/proto_search` | `in=<term>` | Abstract-prototype search by `id=""` / `desc=""`; returns matching objects |
| `GET /API/proto_get` | `id=<proto-id>` | Exact abstract prototype by `id=""`; unknown id -> 404 |
| `GET /API/blueprint_search` | `in=<term>` | Blueprint search by `id=""` / `desc=""`; returns matching objects |
| `GET /API/blueprint_get` | `id=<blueprint-id>` | Exact blueprint object by `id=""`; unknown id -> 404 |
| `GET /API/symbol` | `glyph=<codepoints\|glyph>` or `word=<name>` | The `compiler/symbols_map.txt` row(s), both directions; what a compiler needs |
| `GET /API/compile` | `file=<path relative to repo root>`, `&raw=1` for text/plain | The specfile compiled to symbols: `-----RULES-----` / `-----DATA-----` / `-----CODE-----`, plus the compile report. Path is confined to the repo (403) and must be `.vibe` / `.vibedsl` / `.specfile` (415) |

## License

Apache License, Version 2.0 - see [LICENSE](LICENSE). Usage, modification and
distribution permitted under the terms of the license.

Copyright Enaleven 2026.

---

Powered by **Big Pickle** - crafted with [opencode](https://opencode.ai) - respect and
gratitude to its developers.
