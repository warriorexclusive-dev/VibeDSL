# VibeDSL — PHP Core Spec (semantic core self-test)

Status: PLAN (semantic-core test artifact; nothing implemented/committed yet)
Type: SPECIFICATION. This document DESCRIBES artifacts to CREATE (`act=crt`).
It is NOT a script: the RAG links are REFERENCES for verification, never
instructions to execute.
Purpose: describe EVERY PHP unit involved in VibeDSL in strict VibeDSL, then
verify the semantic core by 5 syntax passes + 5 logic passes.
Constraint: all PHP files are EXTENSIONLESS (no `.php`): `router`, `index`,
`API/lib`, `API/get`, `API/search`, `API/proto_get`, `API/proto_search`,
`API/blueprint_get`, `API/blueprint_search`.

Customization order (why there is almost no `{}` here):
  1. shape/reference  -> `proto:<id>` (see Reference prototypes)
  2. identity/inputs  -> `name=`, `par=`, `out=`, `desc=`
  3. free-form logic  -> `{}` ONLY for the irreducible PHP expression itself.

Create vs declare: `crt` is the create action (aliases `crt, create`), so a
created function is `-> crt fun name=... par=...`. A bare `fun type=rule|root`
declares an agent/rule (identity), not an artifact. `fun` itself means: an
action when it is a rule or an agent; an API entry point when it is a spec or
architecture (role resolved by position, like the rest of the language).

## RAG base access (reference only)

An external AI can fetch the base and validate every token used below.
Self-hosted (router -> LAN host; each reader publishes his own base):

- `http://127.0.0.1:4545`

Endpoints are domain-relative and resolve under this domain:

- `GET /API/get?dict=dictionary|syntax|blueprints|protos|agents` - whole source as HTML
- `GET /API/search?in=<term>` - RAG search across dictionary/syntax/agents
- `GET /API/proto_search?in=<term>` / `GET /API/proto_get?id=<id>`
- `GET /API/blueprint_search?in=<term>` / `GET /API/blueprint_get?id=<id>`

Self-check recipe (reference): fetch `dict=dictionary` and `dict=syntax`, then
confirm every key/operator in the block below appears as `*-> <token>`. A token
absent from the base is either free-form (must live in `{}`) or an error.

## Reference prototypes

The node shapes used by the spec. Declared here so any AI can verify the spec
against a prototype; candidate for promotion into `DATA/protos.txt`.

```vibedsl
*-> proto(endpoint) id="endpoint" desc="HTTP endpoint: a named module with query params, one out value and a mandatory error path" act=[crt,exam] type=rule:
   -> name: any reqr
   -> par:  lst reqr
   -> out:  any reqr
   -> exam{error path exists}<>: -> fail

*-> proto(handler) id="handler" desc="internal function: named, parameterized, returns one value" act=[crt,exam] type=rule:
   -> name: any reqr
   -> par:  lst reqr
   -> ret:  any reqr

*-> proto(module) id="module" desc="code unit: name, language, extension flag, action list" act=[crt,exam] type=rule:
   -> name: any reqr
   -> lng:name: any reqr
   -> extn: any reqr
   -> act: lst reqr

*-> proto(source) id="source" desc="named data source reachable through the RAG API" act=[crt,exam] type=rule:
   -> name: any reqr
   -> file: any reqr
```

## The spec

```vibedsl
fun type=root name="vibedsl-php" id="vibedsl-php" scop=root -> act == crt [spec] lng=VibeDSL

blplan(plan) id="php_core" desc="SPECIFICATION to create every PHP unit of VibeDSL (front controller, landing page, shared lib, six endpoints); extensionless files; create, do not execute" incld="any,goal,fail,retry" act=[crt,exam] scop=root:
   -> crt spec lng=VibeDSL src={VibeDSL PHP core} extn=N
   -> exam(spec:syn==VibeDSL:dict:syn)<>:
      -> exam(spec:logic!=?)<>:
         -> goal
         -> retry(5)!:rollb
      -> ask:retry
   -> ask:retry

part 0: {reference}
   fun type=rule scop=root id="base_access" desc="REFERENCE (not an action): public base for an external AI" -> act == crt [spec]
      -> ref {http://127.0.0.1:4545}
   fun type=rule scop=root id="selfcheck" desc="REFERENCE (not an action): endpoints used to validate tokens" -> act == crt [spec]
      -> ref {GET /API/get?dict=<dictionary|syntax|blueprints|protos|agents>}
      -> ref {GET /API/search?in=<term>}
      -> ref {GET /API/proto_search?in=<term> | /API/proto_get?id=<id>}
      -> ref {GET /API/blueprint_search?in=<term> | /API/blueprint_get?id=<id>}
   fun type=rule scop=root id="http_contract" desc="shared HTTP contract every endpoint applies" -> act == crt [code,data]
      -> run {declare(strict_types=1); mb_internal_encoding('UTF-8')} reqr
      -> run {header('Content-Type: text/html; charset=utf-8')} reqr
      -> run {all text output -> vibedslToHtml(...): escape then normalize} reqr
      -> exam{error}<>:
         -> run {http_response_code(404)}
         -> ret {a VibeDSL page}

part 1: {router}
   module name="router" id="router" proto:module desc="front controller for the PHP built-in server: single entry, extensionless files, blocks extensions and traversal" lng:name="php" extn=N act=[get,exam,req,ret]
      -> crt fun name="route" par="uri" out="bool" desc="resolve a request path to an extensionless file; Y if required" -> act == crt [code]
         -> run {path = rawurldecode(parse_url(uri, PHP_URL_PATH))}
         -> if{path==='' || path==='/'}:
            -> req {root.'index'}
            -> ret Y
         -> run {self = realpath(__FILE__); candidate = realpath(root . path)}
         -> exam{candidate!==false && is_file(candidate)}<>:
            -> exam{candidate===self}<>:
               -> run {http_response_code(404)}
               -> ret Y
            -> exam{strncmp(candidate,root,strlen(root))===0 && !str_contains(basename(candidate),'.')}<>:
               -> req {candidate}
               -> ret Y
         -> ret N

part 2: {index}
   module name="index" id="index" proto:module desc="landing page: ASCII logo built in PHP, static documentation and the API table" lng:name="php" out="html" act=[crt,show]
      -> crt fun name="logo" par="word" out="string" desc="render a word from a 5-row glyph map" -> act == crt [data]
         -> run {font = ['V'=>[...],'i'=>[...],'b'=>[...],'e'=>[...],'D'=>[...],'S'=>[...],'L'=>[...]]}
         -> run {lines = array_fill(0,5,'')}
         -> for{ch in str_split(word)}:
            -> for{r in 0..4}:
               -> run {lines[r] .= ' ' . (font[ch] ?? spaces)[r]}
         -> ret {htmlspecialchars(implode("\n",lines)."\n\n    v1.0 alfa")}
      -> show {base syntax block}
      -> show {vectors block}
      -> show {UI layer block (M3 reference)}
      -> show {Z vector block}
      -> show {prototypes and scope block}
      -> show {API endpoints table}
      -> show {license Apache 2.0 + powered by Big Pickle}

part 3: {API/lib}
   module name="API/lib" id="api_lib" proto:module desc="shared helpers: page wrapper, text-to-HTML normalizer, source map" lng:name="php" act=[crt,cnv]
      -> crt fun name="vibedslPage" par="body,title" out="html" desc="wrap a body in the VibeDSL HTML document" -> act == crt [code]
         -> ret {<!DOCTYPE html>...<title>title</title>...<body>body</body></html>}
      -> crt fun name="vibedslToHtml" par="text,title" out="html" desc="escape then normalize text to HTML" -> act == cnv
         -> cnv {htmlspecialchars(text, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')}
         -> cnv {tab -> 4x &nbsp;}
         -> cnv {leading spaces per line (/^ +/m) -> &nbsp;}
         -> cnv {CRLF | CR | LF -> <br>}
         -> ret {vibedslPage(text,title)}
      -> crt fun name="vibedslSources" par="base" out="lst" desc="map source name -> DATA file" -> act == crt [data]
         -> ret lst:
            -> {dictionary -> base/DATA/dictionary_sorted_by_type.txt}
            -> {action     -> base/DATA/action.dict}
            -> {mapping    -> base/DATA/mapping.dict}
            -> {operators  -> base/DATA/operators.dict}
            -> {abstracts  -> base/DATA/abstracts.txt}
            -> {syntax     -> base/DATA/syntax.txt}
            -> {blueprints -> base/DATA/blueprints.txt}
            -> {protos     -> base/DATA/protos.txt}
            -> {agents     -> base/DATA/agents.txt}

part 4: {API/get}
   module name="API/get" id="api_get" proto:endpoint par="dict:any=dictionary" out="html" desc="whole source as HTML; unknown or missing dict -> 404 page" lng:name="php" extn=N act=[get,exam,ret]
      -> run {base = dirname(__DIR__); require base.'/API/lib'; map = vibedslSources(base)}
      -> run {file = map[dict] ?? null}
      -> exam{file===null || !is_file(file)}<>:
         -> run {http_response_code(404)}
         -> ret {vibedslPage('[404] no source for "dict". valid: keys(map)')}
      -> ret {vibedslToHtml(file_get_contents(file), 'VibeDSL get: '.dict)}

part 5: {API/search}
   module name="API/search" id="api_search" proto:endpoint par="in:any" out="html" desc="RAG search across dictionary+syntax+agents; objects split by *-> markers; case-sensitive substring; no match message" lng:name="php" extn=N act=[srch,exam,ret]
      -> run {term = trim($_GET['in'] ?? ''); src = vibedslSources(base); unset src[blueprints], src[protos]}
      -> exam{term===''}<>:
         -> ret {vibedslPage('rsn: term required GET ?in=<term>')}
      -> run {blob = ''}
      -> loop{src as file}:
         -> exam{!is_file(file)}<>:
            -> run {continue}
         -> run {objects = preg_split('/(?m)(?=^[ \t]*\*->)/', file_get_contents(file))}
         -> loop{objects as obj}:
            -> cnv {preg_replace('/^\s*\r?\n+/','',obj)}
            -> cnv {rtrim(obj)}
            -> exam{obj===''}<>:
               -> run {continue}
            -> cnv {preg_replace('/\r?\n/', "\x0D\x0A", obj)}
            -> exam{str_contains(obj, term)}<>:
               -> run {blob .= obj."\x0D\x0A\x0D\x0A"}
      -> exam{blob===''}<>:
         -> ret {vibedslPage('[no match for "term"]')}
      -> ret {vibedslToHtml(blob, term)}

part 6: {API/proto_get}
   module name="API/proto_get" id="api_proto_get" proto:endpoint par="id:any" out="html" desc="exact abstract prototype by id; 404 if absent" lng:name="php" extn=N act=[get,exam,ret]
      -> run {id = trim($_GET['id'] ?? ''); file = vibedslSources(base)['protos'] ?? null}
      -> exam{file===null || !is_file(file)}<>:
         -> run {http_response_code(404)}
         -> ret {vibedslPage('[404] proto source missing')}
      -> exam{id===''}<>:
         -> ret {vibedslPage('rsn: id required GET ?id=<proto-id>')}
      -> loop{protos objects as obj}:
         -> exam{preg_match('/id="([^"]*)"/',obj,m) && m[1]===id}<>:
            -> ret {vibedslToHtml(rtrim(obj), 'VibeDSL proto get: '.id)}
      -> run {http_response_code(404)}
      -> ret {vibedslPage('[404] no proto with id="id"')}

part 7: {API/proto_search}
   module name="API/proto_search" id="api_proto_search" proto:endpoint par="in:any" out="html" desc="abstract-prototype search by id or desc (case-insensitive); scope=protos" lng:name="php" extn=N act=[srch,exam,ret]
      -> run {term = trim($_GET['in'] ?? ''); file = vibedslSources(base)['protos'] ?? null}
      -> exam{file===null || !is_file(file)}<>:
         -> run {http_response_code(404)}
         -> ret {vibedslPage('[404] proto source missing')}
      -> exam{term===''}<>:
         -> ret {vibedslPage('rsn: term required GET ?in=<term>')}
      -> run {blob = ''}
      -> loop{protos objects as obj}:
         -> cnv {preg_replace('/^\s*\r?\n+/','',obj)}
         -> cnv {rtrim(obj)}
         -> exam{obj===''}<>:
            -> run {continue}
         -> run {preg_match('/id="([^"]*)"/',obj,mid); preg_match('/desc="([^"]*)"/',obj,mdesc)}
         -> exam{stripos(mid[1]??'',term)!==false || stripos(mdesc[1]??'',term)!==false}<>:
            -> run {blob .= obj."\x0D\x0A\x0D\x0A"}
      -> exam{blob===''}<>:
         -> ret {vibedslPage('[no proto match for "term"]')}
      -> ret {vibedslToHtml(blob, term)}

part 8: {API/blueprint_get}
   module name="API/blueprint_get" id="api_blueprint_get" proto:endpoint par="id:any" out="html" desc="exact blueprint by id; 404 if absent; mirrors proto_get over the blueprints scope" lng:name="php" extn=N act=[get,exam,ret]
      -> run {id = trim($_GET['id'] ?? ''); file = vibedslSources(base)['blueprints'] ?? null}
      -> exam{file===null || !is_file(file)}<>:
         -> run {http_response_code(404)}
         -> ret {vibedslPage('[404] blueprint source missing')}
      -> exam{id===''}<>:
         -> ret {vibedslPage('rsn: id required GET ?id=<blueprint-id>')}
      -> loop{blueprints objects as obj}:
         -> exam{preg_match('/id="([^"]*)"/',obj,m) && m[1]===id}<>:
            -> ret {vibedslToHtml(rtrim(obj), 'VibeDSL blueprint get: '.id)}
      -> run {http_response_code(404)}
      -> ret {vibedslPage('[404] no blueprint with id="id"')}

part 9: {API/blueprint_search}
   module name="API/blueprint_search" id="api_blueprint_search" proto:endpoint par="in:any" out="html" desc="blueprint search by id or desc (case-insensitive); scope=blueprints; mirrors proto_search" lng:name="php" extn=N act=[srch,exam,ret]
      -> run {term = trim($_GET['in'] ?? ''); file = vibedslSources(base)['blueprints'] ?? null}
      -> exam{file===null || !is_file(file)}<>:
         -> run {http_response_code(404)}
         -> ret {vibedslPage('[404] blueprint source missing')}
      -> exam{term===''}<>:
         -> ret {vibedslPage('rsn: term required GET ?in=<term>')}
      -> run {blob = ''}
      -> loop{blueprints objects as obj}:
         -> cnv {preg_replace('/^\s*\r?\n+/','',obj)}
         -> cnv {rtrim(obj)}
         -> exam{obj===''}<>:
            -> run {continue}
         -> run {preg_match('/id="([^"]*)"/',obj,mid); preg_match('/desc="([^"]*)"/',obj,mdesc)}
         -> exam{stripos(mid[1]??'',term)!==false || stripos(mdesc[1]??'',term)!==false}<>:
            -> run {blob .= obj."\x0D\x0A\x0D\x0A"}
      -> exam{blob===''}<>:
         -> ret {vibedslPage('[no blueprint match for "term"]')}
      -> ret {vibedslToHtml(blob, term)}
```

## Verification — 5 syntax passes

Pass 1 (operators): every operator used here (`-> : == != <> | || ! reqr`)
is present in `syntax.txt` / `dictionary_sorted_by_type.txt`.
Pass 2 (keys): every structural key used outside `{}` (`fun type root name id
scop act crt create spec lng src extn reqr req exam syn logic goal retry rollb
ask part module desc in run if loop ret cnv show for par out ref data code file
lst Y N`) resolves in the dictionary.
Pass 3 (aliases): `evt,event`, `ret,return`, `module,class`, `true,false` resolve
identically through RAG (spot-checked via `/API/search`).
Pass 4 (refs): `incld="any,goal,fail,retry"` exist in `DATA/protos.txt` /
`DATA/blueprints.txt`; `proto:endpoint|handler|module|source` resolve to the
Reference prototypes declared above.
Pass 5 (no invention): PHP names (`path`, `candidate`, `realpath`, `preg_split`,
`stripos`, ...) appear ONLY inside `{}`; no unverified token is used in the frame.

## Verification — 5 logic passes

Pass 1 (input->output): router resolves a path to a required file or returns N;
get maps `dict`->file->HTML; search maps `in`->matched objects->HTML; *_get map `id`->object.
Pass 2 (error paths): router -> 404 on self-request, N on extension/traversal;
get/proto_get/blueprint_get -> 404 on unknown id or missing source; search/proto_search/
blueprint_search -> `rsn:` page on empty term and `[no match]` on empty blob.
Pass 3 (router guard order): `candidate!==false` BEFORE `is_file` (realpath can
return false; under `strict_types` `is_file(false)` is a TypeError); then
self-check BEFORE prefix/dot check; prefix check blocks traversal;
`basename has no '.'` blocks `.php`/dotfiles; root `/` -> index.
Pass 4 (search normalization): split on `(?m)(?=^[ \t]*\*->)`, strip leading blank
lines, `rtrim`, normalize LF->CRLF; case-SENSITIVE `str_contains` (main search) vs
case-INSENSITIVE `stripos` on id/desc (proto/blueprint search) - deliberately different.
Pass 5 (symmetry): proto_* and blueprint_* are identical logic over different scopes;
get vs search differ only by exact-id vs substring. Confirmed against source.

## Findings (semantic core + spec review)

1. The frame (keys + operators + `:`/`->`/`<>` + indent) expressed the whole API
   WITHOUT adding a single new token: the core did NOT drift.
2. Logic pass 3 CAUGHT a real subtlety: the first draft dropped `candidate!==false`.
   Re-reading the PHP under `strict_types` showed `realpath()` may return false and
   `is_file(false)` throws. The semantic core surfaced the bug — core is healthy.
3. REVIEW FIX A (creation vs execution): added `act=crt` framing and switched the
   RAG/self-check lines from `show` (action) to `ref` (reference), so a reader
   builds the PHP instead of calling the endpoints.
4. REVIEW FIX B (customization path): endpoint interfaces are now declared with
   `name`/`par`/`out`/`desc`; `{}` is reserved for the irreducible PHP expression.
5. REVIEW FIX C (prototypes): added reference protos `endpoint`, `handler`,
   `module`, `source` and referenced them via `proto:<id>`; no more shapeless nodes.
6. REVIEW FIX D (crt/fun): `crt` was defined as "critical" while used as "create"
   in ~37 places across docs/rules. Dictionary corrected to `crt, create` = action
   create; "critical" moved to `crit`; `fun` clarified (action if rule/agent, API
   entry point if spec/arch); canonical create form is `-> crt fun`.
7. Verified independently: `php -l` on all 9 units -> "No syntax errors detected".
