from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.base import clone
from threadpoolctl import threadpool_limits

from .behaviours import first_occurrence, treatment_mask
from .definitions import BEHAVIOURS, EVENTS, NEGATIVE_CONTROLS, PRIMARY_EVENTS, candidate_behaviours
from .stats import (benjamini_hochberg, cluster_bootstrap_ratio, evalue_from_att, hashed_folds, norm_p_two_sided,
                    standardized_differences, z_crit)

HELD_OUT = ("dev", "test")
FOLD_SALT = "crest-crossfit-v1"
PRIOR_EVENTS = tuple(PRIMARY_EVENTS) + ("HANDOFF",)


def _newton_cholesky_available() -> bool:
    try:
        from sklearn.linear_model import LogisticRegression
        LogisticRegression(solver="newton-cholesky").fit(np.array([[0.0], [1.0], [0.0], [1.0]]), np.array([0, 1, 1, 0]))
        return True
    except Exception:
        return False


_HAS_NEWTON_CHOLESKY = _newton_cholesky_available()

DEFAULT_PARAMS = {
    "logistic_ridge": {"prop": {"C": 0.1}, "out": {"alpha": 100.0}},
    "hgb": {"prop": {"max_leaf_nodes": 15, "min_samples_leaf": 40}, "out": {"max_leaf_nodes": 15, "min_samples_leaf": 40}},
}
TUNING_GRID = {
    "logistic_ridge": {"prop": [{"C": c} for c in (0.003, 0.01, 0.03, 0.1, 0.3, 1.0)],
                       "out": [{"alpha": a} for a in (1.0, 10.0, 100.0, 1000.0)]},
    "hgb": {"prop": [{"max_leaf_nodes": 7, "min_samples_leaf": 100}, {"max_leaf_nodes": 15, "min_samples_leaf": 40},
                     {"max_leaf_nodes": 31, "min_samples_leaf": 20}],
            "out": [{"max_leaf_nodes": 7, "min_samples_leaf": 100}, {"max_leaf_nodes": 15, "min_samples_leaf": 40},
                    {"max_leaf_nodes": 31, "min_samples_leaf": 20}]},
}


def learner_spec(learner) -> dict:
    if isinstance(learner, str):
        if learner not in DEFAULT_PARAMS:
            raise ValueError(f"unknown learner {learner}")
        return {"kind": learner, **{k: dict(v) for k, v in DEFAULT_PARAMS[learner].items()}}
    spec = {"kind": learner["kind"], **{k: dict(v) for k, v in DEFAULT_PARAMS[learner["kind"]].items()}}
    for part in ("prop", "out"):
        spec[part].update(learner.get(part) or {})
    return spec


def learner_name(learner) -> str:
    sp = learner_spec(learner)
    return f"{sp['kind']}({', '.join(f'{k}={v}' for k, v in sp['prop'].items())}; " \
           f"{', '.join(f'{k}={v}' for k, v in sp['out'].items())})"


def make_learners(learner, seed: int):
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    sp = learner_spec(learner)
    if sp["kind"] == "logistic_ridge":
        solver = "newton-cholesky" if _HAS_NEWTON_CHOLESKY else "lbfgs"
        return (make_pipeline(StandardScaler(), LogisticRegression(C=float(sp["prop"]["C"]), max_iter=5000, solver=solver)),
                make_pipeline(StandardScaler(), Ridge(alpha=float(sp["out"]["alpha"]))))
    from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
    base = dict(max_iter=150, learning_rate=0.06, l2_regularization=1.0, random_state=seed)
    return (HistGradientBoostingClassifier(**base, **sp["prop"]), HistGradientBoostingRegressor(**base, **sp["out"]))


def _fit_fold(learner, seed, what, X, T, Y, tr, te, threads: int | None = 1):
    with threadpool_limits(limits=threads or None):
        prop, outm = make_learners(learner, seed)
        if what == "e":
            if T[tr].min() == T[tr].max():
                return te, np.full(te.size, float(T[tr].mean()))
            return te, clone(prop).fit(X[tr], T[tr]).predict_proba(X[te])[:, 1]
        ctrl = tr[T[tr] == 0]
        if ctrl.size < 5 or np.ptp(Y[ctrl]) == 0:
            return te, np.full(te.size, float(Y[ctrl].mean()) if ctrl.size else float(Y[tr].mean()))
        return te, clone(outm).fit(X[ctrl], Y[ctrl]).predict(X[te])


def crossfit_nuisance(X, T, Y, folds, learner, seed: int, what: str, train_mask=None, n_jobs: int = 1,
                      threads: int | None = 1) -> np.ndarray:
    n = len(T)
    train_mask = np.ones(n, dtype=bool) if train_mask is None else np.asarray(train_mask, dtype=bool)
    tasks = []
    for f in np.unique(folds):
        te = np.flatnonzero(folds == f)
        tr = np.flatnonzero((folds != f) & train_mask)
        tasks.append((tr, te))
    out = np.empty(n)
    fallback = float(T[train_mask].mean()) if what == "e" else float(Y[train_mask & (T == 0)].mean()) \
        if (train_mask & (T == 0)).any() else float(Y[train_mask].mean()) if train_mask.any() else 0.0
    todo = [(tr, te) for tr, te in tasks if tr.size]
    for tr, te in tasks:
        if not tr.size:
            out[te] = fallback
    if n_jobs and n_jobs != 1 and len(todo) > 1:
        from joblib import Parallel, delayed
        res = Parallel(n_jobs=n_jobs)(delayed(_fit_fold)(learner, seed, what, X, T, Y, tr, te, threads) for tr, te in todo)
    else:
        res = [_fit_fold(learner, seed, what, X, T, Y, tr, te, threads) for tr, te in todo]
    for te, pred in res:
        out[te] = pred
    return out


def crossfit(X, T, Y, folds, learner, seed: int, train_mask=None, n_jobs: int = 1, threads: int | None = 1):
    e = crossfit_nuisance(X, T, Y, folds, learner, seed, "e", train_mask, n_jobs, threads)
    g0 = crossfit_nuisance(X, T, Y, folds, learner, seed, "g0", train_mask, n_jobs, threads)
    return e, g0


@dataclass
class RiskSet:
    event: str
    behaviour: str
    X: np.ndarray
    T: np.ndarray
    Y: np.ndarray
    a_lab: np.ndarray
    clusters: np.ndarray
    call_idx: np.ndarray
    k: np.ndarray
    split: np.ndarray
    feature_names: list
    gold: dict | None = None
    info: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return int(len(self.T))

    @property
    def dsl(self) -> bool:
        return self.gold is not None

    @property
    def n_gold_calls(self) -> int:
        return int(len(np.unique(self.call_idx[self.gold["R"]]))) if self.gold is not None else 0

    def subset(self, rows: np.ndarray) -> "RiskSet":
        g = None if self.gold is None else {k: v[rows] for k, v in self.gold.items()}
        return RiskSet(self.event, self.behaviour, self.X[rows], self.T[rows], self.Y[rows], self.a_lab[rows],
                       self.clusters[rows], self.call_idx[rows], self.k[rows], self.split[rows], self.feature_names,
                       g, dict(self.info))


class RiskSetBuilder:
    def __init__(self, corpus, lm, labels: pd.DataFrame, occ: pd.DataFrame, settings, gold: pd.DataFrame | None = None):
        self.corpus, self.lm, self.settings = corpus, lm, settings
        self.occ = occ
        self.labels = labels.loc[corpus.call_ids]
        self.onset = {e: self.labels[f"{e}_onset"].to_numpy().astype(np.int64) for e in EVENTS}
        m = lm.meta
        self.call = m["call_idx"].to_numpy()
        self.k = m["k"].to_numpy()
        self.party = m["party"].to_numpy()
        self.both = m["both_spoken"].to_numpy()
        self.split = m["split"].to_numpy()
        calls = corpus.calls
        self.named = calls["had_named_speakers"].to_numpy()[self.call]
        self.truncated = calls["qc_possibly_truncated"].to_numpy()[self.call]
        self.singleton = (calls["template_group_size"].to_numpy() <= 1)[self.call]
        codes, _ = pd.factorize(m["template_group"])
        self.cluster = codes.astype(np.int64)
        self._first: dict = {}
        self.gold = None
        self.gold_onset: dict = {}
        if gold is not None and len(gold):
            g = gold.set_index("transcript_id")
            pos = pd.Index(corpus.call_ids).get_indexer(g.index)
            if (pos < 0).any():
                raise ValueError("gold labels contain calls that are not in the corpus")
            if not set(calls["split"].to_numpy()[pos]) <= set(HELD_OUT):
                raise ValueError("gold calls must come from held-out (dev/test) calls only")
            self.gold_inv_pi = np.zeros(corpus.n_calls)
            pi = g["pi"].to_numpy(dtype=float)
            if not ((pi > 0) & (pi <= 1)).all():
                raise ValueError("gold inclusion probabilities must be in (0, 1]")
            self.gold_inv_pi[pos] = 1.0 / pi
            self.in_gold = np.zeros(corpus.n_calls, dtype=bool)
            self.in_gold[pos] = True
            for col in g.columns:
                if col.endswith("_onset"):
                    arr = np.full(corpus.n_calls, -1, dtype=np.int64)
                    arr[pos] = g[col].to_numpy().astype(np.int64)
                    self.gold_onset[col[:-len("_onset")]] = arr
            self.gold = g

    def first_treatment(self, event: str, behaviour: str) -> np.ndarray:
        key = (event, behaviour)
        if key not in self._first:
            mask = treatment_mask(self.corpus.turns, self.occ, event, behaviour)
            self._first[key] = first_occurrence(self.corpus, mask)
        return self._first[key]

    def metadata_covariates(self) -> tuple[np.ndarray, list]:
        calls = self.corpus.calls
        cols, names = [], []
        flagged = self.corpus.leakage_flagged
        if "intent_key" in calls.columns and "intent_key" not in flagged and "intent" not in flagged:
            vals = calls["intent_key"].astype(str).to_numpy()
            train_vals = pd.Series(vals[calls["split"].to_numpy() == "train"]).value_counts().index[:40]
            for v in train_vals:
                cols.append((vals == v)[self.call])
                names.append(f"meta:intent={v}")
        if "call_hour" in calls.columns and "call_hour" not in flagged:
            cols.append(calls["call_hour"].astype(float).fillna(-1).to_numpy(dtype=float)[self.call])
            names.append("meta:call_hour")
        if not cols:
            return np.zeros((len(self.call), 0), dtype=np.float32), []
        return np.column_stack(cols).astype(np.float32), names

    @staticmethod
    def _shift(onset: np.ndarray, shift: int) -> np.ndarray:
        out = onset.copy()
        if shift:
            has = out >= 0
            out[has] = np.maximum(0, out[has] + shift)
        return out

    def build(self, event: str, behaviour: str, splits=HELD_OUT, variant: dict | None = None) -> RiskSet:
        variant = variant or {}
        big = np.iinfo(np.int64).max
        shift = int(variant.get("onset_shift", 0))
        horizon = variant.get("horizon")
        on = self._shift(self.onset[event], shift)[self.call]
        on_eff = np.where(on >= 0, on, big)
        fb = self.first_treatment(event, behaviour)[self.call]
        fb_eff = np.where(fb >= 0, fb, big)
        party = BEHAVIOURS[behaviour].party
        base = (self.k <= fb_eff) & (self.party == party) & self.both & np.isin(self.split, list(splits))
        if variant.get("exclude_named"):
            base &= ~self.named
        if variant.get("exclude_truncated"):
            base &= ~self.truncated
        if variant.get("singletons_only"):
            base &= self.singleton
        for col, val in (variant.get("slice") or {}).items():
            base &= (self.corpus.calls[col].astype(str).to_numpy() == str(val))[self.call]
        clean = variant.get("clean", True)
        prior_cols, prior_names = [], []
        for e2 in PRIOR_EVENTS:
            if e2 == event:
                continue
            o2 = self.onset[e2][self.call]
            prior = (o2 >= 0) & (o2 < self.k)
            if clean:
                base &= ~prior
            else:
                prior_cols.append(prior)
                prior_names.append(f"prior:{e2}")
        a_lab_all = self.k < on_eff
        use_gold = self.gold is not None and variant.get("dsl", True) and event in self.gold_onset
        if use_gold:
            g_on = self._shift(self.gold_onset[event], shift)[self.call]
            in_gold = self.in_gold[self.call]
            a_gold_all = in_gold & (self.k < np.where(g_on >= 0, g_on, big))
            rows = np.flatnonzero(base & (a_lab_all | a_gold_all))
        else:
            rows = np.flatnonzero(base & a_lab_all)
        k = self.k[rows]
        T = (k == fb_eff[rows]).astype(np.int8)

        def outcome(onset_rows):
            if horizon is None:
                return (onset_rows > k).astype(float)
            return ((onset_rows > k) & (onset_rows <= k + int(horizon))).astype(float)
        a_lab = a_lab_all[rows]
        Y = np.where(a_lab, outcome(on[rows]), 0.0)
        X = np.hstack([self.lm.X[rows], np.column_stack(prior_cols)[rows].astype(np.float32)]) if prior_cols \
            else self.lm.X[rows]
        names = list(self.lm.names) + prior_names
        if variant.get("metadata"):
            M, mnames = self.metadata_covariates()
            X = np.hstack([X, M[rows]])
            names += mnames
        gold = None
        if use_gold:
            R = in_gold[rows]
            if R.any():
                a_g = a_gold_all[rows]
                gold = {"R": R, "inv_pi": self.gold_inv_pi[self.call[rows]] * R, "a": a_g,
                        "Y": np.where(a_g, outcome(g_on[rows]), 0.0)}
        return RiskSet(event, behaviour, X, T, Y, a_lab, self.cluster[rows], self.call[rows], k, self.split[rows],
                       names, gold, {"variant": variant, "splits": list(splits)})


def fold_ids(rs: RiskSet, n_folds: int) -> np.ndarray:
    k = int(min(n_folds, max(2, len(np.unique(rs.clusters)))))
    return hashed_folds(rs.clusters, k, FOLD_SALT)


def row_contributions(rs: RiskSet, e: np.ndarray, g0: np.ndarray, settings, sel: np.ndarray) -> dict:
    est = settings.estimator
    T = rs.T[sel].astype(float)
    ee = np.clip(e[sel], est.propensity_clip, 1 - est.propensity_clip)
    keep = ee <= est.trim_upper
    w = ee / (1 - ee)
    g = g0[sel]

    def pieces(a, Y):
        r = Y - g
        a = a.astype(float) * keep
        return a * (T * r - (1 - T) * w * r), a * T, a * T * Y
    num, den, p1n = pieces(rs.a_lab[sel], rs.Y[sel])
    if rs.gold is not None:
        gnum, gden, gp1 = pieces(rs.gold["a"][sel], rs.gold["Y"][sel])
        f = rs.gold["inv_pi"][sel]
        num, den, p1n = num + f * (gnum - num), den + f * (gden - den), p1n + f * (gp1 - p1n)
    return {"num": num, "den": den, "p1num": p1n, "keep": keep, "w": w, "e": ee, "T": T}


def att_core(rs: RiskSet, e: np.ndarray, g0: np.ndarray, settings, rows: np.ndarray | None = None,
             seed: int = 0, with_balance: bool = True) -> dict:
    est = settings.estimator
    if est.outcome_clip:
        g0 = np.clip(g0, 0.0, 1.0)
    sel = np.arange(rs.n) if rows is None else np.asarray(rows)
    c = row_contributions(rs, e, g0, settings, sel)
    lab = rs.a_lab[sel]
    T, keep = c["T"], c["keep"]
    ylab = rs.Y[sel]
    n_treated_all = int((T[lab] == 1).sum())
    tk = lab & keep & (T == 1)
    ck = lab & keep & (T == 0)
    out = {"n_rows": int(lab.sum()), "n_calls": int(len(np.unique(rs.call_idx[sel][lab]))), "n_treated": n_treated_all,
           "dsl": bool(rs.dsl), "n_gold_calls": int(rs.n_gold_calls), "n_treated_kept": int(tk.sum())}
    out["kept_share"] = float(tk.sum() / n_treated_all) if n_treated_all else float("nan")
    out["events_treated"] = int(ylab[tk].sum())
    ctrl_calls = pd.Series(ylab[ck]).groupby(rs.call_idx[sel][ck]).max()
    out["events_control"] = int(ctrl_calls.sum())
    out["control_calls"] = int(len(ctrl_calls))
    if tk.sum() < 2 or ck.sum() < 2:
        out.update(status="not_estimable", reason="fewer than 2 treated or control rows after trimming")
        return _nan_fill(out)
    num, den = c["num"], c["den"]
    D = float(den.sum())
    codes, cl = np.unique(rs.clusters[sel], return_inverse=True)
    G = len(codes)
    if D <= 0 or G < 2:
        out.update(status="not_estimable", reason="no treated rows or fewer than 2 clusters")
        return _nan_fill(out)
    theta = float(num.sum() / D)
    S = np.bincount(cl, weights=num - theta * den, minlength=G)
    se = math.sqrt((G / (G - 1)) * float((S ** 2).sum())) / D
    z = z_crit(est.alpha)
    lo, hi = theta - z * se, theta + z * se
    b_lo, b_hi = cluster_bootstrap_ratio(np.bincount(cl, weights=num, minlength=G), np.bincount(cl, weights=den, minlength=G),
                                         est.bootstrap_draws, seed, est.alpha)
    p1 = float(c["p1num"].sum() / D)
    ev, ev_ci = evalue_from_att(p1, theta, lo, hi)
    n1 = float(tk.sum())
    out.update(status="ok", att=theta, se=se, ci_low=lo, ci_high=hi, p=norm_p_two_sided(theta / se) if se > 0 else float("nan"),
               boot_ci_low=b_lo, boot_ci_high=b_hi, p_treated=p1, p_counterfactual=p1 - theta, clusters=G,
               e_value=ev, e_value_ci=ev_ci, attributable=theta * n1, attributable_ci=[lo * n1, hi * n1],
               propensity_mean_treated=float(c["e"][tk].mean()), propensity_max=float(c["e"][lab].max()))
    if with_balance:
        out.update(balance_diagnostics(rs, c, g0[sel], lab & keep))
    return out


def balance_diagnostics(rs: RiskSet, c: dict, g0: np.ndarray, m: np.ndarray) -> dict:
    Tm = c["T"][m].astype(bool)
    wm = c["w"][m]
    em = c["e"][m]
    logit = np.log(em / (1 - em))
    summ = standardized_differences(np.column_stack([g0[m], logit]), Tm, wm)
    cols = [j for j, n in enumerate(rs.feature_names) if not n.startswith("emb:")]
    smd = standardized_differences(rs.X[m][:, cols], Tm, wm)
    order = np.argsort(-np.abs(np.nan_to_num(smd)))[:5]
    n1 = max(1, int(Tm.sum()))
    w0 = wm[~Tm]
    n0_eff = float(w0.sum() ** 2 / max(1e-12, (w0 ** 2).sum())) if w0.size else 0.0
    slope = float("nan")
    if Tm.any() and (~Tm).any() and np.ptp(logit) > 0:
        from sklearn.linear_model import LogisticRegression
        slope = float(LogisticRegression(C=1e6, max_iter=1000).fit(logit.reshape(-1, 1), Tm.astype(int)).coef_[0, 0])
    return {"balance_smd": float(abs(summ[0])) if np.isfinite(summ[0]) else float("nan"),
            "smd_prognostic": float(summ[0]), "smd_propensity": float(summ[1]), "propensity_calibration_slope": slope,
            "max_abs_smd": float(np.nanmax(np.abs(smd))) if np.isfinite(smd).any() else float("nan"),
            "n_covariates_smd_over_0_1": int((np.abs(smd) > 0.1).sum()),
            "smd_noise_sd": float(math.sqrt(1.0 / n1 + 1.0 / max(1.0, n0_eff))),
            "control_effective_n": n0_eff,
            "top_imbalance": [[rs.feature_names[cols[j]], float(smd[j])] for j in order]}


def _nan_fill(out: dict) -> dict:
    for key in ("att", "se", "ci_low", "ci_high", "p", "boot_ci_low", "boot_ci_high", "p_treated", "p_counterfactual",
                "e_value", "e_value_ci", "attributable", "max_abs_smd", "balance_smd", "smd_prognostic",
                "smd_propensity"):
        out.setdefault(key, float("nan"))
    out.setdefault("attributable_ci", [float("nan"), float("nan")])
    out.setdefault("top_imbalance", [])
    return out


def _not_estimable(rs: RiskSet, reason: str) -> dict:
    lab = rs.a_lab
    return _nan_fill({"status": "not_estimable", "reason": reason, "n_rows": int(lab.sum()),
                      "n_calls": int(len(np.unique(rs.call_idx[lab]))), "n_treated": int(rs.T[lab].sum()),
                      "dsl": rs.dsl, "n_gold_calls": rs.n_gold_calls, "n_treated_kept": 0, "kept_share": float("nan"),
                      "events_treated": 0, "events_control": 0, "control_calls": 0})


def estimate(rs: RiskSet, settings, learner, seed: int, return_nuisances: bool = False, e: np.ndarray | None = None):
    lab = rs.a_lab
    if rs.n == 0 or (rs.T[lab] == 1).sum() < 2 or (rs.T[lab] == 0).sum() < 2:
        out = _not_estimable(rs, "too few treated or control rows")
        return (out, None) if return_nuisances else out
    folds = fold_ids(rs, settings.estimator.n_folds)
    n_jobs = settings.estimator.n_jobs
    T = rs.T.astype(int)
    if e is None:
        e = crossfit_nuisance(rs.X, T, rs.Y, folds, learner, seed, "e", lab, n_jobs, settings.estimator.threads_per_fit)
    g0 = crossfit_nuisance(rs.X, T, rs.Y, folds, learner, seed, "g0", lab, n_jobs, settings.estimator.threads_per_fit)
    out = att_core(rs, e, g0, settings, seed=seed)
    out["learner"] = learner_name(learner)
    return (out, (e, g0)) if return_nuisances else out


def support_band(r: dict, s) -> tuple[str, list]:
    if r.get("status") != "ok":
        return "insufficient", ["not estimable: " + str(r.get("reason", ""))]
    bands, why = [], []
    ev = min(r["events_treated"], r["events_control"])
    bands.append(0 if ev >= s.events_sufficient else 1 if ev >= s.events_borderline else 2)
    if bands[-1]:
        why.append(f"only {ev} events in the smaller arm")
    kept = r["kept_share"]
    bands.append(0 if kept >= s.kept_sufficient else 1 if kept >= s.kept_borderline else 2)
    if bands[-1]:
        why.append(f"{kept:.0%} of treated moments have comparable untreated moments")
    hw = (r["ci_high"] - r["ci_low"]) / 2
    bands.append(0 if hw <= s.halfwidth_sufficient else 1 if hw <= s.halfwidth_borderline else 2)
    if bands[-1]:
        why.append(f"error bar +/-{hw * 100:.0f} points")
    smd = r.get("balance_smd", float("nan"))
    bands.append(0 if np.isfinite(smd) and smd <= s.smd_sufficient else 1 if np.isfinite(smd) and smd <= s.smd_borderline else 2)
    if bands[-1]:
        why.append(f"groups not fully comparable (standardized difference of the predicted risk {smd:.2f})")
    return ["sufficient", "borderline", "insufficient"][max(bands)], why


def _tuning_sets(builder: RiskSetBuilder, pairs, settings) -> list:
    est = settings.estimator
    rng = np.random.default_rng(est.seed + 7)
    out = []
    for (e, b) in pairs:
        rs = builder.build(e, b, ("train",))
        rs = rs.subset(np.flatnonzero(rs.a_lab))
        if rs.n > est.tune_max_rows:
            cl = np.unique(rs.clusters)
            pick = rng.choice(cl, size=max(2, int(len(cl) * est.tune_max_rows / rs.n)), replace=False)
            rs = rs.subset(np.flatnonzero(np.isin(rs.clusters, pick)))
        if rs.T.sum() >= 10 and (rs.T == 0).sum() >= 10:
            out.append(rs)
    return out


def _relative_losses(sets: list, learner, settings, parts=("prop", "out")) -> dict:
    from sklearn.metrics import log_loss, mean_squared_error
    est = settings.estimator
    tot = {p: 0.0 for p in parts}
    for rs in sets:
        folds = fold_ids(rs, est.n_folds)
        T = rs.T.astype(int)
        if "prop" in parts:
            eh = crossfit_nuisance(rs.X, T, rs.Y, folds, learner, est.seed, "e", None, est.n_jobs, est.threads_per_fit)
            tot["prop"] += log_loss(T, np.clip(eh, 1e-6, 1 - 1e-6), labels=[0, 1]) / log_loss(T, np.full(T.size, T.mean()), labels=[0, 1])
        if "out" in parts:
            g0 = crossfit_nuisance(rs.X, T, rs.Y, folds, learner, est.seed, "g0", None, est.n_jobs, est.threads_per_fit)
            ctrl = T == 0
            tot["out"] += mean_squared_error(rs.Y[ctrl], g0[ctrl]) / max(1e-9, float(np.var(rs.Y[ctrl])))
    return {p: (v / len(sets) if sets else float("nan")) for p, v in tot.items()}


def tune_learners(builder: RiskSetBuilder, pairs, settings) -> dict:
    sets = _tuning_sets(builder, pairs, settings)
    tuned, report, totals = {}, {}, {}
    for kind, grid in TUNING_GRID.items():
        best = {}
        best_loss = {}
        for part in ("prop", "out"):
            scores = []
            for params in grid[part]:
                spec = learner_spec(kind)
                spec[part] = dict(params)
                scores.append((_relative_losses(sets, spec, settings, (part,))[part], params))
            ok = [x for x in scores if np.isfinite(x[0])]
            chosen = min(ok, key=lambda x: x[0]) if ok else (float("nan"), DEFAULT_PARAMS[kind][part])
            best[part], best_loss[part] = dict(chosen[1]), chosen[0]
            report[f"{kind}.{part}"] = [[json.dumps(p, sort_keys=True), l] for l, p in scores]
        tuned[kind] = {"kind": kind, **best}
        totals[kind] = best_loss["prop"] + best_loss["out"]
    return {"tuned": tuned, "grid_losses": report, "total_loss": totals, "pairs": [f"{e}:{b}" for e, b in pairs],
            "tuning_rows": [int(rs.n) for rs in sets]}


def choose_learner(builder: RiskSetBuilder, pairs, settings) -> dict:
    t = tune_learners(builder, pairs, settings)
    want = settings.estimator.learner
    if want == "auto":
        ok = {k: v for k, v in t["total_loss"].items() if np.isfinite(v)}
        want = min(ok, key=ok.get) if ok else "logistic_ridge"
    other = "hgb" if want == "logistic_ridge" else "logistic_ridge"
    return {"learner": t["tuned"][want], "other_learner": t["tuned"][other], **t}


def planted_effect_test(builder: RiskSetBuilder, pairs, learner, settings) -> dict:
    est = settings.estimator
    rng = np.random.default_rng(est.seed + 101)
    results, used, skipped = [], [], []
    for (e, b) in pairs:
        if len(used) >= est.planted_pairs:
            break
        rs = builder.build(e, b, ("train",))
        lab_rows = np.flatnonzero(rs.a_lab)
        rs = rs.subset(lab_rows)
        clusters = np.unique(rs.clusters)
        if len(clusters) < 20 or rs.T.sum() < 20:
            skipped.append(f"{e}:{b} ({len(clusters)} template groups, {int(rs.T.sum())} treated moments on train)")
            continue
        sub = None
        for share in sorted({est.planted_subsample, max(est.planted_subsample, 0.5), 1.0}):
            if share < 1.0:
                pick = rng.choice(clusters, size=min(len(clusters), max(20, int(len(clusters) * share))), replace=False)
                cand = rs.subset(np.flatnonzero(np.isin(rs.clusters, pick)))
            else:
                cand = rs
            if cand.T.sum() >= 20:
                sub = cand
                break
        if sub is None:
            skipped.append(f"{e}:{b} (fewer than 20 treated moments)")
            continue
        folds = fold_ids(sub, est.n_folds)
        T = sub.T.astype(int)
        e_hat = crossfit_nuisance(sub.X, T, sub.Y, folds, learner, est.seed, "e", None, est.n_jobs, est.threads_per_fit)
        g_real = crossfit_nuisance(sub.X, T, sub.Y, folds, learner, est.seed, "g0", None, est.n_jobs, est.threads_per_fit)
        p0 = np.clip(g_real, 0.02, 0.98)
        runs = []
        for s in range(est.planted_sims):
            tau = est.planted_effect if s % 2 == 0 else 0.0
            p = np.clip(p0 + tau * sub.T, 0.0, 1.0)
            y = (rng.random(sub.n) < p).astype(float)
            truth = float((p - p0)[sub.T == 1].mean())
            sim = RiskSet(e, b, sub.X, sub.T, y, np.ones(sub.n, dtype=bool), sub.clusters, sub.call_idx, sub.k,
                          sub.split, sub.feature_names)
            r = estimate(sim, settings, learner, est.seed + s, e=e_hat)
            if r["status"] != "ok":
                continue
            runs.append({"pair": f"{e}:{b}", "tau": tau, "truth": truth, "att": r["att"],
                         "se": (r["ci_high"] - r["ci_low"]) / (2 * z_crit(est.alpha)),
                         "covered": bool(r["ci_low"] <= truth <= r["ci_high"]),
                         "significant": bool(r["ci_low"] > 0 or r["ci_high"] < 0)})
        if len(runs) < est.planted_sims / 2:
            skipped.append(f"{e}:{b} (only {len(runs)} of {est.planted_sims} simulated datasets estimable)")
            continue
        results += runs
        used.append(f"{e}:{b}")
    out = summarize_planted(pd.DataFrame(results), est.planted_effect)
    out["skipped_pairs"] = skipped
    if not out["n_sims"]:
        out["reason"] = "no behaviour could test the estimator" + (": " + "; ".join(skipped[:4]) if skipped else
                                                                   " (no candidate behaviour)")
    return out


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def summarize_planted(df: pd.DataFrame, effect: float) -> dict:
    if df.empty:
        return {"n_sims": 0, "passed": False, "reason": "no behaviour could test the estimator"}
    eff = df[df["tau"] > 0]
    null = df[df["tau"] == 0]
    bias = float((eff["att"] - eff["truth"]).mean()) if len(eff) else float("nan")
    mcse = float((eff["att"] - eff["truth"]).std(ddof=1) / math.sqrt(len(eff))) if len(eff) > 1 else float("nan")
    null_bias = float(null["att"].mean()) if len(null) else float("nan")
    cov_k, cov_n = int(eff["covered"].sum()), len(eff)
    fp_k, fp_n = int(null["significant"].sum()), len(null)
    cov_lo, cov_hi = _wilson(cov_k, cov_n)
    fp_lo, fp_hi = _wilson(fp_k, fp_n)
    se_med = float(eff["se"].median()) if len(eff) and "se" in eff else float("nan")
    std_bias = bias / se_med if np.isfinite(bias) and np.isfinite(se_med) and se_med > 0 else float("nan")
    bias_ok = bool(np.isfinite(bias) and abs(bias) <= max(0.01, 2.5 * (mcse if np.isfinite(mcse) else 0),
                                                           0.4 * (se_med if np.isfinite(se_med) else 0)))
    cov_ok = bool(cov_n > 0 and cov_hi >= 0.90 and cov_lo <= 0.98)
    fp_ok = bool(fp_n > 0 and fp_lo <= 0.07)
    return {"n_sims": int(len(df)), "planted_effect": effect, "pairs": sorted(df["pair"].unique().tolist()),
            "bias": bias, "bias_mcse": mcse, "median_se": se_med, "standardized_bias": std_bias,
            "null_mean_estimate": null_bias,
            "coverage": cov_k / cov_n if cov_n else float("nan"), "coverage_ci": [cov_lo, cov_hi],
            "false_alarm_rate": fp_k / fp_n if fp_n else float("nan"), "false_alarm_ci": [fp_lo, fp_hi],
            "passed": bool(bias_ok and cov_ok and fp_ok),
            "checks": {"bias_small": bias_ok, "coverage_consistent_with_95": cov_ok,
                       "false_alarms_consistent_with_5": fp_ok}}


def _pilot_table(builder: RiskSetBuilder, pairs, learner, settings) -> pd.DataFrame:
    rows = []
    for (e, b) in pairs:
        rs = builder.build(e, b, ("train",))
        r = estimate(rs, settings, learner, settings.estimator.seed)
        lab = rs.a_lab
        risk_calls = int(len(np.unique(rs.call_idx[lab]))) if rs.n else 0
        treated_calls = int(len(np.unique(rs.call_idx[lab & (rs.T == 1)]))) if rs.n else 0
        rows.append({"event": e, "behaviour": b, "negative_control": b in NEGATIVE_CONTROLS,
                     "risk_calls": risk_calls, "treated_calls": treated_calls,
                     "treated_call_share": treated_calls / risk_calls if risk_calls else 0.0,
                     **{k: r.get(k) for k in ("status", "att", "ci_low", "ci_high", "n_treated", "kept_share",
                                             "attributable", "balance_smd", "max_abs_smd", "events_treated",
                                             "events_control")}})
    return pd.DataFrame(rows)


def _usable_pairs(table: pd.DataFrame, settings) -> list:
    t = table[~table["negative_control"] & (table["status"] == "ok")
              & (table["kept_share"].fillna(0) >= settings.support.kept_borderline)]
    t = t.sort_values(["n_treated", "event", "behaviour"], ascending=[False, True, True])
    return list(zip(t["event"], t["behaviour"]))


def pilot(builder: RiskSetBuilder, settings, precision: dict | None = None) -> dict:
    precision = precision or {}
    pairs_all = [(e, b) for e in PRIMARY_EVENTS for b in candidate_behaviours(e) + list(NEGATIVE_CONTROLS)]
    sizes = []
    for e, b in pairs_all:
        rs = builder.build(e, b, ("train",))
        sizes.append(((e, b), int(rs.T[rs.a_lab].sum())))
    ranked = [p for p, n in sorted(sizes, key=lambda x: (-x[1], x[0])) if p[1] not in NEGATIVE_CONTROLS and n > 0]
    choice = choose_learner(builder, ranked[:2], settings)
    table = _pilot_table(builder, pairs_all, choice["learner"], settings)
    usable = _usable_pairs(table, settings)
    if usable and not set(ranked[:2]) <= set(usable):
        retuned = [f"{e}:{b}" for e, b in ranked[:2] if (e, b) not in usable]
        choice = {**choose_learner(builder, usable[:2], settings), "retuned_because_not_estimable": retuned}
        table = _pilot_table(builder, pairs_all, choice["learner"], settings)
        usable = _usable_pairs(table, settings) or usable
    learner = choice["learner"]
    planted = planted_effect_test(builder, usable + [p for p in ranked if p not in usable], learner, settings)
    family = select_family(table, settings, precision)
    return {"learner": learner, "other_learner": choice["other_learner"], "learner_choice": choice, "table": table,
            "planted": planted, "family": family, "family_rule": " ".join(select_family.__doc__.split()),
            "sensitivity": {k: v[0] for k, v in SENSITIVITY.items()}}


def select_family(table: pd.DataFrame, settings, precision: dict) -> dict:
    """The written, mechanical selection rule for the confirmatory family (per event):
    estimable on train; the behaviour starts in >= min_treated_call_share of risk-set calls; >= min_treated_rows_pilot
    treated rows; >= kept_borderline of treated rows kept after trimming; not measured below precision_min (when a
    precision check exists); ranked by |attributable events| (ties by name); at most max_behaviours_per_event."""
    est, sup, claim = settings.estimator, settings.support, settings.claim
    out = {}
    for e in PRIMARY_EVENTS:
        t = table[(table["event"] == e) & ~table["negative_control"]].copy()
        ok = (t["status"] == "ok") & (t["treated_call_share"] >= est.min_treated_call_share) \
            & (t["n_treated"] >= est.min_treated_rows_pilot) & (t["kept_share"].fillna(0) >= sup.kept_borderline)
        prec_ok = t["behaviour"].map(lambda b: precision.get(b, {}).get("precision", 1.0) >= claim.precision_min)
        t = t[ok & prec_ok]
        t = t.assign(rank_key=t["attributable"].abs()).sort_values(["rank_key", "behaviour"], ascending=[False, True])
        out[e] = t["behaviour"].head(est.max_behaviours_per_event).tolist()
    return out


SENSITIVITY = {
    "S1": ("6-turn horizon", {"horizon": "H"}),
    "S2": ("without name-labelled calls (inferred roles)", {"exclude_named": True}),
    "S3": ("without possibly truncated calls", {"exclude_truncated": True}),
    "S4": ("with unflagged metadata as covariates", {"metadata": True}),
    "S5": ("including moments after another event (earlier events as covariates)", {"clean": False}),
    "S6": ("the other learner", {"learner": "other"}),
    "S7": ("single-call template groups only", {"singletons_only": True}),
    "S8": ("onset shifted -1 and +1 turn", {"onset_shift": (-1, 1)}),
}


def run_variant(builder, e, b, learner, other_learner, settings, name: str, seed: int) -> list[dict]:
    label, spec = SENSITIVITY[name]
    runs = []
    shifts = spec.get("onset_shift", (0,))
    for sh in (shifts if isinstance(shifts, tuple) else (shifts,)):
        v = {k: val for k, val in spec.items() if k not in ("learner", "onset_shift")}
        if "horizon" in v:
            v["horizon"] = settings.landmark.horizon
        if sh:
            v["onset_shift"] = sh
        lrn = other_learner if spec.get("learner") == "other" else learner
        rs = builder.build(e, b, HELD_OUT, v)
        r = estimate(rs, settings, lrn, seed)
        runs.append({"analysis": name if not sh else f"{name}{'+' if sh > 0 else ''}{sh}", "base": name, "label": label,
                     **{k: r.get(k) for k in ("status", "att", "ci_low", "ci_high", "n_rows", "n_treated")}})
    return runs


def negative_controls_clean(nc: pd.DataFrame) -> bool:
    ok = nc[nc["status"] == "ok"]
    return bool(len(ok) >= 1 and ((ok["ci_low"] <= 0) & (ok["ci_high"] >= 0)).all())


def confirm(builder: RiskSetBuilder, prereg: dict, settings, sensitivity_for: str = "candidates") -> pd.DataFrame:
    est = settings.estimator
    learner = prereg["learner"]
    rows = []
    for e in PRIMARY_EVENTS:
        members = [(b, False) for b in prereg["family"].get(e, [])] + [(b, True) for b in prereg["negative_controls"]]
        for b, is_nc in members:
            rs = builder.build(e, b, HELD_OUT)
            r, nuis = estimate(rs, settings, learner, est.seed, return_nuisances=True)
            row = {"event": e, "behaviour": b, "negative_control": is_nc,
                   "family": "negative_control" if is_nc else "confirmatory", "slice": "all", **r}
            for sp in HELD_OUT:
                rr = att_core(rs, nuis[0], nuis[1], settings, rows=np.flatnonzero(rs.split == sp), seed=est.seed,
                              with_balance=False) if nuis is not None else {}
                row[f"att_{sp}"] = rr.get("att", float("nan"))
                row[f"ci_{sp}"] = [rr.get("ci_low", float("nan")), rr.get("ci_high", float("nan"))]
            rows.append(row)
    lib = pd.DataFrame(rows)
    conf = (lib["family"] == "confirmatory").to_numpy()
    lib["q"] = np.nan
    if conf.any():
        lib.loc[conf, "q"] = benjamini_hochberg(lib.loc[conf, "p"].to_numpy(dtype=float))
    nc_clean = {e: negative_controls_clean(lib[(lib["event"] == e) & lib["negative_control"]]) for e in PRIMARY_EVENTS}
    lib["negative_controls_clean"] = lib["event"].map(nc_clean).astype(bool)
    lib["sensitivity"] = [[] for _ in range(len(lib))]
    for i in lib.index:
        r = lib.loc[i]
        if r["family"] != "confirmatory" or r["status"] != "ok":
            continue
        if sensitivity_for == "candidates" and not (r["q"] < est.bh_q):
            continue
        runs = []
        for name in SENSITIVITY:
            runs += run_variant(builder, r["event"], r["behaviour"], learner, prereg["other_learner"], settings,
                                name, est.seed)
        lib.at[i, "sensitivity"] = runs
    return lib
