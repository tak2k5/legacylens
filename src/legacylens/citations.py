"""Check that a cited line range exists and actually contains what the rule talks about."""

from __future__ import annotations

import re

from .index import Index
from .schema import BusinessRule, Citation

MAX_SPAN = 60
RE_TOKEN = re.compile(r"'([^']{3,})'|\b(\d{2,})\b|\b([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\b")


def evidence_tokens(rule: BusinessRule) -> set[str]:
    """Words a correct citation should contain: data names, codes and messages mentioned by the rule."""
    tokens = {f.upper() for f in rule.fields}
    for text in (rule.condition or "", rule.outcome or ""):
        for m in RE_TOKEN.finditer(text.upper()):
            tokens.add(next(g for g in m.groups() if g))
    return {t.strip() for t in tokens if t.strip()}


def _check_citation(c: Citation, index: Index) -> tuple[list[str], str]:
    problems: list[str] = []
    prog = index.programs.get(c.program)
    if prog is None:
        return [f"unknown program {c.program}"], ""
    if c.end_line > prog.total_lines:
        problems.append(f"{c.program}:{c.end_line} is past the end of the file ({prog.total_lines} lines)")
    if c.end_line - c.start_line + 1 > MAX_SPAN:
        problems.append(f"range {c.start_line}-{c.end_line} is wider than {MAX_SPAN} lines")
    lines = index.read_lines(prog.path, c.start_line, c.end_line)
    code = [t for _, t in lines if len(t) > 6 and t[6] not in "*/" and t[7:].strip()]
    if not code:
        problems.append(f"{c.program}:{c.start_line}-{c.end_line} holds no code")
    return problems, "\n".join(code).upper()


def verify(item: BusinessRule | Citation, index: Index) -> dict:
    if isinstance(item, Citation):
        problems, _ = _check_citation(item, index)
        return {
            "citation": f"{item.program}:{item.start_line}-{item.end_line}",
            "valid": not problems,
            "problems": problems,
        }
    problems: list[str] = []
    cited_text = ""
    for c in item.citations:
        p, text = _check_citation(c, index)
        problems += p
        cited_text += "\n" + text
    tokens = evidence_tokens(item)
    hits = sorted(t for t in tokens if t in cited_text)
    if tokens and not hits:
        problems.append("cited lines contain none of the rule's fields, codes or messages")
    return {
        "rule": item.id,
        "valid": not problems,
        "problems": problems,
        "evidence": hits,
        "evidence_checked": len(tokens),
    }
