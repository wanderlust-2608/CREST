from __future__ import annotations

import re

from .definitions import (CATEGORY_RANK, CORRELATIONAL_RE, DIRECT_CAUSAL_RE, HEDGE_RE, MAX_CATEGORY_FOR_LEVEL,
                          NEGATION_RE, NOUN_CONTEXT)
from .query import find_behaviours, find_events

PLACEHOLDER_RE = re.compile(r"\{([A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+)\}")
FACTOR_TAG_RE = re.compile(r"\[(F\d+)\]")
CITATION_RE = re.compile(r"\[([0-9A-Za-z_\-]+:\d+)\]")
QUOTE_RE = re.compile(r"[\"“]([^\"”]{3,})[\"”]")
WORD_RE = re.compile(r"[a-z0-9']+")
_STOP = set("""a an the and or but if so to of in on at for from with by is are was were be been this that these those it
its their there here as not no do does did have has had can could may might would will than then them they we you he she
i me my our your his her which who whom what when where why how all any each more most less least very also only just
about after before during into over under again further once calls call agent customer customers agents""".split())


def normalize_quote(text: str) -> str:
    t = str(text).lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"[^a-z0-9' ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def gate_numbers(text: str, placeholders: dict) -> list[str]:
    problems = []
    for key in PLACEHOLDER_RE.findall(text):
        if key not in placeholders:
            problems.append(f"unknown placeholder {{{key}}}")
    stripped = PLACEHOLDER_RE.sub(" ", text)
    stripped = QUOTE_RE.sub(" ", stripped)
    stripped = CITATION_RE.sub(" ", stripped)
    stripped = FACTOR_TAG_RE.sub(" ", stripped)
    stripped = re.sub(r"\bF\d+\b", " ", stripped)
    digits = re.findall(r"\d+(?:[.,]\d+)?%?", stripped)
    if digits:
        problems.append(f"number typed outside a placeholder: {digits[:3]}")
    for w in ("percent", "per cent", "half of", "a third of", "a quarter of", "twice", "double", "triple"):
        if re.search(r"\b" + w + r"\b", stripped.lower()):
            problems.append(f"quantity in words outside a placeholder: '{w}'")
    return problems


def classify_causal(sentence: str) -> str:
    s = sentence.lower()
    s = PLACEHOLDER_RE.sub(" X ", s)
    s = QUOTE_RE.sub(" ", s)
    best = "none"
    for m in DIRECT_CAUSAL_RE.finditer(s):
        before = WORD_RE.findall(s[:m.start()])
        prev2 = before[-2:]
        if prev2 and (prev2[-1] in NOUN_CONTEXT or (len(prev2) == 2 and prev2[0] in NOUN_CONTEXT and prev2[1] not in
                                                    ("to", "will", "would", "can", "could", "may", "might", "does", "do"))):
            continue
        window = " ".join(before[-6:])
        if NEGATION_RE.search(window):
            continue
        hedged = bool(HEDGE_RE.search(s[:m.end()]))
        cat = "conditional_causal" if hedged else "direct_causal"
        if CATEGORY_RANK[cat] > CATEGORY_RANK[best]:
            best = cat
    if best == "none":
        for m in CORRELATIONAL_RE.finditer(s):
            window = " ".join(WORD_RE.findall(s[:m.start()])[-4:])
            if NEGATION_RE.search(window):
                continue
            best = "correlational"
            break
    return best


def links_behaviour_to_event(sentence: str) -> bool:
    return bool(find_behaviours(sentence)) and bool(find_events(sentence))


def gate_causal(sentence: str, factor_ids: list, levels: dict) -> list[str]:
    problems = []
    cat = classify_causal(sentence)
    if cat == "direct_causal":
        problems.append("direct causal wording is never allowed")
    ids = [f for f in factor_ids if f in levels]
    ids += [f for f in FACTOR_TAG_RE.findall(sentence) if f in levels and f not in ids]
    ids += [k.split(".")[0] for k in PLACEHOLDER_RE.findall(sentence) if k.split(".")[0] in levels and k.split(".")[0] not in ids]
    if links_behaviour_to_event(sentence) and cat != "none" and not ids:
        problems.append("a sentence linking a behaviour to an event must cite a factor")
    if ids and cat != "direct_causal":
        allowed = min((MAX_CATEGORY_FOR_LEVEL.get(levels[f], "none") for f in ids), key=lambda c: CATEGORY_RANK[c])
        if CATEGORY_RANK[cat] > CATEGORY_RANK[allowed]:
            problems.append(f"wording is {cat.replace('_', ' ')} but the cited factor allows at most {allowed.replace('_', ' ')}")
    return problems


def gate_evidence(quote: str | None, turn_uids: list, turn_text: dict, sentence: str | None = None,
                  support_threshold: float = 0.5) -> list[str]:
    problems = []
    missing = [u for u in turn_uids if u not in turn_text]
    if missing:
        problems.append(f"cited turn(s) not found in the raw dialogue: {missing[:3]}")
    if quote is not None:
        if not turn_uids:
            problems.append("a quote must cite the turn it comes from")
        else:
            q = normalize_quote(quote)
            if not q or not any(q in normalize_quote(turn_text.get(u, "")) for u in turn_uids):
                problems.append("the quote is not an exact substring of the cited turn")
    elif sentence is not None and turn_uids and not missing:
        score = lexical_support(sentence, [turn_text[u] for u in turn_uids])
        if score < support_threshold:
            problems.append(f"the cited turns do not support the sentence (support {score:.2f})")
    return problems


def lexical_support(sentence: str, texts: list[str]) -> float:
    words = [w for w in WORD_RE.findall(PLACEHOLDER_RE.sub(" ", sentence.lower())) if w not in _STOP and len(w) > 2]
    if not words:
        return 1.0
    have = set(WORD_RE.findall(" ".join(texts).lower()))
    return sum(w in have for w in words) / len(words)


def run_gates(sentences: list[dict], placeholders: dict, levels: dict, turn_text: dict) -> list[dict]:
    out = []
    for s in sentences:
        g1 = gate_numbers(s["text"], placeholders)
        g2 = gate_causal(s["text"], s.get("factor_ids", []), levels)
        needs_support = s.get("kind") in ("example_claim",)
        g3 = gate_evidence(s.get("quote"), s.get("turn_uids", []), turn_text,
                           s["text"] if needs_support else None) if (s.get("quote") is not None or s.get("turn_uids")) else []
        out.append({**s, "gates": {"numbers": g1, "causal": g2, "evidence": g3}, "passed": not (g1 or g2 or g3)})
    return out
