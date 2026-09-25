require.config({
    paths: {
        vs: location.protocol === "file:"
            ? "../temp/package/min/vs"
            : location.protocol + "//" + location.host + "/temp/package/min/vs"
    }
});

require(["vs/editor/editor.main"], function () {
    "use strict";
    try {
        init();
    } catch (e) {
        var sb = document.getElementById("status");
        if (sb) {
            sb.textContent = "init error: " + (e && e.message ? e.message : e);
            sb.className = "fail";
        }
        var lg = document.getElementById("log");
        if (lg) lg.textContent = String(e && e.stack ? e.stack : e);
        throw e;
    }
    function init() {
    var DATA = window.VIBEDSL_DATA;

    monaco.languages.register({ id: "vibedsl", extensions: [".vibe", ".txt"] });
    monaco.languages.setLanguageConfiguration("vibedsl", {
        comments: { lineComment: "//", blockComment: ["/*", "*/"] },
        brackets: [["(", ")"], ["[", "]"], ["{", "}"]],
        autoClosingPairs: [
            { open: "(", close: ")" }, { open: "[", close: "]" }, { open: "{", close: "}" },
            { open: "\"", close: "\"" }
        ]
    });
    monaco.languages.setMonarchTokensProvider("vibedsl", {
        defaultToken: "",
        tokenPostfix: ".vibedsl",
        keywords: ["fun", "func", "function", "abstract", "alias", "as", "use",
                   "type", "act", "name", "par", "desc", "id", "ret", "halt"],
        tokenizer: {
            root: [
                [/\/\/.*$/, "comment"],
                [/#.*$/, "comment"],
                [/\/\*/, "comment", "@comment"],
                [/\*->/, "keyword"],
                [/-\[[^\n\]]*\]>/, "operator"],
                [/(<>:|<->|&->|::point:|::|->|<-|<>|<=|>=|==|:\?|:=|\|\||&&)/, "operator"],
                [/[:;,(){}\[\]@~]/, "delimiter"],
                [/"([^"\\]|\\.)*"/, "string"],
                [/"[^"\\]*$/, "string.invalid"],
                [/\d+(\.\d+)?/, "number"],
                [/[a-zA-Z_][\w.]*/, {
                    cases: {
                        "@keywords": "keyword",
                        "@default": "identifier"
                    }
                }]
            ],
            comment: [
                [/[^/*]+/, "comment"],
                [/\*\//, "comment", "@pop"],
                [/[/*]/, "comment"]
            ]
        }
    });

    var model = monaco.editor.createModel(DATA.demo, "vibedsl");
    var editor = monaco.editor.create(document.getElementById("editor"), {
        model: model,
        theme: "vs-dark",
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 14,
        renderWhitespace: "selection",
        scrollBeyondLastLine: false
    });

    var statusEl = document.getElementById("status");
    var logEl = document.getElementById("log");
    var problemsEl = document.getElementById("problems");
    var nameInput = document.getElementById("nameInput");
    var savedEl = document.getElementById("saved");

    var draftPrefix = "vibedsl.draft:";
    var activeKey = "vibedsl.active";
    var httpProto = location.protocol.indexOf("http") === 0;

    function currentName() {
        var n = nameInput.value.trim();
        if (!n) return "edit.vibe";
        if (n.indexOf(".") === -1) return n + ".vibe";
        return n;
    }

    function storeLocal(key, val) {
        try { localStorage.setItem(key, val); } catch (e) { /* private mode */ }
    }
    function readLocal(key) {
        try { return localStorage.getItem(key); } catch (e) { return null; }
    }
    function currentText() { return model.getValue(); }

    function saveDraftLocal() {
        var n = currentName();
        storeLocal(activeKey, n);
        storeLocal(draftPrefix + n, currentText());
    }

    function setSavedLabel(msg, cls) {
        savedEl.textContent = msg;
        savedEl.style.color = cls === "fail" ? "#f48771" : "#6a9955";
    }

    function saveDraftServer(quiet) {
        if (!httpProto) return;
        var body = JSON.stringify({ name: currentName(), text: currentText() });
        fetch("API/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: body
        }).then(function (r) { return r.json(); })
        .then(function (j) {
            if (j && j.ok) {
                var t = new Date();
                var hh = ("0" + t.getHours()).slice(-2);
                var mm = ("0" + t.getMinutes()).slice(-2);
                var ss = ("0" + t.getSeconds()).slice(-2);
                setSavedLabel("saved " + hh + ":" + mm + ":" + ss + "  " + j.file, "pass");
            } else if (!quiet) {
                setSavedLabel(j && j.error ? "save error: " + j.error : "save server error", "fail");
            }
        })
        .catch(function () {
            if (!quiet) setSavedLabel("no autosave server (router down?)", "fail");
        });
    }

    function restoreDraft() {
        var n = readLocal(activeKey);
        var draft = n ? readLocal(draftPrefix + n) : null;
        if (draft !== null && draft !== DATA.demo) {
            model.setValue(draft);
            nameInput.value = n;
            logEl.textContent = "restored autosaved draft '" + n + "' (refresh keeps your text)\n";
            setSavedLabel("draft restored", "pass");
        }
    }

    function validateNow() {
        var res = VibeDSLValidator.validate(model.getValue(), {
            dictText: DATA.dict,
            dictName: DATA.dictName,
            protosText: DATA.protos,
            blueprintsText: DATA.blueprints,
            syntaxText: DATA.syntax,
            srcName: "<editor>"
        });
        monaco.editor.setModelMarkers(model, "vibedsl", res.markers);
        statusEl.textContent = res.verdict + "  (errors=" + res.nerr + " warnings=" + res.nwarn + ")";
        statusEl.className = res.verdict === "PASS" ? "pass" : "fail";
        logEl.textContent = res.out.join("\n");

        problemsEl.innerHTML = "";
        res.markers
            .filter(function (m) { return m.severity === 8; })
            .forEach(function (m) {
                var row = document.createElement("div");
                row.className = "problem";
                row.textContent = m.startLineNumber + ":" + m.startColumn + "  " + m.message;
                row.addEventListener("click", function () {
                    editor.setPosition({ lineNumber: m.startLineNumber, column: m.startColumn });
                    editor.revealLineInCenter(m.startLineNumber);
                    editor.focus();
                });
                problemsEl.appendChild(row);
            });
        if (!problemsEl.children.length) {
            var ok = document.createElement("div");
            ok.className = "ok";
            ok.textContent = "no errors";
            problemsEl.appendChild(ok);
        }
    }

    var timer = null;
    var draftTimer = null;
    model.onDidChangeContent(function () {
        clearTimeout(timer);
        timer = setTimeout(validateNow, 250);
        clearTimeout(draftTimer);
        draftTimer = setTimeout(saveDraftLocal, 400);
        setSavedLabel("editing…", "pass");
    });

    setInterval(function () { saveDraftServer(true); }, 10000);
    window.addEventListener("beforeunload", function () {
        saveDraftLocal();
        saveDraftServer(true);
    });
    document.addEventListener("visibilitychange", function () {
        if (document.visibilityState === "hidden") {
            saveDraftLocal();
            saveDraftServer(true);
        }
    });

    document.getElementById("openBtn").addEventListener("click", function () {
        document.getElementById("fileInput").click();
    });
    document.getElementById("fileInput").addEventListener("change", function (e) {
        var file = e.target.files[0];
        if (!file) return;
        var reader = new FileReader();
        reader.onload = function () {
            nameInput.value = file.name;
            model.setValue(String(reader.result));
            saveDraftLocal();
            saveDraftServer(true);
            editor.focus();
        };
        reader.readAsText(file);
        e.target.value = "";
    });
    document.getElementById("saveBtn").addEventListener("click", function () {
        var n = currentName();
        nameInput.value = n;
        var blob = new Blob([model.getValue()], { type: "text/plain" });
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = n;
        a.click();
        URL.revokeObjectURL(a.href);
        saveDraftLocal();
        saveDraftServer(false);
    });
    document.getElementById("demoBtn").addEventListener("click", function () {
        model.setValue(DATA.demo);
    });

    var panel = document.getElementById("panel");
    var helpText = document.getElementById("helpText");
    var REFS = {
        action: DATA.dictAction || "",
        mapping: DATA.dictMapping || "",
        operators: DATA.dictOperators || "",
        abstracts: DATA.dictAbstracts || "",
        syntax: DATA.syntax || ""
    };
    var CHK_KEYS = ["action", "mapping", "operators", "abstracts", "syntax"];
    var CHK = {};
    function dictCheck(name) {
        if (CHK[name]) return CHK[name];
        CHK[name] = VibeDSLValidator.validate(REFS[name] || "", {
            dictText: DATA.dict,
            dictName: DATA.dictName,
            protosText: DATA.protos,
            blueprintsText: DATA.blueprints,
            syntaxText: DATA.syntax,
            srcName: "dict:" + name
        });
        return CHK[name];
    }
    function refButtons() {
        return Array.prototype.slice.call(document.querySelectorAll("#panelBtns .refBtn"));
    }
    var activeRef = "action";
    function showHelp(name) {
        activeRef = name;
        var head = [];
        if (CHK_KEYS.indexOf(name) !== -1) {
            var r = dictCheck(name);
            if (r.nerr) {
                head.push("---- dictionary check: FAIL (errors=" + r.nerr + ") ----");
                r.markers.forEach(function (m) {
                    head.push("  L" + m.startLineNumber + ": " + m.message);
                });
            } else {
                head.push("---- dictionary check: PASS (errors=0) ----");
            }
            head.push("-------------------------------------------");
        }
        helpText.textContent = (head.length ? head.join("\n") + "\n" : "") + (REFS[name] || "");
        refButtons().forEach(function (b) {
            b.className = b.getAttribute("data-ref") === name ? "refBtn active" : "refBtn";
        });
    }
    refButtons().forEach(function (b) {
        var dataRef = b.getAttribute("data-ref");
        if (CHK_KEYS.indexOf(dataRef) !== -1) {
            try {
                var chk = dictCheck(dataRef);
                var span = document.createElement("span");
                span.className = "chk " + (chk.nerr ? "fail" : "pass");
                span.textContent = chk.nerr ? "(" + chk.nerr + ")" : "(\u2713)";
                b.appendChild(span);
            } catch (e) { /* leave button plain */ }
        }
        b.addEventListener("click", function () { showHelp(b.getAttribute("data-ref")); });
    });
    document.getElementById("helpBtn").addEventListener("click", function () {
        var open = panel.classList.toggle("open");
        if (open && !helpText.textContent) showHelp(activeRef);
        editor.layout();
    });

    var dictModal = document.getElementById("dictModal");
    var addSection = document.getElementById("addSection");
    var addValue = document.getElementById("addValue");
    var addDesc = document.getElementById("addDesc");
    var addExm = document.getElementById("addExm");
    var addPreview = document.getElementById("addPreview");
    var addResult = document.getElementById("addResult");
    var KNOWN_ALIASES = null;
    try {
        KNOWN_ALIASES = VibeDSLValidator.entryAliases(DATA.dict);
    } catch (e) { KNOWN_ALIASES = new Set(); }

    function composePreview() {
        var v = addValue.value.trim(), d = addDesc.value.trim(), e = addExm.value.trim();
        if (!v && !d && !e) {
            addPreview.textContent = "(type the fields above)";
            return;
        }
        var lines = ["*-> " + v + " - " + d];
        if (e) lines.push("    -> exm: " + e);
        addPreview.textContent = lines.join("\n");
    }
    function setAddResult(msg, ok) {
        addResult.textContent = msg;
        addResult.className = ok ? "ok" : "err";
    }
    function openAddDict(section) {
        if (CHK_KEYS.indexOf(section) === -1 || section === "syntax") section = "action";
        addSection.value = section;
        addValue.value = "";
        addDesc.value = "";
        addExm.value = "";
        setAddResult("", true);
        composePreview();
        dictModal.classList.remove("hidden");
        addValue.focus();
    }
    function submitAdd() {
        var v = addValue.value.trim(), d = addDesc.value.trim(), e = addExm.value.trim();
        if (!v || !d) {
            setAddResult("value and description are required", false);
            return;
        }
        var parts = v.split(",");
        for (var i = 0; i < parts.length; i++) {
            var t = parts[i].trim().toLowerCase();
            if (t && KNOWN_ALIASES.has(t)) {
                setAddResult("alias already in dictionary: " + parts[i].trim(), false);
                return;
            }
        }
        setAddResult("saving\u2026", true);
        var body = JSON.stringify({ section: addSection.value, value: v, desc: d, exm: e });
        fetch("API/dict_add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: body
        }).then(function (r) { return r.json(); })
        .then(function (j) {
            if (j && j.ok) {
                storeLocal("vibedsl.addref", j.section || "action");
                var added = (j.value || v).split(",")[0].trim();
                setAddResult("added '" + added + "' to " + (j.section || "?") + " \u2014 reloading\u2026", true);
                setTimeout(function () { location.reload(); }, 400);
            } else {
                setAddResult("error: " + (j && j.error ? j.error : "server rejected the entry"), false);
            }
        })
        .catch(function () {
            setAddResult("error: server unreachable (router down?)", false);
        });
    }
    document.getElementById("addDictBtn").addEventListener("click", function () {
        openAddDict(activeRef);
    });
    document.getElementById("addCancel").addEventListener("click", function () {
        dictModal.classList.add("hidden");
    });
    document.getElementById("addOk").addEventListener("click", submitAdd);
    addValue.addEventListener("input", composePreview);
    addDesc.addEventListener("input", composePreview);
    addExm.addEventListener("input", composePreview);

    var afterAdd = readLocal("vibedsl.addref");
    if (afterAdd) {
        storeLocal("vibedsl.addref", "");
        panel.classList.add("open");
        showHelp(afterAdd);
        editor.layout();
    }

    restoreDraft();
    validateNow();
    editor.focus();
    }
});
