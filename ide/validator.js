/* VibeDSL validator v2 (search-command) - JS port of validator/validator.py
   Output (out[]) is byte-identical to the Python CLI (modulo CRLF).
   Interface: VibeDSLValidator.validate(text, opts) ->
     { out:[], markers:[], nerr, nwarn, verdict }
   opts: { dictText, protosText, blueprintsText, syntaxText, srcName } */
(function (root, factory) {
    var mod = factory();
    if (typeof module === "object" && module.exports) module.exports = mod;
    if (root) root.VibeDSLValidator = mod;
})(typeof self !== "undefined" ? self : this, function () {
    "use strict";

    var RE_ABSTRACT = /\babstract\b[^\n]*?\bid="([^"]+)"|\babstract\b\s+"([^"]+)"/g;
    var RE_AS = /\b(?:[,\s:(]as|:as|\bas)\s+([A-Za-z_]\w*)/g;
    var RE_FUN = /\bfun(?:ction)?\s+(?:id|name)="([^"]+)"/g;
    var RE_ENTITY_ACT = /^\s*(\w+):act="[^"]*"\s*(?::\s*name="([^"]+)")?/;
    var RE_COLON_BRANCH = /<>:|<>:\s*$/;
    var RE_CMD_WORD = /(?:->|<->|<>:|&->|:|\\)\s*([A-Za-z_]\w*)|^\s*([A-Za-z_]\w*)\s*(?:\(|:|\\|$)/g;
    var RE_USE = /\buse\(([^)]*)\)/g;
    var REG_ID = /\bid="([^"]+)"/;
    var REG_PROTO_LIST = /^VibeDSL:proto\[([^\]]*)\]/;
    var REG_USE_SRC = /^use\s+\w+\s+(?:src|name)=/;
    var SKIP_USE = ["agent", "use", "proto", "blueprint", "rule", "type", "scop",
                    "root", "src", "as", "dict", "name", "id", "incld", "act", "desc"];
    var ALNUM = /[\p{L}\p{N}]/u;
    var ABSTRACT_TYPES = ["function", "prop", "item"];

    var RUN = { typed: {}, useReach: new Set() };

    function Node(text, no, indent) {
        this.text = text;
        this.raw = text;
        this.no = no;
        this.indent = indent;
        this.children = [];
        this.parent = null;
        this.symbols = new Set();
        this.blockSyms = new Set();
        this.missingUse = new Set();
        this.absIds = new Set();
        this.dupIds = new Set();
    }

    function maskLines(lines) {
        /* Blank out AI custom blocks { ... } and comments (, human and
           block), preserving quoted string contents.
           Mirror of validator.py mask_lines. */
        var out = [];
        var inCustom = 0, inComment = false;
        for (var li = 0; li < lines.length; li++) {
            var s = String(lines[li]), n = s.length, i = 0, res = [], inStr = false;
            while (i < n) {
                var c = s.charAt(i);
                if (inComment) {
                    if (c === "*" && i + 1 < n && s.charAt(i + 1) === "/") {
                        inComment = false; res.push("  "); i += 2; continue;
                    }
                    res.push(" "); i++; continue;
                }
                if (inCustom) {
                    if (c === "{") inCustom++;
                    else if (c === "}") { inCustom--; if (inCustom < 0) inCustom = 0; }
                    res.push(" "); i++; continue;
                }
                if (!inStr) {
                    if (c === '"') { inStr = true; res.push(c); i++; continue; }
                    if (c === "/" && i + 1 < n && s.charAt(i + 1) === "/") break;
                    if (c === "/" && i + 1 < n && s.charAt(i + 1) === "*") {
                        inComment = true; res.push("  "); i += 2; continue;
                    }
                    if (c === "{") { inCustom = 1; res.push(" "); i++; continue; }
                } else {
                    if (c === "\\" && i + 1 < n) { res.push(s.charAt(i)); res.push(s.charAt(i + 1)); i += 2; continue; }
                    if (c === '"') inStr = false;
                    res.push(c); i++; continue;
                }
                res.push(c); i++;
            }
            out.push(res.join(""));
        }
        return out;
    }

    function buildTree(lines, rawLines) {
        var root = new Node(null, 0, -1);
        var stack = [root];
        for (var i = 0; i < lines.length; i++) {
            var norm = String(lines[i]).replace(/\t/g, "    ");
            var text = norm.trim();
            if (!text || text.charAt(0) === "#") continue;
            var indent = norm.length - norm.replace(/^\s+/, "").length;
            var node = new Node(text, i + 1, indent);
            node.raw = rawLines ? String(rawLines[i]) : text;
            while (stack[stack.length - 1].indent >= node.indent) stack.pop();
            node.parent = stack[stack.length - 1];
            stack[stack.length - 1].children.push(node);
            stack.push(node);
        }
        return root;
    }

    function entryAliases(text) {
        var words = new Set();
        String(text || "").split(/\r\n|\r|\n/).forEach(function (ln) {
            var s = ln.replace(/^\s+/, "");
            if (s.indexOf("*->") !== 0) return;
            var rest = s.replace(/^\*->\s*/, "");
            var head = rest.indexOf(" - ") !== -1 ? rest.split(" - ")[0] : rest;
            head.split(",").forEach(function (part) {
                part = part.trim();
                if (part) { words.add(part); words.add(part.toLowerCase()); }
            });
        });
        return words;
    }

    function loadEntries(protosText, blueprintsText) {
        var entries = {};
        function eat(text) {
            var cur = null, buf = [];
            String(text || "").split(/\r\n|\r|\n/).forEach(function (ln) {
                var s = ln.replace(/^\s+/, "");
                if (s.indexOf("*->") === 0) {
                    if (cur !== null) entries[cur] = buf.join("\n");
                    var m = /id="([^"]+)"/.exec(ln);
                    cur = m ? m[1] : null;
                    buf = [ln];
                } else if (cur !== null) {
                    buf.push(ln);
                }
            });
            if (cur !== null) entries[cur] = buf.join("\n");
        }
        eat(protosText);
        eat(blueprintsText);
        return entries;
    }

    function collectDecls(text) {
        var syms = new Set();
        var m;
        while ((m = RE_ABSTRACT.exec(text || "")) !== null) {
            if (m[1]) syms.add(m[1]);
            if (m[2]) syms.add(m[2]);
        }
        while ((m = RE_AS.exec(text || "")) !== null) syms.add(m[1]);
        while ((m = RE_FUN.exec(text || "")) !== null) syms.add(m[1]);
        var em = RE_ENTITY_ACT.exec(text || "");
        if (em) {
            syms.add(em[1] + ":" + (em[2] || em[1]));
            syms.add(em[1]);
        }
        return syms;
    }

    function parseAbstract(raw, typed, out) {
        /* Full abstract syntax (object spell-checker):
           abstract{description} function{type function,prop,item} id="X" {init} -> {logic}
           Returns the declared id (or null) for uniqueness tracking. */
        var m = /\babstract\b/.exec(raw || "");
        if (!m) return null;
        var seg = raw.slice(m.index);
        var mid = /id="([^"]+)"/.exec(seg);
        if (!mid) return null;
        var aid = mid[1];
        var types = [];
        var tm = /function\s*\{([^}]*)\}/.exec(seg);
        if (tm) {
            tm[1].split(/[\s,]+/).forEach(function (t) {
                t = t.trim().toLowerCase();
                if (ABSTRACT_TYPES.indexOf(t) !== -1) types.push(t);
            });
        }
        var kw = seg.match(/\b(?:function|prop|item)\b/g) || [];
        kw.forEach(function (t) { types.push(t); });
        if (!types.length) types = ["item"];
        var subs = [];
        var mim = /id="[^"]+"\s*\{([^}]*)\}/.exec(seg);
        if (mim) {
            subs = (mim[1].match(/"[^"]+"/g) || []).map(function (s) { return s.slice(1, -1); });
        }
        types.forEach(function (t) {
            if (!typed[t]) typed[t] = new Set();
            typed[t].add(aid);
            subs.forEach(function (s) { typed[t].add(aid + ":" + s); });
        });
        out.add(aid);
        subs.forEach(function (s) { out.add(aid + ":" + s); });
        return aid;
    }

    function useTargets(inner) {
        inner = String(inner || "").trim();
        if (!inner || /agent/i.test(inner) || REG_USE_SRC.test(inner)) return [];
        var m = REG_PROTO_LIST.exec(inner);
        if (m) return m[1].split(",").map(function (t) { return t.trim(); }).filter(Boolean);
        m = REG_ID.exec(inner);
        if (m) return [m[1]];
        var out = [], mm, re = /[A-Za-z_]\w*/g;
        while ((mm = re.exec(inner)) !== null) {
            if (SKIP_USE.indexOf(mm[0].toLowerCase()) === -1) out.push(mm[0]);
        }
        return out;
    }

    function blueprintSymbols(entryText, seen, out, entries) {
        collectDecls(entryText).forEach(function (s) { out.add(s); });
        parseAbstract(entryText, RUN.typed, out);
        var mm;
        while ((mm = RE_USE.exec(entryText)) !== null) {
            useTargets(mm[1]).forEach(function (t) {
                if (seen.has(t)) return;
                seen.add(t);
                if (t in entries) {
                    RUN.useReach.add(t);
                    out.add(t);
                    blueprintSymbols(entries[t], seen, out, entries);
                }
            });
        }
        RE_USE.lastIndex = 0;
        RE_ABSTRACT.lastIndex = 0;
        RE_AS.lastIndex = 0;
        RE_FUN.lastIndex = 0;
    }

    function childrenChain(node) {
        var chain = [];
        node.children.forEach(function (ch) {
            chain.push(ch);
            chain = chain.concat(childrenChain(ch));
        });
        return chain;
    }

    function blockLines(node) {
        if (node === null) return [];
        return [[node, node.text || ""]].concat(childrenChain(node).map(function (ch) {
            return [ch, ch.text || ""];
        }));
    }

    function computeBlocks(node) {
        node.children.forEach(computeBlocks);
        node.blockSyms = new Set(node.symbols);
        node.children.forEach(function (ch) {
            ch.blockSyms.forEach(function (s) { node.blockSyms.add(s); });
        });
        return node.blockSyms;
    }

    function resolveUses(node, entries) {
        var seen = new Set();
        var mm;
        while ((mm = RE_USE.exec(node.text || "")) !== null) {
            useTargets(mm[1]).forEach(function (t) {
                if (seen.has(t)) return;
                seen.add(t);
                if (t in entries) {
                    RUN.useReach.add(t);
                    node.symbols.add(t);
                    blueprintSymbols(entries[t], seen, node.symbols, entries);
                } else {
                    node.missingUse.add(t);
                }
            });
        }
        RE_USE.lastIndex = 0;
        node.children.forEach(function (ch) { resolveUses(ch, entries); });
    }

    function collectAll(node, entries) {
        node.symbols = collectDecls(node.text || "");
        node.absIds = new Set();
        var raw = node.raw || "";
        var mm;
        RE_ABSTRACT.lastIndex = 0;
        while ((mm = RE_ABSTRACT.exec(raw)) !== null) {
            if (mm[1]) node.absIds.add(mm[1]);
            if (mm[2]) node.absIds.add(mm[2]);
        }
        var aid = parseAbstract(raw, RUN.typed, node.symbols);
        if (aid) node.absIds.add(aid);
        resolveUses(node, entries);
        node.children.forEach(function (ch) { collectAll(ch, entries); });
    }

    function dupCheck(root, entries) {
        /* The spell-checker sees ids everywhere in files connected via use():
           an abstract id must not duplicate an id declared in the reachable
           base (or another line of the same spec). */
        var base = new Set(RUN.useReach);
        RUN.useReach.forEach(function (rid) {
            var txt = rid in entries ? entries[rid] : null;
            if (!txt) return;
            var mm;
            RE_ABSTRACT.lastIndex = 0;
            while ((mm = RE_ABSTRACT.exec(txt)) !== null) {
                if (mm[1]) base.add(mm[1]);
                if (mm[2]) base.add(mm[2]);
            }
            RE_FUN.lastIndex = 0;
            while ((mm = RE_FUN.exec(txt)) !== null) base.add(mm[1]);
        });
        var visited = new Set();
        childrenChain(root).forEach(function (nd) {
            nd.absIds.forEach(function (aid) {
                if (base.has(aid) || visited.has(aid)) nd.dupIds.add(aid);
                else visited.add(aid);
            });
        });
    }

    function isVisible(node, sym) {
        for (var cur = node; cur !== null; cur = cur.parent) {
            if (cur.blockSyms.has(sym)) return true;
        }
        return false;
    }

    function commandWords(text) {
        var scan = String(text || "").replace(/"[^"]*"/g, '""');
        var used = new Set();
        var m;
        RE_CMD_WORD.lastIndex = 0;
        while ((m = RE_CMD_WORD.exec(scan)) !== null) {
            var w;
            if (m[1]) {
                w = m[1];
                var before = scan[m.index - 1];
                if (before !== undefined && (ALNUM.test(before) || "_)]".indexOf(before) !== -1)) continue;
            } else {
                w = m[2];
            }
            if (w) used.add(w);
        }
        return used;
    }

    function countParens(s) {
        var o = 0, c = 0, i;
        for (i = 0; i < s.length; i++) {
            if (s.charAt(i) === "(") o++;
            else if (s.charAt(i) === ")") c++;
        }
        return o - c;
    }

    function objectSets() {
        var declared = new Set();
        var owned = new Set();
        Object.keys(RUN.typed).forEach(function (k) {
            RUN.typed[k].forEach(function (v) {
                if (v.indexOf(":") !== -1) owned.add(v);
                else declared.add(v);
            });
        });
        return { declared: declared, owned: owned };
    }

    var RE_PIN = /(?<![:\w])([A-Za-z_]\w*):([A-Za-z_]\w*)/g;

    function checkPins(node, scanText, diags) {
        /* Object spell-checker: a compound obj:pin is allowed only if pin was
           declared for the object (abstract{...} init or obj:act name="..."). */
        var sets = objectSets();
        var sparse = String(scanText || "").replace(/"[^"]*"/g, '""');
        RE_PIN.lastIndex = 0;
        var mm;
        while ((mm = RE_PIN.exec(sparse)) !== null) {
            var obj = mm[1];
            var pin = mm[2];
            if (pin === "act" || pin === "action") continue;
            if (!sets.declared.has(obj)) continue;
            var comp = obj + ":" + pin;
            if (sets.owned.has(comp) || isVisible(node, comp)) continue;
            diags.push([node.no, "E", "line " + node.no + ": unknown pin '" + comp + "' not declared for object '" + obj + "' (abstract init or " + obj + ":act name=...)"]);
        }
        RE_PIN.lastIndex = 0;
    }

    function check(node, KNOWN, diags) {
        var text = node.text || "";

        if (RE_COLON_BRANCH.test(text)) {
            if (!node.children.length) {
                diags.push([node.no, "E", "line " + node.no + ": <>: must have indented variant lines below"]);
            }
            node.children.forEach(function (ch) {
                if (!/^\s*->/.test(ch.text || "")) {
                    diags.push([ch.no, "E", "line " + ch.no + ": <>: variant child must start with -> ahead"]);
                }
            });
        }
        if (text.indexOf("\\(") !== -1 && text.indexOf("act=") === -1 && text.indexOf("action=") === -1) {
            diags.push([node.no, "E", "line " + node.no + ": change operator \\( needs act= or action= inside"]);
        }

        var scanText;
        if (node.parent !== null && RE_COLON_BRANCH.test(node.parent.text || "")) {
            scanText = String(text || "").replace(/^\s*->\s*\w+/, "");
        } else {
            scanText = text;
        }

        commandWords(scanText).forEach(function (w) {
            if (w.length < 2 || KNOWN.has(w) || w === "stage") return;
            if (isVisible(node, w)) return;
            diags.push([node.no, "E", "line " + node.no + ": unknown command word '" + w + "' not declared in visible scope"]);
        });

        objectSets().declared.size !== 0 && checkPins(node, scanText, diags);

        var depth = 0;
        blockLines(node).forEach(function (pair) {
            depth += countParens(pair[1]);
            if (depth < 0) {
                diags.push([pair[0].no, "E", "line " + pair[0].no + ": extra ) before its ( scope"]);
                depth = 0;
            }
        });
        node.missingUse.forEach(function (t) {
            diags.push([node.no, "E", "line " + node.no + ": use(...) target " + t + " not in base (protos.txt/blueprints.txt)"]);
        });
        node.dupIds.forEach(function (aid) {
            diags.push([node.no, "E", "line " + node.no + ": id '" + aid + "' already defined (use base or duplicated)"]);
        });
        if (depth) {
            diags.push([node.no, "E", "line " + node.no + ": unclosed ( ... ) - scope must close before indent returns to command level"]);
        }
    }

    function walk(node, KNOWN, diags) {
        node.children.forEach(function (ch) { walk(ch, KNOWN, diags); });
        if (node.parent !== null) check(node, KNOWN, diags);
    }

    function markGeometry(msg, lineText) {
        var col = 1, end = 2;
        var m = /'(.*?)'/.exec(msg);
        if (m) {
            var idx = lineText.indexOf(m[1]);
            if (idx !== -1) {
                col = idx + 1;
                end = col + Math.max(1, m[1].length);
            }
        }
        return { col: col, end: end };
    }

    function validate(text, opts) {
        opts = opts || {};
        var srcName = opts.srcName || "<line>";
        var out = [];
        var markers = [];

        var KNOWN = entryAliases(opts.dictText || "");
        entryAliases(opts.syntaxText || "").forEach(function (w) { KNOWN.add(w); });
        ["stage", "scop", "srch", "mix"].forEach(function (w) { KNOWN.add(w); });
        var entries = loadEntries(opts.protosText || "", opts.blueprintsText || "");
        RUN.typed = {};
        RUN.useReach = new Set();

        out.push("== " + String(srcName).split(/[\\/]/).pop());

        var lines = String(text || "").split(/\r\n|\r|\n/);
        var root = buildTree(maskLines(lines), lines);
        collectAll(root, entries);
        dupCheck(root, entries);
        root.children.forEach(computeBlocks);

        var diags = [];
        walk(root, KNOWN, diags);

        diags.sort(function (a, b) {
            if (a[0] !== b[0]) return a[0] - b[0];
            if (a[1] < b[1]) return -1;
            if (a[1] > b[1]) return 1;
            if (a[2] < b[2]) return -1;
            if (a[2] > b[2]) return 1;
            return 0;
        });

        var seen = new Set();
        var errs = 0;
        diags.forEach(function (d) {
            if (seen.has(d[2])) return;
            seen.add(d[2]);
            errs++;
            out.push("  " + d[1] + " " + d[2]);
            var geo = markGeometry(d[2], lines[d[0] - 1] || "");
            markers.push({
                startLineNumber: d[0],
                startColumn: geo.col,
                endLineNumber: d[0],
                endColumn: geo.end,
                message: d[2],
                severity: 8
            });
        });

        var verdict = errs === 0 ? "PASS" : "FAIL";
        out.push("# verdict: " + verdict + " (errors=" + errs + ")");

        return {
            out: out,
            markers: markers,
            nerr: errs,
            nwarn: 0,
            verdict: verdict,
            diagnostics: diags
        };
    }

    return {
        validate: validate,
        entryAliases: entryAliases,
        buildTree: buildTree,
        collectDecls: collectDecls,
        useTargets: useTargets
    };
});