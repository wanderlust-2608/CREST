from __future__ import annotations

import hashlib
import math

import numpy as np
from scipy import stats as sps


def norm_p_two_sided(z: float) -> float:
    return float(2.0 * sps.norm.sf(abs(z))) if np.isfinite(z) else float("nan")


def z_crit(alpha: float = 0.05) -> float:
    return float(sps.norm.isf(alpha / 2.0))


def benjamini_hochberg(pvals) -> np.ndarray:
    p = np.asarray(pvals, dtype=float)
    q = np.full(p.shape, np.nan)
    ok = np.isfinite(p)
    m = int(ok.sum())
    if m == 0:
        return q
    pv = p[ok]
    order = np.argsort(pv, kind="mergesort")
    ranked = pv[order] * m / np.arange(1, m + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(ranked, 1.0)
    q[ok] = out
    return q


def evalue_rr(rr: float) -> float:
    if not np.isfinite(rr) or rr <= 0:
        return float("nan")
    rr = 1.0 / rr if rr < 1 else rr
    return float(rr + math.sqrt(rr * (rr - 1.0)))


def evalue_from_att(p1: float, att: float, ci_low: float, ci_high: float) -> tuple[float, float]:
    def rr_for(effect: float) -> float:
        p0 = p1 - effect
        if not (0 < p1 <= 1 and 0 < p0 <= 1):
            return float("nan")
        return p1 / p0
    point = evalue_rr(rr_for(att))
    if not (np.isfinite(ci_low) and np.isfinite(ci_high)):
        return point, float("nan")
    if ci_low <= 0 <= ci_high:
        return point, 1.0
    limit = ci_low if att > 0 else ci_high
    return point, evalue_rr(rr_for(limit))


def standardized_differences(X: np.ndarray, T: np.ndarray, w_control: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    t = np.asarray(T, dtype=bool)
    if t.sum() == 0 or (~t).sum() == 0:
        return np.full(X.shape[1], np.nan)
    m1 = X[t].mean(axis=0)
    w = np.asarray(w_control, dtype=float)[~t]
    if w.sum() <= 0:
        return np.full(X.shape[1], np.nan)
    m0 = (X[~t] * w[:, None]).sum(axis=0) / w.sum()
    sd = np.sqrt((X[t].var(axis=0) + X[~t].var(axis=0)) / 2.0)
    out = np.zeros(X.shape[1])
    nz = sd > 1e-12
    out[nz] = (m1[nz] - m0[nz]) / sd[nz]
    return out


def cluster_sums(values: np.ndarray, cluster_codes: np.ndarray, n_clusters: int) -> np.ndarray:
    return np.bincount(cluster_codes, weights=values, minlength=n_clusters)


def cluster_bootstrap_ratio(num_by_cluster: np.ndarray, den_by_cluster: np.ndarray, draws: int, seed: int,
                            alpha: float = 0.05, chunk: int = 250) -> tuple[float, float]:
    g = num_by_cluster.shape[0]
    if g < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    stats_ = []
    probs = np.full(g, 1.0 / g)
    for start in range(0, draws, chunk):
        n = min(chunk, draws - start)
        counts = rng.multinomial(g, probs, size=n)
        den = counts @ den_by_cluster
        num = counts @ num_by_cluster
        with np.errstate(divide="ignore", invalid="ignore"):
            stats_.append(np.where(den > 0, num / den, np.nan))
    s = np.concatenate(stats_)
    s = s[np.isfinite(s)]
    if s.size < draws * 0.9:
        return float("nan"), float("nan")
    return float(np.quantile(s, alpha / 2)), float(np.quantile(s, 1 - alpha / 2))


def hashed_folds(groups, k: int, salt: str) -> np.ndarray:
    groups = np.asarray(groups).astype(str)
    uniq, inv = np.unique(groups, return_inverse=True)
    fold_of = np.array([int(hashlib.sha1(f"{salt}:{g}".encode()).hexdigest()[:8], 16) % k for g in uniq], dtype=np.int64)
    return fold_of[inv]


def weighted_prf(y_true, y_pred, weights) -> dict:
    y_true = np.asarray(y_true, dtype=bool)
    y_pred = np.asarray(y_pred, dtype=bool)
    w = np.asarray(weights, dtype=float)
    tp = float(w[y_true & y_pred].sum())
    fp = float(w[~y_true & y_pred].sum())
    fn = float(w[y_true & ~y_pred].sum())
    precision = tp / (tp + fp) if tp + fp > 0 else float("nan")
    recall = tp / (tp + fn) if tp + fn > 0 else float("nan")
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else float("nan")
    return {"precision": precision, "recall": recall, "f1": f1}


def bootstrap_ci(values_fn, n_units: int, draws: int, seed: int, alpha: float = 0.05) -> tuple[float, float]:
    if n_units < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(draws):
        v = values_fn(rng.integers(0, n_units, n_units))
        if v is not None and np.isfinite(v):
            out.append(v)
    if len(out) < draws * 0.5:
        return float("nan"), float("nan")
    return float(np.quantile(out, alpha / 2)), float(np.quantile(out, 1 - alpha / 2))


def cohen_kappa(a, b) -> float:
    a = np.asarray(a)
    b = np.asarray(b)
    if a.size == 0:
        return float("nan")
    cats = np.unique(np.concatenate([a, b]))
    po = float((a == b).mean())
    pe = float(sum((a == c).mean() * (b == c).mean() for c in cats))
    return float("nan") if pe >= 1 else (po - pe) / (1 - pe)


def ppi_mean_ci(y_gold, yhat_gold, yhat_unlabeled, alpha: float = 0.05) -> tuple[float, float, float]:
    y = np.asarray(y_gold, dtype=float)
    fg = np.asarray(yhat_gold, dtype=float)
    fu = np.asarray(yhat_unlabeled, dtype=float)
    n, N = y.size, fu.size
    if n < 2 or N < 2:
        return float("nan"), float("nan"), float("nan")
    rect = y - fg
    theta = float(fu.mean() + rect.mean())
    se = math.sqrt(fu.var(ddof=1) / N + rect.var(ddof=1) / n)
    z = z_crit(alpha)
    return theta, theta - z * se, theta + z * se


def paired_bootstrap_diff(a_by_unit, b_by_unit, draws: int = 2000, seed: int = 0, alpha: float = 0.05) -> dict:
    d = np.asarray(a_by_unit, dtype=float) - np.asarray(b_by_unit, dtype=float)
    d = d[np.isfinite(d)]
    if d.size < 2:
        return {"diff": float("nan"), "ci": [float("nan"), float("nan")], "p_one_sided": float("nan")}
    rng = np.random.default_rng(seed)
    means = np.array([d[rng.integers(0, d.size, d.size)].mean() for _ in range(draws)])
    return {"diff": float(d.mean()), "ci": [float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))],
            "p_one_sided": float((means <= 0).mean())}


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.asarray(x, dtype=float)))
