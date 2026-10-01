import json

import pytest

from crest.definitions import UNSUPPORTED_MESSAGES, unsupported_message
from crest.evaluate import judge_queries
from crest.gates import gate_causal, gate_numbers
from crest.queries import load_jsonl, query_diversity, questions_of
from crest.query import QueryParser
from crest.session import merge, propose_delta

P = QueryParser(brands=["shopnest", "northstar airways"], year_hint=2025)


def attrs(spec):
    return {u["attribute"] for u in spec.unsupported}


def test_questions_that_used_to_be_answered_as_something_else():
    s = P.parse("Do escalations lead to refund requests?")
    assert s.question_type == "event_link" and s.compare["values"] == ["ESC", "REF"]
    assert "effects between events" in attrs(s)
    s = P.parse("Which industry has the most refund requests?")
    assert (s.event, s.question_type, s.compare["rank"], s.compare["dimension"]) == ("REF", "compare", True, "industry")
    s = P.parse("Which industry has the highest escalation rate, and what drives escalations there?")
    assert s.compare["rank"] and s.compare["explain_top"]
    s = P.parse("Do the behaviours that raise escalations also raise churn threats?")
    assert s.question_type == "shared" and s.compare["values"] == ["ESC", "CHURN"]
    s = P.parse("Does empathy reduce escalations and refunds?")
    assert s.question_type == "shared" and s.behaviour == "empathy"
    assert attrs(P.parse("Does sarcasm make customers threaten to cancel?")) == {"unmeasured behaviour"}
    assert attrs(P.parse("Does the customer's tone of voice predict escalations?")) == {"audio"}
    s = P.parse("How long are customers kept on hold before they escalate?")
    assert attrs(s) == {"call duration"} and s.behaviour == "hold_request"
    s = P.parse("What would happen to escalations if agents never refused anything?")
    assert "whole-call policy" in attrs(s) and s.behaviour == "refusal"
    s = P.parse("Why do customers who were refused a refund escalate?")
    assert (s.event, s.question_type, s.filters) == ("ESC", "why", {"with_event": ["REF_DENIED"]})
    assert "two events" in attrs(P.parse("Show me examples of escalations and refunds"))


def test_product_questions_and_behaviour_labels():
    for q in ("Which product or service problems lead to refund requests?",
              "What do customers complain about before they ask for a supervisor?",
              "What should the product team fix to reduce churn threats?"):
        assert P.parse(q).question_type == "issues", q
    s = P.parse("Are unresolved-issue complaints linked to churn threats?")
    assert s.question_type == "effect_of" and s.behaviour == "issue_persistence"


def test_existing_comparisons_are_unchanged_and_unclear_ones_ask():
    assert P.parse("Compare escalations and refunds").compare == {"dimension": "event", "values": ["ESC", "REF"]}
    assert P.parse("How often do escalations and refunds happen?").question_type == "compare"
    assert P.parse("Compare escalation rates between airline and telecom calls").compare == \
        {"dimension": "industry", "values": ["airline", "telecom"]}
    s = P.parse("Compare escalations in hotel calls")
    assert s.compare is None and "which groups to compare" in s.ambiguous


def test_notices_pass_the_gates():
    samples = {"call duration": {"text": "how long"}, "audio": {"text": "tone of voice"},
               "unmeasured behaviour": {"text": "sarcasm"},
               "two events": {"text": "escalations and refund episodes", "first": "escalations", "second": "refund episodes"},
               "effects between events": {"text": "escalations and refund episodes"},
               "whole-call policy": {"text": "if agents never refused refunds"},
               "effect-size threshold": {"text": "by more than five percentage points"},
               "rate threshold": {"text": "more than 20%"}, "agent identity": {"text": "which agent"},
               "customer tier": {"text": "premium customers"}, "demographics": {"text": "young"},
               "plan or segment": {"text": "premium plan"}, "account age": {"text": "new customers"},
               "effect modification": {"text": "only when the customer is already frustrated"},
               "no clear effect": {"text": "do not affect"},
               "single-call counterfactual": {"text": "would the customer still"}}
    assert set(samples) == set(UNSUPPORTED_MESSAGES)
    for attr, u in samples.items():
        msg = unsupported_message({"attribute": attr, **u})
        assert "{" not in msg and not gate_numbers(msg, {}) and not gate_causal(msg, [], {}), (attr, msg)
    assert "no customer-tier field" in unsupported_message({"attribute": "customer tier", "text": "vip"})


def test_followup_after_a_multi_event_answer_keeps_one_event():
    prev = P.parse("Do the behaviours that raise escalations also raise churn threats?")
    d = propose_delta(prev, "what about refunds?", P)
    new = merge(prev, d, "what about refunds?")
    assert new.event == "REF" and new.compare is None and new.question_type == "why"
    prev = P.parse("Which industry has the most refund requests?")
    d = propose_delta(prev, "why in hotel calls?", P)
    new = merge(prev, d, "why in hotel calls?")
    assert (new.event, new.question_type, new.filters, new.compare) == ("REF", "why", {"industry": ["hospitality"]}, None)


def test_diversity_measures():
    items = [{"id": "q1", "category": "why", "task": "task1", "difficulty": "medium", "query_type": "multi_hop",
              "use_case": "root_cause", "question": "Why do customers escalate?", "expected": {"event": "ESC"}},
             {"id": "q2", "category": "how_often", "task": "task1", "difficulty": "easy", "query_type": "simple_retrieval",
              "use_case": "monitoring", "question": "How often do refunds happen?", "expected": {"event": "REF"}},
             {"id": "s1", "category": "session", "task": "task2", "difficulty": "medium", "query_type": "follow_up",
              "use_case": "follow_up", "session": [{"question": "Why do customers escalate?",
                                                    "expected": {"event": "ESC", "route": "first", "industry": []}},
                                                   {"question": "what about refunds?",
                                                    "expected": {"event": "REF", "route": "new_lookup", "industry": []}}]}]
    assert [q[0] for q in questions_of(items)] == ["q1", "q2", "s1.1", "s1.2"]
    d = query_diversity(items)
    assert d["n_questions"] == 4 and 0 < d["distinct_1"] <= 1 and 0 < d["distinct_2"] <= 1
    assert d["max_pairwise_rouge_l"] == pytest.approx(1.0)
    assert 0 <= d["mean_pairwise_rouge_l"] < 1 and d["evenness"]["task"] > 0


class FakeJudge:
    available, model = True, "fake-judge"

    def __init__(self):
        self.payloads = []

    def json_call(self, system, user, schema, purpose, effort=None):
        items = json.loads(user)
        self.payloads.append(items)
        return {"ratings": [{"id": it["id"], "realism": 2 if "blow up" in it["question"] else 4, "contextual_fit": 4,
                             "category_ok": True, "comment": "ok"} for it in items] + [
            {"id": "not-a-question", "realism": 1, "contextual_fit": 1, "category_ok": False, "comment": "ignored"}]}


def test_llm_judge_masks_brands_and_summarises():
    items = [{"id": f"q{i}", "category": "why", "question": f"Why do Shopnest customers escalate {i}?", "expected": {}}
             for i in range(30)]
    items.append({"id": "q99", "category": "known_limitation", "question": "What makes callers blow up?", "expected": {}})
    llm = FakeJudge()
    out = judge_queries(llm, items, brands=["ShopNest"], batch=25)
    sent = [it["question"] for p in llm.payloads for it in p]
    assert len(llm.payloads) == 2 and all("shopnest" not in q.lower() for q in sent) and "<brand>" in sent[0]
    s = out["summary"]
    assert s["n_rated"] == 31 and not s["missing"] and s["flagged_for_review"] == ["q99"]
    assert s["realism_mean"] == pytest.approx((30 * 4 + 2) / 31) and s["category_ok_share"] == 1.0


def test_new_answer_kinds_pass_the_gates_and_keep_context(engine):
    for q, kind in [("Which industry has the most refund requests?", "rank"),
                    ("Which product or service problems lead to refund requests?", "topics"),
                    ("Do the behaviours that raise escalations also raise churn threats?", "shared"),
                    ("Do escalations lead to refund requests?", "link"),
                    ("Which industry has the highest escalation rate, and what drives escalations there?", "factor")]:
        ans, _ = engine.ask(q)
        assert not ans["dropped"] and not ans["degraded"], (q, ans["dropped"])
        assert kind in {s["kind"] for s in ans["sentences"]}, (q, ans["text"])
    ans, st = engine.ask("Which event is most common?")
    top = ans["pack"]["rank"]["groups"][0]["value"]
    ans2, st = engine.ask("why?", st)
    assert st.spec["event"] == top and st.spec["question_type"] == "why" and not ans2["degraded"]


def test_new_categories_answered_as_expected(demo):
    m = demo["metrics"]
    for sp in ("dev", "test"):
        cats = m[sp]["by_category"]
        assert "known_limitation" not in cats
        kl = m[sp]["known_limitations"]
        assert kl["n"] >= 1 and all(it["why"] and it["system_did"] for it in kl["items"])
    for cat in ("product_improvement", "ranking", "multi_hop", "out_of_scope", "conditional", "before_after", "threshold",
                "behaviour_profile", "overview", "retention_risk", "single_call", "noisy_text", "multilingual"):
        n = sum(m[sp]["by_category"].get(cat, {}).get("n", 0) for sp in ("dev", "test"))
        ok = sum(m[sp]["by_category"].get(cat, {}).get("n", 0) * m[sp]["by_category"].get(cat, {}).get("share_ok", 0)
                 for sp in ("dev", "test"))
        assert n >= 1 and ok == n, (cat, m["dev"]["by_category"].get(cat), m["test"]["by_category"].get(cat))


def test_readable_outputs_and_review_sheet(demo):
    import pandas as pd
    root = demo["pipe"].ws.root
    items = load_jsonl(root / "queries" / "queries_dev.jsonl") + load_jsonl(root / "queries" / "queries_test.jsonl")
    md = (root / "outputs" / "QUERY_OUTPUTS.md").read_text(encoding="utf-8")
    for q in items:
        assert f"#### {q['id']} " in md, q["id"]
    assert "Task 2: follow-up questions in context" in md and "known_limitation" in md
    n_questions = len(questions_of(items))
    assert len(pd.read_csv(root / "queries" / "queries.csv")) == n_questions
    review = pd.read_csv(root / "queries" / "queries_review.csv")
    assert len(review) == n_questions and {"realistic_1_5", "keep_edit_drop"} <= set(review.columns)
    assert demo["metrics"]["query_set"]["diversity"]["distinct_2"] > 0.3
    assert (root / "library" / "issue_terms.json").is_file()
