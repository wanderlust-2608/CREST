from __future__ import annotations

import re

import numpy as np
import pandas as pd

DISENGAGE_RE = re.compile(
    r"\b(?:i'?m|i am|we'?re|we are)\s+(?:so\s+|just\s+|really\s+|totally\s+|completely\s+|honestly\s+)?(?:done|finished|"
    r"through)\s+with\s+(?:you(?:\s+(?:people|guys|all))?\b(?!\s+(?:now|for (?:now|today)))|your\s+(?:company|service|hotels?|brand|airline|bank|"
    r"business|people)|y'?all|this\s+(?:company|hotel|place|brand|airline|bank|service|chain))"
    r"|\bi'?ve had (?:it|enough)\s+with\s+(?:you|your|this)\b"
    r"|\b(?:you(?:'ve| have)?\s+)?(?:just\s+)?lost\s+(?:a|my|me as a|one)\s+(?:loyal\s+|long-?time\s+)?(?:customer|client|guest|"
    r"business)\b"
    r"|\b(?:never|not)\s+(?:going to\s+|gonna\s+)?(?:use|book\w*|fly\w*|stay\w*|call\w*|deal\w*\s+with|do business with|"
    r"come back to|return to)\s+(?:you|your\s+\w+|this\s+\w+|here)(?:\s+\w+)?\s+(?:again|ever again|anymore|any more)\b"
    r"|\b(?:find|look for|get)\s+(?:a|another|a new|a different|some other)\s+(?:provider|company|bank|hotel|airline|"
    r"carrier|insurer|service|place|chain)\b"
    r"|\bi want out\b|\bget me out of (?:this|my|the)\b"
    r"|\b(?:end|terminate)\s+(?:this|our|the|my)\s+(?:relationship|contract|membership|business)\b"
    r"|\bthis is the last (?:time|straw)\b"
    r"|\bwon'?t be (?:coming|calling|booking|staying|flying) (?:back|with you|again)\b"
    r"|\bnot worth (?:it|staying|the hassle|my money) anymore\b"
    r"|\b(?:i(?:'ll| will)|we(?:'ll| will))\s+(?:take|move)\s+(?:my|our)\s+(?:business|account)\s+(?:elsewhere|somewhere else)\b"
    r"|\b(?:i(?:'ll| will)|we(?:'ll| will))\s+(?:go|take my business|move)\s+(?:elsewhere|somewhere else)\b"
    r"|\b(?:i|we)\s+(?:will\s+)?(?:use|go with|choose)\s+(?:someone|somewhere|some other|another)\s+else\b"
    r"|\b(?:you(?:'ve| have)\s+)?lost\s+me\b")
WAVERING_RE = re.compile(
    r"\b(?:second thoughts|having doubts|losing (?:my )?(?:patience|faith|trust) in (?:you|your)|not sure (?:i'?ll|i will|if "
    r"i'?ll|whether i'?ll) (?:stay|keep|renew|book|come back)|thinking twice|last chance|one more chance|is this how you "
    r"treat (?:your )?(?:loyal|long-?time|valued) (?:customers|members|guests))\b")
LOYAL_RE = re.compile(r"\b(?:chose|choose|chosen|picked|prefer\w*|always (?:chosen|picked|stayed with|booked with))\b.{0,50}\bover\b"
                      r"|\b(?:coming|came|moved|switched|switching) (?:over |back )?from\b")
BOOKING_ONLY_RE = re.compile(
    r"\bcancel\w*\s+(?:my|the|this|our)\s+(?:booking|reservation|order|flight|stay|room|ticket|appointment)\b.*"
    r"\b(?:plans? (?:changed|change)|change of plans|no longer need|can'?t make it|schedule|emergency|sick|illness|family)\b")
LEAVE_LEXICON_RE = re.compile(
    r"\b(?:cancel\w*|switch\w*|leav\w*|quit\w*|done|elsewhere|another|other|competitor\w*|renew\w*|clos\w*|end\w*|business|"
    r"loyal\w*|never|again|anymore|finished|through|out)\b")
SEMANTIC_THRESHOLD = 0.9


def _call_cummax(call_idx: np.ndarray, values: np.ndarray) -> np.ndarray:
    return pd.Series(values.astype(np.int8)).groupby(call_idx).cummax().to_numpy().astype(bool)


def _recent(call_idx: np.ndarray, values: np.ndarray, lags: int) -> np.ndarray:
    out = np.zeros(len(values), dtype=bool)
    for lag in range(1, lags + 1):
        if lag >= len(values):
            break
        same = np.zeros(len(values), dtype=bool)
        same[lag:] = call_idx[lag:] == call_idx[:-lag]
        shifted = np.zeros(len(values), dtype=bool)
        shifted[lag:] = values[:-lag]
        out |= same & shifted
    return out


def _match(rx: re.Pattern, texts) -> np.ndarray:
    return np.fromiter((bool(rx.search(x)) for x in texts), dtype=bool, count=len(texts))


def sentence_encoder(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
    except Exception:
        return None
    return lambda texts: model.encode(list(texts), batch_size=256, show_progress_bar=False, normalize_embeddings=True)


def semantic_scores(texts: list[str], pos: np.ndarray, neg: np.ndarray, train: np.ndarray, cand: np.ndarray,
                    encoder=None, seed: int = 0):
    from scipy.sparse import hstack
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    fit_rows = np.flatnonzero(train & (pos | neg))
    if (pos & train).sum() < 20 or (neg & train).sum() < 50:
        return None, "skipped (too few rule-labelled turns to learn from)"
    rng = np.random.default_rng(seed)
    negs = fit_rows[~pos[fit_rows]]
    if len(negs) > 40 * pos[fit_rows].sum():
        negs = rng.choice(negs, size=int(40 * pos[fit_rows].sum()), replace=False)
    rows = np.concatenate([fit_rows[pos[fit_rows]], negs])
    fit_texts = [texts[i] for i in rows]
    score_rows = np.flatnonzero(cand)
    score_texts = [texts[i] for i in score_rows]
    out = np.zeros(len(texts))
    clf = LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000, random_state=seed)
    if encoder is not None:
        clf.fit(encoder(fit_texts), pos[rows])
        if len(score_rows):
            out[score_rows] = clf.predict_proba(encoder(score_texts))[:, 1]
        return out, "sentence-embeddings-weak-supervision"
    word = TfidfVectorizer(ngram_range=(1, 2), min_df=3, sublinear_tf=True, max_features=50_000)
    char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=5, sublinear_tf=True, max_features=80_000)
    Xw, Xc = word.fit_transform(fit_texts), char.fit_transform(fit_texts)
    clf.fit(hstack([Xw, Xc]).tocsr(), pos[rows])
    if len(score_rows):
        out[score_rows] = clf.predict_proba(hstack([word.transform(score_texts), char.transform(score_texts)]).tocsr())[:, 1]
    return out, "tfidf-weak-supervision"


def churn_signals(turns: pd.DataFrame, view: list[str], cust: np.ndarray, explicit: np.ndarray, negative: np.ndarray,
                  competitor_words: np.ndarray, use_semantic: bool = True, threshold: float = SEMANTIC_THRESHOLD,
                  encoder=None) -> dict:
    ci = turns["call_idx"].to_numpy()
    agent = ~cust
    disengage = cust & _match(DISENGAGE_RE, view)
    booking = cust & _match(BOOKING_ONLY_RE, view)
    negative = negative | booking
    complaint = cust & (turns["cue_negative_emotion"].to_numpy() | turns["cue_issue_persistence"].to_numpy() |
                        turns["cue_repeat_contact"].to_numpy())
    refused = agent & turns["cue_refusal"].to_numpy()
    unhappy = _call_cummax(ci, complaint) | _recent(ci, refused, 3)
    competitor = cust & (turns["cue_competitor_mention"].to_numpy() | competitor_words)
    rule_churn = cust & (explicit | disengage) & ~negative
    semantic = np.zeros(len(view), dtype=bool)
    info = {"semantic": "off"}
    if use_semantic and "split" in turns.columns:
        train = turns["split"].to_numpy() == "train"
        lexical = _match(LEAVE_LEXICON_RE, view)
        cand = cust & ~rule_churn & ~negative & (unhappy | competitor) & lexical
        neg = cust & ~(explicit | disengage) & ~_call_cummax(ci, rule_churn | competitor)
        scores, how = semantic_scores(view, rule_churn, neg, train, cand, encoder)
        info = {"semantic": how}
        if scores is not None:
            semantic = cand & (scores >= threshold)
            info.update({"threshold": threshold, "candidates": int(cand.sum()), "turns_added": int(semantic.sum()),
                         "rule_turns": int(rule_churn.sum())})
    churn = rule_churn | semantic
    wavering = cust & _match(WAVERING_RE, view) & ~negative
    competitor_risk = competitor & unhappy & ~negative & ~_match(LOYAL_RE, view)
    risk = churn | wavering | competitor_risk
    kind = np.where(churn, "explicit", np.where(competitor_risk, "competitor", np.where(wavering, "wavering", "")))
    info.update({"churn_turns": int(churn.sum()), "risk_turns": int(risk.sum()), "disengage_turns": int(disengage.sum())})
    return {"churn": churn, "risk": risk, "risk_kind": kind, "disengage": disengage, "semantic": semantic, "info": info}
