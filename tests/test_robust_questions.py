import pytest

from crest.query import QueryParser
from crest.session import SessionState, merge, propose_delta

P = QueryParser(brands=["shopnest", "northstar airways"], year_hint=2025)


def attrs(spec):
    return {u["attribute"] for u in spec.unsupported}


def test_misspellings_are_corrected_and_reported():
    s = P.parse("why do custmers escalte so often?")
    assert (s.event, s.question_type) == ("ESC", "why")
    assert s.notes == [{"kind": "reading", "items": [["custmers", "customers"], ["escalte", "escalate"]]}]
    s = P.parse("chrun in airlnie calls")
    assert s.event == "CHURN" and s.filters["industry"] == ["airline"]


def test_real_words_are_never_corrected():
    for q in ("Why do customers want their money back?", "How quite often do refunds happen?",
              "Why do customers fight with agents about refunds?", "How do we manage refund requests?"):
        s = P.parse(q)
        assert s.event == "REF" and not s.notes and "industry" not in s.filters, (q, s)


def test_slang_and_other_languages():
    s = P.parse("What makes callers blow up and demand the boss?")
    assert (s.event, s.behaviour) == ("ESC", "negative_emotion")
    assert ["the boss", "a supervisor"] in s.notes[0]["items"]
    s = P.parse("¿Por qué los clientes piden un reembolso?")
    assert (s.event, s.question_type) == ("REF", "why") and s.notes[0]["language"] == "Spanish"
    s = P.parse("customers refund kyun maangte hain?")
    assert (s.event, s.question_type) == ("REF", "why") and s.notes[0]["kind"] == "language"
    assert not P.parse("Why do customers escalate?").notes


def test_thresholds_on_effects_and_on_rates():
    s = P.parse("Which behaviours raise escalations by more than five percentage points?")
    assert s.event == "ESC" and s.threshold["value"] == pytest.approx(0.05) and s.threshold["direction"] == 1
    assert "effect-size threshold" in attrs(s)
    s = P.parse("Which industries have more than 20% refund requests?")
    assert s.compare["rank"] and s.threshold["value"] == pytest.approx(0.2) and "rate threshold" in attrs(s)


def test_policy_change_needs_a_date_and_takes_it_from_a_follow_up():
    s = P.parse("Did escalations increase after the new refund policy was introduced?")
    assert (s.event, s.question_type, s.compare) == ("ESC", "trend", None)
    assert s.change == {"what": "new refund policy", "side": "after", "date": None}
    d = propose_delta(s, "it started on 8 November", P)
    new = merge(s, d, "it started on 8 November")
    assert new.change["date"] == "2025-11-08" and "date_from" not in new.filters
    s = P.parse("Compare refunds before and after 2025-11-08")
    assert s.change["date"] == "2025-11-08" and not s.ambiguous and s.event == "REF"


def test_conditions_between_events():
    s = P.parse("Why do customers who were refused a refund escalate?")
    assert (s.event, s.question_type, s.filters, s.behaviour) == ("ESC", "why", {"with_event": ["REF_DENIED"]}, None)
    s = P.parse("Why do customers escalate after a refund is denied?")
    assert s.event == "ESC" and s.filters["with_event"] == ["REF_DENIED"]
    s = P.parse("Do refunds happen more in calls with escalations?")
    assert s.event == "REF" and s.filters["with_event"] == ["ESC"]
    s = P.parse("Do escalations lead to refund requests?")
    assert s.question_type == "event_link" and "with_event" not in s.filters


def test_brand_words_do_not_become_industries_and_product_questions_have_no_behaviour():
    s = P.parse("What drives refund requests for Northstar Airways calls in telecom calls?")
    assert s.filters == {"industry": ["telecom"], "brand": ["northstar airways"]}
    s = P.parse("What should the product team fix to reduce churn threats?")
    assert (s.question_type, s.behaviour) == ("issues", None)


def test_behaviour_only_questions_get_a_profile_not_a_clarification():
    s = P.parse("Why do customers get frustrated?")
    assert (s.event, s.question_type, s.behaviour, s.ambiguous) == (None, "behaviour", "negative_emotion", "")
    d = propose_delta(s, "what about escalations?", P)
    new = merge(s, d, "what about escalations?")
    assert (new.event, new.question_type, new.behaviour) == ("ESC", "effect_of", "negative_emotion")


def _kinds(ans):
    return [s["kind"] for s in ans["sentences"]]


def test_every_answer_type_explains_itself(engine):
    for q in ("How have escalations changed over time?", "What do customers complain about before they ask for a supervisor?",
              "Do the behaviours that raise escalations also raise churn threats?", "Do escalations lead to refund requests?",
              "Are customer hesitations linked to escalations?", "Why do customers who were refused a refund escalate?",
              "Which behaviours raise escalations by more than five percentage points?", "why do custmers escalte so often?",
              "¿Por qué los clientes piden un reembolso?", "Which premium customers escalate the most?"):
        ans, _ = engine.ask(q)
        assert not ans["dropped"] and not ans["degraded"], (q, [d["text"] for d in ans["dropped"]])
        assert "rationale" in _kinds(ans), (q, ans["text"])
    ans, st = engine.ask("Why do refunds happen?")
    ans, st = engine.ask("explain the first factor", st)
    assert ans["spec"]["question_type"] == "describe_factor" and "rationale" in _kinds(ans)


def test_condition_threshold_proxy_and_profile_answers(engine):
    ans, _ = engine.ask("Why do customers who were refused a refund escalate?")
    assert ans["text"].startswith("This answer looks only at calls where a refund was refused")
    ans, _ = engine.ask("Which behaviours raise escalations by more than five percentage points?")
    assert "Behaviours whose estimated difference" in ans["text"] or "No behaviour's estimated difference" in ans["text"]
    ans, _ = engine.ask("Which premium customers escalate the most?")
    assert "customer-tier field" in ans["text"] and "proxy" in ans["text"]
    ans, _ = engine.ask("Why do customers get frustrated?")
    assert not ans["dropped"] and "How this relates to the business events" in ans["text"]
    assert "rationale" in _kinds(ans)


def test_policy_question_asks_for_the_date_then_compares(engine):
    ans, st = engine.ask("Did escalations increase after the new refund policy was introduced?")
    assert ans["sentences"][-1]["kind"] == "clarify" and "When did the new refund policy start?" in ans["text"]
    day = engine.builder.example_date()
    ans, st = engine.ask(f"it started on {day}", st)
    assert ans["route"] == "new_lookup" and not ans["dropped"], [d["text"] for d in ans["dropped"]]
    assert "before " + day in ans["text"] and "not to the new refund policy" in ans["text"]
    assert "Interrupted time series" in ans["text"] and "Placebo check" in ans["text"]
    ans, _ = engine.ask("Did refunds go up after 1 March 2020?", SessionState())
    assert "outside the calls in the data" in ans["text"]


def test_event_less_questions_rate_questions_and_factor_ids():
    s = P.parse("What should agents stop doing?")
    assert s.question_type == "shared" and s.compare["values"] == ["ESC", "REF", "CHURN"] and not s.ambiguous
    assert P.parse("Why does this happen?").ambiguous
    s = P.parse("What is the escalation rate in November 2025?")
    assert (s.event, s.question_type, s.filters["date_from"]) == ("ESC", "how_often", "2025-11-01")
    s = P.parse("Are refunds more than 10% of calls?")
    assert s.threshold["target"] == "rate" and "rate threshold" in attrs(s)
    assert P.parse("Tell me about factor F1").factor_ref == "F1"
    prev = P.parse("Why do customers escalate?")
    new = merge(prev, propose_delta(prev, "compare with refunds", P), "compare with refunds")
    assert new.question_type == "compare" and new.compare == {"dimension": "event", "values": ["ESC", "REF"]}


def test_event_less_and_factor_id_answers(engine):
    ans, _ = engine.ask("What should agents stop doing?")
    assert not ans["dropped"] and "shared" in _kinds(ans) and "rationale" in _kinds(ans)
    fid = engine.art.library["factor_id"].iloc[0]
    ans, _ = engine.ask(f"Tell me about factor {fid}")
    assert ans["spec"]["question_type"] == "describe_factor" and f"[{fid}]" in ans["text"]
    ans, _ = engine.ask("Are refunds more than 10% of calls?")
    assert "threshold in the question" in ans["text"] and not ans["dropped"]


class _StubLLM:
    available = True
    model = "stub"

    def __init__(self, english):
        self.english = english
        self.calls = []

    def json_call(self, system, user, schema, purpose, effort=None):
        self.calls.append(purpose)
        if purpose == "normalize_query":
            return {"english": self.english, "language": "Swahili"}
        if purpose == "delta":
            return {"ops": [{"op": "set", "slot": "event", "value": "REF"}], "clarify": ""}
        raise RuntimeError("not used")


def test_llm_fallback_reads_what_the_rules_cannot(engine):
    from crest.session import Engine
    stub = _StubLLM("Why do customers ask for a supervisor?")
    eng = Engine(engine.art, engine.s, engine.parser, llm=stub)
    ans, st = eng.ask("Kwa nini wateja wanaomba msimamizi?")
    assert ans["spec"]["event"] == "ESC" and "normalize_query" in stub.calls and not ans["dropped"]
    assert "read (with the LLM) as" in ans["text"]
    ans, st = eng.ask("na marejesho ya pesa je?", st)
    assert ans["spec"]["event"] == "REF" and "delta" in stub.calls
    plain = Engine(engine.art, engine.s, engine.parser)
    ans, _ = plain.ask("Kwa nini wateja wanaomba msimamizi?")
    assert ans["route"] == "first" and any(s["kind"] == "clarify" for s in ans["sentences"])


def test_several_conditions_and_the_main_event():
    s = P.parse("Why do customers who were refused a refund and threatened to cancel escalate?")
    assert (s.event, s.filters) == ("ESC", {"with_event": ["REF_DENIED", "CHURN"]})
    s = P.parse("Do refunds happen more in calls with escalations and churn threats?")
    assert (s.event, s.filters) == ("REF", {"with_event": ["ESC", "CHURN"]})
    s = P.parse("What drives churn threats in calls where a supervisor joined?")
    assert (s.event, s.question_type, s.filters) == ("CHURN", "why", {"with_event": ["HANDOFF"]})
    assert P.parse("Show me calls where customers escalate").question_type == "examples"


def test_single_call_questions():
    q = QueryParser(year_hint=2025, call_ids={"abc123", "36bc5284-d07b-b626-326a-b4614a74e6a8"})
    s = q.parse("Why did call 36BC5284-D07B-B626-326A-B4614A74E6A8 escalate?")
    assert (s.event, s.question_type, s.filters) == ("ESC", "call", {"call": ["36bc5284-d07b-b626-326a-b4614a74e6a8"]})
    s = q.parse("what happened in abc123?")
    assert (s.event, s.question_type, s.ambiguous) == (None, "call", "")
    assert q.parse("tell me about call #4471").filters == {"call": ["4471"]}
    for text in ("How many calls in 2025 escalated?", "calls from 2025-11-08 with refunds"):
        assert "call" not in q.parse(text).filters, text


def test_no_effect_modifier_counterfactual_and_account_questions():
    s = P.parse("Which behaviours do not affect escalations?")
    assert (s.event, s.question_type, s.threshold["op"]) == ("ESC", "why", "null") and "no clear effect" in attrs(s)
    assert P.parse("Does empathy not affect escalations?").threshold is None
    s = P.parse("Does empathy reduce escalations only when the customer is already frustrated?")
    assert s.behaviour == "empathy" and "effect modification" in attrs(s)
    assert "effect modification" not in attrs(P.parse("Does empathy reduce escalations only in hotel calls?"))
    s = P.parse("If agents had offered a solution earlier in this call, would the customer still have escalated?")
    assert "single-call counterfactual" in attrs(s)
    assert not attrs(P.parse("If agents had offered solutions earlier, would fewer customers escalate?"))
    assert "plan or segment" in attrs(P.parse("Why do customers on the premium plan escalate?"))
    assert "account age" in attrs(P.parse("Do new customers escalate more?"))
    q = QueryParser(year_hint=2025, account={"plan": ["basic", "unlimited"]})
    s = q.parse("Why do customers on the premium plan escalate?")
    assert "plan or segment" not in attrs(s) and "which plan or segment" in s.ambiguous


def test_direction_words_ask_for_a_trend_and_other_languages_name_churn():
    for text in ("Did escalations go up in the second week?", "Have refund requests increased in hotel calls?",
                 "Are churn threats rising?", "Did the number of escalations change?"):
        assert P.parse(text).question_type == "trend", text
    assert P.parse("Did empathy increase escalations?").question_type == "effect_of"
    for text in ("¿Por qué los clientes amenazan con irse?", "Pourquoi les clients menacent-ils de partir ?",
                 "Warum drohen Kunden zu gehen?", "Por que os clientes ameaçam sair?",
                 "Perché i clienti minacciano di andarsene?", "customers chhodne ki dhamki kyun dete hain?"):
        assert P.parse(text).event == "CHURN", text
    assert P.parse("Pourquoi les clients partent-ils en vacances?").event is None
    assert P.parse("y do customers want there money bak?").event == "REF"
    assert not P.parse("why do customers want their money back?").notes


def test_call_and_no_effect_answers_pass_the_gates(engine):
    lab, calls = engine.art.labels, engine.art.calls
    on = lab.loc[calls["transcript_id"], "ESC_onset"].to_numpy()
    tid = str(calls["transcript_id"][on >= 0].iloc[0])
    ans, st = engine.ask(f"Why did call {tid} escalate?")
    kinds = _kinds(ans)
    assert ans["spec"]["question_type"] == "call" and not ans["dropped"] and "quote" in kinds, ans["text"]
    assert ans["text"].startswith(f"Call {tid} is") and "Then the escalation" in ans["text"]
    ans, _ = engine.ask("did the agent apologise?", st)
    assert ans["spec"]["behaviour"] == "apology" and ans["spec"]["question_type"] == "call" and not ans["dropped"]
    ans, _ = engine.ask("What happened in call 00000000-0000-0000-0000-000000000000?")
    assert "No call with the id" in ans["text"]
    ans, _ = engine.ask(f"What happened in call {tid[:8]}?")
    assert ans["text"].startswith(f"Call {tid} is")
    ans, _ = engine.ask("Which behaviours do not affect escalations?")
    assert not ans["dropped"] and ("no clear difference" in ans["text"] or "none of their intervals" in ans["text"])
    ans, _ = engine.ask("Why do customers who were refused a refund and threatened to cancel escalate?")
    assert not ans["dropped"] and "calls where a refund was refused and a churn threat came up" in ans["text"]
