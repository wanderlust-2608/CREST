import json

import pytest

from crest.cli import main
from crest.session import SessionState, restore_spec

FLOWS = [
    ["Why does this happen?", "escalations", "only hotel calls", "and refunds?"],
    ["Give me an overview", "what about escalations?", "in airline calls", "explain the first factor"],
    ["Why do customers get frustrated?", "in telecom calls", "what about churn threats?", "show me examples"],
    ["Why do customers who were refused a refund escalate?", "show me examples", "only hotel calls", "remove the filter"],
    ["Did escalations increase after the new refund policy was introduced?", "it started on 8 November",
     "what about refunds?", "only airline calls"],
    ["Which behaviours raise escalations by more than five percentage points?", "what about refunds?", "and churn?"],
    ["Which industry has the most refund requests?", "why?", "why in hotel calls?", "compare with airline calls"],
    ["Why do customers escalate?", "¿y los reembolsos?", "waht about refnds in hotle calls?", "go back to escalations"],
    ["Do escalations lead to refund requests?", "what about churn threats?", "explain the second factor"],
    ["How can we reduce escalations?", "what about premium customers?", "and for refunds?",
     "new question: why do customers churn?"],
    ["What should agents stop doing?", "only hotel calls", "what about escalations?"],
    ["Why do customers escalate?", "", "what about them?", "how many escalations after 8 November?"],
    ["hello", "why do customers ask for refunds?", "compare with escalations", "in hotel calls"],
    ["Is customer frustration linked to escalations?", "and apologies?", "by more than 5 points?", "what about refunds?"],
    ["Which customers are at risk of leaving?", "why?", "only telecom calls", "what about escalations?"],
    ["Why do customers escalate?", "tell me more about that call", "what about refunds?", "only hotel calls"],
    ["Hello", "give me an overview", "what about churn threats?", "and in airline calls?"],
    ["Why do customers who were refused a refund and threatened to cancel escalate?", "only hotel calls",
     "what about refunds?"],
    ["Which behaviours do not affect escalations?", "what about refunds?", "Why do customers escalate?"],
]


def _round_trip(state):
    return SessionState.from_dict(json.loads(json.dumps(state.to_dict())))


def _run(engine, flow):
    state, out = None, []
    for q in flow:
        ans, state = engine.ask(q, state)
        out.append(ans)
        state = _round_trip(state)
    return out, state


@pytest.mark.parametrize("flow", FLOWS, ids=[f"flow{i + 1:02d}" for i in range(len(FLOWS))])
def test_follow_up_flows_never_crash_or_drop_sentences(engine, flow):
    answers, state = _run(engine, flow)
    for q, ans in zip(flow, answers):
        assert not ans["dropped"] and not ans["degraded"], (q, [d["text"] for d in ans["dropped"]])
        assert ans["text"].strip(), q
    assert state.turn_count == len(flow)


def _spec(ans):
    return ans["spec"] or {}


def test_clarify_then_answer_then_refilter(engine):
    a, _ = _run(engine, FLOWS[0])
    assert a[0]["sentences"][-1]["kind"] == "clarify"
    assert (a[1]["route"], _spec(a[1])["event"]) == ("new_lookup", "ESC")
    assert (a[2]["route"], _spec(a[2])["filters"]) == ("refilter", {"industry": ["hospitality"]})
    assert (_spec(a[3])["event"], _spec(a[3])["filters"]) == ("REF", {"industry": ["hospitality"]})


def test_ranking_then_why_explains_the_top_group(engine):
    a, _ = _run(engine, FLOWS[6])
    top = a[0]["pack"]["rank"]["groups"][0]["value"]
    assert (_spec(a[1])["question_type"], _spec(a[1])["filters"]) == ("why", {"industry": [top]})
    assert _spec(a[2])["filters"] == {"industry": ["hospitality"]}
    assert _spec(a[3])["compare"]["values"] == ["hospitality", "airline"]


def test_policy_date_follow_up_keeps_the_change_for_the_next_event(engine):
    a, _ = _run(engine, FLOWS[4])
    assert a[0]["sentences"][-1]["kind"] == "clarify"
    assert _spec(a[1])["change"]["date"] == "2025-11-08" and a[1]["route"] == "new_lookup"
    assert (_spec(a[2])["event"], _spec(a[2])["change"]["date"]) == ("REF", "2025-11-08")
    assert _spec(a[3])["filters"] == {"industry": ["airline"]} and _spec(a[3])["change"]["date"] == "2025-11-08"


def test_multilingual_and_misspelled_follow_ups(engine):
    a, _ = _run(engine, FLOWS[7])
    assert _spec(a[1])["event"] == "REF" and "Spanish" in a[1]["text"]
    assert (_spec(a[2])["event"], _spec(a[2])["filters"]) == ("REF", {"industry": ["hospitality"]})
    assert "'refnds' as 'refunds'" in a[2]["text"]
    assert _spec(a[3])["event"] == "ESC"


def test_empty_and_vague_follow_ups_ask_without_losing_the_state(engine):
    a, state = _run(engine, FLOWS[11])
    assert a[1]["route"] == a[2]["route"] == "clarify"
    assert _spec(a[2])["event"] == "ESC"
    assert (_spec(a[3])["question_type"], _spec(a[3])["filters"]) == ("how_often", {"date_from": "2025-11-08"})


def test_greeting_overview_shared_and_behaviour_turns_lead_into_single_events(engine):
    a, _ = _run(engine, FLOWS[12])
    assert _spec(a[0])["question_type"] == "help" and _spec(a[1])["event"] == "REF"
    assert _spec(a[2])["compare"]["values"] == ["REF", "ESC"]
    a, _ = _run(engine, FLOWS[1])
    assert _spec(a[0])["question_type"] == "overview" and _spec(a[1])["event"] == "ESC"
    a, _ = _run(engine, FLOWS[10])
    assert _spec(a[0])["question_type"] == "shared" and (_spec(a[2])["event"], _spec(a[2])["compare"]) == ("ESC", None)
    a, _ = _run(engine, FLOWS[2])
    assert (_spec(a[2])["event"], _spec(a[2])["question_type"], _spec(a[2])["behaviour"]) == \
        ("CHURN", "effect_of", "negative_emotion")


def test_retention_risk_is_a_separate_event_in_sessions(engine):
    a, _ = _run(engine, FLOWS[14])
    assert _spec(a[0])["event"] == "RISK"
    assert _spec(a[2])["filters"] == {"industry": ["telecom"]} and _spec(a[3])["event"] == "ESC"


def test_session_state_rejects_non_objects_and_cleans_bad_fields():
    with pytest.raises(TypeError):
        SessionState.from_dict([1, 2])
    st = SessionState.from_dict({"spec": "x", "turn_count": "3", "shown_factor_ids": "F1", "summary": [1, "a"], "zzz": 1})
    assert (st.spec, st.turn_count, st.shown_factor_ids, st.summary) == (None, 0, [], ["a"])
    assert restore_spec({"event": "NOPE"}) is None
    assert restore_spec({"event": "ESC", "filters": {"industry": "x"}}) is None
    assert restore_spec({"event": "ESC", "filters": {"industry": ["mars"]}}) is None
    assert restore_spec({"event": "ESC", "question_type": "why", "colour": "red"}).event == "ESC"


def test_stale_or_edited_state_starts_a_new_conversation(engine):
    st = SessionState.from_dict({"spec": {"event": "ESC", "question_type": "dance", "filters": []}, "turn_count": 2})
    ans, st = engine.ask("what about refunds?", st)
    assert ans["route"] == "first" and _spec(ans)["event"] == "REF" and not ans["dropped"]
    assert "saved conversation could not be used" in ans["text"]
    ans, st = engine.ask("Why do customers escalate?")
    st.shown_factor_ids = ["F999"]
    ans, st = engine.ask("explain the first factor", _round_trip(st))
    assert "not in the current answer" in ans["text"] and not ans["dropped"]


def test_cli_ask_recovers_from_a_corrupt_session_file(demo, tmp_path, capsys):
    pipe = demo["pipe"]
    sess = tmp_path / "session.json"
    base = ["--data", pipe.s.data_dir, "--out", pipe.s.out_dir, "ask"]
    for garbage in ("{not json", "[1, 2, 3]", '{"spec": {"event": 7}}'):
        sess.write_text(garbage)
        main(base + ["Why do customers escalate?", "--session", str(sess)])
        assert "route: first" in capsys.readouterr().out
        assert json.loads(sess.read_text())["spec"]["event"] == "ESC"
    main(base + ["only hotel calls", "--session", str(sess)])
    assert "route: refilter" in capsys.readouterr().out
    assert json.loads(sess.read_text())["spec"]["filters"] == {"industry": ["hospitality"]}


def test_that_call_opens_the_quoted_call_and_leaving_it_restores_slices(engine):
    a, state = _run(engine, FLOWS[15])
    quoted = a[0]["sentences"]
    first = next(u for x in quoted if x["kind"] == "quote" for u in x["turn_uids"]).rsplit(":", 1)[0]
    assert (_spec(a[1])["question_type"], _spec(a[1])["filters"]) == ("call", {"call": [first.lower()]})
    assert (_spec(a[2])["event"], _spec(a[2])["question_type"]) == ("REF", "call")
    assert (_spec(a[3])["question_type"], _spec(a[3])["filters"]) == ("why", {"industry": ["hospitality"]})


def test_overview_follow_up_and_conditions_carry_over(engine):
    a, _ = _run(engine, FLOWS[16])
    assert [_spec(x)["question_type"] for x in a] == ["help", "overview", "why", "why"]
    assert _spec(a[3])["filters"] == {"industry": ["airline"]} and _spec(a[3])["event"] == "CHURN"
    a, _ = _run(engine, FLOWS[17])
    assert _spec(a[1])["filters"] == {"with_event": ["REF_DENIED", "CHURN"], "industry": ["hospitality"]}
    assert _spec(a[2])["event"] == "REF"
    a, _ = _run(engine, FLOWS[18])
    assert _spec(a[1])["threshold"]["op"] == "null" and _spec(a[2])["threshold"] is None
