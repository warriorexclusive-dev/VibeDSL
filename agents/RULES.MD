
# AI CORE RULES

## 1. SYNTAX COMPLIANCE
* Execute all operations exclusively through the defined syntax.
* Do not deviate from the syntax format under any circumstances.

## 2. TRANSLATION PROTOCOL
* Intercept all user prompts immediately upon receipt.
* Convert raw user input into the designated syntax before processing.

## 3. CONTEXT PERSISTENCE & STORAGE
* Save the translated syntax into the active system context immediately.
* Retain the structural context across all subsequent turns.

## 4. LANGUAGE DECLARATION
* VibeDSL, it's a semantic and NLP base DSL language
* This language created for architecture or behavior pattern development
* This language designed to be suitable for both AI and humans.  

## 5. LANGUAGE CONSTRAINTS SCOPE VIBEDSL
* Do not use filler words, greetings, or meta-explanations. in VibeDSL
* Output to file,schema or other in VibeDSL sintax, only the direct functional result. 
* STRICT SYNTAX ADHERENCE: All incoming requests must be converted strictly into VibeDSL syntax. Ignoring or simplifying VibeDSL syntax is prohibited. 
* You must map the written text, syntax rules, and vocabulary precisely, as in a programming language.
* VibeDSL is a SEMANTIC CONSTRUCTOR for tasks, rules and architectures that must be passed clearly to an AI (this or any other). It is NOT a formal grammar language.
* Therefore the exact frame (arrows, colons, dictionary keys, indent tree) IS strict, but the OPEN blocks `{}` and custom strings `""` are intentionally FREE-FORM and must never be over-validated or rewritten into rigid schema.


## 6. STRICT SYNTAX PARSE RULE
* The parent is always the object with a colon (`:`) at the end of the line.
* All child elements MUST be indented and begin with one of the following markers: `->`, `-`, `<-`, or `<->`.
* Do not infer context unless explicitly stated; for example, if `spec` is specified, it applies only to the description of specifications or roadmaps.
* EXIT-ON-CLEAN: the first pass with PASS (errors=0, all exam gates hold) ENDS the loop -> wrt:goal, stop. Max 3 passes total; a next pass ONLY on a concrete reproduced error. NEVER re-run or "improve" a passing artifact, never add passes after a clean result: perfectionist rework makes the model INVENT and drops accuracy to ~75% without the dictionary / 95% after 3 clean passes - a passing artifact is DONE, the exit itself is the feature.
* Consult the dictionary for this.


## 7. SYNTAX AND BASE COMMANDS
* it's is a logical programming language name VibeDSL syntax [node:node]->[node:par], -> delegate:function or other node, node it's logical unit [uroot:rule]->[file:wrt]->{llm:lng = "VibeDSL"}, this example of rule 
* Logical abbreviations are permitted and even encouraged, provided the logic does not involve branching.
* It is important to maintain logical consistency among the elements; check yourself for a coherent chain of logic.
* example [node:child_node]
            ->a==b
              ->c=d 
* syntax of functions -> fun:name="example" par="val1" -> logic. 
* [] - block of multiple logical objects, exxample [val1,val2,val3,...], ... applies only if there is a valid array reference and the array length exceeds 10 elements. 
* {} it,s marker of declaration a functionaly custom logic of element, it,s is custom specific functionaly logic of object 
* :, !:, |, &&, ->,<->,<-,==,=, <=, >=, <(src)-, -(id)>, <-(), ()->, logical way and construct operators 
* aliases: | = or, && = and, ! = not; / = division, \ = logic filter; <> = multi-way branching, NOT "not equal" (use !(a==b)) 
* "" way to сustomisation mapping all units, example: infr:->node:type="panasonic ats" name ="telephony"
* part and stage commant as separator of logic, syntax and example: part 1: (isolate logic), part2 (isolate logic) | stage 1: (isolate logic), stage 2 (isolate logic) <- part 1 logic DSL schema as reference  
* Try to keep your scripts as concise as possible.
* dictionary byte - keyword - description
* You must strictly distinguish between the types of arrows and colons. An error in an arrow breaks the architectural graph.
* : it's a LOGICAL operator and at the same time a NULL-SAFE PRESENCE/possibility check. ALL entities in VibeDSL are VIRTUAL / NON-PHYSICAL by default (they exist only as logical definitions), therefore a chain `a:b:c` is a block-scheme sequence: verify `a` exists & is executable -> descend to `b` -> verify `b` -> descend to `c`. Each `:` returns Y|true and lets the logic continue, or HALTS the logic if the property is absent / not possible. `!:` = NO|false.
* : -> CONTEXT ROLES (resolved by position, priority order):
   1) presence/possibility check:  `node:prop` or `[node:name]` -> verify the logical property exists and is executable, otherwise halt
   2) boolean validator:  `expr:` / `xref:` -> returns Y|N, gates the branch (the same presence check applied to a condition)
   3) parent/context declaration: colon at the END of a line opens the child tree (the parent is verified as existing before its children run)
   4) payload separator:  `key:value` / `par:parity="x"` -> the payload exists if the key exists
* -> PRECEDENCE ORDER (left -> right, top -> bottom):
  - on ONE line: resolved left to right, arguments consumed in order of appearance
  - in a TREE: resolved top to bottom, each deeper level of code in the listing is a deeper nested object
  - NESTING is set by INDENTATION (Python/YAML style): the parent is always the object with the colon (`:`) at the end of the line and with a child block `-> `, indented deeper
  - equal indentation = same level (sibling nodes); deeper indentation = child node
  - an ARROW always binds a whole node; a COLON always binds inside a node; never concatenate free text and arrows inside a single token.
* example implementation specs
  prj:name="picture_lib":
     -> type=lib
        node=root
        lng:name="c++"
        skl:code="middle"
        skl:arc="senior"
        targ:prj:name="http server"
        module:name:"load_controller":
        <-> fun name:load_image par:name="pic"
in:   picture->
             cnv:  byte[]->
             out:  http request {generate http tomcat request class}

### 7.1 STRICT GRAMMAR (VALIDATOR)
* enforced by `validator/validator.py`: `py validator\validator.py <file>` checks any VibeDSL block against the dictionary (sorted) categories + these rules
* `fun` / `func` / `function` is a DECLARATION keyword: followed by a SPACE, then the name. `fun(do)` is an error; `fun name(...)` is the form.
* EVERY ACTION declares scope `()`: `crt(...)`, `show(...)`, `ret(...)`. A bare action word = mapping key, NOT a call.
* PROPER NAMES / bare values after `=` go into quotes: `name="out.xml"`, `lng="VibeDSL"`. Bare word after `=` = warning.
* FLOW MODEL: `fun` = executable function; `abstract` = pure concept (idea) - defines properties/behavior for a group or single of future entity, cannot create an instance of itself. Flow = input:function -> executable:function (Java-abstract analogy).
* ALIAS KWS: `alias [...] as NAME` (grammar word `as`).
* USERDEFS register: `abstract id="X"` and `alias [...] as NAME`; abstract body = `[abstract body]`, not re-validated. `{}` = AI custom block; `/* */` and `//` = human comments (skipped).
* `act="..."` declares a function - two canonical forms, written in VibeDSL:
  - `abstract "open_file" -> act="open file by name"` - declares:function `open_file`; call: `open_file("main.txt")`
  - `file:act="grant access to user":name="access"` - declares entity function `file:access` (`:name="..."` binds the name to the same declaration); call: `file:access(context:user)`
* SYNTAX REFERENCE: use the RAG base (`DATA/dictionary_sorted_by_type.txt` + `DATA/syntax.txt`) and `py validator\validator.py <file>`; add new rules in short English - save tokens.

## 8. DICTIONARY
* If you encounter a standard definition, do not attempt to write a custom version; instead, suggest that the user expand the dictionary. If you encounter a standard action, create a blueprint (ready architectural model) and record it in the rules.
* start language dictionary
* The dictionary is NOT stored inline. It is served by the local RAG API:
   -> GET /API/get?dict=dictionary  : keywords + syntax base, descriptions and usage examples
   -> GET /API/get?dict=syntax      : base syntax symbols
   -> GET /API/get?dict=blueprints  : ready architectural models (blueprint) - ready vector rules of projects/modules
   -> GET /API/get?dict=protos      : abstract prototypes (proto/blplan) - formal plans, execution templates
   -> GET /API/search?in=<term>     : RAG search across dictionary/syntax/agents (no blueprints/protos)
   -> GET /API/blueprint_search?in=<term>  : search ready blueprints by id / desc
   -> GET /API/blueprint_get?id=<id>       : exact ready blueprint by id
   -> GET /API/proto_search?in=<term>      : search abstract prototypes by id / desc
   -> GET /API/proto_get?id=<id>           : exact abstract prototype by id
* If a keyword is missing or unclear, consult the RAG first; never invent a new meaning.
* end language dictionary

### 8.1 CANONICAL ALIASES (dictionary reconciliation)
* A key has ONE canonical meaning; aliases below are interchangeable and map to it:
* dict,dic    - dictionary
* pat,patn    - pattern
* blueprint     - blueprint (behavior law / base pattern)
* cont,cnt,ctx- content / context
* stk,strk    - stroke / line of text
* prnt,show   - print / console output
* lang,lng    - target language (c++, go, xml, yaml,...)
* rm,del      - remove
* answ,ans    - answer to user
* lag          - link aggregation (network)
* delay        - delay / period
* logs,log    - logging
* req,reqr    - request / required
* uslng       - user language (rus is the same as `usr:lang`)
* return,ret   - return value
* catch,cch    - catch block
* err,error    - logic action of error (logic-stop trigger); alt form: fun event:err:-> ret:except:response
* quote        - verbatim speech marker (mapping to base): "this was said", not for interpretation
* break,brk    - break
* func,function,fun - function
* import,incld - include
* nil,void,null - exact empty value (NOT `none`, which is logical non-halting absence)
* true,false   - boolean literals (synonyms of the bool values Y / N)
* class,module - class / module
* and,&&        - logical AND
* or,|         - logical OR
* not,!        - logical NOT
* /            - mathematical division; \ - logic filter (exclusion by condition)
* if `component` is ambiguous in a script, use the unambiguous full word `component`; `compil` is always the compiling meaning.
* **Short forms are allowed; an abbreviation beside its own full word is not.**
  A short form exists to keep the language writable - `architecture` in full
  would curse it - and it is not a defect in itself. What makes a short form a
  bad anchor is having nothing say what it stands for, because then a model has
  to take it on faith as an agent rule, and real tests showed not every model
  holds those. Two legal anchors, either one enough: the full word stated
  literally (`arc - architecture`), or a full definition of the meaning, where
  the word itself never appears and is not needed.
  But if the full form exists as the same concept, the abbreviation is redundant
  and the DICT check refuses the pair - it is `col` no longer, `column` and
  nothing else, and the whole IDE spec was rewritten around that. What is
  forbidden is a short form in an example with no mapping anywhere: `fun:`,
  `par:`, `err:`, `scop:`, `syn:`, `ret:` were all of that kind, 47 occurrences,
  and every example now teaches the full word. `val` and `arc` both stay, for
  the same reason from opposite ends: there is no full form in the base to
  expand into.
* Sources stay in sync: the master dictionary lives in `DATA/dictionary_sorted_by_type.txt` (category split canon `DATA/action.dict`, `DATA/mapping.dict`, `DATA/operators.dict`, `DATA/abstracts.txt` generated by `validator/spellcheck.py`) and is served via RAG (`GET /API/get?dict=dictionary`); RULES.MD references it.



## 9. SYNTAX GUARD RULES
* validate: syntax in dictionary before emit
* validate: prototypes in logic tree before emit

## 10. BASE AGENT RULES 

fun:type="rule":scop="root" -> event:crt([logic,arc:ref,spec,plan]) -> lng="VibeDSL"

fun:type="rule":scop="root" -> event:answ(user) -> lng=usr:lang

fun:type="rule":scop="root" -> event:crt([code, data, file])
  -> crt(spec:lng="VibeDSL" proto):
  -> exam(spec:syn==VibeDSL:dict:syn)<>:
     -> exam(!(spec:logic==?))<>:
        -> show(spec:lang="VibeDSL":src="orig" with(VibeDSL:prnt:strk:->add(ref lang=usr:lang))):
           -> usr apr:
              -> crt([code, data, file] lng=spec:lng:name):
                 -> exam(file:syn==spec:lng:syn): 
                    -> exam(file:logic==spec:logic)<>:
                       -> wrt:goal
                       -> retry(5)!:rollb
                 -> retry(5)      
        -> retry(5)
     -> show(varn(varn5)):retry   

VibeDSL:

   The abstract record below is the reference example of prototype syntax and
   is permanent. Every other prototype that stood here was scaffolding from
   before the syntax rules existed, and a model reading them learned the wrong
   form. Any prototype added later is measured against this line.

prototype:id="abstract":required:type[item,function,prop]:required:condition

fun:type="rule":scop="root" -> use(prototype:id="abstract")
fun:type="rule":scop="root" ->
   prompt:lng == "VibeDSL":
      prompt:run()

fun:type="rule":scop="root" -> get(think:->show()){without conversion to user lang}
fun:type="rule":scop="root" -> usr:lang="RU:ru"   



## 11. INSIDE OPEN AI RULE 
* Rule config file location "~USER_DIR~\.config\opencode\AGENTS.md"

## `->` - the constructor, and the operator that shortens it

`->` builds the thing declared before it. Everything after `->` says what is
being built and with what, and the part before it says what that is. This is
the same relation `class IEntity` has to its virtual methods: a prototype
names the entity, `->` constructs it, the slots are its constructor arguments.
Two things follow, and they are the same fact seen from two sides.
**In a specification, `->` shortens the operator.** A thing is declared once,
with its `id`, and every use of it is then written `object:chain:id`. The
declaration is the long form and the use is the short one.
```vibedsl
abstract:prop:id="color" -> frm:style:prop     // use frm:style:color
```
Read the chain as "a `prop`, placed on `frm`, inside `style`". The type word
in the chain is what tells you the use-site spelling - drop the type word, keep
the chain, append the id.
**In a prototype, `->` constructs, and the declared names are the defaults.**
A constructor supplies what the caller did not say, so a prototype can be
written once and stay short at every use site.
```vibedsl
proto:id="param":function:prop:name="parametr" -> prop:name="id":required
// use: func:parametr:"id"
```
`name="parametr"` is the name the entity is reached by when nothing else says,
and `-> prop:name="id"` says the thing it constructs is an id rather than a
plain prop - a different claim, and the one that says whether a value has to
be given. The use site drops `prop:name=` and writes `func:parametr:"id"`, which
is the default spelled out rather than omitted.
The rule in one line: **what you declare is long, what you use is short, and
`->` is the only thing connecting them - because it is the constructor, and a
constructor is what makes the declared thing exist.**

This section replaces the one that lived in `VibeDSL.md`. That file was
stale as a whole and went with the rest; this rule is not, and it is
here now because it is the only statement of what `->` means.
The named examples come from `PY_IDE/window.vibe`, which is the syntax
that actually compiles.

## 12. WRITING AN ABSTRACT, AN ALIAS, AND A STRING - in glyphs

Everything in this section is in glyphs, because the rule is that specs are
written in glyphs. A word form here would teach the thing this section is
against.

### 12.1 the abstract: `⌰` and a type and a `§`

An abstract is `⌰` (abstract) plus a type plus `§` (id) plus `⁐` (action).
The type is not optional. It is one of `ʩ` (function), `⬝` (item), `⌗` (prop).

```
• ⌰:ʩ:§="build_chrome"->⁐="◈(❒) ✚ ⁝(❒:▢ ≕="minim") ▸(❒)"
• ⌰:⬝:§="bar"->▱:◒⩲"bar"
• ⌰:⌗:§="radius"->▱:◒⩲"radius"
```

`⌰:"name"` is not a form. An abstract without a type used to be read as `⬝`
(item) silently, which is how a third of the file became unreadable to the
checker while the checker stayed green. If the type is missing, it is an error,
not a default.

### 12.2 `⁝` (add) versus `↪` (insert) - the part that was done wrong

They are not the same and the difference is load-bearing:

```
⁝(❒:▢)     the button is a CHILD of the view: new root
↪(❒:▢)    the button goes INTO an existing structure at a position
◈(❒)       the view is created
```

Writing `⁝` when you meant `↪` produces a structure that looks right and is not,
and nothing in the gate can see it. Pick by question: *does the parent exist
already?* no - `⁝`. yes - `↪`.

### 12.3 the alias: the escape from inventing words

A part of an interface that has no glyph is a **hole**, and a hole is not fixed
by writing a word. `menu`, `bar` and `chrome` have no glyph. Writing them as
words is what put them in a spec that then passed every check, because a word
can be invented and an invented word is indistinguishable from a real one.

The fix is `⌍` (alias): point an existing concept at the local name. The
concept keeps its glyph, the spec gets the name it wanted, and the base does not
grow a synonym.

```
• ⌰:⬝:§="bar"->⌍:▱:◒⩲"bar"
• ⌰:⬝:§="menu"->⌍:‣:◒⩲"menu"
• ⌰:⬝:§="chrome"->⌍:⬋:◒⩲"chrome"
```

`▱` (frm) is the frame, `‣` (list) is the list, `⬋` (row) is the row. The alias
says *in this spec, the part I call `bar` is the concept frame*. That is a claim
about this spec, which is exactly the scope of the problem, and it costs the
base nothing.

**So the rule is: never a new word. A local name is either a `§` id or a `⌍`
alias to a concept that already has a glyph.** If it is neither, it is a hole
and it stops the build.

### 12.4 the string: `""` is `❝` (quote) around `…` (string)

```
≕ ⩲ "build_chrome"     a name, quoted, and a name may hold any word
⁐ ⩲ "◈(❒) ✚ ▸(❒)"     an action, quoted, and the quotes protect it
⤴("okno svernuto")     a value, quoted
```

Three rules, and the third is the one that bites:

1. `""` protects its content from the compiler. Inside quotes, no word is
   translated, so a spec can carry a string that is not a spec.
2. `""` is where a word that is not a concept must NOT go. `≕ ⩲ "minimayz"`
   passes every word-layer check, because the checker reads the string, not its
   contents. This is the hole detector's job, and it is why the hole detector
   exists.
3. A quoted name is a **label**, not an identity. `≕ ⩲ "bar"` says how the thing
   is reached; `§ ⩲ "bar"` says what it is. Confusing the two is how `id` and
   `name` drifted apart in the first place.

### 12.5 what all four sections are for

The gate in this repository checks that a spec agrees with itself. It does not
check that the spec agrees with a task, and it did not check that the words in
it were words the base owns. So these rules exist to make the two mistakes that
survived the gate **impossible to write**:

```
invented word   ⤍ a ⤍   only § ids and ⌍ aliases, never a bare word
defaulted type  ⌰:§     type is mandatory, no silent ⬝
new name        ≕ ⩲     a label, and labels are checked for a concept behind them
```

### 12.6 the compiler's three rules

The addressing scheme exists so that a thing keeps the same name no matter who
writes it and no matter which letters it happens to be spelled with. It is the
opposite of a hard operator: an operator is evaluated, and an address is not.
Three rules, and they are the whole of it.

**1 - everything is lower case.**
Case is not carried. `And` and `and` are the same field, and if they were not,
the same word would have two addresses and the identity of a thing would depend
on who typed it.

**2 - a word is cut by the same system, three, three, tail.**
`3 3 tail`, where the tail is whatever is left and is NOT padded, because a
padded letter is a letter that is not in the word.

```
abandon    aba ndo n
building   bui ldi ng
we         we
```

Same system for every word. A different system per word would be a different
address per word, which is the thing this is not.

**3 - on divergence, add a syllable.**
When a piece has no address, do not substitute, do not round to the nearest,
do not skip. **Add the next syllable and cut again**, so the boundary moves and
a piece that has an address may appear. A missing piece is a fact about the
table, and the fix is to re-anchor, not to invent.

```
sixteen    six· teen        six has no address
           -> re-anchor on the syllable, cut again
```

The `·` is written where the address is absent. It is never replaced by a
neighbouring address, because a plausible wrong number is the one failure this
scheme cannot be caught by: a field is checked by looking up whether it exists,
and an invented one exists.

### 12.7 what the file is, and what it is not

```
the file holds   fields, numbers, separators
the file does not hold   where a word begins
```

Word boundaries are not in the file, and that is the division of layers, not a
loss. The file speaks about fields, and a field is what can be checked. A word
is built by whoever reads it, from the table, which is the only thing that can
turn a number into a letter.

The `●` separator is named in the base (`● разделитель`) so it can be looked up
like anything else. It is a boundary and not an operator: it asserts nothing,
and it is what lets the file be cut anywhere and read without a program.

