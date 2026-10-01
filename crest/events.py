from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .churn import churn_signals, sentence_encoder
from .cues import cue_view
from .definitions import CANCEL_DONE_RE, CHURN_SUBTYPE_RES, EVENTS, GRANT_RE, PRIMARY_EVENTS
from .stats import bootstrap_ci, cohen_kappa, weighted_prf

HELD_OUT = ("dev", "test")
TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
SENIOR = (r"(?:supervisors?|managers?|management|team lead(?:er)?s?|senior (?:agents?|representatives?|colleagues?|staff|team)|"
          r"escalations? (?:team|department|desk)|higher[- ]ups?)")
DET = r"(?:(?:my|a|the|our|your)\s+(?:\w+\s+)?)?"
ESC_HANDOFF_RE = re.compile(
    r"\bescalat\w*\b(?:\s+\S+){0,8}?\s+(?:to|with)\s+" + DET + SENIOR +
    r"|\b(?:get|grab|bring(?: in)?|fetch|call(?: over)?|loop in|involve|page|have)\s+(?:my|a|the|our)\s+" + SENIOR +
    r"|\b(?:check|speak|talk|consult|confer)\w*\s+with\s+(?:my|a|the|our)\s+" + SENIOR +
    r"|\b(?:transfer\w*|connect\w*|put\w*|pass\w*|hand\w*)\s+(?:you|this|your call|the call|it)\s+(?:over\s+|through\s+|across\s+)?"
    r"(?:to|with)\s+(?:my|a|the|our)\s+" + SENIOR +
    r"|\b(?:my|a|the|our)\s+(?:supervisor|manager|team lead(?:er)?)\s+(?:will|is going to|is here|is on the line|has joined|"
    r"is joining|will be with you|is coming|can (?:help|take|speak|look))\b")
ESC_OFFER_RE = re.compile(r"\b(?:would you like (?:me )?to|do you want me to|want me to|shall i|should i|i can|i could|"
                          r"i'?d be happy to|happy to|if you'?d like|if you want|i (?:recommend|suggest)|we can|we could|"
                          r"let me know if)\b")
ESC_COND_RE = re.compile(r"\bif (?:necessary|needed|need be|required|it comes to that|that'?s necessary|it'?s necessary|"
                         r"you (?:want|wish|prefer|need|insist))\b|\bif (?:this|that|it) (?:doesn'?t|does not|isn'?t|is not|still)\b")
ESC_ANY_OFFER_RE = re.compile(r"\b(?:would you like (?:me )?to|do you want me to|want me to|shall i|should i|i can|i could|"
                              r"if you'?d like|if you want|i (?:recommend|suggest))\b(?:\s+\S+){0,6}?\s+escalat\w*")
ACCEPT_RE = re.compile(r"^(?:(?:oh|well|okay so|so|hmm|alright then)\s+)?(?:yes|yeah|yep|yup|sure|please|ok(?:ay)?|alright|"
                       r"all right|that would|that'?d|go ahead|do that|i'?d (?:appreciate|like) (?:that|it)|absolutely|"
                       r"definitely|of course|fine|that sounds|sounds good|let'?s do|i would)\b")
ESC_CUSTOMER_EXTRA_RE = re.compile(r"\b(?:someone|somebody|anyone|a person) (?:above you|higher up|higher|more senior|senior|"
                                   r"in charge|with (?:more )?authority)\b|\b(?:speak|talk)\w* to your (?:superior|boss|"
                                   r"supervisor|manager)\b")
COMPETITORS = (r"(?:marriott|hilton|hyatt|airbnb|vrbo|ihg|holiday inn|sheraton|westin|radisson|wyndham|best western|"
               r"four seasons|ritz(?:[- ]carlton)?|accor|novotel|expedia|booking(?:\.com| dot com)|verizon|at ?& ?t|t-?mobile|"
               r"sprint|comcast|xfinity|spectrum|vodafone|airtel|jio|chase|wells fargo|bank of america|citi(?:bank)?|"
               r"capital one|delta|united airlines|american airlines|southwest|jetblue|emirates|lufthansa|british airways|"
               r"geico|progressive|state farm|allstate|amazon|walmart|ebay)")
OTHER_PROVIDER = (r"(?:elsewhere|somewhere else|(?:another|a different|a new|some other|other|the other|different) (?:hotels?|"
                  r"hotel chains?|chains?|brands?|compan(?:y|ies)|providers?|carriers?|airlines?|banks?|insurers?|stores?|"
                  r"options?|places?|services?)|the competition|(?:a |your |one of your )?competitors?|" + COMPETITORS + ")")
INTENT = (r"(?:considering|considered|consider|thinking (?:about|of)|thought (?:about|of)|plan(?:ning)? (?:to|on)|going to|gonna|"
          r"about to|ready to|tempted to|wonder(?:ing)? if i should|"
          r"might|may|could|will|would|i'?ll|i'?d|rather|should|need to|want to|have to|maybe|perhaps|probably|"
          r"i'?m|i am|we'?re|we are)")
CHURN_EXTRA_RE = re.compile(
    r"\b" + INTENT + r"(?:\s+\w+){0,3}?\s+(?:switch\w*|mov(?:e|ing)|tak(?:e|ing) (?:my|our) business|go(?:ing)?|look(?:ing)?|"
    r"check(?:ing)?(?: out)?|stay(?:ing)?|book(?:ing)?|try(?:ing)?|us(?:e|ing)|shop(?:ping)?)\s+(?:over\s+|just\s+)?"
    r"(?:to|with|at|into|for)?\s*(?:the\s+)?" + OTHER_PROVIDER + r"\b"
    r"|\b(?:look|go|shop|book|stay|take my business)\w*\s+elsewhere\b"
    r"|\b(?:question\w*|rethink\w*|reconsider\w*|re-?evaluat\w*|affect\w*|hurt\w*|test\w*|los(?:e|ing)|lost)\s+(?:my|our)\s+"
    r"(?:loyalty|membership|relationship|business|trust)\b(?!\s+(?:status|points?|tiers?|levels?|benefits?|perks?|rewards?|"
    r"program\w*|numbers?|accounts?|cards?|discounts?|codes?))"
    r"|\b(?:consider\w*|thinking (?:about|of)|thought (?:about|of)|might|may|could|should|will|i'?ll|going to|gonna)\s+"
    r"(?:\w+\s+){0,2}?switch(?:ing)?\b(?!\s+(?:from|rooms?|dates?|to (?:a |the )?(?:suite|room|date|plan|package|card)))"
    r"|\bwhy (?:should|would) i (?:stick|stay) with\b"
    r"|\b(?:not|never|won'?t|wouldn'?t|will not|would not)\s+(?:be\s+)?(?:book\w*|stay\w*|com\w*)\s+(?:back\s+)?"
    r"(?:with|at|to)\s+(?:you|your|this)\w*(?:\s+\w+)?\s+(?:again|anymore|any more)\b")
CHURN_NOT_RE = re.compile(
    r"\bswitch\w*\s+(?:over\s+)?from\b|\b(?:came|moved|switched|converted)\s+(?:over\s+)?(?:here\s+)?from\b|"
    r"\b(?:almost|nearly|should'?ve|should have|could'?ve|could have)\s+(?:\w+\s+)?(?:switch\w*|mov\w*|gone|went|left|cancel\w*)|"
    r"\b(?:don'?t|do not|didn'?t|did not|wouldn'?t|would not|won'?t|will not|never|not)\s+(?:\w+\s+){0,2}?"
    r"(?:want to |wanna |going to |gonna |plan(?:ning)? to |intend(?:ing)? to )?(?:switch\w*|mov(?:e|ing)|leav\w*|"
    r"cancel\w*|go(?:ing)? (?:to|with)|look\w* elsewhere)")


def empty_label_table(call_ids) -> pd.DataFrame:
    df = pd.DataFrame(index=pd.Index(call_ids, name="transcript_id"))
    for e in EVENTS:
        df[f"{e}_onset"] = -1
        df[f"{e}_subtype"] = ""
    return df


def first_turn_per_call(corpus, mask: np.ndarray) -> np.ndarray:
    first = np.full(corpus.n_calls, -1, dtype=np.int64)
    idx = np.flatnonzero(mask)
    if idx.size:
        calls = corpus.turns["call_idx"].to_numpy()[idx]
        uniq, pos = np.unique(calls, return_index=True)
        first[uniq] = corpus.turns["turn_id"].to_numpy()[idx[pos]]
    return first


def _shift_within_call(corpus, values: np.ndarray, lag: int) -> np.ndarray:
    out = np.zeros_like(values)
    if lag >= len(values):
        return out
    same = corpus.turns["call_idx"].to_numpy()
    ok = np.zeros(len(values), dtype=bool)
    ok[lag:] = same[lag:] == same[:-lag]
    out[lag:] = values[:-lag]
    return np.where(ok, out, np.zeros_like(out))


def _next_within_call(corpus, values: np.ndarray, lead: int = 1) -> np.ndarray:
    out = np.zeros_like(values)
    if lead >= len(values):
        return out
    same = corpus.turns["call_idx"].to_numpy()
    ok = np.zeros(len(values), dtype=bool)
    ok[:-lead] = same[:-lead] == same[lead:]
    out[:-lead] = values[lead:]
    return np.where(ok, out, np.zeros_like(out))


def _match(rx: re.Pattern, texts) -> np.ndarray:
    return np.fromiter((bool(rx.search(x)) for x in texts), dtype=bool, count=len(texts))


def agent_escalation_turns(corpus, view, agent: np.ndarray, cust: np.ndarray) -> np.ndarray:
    handoff = agent & _match(ESC_HANDOFF_RE, view)
    offer = agent & ((_match(ESC_OFFER_RE, view) & handoff) | _match(ESC_ANY_OFFER_RE, view))
    cond = agent & _match(ESC_COND_RE, view)
    committed = handoff & ~offer & ~cond
    accepts = cust & _match(ACCEPT_RE, view)
    accepted = (offer | (handoff & cond)) & (_next_within_call(corpus, accepts, 1) | _next_within_call(corpus, committed, 2))
    return committed | accepted


def churn_turns(view, cust: np.ndarray, cue: np.ndarray) -> np.ndarray:
    extra = cust & _match(CHURN_EXTRA_RE, view)
    return cust & (cue | extra) & ~_match(CHURN_NOT_RE, view)


COMPETITOR_WORD_RE = re.compile(r"\b" + COMPETITORS + r"\b")
REF_EXTRA_RE = re.compile(r"\b(?:(?:my|our|the) money (?:returned|refunded)|return (?:my|our|the) money|(?:get|want|need) (?:my|our) "
                          r"money (?:back|returned))\b")


def lexicon_labels(corpus, semantic: bool = True, threshold: float = 0.9, encoder: str = "auto",
                   st_model: str = "sentence-transformers/all-MiniLM-L6-v2") -> pd.DataFrame:
    t = corpus.turns
    cust = (t["party"] == "Customer").to_numpy()
    agent = ~cust
    sup = (t["speaker"] == "Supervisor").to_numpy()
    view = [cue_view(str(x)) for x in t["text_clean"].to_numpy()]
    esc_req = (t["cue_escalation_request"].to_numpy() | _match(ESC_CUSTOMER_EXTRA_RE, view)) & cust
    esc_agent = agent_escalation_turns(corpus, view, agent, cust)
    refund = t["cue_refund"].to_numpy() | _match(REF_EXTRA_RE, view)
    explicit = cust & (t["cue_churn_intent"].to_numpy() | _match(CHURN_EXTRA_RE, view))
    sig = churn_signals(t, view, cust, explicit, _match(CHURN_NOT_RE, view), _match(COMPETITOR_WORD_RE, view), semantic,
                        threshold, sentence_encoder(st_model) if semantic and encoder == "auto" else None)
    churn = sig["churn"]
    refusal = t["cue_refusal"].to_numpy() & agent
    text = t["text_clean"].to_numpy()
    lab = empty_label_table(corpus.call_ids)
    tid_of_turn = t["transcript_id"].to_numpy()

    def put(code: str, mask: np.ndarray, subtype_fn=None):
        onset = first_turn_per_call(corpus, mask)
        lab[f"{code}_onset"] = onset
        if subtype_fn is not None:
            sub = np.array([""] * corpus.n_calls, dtype=object)
            has = onset >= 0
            rows = corpus.call_start[has] + onset[has]
            sub[has] = [subtype_fn(int(r)) for r in rows]
            lab[f"{code}_subtype"] = sub

    put("ESC", esc_req | esc_agent | sup, lambda r: "customer_request" if esc_req[r] else "agent_handoff")
    put("REF", refund, lambda r: "customer_request" if cust[r] else "agent_offer")
    put("CHURN", churn, lambda r: next((name for name, rx in CHURN_SUBTYPE_RES if rx.search(text[r])), "other"))
    put("HANDOFF", sup, lambda r: "supervisor")
    grant = agent & np.array([bool(GRANT_RE.search(x)) for x in text]) & (refund | _shift_within_call(corpus, refund & cust, 1))
    put("REF_GRANTED", grant, lambda r: "granted")
    cust_ref = refund & cust
    denied = refusal & (refund | _shift_within_call(corpus, cust_ref, 1) | _shift_within_call(corpus, cust_ref, 2))
    put("REF_DENIED", denied, lambda r: "denied")
    cancel_done = agent & np.array([bool(CANCEL_DONE_RE.search(x)) for x in text])
    put("CANCEL_DONE", cancel_done, lambda r: "done")
    put("RISK", sig["risk"], lambda r: str(sig["risk_kind"][r]) or "explicit")
    lab.attrs["churn_detector"] = sig["info"]
    if corpus.n_calls and not (tid_of_turn[corpus.call_start] == np.asarray(corpus.call_ids)).all():
        raise ValueError("turn table and call table are out of alignment (per-call turn offsets do not match)")
    return lab


def event_sequence(labels: pd.DataFrame) -> pd.Series:
    rows = []
    cols = [e for e in EVENTS]
    onsets = labels[[f"{e}_onset" for e in cols]].to_numpy()
    for r in onsets:
        seq = sorted(((cols[j], int(v)) for j, v in enumerate(r) if v >= 0), key=lambda x: (x[1], x[0]))
        rows.append(json.dumps(seq))
    return pd.Series(rows, index=labels.index, name="event_sequence")


LLM_EVENT_SCHEMA = {
    "type": "object",
    "properties": {e: {
        "type": "object",
        "properties": {"present": {"type": "boolean"},
                       "onset_turn": {"type": "integer"},
                       "onset_quote": {"type": "string"},
                       "subtype": {"type": "string", "enum": list(EVENTS[e].subtypes) + ["none"]}},
        "required": ["present", "onset_turn", "onset_quote", "subtype"],
        "additionalProperties": False} for e in PRIMARY_EVENTS},
    "required": list(PRIMARY_EVENTS),
    "additionalProperties": False,
}


def _llm_system_prompt() -> str:
    lines = ["You label customer-service call transcripts. The turns are numbered from 0.",
             "For each event below decide whether it happens in the call and, if it does, give the number of the FIRST "
             "turn where it happens and copy the exact words of that turn that show it (onset_quote).",
             "If the event does not happen, set present=false, onset_turn=-1, onset_quote=\"\" and subtype=\"none\".",
             "Use only what is said in the transcript. Do not guess from the topic of the call."]
    for e in PRIMARY_EVENTS:
        d = EVENTS[e]
        lines.append(f"- {e} ({d.name}): {d.onset_rule}. Subtypes: {', '.join(d.subtypes)}.")
    return "\n".join(lines)


def render_call(turns: pd.DataFrame) -> str:
    return "\n".join(f"[{int(r.turn_id)}] {r.speaker}: {r.text}" for r in turns.itertuples(index=False))


def quote_matches(quote: str, turn_text: str, min_recall: float = 0.9) -> bool:
    q = TOKEN_RE.findall(quote.lower())
    if not q:
        return False
    words = set(TOKEN_RE.findall(turn_text.lower()))
    return sum(w in words for w in q) / len(q) >= min_recall


def stratified_sample(ids: np.ndarray, flagged: np.ndarray, n_flagged: int, n_unflagged: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for stratum, mask, n in (("flagged", flagged, n_flagged), ("unflagged", ~flagged, n_unflagged)):
        pool = ids[mask]
        k = int(min(max(n, 0), pool.size))
        if k == 0:
            continue
        chosen = rng.choice(pool, size=k, replace=False)
        rows += [{"transcript_id": c, "stratum": stratum, "pi": k / pool.size} for c in sorted(chosen)]
    return pd.DataFrame(rows, columns=["transcript_id", "stratum", "pi"])


def llm_dev_labels(corpus, lexicon: pd.DataFrame, llm, size: int, seed: int) -> pd.DataFrame:
    calls = corpus.calls
    train_ids = calls.index[calls["split"] == "train"].to_numpy()
    flagged = (lexicon.loc[train_ids, [f"{e}_onset" for e in PRIMARY_EVENTS]].to_numpy() >= 0).any(axis=1)
    n_f = min(int(flagged.sum()), size // 2)
    sample = stratified_sample(train_ids, flagged, n_f, size - n_f, seed)
    system = _llm_system_prompt()
    rows = []
    for tid in sample["transcript_id"]:
        turns = corpus.turns_of(tid)
        out = llm.json_call(system=system, user=render_call(turns), schema=LLM_EVENT_SCHEMA, purpose="event_labels")
        rec = {"transcript_id": tid}
        for e in PRIMARY_EVENTS:
            r = out.get(e, {})
            onset = int(r.get("onset_turn", -1)) if r.get("present") else -1
            ok = True
            if onset >= 0:
                ok = 0 <= onset < len(turns) and quote_matches(str(r.get("onset_quote", "")), turns["text"].iloc[onset])
            rec[f"{e}_onset"] = onset if ok else -1
            rec[f"{e}_verified"] = ok
            rec[f"{e}_subtype"] = r.get("subtype", "none") if ok and onset >= 0 else ""
        rows.append(rec)
    out = sample.merge(pd.DataFrame(rows), on="transcript_id")
    return out


def _turn_text_pairs(corpus) -> list[str]:
    t = corpus.turns
    prev = np.concatenate([[""], t["text_clean"].to_numpy()[:-1]]).astype(object)
    first = t["turn_id"].to_numpy() == 0
    prev[first] = ""
    party = t["party"].str.lower().to_numpy()
    return [f"{p} :: {a} || {b}" for p, a, b in zip(party, prev, t["text_clean"].to_numpy())]


def train_onset_detectors(corpus, dev: pd.DataFrame, seed: int = 0) -> dict:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    texts = _turn_text_pairs(corpus)
    t = corpus.turns
    idx_of = {tid: i for i, tid in enumerate(corpus.call_ids)}
    dev_idx = np.array([idx_of[x] for x in dev["transcript_id"]])
    call_of_turn = t["call_idx"].to_numpy()
    in_dev = np.isin(call_of_turn, dev_idx)
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=50_000, sublinear_tf=True, dtype=np.float32)
    vec.fit([texts[i] for i in np.flatnonzero(in_dev)])
    detectors = {"vectorizer": vec, "models": {}, "thresholds": {}}
    dev_onset = {e: dict(zip(dev["transcript_id"], dev[f"{e}_onset"])) for e in PRIMARY_EVENTS}
    tids = t["transcript_id"].to_numpy()
    turn_id = t["turn_id"].to_numpy()
    rows = np.flatnonzero(in_dev)
    X = vec.transform([texts[i] for i in rows])
    for e in PRIMARY_EVENTS:
        on = np.array([dev_onset[e][tids[i]] for i in rows])
        keep = (on < 0) | (turn_id[rows] <= on)
        y = (turn_id[rows] == on) & (on >= 0)
        if y[keep].sum() < 5:
            detectors["models"][e] = None
            continue
        clf = LogisticRegression(C=4.0, max_iter=2000, class_weight="balanced", random_state=seed)
        clf.fit(X[keep], y[keep])
        detectors["models"][e] = clf
        p = clf.predict_proba(X)[:, 1]
        best, best_thr = -1.0, 0.5
        calls_rows = pd.Series(p).groupby(tids[rows]).max()
        truth = pd.Series({k: v >= 0 for k, v in dev_onset[e].items()})
        for thr in np.linspace(0.2, 0.95, 16):
            pred = calls_rows >= thr
            tp = float((pred & truth.reindex(pred.index)).sum())
            fp = float((pred & ~truth.reindex(pred.index)).sum())
            fn = float((~pred & truth.reindex(pred.index)).sum())
            f1 = 2 * tp / (2 * tp + fp + fn) if tp else 0.0
            if f1 > best:
                best, best_thr = f1, float(thr)
        detectors["thresholds"][e] = best_thr
    return detectors


def detector_labels(corpus, detectors: dict, fallback: pd.DataFrame) -> pd.DataFrame:
    lab = fallback.copy()
    texts = _turn_text_pairs(corpus)
    X = detectors["vectorizer"].transform(texts)
    for e in PRIMARY_EVENTS:
        clf = detectors["models"].get(e)
        if clf is None:
            continue
        p = clf.predict_proba(X)[:, 1]
        lab[f"{e}_onset"] = first_turn_per_call(corpus, p >= detectors["thresholds"][e])
        lab[f"{e}_subtype"] = np.where(lab[f"{e}_onset"] >= 0, "detected", "")
    return lab


GOLD_EVENTS = PRIMARY_EVENTS


def draw_gold_sample(corpus, labels: pd.DataFrame, n_random: int, n_stress: int, n_double: int, seed: int) -> pd.DataFrame:
    calls = corpus.calls
    ids = calls.index[calls["split"].isin(HELD_OUT)].to_numpy()
    if ids.size == 0:
        raise ValueError("no held-out (dev/test) calls: the gold set must come from held-out calls")
    flagged = (labels.loc[ids, [f"{e}_onset" for e in GOLD_EVENTS]].to_numpy() >= 0).any(axis=1)
    share = flagged.mean()
    n_f = int(round(n_random * share)) + n_stress
    n_u = n_random - int(round(n_random * share))
    sample = stratified_sample(ids, flagged, n_f, n_u, seed)
    rng = np.random.default_rng(seed + 1)
    dbl = set(rng.choice(sample["transcript_id"].to_numpy(), size=min(n_double, len(sample)), replace=False)) if len(sample) else set()
    sample["double_coded"] = sample["transcript_id"].isin(dbl)
    return sample


GOLD_README = """GOLD LABELLING INSTRUCTIONS (blind: do not look at any model output)

For each call file in this folder, read the numbered turns and fill in gold_to_label.csv:
  * <EVENT>_present : yes / no
  * <EVENT>_onset   : number of the FIRST turn where the event happens (leave empty if not present)
  * <EVENT>_subtype : one of the allowed values below (leave empty if not present)
Rows with annotator = B are the double-coded calls: a second person labels them independently.
If A and B disagree, add a third row for that call with annotator = ADJ holding the agreed labels.

Events:
{events}
"""


def write_gold_packets(corpus, sample: pd.DataFrame, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "calls").mkdir(exist_ok=True)
    for tid in sample["transcript_id"]:
        (folder / "calls" / f"{tid}.txt").write_text(render_call(corpus.turns_of(tid)) + "\n", encoding="utf-8")
    ev = "\n".join(f"  {e}: {EVENTS[e].onset_rule}. Subtypes: {', '.join(EVENTS[e].subtypes)}" for e in GOLD_EVENTS)
    (folder / "README.txt").write_text(GOLD_README.format(events=ev), encoding="utf-8")
    rows = []
    for r in sample.itertuples(index=False):
        for ann in (["A", "B"] if r.double_coded else ["A"]):
            row = {"transcript_id": r.transcript_id, "annotator": ann}
            for e in GOLD_EVENTS:
                row.update({f"{e}_present": "", f"{e}_onset": "", f"{e}_subtype": ""})
            rows.append(row)
    path = folder / "gold_to_label.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


_YES = {"yes", "y", "true", "1", "1.0"}
_NO = {"no", "n", "false", "0", "0.0"}


def _parse_label_row(row, n_turns: int, problems: list, tid: str, ann: str) -> dict:
    out = {}
    for e in GOLD_EVENTS:
        pres = str(row.get(f"{e}_present", "")).strip().lower()
        if pres in _YES:
            present = True
        elif pres in _NO:
            present = False
        else:
            problems.append(f"{tid} ({ann}): {e}_present must be yes/no, got {pres!r}")
            continue
        onset = -1
        if present:
            raw = str(row.get(f"{e}_onset", "")).strip()
            try:
                onset = int(float(raw))
            except ValueError:
                problems.append(f"{tid} ({ann}): {e}_onset missing or not a number ({raw!r})")
                continue
            if not 0 <= onset < n_turns:
                problems.append(f"{tid} ({ann}): {e}_onset {onset} outside 0..{n_turns - 1}")
                continue
            sub = str(row.get(f"{e}_subtype", "")).strip()
            if sub and sub.lower() != "nan" and sub not in EVENTS[e].subtypes:
                problems.append(f"{tid} ({ann}): {e}_subtype {sub!r} not in {EVENTS[e].subtypes}")
        out[e] = onset
    return out


def ingest_gold(path: Path, sample: pd.DataFrame, corpus) -> pd.DataFrame:
    from .io import DataValidationError
    df = pd.read_csv(path, dtype=str).fillna("")
    problems: list[str] = []
    df["annotator"] = df["annotator"].str.strip().str.upper()
    sampled = set(sample["transcript_id"])
    extra = set(df["transcript_id"]) - sampled
    if extra:
        problems.append(f"{len(extra)} labelled calls are not in the gold sample (e.g. {sorted(extra)[:3]})")
    parsed = {}
    for r in df.to_dict("records"):
        tid, ann = r["transcript_id"], r["annotator"]
        if tid not in sampled:
            continue
        n_turns = int(corpus.calls.loc[tid, "n_turns"])
        parsed[(tid, ann)] = _parse_label_row(r, n_turns, problems, tid, ann)
    final, pairs = [], []
    for s in sample.itertuples(index=False):
        a, b, adj = parsed.get((s.transcript_id, "A")), parsed.get((s.transcript_id, "B")), parsed.get((s.transcript_id, "ADJ"))
        if a is None or len(a) < len(GOLD_EVENTS):
            problems.append(f"{s.transcript_id}: annotator A labels missing or invalid")
            continue
        if s.double_coded:
            if b is None or len(b) < len(GOLD_EVENTS):
                problems.append(f"{s.transcript_id}: double-coded call needs annotator B labels")
                continue
            pairs.append((a, b))
            if a != b and adj is None:
                problems.append(f"{s.transcript_id}: A and B disagree -- add an ADJ row with the agreed labels")
                continue
        chosen = adj if adj is not None and len(adj) == len(GOLD_EVENTS) else a
        final.append({"transcript_id": s.transcript_id, "stratum": s.stratum, "pi": s.pi,
                      **{f"{e}_onset": chosen[e] for e in GOLD_EVENTS}})
    if problems:
        raise DataValidationError(problems[:50] + ([f"... and {len(problems) - 50} more"] if len(problems) > 50 else []))
    gold = pd.DataFrame(final)
    gold.attrs["pairs"] = pairs
    return gold


def gold_metrics(gold: pd.DataFrame, labels: pd.DataFrame, draws: int = 1000, seed: int = 0) -> dict:
    w = 1.0 / gold["pi"].to_numpy()
    out = {"n_gold_calls": int(len(gold)), "by_event": {}}
    pairs = gold.attrs.get("pairs", [])
    for e in GOLD_EVENTS:
        g_on = gold[f"{e}_onset"].to_numpy()
        p_on = labels.loc[gold["transcript_id"], f"{e}_onset"].to_numpy()
        yt, yp = g_on >= 0, p_on >= 0
        m = weighted_prf(yt, yp, w)

        def f1_of(ix):
            r = weighted_prf(yt[ix], yp[ix], w[ix])
            return r["f1"]
        ci = bootstrap_ci(f1_of, len(gold), draws, seed)
        both = yt & yp
        exact = float(np.mean(g_on[both] == p_on[both])) if both.any() else float("nan")
        within1 = float(np.mean(np.abs(g_on[both] - p_on[both]) <= 1)) if both.any() else float("nan")
        kappa = cohen_kappa([a[e] >= 0 for a, _ in pairs], [b[e] >= 0 for _, b in pairs]) if pairs else float("nan")
        out["by_event"][e] = {**m, "f1_ci": list(ci), "onset_exact": exact, "onset_within1": within1,
                              "n_gold_events": int(yt.sum()), "n_labeller_events": int(yp.sum()),
                              "kappa_presence": kappa, "n_double_coded": len(pairs)}
    return out
