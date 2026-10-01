from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field

from .answer import (Artifacts, PackBuilder, WRITER_VERSION, finalize, llm_write, write_answer)
from .definitions import BEHAVIOURS, EVENTS, INDUSTRIES
from .query import (HELP_RE, OVERVIEW_RE, QUESTION_TYPES, TYPE_PATTERNS, QueryParser, QuerySpec, _norm, llm_normalize,
                    llm_parse, parse_point_date, unsure)

SLOTS = ("event", "question_type", "behaviour", "factor_ref", "industry", "brand", "intent", "date_from", "date_to",
         "with_event", "threshold", "change", "tier", "plan", "segment", "tenure", "self_status", "call")
FILTER_SLOTS = ("industry", "brand", "intent", "date_from", "date_to", "with_event", "tier", "plan", "segment", "tenure",
                "self_status", "call")
RULE_SLOTS = ("with_event", "threshold", "change", "tier", "plan", "segment", "tenure", "self_status", "call")
GENERAL_RE = re.compile(r"\b(?:customers|callers|people|calls|agents|clients|guests|passengers|users|everyone)\b")
LEAVE_CALL_TYPES = ("how_often", "examples", "compare", "trend", "issues", "shared", "overview", "what_to_change")
RESET_RE = re.compile(r"^\s*(?:new question|start over|forget (?:that|everything|the filters?)|reset)\b")
REMOVE_FILTER_RE = re.compile(r"\b(?:all|any|every) (?:industr(?:y|ies)|sectors?|brands?|calls)\b|\bacross (?:all )?"
                              r"industries\b|\bwithout (?:the |any )?(?:industry |brand )?filters?\b|\bremove (?:the |all )?"
                              r"(?:industry |brand )?filters?\b|\boverall\b|\bin general\b|\bdrop the (?:industry |brand )?filters?\b")
ADD_RE = re.compile(r"\b(?:also|as well|too|and also|plus|in addition)\b")
REUSE_RE = re.compile(r"^\s*(?:why\??|how come\??|explain(?: (?:that|this|it|more))?|tell me more|more details?|go on|"
                      r"and\??|ok(?:ay)?,? (?:and )?why\??|can you elaborate)\W*$")
PRONOUN_RE = re.compile(r"\b(?:it|that|this|those|them|these|there)\b")
FOLLOWUP_RE = re.compile(r"^\s*(?:and|also|but|so|then|ok(?:ay)?|only|just|same)\b|\b(?:what|how) about\b|\b(?:also|too|as well|"
                         r"instead|same|again|it|that|this|those|them|these|there|other|others|rest|remaining|elsewhere)\b")
QUOTE_REF_RE = re.compile(r"\b(?:that|this|the same|the (first|second|third|fourth|last|previous)) (?:call|conversation|transcript|"
                          r"quote|example|customer|caller)\b")
QUOTE_ORDINAL = {"first": 0, "second": 1, "third": 2, "fourth": 3, "last": -1}
OTHER_INDUSTRIES_RE = re.compile(r"\b(?:other|remaining|rest of the) (?:domains?|industr(?:y|ies)|sectors?)\b|\belsewhere\b|"
                                 r"\bin the other ones\b")


def is_standalone(t: str, new: QuerySpec, qt: str | None) -> bool:
    return bool(new.event and qt and len(t.split()) >= 5 and not FOLLOWUP_RE.search(t))


@dataclass
class SessionState:
    spec: dict | None = None
    shown_factor_ids: list = field(default_factory=list)
    shown_turn_uids: list = field(default_factory=list)
    library_version: str = ""
    index_version: str = ""
    summary: list = field(default_factory=list)
    turn_count: int = 0
    history: list = field(default_factory=list)
    quoted: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return json.loads(json.dumps(asdict(self), default=str))

    @classmethod
    def from_dict(cls, d: dict) -> "SessionState":
        if not isinstance(d, dict):
            raise TypeError(f"session state must be a JSON object, not {type(d).__name__}")
        out = cls()
        for k, v in d.items():
            if k not in cls.__dataclass_fields__:
                continue
            default = getattr(out, k)
            if k == "spec":
                out.spec = v if isinstance(v, dict) else None
            elif isinstance(default, list):
                out.__dict__[k] = [x for x in v if isinstance(x, (str, dict))] if isinstance(v, list) else []
            elif isinstance(default, int):
                out.__dict__[k] = v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else 0
            else:
                out.__dict__[k] = v if isinstance(v, str) else ""
        return out


SPEC_DICT_FIELDS = ("compare", "threshold", "change")
SPEC_LIST_FIELDS = ("presuppositions", "unsupported", "declined_filters", "notes")


def restore_spec(d) -> QuerySpec | None:
    if not isinstance(d, dict):
        return None
    try:
        spec = QuerySpec.from_dict(d)
    except TypeError:
        return None
    if spec.event is not None and spec.event not in EVENTS or spec.question_type not in QUESTION_TYPES:
        return None
    if spec.behaviour is not None and spec.behaviour not in BEHAVIOURS:
        return None
    if spec.factor_ref is not None and not isinstance(spec.factor_ref, str):
        return None
    if not isinstance(spec.filters, dict):
        return None
    for k, v in list(spec.filters.items()):
        if k not in FILTER_SLOTS or not isinstance(v, (list, str)) or isinstance(v, list) and not all(isinstance(x, str) for x in v):
            return None
    if not set(spec.filters.get("industry", [])) <= set(INDUSTRIES) or not set(spec.filters.get("with_event", [])) <= set(EVENTS):
        return None
    for k in SPEC_DICT_FIELDS:
        if getattr(spec, k) is not None and not isinstance(getattr(spec, k), dict):
            return None
    if spec.compare is not None and not isinstance(spec.compare.get("values", []), list):
        return None
    for k in SPEC_LIST_FIELDS:
        if not isinstance(getattr(spec, k), list):
            setattr(spec, k, [])
    if not isinstance(spec.raw, str) or not isinstance(spec.ambiguous, str):
        return None
    spec.leading = bool(spec.leading)
    return spec


def explicit_type(text: str) -> str | None:
    t = _norm(text)
    for qt, pat in TYPE_PATTERNS:
        if re.search(pat, t):
            return qt
    return None


def propose_delta(prev: QuerySpec, text: str, parser: QueryParser) -> dict:
    t = _norm(text)
    new = parser.parse(text)
    delta = {"ops": [], "reset": bool(RESET_RE.search(t)), "clarify": "", "notices": {
        "unsupported": new.unsupported, "declined_filters": new.declined_filters, "presuppositions": new.presuppositions,
        "leading": new.leading, "notes": new.notes}}
    if delta["reset"]:
        delta["ops"] = [{"op": "replace_all", "slot": "*", "value": new.to_dict()}]
        return delta
    ops = delta["ops"]
    qt = explicit_type(text)
    standalone = is_standalone(t, new, qt)
    if new.event and new.event != prev.event:
        ops.append({"op": "set", "slot": "event", "value": new.event})
    if not new.compare and qt == "compare" and new.event and prev.event and new.event != prev.event:
        new.compare = {"dimension": "event", "values": [prev.event, new.event]}
    if not new.compare and qt == "compare" and new.filters.get("industry") and prev.filters.get("industry"):
        vals = list(dict.fromkeys(prev.filters["industry"] + new.filters["industry"]))
        if len(vals) > 1:
            new.compare = {"dimension": "industry", "values": vals}
            new.filters.pop("industry")
    if new.compare:
        ops.append({"op": "set", "slot": "compare", "value": new.compare})
    elif standalone and prev.compare:
        ops.append({"op": "remove", "slot": "compare", "value": None})
    by_industry = bool(new.compare and new.compare.get("dimension") == "industry")
    if REMOVE_FILTER_RE.search(t) or standalone or by_industry:
        for s in FILTER_SLOTS:
            if prev.filters.get(s) and not new.filters.get(s) and (s == "industry" or not by_industry or standalone or
                                                                    REMOVE_FILTER_RE.search(t)):
                ops.append({"op": "remove", "slot": s, "value": None})
    if (OTHER_INDUSTRIES_RE.search(t) and prev.filters.get("industry") and not new.filters.get("industry")
            and not by_industry):
        rest = [i for i in INDUSTRIES if i not in prev.filters["industry"]]
        if rest:
            ops.append({"op": "set", "slot": "industry", "value": rest})
    for s in ("with_event", "tier", "plan", "segment", "self_status"):
        if new.filters.get(s):
            ops.append({"op": "set", "slot": s, "value": list(new.filters[s])})
    if new.filters.get("tenure"):
        ops.append({"op": "set", "slot": "tenure", "value": new.filters["tenure"]})
    if new.threshold:
        ops.append({"op": "set", "slot": "threshold", "value": new.threshold})
    elif (standalone or (qt and new.event and not REUSE_RE.search(t))) and prev.threshold:
        ops.append({"op": "remove", "slot": "threshold", "value": None})
    when = parse_point_date(t, parser.year_hint)
    if new.change:
        ops.append({"op": "set", "slot": "change", "value": new.change})
    elif prev.change and not prev.change.get("date") and when:
        ops.append({"op": "set", "slot": "change", "value": {**prev.change, "date": when}})
        new.filters.pop("date_from", None)
        new.filters.pop("date_to", None)
    elif standalone and prev.change:
        ops.append({"op": "remove", "slot": "change", "value": None})
    for s in ("industry", "brand", "intent"):
        if new.filters.get(s):
            mode = "add" if ADD_RE.search(t) and prev.filters.get(s) else "set"
            ops.append({"op": mode, "slot": s, "value": list(new.filters[s])})
    for s in ("date_from", "date_to"):
        if new.filters.get(s):
            ops.append({"op": "set", "slot": s, "value": new.filters[s]})
    if standalone and prev.behaviour and not new.behaviour:
        ops.append({"op": "remove", "slot": "behaviour", "value": None})
    if new.factor_ref:
        ops.append({"op": "set", "slot": "factor_ref", "value": new.factor_ref})
        ops.append({"op": "set", "slot": "question_type", "value": "describe_factor"})
    elif qt and qt != prev.question_type:
        ops.append({"op": "set", "slot": "question_type", "value": qt})
    if new.behaviour and new.behaviour != prev.behaviour:
        ops.append({"op": "set", "slot": "behaviour", "value": new.behaviour})
        if not qt and not new.factor_ref:
            ops.append({"op": "set", "slot": "question_type", "value": "effect_of" if (prev.event or new.event) else "behaviour"})
    elif new.event and prev.question_type == "behaviour" and prev.behaviour and not qt:
        ops.append({"op": "set", "slot": "question_type", "value": "effect_of"})
    if new.event and prev.question_type in ("overview", "help") and not qt and not new.behaviour:
        ops.append({"op": "set", "slot": "question_type", "value": "why"})
    if not new.event and not new.behaviour and new.question_type in ("overview", "help") and \
            new.question_type != prev.question_type and not new.filters.get("call") and \
            (OVERVIEW_RE.search(t) or HELP_RE.search(t)):
        ops.append({"op": "set", "slot": "question_type", "value": new.question_type})
        ops += [{"op": "remove", "slot": x, "value": None} for x in ("event", "behaviour", "compare") if getattr(prev, x)]
    if prev.question_type == "shared" and new.event and not new.compare and not any(op["slot"] == "compare" for op in ops):
        asked = (prev.compare or {}).get("asked")
        ops += [{"op": "set", "slot": "event", "value": new.event}, {"op": "remove", "slot": "compare", "value": None},
                {"op": "set", "slot": "question_type", "value": qt or (asked if asked in ("what_to_change", "effect_of") else "why")}]
    top = (prev.compare or {}).get("top")
    if prev.compare and prev.compare.get("rank") and top and prev.compare.get("dimension") not in ("event",) and \
            re.match(r"^\s*(?:why|how come|explain(?: (?:that|this|it|why))?|what drives (?:that|this|it))\W*$", t):
        ops += [{"op": "remove", "slot": "compare", "value": None}, {"op": "set", "slot": "question_type", "value": "why"},
                {"op": "set", "slot": prev.compare["dimension"], "value": [top]}]
    if any(op["slot"] == "change" and op["op"] == "set" for op in ops) and prev.question_type != "trend":
        ops.append({"op": "set", "slot": "question_type", "value": "trend"})
    if new.filters.get("call"):
        ops[:] = [op for op in ops if op["slot"] not in FILTER_SLOTS + ("compare", "question_type", "factor_ref")]
        ops += [{"op": "remove", "slot": f, "value": None} for f in FILTER_SLOTS if prev.filters.get(f) and f != "call"]
        ops += [{"op": "set", "slot": "call", "value": list(new.filters["call"])},
                {"op": "set", "slot": "question_type", "value": "call"}]
        if prev.compare:
            ops.append({"op": "remove", "slot": "compare", "value": None})
        if new.behaviour and new.behaviour != prev.behaviour:
            ops.append({"op": "set", "slot": "behaviour", "value": new.behaviour})
        elif prev.behaviour and not new.behaviour:
            ops.append({"op": "remove", "slot": "behaviour", "value": None})
    elif prev.filters.get("call"):
        leaves = (standalone or qt in LEAVE_CALL_TYPES or new.compare or new.factor_ref or bool(GENERAL_RE.search(t)) or
                  any(new.filters.get(f) for f in FILTER_SLOTS if f != "call"))
        if leaves:
            ops.append({"op": "remove", "slot": "call", "value": None})
            if not any(op["slot"] == "question_type" for op in ops):
                ops.append({"op": "set", "slot": "question_type", "value": "why"})
        else:
            ops[:] = [op for op in ops if not (op["slot"] == "question_type" and op["value"] in ("effect_of", "why"))]
    if not ops and not REUSE_RE.search(t) and not (new.event and new.event == prev.event):
        if PRONOUN_RE.search(t) or len(t.split()) <= 3:
            delta["clarify"] = ("Could you say what you would like to change: the event (escalations, refunds, churn), "
                                "the calls (an industry or brand), or which factor to explain?")
        elif new.unsupported or new.declined_filters:
            pass
        else:
            delta["clarify"] = "I could not tell what to change in the current question. Could you rephrase it?"
    return delta


def validate_delta(delta: dict, parser: QueryParser) -> list[str]:
    problems = []
    for op in delta["ops"]:
        s, v = op["slot"], op["value"]
        if op["op"] == "replace_all":
            continue
        if op["op"] == "remove" and (s in SLOTS or s == "compare"):
            continue
        if s not in SLOTS and s != "compare":
            problems.append(f"unknown slot {s}")
        elif s == "event" and v not in EVENTS:
            problems.append(f"unknown event {v}")
        elif s == "question_type" and v not in QUESTION_TYPES:
            problems.append(f"unknown question type {v}")
        elif s == "behaviour" and v not in BEHAVIOURS:
            problems.append(f"unknown behaviour {v}")
        elif s == "industry" and v is not None and not set(v) <= set(INDUSTRIES):
            problems.append(f"unknown industry {v}")
        elif s == "brand" and v is not None and not {b.lower() for b in v} <= set(parser.brands):
            problems.append(f"unknown brand {v}")
        elif s == "with_event" and v is not None and not set(v) <= set(EVENTS):
            problems.append(f"unknown event {v}")
        elif s in ("threshold", "change") and v is not None and not isinstance(v, dict):
            problems.append(f"malformed {s} {v}")
        elif s == "call" and v is not None and not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
            problems.append(f"malformed call id {v}")
    return problems


def merge(prev: QuerySpec, delta: dict, text: str) -> QuerySpec:
    new = QuerySpec.from_dict(prev.to_dict())
    new.raw = text
    new.presuppositions, new.unsupported, new.declined_filters, new.leading = [], [], [], False
    new.ambiguous = ""
    new.notes = []
    for op in delta["ops"]:
        s, v = op["slot"], op["value"]
        if op["op"] == "replace_all":
            new = QuerySpec.from_dict(v)
            continue
        if s in FILTER_SLOTS:
            if op["op"] == "remove":
                new.filters.pop(s, None)
            elif op["op"] == "add":
                cur = list(new.filters.get(s, []))
                new.filters[s] = cur + [x for x in v if x not in cur]
            else:
                new.filters[s] = v
        elif s == "compare":
            new.compare = None if op["op"] == "remove" else v
        elif op["op"] == "remove":
            setattr(new, s, None)
        else:
            setattr(new, s, v)
        if s == "event" and new.compare and new.compare.get("dimension") == "event":
            new.compare = None
        if s == "question_type" and v != "compare" and new.compare and \
                (new.compare.get("dimension") == "event" or new.compare.get("rank")):
            new.compare = None
        if s == "question_type" and v != "describe_factor":
            new.factor_ref = None
    if new.question_type in ("shared", "event_link") and not new.compare:
        new.question_type = "why"
    changed = {op["slot"] for op in delta["ops"]}
    if new.question_type == "describe_factor" and changed & (set(FILTER_SLOTS) | {"event"}) and "factor_ref" not in changed:
        new.question_type, new.factor_ref = "why", None
    n = delta.get("notices", {})
    new.presuppositions = [p for p in n.get("presuppositions", []) if p.get("event") == new.event] or \
        ([dict(p, event=new.event) for p in n.get("presuppositions", [])] if new.event else [])
    new.unsupported = n.get("unsupported", [])
    new.declined_filters = n.get("declined_filters", [])
    new.leading = bool(n.get("leading"))
    new.notes = n.get("notes", [])
    return new


def route(prev: QuerySpec, new: QuerySpec, delta: dict) -> str:
    if delta.get("clarify"):
        return "clarify"
    changed = {op["slot"] for op in delta["ops"]}
    if delta.get("reset") or changed & {"event", "question_type", "behaviour", "compare", "threshold", "change"} - {"question_type"} or \
            ("question_type" in changed and new.question_type != "describe_factor"):
        return "new_lookup"
    if changed & set(FILTER_SLOTS):
        return "refilter"
    return "reuse"


def retrieval_text(spec: QuerySpec, text: str) -> str:
    parts = [text]
    if spec.event:
        parts.append(EVENTS[spec.event].name)
    if spec.behaviour:
        parts.append(BEHAVIOURS[spec.behaviour].label)
    return " ".join(parts)


LLM_DELTA_SCHEMA = {
    "type": "object",
    "properties": {"ops": {"type": "array", "items": {"type": "object", "properties": {
        "op": {"type": "string", "enum": ["set", "add", "remove"]},
        "slot": {"type": "string", "enum": [s for s in SLOTS if s not in RULE_SLOTS]},
        "value": {"type": "string"}}, "required": ["op", "slot", "value"], "additionalProperties": False}},
        "clarify": {"type": "string"}},
    "required": ["ops", "clarify"], "additionalProperties": False,
}
IC_DST_EXAMPLES = [
    ({"event": "ESC", "question_type": "why", "filters": {"industry": ["telecom"]}}, "what about refunds?",
     {"ops": [{"op": "set", "slot": "event", "value": "REF"}], "clarify": ""}),
    ({"event": "REF", "question_type": "why", "filters": {"industry": ["telecom"]}}, "only airline calls",
     {"ops": [{"op": "set", "slot": "industry", "value": "airline"}], "clarify": ""}),
    ({"event": "ESC", "question_type": "why", "filters": {"industry": ["airline"]}}, "and across all industries?",
     {"ops": [{"op": "remove", "slot": "industry", "value": ""}], "clarify": ""}),
    ({"event": "ESC", "question_type": "why", "filters": {}}, "explain the second factor",
     {"ops": [{"op": "set", "slot": "factor_ref", "value": "#2"}, {"op": "set", "slot": "question_type", "value": "describe_factor"}], "clarify": ""}),
    ({"event": "ESC", "question_type": "why", "filters": {}}, "what about that?",
     {"ops": [], "clarify": "Which part should change: the event, the calls, or a factor?"}),
]


def llm_delta(llm, prev: QuerySpec, text: str) -> dict:
    shots = "\n\n".join(f"STATE: {json.dumps(s)}\nFOLLOW-UP: {u}\nDELTA: {json.dumps(d)}" for s, u, d in IC_DST_EXAMPLES)
    system = ("Track the state of a question about customer-service calls. Output only what the follow-up changes, as "
              "operations on slots; leave every other slot alone. Values: event in " + ", ".join(EVENTS) +
              "; industry in " + ", ".join(INDUSTRIES) + "; question_type in " + ", ".join(QUESTION_TYPES) +
              ". Ask to clarify when the follow-up is ambiguous.\n\n" + shots)
    state = {"event": prev.event, "question_type": prev.question_type, "filters": prev.filters}
    out = llm.json_call(system=system, user=f"STATE: {json.dumps(state)}\nFOLLOW-UP: {text}\nDELTA:",
                        schema=LLM_DELTA_SCHEMA, purpose="delta", effort="low")
    ops = []
    for op in out["ops"]:
        v = op["value"]
        if op["slot"] in ("industry", "brand", "intent"):
            v = [v] if op["op"] != "remove" else None
        ops.append({"op": op["op"], "slot": op["slot"], "value": v})
    return {"ops": ops, "reset": False, "clarify": out["clarify"], "notices": {}}


class Engine:
    def __init__(self, art: Artifacts, settings, parser: QueryParser, llm=None, use_llm_writer: bool = False,
                 use_llm_parser: bool = False):
        self.art, self.s, self.parser = art, settings, parser
        self.llm = llm if (llm is not None and getattr(llm, "available", False)) else None
        self.use_llm_writer = use_llm_writer and self.llm is not None
        self.use_llm_parser = use_llm_parser and self.llm is not None
        self.builder = PackBuilder(art, settings)
        lib = art.library
        self.levels = dict(zip(lib["factor_id"], lib["level"]))
        self.cache: dict = {}

    def cache_key(self, spec: QuerySpec, shown: list) -> str:
        blob = json.dumps({"spec": spec.key(), "library": self.art.library_version, "index": self.art.index_version,
                           "writer": WRITER_VERSION if not self.use_llm_writer else f"llm:{getattr(self.llm, 'model', '')}",
                           "shown": shown if spec.question_type == "describe_factor" else []}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    def answer_spec(self, spec: QuerySpec, state: SessionState, query_text: str) -> dict:
        ref = spec.factor_ref
        if spec.event is None and ref and ref.startswith("#") and ref[1:].isdigit():
            k = int(ref[1:]) - 1
            ref = state.shown_factor_ids[k] if 0 <= k < len(state.shown_factor_ids) else ref
        if spec.event is None and ref and ref.startswith("F"):
            row = self.art.library[self.art.library["factor_id"] == ref]
            if len(row):
                spec.event, spec.question_type, spec.ambiguous = str(row.iloc[0]["event"]), "describe_factor", ""
        key = self.cache_key(spec, state.shown_factor_ids)
        if key in self.cache:
            return dict(self.cache[key], cache_hit=True)
        pack = self.builder.build(spec, shown=state.shown_factor_ids)
        if spec.ambiguous and "event" not in pack:
            pack["clarify"] = f"Could you clarify: {spec.ambiguous}"
        if spec.question_type == "examples" and self.art.index is not None and "event" in pack:
            pack["examples"] = self.examples(spec, query_text)
        if self.use_llm_writer and "event" in pack and not pack.get("clarify") and not pack.get("call"):
            try:
                sents = llm_write(self.llm, pack)
                rewrite = (lambda failed: llm_write(self.llm, pack, failed))
            except Exception as exc:
                sents, rewrite = write_answer(pack, spec), None
                pack["notices"].append({"kind": "writer", "text": f"(template writer used: {type(exc).__name__})"})
        else:
            sents, rewrite = write_answer(pack, spec), None
        res = finalize(sents, pack, self.levels, self.art.turn_text, rewrite=rewrite)
        if res["degraded"] and rewrite is not None:
            res = finalize(write_answer(pack, spec), pack, self.levels, self.art.turn_text)
        out = {"text": res["text"], "sentences": res["sentences"], "dropped": res["dropped"], "degraded": res["degraded"],
               "rewrites": res["rewrites"], "pack": pack, "spec": spec.to_dict(), "cache_hit": False,
               "levels": {f: self.levels.get(f) for f in dict.fromkeys(x for s in res["sentences"] for x in s["factor_ids"])},
               "versions": {"library": self.art.library_version, "index": self.art.index_version, "writer": WRITER_VERSION}}
        self.cache[key] = out
        return out

    def read_question(self, text: str) -> QuerySpec:
        spec = self.parser.parse(text)
        if self.llm is None:
            return spec
        foreign = any(n.get("kind") in ("language", "reading") for n in spec.notes)
        try:
            if unsure(spec) or foreign:
                norm = llm_normalize(self.llm, text)
                eng = str(norm.get("english") or "").strip()
                if eng:
                    spec2 = self.parser.parse(eng)
                    if not unsure(spec2) or unsure(spec):
                        spec2.raw = text
                        spec2.notes = [{"kind": "llm_reading", "text": eng, "language": str(norm.get("language") or "")}]
                        spec = spec2
            if self.use_llm_parser:
                spec = llm_parse(self.llm, text, spec)
        except Exception:
            pass
        return spec

    def examples(self, spec: QuerySpec, query_text: str, n: int = 5) -> list[dict]:
        e = spec.event
        filt = {"split": ["dev", "test"]}
        for k in ("industry", "brand"):
            if spec.filters.get(k):
                filt[k] = spec.filters[k]
        if spec.behaviour:
            filt[f"pos_{e}"] = ["before", "contains"]
            filt["behaviour"] = [spec.behaviour]
        else:
            filt[f"pos_{e}"] = ["contains"]
        conds = [c for c in spec.filters.get("with_event") or [] if f"{c}_onset" in self.art.labels.columns]
        hits = self.art.index.search(retrieval_text(spec, query_text), filt, top_k=n * (8 if conds else 2))
        onset = self.art.labels[f"{e}_onset"]
        out = []
        for h in hits:
            tid = h["transcript_id"]
            if any(int(self.art.labels[f"{c}_onset"].get(tid, -1)) < 0 for c in conds):
                continue
            on = int(onset.get(tid, -1))
            turn = None
            if spec.behaviour:
                for ln in h["text"].split("\n"):
                    k = int(ln.split("]")[0].strip("["))
                    if (on < 0 or k < on) and _line_has(ln, spec.behaviour):
                        turn = k
                        break
            elif h["start"] <= on <= h["end"]:
                turn = on
            if turn is None:
                continue
            uid = f"{tid}:{turn}"
            txt = self.art.turn_text.get(uid)
            if txt:
                out.append({"quote": txt, "turn_uid": uid, "transcript_id": tid, "turn_id": turn})
            if len(out) >= n:
                break
        return out

    def ask(self, text: str, state: SessionState | None = None) -> tuple[dict, SessionState]:
        t0 = time.time()
        state = state or SessionState(library_version=self.art.library_version, index_version=self.art.index_version)
        if state.library_version and state.library_version != self.art.library_version:
            state.history.append({"note": "library updated mid-session; previous answers used an older version"})
            state.library_version = self.art.library_version
        prev = restore_spec(state.spec) if state.spec is not None else None
        m = QUOTE_REF_RE.search(_norm(text))
        calls_quoted = list(dict.fromkeys(str(u).rsplit(":", 1)[0] for u in state.quoted if ":" in str(u)))
        if m and calls_quoted and prev is not None and not self.parser.parse(text).filters.get("call"):
            k = QUOTE_ORDINAL.get(m.group(1) or "", 0)
            if -len(calls_quoted) <= k < len(calls_quoted):
                text = f"{text} (call {calls_quoted[k]})"
        if prev is None:
            spec = self.read_question(text)
            if state.spec is not None:
                spec.notes = spec.notes + [{"kind": "restart"}]
                state.spec, state.shown_factor_ids = None, []
            delta, rt = None, "first"
        else:
            delta = propose_delta(prev, text, self.parser)
            if self.llm is not None and (self.use_llm_parser or delta["clarify"]):
                try:
                    ld = llm_delta(self.llm, prev, text)
                    ld["notices"] = delta["notices"]
                    ld["ops"] += [op for op in delta["ops"] if op["slot"] in RULE_SLOTS]
                    if not validate_delta(ld, self.parser) and (ld["ops"] or ld["clarify"]):
                        delta = ld
                except Exception:
                    pass
            problems = validate_delta(delta, self.parser)
            if problems:
                delta["clarify"] = "I could not apply that change (" + "; ".join(problems) + "). Could you rephrase?"
            spec = merge(prev, delta, text) if not delta["clarify"] else prev
            rt = route(prev, spec, delta)
        if rt == "clarify":
            ans = {"text": delta["clarify"], "sentences": [{"text": delta["clarify"], "kind": "clarify", "factor_ids": [],
                                                            "turn_uids": []}], "dropped": [], "degraded": False,
                   "rewrites": 0, "pack": {}, "spec": state.spec, "cache_hit": False, "levels": {}, "versions": {}}
        else:
            ans = self.answer_spec(spec, state, text)
            unknown_call = (ans.get("pack") or {}).get("call", {}).get("found") is False
            if unknown_call and prev is not None:
                ans["route"] = rt = "clarify"
            state.spec = None if unknown_call and prev is None else prev.to_dict() if unknown_call else spec.to_dict()
            rk = (ans.get("pack") or {}).get("rank") or {}
            if rk.get("dimension") == "event" and rk.get("groups"):
                state.spec["event"] = rk["groups"][0]["value"]
            elif rk.get("groups") and state.spec.get("compare"):
                state.spec["compare"]["top"] = rk["groups"][0]["value"]
            factor_order = [f["id"] for f in ans["pack"].get("factors", [])]
            if spec.question_type != "describe_factor" and factor_order:
                state.shown_factor_ids = factor_order
            state.shown_turn_uids = list(dict.fromkeys(state.shown_turn_uids + [u for s in ans["sentences"] for u in s["turn_uids"]]))[-50:]
            state.summary = [s["text"] for s in ans["sentences"] if s.get("core")][:3]
            if not unknown_call:
                state.quoted = [u for s in ans["sentences"] if s["kind"] == "quote" for u in s["turn_uids"]][:20]
        state.turn_count += 1
        state.history.append({"question": text, "route": rt, "delta": delta["ops"] if delta else None,
                              "spec_key": QuerySpec.from_dict(state.spec).key() if state.spec else None})
        ans.update({"question": text, "route": rt, "delta": delta, "seconds": round(time.time() - t0, 3)})
        return ans, state


def _line_has(line: str, behaviour: str) -> bool:
    from .query import find_behaviours
    return any(b == behaviour for _, b in find_behaviours(line))
