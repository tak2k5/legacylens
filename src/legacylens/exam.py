"""The timed onboarding test (step 10), taken by a tester in the UI instead of over a shared screen.

Each person does two parts of 10 questions: one by reading the code only, one with LegacyLens. The 20 questions are
drawn at random from the bank (onboarding/ngan_hang.jsonl: 24 programs, 10 questions each), one question per
program, so no two questions of a paper are about the same program. The draw is fixed per person number and seed, so
a page reload shows the same paper, and the answer file records which bank question each Qnn was. The clock starts when the tester presses Start and is kept
in a file, so a page reload does not reset it. Submitting writes the answers (Q01: ...) for `make grade` and one row
to onboarding/bai_lam.csv; the score is added later by the person running the test (guide step 10.3).
"""

from __future__ import annotations

import csv
import os
import random
import re
import time
from pathlib import Path

from .qa import Question

READ, TOOL = "1", "2"  # same codes as onboarding/ket_qua_bam_gio.csv: 1 = read the code only, 2 = LegacyLens
METHOD_NAMES = {READ: "chỉ đọc code", TOOL: "dùng LegacyLens"}
FIELDS = ["nguoi", "cach", "cau", "giay", "file", "phut_dem_nguoc"]
DEFAULT_MINUTES = 15  # countdown shown to the tester; it warns, it never cuts the tester off


MAX_PEOPLE = 30
BANK = "onboarding/ngan_hang.jsonl"
PER_PAPER = 20
RE_PAPER = re.compile(r"^Đề:\s*(.+)$", re.M)


def parts(person: str) -> list[tuple[str, str]]:
    """[(method, question range)] in the order the person takes them (guide table in step 10).

    Odd numbers read the code for Q01-Q10 and use LegacyLens for Q11-Q20; even numbers swap the halves. Each paper is
    drawn at random from the bank, so which half is harder is chance, and it evens out over many people.
    """
    if not (person.isdigit() and 1 <= int(person) <= MAX_PEOPLE):
        raise ValueError(f"person must be 1-{MAX_PEOPLE}")
    if int(person) % 2:
        return [(READ, "Q01-Q10"), (TOOL, "Q11-Q20")]
    return [(READ, "Q11-Q20"), (TOOL, "Q01-Q10")]


def questions_in(questions: list[Question], part: str) -> list[Question]:
    a, b = (1, 10) if part == "Q01-Q10" else (11, 20)
    return [q for q in questions if a <= int(q.id[1:]) <= b]


def exam_seed() -> str:
    """LEGACYLENS_EXAM_SEED in .env (guide step 10.1) changes every paper; without it the draw is still per person."""
    return os.getenv("LEGACYLENS_EXAM_SEED", "legacylens")


def paper(bank: list[Question], person: str, seed: str | None = None) -> list[Question]:
    """The person's 20 questions as Q01-Q20, each from a different program, drawn at random but repeatable.

    Questions sharing a topic (the CICS transaction ID of a screen, asked for most screens) appear once at most.
    """
    parts(person)  # validates the number
    by_program: dict[str, list[Question]] = {}
    for q in bank:
        by_program.setdefault(q.program or q.id.rsplit("-", 1)[0], []).append(q)
    if len(by_program) < PER_PAPER:
        raise ValueError(f"the bank needs {PER_PAPER} programs, it has {len(by_program)}")
    rng = random.Random(f"{exam_seed() if seed is None else seed}:{int(person)}")
    picked, topics = [], set()
    for p in rng.sample(sorted(by_program), PER_PAPER):
        q = rng.choice([q for q in by_program[p] if q.topic is None or q.topic not in topics])
        topics.add(q.topic)
        picked.append(q)
    return [q.model_copy(update={"id": f"Q{i:02d}", "bank_id": q.id}) for i, q in enumerate(picked, 1)]


def paper_line(questions: list[Question]) -> str:
    """'Đề: Q01=COSGN00C-03 Q02=...', written into the answer file so grading never depends on the seed."""
    return "Đề: " + " ".join(f"{q.id}={q.bank_id}" for q in questions if q.bank_id)


def paper_from_text(text: str, bank: list[Question]) -> list[Question] | None:
    """The paper an answer file was written for, from its 'Đề:' line; None for files without one."""
    m = RE_PAPER.search(text[:2000])
    if not m:
        return None
    by_id = {q.id: q for q in bank}
    out = []
    for pair in m.group(1).split():
        qid, _, bid = pair.partition("=")
        if bid not in by_id:
            raise ValueError(f"{bid} is not in the question bank")
        out.append(by_id[bid].model_copy(update={"id": qid, "bank_id": bid}))
    return out


class Exam:
    def __init__(self, folder: str | Path = "onboarding"):
        self.folder = Path(folder)
        self.answers = self.folder / "tra_loi"
        self.log = self.folder / "bai_lam.csv"

    def _clock(self, person: str, method: str) -> Path:
        return self.answers / f".bat_dau_nguoi{person}_cach{method}"

    def done(self) -> list[dict]:
        if not self.log.exists():
            return []
        with self.log.open(encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def is_done(self, person: str, method: str) -> bool:
        return any(r["nguoi"] == person and r["cach"] == method for r in self.done())

    def _read_clock(self, person: str, method: str) -> tuple[float, int] | None:
        clock = self._clock(person, method)
        if not clock.exists():
            return None
        start, *rest = clock.read_text().split()
        return float(start), int(rest[0]) if rest else DEFAULT_MINUTES

    def started(self, person: str, method: str) -> float | None:
        clock = self._read_clock(person, method)
        return clock[0] if clock else None

    def minutes(self, person: str, method: str) -> int:
        """The countdown the tester chose when pressing Start."""
        clock = self._read_clock(person, method)
        return clock[1] if clock else DEFAULT_MINUTES

    def remaining(self, person: str, method: str, now: float | None = None) -> int | None:
        """Seconds left on the countdown; negative once time is up (the overrun is still measured)."""
        start = self.started(person, method)
        if start is None:
            return None
        return round(self.minutes(person, method) * 60 - ((time.time() if now is None else now) - start))

    def start(self, person: str, method: str, now: float | None = None, minutes: int = DEFAULT_MINUTES) -> float:
        """Start the clock once; pressing Start again (or reloading the page) keeps the first time."""
        if self.is_done(person, method):
            raise ValueError(f"person {person} already submitted the part '{METHOD_NAMES[method]}'")
        old = self.started(person, method)
        if old is not None:
            return old
        self.answers.mkdir(parents=True, exist_ok=True)
        t = time.time() if now is None else now
        if not 1 <= int(minutes) <= 180:
            raise ValueError("countdown must be 1-180 minutes")
        self._clock(person, method).write_text(f"{t} {int(minutes)}")
        return t

    def submit(
        self,
        person: str,
        method: str,
        part: str,
        answers: dict[str, str],
        now: float | None = None,
        questions: list[Question] | None = None,
    ) -> dict:
        started = self.started(person, method)
        if started is None:
            raise ValueError("press Start before submitting")
        if self.is_done(person, method):
            raise ValueError("this part was already submitted")
        seconds = round((time.time() if now is None else now) - started)
        name = f"nguoi{person}_cach{method}.txt"
        body = [f"Người {person}, {METHOD_NAMES[method]}, {part}, {seconds} giây"]
        if questions:
            body.append(paper_line(questions_in(questions, part)))
        body.append("")
        body += [f"{qid}: {text.strip()}" for qid, text in sorted(answers.items())]
        (self.answers / name).write_text("\n".join(body) + "\n", encoding="utf-8")
        row = {
            "nguoi": person,
            "cach": method,
            "cau": part,
            "giay": str(seconds),
            "file": f"tra_loi/{name}",
            "phut_dem_nguoc": str(self.minutes(person, method)),
        }
        new = not self.log.exists()
        fields = FIELDS
        if not new:  # a log written by an older version keeps its own columns
            with self.log.open(encoding="utf-8") as f:
                fields = next(csv.reader(f), FIELDS)
        with self.log.open("a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            if new:
                w.writeheader()
            w.writerow(row)
        self._clock(person, method).unlink()
        return row


def email_ready() -> bool:
    """Sending a copy is optional: it only works when SMTP_USER and SMTP_PASSWORD are set in .env."""
    import os

    return bool(os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"))


def send_copy(to: str, subject: str, body: str) -> tuple[bool, str]:
    """Mail the tester a copy of their answers. The address is used for this one mail only and never saved."""
    import os
    import re
    import smtplib
    from email.message import EmailMessage

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", to.strip()):
        return False, "Email không hợp lệ."
    if not email_ready():
        return False, "Chưa cấu hình gửi email (SMTP_USER, SMTP_PASSWORD trong .env)."
    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_FROM") or os.environ["SMTP_USER"]
    msg["To"] = to.strip()
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(
            os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "587")), timeout=20
        ) as s:
            s.starttls()
            s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            s.send_message(msg)
    except (OSError, smtplib.SMTPException) as exc:
        return False, f"Không gửi được email ({type(exc).__name__})."
    return True, f"Đã gửi bản sao tới {to.strip()}."


def summary(path: str | Path = "onboarding/ket_qua_bam_gio.csv") -> dict | None:
    """Graded results (guide step 10.3) per method: minutes per question and questions answered correctly.

    Returns None until both methods have at least one graded part, so the page never shows a one-sided comparison.
    `per_person` keeps each person's own pair; `paired` counts people graded both ways, `faster` and `better` how many
    of them were faster / got more right with LegacyLens.
    """
    path = Path(path)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out: dict = {}
    for method in (READ, TOOL):
        rs = [r for r in rows if r["cach"] == method]
        if not rs:
            return None
        asked = 10 * len(rs)
        out[method] = {
            "phut_moi_cau": round(sum(int(r["giay"]) for r in rs) / 60 / asked, 1),
            "dung": sum(int(r["dung"]) for r in rs),
            "tong": asked,
        }
    people: dict[str, dict] = {}
    for r in rows:
        people.setdefault(r["nguoi"], {})[r["cach"]] = {
            "phut_moi_cau": round(int(r["giay"]) / 600, 1),
            "dung": int(r["dung"]),
        }
    out["per_person"] = dict(sorted(people.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0))
    pairs = [p for p in people.values() if READ in p and TOOL in p]
    out["nguoi"] = len(people)
    out["paired"] = len(pairs)
    out["faster"] = sum(p[TOOL]["phut_moi_cau"] < p[READ]["phut_moi_cau"] for p in pairs)
    out["better"] = sum(p[TOOL]["dung"] > p[READ]["dung"] for p in pairs)
    return out


def report_markdown(s: dict) -> str:
    """reports/bai_kiem_tra.md: the comparison as GitHub-rendered Mermaid charts plus the per-person table."""
    read, tool = s[READ], s[TOOL]
    top_min = max(read["phut_moi_cau"], tool["phut_moi_cau"], 1) * 1.2
    pct = [round(100 * m["dung"] / m["tong"]) for m in (read, tool)]
    both = {k: p for k, p in s["per_person"].items() if READ in p and TOOL in p}  # a half-done person has no pair
    names = [f"Người {k}" for k in both]
    by = [[p[m]["phut_moi_cau"] for p in both.values()] for m in (READ, TOOL)]
    lines = [
        "# Bài kiểm tra onboarding với người thật",
        "",
        f"{s['nguoi']} người chưa từng đọc CardDemo. Mỗi người làm 10 câu khi chỉ đọc code và 10 câu khi dùng "
        "LegacyLens; người số lẻ và số chẵn đổi nửa câu hỏi cho nhau. Thời gian do giao diện tự bấm, số câu đúng do "
        "người chạy bài kiểm tra quyết định sau khi đọc gợi ý chấm của mô hình.",
        "",
        f"- Chỉ đọc code: {read['phut_moi_cau']} phút mỗi câu, đúng {read['dung']}/{read['tong']} ({pct[0]}%)",
        f"- Dùng LegacyLens: {tool['phut_moi_cau']} phút mỗi câu, đúng {tool['dung']}/{tool['tong']} ({pct[1]}%)",
        f"- Trong {s['paired']} người làm đủ hai cách: {s['faster']} người nhanh hơn, {s['better']} người đúng nhiều "
        "hơn khi dùng LegacyLens",
        "",
        "```mermaid",
        "xychart-beta",
        '    title "Phút mỗi câu (thấp hơn là tốt hơn)"',
        '    x-axis ["Chỉ đọc code", "Dùng LegacyLens"]',
        f'    y-axis "phút" 0 --> {top_min:.1f}',
        f"    bar [{read['phut_moi_cau']}, {tool['phut_moi_cau']}]",
        "```",
        "",
        "```mermaid",
        "xychart-beta",
        '    title "Tỉ lệ câu đúng (%)"',
        '    x-axis ["Chỉ đọc code", "Dùng LegacyLens"]',
        '    y-axis "%" 0 --> 100',
        f"    bar [{pct[0]}, {pct[1]}]",
        "```",
        "",
        "Từng người làm đủ hai cách, phút mỗi câu: cột là chỉ đọc code, đường là dùng LegacyLens.",
        "",
        "```mermaid",
        "xychart-beta",
        "    x-axis [" + ", ".join(f'"{n}"' for n in names) + "]",
        f'    y-axis "phút" 0 --> {max(by[0] + by[1] + [1]) * 1.2:.1f}',
        "    bar [" + ", ".join(map(str, by[0])) + "]",
        "    line [" + ", ".join(map(str, by[1])) + "]",
        "```",
        "",
        "| Người | Chỉ đọc code: phút/câu | Chỉ đọc code: đúng | LegacyLens: phút/câu | LegacyLens: đúng |",
        "| --- | --- | --- | --- | --- |",
    ]
    for k, p in s["per_person"].items():
        cell = [(f"{p[m]['phut_moi_cau']}", f"{p[m]['dung']}/10") if m in p else ("-", "-") for m in (READ, TOOL)]
        lines.append(f"| {k} | {cell[0][0]} | {cell[0][1]} | {cell[1][0]} | {cell[1][1]} |")
    return "\n".join(lines) + "\n"
