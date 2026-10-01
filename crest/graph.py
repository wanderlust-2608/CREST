from __future__ import annotations

import pandas as pd

from .definitions import BEHAVIOURS
from .library import to_storage

PROVENANCE_RULES = {
    "raw_dialogue": "may be quoted (exact substrings only) and cited by turn_uid",
    "derived_event_label": "labels from the event labeller; counts must state the labeller's gold F1",
    "derived_behaviour_label": "turn-local behaviour detections",
    "gold_label": "blind human labels on held-out calls (measurement and DSL correction only)",
    "causal_estimate": "the only source of effect numbers (Factor Library, claim level attached)",
    "descriptive_stat": "the only source of counts and rates",
    "metadata_unaudited": "unflagged metadata: descriptive filters only, never covariates in the main analysis",
}


def write_graph(ws, corpus, labels: pd.DataFrame, occ: pd.DataFrame, library: pd.DataFrame, descriptive: pd.DataFrame,
                spans: pd.DataFrame | None, gold: pd.DataFrame | None) -> dict:
    calls = corpus.calls
    base_cols = ["transcript_id", "split", "opening_domain_vote", "brand", "template_group", "n_turns",
                 "qc_possibly_truncated", "had_named_speakers"]
    c = calls[base_cols].reset_index(drop=True).assign(provenance="raw_dialogue")
    meta_cols = [x for x in ("call_date", "call_hour", "intent") if x in calls.columns and x not in corpus.leakage_flagged]
    if meta_cols:
        ws.write_parquet(calls[["transcript_id"] + meta_cols].reset_index(drop=True).assign(provenance="metadata_unaudited"),
                         "graph/call_metadata.parquet")
    ws.write_parquet(c, "graph/calls.parquet")
    t = corpus.turns
    ws.write_parquet(t[["turn_uid", "transcript_id", "turn_id", "speaker", "party", "text"]].assign(provenance="raw_dialogue"),
                     "graph/turns.parquet")
    ev = labels.reset_index()
    ws.write_parquet(ev.assign(provenance="derived_event_label"), "graph/events.parquet")
    long = []
    uids = t["turn_uid"].to_numpy()
    for b in BEHAVIOURS:
        m = occ[b].to_numpy()
        if m.any():
            long.append(pd.DataFrame({"turn_uid": uids[m], "behaviour": b}))
    occ_long = pd.concat(long, ignore_index=True) if long else pd.DataFrame({"turn_uid": [], "behaviour": []})
    ws.write_parquet(occ_long.assign(provenance="derived_behaviour_label"), "graph/behaviour_occurrences.parquet")
    ws.write_parquet(to_storage(library).assign(provenance="causal_estimate"), "graph/factor_library.parquet")
    ws.write_parquet(descriptive.assign(provenance="descriptive_stat"), "graph/descriptive.parquet")
    if spans is not None and len(spans):
        ws.write_parquet(spans.assign(provenance="raw_dialogue"), "graph/evidence_spans.parquet")
    if gold is not None and len(gold):
        ws.write_parquet(gold.assign(provenance="gold_label"), "graph/gold.parquet")
    info = {"tables": sorted(p.name for p in (ws.root / "graph").glob("*.parquet")), "provenance_rules": PROVENANCE_RULES,
            "never_indexed_or_quoted": ["annotations_quarantine (analyst notes)", "reason_for_call and other metadata text",
                                        "LLM summaries"]}
    ws.write_json(info, "graph/README.json")
    return info
