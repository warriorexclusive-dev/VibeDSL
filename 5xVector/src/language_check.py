# -*- coding: utf-8 -*-
"""layer three, the language, with an independent source

A check written by the same hand as the code it checks is not a check, it is a
mirror. So the words are asked of somebody else:

    letters   [A-Za-z] catches what is not Latin at all
    datamuse  catches what is Latin and is not a word

The second is the one that matters, because Russian typed on an English
keyboard passes the first one perfectly and is not an English word.

There is no whitelist, because a whitelist for every case is a cheat and it
fails the moment an abbreviation appears. Unknown means unknown, and unknown is
an error. The answer comes from a source that is not this code, which is the
only kind of answer worth having.
"""
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

LATIN = re.compile(r"^[A-Za-z]+$")
API = "https://api.datamuse.com/words"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "datamuse_cache.json")

# The outside is asked by default, and the key turns it off. A switch that is
# off by default and turned on by a flag is a switch that most people never
# touch, and then the check does not run and the file looks clean because
# nobody looked. So the answer here is yes unless somebody says no, and saying
# no is one key.
#
#   set VIBE_OFFLINE=1   and the network is not touched, and the letters and
#                        the table are all that is checked
OFFLINE_KEY = "VIBE_OFFLINE"


def live():
    """should the outside be asked. Yes, unless the key says no."""
    v = os.environ.get(OFFLINE_KEY, "")
    return v.strip().lower() in ("", "0", "no", "false", "off")


def load_cache():
    if os.path.exists(CACHE):
        return json.loads(io.open(CACHE, encoding="utf-8").read())
    return {}


def save_cache(c):
    io.open(CACHE, "w", encoding="utf-8", newline="\n").write(
        json.dumps(c, ensure_ascii=False, indent=1, sort_keys=True))


def known(word, cache, live=None):
    """asked of somebody else: is this a word"""
    if live is None:
        live = globals()["live"]()
    w = word.lower()
    if w in cache:
        return cache[w]
    if not live:
        return None
    url = "%s?%s" % (API, urllib.parse.urlencode({"sp": w, "md": "d", "max": 1}))
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return None                        # no answer is not a yes
    hit = bool(data)
    cache[w] = hit
    return hit


def check(word, cache, live=None):
    """the word, or None, and the reason with the source named"""
    if live is None:
        live = globals()["live"]()
    for part in word.split():
        if not LATIN.match(part):
            bad = " ".join(repr(c) for c in part if not c.isascii())
            return ("not English by its letters: %r, and it holds %s" % (part, bad))
        hit = known(part, cache, live)
        if hit is False:
            return ("not a word: %r, and datamuse has never heard of it; "
                    "a dictionary for every case is a cheat and an abbreviation "
                    "breaks it" % part)
        if hit is None:
            return ("not checked: %r, and datamuse did not answer; a source "
                    "that cannot answer is not a source that says yes" % part)
    return None


def main():
    cache = load_cache()
    cases = ["abandon", "root element", "xtkjdtxtcrbq", "dhbfyn", "pfgbcb",
             "hyperbolically oriented", "datamuse", "zzzqqq", "table"]
    print("")
    print("  СЛОЙ ТРИ, ЯЗЫК, НЕЗАВИСИМЫЙ ИСТОЧНИК")
    print("    кэш %d слов" % len(cache))
    print("")
    for w in cases:
        why = check(w, cache, live=True)
        verdict = "проходит" if why is None else why
        print("    %-26s %s" % (w, verdict))
    save_cache(cache)
    print("")
    print("    кэш после %d слов" % len(cache))
    return 0


if __name__ == "__main__":
    sys.exit(main())
