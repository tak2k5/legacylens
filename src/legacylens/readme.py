"""Write measured numbers into the README results table, so nobody copies them by hand.

Reads reports/eval.json (make eval), reports/eval_qa.json (make eval-qa) and reports/runs.jsonl (make extract).
Only rows whose source file exists are changed; the others keep their current text. A plain run refreshes the
measured rows. A run with an attempt, human results or a video link changes only that, so the main table keeps the run
you chose.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ATTEMPTS_HEADER = [
    "### Các lần thử",
    "",
    "| Lần | Thay đổi | Mô hình | P / R / F1 | Token mỗi chương trình |",
    "| --- | --- | --- | --- | --- |",
]


def _pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.1%}"


def _set_row(lines: list[str], label: str, value: str) -> None:
    for i, line in enumerate(lines):
        if line.startswith(f"| {label} |"):
            lines[i] = f"| {label} | {value} |"
            return
    raise ValueError(f"README row not found: {label}")


def last_runs(runs_path: Path, programs: list[str] | None) -> list[dict]:
    """Latest extract run of each program (the one whose rules are in out/rules)."""
    latest: dict[str, dict] = {}
    for line in runs_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            latest[row["program"]] = row
    return [r for p, r in latest.items() if programs is None or p in programs]


def fill(text: str, reports: Path, human: dict | None = None, attempt: str | None = None, video: str | None = None):
    lines = text.splitlines()
    changed: list[str] = []
    ev = json.loads((reports / "eval.json").read_text()) if (reports / "eval.json").exists() else None
    runs = (
        last_runs(reports / "runs.jsonl", ev["programs"] if ev else None) if (reports / "runs.jsonl").exists() else []
    )
    model = runs[-1]["model"] if runs else None
    tokens = round(sum(r["prompt_tokens"] + r["completion_tokens"] for r in runs) / len(runs)) if runs else None
    seconds = round(sum(r["seconds"] for r in runs) / len(runs), 1) if runs else None
    main = attempt is None and human is None and video is None  # plain run: refresh the measured rows
    if ev and main:
        _set_row(lines, "Precision / Recall / F1", f"{_pct(ev['precision'])} / {_pct(ev['recall'])} / {_pct(ev['f1'])}")
        _set_row(lines, "Trích dẫn qua kiểm tra", _pct(ev.get("citation_validity")))
        changed += ["Precision / Recall / F1", "Trích dẫn qua kiểm tra"]
    if runs and main:
        _set_row(lines, "Token và thời gian mỗi chương trình", f"{tokens} token, {seconds} giây (mô hình {model})")
        changed.append("Token và thời gian")
    qa_path = reports / "eval_qa.json"
    if qa_path.exists() and main:
        qa = json.loads(qa_path.read_text())["summary"]
        label = next((ln.split("|")[1].strip() for ln in lines if ln.startswith("| Agent trả lời đúng")), None)
        if label:
            _set_row(
                lines,
                label,
                f"{qa['correct']}/{qa['questions']}, trích đúng dòng {_pct(qa.get('citation_hit_rate'))} "
                f"(mô hình {qa.get('model')})",
            )
            changed.append("Hỏi đáp onboarding")
    if human:
        _set_row(
            lines,
            "Người trả lời 20 câu, chỉ đọc code / dùng LegacyLens",
            f"{human['read_min']} / {human['tool_min']} phút mỗi câu; đúng {human['read_ok']} / {human['tool_ok']} "
            f"({human['people']})",
        )
        changed.append("Bài kiểm tra với người thật")
    if attempt:
        if not ev:
            raise ValueError("run `make eval` before recording an attempt")
        if "### Các lần thử" not in lines:
            at = next(i for i, ln in enumerate(lines) if ln.startswith("## Cách chấm"))
            lines[at:at] = [*ATTEMPTS_HEADER, ""]
        start = lines.index("### Các lần thử")
        end = start + 4
        while end < len(lines) and lines[end].startswith("|"):
            end += 1
        n = end - (start + 4) + 1
        prf = f"{_pct(ev['precision'])} / {_pct(ev['recall'])} / {_pct(ev['f1'])}"
        lines.insert(end, f"| {n} | {attempt} | {model} | {prf} | {tokens} |")
        changed.append(f"Lần thử {n}")
    if video:
        lines = [ln for ln in lines if not ln.startswith("Video demo 2 phút:")]
        title = next(i for i, ln in enumerate(lines) if ln.startswith("# "))
        lines[title + 1 : title + 1] = ["", f"Video demo 2 phút: {video}"]
        changed.append("Video")
    out = "\n".join(lines) + "\n"
    return re.sub(r"\n{3,}", "\n\n", out), changed
