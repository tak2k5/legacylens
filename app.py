"""Streamlit UI: pick a program, see its outline and rules, ask an onboarding question.

Run with `make ui` (needs .env for the Ask tab; the other tabs work offline).
"""

import json
import os
from pathlib import Path

import streamlit as st

from legacylens.aliases import expand, label
from legacylens.citations import verify
from legacylens.docgen import render
from legacylens.index import Index
from legacylens.schema import RuleSet
from legacylens.tools import Toolbox

SRC = os.getenv("LEGACYLENS_SRC", "data/carddemo/app")
RULES = Path(os.getenv("LEGACYLENS_RULES", "out/rules"))

st.set_page_config(page_title="LegacyLens", layout="wide")


@st.cache_resource
def load_index(src: str) -> Index:
    return Index.build(src)


idx = load_index(SRC)
stats = idx.stats()
st.sidebar.title("LegacyLens")
st.sidebar.caption(
    f"{stats['programs']} programs · {stats['copybooks']} copybooks · {stats['jcl_steps']} JCL steps · {stats['loc']:,} LOC"
)
program = st.sidebar.selectbox(
    "Program (gõ mã hoặc tên tiếng Việt để tìm)",
    sorted(idx.programs),
    index=sorted(idx.programs).index("CBTRN02C") if "CBTRN02C" in idx.programs else 0,
    format_func=label,
)
lang = st.sidebar.radio("Doc language", ["vi", "ja", "en"], horizontal=True)

tab_doc, tab_outline, tab_ask = st.tabs(["Design doc", "Outline", "Ask"])

rules = checks = None
rule_file = RULES / f"{program}.json"
if rule_file.exists():
    rules = RuleSet.model_validate_json(rule_file.read_text(encoding="utf-8"))
    checks = [verify(r, idx) for r in rules.rules]

with tab_doc:
    shown = rules
    cached = RULES.with_name(f"{RULES.name}_{lang}") / f"{program}.json"  # written by make doc ARGS=--translate
    if rules and lang != "en" and cached.exists():
        shown = RuleSet.model_validate(json.loads(cached.read_text(encoding="utf-8"))["rules"])
    st.markdown(render(idx, program, shown, checks, lang=lang))

with tab_outline:
    st.code(Toolbox(idx).program_outline(program), language="text")
    impact = idx.impact(program)
    st.write(f"Changing {program} may affect {len(impact)} programs:", ", ".join(impact) or "none")

with tab_ask:
    question = st.text_input("Question", "Why would a daily transaction be rejected in the posting job?")
    st.caption(
        "Có thể gõ tên tiếng Việt thay cho mã, ví dụ: What does thanh-toan-hoa-don do? Danh sách tên ở thanh bên."
    )
    add_vi = st.checkbox("Thêm bản tiếng Việt", value=True)
    if st.button("Ask") and question:
        from legacylens.agent import Agent

        try:
            with st.spinner("Reading the code..."):
                asked = expand(question)  # "thanh-toan-hoa-don" -> "COBIL00C (thanh-toan-hoa-don)"
                answer, cite_checks, trace = Agent(idx).ask(asked, mode=os.getenv("LEGACYLENS_ASK_MODE", "guided"))
        except Exception as exc:  # missing key, rate limit, model gave no JSON
            st.error(f"{type(exc).__name__}: {str(exc)[:400]}")
            st.stop()
        st.markdown(answer.answer)
        if add_vi:
            with st.spinner("Đang dịch sang tiếng Việt..."):
                vi = Agent(idx).translate_answer(answer.answer, "vi")
            st.markdown(f"**Tiếng Việt:** {vi}" if vi else "_Chưa dịch được, đọc bản tiếng Anh ở trên._")
        tb = Toolbox(idx)
        for c, chk in zip(answer.citations, cite_checks, strict=True):
            status = "ok" if chk["valid"] else "FAILED: " + "; ".join(chk["problems"])
            label = f"{c.program}:{c.start_line}-{c.end_line} · {status}"
            with st.expander(label):
                st.code(tb.read_lines(c.program, c.start_line, c.end_line), language="cobol")
        st.caption(json.dumps({k: v for k, v in trace.as_dict().items() if k != "calls"}))
