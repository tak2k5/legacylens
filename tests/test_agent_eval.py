"""Agent loop, citation check, scoring and doc rendering, with a scripted fake LLM (no network)."""

import json
import re
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


def read(i=0):
    return tool_msg("read_paragraph", {"program": "PAYCHK", "paragraph": "1000-CHECK-AMOUNT", "n": i}, f"r{i}")


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
    assert trace.max_prompt_tokens == 100
    assert "Vietnamese" in client.requests[0][1]["content"]
    tool_results = [m["content"] for m in client.requests[2] if m["role"] == "tool"]
    assert "5000" in tool_results[0] and tool_results[1].startswith("BLOCKED")


def test_agent_repairs_invalid_json(idx):
    bad = {"program": "PAYCHK", "purpose": "x", "rules": [{**RULE, "citations": []}]}
    good = {"program": "PAYCHK", "purpose": "x", "rules": [RULE]}
    client = FakeClient([read(0), read(1), text_msg(json.dumps(bad)), text_msg(json.dumps(good))])
    rules, _, trace = Agent(idx, client=client, model="fake").extract_rules("PAYCHK")
    assert trace.repairs == 1 and len(rules.rules) == 1
    assert "invalid" in client.requests[3][-1]["content"]


def test_agent_sends_model_back_to_the_code(idx):
    good = {"program": "PAYCHK", "purpose": "x", "rules": [RULE]}
    client = FakeClient([text_msg(""), text_msg(json.dumps(good)), read(0), read(1), text_msg(json.dumps(good))])
    rules, _, trace = Agent(idx, client=client, model="fake").extract_rules("PAYCHK")
    assert (trace.nudges, trace.tool_calls, trace.repairs) == (2, 2, 0)
    assert "empty" in client.requests[1][-1]["content"]
    assert "without reading" in client.requests[2][-1]["content"]


def test_merge_stream_rebuilds_tool_calls():
    from legacylens.agent import merge_stream

    def chunk(content=None, calls=None, finish=None, usage=None):
        choices = [] if usage else [NS(delta=NS(content=content, tool_calls=calls), finish_reason=finish)]
        return NS(choices=choices, usage=usage)

    fn = NS
    chunks = [
        chunk(calls=[NS(index=0, id="t1", function=fn(name="read_lines", arguments='{"program": '))]),
        chunk(calls=[NS(index=0, id=None, function=fn(name=None, arguments='"PAYCHK"}'))]),
        chunk(content="ok", finish="tool_calls"),
        chunk(usage=NS(prompt_tokens=7, completion_tokens=3)),
    ]
    msg, finish, usage = merge_stream(chunks)
    assert msg.content == "ok" and finish == "tool_calls" and usage.prompt_tokens == 7
    assert msg.tool_calls[0].id == "t1" and json.loads(msg.tool_calls[0].function.arguments) == {"program": "PAYCHK"}


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
    answer, checks, _ = Agent(idx, client=FakeClient([read(), text_msg(json.dumps(ans))]), model="fake").ask("who?")
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
    monkeypatch.setattr(agent_mod, "make_client", lambda: FakeClient([read(), text_msg(json.dumps(ans))]))
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


def test_context_warning(idx, monkeypatch, capsys):
    monkeypatch.setenv("LLM_CONTEXT", "1000")
    agent = Agent(idx, client=FakeClient([read(), text_msg(json.dumps({"answer": "x", "citations": []}))]))
    agent.ask("q")
    assert "WARNING" not in capsys.readouterr().err
    agent.context = 50
    agent.client = FakeClient([read(), text_msg(json.dumps({"answer": "x", "citations": []}))])
    agent.ask("q")
    assert "WARNING" in capsys.readouterr().err


def test_streaming_is_on_for_colab_tunnels(idx, monkeypatch):
    monkeypatch.delenv("LLM_STREAM", raising=False)
    tunnel = NS(base_url="https://abc.trycloudflare.com/v1/", chat=None)
    assert Agent(idx, client=tunnel).stream is True
    assert Agent(idx, client=NS(base_url="https://api.groq.com/openai/v1", chat=None)).stream is False
    monkeypatch.setenv("LLM_STREAM", "0")
    assert Agent(idx, client=tunnel).stream is False


def test_gold_edit_commands(tmp_path, capsys):
    gold = tmp_path / "rules.jsonl"
    gold.write_text(json.dumps(RULE) + "\n")
    run = ["--src", str(FIX), "gold-edit"]
    main([*run, "ok", "PAYCHK-R1", "--gold", str(gold)])
    assert (tmp_path / "REVIEWED.txt").read_text().split() == ["PAYCHK-R1"]
    main([*run, "set", "PAYCHK-R1", "Payments over 5000 are flagged.", "--gold", str(gold)])
    assert json.loads(gold.read_text())["summary"] == "Payments over 5000 are flagged."
    assert (tmp_path / "REVIEWED.txt").read_text().split() == []  # edited, so it needs a new review
    with pytest.raises(SystemExit):
        main([*run, "lines", "PAYCHK-R1", "1-2", "--gold", str(gold)])  # would fail the citation check
    assert json.loads(gold.read_text())["citations"][0]["start_line"] == 27
    main([*run, "copy", "PAYCHK-R1", "PAYCHK-R2", "--gold", str(gold)])
    main([*run, "delete", "PAYCHK-R1", "--gold", str(gold)])
    assert [json.loads(line)["id"] for line in gold.read_text().splitlines()] == ["PAYCHK-R2"]

    main(
        [
            *run,
            "add",
            "PAYCHK-R3",
            "--new-lines",
            "27-30",
            "--new-summary",
            "Limit.",
            "--new-fields",
            "PAY-AMT",
            "--new-kind",
            "validation",
            "--gold",
            str(gold),
        ]
    )
    main([*run, "fix", "PAYCHK-R3", "--new-lines", "27-29", "--new-fields", "PAY-AMT, WS-REASON", "--gold", str(gold)])
    added = json.loads(gold.read_text().splitlines()[-1])
    assert list(added)[:3] == ["id", "program", "paragraph"] or list(added)[:2] == ["id", "program"]
    assert added["fields"] == ["PAY-AMT", "WS-REASON"] and added["citations"][0]["end_line"] == 29


def test_readme_fill(tmp_path):
    from legacylens.readme import fill

    readme = (Path(__file__).parent.parent / "README.md").read_text()
    # the real README may already hold attempts from make readme; start from the template table
    readme = re.sub(r"### Các lần thử\n\n(?:\|.*\n)+\n?", "", readme)
    rep = tmp_path
    (rep / "eval.json").write_text(
        json.dumps({"programs": ["A"], "precision": 0.5, "recall": 0.25, "f1": 1 / 3, "citation_validity": 0.9})
    )
    runs = [
        {"program": "A", "model": "m1", "prompt_tokens": 1, "completion_tokens": 1, "seconds": 1},
        {"program": "A", "model": "qwen", "prompt_tokens": 90, "completion_tokens": 10, "seconds": 20},
        {"program": "B", "model": "qwen", "prompt_tokens": 999, "completion_tokens": 1, "seconds": 99},
    ]
    (rep / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in runs))
    (rep / "eval_qa.json").write_text(
        json.dumps({"summary": {"correct": 12, "questions": 20, "citation_hit_rate": 0.7, "model": "qwen"}})
    )
    human = {"read_min": "40", "tool_min": "15", "read_ok": "7", "tool_ok": "9", "people": "2 người"}
    text, _ = fill(readme, rep)
    text, _ = fill(text, rep, human)
    text, _ = fill(text, rep, video="https://youtu.be/x")
    text, _ = fill(text, rep, attempt="Bản đầu")
    (rep / "eval.json").write_text(json.dumps({"programs": ["A"], "precision": 0.1, "recall": 0.1, "f1": 0.1}))
    after, _ = fill(text, rep, attempt="Worse")
    assert "| Precision / Recall / F1 | 50.0% / 25.0% / 33.3% |" in after and "10.0% / 10.0% / 10.0%" in after
    assert "| Precision / Recall / F1 | 50.0% / 25.0% / 33.3% |" in text
    assert "100 token, 20.0 giây (mô hình qwen)" in text  # latest run of scored programs only
    assert "12/20, trích đúng dòng 70.0%" in text and "40 / 15 phút mỗi câu; đúng 7 / 9 (2 người)" in text
    assert "| 1 | Bản đầu | qwen | 50.0% / 25.0% / 33.3% | 100 |" in text
    assert "[X]" not in text and "Video demo 2 phút: https://youtu.be/x" in text
    text2, _ = fill(text, rep, attempt="Lần hai")
    assert "| 2 | Lần hai |" in text2 and text2.count("### Các lần thử") == 1


def test_extra_rules_reach_the_prompt(idx, monkeypatch):
    monkeypatch.setenv("LLM_EXTRA_RULES", "Each WHEN branch is a separate rule.")
    final = {"program": "PAYCHK", "purpose": "x", "rules": [RULE]}
    client = FakeClient([read(0), read(1), text_msg(json.dumps(final))])
    Agent(idx, client=client, model="fake").extract_rules("PAYCHK")
    system = client.requests[0][0]["content"]
    assert "- Each WHEN branch is a separate rule.\n\nWhen done," in system
