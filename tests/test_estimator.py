import numpy as np
import pytest

from crest.analysis import RiskSet, att_core, crossfit, estimate, fold_ids, learner_spec
from crest.config import Settings


def simulate_confounded(n=6000, att=0.10, seed=0, clusters=600):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 4)).astype(np.float32)
    e = 1 / (1 + np.exp(-(-1.0 + 1.2 * X[:, 0] - 0.8 * X[:, 1])))
    T = (rng.random(n) < e).astype(np.int8)
    p0 = 1 / (1 + np.exp(-(-0.5 + 1.0 * X[:, 0] + 0.5 * X[:, 2])))
    p = np.clip(p0 + att * T, 0, 1)
    Y = (rng.random(n) < p).astype(float)
    cl = rng.integers(0, clusters, n)
    rs = RiskSet("ESC", "refusal", X, T, Y, np.ones(n, bool), cl, np.arange(n), np.zeros(n, int), np.array(["dev"] * n),
                 [f"x{i}" for i in range(4)])
    naive = Y[T == 1].mean() - Y[T == 0].mean()
    rs.info["true_att"] = float((p - p0)[T == 1].mean())
    return rs, naive


def settings():
    s = Settings()
    s.estimator.bootstrap_draws = 300
    return s


def test_recovers_known_att_under_confounding():
    rs, naive = simulate_confounded()
    truth = rs.info["true_att"]
    r = estimate(rs, settings(), "logistic_ridge", 7)
    assert r["status"] == "ok"
    assert abs(naive - truth) > 0.05
    assert r["ci_low"] <= truth <= r["ci_high"]
    assert abs(r["att"] - truth) < 0.04
    assert r["boot_ci_low"] < r["att"] < r["boot_ci_high"]


def test_null_effect_is_not_significant():
    rs, _ = simulate_confounded(att=0.0, seed=5)
    r = estimate(rs, settings(), "logistic_ridge", 7)
    assert r["ci_low"] <= 0 <= r["ci_high"]


def test_att_core_is_the_doubleml_atte_score():
    rs, _ = simulate_confounded(n=2000, seed=2)
    s = settings()
    e, g0 = crossfit(rs.X, rs.T.astype(int), rs.Y, fold_ids(rs, 5), "logistic_ridge", 0)
    r = att_core(rs, e, g0, s)
    ee = np.clip(e, 1e-3, 1 - 1e-3)
    g = np.clip(g0, 0.0, 1.0)
    keep = ee <= s.estimator.trim_upper
    T, Y = rs.T[keep], rs.Y[keep]
    w = ee[keep] / (1 - ee[keep])
    theta = np.sum(T * (Y - g[keep]) - (1 - T) * w * (Y - g[keep])) / T.sum()
    assert r["att"] == pytest.approx(theta, rel=1e-10)


def _label_error_case(seed, rng, miss_rate=0.4):
    rs, _ = simulate_confounded(n=5000, seed=seed)
    truth_Y = rs.Y.copy()
    miss = (rs.T == 1) & (truth_Y == 1) & (rng.random(rs.n) < miss_rate)
    lab_Y = np.where(miss, 0.0, truth_Y)

    def mk(Y, gold=None):
        return RiskSet(rs.event, rs.behaviour, rs.X, rs.T, Y, rs.a_lab, rs.clusters, rs.call_idx, rs.k, rs.split,
                       rs.feature_names, gold=gold)
    return rs, truth_Y, lab_Y, mk


def test_dsl_is_unbiased_for_the_full_label_estimate():
    rng = np.random.default_rng(5)
    s = settings()
    rs, truth_Y, lab_Y, mk = _label_error_case(103, rng)
    e, g0 = crossfit(rs.X, rs.T.astype(int), lab_Y, fold_ids(rs, 5), "logistic_ridge", 0)
    full = att_core(mk(truth_Y), e, g0, s, with_balance=False)["att"]
    naive = att_core(mk(lab_Y), e, g0, s, with_balance=False)["att"]
    d = []
    for _ in range(300):
        R = rng.random(rs.n) < 0.15
        g = {"R": R, "inv_pi": R / 0.15, "a": np.ones(rs.n, bool), "Y": truth_Y}
        d.append(att_core(mk(lab_Y, g), e, g0, s, with_balance=False)["att"] - full)
    d = np.asarray(d)
    assert abs(naive - full) > 0.1
    assert abs(d.mean()) < 4 * d.std() / np.sqrt(d.size)


def test_dsl_correction_removes_label_error_bias_end_to_end():
    rng = np.random.default_rng(11)
    s = settings()
    naive_err, dsl_err = [], []
    for rep in range(16):
        rs, truth_Y, lab_Y, mk = _label_error_case(100 + rep, rng)
        R = rng.random(rs.n) < 0.3
        gold = {"R": R, "inv_pi": R / 0.3, "a": np.ones(rs.n, bool), "Y": truth_Y}
        truth = rs.info["true_att"]
        naive_err.append(estimate(mk(lab_Y), s, "logistic_ridge", rep)["att"] - truth)
        dsl_err.append(estimate(mk(lab_Y, gold), s, "logistic_ridge", rep)["att"] - truth)
    se = np.std(dsl_err, ddof=1) / np.sqrt(len(dsl_err))
    assert abs(np.mean(naive_err)) > 0.1
    assert abs(np.mean(dsl_err)) < max(0.01, 3 * se)


def test_dsl_corrects_risk_set_membership():
    rs, _ = simulate_confounded(n=3000, seed=4)
    s = settings()
    gold_a = np.ones(rs.n, bool)
    gold_a[:300] = False
    R = np.ones(rs.n, bool)
    rs_g = RiskSet(rs.event, rs.behaviour, rs.X, rs.T, rs.Y, rs.a_lab, rs.clusters, rs.call_idx, rs.k, rs.split,
                   rs.feature_names, gold={"R": R, "inv_pi": R.astype(float), "a": gold_a, "Y": np.where(gold_a, rs.Y, 0.0)})
    e, g0 = crossfit(rs.X, rs.T.astype(int), rs.Y, fold_ids(rs, 5), "logistic_ridge", 0)
    full = att_core(rs_g, e, g0, s)
    sub = att_core(rs.subset(np.arange(300, rs.n)), e[300:], g0[300:], s)
    assert full["att"] == pytest.approx(sub["att"], rel=1e-9)


def test_learner_specs():
    sp = learner_spec({"kind": "logistic_ridge", "prop": {"C": 0.03}})
    assert sp["prop"]["C"] == 0.03 and sp["out"]["alpha"] == 100.0
    with pytest.raises(ValueError):
        learner_spec("random_forest")


def test_matches_doubleml_on_identical_folds():
    dml = pytest.importorskip("doubleml")
    from sklearn.base import clone
    from crest.analysis import make_learners
    rs, _ = simulate_confounded(n=3000, seed=9)
    s = settings()
    s.estimator.trim_upper = 0.999
    s.estimator.propensity_clip = 1e-12
    s.estimator.outcome_clip = False
    folds = fold_ids(rs, 5)
    e, g0 = crossfit(rs.X, rs.T.astype(int), rs.Y, folds, "logistic_ridge", 0)
    ours = att_core(rs, e, g0, s)
    import pandas as pd
    df = pd.DataFrame(rs.X, columns=rs.feature_names).assign(y=rs.Y, d=rs.T.astype(int))
    data = dml.DoubleMLData(df, "y", "d")
    prop, outm = make_learners("logistic_ridge", 0)
    m = dml.DoubleMLIRM(data, ml_g=clone(outm), ml_m=clone(prop), score="ATTE", n_folds=5, n_rep=1,
                        trimming_threshold=1e-12, draw_sample_splitting=False)
    smpls = [(np.flatnonzero(folds != f), np.flatnonzero(folds == f)) for f in range(5)]
    m.set_sample_splitting(smpls)
    m.fit()
    assert float(m.coef[0]) == pytest.approx(ours["att"], abs=2e-3)
