import shutil

import numpy as np
import pandas as pd

from crest.io import load_account_attributes
from crest.query import QueryParser


def test_account_columns_are_recognised_and_normalised(tmp_path):
    calls = pd.DataFrame({"transcript_id": ["a", "b", "c"]})
    pd.DataFrame({"transcript_id": ["a", "b"], "Loyalty_Tier": ["Gold ", "Basic"], "tenure": [30, 2]}) \
        .to_csv(tmp_path / "account_attributes.csv", index=False)
    out, info = load_account_attributes(tmp_path, calls)
    assert out["tier"].tolist() == ["gold", "basic", "unknown"] and out["tenure_months"].tolist()[:2] == [30, 2]
    assert info["fields"]["tier"]["source_column"] == "loyalty_tier"
    assert load_account_attributes(tmp_path / "missing", calls)[1] == {}


def test_parser_uses_real_tiers_and_keeps_self_reports_separate():
    P = QueryParser(year_hint=2025, account={"tier": ["basic", "gold", "platinum"]}, has_tenure=True)
    s = P.parse("Which premium customers escalate the most?")
    assert s.filters == {"tier": ["gold", "platinum"]} and not s.unsupported
    assert P.parse("Which tier asks for refunds the most?").compare["dimension"] == "tier"
    assert P.parse("How often do new customers threaten to cancel?").filters == {"tenure": "new"}
    assert P.parse("Why do customers who say they are gold members escalate?").filters == {"self_status": ["gold"]}
    s = QueryParser(year_hint=2025).parse("Which premium customers escalate the most?")
    assert [u["attribute"] for u in s.unsupported] == ["customer tier"] and not s.filters


def test_engine_with_an_account_file(demo, tmp_path):
    from crest.pipeline import Pipeline
    data = tmp_path / "cleaned"
    shutil.copytree(demo["pipe"].s.data_dir, data)
    ids = pd.read_parquet(data / "conversations.parquet", columns=["transcript_id"])["transcript_id"]
    rng = np.random.default_rng(0)
    pd.DataFrame({"transcript_id": ids, "customer_tier": rng.choice(["Basic", "Gold", "Platinum"], len(ids))}) \
        .to_csv(data / "account_attributes.csv", index=False)
    s = demo["pipe"].s
    s2 = type(s).from_dict({k: v for k, v in s.to_dict().items() if k not in ("data_dir", "out_dir")})
    s2.data_dir, s2.out_dir = str(data), s.out_dir
    eng = Pipeline(s2, log=lambda m: None).engine()
    ans, _ = eng.ask("Which tier escalates the most?")
    assert ans["pack"]["rank"]["dimension"] == "tier" and len(ans["pack"]["rank"]["groups"]) == 3 and not ans["dropped"]
    ans, _ = eng.ask("Why do premium customers escalate?")
    assert ans["spec"]["filters"] == {"tier": ["gold", "platinum"]} and "customer-tier field" not in ans["text"]
    ans, _ = eng.ask("How often do customers who say they are gold members escalate?")
    assert ans["spec"]["filters"] == {"self_status": ["gold"]} and "self-reported, not a verified tier" in ans["text"]
