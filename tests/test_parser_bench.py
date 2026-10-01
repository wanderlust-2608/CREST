import numpy as np

from crest.cli import main
from crest.lexicon import correct_spelling, detect_language
from crest.parser_bench import bench, misspell, run_bench
from crest.query import QueryParser


def test_benchmark_is_deterministic_and_split():
    a, b = bench("test"), bench("test")
    assert [q["question"] for q in a] == [q["question"] for q in b]
    assert not {q["question"] for q in bench("dev")} & {q["question"] for q in a if q["category"] != "misspelled"}
    assert misspell("Why do customers escalate?", np.random.default_rng(0)) != "Why do customers escalate?"


def test_parser_on_noisy_and_multilingual_questions():
    for split, floor in (("dev", 0.95), ("test", 0.9)):
        res = run_bench(QueryParser(year_hint=2025), split)
        assert res["all_slots"] >= floor, res["failures"]
        assert all(r["event"] >= 0.9 for r in res["by_category"].values()), res["by_category"]


def test_language_identification():
    cases = {"¿Por qué los clientes piden un reembolso?": "Spanish", "Pourquoi les clients appellent-ils ?": "French",
             "Warum kündigen Kunden?": "German", "Por que os clientes cancelam?": "Portuguese",
             "Perché i clienti chiedono un rimborso?": "Italian", "refund kyun maangte hain": "Hindi (romanised)",
             "ग्राहक क्यों नाराज़ होते हैं": "Hindi", "Why do customers escalate?": "English",
             "What about refunds in hotel calls?": "English"}
    for text, lang in cases.items():
        assert detect_language(text)[0] == lang, (text, detect_language(text))


def test_corpus_words_are_protected_from_correction():
    assert correct_spelling("why do minibar charges cause refnds", {"minibar": 40})[0] == "why do minibar charges cause refunds"
    assert correct_spelling("pnr issues", {"pnr": 12})[1] == []


def test_cli_parser_bench_runs_without_a_workspace(tmp_path, capsys):
    assert main(["--out", str(tmp_path / "none"), "parser-bench", "--split", "dev"]) == 0
    assert "Parser benchmark (dev split" in capsys.readouterr().out
