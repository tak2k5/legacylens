"""Streamlit UI: pick a program, see its outline and rules, ask an onboarding question.

Run with `make ui` (needs .env for the Ask tab; the other tabs work offline).
"""

import json
import os
from pathlib import Path

import streamlit as st

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
    "Program", sorted(idx.programs), index=sorted(idx.programs).index("CBTRN02C") if "CBTRN02C" in idx.programs else 0
)
lang = st.sidebar.radio("Doc language", ["vi", "ja", "en"], horizontal=True)

tab_doc, tab_outline, tab_ask = st.tabs(["Design doc", "Outline", "Ask"])

rules = checks = None
rule_file = RULES / f"{program}.json"
if rule_file.exists():
    rules = RuleSet.model_validate_json(rule_file.read_text(encoding="utf-8"))
    checks = [verify(r, idx) for r in rules.rules]

with tab_doc:
    st.markdown(render(idx, program, rules, checks, lang=lang))

with tab_outline:
    st.code(Toolbox(idx).program_outline(program), language="text")
    impact = idx.impact(program)
    st.write(f"Changing {program} may affect {len(impact)} programs:", ", ".join(impact) or "none")

with tab_ask:
    question = st.text_input("Question", "Why would a daily transaction be rejected in the posting job?")
    if st.button("Ask") and question:
        from legacylens.agent import Agent

        try:
            with st.spinner("Reading the code..."):
                answer, cite_checks, trace = Agent(idx).ask(question)
        except Exception as exc:  # missing key, rate limit, model gave no JSON
            st.error(f"{type(exc).__name__}: {str(exc)[:400]}")
            st.stop()
        st.markdown(answer.answer)
        tb = Toolbox(idx)
        for c, chk in zip(answer.citations, cite_checks, strict=True):
            label = f"{c.program}:{c.start_line}-{c.end_line} · {'ok' if chk['valid'] else 'FAILED'}"
            with st.expander(label):
                st.code(tb.read_lines(c.program, c.start_line, c.end_line), language="cobol")
        st.caption(json.dumps({k: v for k, v in trace.as_dict().items() if k != "calls"}))
