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
from legacylens.index import Index
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

tab_ask, tab_doc, tab_map = st.tabs(["💬 Hỏi đáp", "📄 Tài liệu thiết kế", "🗺️ Bản đồ chương trình"])

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
