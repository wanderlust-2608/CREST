import pytest

from crest.gates import classify_causal, gate_causal, gate_evidence, gate_numbers, run_gates

LEVELS = {"F1": "L3", "F2": "L2", "F3": "L1"}
PH = {"F1.att": "+12.0 percentage points", "F1.ci": "95% CI +5.0 to +19.0 points", "F2.att": "+4.0 percentage points",
      "F2.ci": "95% CI +1.0 to +7.0 points", "D.rate": "18.0%"}
TURNS = {"c1:5": "I'm afraid we cannot make an exception here.", "c1:6": "I want to speak to a supervisor right now."}


@pytest.mark.parametrize("sentence", [
    "Escalations happened in 18% of calls.",
    "About half of the calls escalated.",
    "Refusals raise escalations by {F9.att} [F9].",
])
def test_gate1_numbers_caught(sentence):
    assert gate_numbers(sentence, PH)


@pytest.mark.parametrize("sentence", [
    "Policy refusals cause escalations [F1].",
    "Refusals lead to escalations.",
    "The reason for escalations is policy refusals [F1].",
    "That is why customers escalate after refusals [F1].",
    "Refusals are estimated to raise the chance of an escalation [F2].",
    "Holds are associated with a higher chance of an escalation [F3].",
    "Holds often precede escalations.",
])
def test_gate2_causal_licensing_caught(sentence):
    assert gate_causal(sentence, [], LEVELS)


@pytest.mark.parametrize("sentence", [
    "Under the stated assumptions, policy refusals are estimated to raise the chance of an escalation by {F1.att} [F1].",
    "Policy refusals are associated with a higher chance of an escalation ({F2.att}, {F2.ci}) [F2].",
    "The data does not show that apologies raise the chance of a refund [F2].",
    "In calls with holds, no escalation followed in most cases [F3].",
    "There was an increase in hold music complaints.",
    "Escalations happened in {D.rate} of calls.",
])
def test_licensed_sentences_pass(sentence):
    assert not gate_causal(sentence, [], LEVELS)
    assert not gate_numbers(sentence, PH)


def test_gate3_quotes():
    assert not gate_evidence("we cannot make an exception", ["c1:5"], TURNS)
    assert gate_evidence("we will refund you in full", ["c1:5"], TURNS)
    assert gate_evidence("no escalation occurred", ["note:1"], TURNS)
    assert gate_evidence("I want to speak to a supervisor", [], TURNS)
    assert not gate_evidence("i want to speak to a supervisor right now", ["c1:6"], TURNS)


def test_classifier_categories():
    assert classify_causal("X is estimated to lower the chance of Y") == "conditional_causal"
    assert classify_causal("X may lead to Y") == "conditional_causal"
    assert classify_causal("X lowers Y") == "direct_causal"
    assert classify_causal("X has a lower chance of Y") == "correlational"
    assert classify_causal("X is not associated with Y") == "none"
    assert classify_causal("an increase in X") == "correlational"


def test_run_gates_marks_failures():
    sents = [{"text": "Policy refusals cause escalations [F1].", "kind": "factor", "factor_ids": ["F1"], "turn_uids": []},
             {"text": "“we cannot make an exception” [c1:5]", "kind": "quote", "factor_ids": [], "turn_uids": ["c1:5"],
              "quote": "we cannot make an exception"}]
    out = run_gates(sents, PH, LEVELS, TURNS)
    assert not out[0]["passed"] and out[1]["passed"]


def test_template_answers_always_pass_the_gates(engine):
    qs = ["Why do customers escalate?", "How can we reduce refunds?", "Why does empathy cause churn?",
          "Show me examples of policy refusals before escalations", "How often do customers ask for refunds?",
          "Compare churn threats between hotel and airline calls", "Is empathy linked to escalations?"]
    for q in qs:
        ans, _ = engine.ask(q)
        assert not ans["dropped"], (q, [d["gates"] for d in ans["dropped"]])
        assert not ans["degraded"], q


def test_fixed_reason_texts_pass_the_numbers_gate():
    from crest.answer import PLAIN_REASON
    for check, text in PLAIN_REASON.items():
        assert gate_numbers(f"Not a confirmed effect: {text} [F1].", {}) == [], check
