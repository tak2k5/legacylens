"""Command line: legacylens <command> ...  (python -m legacylens.cli when not installed)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .citations import verify
from .evaluate import load_rules, score, to_markdown
from .index import Index
from .schema import RuleSet
from .tools import Toolbox

DEFAULT_SRC = "data/carddemo/app"


def _index(args) -> Index:
    src = Path(args.src)
    if not src.exists():
        sys.exit(f"{src} not found. Run `make data` to download AWS CardDemo first.")
    return Index.build(src)


def cmd_stats(args) -> None:
    print(json.dumps(_index(args).stats(), indent=2))


def cmd_graph(args) -> None:
    idx = _index(args)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "graph.json").write_text(idx.to_json(), encoding="utf-8")
    name = f"graph-{args.focus.lower()}.mmd" if args.focus else "graph.mmd"
    (out / name).write_text(idx.to_mermaid(args.focus), encoding="utf-8")
    print(f"wrote {out / 'graph.json'} and {out / name}")


def cmd_outline(args) -> None:
    print(Toolbox(_index(args)).program_outline(args.program))


def cmd_extract(args) -> None:
    from .agent import Agent

    idx = _index(args)
    agent = Agent(idx, model=args.model, max_steps=args.max_steps)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    programs = sorted(idx.programs) if args.program == ["ALL"] else args.program
    log = Path(args.log)
    log.parent.mkdir(parents=True, exist_ok=True)
    failed = []
    for name in programs:
        try:
            rules, checks, trace = agent.extract_rules(name, lang=args.lang)
        except Exception as exc:  # one bad program (rate limit, invalid JSON) must not lose the others
            failed.append(name)
            print(f"{name}: FAILED {type(exc).__name__}: {str(exc)[:300]}")
            continue
        (out / f"{rules.program}.json").write_text(rules.model_dump_json(indent=2), encoding="utf-8")
        (out / f"{rules.program}.check.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
        ok = sum(c["valid"] for c in checks)
        row = {
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "program": rules.program,
            "model": agent.model,
            "rules": len(rules.rules),
            "citations_ok": ok,
            **trace.as_dict(),
        }
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        print(
            f"{rules.program}: {len(rules.rules)} rules, {ok} pass the citation check, "
            f"{trace.tool_calls} tool calls ({trace.blocked_repeats} repeats blocked), "
            f"{trace.prompt_tokens}+{trace.completion_tokens} tokens, {trace.seconds}s"
        )
    if failed:
        sys.exit(f'failed: {" ".join(failed)}. Fix the cause, then run: make extract PROGS="{" ".join(failed)}"')


def cmd_doc(args) -> None:
    from .docgen import render

    idx = _index(args)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    programs = sorted(idx.programs) if args.program == ["ALL"] else args.program
    for name in programs:
        prog = idx.program(name)
        rules = checks = None
        rule_file = Path(args.rules) / f"{prog.program_id}.json"
        if rule_file.exists():
            rules = RuleSet.model_validate_json(rule_file.read_text(encoding="utf-8"))
            checks = [verify(r, idx) for r in rules.rules]
        path = out / f"{prog.program_id}.{args.lang}.md"
        path.write_text(
            render(idx, prog.program_id, rules, checks, lang=args.lang, link_base=args.link_base), encoding="utf-8"
        )
        print(f"wrote {path}")


def cmd_ask(args) -> None:
    from .agent import Agent

    agent = Agent(_index(args), model=args.model, max_steps=args.max_steps)
    answer, checks, trace = agent.ask(args.question)
    print(answer.answer)
    for c, chk in zip(answer.citations, checks, strict=True):
        print(
            f"  [{c.program}:{c.start_line}-{c.end_line}] {'ok' if chk['valid'] else 'FAILED ' + '; '.join(chk['problems'])}"
        )
    print(f"({trace.tool_calls} tool calls, {trace.prompt_tokens}+{trace.completion_tokens} tokens, {trace.seconds}s)")


def cmd_check_gold(args) -> None:
    idx = _index(args)
    rules = load_rules(args.gold)
    bad = 0
    for r in rules:
        chk = verify(r, idx)
        if not chk["valid"]:
            bad += 1
            print(f"{r.id}: {'; '.join(chk['problems'])}")
    print(f"{len(rules) - bad}/{len(rules)} gold rules pass the citation check")
    sys.exit(1 if bad else 0)


def cmd_review_gold(args) -> None:
    """Print each gold rule of one program next to the lines it cites, for a human to check."""
    idx = _index(args)
    tb = Toolbox(idx)
    rules = [r for r in load_rules(args.gold) if r.program.upper() == args.program.upper()]
    if not rules:
        sys.exit(f"no gold rule for {args.program}")
    for r in rules:
        print(f"=== {r.id} [{r.kind}] {r.paragraph}\n{r.summary}")
        print(f"  condition: {r.condition}\n  outcome:   {r.outcome}\n  fields:    {', '.join(r.fields)}")
        for c in r.citations:
            print(tb.read_lines(c.program, c.start_line, c.end_line))
        print()
    print(f"{len(rules)} rules. Edit gold/rules.jsonl, then run `make check-gold`.")


def cmd_eval(args) -> None:
    idx = _index(args)
    gold = load_rules(args.gold)
    pred = load_rules(args.pred)
    result = score(gold, pred)
    scored = [p for p in pred if p.program in set(result["programs"])]
    validity = sum(verify(p, idx)["valid"] for p in scored) / len(scored) if scored else None
    md = to_markdown(result, validity)
    print(md)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(md + "\n", encoding="utf-8")
        Path(args.out).with_suffix(".json").write_text(json.dumps(result | {"citation_validity": validity}, indent=2))


def cmd_eval_qa(args) -> None:
    from .agent import Agent
    from .qa import dump_row, load_questions, summarize
    from .qa import to_markdown as qa_markdown

    agent = Agent(_index(args), model=args.model, max_steps=args.max_steps)
    questions = load_questions(args.questions)
    if args.limit:
        questions = questions[: args.limit]
    rows = []
    for q in questions:
        try:
            answer, checks, trace = agent.ask(q.question)
            row = dump_row(q, answer, checks, trace.as_dict())
        except Exception as exc:  # count as wrong, keep going
            row = {
                "id": q.id,
                "keywords_ok": False,
                "keyword_groups_matched": "0/0",
                "citation_hit": False,
                "correct": False,
                "citations_valid": None,
                "error": str(exc)[:300],
            }
        rows.append(row)
        print(f"{q.id}: {'ok' if row['correct'] else 'wrong'}")
    summary = summarize(rows) | {"model": agent.model}
    md = qa_markdown(summary, rows)
    print(md)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"Model: {agent.model}\n\n{md}\n", encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="legacylens", description="Read COBOL, extract business rules with citations.")
    ap.add_argument("--src", default=DEFAULT_SRC, help="COBOL source tree (default: %(default)s)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("stats", help="Count programs, copybooks, jobs, lines").set_defaults(fn=cmd_stats)
    g = sub.add_parser("graph", help="Write dependency graph (JSON + Mermaid)")
    g.add_argument("--out", default="reports")
    g.add_argument("--focus", help="Only this program/file/copybook and its neighbours")
    g.set_defaults(fn=cmd_graph)
    o = sub.add_parser("outline", help="Static outline of one program")
    o.add_argument("program")
    o.set_defaults(fn=cmd_outline)

    for name, fn, helptext in (
        ("extract", cmd_extract, "Extract business rules with the LLM agent"),
        ("ask", cmd_ask, "Ask an onboarding question"),
    ):
        s = sub.add_parser(name, help=helptext)
        if name == "extract":
            s.add_argument("program", nargs="+", help="Program ids, or ALL")
            s.add_argument("--out", default="out/rules")
            s.add_argument("--lang", default="en", choices=["en", "vi", "ja"])
            s.add_argument("--log", default="reports/runs.jsonl")
        else:
            s.add_argument("question")
        s.add_argument("--model", default=None, help="Defaults to $LLM_MODEL")
        s.add_argument("--max-steps", type=int, default=16)
        s.set_defaults(fn=fn)

    d = sub.add_parser("doc", help="Write design documents (Markdown)")
    d.add_argument("program", nargs="+", help="Program ids, or ALL")
    d.add_argument("--rules", default="out/rules")
    d.add_argument("--out", default="docs/generated")
    d.add_argument("--lang", default="vi", choices=["vi", "en", "ja"])
    d.add_argument("--link-base", default="../../data/carddemo/app/")
    d.set_defaults(fn=cmd_doc)

    c = sub.add_parser("check-gold", help="Check that gold labels cite real lines")
    c.add_argument("--gold", default="gold/rules.jsonl")
    c.set_defaults(fn=cmd_check_gold)
    rg = sub.add_parser("review-gold", help="Show the gold rules of one program with the lines they cite")
    rg.add_argument("program")
    rg.add_argument("--gold", default="gold/rules.jsonl")
    rg.set_defaults(fn=cmd_review_gold)
    e = sub.add_parser("eval", help="Score extracted rules against gold labels")
    e.add_argument("--gold", default="gold/rules.jsonl")
    e.add_argument("--pred", default="out/rules")
    e.add_argument("--out", default="reports/eval.md")
    e.set_defaults(fn=cmd_eval)
    q = sub.add_parser("eval-qa", help="Ask the onboarding questions and score the answers (needs the LLM)")
    q.add_argument("--questions", default="onboarding/questions.jsonl")
    q.add_argument("--out", default="reports/eval_qa.md")
    q.add_argument("--limit", type=int, default=0)
    q.add_argument("--model", default=None)
    q.add_argument("--max-steps", type=int, default=12)
    q.set_defaults(fn=cmd_eval_qa)

    args = ap.parse_args(argv)
    try:
        args.fn(args)
    except RuntimeError as exc:  # e.g. no LLM endpoint configured: a clear message, not a traceback
        sys.exit(f"error: {exc}")


if __name__ == "__main__":
    main()
