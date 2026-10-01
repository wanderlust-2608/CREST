from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

PROMPT_VERSION = "crest-prompts-v2"
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class LLMUnavailable(RuntimeError):
    pass


class LLMRefusal(RuntimeError):
    pass


class LLMOutputError(RuntimeError):
    pass


_TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def validate_schema(obj, schema: dict, path: str = "$") -> list[str]:
    problems: list[str] = []
    t = schema.get("type")
    if t is not None:
        types = t if isinstance(t, list) else [t]
        ok = False
        for ty in types:
            if ty == "integer":
                ok |= isinstance(obj, int) and not isinstance(obj, bool)
            elif ty == "number":
                ok |= isinstance(obj, (int, float)) and not isinstance(obj, bool)
            else:
                ok |= isinstance(obj, _TYPES.get(ty, object))
        if not ok:
            return [f"{path}: expected {t}, got {type(obj).__name__}"]
    if "enum" in schema and obj not in schema["enum"]:
        problems.append(f"{path}: {obj!r} not in {schema['enum']}")
    if isinstance(obj, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in obj:
                problems.append(f"{path}: missing '{req}'")
        if schema.get("additionalProperties") is False:
            extra = set(obj) - set(props)
            if extra:
                problems.append(f"{path}: unexpected keys {sorted(extra)}")
        for k, v in obj.items():
            if k in props:
                problems += validate_schema(v, props[k], f"{path}.{k}")
    if isinstance(obj, list) and "items" in schema:
        for i, v in enumerate(obj):
            problems += validate_schema(v, schema["items"], f"{path}[{i}]")
    return problems


def check_schema_is_strict(schema: dict, path: str = "$") -> list[str]:
    problems = []
    if schema.get("type") == "object":
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is not False:
            problems.append(f"{path}: additionalProperties must be false")
        missing = set(props) - set(schema.get("required", []))
        if missing:
            problems.append(f"{path}: properties not required: {sorted(missing)}")
        for k, v in props.items():
            problems += check_schema_is_strict(v, f"{path}.{k}")
    if schema.get("type") == "array" and "items" in schema:
        problems += check_schema_is_strict(schema["items"], f"{path}[]")
    return problems


class NoLLM:
    available = False
    name = "none"

    def json_call(self, system: str, user: str, schema: dict, purpose: str, effort: str | None = None) -> dict:
        raise LLMUnavailable("no LLM backend configured (llm.backend = 'none'); the deterministic path is used instead")


class ClaudeLLM:
    available = True
    name = "anthropic"

    def __init__(self, llm_settings, cache_dir: str | Path, client=None, use_fallbacks: bool = True):
        self.model = llm_settings.model
        self.effort = llm_settings.effort
        self.max_tokens = int(llm_settings.max_tokens)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.cache_dir / "calls.jsonl"
        self.use_fallbacks = use_fallbacks
        if client is None:
            try:
                import anthropic
            except ImportError as exc:
                raise LLMUnavailable("the 'anthropic' package is not installed (pip install anthropic)") from exc
            try:
                client = anthropic.Anthropic(timeout=600.0, max_retries=3)
            except Exception as exc:
                raise LLMUnavailable(f"could not create the Anthropic client: {exc}") from exc
        self.client = client

    def cache_key(self, system: str, user: str, schema: dict, effort: str) -> str:
        blob = json.dumps({"model": self.model, "effort": effort, "max_tokens": self.max_tokens, "system": system,
                           "user": user, "schema": schema, "prompt_version": PROMPT_VERSION}, sort_keys=True)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _request(self, system: str, user: str, schema: dict, effort: str, max_tokens: int):
        kwargs = dict(model=self.model, max_tokens=max_tokens, system=system,
                      messages=[{"role": "user", "content": user}],
                      output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}})
        if self.use_fallbacks:
            try:
                return self.client.beta.messages.create(betas=[FALLBACK_BETA], fallbacks="default", **kwargs)
            except Exception as exc:
                if "fallback" not in str(exc).lower() and type(exc).__name__ not in ("TypeError", "BadRequestError"):
                    raise
                self.use_fallbacks = False
        return self.client.messages.create(**kwargs)

    def json_call(self, system: str, user: str, schema: dict, purpose: str, effort: str | None = None) -> dict:
        effort = effort or self.effort
        key = self.cache_key(system, user, schema, effort)
        path = self.cache_dir / f"{key}.json"
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))["data"]
        started = time.time()
        max_tokens = self.max_tokens
        for attempt in range(2):
            resp = self._request(system, user, schema, effort, max_tokens)
            stop = getattr(resp, "stop_reason", None)
            if stop == "refusal":
                det = getattr(resp, "stop_details", None)
                why = f"{getattr(det, 'category', None)}: {getattr(det, 'explanation', None)}" if det else "no details"
                self._log(purpose, key, resp, started, error=f"refusal ({why})")
                raise LLMRefusal(f"the model declined the '{purpose}' request ({why})")
            if stop == "max_tokens":
                if attempt == 0 and max_tokens < 32000:
                    max_tokens = min(32000, max_tokens * 2)
                    continue
                self._log(purpose, key, resp, started, error="max_tokens")
                raise LLMOutputError(f"the '{purpose}' reply was cut off at max_tokens={max_tokens}")
            break
        text = next((b.text for b in resp.content if getattr(b, "type", None) == "text"), None)
        if text is None:
            self._log(purpose, key, resp, started, error="no text block")
            raise LLMOutputError(f"the '{purpose}' reply has no text block")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            self._log(purpose, key, resp, started, error="invalid JSON")
            raise LLMOutputError(f"the '{purpose}' reply is not valid JSON: {exc}") from exc
        problems = validate_schema(data, schema)
        if problems:
            self._log(purpose, key, resp, started, error="schema: " + "; ".join(problems[:5]))
            raise LLMOutputError(f"the '{purpose}' reply does not match its schema: {problems[:5]}")
        path.write_text(json.dumps({"data": data, "model": getattr(resp, "model", self.model), "purpose": purpose,
                                    "request_id": getattr(resp, "_request_id", None), "effort": effort,
                                    "created_utc": datetime.now(timezone.utc).isoformat()}, indent=1), encoding="utf-8")
        self._log(purpose, key, resp, started)
        return data

    def _log(self, purpose, key, resp, started, error=None):
        usage = getattr(resp, "usage", None)
        rec = {"utc": datetime.now(timezone.utc).isoformat(), "purpose": purpose, "key": key,
               "model": getattr(resp, "model", self.model), "stop_reason": getattr(resp, "stop_reason", None),
               "request_id": getattr(resp, "_request_id", None), "seconds": round(time.time() - started, 2),
               "input_tokens": getattr(usage, "input_tokens", None), "output_tokens": getattr(usage, "output_tokens", None),
               "error": error}
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")


def make_llm(settings, out_dir: str | Path, client=None):
    if settings.llm.backend == "none":
        return NoLLM()
    try:
        return ClaudeLLM(settings.llm, Path(out_dir) / "llm_cache", client=client)
    except LLMUnavailable as exc:
        nl = NoLLM()
        nl.reason = str(exc)
        return nl
