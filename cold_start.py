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
    with LOCK:
        o = C.tick(message=message, will="recall")
        acts = (o["emission"].world or {}).get("acts") or {}
        r = (acts.get("recall") or {}).get("result") or {}
        want = o.get("wants_to_know") or {}
        if r.get("found"):
            text, src = r["text"], r.get("from", "archive")
        elif want.get("say"):
            text, src = want["say"], "asking"
        else:
            text = C.tongue2.speak(C, o, occupied=True, store=STORE)["text"]
            src = "state"
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
