import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crest.answer import write_answer
from crest.churn import DISENGAGE_RE
from crest.gates import run_gates
from crest.query import QueryParser, QuerySpec, llm_parse
from crest.session import merge, propose_delta


class FakeLLM:
    def json_call(self, **kwargs):
        return {
            "event": "ESC",
            "question_type": "counterevidence",
            "industry": [],
            "behaviour": "none",
            "presupposition_behaviour": "none",
            "presupposition_direction": 0,
            "leading": False,
        }


def parser():
    return QueryParser((), (), (), None, False, account={}, has_tenure=False, call_ids=set())


def test_causal_failure_is_cross_event_and_not_ambiguous():
    p = parser()
    for q in (
        "Which apparent explanations are not supported by the causal checks?",
        "Which factors were not supported as causal explanations?",
        "What conclusions should not be interpreted causally?",
        "Which observed behaviours have no clear causal evidence?",
    ):
        spec = p.parse(q)
        assert spec.event is None, q
        assert spec.question_type == "causal_failure", q
        assert not spec.ambiguous, q


def test_generic_event_does_not_inherit_previous_event():
    p = parser()
    prev = p.parse("Why do customers threaten to cancel?")
    text = "Are there behaviours that occur frequently before an event but do not meaningfully distinguish event from non-event calls?"
    delta = propose_delta(prev, text, p)
    new = merge(prev, delta, text)
    assert new.event is None
    assert new.question_type == "counterevidence"


def test_llm_cannot_invent_event_for_generic_event_question():
    p = parser()
    text = "Are there behaviours that occur frequently before an event but do not meaningfully distinguish event from non-event calls?"
    rules = p.parse(text)
    out = llm_parse(FakeLLM(), text, rules)
    assert out.event is None
    assert out.question_type == "counterevidence"


def test_complaint_is_not_silently_mapped_to_supported_event():
    spec = parser().parse("What tends to precede a complaint?")
    assert spec.event is None
    assert "Complaint is not a separately labelled business event" in spec.ambiguous


def test_implicit_disengagement_phrase_is_recognized():
    assert DISENGAGE_RE.search("i'm done with you people")
    assert DISENGAGE_RE.search("i'll take my business elsewhere")
    assert DISENGAGE_RE.search("you've lost me")


def test_causal_failure_answer_passes_gates():
    pack = {
        "causal_evidence": {"events": [{
            "event": "REF",
            "name": "refund episode",
            "plural": "refund episodes",
            "negative_control_flagged": False,
            "event_f1": 0.89,
            "factors": [{
                "id": "F5",
                "short": "customer frustration",
                "label": "customer frustration",
                "ci_low": -0.039,
                "ci_high": 0.121,
                "att": 0.041,
                "p_treated": 0.20,
                "reasons": ["negative-control check failed"],
            }],
        }]},
        "placeholders": {
            "F5.att": "+4.1 percentage points",
            "F5.ci": "95% CI -3.9 to +12.1 points",
            "REF.f1": "0.89",
        },
        "notices": [],
    }
    spec = QuerySpec(question_type="causal_failure")
    sentences = write_answer(pack, spec)
    checked = run_gates(sentences, pack["placeholders"], {"F5": "L2"}, {})
    assert all(row["passed"] for row in checked), [row for row in checked if not row["passed"]]


def test_causal_failure_followup_does_not_inherit_previous_event():
    p = parser()
    prev = p.parse("Why do customers threaten to cancel?")
    for q in (
        "Which factors were not supported as causal explanations?",
        "What conclusions should not be interpreted causally?",
        "Which observed behaviours have no clear causal evidence?",
    ):
        delta = propose_delta(prev, q, p)
        new = merge(prev, delta, q)
        assert new.event is None, (q, new.event, delta)
        assert new.question_type == "causal_failure", (q, new.question_type)
