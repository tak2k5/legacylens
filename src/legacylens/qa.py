"""Onboarding question set: score the agent's answers automatically.

Each question has keyword groups (every group must match, any word inside a group is enough) and, when the
answer lives in specific lines, expected citations; an answer "hits" when one of its citations overlaps them.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

from .schema import Answer, Citation


class Question(BaseModel):
    id: str
    question: str
    keywords: list[list[str]] = Field(description="All groups must match; any word in a group matches it")
    expected: list[Citation] = Field(default_factory=list)


def load_questions(path: str | Path) -> list[Question]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [Question.model_validate_json(line) for line in lines if line.strip()]


def _overlaps(a: Citation, b: Citation) -> bool:
    return a.program == b.program and a.start_line <= b.end_line and b.start_line <= a.end_line


def _has(text: str, word: str) -> bool:
    """Numbers must match as a whole number ("4" is not found in "line 42"); other words as substrings."""
    word = word.lower()
    if word.isdigit():
        return re.search(rf"(?<!\d){word}(?!\d)", text) is not None
    return word in text


def score_answer(q: Question, answer: Answer) -> dict:
    text = answer.answer.lower()
    groups = [any(_has(text, word) for word in group) for group in q.keywords]
    hit = None
    if q.expected:
        hit = any(_overlaps(c, e) for c in answer.citations for e in q.expected)
    return {
        "id": q.id,
        "keywords_ok": all(groups),
        "keyword_groups_matched": f"{sum(groups)}/{len(groups)}",
        "citation_hit": hit,
        "correct": all(groups) and hit is not False,
    }


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    with_expected = [r for r in rows if r["citation_hit"] is not None]
    valid = [r["citations_valid"] for r in rows if r.get("citations_valid") is not None]
    return {
        "questions": n,
        "correct": sum(r["correct"] for r in rows),
        "accuracy": round(sum(r["correct"] for r in rows) / n, 3) if n else 0.0,
        "citation_hit_rate": round(sum(r["citation_hit"] for r in with_expected) / len(with_expected), 3)
        if with_expected
        else None,
        "citation_validity": round(sum(valid) / len(valid), 3) if valid else None,
        "avg_tokens": round(sum(r.get("tokens", 0) for r in rows) / n) if n else 0,
        "avg_seconds": round(sum(r.get("seconds", 0) for r in rows) / n, 2) if n else 0,
    }


def to_markdown(summary: dict, rows: list[dict]) -> str:
    out = [
        "| Metric | Value |",
        "| --- | --- |",
        f"| Questions | {summary['questions']} |",
        f"| Correct (keywords + citation) | {summary['correct']} ({summary['accuracy']:.1%}) |",
    ]
    if summary["citation_hit_rate"] is not None:
        out.append(f"| Answers citing the expected lines | {summary['citation_hit_rate']:.1%} |")
    if summary["citation_validity"] is not None:
        out.append(f"| Citations that pass the source check | {summary['citation_validity']:.1%} |")
    out += [
        f"| Average tokens per question | {summary['avg_tokens']} |",
        f"| Average seconds per question | {summary['avg_seconds']} |",
    ]
    out += ["", "| Question | Correct | Keywords | Citation hit |", "| --- | --- | --- | --- |"]
    out += [
        f"| {r['id']} | {'yes' if r['correct'] else 'no'} | {r['keyword_groups_matched']} | {'' if r['citation_hit'] is None else r['citation_hit']} |"
        for r in rows
    ]
    return "\n".join(out)


def dump_row(q: Question, answer: Answer, checks: list[dict], trace_dict: dict) -> dict:
    row = score_answer(q, answer)
    row["citations_valid"] = (sum(c["valid"] for c in checks) / len(checks)) if checks else None
    row["tokens"] = trace_dict.get("prompt_tokens", 0) + trace_dict.get("completion_tokens", 0)
    row["seconds"] = trace_dict.get("seconds", 0)
    row["tool_calls"] = trace_dict.get("tool_calls", 0)
    row["answer"] = answer.answer
    row["citations"] = [json.loads(c.model_dump_json()) for c in answer.citations]
    return row
