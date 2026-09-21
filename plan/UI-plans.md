# VibeDSL — UI Layer Plan (Material Design 3 reference)

Status: PLANNING (nothing added to dictionary yet)
Reference: Material Design 3 (m3.material.io) — reasons:
  1. M3 is the current trend in interface design
  2. M3 is a clean textbook of interface vocabulary

## Scope note
Network layer is CLOSED (lan/dmz/vpn/.../wan committed). This plan covers
the visual/frontend zone. Backend/util/games are separate future plans.

## Design principles (agreed)
- Tokens are SHORT (3-4 chars) — the language targets small models, balance
  clarity vs memory footprint: `vis`, `pan`, `thm`, `tab`, `tree` style.
- Prefer ABSTRACT tokens over precise ones: more implementation freedom.
  Precision is closed via `styp` (type) or `{}`/`desc` description.
- Do NOT drag N implementations of one thing into the base dictionary.
- M3 names are the REFERENCE VOCABULARY, not literal tokens: e.g. "text field"
  -> `inp` + type. Renders/builders diverge in `{}` blocks, not in tokens.
- Each token gets ONE meaning; ambiguity is resolved by position like the rest.

## Proposed token groups

## T0. COMPOSITION (priority, abstract)
Layout/containment primitives — needed FIRST, everything else sits inside them.
- row   - linear horizontal axis of children
- col   - linear vertical axis of children
- grd   - grid: two-axis placement (columns/areas)
- frm   - frame: bordered/inset container, viewport crop
- grp   - group: logical cluster of elements (one unit of state)
- ovl   - overlay: layer stacked above the base surface
- pag   - page: screen/route boundary
- sec   - section: block within a page
- hscroll - horizontal base scroll container
- vscroll - vertical base scroll container
- spr   - spacer: flexible empty space

## T0b. RECYCLER (first-class, NOT composed from abstracts)
- rcl   - virtualized list component; own adapter/view-holder pool, view
          reuse, lazy data binding via src; recycler view pattern

## T1. NAVIGATION (abstract)
- nav   - navigation rail/bar/drawer/tab-row as one concept; concrete via styp
- tab   - exists (tree tab) — reuse for tab row semantics
- link  - exists (target affiliation) — reuse for in-app links
- bct   - breadcrumb: trail of parent contexts (candidate; may fold into nav)

## T2. INPUT CONTROLS (abstract, selection-focused)
- inp   - input field (text/num/ml авто via styp)
- btn   - button (plain/fab/icon via styp)
- sel   - exists (selection) — covers checkbox/radio/switch/toggle semantics
- tgl   - binary toggle (switch feel) — candidate, may fold into sel
- slr   - slider: continuous value input
- pic   - exists (picture) — file/upload/image input via styp
- srch  - exists (search) — reuse for search input

## T2b. USER INPUT (events, user-driven)
- kdown   - key pressed down
- kpress  - key press (down+up, full stroke)
- kup     - key released up
- mosup   - mouse button up
- mosdown - mouse button down
- scrtap  - screen tap (touch)
- enter   - enter key: confirm/select

## T3. DISPLAY & FEEDBACK (abstract)
- crd   - card/surface container
- lst   - exists (list) — reuse for list/table rows
- icn   - icon: pictographic marker
- avt   - avatar: identity surface (person/entity)
- bdg   - badge: counters/status dot
- dvr   - divider: separator line
- prg   - progress: busy/loading indicator (linear/circular via styp)
- skn   - skeleton/shimmer placeholder
- tip   - tooltip: hover help
- msg   - exists (message) — covers snackbar/banner/toast semantics
- dlg   - dialog: modal/alert
- sht   - sheet: bottom/side panel (candidate; may fold into ovl+nav)
- thm   - exists (theme) — M3 color/shape/elevation system lives here

## Soft vetoes (NOT new tokens; avoid duplicates)
- chk exists as "check/verify" — do NOT reuse for checkbox; checkbox -> sel
- switch exists as SWITCH-CASE operator — do NOT reuse for UI toggle; toggle -> sel/tgl
- skl exists as "skill" — skeleton stays `skn`

## Syntax sketch
```
prj name="settings" thm="m3":
  -> pag name="main":
     -> col: -> sec name="profile" | -> frm name="list_card":
        -> inp name="login" styp:text
        -> sel name="theme" styp:switch
        -> btn name="save" act:apr
  -> rcl src="msg:list" item="row"
  -> ovl: -> dlg name="confirm" | -> msg name="saved" styp:snackbar
  -> hscroll: row: card name="c1"
```
Composition is explicit (`col`/`frm`/`ovl`), concrete effects follow the
`-> -> act` chain as usual. Recycler is a first-class component (`rcl`),
not composed from abstracts.

## Open questions for user review
- [x] (answered) T0 composition minus scr -> replaced by hscroll/vscroll; rcl first-class
- [x] (answered) tgl/sht/bct/avt kept separate
- [x] (answered) state handling via styp
- [ ] Still open: backend/util/games zones (future plans)
- [ ] Still open: how deep UI states (enabled/hover/focus) get documented

## TODO
- [x] Add approved UI tokens to DATA/dictionary.txt (COMPOSITION + NAV + INPUT + DISPLAY + USER INPUT)
- [ ] M3-reference block into VibeDSL.md + README.md + index
- [x] Sync RAG mirror + global agents
- [ ] Commit after docs