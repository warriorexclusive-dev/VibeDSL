
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
* it's is a logical programming language name VibeDSL syntax [node:node]->[node:par], -> delegate function or other node, node it's logical unit [uroot:rule]->[file:wrt]->{llm:lng = "VibeDSL"}, this example of rule 
* Logical abbreviations are permitted and even encouraged, provided the logic does not involve branching.
* It is important to maintain logical consistency among the elements; check yourself for a coherent chain of logic.
* example [node:child_node]
            ->a==b
              ->c=d 
* syntax of functions -> fun name="example" par="val1" -> logic. 
* [] - block of multiple logical objects, exxample [val1,val2,val3,...], ... applies only if there is a valid array reference and the array length exceeds 10 elements. 
* {} it,s marker of declaration a functionaly custom logic of element, it,s is custom specific functionaly logic of object 
* :, !:, |, ||, ->,<->,<-,==,=, <=, >=, <(src)-, -(id)>, <-(), ()->, logical way and construct operators 
* aliases: | = or, || = and (also &&), ! = not; / = division, \ = logic filter; <> = multi-way branching, NOT "not equal" (use !(a==b)) 
* "" way to сustomisation mapping all units, example: infr:->node type="panasonic ats" name ="telephony"
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
  prj name="picture_lib":
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
* FLOW MODEL: `fun` = executable function; `abstract` = pure concept (idea) - defines properties/behavior for a group or single of future entity, cannot create an instance of itself. Flow = input function -> executable function (Java-abstract analogy).
* ALIAS KWS: `alias [...] as NAME` (grammar word `as`).
* USERDEFS register: `abstract name="X"` and `alias [...] as NAME`; abstract body = `[abstract body]`, not re-validated. `{}` = AI custom block; `/* */` and `//` = human comments (skipped).
* `act="..."` declares a function - two canonical forms, written in VibeDSL:
  - `abstract "open_file" -> act="open file by name"` - declares function `open_file`; call: `open_file("main.txt")`
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
* and,&&,||    - logical AND
* or,|         - logical OR
* not,!        - logical NOT
* /            - mathematical division; \ - logic filter (exclusion by condition)
* if `component` is ambiguous in a script, use the unambiguous full word `component`; `compil` is always the compiling meaning.
* Sources stay in sync: the master dictionary lives in `DATA/dictionary_sorted_by_type.txt` (category split canon `DATA/action.dict`, `DATA/mapping.dict`, `DATA/operators.dict`, `DATA/abstracts.txt` generated by `validator/spellcheck.py`) and is served via RAG (`GET /API/get?dict=dictionary`); RULES.MD references it.



## 9. SYNTAX GUARD RULES
* validate: syntax in dictionary before emit
* validate: prototypes in logic tree before emit

## 10. BASE AGENT RULES 

fun type="rule" scop="root" -> event:crt([logic,arc:ref,spec,plan]) -> lng="VibeDSL"

fun type="rule" scop="root" -> event:answ(user) -> lng=usr:lang

fun type="rule" scop="root" -> event:crt([code, data, file])
  -> crt(spec lng="VibeDSL" proto):
  -> exam(spec:syn==VibeDSL:dict:syn)<>:
     -> exam(!(spec:logic==?))<>:
        -> show(spec lang="VibeDSL" src="orig" with(VibeDSL:prnt:strk:->add(ref lang=usr:lang))):
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
-> proto(any) is node act=[crt,exam] type=rule:
   -> lang: any reqr
      type: any reqr
      type==[dom,file]:
      -> name: any reqr

-> proto(if) id="if" act=[crt,exam]
   if(instr is single): 
   -> syn="obj~obj"
   else
   -> syn="instr(obj~obj)"

-> proto(goal) id="goal" act=[wrt,exam,crt]
   show(cxt)
   show(msg(goal))

-> proto(fail) id="fail" act=[wrt,exam,crt]
   show(err)
   if(act==[wrt,crt]){
      usr:apr:retry
   }   

-> proto(varn) id="varn5" type=rule scop=root
   show(varn:max(5)||req) ret=usr:sel:->

-> proto(retry) id="r5" type="rule" scop="root"
      for(var i=0;i<5;i=incr(1))<>:
      -> retry()
      -> show(llm->user req?)<>:
         -> retry()
         -> fail


-> proto(?) type="rule" scop="root" act=[wrt,exam,crt]
   show(varn:max(3)||req) ret=usr:sel1:->

fun type="rule" scop="root" -> use(VibeDSL:proto[if,goal,fail])
fun type="rule" scop="root" ->
   prompt:lng == "VibeDSL":
      prompt:run()

fun type="rule" scop="root" -> get(think:->show()){without conversion to user lang}
fun type="rule" scop="root" -> usr:lang="RU:ru"   



## 11. INSIDE OPEN AI RULE 
* Rule config file location "~USER_DIR~\.config\opencode\AGENTS.md"
