"""Grade the written answers of a person taking the timed onboarding test (step 10).

The answers come as a text file, one block per question (`Q01: ...`). Each answer is checked two ways: the keyword
groups of the answer key (strict, English words) and the LLM, which compares the answer with the answer key and the
cited code and gives a reason. The model only suggests: the person running the test decides the final count.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .qa import Question, _has

SAMPLE_MARK = "MẪU THỬ"  # files written to try the grader; never recorded as a real result

RE_QID = re.compile(r"\s*[*#]*\s*(?:Q|Câu|Cau)\s*0?(\d{1,2})\b[\s.:)\-*]*(.*)", re.I)

SYSTEM_GRADE = """You grade one answer from a developer who is new to a COBOL code base.
You get the question, the answer key (facts the answer must contain), the code lines where the answer lives, and the
developer's answer, which may be in Vietnamese or English. The answer is correct when it states every fact of the key,
in any words or language. Missing or wrong facts make it incorrect; extra harmless detail is fine.
Reply with ONLY this JSON: {"correct": true or false, "reason": "<one or two sentences in Vietnamese>"}"""


def is_sample(text: str) -> bool:
    return SAMPLE_MARK in text[:500]


def parse_answers(text: str) -> dict[str, str]:
    answers: dict[str, str] = {}
    cur = None
    for line in text.splitlines():
        m = RE_QID.match(line)
        if m and 1 <= int(m.group(1)) <= 20:
            cur = f"Q{int(m.group(1)):02d}"
            answers[cur] = m.group(2).strip()
        elif cur and line.strip():
            answers[cur] = (answers[cur] + " " + line.strip()).strip()
    return answers


def missing_keywords(q: Question, answer: str) -> list[str]:
    text = answer.lower()
    return [" / ".join(g) for g in q.keywords if not any(_has(text, w) for w in g)]


def answer_key(q: Question) -> str:
    return "; ".join(" or ".join(g) for g in q.keywords)


def grade(agent, q: Question, answer: str) -> tuple[bool | None, str]:
    """(correct, reason) from the model; (None, why) when it cannot be asked or gives no usable reply."""
    if not answer.strip():
        return False, "Không có câu trả lời."
    code = "\n\n".join(agent.tools.read_lines(e.program, e.start_line, e.end_line) for e in q.expected) or "-"
    user = (
        f"Question: {q.question}\n\nAnswer key (every group must be present, any word of a group is enough): "
        f"{answer_key(q)}\n\nCode where the answer lives:\n{code}\n\nDeveloper's answer:\n{answer}"
    )
    messages = [{"role": "system", "content": SYSTEM_GRADE}, {"role": "user", "content": user}]
    try:
        msg, _ = agent._complete(messages, _trace(), tools=False)
    except Exception as exc:  # Colab gone
        return None, f"Không gọi được mô hình ({type(exc).__name__})."
    text = re.sub(r"<think>.*?</think>", "", msg.content or "", flags=re.S)
    m = re.search(r"\{.*\}", text, flags=re.S)
    try:
        data = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data.get("correct"), bool):
        return None, "Mô hình trả lời không đúng định dạng, tự chấm câu này."
    return data["correct"], str(data.get("reason") or "").strip()


def _trace():
    from .agent import Trace

    return Trace()


def grade_file(agent, questions: list[Question], path: Path, part: str) -> tuple[int, int, str]:
    """Return (model_correct, keyword_correct, markdown report) for one part (Q01-Q10 or Q11-Q20)."""
    a, b = (1, 10) if part == "Q01-Q10" else (11, 20)
    text = path.read_text(encoding="utf-8", errors="replace")
    answers = parse_answers(text)
    lines = [f"# Chấm {path.name}, {part}", ""]
    if is_sample(text):
        lines += [f"**{SAMPLE_MARK}: không phải dữ liệu thật, không ghi vào kết quả.**", ""]
    lines += ["| Câu | Mô hình | Lý do | Từ khóa |", "| --- | --- | --- | --- |"]
    model_ok = kw_ok = 0
    for q in questions:
        if not a <= int(q.id[1:]) <= b:
            continue
        ans = answers.get(q.id, "")
        ok, reason = grade(agent, q, ans)
        miss = missing_keywords(q, ans) if ans else ["không có câu trả lời"]
        model_ok += ok is True
        kw_ok += not miss
        verdict = {True: "đúng", False: "sai", None: "?"}[ok]
        kw = "đủ" if not miss else "thiếu " + "; ".join(miss)
        lines.append(f"| {q.id} | {verdict} | {reason.replace('|', '/')} | {kw} |")
    lines += ["", f"Mô hình chấm đúng {model_ok}/10, từ khóa đủ {kw_ok}/10."]
    return model_ok, kw_ok, "\n".join(lines) + "\n"
