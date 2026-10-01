from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import scipy.sparse as sp

from .analysis import HELD_OUT
from .behaviours import treatment_mask
from .definitions import BEHAVIOURS, EVENTS
from .events import first_turn_per_call
from .landmarks import (EXTRA_BEHAVIOURS, _NOT_RECENT, exclusive_cumsum, opening_features, signal_spec, turn_signals)
from .stats import hashed_folds

FORECAST_SALT = "crest-forecaster-v1"
NEUTRAL_TEXT = "okay"


@dataclass
class TurnMaterial:
    S: np.ndarray
    E: np.ndarray | None
    excl_S: np.ndarray
    excl_E: np.ndarray | None
    party: np.ndarray
    speaker: np.ndarray
    text: np.ndarray
    call_start: np.ndarray
    neutral_E: np.ndarray | None = None
    _neutral_S: dict = field(default_factory=dict)

    def neutral_S(self, g: int) -> np.ndarray:
        key = (self.party[g], self.speaker[g])
        if key not in self._neutral_S:
            nt = neutral_turn(*key)
            occ = pd.DataFrame({b: [False] for b in EXTRA_BEHAVIOURS})
            self._neutral_S[key] = turn_signals(nt, occ).astype(np.float64)[0]
        return self._neutral_S[key]


def neutral_turn(party: str, speaker: str | None = None) -> pd.DataFrame:
    from .cues import CUE_COLS
    row = {"party": party, "speaker": speaker or party, "n_words": 1, "is_question": False, "is_backchannel": True,
           "n_filled_pauses": 0, "nonverbal_types": [[]], "text_clean": NEUTRAL_TEXT, "text": NEUTRAL_TEXT,
           "is_repeat": False, **{c: False for c in CUE_COLS}}
    return pd.DataFrame({k: (v if isinstance(v, list) else [v]) for k, v in row.items()})


def build_material(corpus, lm) -> TurnMaterial:
    from .behaviours import occurrence_matrix
    t = corpus.turns
    S = turn_signals(t, occurrence_matrix(t, EXTRA_BEHAVIOURS)).astype(np.float64)
    E = lm.embedder.transform(t["text_clean"].tolist())
    E = None if E is None else E.astype(np.float64)
    call_of = t["call_idx"].to_numpy()
    mat = TurnMaterial(S=S, E=E, excl_S=exclusive_cumsum(S, call_of), excl_E=None if E is None else exclusive_cumsum(E, call_of),
                       party=t["party"].to_numpy(), speaker=t["speaker"].astype(str).to_numpy(),
                       text=t["text_clean"].to_numpy().astype(object), call_start=corpus.call_start)
    Ez = lm.embedder.transform([NEUTRAL_TEXT])
    mat.neutral_E = None if Ez is None else Ez.astype(np.float64)[0]
    return mat


_SIG_NAMES = [n for n, _ in signal_spec()]
_RECENT_IDX = [i for i, n in enumerate(_SIG_NAMES) if n not in _NOT_RECENT]
_IDX = {n: j for j, n in enumerate(_SIG_NAMES)}


def edited_features(mat: TurnMaterial, call_idx: int, k: int, last_k: int, opening_row: np.ndarray,
                    drop=(), replace=()) -> np.ndarray:
    s = int(mat.call_start[call_idx])
    drop = sorted(set(int(j) for j in drop))
    replace = sorted(set(int(j) for j in replace) - set(drop))
    cum = mat.excl_S[s + k].copy()
    esum = None if mat.excl_E is None else mat.excl_E[s + k].copy()
    for j in drop:
        cum -= mat.S[s + j]
        if esum is not None:
            esum -= mat.E[s + j]
    for j in replace:
        cum += mat.neutral_S(s + j) - mat.S[s + j]
        if esum is not None:
            esum += mat.neutral_E - mat.E[s + j]
    kept = [j for j in range(k) if j not in set(drop)]
    k2 = len(kept)
    window = kept[max(0, k2 - last_k):]
    rep = set(replace)
    rsum = np.zeros_like(cum)
    for j in window:
        rsum += mat.neutral_S(s + j) if j in rep else mat.S[s + j]
    recent = (rsum[_RECENT_IDX] > 0).astype(np.float64)
    fp_rate = cum[_IDX["c:filled_pauses"]] / max(1.0, cum[_IDX["c:words"]])
    neg_share = cum[_IDX["c:negative_emotion"]] / max(1.0, cum[_IDX["c:turn"]])
    parts = [np.array([k2, math.log1p(k2)], dtype=np.float64), cum, recent, np.array([fp_rate, neg_share])]
    if esum is not None:
        parts.append(esum / max(1.0, float(k2)))
    h = np.concatenate(parts).astype(np.float32)
    return np.concatenate([h, opening_row.astype(np.float32)])


def window_text(mat: TurnMaterial, call_idx: int, k: int, width: int, drop=(), replace=()) -> str:
    s = int(mat.call_start[call_idx])
    dropped = set(int(j) for j in drop)
    rep = set(int(j) for j in replace)
    kept = [j for j in range(k) if j not in dropped][-width:]
    out = []
    for j in kept:
        tag = "a" if mat.party[s + j] == "Agent" else "c"
        txt = NEUTRAL_TEXT if j in rep else mat.text[s + j]
        out.append(" ".join(f"{tag}_{w}" for w in str(txt).split()))
    return " ".join(out)


@dataclass
class Forecaster:
    event: str
    fold_of_call: np.ndarray
    models: list
    scaler: object
    vectorizer: object
    width: int
    last_k: int
    n_train_rows: int
    n_events: int
    version: str = "forecaster-v1"

    def design(self, dense: np.ndarray, texts: list[str]):
        Xd = sp.csr_matrix(self.scaler.transform(dense.astype(np.float64)))
        return sp.hstack([Xd, self.vectorizer.transform(texts)], format="csr")

    def predict(self, call_idx: np.ndarray, dense: np.ndarray, texts: list[str]) -> np.ndarray:
        X = self.design(dense, texts)
        folds = self.fold_of_call[np.asarray(call_idx)]
        out = np.empty(len(texts))
        for f, m in enumerate(self.models):
            sel = folds == f
            if sel.any():
                out[sel] = m.predict_proba(X[sel])[:, 1] if m is not None else 0.0
        return out


def _opening_matrix(corpus, lm) -> np.ndarray:
    O, _ = opening_features(corpus.calls, lm.opening_levels)
    return O


def train_forecaster(corpus, lm, labels: pd.DataFrame, event: str, settings, mat: TurnMaterial | None = None) -> Forecaster | None:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    ev = settings.evidence
    last_k = settings.landmark.last_k
    mat = mat or build_material(corpus, lm)
    m = lm.meta
    call = m["call_idx"].to_numpy()
    k = m["k"].to_numpy()
    onset = labels.loc[corpus.call_ids, f"{event}_onset"].to_numpy()[call]
    at_risk = (onset < 0) | (k <= onset)
    y_all = (onset == k) & (onset >= 0)
    rows = np.flatnonzero(at_risk)
    y = y_all[rows].astype(int)
    if y.sum() < 20 or (y == 0).sum() < 20:
        return None
    rng = np.random.default_rng(settings.seed + 17)
    n_neg = int((y == 0).sum())
    rate = min(1.0, ev.forecast_max_negatives / max(1, n_neg))
    keep = (y == 1) | (rng.random(rows.size) < rate)
    rows, y = rows[keep], y[keep]
    w = np.where(y == 1, 1.0, 1.0 / rate)
    O = _opening_matrix(corpus, lm)
    dense = lm.X[rows].astype(np.float32).copy()
    texts = [window_text(mat, int(call[r]), int(k[r]), ev.window_turns) for r in rows]
    aug = np.flatnonzero(rng.random(rows.size) < ev.dropout_share)
    for i in aug:
        r = rows[i]
        c, kk = int(call[r]), int(k[r])
        nd = int(min(kk, rng.integers(1, 3)))
        dr = rng.choice(kk, size=nd, replace=False)
        dense[i] = edited_features(mat, c, kk, last_k, O[c], drop=dr)
        texts[i] = window_text(mat, c, kk, ev.window_turns, drop=dr)
    groups = corpus.calls["template_group"].astype(str).to_numpy()
    fold_of_call = hashed_folds(groups, settings.estimator.n_folds, FORECAST_SALT)
    folds = fold_of_call[call[rows]]
    scaler = StandardScaler().fit(dense)
    vec = TfidfVectorizer(max_features=ev.tfidf_features, min_df=3, sublinear_tf=True, dtype=np.float64,
                          token_pattern=r"[a-z]_[^\s]+")
    vec.fit([texts[i] for i in np.flatnonzero(y == 1)] + [texts[i] for i in rng.choice(len(texts), size=min(len(texts), 50000), replace=False)])
    fc = Forecaster(event, fold_of_call, [], scaler, vec, ev.window_turns, last_k, int(rows.size), int(y.sum()))
    X = fc.design(dense, texts)
    for f in range(settings.estimator.n_folds):
        tr = folds != f
        if y[tr].sum() < 5 or (y[tr] == 0).sum() < 5:
            fc.models.append(None)
            continue
        clf = LogisticRegression(C=ev.forecaster_C, max_iter=2000)
        clf.fit(X[tr], y[tr], sample_weight=w[tr])
        fc.models.append(clf)
    return fc


def forecaster_quality(fc: Forecaster, corpus, lm, labels: pd.DataFrame, mat: TurnMaterial, settings,
                       splits=HELD_OUT, draws: int = 500) -> dict:
    from sklearn.metrics import roc_auc_score
    m = lm.meta
    call = m["call_idx"].to_numpy()
    k = m["k"].to_numpy()
    onset = labels.loc[corpus.call_ids, f"{fc.event}_onset"].to_numpy()[call]
    sel = np.flatnonzero(((onset < 0) | (k <= onset)) & m["split"].isin(list(splits)).to_numpy())
    if sel.size == 0:
        return {"event": fc.event, "n_rows": 0}
    texts = [window_text(mat, int(call[r]), int(k[r]), fc.width) for r in sel]
    p = fc.predict(call[sel], lm.X[sel], texts)
    y1 = ((onset[sel] == k[sel]) & (onset[sel] >= 0)).astype(int)
    y3 = ((onset[sel] >= k[sel]) & (onset[sel] <= k[sel] + 2)).astype(int)
    calls = call[sel]
    uniq, inv = np.unique(calls, return_inverse=True)
    rng = np.random.default_rng(settings.seed)

    def auc(y, s):
        return float(roc_auc_score(y, s)) if 0 < y.sum() < y.size else float("nan")

    order = np.argsort(inv, kind="mergesort")
    by = np.split(order, np.cumsum(np.bincount(inv, minlength=len(uniq)))[:-1])

    def boot(y, s):
        vals = []
        for _ in range(draws):
            pick = rng.integers(0, len(uniq), len(uniq))
            idx = np.concatenate([by[g] for g in pick])
            v = auc(y[idx], s[idx])
            if np.isfinite(v):
                vals.append(v)
        return [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))] if len(vals) > draws * 0.5 else [float("nan")] * 2
    out = {"event": fc.event, "n_rows": int(sel.size), "n_events": int(y1.sum()),
           "auc_next_turn": auc(y1, p), "auc_next_turn_ci": boot(y1, p),
           "auc_within_3": auc(y3, p), "auc_within_3_ci": boot(y3, p),
           "brier": float(np.mean((p - y1) ** 2)), "mean_predicted": float(p.mean()), "observed_rate": float(y1.mean())}
    lp = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
    if 0 < y1.sum() < y1.size:
        from sklearn.linear_model import LogisticRegression
        cal = LogisticRegression(C=1e6, max_iter=1000).fit(lp.reshape(-1, 1), y1)
        out["calibration_slope"] = float(cal.coef_[0, 0])
        out["calibration_intercept"] = float(cal.intercept_[0])
    bins = np.quantile(p, np.linspace(0, 1, 11))
    b = np.clip(np.searchsorted(bins, p, side="right") - 1, 0, 9)
    out["ece"] = float(sum(abs(p[b == i].mean() - y1[b == i].mean()) * (b == i).mean() for i in range(10) if (b == i).any()))
    return out


def _first_behaviour(corpus, occ, event, behaviour) -> np.ndarray:
    return first_turn_per_call(corpus, treatment_mask(corpus.turns, occ, event, behaviour))


def grounding_candidates(corpus, lm, labels: pd.DataFrame, occ: pd.DataFrame, event: str, behaviour: str,
                         splits=HELD_OUT) -> pd.DataFrame:
    fb = _first_behaviour(corpus, occ, event, behaviour)
    onset = labels.loc[corpus.call_ids, f"{event}_onset"].to_numpy()
    calls = corpus.calls
    ok = calls["split"].isin(list(splits)).to_numpy() & (fb >= corpus.opening_turns)
    party = BEHAVIOURS[behaviour].party
    t = corpus.turns
    rows = []
    for ci in np.flatnonzero(ok):
        j = int(fb[ci])
        if onset[ci] >= 0 and j >= onset[ci]:
            continue
        g = int(corpus.call_start[ci] + j)
        if t["party"].iat[g] != party:
            continue
        rows.append({"call_idx": int(ci), "transcript_id": corpus.call_ids[ci], "turn_id": j, "turn_uid": t["turn_uid"].iat[g],
                     "speaker": t["speaker"].iat[g], "quote": t["text"].iat[g], "onset_turn": int(onset[ci]),
                     "event_followed": bool(onset[ci] > j), "split": calls["split"].iat[ci],
                     "industry": calls["opening_domain_vote"].iat[ci], "brand": calls["brand"].iat[ci]})
    return pd.DataFrame(rows)


def faithfulness(fc: Forecaster | None, mat: TurnMaterial, O: np.ndarray, spans: pd.DataFrame, settings,
                 direction: int = 1) -> pd.DataFrame:
    ev = settings.evidence
    last_k = settings.landmark.last_k
    rng = np.random.default_rng(settings.seed + 29)
    out = spans.copy()
    for c in ("p_full", "drop_remove", "drop_neutral", "drop_random_median", "faithfulness_score", "faithfulness_percentile"):
        out[c] = np.nan
    out["sign_agrees"] = False
    out["direction"] = int(direction)
    if fc is None or out.empty:
        return out
    dense, texts, owner = [], [], []
    plan = []
    for i, r in enumerate(out.itertuples(index=False)):
        c, j, k = int(r.call_idx), int(r.turn_id), int(r.onset_turn)
        if k < 0 or j >= k:
            plan.append(None)
            continue
        s = int(mat.call_start[c])
        same = [x for x in range(k) if x != j and mat.party[s + x] == mat.party[s + j]]
        rand = rng.choice(same, size=min(ev.random_baseline_draws, len(same)), replace=False) if same else []
        variants = [((), ()), ((j,), ()), ((), (j,))] + [((int(x),), ()) for x in rand]
        plan.append(len(variants))
        for dr, rp in variants:
            dense.append(edited_features(mat, c, k, last_k, O[c], drop=dr, replace=rp))
            texts.append(window_text(mat, c, k, fc.width, drop=dr, replace=rp))
            owner.append(c)
    if not dense:
        return out
    p = fc.predict(np.asarray(owner), np.vstack(dense), texts)
    pos = 0
    for i, n in enumerate(plan):
        if n is None:
            continue
        v = p[pos:pos + n]
        pos += n
        full, rem, neu, rnd = v[0], v[1], v[2], v[3:]
        d_rem, d_neu = direction * (full - rem), direction * (full - neu)
        d_rnd = direction * (full - rnd) if rnd.size else np.array([np.nan])
        out.iat[i, out.columns.get_loc("p_full")] = full
        out.iat[i, out.columns.get_loc("drop_remove")] = d_rem
        out.iat[i, out.columns.get_loc("drop_neutral")] = d_neu
        if rnd.size:
            med = float(np.median(d_rnd))
            out.iat[i, out.columns.get_loc("drop_random_median")] = med
            out.iat[i, out.columns.get_loc("faithfulness_score")] = d_rem - med
            out.iat[i, out.columns.get_loc("faithfulness_percentile")] = 100.0 * (np.mean(d_rnd < d_rem) + 0.5 * np.mean(d_rnd == d_rem))
        out.iat[i, out.columns.get_loc("sign_agrees")] = bool(np.sign(d_rem) == np.sign(d_neu))
    return out


def comprehensiveness(fc: Forecaster | None, mat: TurnMaterial, O: np.ndarray, rationale: dict, settings) -> dict:
    if fc is None or not rationale:
        return {"n_calls": 0}
    ev = settings.evidence
    rng = np.random.default_rng(settings.seed + 31)
    diffs = []
    for (c, k), turns in rationale.items():
        s = int(mat.call_start[c])
        turns = sorted(set(int(j) for j in turns if j < k))
        if not turns:
            continue
        pool = [x for x in range(k) if x not in turns and mat.party[s + x] in {mat.party[s + j] for j in turns}]
        if len(pool) < len(turns):
            continue
        variants = [(), tuple(turns)] + [tuple(rng.choice(pool, size=len(turns), replace=False)) for _ in range(ev.random_baseline_draws)]
        dense = [edited_features(mat, c, k, settings.landmark.last_k, O[c], drop=v) for v in variants]
        texts = [window_text(mat, c, k, fc.width, drop=v) for v in variants]
        p = fc.predict(np.full(len(variants), c), np.vstack(dense), texts)
        comp = p[0] - p[1]
        base = float(np.median(p[0] - p[2:]))
        diffs.append(comp - base)
    if not diffs:
        return {"n_calls": 0}
    d = np.asarray(diffs)
    boot = [float(np.mean(d[rng.integers(0, d.size, d.size)])) for _ in range(1000)]
    return {"n_calls": int(d.size), "comprehensiveness_minus_random": float(d.mean()),
            "ci": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]}


def build_evidence(corpus, lm, labels: pd.DataFrame, occ: pd.DataFrame, library: pd.DataFrame, settings,
                   log=print) -> dict:
    ev = settings.evidence
    mat = build_material(corpus, lm)
    O = _opening_matrix(corpus, lm)
    rng = np.random.default_rng(settings.seed + 37)
    factors = library[(library["slice"] == "all") & ~library["negative_control"] & (library["status"] == "ok")]
    forecasters, quality, span_frames, rationale, fsum = {}, {}, [], {}, []
    for e in sorted(factors["event"].unique(), key=list(EVENTS).index):
        fc = train_forecaster(corpus, lm, labels, e, settings, mat)
        forecasters[e] = fc
        quality[e] = forecaster_quality(fc, corpus, lm, labels, mat, settings) if fc is not None else {"event": e, "trained": False}
        log(f"  forecaster {e}: " + (f"AUC(next turn) {quality[e].get('auc_next_turn', float('nan')):.3f}" if fc else "not trained (too few events)"))
        for r in factors[factors["event"] == e].itertuples(index=False):
            cand = grounding_candidates(corpus, lm, labels, occ, e, r.behaviour)
            if cand.empty:
                fsum.append({"factor_id": r.factor_id, "event": e, "behaviour": r.behaviour, "n_candidates": 0,
                             "calls_with_behaviour": 0, "calls_without_event": 0})
                continue
            pos = cand[cand["event_followed"]]
            picks = []
            for _, grp in pos.groupby("industry", sort=True):
                n = min(ev.spans_per_slice, len(grp))
                picks.append(grp.iloc[np.sort(rng.choice(len(grp), size=n, replace=False))])
            chosen = pd.concat(picks) if picks else pos.iloc[:0]
            direction = -1 if (np.isfinite(r.att) and r.att < 0) else 1
            scored = faithfulness(fc, mat, O, chosen, settings, direction)
            scored.insert(0, "factor_id", r.factor_id)
            scored.insert(1, "event", e)
            scored.insert(2, "behaviour", r.behaviour)
            scored["turns_before_onset"] = scored["onset_turn"] - scored["turn_id"]
            span_frames.append(scored)
            for x in scored.itertuples(index=False):
                rationale.setdefault(e, {}).setdefault((int(x.call_idx), int(x.onset_turn)), []).append(int(x.turn_id))
            pct = scored["faithfulness_percentile"].dropna()
            fsum.append({"factor_id": r.factor_id, "event": e, "behaviour": r.behaviour, "n_candidates": int(len(pos)),
                         "calls_with_behaviour": int(len(cand)), "calls_without_event": int((~cand["event_followed"]).sum()),
                         "n_scored": int(len(pct)), "median_percentile": float(pct.median()) if len(pct) else float("nan"),
                         "share_sign_agrees": float(scored["sign_agrees"].mean()) if len(scored) else float("nan"),
                         "faithfulness_passed": bool(len(pct) >= 5 and pct.median() > 50)})
    spans = pd.concat(span_frames, ignore_index=True) if span_frames else pd.DataFrame()
    if len(spans):
        spans.insert(0, "span_id", [f"S{i + 1}" for i in range(len(spans))])
        spans["provenance"] = "raw_dialogue"
        spans["forecaster_version"] = "forecaster-v1"
    comp = {e: comprehensiveness(fc, mat, O, rationale.get(e, {}), settings) for e, fc in forecasters.items()}
    return {"spans": spans, "factor_summary": pd.DataFrame(fsum), "forecaster_quality": quality,
            "comprehensiveness": comp, "forecasters": forecasters}
