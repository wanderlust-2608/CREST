from __future__ import annotations

import json
import math
import re

import numpy as np
import pandas as pd

from .analysis import HELD_OUT, RiskSetBuilder, estimate, support_band
from .definitions import BEHAVIOURS, EVENTS, PRIMARY_EVENTS
from .stats import benjamini_hochberg

LIBRARY_SCHEMA_VERSION = "2"
LEVELS = ("L0", "L1", "L2", "L3")

CHECKS = {
    "preregistered": "the factor was not in the frozen pre-registration (or the plan was changed after freezing)",
    "actionable": "it is a customer state, not something the company can change",
    "support_sufficient": "support is not 'sufficient' (events per arm, overlap, CI width or balance)",
    "bh_significant": "not significant after the Benjamini-Hochberg correction over the pre-registered family",
    "bootstrap_excludes_zero": "the cluster-bootstrap interval includes zero",
    "sensitivity_stable": "the sign is not stable across the required sensitivity analyses",
    "dev_test_agree": "the dev and test halves disagree in sign",
    "negative_controls_clean": "a negative control for this event shows an effect (possible hidden bias), or no control "
                               "could be estimated",
    "planted_test_passed": "the planted-effect test of the estimator did not pass",
    "gold_f1_ok": "the event labeller was not verified on the gold set (F1 unknown or below the threshold)",
    "precision_verified": "a person has not confirmed that the behaviour detector is precise enough",
}
JSON_COLUMNS = ("sensitivity", "checks", "failed_checks", "support_reasons", "top_imbalance", "co_occurring",
                "attributable_ci", "e_value_ci_pair", "ci_dev", "ci_test")


def _sign(x: float) -> int:
    return 0 if not np.isfinite(x) or x == 0 else (1 if x > 0 else -1)


def sensitivity_check(att: float, runs: list[dict], required) -> tuple[bool, str]:
    s0 = _sign(att)
    if not runs:
        return False, "sensitivity analyses were not run"
    by_base: dict[str, list] = {}
    for r in runs:
        by_base.setdefault(r.get("base", r["analysis"][:2]), []).append(r)
    problems = []
    for name in required:
        rr = by_base.get(name, [])
        if not rr or any(r.get("status") != "ok" for r in rr):
            problems.append(f"{name} not estimable")
    for r in runs:
        if r.get("status") != "ok":
            continue
        if _sign(r["att"]) != s0:
            sig = (r["ci_low"] > 0 or r["ci_high"] < 0)
            problems.append(f"{r['analysis']} {'significantly ' if sig else ''}opposite sign")
    return (not problems), "; ".join(problems)


def descriptive_ok(n_calls: int) -> bool:
    return n_calls >= 5


def assign_level(row: dict, checks: dict, band: str, exploratory: bool) -> tuple[str, str]:
    if row.get("negative_control"):
        return "NC", "negative control (used only to check for hidden bias)"
    if row.get("status") != "ok":
        return ("L1" if descriptive_ok(int(row.get("n_calls") or 0)) else "L0"), "no estimate: " + str(row.get("reason", ""))
    if band == "insufficient":
        return "L1", "support insufficient for an estimate"
    if all(checks.values()) and not exploratory and band == "sufficient":
        return "L3", "all checks passed"
    failed = [k for k, v in checks.items() if not v]
    why = "exploratory slice" if exploratory else "failed: " + ", ".join(failed)
    return "L2", why


def build_library(confirm_df: pd.DataFrame, ctx: dict, slices: pd.DataFrame | None = None) -> pd.DataFrame:
    s = ctx["settings"]
    rows = []
    frames = [confirm_df.assign(exploratory=False)]
    if slices is not None and len(slices):
        frames.append(slices.assign(exploratory=True))
    df = pd.concat(frames, ignore_index=True)
    nc_status = confirm_df.groupby("event")["negative_controls_clean"].first().to_dict() if len(confirm_df) else {}
    slice_rows = df["exploratory"].to_numpy()
    df.loc[slice_rows, "negative_controls_clean"] = df.loc[slice_rows, "event"].map(nc_status).fillna(False).astype(bool).to_numpy()
    gold = ctx.get("gold") or {}
    for r in df.to_dict("records"):
        e, b = r["event"], r["behaviour"]
        beh = BEHAVIOURS[b]
        band, reasons = support_band(r, s.support)
        gm = gold.get("by_event", {}).get(e, {}) if gold else {}
        f1 = gm.get("f1", float("nan"))
        prec = ctx.get("precision", {}).get(b, {})
        sens_ok, sens_why = sensitivity_check(r.get("att", float("nan")), r.get("sensitivity") or [],
                                              s.claim.min_sensitivity)
        checks = {
            "preregistered": bool(ctx.get("prereg_ok")) and not r["exploratory"],
            "actionable": bool(beh.actionable),
            "support_sufficient": band == "sufficient",
            "bh_significant": bool(np.isfinite(r.get("q", np.nan)) and r.get("q") < s.estimator.bh_q),
            "bootstrap_excludes_zero": bool(np.isfinite(r.get("boot_ci_low", np.nan))
                                            and (r["boot_ci_low"] > 0 or r["boot_ci_high"] < 0)
                                            and _sign(r["boot_ci_low"]) == _sign(r.get("att", np.nan))),
            "sensitivity_stable": bool(sens_ok),
            "dev_test_agree": bool(_sign(r.get("att_dev", np.nan)) != 0
                                   and _sign(r.get("att_dev", np.nan)) == _sign(r.get("att_test", np.nan))
                                   == _sign(r.get("att", np.nan))),
            "negative_controls_clean": bool(r.get("negative_controls_clean")),
            "planted_test_passed": bool(ctx.get("planted_passed")),
            "gold_f1_ok": bool(np.isfinite(f1) and f1 >= s.claim.gold_f1_min),
            "precision_verified": bool(prec.get("n_judged", 0) >= 20 and prec.get("precision", 0) >= s.claim.precision_min),
        }
        level, why = assign_level(r, checks, band, bool(r["exploratory"]))
        if level == "L2" and band == "borderline" and why == "failed: ":
            why = "support borderline"
        failed = [k for k, v in checks.items() if not v] if level not in ("NC",) else []
        co = []
        cooc = ctx.get("cooc")
        if cooc is not None and len(cooc):
            m = cooc[((cooc["a"] == b) | (cooc["b"] == b)) & (cooc["call_phi"] >= 0.2)]
            co = [[x.b if x.a == b else x.a, round(float(x.call_phi), 2)] for x in m.itertuples(index=False)]
            co = sorted(co, key=lambda t: -t[1])[:4]
        rec = dict(r)
        rec.update({
            "behaviour_label": beh.label, "behaviour_short": beh.short, "party": beh.party, "actionable": beh.actionable,
            "event_name": EVENTS[e].name, "support_band": band, "support_reasons": reasons, "checks": checks,
            "failed_checks": failed, "sensitivity_note": sens_why, "level": level, "level_reason": why,
            "gold_f1": f1, "precision": prec.get("precision", float("nan")), "precision_n": int(prec.get("n_judged", 0)),
            "co_occurring": co, "prereg_sha256": ctx.get("prereg_sha256"), "library_version": ctx.get("library_version"),
            "learner": ctx.get("learner"), "schema_version": LIBRARY_SCHEMA_VERSION,
        })
        rows.append(rec)
    lib = pd.DataFrame(rows)
    lib = assign_factor_ids(lib)
    return lib


def assign_factor_ids(lib: pd.DataFrame) -> pd.DataFrame:
    lvl_rank = {"L3": 0, "L2": 1, "L1": 2, "L0": 3, "NC": 4}
    ev_rank = {e: i for i, e in enumerate(EVENTS)}
    key = pd.DataFrame({
        "g": lib["exploratory"].astype(int) + 2 * lib["negative_control"].astype(int),
        "ev": lib["event"].map(ev_rank), "lvl": lib["level"].map(lvl_rank),
        "att": -lib["attributable"].abs().fillna(-1.0), "slice": lib["slice"].astype(str), "b": lib["behaviour"]})
    order = key.sort_values(["g", "ev", "slice", "lvl", "att", "b"], kind="mergesort").index
    lib = lib.loc[order].reset_index(drop=True)
    lib.insert(0, "factor_id", [f"F{i + 1}" for i in range(len(lib))])
    return lib


def to_storage(lib: pd.DataFrame) -> pd.DataFrame:
    from .io import sanitize_json
    out = lib.copy()
    for c in out.columns:
        if out[c].map(lambda v: isinstance(v, (list, dict, tuple))).any():
            out[c] = out[c].map(lambda v: json.dumps(sanitize_json(v)))
            out = out.rename(columns={c: c + "_json"})
    return out


def from_storage(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in list(out.columns):
        if c.endswith("_json"):
            out[c[:-5]] = out[c].map(lambda v: json.loads(v) if isinstance(v, str) else v)
            out = out.drop(columns=c)
    return out


def validate_library(lib: pd.DataFrame, settings) -> list[str]:
    problems = []
    need = ["factor_id", "event", "behaviour", "slice", "level", "checks", "failed_checks", "att", "ci_low", "ci_high",
            "support_band", "prereg_sha256", "library_version"]
    miss = [c for c in need if c not in lib.columns]
    if miss:
        return [f"missing columns {miss}"]
    if not lib["factor_id"].is_unique:
        problems.append("factor ids are not unique")
    for r in lib.to_dict("records"):
        if r["level"] not in LEVELS + ("NC",):
            problems.append(f"{r['factor_id']}: unknown level {r['level']}")
            continue
        if r["level"] == "L3":
            if not all(r["checks"].values()) or r["support_band"] != "sufficient" or r.get("exploratory"):
                problems.append(f"{r['factor_id']}: L3 without every check")
        if r["level"] in ("L2", "L3") and not (np.isfinite(r["att"]) and np.isfinite(r["ci_low"])):
            problems.append(f"{r['factor_id']}: {r['level']} without an estimate")
        if r["level"] in ("L2", "L3") and r["support_band"] == "insufficient":
            problems.append(f"{r['factor_id']}: {r['level']} with insufficient support")
    return problems


def slice_values(corpus, column: str, min_calls: int = 20) -> list[str]:
    held = corpus.calls[corpus.calls["split"].isin(HELD_OUT)]
    vc = held[column].astype(str).value_counts()
    return [v for v, n in vc.items() if n >= min_calls and v not in ("unknown", "none", "nan")]


def slice_estimates(builder: RiskSetBuilder, prereg: dict, settings, columns=("opening_domain_vote",)) -> pd.DataFrame:
    est = settings.estimator
    rows = []
    for col in columns:
        for val in slice_values(builder.corpus, col):
            for e in PRIMARY_EVENTS:
                for b in prereg["family"].get(e, []):
                    rs = builder.build(e, b, HELD_OUT, {"slice": {col: val}})
                    r = estimate(rs, settings, prereg["learner"], est.seed)
                    rows.append({"event": e, "behaviour": b, "negative_control": False, "family": "exploratory_slice",
                                 "slice": f"{col}={val}", **r})
    df = pd.DataFrame(rows)
    if len(df):
        df["q"] = benjamini_hochberg(df["p"].to_numpy(dtype=float))
        df["negative_controls_clean"] = False
        df["sensitivity"] = [[] for _ in range(len(df))]
        df["att_dev"] = np.nan
        df["att_test"] = np.nan
    return df


_TOKEN = re.compile(r"[a-z][a-z']+")
_STOP = set("""a an the and or but if so to of in on at for from with by is are was were be been am i you he she it we
they me my your our their this that these those there here what which who whom whose do does did have has had not no
yes okay ok just can could would will shall should may might please hi hello thank thanks um uh like really very im
i'm it's that's calling call because about today get got one also well oh yeah sure right now""".split())


def opening_terms(corpus, labels: pd.DataFrame, event: str, n: int = 8, splits=None) -> list[dict]:
    t = corpus.turns
    op = (t["turn_id"] < corpus.opening_turns) & (t["party"] == "Customer")
    if splits is not None:
        op &= t["split"].isin(list(splits))
    onset = labels.loc[corpus.call_ids, f"{event}_onset"].to_numpy()
    call_of = t["call_idx"].to_numpy()
    grp_a = (onset >= 0) & (onset < corpus.opening_turns)
    grp_b = onset < 0
    texts = t.loc[op, "text_clean"].to_numpy()
    calls = call_of[op.to_numpy()]
    ca, cb = {}, {}
    for txt, c in zip(texts, calls):
        tgt = ca if grp_a[c] else cb if grp_b[c] else None
        if tgt is None:
            continue
        for g in _grams(txt):
            tgt[g] = tgt.get(g, 0) + 1
    if not ca or not cb:
        return []
    vocab = set(ca) | set(cb)
    alpha = {w: 0.01 * (ca.get(w, 0) + cb.get(w, 0)) + 0.01 for w in vocab}
    a0 = sum(alpha.values())
    na, nb = sum(ca.values()), sum(cb.values())
    out = []
    n_a_calls = int(grp_a.sum())
    for w in vocab:
        ya, yb, aw = ca.get(w, 0), cb.get(w, 0), alpha[w]
        if ya < 3:
            continue
        d = math.log((ya + aw) / (na + a0 - ya - aw)) - math.log((yb + aw) / (nb + a0 - yb - aw))
        var = 1.0 / (ya + aw) + 1.0 / (yb + aw)
        out.append({"term": w, "z": d / math.sqrt(var), "calls_with_term": ya, "share": ya / max(1, n_a_calls)})
    out.sort(key=lambda x: -x["z"])
    return out[:n]


_ANY_TOKEN = re.compile(r"[a-z0-9][a-z0-9']*")
_TOPIC_STOP = set("""pretty honestly completely totally absolutely actually literally basically seriously still even already
again ever never always only two three four five six seven eight nine ten twenty first second third last next after before
since ago back going gonna wanna want wanted need needed trying tried try said says told tell called know think see help hey
morning afternoon evening name phone number hurry asap immediately quickly soon today yesterday week weeks day days hour
hours minute minutes time times thing things something anything way lot bit""".split())


def _grams(text: str, topic: bool = False) -> set:
    toks = _ANY_TOKEN.findall(str(text).lower())
    stop = _STOP | _TOPIC_STOP if topic else _STOP
    keep = [len(w) > (2 if topic else 1) and w.replace("'", "").isalpha() and w not in stop for w in toks]
    uni = {w for w, k in zip(toks, keep) if k}
    return uni | {f"{a} {b}" for a, b, ka, kb in zip(toks, toks[1:], keep, keep[1:]) if ka and kb}


def issue_terms(corpus, labels: pd.DataFrame, events=PRIMARY_EVENTS, n: int = 6, min_calls: int = 5, min_slice_calls: int = 30,
                slice_col: str = "opening_domain_vote", n_examples: int = 2) -> dict:
    from .cues import CUES
    from .query import find_behaviours, find_events
    t = corpus.turns
    op = ((t["turn_id"] < corpus.opening_turns) & (t["party"] == "Customer")).to_numpy()
    rows = np.flatnonzero(op)
    call_of = t["call_idx"].to_numpy()[rows]
    turn_id = t["turn_id"].to_numpy()[rows]
    text_clean = t["text_clean"].to_numpy()[rows]
    uids = t["turn_uid"].to_numpy()[rows]
    raw = t["text"].to_numpy()[rows]
    grams = [_grams(x, topic=True) for x in text_clean]
    n_words = np.array([len(str(x).split()) for x in raw])
    slice_vals = corpus.calls[slice_col].astype(str).to_numpy() if slice_col in corpus.calls.columns else None
    slices = [("all", None)]
    if slice_vals is not None:
        for v, k in pd.Series(slice_vals).value_counts().items():
            if k >= min_slice_calls and v not in ("unknown", "nan", "none"):
                slices.append((f"{slice_col}={v}", v))
    usable: dict[str, bool] = {}

    def keep(term: str) -> bool:
        if term not in usable:
            usable[term] = not (find_events(term) or find_behaviours(term) or any(rx.search(term) for _, rx in CUES.values()))
        return usable[term]

    out: dict = {}
    for e in events:
        onset = labels.loc[corpus.call_ids, f"{e}_onset"].to_numpy()
        on_row = onset[call_of]
        in_a = (on_row >= 0) & (turn_id < on_row)
        in_b = on_row < 0
        out[e] = {}
        for name, val in slices:
            in_slice = np.ones(len(rows), dtype=bool) if val is None else slice_vals[call_of] == val
            docs = {"a": {}, "b": {}}
            for grp, mask in (("a", in_a & in_slice), ("b", in_b & in_slice)):
                per_call: dict = {}
                for i in np.flatnonzero(mask):
                    per_call.setdefault(call_of[i], set()).update(grams[i])
                cnt: dict = {}
                for gs in per_call.values():
                    for g in gs:
                        cnt[g] = cnt.get(g, 0) + 1
                docs[grp] = (cnt, len(per_call))
            (ca, na_calls), (cb, nb_calls) = docs["a"], docs["b"]
            if na_calls < min_calls or nb_calls < min_calls:
                out[e][name] = {"n_event_calls": int(na_calls), "n_other_calls": int(nb_calls), "terms": []}
                continue
            vocab = set(ca) | set(cb)
            alpha = {w: 0.01 * (ca.get(w, 0) + cb.get(w, 0)) + 0.01 for w in vocab}
            a0 = sum(alpha.values())
            na, nb = sum(ca.values()), sum(cb.values())
            scored = []
            for w in vocab:
                ya, yb, aw = ca.get(w, 0), cb.get(w, 0), alpha[w]
                if ya < min_calls or ya / na_calls <= yb / nb_calls or not keep(w):
                    continue
                d = math.log((ya + aw) / (na + a0 - ya - aw)) - math.log((yb + aw) / (nb + a0 - yb - aw))
                scored.append((d / math.sqrt(1.0 / (ya + aw) + 1.0 / (yb + aw)), w, ya, yb))
            scored.sort(key=lambda x: (-x[0], x[1]))
            terms = []
            for z, w, ya, yb in scored:
                if z < 1.96:
                    break
                if any(set(w.split(" ")) & set(c["term"].split(" ")) for c in terms):
                    continue
                terms.append({"term": w, "z": float(z), "calls_event": int(ya), "calls_other": int(yb),
                              "share_event": ya / na_calls, "share_other": yb / nb_calls})
                if len(terms) >= n:
                    break
            cand = np.flatnonzero(in_a & in_slice)
            order = cand[np.lexsort((uids[cand].astype(str), n_words[cand]))]
            for c in terms:
                ex, seen = [], set()
                for i in order:
                    if c["term"] in grams[i] and call_of[i] not in seen and n_words[i] <= 60:
                        ex.append(str(uids[i]))
                        seen.add(call_of[i])
                        if len(ex) >= n_examples:
                            break
                c["examples"] = ex
            out[e][name] = {"n_event_calls": int(na_calls), "n_other_calls": int(nb_calls), "terms": terms}
    return out


def descriptive_table(corpus, labels: pd.DataFrame, occ: pd.DataFrame, gold: pd.DataFrame | None = None,
                      slice_columns=("opening_domain_vote", "brand")) -> pd.DataFrame:
    calls = corpus.calls
    call_idx = corpus.turns["call_idx"].to_numpy()
    beh_calls = occ.groupby(call_idx).any()
    beh_calls.index = corpus.call_ids[beh_calls.index.to_numpy()]
    slices = [("all", np.ones(corpus.n_calls, dtype=bool))]
    for col in slice_columns:
        for v in calls[col].astype(str).value_counts().index:
            slices.append((f"{col}={v}", (calls[col].astype(str) == v).to_numpy()))
    rows = []
    for e in EVENTS:
        on = labels.loc[corpus.call_ids, f"{e}_onset"].to_numpy()
        has = on >= 0
        opening = has & (on < corpus.opening_turns)
        for name, m in slices:
            n = int(m.sum())
            rows.append({"kind": "event", "event": e, "behaviour": "", "slice": name, "calls": n,
                         "event_calls": int((has & m).sum()), "rate": float((has & m).sum() / n) if n else float("nan"),
                         "opening_share": float((opening & m).sum() / max(1, (has & m).sum())),
                         "median_onset": float(np.median(on[has & m])) if (has & m).any() else float("nan")})
            if name != "all" and not name.startswith("opening_domain_vote"):
                continue
            for b in occ.columns:
                bc = beh_calls[b].reindex(corpus.call_ids).fillna(False).to_numpy().astype(bool)
                with_b = bc & m
                rows.append({"kind": "behaviour", "event": e, "behaviour": b, "slice": name, "calls": int(with_b.sum()),
                             "event_calls": int((with_b & has).sum()),
                             "rate": float((with_b & has).sum() / with_b.sum()) if with_b.any() else float("nan"),
                             "without_event": int((with_b & ~has).sum()), "opening_share": float("nan"),
                             "median_onset": float("nan")})
    df = pd.DataFrame(rows)
    df["provenance"] = "descriptive_stat"
    return df


def corrected_event_rates(corpus, labels: pd.DataFrame, gold: pd.DataFrame | None, alpha: float = 0.05) -> dict:
    from .stats import z_crit
    if gold is None or not len(gold):
        return {}
    held = corpus.calls.index[corpus.calls["split"].isin(HELD_OUT)]
    N = len(held)
    out = {}
    g = gold.set_index("transcript_id")
    for e in PRIMARY_EVENTS:
        yhat = (labels.loc[held, f"{e}_onset"] >= 0).astype(float)
        diff = (g[f"{e}_onset"] >= 0).astype(float) - (labels.loc[g.index, f"{e}_onset"] >= 0).astype(float)
        w = 1.0 / g["pi"].astype(float)
        total = float(yhat.sum() + (w * diff).sum())
        contrib = w * diff
        var = float(len(g) / max(1, len(g) - 1) * ((contrib - contrib.mean()) ** 2).sum()) if len(g) > 1 else float("nan")
        rate = total / N
        se = math.sqrt(var) / N if np.isfinite(var) else float("nan")
        z = z_crit(alpha)
        out[e] = {"rate": rate, "ci": [rate - z * se, rate + z * se], "labeller_rate": float(yhat.mean()), "n_calls": int(N)}
    return out
