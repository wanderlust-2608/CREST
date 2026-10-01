from types import SimpleNamespace

import pytest

from crest.answer import LLM_ANSWER_SCHEMA
from crest.behaviours import PROPOSAL_SCHEMA
from crest.config import Settings
from crest.events import LLM_EVENT_SCHEMA
from crest.llm import (ClaudeLLM, LLMOutputError, LLMRefusal, NoLLM, LLMUnavailable, check_schema_is_strict, make_llm,
                       validate_schema)
from crest.query import LLM_SPEC_SCHEMA
from crest.session import LLM_DELTA_SCHEMA

SCHEMA = {"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"], "additionalProperties": False}


class FakeMessages:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)
        stop, text = self.replies.pop(0)
        return SimpleNamespace(stop_reason=stop, content=[SimpleNamespace(type="text", text=text)], model=kw["model"],
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5), stop_details=None, _request_id="req_1")


def fake_client(replies):
    m = FakeMessages(replies)
    return SimpleNamespace(messages=m, beta=SimpleNamespace(messages=m)), m


def test_request_shape_and_cache(tmp_path):
    client, m = fake_client([("end_turn", '{"x": 3}')])
    llm = ClaudeLLM(Settings().llm, tmp_path, client=client)
    assert llm.json_call("sys", "user", SCHEMA, "t") == {"x": 3}
    kw = m.calls[0]
    assert kw["model"] == "claude-opus-5-5" and kw["max_tokens"] == 16000 and kw["system"] == "sys"
    assert kw["messages"] == [{"role": "user", "content": "user"}]
    assert kw["output_config"] == {"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}}
    assert kw["betas"] == ["server-side-fallback-2026-07-01"] and kw["fallbacks"] == "default"
    assert "temperature" not in kw and "thinking" not in kw
    assert llm.json_call("sys", "user", SCHEMA, "t") == {"x": 3}
    assert len(m.calls) == 1
    assert (tmp_path / "calls.jsonl").is_file()


def test_refusal_and_truncation_and_bad_output(tmp_path):
    client, _ = fake_client([("refusal", "")])
    with pytest.raises(LLMRefusal):
        ClaudeLLM(Settings().llm, tmp_path / "a", client=client).json_call("s", "u", SCHEMA, "t")
    client, m = fake_client([("max_tokens", '{"x"'), ("max_tokens", '{"x"')])
    with pytest.raises(LLMOutputError):
        ClaudeLLM(Settings().llm, tmp_path / "b", client=client).json_call("s", "u", SCHEMA, "t")
    assert m.calls[1]["max_tokens"] == 32000
    client, _ = fake_client([("end_turn", "not json")])
    with pytest.raises(LLMOutputError):
        ClaudeLLM(Settings().llm, tmp_path / "c", client=client).json_call("s", "u", SCHEMA, "t")
    client, _ = fake_client([("end_turn", '{"x": "three"}')])
    with pytest.raises(LLMOutputError):
        ClaudeLLM(Settings().llm, tmp_path / "d", client=client).json_call("s", "u", SCHEMA, "t")


def test_no_llm_by_default(tmp_path):
    s = Settings()
    assert isinstance(make_llm(s, tmp_path), NoLLM)
    with pytest.raises(LLMUnavailable):
        NoLLM().json_call("s", "u", SCHEMA, "t")


@pytest.mark.parametrize("schema", [LLM_EVENT_SCHEMA, PROPOSAL_SCHEMA, LLM_SPEC_SCHEMA, LLM_DELTA_SCHEMA, LLM_ANSWER_SCHEMA])
def test_every_output_schema_is_strict(schema):
    assert check_schema_is_strict(schema) == []


def test_validator():
    assert validate_schema({"x": 1}, SCHEMA) == []
    assert validate_schema({"x": 1, "y": 2}, SCHEMA)
    assert validate_schema({}, SCHEMA)
    assert validate_schema({"x": True}, SCHEMA)


def test_installed_sdk_accepts_the_request_shape():
    pytest.importorskip("anthropic")
    import inspect
    from anthropic.resources.beta.messages import Messages as Beta
    from anthropic.resources.messages import Messages
    p = inspect.signature(Beta.create).parameters
    assert {"betas", "fallbacks", "output_config", "system", "messages", "max_tokens", "model"} <= set(p)
    assert "output_config" in inspect.signature(Messages.create).parameters
