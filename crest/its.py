from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

FREQS = (("7D", "week", 168.0), ("D", "day", 24.0), ("6h", "6-hour block", 6.0), ("h", "hour", 1.0))
MIN_SIDE = 6
MIN_CALLS = 15
MAX_PLACEBOS = 20


def call_times(calls: pd.DataFrame) -> pd.Series:
    if "time_of_interaction" in calls.columns:
        ts = pd.to_datetime(calls["time_of_interaction"], errors="coerce")
        if ts.notna().any():
            return ts.reset_index(drop=True)
    if "call_date" in calls.columns:
        ts = pd.to_datetime(calls["call_date"], errors="coerce")
        if "call_hour" in calls.columns:
            ts = ts + pd.to_timedelta(pd.to_numeric(calls["call_hour"], errors="coerce").fillna(0), unit="h")
        return ts.reset_index(drop=True)
    return pd.Series(pd.NaT, index=range(len(calls)))


def build_series(ts: pd.Series, y: np.ndarray, mask: np.ndarray, freq: str) -> pd.DataFrame:
    ok = mask & ts.notna().to_numpy()
    if not ok.any():
        return pd.DataFrame(columns=["period", "n", "k", "rate"])
    df = pd.DataFrame({"period": ts[ok].dt.floor(freq).to_numpy(), "y": y[ok].astype(float)})
    g = df.groupby("period")["y"].agg(["size", "sum"]).reset_index()
    g.columns = ["period", "n", "k"]
    g["rate"] = g["k"] / g["n"]
    return g


def choose_freq(ts: pd.Series, y: np.ndarray, mask: np.ndarray, date: pd.Timestamp):
    for freq, label, hours in FREQS:
        s = build_series(ts, y, mask, freq)
        if not len(s):
            return None
        s = s[s["n"] >= 5]
        pre, post = s[s["period"] < date], s[s["period"] >= date]
        if len(pre) >= MIN_SIDE and len(post) >= MIN_SIDE and s["n"].median() >= MIN_CALLS:
            return freq, label, hours
    return None


def _season(periods: pd.Series, freq: str, n_pre: int, n_post: int) -> tuple[np.ndarray, str]:
    if freq in ("h", "6h") and min(n_pre, n_post) >= (48 if freq == "h" else 8):
        key = periods.dt.hour if freq == "h" else periods.dt.hour // 6
        return pd.get_dummies(key, drop_first=True).to_numpy(dtype=float), "time-of-day"
    if freq == "D" and min(n_pre, n_post) >= 14:
        return pd.get_dummies(periods.dt.dayofweek, drop_first=True).to_numpy(dtype=float), "day-of-week"
    return np.zeros((len(periods), 0)), ""


def _hac(Xw: np.ndarray, u: np.ndarray, lags: int) -> np.ndarray:
    Z = Xw * u[:, None]
    S = Z.T @ Z
    for lag in range(1, lags + 1):
        G = Z[lag:].T @ Z[:-lag]
        S += (1 - lag / (lags + 1)) * (G + G.T)
    return S


def segmented_fit(s: pd.DataFrame, date: pd.Timestamp, freq: str, hours: float, seasonal: bool = True) -> dict:
    s = s[s["n"] >= 5].sort_values("period").reset_index(drop=True)
    t = ((s["period"] - date) / pd.Timedelta(hours=hours)).to_numpy(dtype=float)
    post = (s["period"] >= date).to_numpy(dtype=float)
    n_pre, n_post = int((post == 0).sum()), int(post.sum())
    S_, season = _season(s["period"], freq, n_pre, n_post) if seasonal else (np.zeros((len(s), 0)), "")
    X = np.column_stack([np.ones(len(s)), t, post, t * post, S_])
    if S_.shape[1]:
        X[:, 4:] -= X[:, 4:].mean(axis=0)
    y = s["rate"].to_numpy(dtype=float)
    w = s["n"].to_numpy(dtype=float)
    T, k = X.shape
    if T - k < 3:
        return {"ok": False}
    sw = np.sqrt(w / w.mean())
    Xw, yw = X * sw[:, None], y * sw
    beta, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    u = yw - Xw @ beta
    lags = max(1, int(np.floor(4 * (T / 100) ** (2 / 9))))
    bread = np.linalg.pinv(Xw.T @ Xw)
    V = bread @ _hac(Xw, u, lags) @ bread * T / (T - k)
    se = np.maximum(np.sqrt(np.clip(np.diag(V), 0, None)), np.sqrt(np.clip(np.diag(bread) * (u @ u) / (T - k), 0, None)))
    tcrit = float(stats.t.ppf(0.975, T - k))
    resid = y - X @ beta
    rho1 = float(np.corrcoef(resid[1:], resid[:-1])[0, 1]) if T > 3 and np.std(resid) > 0 else float("nan")

    def ci(j):
        return [float(beta[j] - tcrit * se[j]), float(beta[j] + tcrit * se[j])]

    return {"ok": True, "n_pre": n_pre, "n_post": n_post, "periods": T, "lags": lags, "season": season,
            "base": float(beta[0]), "pre_slope": float(beta[1]), "pre_slope_ci": ci(1), "level": float(beta[2]),
            "level_se": float(se[2]), "level_ci": ci(2), "slope": float(beta[3]), "slope_se": float(se[3]),
            "slope_ci": ci(3), "rho1": rho1}


def placebos(s: pd.DataFrame, date: pd.Timestamp, freq: str, hours: float, seasonal: bool) -> list[float]:
    pre = s[(s["period"] < date) & (s["n"] >= 5)].sort_values("period").reset_index(drop=True)
    if len(pre) < 2 * MIN_SIDE:
        return []
    idx = np.arange(MIN_SIDE, len(pre) - MIN_SIDE + 1)
    if len(idx) > MAX_PLACEBOS:
        idx = np.unique(np.linspace(idx[0], idx[-1], MAX_PLACEBOS).round().astype(int))
    out = []
    for i in idx:
        f = segmented_fit(pre, pre["period"].iloc[i], freq, hours, seasonal)
        if f.get("ok"):
            out.append(f["level"])
    return out


def analyse(ts: pd.Series, y: np.ndarray, mask: np.ndarray, date: str, control_mask: np.ndarray | None = None) -> dict:
    D = pd.Timestamp(date)
    pick = choose_freq(ts, y, mask, D)
    if pick is None:
        return {"available": False, "reason": "too few periods with enough calls on each side of the date"}
    freq, label, hours = pick
    s = build_series(ts, y, mask, freq)
    fit = segmented_fit(s, D, freq, hours)
    if not fit.get("ok"):
        return {"available": False, "reason": "too few periods for the model"}
    out = {"available": True, "freq": freq, "unit": label, **fit}
    pl = placebos(s, D, freq, hours, True)
    out["placebo_levels"] = pl
    out["placebo_large"] = int(sum(abs(p) >= abs(fit["level"]) for p in pl))
    if control_mask is not None and control_mask.any():
        c = segmented_fit(build_series(ts, y, control_mask, freq), D, freq, hours)
        if c.get("ok"):
            d = fit["level"] - c["level"]
            se = float(np.sqrt(fit["level_se"] ** 2 + c["level_se"] ** 2))
            out["control"] = {"level": c["level"], "level_ci": c["level_ci"], "diff": d, "diff_ci": [d - 1.96 * se, d + 1.96 * se]}
    return out
