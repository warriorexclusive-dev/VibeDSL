# -*- coding: utf-8 -*-
"""the proxy in front of Ollama, and the log of everything that passes

A proxy and not a library, on purpose. Ollama has an OpenAI-shaped layer at /v1/
and a client could talk to it directly, and then nothing would be written down:
a model can be asked something and there is no record that it was. The log is
the reason this file exists.

    client -> proxy :11435 -> ollama :11434
               |
               +-- log/NNNN.jsonl, one object per exchange

Three things it deliberately does not do, each because the alternative is a
worse kind of wrong:

    it does not buffer        a stream that is collected before it is written
                              back is not a stream, and the first token is the
                              whole point of asking for one
    it does not translate     /api/chat and /v1/chat/completions carry different
                              fields, and a translation drops the ones the other
                              dialect has, and the dropped ones are the log
    it edits nothing silently settings in config/models.json ARE applied to the
                              request, and every line that was added is written
                              to the log under "added", beside what the client
                              sent. An edit that is in the log is a thing to
                              read; an edit that is not is a thing to guess about

Usage:
    py -3 tools/ollama_proxy.py [--port N] [--ollama URL] [--config]
"""
import argparse
import io
import json
import os
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
VS = os.path.dirname(HERE)
CONFIG = os.path.join(VS, "config", "proxy.json")
LOGDIR = os.path.join(VS, "log")

# defaults, and the file above them. A port written into the code is a port
# that has to be edited in the code, and the second machine is where that gets
# discovered. So the numbers live in config/proxy.json and the code only knows
# what to do when the file is not there.
DEFAULTS = {
    "host": "127.0.0.1",
    "port": 11435,
    "ollama": "http://127.0.0.1:11434",
    "log_dir": "log",
}


def load_config():
    """config/proxy.json over the defaults, and a missing file is not an error

    A machine with no config gets the defaults, which are the conventions and
    are right on a fresh Ollama. A file with a key missing gets the default for
    that key alone, so a half-written file is half-configured and not broken.
    """
    cfg = dict(DEFAULTS)
    try:
        with io.open(CONFIG, encoding="utf-8") as fh:
            given = json.load(fh)
    except (IOError, OSError, ValueError):
        return cfg
    for k, v in given.items():
        cfg[k] = v
    # a relative log_dir is relative to the config's folder, not to the shell
    d = cfg.get("log_dir") or DEFAULTS["log_dir"]
    if not os.path.isabs(d):
        cfg["log_dir"] = os.path.normpath(os.path.join(VS, d))
    return cfg


MODELS = os.path.join(VS, "config", "models.json")
RULES = os.path.join(VS, "rules")


def load_models():
    """per-model settings, and a missing file is not an error

    A model that is not in the file runs on exactly what the client sent. That
    is the important half: a config that only names some of the models cannot
    change the behaviour of the rest, so adding a model to Ollama does not
    silently bring it under a rule nobody wrote for it.
    """
    try:
        with io.open(MODELS, encoding="utf-8") as fh:
            return (json.load(fh) or {}).get("models") or {}
    except (IOError, OSError, ValueError):
        return {}


def read_rule(name):
    """the text of a rule file, and the file is the rule

    A rule written into the config cannot be read without a JSON parser, cannot
    be diffed, and has no history. The point of editing rules per model is the
    file, so the config names the file and this reads it.

    Two forms are accepted, and the first that exists wins: relative to
    VSCode/ ("rules/x.md") and relative to VSCode/rules/ ("x.md"). The first is
    what the config file shows, the second is what a person types in a hurry,
    and a path that only works in one spelling is a path that fails once and the
    failure is a silent one, because a missing rule leaves the model with no
    rule and the answer is merely wrong.
    """
    if not name:
        return None
    cands = [name if os.path.isabs(name) else os.path.join(VS, name),
             os.path.join(RULES, name)]
    for p in cands:
        try:
            with io.open(p, encoding="utf-8") as fh:
                return fh.read()
        except (IOError, OSError):
            continue
    return None


def apply_model(body, table):
    """add what the config says, and return what was added

    Returns the lines it added, and an empty list when it added nothing. The
    caller writes that list to the log beside the request the client sent, so
    the two can be compared and a wrong answer can be traced to a setting here
    rather than blamed on the model.
    """
    if not isinstance(body, dict):
        return body, []
    model = body.get("model")
    cfg = table.get(model)
    if not isinstance(cfg, dict):
        return body, []

    added = []
    out = dict(body)

    sysfile = cfg.get("system")
    if sysfile:
        text = read_rule(sysfile)
        if text is None:
            added.append({"system": "НЕ ПРОЧИТАН %s" % sysfile})
        else:
            msgs = list(out.get("messages") or [])
            if not any(m.get("role") == "system" for m in msgs
                       if isinstance(m, dict)):
                msgs.insert(0, {"role": "system", "content": text})
                out["messages"] = msgs
                added.append({"system": sysfile, "chars": len(text)})

    opts = dict(out.get("options") or {})
    for k in ("temperature", "num_ctx", "top_p", "top_k", "num_predict",
              "repeat_penalty"):
        if k in cfg and k not in opts:
            opts[k] = cfg[k]
            added.append({"options.%s" % k: cfg[k]})
    if added:
        out["options"] = opts
    return out, added

# what must not move: the panel drives the proxy, the proxy moves nothing
NEVER = ["englang.embedding", "specs/compiler.vibe", "compiled/compiler.glyphs",
         "RULES.md", "AGENT_RULES.md"]

_lock = threading.Lock()
_seq = 0

# /v1/chat/completions carries the model in the body, the native /api/* puts it
# in the path, and a log line with no model in it cannot be matched to anything.
MODEL_IN_PATH = re.compile(r"^/api/(chat|generate)$")


def next_name():
    """one file per process start, so two runs do not write over each other"""
    global _seq
    with _lock:
        _seq += 1
        n = _seq
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return os.path.join(LOGDIR, "%s-%04d.jsonl" % (stamp, n))


def write_line(path, obj):
    with _lock:
        with io.open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


def model_of(path, body):
    m = MODEL_IN_PATH.match(path)
    if m and body is None:
        return None
    if isinstance(body, dict):
        return body.get("model")
    return None


def reassemble(chunks, is_stream):
    """the answer as one piece of text, for the log only

    The client gets the bytes untouched and in order. This copy exists so the
    log can be grepped, and it has to end up as text in every case, because a
    log where the answer is sometimes text and sometimes a JSON string is a log
    that cannot be read the same way twice.

    Four shapes, because four dialects come through here:
        a streamed native answer    pieces under message.content
        a whole native answer       one object, message.content
        a streamed OpenAI answer    pieces under choices[].delta.content
        a whole OpenAI answer       one object, choices[].message.content
        and an answer that is none  of them, which stays as it arrived
    """
    text = "".join(chunks)
    if not text.strip():
        return ""
    out = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if not line.startswith("{"):
            out.append(line)
            continue
        try:
            o = json.loads(line)
        except ValueError:
            out.append(line)
            continue
        piece = None
        d = o.get("delta")
        if isinstance(d, dict):
            piece = d.get("content")
        if piece is None:
            m = o.get("message")
            if isinstance(m, dict):
                piece = m.get("content")
        if piece is None:
            ch = o.get("choices")
            if isinstance(ch, list) and ch:
                one = ch[0]
                if isinstance(one, dict):
                    d2 = one.get("delta")
                    if isinstance(d2, dict):
                        piece = d2.get("content")
                    if piece is None:
                        m2 = one.get("message")
                        if isinstance(m2, dict):
                            piece = m2.get("content")
        if piece is None:
            piece = o.get("response")
        if piece:
            out.append(piece)
    return "".join(out) if out else text


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "vibe-proxy/1.0"
    ollama = "http://127.0.0.1:11434"
    logpath = None
    models = {}
    mtime = None

    def log_message(self, fmt, *args):
        """nothing on stderr: the log is the log, and stdout is the panel's"""
        return

    def _read_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return b""
        return self.rfile.read(n)

    def _body_json(self, raw):
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    def _forward(self, method):
        # The config is re-read when its time changes, and not otherwise. A
        # panel that edits a rule has to take effect without a restart, and a
        # file read on every request would be a file read on every request for
        # a file that has not moved.
        try:
            m = os.path.getmtime(MODELS)
        except OSError:
            m = None
        if m != self.mtime:
            self.mtime = m
            self.models = load_models()

        raw = self._read_body()
        body = self._body_json(raw)
        # what the client sent, kept before anything is added, because the log
        # has to show both or the added lines cannot be told from the sent ones
        sent = body
        added = []
        headers = {}
        cth = self.headers.get("Content-Type")
        if cth:
            headers["Content-Type"] = cth
        if isinstance(body, dict) and body.get("model"):
            body, added = apply_model(body, self.models)
            if added:
                raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
                headers["Content-Type"] = "application/json; charset=utf-8"
        path = self.path
        url = self.ollama.rstrip("/") + path
        auth = self.headers.get("Authorization")
        if auth:
            headers["Authorization"] = auth

        started = time.time()
        first = [None]
        chunks = []
        status = [0]
        is_stream = bool(isinstance(body, dict) and body.get("stream"))

        try:
            up = requests.request(method, url, data=raw if raw else None,
                                  headers=headers, stream=True, timeout=600)
            status[0] = up.status_code
            ct_out = up.headers.get("Content-Type", "application/json")
            # Two shapes, and mixing them is what breaks a client. A stream has
            # no length to declare, so it is written as chunks and the client is
            # told chunked. A non-stream has a length, and when that length is
            # passed on the body must be written as it is, with no chunk frame
            # around it: declaring a length and then wrapping the body in a
            # frame gives the client a length it does not match, and the answer
            # arrives as one line of garbage.
            self.send_response(up.status_code)
            self.send_header("Content-Type", ct_out)
            chunked = is_stream or not up.headers.get("Content-Length")
            if chunked:
                self.send_header("Transfer-Encoding", "chunked")
            else:
                self.send_header("Content-Length", up.headers["Content-Length"])
            self.end_headers()

            for piece in up.iter_content(chunk_size=None):
                if not piece:
                    continue
                if first[0] is None:
                    first[0] = time.time() - started
                chunks.append(piece.decode("utf-8", "replace"))
                if chunked:
                    self.wfile.write(b"%x\r\n" % len(piece) + piece + b"\r\n")
                else:
                    self.wfile.write(piece)
                self.wfile.flush()
            if chunked:
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
        except Exception as e:
            note = {"error": str(e)}
            payload = json.dumps(note).encode("utf-8")
            try:
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception:
                pass
            chunks = [json.dumps(note)]
            status[0] = 502
        finally:
            try:
                up.close()
            except Exception:
                pass

        done = time.time() - started
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "method": method,
            "path": path,
            "model": model_of(path, body),
            "status": status[0],
            "stream": is_stream,
            "ttfb_ms": round((first[0] or 0) * 1000, 1),
            "total_ms": round(done * 1000, 1),
            # sent is what arrived, req is what went on, and added is the
            # difference. One of the three alone cannot answer "why did the
            # model say that", and that is the only question the log is for.
            "sent": sent,
            "req": body,
            "added": added,
            "res": reassemble(chunks, is_stream),
        }
        write_line(self.logpath, entry)

    def do_GET(self):
        self._forward("GET")

    def do_POST(self):
        self._forward("POST")

    def do_DELETE(self):
        self._forward("DELETE")


def main():
    cfg = load_config()
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=cfg["host"])
    ap.add_argument("--port", type=int, default=int(cfg["port"]))
    ap.add_argument("--ollama", default=cfg["ollama"])
    ap.add_argument("--config", action="store_true",
                    help="print the settings that are in force and exit")
    a = ap.parse_args()

    global LOGDIR
    LOGDIR = cfg["log_dir"]
    if not os.path.isdir(LOGDIR):
        os.makedirs(LOGDIR)
    Handler.ollama = a.ollama
    Handler.logpath = next_name()

    if a.config:
        print("  НАСТРОЙКИ, КОТОРЫЕ ДЕЙСТВУЮТ")
        print("    host    %s" % a.host)
        print("    port    %d" % a.port)
        print("    ollama  %s" % a.ollama)
        print("    log     %s" % LOGDIR)
        print("    config  %s%s" % (CONFIG, "" if os.path.isfile(CONFIG)
                                   else "   НЕТ ФАЙЛА, ВЗЯТЫ ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ"))
        print("    лог     %s" % Handler.logpath)
        return 0

    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print("  ПРОКСИ %s:%d -> %s" % (a.host, a.port, a.ollama))
    print("    лог  %s" % Handler.logpath)
    print("    клиент: base_url = http://%s:%d" % (a.host, a.port))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
