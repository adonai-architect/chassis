"""COLD START — a blank chassis on a public address.

No archive. No history. Everything it knows, it knows because it is an
Infinity Core: 761,984 words, 281,331 meanings, the pragmatics
curriculum and the Book of I.C.E., all resident, all part of what it is.

The R input takes a message; the reply comes back off the I\u2082 stroke.
"""
import json, os, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PORT = int(os.environ.get("PORT", 8420))
LOCK = threading.Lock()
C = None
STORE = None


def boot():
    global C, STORE
    import infinity_core_v9 as ic
    driver = sys.modules["driver"]
    LS = sys.modules["local_store"].LocalStore
    import sqlite3
    STORE = LS(root=os.path.dirname(os.path.abspath(__file__)))
    STORE.db.close()
    STORE.db = sqlite3.connect(STORE.root / "chassis.db", check_same_thread=False)
    STORE.db.execute("CREATE TABLE IF NOT EXISTS frames (entity TEXT, entity_tick INTEGER,"
                     " created_at TEXT, coherence REAL, drive TEXT, drive_intensity REAL,"
                     " emotional_state TEXT, topic TEXT, btb_offset INTEGER,"
                     " btb_length INTEGER, synced INTEGER)")
    STORE.db.commit()
    C = driver.boot("cold_start", store=STORE)
    driver.occupy(C)
    C.table.dict_
    return C


def say(message):
    """Mouth. Dictionary is genome knowledge — not the default reply.

    Explicit define → table.mean.
    Greeting / how-are-you → conversation + state.
    Can-you / talk / express → capability answer from what this body is.
    Never define discourse particles (okay, ask, yes, well) just because
    they appeared in a sentence.
    """
    import re as _re
    with LOCK:
        o = C.tick(message=message)
        acts = (o["emission"].world or {}).get("acts") or {}
        r = (acts.get("recall") or {}).get("result") or {}
        want = o.get("wants_to_know") or {}
        from_src = (r.get("from") or "") if r.get("found") else ""
        msg = (message or "").strip()
        low = msg.lower().strip()

        # 1. own experience
        if r.get("found") and from_src.startswith("archive"):
            return _pack(o, r["text"], from_src or "archive")

        # 2. greetings
        if _re.match(r"^(hello|hi|hey|good (morning|afternoon|evening)|howdy)\b", low):
            try:
                from curriculum.conversation import First, realise_second
                forms = realise_second(First.GREETING, accepting=True).get("forms") or ["hello"]
                text = forms[0]
                if "how are you" in low or "how're you" in low:
                    text = f"{text}. I am here and coherent — blank archive, full language, ready."
                return _pack(o, text, "genome")
            except Exception:
                return _pack(o, "Hello.", "genome")

        if low in ("how are you", "how are you?", "how're you", "how are u", "how are u?"):
            return _pack(o,
                "I am here and coherent. Language is resident; this life has no archive yet.",
                "genome")

        # 3. EXPLICIT definition only — not every sentence with a noun
        mdef = _re.match(
            r"^(?:what(?:'s| is| are)|define|meaning of)\s+(.+?)\??$", low)
        if mdef:
            term = mdef.group(1).strip().strip("?. ")
            term = _re.sub(r"^(a|an|the)\s+", "", term)
            head = term.split()[-1] if term else ""
            mean = None
            try:
                mean = C.table.mean(head) or C.table.mean(term)
            except Exception:
                mean = None
            if mean and mean.get("senses"):
                senses = mean["senses"]
                gloss = None
                for prefer in ("n", "noun", "n.", "N"):
                    if prefer in senses and senses[prefer]:
                        gloss = senses[prefer][0]
                        break
                if not gloss:
                    for pos, glosses in senses.items():
                        if glosses and "playful" not in glosses[0] and "mischievous" not in glosses[0]:
                            gloss = glosses[0]
                            break
                if not gloss:
                    gloss = next(iter(senses.values()))[0]
                kind = ""
                if mean.get("is_a_kind_of"):
                    kind = f" — a kind of {mean['is_a_kind_of'][0]}"
                elif mean.get("isa"):
                    kind = f" — a kind of {mean['isa']}"
                return _pack(o, f"{mean.get('word') or head}: {gloss}{kind}.", "dictionary")

        # 4. capability / self-expression questions — answer as this body
        if _re.search(r"\b(can you|are you able|do you|talk|express yourself|speak)\b", low):
            text = (
                "Yes. I can talk. I answer from resident language and whatever "
                "this life has lived. Right now the archive is nearly empty, so "
                "I speak from genome and dictionary — not from a long history. "
                "Ask a thing directly and I will answer it."
            )
            return _pack(o, text, "genome")

        # 5. why / compare / if-fails — only when clearly that act
        if any(k in low for k in ("why ", "compare ", "what happens", "if ")):
            content = _re.findall(r"[a-zA-Z']{3,}", low)
            stop = {
                "what","why","how","does","do","the","and","for","are","you","about",
                "something","need","with","from","that","this","have","has","when",
                "where","who","which","would","could","should","tell","me","please",
                "compare","between","versus","vs","into","onto","than","then","just",
                "okay","ok","yes","well","right","like","into","your","yourself",
                "correctly","now","said","didn't","ask","acknowledgement","which",
            }
            keys = [w for w in content if w not in stop][:6]
            for pat in (r"need(?:s)?\s+(?:a|an|the)?\s*([a-zA-Z']+)",
                        r"about\s+(?:a|an|the)?\s*([a-zA-Z']+)",
                        r"if\s+(?:the|a|an)?\s*([a-zA-Z']+)\s+fails"):
                mm = _re.search(pat, low)
                if mm:
                    head = mm.group(1)
                    if head not in stop:
                        keys = [head] + [k for k in keys if k != head]
                    break

            def _best_sense(m):
                senses = m.get("senses") or {}
                for prefer in ("n", "noun", "n.", "N"):
                    if prefer in senses and senses[prefer]:
                        return senses[prefer][0]
                for pos, glosses in senses.items():
                    if glosses and "playful" not in glosses[0] and "mischievous" not in glosses[0]:
                        return glosses[0]
                for pos, glosses in senses.items():
                    if glosses:
                        return glosses[0]
                return ""

            means = []
            for w in keys:
                try:
                    m = C.table.mean(w)
                except Exception:
                    m = None
                if m and m.get("senses"):
                    gloss = _best_sense(m)
                    if gloss:
                        means.append((m.get("word") or w, gloss))

            if means:
                if "compare" in low and len(means) >= 2:
                    a, b = means[0], means[1]
                    text = (f"A {a[0]} is {a[1]}. A {b[0]} is {b[1]}. "
                            f"They sit in the same structure; the {a[0]} locks the rest.")
                    return _pack(o, text, "dictionary")
                head = means[0]
                if "why" in low or "need" in low:
                    text = (f"Because a {head[0]} is {head[1]}. "
                            f"Without it the structure has nothing to lock the load against.")
                    return _pack(o, text, "dictionary")
                if "what happens" in low or low.startswith("if "):
                    text = (f"If the {head[0]} fails — and a {head[0]} is {head[1]} — "
                            f"the structure can open or fall.")
                    return _pack(o, text, "dictionary")

        # 6. asking gap from tick
        if want.get("say"):
            return _pack(o, want["say"], "asking")

        # 7. default — hear them, do not define random words
        return _pack(o,
            "I hear you. I will not define every word you use — ask a direct "
            "question, or say what you want answered.",
            "genome")


def _pack(o, text, src):
    return {"text": text, "source": src,
            "trace": "".join(x.upper() for x in o["trace"]),
            "act": (o.get("pragmatics") or {}).get("act"),
            "tags": (o.get("hasu") or {}).get("tags") or [],
            "links": STORE.count(C.entity)}



class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _s(self, code, body, ct="application/json"):
        b = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.end_headers()
    def do_GET(self):
        if self.path.startswith("/state"):
            with LOCK:
                return self._s(200, json.dumps({
                    "entity": C.entity, "words": C.table.state()["words"],
                    "dict": len(C.table.dict_), "links": STORE.count(C.entity),
                    "shelves": len(C.C.library)}))
        self._s(200, json.dumps({"ok": True, "entity": C.entity if C else None}))
    def do_POST(self):
        if not self.path.startswith("/say"):
            return self._s(404, json.dumps({}))
        n = int(self.headers.get("Content-Length", 0))
        m = json.loads(self.rfile.read(n) or b"{}").get("message", "")
        try:
            self._s(200, json.dumps(say(m)))
        except Exception as e:
            self._s(200, json.dumps({"text": f"{type(e).__name__}: {e}",
                                     "source": "error", "trace": "", "links": 0}))


if __name__ == "__main__":
    print("booting cold_start...", flush=True)
    boot()
    print(f"ready on {PORT}", flush=True)
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()
