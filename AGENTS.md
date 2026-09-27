# AGENTS.md — VibeDSL

Pure PHP site (no composer, no build step). PHP >= 8.2, `str_contains`/`readonly` assumed.
Respond to the user in their language. Write code without comments unless the specfile asks.

## Run / verify
- `php -S 127.0.0.1:8000 router` — local server (router is REQUIRED: app files have no `.php` extension and the dev server executes only via the router).
- `php -l <file>` — syntax check (all files pass).
- Test endpoints headless: run `php API/search` / `php API/get` / `php API/blueprint_*` / `php API/proto_*` with `$_GET` preset (no PHPUnit; repo is script-testable).

## API
- `API/search?in=<term>` — RAG search over `DATA/dictionary_sorted_by_type.txt`, `DATA/syntax.txt`, `DATA/agents.txt` (blueprints and protos NOT searched; use `blueprint_*` / `proto_*`). Splits each source on the `*->` marker into objects, returns matching objects as an HTML page: `\r\n` -> `<br>`, tabs/leading spaces -> `&nbsp;` (indentation preserved), content escaped. Empty `in` -> "term required"; no match -> `[no match ...]`.
- `API/blueprint_search?in=<term>` — search ready blueprints only (ready architectural models), matches by `id=""` / `desc=""`; empty `in` -> term required.
- `API/blueprint_get?id=<id>` — exact ready blueprint by `id=""`; 404 if absent or `id` missing.
- `API/proto_search?in=<term>` — search abstract prototypes only (proto/blplan formal plans), matches by `id=""` / `desc=""`; empty `in` -> term required.
- `API/proto_get?id=<id>` — exact abstract prototype by `id=""`; 404 if absent or `id` missing.
- `API/get?dict=<dictionary|action|mapping|operators|abstracts|syntax|blueprints|protos|agents>` — whole source file as HTML (the four category split dicts `action.dict`/`mapping.dict`/`operators.dict`/`abstracts.txt` are generated into `DATA/` by `validator/spellcheck.py`); unknown dict -> 404 page.
- `API/compile?file=<path>[&raw=1]` — compiles a `.vibe`/`.vibedsl`/`.specfile` into the symbol layer by shelling out to `compiler/compile.py` (one implementation, not two). Returns `-----RULES-----` / `-----DATA-----` / `-----CODE-----` plus the compile report. Path is `realpath`-confined to the repo (403 outside), extension-checked (415), missing -> 404. `raw=1` gives `text/plain` instead of the HTML page. Override the interpreter with `VIBEDSL_PYTHON`.
- `API/symbol?glyph=<codepoints|glyph>` / `?word=<name>` — the `compiler/symbols_map.txt` row(s) in both directions; this is the lookup a compiler uses.
- `API/dict_add` — POST JSON `{section, value, desc, example}` (`section` in action|mapping|operators|abstracts), used by the IDE dictionary editor. Sanitizes (single-line fields, rejects `*->` / ` - ` in value), then calls `validator/pipeline_add.py`, which rejects duplicate aliases, appends the entry under the matching `type:` section of the master, and rebuilds canon splits + `ide/data.js` via `sort_dict.py --write` + `spellcheck.py` + `gen_data.py`. Ret JSON `{ok, section, value} | {ok, error}`.
- `API/lib` — shared helpers (`vibedslPage`, `vibedslToHtml`, `vibedslSources`). Source paths live here; change them in one place.

- **Several models work on this repository at once, and the work is partitioned between them.** That is the POINT, not a hazard to defend against. This gate runs over the WHOLE repository on purpose, so each model finds the other models' errors too — an earlier version refused to touch a "hot" file younger than 180 s, and that was wrong here: it would have hidden exactly the in-flight work a cross-check exists to catch.
- What replaced the lock is INFORMATION: **every failure carries the age of its file** (`plan/x.vibe (4m ago - likely still in progress)` vs `example/y.vibe (2d ago)`), so a specfile still being written reads differently from one nobody has touched. Judging which is which is the reader's job.
- `--scope=A,B` is a FOCUS flag for a quick targeted run, not a safety boundary. Leaving it off is the normal, correct way to run this.
- Two things are still worth coordinating, because they are shared derived state rather than findings: `spellcheck.py` / `ide/gen_data.py` regenerate files *from* the master dictionary, so they race with anyone editing the master; and `--bless` overwrites `spell_checker_v2.baseline.txt`, which is one shared list of known debt.

## The gate: `validator/spell_checker_v2.py`
One command, one verdict, one exit code. Run it before claiming anything works.
```
py -X utf8 validator\spell_checker_v2.py            # check everything
py -X utf8 validator\spell_checker_v2.py --list     # what it checks
py -X utf8 validator\spell_checker_v2.py --fix      # apply the safe rewrites, re-verify, then report
py -X utf8 validator\spell_checker_v2.py --bless    # record current failures as known debt
py -X utf8 validator\spell_checker_v2.py --only=GLYPHS,SPELL
py -X utf8 validator\spell_checker_v2.py plan\ide-specfile.vibe      # limit the specfile scope
```
| Check | What it proves | Module it calls |
|---|---|---|
| `ORDER` | the master dictionary is in alias order | `sort_dict.py` |
| `SPLITS` | the four category files are what the master implies | `spellcheck.py` |
| `GLYPHS` | G1-G8 on the mark table | `glyphs.py` (subprocess - it exits at import) |
| `HEADER` | every slot `compiler/header.txt` asks for is known, and none is left unfilled | `compiler/compile.py` |
| `PROSE` | the rewrite tool still leaves prose, payload and `{}` blocks alone | `explicit_inherit.py` |
| `INHERIT` | no implicit inheritance left in any code line | `explicit_inherit.py` |
| `CUT` | no context cut `;` inside a `for(...)` clause list | — |
| `SPELL` | every specfile passes the grammar | `validator.py` |
| `SYMBOLS` | every specfile compiles, emits only known marks, indentation byte-identical | `compiler/compile.py` |
| `TWICE` | compiling an already-compiled file changes nothing | `compiler/compile.py` |

- **The baseline.** The repo arrived with real debt: `example/IDE/*` and `PY_IDE/window.vibe` use action words (`halt`, `resolve`, `restore`, `apply`, `wrap`) and fields (`frm:prop`, `frm:corner`, `font:prop`) that were never added to the master. A gate that is red on day one gets ignored, so those are blessed into `validator/spell_checker_v2.baseline.txt` and only NEW failures fail the run. Close one with `--bless` after fixing it.
- **It imports, it does not reimplement.** The first version of `explicit_inherit.py` had its own line scanner and turned `the structure: a deeper` into `the:structure: a deeper`. A second implementation of "what is code and what is payload" is a second chance at that bug, so every check calls the module that already does the work.
- **One definition of scope.** `explicit_inherit.iter_targets()` is the single list of reference files. A case-sensitive `endswith(".md")` once skipped `RULES.MD` silently, and 14 lines of it were thought to be finished while they were not.
- `TWICE` earned its place on its first run: `!=` compiled to `¬=` and then to `¬⩲`, because the guard against compiling `=` after `!` was textual. The guard is now `(?<![!¬])` and `!=` is reported instead of silently mangled.

## The symbol layer (text -> symbols), for weak models
- `compiler/header.txt` is the compiler's `include.h`: ONE hand-written file with every invariant sentence of the RULES block (base task in English, what the three blocks are, how to read a mark, which ASCII is reserved). `compiler/compile.py` inlines it into every compiled specfile. It is a base file, not code: served by `GET /API/get?dict=header`, embedded into the IDE by `py ide/gen_data.py`, opened read-only. It is the same bytes on every compile, which is what makes it cheap for a small model. **Edit the prose there, never in `compile.py`.**
- Header slots: `@SOURCE@ @COUNT_MARKS@ @COUNT_TOTAL@ @COUNT_CONCEPTS@ @COUNT_DATA@ @ANCHOR@ @BLOCK_RULES@ @BLOCK_DATA@ @BLOCK_CODE@`. An unknown slot is a hard error (exit 1), so a typo can never reach a model as a hole in its instructions. Only the GLYPHS table under the header is generated per file.
- `compiler/compile.py` is the compiler: `py -X utf8 validator\compile.py <specfile.vibe> [-o out.txt] [--all-glyphs]`. It emits ONE file with three blocks — `-----RULES-----` (the header + the marks this file uses), `-----DATA-----` (every abstract/proto/blueprint/agent that `use()` pulled out of the RAG base, each marked with the anchor `•` U+2022), `-----CODE-----` (the specfile; execution starts here).
- The mark is looked up BY CONCEPT, in two passes. Pass 1: a word with a mark of its own keeps it. Pass 2: a word with no mark of its own inherits from its siblings, but only when they all agree on ONE mark. The master declares one concept as several words (`create, create`, `length, size, length`, `location, location`) while `symbols_map.txt` files the mark under one of them, usually the short phonetic one — the old reader looked up by the concept's own name, missed, and rescued only the single alias that happened to match, so 74 words across 64 concepts had a mark no input could reach. Where siblings disagree the dictionary contradicts itself (`unknown, none, unknown`; `include, import, incld`) and the word is left as text and reported: **a wrong mark is worse than no mark.**
- `RX_ENTRY` must keep the ` - ` (space-dash-space) separator and the `RX_ENTRY_BARE` fallback. A bare `-` separator truncates every head containing a dash — `*-> <-  - left strict link` parsed as head `<` with the description starting at `- left...`, so `<-` and `<->` vanished from the dictionary.
- Words AND grammar operators are compiled. Operator marks live in `symbols_map.txt` under the `# frame operators` block, declared in the master `type:logical operators` section, matched longest-alias-first so `<->` never degrades to `<-` and `<`. Word-shaped aliases carry word-boundary lookarounds so `styp` is not eaten by `sty`.
- `&->` is emitted as `•` U+2022 and `-[N]>` as `⪪` U+2AAA. Both are lifted out in `segments()` before the bracket rule, otherwise `-[3]>` would open a `[]` scope and never compile.
- Never rewritten, by design: text inside `""`, `{}`, `()` and `[]`, and `//` / `/* */` comments. `""` is the payload marker, `{}` is the free-form block, `()` is action scope — that boundary is how a model tells logic from a literal. The reserved-ASCII list lives in `compiler/header.txt` and nowhere else.
- `use()` is the ONLY import. All four written forms resolve: `use(id)`, `use(a,b)`, `use(VibeDSL:proto[if,goal,fail])`, `use(agent:name="coder")` / `use(agent name="coder")`. Nested `use()` inside a pulled body is followed. `incld="<id>"` is a mapping attribute, not an import — README says the same. An entry is delimited by the anchor line; the base's own `*->` marker is stripped, because compiled it became a multiplication sign glued to an arrow.
- The base is read-only. `compile.py` never writes to `DATA/`.
- The report is part of the contract: replacements, distinct marks emitted, `use()` resolution, words left as text because the base knows them but they own no mark, and a **hard failure (exit 1) if a mark is emitted that is not in `compiler/symbols_map.txt`**.
- A compile of an already-compiled file is effectively a no-op, so the transform is safe to re-run.
- `py -X utf8 validator\glyphs.py` guards the table (G1 no duplicate codepoint, G2 no CJK/Hangul/fullwidth, G3 NFC+NFKC safe, G4 every mark word exists in the master, G5 no description contradicts the master, G6 order, G7 one mark per word, G8 multi-codepoint rows explicit). Exit 1 on any violation. Adding a mark means: a row in the master `type:logical operators` section, a row in `compiler/symbols_map.txt`, then `sort_dict.py` -> `spellcheck.py` -> `ide/gen_data.py`.



## Data model (single source of truth = DATA/*.txt
- `DATA/dictionary_sorted_by_type.txt` — master dictionary (type sections, single source); category splits generated by `validator/spellcheck.py` into `DATA/action.dict` + `DATA/mapping.dict` + `DATA/operators.dict` + `DATA/abstracts.txt` (tracked). Category semantics: `mapping` = attribute/state/ref/entity-kind operators (`...mapping of any entity`), `action` = verbs/action functions, `logical operators` = grammar, `behavior` = logic/events/patterns, `abstracts` = pure concepts only (`abstract`, `blueprint`, `proto`, `as`). `DATA/protos.txt` — abstract prototypes (proto/blplan: formal plans, execution templates); `DATA/blueprints.txt` — ready architectural models (blueprint: ready vector rules of projects/modules); `DATA/agents.txt` — agent rules. Semantic difference: prototypes are the ABSTRACT of ready models, blueprints are the READY (physically complete) models pulled in via `incld="<blueprint-id>"`.
- Every object starts with the marker `*->` on its own line; example lines are indented `-> example:...`. CRLF line endings, UTF-8.
- Master dictionary order is enforced by `validator/sort_dict.py`: `py -X utf8 validator\sort_dict.py` (report only, lists inversions, exit code 1) or `--write` (rewrites sections into alphabetical-by-primary-alias order). Always re-run after manual inserts, then `validator/spellcheck.py` to rebuild `action.dict` / `mapping.dict` / `operators.dict` / `abstracts.txt`.
- `compiler/symbols_map.txt` is the canonical word <-> glyph table (`U+XXXX  glyph  *-> word - meaning`). Read it, never hand-edit around `validator/glyphs.py`.
- The RAG API is the canonical read path for the language base: `GET /API/get?dict=dictionary|action|mapping|operators|abstracts|syntax|blueprints|protos|agents`, `GET /API/search?in=<term>` (dictionary/syntax/agents), `GET /API/blueprint_search?in=<term>` / `GET /API/blueprint_get?id=<id>` for ready blueprints and `GET /API/proto_search?in=<term>` / `GET /API/proto_get?id=<id>` for abstract prototypes. It reads the `DATA/*.txt` files (XML/base64 sources removed).

## Rules / protocol
- VibeDSL BASE AGENT RULES (the `coder` chain: specfile -> exam -> usr approve -> create -> exam -> goal|retry/rollback) and the dictionary are enforced by the agents declared in `agents/` (working copy: `agents/coder.md`), which read the RAG workspace `~/.config/opencode/opendsl/` (`agents.txt`, `protos.txt`, `blueprints.txt`, `DATA/`). Project copies of those data files live under `DATA/` here. Agent import into opencode happens after verification.
- `*->` marker semantics and the object split are parser contract — keep it when editing data files.
- `plan/*.vibe` are executable specs (validator PASS expected): `exit-on-clean.vibe`, `object-spellcheck.vibe`, `spellcheck-stage1.vibe`. `plan/models-compat.md` — empiric model-transfer numbers (~75% without dict, ~95% after 3 clean passes, never 100% — perfectionist error).