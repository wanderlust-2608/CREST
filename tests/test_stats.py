import math

import numpy as np
import pytest

from crest import stats


def test_benjamini_hochberg_matches_hand_computation():
    p = [0.01, 0.04, 0.03, 0.5, np.nan]
    q = stats.benjamini_hochberg(p)
    assert np.allclose(q[:4], [0.04, 0.0533333, 0.0533333, 0.5], atol=1e-6)
    assert np.isnan(q[4])


def test_evalue_published_example():
    assert stats.evalue_rr(3.9) == pytest.approx(7.26, abs=0.01)
    assert stats.evalue_rr(1 / 3.9) == pytest.approx(7.26, abs=0.01)
    point, ci = stats.evalue_from_att(0.5, 0.25, 0.1, 0.4)
    assert point == pytest.approx(2 + math.sqrt(2), abs=1e-9)
    assert stats.evalue_from_att(0.5, 0.1, -0.1, 0.3)[1] == 1.0


def test_standardized_differences_weighted():
    X = np.array([[0.0], [1.0], [0.0], [2.0]])
    T = np.array([True, True, False, False])
    smd = stats.standardized_differences(X, T, np.array([1, 1, 1.0, 1.0]))
    sd = math.sqrt((np.var([0, 1]) + np.var([0, 2])) / 2)
    assert smd[0] == pytest.approx((0.5 - 1.0) / sd)
    w = np.array([0, 0, 3.0, 1.0])
    assert stats.standardized_differences(X, T, w)[0] == pytest.approx(0.0)


def test_cluster_bootstrap_ratio_covers_ratio():
    rng = np.random.default_rng(0)
    num = rng.normal(2.0, 1.0, 300)
    den = np.ones(300)
    lo, hi = stats.cluster_bootstrap_ratio(num, den, 1000, seed=1)
    assert lo < num.mean() < hi
    assert hi - lo < 0.5


def test_hashed_folds_deterministic_and_group_respecting():
    groups = np.array(["a", "b", "a", "c", "b", "d"] * 10)
    f1 = stats.hashed_folds(groups, 3, "salt")
    f2 = stats.hashed_folds(groups[::-1], 3, "salt")[::-1]
    assert (f1 == f2).all()
    for g in np.unique(groups):
        assert len(set(f1[groups == g])) == 1


def test_weighted_prf_uses_inverse_probability_weights():
    y = np.array([1, 1, 0, 0], bool)
    p = np.array([1, 0, 1, 0], bool)
    r = stats.weighted_prf(y, p, [1, 1, 3, 1])
    assert r["precision"] == pytest.approx(0.25)
    assert r["recall"] == pytest.approx(0.5)


def test_cohen_kappa_known_value():
    a = [1, 1, 0, 0, 1, 0, 1, 1]
    b = [1, 0, 0, 0, 1, 0, 1, 1]
    po = 7 / 8
    pe = (5 / 8) * (4 / 8) + (3 / 8) * (4 / 8)
    assert stats.cohen_kappa(a, b) == pytest.approx((po - pe) / (1 - pe))


def test_ppi_mean_matches_formula_and_reference_package():
    rng = np.random.default_rng(3)
    y = rng.binomial(1, 0.6, 200).astype(float)
    yhat = np.clip(y + rng.normal(0, 0.3, 200), 0, 1)
    yhat_u = np.clip(rng.binomial(1, 0.6, 5000) + rng.normal(0, 0.3, 5000), 0, 1)
    theta, lo, hi = stats.ppi_mean_ci(y, yhat, yhat_u)
    assert theta == pytest.approx(yhat_u.mean() + (y - yhat).mean())
    ppi = pytest.importorskip("ppi_py")
    ref = ppi.ppi_mean_ci(y, yhat, yhat_u, alpha=0.05)
    assert lo == pytest.approx(float(np.ravel(ref[0])[0]), abs=2e-3)
    assert hi == pytest.approx(float(np.ravel(ref[1])[0]), abs=2e-3)


def test_paired_bootstrap_detects_difference():
    a = np.full(50, 1.0)
    b = np.zeros(50)
    r = stats.paired_bootstrap_diff(a, b, 500)
    assert r["diff"] == 1.0 and r["ci"][0] > 0
