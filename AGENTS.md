# AGENTS.md — VibeDSL

Pure PHP site (no composer, no build step). PHP >= 8.2, `str_contains`/`readonly` assumed.
Respond to the user in their language. Write code without comments unless the spec asks.

## Run / verify
- `php -S 127.0.0.1:8000 router` — local server (router is REQUIRED: app files have no `.php` extension and the dev server executes only via the router).
- `php -l <file>` — syntax check (all files pass).
- Test endpoints headless: run `php API/search` / `php API/get` / `php API/blueprint_*` / `php API/proto_*` with `$_GET` preset (no PHPUnit; repo is script-testable).

## API
- `API/search?in=<term>` — RAG search over `DATA/dictionary.txt`, `DATA/syntax.txt`, `DATA/agents.txt` (blueprints and protos NOT searched; use `blueprint_*` / `proto_*`). Splits each source on the `*->` marker into objects, returns matching objects as an HTML page: `\r\n` -> `<br>`, tabs/leading spaces -> `&nbsp;` (indentation preserved), content escaped. Empty `in` -> "term required"; no match -> `[no match ...]`.
- `API/blueprint_search?in=<term>` — search ready blueprints only (ready architectural models), matches by `id=""` / `desc=""`; empty `in` -> term required.
- `API/blueprint_get?id=<id>` — exact ready blueprint by `id=""`; 404 if absent or `id` missing.
- `API/proto_search?in=<term>` — search abstract prototypes only (proto/blpt formal plans), matches by `id=""` / `desc=""`; empty `in` -> term required.
- `API/proto_get?id=<id>` — exact abstract prototype by `id=""`; 404 if absent or `id` missing.
- `API/get?dict=<dictionary|syntax|blueprints|protos|agents>` — whole source file as HTML; unknown dict -> 404 page.
- `API/lib` — shared helpers (`vibedslPage`, `vibedslToHtml`, `vibedslSources`). Source paths live here; change them in one place.

## Data model (single source of truth = DATA/*.txt)
- `DATA/dictionary.txt` — full dictionary entries (incl. keyword list); `DATA/protos.txt` — abstract prototypes (proto/blpt: formal plans, execution templates); `DATA/blueprints.txt` — ready architectural models (blpr: ready vector rules of projects/modules); `DATA/agents.txt` — agent rules. Semantic difference: prototypes are the ABSTRACT of ready models, blueprints are the READY (physically complete) models pulled in via `inc="<blueprint-id>"`.
- Every object starts with the marker `*->` on its own line; example lines are indented `-> exm:...`. CRLF line endings, UTF-8.
- The RAG API is the canonical read path for the language base: `GET /API/get?dict=dictionary|syntax|blueprints|protos|agents`, `GET /API/search?in=<term>` (dictionary/syntax/agents), `GET /API/blueprint_search?in=<term>` / `GET /API/blueprint_get?id=<id>` for ready blueprints and `GET /API/proto_search?in=<term>` / `GET /API/proto_get?id=<id>` for abstract prototypes. It reads the `DATA/*.txt` files (XML/base64 sources removed).

## Rules / protocol
- VibeDSL BASE AGENT RULES (the `coder` chain: spc -> exam -> usr apr -> crt -> exam -> goal|retry/rollback) and the dictionary are enforced by the agents declared in `agents/` (working copy: `agents/coder.md`), which read the RAG workspace `~/.config/opencode/opendsl/` (`agents.txt`, `protos.txt`, `blueprints.txt`, `DATA/`). Project copies of those data files live under `DATA/` here. Agent import into opencode happens after verification.
- `*->` marker semantics and the object split are parser contract — keep it when editing data files.