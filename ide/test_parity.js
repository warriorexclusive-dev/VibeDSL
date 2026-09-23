/* Parity test: JS validator output must equal Python CLI output.
   node ide/test_parity.js            (runs everything)
   node ide/test_parity.js syntax     (single case)                       */
"use strict";
const spawnSync = require("child_process").spawnSync;
const path = require("path");
const fs = require("fs");

const ROOT = path.join(__dirname, "..");
const V = require("./validator.js");
const DATA = require("./data.js");
const PY = path.join(ROOT, "validator", "validator.py");

function jsOut(text, srcName) {
    return V.validate(text, {
        dictText: DATA.dict,
        dictName: DATA.dictName,
        protosText: DATA.protos,
        blueprintsText: DATA.blueprints,
        syntaxText: DATA.syntax,
        srcName: srcName
    }).out.join("\n");
}

function pyOut(args) {
    const r = spawnSync("py", ["-X", "utf8", PY].concat(args), {
        cwd: ROOT, encoding: "utf8", maxBuffer: 64 * 1024 * 1024
    });
    if (r.error) throw r.error;
    return r.stdout;
}

function norm(s) {
    return String(s).replace(/\r\n/g, "\n").split("\n").filter((l, i, a) => !(i === a.length - 1 && l === ""));
}

const cases = [];
function file(name, rel) { cases.push({ name: name, args: [rel], rel: rel }); }
function line(name, text) { cases.push({ name: name, args: [text], rel: null, text: text }); }

file("syntax.txt", "DATA\\syntax.txt");
file("protos.txt", "DATA\\protos.txt");
file("blueprints.txt", "DATA\\blueprints.txt");
file("dictionary.txt", "DATA\\dictionary.txt");
file("demo_act.vibe", path.join(process.env.TEMP, "opencode", "demo_act.vibe"));

line("neg: undeclared call", "get_me_all()");
line("neg: use(not_a_thing)", "use(not_a_thing)");
line("broken evt line 1", "evt:notify -> show");
line("ok    evt line 1", "evt:notify -> show()");
line("broken evt line 2", 'event:onCreate -> load view name="main"');
line("ok    evt line 2", 'event:onCreate -> load(view name="main")');
line("load ok", 'load(view name="main")');
line("srch exm", 'srch(in) type="RAG"');
line("multivec", 'crt(model:-[3]> type="human")  // - критический узел');
line("multivec block",
     '-[3]> [a,b,c]:[d,e,f]:[x,y,z]:  : selects one element -> one common logic\n'
     + '-[3]> [a,b,c]:[d,e,f]:[x,y,z]<>: paths depend on the selection\n'
     + '     a,d,z -> val a = d = z\n'
     + '     b,e,y -> val b = y / e   // / = division\n'
     + '     ->  show()               // default: every selection except the two above');
line("abstract act decl", 'abstract "open_file" -> act="open file by name"\nopen_file("main.txt")');
line("entity act decl", 'file:act="grant access to user":name="access"\nfile:access(context:user)');

const only = process.argv[2];
let failed = 0;
for (const c of cases) {
    if (only && c.name !== only) continue;
    const srcName = c.rel !== null ? c.rel : "<line>";
    const a = norm(pyOut(c.args));
    const b = norm(jsOut(c.text !== undefined ? c.text
    : fs.readFileSync(path.isAbsolute(c.rel) ? c.rel : path.join(ROOT, c.rel), "utf8"), srcName));
    let ok = a.length === b.length;
    let firstDiff = -1;
    if (ok) {
        for (let i = 0; i < a.length; i++) {
            if (a[i] !== b[i]) { ok = false; firstDiff = i; break; }
        }
    } else {
        firstDiff = 0;
    }
    if (!ok) {
        failed++;
        console.log("FAIL  " + c.name + "  (py " + a.length + " lines / js " + b.length + " lines)");
        const i = firstDiff;
        console.log("  py: " + JSON.stringify(a[i]));
        console.log("  js: " + JSON.stringify(b[i]));
    } else {
        // echo a one-line verdict summary to show both agreed
        const verdictLine = a[a.length - 1];
        console.log("OK    " + c.name + "  " + verdictLine.replace("# verdict: ", ""));
    }
}
console.log(failed === 0 ? "ALL CASES PASS" : failed + " FAILED");
process.exit(failed ? 1 : 0);