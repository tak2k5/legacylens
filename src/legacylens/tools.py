"""Tools the agent may call. Each returns plain text with file line numbers so the model can cite them."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

from .index import Index

MAX_LINES = 120
MAX_HITS = 40


class Toolbox:
    def __init__(self, index: Index):
        self.index = index
        self._tools: dict[str, tuple[Callable[..., str], dict]] = {
            "program_outline": (
                self.program_outline,
                {
                    "description": "Structure of one program: kind, files with read/write mode, transfers to other programs, copybooks, paragraphs with line ranges and PERFORM targets.",
                    "parameters": {
                        "type": "object",
                        "properties": {"program": {"type": "string"}},
                        "required": ["program"],
                    },
                },
            ),
            "read_lines": (
                self.read_lines,
                {
                    "description": f"Read source lines of a program with line numbers (at most {MAX_LINES} lines per call).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "program": {"type": "string"},
                            "start": {"type": "integer"},
                            "end": {"type": "integer"},
                        },
                        "required": ["program", "start", "end"],
                    },
                },
            ),
            "read_paragraph": (
                self.read_paragraph,
                {
                    "description": "Read one paragraph of a program by name, with line numbers.",
                    "parameters": {
                        "type": "object",
                        "properties": {"program": {"type": "string"}, "paragraph": {"type": "string"}},
                        "required": ["program", "paragraph"],
                    },
                },
            ),
            "open_copybook": (
                self.open_copybook,
                {
                    "description": "Read a copybook (record layout) with line numbers.",
                    "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
                },
            ),
            "who_uses": (
                self.who_uses,
                {
                    "description": "Who calls a program, or which programs read/write a file or include a copybook; plus the transitive impact set.",
                    "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
                },
            ),
            "search_code": (
                self.search_code,
                {
                    "description": f"Regex search over all programs; returns up to {MAX_HITS} hits as PROGRAM:line: text.",
                    "parameters": {
                        "type": "object",
                        "properties": {"pattern": {"type": "string"}},
                        "required": ["pattern"],
                    },
                },
            ),
        }

    # ---------- schema for the LLM ----------
    def specs(self) -> list[dict[str, Any]]:
        return [{"type": "function", "function": {"name": n, **spec}} for n, (_, spec) in self._tools.items()]

    def call(self, name: str, arguments: str | dict) -> str:
        if name not in self._tools:
            return f"ERROR: unknown tool {name}"
        try:
            args = json.loads(arguments) if isinstance(arguments, str) else arguments
            return self._tools[name][0](**args)
        except Exception as exc:  # the model sees the error and can recover
            return f"ERROR: {type(exc).__name__}: {exc}"

    # ---------- tools ----------
    def program_outline(self, program: str) -> str:
        p = self.index.program(program)
        out = [f"PROGRAM {p.program_id} ({p.kind}, {p.loc} lines of code, file {p.path.split('/')[-1]})"]
        if p.file_ops:
            out.append("FILES:")
            seen = set()
            for op in p.file_ops:
                ds = self.index.dataset_for(p, op.file)
                key = (op.file, op.mode)
                if key not in seen:
                    seen.add(key)
                    out.append(
                        f"  {op.mode:<10} {op.file}" + (f" -> {ds}" if ds != op.file else "") + f" (line {op.line})"
                    )
        transfers = p.transfers()
        if transfers:
            out.append("TRANSFERS:")
            out += [f"  {verb} {target} (line {line})" for verb, target, line in transfers]
        if p.copybooks:
            out.append("COPYBOOKS: " + ", ".join(f"{c.name}@{c.line}" for c in p.copybooks))
        out.append("PARAGRAPHS:")
        for para in p.paragraphs:
            performs = sorted({r.name for r in para.performs})
            out.append(f"  {para.name} [{para.start}-{para.end}]" + (f" -> {', '.join(performs)}" if performs else ""))
        return "\n".join(out)

    def read_lines(self, program: str, start: int, end: int) -> str:
        p = self.index.program(program)
        end = min(end, start + MAX_LINES - 1)
        return "\n".join(f"{n:>5}: {t}" for n, t in self.index.read_lines(p.path, start, end))

    def read_paragraph(self, program: str, paragraph: str) -> str:
        p = self.index.program(program)
        para = p.paragraph(paragraph)
        if para is None:
            return f"ERROR: no paragraph {paragraph} in {p.program_id}"
        text = self.read_lines(program, para.start, para.end)
        if para.end - para.start + 1 > MAX_LINES:
            text += f"\n... truncated; continue with read_lines from {para.start + MAX_LINES}"
        return text

    def open_copybook(self, name: str) -> str:
        cb = self.index.copybooks.get(name.upper())
        if cb is None:
            return f"ERROR: copybook {name} not in source tree (system copybook or missing)"
        lines = self.index.read_lines(cb.path, 1, min(cb.total_lines, MAX_LINES))
        return f"COPYBOOK {cb.name}\n" + "\n".join(f"{n:>5}: {t}" for n, t in lines)

    def who_uses(self, name: str) -> str:
        direct = self.index.callers(name)
        if not direct:
            return f"No program, file or copybook named {name} has users in the graph."
        lines = [f"  {d['from'].split(':', 1)[1]} {d['rel']} (line {d['line']})" for d in direct]
        impact = self.index.impact(name)
        return "DIRECT:\n" + "\n".join(lines) + f"\nIMPACT ({len(impact)} programs): {', '.join(impact)}"

    def search_code(self, pattern: str) -> str:
        rx = re.compile(pattern, re.I)
        hits = []
        for p in self.index.programs.values():
            for n, t in self.index.read_lines(p.path, 1, p.total_lines):
                if len(t) > 6 and t[6] in "*/":
                    continue
                if rx.search(t):
                    hits.append(f"{p.program_id}:{n}: {t.strip()}")
                    if len(hits) >= MAX_HITS:
                        return "\n".join(hits) + "\n... more hits, narrow the pattern"
        return "\n".join(hits) or "no hits"
