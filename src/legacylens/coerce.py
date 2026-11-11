"""Tolerant reading of the final JSON that small open-weight models write.

A 7B model often gets the content right but the shape slightly wrong: a trailing comma, `"fields": "A, B"`
instead of a list, `"lines": "88-90"` instead of start_line/end_line, a kind outside the list. Rejecting the whole
answer for that loses every good rule in it. This module fixes the shape only. It never invents content: a rule
without a summary or without any usable citation is dropped and counted, so the score shows the loss.
"""

from __future__ import annotations

import json
import re
from typing import Any, get_args

from .schema import Answer, RuleKind, RuleSet

KINDS = set(get_args(RuleKind))
KIND_ALIASES = {
    "validate": "validation",
    "check": "validation",
    "input-validation": "validation",
    "compute": "calculation",
    "computation": "calculation",
    "calc": "calculation",
    "navigation": "routing",
    "control-flow": "routing",
    "transfer": "routing",
    "data": "data-access",
    "file-access": "data-access",
    "io": "data-access",
    "database": "data-access",
    "error": "error-handling",
    "exception": "error-handling",
    "security": "authorization",
    "authentication": "authorization",
    "auth": "authorization",
}


def loads_lenient(text: str) -> Any:
    """json.loads, then retry without // comments and trailing commas."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    cleaned = re.sub(r"^\s*//.*$", "", text, flags=re.M)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return json.loads(cleaned)


def _text(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, list):
        return "; ".join(str(x) for x in v)
    return str(v)


def _kind(v: Any) -> str:
    k = str(v or "other").strip().lower().replace("_", "-").replace(" ", "-")
    return k if k in KINDS else KIND_ALIASES.get(k, "other")


def _citation(c: Any, program: str | None) -> dict | None:
    if isinstance(c, str):  # "COSGN00C:88-90", "88-90", "88"
        m = re.match(r"\s*(?:([A-Za-z0-9-]+)\s*[:@ ]\s*)?(\d+)\s*(?:-\s*(\d+))?\s*$", c)
        if not m:
            return None
        prog, a, b = m.group(1) or program, int(m.group(2)), int(m.group(3) or m.group(2))
    elif isinstance(c, dict):
        prog = c.get("program") or program
        a, b = c.get("start_line", c.get("start")), c.get("end_line", c.get("end"))
        lines = c.get("lines", c.get("line"))
        if a is None and lines is not None:
            if isinstance(lines, (list, tuple)) and lines:
                a, b = lines[0], lines[-1]
            else:
                found = _citation(str(lines), prog)
                return found
        if b is None:
            b = a
        try:
            a, b = int(a), int(b)
        except (TypeError, ValueError):
            return None
    else:
        return None
    if not prog or a < 1 or b < 1:
        return None
    a, b = min(a, b), max(a, b)
    return {"program": str(prog), "start_line": a, "end_line": b}


def _citations(v: Any, program: str | None) -> list[dict]:
    items = v if isinstance(v, list) else [v] if v else []
    return [c for c in (_citation(x, program) for x in items) if c]


def coerce(data: Any, model_cls: type, program: str | None = None) -> tuple[Any, int]:
    """Return (data with the shape fixed, number of rules dropped)."""
    if model_cls is RuleSet:
        if isinstance(data, list):
            data = {"rules": data}
        if not isinstance(data, dict) or "rules" not in data:
            return data, 0  # not a rule set at all (e.g. a tool call written as text): let validation reject it
        # the program we asked about wins: a model that copies another program's name must not overwrite its file
        prog = str(program or data.get("program") or "").strip().upper() or None
        rules, dropped, seen = [], 0, set()
        for i, r in enumerate(data.get("rules") or [], 1):
            if not isinstance(r, dict):
                dropped += 1
                continue
            rp = prog or str(r.get("program") or "").strip().upper() or None
            summary = _text(r.get("summary") or r.get("description") or r.get("rule"))
            cits = _citations(r.get("citations", r.get("citation")), rp)
            if not summary or not cits or not rp:
                dropped += 1
                continue
            fields = r.get("fields") or []
            if isinstance(fields, str):
                fields = [f for f in re.split(r"[,\s]+", fields) if f]
            rid = str(r.get("id") or f"{rp}-R{i}")
            if rid in seen:  # small models repeat ids; scoring and docs need them unique
                rid = f"{rid}-{i}"
            seen.add(rid)
            rules.append(
                {
                    "id": rid,
                    "program": rp,
                    "paragraph": _text(r.get("paragraph")),
                    "kind": _kind(r.get("kind") or r.get("type")),
                    "summary": summary,
                    "condition": _text(r.get("condition")),
                    "outcome": _text(r.get("outcome")),
                    "fields": [str(f) for f in fields] if isinstance(fields, list) else [],
                    "citations": cits,
                }
            )
        return {"program": prog, "purpose": _text(data.get("purpose")) or "", "rules": rules}, dropped
    if model_cls is Answer and isinstance(data, dict):
        answer = _text(data.get("answer") or data.get("text") or data.get("response"))
        return {"answer": answer, "citations": _citations(data.get("citations"), None)}, 0
    return data, 0
