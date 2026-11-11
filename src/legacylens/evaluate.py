"""Score extracted rules against hand-labelled gold rules.

A predicted rule matches a gold rule of the same program when its cited lines cover at least half of the gold
lines and at least a quarter of its own lines fall inside the gold range (so citing a whole program does not match).
Matching is one-to-one, best overlap first.
"""

from __future__ import annotations

import json
from pathlib import Path

from .schema import BusinessRule, RuleSet

MIN_GOLD_COVER = 0.5
MIN_PRED_PRECISION = 0.25


def lines_of(rule: BusinessRule) -> set[tuple[str, int]]:
    return {(c.program, n) for c in rule.citations for n in range(c.start_line, c.end_line + 1)}


def load_rules(path: str | Path) -> list[BusinessRule]:
    """Accept JSONL of rules, a RuleSet JSON, or a directory of RuleSet JSON files."""
    path = Path(path)
    if path.is_dir():
        out: list[BusinessRule] = []
        for f in sorted(path.glob("*.json")):
            if f.name.endswith(".check.json"):
                continue
            out += load_rules(f)
        return out
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [BusinessRule.model_validate_json(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if "rules" in data:
        return RuleSet.model_validate(data).rules
    return [BusinessRule.model_validate(data)]


def match(gold: list[BusinessRule], pred: list[BusinessRule]) -> list[tuple[BusinessRule, BusinessRule, float]]:
    candidates = []
    for gi, g in enumerate(gold):
        gl = lines_of(g)
        for pi, p in enumerate(pred):
            if p.program != g.program:
                continue
            pl = lines_of(p)
            inter = len(gl & pl)
            if not inter:
                continue
            cover, prec = inter / len(gl), inter / len(pl)
            if cover >= MIN_GOLD_COVER and prec >= MIN_PRED_PRECISION:
                candidates.append((cover * prec, gi, pi))
    used_g, used_p, pairs = set(), set(), []
    for score, gi, pi in sorted(candidates, key=lambda c: (-c[0], c[1], c[2])):  # ties: earliest first
        if gi in used_g or pi in used_p:
            continue
        used_g.add(gi)
        used_p.add(pi)
        pairs.append((gold[gi], pred[pi], round(score, 3)))
    return pairs


def score(gold: list[BusinessRule], pred: list[BusinessRule], programs: set[str] | None = None) -> dict:
    """Only programs that have gold labels are scored, so unlabelled programs do not count as false positives."""
    programs = programs or {g.program for g in gold}
    gold = [g for g in gold if g.program in programs]
    pred = [p for p in pred if p.program in programs]
    pairs = match(gold, pred)
    tp = len(pairs)
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    kind_ok = sum(g.kind == p.kind for g, p, _ in pairs)
    matched_g = {id(g) for g, _, _ in pairs}  # by object, so a repeated id cannot hide a miss
    matched_p = {id(p) for _, p, _ in pairs}
    return {
        "programs": sorted(programs),
        "gold": len(gold),
        "predicted": len(pred),
        "matched": tp,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "kind_accuracy_on_matched": round(kind_ok / tp, 3) if tp else None,
        "missed": [g.id for g in gold if id(g) not in matched_g],
        "extra": [p.id for p in pred if id(p) not in matched_p],
        "pairs": [{"gold": g.id, "pred": p.id, "overlap": s} for g, p, s in pairs],
    }


def to_markdown(result: dict, citation_validity: float | None = None) -> str:
    rows = [
        "| Metric | Value |",
        "| --- | --- |",
        f"| Programs scored | {len(result['programs'])} ({', '.join(result['programs'])}) |",
        f"| Gold rules | {result['gold']} |",
        f"| Predicted rules | {result['predicted']} |",
        f"| Precision | {result['precision']:.1%} |",
        f"| Recall | {result['recall']:.1%} |",
        f"| F1 | {result['f1']:.1%} |",
    ]
    if result["kind_accuracy_on_matched"] is not None:
        rows.append(f"| Rule kind correct (matched rules) | {result['kind_accuracy_on_matched']:.1%} |")
    if citation_validity is not None:
        rows.append(f"| Citations that pass the source check | {citation_validity:.1%} |")
    out = "\n".join(rows)
    if result["missed"]:
        out += "\n\nMissed gold rules: " + ", ".join(result["missed"])
    if result["extra"]:
        out += "\n\nPredicted rules with no gold match: " + ", ".join(result["extra"])
    return out
