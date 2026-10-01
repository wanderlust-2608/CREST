import json

import numpy as np
import pandas as pd
import pytest

from crest.analysis import HELD_OUT
from crest.definitions import NEGATIVE_CONTROLS, PRIMARY_EVENTS


def test_build_checks_passed(demo):
    checks = demo["pipe"].ws.read_json("checks/build_checks.json")
    assert checks["future_invariance"]["passed"] and checks["future_invariance"]["rows_checked"] >= 500
    assert checks["cue_blindness"]["passed"] and checks["regex_blindness"]["passed"]


def test_risk_sets_follow_the_protocol(demo):
    pipe = demo["pipe"]
    b = pipe.builder(with_gold=False)
    labels = pipe.labels().loc[pipe.corpus().call_ids]
    for e in PRIMARY_EVENTS:
        for beh in ("refusal", "offer_solution", "negative_emotion"):
            rs = b.build(e, beh, HELD_OUT)
            onset = labels[f"{e}_onset"].to_numpy()[rs.call_idx]
            assert not ((onset >= 0) & (rs.k >= onset))[rs.a_lab].any(), "row at or after the onset"
            treated = pd.Series(rs.T[rs.a_lab]).groupby(rs.call_idx[rs.a_lab]).sum()
            assert treated.max() <= 1, "more than one treated row per call"
            assert (rs.k >= pipe.corpus().opening_turns).all()
            assert set(np.unique(rs.split)) <= set(HELD_OUT)


def test_gold_set_rules(demo):
    pipe = demo["pipe"]
    sample = pipe.ws.read_parquet("gold/sample.parquet")
    calls = pipe.corpus().calls
    assert set(calls.loc[sample["transcript_id"], "split"]) <= set(HELD_OUT)
    assert ((sample["pi"] > 0) & (sample["pi"] <= 1)).all()
    m = pipe.ws.read_json("gold/gold_metrics.json")
    for e in PRIMARY_EVENTS:
        assert 0 <= m["by_event"][e]["f1"] <= 1 and m["by_event"][e]["f1_ci"][0] <= m["by_event"][e]["f1"]


def test_gold_ingest_rejects_bad_files(demo, tmp_path):
    from crest.events import ingest_gold
    from crest.io import DataValidationError
    pipe = demo["pipe"]
    sample = pipe.ws.read_parquet("gold/sample.parquet")
    good = pd.read_csv(pipe.ws.root / "gold" / "gold_labelled.csv", dtype=str)
    bad = good.copy()
    bad.loc[bad.index[0], "ESC_present"] = "maybe"
    bad.loc[bad.index[1], "ESC_present"], bad.loc[bad.index[1], "ESC_onset"] = "yes", "9999"
    p = tmp_path / "bad.csv"
    bad.to_csv(p, index=False)
    with pytest.raises(DataValidationError) as err:
        ingest_gold(p, sample, pipe.corpus())
    assert "yes/no" in str(err.value) and "outside" in str(err.value)
    dbl = sample.loc[sample["double_coded"], "transcript_id"].iloc[0]
    nob = good[~((good["transcript_id"] == dbl) & (good["annotator"] == "B"))]
    nob.to_csv(p, index=False)
    with pytest.raises(DataValidationError):
        ingest_gold(p, sample, pipe.corpus())


def test_prereg_is_enforced(demo, tmp_path):
    from crest.io import Workspace
    from crest.prereg import freeze, verify
    pipe = demo["pipe"]
    v = verify(pipe.ws, pipe.s, pipe.corpus(), pipe.labels())
    assert v["ok"], v["problems"]
    ws = Workspace(tmp_path / "w")
    pr = json.loads((pipe.ws.root / "prereg" / "prereg.json").read_text())
    freeze(ws, pr)
    (ws.root / "prereg" / "prereg.json").write_text((ws.root / "prereg" / "prereg.json").read_text().replace("logistic", "LOGISTIC"))
    assert not verify(ws)["ok"]
    with pytest.raises(RuntimeError):
        freeze(ws, dict(pr, family={}))
    rec = freeze(ws, dict(pr, family={}), force=True)
    assert rec["amended"]
    s2 = type(pipe.s).from_dict({"estimator": {"n_folds": 4}})
    assert any("settings" in p for p in verify(pipe.ws, s2)["problems"])


def test_confirm_refuses_without_prereg(demo, tmp_path):
    import copy
    from crest.pipeline import Pipeline
    pipe = demo["pipe"]
    s2 = copy.deepcopy(pipe.s)
    s2.out_dir = str(tmp_path / "w2")
    p2 = Pipeline(s2, log=lambda m: None)
    with pytest.raises((RuntimeError, FileNotFoundError)):
        p2.confirm()


def test_levels_are_computed_by_code(demo):
    from crest.library import validate_library
    pipe = demo["pipe"]
    lib = pipe.library()
    assert validate_library(lib, pipe.s) == []
    assert not lib[lib["behaviour"].isin(NEGATIVE_CONTROLS)]["level"].isin(["L2", "L3"]).any()
    assert not lib[lib["exploratory"]]["level"].eq("L3").any()
    assert not lib[~lib["actionable"]]["level"].eq("L3").any()
    hacked = lib.copy()
    i = hacked.index[hacked["level"] == "L2"][0]
    hacked.at[i, "level"] = "L3"
    assert validate_library(hacked, pipe.s)


def test_level_rules_unit():
    from crest.config import Settings
    from crest.library import assign_level
    ok = {k: True for k in ("preregistered", "actionable", "support_sufficient")}
    row = {"status": "ok", "n_calls": 500}
    assert assign_level(row, ok, "sufficient", False)[0] == "L3"
    assert assign_level(row, dict(ok, actionable=False), "sufficient", False)[0] == "L2"
    assert assign_level(row, ok, "borderline", False)[0] == "L2"
    assert assign_level(row, ok, "insufficient", False)[0] == "L1"
    assert assign_level(row, ok, "sufficient", True)[0] == "L2"
    assert assign_level({"status": "not_estimable", "n_calls": 2}, ok, "insufficient", False)[0] == "L0"
    assert assign_level({"status": "ok", "negative_control": True}, ok, "sufficient", False)[0] == "NC"
    del Settings


def test_perturbations_use_the_same_code_path(demo):
    from crest.evidence import _opening_matrix, build_material, edited_features, neutral_turn
    from crest.landmarks import features_for_call
    pipe = demo["pipe"]
    corpus, lm = pipe.corpus(), pipe.landmarks()
    mat, O = build_material(corpus, lm), _opening_matrix(corpus, lm)
    rng = np.random.default_rng(0)
    for r in rng.choice(len(lm.meta), 60, replace=False):
        c, k, tid = int(lm.meta["call_idx"].iat[r]), int(lm.meta["k"].iat[r]), lm.meta["transcript_id"].iat[r]
        one = corpus.turns_of(tid).reset_index(drop=True)
        j = int(rng.integers(0, k))
        mod = one.drop(index=j).reset_index(drop=True)
        mod["turn_id"] = np.arange(len(mod))
        ref = features_for_call(mod, corpus.calls.loc[[tid]], lm, [k - 1], pipe.s.landmark.last_k)[0]
        assert np.allclose(ref, edited_features(mat, c, k, pipe.s.landmark.last_k, O[c], drop=[j]), atol=1e-6)
        rep = one.copy()
        nt = neutral_turn(one.at[j, "party"], one.at[j, "speaker"])
        for col in nt.columns:
            if col in rep.columns:
                rep.at[j, col] = nt.at[0, col]
        ref = features_for_call(rep, corpus.calls.loc[[tid]], lm, [k], pipe.s.landmark.last_k)[0]
        assert np.allclose(ref, edited_features(mat, c, k, pipe.s.landmark.last_k, O[c], replace=[j]), atol=1e-6)


def test_evidence_spans_are_before_onset_and_quotable(demo):
    pipe = demo["pipe"]
    spans = pipe.ws.read_parquet("evidence/evidence_spans.parquet")
    assert len(spans)
    assert (spans["turn_id"] < spans["onset_turn"]).all()
    text = pd.Series(pipe.corpus().turns["text"].to_numpy(), index=pipe.corpus().turns["turn_uid"].to_numpy())
    assert (spans["quote"].to_numpy() == text.loc[spans["turn_uid"]].to_numpy()).all()
    assert set(pipe.corpus().calls.loc[spans["transcript_id"], "split"]) <= set(HELD_OUT)


def test_search_index(demo, engine):
    idx = engine.art.index
    hits = idx.search("customer asks for a supervisor", {"split": ["dev", "test"]}, top_k=10)
    assert hits and len({h["transcript_id"] for h in hits}) == len(hits)
    text = set(demo["pipe"].corpus().turns["text"])
    for h in hits:
        for line in h["text"].split("\n"):
            assert line.split(": ", 1)[1] in text
    m = demo["metrics"].get("retrieval")
    assert m and m["recall@10"] >= 0.6


def test_bm25_matches_rank_bm25():
    rank_bm25 = pytest.importorskip("rank_bm25")
    from crest.index import BM25, tokenize
    docs = ["the agent refused the refund", "customer asks for a supervisor now", "refund refund please",
            "hold on one moment please", "the the the agent", "supervisor please"]
    toks = [tokenize(d) for d in docs]
    ours, ref = BM25(toks), rank_bm25.BM25Okapi(toks)
    for q in (["refund"], ["the", "agent"], ["supervisor", "please", "please"], ["unknown"]):
        assert np.allclose(ours.get_scores(q), ref.get_scores(q))
        assert np.allclose(ours.get_scores(q, np.array([1, 3, 5])), ref.get_scores(q)[[1, 3, 5]])


def test_cue_copy_is_in_sync_with_the_notebook():
    from crest.devtools import check_cues_sync
    r = check_cues_sync()
    assert r["in_sync"], r


def test_prereg_detects_a_redrawn_gold_sample(demo, tmp_path):
    import shutil
    from crest.io import Workspace
    from crest.prereg import verify
    src = demo["pipe"].ws.root
    for d in ("prereg", "gold"):
        shutil.copytree(src / d, tmp_path / d)
    assert verify(Workspace(tmp_path))["ok"]
    s = pd.read_parquet(tmp_path / "gold" / "sample.parquet")
    s.iloc[1:].to_parquet(tmp_path / "gold" / "sample.parquet", index=False)
    v = verify(Workspace(tmp_path))
    assert not v["ok"] and any("gold sample" in p for p in v["problems"])
