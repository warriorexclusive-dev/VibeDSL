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
<=  >=  !=                    comparison: less-or-equal / greater-or-equal / not equal
+=  -=                       add/subtract to the object (numbers or logic, OOP-like)
c++                           postfix increment by one (C-style)
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

## Z vector (`-Z>`)

Industrial requests need three-dimensional states, and `-Z>` lifts such an object off
the 2D graph **without breaking it** - the object stays a tagged node instead of the
graph branching into 3D. The dimensions are **logical (states)**, NOT spatial geometry.
The flag is optional, usually written after the colon (`:-Z>`) as in
`crt model:-Z> type=human`, and never changes semantics.

`:` between vectors selects one element and flows into one common logic; `<>:` opens
several logic paths depending on the selection and requires explicit conditions.

```
crt model:-Z> type=human      -Z> = lift this node into the 3rd state axis

-Z> [a,b,c]:[d,e,f]:[x,y,z]:  : selects one element -> one common logic
-Z> [a,b,c]:[d,e,f]:[x,y,z]<>: paths depend on the selection
     a,d,z -> val a = d = z
     b,e,y -> val b = y \ e   \ = division
     ->  show                 default: every selection except the two above
```

`/` subtracts logic - exclusion/filtering when used inside brackets or quotes;
`\` is plain mathematical division:

```
crt/show file name="out.xml"     create, but do not show (logic subtraction)
list/users                       filter: everything except "users"
val rate = 10 \ 2                \ = division
```

## Prototypes, blueprints and scope

`scop` sets the scope of a rule or prototype - `scop=root` means global and always active.

```
fun type=agent scop=root -> act == crt [code, data, file]
   -> crt spec lng=VibeDSL proto:
   -> exam(spec:syn==VibeDSL:dict:syn)<>:
      -> exam(spec:logic!=?)<>:
         -> show spec lang=VibeDSL src=orig with(VibeDSL:prnt:strk:->add(ref lang=usr:lang)):
            -> usr apr:
               -> crt [code, data, file] lng = spec:lng:name:
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
blplan(plan) id="p_goal" desc="formal plan blueprint" incld="goal,retry" act=[crt,exam] scop=root:
   -> crt plan lng=VibeDSL
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
DATA/dictionary.txt   full dictionary entries (incl. keyword list)
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
