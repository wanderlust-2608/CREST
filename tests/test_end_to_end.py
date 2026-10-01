import json

from crest.queries import load_jsonl


def test_every_stage_recorded(demo):
    stages = demo["pipe"].ws.manifest()["stages"]
    for st in ("build", "gold-sample", "gold-ingest", "pilot", "prereg", "confirm", "evidence", "index", "queries",
               "run-queries", "evaluate"):
        assert st in stages, st
    assert (demo["pipe"].ws.root / "REPORT.md").is_file()


def test_planted_effect_test_passed(demo):
    pl = demo["pipe"].ws.read_json("pilot/pilot.json")["planted"]
    assert pl["passed"], pl


def test_known_effects_are_recovered(demo):
    cv = demo["metrics"]["causal_validity"]
    assert cv["n"] >= 9
    assert cv["coverage"]["mean"] >= 0.75
    assert cv["false_l3"] == 0
    if cv["l3_count"]:
        assert cv["l3_sign_correct"] == 1.0
    t = {(r["event"], r["behaviour"]): r for r in cv["table"]}
    esc_ref = t[("ESC", "refusal")]
    assert esc_ref["ci_low"] > 0


def test_negative_controls_do_not_become_claims(demo):
    lib = demo["pipe"].library()
    nc = lib[lib["negative_control"]]
    assert (nc["level"] == "NC").all()


def test_query_set_answers(demo):
    m = demo["metrics"]
    for sp in ("dev", "test"):
        s = m[sp]
        assert s["expected_behaviour_met"]["mean"] >= 0.9, (sp, s["by_category"])
        assert s["wording_violations_after_gates"] == 0
        assert s["sentences_dropped_by_gates"] == 0, s["dropped_by_gate"]
        assert s["followup_carry_over"]["mean"] >= 0.9
        assert s["degraded_answers"] == 0
    assert m["dev"]["B2"]["carry_over"]["mean"] < m["dev"]["followup_carry_over"]["mean"]


def test_outputs_have_citations_that_resolve(demo):
    pipe = demo["pipe"]
    turns = set(pipe.corpus().turns["turn_uid"])
    rows = load_jsonl(pipe.ws.root / "outputs" / "outputs_test.jsonl")
    n = 0
    for r in rows:
        for t in (r["turns"] if r["category"] == "session" else [r]):
            for s in t["sentences"]:
                for u in s["turn_uids"]:
                    assert u in turns
                    n += 1
    assert n > 0


def test_locked_test_queries_detect_tampering(demo, tmp_path):
    import shutil
    import pytest
    pipe = demo["pipe"]
    p = pipe.ws.root / "queries" / "queries_test.jsonl"
    backup = tmp_path / "q.jsonl"
    shutil.copy(p, backup)
    try:
        p.write_text(p.read_text() + json.dumps({"id": "x", "category": "why", "question": "Why?", "expected": {}}) + "\n")
        with pytest.raises(RuntimeError):
            pipe.run_queries("test")
    finally:
        shutil.copy(backup, p)


def test_evidence_quality_reported(demo):
    ev = demo["pipe"].ws.read_json("evidence/forecaster_quality.json")
    aucs = [q["auc_next_turn"] for q in ev["forecaster_quality"].values() if q.get("auc_next_turn") is not None]
    assert aucs and min(aucs) > 0.6


def test_queries_are_organised_by_task_difficulty_kind_and_use_case(demo):
    root = demo["pipe"].ws.root
    items = load_jsonl(root / "queries" / "queries_dev.jsonl") + load_jsonl(root / "queries" / "queries_test.jsonl")
    assert all(q[k] for q in items for k in ("task", "difficulty", "query_type", "use_case"))
    assert {q["task"] for q in items} == {"task1", "task2"}
    assert {q["difficulty"] for q in items} == {"easy", "medium", "hard"}
    assert {"simple_retrieval", "multi_hop", "ambiguous", "cannot_answer", "premise_check", "follow_up"} <= \
        {q["query_type"] for q in items}
    assert 50 <= len(items) <= 100
    lock = demo["pipe"].ws.read_json("queries/queries_lock.json")
    assert sum(lock["distribution"]["difficulty"].values()) == len(items)
    m = demo["metrics"]["dev"]
    assert set(m["by_difficulty"]) == {"easy", "medium", "hard"} and m["by_query_type"]
    outs = load_jsonl(root / "outputs" / "outputs_test.jsonl")
    assert all("difficulty" in r for r in outs)
