from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "01_data_cleaning.ipynb"
CUES_PY = Path(__file__).resolve().parent / "cues.py"
BLOCKS = (("QUOTE_MAP", "extract_stage_directions"), ("CUE_DEFS", "is_question"))


def notebook_code(nb_path: str | Path = NOTEBOOK) -> str:
    nb = json.loads(Path(nb_path).read_text(encoding="utf-8"))
    cells = []
    for c in nb["cells"]:
        if c.get("cell_type") == "code":
            src = c["source"]
            cells.append("".join(src) if isinstance(src, list) else src)
    return "\n\n".join(cells)


def _block(lines: list[str], start: str, end_func: str) -> str:
    i = next(n for n, line in enumerate(lines) if line.startswith(start))
    j = next(n for n in range(i, len(lines)) if lines[n].startswith(f"def {end_func}("))
    k = j + 1
    while k < len(lines) and (lines[k].startswith((" ", "\t")) or not lines[k].strip()):
        k += 1
    while not lines[k - 1].strip():
        k -= 1
    return "\n".join(lines[i:k])


def notebook_cue_blocks(nb_path: str | Path = NOTEBOOK) -> list[str]:
    lines = notebook_code(nb_path).split("\n")
    return [_block(lines, s, e) for s, e in BLOCKS]


def check_cues_sync(nb_path: str | Path = NOTEBOOK, cues_path: str | Path = CUES_PY) -> dict:
    text = Path(cues_path).read_text(encoding="utf-8")
    blocks = notebook_cue_blocks(nb_path)
    ok = [b in text for b in blocks]
    return {"in_sync": all(ok), "blocks": dict(zip([s for s, _ in BLOCKS], ok))}


def sync_cues(nb_path: str | Path = NOTEBOOK, cues_path: str | Path = CUES_PY) -> bool:
    p = Path(cues_path)
    text = p.read_text(encoding="utf-8")
    lines = text.split("\n")
    new = text
    for (start, end), nb_block in zip(BLOCKS, notebook_cue_blocks(nb_path)):
        old_block = _block(lines, start, end)
        new = new.replace(old_block, nb_block)
    if new != text:
        p.write_text(new, encoding="utf-8")
        return True
    return False


def run_cleaning_notebook(raw_path: str | Path, out_dir: str | Path, nb_path: str | Path = NOTEBOOK,
                          log_path: str | Path | None = None) -> Path:
    code = notebook_code(nb_path)
    env_backup = dict(os.environ)
    os.environ["RAW_TRANSCRIPTS_PATH"] = str(raw_path)
    os.environ["CLEANED_DATA_DIR"] = str(out_dir)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(code, str(nb_path), "exec"), {"__name__": "__main__", "__file__": str(nb_path)})
    finally:
        os.environ.clear()
        os.environ.update(env_backup)
        if log_path is not None:
            Path(log_path).write_text(buf.getvalue(), encoding="utf-8")
    report = json.loads((Path(out_dir) / "cleaning_report.json").read_text(encoding="utf-8"))
    bad = [c for c in report.get("integrity_checks", []) if not c.get("ok")]
    if bad:
        raise AssertionError(f"cleaning notebook integrity checks failed: {bad}")
    return Path(out_dir)
