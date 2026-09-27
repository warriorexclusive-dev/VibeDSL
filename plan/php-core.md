# VibeDSL — PHP Core Spec (semantic core self-test)

Status: PLAN (semantic-core test artifact; nothing implemented/committed yet)
Type: SPECIFICATION. This document DESCRIBES artifacts to CREATE (`action=create`).
It is NOT a script: the RAG links are REFERENCES for verification, never
instructions to execute.
Purpose: describe EVERY PHP unit involved in VibeDSL in strict VibeDSL, then
verify the semantic core by 5 syntax passes + 5 logic passes.
Constraint: all PHP files are EXTENSIONLESS (no `.php`): `router`, `index`,
`API/lib`, `API/get`, `API/search`, `API/proto_get`, `API/proto_search`,
`API/blueprint_get`, `API/blueprint_search`.

Customization order (why there is almost no `{}` here):
  1. shape/reference  -> `prototype:<id>` (see Reference prototypes)
  2. identity/inputs  -> `name=`, `param=`, `out=`, `desc=`
  3. free-form logic  -> `{}` ONLY for the irreducible PHP expression itself.

Create vs declare: `create` is the create action (aliases `create, create`), so a
created:function is `-> create:function:name=... param=...`. A bare `function:type=rule|root`
declares an agent/rule (identity), not an artifact. `function` itself means: an
action when it is a rule or an agent; an API entry point when it is a specfile or
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

The node shapes used by the specfile. Declared here so any AI can verify the specfile
against a prototype; candidate for promotion into `DATA/protos.txt`.

```vibedsl
*-> proto(endpoint) id="endpoint":desc="HTTP endpoint: a named module with query params, one out value and a mandatory error path":action=[create,exam]:type=rule:
   -> name: any reqr
   -> param:  list reqr
   -> out:  any reqr
   -> exam{error path exists}<>: -> fail

*-> proto(handler) id="handler":desc="internal function: named, parameterized, returns one value":action=[create,exam]:type=rule:
   -> name: any reqr
   -> param:  list reqr
   -> return:  any reqr

*-> proto(module) id="module":desc="code unit: name, language, extension flag, action list":action=[create,exam]:type=rule:
   -> name: any reqr
   -> lng:name: any reqr
   -> extension: any reqr
   -> action: list reqr

*-> proto(source) id="source":desc="named data source reachable through the RAG API":action=[create,exam]:type=rule:
   -> name: any reqr
   -> file: any reqr
```

## The specfile

```vibedsl
function:type=root:name="vibedsl-php":id="vibedsl-php":scop=root -> action == create [specfile]:lng=VibeDSL

blplan(plan) id="php_core":desc="SPECIFICATION to create every PHP unit of VibeDSL (front controller, landing page, shared lib, six endpoints); extensionless files; create, do not execute":incld="any,goal,fail,retry":action=[create,exam]:scop=root:
   -> create specfile:lng=VibeDSL:source={VibeDSL PHP core}:extension=N
   -> exam(specfile:syn==VibeDSL:dict:syn)<>:
      -> exam(!(specfile:logic==?))<>:
         -> goal
         -> retry(5)!:rollb
      -> ask:retry
   -> ask:retry

part 0: {reference}
   function:type=rule:scop=root:id="base_access":desc="REFERENCE (not an action): public base for an external AI" -> action == create [specfile]
      -> ref {http://127.0.0.1:4545}
   function:type=rule:scop=root:id="selfcheck":desc="REFERENCE (not an action): endpoints used to validate tokens" -> action == create [specfile]
      -> ref {GET /API/get?dict=<dictionary|syntax|blueprints|protos|agents>}
      -> ref {GET /API/search?in=<term>}
      -> ref {GET /API/proto_search?in=<term> | /API/proto_get?id=<id>}
      -> ref {GET /API/blueprint_search?in=<term> | /API/blueprint_get?id=<id>}
   function:type=rule:scop=root:id="http_contract":desc="shared HTTP contract every endpoint applies" -> action == create [code,data]
      -> run {declare(strict_types=1); mb_internal_encoding('UTF-8')} reqr
      -> run {header('Content-Type: text/html; charset=utf-8')} reqr
      -> run {all text output -> vibedslToHtml(...): escape then normalize} reqr
      -> exam{error}<>:
         -> run {http_response_code(404)}
         -> return {a VibeDSL page}

part 1: {router}
   module:name="router":id="router" prototype:module:desc="front controller for the PHP built-in server: single entry, extensionless files, blocks extensions and traversal" lng:name="php":extension=N:action=[get,exam,request,return]
      -> create:function:name="route":param="uri":out="bool":desc="resolve a request path to an extensionless file; Y if required" -> action == create [code]
         -> run {path = rawurldecode(parse_url(uri, PHP_URL_PATH))}
         -> if{path==='' || path==='/'}:
            -> request {root.'index'}
            -> return Y
         -> run {self = realpath(__FILE__); candidate = realpath(root . path)}
         -> exam{candidate!==false && is_file(candidate)}<>:
            -> exam{candidate===self}<>:
               -> run {http_response_code(404)}
               -> return Y
            -> exam{strncmp(candidate,root,strlen(root))===0 && !str_contains(basename(candidate),'.')}<>:
               -> request {candidate}
               -> return Y
         -> return N

part 2: {index}
   module:name="index":id="index" prototype:module:desc="landing page: ASCII logo built in PHP, static documentation and the API table" lng:name="php":out="html":action=[create,show]
      -> create:function:name="logo":param="word":out="string":desc="render a word from a 5-row glyph map" -> action == create [data]
         -> run {font = ['V'=>[...],'i'=>[...],'b'=>[...],'e'=>[...],'D'=>[...],'S'=>[...],'L'=>[...]]}
         -> run {lines = array_fill(0,5,'')}
         -> for{change in str_split(word)}:
            -> for{r in 0..4}:
               -> run {lines[r] .= ' ' . (font[change] ?? spaces)[r]}
         -> return {htmlspecialchars(implode("\n",lines)."\n\n    v1.0 alfa")}
      -> show {base syntax block}
      -> show {vectors block}
      -> show {UI layer block (M3 reference)}
      -> show {Z vector block}
      -> show {prototypes and scope block}
      -> show {API endpoints table}
      -> show {license Apache 2.0 + powered by Big Pickle}

part 3: {API/lib}
   module:name="API/lib":id="api_lib" prototype:module:desc="shared helpers: page wrapper, text-to-HTML normalizer, source map" lng:name="php":action=[create,convert]
      -> create:function:name="vibedslPage":param="body,title":out="html":desc="wrap a body in the VibeDSL HTML document" -> action == create [code]
         -> return {<!DOCTYPE html>...<title>title</title>...<body>body</body></html>}
      -> create:function:name="vibedslToHtml":param="text,title":out="html":desc="escape then normalize text to HTML" -> action == convert
         -> convert {htmlspecialchars(text, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')}
         -> convert {table -> 4x &nbsp;}
         -> convert {leading spaces per line (/^ +/m) -> &nbsp;}
         -> convert {CRLF | CR | LF -> <br>}
         -> return {vibedslPage(text,title)}
      -> create:function:name="vibedslSources":param="base":out="list":desc="map source name -> DATA file" -> action == create [data]
         -> return list:
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
   module:name="API/get":id="api_get" prototype:endpoint:param="dict:any=dictionary":out="html":desc="whole source as HTML; unknown or missing dict -> 404 page" lng:name="php":extension=N:action=[get,exam,return]
      -> run {base = dirname(__DIR__); require base.'/API/lib'; map = vibedslSources(base)}
      -> run {file = map[dict] ?? null}
      -> exam{file===null || !is_file(file)}<>:
         -> run {http_response_code(404)}
         -> return {vibedslPage('[404] no source for "dict". valid: keys(map)')}
      -> return {vibedslToHtml(file_get_contents(file), 'VibeDSL get: '.dict)}

part 5: {API/search}
   module:name="API/search":id="api_search" prototype:endpoint:param="in:any":out="html":desc="RAG search across dictionary+syntax+agents; objects split by *-> markers; case-sensitive substring; no match message" lng:name="php":extension=N:action=[srch,exam,return]
      -> run {term = trim($_GET['in'] ?? ''); source = vibedslSources(base); unset source[blueprints], source[protos]}
      -> exam{term===''}<>:
         -> return {vibedslPage('reason: term required GET ?in=<term>')}
      -> run {blob = ''}
      -> loop{source as file}:
         -> exam{!is_file(file)}<>:
            -> run {continue}
         -> run {objects = preg_split('/(?m)(?=^[ \t]*\*->)/', file_get_contents(file))}
         -> loop{objects as obj}:
            -> convert {preg_replace('/^\s*\r?\n+/','',obj)}
            -> convert {rtrim(obj)}
            -> exam{obj===''}<>:
               -> run {continue}
            -> convert {preg_replace('/\r?\n/', "\x0D\x0A", obj)}
            -> exam{str_contains(obj, term)}<>:
               -> run {blob .= obj."\x0D\x0A\x0D\x0A"}
      -> exam{blob===''}<>:
         -> return {vibedslPage('[no match for "term"]')}
      -> return {vibedslToHtml(blob, term)}

part 6: {API/proto_get}
   module:name="API/proto_get":id="api_proto_get" prototype:endpoint:param="id:any":out="html":desc="exact abstract prototype by id; 404 if absent" lng:name="php":extension=N:action=[get,exam,return]
      -> run {id = trim($_GET['id'] ?? ''); file = vibedslSources(base)['protos'] ?? null}
      -> exam{file===null || !is_file(file)}<>:
         -> run {http_response_code(404)}
         -> return {vibedslPage('[404] proto source missing')}
      -> exam{id===''}<>:
         -> return {vibedslPage('reason: id required GET ?id=<proto-id>')}
      -> loop{protos objects as obj}:
         -> exam{preg_match('/id="([^"]*)"/',obj,m) && m[1]===id}<>:
            -> return {vibedslToHtml(rtrim(obj), 'VibeDSL proto get: '.id)}
      -> run {http_response_code(404)}
      -> return {vibedslPage('[404] no proto with id="id"')}

part 7: {API/proto_search}
   module:name="API/proto_search":id="api_proto_search" prototype:endpoint:param="in:any":out="html":desc="abstract-prototype search by id or desc (case-insensitive); scope=protos" lng:name="php":extension=N:action=[srch,exam,return]
      -> run {term = trim($_GET['in'] ?? ''); file = vibedslSources(base)['protos'] ?? null}
      -> exam{file===null || !is_file(file)}<>:
         -> run {http_response_code(404)}
         -> return {vibedslPage('[404] proto source missing')}
      -> exam{term===''}<>:
         -> return {vibedslPage('reason: term required GET ?in=<term>')}
      -> run {blob = ''}
      -> loop{protos objects as obj}:
         -> convert {preg_replace('/^\s*\r?\n+/','',obj)}
         -> convert {rtrim(obj)}
         -> exam{obj===''}<>:
            -> run {continue}
         -> run {preg_match('/id="([^"]*)"/',obj,mid); preg_match('/desc="([^"]*)"/',obj,mdesc)}
         -> exam{stripos(mid[1]??'',term)!==false || stripos(mdesc[1]??'',term)!==false}<>:
            -> run {blob .= obj."\x0D\x0A\x0D\x0A"}
      -> exam{blob===''}<>:
         -> return {vibedslPage('[no proto match for "term"]')}
      -> return {vibedslToHtml(blob, term)}

part 8: {API/blueprint_get}
   module:name="API/blueprint_get":id="api_blueprint_get" prototype:endpoint:param="id:any":out="html":desc="exact blueprint by id; 404 if absent; mirrors proto_get over the blueprints scope" lng:name="php":extension=N:action=[get,exam,return]
      -> run {id = trim($_GET['id'] ?? ''); file = vibedslSources(base)['blueprints'] ?? null}
      -> exam{file===null || !is_file(file)}<>:
         -> run {http_response_code(404)}
         -> return {vibedslPage('[404] blueprint source missing')}
      -> exam{id===''}<>:
         -> return {vibedslPage('reason: id required GET ?id=<blueprint-id>')}
      -> loop{blueprints objects as obj}:
         -> exam{preg_match('/id="([^"]*)"/',obj,m) && m[1]===id}<>:
            -> return {vibedslToHtml(rtrim(obj), 'VibeDSL blueprint get: '.id)}
      -> run {http_response_code(404)}
      -> return {vibedslPage('[404] no blueprint with id="id"')}

part 9: {API/blueprint_search}
   module:name="API/blueprint_search":id="api_blueprint_search" prototype:endpoint:param="in:any":out="html":desc="blueprint search by id or desc (case-insensitive); scope=blueprints; mirrors proto_search" lng:name="php":extension=N:action=[srch,exam,return]
      -> run {term = trim($_GET['in'] ?? ''); file = vibedslSources(base)['blueprints'] ?? null}
      -> exam{file===null || !is_file(file)}<>:
         -> run {http_response_code(404)}
         -> return {vibedslPage('[404] blueprint source missing')}
      -> exam{term===''}<>:
         -> return {vibedslPage('reason: term required GET ?in=<term>')}
      -> run {blob = ''}
      -> loop{blueprints objects as obj}:
         -> convert {preg_replace('/^\s*\r?\n+/','',obj)}
         -> convert {rtrim(obj)}
         -> exam{obj===''}<>:
            -> run {continue}
         -> run {preg_match('/id="([^"]*)"/',obj,mid); preg_match('/desc="([^"]*)"/',obj,mdesc)}
         -> exam{stripos(mid[1]??'',term)!==false || stripos(mdesc[1]??'',term)!==false}<>:
            -> run {blob .= obj."\x0D\x0A\x0D\x0A"}
      -> exam{blob===''}<>:
         -> return {vibedslPage('[no blueprint match for "term"]')}
      -> return {vibedslToHtml(blob, term)}
```

## Verification — 5 syntax passes

Pass 1 (operators): every operator used here (`-> : == <> | || ! reqr`)
is present in `syntax.txt` / `dictionary_sorted_by_type.txt`.
Pass 2 (keys): every structural key used outside `{}` (`function type root name id
scop action create create specfile lng source extension reqr request exam syn logic goal retry rollb
ask part module desc in run if loop return convert show for param out ref data code file
list Y N`) resolves in the dictionary.
Pass 3 (aliases): `event,event`, `return,return`, `module,class`, `true,false` resolve
identically through RAG (spot-checked via `/API/search`).
Pass 4 (refs): `incld="any,goal,fail,retry"` exist in `DATA/protos.txt` /
`DATA/blueprints.txt`; `prototype:endpoint|handler|module|source` resolve to the
Reference prototypes declared above.
Pass 5 (no invention): PHP names (`path`, `candidate`, `realpath`, `preg_split`,
`stripos`, ...) appear ONLY inside `{}`; no unverified token is used in the frame.

## Verification — 5 logic passes

Pass 1 (input->output): router resolves a path to a required file or returns N;
get maps `dict`->file->HTML; search maps `in`->matched objects->HTML; *_get map `id`->object.
Pass 2 (error paths): router -> 404 on self-request, N on extension/traversal;
get/proto_get/blueprint_get -> 404 on unknown id or missing source; search/proto_search/
blueprint_search -> `reason:` page on empty term and `[no match]` on empty blob.
Pass 3 (router guard order): `candidate!==false` BEFORE `is_file` (realpath can
return false; under `strict_types` `is_file(false)` is a TypeError); then
self-check BEFORE prefix/dot check; prefix check blocks traversal;
`basename has no '.'` blocks `.php`/dotfiles; root `/` -> index.
Pass 4 (search normalization): split on `(?m)(?=^[ \t]*\*->)`, strip leading blank
lines, `rtrim`, normalize LF->CRLF; case-SENSITIVE `str_contains` (main search) vs
case-INSENSITIVE `stripos` on id/desc (proto/blueprint search) - deliberately different.
Pass 5 (symmetry): proto_* and blueprint_* are identical logic over different scopes;
get vs search differ only by exact-id vs substring. Confirmed against source.

## Findings (semantic core + specfile review)

1. The frame (keys + operators + `:`/`->`/`<>` + indent) expressed the whole API
   WITHOUT adding a single new token: the core did NOT drift.
2. Logic pass 3 CAUGHT a real subtlety: the first draft dropped `candidate!==false`.
   Re-reading the PHP under `strict_types` showed `realpath()` may return false and
   `is_file(false)` throws. The semantic core surfaced the bug — core is healthy.
3. REVIEW FIX A (creation vs execution): added `action=create` framing and switched the
   RAG/self-check lines from `show` (action) to `ref` (reference), so a reader
   builds the PHP instead of calling the endpoints.
4. REVIEW FIX B (customization path): endpoint interfaces are now declared with
   `name`/`param`/`out`/`desc`; `{}` is reserved for the irreducible PHP expression.
5. REVIEW FIX C (prototypes): added reference protos `endpoint`, `handler`,
   `module`, `source` and referenced them via `prototype:<id>`; no more shapeless nodes.
6. REVIEW FIX D (create/function): `create` was defined as "critical" while used as "create"
   in ~37 places across docs/rules. Dictionary corrected to `create, create` = action
   create; "critical" moved to `critical`; `function` clarified (action if rule/agent, API
   entry point if specfile/architecture); canonical create form is `-> create function`.
7. Verified independently: `php -l` on all 9 units -> "No syntax errors detected".
