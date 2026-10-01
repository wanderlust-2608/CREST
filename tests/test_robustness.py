import shutil

import numpy as np
import pandas as pd
import pytest

from crest.analysis import RiskSet, att_core, estimate, support_band
from crest.config import Settings
from crest.io import DataValidationError, load_corpus


def _rs(n=50, treated=0):
    T = np.zeros(n, np.int8)
    T[:treated] = 1
    return RiskSet("ESC", "refusal", np.zeros((n, 2), np.float32), T, np.zeros(n), np.ones(n, bool), np.arange(n) % 5,
                   np.arange(n), np.zeros(n, int), np.array(["dev"] * n), ["a", "b"])


def test_no_treated_rows_is_not_estimable():
    r = estimate(_rs(treated=0), Settings(), "logistic_ridge", 0)
    assert r["status"] == "not_estimable" and np.isnan(r["att"])
    assert support_band(r, Settings().support)[0] == "insufficient"


def test_everything_trimmed_is_not_estimable():
    rs = _rs(treated=10)
    e = np.full(rs.n, 0.99)
    r = att_core(rs, e, np.zeros(rs.n), Settings())
    assert r["status"] == "not_estimable"


def test_settings_validation():
    with pytest.raises(KeyError):
        Settings.from_dict({"estimator": {"no_such_key": 1}})
    with pytest.raises(ValueError):
        Settings.from_dict({"estimator": {"trim_upper": 1.5}})
    with pytest.raises(ValueError):
        Settings.from_dict({"claim": {"min_sensitivity": ["S9"]}})


def test_missing_data_folder():
    with pytest.raises(FileNotFoundError):
        load_corpus("/nonexistent/cleaned_data")


def test_broken_cleaned_data_is_rejected(demo, tmp_path):
    src = demo["root"] / "cleaned_data"
    for breakage in ("drop_column", "duplicate_turn_uid", "straddling_template", "no_registry"):
        d = tmp_path / breakage
        shutil.copytree(src, d)
        if breakage == "drop_column":
            t = pd.read_parquet(d / "turns.parquet").drop(columns=["cue_refusal"])
            t.to_parquet(d / "turns.parquet", index=False)
        elif breakage == "duplicate_turn_uid":
            t = pd.read_parquet(d / "turns.parquet")
            t.loc[1, "turn_uid"] = t.loc[0, "turn_uid"]
            t.to_parquet(d / "turns.parquet", index=False)
        elif breakage == "straddling_template":
            c = pd.read_parquet(d / "conversations.parquet")
            tr, te = c.index[c["split"] == "train"][0], c.index[c["split"] == "test"][0]
            c.loc[te, "template_group"] = c.loc[tr, "template_group"]
            c.to_parquet(d / "conversations.parquet", index=False)
        else:
            (d / "column_availability.csv").unlink()
        with pytest.raises(DataValidationError):
            load_corpus(d)


def test_gold_from_train_is_rejected(demo):
    from crest.analysis import RiskSetBuilder
    pipe = demo["pipe"]
    corpus = pipe.corpus()
    train_id = corpus.calls.index[corpus.calls["split"] == "train"][0]
    gold = pd.DataFrame({"transcript_id": [train_id], "pi": [0.1], "ESC_onset": [-1], "REF_onset": [-1], "CHURN_onset": [-1]})
    with pytest.raises(ValueError):
        RiskSetBuilder(corpus, pipe.landmarks(), pipe.labels(), pipe.occurrences(), pipe.s, gold)


@pytest.mark.parametrize("q", ["", "???", "Why?", "Tell me about calls", "x" * 5000, "¿Por qué escalan los clientes?",
                               "Why do escalations happen in Antarctica calls on 2031-02-30?"])
def test_odd_questions_never_crash(engine, q):
    ans, st = engine.ask(q)
    assert isinstance(ans["text"], str) and ans["text"]


def test_filter_with_no_calls(engine):
    ans, _ = engine.ask("Why do escalations happen at shopnest in telecom calls?")
    assert ans["text"] and not ans["dropped"]


def test_run_without_gold_caps_claims_at_l2(demo, tmp_path):
    from crest.library import build_library
    pipe = demo["pipe"]
    lib = pipe.library()
    conf = lib[~lib["exploratory"]].copy()
    ctx = {"settings": pipe.s, "prereg_ok": True, "prereg_sha256": "x", "planted_passed": True, "gold": None,
           "precision": pipe.precision(), "cooc": None, "learner": "", "library_version": "t"}
    new = build_library(conf.drop(columns=["factor_id"]), ctx)
    assert not (new["level"] == "L3").any()
    assert new.loc[new["level"] == "L2", "failed_checks"].map(lambda x: "gold_f1_ok" in x).any()


def test_calls_without_turns_are_set_aside(demo, tmp_path):
    from crest.events import lexicon_labels
    src = demo["root"] / "cleaned_data"
    d = tmp_path / "with_empty_call"
    shutil.copytree(src, d)
    c = pd.read_parquet(d / "conversations.parquet")
    empty = c.iloc[[0]].copy()
    empty["transcript_id"], empty["n_turns"] = "empty-call", 0
    empty["file_order"] = c["file_order"].max() + 1
    empty["template_group"] = "empty-call-group"
    pd.concat([c, empty], ignore_index=True).to_parquet(d / "conversations.parquet", index=False)
    corpus = load_corpus(d)
    assert list(corpus.excluded["transcript_id"]) == ["empty-call"]
    assert corpus.n_calls == len(c) and "empty-call" not in corpus.calls.index
    labels = lexicon_labels(corpus)
    assert len(labels) == corpus.n_calls


def test_report_numbers_tolerate_missing_values():
    from crest.evaluate import _ci, _fmt
    assert _fmt(None) == "n/a" and _fmt(float("nan")) == "n/a" and _fmt("x") == "n/a"
    assert _fmt(0.1234, "+.1f", 100) == "+12.3"
    assert _ci({"mean": None, "ci": [None, None], "n": 0}) == "n/a"
    assert _ci({"mean": 0.5, "ci": [None, 0.6], "n": 3}) == "50.0% (95% CI n/a–60.0%, n=3)"


def test_negative_control_rule_needs_one_estimable_control():
    from crest.analysis import negative_controls_clean
    ok = {"status": "ok", "ci_low": -0.02, "ci_high": 0.03}
    flagged = {"status": "ok", "ci_low": 0.01, "ci_high": 0.05}
    rare = {"status": "not_estimable", "ci_low": np.nan, "ci_high": np.nan}
    assert negative_controls_clean(pd.DataFrame([ok, rare]))
    assert not negative_controls_clean(pd.DataFrame([rare, rare]))
    assert not negative_controls_clean(pd.DataFrame([ok, flagged]))
    assert not negative_controls_clean(pd.DataFrame(columns=["status", "ci_low", "ci_high"]))


def test_effect_question_about_a_factor_without_estimate_gives_counts(engine):
    from crest.definitions import BEHAVIOURS
    from crest.queries import EV_WORD
    lib = engine.art.library
    rows = lib[(lib["slice"] == "all") & (lib["level"] == "L1") & (lib["status"] == "ok") & ~lib["negative_control"]]
    if not len(rows):
        pytest.skip("no L1 factor with an estimate in this synthetic library")
    r = rows.iloc[0]
    short = BEHAVIOURS[r["behaviour"]].short
    ans, _ = engine.ask(f"{'Are' if short.endswith('s') else 'Is'} {short} linked to {EV_WORD[r['event']][0]}?")
    assert not ans["degraded"] and not ans["dropped"]
    assert "no reliable estimate" in ans["text"] and "Counts only" in ans["text"]


def test_question_about_a_negative_control_says_so(engine):
    ans, _ = engine.ask("Does reading back details affect escalations?")
    assert "negative control" in ans["text"] and not ans["degraded"]


def test_thread_settings_do_not_change_the_preregistration_hash():
    a, b = Settings(), Settings()
    b.estimator.threads_per_fit, b.estimator.n_jobs = 0, 4
    assert a.hash() == b.hash()
    with pytest.raises(ValueError):
        Settings.from_dict({"estimator": {"n_jobs": 0}}).validate()
