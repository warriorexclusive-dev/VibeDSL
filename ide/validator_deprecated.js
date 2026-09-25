/* ARCHIVED v1 validator - DO NOT RUN. Canon: ide/validator.js (v2, py/js parity).
   v1 tokens use removed operators (<|, |>, !=, +=, -=). Kept for reference only. */
/* VibeDSL validator v1 - JS port of validator/validator.py
   Output (out[]) is byte-identical to the Python CLI (modulo CRLF). */
(function (root, factory) {
    var mod = factory();
    if (typeof module === "object" && module.exports) module.exports = mod;
    if (root) root.VibeDSLValidator = mod;
})(typeof self !== "undefined" ? self : this, function () {
    "use strict";

    var MULTI_OP = ["<>:", "<-()", "()->", "<->", "&->", "<>=", "::point:", "<=>",
                    "<=<", "|>", ":?", ":=", "<=", ">=", "!=", "==", "+=", "-=",
                    "->", "<-", "<>", "||", "&&", "*?", "//"]
        .slice().sort(function (a, b) { return b.length - a.length; });
    var SINGLE_PUNCT = ":;,()[]{}@~";
    var DECL = { fun: 1, func: 1, "function": 1 };
    var START_OPS = "+-*/%!|?~<>=&^\\";
    var CONT_OPS = "+-*/%!|?~<>=&^";

    var RE_ALPHA = /[\p{L}_]/u;
    var RE_ALNUM = /[\p{L}\p{N}]/u;
    var RE_DIGIT = /[0-9]/;

    function isAlpha(c) { return c !== undefined && RE_ALPHA.test(c); }
    function isAlnum(c) { return c !== undefined && RE_ALNUM.test(c); }
    function isDigit(c) { return c !== undefined && RE_DIGIT.test(c); }

    function pyRepr(s) {
        if (s.indexOf("'") !== -1 && s.indexOf("\\") === -1) return '"' + s + '"';
        return "'" + s.replace(/\\/g, "\\\\").replace(/'/g, "\\'") + "'";
    }

    function splitLines(text) { return text.split(/\r\n|\r|\n/); }

    function Token(kind, val, pos, line) {
        this.kind = kind;
        this.val = val;
        this.pos = pos;
        this.line = line;
        this.issue = null;
    }

    function Category() {
        this.alias2cat = Object.create(null);
        this.catNames = [];
    }

    Category.prototype.load = function (text) {
        var cur = null;
        var self = this;
        splitLines(text).forEach(function (ln) {
            var s = ln.trim();
            if (s.indexOf("type:") === 0) {
                cur = s.slice(5).trim();
                if (self.catNames.indexOf(cur) === -1) self.catNames.push(cur);
            } else if (s.indexOf("*->") === 0 && cur) {
                var head = s.slice(3).trim();
                var m = head.match(/^(.*?)\s+-\s?(.*)$/);
                var kws = (m ? m[1] : head).trim();
                kws.split(/[,\s]/).forEach(function (a) {
                    a = a.trim().toLowerCase();
                    if (a && !(a in self.alias2cat)) self.alias2cat[a] = cur;
                });
            }
        });
        return Object.keys(this.alias2cat).length;
    };

    Category.prototype.cat_of = function (tok) {
        var v = this.alias2cat[String(tok).toLowerCase()];
        return v === undefined ? null : v;
    };

    function tokenize(text) {
        var toks = [];
        var i = 0, n = text.length, line = 1;
        while (i < n) {
            var c = text[i];
            if (c === "\n") { line++; i++; continue; }
            if (c === " " || c === "\t" || c === "\r") { i++; continue; }
            if (c === "/" && text[i + 1] === "/") {
                var j = text.indexOf("\n", i);
                toks.push(new Token("hcomment", text.slice(i, j === -1 ? n : j), i, line));
                i = j === -1 ? n : j;
                continue;
            }
            if (c === "/" && text[i + 1] === "*") {
                var j2 = text.indexOf("*/", i + 2);
                if (j2 === -1) {
                    var t0 = new Token("hcomment", text.slice(i, n), i, line);
                    t0.issue = "error";
                    toks.push(t0);
                    i = n;
                } else {
                    toks.push(new Token("hcomment", text.slice(i, j2 + 2), i, line));
                    i = j2 + 2;
                }
                continue;
            }
            if (c === "#") {
                var j3 = text.indexOf("\n", i);
                toks.push(new Token("hcomment", text.slice(i, j3 === -1 ? n : j3), i, line));
                i = j3 === -1 ? n : j3;
                continue;
            }
            if (c === "{") {
                var j4 = i + 1, depth = 1;
                while (j4 < n && depth) {
                    if (text[j4] === "{") depth++;
                    else if (text[j4] === "}") depth--;
                    else if (text[j4] === "\n") line++;
                    j4++;
                }
                if (depth) {
                    var t1 = new Token("custom", text.slice(i + 1, n), i, line);
                    t1.issue = "error";
                    toks.push(t1);
                } else {
                    toks.push(new Token("custom", text.slice(i + 1, j4 - 1), i, line));
                }
                i = j4;
                continue;
            }
            if (c === '"') {
                var j5 = i + 1;
                while (j5 < n && text[j5] !== '"') {
                    if (text[j5] === "\n") line++;
                    j5++;
                }
                if (j5 >= n) {
                    var t2 = new Token("str", text.slice(i + 1, j5), i, line);
                    t2.issue = "error";
                    toks.push(t2);
                } else {
                    toks.push(new Token("str", text.slice(i + 1, j5), i, line));
                }
                i = j5 + 1;
                continue;
            }
            if (isDigit(c)) {
                var j6 = i + 1;
                while (j6 < n && (isAlnum(text[j6]) || text[j6] === "_" || text[j6] === ".")) {
                    j6++;
                }
                var num = text.slice(i, j6).replace(/[._]+$/, "");
                toks.push(new Token("num", num, i, line));
                i = j6;
                continue;
            }
            if (c === "-" && text.startsWith("-[", i)) {
                var br = text.indexOf("]", i + 2);
                if (br !== -1 && br + 1 < n && text[br + 1] === ">") {
                    var op = text.slice(i, br + 2);
                    toks.push(new Token("op", op, i, line));
                    var nl = op.split("\n").length - 1;
                    line += nl;
                    i = br + 2;
                    continue;
                }
            }
            var hit = null;
            for (var mi = 0; mi < MULTI_OP.length; mi++) {
                if (text.startsWith(MULTI_OP[mi], i)) { hit = MULTI_OP[mi]; break; }
            }
            if (hit) {
                toks.push(new Token("op", hit, i, line));
                i += hit.length;
                continue;
            }
            if (isAlpha(c)) {
                var j7 = i + 1;
                while (j7 < n && (isAlnum(text[j7]) || text[j7] === "_" || text[j7] === ".")) j7++;
                toks.push(new Token("word", text.slice(i, j7), i, line));
                i = j7;
                continue;
            }
            if (START_OPS.indexOf(c) !== -1) {
                var j8 = i + 1;
                while (j8 < n && CONT_OPS.indexOf(text[j8]) !== -1) j8++;
                toks.push(new Token("op", text.slice(i, j8), i, line));
                i = j8;
                continue;
            }
            if (SINGLE_PUNCT.indexOf(c) !== -1) {
                toks.push(new Token("punct", c, i, line));
                i++;
                continue;
            }
            var t3 = new Token("other", c, i, line);
            t3.issue = "error";
            toks.push(t3);
            i++;
        }
        return toks;
    }

    function checkStructure(toks) {
        var errors = [];
        var stack = [];
        var pairs = { ")": "(", "]": "[", "}": "{" };
        toks.forEach(function (t) {
            if (t.kind === "punct" && "([{".indexOf(t.val) !== -1) {
                stack.push([t, t.val]);
            } else if (t.kind === "punct" && ")]}".indexOf(t.val) !== -1) {
                if (!stack.length || stack[stack.length - 1][1] !== pairs[t.val]) {
                    errors.push([t, t.val]);
                } else {
                    stack.pop();
                }
            }
        });
        stack.forEach(function (e) { errors.push([e[0], e[1]]); });
        return errors;
    }

    function scanUserdefs(toks) {
        var userdefs = Object.create(null);
        var body = new Set();
        var sig = toks;
        var n = sig.length;
        for (var i = 0; i < n; i++) {
            var t = sig[i];
            if (t.kind === "word" && t.val.toLowerCase() === "alias") {
                var j = i + 1;
                while (j < n && !(sig[j].kind === "punct" && sig[j].val === "]")) j++;
                j++;
                while (j < n && !(sig[j].kind === "word" && sig[j].val.toLowerCase() === "as")) j++;
                if (j + 1 < n && sig[j + 1].kind === "word") {
                    userdefs[sig[j + 1].val.toLowerCase()] = "useralias";
                }
            } else if (t.kind === "word" && t.val.toLowerCase() === "abstract") {
                var jj = i + 1;
                if (jj + 2 < n && sig[jj].kind === "word" && sig[jj].val.toLowerCase() === "name"
                        && sig[jj + 1].kind === "op" && sig[jj + 1].val === "="
                        && sig[jj + 2].kind === "str") {
                    userdefs[sig[jj + 2].val.toLowerCase()] = "userabstract";
                    for (var k = jj + 3; k < n; k++) {
                        if (sig[k].kind === "word" && sig[k].line === sig[jj + 2].line) {
                            body.add(sig[k].line + ":" + sig[k].pos);
                        }
                    }
                }
            }
        }
        return { userdefs: userdefs, abody: body };
    }

    function ruleChecks(toks, text, cat) {
        var out = [];
        var sig = toks.filter(function (t) { return t.kind !== "hcomment"; });
        var depth_p = 0, depth_b = 0;
        var header_lines = new Set();
        splitLines(text).forEach(function (ln, li) {
            if (ln.trim().startsWith("*->")) header_lines.add(li);
        });
        for (var idx = 0; idx < sig.length; idx++) {
            var t = sig[idx];
            if (t.kind === "punct") {
                if (t.val === "(") depth_p++;
                else if (t.val === ")") depth_p = Math.max(0, depth_p - 1);
                else if (t.val === "[") depth_b++;
                else if (t.val === "]") depth_b = Math.max(0, depth_b - 1);
            }
            if (t.kind !== "word") continue;
            if (header_lines.has(t.line - 1)) continue;
            var low = t.val.toLowerCase();
            var c = cat.cat_of(low);
            if (low in DECL) {
                if (idx + 1 >= sig.length) {
                    out.push({ msg: "declaration '" + t.val + "' has no target after it", tok: t });
                    continue;
                }
                var nx0 = sig[idx + 1];
                var gap = text.slice(t.pos + t.val.length, nx0.pos);
                if (nx0.kind === "other") continue;
                if (!/\s/.test(gap)) {
                    out.push({ msg: "declaration '" + t.val + "' must be followed by a space", tok: t });
                }
                continue;
            }
            if (c === "action" && depth_p === 0 && depth_b === 0) {
                var nx = sig[idx + 1] || null;
                var prev = idx > 0 ? sig[idx - 1] : null;
                var vn = nx ? nx.val : null;
                var vp = prev ? prev.val : null;
                if (vn === "=" || vn === "==") continue;
                if (vn === "\\") continue;
                if (vn === "(") continue;
                if (vn === ":") continue;
                if (prev && (prev.kind === "punct" || prev.kind === "op")
                        && ["(", "[", ",", "]", "=", ":", ")"].indexOf(vp) !== -1) continue;
                if (prev && prev.kind === "word") continue;
                if (prev && (prev.kind === "str" || prev.kind === "num")) continue;
                if (["->", "<-", "<->", "|", "!", "<>", "<>:", ";"].indexOf(vp) !== -1) { /* pass */ }
                out.push({ msg: "action '" + t.val + "' must declare scope '()'", tok: t });
            }
            if (c === null && depth_p === 0 && depth_b === 0) {
                var nx1 = sig[idx + 1] || null;
                var prev1 = idx > 0 ? sig[idx - 1] : null;
                var vn1 = nx1 ? nx1.val : null;
                var vp1 = prev1 ? prev1.val : null;
                if (prev1 && prev1.kind === "op"
                        && ["->", "<-", "<->", "<>:", "&->"].indexOf(vp1) !== -1) {
                    if (["(", "[", "=", ":", "\\", "{", ";", ")", "]"].indexOf(vn1) !== -1) continue;
                    if (nx1 && nx1.kind === "word") {
                        var after = sig[idx + 2] || null;
                        if (after && after.val === "=") continue;
                        var eol = text.indexOf("\n", t.pos);
                        var tail = text.slice(t.pos, eol === -1 ? text.length : eol);
                        if (tail.indexOf("=") === -1) continue;
                        out.push({ msg: "unknown word '" + t.val + "' in step position looks like a call without scope: use " + t.val + "(...)", tok: t });
                    }
                }
            }
        }
        return out;
    }

    function loadBase(text) {
        var entries = Object.create(null);
        var cur_id = null;
        var buf = [];
        function flush() {
            if (cur_id !== null) entries[cur_id] = buf.join("\n");
        }
        splitLines(text || "").forEach(function (ln) {
            if (ln.trim().startsWith("*->")) {
                flush();
                var m = ln.match(/id="([^"]+)"/);
                cur_id = m ? m[1] : null;
                buf = [ln];
            } else {
                buf.push(ln);
            }
        });
        flush();
        return entries;
    }

    function scanActs(toks) {
        var acts = Object.create(null);
        var sig = toks.filter(function (t) { return t.kind !== "hcomment"; });
        var n = sig.length;
        for (var i = 0; i < n; i++) {
            var t = sig[i];
            if (t.kind === "word" && t.val.toLowerCase() === "abstract" && i + 1 < n) {
                var nx = sig[i + 1];
                var name = null;
                if (nx.kind === "str") name = nx.val;
                else if (nx.kind === "word") name = nx.val;
                if (name) {
                    var j = i + 2;
                    while (j + 2 < n && sig[j].line - t.line <= 4) {
                        if (sig[j].kind === "op" && sig[j].val === "->"
                                && sig[j + 1].kind === "word" && sig[j + 1].val.toLowerCase() === "act"
                                && sig[j + 2].kind === "op" && sig[j + 2].val === "=") {
                            acts[name.toLowerCase()] = "abstract act: " + name;
                            break;
                        }
                        j++;
                    }
                }
            }
            if (t.kind === "word" && i + 3 < n
                    && sig[i + 1].kind === "punct" && sig[i + 1].val === ":"
                    && sig[i + 2].kind === "word" && sig[i + 2].val.toLowerCase() === "act"
                    && sig[i + 3].kind === "op" && sig[i + 3].val === "=") {
                var entity = t.val.toLowerCase();
                var alias = "act";
                var k = i + 4;
                if (k < n && sig[k].kind === "str") k++;
                if (k + 3 < n && sig[k].kind === "punct" && sig[k].val === ":"
                        && sig[k + 1].kind === "word" && sig[k + 1].val.toLowerCase() === "name"
                        && sig[k + 2].kind === "op" && sig[k + 2].val === "="
                        && sig[k + 3].kind === "str") {
                    alias = sig[k + 3].val.toLowerCase();
                }
                acts[entity + ":" + alias] = "entity act: " + entity + ":" + alias;
            }
        }
        return acts;
    }

    function assetChecks(toks, text, cat, userdefs, acts, abody, proto_ids, bp_ids) {
        var out = [];
        var used = [];
        var sig = toks.filter(function (t) { return t.kind !== "hcomment"; });
        var n = sig.length;
        var line_zone = {};
        var li = 0;
        splitLines(text).forEach(function (ln) {
            var s = ln.trim();
            if (s.startsWith("*->")) {
                var i = ln.indexOf(" - ");
                line_zone[li] = i >= 0 ? i : null;
            }
            li++;
        });

        for (var idx = 0; idx < n; idx++) {
            var t = sig[idx];
            if (t.kind !== "word") continue;
            var low = t.val.toLowerCase();
            var z = line_zone[t.line - 1];
            if (z !== undefined && z !== null && t.pos >= z) continue;
            var nx = idx + 1 < n ? sig[idx + 1] : null;
            var is_call = nx !== null && nx.kind === "punct" && nx.val === "(";
            var pv = idx > 0 ? sig[idx - 1] : null;
            var bnd = (pv === null
                || (pv.kind === "op" && ["->", "<-", "<->", ":-"].indexOf(pv.val) !== -1)
                || (pv.kind === "punct" && [":", ",", "(", ")", "{", ";", "]"].indexOf(pv.val) !== -1));
            var close = null;
            var depth = 0;
            for (var k = idx + 2; k < n; k++) {
                if (sig[k].line > t.line) break;
                if (sig[k].kind === "punct" && sig[k].val === "(") depth++;
                else if (sig[k].kind === "punct" && sig[k].val === ")") {
                    if (depth === 0) { close = k; break; }
                    depth--;
                }
            }
            var prose_trail = (close !== null && close + 1 < n && sig[close + 1].line === t.line
                && sig[close + 1].kind === "word");
            var code_site = bnd && close !== null && !prose_trail;
            if (is_call && low === "use") {
                if (!code_site) continue;
                depth = 1;
                var j = idx + 2;
                var inner = [];
                while (j < n && depth) {
                    if (sig[j].kind === "punct") {
                        if (sig[j].val === "(") depth++;
                        else if (sig[j].val === ")") {
                            depth--;
                            if (depth === 0) break;
                        }
                    }
                    if (sig[j].kind === "word") inner.push(sig[j].val.toLowerCase());
                    j++;
                }
                var hit = null;
                for (var w = 0; w < inner.length; w++) {
                    if (inner[w] in proto_ids || inner[w] in bp_ids) { hit = inner[w]; break; }
                }
                var anyCat = false;
                for (var w2 = 0; w2 < inner.length; w2++) {
                    if (cat.cat_of(inner[w2])) { anyCat = true; break; }
                }
                if (hit === null && !anyCat) {
                    var innerRepr = inner.map(function (w) { return pyRepr(w); }).join(", ");
                    out.push({
                        msg: "use(...) target [" + innerRepr + "] not in base (DATA/protos.txt / DATA/blueprints.txt) nor in dictionary",
                        tok: t
                    });
                } else if (hit !== null) {
                    used.push(hit);
                }
                continue;
            }
            if (!is_call || !code_site) continue;
            if (low in DECL) continue;
            if (abody.has(t.line + ":" + t.pos)) continue;
            var cat_ok = cat.cat_of(low) !== null;
            if (!cat_ok && idx >= 2 && sig[idx - 1].kind === "punct" && sig[idx - 1].val === ":"
                    && sig[idx - 2].kind === "word") {
                var composite = sig[idx - 2].val.toLowerCase() + ":" + low;
                if (composite in acts) continue;
            }
            if (cat_ok || low in userdefs || low in acts) continue;
            out.push({
                msg: "call to undeclared function '" + t.val + "()' - declare it: "
                    + "abstract \"" + low + "\" -> act=\"...\" ; or " + low + ":act=\"...\":name=\"" + low
                    + "\"; or add the word to the base",
                tok: t
            });
        }
        return { errs: out, used: used };
    }

    function lineStarts(text) {
        var starts = [];
        var pos = 0;
        while (pos <= text.length) {
            starts.push(pos);
            var nl = text.indexOf("\n", pos);
            if (nl === -1) break;
            pos = nl + 1;
        }
        return starts;
    }

    function tokenCol(text, starts, t) {
        var s = t.line - 1;
        var start = s >= 0 && s < starts.length ? starts[s] : 0;
        return t.pos - start + 1;
    }

    function tokenLen(t) {
        if (t.kind === "str") return t.val.length + 2;
        if (t.kind === "custom") return Math.min(t.val.length + 2, 40) || 1;
        return (t.val && t.val.length) ? t.val.length : 1;
    }

    function validate(text, opts) {
        opts = opts || {};
        var out = [];
        var markers = [];

        var cat = new Category();
        var dictName = opts.dictName || "dictionary_sorted_by_type.txt";
        var nAliases = cat.load(opts.dictText || "");
        out.push("# dictionary: " + dictName + " (" + nAliases + " aliases; cats: "
            + cat.catNames.join(", ") + ")");

        var protos = loadBase(opts.protosText || "");
        var blueprints = loadBase(opts.blueprintsText || "");
        var protoCount = Object.keys(protos).length;
        var bpCount = Object.keys(blueprints).length;
        out.push("# base: protos=" + protoCount + " blueprints=" + bpCount);
        out.push("# source: " + (opts.srcName || "<line>"));

        var starts = lineStarts(text);
        function mkMarker(t, severity, message) {
            var col = tokenCol(text, starts, t);
            markers.push({
                startLineNumber: t.line,
                startColumn: col,
                endLineNumber: t.line,
                endColumn: col + Math.max(1, tokenLen(t)),
                message: message,
                severity: severity
            });
        }

        var toks = tokenize(text);
        var errors = checkStructure(toks);
        var ud = scanUserdefs(toks);
        var userdefs = ud.userdefs, abody = ud.abody;
        Object.keys(userdefs).forEach(function (nm) {
            out.push("  [user " + userdefs[nm] + "] " + nm + " (declared)");
        });
        var acts = scanActs(toks);
        Object.keys(acts).forEach(function (nm) {
            out.push("  [act] " + nm + "  (" + acts[nm] + ")");
        });
        var rerrs = ruleChecks(toks, text, cat);
        var proto_ids = Object.create(null);
        Object.keys(protos).forEach(function (k) { proto_ids[k] = 1; });
        var bp_ids = Object.create(null);
        Object.keys(blueprints).forEach(function (k) { bp_ids[k] = 1; });
        var ac = assetChecks(toks, text, cat, userdefs, acts, abody, proto_ids, bp_ids);
        var aerrs = ac.errs, used = ac.used;

        var base_errs = [];
        var visited = Object.create(null);
        function check_base(name) {
            if (name in visited) return 0;
            visited[name] = 1;
            var block = protos[name] !== undefined ? protos[name]
                : (blueprints[name] !== undefined ? blueprints[name] : null);
            if (block === null) return 0;
            var kind = name in proto_ids ? "proto" : "blueprint";
            var btoks = tokenize(block);
            var berr = checkStructure(btoks);
            var bud = scanUserdefs(btoks);
            var bact = scanActs(btoks);
            var br = ruleChecks(btoks, block, cat);
            var be = assetChecks(btoks, block, cat, bud.userdefs, bact, bud.abody, proto_ids, bp_ids);
            var ne = berr.length + br.length + be.errs.length
                + btoks.filter(function (x) { return x.issue === "error"; }).length;
            berr.forEach(function (e) {
                base_errs.push("  E [" + kind + " " + name + "] unbalanced " + pyRepr(e[1]));
            });
            br.forEach(function (m) {
                base_errs.push("  E [" + kind + " " + name + "] " + m.msg);
            });
            be.errs.forEach(function (m) {
                base_errs.push("  E [" + kind + " " + name + "] " + m.msg);
            });
            be.used.forEach(check_base);
            return ne;
        }

        var used_base = 0;
        used.forEach(function (u) { used_base += check_base(u); });

        var prev = null;
        for (var ti = 0; ti < toks.length; ti++) {
            var t = toks[ti];
            if (t.issue === "error") {
                if (t.kind === "str") {
                    out.push("  E line " + t.line + " pos " + t.pos + ": unterminated string literal");
                    mkMarker(t, 8, "unterminated string literal");
                } else if (t.kind === "custom") {
                    out.push("  E line " + t.line + " pos " + t.pos + ": unbalanced custom block { ...");
                    mkMarker(t, 8, "unbalanced custom block { ...");
                } else if (t.kind === "hcomment") {
                    out.push("  E line " + t.line + " pos " + t.pos + ": unterminated block comment /*");
                    mkMarker(t, 8, "unterminated block comment /*");
                } else {
                    out.push("  E line " + t.line + " pos " + t.pos + ": unexpected char " + pyRepr(t.val));
                    mkMarker(t, 8, "unexpected char " + pyRepr(t.val));
                }
                continue;
            }
            if (t.kind === "hcomment") continue;
            if (t.kind === "custom") {
                var snippet = t.val.split(/\s+/).filter(Boolean).join(" ");
                out.push("  [AI custom] { " + snippet.slice(0, 80) + " }");
                continue;
            }
            if (t.kind === "word") {
                var sl = t.val.toLowerCase();
                var c = cat.cat_of(t.val);
                var inbody = abody.has(t.line + ":" + t.pos);
                var ukind = userdefs[sl];
                if (inbody) {
                    out.push("  [abstract body] " + t.val);
                } else if (c && (sl in DECL)) {
                    out.push("  [declaration] " + t.val);
                } else if (c) {
                    out.push("  [" + c + "] " + t.val);
                } else if (ukind) {
                    out.push("  [" + ukind + "] " + t.val);
                } else if (sl === "as") {
                    t.issue = "grammar";
                    out.push("  [grammar] as");
                    mkMarker(t, 4, "keyword 'as' is reserved for aliases");
                } else if (prev !== null && (prev.kind === "op" || prev.kind === "punct") && prev.val === "=") {
                    t.issue = "warn:" + t.val;
                    out.push("  [?] " + t.val + "   <- proper name: wrap value in quotes, e.g. name=\"" + t.val + "\"");
                    mkMarker(t, 4, "proper name: wrap value in quotes, e.g. name=\"" + t.val + "\"");
                } else {
                    t.issue = "warn:" + t.val;
                    out.push("  [?] " + t.val + "   <- not in dictionary (extension/property?)");
                    mkMarker(t, 4, "not in dictionary (extension/property?)");
                }
            }
            prev = t;
        }
        errors.forEach(function (e) {
            out.push("  E line " + e[0].line + " pos " + e[0].pos + ": unbalanced " + pyRepr(e[1]));
            mkMarker(e[0], 8, "unbalanced " + pyRepr(e[1]));
        });
        rerrs.forEach(function (m) {
            out.push("  E rule: " + m.msg);
            mkMarker(m.tok, 8, m.msg);
        });
        aerrs.forEach(function (m) {
            out.push("  E asset: " + m.msg);
            mkMarker(m.tok, 8, m.msg);
        });
        base_errs.forEach(function (m) { out.push(m); });
        if (used.length) {
            var uuniq = Array.from(new Set(used)).sort();
            out.push("  [use] reads base entries: " + uuniq.join(", "));
        }

        var nerr = toks.filter(function (t) { return t.issue === "error"; }).length
            + errors.length + rerrs.length + aerrs.length + used_base;
        var nwarn = toks.filter(function (t) { return t.issue && t.issue.indexOf("warn:") === 0; }).length;
        var verdict = nerr ? "FAIL" : "PASS";
        out.push("# verdict: " + verdict + " (errors=" + nerr + " warnings=" + nwarn + ")");

        return {
            out: out,
            markers: markers,
            nerr: nerr,
            nwarn: nwarn,
            verdict: verdict,
            usedBase: used_base,
            baseErrs: base_errs,
            cat: cat,
            acts: acts
        };
    }

    return {
        tokenize: tokenize,
        Category: Category,
        checkStructure: checkStructure,
        scanUserdefs: scanUserdefs,
        ruleChecks: ruleChecks,
        scanActs: scanActs,
        assetChecks: assetChecks,
        loadBase: loadBase,
        validate: validate
    };
});
