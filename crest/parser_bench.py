from __future__ import annotations

import json
import math

import numpy as np

from .query import QueryParser


def _q(cat, lang, text, event, qt=None, industry=None, with_event=None, behaviour=None):
    return {"category": cat, "language": lang, "question": text,
            "expected": {k: v for k, v in {"event": event, "question_type": qt, "industry": industry,
                                           "with_event": with_event, "behaviour": behaviour}.items() if v is not None}}


CLEAN_DEV = [
    _q("clean", "en", "Why do customers escalate?", "ESC", "why"),
    _q("clean", "en", "Why do customers ask for refunds?", "REF", "why"),
    _q("clean", "en", "Why do customers threaten to cancel?", "CHURN", "why"),
    _q("clean", "en", "How often do customers escalate in hotel calls?", "ESC", "how_often", ["hospitality"]),
    _q("clean", "en", "How often do customers ask for refunds in airline calls?", "REF", "how_often", ["airline"]),
    _q("clean", "en", "Show me examples of churn threats", "CHURN", "examples"),
    _q("clean", "en", "How can we reduce escalations?", "ESC", "what_to_change"),
    _q("clean", "en", "Is customer frustration linked to escalations?", "ESC", "effect_of", behaviour="negative_emotion"),
    _q("clean", "en", "Are agent apologies linked to refund requests?", "REF", "effect_of", behaviour="apology"),
    _q("clean", "en", "Why do customers escalate in insurance calls?", "ESC", "why", ["insurance"]),
    _q("clean", "en", "Why do customers who were refused a refund escalate?", "ESC", "why", with_event=["REF_DENIED"]),
    _q("clean", "en", "Do escalations lead to refund requests?", "ESC", "event_link"),
]
CLEAN_TEST = [
    _q("clean", "en", "What drives churn threats in banking calls?", "CHURN", "why", ["banking"]),
    _q("clean", "en", "Why do refunds happen in telecom calls?", "REF", "why", ["telecom"]),
    _q("clean", "en", "Are policy refusals linked to churn threats?", "CHURN", "effect_of", behaviour="refusal"),
    _q("clean", "en", "How often do customers who escalate threaten to leave?", "CHURN", "how_often", with_event=["ESC"]),
    _q("clean", "en", "Which industry has the most churn threats?", "CHURN", "compare"),
    _q("clean", "en", "How have refund requests changed over time?", "REF", "trend"),
    _q("clean", "en", "Give me examples of customers asking for a supervisor", "ESC", "examples"),
    _q("clean", "en", "What can agents do to prevent refund requests?", "REF", "what_to_change"),
    _q("clean", "en", "Why do customers escalate in retail calls?", "ESC", "why", ["retail_ecommerce"]),
    _q("clean", "en", "Do refund requests happen more in calls with escalations?", "REF", None, with_event=["ESC"]),
]
MULTI_DEV = [
    _q("multilingual", "es", "¿Por qué escalan los clientes?", "ESC", "why"),
    _q("multilingual", "es", "¿Por qué los clientes piden reembolsos?", "REF", "why"),
    _q("multilingual", "es", "¿Con qué frecuencia escalan los clientes en llamadas de hoteles?", "ESC", "how_often", ["hospitality"]),
    _q("multilingual", "es", "¿Cómo podemos reducir las escalaciones?", "ESC", "what_to_change"),
    _q("multilingual", "fr", "Pourquoi les clients demandent-ils un remboursement ?", "REF", "why"),
    _q("multilingual", "fr", "Pourquoi les clients menacent-ils de résilier ?", "CHURN", "why"),
    _q("multilingual", "fr", "Comment pouvons-nous réduire les escalades ?", "ESC", "what_to_change"),
    _q("multilingual", "de", "Warum verlangen Kunden eine Rückerstattung?", "REF", "why"),
    _q("multilingual", "de", "Wie oft verlangen Kunden in Hotelanrufen einen Vorgesetzten?", "ESC", "how_often", ["hospitality"]),
    _q("multilingual", "de", "Wie können wir Eskalationen reduzieren?", "ESC", "what_to_change"),
    _q("multilingual", "pt", "Por que os clientes pedem reembolso?", "REF", "why"),
    _q("multilingual", "pt", "Por que os clientes ameaçam cancelar?", "CHURN", "why"),
    _q("multilingual", "it", "Perché i clienti chiedono un rimborso?", "REF", "why"),
    _q("multilingual", "it", "Come possiamo ridurre le escalation?", "ESC", "what_to_change"),
    _q("multilingual", "hi-latn", "customers refund kyun maangte hain?", "REF", "why"),
    _q("multilingual", "hi-latn", "hotel calls me customers kitni baar escalate karte hain?", "ESC", "how_often", ["hospitality"]),
    _q("multilingual", "hi", "ग्राहक रिफंड क्यों मांगते हैं?", "REF", "why"),
    _q("multilingual", "hi", "ग्राहक कैंसिल करने की धमकी क्यों देते हैं?", "CHURN", "why"),
    _q("multilingual", "es", "¿Por qué los clientes amenazan con irse?", "CHURN", "why"),
    _q("multilingual", "fr", "Pourquoi les clients menacent-ils de partir ?", "CHURN", "why"),
    _q("multilingual", "de", "Warum drohen Kunden zu gehen?", "CHURN", "why"),
    _q("multilingual", "it", "Perché i clienti minacciano di andarsene?", "CHURN", "why"),
    _q("multilingual", "hi-latn", "customers chhodne ki dhamki kyun dete hain?", "CHURN", "why"),
]
MULTI_TEST = [
    _q("multilingual", "es", "¿Por qué los clientes amenazan con cancelar en las aerolíneas?", "CHURN", "why", ["airline"]),
    _q("multilingual", "es", "Muéstrame ejemplos de clientes que piden un supervisor", "ESC", "examples"),
    _q("multilingual", "fr", "À quelle fréquence les clients demandent-ils un superviseur dans les appels d'hôtels ?", "ESC", "how_often", ["hospitality"]),
    _q("multilingual", "fr", "La frustration des clients est-elle liée aux escalades ?", "ESC", "effect_of", behaviour="negative_emotion"),
    _q("multilingual", "de", "Warum drohen Kunden mit Kündigung?", "CHURN", "why"),
    _q("multilingual", "de", "Warum verlangen Kunden bei Versicherungsanrufen einen Vorgesetzten?", "ESC", "why", ["insurance"]),
    _q("multilingual", "pt", "Com que frequência os clientes pedem um supervisor em chamadas de hotel?", "ESC", "how_often", ["hospitality"]),
    _q("multilingual", "pt", "A frustração dos clientes está ligada às escalações?", "ESC", "effect_of", behaviour="negative_emotion"),
    _q("multilingual", "it", "Perché i clienti minacciano di disdire?", "CHURN", "why"),
    _q("multilingual", "it", "La frustrazione dei clienti è collegata alle escalation?", "ESC", "effect_of", behaviour="negative_emotion"),
    _q("multilingual", "hi-latn", "insurance calls me customers escalate kyun karte hain?", "ESC", "why", ["insurance"]),
    _q("multilingual", "hi-latn", "escalations kaise kam kar sakte hain?", "ESC", "what_to_change"),
    _q("multilingual", "hi", "बीमा कॉल में ग्राहक एस्केलेशन क्यों करते हैं?", "ESC", "why", ["insurance"]),
    _q("multilingual", "hi", "एस्केलेशन कैसे कम करें?", "ESC", "what_to_change"),
]
SLANG_DEV = [
    _q("slang", "en", "What makes customers lose it and ask for the boss?", "ESC", "why"),
    _q("slang", "en", "Why do callers jump ship?", "CHURN", "why"),
    _q("slang", "en", "How often do people want their cash back?", "REF", "how_often"),
    _q("slang", "en", "Why do customers go over the agent's head?", "ESC", "why"),
    _q("slang", "en", "What makes guests take their business elsewhere?", "CHURN", "why"),
]
SLANG_TEST = [
    _q("slang", "en", "Why do customers demand someone in charge in hotel calls?", "ESC", "why", ["hospitality"]),
    _q("slang", "en", "How often do customers walk away in telecom calls?", "CHURN", "how_often", ["telecom"]),
    _q("slang", "en", "How can we stop customers ditching us?", "CHURN", "what_to_change"),
    _q("slang", "en", "Why do callers go ballistic and ask for their money back?", "REF", "why"),
    _q("slang", "en", "What makes people blow up before they ask for a manager?", "ESC", "why"),
]
KEYBOARD = {c: n for row in ("qwertyuiop", "asdfghjkl", "zxcvbnm") for i, c in enumerate(row)
            for n in [row[max(0, i - 1):i] + row[i + 1:i + 2]]}


def misspell(text: str, rng: np.random.Generator, n_edits: int = 2) -> str:
    words = text.split(" ")
    idx = [i for i, w in enumerate(words) if len(w.strip("?,.")) >= 6]
    for i in rng.choice(idx, size=min(n_edits, len(idx)), replace=False) if idx else []:
        w = words[i]
        core = w.rstrip("?,.")
        tail = w[len(core):]
        j = int(rng.integers(1, len(core) - 1))
        kind = int(rng.integers(0, 4))
        if kind == 0:
            core = core[:j] + core[j + 1:]
        elif kind == 1:
            core = core[:j] + core[j + 1] + core[j] + core[j + 2:]
        elif kind == 2:
            near = KEYBOARD.get(core[j].lower(), "e")
            core = core[:j] + (near[int(rng.integers(0, len(near)))] if near else "e") + core[j + 1:]
        else:
            core = core[:j] + core[j] + core[j:]
        words[i] = core + tail
    return " ".join(words)


def noisy(items: list[dict], seed: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    return [{**q, "category": "misspelled", "question": misspell(q["question"], rng)} for q in items]


def bench(split: str) -> list[dict]:
    if split == "dev":
        items = CLEAN_DEV + noisy(CLEAN_DEV, 1) + MULTI_DEV + SLANG_DEV
    else:
        items = CLEAN_TEST + noisy(CLEAN_TEST, 2) + noisy(CLEAN_DEV, 3) + MULTI_TEST + SLANG_TEST
    return [{"id": f"{split}{i + 1:03d}", "split": split, **q} for i, q in enumerate(items)]


def _wilson(k: int, n: int) -> list[float]:
    if not n:
        return [float("nan"), float("nan")]
    z, p = 1.96, k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, c - h), min(1.0, c + h)]


def score(spec, ex: dict) -> dict:
    out = {"event": spec.event == ex["event"]}
    if "question_type" in ex:
        out["question_type"] = spec.question_type == ex["question_type"]
    if "industry" in ex:
        out["industry"] = sorted(spec.filters.get("industry") or []) == sorted(ex["industry"])
    if "with_event" in ex:
        out["with_event"] = (spec.filters.get("with_event") or []) == ex["with_event"]
    if "behaviour" in ex:
        out["behaviour"] = spec.behaviour == ex["behaviour"]
    out["all"] = all(out.values())
    return out


def run_bench(parser: QueryParser | None = None, split: str = "test", reader=None) -> dict:
    parser = parser or QueryParser(year_hint=2025)
    read = reader or parser.parse
    rows = []
    for q in bench(split):
        spec = read(q["question"])
        rows.append({**q, "got": {"event": spec.event, "question_type": spec.question_type,
                                   "industry": spec.filters.get("industry"), "with_event": spec.filters.get("with_event"),
                                   "behaviour": spec.behaviour}, "score": score(spec, q["expected"])})
    res = {"split": split, "n": len(rows), "by_category": {}}
    for cat in sorted({r["category"] for r in rows}):
        rs = [r for r in rows if r["category"] == cat]
        k = sum(r["score"]["all"] for r in rs)
        ke = sum(r["score"]["event"] for r in rs)
        res["by_category"][cat] = {"n": len(rs), "all_slots": k / len(rs), "all_slots_ci": _wilson(k, len(rs)),
                                   "event": ke / len(rs), "event_ci": _wilson(ke, len(rs))}
    k = sum(r["score"]["all"] for r in rows)
    res["all_slots"], res["all_slots_ci"] = k / len(rows), _wilson(k, len(rows))
    res["failures"] = [{"id": r["id"], "question": r["question"], "expected": r["expected"], "got": r["got"]}
                       for r in rows if not r["score"]["all"]]
    return res


def format_bench(res: dict) -> str:
    lines = [f"Parser benchmark ({res['split']} split, {res['n']} questions): all slots right in "
             f"{100 * res['all_slots']:.0f}% (95% CI {100 * res['all_slots_ci'][0]:.0f}-{100 * res['all_slots_ci'][1]:.0f}%)"]
    for cat, r in res["by_category"].items():
        lines.append(f"  {cat:13s} n={r['n']:3d}  event {100 * r['event']:5.1f}%  all slots {100 * r['all_slots']:5.1f}% "
                     f"(95% CI {100 * r['all_slots_ci'][0]:.0f}-{100 * r['all_slots_ci'][1]:.0f}%)")
    for f in res["failures"][:20]:
        lines.append(f"  miss {f['id']}: {f['question']!r} expected {json.dumps(f['expected'])} got {json.dumps(f['got'])}")
    return "\n".join(lines)
