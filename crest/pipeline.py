from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

from .config import Settings
from .io import Workspace, file_sha256, json_sha256, load_corpus

STAGES = ["build", "gold-sample", "precision-sheets", "gold-ingest", "pilot", "prereg", "confirm", "evidence", "index",
          "queries", "run-queries", "evaluate"]


def _log(msg: str) -> None:
    print(msg, flush=True)


class Pipeline:
    def __init__(self, settings: Settings, log=_log):
        self.s = settings
        self.ws = Workspace(settings.out_dir)
        self.log = log
        self._corpus = None
        self._lm = None

    def corpus(self):
        if self._corpus is None:
            self._corpus = load_corpus(self.s.data_dir, self.s.opening_turns)
        return self._corpus

    def labels(self) -> pd.DataFrame:
        df = self.ws.read_parquet("events/events.parquet").set_index("transcript_id")
        return df

    def occurrences(self) -> pd.DataFrame:
        from .definitions import BEHAVIOURS
        occ = self.ws.read_parquet("behaviours/occurrences.parquet")
        return occ[list(BEHAVIOURS)]

    def landmarks(self):
        from .landmarks import Landmarks
        if self._lm is None:
            p = self.ws.root / "landmarks"
            if not (p / "X.npy").is_file():
                raise FileNotFoundError("landmarks not built -- run `python -m crest build` first")
            self._lm = Landmarks.load(p)
        return self._lm

    def gold(self) -> pd.DataFrame | None:
        return self.ws.read_parquet("gold/gold.parquet") if self.ws.exists("gold/gold.parquet") else None

    def precision(self) -> dict:
        from .behaviours import read_precision
        return read_precision(self.ws.root / "precision")

    def build(self, labeller: str = "lexicon", llm=None) -> dict:
        from .behaviours import (blindness_check, cooccurrence, families, occurrence_matrix, prevalence,
                                 regex_blindness_check)
        from .events import (detector_labels, event_sequence, lexicon_labels, llm_dev_labels, train_onset_detectors)
        from .landmarks import build_landmarks, future_invariance_test
        t0 = time.time()
        corpus = self.corpus()
        self.log(f"[build] {corpus.n_calls:,} calls, {len(corpus.turns):,} turns; opening = {corpus.opening_turns} turns"
                 + (f"; {len(corpus.excluded)} calls without dialogue turns set aside" if len(corpus.excluded) else ""))
        lb = self.s.labeller
        labels = lexicon_labels(corpus, lb.semantic_churn, lb.semantic_threshold, lb.semantic_encoder, self.s.index.st_model)
        label_info = {"kind": "lexicon", "churn_detector": labels.attrs.get("churn_detector", {})}
        if labeller == "llm":
            if llm is None or not getattr(llm, "available", False):
                raise RuntimeError("--labeller llm needs llm.backend = 'anthropic' (and the data rules must allow it)")
            dev = llm_dev_labels(corpus, labels, llm, self.s.llm.dev_sample_size, self.s.seed)
            self.ws.write_parquet(dev, "events/llm_dev_sample.parquet")
            verified = {e: float(dev[f"{e}_verified"].mean()) for e in ("ESC", "REF", "CHURN")}
            det = train_onset_detectors(corpus, dev, self.s.seed)
            labels = detector_labels(corpus, det, labels)
            label_info = {"kind": "llm_detector", "dev_sample": int(len(dev)), "quote_verified_share": verified}
        seq = event_sequence(labels)
        ev = labels.copy()
        ev["event_sequence"] = seq
        ev["label_source"] = label_info["kind"]
        ev["provenance"] = "derived_event_label"
        self.ws.write_parquet(ev.reset_index(), "events/events.parquet")
        occ = occurrence_matrix(corpus.turns)
        occ_out = occ.copy()
        occ_out.insert(0, "turn_uid", corpus.turns["turn_uid"].to_numpy())
        occ_out["provenance"] = "derived_behaviour_label"
        self.ws.write_parquet(occ_out, "behaviours/occurrences.parquet")
        prevalence(corpus, occ).to_csv(self.ws.path("behaviours/prevalence.csv"))
        co = cooccurrence(corpus, occ)
        co.to_csv(self.ws.path("behaviours/cooccurrence.csv"), index=False)
        fam = families(co, 0.7)
        lm = build_landmarks(corpus, self.s)
        lm.save(self.ws.root / "landmarks")
        self._lm = lm
        fi = future_invariance_test(corpus, lm, n=min(1000, len(lm.meta)), seed=self.s.seed, last_k=self.s.landmark.last_k)
        bl = blindness_check(corpus.turns, sample=min(20000, len(corpus.turns)), seed=self.s.seed)
        rb = regex_blindness_check(corpus.turns)
        onset_counts = {e: {"calls_with_event": int((labels[f"{e}_onset"] >= 0).sum()),
                            "in_opening": int(((labels[f"{e}_onset"] >= 0) & (labels[f"{e}_onset"] < corpus.opening_turns)).sum())}
                        for e in ("ESC", "REF", "CHURN")}
        checks = {"future_invariance": fi, "cue_blindness": bl, "regex_blindness": rb, "families_phi_gt_0_7": fam,
                  "labeller": label_info, "event_counts": onset_counts, "landmark_rows": int(len(lm.meta)),
                  "n_features": int(lm.X.shape[1]), "leakage_flagged_columns": sorted(corpus.leakage_flagged),
                  "opening_domain_filled_from_brand": int(corpus.report.get("opening_domain_filled_from_brand", 0)),
                  "excluded_calls": corpus.excluded.to_dict("records")}
        self.ws.write_json(checks, "checks/build_checks.json")
        if not fi["passed"]:
            raise AssertionError(f"future-invariance test failed: {fi}")
        if not bl["passed"] or not rb["passed"]:
            raise AssertionError(f"outcome-blindness check failed: {bl} {rb}")
        self.ws.record_stage("build", ["events/events.parquet", "behaviours/occurrences.parquet", "landmarks/X.npy",
                                       "checks/build_checks.json"], self.s.hash(), {"labeller": label_info}, t0)
        self.log(f"[build] future invariance {fi['failures']}/{fi['rows_checked']} failures; blindness passed; "
                 f"landmark rows {len(lm.meta):,} x {lm.X.shape[1]} features ({time.time() - t0:.0f}s)")
        return checks

    def gold_sample(self, force: bool = False) -> Path:
        from .events import draw_gold_sample, write_gold_packets
        t0 = time.time()
        if self.ws.exists("gold/sample.parquet") and not force:
            self.log("[gold-sample] a gold sample already exists (it may already be with annotators); use --force to redraw")
            return self.ws.root / "gold" / "gold_to_label.csv"
        corpus, labels = self.corpus(), self.labels()
        g = self.s.gold
        sample = draw_gold_sample(corpus, labels, g.n_random, g.n_stress, g.n_double, g.seed)
        self.ws.write_parquet(sample, "gold/sample.parquet")
        path = write_gold_packets(corpus, sample, self.ws.root / "gold")
        self.ws.record_stage("gold-sample", ["gold/sample.parquet", "gold/gold_to_label.csv"], self.s.hash(),
                             {"n_calls": int(len(sample))}, t0)
        self.log(f"[gold-sample] {len(sample)} held-out calls ({int(sample['double_coded'].sum())} double-coded) -> {path}")
        return path

    def precision_sheets(self) -> list:
        from .behaviours import precision_sheets
        corpus = self.corpus()
        paths = precision_sheets(corpus, self.occurrences(), self.ws.root / "precision", n=20, seed=self.s.seed)
        self.log(f"[precision-sheets] {len(paths)} sheets in {self.ws.root / 'precision'} (train turns only)")
        return paths

    def gold_ingest(self, file: str | Path) -> dict:
        from .events import gold_metrics, ingest_gold
        t0 = time.time()
        sample = self.ws.read_parquet("gold/sample.parquet")
        gold = ingest_gold(Path(file), sample, self.corpus())
        m = gold_metrics(gold, self.labels())
        self.ws.write_parquet(gold, "gold/gold.parquet")
        m["file_sha256"] = file_sha256(file)
        self.ws.write_json(m, "gold/gold_metrics.json")
        self.ws.record_stage("gold-ingest", ["gold/gold.parquet", "gold/gold_metrics.json"], self.s.hash(), {}, t0)
        for e, d in m["by_event"].items():
            self.log(f"[gold-ingest] {e}: F1 {d['f1']:.3f} (95% CI {d['f1_ci'][0]:.3f}-{d['f1_ci'][1]:.3f}), onset within 1 "
                     f"turn {d['onset_within1']:.2f}, kappa {d['kappa_presence']:.2f}")
        return m

    def builder(self, with_gold: bool):
        from .analysis import RiskSetBuilder
        return RiskSetBuilder(self.corpus(), self.landmarks(), self.labels(), self.occurrences(), self.s,
                              self.gold() if with_gold else None)

    def pilot(self) -> dict:
        from .analysis import pilot
        t0 = time.time()
        if (self.ws.root / "prereg" / "prereg.sha256").is_file():
            self.log("[pilot] note: a pre-registration is already frozen; a new pilot only matters with `prereg --force`")
        res = pilot(self.builder(with_gold=False), self.s, self.precision())
        res["table"].to_csv(self.ws.path("pilot/pilot_table.csv"), index=False)
        self.ws.write_json({k: v for k, v in res.items() if k != "table"}, "pilot/pilot.json")
        self.ws.record_stage("pilot", ["pilot/pilot.json", "pilot/pilot_table.csv"], self.s.hash(),
                             {"learner": res["learner"], "planted_passed": res["planted"].get("passed")}, t0)
        tab = res["table"]
        for e, grp in tab[tab["negative_control"]].groupby("event"):
            usable = grp[(grp["status"] == "ok") & (grp["n_treated"].fillna(0) >= 20)]
            if not len(usable):
                self.log(f"[pilot] WARNING: no negative control is estimable for {e} on train "
                         f"({', '.join(f'{r.behaviour}: {int(r.n_treated or 0)} treated moments' for r in grp.itertuples())}); "
                         f"if none is estimable on held-out calls either, no {e} claim can reach L3")
        pl = res["planted"]
        planted_msg = (f"planted-effect test passed={pl.get('passed')} (bias {pl.get('bias', float('nan')):+.4f}, "
                       f"coverage {pl.get('coverage', float('nan')):.2f}, false alarms {pl.get('false_alarm_rate', float('nan')):.2f})"
                       if pl.get("n_sims") else f"planted-effect test NOT RUN: {pl.get('reason')} -- no claim can reach L3")
        self.log(f"[pilot] learner {res['learner']}; {planted_msg}; family sizes "
                 f"{ {e: len(v) for e, v in res['family'].items()} } ({time.time() - t0:.0f}s)")
        return res

    def prereg(self, force: bool = False) -> dict:
        from .prereg import build_prereg, freeze
        t0 = time.time()
        pil = self.ws.read_json("pilot/pilot.json")
        pil["table"] = pd.read_csv(self.ws.root / "pilot" / "pilot_table.csv")
        sample = self.ws.read_parquet("gold/sample.parquet") if self.ws.exists("gold/sample.parquet") else None
        labeller = self.ws.manifest().get("stages", {}).get("build", {}).get("labeller", {}).get("kind", "lexicon")
        pr = build_prereg(self.s, self.corpus(), self.labels(), pil, self.precision(), sample, labeller)
        rec = freeze(self.ws, pr, force=force)
        self.ws.record_stage("prereg", ["prereg/prereg.json", "prereg/prereg.sha256"], self.s.hash(),
                             {"prereg_sha256": rec["sha256"], "amended": rec.get("amended", False)}, t0)
        self.log(f"[prereg] frozen: sha256 {rec['sha256']} -> commit prereg/prereg.json and prereg.sha256 before `confirm`")
        return rec

    def confirm(self, allow_posthoc: bool = False) -> pd.DataFrame:
        from .analysis import confirm
        from .behaviours import cooccurrence
        from .library import (build_library, corrected_event_rates, descriptive_table, issue_terms, opening_terms,
                              slice_estimates, to_storage, validate_library)
        from .prereg import verify
        t0 = time.time()
        corpus, labels = self.corpus(), self.labels()
        v = verify(self.ws, self.s, corpus, labels)
        if not v["ok"]:
            if not v.get("frozen") or not allow_posthoc:
                raise RuntimeError("pre-registration check failed: " + "; ".join(v["problems"]) +
                                   ("" if v.get("frozen") else "") + " (use --allow-posthoc to run anyway; every result is then "
                                   "exploratory, at most L2)")
            self.log("[confirm] WARNING: running post hoc -- every result is capped at L2: " + "; ".join(v["problems"]))
        prereg_ok = v["ok"] and not v.get("amended")
        prereg = v["prereg"]
        gold = self.gold()
        builder = self.builder(with_gold=True)
        conf = confirm(builder, prereg, self.s)
        self.log(f"[confirm] {len(conf)} pre-registered estimates on held-out calls "
                 f"({'with' if gold is not None else 'without'} the DSL gold correction)")
        sl = slice_estimates(builder, prereg, self.s)
        gm = self.ws.read_json("gold/gold_metrics.json") if self.ws.exists("gold/gold_metrics.json") else None
        occ = self.occurrences()
        co = cooccurrence(corpus, occ)
        planted = prereg.get("planted_effect_test", {})
        lib_version = "lib-" + json_sha256({"prereg": v.get("sha256"), "settings": self.s.hash(),
                                            "gold": gm.get("file_sha256") if gm else None,
                                            "labels": prereg.get("labeller", {}).get("labels_sha256")})[:16]
        ctx = {"settings": self.s, "prereg_ok": prereg_ok, "prereg_sha256": v.get("sha256"),
               "planted_passed": bool(planted.get("passed")), "gold": gm, "precision": self.precision(), "cooc": co,
               "learner": json.dumps(prereg.get("learner")), "library_version": lib_version}
        lib = build_library(conf, ctx, sl)
        problems = validate_library(lib, self.s)
        if problems:
            raise AssertionError("factor library failed validation: " + "; ".join(problems[:10]))
        self.ws.write_parquet(to_storage(lib), "library/factor_library.parquet")
        readable = lib[["factor_id", "event", "behaviour", "slice", "level", "att", "ci_low", "ci_high", "q", "boot_ci_low",
                        "boot_ci_high", "n_treated", "events_treated", "events_control", "kept_share", "balance_smd",
                        "support_band", "e_value", "attributable", "att_dev", "att_test", "dsl", "failed_checks"]].copy()
        readable["failed_checks"] = readable["failed_checks"].map(lambda x: ", ".join(x))
        readable.to_csv(self.ws.path("library/factor_library.csv"), index=False)
        desc = descriptive_table(corpus, labels, occ)
        self.ws.write_parquet(desc, "library/descriptive.parquet")
        report = {"prereg_sha256": v.get("sha256"), "prereg_ok": prereg_ok, "library_version": lib_version,
                  "corrected_rates": corrected_event_rates(corpus, labels, gold),
                  "opening_terms": {e: opening_terms(corpus, labels, e) for e in ("ESC", "REF", "CHURN")},
                  "gold_metrics": gm, "planted_effect_test": planted,
                  "levels": lib[lib["slice"] == "all"].groupby(["event", "level"]).size().unstack(fill_value=0).to_dict("index"),
                  "negative_controls": lib[lib["negative_control"]][["event", "behaviour", "att", "ci_low", "ci_high"]].to_dict("records")}
        self.ws.write_json(report, "library/library_report.json")
        self.ws.write_json(issue_terms(corpus, labels), "library/issue_terms.json")
        self.ws.record_stage("confirm", ["library/factor_library.parquet", "library/descriptive.parquet",
                                         "library/library_report.json", "library/issue_terms.json"], self.s.hash(),
                             {"library_version": lib_version, "prereg_sha256": v.get("sha256"), "posthoc": not prereg_ok}, t0)
        main = lib[(lib["slice"] == "all") & ~lib["negative_control"]]
        self.log(f"[confirm] library {lib_version}: " + ", ".join(f"{k} {n}" for k, n in main["level"].value_counts().sort_index().items())
                 + f" ({time.time() - t0:.0f}s)")
        return lib

    def library(self) -> pd.DataFrame:
        from .library import from_storage
        return from_storage(self.ws.read_parquet("library/factor_library.parquet"))

    def evidence(self) -> dict:
        from .evidence import build_evidence
        t0 = time.time()
        res = build_evidence(self.corpus(), self.landmarks(), self.labels(), self.occurrences(), self.library(), self.s, self.log)
        spans = res["spans"]
        self.ws.write_parquet(spans if len(spans) else pd.DataFrame({"span_id": []}), "evidence/evidence_spans.parquet")
        res["factor_summary"].to_csv(self.ws.path("evidence/factor_faithfulness.csv"), index=False)
        self.ws.write_json({"forecaster_quality": res["forecaster_quality"], "comprehensiveness": res["comprehensiveness"]},
                           "evidence/forecaster_quality.json")
        self.ws.record_stage("evidence", ["evidence/evidence_spans.parquet", "evidence/factor_faithfulness.csv",
                                          "evidence/forecaster_quality.json"], self.s.hash(), {}, t0)
        self.log(f"[evidence] {len(spans)} grounding spans; forecaster AUC " + ", ".join(
            f"{e} {q.get('auc_next_turn', float('nan')):.3f}" for e, q in res["forecaster_quality"].items()) + f" ({time.time() - t0:.0f}s)")
        return res

    def index(self) -> dict:
        from .graph import write_graph
        from .index import SearchIndex
        t0 = time.time()
        idx = SearchIndex.build(self.corpus(), self.labels(), self.occurrences(), self.s, self.log)
        idx.save(self.ws.root / "index")
        from .lexicon import vocabulary
        self.ws.write_json(vocabulary(self.corpus().turns["text_clean"]), "index/vocab.json")
        write_graph(self.ws, self.corpus(), self.labels(), self.occurrences(), self.library(),
                    self.ws.read_parquet("library/descriptive.parquet"),
                    self.ws.read_parquet("evidence/evidence_spans.parquet") if self.ws.exists("evidence/evidence_spans.parquet") else None,
                    self.gold())
        self.ws.record_stage("index", ["index/windows.parquet", "index/index.pkl"], self.s.hash(),
                             {"index_version": idx.version, "embedder": idx.embedder.backend}, t0)
        self.log(f"[index] {len(idx.windows):,} windows, embedder {idx.embedder.backend}, version {idx.version} "
                 f"({time.time() - t0:.0f}s)")
        return {"version": idx.version, "windows": int(len(idx.windows))}

    def artifacts(self):
        from .answer import Artifacts
        from .index import SearchIndex
        corpus = self.corpus()
        calls = corpus.calls
        keep = ["transcript_id", "split", "opening_domain_vote", "brand", "n_turns"]
        for c in ("call_date", "intent", "time_of_interaction", "call_hour", "tier", "plan", "segment", "tenure_months"):
            if c in calls.columns and c not in corpus.leakage_flagged:
                keep.append(c)
        rep = self.ws.read_json("library/library_report.json")
        if not self.ws.exists("library/issue_terms.json"):
            from .library import issue_terms
            self.ws.write_json(issue_terms(corpus, self.labels()), "library/issue_terms.json")
        rep["issue_terms"] = self.ws.read_json("library/issue_terms.json")
        idx = SearchIndex.load(self.ws.root / "index") if (self.ws.root / "index" / "index.pkl").is_file() else None
        spans = self.ws.read_parquet("evidence/evidence_spans.parquet") if self.ws.exists("evidence/evidence_spans.parquet") else pd.DataFrame()
        faith = pd.read_csv(self.ws.root / "evidence" / "factor_faithfulness.csv") if (self.ws.root / "evidence" / "factor_faithfulness.csv").is_file() else pd.DataFrame()
        turn_text = pd.Series(corpus.turns["text"].to_numpy(), index=corpus.turns["turn_uid"].to_numpy())
        turns = corpus.turns[["call_idx", "turn_id", "party"]].reset_index(drop=True)
        if self.ws.exists("behaviours/occurrences.parquet"):
            occ = self.occurrences().reset_index(drop=True)
            if len(occ) == len(turns):
                turns = pd.concat([turns, occ.astype(bool)], axis=1)
        from .answer import self_reported_status
        ct = corpus.turns
        first, word = self_reported_status(ct["call_idx"].to_numpy(), ct["turn_id"].to_numpy(), ct["party"].to_numpy(),
                                           ct["text_clean"].to_numpy(), corpus.n_calls)
        calls = calls[keep].reset_index(drop=True).assign(self_status=word, self_status_turn=first)
        return Artifacts(library=self.library(), calls=calls, labels=self.labels(),
                         turn_text=turn_text, spans=spans, faithfulness=faith, report=rep, index=idx,
                         library_version=rep["library_version"], index_version=idx.version if idx else "none",
                         opening_turns=corpus.opening_turns, turns=turns)

    def engine(self, llm=None, use_llm_writer=False, use_llm_parser=False):
        from .query import QueryParser
        from .session import Engine
        art = self.artifacts()
        corpus = self.corpus()
        parser = QueryParser.from_corpus_calls(corpus.calls, corpus.leakage_flagged)
        if self.ws.exists("index/vocab.json"):
            parser.vocab = self.ws.read_json("index/vocab.json")
        else:
            from .lexicon import vocabulary
            parser.vocab = vocabulary(corpus.turns["text_clean"])
            self.ws.write_json(parser.vocab, "index/vocab.json")
        return Engine(art, self.s, parser, llm, use_llm_writer, use_llm_parser)

    def queries(self, force: bool = False) -> dict:
        from .queries import build_query_set, write_query_set
        t0 = time.time()
        if self.ws.exists("queries/queries_test.jsonl") and not force:
            self.log("[queries] a query set already exists (the test split is locked); use --force to rebuild it")
            return self.ws.read_json("queries/queries_lock.json")
        try:
            labels = self.labels()
        except Exception:
            labels = None
        qs = build_query_set(self.corpus(), self.library(), self.s, labels)
        lock = write_query_set(self.ws, qs)
        self.ws.record_stage("queries", ["queries/queries_dev.jsonl", "queries/queries_test.jsonl", "queries/queries.csv",
                                         "queries/queries_review.csv"], self.s.hash(), lock, t0)
        self.log(f"[queries] {lock['n_dev']} dev + {lock['n_test']} locked test queries; test sha256 {lock['test_sha256'][:16]}")
        return lock

    def run_queries(self, split: str = "all", llm=None, use_llm_writer=False, use_llm_parser=False) -> dict:
        from .evaluate import run_query_file
        t0 = time.time()
        eng = self.engine(llm, use_llm_writer, use_llm_parser)
        out = {}
        for sp in (["dev", "test"] if split == "all" else [split]):
            path = self.ws.root / "queries" / f"queries_{sp}.jsonl"
            if sp == "test":
                lock = self.ws.read_json("queries/queries_lock.json")
                if file_sha256(path) != lock["test_sha256"]:
                    raise RuntimeError("queries_test.jsonl changed after it was locked")
            res = run_query_file(eng, path, self.ws.path(f"outputs/outputs_{sp}.jsonl"))
            out[sp] = res
        self.ws.record_stage("run-queries", [f"outputs/outputs_{sp}.jsonl" for sp in out], self.s.hash(), {}, t0)
        self.log("[run-queries] " + ", ".join(f"{k}: {v['n']} queries" for k, v in out.items()) + f" ({time.time() - t0:.0f}s)")
        return out

    def evaluate(self, truth: dict | None = None, llm=None) -> dict:
        from .evaluate import evaluate_all
        t0 = time.time()
        res = evaluate_all(self, truth, llm)
        self.ws.record_stage("evaluate", ["eval/metrics.json", "REPORT.md", "outputs/QUERY_OUTPUTS.md"], self.s.hash(), {}, t0)
        self.log(f"[evaluate] report written to {self.ws.root / 'REPORT.md'} ({time.time() - t0:.0f}s)")
        return res

    def status(self) -> str:
        m = self.ws.manifest().get("stages", {})
        lines = [f"workspace: {self.ws.root}"]
        for st in STAGES:
            info = m.get(st)
            lines.append(f"  {'done' if info else '    '}  {st:17s} {info['finished_utc'] if info else ''}")
        nxt = next((st for st in STAGES if st not in m), None)
        lines.append(f"next: {nxt}" if nxt else "all stages done")
        return "\n".join(lines)
