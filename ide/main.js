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
                [/(<>:|<->|&->|::point:|::|->|<-|<>|<=|>=|!=|==|\+=|-=|:\?|:=|\|\||&&|\|>)/, "operator"],
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

    function validateNow() {
        var res = VibeDSLValidator.validate(model.getValue(), {
            dictText: DATA.dict,
            dictName: DATA.dictName,
            protosText: DATA.protos,
            blueprintsText: DATA.blueprints,
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
    model.onDidChangeContent(function () {
        clearTimeout(timer);
        timer = setTimeout(validateNow, 250);
    });

    document.getElementById("openBtn").addEventListener("click", function () {
        document.getElementById("fileInput").click();
    });
    document.getElementById("fileInput").addEventListener("change", function (e) {
        var file = e.target.files[0];
        if (!file) return;
        var reader = new FileReader();
        reader.onload = function () {
            model.setValue(String(reader.result));
            editor.focus();
        };
        reader.readAsText(file);
        e.target.value = "";
    });
    document.getElementById("saveBtn").addEventListener("click", function () {
        var blob = new Blob([model.getValue()], { type: "text/plain" });
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "edit.vibe";
        a.click();
        URL.revokeObjectURL(a.href);
    });
    document.getElementById("demoBtn").addEventListener("click", function () {
        model.setValue(DATA.demo);
    });

    var panel = document.getElementById("panel");
    var helpText = document.getElementById("helpText");
    function showHelp(name) {
        helpText.textContent = name === "dict" ? DATA.dict
                             : name === "syntax" ? (DATA.syntax || "") : "";
        document.getElementById("dictBtn").className = name === "dict" ? "active" : "";
        document.getElementById("syntaxBtn").className = name === "syntax" ? "active" : "";
    }
    document.getElementById("helpBtn").addEventListener("click", function () {
        var open = panel.classList.toggle("open");
        if (open && !helpText.textContent) showHelp("dict");
        editor.layout();
    });
    document.getElementById("dictBtn").addEventListener("click", function () { showHelp("dict"); });
    document.getElementById("syntaxBtn").addEventListener("click", function () { showHelp("syntax"); });

    validateNow();
    editor.focus();
    }
});
