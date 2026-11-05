"""Agent loop, citation check, scoring and doc rendering, with a scripted fake LLM (no network)."""

import json
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from legacylens.agent import Agent, LoopGuard, llm_settings
from legacylens.citations import verify
from legacylens.cli import main
from legacylens.docgen import render
from legacylens.evaluate import load_rules, score, to_markdown
from legacylens.index import Index
from legacylens.schema import BusinessRule, Citation, RuleSet

FIX = Path(__file__).parent / "fixtures"

RULE = {
    "id": "PAYCHK-R1",
    "program": "PAYCHK",
    "paragraph": "1000-CHECK-AMOUNT",
    "kind": "validation",
    "summary": "Payments above 5000 are flagged.",
    "condition": "PAY-AMT > 5000",
    "outcome": "WS-REASON = 200, 'AMOUNT OVER LIMIT'",
    "fields": ["PAY-AMT", "WS-REASON"],
    "citations": [{"program": "PAYCHK", "start_line": 27, "end_line": 30}],
}


def tool_msg(name, args, call_id="c1"):
    fn = NS(name=name, arguments=json.dumps(args))
    return NS(
        choices=[NS(message=NS(content=None, tool_calls=[NS(id=call_id, function=fn)]))],
        usage=NS(prompt_tokens=100, completion_tokens=10),
    )


def text_msg(text):
    return NS(choices=[NS(message=NS(content=text, tool_calls=None))], usage=NS(prompt_tokens=50, completion_tokens=40))


class FakeClient:
    def __init__(self, script):
        self.script = list(script)
        self.requests = []
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(json.loads(json.dumps(kwargs["messages"], default=str)))
        return self.script.pop(0)


@pytest.fixture(scope="module")
def idx():
    return Index.build(FIX)


def test_agent_extracts_rules_and_blocks_repeated_calls(idx):
    final = {"program": "PAYCHK", "purpose": "Checks payments.", "rules": [RULE]}
    client = FakeClient(
        [
            tool_msg("read_paragraph", {"program": "PAYCHK", "paragraph": "1000-CHECK-AMOUNT"}, "c1"),
            tool_msg("read_paragraph", {"paragraph": "1000-CHECK-AMOUNT", "program": "PAYCHK"}, "c2"),  # same call
            text_msg("```json\n" + json.dumps(final) + "\n```"),
        ]
    )
    rules, checks, trace = Agent(idx, client=client, model="fake").extract_rules("PAYCHK", lang="vi")
    assert rules.rules[0].id == "PAYCHK-R1"
    assert checks[0]["valid"] and "5000" in checks[0]["evidence"]
    assert (trace.steps, trace.tool_calls, trace.blocked_repeats) == (3, 2, 1)
    assert trace.prompt_tokens == 250 and trace.completion_tokens == 60
    assert "Vietnamese" in client.requests[0][1]["content"]
    tool_results = [m["content"] for m in client.requests[2] if m["role"] == "tool"]
    assert "5000" in tool_results[0] and tool_results[1].startswith("BLOCKED")


def test_agent_repairs_invalid_json(idx):
    bad = {"program": "PAYCHK", "purpose": "x", "rules": [{**RULE, "citations": []}]}
    good = {"program": "PAYCHK", "purpose": "x", "rules": [RULE]}
    client = FakeClient([text_msg(json.dumps(bad)), text_msg(json.dumps(good))])
    rules, _, trace = Agent(idx, client=client, model="fake").extract_rules("PAYCHK")
    assert trace.repairs == 1 and len(rules.rules) == 1
    assert "invalid" in client.requests[1][-1]["content"]


def test_agent_gives_up_after_budget(idx):
    client = FakeClient([tool_msg("search_code", {"pattern": f"X{i}"}, f"c{i}") for i in range(3)])
    with pytest.raises(RuntimeError):
        Agent(idx, client=client, model="fake", max_steps=3).extract_rules("PAYCHK")


def test_ask_checks_citations(idx):
    ans = {
        "answer": "PAYCHK calls PAYPOST.",
        "citations": [
            {"program": "PAYCHK", "start_line": 23, "end_line": 23},
            {"program": "PAYCHK", "start_line": 900, "end_line": 901},
        ],
    }
    answer, checks, _ = Agent(idx, client=FakeClient([text_msg(json.dumps(ans))]), model="fake").ask("who?")
    assert [c["valid"] for c in checks] == [True, False]


def test_loop_guard_normalises_argument_order():
    g = LoopGuard()
    assert g.check("t", '{"a": 1, "b": 2}') is None
    assert g.check("t", '{"b": 2, "a": 1}').startswith("BLOCKED")


def test_citation_check_catches_wrong_lines(idx):
    good = BusinessRule.model_validate(RULE)
    assert verify(good, idx)["valid"]
    wrong = BusinessRule.model_validate({**RULE, "citations": [{"program": "PAYCHK", "start_line": 1, "end_line": 3}]})
    assert "none of the rule" in verify(wrong, idx)["problems"][0]
    past = BusinessRule.model_validate(
        {**RULE, "citations": [{"program": "PAYCHK", "start_line": 30, "end_line": 400}]}
    )
    problems = " ".join(verify(past, idx)["problems"])
    assert "past the end" in problems and "wider than" in problems
    assert not verify(Citation(program="NOPE", start_line=1, end_line=1), idx)["valid"]
    with pytest.raises(ValueError):
        Citation(program="PAYCHK", start_line=5, end_line=4)


def test_scoring_is_one_to_one_and_rejects_wide_citations():
    gold = [
        BusinessRule.model_validate(RULE),
        BusinessRule.model_validate(
            {**RULE, "id": "G2", "citations": [{"program": "PAYCHK", "start_line": 33, "end_line": 34}]}
        ),
    ]
    exact = BusinessRule.model_validate({**RULE, "id": "P1"})
    dup = BusinessRule.model_validate({**RULE, "id": "P2"})
    wide = BusinessRule.model_validate(
        {**RULE, "id": "P3", "citations": [{"program": "PAYCHK", "start_line": 1, "end_line": 36}]}
    )
    other = BusinessRule.model_validate(
        {**RULE, "id": "P4", "program": "MENU01", "citations": [{"program": "MENU01", "start_line": 9, "end_line": 12}]}
    )
    r = score(gold, [exact, dup, wide, other])
    assert r["programs"] == ["PAYCHK"] and r["predicted"] == 3  # MENU01 has no gold, not scored
    assert r["matched"] == 1 and r["precision"] == pytest.approx(1 / 3, abs=1e-3) and r["recall"] == 0.5
    assert r["missed"] == ["G2"] and set(r["extra"]) == {"P2", "P3"}
    assert "| Recall | 50.0% |" in to_markdown(r, 0.5)


def test_load_rules_formats(tmp_path):
    (tmp_path / "rules").mkdir()
    rs = RuleSet(program="PAYCHK", purpose="x", rules=[BusinessRule.model_validate(RULE)])
    (tmp_path / "rules/PAYCHK.json").write_text(rs.model_dump_json())
    (tmp_path / "rules/PAYCHK.check.json").write_text("[]")
    (tmp_path / "g.jsonl").write_text(json.dumps(RULE) + "\n\n")
    assert len(load_rules(tmp_path / "rules")) == 1 and len(load_rules(tmp_path / "g.jsonl")) == 1


@pytest.mark.parametrize("lang,heading", [("vi", "Quy tắc nghiệp vụ"), ("en", "Business rules"), ("ja", "業務ルール")])
def test_docgen(idx, lang, heading):
    rs = RuleSet(program="PAYCHK", purpose="Checks payments.", rules=[BusinessRule.model_validate(RULE)])
    md = render(idx, "PAYCHK", rs, [verify(r, idx) for r in rs.rules], lang=lang, link_base="src/")
    assert heading in md and "src/cbl/PAYCHK.cbl#L27-L30" in md and "PROD.PAY.DAILY" in md
    assert "```mermaid" in md and "PAYJOB" in md
    assert "Chưa trích xuất" in render(idx, "PAYCHK", lang="vi")


def test_cli_offline_commands(tmp_path, capsys):
    gold = tmp_path / "gold.jsonl"
    gold.write_text(json.dumps(RULE) + "\n")
    rules = tmp_path / "rules"
    rules.mkdir()
    (rules / "PAYCHK.json").write_text(json.dumps({"program": "PAYCHK", "purpose": "x", "rules": [RULE]}))
    src = ["--src", str(FIX)]
    main(src + ["stats"])
    main(src + ["graph", "--out", str(tmp_path / "rep")])
    main(src + ["doc", "ALL", "--rules", str(rules), "--out", str(tmp_path / "docs"), "--lang", "ja"])
    with pytest.raises(SystemExit) as e:
        main(src + ["check-gold", "--gold", str(gold)])
    assert e.value.code == 0
    main(src + ["eval", "--gold", str(gold), "--pred", str(rules), "--out", str(tmp_path / "rep/eval.md")])
    out = capsys.readouterr().out
    assert '"programs": 2' in out and "| F1 | 100.0% |" in out
    assert (tmp_path / "docs/PAYCHK.ja.md").exists() and (tmp_path / "rep/graph.mmd").exists()
    assert json.loads((tmp_path / "rep/eval.json").read_text())["citation_validity"] == 1.0


def test_qa_scoring():
    from legacylens.qa import Question, score_answer, summarize
    from legacylens.schema import Answer

    q = Question(
        id="Q",
        question="?",
        keywords=[["5000"], ["reject", "flag"]],
        expected=[Citation(program="PAYCHK", start_line=27, end_line=30)],
    )
    good = Answer(
        answer="Amounts over 5000 are flagged.", citations=[Citation(program="PAYCHK", start_line=28, end_line=28)]
    )
    wrong_lines = Answer(
        answer="Amounts over 5000 are flagged.", citations=[Citation(program="PAYCHK", start_line=1, end_line=2)]
    )
    missing_kw = Answer(answer="Amounts over 5000.", citations=good.citations)
    rows = [score_answer(q, a) for a in (good, wrong_lines, missing_kw)]
    assert [r["correct"] for r in rows] == [True, False, False]
    assert rows[2]["keyword_groups_matched"] == "1/2"
    no_expected = Question(id="Q2", question="?", keywords=[["PAYCHK"]])
    assert score_answer(no_expected, Answer(answer="PAYCHK", citations=[]))["correct"] is True
    s = summarize(rows)
    assert s["correct"] == 1 and s["citation_hit_rate"] == pytest.approx(2 / 3, abs=1e-3)


def test_cli_eval_qa_with_fake_llm(tmp_path, monkeypatch, capsys):
    import legacylens.agent as agent_mod

    qfile = tmp_path / "q.jsonl"
    qfile.write_text(
        json.dumps(
            {
                "id": "Q1",
                "question": "Limit?",
                "keywords": [["5000"]],
                "expected": [{"program": "PAYCHK", "start_line": 27, "end_line": 30}],
            }
        )
        + "\n"
    )
    ans = {"answer": "Over 5000 is flagged.", "citations": [{"program": "PAYCHK", "start_line": 27, "end_line": 28}]}
    monkeypatch.setattr(agent_mod, "make_client", lambda: FakeClient([text_msg(json.dumps(ans))]))
    out = tmp_path / "qa.md"
    main(["--src", str(FIX), "eval-qa", "--questions", str(qfile), "--out", str(out), "--model", "fake"])
    assert "| Correct (keywords + citation) | 1 (100.0%) |" in out.read_text()
    assert json.loads(out.with_suffix(".json").read_text())["rows"][0]["citations_valid"] == 1.0


def test_shipped_data_files_parse():
    from legacylens.qa import load_questions

    root = Path(__file__).parent.parent
    gold = load_rules(root / "gold/rules.jsonl")
    assert len(gold) >= 45 and len({g.id for g in gold}) == len(gold)
    qs = load_questions(root / "onboarding/questions.jsonl")
    assert len(qs) == 20 and all(q.keywords for q in qs)


CARDDEMO = Path(__file__).parent.parent / "data/carddemo/app"


@pytest.mark.skipif(not CARDDEMO.exists(), reason="run `make data` first")
def test_gold_and_questions_cite_real_lines():
    from legacylens.qa import load_questions

    real = Index.build(CARDDEMO)
    root = Path(__file__).parent.parent
    assert all(verify(r, real)["valid"] for r in load_rules(root / "gold/rules.jsonl"))
    for q in load_questions(root / "onboarding/questions.jsonl"):
        assert all(verify(c, real)["valid"] for c in q.expected), q.id


def test_llm_settings_accepts_project_and_provider_names():
    s = llm_settings({"LLM_BASE_URL": "http://x/v1", "LLM_API_KEY": "k"})
    assert (s["base_url"], s["api_key"]) == ("http://x/v1", "k")
    assert llm_settings({"OPENAI_API_KEY": "o", "LLM_API_KEY": "k"})["api_key"] == "o"
    assert "groq" in llm_settings({"GROQ_API_KEY": "g"})["base_url"]
    assert llm_settings({"LLM_BASE_URL": "http://colab/v1"})["api_key"] == "not-needed"
    with pytest.raises(RuntimeError, match="No LLM endpoint"):
        llm_settings({})
