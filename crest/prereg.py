from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from .definitions import NEGATIVE_CONTROLS, definitions_snapshot
from .io import json_sha256, sanitize_json

PREREG_FILE = "prereg/prereg.json"
PREREG_LOCK = "prereg/prereg.sha256"
PREREG_VERSION = 2

ESTIMAND_CARD = {
    "population": "held-out calls (dev + test); landmark rows (call, turn k) with k >= opening_turns, the event not yet "
                  "started, no other confirmatory event and no supervisor handoff started before k (S5 relaxes this), "
                  "behaviour B not yet used, turn k spoken by B's party, both parties already spoken",
    "treatment": "B first happens at turn k",
    "comparator": "B does not happen at turn k (it may happen later: natural course afterwards)",
    "outcome": "the event starts after turn k, before the call ends (primary); within the next 6 turns (S1)",
    "time_zero": "turn k",
    "contrast": "average effect on the treated (ATT), risk difference in points",
    "covariates": "only opening and turn-past columns of turns before k (availability registry; future-invariance test)",
    "unit_and_clusters": "row = (call, k); clusters = template groups (cross-fitting folds and standard errors)",
    "call_end": "the end of the call is part of the outcome (total effect), not censoring",
    "truncation": "primary analysis treats every transcript as complete; S3 drops calls flagged as possibly truncated",
    "label_error": "DSL correction with the blind held-out gold set when it exists (outcome and risk-set membership)",
}

CLAIM_RULES = [
    "L3 requires every check: preregistered, actionable, support sufficient, BH q < bh_q, cluster-bootstrap CI excludes 0, "
    "required sensitivity analyses (claim.min_sensitivity) estimable with the same sign and none significantly opposite, "
    "dev and test agree in sign, negative controls clean, planted-effect test passed, gold presence F1 >= gold_f1_min, "
    "detector precision verified >= precision_min",
    "L2: an estimate exists with at least borderline support but some L3 check fails (failed checks are listed)",
    "L1: no usable estimate (not estimable or insufficient support) but calls can be counted",
    "L0: nothing can be said reliably",
    "exploratory slices and anything not pre-registered: at most L2",
]


def labels_hash(labels: pd.DataFrame) -> str:
    cols = sorted(c for c in labels.columns if c.endswith("_onset"))
    ids = [str(i) for i in labels.index]
    vals = labels[cols].to_numpy(dtype=np.int64)
    order = np.argsort(np.asarray(ids, dtype=object), kind="mergesort")
    lines = [",".join(cols)] + [ids[i] + "," + ",".join(str(int(v)) for v in vals[i]) for i in order]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def build_prereg(settings, corpus, labels: pd.DataFrame, pilot_result: dict, precision: dict,
                 gold_sample: pd.DataFrame | None, labeller: str) -> dict:
    defs = definitions_snapshot()
    table = pilot_result["table"]
    return sanitize_json({
        "prereg_version": PREREG_VERSION,
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "estimand": ESTIMAND_CARD,
        "family": pilot_result["family"],
        "negative_controls": list(NEGATIVE_CONTROLS),
        "family_rule": " ".join((pilot_result.get("family_rule") or "").split()),
        "learner": pilot_result["learner"],
        "other_learner": pilot_result["other_learner"],
        "learner_choice": pilot_result["learner_choice"],
        "planted_effect_test": pilot_result["planted"],
        "claim_rules": CLAIM_RULES,
        "sensitivity_analyses": pilot_result.get("sensitivity", {}),
        "precision_checks": precision,
        "labeller": {"kind": labeller, "labels_sha256": labels_hash(labels)},
        "gold_sample_sha256": json_sha256(sorted(gold_sample["transcript_id"].tolist())) if gold_sample is not None else None,
        "data_fingerprint": corpus.fingerprint(),
        "settings": settings.analysis_dict(),
        "settings_sha256": settings.hash(),
        "definitions": defs,
        "definitions_sha256": json_sha256(defs),
        "pilot_summary": {"n_pairs": int(len(table)), "estimable": int((table["status"] == "ok").sum())},
    })


def _canonical_bytes(prereg: dict) -> bytes:
    return (json.dumps(prereg, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def freeze(ws, prereg: dict, force: bool = False) -> dict:
    data = _canonical_bytes(prereg)
    sha = hashlib.sha256(data).hexdigest()
    lock = ws.root / PREREG_LOCK
    history = []
    if lock.is_file():
        old = json.loads(lock.read_text(encoding="utf-8"))
        if old["sha256"] == sha:
            return old
        if not force:
            raise RuntimeError("a different pre-registration is already frozen (prereg/prereg.sha256). Changing the plan "
                               "after freezing makes the confirmation post hoc; rerun with --force to record an amendment.")
        history = old.get("history", []) + [{"sha256": old["sha256"], "frozen_utc": old["frozen_utc"]}]
    path = ws.path(PREREG_FILE)
    path.write_bytes(data)
    rec = {"sha256": sha, "frozen_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "amended": bool(history),
           "history": history, "file": PREREG_FILE}
    ws.path(PREREG_LOCK).write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return rec


def verify(ws, settings=None, corpus=None, labels: pd.DataFrame | None = None) -> dict:
    lock_p, file_p = ws.root / PREREG_LOCK, ws.root / PREREG_FILE
    if not lock_p.is_file() or not file_p.is_file():
        return {"frozen": False, "ok": False, "problems": ["no frozen pre-registration (run `python -m crest prereg`)"]}
    lock = json.loads(lock_p.read_text(encoding="utf-8"))
    data = file_p.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    prereg = json.loads(data.decode("utf-8"))
    problems = []
    if sha != lock["sha256"]:
        problems.append("prereg.json was edited after it was frozen (hash mismatch)")
    if settings is not None and prereg.get("settings_sha256") != settings.hash():
        problems.append("analysis settings differ from the frozen ones")
    if prereg.get("definitions_sha256") != json_sha256(definitions_snapshot()):
        problems.append("event/behaviour definitions differ from the frozen ones")
    if corpus is not None and prereg.get("data_fingerprint") != sanitize_json(corpus.fingerprint()):
        problems.append("the cleaned data differ from the data the plan was frozen on")
    if labels is not None and prereg.get("labeller", {}).get("labels_sha256") != labels_hash(labels):
        problems.append("event labels differ from the frozen labeller output")
    gs = ws.root / "gold" / "sample.parquet"
    current = json_sha256(sorted(pd.read_parquet(gs)["transcript_id"].astype(str).tolist())) if gs.is_file() else None
    if current != prereg.get("gold_sample_sha256"):
        problems.append("the gold sample differs from the one recorded when the plan was frozen (draw the gold sample "
                        "before `prereg`, or amend the plan with `prereg --force`)")
    return {"frozen": True, "ok": not problems, "problems": problems, "sha256": sha, "amended": bool(lock.get("amended")),
            "prereg": prereg}


def family_size(prereg: dict) -> int:
    return int(np.sum([len(v) for v in prereg["family"].values()]))
