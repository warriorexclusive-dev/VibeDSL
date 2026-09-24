# VibeDSL

**VibeDSL** is a semantic, NLP-based domain-specific language - a **logic constructor**
for tasks, rules and architectures that must be passed clearly to an AI. It is designed
for both AI and humans: a human can write it by hand, and a minimal set of precise
instructions is enough for an AI to assemble the logic.

Version: **v1.0 alfa** - License: **Apache 2.0**.

The language is a **two-dimensional diagram in text**: nodes, arrows and indentation
form two axes (a whiteboard like Miro). The third axis (Z) holds **states** - see
[Z vector](#z-vector--z-) below.

## Base syntax

```
[node:name] -> [node:par]     chain: a logical unit delegates to a node

parent:                       parent is the object with a colon at the end of the line
   -> child                   children are indented and begin with an arrow marker
     -> grandchild            indentation = nesting (Python/YAML style)

:                             logical operator + null-safe presence check (a:b:c);
                              checks the object and marks the condition that the logic
                              is done; can take the <> multi-way prefix
->  <-  <->                   right strict link / inverse / two-way public interface
==  =                         equality (if-then gate) / assignment
<=  >=                        comparison: less-or-equal / greater-or-equal
-(id)>                         link to an internal object of the spec (by id)
<(src)-                        link to an external source beyond the spec: one-way departure, may not return
|  ||  !                      logical or / and / reverse
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
| `&->` | remember/author marker - memorizes the node as an etalon (used by `abstract`: `&-> abstract(act id=...)`) |
| `quote` | verbatim speech marker (mapping to base) - "this was said", not for interpretation |
| `=` `==` | assignment / equality (if-then gate) |
| `->` `<-` `<->` | right strict link / inverse / two-way public interface |
| `id=""` `desc=""` | object identity and description (used by `*_get` / `*_search`) |
| `ask` | resolution cascade (see below) |

Command style uses phonetic abbreviations (`crt`, `exam`, `wrt`, `apr`, `strk`, `vld`,
`exst`, `rollb`, `prnt`, `varn`) - readable without a dictionary.

## Vectors

Logic is built as chains of linked vectors: `[model1]->[model2]` delegates a logical
unit to the next node. Ordered collections are vectors too: `[]` blocks, `lst`
(list/array/collection), `tab` (in-memory table), `inx` (indexed access), `fifo` (queue).

Vertical structure is built like YAML: a colon-parent opens an object, indented
arrow-children nest into it.

```
root:
   -> lst:[v1,v2,v3]
      -> tab:rows
         -> inx:[0,1,2]
   -> sel[val1,val2]->fun data=sel:ret
      -> for(i<10,incr(1))
         -> data:inx[i]

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

- Composition: `row col grd frm grp ovl pag sec hscroll vscroll spr`
- Recycler (first-class, not composed from abstracts): `rcl`
- Navigation: `nav bct tab link`
- Input controls: `inp btn sel tgl slr pic srch`
- Display & feedback: `crd lst icn avt bdg dvr prg skn tip msg dlg sht thm`
- User input events: `kdown kpress kup mosup mosdown scrtap enter`
- Entities: `view` (concrete frame/screen - not `vis`, that is the visual element/type abstraction), `evt,event` (lifecycle/callback marker alias, e.g. `event type="onCreate" -> load view`)

Sketch:

```vibedsl
prj name="settings" thm="m3":
   -> pag name="main":
      -> col: -> sec name="profile" | -> frm name="list_card":
         -> inp name="login" styp:text
         -> sel name="theme" styp:switch
         -> btn name="save" act:apr
   -> rcl src="msg:list" item="row"
   -> ovl: -> dlg name="confirm" | -> msg name="saved" styp:snackbar
```

## Multi vector (`-[]>`)

`-[N]>` marks a **critical branching node of logic**: it lifts an object into N
parallel state dimensions instead of a plain yes/no path. The choice is important -
it splits into N state paths and deserves attention when you read the logic. The
dimensions are **logical (states)**, NOT spatial geometry. Usually written after the
colon (`:-[N]>`) as in `crt model:-[3]> type=human`.

`:` between vectors selects one element and flows into one common logic; `<>:` opens
several logic paths depending on the selection and requires explicit conditions.

```
crt(model:-[3]> type="human")   // -[3]> = critical branching node: 3 state axes

-[3]> [a,b,c]:[d,e,f]:[x,y,z]:  : selects one element -> one common logic
-[3]> [a,b,c]:[d,e,f]:[x,y,z]<>: paths depend on the selection
     a,d,z -> val a = d = z
     b,e,y -> val b = y / e   // / = division
     ->  show()               // default: every selection except the two above
```

`\` filters logic - exclusion/filtering by condition when used inside brackets or
quotes; `/` is plain mathematical division:

```
crt\show(file name="out.xml")  // create, but do not show (logic filter)
list\users                     // filter: everything except "users"
val rate = 10 / 2              // / = division
```

## Prototypes, blueprints and scope

`scop` sets the scope of a rule or prototype - `scop=root` means global and always active.

```
fun type="agent" scop="root" -> event:crt([code, data, file])
   -> crt(spec lng="VibeDSL" proto):
   -> exam(spec:syn==VibeDSL:dict:syn)<>:
      -> exam(!(spec:logic==?))<>:
         -> show(spec lang="VibeDSL" src="orig" with(VibeDSL:prnt:strk:->add(ref lang="usr:lang"))):
            -> usr apr:
               -> crt([code, data, file] lng=spec:lng:name):
                  -> exam(file:syn==spec:lng:syn):
                     -> exam(file:logic==spec:logic)<>:
                        -> wrt:goal
                        -> retry(5)!:rollb
```

- **Prototypes** (`proto` / `blplan`) are the **abstract** formal plans and execution
  templates, kept in `DATA/protos.txt`. `blplan` is the more formal plan variant.
- **Blueprints** are the **ready** models - physically complete vector rules of a
  project/module, kept in `DATA/blueprints.txt`. They are pulled in by id through the
  `incld="<blueprint-id>"` attribute, which resolves via `blueprint_get` and injects the
  blueprint's behavior into the prototype.

```
blplan(plan) id="p_goal" desc="formal plan blueprint" incld="goal,retry" act=[crt,exam] scop="root":
   -> crt(plan lng="VibeDSL")
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
  step sideways / scope end. A spec is validated as a tree, not a flat token list.
- **Action scope `()`**: an `action(` opening paren must be closed before the
  indent returns to the command start level; an `extra ) before its ( scope` and
  an `unclosed ( ... )` are errors.
- **`<>:` variant**: the following child lines must each carry `->` ahead
  (`a, d, z -> value = a = d = z`).
- **`\(` change operator** must carry `act="..."` (or `action="..."`) inside.
- **Symbols**: `abstract id="X"` declares objects you can extend with
  `X:prop`/`X:fun name="Y"`; `crt ... as v` binds variables; `fun name="Z"`
  declares functions; `entity:act="...":name="access"` declares
  `entity:access`. A command word is flagged only when its declaration is not
  visible in the scope chain.
- **`use(...)`**: keeps protos/blueprints loaded by id
  (`PROTO/DATA/protos.txt`, `DATA/blueprints.txt`) in memory as higher-level
  code chunks - their ids and declared symbols resolve in the importing scope
  (`use(order_bp)`, `use(VibeDSL:proto[if,goal,fail])`, `use(agent name=...)`).
- **`{}` = AI custom block, `/* */` and `//` = human comments** (skipped).

Current base additions: `err, error` is a **logic action** (logic-stop trigger;
`fun event:err:-> ret:except:response`); `quote` is a verbatim-speech mapping
marker; `rebuild` is an action; `num` is the unified numeric value with
`format("...")` patterns; `flow` is a behavior, `sort` is a mapping.

## Project layout

```
index            landing page (concepts, syntax, Z vector, prototypes, API table)
router           dev-server router - REQUIRED to execute the extensionless app files
API/get          whole source by dict=dictionary|syntax|blueprints|protos|agents
API/search       RAG search across dictionary/syntax/agents
API/proto_search search abstract prototypes by id / desc
API/proto_get    exact abstract prototype by id
API/blueprint_search  search ready blueprints by id / desc
API/blueprint_get     exact ready blueprint by id
API/lib          shared helpers (vibedslPage, vibedslToHtml, vibedslSources)
DATA/dictionary_sorted_by_type.txt  master dictionary entries (type sections)
DATA/action.dict, DATA/mapping.dict, DATA/operators.dict, DATA/abstracts.txt  category split canon (validator/spellcheck.py)
DATA/syntax.txt       base syntax symbols
DATA/protos.txt       abstract prototypes (proto / blplan)
DATA/blueprints.txt   ready architectural models (blueprint)
DATA/agents.txt       agent rules
agents/coder.md       the coder agent (spec -> exam -> usr apr -> crt -> exam -> goal|retry/rollback)
RULES.MD              working rules / protocol
AGENTS.md             repo guide for agents
VibeDSL.md            language overview
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
| `GET /API/get` | `dict=dictionary\|syntax\|blueprints\|protos\|agents` | Whole requested source as HTML; unknown `dict` -> 404 page |
| `GET /API/search` | `in=<term>` | RAG search across dictionary/syntax/agents; no match -> `[no match ...]` |
| `GET /API/proto_search` | `in=<term>` | Abstract-prototype search by `id=""` / `desc=""`; returns matching objects |
| `GET /API/proto_get` | `id=<proto-id>` | Exact abstract prototype by `id=""`; unknown id -> 404 |
| `GET /API/blueprint_search` | `in=<term>` | Blueprint search by `id=""` / `desc=""`; returns matching objects |
| `GET /API/blueprint_get` | `id=<blueprint-id>` | Exact blueprint object by `id=""`; unknown id -> 404 |

## License

Apache License, Version 2.0 - see [LICENSE](LICENSE). Usage, modification and
distribution permitted under the terms of the license.

Copyright Enaleven 2026.

---

Powered by **Big Pickle** - crafted with [opencode](https://opencode.ai) - respect and
gratitude to its developers.
