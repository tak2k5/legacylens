"""Static parser for fixed-format COBOL (IBM Enterprise COBOL style).

It does not try to be a full COBOL grammar. It extracts the facts the agent needs to stay grounded:
program id, copybooks, static and dynamic calls, CICS commands, files, paragraphs and PERFORM edges,
each with the line number where it appears. Everything the LLM later claims must be checkable against these facts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

COBOL_SUFFIXES = {".cbl", ".cob", ".cobol"}
COPYBOOK_SUFFIXES = {".cpy", ".copy"}

_NAME = r"[A-Z0-9][A-Z0-9-]*"
RE_PROGRAM_ID = re.compile(rf"PROGRAM-ID\.\s*({_NAME})", re.I)
RE_COPY = re.compile(rf"^\s*COPY\s+['\"]?({_NAME})['\"]?", re.I)
RE_CALL = re.compile(rf"(?<![A-Z0-9-])CALL\s+(?:'({_NAME})'|\"({_NAME})\"|({_NAME}))", re.I)
RE_PARAGRAPH = re.compile(rf"^({_NAME})(\s+SECTION)?\s*\.\s*$", re.I)
RE_PERFORM = re.compile(rf"(?<![A-Z0-9-])PERFORM\s+({_NAME})(?:\s+(?:THRU|THROUGH)\s+({_NAME}))?", re.I)
RE_SELECT = re.compile(rf"\bSELECT\s+({_NAME})\s+ASSIGN\s+TO\s+({_NAME})", re.I)
RE_OPEN = re.compile(r"\bOPEN\s+(INPUT|OUTPUT|I-O|EXTEND)\s+([A-Z0-9-]+(?:\s+[A-Z0-9-]+)*)", re.I)
RE_VALUE = re.compile(rf"^\s*\d\d\s+({_NAME})\s+.*?\bVALUE\s+'([^']+)'", re.I)
RE_MOVE_LIT = re.compile(rf"\bMOVE\s+'([^']+)'\s+TO\s+({_NAME})", re.I)
RE_MOVE_VAR = re.compile(rf"\bMOVE\s+({_NAME})\s+TO\s+({_NAME})", re.I)
RE_DATA_ITEM = re.compile(rf"^\s*\d\d\s+({_NAME})\b", re.I)
RE_CICS_OPT = re.compile(rf"\b(PROGRAM|FILE|DATASET|MAP|MAPSET|TRANSID)\s*\(\s*(?:'([^']+)'|({_NAME}))\s*\)", re.I)

# Words that can follow PERFORM but are not paragraph names.
PERFORM_KEYWORDS = {"UNTIL", "VARYING", "WITH", "TEST", "TIMES", "FOREVER"}
CICS_FILE_VERBS = {"READ", "WRITE", "REWRITE", "DELETE", "STARTBR", "READNEXT", "READPREV", "ENDBR", "RESETBR"}
CICS_WRITE_VERBS = {"WRITE", "REWRITE", "DELETE"}


@dataclass
class Ref:
    name: str
    line: int


@dataclass
class CicsCommand:
    verb: str
    line: int
    end_line: int
    options: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class FileOp:
    file: str
    mode: str  # read | write | read-write
    line: int


@dataclass
class Paragraph:
    name: str
    start: int
    end: int
    performs: list[Ref] = field(default_factory=list)


@dataclass
class Program:
    program_id: str
    path: str
    total_lines: int
    loc: int
    kind: str  # online (CICS) | batch
    copybooks: list[Ref] = field(default_factory=list)
    calls: list[Ref] = field(default_factory=list)
    cics: list[CicsCommand] = field(default_factory=list)
    selects: dict[str, str] = field(default_factory=dict)  # logical file -> DD name
    file_ops: list[FileOp] = field(default_factory=list)
    paragraphs: list[Paragraph] = field(default_factory=list)
    literals: dict[str, set[str]] = field(default_factory=dict)  # variable -> literals it can hold
    aliases: dict[str, set[str]] = field(default_factory=dict)  # variable -> variables moved into it

    def paragraph(self, name: str) -> Paragraph | None:
        name = name.upper()
        return next((p for p in self.paragraphs if p.name == name), None)

    def paragraph_at(self, line: int) -> Paragraph | None:
        return next((p for p in self.paragraphs if p.start <= line <= p.end), None)

    def transfers(self) -> list[tuple[str, str, int]]:
        """(verb, target program, line) for CICS XCTL/LINK and static CALL, dynamic targets resolved."""
        out: list[tuple[str, str, int]] = []
        for cmd in self.cics:
            if cmd.verb in {"XCTL", "LINK"}:
                for target in cmd.options.get("PROGRAM", []):
                    out.extend((cmd.verb, t, cmd.line) for t in self.resolve(target))
        for call in self.calls:
            out.extend(("CALL", t, call.line) for t in self.resolve(call.name))
        return out

    def resolve(self, token: str) -> list[str]:
        """A literal stays as is; a variable becomes every literal it can hold via VALUE or MOVE.

        MOVE var TO var is followed transitively. A variable with no literal source stays as its own name,
        which marks a target only known at run time (for example the caller's program name).
        """
        if token.startswith("'"):
            return [token.strip("'").upper()]
        found: set[str] = set()
        seen: set[str] = set()
        stack = [token.upper()]
        while stack:
            var = stack.pop()
            if var in seen:
                continue
            seen.add(var)
            found |= self.literals.get(var, set())
            stack.extend(self.aliases.get(var, ()))
        return sorted(found) if found else [token.upper()]


def code_lines(path: Path) -> list[tuple[int, str]]:
    """Return (line number, code area) pairs; comment and debug lines are dropped.

    Fixed format: columns 1-6 sequence area, 7 indicator, 8-72 code. Line numbers are 1-based and match the file.
    """
    out: list[tuple[int, str]] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for no, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip("\n")
        if len(line) > 6 and line[6] in "*/Dd":
            continue
        code = line[7:72] if len(line) > 7 else ""
        out.append((no, code.rstrip()))
    return out


def _statement_spans(lines: list[tuple[int, str]], start_idx: int, terminator: re.Pattern[str]) -> tuple[str, int, int]:
    """Join lines from start_idx until terminator matches; returns (text, last index, last line number)."""
    parts = []
    idx = start_idx
    while idx < len(lines):
        parts.append(lines[idx][1].strip())
        if terminator.search(lines[idx][1]):
            break
        idx += 1
    idx = min(idx, len(lines) - 1)
    return " ".join(parts), idx, lines[idx][0]


RE_END_EXEC = re.compile(r"END-EXEC", re.I)
RE_PERIOD = re.compile(r"\.\s*$")


def parse_program(path: Path) -> Program:
    lines = code_lines(path)
    total = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    loc = sum(1 for _, c in lines if c.strip())
    program_id = path.stem.upper()
    prog = Program(program_id=program_id, path=str(path), total_lines=total, loc=loc, kind="batch")

    in_procedure = False
    current: Paragraph | None = None
    i = 0
    while i < len(lines):
        no, code = lines[i]
        upper = code.upper()
        stripped = upper.strip()

        if m := RE_PROGRAM_ID.search(upper):
            prog.program_id = m.group(1)
        if m := RE_COPY.match(upper):
            prog.copybooks.append(Ref(m.group(1), no))
        if not in_procedure and RE_DATA_ITEM.match(upper):
            # A data item may put VALUE on the next line; join up to the closing period.
            text, _, _ = _statement_spans(lines, i, RE_PERIOD)
            if m := RE_VALUE.match(text.upper()):
                prog.literals.setdefault(m.group(1), set()).add(m.group(2).strip())
        for m in RE_MOVE_LIT.finditer(upper):
            prog.literals.setdefault(m.group(2), set()).add(m.group(1).strip())
        for m in RE_MOVE_VAR.finditer(_mask_strings(upper)):
            prog.aliases.setdefault(m.group(2), set()).add(m.group(1))
        if "SELECT " in upper:
            text, _, _ = _statement_spans(lines, i, RE_PERIOD)
            if m := RE_SELECT.search(text.upper()):
                prog.selects[m.group(1)] = m.group(2)
        if stripped.startswith("PROCEDURE DIVISION"):
            in_procedure = True
            i += 1
            continue

        if "EXEC CICS" in upper:
            text, end_idx, end_no = _statement_spans(lines, i, RE_END_EXEC)
            text_u = text.upper()
            after = text_u.split("EXEC CICS", 1)[1].split()
            verb = after[0] if after else "?"
            cmd = CicsCommand(verb=verb, line=no, end_line=end_no)
            for m in RE_CICS_OPT.finditer(text_u):
                value = f"'{m.group(2)}'" if m.group(2) else m.group(3)
                cmd.options.setdefault(m.group(1), []).append(value)
            prog.cics.append(cmd)
            prog.kind = "online"
            for f in cmd.options.get("FILE", []) + cmd.options.get("DATASET", []):
                if verb in CICS_FILE_VERBS:
                    mode = "write" if verb in CICS_WRITE_VERBS else "read"
                    for target in prog.resolve(f):
                        prog.file_ops.append(FileOp(target, mode, no))
            if current:
                current.end = end_no
            i = end_idx + 1
            continue

        if in_procedure:
            # Paragraph headers start in Area A (column 8), i.e. the code area does not start with a space.
            if code and not code[0].isspace() and (m := RE_PARAGRAPH.match(stripped)):
                if current:
                    current.end = _last_code_line(lines, i - 1, current.start)
                current = Paragraph(name=m.group(1), start=no, end=no)
                prog.paragraphs.append(current)
            elif current:
                current.end = no
            elif stripped:
                # Statements right after PROCEDURE DIVISION, before the first paragraph header.
                current = Paragraph(name="MAIN", start=no, end=no)
                prog.paragraphs.append(current)
            masked = _mask_strings(upper)
            for m in RE_PERFORM.finditer(masked):
                target = m.group(1)
                if target in PERFORM_KEYWORDS or target.isdigit():
                    continue
                if current:
                    current.performs.append(Ref(target, no))
                    if m.group(2):
                        current.performs.append(Ref(m.group(2), no))
            for m in RE_CALL.finditer(upper):
                if _inside_string(upper, m.start()):
                    continue
                name = m.group(1) or m.group(2)
                prog.calls.append(Ref(f"'{name}'" if name else m.group(3), no))
            if m := RE_OPEN.search(masked):
                mode = {"INPUT": "read", "OUTPUT": "write", "EXTEND": "write", "I-O": "read-write"}[m.group(1)]
                for f in m.group(2).split():
                    prog.file_ops.append(FileOp(f, mode, no))
        i += 1

    if current:
        current.end = _last_code_line(lines, len(lines) - 1, current.start)
    return prog


RE_STRING = re.compile(r"'[^']*'|\"[^\"]*\"")


def _mask_strings(code: str) -> str:
    """Blank out string literals so words inside DISPLAY 'CALL FAILED' are not read as code."""
    return RE_STRING.sub(lambda m: " " * len(m.group(0)), code)


def _inside_string(code: str, pos: int) -> bool:
    return any(m.start() < pos < m.end() for m in RE_STRING.finditer(code))


def _last_code_line(lines: list[tuple[int, str]], idx: int, floor: int) -> int:
    while idx >= 0 and not lines[idx][1].strip():
        idx -= 1
    return max(lines[idx][0], floor) if idx >= 0 else floor


@dataclass
class Copybook:
    name: str
    path: str
    total_lines: int
    fields: list[Ref] = field(default_factory=list)


RE_FIELD = re.compile(rf"^\s*(\d\d)\s+({_NAME})", re.I)


def parse_copybook(path: Path) -> Copybook:
    cb = Copybook(name=path.stem.upper(), path=str(path), total_lines=0)
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    cb.total_lines = len(text)
    for no, code in code_lines(path):
        if m := RE_FIELD.match(code.upper()):
            if m.group(2) != "FILLER":
                cb.fields.append(Ref(m.group(2), no))
    return cb


@dataclass
class JclStep:
    job: str
    step: str
    program: str
    line: int
    dds: dict[str, str] = field(default_factory=dict)  # DD name -> dataset name


RE_JOB = re.compile(r"^//(\S+)\s+JOB\b", re.I)
RE_STEP = re.compile(r"^//(\S+)\s+EXEC\s+(?:PGM=)([A-Z0-9#@$]+)", re.I)
RE_DD = re.compile(r"^//(\S+)\s+DD\b.*?\bDSN=([A-Z0-9.#@$()+-]+)", re.I)
RE_DD_CONT = re.compile(r"^//\s+.*?\bDSN=([A-Z0-9.#@$()+-]+)", re.I)


def parse_jcl(path: Path) -> list[JclStep]:
    job = path.stem.upper()
    steps: list[JclStep] = []
    last_dd: str | None = None
    for no, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = raw[:72]
        if line.startswith("//*"):
            continue
        if m := RE_JOB.match(line):
            job = m.group(1).upper()
        elif m := RE_STEP.match(line):
            steps.append(JclStep(job=job, step=m.group(1).upper(), program=m.group(2).upper(), line=no))
            last_dd = None
        elif steps and (m := RE_DD.match(line)):
            last_dd = m.group(1).upper()
            steps[-1].dds[last_dd] = m.group(2).upper()
        elif steps and line.startswith("//") and not line.startswith("// ") and " DD " in line.upper():
            last_dd = line[2:].split()[0].upper()
        elif steps and last_dd and (m := RE_DD_CONT.match(line)) and last_dd not in steps[-1].dds:
            steps[-1].dds[last_dd] = m.group(1).upper()
    return steps
