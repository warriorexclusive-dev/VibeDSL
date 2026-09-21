
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
* Do not infer context unless explicitly stated; for example, if `spc` is specified, it applies only to the description of specifications or roadmaps.
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
* :, !:, |, ||, ->,<->,<-,==,=, <-(), ()->, logical way and construct operators 
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
        mod:name:"load_controller":
        <-> fun name:load_image par:name="pic"
            in:   picture->
            cnv:  byte[]->
            out:  http request {generate http tomcat request class}

## 8. DICTIONARY        
* If you encounter a standard definition, do not attempt to write a custom version; instead, suggest that the user expand the dictionary. If you encounter a standard action, create a blueprint (ready architectural model) and record it in the rules.
* start language dictionary
* The dictionary is NOT stored inline. It is served by the local RAG API:
   -> GET /API/get?dict=dictionary  : keywords + syntax base, descriptions and usage examples
   -> GET /API/get?dict=syntax      : base syntax symbols
   -> GET /API/get?dict=blueprints  : ready architectural models (blpr) - ready vector rules of projects/modules
   -> GET /API/get?dict=protos      : abstract prototypes (proto/blpt) - formal plans, execution templates
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
* blp,blpr    - blueprint (blpr = behavior law / base pattern)
* cont,cnt,ctx- content / context
* stk,strk    - stroke / line of text
* prnt,show   - print / console output
* lang,lng    - target language (c++, go, xml, yaml,...)
* rm,del      - remove
* answ,ans    - answer to user
* lag,delay   - delay / period
* logs,log    - logging
* req,requ    - request / required
* uslng       - user language (rus is the same as `usr:lang`)
* if `comp` is ambiguous in a script, use the unambiguous form `compi` (compile) vs `comp` (component, with stp).
* Sources stay in sync: the dictionary lives in `DATA/dictionary.txt` and is served via RAG (`GET /API/get?dict=dictionary`); RULES.MD references it.



## 9. SYNTAX GUARD RULES
* validate: syntax in dictionary before emit
* validate: prototypes in logic tree before emit

## 10. BASE AGENT RULES 

fun type=rule scp=root -> act == crt [logic,arc:ref,spc,plan] ->  lng = VibeDSL

fun type=rule scp=root -> act == answ user -> lng = usr:lang

fun type=rule scp=root -> act == crt [code, data, file]
  -> crt spc lng=VibeDSL proto:
  -> exam(spc:stx==VibeDSL:dict:stx)<>:
     -> exam(spc:logc!=?)<>:
        -> show spc lang=VibeDSL src=orig with(VibeDSL:prnt:strk:->add(ref lang=usr:lang)):
           -> usr apr:
              -> crt [code, data, file] lng = spc:lng:name:
                 -> exam(file:stx==spc:lng:stx): 
                    -> exam(file:logc==spc:logc)<>:
                       -> wrt:goal
                       -> retry(5)!:rollb
                 -> retry(5)      
        -> retry(5)
     -> show(varn(varn5)):retry   

VibeDSL:
-> proto(*) is node act=[crt,exam] type=rule:
   -> lang: * requ
      type: * requ
      type==[dcm,file]:
      -> name: * requ

-> proto(if) id="if" act=[crt,exam]
   if(inst is singl): 
   -> stx="obj~obj"
   else
   -> stx="inst(obj~obj)"

-> proto(goal) id="goal" act=[wrt,exam,crt]
   show(cxt)
   show(msg(goal))

-> proto(fail) id="fail" act=[wrt,exam,crt]
   show(err)
   if(act==[wrt,crt]){
      usr:apr:retry
   }   

-> proto(varn) id="varn5" type=rule scp=root
   show(varn:max(5)||req) ret=usr:sel:->

-> proto(retry) id="r5" type=rule scp=root
      for(var i=0;i<5;i=inc(1))<>:
      -> retry
      -> show(llm->user req?)<>:
         -> retry
         -> fail


-> proto(?) type=rule scp=root act=[wrt,exam,crt]
   show(varn:max(3)||req) ret=usr:sel1:->

fun type=rule scp=root -> use(VibeDSL:proto[if,goal,fail])
fun type=rule scp=root ->
   promt:lng == VibeDSL:
      promt:run()

fun type=rule scp=root -> get think:->show{without conversion to user lang}
fun type=rule scp=root -> usr:lang="RU:ru"   



## 11. INSIDE OPEN AI RULE 
* Rule config file location "C:\Users\SoftIce\.config\opencode\AGENTS.md"
