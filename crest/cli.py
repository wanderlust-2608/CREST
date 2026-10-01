from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .config import Settings


def _settings(args) -> Settings:
    s = Settings.load(args.config)
    if args.data:
        s.data_dir = args.data
    if args.out:
        s.out_dir = args.out
    if getattr(args, "llm", False):
        s.llm.backend = "anthropic"
    s.validate()
    return s


def _llm(s: Settings):
    from .llm import make_llm
    llm = make_llm(s, s.out_dir)
    if s.llm.backend != "none" and not getattr(llm, "available", False):
        print(f"LLM backend unavailable ({getattr(llm, 'reason', 'unknown')}); using the deterministic path", file=sys.stderr)
    return llm


def cmd_ask(pipe, args):
    from .session import SessionState
    s = pipe.s
    eng = pipe.engine(_llm(s), args.llm_writer, args.llm_parser)
    state = None
    if args.session:
        p = Path(args.session)
        try:
            state = SessionState.from_dict(json.loads(p.read_text(encoding="utf-8"))) if p.is_file() else None
        except (ValueError, TypeError) as exc:
            print(f"(session file {p} could not be read ({type(exc).__name__}); starting a new conversation)", file=sys.stderr)
            state = None
    ans, state = eng.ask(args.question, state)
    if args.session:
        Path(args.session).parent.mkdir(parents=True, exist_ok=True)
        Path(args.session).write_text(json.dumps(state.to_dict(), indent=1), encoding="utf-8")
    if args.json:
        print(json.dumps({k: ans[k] for k in ("question", "route", "text", "spec", "levels", "seconds")}, indent=1, default=str))
    else:
        print(ans["text"])
        print(f"\n[route: {ans['route']}; levels: {ans['levels']}; {ans['seconds']:.2f}s]")


def cmd_chat(pipe, args):
    from .session import SessionState
    eng = pipe.engine(_llm(pipe.s), args.llm_writer, args.llm_parser)
    state = SessionState(library_version=eng.art.library_version, index_version=eng.art.index_version)
    print("CREST chat -- ask about escalations, refunds or churn threats. Empty line or 'quit' to stop.")
    while True:
        try:
            q = input("\nyou> ").strip()
        except EOFError:
            break
        if not q or q.lower() in ("quit", "exit"):
            break
        ans, state = eng.ask(q, state)
        print("\n" + ans["text"])
        print(f"[route: {ans['route']}; spec: event={ans['spec'] and ans['spec'].get('event')}, "
              f"filters={ans['spec'] and ans['spec'].get('filters')}]")


def cmd_parser_bench(args):
    from .parser_bench import format_bench, run_bench
    from .query import QueryParser
    s = _settings(args)
    reader, parser, ws = None, QueryParser(year_hint=2025), None
    if Path(s.out_dir, "manifest.json").is_file():
        from .pipeline import Pipeline
        pipe = Pipeline(s)
        ws = pipe.ws
        if args.llm:
            eng = pipe.engine(_llm(s))
            reader, parser = eng.read_question, eng.parser
    out = {}
    for sp in (["dev", "test"] if args.split == "all" else [args.split]):
        out[sp] = run_bench(parser, sp, reader)
        print(format_bench(out[sp]))
    if ws is not None:
        ws.write_json(out, "eval/parser_bench.json")
    return 0


def cmd_demo(args):
    from .devtools import run_cleaning_notebook
    from .simulate import SimConfig, fill_gold_labels, fill_precision_sheets, write_corpus
    from .pipeline import Pipeline
    out = Path(args.out or "demo_out")
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "synthetic_transcripts.json"
    t0 = time.time()
    if not raw.is_file():
        print(f"[demo] simulating {args.n_calls} calls (seed {args.seed}) ...", flush=True)
        write_corpus(raw, SimConfig(n_calls=args.n_calls, seed=args.seed))
    truth = json.loads((out / "synthetic_transcripts_truth.json").read_text())["calls"]
    cleaned = out / "cleaned_data"
    if not (cleaned / "turns.parquet").is_file():
        print("[demo] running notebooks/01_data_cleaning.ipynb ...", flush=True)
        run_cleaning_notebook(raw, cleaned, log_path=out / "cleaning.log")
    s = Settings.load(args.config)
    s.data_dir, s.out_dir = str(cleaned), str(out / "crest_out")
    pipe = Pipeline(s)
    pipe.build()
    gold_csv = pipe.gold_sample()
    sample = pipe.ws.read_parquet("gold/sample.parquet")
    filled = fill_gold_labels(sample, truth, gold_csv, pipe.ws.root / "gold" / "gold_labelled_simulated.csv", seed=1)
    pipe.precision_sheets()
    fill_precision_sheets(pipe.ws.root / "precision", truth)
    pipe.gold_ingest(filled)
    pipe.pilot()
    pipe.prereg(force=True)
    pipe.confirm()
    pipe.evidence()
    pipe.index()
    write_retrieval_queries(pipe, truth)
    pipe.queries(force=True)
    pipe.run_queries("all")
    pipe.evaluate(truth)
    print(f"[demo] done in {time.time() - t0:.0f}s -- see {pipe.ws.root / 'REPORT.md'}")


def write_retrieval_queries(pipe, truth) -> Path:
    corpus = pipe.corpus()
    held = corpus.calls[corpus.calls["split"].isin(["dev", "test"])]
    by_id = {t["transcript_id"]: t for t in truth}
    qs = []
    for ind in sorted(held["opening_domain_vote"].unique()):
        ids = held.index[held["opening_domain_vote"] == ind]
        rel = [i for i in ids if "ESC" in by_id[i]["onsets_visible"] and any("refusal" in b for b in by_id[i]["behaviours"].values())]
        if len(rel) >= 3:
            qs.append({"query": "customer asks for a supervisor after the agent refuses citing policy",
                       "filters": {"split": ["dev", "test"], "industry": [ind]}, "relevant": rel})
        rel = [i for i in ids if "REF" in by_id[i]["onsets_visible"]]
        if len(rel) >= 3:
            qs.append({"query": "customer wants a refund or their money back", "filters": {"split": ["dev", "test"], "industry": [ind]},
                       "relevant": rel})
        rel = [i for i in ids if "CHURN" in by_id[i]["onsets_visible"]]
        if len(rel) >= 3:
            qs.append({"query": "customer threatens to switch to another provider or cancel",
                       "filters": {"split": ["dev", "test"], "industry": [ind]}, "relevant": rel})
    p = pipe.ws.path("eval/retrieval_queries.jsonl")
    p.write_text("".join(json.dumps(q) + "\n" for q in qs), encoding="utf-8")
    return p


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(prog="python -m crest", description="Causal rationale extraction pipeline (see docs/METHODOLOGY.md)")
    ap.add_argument("--data", help="cleaned data folder (default: cleaned_data)")
    ap.add_argument("--out", help="output workspace (default: crest_out)")
    ap.add_argument("--config", help="JSON file with settings to override")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data", default=argparse.SUPPRESS, help="cleaned data folder (default: cleaned_data)")
    common.add_argument("--out", default=argparse.SUPPRESS, help="output workspace (default: crest_out)")
    common.add_argument("--config", default=argparse.SUPPRESS, help="JSON file with settings to override")
    sub = ap.add_subparsers(dest="cmd", required=True)
    _add = sub.add_parser
    sub.add_parser = lambda name, **kw: _add(name, parents=[common], **kw)
    sub.add_parser("status", help="show which stages are done")
    b = sub.add_parser("build", help="Steps 1-3: event labels, behaviours, landmark features, integrity tests")
    b.add_argument("--labeller", choices=["lexicon", "llm"], default="lexicon")
    b.add_argument("--llm", action="store_true", help="enable the Anthropic backend for this command")
    g = sub.add_parser("gold-sample", help="Step 1e: draw the blind gold sample from held-out calls")
    g.add_argument("--force", action="store_true")
    sub.add_parser("precision-sheets", help="Step 3: sheets for the human precision check (train turns)")
    gi = sub.add_parser("gold-ingest", help="Step 1e: validate the filled-in gold labels and measure the labeller")
    gi.add_argument("--file", required=True)
    sub.add_parser("pilot", help="Step 4 phase 1 (train only): learner tuning, planted-effect test, family selection")
    pr = sub.add_parser("prereg", help="Step 4 phase 2: freeze the analysis plan (commit the hash)")
    pr.add_argument("--force", action="store_true")
    cf = sub.add_parser("confirm", help="Step 4 phase 3: estimate once on held-out calls; Factor Library with claim levels")
    cf.add_argument("--allow-posthoc", action="store_true")
    sub.add_parser("evidence", help="Step 5: grounding spans, forecaster, faithfulness")
    sub.add_parser("index", help="Step 6: evidence graph and hybrid search index")
    for name in ("ask", "chat"):
        a = sub.add_parser(name, help="Steps 7-12: answer a question" if name == "ask" else "interactive session (Task 2)")
        if name == "ask":
            a.add_argument("question")
            a.add_argument("--session", help="JSON file holding the conversation state (created if missing)")
            a.add_argument("--json", action="store_true")
        a.add_argument("--llm", action="store_true")
        a.add_argument("--llm-writer", action="store_true")
        a.add_argument("--llm-parser", action="store_true")
    q = sub.add_parser("queries", help="Step 14: build the dev / locked-test query set")
    q.add_argument("--force", action="store_true")
    rq = sub.add_parser("run-queries", help="answer the query set -> outputs/*.jsonl")
    rq.add_argument("--split", choices=["dev", "test", "all"], default="all")
    rq.add_argument("--llm", action="store_true")
    rq.add_argument("--llm-writer", action="store_true")
    rq.add_argument("--llm-parser", action="store_true")
    ev = sub.add_parser("evaluate", help="Step 13: metrics, baselines, REPORT.md and outputs/QUERY_OUTPUTS.md")
    ev.add_argument("--truth", help="simulator truth file (synthetic corpora only)")
    ev.add_argument("--llm", action="store_true", help="also rate the query set with an LLM judge (optional; brands masked)")
    ra = sub.add_parser("run-all", help="every stage in order (needs gold labels via --gold-file for L3 claims)")
    ra.add_argument("--gold-file")
    d = sub.add_parser("demo", help="synthetic end-to-end run with known causes (no real data needed)")
    d.add_argument("--n-calls", type=int, default=4000)
    d.add_argument("--seed", type=int, default=11)
    sc = sub.add_parser("sync-cues", help="copy the cue lexicons from the notebook into crest/cues.py")
    sc.add_argument("--check", action="store_true")
    pb = sub.add_parser("parser-bench", help="score the question parser on noisy and multilingual questions")
    pb.add_argument("--split", choices=["dev", "test", "all"], default="all")
    pb.add_argument("--llm", action="store_true", help="read questions with the LLM fallback (needs a workspace)")
    args = ap.parse_args(argv)

    if args.cmd == "demo":
        return cmd_demo(args)
    if args.cmd == "parser-bench":
        return cmd_parser_bench(args)
    if args.cmd == "sync-cues":
        from .devtools import check_cues_sync, sync_cues
        if args.check:
            r = check_cues_sync()
            print(json.dumps(r))
            return 0 if r["in_sync"] else 1
        print("updated" if sync_cues() else "already in sync")
        return 0
    from .pipeline import Pipeline
    s = _settings(args)
    pipe = Pipeline(s)
    if args.cmd == "status":
        print(pipe.status())
    elif args.cmd == "build":
        pipe.build(args.labeller, _llm(s) if args.labeller == "llm" else None)
    elif args.cmd == "gold-sample":
        pipe.gold_sample(args.force)
    elif args.cmd == "precision-sheets":
        pipe.precision_sheets()
    elif args.cmd == "gold-ingest":
        pipe.gold_ingest(args.file)
    elif args.cmd == "pilot":
        pipe.pilot()
    elif args.cmd == "prereg":
        pipe.prereg(args.force)
    elif args.cmd == "confirm":
        pipe.confirm(args.allow_posthoc)
    elif args.cmd == "evidence":
        pipe.evidence()
    elif args.cmd == "index":
        pipe.index()
    elif args.cmd == "ask":
        cmd_ask(pipe, args)
    elif args.cmd == "chat":
        cmd_chat(pipe, args)
    elif args.cmd == "queries":
        pipe.queries(args.force)
    elif args.cmd == "run-queries":
        pipe.run_queries(args.split, _llm(s), args.llm_writer, args.llm_parser)
    elif args.cmd == "evaluate":
        truth = json.loads(Path(args.truth).read_text())["calls"] if args.truth else None
        pipe.evaluate(truth, _llm(s) if args.llm else None)
    elif args.cmd == "run-all":
        pipe.build()
        pipe.gold_sample()
        pipe.precision_sheets()
        if args.gold_file:
            pipe.gold_ingest(args.gold_file)
        pipe.pilot()
        pipe.prereg()
        pipe.confirm()
        pipe.evidence()
        pipe.index()
        pipe.queries()
        pipe.run_queries("all")
        pipe.evaluate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
