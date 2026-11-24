"""Streamlit UI: ask a question about CardDemo, read a program's design document, see its outline.

Run with `make ui` (needs .env for the question tab; the other tabs work offline).
"""

import json
import os
from pathlib import Path

import streamlit as st

from legacylens.aliases import expand, label, sample_questions
from legacylens.citations import verify
from legacylens.docgen import CARDDEMO_LINK, render
from legacylens.exam import (
    BANK,
    DEFAULT_MINUTES,
    MAX_PEOPLE,
    METHOD_NAMES,
    READ,
    TOOL,
    Exam,
    email_ready,
    paper,
    paper_from_text,
    parts,
    questions_in,
    send_copy,
    summary,
)
from legacylens.index import Index
from legacylens.qa import load_questions
from legacylens.schema import RuleSet
from legacylens.tools import Toolbox

SRC = os.getenv("LEGACYLENS_SRC", "data/carddemo/app")
RULES = Path(os.getenv("LEGACYLENS_RULES", "out/rules"))
SAMPLES = Path("onboarding/CAU_HOI_MAU.md")
ASK_MODE = os.getenv("LEGACYLENS_ASK_MODE", "guided")

st.set_page_config(page_title="LegacyLens", page_icon="🔎", layout="wide")


@st.cache_resource
def load_index(src: str) -> Index:
    return Index.build(src)


@st.cache_data
def catalogue(src: str) -> dict[str, str]:
    """Program id -> what its header says it does."""
    out = {}
    for line in Toolbox(load_index(src)).program_catalogue().splitlines():
        name, _, what = line.partition(": ")
        out[name.split(" ")[0]] = what
    return out


@st.cache_data
def source_text(src: str, program: str) -> tuple[str, str, int]:
    """(file name, full source, line count) for the code shown under a test question."""
    path = Path(load_index(src).program(program).path)
    text = path.read_text(encoding="utf-8", errors="replace")
    return path.name, text, text.count("\n") + 1


def question_context(q) -> None:
    """Under a test question: which program it is about, what its header says, and the whole source."""
    if not q.program:
        return
    p = idx.program(q.program)
    name, text, n = source_text(SRC, q.program)
    kind = "chạy theo lô (batch)" if p.kind == "batch" else "màn hình CICS (online)"
    what = catalogue(SRC).get(q.program, "-")
    note = f" Ghi chú đầu file: _{what}_" if what != "-" else ""
    st.caption(f"Chương trình **{q.program}**, {kind}, file {name}, {n} dòng.{note}")
    with st.expander(f"Xem toàn bộ mã nguồn {name}"):
        st.code(text, language="cobol", line_numbers=True, height=420)


def github_link(program: str, start: int, end: int) -> str:
    p = idx.program(program)
    rel = Path(p.path).resolve().relative_to(idx.root.resolve()).as_posix()
    return f"{CARDDEMO_LINK}{rel}#L{start}-L{end}"


idx = load_index(SRC)
tb = Toolbox(idx)
programs = sorted(idx.programs)
st.session_state.setdefault("question", "")
st.session_state.setdefault("history", [])

# ---------------------------------------------------------------- sidebar: one program for the doc and map tabs
st.sidebar.title("🔎 LegacyLens")
st.sidebar.caption("Đọc hiểu COBOL của AWS CardDemo, mọi câu trả lời kèm dòng code.")
program = st.sidebar.selectbox(
    "Chương trình",
    programs,
    index=programs.index("CBTRN02C") if "CBTRN02C" in programs else 0,
    format_func=label,
    help="Gõ mã (COBIL00C) hoặc tên tiếng Việt (thanh-toan) để lọc.",
)
what = catalogue(SRC).get(program, "")
if what and what != "-":
    st.sidebar.info(f"**{program}** làm gì (theo chú thích đầu file): {what}")
stats = idx.stats()
st.sidebar.caption(
    f"{stats['programs']} chương trình · {stats['copybooks']} copybook · {stats['jcl_steps']} bước JCL · "
    f"{stats['loc']:,} dòng code"
)
st.sidebar.caption("🌗 Giao diện sáng/tối: bấm ⋮ ở góc trên bên phải → Settings → chọn Light, Dark hoặc theo máy.")

tab_ask, tab_doc, tab_map, tab_exam = st.tabs(
    ["💬 Hỏi đáp", "📄 Tài liệu thiết kế", "🗺️ Bản đồ chương trình", "📝 Bài kiểm tra"]
)

# ---------------------------------------------------------------- ask
with tab_ask:
    st.subheader("Hỏi về code")
    st.caption(
        "Hỏi bằng tiếng Anh cho kết quả tốt nhất. Có thể gõ tên tiếng Việt thay cho mã chương trình, ví dụ "
        "`What does thanh-toan-hoa-don do?`. Mỗi câu mất khoảng 30 giây đến 2 phút."
    )
    samples = sample_questions(program, SAMPLES.read_text(encoding="utf-8") if SAMPLES.exists() else "")

    def use_sample(key: str) -> None:
        if st.session_state[key]:
            st.session_state["question"] = st.session_state[key]

    st.selectbox(
        f"Chọn câu hỏi gợi ý cho {label(program)}, hoặc tự gõ ở ô dưới",
        [""] + samples,
        key=f"sample-{program}",
        on_change=use_sample,
        args=(f"sample-{program}",),
        format_func=lambda q: q or "(chọn một câu)",
    )
    with st.form("ask"):
        question = st.text_area(
            "Câu hỏi", key="question", height=80, placeholder="Ví dụ: Which program checks the password?"
        )
        c1, c2 = st.columns([1, 3])
        asked_now = c1.form_submit_button("Hỏi", type="primary", use_container_width=True)
        add_vi = c2.checkbox("Thêm bản tiếng Việt (chậm thêm 10-30 giây)", value=True)

    if asked_now and question.strip():
        from legacylens.agent import Agent

        try:
            with st.spinner("Đang đọc code..."):
                agent = Agent(idx)
                answer, cite_checks, trace = agent.ask(expand(question), mode=ASK_MODE)
            vi = None
            if add_vi:
                with st.spinner("Đang dịch sang tiếng Việt..."):
                    vi = agent.translate_answer(answer.answer, "vi")
        except Exception as exc:  # no .env, Colab stopped, model gave no JSON
            msg = str(exc)
            if "Connection" in type(exc).__name__ or "530" in msg or "1033" in msg:
                st.error("Không gọi được mô hình: Colab đã ngắt. Làm bước 6.2 trong hướng dẫn rồi hỏi lại.")
            else:
                st.error(f"{type(exc).__name__}: {msg[:400]}")
            st.stop()
        st.session_state["history"].insert(
            0,
            {
                "question": question.strip(),
                "answer": answer.answer,
                "vi": vi,
                "citations": [
                    {
                        "program": c.program,
                        "start": c.start_line,
                        "end": c.end_line,
                        "ok": chk["valid"],
                        "problems": chk["problems"],
                    }
                    for c, chk in zip(answer.citations, cite_checks, strict=True)
                ],
                "trace": {k: v for k, v in trace.as_dict().items() if k != "calls"},
            },
        )

    for n, item in enumerate(st.session_state["history"]):
        if n == 1:
            st.markdown("#### Các câu đã hỏi trước")
        with st.container(border=True):
            st.markdown(f"**❓ {item['question']}**")
            st.markdown(item["answer"])
            if item["vi"]:
                st.markdown(f"🇻🇳 {item['vi']}")
            elif n == 0 and add_vi and item["vi"] is None:
                st.caption("Chưa dịch được sang tiếng Việt, đọc bản tiếng Anh ở trên.")
            cits = sorted(item["citations"], key=lambda c: not c["ok"])  # verified ones first
            good = sum(c["ok"] for c in cits)
            if cits:
                st.caption(
                    f"Trích dẫn: {good}/{len(cits)} qua kiểm tra tự động. Chỉ tin các trích dẫn ✅, mở ra để xem code."
                )
            else:
                st.caption("Không có trích dẫn: tự kiểm tra lại trong code trước khi tin câu trả lời.")
            for i, c in enumerate(cits):
                head = f"{label(c['program'])} · dòng {c['start']}-{c['end']}"
                if c["ok"]:
                    with st.expander(f"✅ {head}", expanded=(n == 0 and i == 0)):
                        st.code(tb.read_lines(c["program"], c["start"], c["end"]), language="cobol")
                        st.markdown(f"[Mở trên GitHub]({github_link(c['program'], c['start'], c['end'])})")
                else:
                    with st.expander(f"⚠️ {head} · không qua kiểm tra"):
                        st.warning("Lý do: " + "; ".join(c["problems"]))
                        st.code(tb.read_lines(c["program"], c["start"], c["end"]), language="cobol")
            t = item["trace"]
            st.caption(f"{t.get('tool_calls', 0)} lần đọc code · {t.get('seconds', 0)} giây")
    if st.session_state["history"]:
        with st.expander("Chi tiết kỹ thuật của câu mới nhất"):
            st.code(json.dumps(st.session_state["history"][0]["trace"], indent=1), language="json")
        if st.button("Xóa các câu đã hỏi"):
            st.session_state["history"] = []
            st.rerun()

# ---------------------------------------------------------------- design document
with tab_doc:
    lang = st.radio(
        "Ngôn ngữ tài liệu",
        ["vi", "ja", "en"],
        horizontal=True,
        format_func={"vi": "Tiếng Việt", "ja": "日本語", "en": "English"}.get,
    )
    rules = checks = None
    rule_file = RULES / f"{program}.json"
    if rule_file.exists():
        rules = RuleSet.model_validate_json(rule_file.read_text(encoding="utf-8"))
        checks = [verify(r, idx) for r in rules.rules]
    else:
        st.info(f"{program} chưa có rule trích bằng mô hình. Tài liệu chỉ có phần phân tích tĩnh.")
    shown = rules
    cached = RULES.with_name(f"{RULES.name}_{lang}") / f"{program}.json"  # written by make doc ARGS=--translate
    if rules and lang != "en" and cached.exists():
        shown = RuleSet.model_validate(json.loads(cached.read_text(encoding="utf-8"))["rules"])
    st.markdown(render(idx, program, shown, checks, lang=lang, link_base=CARDDEMO_LINK))

# ---------------------------------------------------------------- program map
with tab_map:
    st.subheader(label(program))
    st.caption(
        "Phân tích tĩnh, không dùng mô hình: file đọc và ghi, chương trình được chuyển tới, copybook, và các đoạn "
        "(paragraph) kèm số dòng. Xem ở đây trước để biết nên mở dòng nào."
    )
    impact = idx.impact(program)
    st.metric("Sửa chương trình này có thể ảnh hưởng tới", f"{len(impact)} chương trình")
    if impact:
        st.write(", ".join(label(p) for p in impact))
    st.code(tb.program_outline(program), language="text")


# ---------------------------------------------------------------- timed test for a new developer (guide step 10)
@st.fragment(run_every=1)
def countdown(exam: Exam, person: str, method: str) -> None:
    """Live countdown, redrawn every second on its own so the answers being typed are not touched."""
    left = exam.remaining(person, method)
    if left is None:
        return
    total = exam.minutes(person, method) * 60
    if left >= 0:
        st.markdown(f"### ⏳ Còn {left // 60:02d}:{left % 60:02d}")
        st.progress(left / total)
        if left <= 120:
            st.warning("Sắp hết giờ, nhớ bấm Nộp ở cuối trang.")
    else:
        over = -left
        st.error(
            f"### ⏰ Hết giờ, quá {over // 60:02d}:{over % 60:02d}\n"
            "Bạn vẫn nộp được, câu trả lời không bị mất. Thời gian thật vẫn được ghi lại."
        )


with tab_exam:
    exam = Exam("onboarding")
    st.subheader("Bài kiểm tra onboarding")
    st.markdown(
        "Bài này đo xem LegacyLens giúp người mới hiểu code nhanh hơn bao nhiêu. Có **2 phần, mỗi phần 10 câu**. "
        "Đồng hồ chạy từ lúc bấm **Bắt đầu** tới lúc bấm **Nộp**, nên hãy làm liền một mạch. Trả lời ngắn, bằng "
        "tiếng Việt hay tiếng Anh đều được. Không biết thì ghi đoán của bạn hoặc bỏ trống."
    )
    person = str(
        st.number_input(
            "Số thứ tự của bạn",
            min_value=1,
            max_value=MAX_PEOPLE,
            value=1,
            step=1,
            key="exam-person",
            help="Người mời bạn làm bài gửi kèm số này. Mỗi người một số, đừng dùng số của người khác.",
        )
    )
    email = st.text_input(
        "Email của bạn (không bắt buộc)",
        key="exam-email",
        placeholder="ten@gmail.com",
        help="Chỉ dùng để gửi bản sao bài làm cho bạn, không được lưu lại.",
        disabled=not email_ready(),
    )
    if not email_ready():
        st.caption("Gửi email chưa bật trên máy này. Sau khi nộp, bạn vẫn tải được bài làm về máy.")
    bank = load_questions(BANK)
    questions = paper(bank, person)  # 20 questions, one per program, the same on every reload
    order = parts(person)
    if all(exam.is_done(person, m) for m, _ in order):
        st.success(
            "Bạn đã xong cả hai phần, cảm ơn bạn! Giờ bạn có thể hỏi agent thoải mái ở mục 💬 Hỏi đáp, ví dụ về những "
            "câu bạn chưa chắc."
        )
    for k, (method, part) in enumerate(order, 1):
        with st.container(border=True):
            st.markdown(f"#### Phần {k}: {METHOD_NAMES[method]} ({part})")
            if exam.is_done(person, method):
                row = next(r for r in exam.done() if r["nguoi"] == person and r["cach"] == method)
                st.success(f"Đã nộp, {int(row['giay']) // 60} phút {int(row['giay']) % 60} giây. Cảm ơn bạn!")
                copy = Path("onboarding") / row["file"]
                if copy.exists():
                    st.download_button(
                        "Tải bài làm về máy",
                        copy.read_text(encoding="utf-8"),
                        file_name=copy.name,
                        key=f"dl-{copy.name}",
                    )
                note = st.session_state.get(f"mail-{person}-{method}")
                if note:
                    (st.info if note[0] else st.warning)(note[1])
                continue
            if k == 2 and not exam.is_done(person, order[0][0]):
                st.caption("Làm xong phần 1 rồi mới tới phần này.")
                continue
            if method == READ:
                st.info(
                    "Chỉ đọc code: mở **Xem toàn bộ mã nguồn** dưới mỗi câu và tìm bằng Ctrl+F, hoặc đọc trên GitHub "
                    f"([mã nguồn CardDemo]({CARDDEMO_LINK})). **Không** dùng mục Hỏi đáp, Tài liệu hay Bản đồ."
                )
            else:
                st.info(
                    "Dùng LegacyLens: hỏi ở mục 💬 Hỏi đáp, xem 📄 Tài liệu và 🗺️ Bản đồ. Mỗi câu hỏi mất 30 giây đến "
                    "2 phút. Mở trích dẫn ✅ để kiểm tra trước khi ghi câu trả lời."
                )
            started = exam.started(person, method)
            if started is None:
                minutes = st.number_input(
                    "Đếm ngược (phút)",
                    min_value=1,
                    max_value=180,
                    value=DEFAULT_MINUTES,
                    step=5,
                    key=f"min-{person}-{method}",
                    help="Hết giờ thì trang báo đỏ nhưng không khóa bài, thời gian thật vẫn được ghi.",
                )
                if st.button(f"Bắt đầu phần {k}", key=f"start-{person}-{method}", type="primary"):
                    exam.start(person, method, minutes=int(minutes))
                    st.rerun()
                continue
            countdown(exam, person, method)
            st.caption("Đừng tải lại trang: câu trả lời đã gõ sẽ mất (đồng hồ thì không mất).")
            with st.form(f"exam-{person}-{method}"):
                answers = {}
                for q in questions_in(questions, part):
                    st.markdown(f"**{q.id}. {q.question}**")
                    question_context(q)
                    answers[q.id] = st.text_area(
                        f"Trả lời {q.id}",
                        key=f"ans-{person}-{method}-{q.id}",
                        height=70,
                        label_visibility="collapsed",
                        placeholder=f"Câu trả lời {q.id}",
                    )
                if st.form_submit_button(f"Nộp phần {k}", type="primary"):
                    row = exam.submit(person, method, part, answers, questions=questions)
                    if email.strip():  # optional copy for the tester; the address is not stored anywhere
                        body = (Path("onboarding") / row["file"]).read_text(encoding="utf-8")
                        st.session_state[f"mail-{person}-{method}"] = send_copy(
                            email, f"LegacyLens: bài làm phần {k} ({METHOD_NAMES[method]})", body
                        )
                    st.rerun()

    result = summary("onboarding/ket_qua_bam_gio.csv")
    with st.expander("📊 Kết quả: không có agent và có agent", expanded=result is not None):
        if result is None:
            st.caption(
                "Chưa có. Kết quả hiện ở đây sau khi người chạy bài kiểm tra chấm xong ít nhất một phần mỗi cách "
                "(bước 10.3 trong hướng dẫn)."
            )
        else:
            import pandas as pd

            read, tool = result[READ], result[TOOL]
            pct = {m: round(100 * result[m]["dung"] / result[m]["tong"]) for m in (READ, TOOL)}
            c1, c2 = st.columns(2)
            c1.metric("Chỉ đọc code: phút mỗi câu", read["phut_moi_cau"])
            c2.metric(
                "Dùng LegacyLens: phút mỗi câu",
                tool["phut_moi_cau"],
                delta=round(tool["phut_moi_cau"] - read["phut_moi_cau"], 1),
                delta_color="inverse",
            )
            c1.metric("Chỉ đọc code: câu đúng", f"{pct[READ]}% ({read['dung']}/{read['tong']})")
            c2.metric(
                "Dùng LegacyLens: câu đúng",
                f"{pct[TOOL]}% ({tool['dung']}/{tool['tong']})",
                delta=f"{pct[TOOL] - pct[READ]:+d} điểm %",
            )
            names = [METHOD_NAMES[READ], METHOD_NAMES[TOOL]]
            g1, g2 = st.columns(2)
            g1.caption("Phút mỗi câu (thấp hơn là tốt hơn)")
            g1.bar_chart(
                pd.DataFrame({"cách": names, "phút mỗi câu": [read["phut_moi_cau"], tool["phut_moi_cau"]]}),
                x="cách",
                y="phút mỗi câu",
                horizontal=True,
                height=200,
            )
            g2.caption("Tỉ lệ câu đúng (%)")
            g2.bar_chart(
                pd.DataFrame({"cách": names, "% đúng": [pct[READ], pct[TOOL]]}),
                x="cách",
                y="% đúng",
                horizontal=True,
                height=200,
            )
            both = {k: p for k, p in result["per_person"].items() if READ in p and TOOL in p}
            if both:
                st.caption("Từng người làm đủ hai cách: phút mỗi câu")
                st.bar_chart(
                    pd.DataFrame(
                        {
                            "người": [f"Người {k}" for k in both],
                            names[0]: [p[READ]["phut_moi_cau"] for p in both.values()],
                            names[1]: [p[TOOL]["phut_moi_cau"] for p in both.values()],
                        }
                    ),
                    x="người",
                    y=names,
                    stack=False,
                    horizontal=True,
                    x_label="",
                    y_label="phút mỗi câu",
                    height=max(200, 45 * len(both)),
                )
            st.caption(
                f"{result['nguoi']} người, {result['paired']} người làm đủ hai cách: {result['faster']} người nhanh "
                f"hơn, {result['better']} người đúng nhiều hơn khi dùng LegacyLens. Mỗi người một đề ngẫu nhiên từ ngân "
                "hàng 240 câu, mỗi câu về một chương trình khác nhau. Số câu đúng do người chạy bài kiểm tra quyết định, mô hình chỉ gợi ý."
            )
    with st.expander("📤 Chấm file câu trả lời (chỉ người chạy bài kiểm tra)"):
        pin = os.getenv("LEGACYLENS_GRADE_PIN", "")
        if not pin:
            st.caption("Chưa có mã chấm bài trên máy này. Chạy lại khối 10.1 trong hướng dẫn để tạo mã.")
        elif st.text_input("Mã chấm bài", type="password", key="grade-pin") != pin:
            st.caption(
                "Nhập mã chấm bài mà khối 10.1 in ra. Mã giữ cho người làm bài không xem được lý do chấm, "
                "vì lý do chấm để lộ đáp án."
            )
        else:
            from legacylens.grade import grade_text, guess_part, is_sample

            for up in st.file_uploader(
                "File câu trả lời (.txt hoặc .md, mỗi câu một dòng dạng Q01: ...). File mẫu cũng chấm được.",
                type=["txt", "md"],
                accept_multiple_files=True,
                key="grade-files",
            ):
                text = up.getvalue().decode("utf-8", errors="replace")
                sample = is_sample(text)
                with st.container(border=True):
                    st.markdown(f"**{up.name}**" + (" · file mẫu" if sample else ""))
                    halves = ["Q01-Q10", "Q11-Q20"]
                    part = st.radio(
                        "Phần", halves, index=halves.index(guess_part(text)), horizontal=True, key=f"gp-{up.name}"
                    )
                    key = f"graded-{up.name}-{part}"
                    if st.button("Chấm bằng mô hình (vài phút)", key=f"gb-{up.name}"):
                        from legacylens.agent import Agent

                        try:
                            with st.spinner("Mô hình đang chấm 10 câu..."):
                                drawn = paper_from_text(text, bank) or load_questions("onboarding/questions.jsonl")
                                st.session_state[key] = grade_text(Agent(idx), drawn, text, up.name, part)
                        except Exception as exc:  # Colab stopped or no .env
                            st.error(f"Không gọi được mô hình ({type(exc).__name__}). Làm bước 6.2 rồi chấm lại.")
                    if key in st.session_state:
                        model_ok, kw_ok, report = st.session_state[key]
                        st.markdown(report.split("\n", 1)[1])  # drop the "# Chấm ..." title, the box names the file
                        st.download_button(
                            "Tải bảng chấm", report, file_name=Path(up.name).stem + ".cham.md", key=f"gd-{key}"
                        )
                        if sample:
                            st.warning("File mẫu: chỉ để thử cách chấm. Không ghi vào kết quả, không đưa vào CV.")
                        else:
                            st.info(
                                "Mô hình chỉ gợi ý. Muốn ghi vào kết quả: bấm lưu dưới đây rồi làm bước 10.3b, "
                                "bạn đọc lý do và tự quyết số câu đúng."
                            )
                            if st.button("Lưu file vào onboarding/tra_loi", key=f"gs-{key}"):
                                dest = Path("onboarding/tra_loi") / Path(up.name).name
                                dest.parent.mkdir(parents=True, exist_ok=True)
                                dest.write_text(text, encoding="utf-8")
                                st.success(f"Đã lưu {dest}. Ở bước 10.3b gõ tên file: {dest.name}")
