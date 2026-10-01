from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "01_data_cleaning.ipynb"
sys.path.insert(0, str(Path(__file__).parent))
from make_synthetic_fixture import generate


@pytest.fixture(scope="module")
def cleaned(tmp_path_factory):
    nbformat = pytest.importorskip("nbformat")
    nbconvert = pytest.importorskip("nbconvert.preprocessors")
    tmp = tmp_path_factory.mktemp("clean")
    records, truth = generate(n=800, seed=7)
    raw_path = tmp / "synthetic_transcripts.json"
    raw_path.write_text(json.dumps(records), encoding="utf-8")
    out_dir = tmp / "cleaned_data"
    env_backup = dict(os.environ)
    os.environ.update(RAW_TRANSCRIPTS_PATH=str(raw_path), CLEANED_DATA_DIR=str(out_dir))
    try:
        nb = nbformat.read(NOTEBOOK, as_version=4)
        ep = nbconvert.ExecutePreprocessor(timeout=900, kernel_name=os.environ.get("TEST_KERNEL", "python3"))
        ep.preprocess(nb, {"metadata": {"path": str(NOTEBOOK.parent)}})
    finally:
        os.environ.clear()
        os.environ.update(env_backup)
    return {
        "truth": {t["transcript_id"]: t for t in truth},
        "json": json.loads((out_dir / "cleaned_data.json").read_text(encoding="utf-8")),
        "turns": pd.read_parquet(out_dir / "turns.parquet"),
        "convs": pd.read_parquet(out_dir / "conversations.parquet"),
        "quarantine": pd.read_parquet(out_dir / "annotations_quarantine.parquet"),
        "report": json.loads((out_dir / "cleaning_report.json").read_text(encoding="utf-8")),
        "out_dir": out_dir,
    }


def test_all_outputs_written(cleaned):
    for name in ["cleaned_data.json", "turns.parquet", "conversations.parquet", "annotations_quarantine.parquet",
                 "speaker_role_map.csv", "domain_mapping.csv", "duplicates.csv", "qc_log.csv",
                 "leakage_audit.csv", "column_availability.csv", "cleaning_report.json", "DATA_CARD.md"]:
        assert (cleaned["out_dir"] / name).is_file(), name
    assert all(c["ok"] for c in cleaned["report"]["integrity_checks"])


def test_exact_duplicates_dropped(cleaned):
    kept = set(cleaned["convs"]["transcript_id"])
    dups = [t for t in cleaned["truth"].values() if t["duplicate_of"]]
    assert dups, "fixture should contain duplicates"
    for t in dups:
        assert t["transcript_id"] not in kept
        assert t["duplicate_of"] in kept


def test_speaker_roles_match_truth(cleaned):
    by_call = {r["transcript_id"]: [t["speaker"].lower() for t in r["conversation"]] for r in cleaned["json"]}
    wrong = []
    for tid, roles in by_call.items():
        expected = cleaned["truth"][tid]["expected_roles"]
        if roles != expected:
            wrong.append(tid)
    assert not wrong, f"{len(wrong)} calls with wrong roles, e.g. {wrong[:3]}"
    named = [t for t in cleaned["truth"].values() if t["named_speakers"] and not t["duplicate_of"]]
    assert len(named) > 20


def test_annotations_quarantined_and_markers_removed(cleaned):
    convs = cleaned["convs"].set_index("transcript_id")
    for tid, t in cleaned["truth"].items():
        if tid not in convs.index:
            continue
        assert convs.loc[tid, "n_annotations_removed"] == t["n_annotations"], tid
        assert convs.loc[tid, "n_marker_events"] == t["n_marker_only"], tid
    labels = set(cleaned["turns"]["speaker_label_raw"])
    assert not any(l.startswith(("-", "[", "*", "(N", "(S")) for l in labels)
    assert {"Domain", "Outcome", "Key Events", "Student"}.isdisjoint(labels)


def test_embedded_dialogues_resplit(cleaned):
    convs = cleaned["convs"].set_index("transcript_id")
    emb = [tid for tid, t in cleaned["truth"].items() if t["embedded"] and tid in convs.index]
    assert emb
    for tid in emb:
        assert convs.loc[tid, "had_embedded_dialogue"]
        assert convs.loc[tid, "n_turns"] == len(cleaned["truth"][tid]["expected_roles"])
    assert not cleaned["turns"]["text"].str.contains(r"\\n").any()


def test_business_domain_recovered(cleaned):
    convs = cleaned["convs"].set_index("transcript_id")
    rows = [(convs.loc[tid, "business_domain"], t["domain"]) for tid, t in cleaned["truth"].items()
            if tid in convs.index and t["scenario"] != "degenerate"]
    acc = sum(a == b for a, b in rows) / len(rows)
    assert acc >= 0.97, acc
    assert set(convs["domain_raw"].dropna()) == {"Insurance"}


def test_event_signals(cleaned):
    convs = cleaned["convs"].set_index("transcript_id")
    for tid, t in cleaned["truth"].items():
        if tid not in convs.index or t["scenario"] == "degenerate":
            continue
        c = convs.loc[tid]
        if t["scenario"] == "escalation":
            assert c["ev_escalation"] and c["escalation_turn_id"] >= 0, tid
            assert c["esc_customer_requested"], tid
        if t["has_supervisor"]:
            assert c["esc_supervisor_joined"], tid
        if t["scenario"] == "refund":
            assert c["ev_refund"], tid
        if t["scenario"] == "churn":
            assert c["ev_churn_risk"], tid
        if t["scenario"] == "confusion":
            assert c["customer_cue_confusion"] > 0, tid
        if t["scenario"] in ("smooth", "hold", "confusion"):
            assert not c["ev_escalation"], tid


def test_event_turn_precedes_supervisor(cleaned):
    turns = cleaned["turns"]
    first_sup = turns[turns["speaker"] == "Supervisor"].groupby("transcript_id")["turn_id"].min()
    convs = cleaned["convs"].set_index("transcript_id")
    assert (convs.loc[first_sup.index, "escalation_turn_id"] <= first_sup).all()


def test_text_views(cleaned):
    turns = cleaned["turns"]
    assert (turns["text"].str.len() > 0).all() and (turns["text_clean"].str.len() > 0).all()
    assert not turns["text"].str.contains("’").any()
    assert turns["n_filled_pauses"].sum() > 0
    assert not turns["text_clean"].str.contains(r"\b(?:um|uh)\b(?! huh)", regex=True).any()
    assert turns["turn_uid"].is_unique


def test_splits_deterministic_and_complete(cleaned):
    convs = cleaned["convs"]
    assert set(convs["split"]) <= {"train", "dev", "test"}
    share = convs["split"].value_counts(normalize=True)
    assert 0.7 < share["train"] < 0.9


def test_reused_calls_share_template_group_and_split(cleaned):
    convs = cleaned["convs"].set_index("transcript_id")
    variants = [t for t in cleaned["truth"].values() if t["near_dup_of"]]
    assert variants, "fixture should contain re-used calls"
    for t in variants:
        a, b = convs.loc[t["transcript_id"]], convs.loc[t["near_dup_of"]]
        assert a["template_group"] == b["template_group"] and a["split"] == b["split"], t["transcript_id"]
        assert a["near_dup_cluster_size"] >= 2
    assert (cleaned["convs"].groupby("template_group")["split"].nunique() == 1).all()


def test_leakage_audit_flags_post_call_reason(cleaned):
    audit = cleaned["report"]["leakage_audit"]
    assert "reason_for_call" in audit["flagged_fields"]
    assert "intent_key" not in audit["flagged_fields"] and "intent" not in audit["flagged_fields"]
    leak = pd.read_csv(cleaned["out_dir"] / "leakage_audit.csv")
    row = leak[(leak["probe"] == "predictive") & (leak["field"] == "reason_for_call") & (leak["target"] == "ev_refund")]
    assert len(row) == 1 and bool(row["flagged"].iloc[0])
    assert float(row["excess_auc"].iloc[0]) >= 0.05
    content = leak[(leak["probe"] == "content") & (leak["field"] == "reason_for_call")]
    assert bool(content["flagged"].iloc[0])


def test_column_availability_registry(cleaned):
    avail = pd.read_csv(cleaned["out_dir"] / "column_availability.csv")
    for table, df in (("turns", cleaned["turns"]), ("conversations", cleaned["convs"])):
        cls = avail[avail["table"] == table].set_index("column")["availability"]
        assert set(df.columns) <= set(cls.index), set(df.columns) - set(cls.index)
        assert cls.notna().all()
    turns = avail[avail["table"] == "turns"].set_index("column")["availability"]
    convs = avail[avail["table"] == "conversations"].set_index("column")
    assert turns["rel_position"] == "whole-call" and turns["phase"] == "whole-call"
    assert turns["cue_escalation_request"] == "turn-past" and turns["text"] == "turn-past"
    assert convs.loc["n_turns", "availability"] == "whole-call"
    assert convs.loc["ev_escalation", "availability"] == "outcome"
    assert convs.loc["escalation_turn_id", "availability"] == "outcome"
    assert convs.loc["opening_domain_vote", "availability"] == "opening"
    assert convs.loc["template_group", "availability"] == "design"
    assert bool(convs.loc["reason_for_call", "leakage_flag"])
    assert convs.loc["reason_for_call", "usable_as_covariate"].startswith("no")
    assert convs.loc["business_domain", "usable_as_covariate"].startswith("no")


def test_opening_domain_vote(cleaned):
    convs = cleaned["convs"].set_index("transcript_id")
    rows = [(convs.loc[tid, "opening_domain_vote"], t["domain"]) for tid, t in cleaned["truth"].items()
            if tid in convs.index and t["scenario"] != "degenerate"]
    acc = sum(a == b for a, b in rows) / len(rows)
    assert acc >= 0.9, acc
