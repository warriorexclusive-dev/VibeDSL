# VibeDSL

**VibeDSL** = **V**ector-based, **i**nheritance-based, **b**ehavioral,
**e**vent-driven, **d**omain-oriented **l**anguage.

A semantic and NLP-based DSL — a **logic constructor** for tasks, rules and
architectures that must be passed clearly to an AI. It is designed for both AI
and humans. Syntax is strict in the frame (arrows, colons, dictionary keys,
indent tree), while open blocks `{}` and custom strings `""` are intentionally
free-form.

The language base is served by the local RAG API:

- `GET /API/get?dict=dictionary` — full keyword dictionary with examples
- `GET /API/get?dict=syntax` — base syntax symbols
- `GET /API/get?dict=agents` — agent rules
- `GET /API/search?in=<term>` — RAG search across dictionary/syntax/agents
- `GET /API/blueprint_search?in=<term>` — search blueprints by `id=""` / `desc=""`
- `GET /API/blueprint_get?id=<id>` — exact blueprint object by `id=""` (404 if absent)

Sources under `DATA/`: `dictionary.txt`, `syntax.txt`, `blueprints.txt`, `agents.txt`.

---

## Templates — шаблоны

Templates are declared with the `proto` keyword: a prototype describes the
structure and constraints of a node; every artifact is examined (`exam`) against
it before it is accepted. `blueprint` are blueprints — base abstract patterns
and behavior laws that always hold.

```vibedsl
*-> proto(if) id="if" act=[crt,exam] type=rule:
   -> syn="obj~obj"

*-> proto(goal) id="goal" act=[wrt,exam,crt]
   show(cxt)
   show(msg(goal))
```

Instantiation / referencing a template by name and checking an artifact:

```vibedsl
fun type=rule scop=root
   -> crt spec lng=VibeDSL proto:if
   -> exam(spec:syn==VibeDSL:dict:syn)<>:goal
```

## Vectors — векторы

Logic is built as chains of linked vectors: `[model1]->[model2]` delegates a
logical unit to the next node. Ordered collections are vectors too: `[]` blocks,
`lst` (list/array/collection), `tab` (in-memory table), `inx` (indexes), `fifo`
queues.

```vibedsl
-> lst:[v1,v2,v3]
-> tab:rows -> inx:[0,1,2]
sel[val1,val2]->fun data=sel:ret
for(i<10,incr(1))->data:inx[i]
```

## Inheritance — наследование

Hierarchy is expressed with `sub` (subclass / child entity), `mod` (class,
module), `abfun` (abstract / interface / inject), `generic` (generic), `gener`
(generation). Presence and typing: `is` / `pres` (instanceof), `tp:type`, `styp`
(subtype), `<->` two-way public interface.

```vibedsl
-> mod name="base_controller"
   -> sub:cls
   -> abfun:interface
   -> generic:T
```

## Behavioral — поведение

The language is rule-oriented: `fun type=rule scop=root` with an `act` chain.
Gates: `if` / `elif` / `els`, `switch` / `case` / `brk`, loops `loop`, examination
`exam(obj~obj)`, `retry(N)`, rollback `rollb`, and explicit ends `goal` / `fail`,
variants `varn`.

```vibedsl
if(a==b)->ret
switch: case val1: data1=val1 bk
exam(obj~obj):retry(5)!:rollb
```

## Events — события через инструкцию `fun`

`fun` is the function declaration instruction. Combined with the `evt`
(event/callback) marker it declares an **event** or callback handler; `call` is
the entry/function-call point. Timers that raise events: `dtim` (delayed timer),
`tik` (time elapse), `delay` (period).

```vibedsl
fun name="on_update" par="data" evt:
   -> run:check par=data:
      -> data:pres(data)->ret
   -> call:notify{async}
   -> with(strk)->add(ref lang=usr:lang)
```

Timers and error events:

```vibedsl
[llm:con:out:txt="hi im here" tic(1m)]
dtim:500 -> call:on_tick
try:->logic ->cch:err ->fin:close
```

## Domain-oriented — домен

Targeted at domains: `domain` (domain), `dir` (directory / subdomain), `prj`
(project), `infr` (infrastructure unit), `svc` (service), `ept` (endpoint),
`api` (API / interface contract).

```vibedsl
prj name="picture_lib":
   -> domain:name
   -> svc:micro
   -> ept:"/api/v1"
```

---

Dictionary keys, prototypes and agent rules live in `DATA/*.txt` and are served
via the local RAG API (`API/get`, `API/search`, `API/blueprint_search`, `API/blueprint_get`) to the agents.