from crest.query import QueryParser, QuerySpec
from crest.session import SessionState, merge, propose_delta, route

P = QueryParser(brands=["shopnest", "northstar airways"], intents=["Delivery Delays"], flagged={"reason_for_call"},
                year_hint=2025)


def test_slots():
    s = P.parse("Why do escalations happen in telecom calls?")
    assert (s.event, s.question_type, s.filters) == ("ESC", "why", {"industry": ["telecom"]})
    s = P.parse("How often do customers ask for a supervisor at northstar airways?")
    assert s.question_type == "how_often" and s.filters["brand"] == ["northstar airways"]
    s = P.parse("Compare escalation rates between airline and telecom calls")
    assert s.question_type == "compare" and s.compare == {"dimension": "industry", "values": ["airline", "telecom"]}
    assert P.parse("How can we reduce churn?").question_type == "what_to_change"


def test_presuppositions_and_leading():
    s = P.parse("Why does empathy cause escalations?")
    assert s.presuppositions == [{"behaviour": "empathy", "event": "ESC", "direction": 1, "strength": "causal"}]
    assert P.parse("Does empathy cause escalations?").presuppositions == []
    s = P.parse("Isn't it true that policy refusals cause escalations?")
    assert s.leading and s.presuppositions[0]["behaviour"] == "refusal"
    assert P.parse("How much does apologising reduce refunds?").presuppositions[0]["direction"] == -1


def test_unsupported_and_declined():
    s = P.parse("Which premium customers in Miami churn the most?")
    assert {u["attribute"] for u in s.unsupported} == {"customer tier", "location"}
    s = P.parse("Why do calls whose reason for call mentions billing escalate?")
    assert s.declined_filters and s.declined_filters[0]["field"] == "reason_for_call"
    assert not P.parse("customers in a frustrated emotional state escalate?").unsupported


def test_ambiguous():
    assert P.parse("Why does this happen?").ambiguous


def test_followups_keep_unmentioned_filters():
    prev = P.parse("Why do escalations happen in telecom calls?")
    d = propose_delta(prev, "what about refunds?", P)
    new = merge(prev, d, "what about refunds?")
    assert new.event == "REF" and new.filters == {"industry": ["telecom"]} and route(prev, new, d) == "new_lookup"
    d2 = propose_delta(new, "only airline calls", P)
    n2 = merge(new, d2, "only airline calls")
    assert n2.filters == {"industry": ["airline"]} and n2.event == "REF" and route(new, n2, d2) == "refilter"
    d3 = propose_delta(n2, "also hotel calls", P)
    assert merge(n2, d3, "").filters == {"industry": ["airline", "hospitality"]}
    d4 = propose_delta(n2, "and across all industries?", P)
    assert merge(n2, d4, "").filters == {}


def test_followup_routes_and_clarify():
    prev = P.parse("Why do customers escalate?")
    for text, want in [("explain the second factor", "reuse"), ("why?", "reuse"), ("show me examples", "new_lookup"),
                       ("what about that one?", "clarify"), ("new question: how often do refunds happen?", "new_lookup")]:
        d = propose_delta(prev, text, P)
        new = merge(prev, d, text) if not d["clarify"] else prev
        assert route(prev, new, d) == want, text


def test_describe_factor_ends_when_the_slice_changes():
    prev = P.parse("Why do escalations happen in airline calls?")
    d = propose_delta(prev, "explain the first factor", P)
    desc = merge(prev, d, "explain the first factor")
    assert desc.question_type == "describe_factor" and desc.factor_ref == "#1"
    d2 = propose_delta(desc, "and across all industries?", P)
    after = merge(desc, d2, "")
    assert after.question_type == "why" and after.factor_ref is None


def test_engine_session_and_versioned_cache(engine):
    ans, st = engine.ask("Why do escalations happen in hotel calls?")
    assert st.spec["filters"] == {"industry": ["hospitality"]}
    ans2, st = engine.ask("what about refunds?", st)
    assert ans2["route"] == "new_lookup" and st.spec["event"] == "REF" and st.spec["filters"] == {"industry": ["hospitality"]}
    ans3, st = engine.ask("explain the first factor", st)
    assert ans3["route"] == "reuse"
    again, _ = engine.ask("Why do escalations happen in hotel calls?")
    assert again["cache_hit"]
    k1 = engine.cache_key(QuerySpec.from_dict(ans["spec"]), [])
    old = engine.art.library_version
    engine.art.library_version = "lib-changed"
    try:
        assert engine.cache_key(QuerySpec.from_dict(ans["spec"]), []) != k1
    finally:
        engine.art.library_version = old


def test_state_roundtrip():
    st = SessionState(spec={"event": "ESC"}, shown_factor_ids=["F1"])
    assert SessionState.from_dict(st.to_dict()).shown_factor_ids == ["F1"]


def _replay(first, turns):
    prev = P.parse(first)
    out = []
    for q in turns:
        d = propose_delta(prev, q, P)
        new = merge(prev, d, q) if not d["clarify"] else prev
        out.append((route(prev, new, d), new))
        prev = new
    return out


def test_standalone_question_does_not_inherit_old_filters():
    (r1, a), (r2, b), (r3, c) = _replay("What share of hotel calls include refund requests?", [
        "How often do customers threaten to cancel?", "what about refunds?", "how often does that happen in hotel calls?"])
    assert a.filters == {} and a.event == "CHURN"
    assert b.filters == {} and b.event == "REF"
    assert c.filters == {"industry": ["hospitality"]}
    (_, d), = _replay("Is hold time linked to escalations in telecom calls?", ["Why do customers ask for refunds?"])
    assert d.filters == {} and d.behaviour is None and d.question_type == "why"


def test_ranking_and_comparing_industries_clears_the_industry_filter():
    (_, a), (_, b), (_, c) = _replay("What share of hotel calls include refund requests?", [
        "Which industry has the most refund requests?", "Compare refund requests between hotel and airline calls",
        "show me examples"])
    assert a.filters == {} and a.compare["rank"]
    assert b.filters == {} and b.compare["values"] == ["hospitality", "airline"]
    assert c.question_type == "examples" and c.filters == {}


def test_excluding_an_industry_and_asking_about_the_others():
    rest = ["airline", "telecom", "banking", "insurance", "retail_ecommerce"]
    assert P.parse("Why do escalations happen in calls other than hotel calls?").filters == {"industry": rest}
    assert P.parse("Why do escalations happen in non-hotel calls?").filters == {"industry": rest}
    assert P.parse("How often do refunds happen excluding airline calls?").filters["industry"] == \
        ["hospitality", "telecom", "banking", "insurance", "retail_ecommerce"]
    assert P.parse("Why do escalations not happen in hotel calls?").filters == {"industry": ["hospitality"]}
    (r1, a), (r2, b) = _replay("Show me examples of calls where customers escalate in hotel calls", [
        "in other domains", "what about escalations in domains other than hotel calls"])
    assert r1 == "refilter" and a.filters == {"industry": rest}
    assert b.filters == {"industry": rest} and b.event == "ESC"


def test_naming_the_current_event_again_answers_instead_of_asking():
    (r, a), = _replay("Why do refunds happen in hotel calls?", ["what about refunds?"])
    assert r == "reuse" and a.event == "REF" and a.filters == {"industry": ["hospitality"]}
