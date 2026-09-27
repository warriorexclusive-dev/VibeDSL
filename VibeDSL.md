# VibeDSL

**VibeDSL** = **V**ector-based, **i**nheritance-based, **b**ehavioral,
**e**vent-driven, **d**omain-oriented **l**anguage.

A semantic and NLP-based DSL — a **logic constructor** for tasks, rules and
architectures that must be passed clearly to an AI. It is designed for both AI
and humans. Syntax is strict in the frame (arrows, colons, dictionary keys,
indent tree), while open blocks `{}` and custom strings `""` are intentionally
free-form.

The language base is served by the local RAG API:

- `GET /API/get?dict=dictionary` — full keyword dictionary with examples (master, separated by type)
- `GET /API/get?dict=action|mapping|operators|abstracts` — category split dictionaries (generated into `DATA/` by `validator/spellcheck.py`)
- `GET /API/get?dict=syntax` — base syntax symbols
- `GET /API/get?dict=agents` — agent rules
- `GET /API/search?in=<term>` — RAG search across dictionary/syntax/agents
- `GET /API/blueprint_search?in=<term>` — search blueprints by `id=""` / `desc=""`
- `GET /API/blueprint_get?id=<id>` — exact blueprint object by `id=""` (404 if absent)

Sources under `DATA/`: `dictionary_sorted_by_type.txt` (master), split canon `action.dict` / `mapping.dict` / `operators.dict` / `abstracts.txt`, `syntax.txt`, `blueprints.txt`, `agents.txt`.

---

## Templates — шаблоны

Templates are declared with the `proto` keyword: a prototype describes the
structure and constraints of a node; every artifact is examined (`exam`) against
it before it is accepted. `blueprint` are blueprints — base abstract patterns
and behavior laws that always hold.

```vibedsl
prototype:id="abstract":required:type[item,function,prop]:required:condition
```

Instantiation / referencing a template by name and checking an artifact:

```vibedsl
function:type=rule:scop=root
   -> create specfile:lng=VibeDSL prototype:if
   -> exam(specfile:syn==VibeDSL:dict:syn)<>:goal
```

## Vectors — векторы

Logic is built as chains of linked vectors: `[model1]->[model2]` delegates a
logical unit to the next node. Ordered collections are vectors too: `[]` blocks,
`list` (list/array/collection), `table` (in-memory table), `index` (indexes), `fifo`
queues.

```vibedsl
-> list:[v1,v2,v3]
-> table:rows -> index:[0,1,2]
sel[val1,val2]->function:data=sel:return
for(i<10,incr(1))->data:index[i]
```

## Inheritance — наследование

Hierarchy is expressed with `sub` (subclass / child entity), `module` (class,
module), `abfun` (abstract / interface / inject), `generic` (generic), `gener`
(generation). Presence and typing: `is` / `pres` (instanceof), `tp:type`, `styp`
(subtype), `<->` two-way public interface. `mod` is the logic modify operator.

```vibedsl
-> module:name="base_controller"
   -> sub:cls
   -> abfun:interface
   -> generic:T
```

## Behavioral — поведение

The language is rule-oriented: `function type=rule scop=root` with an `action` chain.
Gates: `if` / `elif` / `else`, `switch` / `case` / `break`, loops `loop`, examination
`exam(obj~obj)`, `retry(N)`, rollback `rollb`, and explicit ends `goal` / `fail`,
variants `variant`.

```vibedsl
if(a==b)->return
switch: case val1: data1=val1 bk
exam(obj~obj):retry(5)!:rollb
```

## Events — события через инструкцию `function`

`function` is the function declaration instruction. Combined with the `event`
(event/callback) marker it declares an **event** or callback handler; `call` is
the entry/function-call point. Timers that raise events: `dtim` (delayed timer),
`tik` (time elapse), `delay` (period).

```vibedsl
function:name="on_update":param="data" event:
   -> run:check:param=data:
      -> data:pres(data)->return
   -> call:notify{async}
   -> with(strk)->add(ref lang=usr:lang)
```

Timers and error events:

```vibedsl
[llm:con:out:txt="hi im here" tic(1m)]
dtim:500 -> call:on_tick
try:->logic ->catch:error ->finally:close
```

## Domain-oriented — домен

Targeted at domains: `domain` (domain), `directory` (directory / subdomain), `prj`
(project), `infr` (infrastructure unit), `service` (service), `ept` (endpoint),
`api` (API / interface contract).

```vibedsl
prj:name="picture_lib":
   -> domain:name
   -> service:micro
   -> ept:"/api/v1"
```

---

## UI — визуал (Material Design 3 reference)

The visual/frontend zone follows Material Design 3 vocabulary (truly in trend,
and a clear textbook). Tokens are short (3-4 chars) for small-model memory,
abstract over precise (precision closes via `styp`/`{}`).

Composition: `row col grd frm grp ovl pag sec hscroll vscroll spr`
Recycler (first-class, not composed): `rcl`
Navigation: `nav bct table link`
Input controls: `inp btn sel tgl slr pic srch`
Display & feedback: `crd list icn avt bdg dvr prg skn tip msg dlg sht theme`
User input events: `kdown kpress kup mosup mosdown scrtap enter`
Entities: `view` (concrete frame/screen, distinct from `graphics` - visual element/type), `event,event` (lifecycle/callback marker alias)

```vibedsl
prj:name="settings":theme="m3":
   -> pag:name="main":
      -> col: -> sec:name="profile" | -> frm:name="list_card":
         -> inp:name="login" styp:text
         -> sel:name="theme" styp:switch
         -> btn:name="save" action:approve
   -> rcl:source="msg:list":item="row"
   -> ovl: -> dlg:name="confirm" | -> msg:name="saved" styp:snackbar
```

---

Dictionary keys, prototypes and agent rules live in `DATA/*.txt` and are served
via the local RAG API (`API/get`, `API/search`, `API/blueprint_search`, `API/blueprint_get`) to the agents.