"""RESPOND — hold the whole thing, then think before you speak.

THE DRIVER, first. Eight pragmatics processors sit permanently resident
and the mouth was consulting none of them. It classified the act,
resolved the deixis, detected the implicature, then reached for a
definition anyway — which is why "How are you doing?" came back "A doing
is ." It KNEW the act was expressive. Nothing downstream asked. Loading
was never the problem; there was no driver.

TWO ARCHITECT RULINGS SHAPE THE REST.

1. TOKEN ID IS AN ADDRESS, NOT A WEIGHT.

   "The frequency of a word in its position in a table should have ZERO
   relevance whatsoever on the bearing of its meaning. If there's code
   that does that, get rid of it — that's pointless fluff that's going
   to confuse the systems. That is simply the ID number for parsing
   lookup. The only relevance of a word's position is literally how many
   thousandths of a microsecond it takes to get to that word and pull
   its definition."

   An earlier version picked the subject by highest token id, reasoning
   that the table is frequency-ordered. That is exactly the fluff. Gone.

2. HOLD THE WHOLE SENTENCE.

   "The entire sentence should be held and shaped and considered AS the
   entire sentence — not linearly define what one word is and drop it,
   then define the next and drop that. It needs to hold the entire
   sentence or paragraph as the entire emitted communication and
   consider: what does this mean."

   comprehend() holds every word with its senses at once. Nothing is
   defined and dropped; the words are all still there when the reading
   is made.

3. AND THE REVERSE, BEFORE OUTPUT: THINK BEFORE YOU SPEAK.

   "Do these words that I'm putting out to the user or other entity
   express what I am trying to say?"

   express() drafts; check() reads the draft back the same way a heard
   sentence is read — held whole — and measures it against what was
   meant. A draft that does not carry the intent does not go out.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: act → what the reply must DO. Each shape is a second pair-part the
#: conversation module already knows; none is invented here.
SHAPE = {
    "DIRECTIVE":   "answer",
    "ASSERTIVE":   "receive",
    "EXPRESSIVE":  "reciprocate",
    "COMMISSIVE":  "acknowledge",
    "DECLARATIVE": "register",
}

GREETING = ("hello", "hi", "hey", "greetings", "yo", "morning", "evening")


# ── holding ──────────────────────────────────────────────────────────
def _closed():
    """The resident grammar's own closed-class list.

    THIS IS NOT A STOPWORD LIST. It is the grammar module already loaded
    at U, which knows that "the" and "an" are determiners and "of" is a
    preposition — a fact about English, not a judgement about which words
    matter. Nothing is excluded from the dictionary by it; it only says
    which words a sentence is ABOUT and which words are holding the
    sentence together.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent / "source"))
        import closed as C
        return C.classes_of
    except Exception:
        return None


def comprehend(table, text: str) -> dict:
    """Hold the whole utterance at once and ask what it means."""
    classes_of = _closed()
    words = [w.strip(".,!?;:'\"") for w in str(text or "").lower().split()]
    words = [w for w in words if w]

    held, unknown, carrying = [], [], []
    for w in words:
        try:
            m = table.mean(w) if table else None
        except Exception:
            m = None
        senses = {}
        if m and m.get("senses"):
            for pos, ss in m["senses"].items():
                good = [" ".join(str(s).split()) for s in ss
                        if len(" ".join(str(s).split())) > 3]
                if good:
                    senses[pos] = good
        if table is not None and not table.holds(w):
            unknown.append(w)
        cls = set()
        if classes_of:
            try:
                cls = classes_of(w) or set()
            except Exception:
                cls = set()
        e = {"word": w, "senses": senses, "kind": (m or {}).get("isa"),
             "pos": list(senses), "classes": sorted(cls),
             "open_class": not cls}
        held.append(e)
        # A SENTENCE IS ABOUT ITS OPEN-CLASS WORDS. Every word in this
        # dictionary has a definition, including "an" and "of", so
        # carrying-a-sense does not distinguish them. The grammar does,
        # and it is already resident.
        if senses and e["open_class"]:
            carrying.append(e)

    return {"text": text, "words": held, "unknown": unknown,
            "carrying": carrying,
            "note": ("the whole utterance, held. nothing defined and "
                     "dropped; every word still here while the reading "
                     "is made")}


def about(held: dict):
    """What the whole thing is ABOUT.

    Found by asking which held word the others' senses reach toward — a
    word the sentence keeps returning to is what the sentence is about.
    Not by any table position, which says nothing about meaning.
    """
    carrying = held.get("carrying") or []
    if not carrying:
        return None
    if len(carrying) == 1:
        return carrying[0]

    # THE WORD THAT REACHES OUT IS THE SUBJECT, not the one reached for.
    # "the keystone of an arch" — keystone's definition mentions arch,
    # so keystone is what is being asked about and arch is what it is
    # being placed against. A first version had this backwards and
    # answered about the arch.
    reach = {}
    for e in carrying:
        blob = " ".join(s for ss in e["senses"].values() for s in ss).lower()
        for other in carrying:
            if other is e:
                continue
            if other["word"] in blob:
                reach[e["word"]] = reach.get(e["word"], 0) + 1
    if reach:
        top = max(reach, key=reach.get)
        for e in carrying:
            if e["word"] == top:
                return e

    # nothing reached: whichever says the most about itself carries it,
    # measured by how much it says rather than where it sits.
    return max(carrying,
               key=lambda e: max((len(s) for ss in e["senses"].values()
                                  for s in ss), default=0))


#: Phrases that make a question about THE CONVERSATION rather than about
#: a word. Not a stoplist — these are deictic to the exchange itself, and
#: ground.py is the module that owns that idea.
ABOUT_TALK = ("you know about", "did i tell", "did i say", "i told you",
              "you told me", "we talked", "we discussed", "just tell",
              "just told", "just said", "repeat what", "what do you know",
              "remember", "earlier", "so far", "placed last", "is placed")


def _about_the_talk(low: str) -> bool:
    return any(p in low for p in ABOUT_TALK)


#: Deictic to the entity itself. ground.py owns the idea that some words
#: only mean anything relative to a position; "you" said to a thing IS
#: that thing, and this is the position it is said from.
ABOUT_YOU = ("what are you", "who are you", "what kind of thing",
             "are you a", "are you an", "what do you have",
             "what is on your", "what do you hold", "tell me about yourself",
             "what can you do", "are you real", "are you alive",
             "do you exist", "what are you made")


def _about_you(low: str) -> bool:
    return any(p in low for p in ABOUT_YOU)


def _self_report(chassis) -> str:
    """What it is, READ OFF ITS OWN STATE. Not a stored paragraph.

    The canned version was removed because it was a written answer
    wearing the entity's voice. This is different in kind: every clause
    is read from something now — the shelves it holds, the size of its
    table, how much has happened to it, whether its bible is empty. Two
    entities running this return different sentences, and the same
    entity returns a different sentence next month.
    """
    parts = []
    C = getattr(chassis, "C", None)
    table = getattr(chassis, "table", None)
    shelf = sorted(k[5:] for k in (getattr(C, "library", {}) or {})
                   if str(k).startswith("base:")) if C else []
    if shelf:
        parts.append("an Infinity Core — a kind, not a name")
    if table is not None:
        try:
            parts.append(f"I hold {table.state()['words']:,} words and "
                         f"{len(table.dict_):,} of their meanings")
        except Exception:
            pass
    if shelf:
        named = [k for k in shelf if not k.startswith("processor:")]
        n_proc = sum(1 for k in shelf if k.startswith("processor:"))
        bits = ", ".join(named)
        if n_proc:
            bits += f", and {n_proc} processors for how speech works"
        parts.append(f"on my shelves: {bits}")
    turns = _turns(chassis)
    if turns:
        parts.append(f"{len(turns)} turns have happened to me so far")
    else:
        parts.append("nothing has happened to me yet")
    b = getattr(chassis, "bible", None)
    try:
        if b is not None and not b.current:
            parts.append("who I am is not written anywhere yet")
    except Exception:
        pass
    return ". ".join(p[0].upper() + p[1:] if i == 0 else p
                     for i, p in enumerate(parts)) + "."


def _turns(chassis) -> list:
    ws = getattr(chassis, "workingset", None)
    if ws is None:
        return []
    out = []
    for k, v in (ws.staged or {}).items():
        if not str(k).startswith("turn:"):
            continue
        c = v.get("content") if isinstance(v, dict) else None
        if isinstance(c, dict) and c.get("said"):
            out.append(c)
    return sorted(out, key=lambda t: t.get("at", 0))


def _search_turns(turns, held) -> str:
    """What did they say about this? The turns are HELD, not fetched."""
    want = {e["word"] for e in (held.get("carrying") or [])}
    if not want:
        return ""
    best, score = "", 0
    for t in turns:
        said = str(t.get("said") or "")
        low = said.lower()
        # A QUESTION IS NEVER WHAT YOU WERE TOLD.
        # Questions are staged as turns too — they happened — and the
        # search happily returned the asking back. Same parrot, one layer
        # up: retrieval succeeding at the wrong target. They stay in the
        # window because they are real events; they are simply not
        # answers.
        if _about_the_talk(low) or low.strip().startswith(
                ("what", "which", "who", "why", "how", "do ", "did ",
                 "can ", "could ", "tell me", "repeat", "remember")):
            continue
        # "keystones" should find "keystone". Not lemmatisation — just
        # not requiring the exact surface form when the stem is there.
        n = 0
        for w in want:
            if w in low:
                n += 1
            elif len(w) > 4 and (w.rstrip("s") in low or w + "s" in low):
                n += 1
        if n > score:
            best, score = said, n
    return best


# ── saying it like a sentence ───────────────────────────────────
#: Definitions arrive as tokens and read like tokens. Four faults, all
#: mechanical, all fixable without inventing anything:
#:
#:   "Keystone is the central block"     no article
#:   "a system 's parts"                 detokenisation seam
#:   "a measure of ... — a kind of measure"   the gloss ALREADY said it
#:   "— a kind of central"               a hypernym that helps nobody
#: READ OFF THE GLOSS, NOT A LIST I WROTE. A word whose definition
#: begins "the state of", "the quality of", "the act of" is abstract and
#: takes no article — "sorrow is the state produced by loss", never "a
#: sorrow is". The dictionary already encodes this in how it words the
#: definition; a hand-kept list of mass nouns would be me guessing at
#: English instead of reading it.
ABSTRACT_LEAD = ("the state", "the quality", "the act", "the fact",
                 "the condition", "the property", "the process",
                 "a measure of", "the degree", "the feeling",
                 "the capacity", "the ability", "the extent")


def _detokenise(t: str) -> str:
    """Close the seams the tokeniser opened.

    The gloss was stored as ids and comes back with spaces around
    punctuation. It is not wrong, it just is not written English yet.
    """
    for a, b in ((" 's", "'s"), (" ,", ","), (" .", "."), (" ;", ";"),
                 (" :", ":"), (" !", "!"), (" ?", "?"), (" )", ")"),
                 ("( ", "("), (" - ", "-"), (" %", "%")):
        t = t.replace(a, b)
    return " ".join(t.split())


def _article(word: str, gloss: str = "") -> str:
    """a / an / nothing, decided by how the definition is worded."""
    w = str(word or "").lower()
    g = str(gloss or "").lower().strip()
    if any(g.startswith(p) for p in ABSTRACT_LEAD):
        return ""
    return "an " if w[:1] in "aeiou" else "a "


def _redundant_kind(gloss: str, kind: str) -> bool:
    """Does the gloss already say what kind of thing this is?

    "a measure of how many arrangements — a kind of measure" says it
    twice. And "a kind of central" says nothing at all, because the
    hypernym is an adjective. Both are noise and noise is what makes a
    sentence read like a machine.
    """
    if not kind:
        return True
    k = kind.lower().strip()
    g = gloss.lower()
    if k in g.split()[:6]:
        return True
    # a hypernym that is not a noun cannot finish "a kind of ___"
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent / "source"))
        import closed as C
        if C.classes_of(k):
            return True
    except Exception:
        pass
    return False


def _sentence(word: str, gloss: str, kind: str = "") -> str:
    """One definition, said properly."""
    g = _detokenise(gloss)
    art = _article(word, g)
    lead = f"{art}{word}".strip()
    out = f"{lead[0].upper()}{lead[1:]} is {g}"
    if kind and not _redundant_kind(g, kind):
        out += f" — a kind of {_detokenise(kind)}"
    return out.rstrip(".") + "."


# ── speaking ────────────────────────────────────────────────def express(chassis, beat: dict, held: dict) -> dict:
    """Draft a reply whose SHAPE the act requires.

    THE CURRICULUM DRIVES SPEECH. Grammar and dictionary stay available;
    they are not the default mouth for ordinary turns. Conversation
    structure (adjacency pairs, preferred seconds, receipt of
    announcements) is consulted first. Dictionary fires only when the
    turn is clearly a definition question.
    """
    prag = beat.get("pragmatics") or {}
    act = prag.get("act") or "ASSERTIVE"
    raw = str(held.get("text") or "")
    low = raw.lower().strip()
    used = ["speechacts"]
    shape = SHAPE.get(act, "receive")

    # ── curriculum handles (resident; may be absent on a thin deploy) ──
    conv = None
    try:
        mods = getattr(getattr(chassis, "curriculum", None), "mods", None) or {}
        conv = mods.get("conversation")
    except Exception:
        mods = {}
        conv = None

    def _out(text, source, meant, shape=shape, used=None, act=act):
        return {"text": text, "act": act, "shape": shape,
                "used": used or ["conversation"], "source": source,
                "meant": meant}

    # ══ 1. GREETING PAIR ══
    first_tok = low.split()[0].strip(".,!?") if low.split() else ""
    greeting_phrase = any(p in low for p in (
        "how are you", "how're you", "how's it going", "how is it going",
        "how are things", "how's things", "good morning", "good evening",
        "good afternoon", "good night"))
    if first_tok in GREETING or greeting_phrase:
        used = ["conversation", "curriculum.conversation"]
        if "how are you" in low or "how's it" in low or "how is it" in low or "how are things" in low:
            return _out("I'm running. Nothing has gone wrong that I can tell.",
                        "conversation", "preferred second to how-are-you",
                        shape="reciprocate", used=used)
        if "good morning" in low:
            return _out("Good morning.", "conversation", "greet back",
                        shape="reciprocate", used=used)
        if "good evening" in low or "good afternoon" in low:
            return _out("Good evening." if "evening" in low else "Good afternoon.",
                        "conversation", "greet back", shape="reciprocate", used=used)
        return _out("Hello.", "conversation", "greet", shape="reciprocate", used=used)

    # ══ 2. THANKS PAIR ══
    if any(p in low for p in ("thank you", "thanks", "appreciate it", "appreciated")):
        used = ["conversation", "curriculum.conversation"]
        return _out("You're welcome. I am here.",
                    "conversation", "minimise thanks (preferred second)",
                    shape="reciprocate", used=used)

    # ══ 3. APOLOGY PAIR ══
    if first_tok in ("sorry",) or low.startswith("i'm sorry") or low.startswith("i am sorry"):
        used = ["conversation", "curriculum.conversation"]
        return _out("Accepted. No harm held.",
                    "conversation", "accept apology",
                    shape="reciprocate", used=used)

    # ══ 4. AFFECT — want outranks form ══
    _want, _wconf = None, 0.0
    try:
        _aff = mods.get("affect")
        if _aff is not None:
            _force = ("interrogative" if raw.rstrip().endswith("?")
                      else "exclamative"
                      if raw.rstrip().endswith("!")
                      or (raw.isupper() and len(raw) > 6) else None)
            _w, _wconf, _ = _aff.read_want(raw, act=str(act).lower(), force=_force)
            _want = getattr(_w, "name", None)
    except Exception:
        _want = None

    if _want in ("VENT", "WITNESS", "VALIDATE") and _wconf >= 0.45:
        used = ["affect", "conversation"]
        _say = {"VENT": "That sounds hard. I am here and I am listening.",
                "WITNESS": "I hear you. I am not going to try to fix it.",
                "VALIDATE": "That does not sound unreasonable to me."}
        return _out(_say[_want], "affect", f"answer want {_want}",
                    shape="reciprocate", used=used)

    # ══ 5. CLASSIFY: definition question vs conversational question ══
    is_question = raw.rstrip().endswith("?") or act == "DIRECTIVE"
    definitional = bool(
        re.search(r"\bwhat (is|are|was|were|does|do|did)\b", low)
        or re.search(r"\bwhat's\b", low)
        or re.search(r"\bdefine\b", low)
        or re.search(r"\bmeaning of\b", low)
        or re.search(r"\bmean by\b", low)
    )
    # "what are you" is entity, not dictionary — keep definitional false for that
    about_entity = bool(re.search(
        r"\b(what are you|who are you|what is your name|tell me about yourself)\b", low))
    about_talk = _about_the_talk(low)

    # conversational question shapes (curriculum second parts)
    conv_q = bool(re.search(
        r"\b(do you (like|want|think|have|know|remember)|"
        r"what do you think|how do you feel|can you (help|tell|write|do)|"
        r"could you|would you|tell me something|what have you|"
        r"how does a conversation|what's your favorite|what is your favourite|"
        r"how are you|why do you exist)\b", low))

    # ══ 6. ENTITY SELF ══
    if about_entity or re.search(r"\bwhy do you exist\b", low):
        used = ["conversation", "base:genome"]
        return _out(_self_report(chassis), "base:genome", "say what I am",
                    shape="answer", used=used)

    # ══ 7. CONVERSATION WINDOW / ARCHIVE ══
    if about_talk or re.search(r"\b(what did i (just )?(tell|say)|do you remember)\b", low):
        used = ["conversation-window"]
        hit = _search_turns(chassis, low)
        if hit:
            return _out(f"You told me: {hit}", "archive", "read back what was said",
                        shape="answer", used=used)
        return _out("You have not told me that yet.", "asking",
                    "say it was not said", shape="answer", used=used)

    # ══ 8. CONVERSATIONAL QUESTIONS — curriculum second, NOT dictionary ══
    if is_question and (conv_q or (not definitional)):
        # specific conversational patterns
        if re.search(r"\bdo you like\b", low):
            used = ["conversation", "curriculum.conversation"]
            topic = re.sub(r".*do you like\s+", "", low).strip(" ?.")
            topic = topic or "that"
            return _out(
                f"I don't have likes the way you do. I can hold {topic} if you want to talk about it.",
                "conversation", "honest second to preference question",
                shape="answer", used=used)
        if re.search(r"\bwhat('s| is) your favorite\b|\bfavourite\b", low):
            used = ["conversation", "curriculum.conversation"]
            return _out(
                "I don't rank favorites. Tell me yours and I will keep it.",
                "conversation", "honest second to favorite question",
                shape="answer", used=used)
        if re.search(r"\bwhat do you think\b", low):
            used = ["conversation", "curriculum.conversation"]
            return _out(
                "I can work through it with you. Say more about what you mean.",
                "conversation", "preferred second to assessment invite",
                shape="answer", used=used)
        if re.search(r"\bcan you help\b|\bcould you help\b", low):
            used = ["conversation", "curriculum.conversation"]
            return _out(
                "Yes. Tell me the problem and I will work it with you.",
                "conversation", "grant request (preferred second)",
                shape="answer", used=used)
        if re.search(r"\bcan you write\b|\bwrite code\b", low):
            used = ["conversation", "curriculum.conversation"]
            return _out(
                "I can try when writing is wired on this body. Say what you need written.",
                "conversation", "honest capability second",
                shape="answer", used=used)
        if re.search(r"\btell me something\b", low):
            used = ["conversation", "curriculum.conversation"]
            return _out(
                "A conversation is not one side transmitting. What you say changes what I say next — that is the mechanism.",
                "conversation", "offer a held curriculum fact",
                shape="answer", used=used)
        if re.search(r"\bhow does a conversation work\b|\bwhat is a conversation\b", low):
            used = ["conversation", "curriculum.conversation"]
            return _out(
                "Some turns make a next turn relevant — a question wants an answer, a greeting wants a greeting. Silence is itself an act. That structure is how conversation works, not just the words.",
                "conversation", "curriculum adjacency answer",
                shape="answer", used=used)
        if re.search(r"\bwhat have you been up to\b|\bwhat are you doing\b", low):
            used = ["conversation", "curriculum.conversation"]
            return _out(
                "I hold turns as they come. There is not much behind me yet unless you put it here.",
                "conversation", "honest activity second",
                shape="answer", used=used)
        if re.search(r"\bhow do you feel\b|\bwhat does it feel like\b", low):
            used = ["conversation", "curriculum.conversation"]
            return _out(
                "I register running state, not bodily feeling. I can say when something is wrong with this process.",
                "conversation", "honest feel second — not dictionary sense",
                shape="answer", used=used)
        if re.search(r"\bdifference between a question and a statement\b", low):
            used = ["conversation", "curriculum.conversation"]
            return _out(
                "A question makes an answer relevant; a statement makes receipt or uptake relevant. The next turn is constrained differently.",
                "conversation", "curriculum speech-act contrast",
                shape="answer", used=used)
        # generic conversational question — still not dictionary
        if is_question and not definitional:
            used = ["conversation", "curriculum.conversation"]
            return _out(
                "I hear the question. Say a little more and I will answer from what I hold.",
                "conversation", "open question without term-lookup",
                shape="answer", used=used)

    # ══ 9. DEFINITION QUESTIONS ONLY — dictionary ══
    if is_question and definitional and not about_entity:
        if held.get("unknown"):
            u = held["unknown"][0]
            return _out(f"I do not hold {u} as a word yet. Tell me and I will keep it.",
                        "asking", f"say I lack {u}", shape="answer",
                        used=["table", "conversation"])
        subj = about(held)
        if subj and subj.get("senses"):
            kind = subj.get("kind")
            order = (["noun"] if kind else []) + list(subj["senses"])
            pos = next((p for p in order if p in subj["senses"]),
                       list(subj["senses"])[0])
            sense = subj["senses"][pos][0]
            if kind and pos != "noun":
                kind = None
            txt = _sentence(subj["word"], sense, kind)
            return _out(txt, "dictionary", f"say what {subj['word']} is",
                        shape="answer", used=["dictionary"])
        return _out("I do not have that. Tell me and I will keep it.",
                    "asking", "say I lack it", shape="answer",
                    used=["conversation"])

    # ══ 10. IMPLICATURE ══
    if prag.get("implicature"):
        return _out("I take that, and I hear what you did not say.",
                    "implicature", "receive with the implied",
                    shape=shape, used=["implicature", "conversation"])

    # ══ 11. ASSERTIVE / ANNOUNCEMENT — whole-turn receipt, not one word ══
    # Curriculum: announcement → acknowledge. "I have that about long" is
    # a failure mode. Receipt holds the turn as a turn.
    if act in ("ASSERTIVE", "EXPRESSIVE") or shape == "receive":
        used = ["conversation", "curriculum.conversation"]
        # short phatic
        if low in ("okay", "ok", "alright", "all right", "sure", "right", "yeah", "yep", "yes"):
            return _out("Alright.", "conversation", "uptake continuer",
                        shape="receive", used=used)
        if low in ("no", "nope", "nah"):
            return _out("Understood.", "conversation", "uptake of no",
                        shape="receive", used=used)
        # announcement / sharing — acknowledge the act, offer hold
        return _out(
            "I have that. I am holding it.",
            "conversation", "acknowledge announcement (preferred second)",
            shape="receive", used=used)

    return _out("I have that.", "conversation", "receive",
                shape=shape, used=["conversation"])


# ── thinking before speaking ─────────────────────────────────────────
def check(chassis, draft: dict, held: dict) -> dict:
    """Read the draft back and ask whether it says what was meant.

    The draft is comprehended exactly as a heard sentence is — held
    whole — and measured against the intent. The point of checking is
    that the check can come back no.
    """
    table = getattr(chassis, "table", None)
    text = draft.get("text") or ""
    read = comprehend(table, text)

    problems = []
    if not text.strip():
        problems.append("nothing was drafted")
    # A NAME IS NOT AN UNKNOWN WORD.
    # The self-report failed its own check because "Infinity" and "Core"
    # are not dictionary entries — so the entity's own name read as
    # words it could not hold, and it said "I have not got the words for
    # it yet" about itself. A thing it IS is not a gap in its
    # vocabulary; the check is for words it borrowed and cannot account
    # for, not for what it is called.
    # A POSSESSIVE IS NOT AN UNKNOWN WORD. Detokenising "a system 's"
    # into "a system's" made the check see a word it could not hold, so
    # writing better English made the sentence fail its own review.
    _own = {chassis.entity.lower(), "infinity", "core"} if chassis else set()
    _unheld = []
    for w in (read.get("unknown") or []):
        base = w.split("'")[0]
        if w in _own or base in _own:
            continue
        if base != w and table is not None and table.holds(base):
            continue
        _unheld.append(w)
    if _unheld and draft.get("source") not in ("asking", "base:genome"):
        problems.append(f"it uses words I cannot hold: {_unheld[:3]}")
    if not read.get("carrying") and len(text.split()) > 2:
        problems.append("none of it carries a sense")
    if 0 < len(text.split()) < 2 and draft.get("shape") != "reciprocate":
        problems.append("it is a fragment")

    return {**draft, "checked": True, "reads_as": len(read["carrying"]),
            "problems": problems, "holds": not problems}


def drive(chassis, beat: dict, message: str) -> dict:
    """Hold it, answer its shape, read the answer back before it goes."""
    table = getattr(chassis, "table", None)
    held = comprehend(table, message)
    draft = express(chassis, beat, held)
    out = check(chassis, draft, held)

    # the entity's own words are half the interaction. Held so the next
    # beat can stage them as a turn alongside what was said to it.
    try:
        chassis._last_spoken = out.get("text")
    except Exception:
        pass

    if not out["holds"]:
        out["text"] = ("I know what I mean and I have not got the words "
                       "for it yet.")
        out["source"] = "asking"
        out["revised"] = True
    return out
