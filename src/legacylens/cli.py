"""Command line: legacylens <command> ...  (python -m legacylens.cli when not installed)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from .citations import verify
from .evaluate import load_rules, score, to_markdown
from .index import Index
from .schema import BusinessRule, RuleSet
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
    reviewed = _reviewed(args.gold)
    for r in rules:
        print(f"=== {r.id} [{r.kind}] {r.paragraph}\n{r.summary}")
        print(f"  condition: {r.condition}\n  outcome:   {r.outcome}\n  fields:    {', '.join(r.fields)}")
        for c in r.citations:
            print(tb.read_lines(c.program, c.start_line, c.end_line))
        mark = "REVIEWED" if r.id in reviewed else "not reviewed yet"
        print(f"  [{mark}]  correct:  make gold-ok ID={r.id}")
        print(
            f'             fix text: make gold-set ID={r.id} F=summary V="..."   (F: summary, condition, outcome, ...)'
        )
        print(f"             fix lines: make gold-lines ID={r.id} L=START-END")
        print()
    done = sum(r.id in reviewed for r in rules)
    print(f"{len(rules)} rules, {done} reviewed. Missing rule: step 4, part c of HUONG_DAN.md (make gold-add)")


EDITABLE = ("summary", "condition", "outcome", "paragraph", "kind", "fields")


def _reviewed_path(gold: str) -> Path:
    return Path(gold).with_name("REVIEWED.txt")


def _reviewed(gold: str) -> set[str]:
    path = _reviewed_path(gold)
    return set(path.read_text(encoding="utf-8").split()) if path.exists() else set()


def cmd_gold_edit(args) -> None:
    """Change one gold rule without hand-editing JSON. The file is only written when the rule still passes."""
    idx = _index(args)
    path = Path(args.gold)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    pos = next((i for i, r in enumerate(rows) if r["id"] == args.id), None)
    if args.action == "add":
        if pos is not None:
            sys.exit(f"id {args.id} already exists")
        program = args.id.rsplit("-", 1)[0].upper()
        same = [i for i, r in enumerate(rows) if r["program"] == program]
        if not same:
            sys.exit(f"id must start with a labelled program, e.g. COSGN00C-G10 (got {args.id})")
        rows.insert(same[-1] + 1, {"id": args.id, "program": program, "kind": "other", "citations": []})
        pos, args.action = same[-1] + 1, "fix"
    if pos is None:
        sys.exit(f"no gold rule with id {args.id}. Ids are listed by `make review PROG=...`")
    reviewed = _reviewed(args.gold)
    if args.action == "ok":
        reviewed.add(args.id)
        _reviewed_path(args.gold).write_text("\n".join(sorted(reviewed)) + "\n", encoding="utf-8")
        program = rows[pos]["program"]
        left = [r["id"] for r in rows if r["program"] == program and r["id"] not in reviewed]
        print(f"{args.id} marked as reviewed. {program}: {len(left)} left {' '.join(left)}")
        return
    if args.action == "delete":
        removed = rows.pop(pos)
        reviewed.discard(args.id)
    else:
        rule = dict(rows[pos])
        if args.action == "fix":  # several fields at once, checked together
            for name in EDITABLE:
                val = getattr(args, f"new_{name}")
                if val is not None:
                    rule[name] = [v.strip() for v in val.split(",") if v.strip()] if name == "fields" else val
            if args.new_lines:
                try:
                    start, end = (int(x) for x in args.new_lines.split("-"))
                except ValueError:
                    sys.exit("L must look like 118-122")
                rule["citations"] = [{"program": rule["program"], "start_line": start, "end_line": end}]
        if args.action == "copy":
            if any(r["id"] == args.value for r in rows):
                sys.exit(f"id {args.value} already exists")
            rule["id"] = args.value
        elif args.action == "lines":
            try:
                start, end = (int(x) for x in args.value.split("-"))
            except ValueError:
                sys.exit("L must look like 118-122")
            rule["citations"] = [{"program": rule["program"], "start_line": start, "end_line": end}]
        elif args.action == "set":
            if args.field not in EDITABLE:
                sys.exit(f"F must be one of: {', '.join(EDITABLE)}")
            value = args.value
            if args.field == "fields":
                value = [v.strip() for v in value.split(",") if v.strip()]
            rule[args.field] = value
        try:
            checked = BusinessRule.model_validate(rule)
        except ValidationError as exc:
            sys.exit(f"not saved: {str(exc)[:400]}")
        chk = verify(checked, idx)
        if not chk["valid"]:
            sys.exit(f"not saved, the rule would fail the citation check: {'; '.join(chk['problems'])}")
        if args.action == "copy":
            rows.insert(pos + 1, rule)
        else:
            rows[pos] = {k: rule[k] for k in BusinessRule.model_fields if k in rule}  # schema order
            reviewed.discard(args.id)  # changed: needs a new look before it counts as reviewed
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    _reviewed_path(args.gold).write_text("".join(f"{i}\n" for i in sorted(reviewed)), encoding="utf-8")
    if args.action == "delete":
        print(f"deleted {removed['id']}")
    else:
        target = args.value if args.action == "copy" else args.id
        print(f"saved {target}. Check it: make review PROG={rule['program']}")
        if args.action == "copy":
            print(
                f'now edit the copy: make gold-set ID={target} F=summary V="..." and make gold-lines ID={target} L=..'
            )


def cmd_readme(args) -> None:
    from .readme import fill

    path = Path(args.readme)
    human = None
    if args.read_min:
        human = {
            "read_min": args.read_min,
            "tool_min": args.tool_min,
            "read_ok": args.read_ok,
            "tool_ok": args.tool_ok,
            "people": args.people,
        }
    try:
        text, changed = fill(path.read_text(encoding="utf-8"), Path(args.reports), human, args.attempt, args.video)
    except ValueError as exc:
        sys.exit(f"README not changed: {exc}")
    path.write_text(text, encoding="utf-8")
    print("updated: " + (", ".join(changed) if changed else "nothing (no report found, run make eval first)"))
    left = text.count("[X]")
    print(f"{left} [X] left in README" if left else "no [X] left in README")


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
    ge = sub.add_parser("gold-edit", help="Edit one gold rule: ok, set, lines, copy, delete")
    ge.add_argument("action", choices=["ok", "set", "lines", "fix", "add", "copy", "delete"])
    for name in ("summary", "condition", "outcome", "fields", "paragraph", "kind", "lines"):
        ge.add_argument(f"--new-{name}", dest=f"new_{name}", default=None)
    ge.add_argument("id")
    ge.add_argument("value", nargs="?", default="", help="new text / START-END / new id")
    ge.add_argument("--field", default="summary")
    ge.add_argument("--gold", default="gold/rules.jsonl")
    ge.set_defaults(fn=cmd_gold_edit)
    rd = sub.add_parser("readme", help="Write measured numbers from reports/ into the README results table")
    rd.add_argument("--readme", default="README.md")
    rd.add_argument("--reports", default="reports")
    rd.add_argument("--attempt", default=None, help="Also add a row to the attempts table, with this description")
    rd.add_argument("--video", default=None)
    for name in ("read-min", "tool-min", "read-ok", "tool-ok", "people"):
        rd.add_argument(f"--{name}", default=None)
    rd.set_defaults(fn=cmd_readme)
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
