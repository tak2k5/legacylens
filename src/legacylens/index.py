"""Load a COBOL source tree into one index and a dependency graph."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx

from .parser import (
    COBOL_SUFFIXES,
    COPYBOOK_SUFFIXES,
    Copybook,
    JclStep,
    Program,
    parse_copybook,
    parse_jcl,
    parse_program,
)


@dataclass
class Index:
    root: Path
    programs: dict[str, Program] = field(default_factory=dict)
    copybooks: dict[str, Copybook] = field(default_factory=dict)
    jcl_steps: list[JclStep] = field(default_factory=list)
    graph: nx.MultiDiGraph = field(default_factory=nx.MultiDiGraph)

    # ---------- loading ----------
    @classmethod
    def build(cls, root: str | Path) -> Index:
        root = Path(root)
        idx = cls(root=root)
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix in COBOL_SUFFIXES:
                prog = parse_program(path)
                idx.programs.setdefault(prog.program_id, prog)
            elif suffix in COPYBOOK_SUFFIXES:
                cb = parse_copybook(path)
                idx.copybooks.setdefault(cb.name, cb)
            elif suffix in {".jcl", ".prc", ".proc"}:
                idx.jcl_steps.extend(parse_jcl(path))
        idx._build_graph()
        return idx

    def _build_graph(self) -> None:
        g = self.graph
        for prog in self.programs.values():
            p = f"program:{prog.program_id}"
            g.add_node(p, kind="program", name=prog.program_id, program_kind=prog.kind, loc=prog.loc)
            for ref in prog.copybooks:
                c = f"copybook:{ref.name}"
                g.add_node(c, kind="copybook", name=ref.name, known=ref.name in self.copybooks)
                g.add_edge(p, c, rel="copies", line=ref.line)
            for verb, target, line in prog.transfers():
                t = f"program:{target}"
                if t not in g:
                    g.add_node(t, kind="program", name=target, external=target not in self.programs)
                g.add_edge(p, t, rel=verb.lower(), line=line)
            for op in prog.file_ops:
                f = f"file:{self.dataset_for(prog, op.file)}"
                g.add_node(f, kind="file", name=f.split(":", 1)[1])
                if op.mode in {"read", "read-write"}:
                    g.add_edge(f, p, rel="read_by", line=op.line)
                if op.mode in {"write", "read-write"}:
                    g.add_edge(p, f, rel="writes", line=op.line)
        for step in self.jcl_steps:
            j = f"job:{step.job}"
            g.add_node(j, kind="job", name=step.job)
            t = f"program:{step.program}"
            if t not in g:
                g.add_node(t, kind="program", name=step.program, external=step.program not in self.programs)
            g.add_edge(j, t, rel="runs", line=step.line, step=step.step)

    def dataset_for(self, prog: Program, logical: str) -> str:
        """Map a batch logical file to its DD name (and the JCL dataset when a job runs the program)."""
        dd = prog.selects.get(logical)
        if dd is None:
            return logical  # CICS file names are already the resource name
        for step in self.jcl_steps:
            if step.program == prog.program_id and dd in step.dds:
                return step.dds[dd]
        return dd

    # ---------- queries ----------
    def program(self, name: str) -> Program:
        key = name.upper()
        if key not in self.programs:
            raise KeyError(f"unknown program {name}; known: {', '.join(sorted(self.programs))}")
        return self.programs[key]

    def read_lines(self, path: str, start: int, end: int) -> list[tuple[int, str]]:
        text = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(1, start)
        end = min(len(text), end)
        return [(n, text[n - 1].rstrip()[:72]) for n in range(start, end + 1)]

    def callers(self, name: str) -> list[dict]:
        """Who depends on this program, copybook or file (one hop)."""
        name = name.upper()
        out = []
        for node in (f"program:{name}", f"copybook:{name}", f"file:{name}"):
            if node not in self.graph:
                continue
            for src, _, data in self.graph.in_edges(node, data=True):
                out.append({"from": src, "rel": data["rel"], "line": data.get("line")})
            if node.startswith("file:"):
                for _, dst, data in self.graph.out_edges(node, data=True):
                    out.append({"from": dst, "rel": data["rel"], "line": data.get("line")})
        return out

    def impact(self, name: str) -> list[str]:
        """Every program that can be affected by changing a copybook, file or program (transitive callers)."""
        name = name.upper()
        seeds = [n for n in (f"program:{name}", f"copybook:{name}", f"file:{name}") if n in self.graph]
        hit: set[str] = set()
        frontier = list(seeds)
        while frontier:
            node = frontier.pop()
            neighbours = [s for s, _ in self.graph.in_edges(node)]
            if node.startswith("file:"):
                neighbours += [d for _, d in self.graph.out_edges(node)]
            for n in neighbours:
                if n.startswith("program:") and n not in hit:
                    hit.add(n)
                    frontier.append(n)
        return sorted(h.split(":", 1)[1] for h in hit if h not in seeds)

    def stats(self) -> dict:
        kinds: dict[str, int] = {}
        for _, data in self.graph.nodes(data=True):
            kinds[data["kind"]] = kinds.get(data["kind"], 0) + 1
        return {
            "programs": len(self.programs),
            "online_programs": sum(p.kind == "online" for p in self.programs.values()),
            "batch_programs": sum(p.kind == "batch" for p in self.programs.values()),
            "copybooks": len(self.copybooks),
            "jcl_steps": len(self.jcl_steps),
            "loc": sum(p.loc for p in self.programs.values()),
            "paragraphs": sum(len(p.paragraphs) for p in self.programs.values()),
            "graph_nodes": self.graph.number_of_nodes(),
            "graph_edges": self.graph.number_of_edges(),
            "nodes_by_kind": kinds,
        }

    # ---------- export ----------
    def to_json(self) -> str:
        data = nx.node_link_data(self.graph, edges="edges")
        return json.dumps({"stats": self.stats(), "graph": data}, indent=2, default=str)

    def to_mermaid(self, focus: str | None = None) -> str:
        """Program-level flow (calls, XCTL, LINK, jobs, files). With focus, only that node's neighbourhood."""
        g = self.graph
        nodes = set(g.nodes)
        if focus:
            f = next((n for n in g.nodes if n.split(":", 1)[1] == focus.upper()), None)
            if f is None:
                raise KeyError(focus)
            nodes = {f} | set(g.predecessors(f)) | set(g.successors(f))
        shape = {"program": ("[", "]"), "job": ("[[", "]]"), "file": ("[(", ")]"), "copybook": ("[/", "/]")}
        lines = ["flowchart LR"]
        ids = {n: f"n{i}" for i, n in enumerate(sorted(nodes))}
        for n in sorted(nodes):
            kind = g.nodes[n]["kind"]
            if kind == "copybook" and not focus:
                continue
            o, c = shape[kind]
            lines.append(f'    {ids[n]}{o}"{g.nodes[n]["name"]}"{c}')
        seen = set()
        for u, v, data in g.edges(data=True):
            if u not in nodes or v not in nodes:
                continue
            if not focus and "copybook" in (g.nodes[u]["kind"], g.nodes[v]["kind"]):
                continue
            key = (u, v, data["rel"])
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"    {ids[u]} -- {data['rel']} --> {ids[v]}")
        return "\n".join(lines)
