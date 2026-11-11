"""Tool-using agent over an OpenAI-compatible chat API (OpenAI, vLLM, LiteLLM gateway, ...).

Two jobs: extract business rules of one program, and answer an onboarding question. Both end in JSON that is
validated with Pydantic, then every citation is checked against the source by `citations.verify`.

A loop guard stops the agent from repeating the same tool call (the token-burning loop seen with enterprise
agents), and every run records token usage so the cost of each answer is known.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel, ValidationError

from .citations import verify
from .coerce import KINDS, coerce, loads_lenient
from .index import Index
from .schema import Answer, RuleSet
from .tools import Toolbox

SYSTEM_RULES = """You are a mainframe modernization analyst. You read COBOL and explain the business rules it encodes
to an engineer who joined the project today.

Method:
1. Start from the outline you are given. Read the paragraphs that decide something: IF/EVALUATE on business
   data, COMPUTE, READ ... INVALID KEY, error codes and messages, XCTL routing.
2. Skip pure plumbing (OPEN/CLOSE status checks, ABEND helpers) unless it changes business behaviour.
3. Open a copybook only when you need a field's meaning.

Rules for the answer:
- Each rule cites the exact lines (program, start_line, end_line) that implement it. Keep ranges tight, at most
  30 lines. Never cite a line you did not read.
- summary is plain language. condition and outcome name the values (codes, messages, limits) found in the code.
- fields lists the COBOL data names the rule reads or sets, spelled as in the code.
- Do not invent rules. If the program has none, return an empty list.

When done, reply with ONLY a JSON object matching this schema, no prose and no code fence:
{schema}"""

MAX_CALLS_PER_STEP = 5
CONTEXT_STOP = 0.6  # share of LLM_CONTEXT after which the agent is told to answer now

SYSTEM_CHUNK = """You are a mainframe modernization analyst. You get numbered lines from one paragraph of a COBOL
program. List every business rule these lines implement, for an engineer who joined the project today.

A business rule is one decision: an IF or WHEN branch that rejects input, sets an error message or code, chooses
where to go next (XCTL, PERFORM, RETURN), computes an amount, or reads or writes a business record under a
condition. Write one rule per decision, never one rule for the whole paragraph. Skip plumbing: file status checks
right after OPEN or CLOSE, screen header fill, ABEND helpers.

For each rule cite the tight range that implements it, usually 2 to 10 lines, using only line numbers shown.
condition and outcome name the values found in the code (codes, messages, limits). fields lists the COBOL data
names the rule reads or sets.

Reply with ONLY this JSON, no prose and no code fence. If the lines hold no business rule, reply {{"rules": []}}.
{{"rules": [{{"kind": "one of {kinds}", "summary": "...", "condition": "...", "outcome": "...",
"fields": ["..."], "citations": [{{"start_line": 0, "end_line": 0}}]}}]}}"""

CHUNK_LINES = 60  # lines per request in chunked mode; long paragraphs are cut between top-level statements
RE_DECISION = re.compile(r"\b(IF|EVALUATE|WHEN|COMPUTE|ADD|SUBTRACT|MULTIPLY|DIVIDE|XCTL|INVALID KEY|RETURN-CODE)\b")
RE_PLUMBING = re.compile(r"(-OPEN|-CLOSE|DISPLAY-IO-STATUS|ABEND)", re.I)

LANGUAGES = {"en": "English", "vi": "Vietnamese", "ja": "Japanese"}

SYSTEM_ASK = """You answer questions about a COBOL code base for an engineer who joined the project today.
Use the tools to find evidence. Cite every claim with (program, start_line, end_line) of lines you read.
If the code does not answer the question, say so. Reply with ONLY a JSON object matching this schema:
{schema}"""


@dataclass
class Trace:
    steps: int = 0
    tool_calls: int = 0
    blocked_repeats: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    max_prompt_tokens: int = 0  # largest single request: must stay below the model's context window
    repairs: int = 0
    nudges: int = 0
    capped_calls: int = 0  # tool calls ignored because one turn asked for more than MAX_CALLS_PER_STEP
    dropped_rules: int = 0
    chunks_failed: int = 0  # chunked mode: pieces whose answer stayed invalid JSON after one repair  # rules thrown away because they had no summary or no usable citation
    seconds: float = 0.0
    calls: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if k != "calls"} | {"calls": self.calls}


class LoopGuard:
    """Refuse a tool call identical to one already made in this run; the model gets the reason instead."""

    def __init__(self, max_repeats: int = 1):
        self.seen: dict[str, int] = {}
        self.max_repeats = max_repeats

    def check(self, name: str, arguments: str) -> str | None:
        try:
            key = name + json.dumps(json.loads(arguments or "{}"), sort_keys=True)
        except json.JSONDecodeError:
            key = name + (arguments or "")
        self.seen[key] = self.seen.get(key, 0) + 1
        if self.seen[key] > self.max_repeats:
            return (
                f"BLOCKED: you already called {name} with these arguments; the result is above. "
                "Use it, call a different tool, or give the final JSON."
            )
        return None


PROVIDER_URLS = {
    "GROQ_API_KEY": "https://api.groq.com/openai/v1",
    "GEMINI_API_KEY": "https://generativelanguage.googleapis.com/v1beta/openai/",
}


def llm_settings(env: dict[str, str] | None = None) -> dict[str, Any]:
    """Read the endpoint from the environment. OPENAI_* wins, then LLM_*, then a bare GROQ_/GEMINI_API_KEY."""
    env = dict(os.environ) if env is None else env
    base_url = env.get("OPENAI_BASE_URL") or env.get("LLM_BASE_URL") or None
    api_key = env.get("OPENAI_API_KEY") or env.get("LLM_API_KEY") or None
    if not api_key:
        for name, url in PROVIDER_URLS.items():
            if env.get(name):
                api_key, base_url = env[name], base_url or url
                break
    if not api_key and not base_url:
        raise RuntimeError(
            "No LLM endpoint configured. Set LLM_BASE_URL, LLM_API_KEY and LLM_MODEL in .env or as Codespaces "
            "secrets (see .env.example)."
        )
    return {
        "base_url": base_url,
        "api_key": api_key or "not-needed",  # local servers (Ollama, vLLM) accept any key
        "max_retries": int(env.get("LLM_MAX_RETRIES") or 6),
    }


def make_client():
    from openai import OpenAI

    return OpenAI(**llm_settings())


class Agent:
    def __init__(
        self, index: Index, client=None, model: str | None = None, max_steps: int = 16, temperature: float = 0.0
    ):
        self.index = index
        self.tools = Toolbox(index)
        self.client = client or make_client()
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.max_steps = max_steps
        self.temperature = temperature
        # seconds to wait between two LLM calls, to stay under a free tier's requests/tokens per minute
        self.pause = float(os.getenv("LLM_PAUSE") or 0)
        # context window of the served model (e.g. OLLAMA_CONTEXT_LENGTH). Ollama silently drops the start of a
        # prompt that is too long, so the run is flagged when a request comes close to it.
        self.context = int(os.getenv("LLM_CONTEXT") or 0)
        # Stream the reply so a slow GPU never leaves the connection silent: Cloudflare quick tunnels (Colab) cut a
        # request after 100 s without data (HTTP 524). On by default for trycloudflare URLs.
        flag = os.getenv("LLM_STREAM")
        base = str(getattr(self.client, "base_url", "") or "")
        self.stream = flag == "1" if flag in ("0", "1") else "trycloudflare.com" in base

    # ---------- public jobs ----------
    def extract_rules(self, program: str, lang: str = "en") -> tuple[RuleSet, list[dict], Trace]:
        prog = self.index.program(program)
        system = SYSTEM_RULES.format(schema=json.dumps(RuleSet.model_json_schema()))
        extra = os.getenv("LLM_EXTRA_RULES", "").strip()  # one-line prompt experiments without editing code
        if extra:
            system = system.replace("\n\nWhen done,", f"\n- {extra}\n\nWhen done,", 1)
        user = (
            f"Extract the business rules of program {prog.program_id}. Write purpose, summary, condition and "
            f"outcome in {LANGUAGES.get(lang, 'English')}; keep COBOL names, codes and messages as in the code."
            f"\n\nOutline:\n{self.tools.program_outline(prog.program_id)}"
        )
        result, trace = self._run(system, user, RuleSet, min_tool_calls=2, program=prog.program_id)
        checks = [verify(rule, self.index) for rule in result.rules]
        return result, checks, trace

    def chunks(self, program: str) -> list[tuple[str, int, int]]:
        """Paragraphs that hold a decision, cut into pieces of at most CHUNK_LINES lines. Static analysis picks
        what to read, so a small model only has to explain the lines in front of it."""
        prog = self.index.program(program)
        out: list[tuple[str, int, int]] = []
        for para in prog.paragraphs:
            if RE_PLUMBING.search(para.name):
                continue
            lines = [
                (n, t)
                for n, t in self.index.read_lines(prog.path, para.start, para.end)
                if len(t) > 7 and t[6] not in "*/"
            ]
            if not any(RE_DECISION.search(t[7:]) for _, t in lines):
                continue
            starts = {
                n: len(t[7:]) - len(t[7:].lstrip())
                for n, t in lines
                if re.match(r"\s*(IF|EVALUATE|WHEN|PERFORM|MOVE|EXEC|READ|WRITE|REWRITE|COMPUTE)\b", t[7:])
            }
            start = para.start
            while start <= para.end:
                end = min(para.end, start + CHUNK_LINES - 1)
                if end < para.end:  # cut before the least indented statement in the second half of the window
                    cut = [n for n in starts if start + CHUNK_LINES // 2 < n <= end]
                    if cut:
                        least = min(starts[n] for n in cut)
                        end = max(n for n in cut if starts[n] == least) - 1
                out.append((para.name, start, end))
                start = end + 1
        return out

    def extract_rules_chunked(self, program: str, lang: str = "en") -> tuple[RuleSet, list[dict], Trace]:
        prog = self.index.program(program)
        pid = prog.program_id
        trace = Trace()
        t0 = time.perf_counter()
        system = SYSTEM_CHUNK.format(kinds=", ".join(sorted(KINDS)))
        extra = os.getenv("LLM_EXTRA_RULES", "").strip()
        if extra:
            system = system.replace("\n\nReply with ONLY", f"\n{extra}\n\nReply with ONLY", 1)
        language = LANGUAGES.get(lang, "English")
        rules: list[Any] = []
        failed = 0
        for para, start, end in self.chunks(pid):
            code = self.tools.read_lines(pid, start, end)
            user = (
                f"Program {pid}, paragraph {para}, lines {start}-{end}. Write summary, condition and outcome in "
                f"{language}; keep COBOL names, codes and messages as in the code.\n\n{code}"
            )
            messages: list[dict[str, Any]] = [{"role": "system", "content": system}, {"role": "user", "content": user}]
            got = None
            for _attempt in range(2):
                if trace.steps and self.pause:
                    time.sleep(self.pause)
                trace.steps += 1
                msg, _ = self._complete(messages, trace, tools=False)
                text = msg.content or ""
                got, error, dropped = _parse(text, RuleSet, pid)
                if got is not None:
                    trace.dropped_rules += dropped
                    break
                trace.repairs += 1
                messages += [
                    {"role": "assistant", "content": text},
                    {"role": "user", "content": f"Your JSON is invalid: {error}. Reply with the corrected JSON only."},
                ]
            if got is None:
                failed += 1
                continue
            for r in got.rules:
                inside = [c for c in r.citations if c.program == pid and start <= c.start_line and c.end_line <= end]
                if not inside:  # cites lines it was not shown: cannot be trusted
                    trace.dropped_rules += 1
                    continue
                rules.append(r.model_copy(update={"citations": inside, "paragraph": r.paragraph or para}))
        for i, r in enumerate(rules, 1):
            r.id, r.program = f"{pid}-R{i}", pid
        trace.chunks_failed = failed
        purpose = self._purpose(pid, language, trace)
        trace.seconds = round(time.perf_counter() - t0, 2)
        self._warn_context(trace)
        result = RuleSet(program=pid, purpose=purpose, rules=rules)
        return result, [verify(rule, self.index) for rule in result.rules], trace

    def _purpose(self, pid: str, language: str, trace: Trace) -> str:
        trace.steps += 1
        messages = [
            {"role": "system", "content": "You explain COBOL programs to a new engineer. Reply with plain text only."},
            {
                "role": "user",
                "content": f"In two sentences in {language}, what does this program do for the business?\n\n"
                + self.tools.program_outline(pid),
            },
        ]
        msg, _ = self._complete(messages, trace, tools=False)
        return re.sub(r"<think>.*?</think>", "", msg.content or "", flags=re.S).strip()[:600]

    def ask(self, question: str) -> tuple[Answer, list[dict], Trace]:
        system = SYSTEM_ASK.format(schema=json.dumps(Answer.model_json_schema()))
        programs = ", ".join(sorted(self.index.programs))
        result, trace = self._run(
            system, f"Programs in the code base: {programs}\n\nQuestion: {question}", Answer, min_tool_calls=1
        )
        checks = [verify(c, self.index) for c in result.citations]
        return result, checks, trace

    # ---------- loop ----------
    def _run(
        self, system: str, user: str, model_cls: type[BaseModel], min_tool_calls: int = 0, program: str | None = None
    ) -> tuple[Any, Trace]:
        trace = Trace()
        guard = LoopGuard()
        t0 = time.perf_counter()
        messages: list[dict[str, Any]] = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        final_text = None
        error = None
        fallback: tuple[Any, int] | None = None
        nudges = 0
        full_warned = False
        while trace.steps < self.max_steps:
            if trace.steps and self.pause:
                time.sleep(self.pause)
            trace.steps += 1
            msg, finish = self._complete(messages, trace)
            tool_calls = getattr(msg, "tool_calls", None) or []
            if len(tool_calls) > MAX_CALLS_PER_STEP:  # small models sometimes emit hundreds of calls in one turn
                trace.capped_calls += len(tool_calls) - MAX_CALLS_PER_STEP
                tool_calls = tool_calls[:MAX_CALLS_PER_STEP]
            if not tool_calls:
                final_text = msg.content or ""
                # Small open models often answer from the outline alone, or reply with nothing. Send them back to
                # the code a couple of times before accepting an answer; these nudges are not JSON repairs.
                if nudges < 2 and (not final_text.strip() or trace.tool_calls < min_tool_calls):
                    nudges += 1
                    trace.nudges += 1
                    why = (
                        "Your reply was empty"
                        if not final_text.strip()
                        else "You answered without reading any code, so your citations cannot be trusted"
                    )
                    messages.append({"role": "assistant", "content": final_text})
                    messages.append(
                        {
                            "role": "user",
                            "content": f"{why}. Call read_paragraph or read_lines on the relevant code first, "
                            "then reply with the JSON, citing only lines you read.",
                        }
                    )
                    continue
                parsed, error, dropped = _parse(final_text, model_cls, program)
                if parsed is not None and (not dropped or trace.repairs >= 2):
                    trace.dropped_rules = dropped
                    trace.seconds = round(time.perf_counter() - t0, 2)
                    self._warn_context(trace)
                    return parsed, trace
                if parsed is not None:  # usable, but some rules lost: ask once more, keep this as a fallback
                    fallback = (parsed, dropped)
                    error = (
                        f"{dropped} rule(s) had no summary or no citation with program, start_line and end_line, "
                        "so they would be removed"
                    )
                if trace.repairs >= 2:
                    break
                trace.repairs += 1
                messages.append({"role": "assistant", "content": final_text})
                messages.append(
                    {"role": "user", "content": f"Your JSON is invalid: {error}. Reply with the corrected JSON only."}
                )
                continue
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in tool_calls
                    ],
                }
            )
            for tc in tool_calls:
                trace.tool_calls += 1
                trace.calls.append(f"{tc.function.name}({tc.function.arguments})")
                blocked = guard.check(tc.function.name, tc.function.arguments)
                if blocked:
                    trace.blocked_repeats += 1
                    content = blocked
                else:
                    content = self.tools.call(tc.function.name, tc.function.arguments)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": content})
            if trace.steps == self.max_steps - 1:
                messages.append({"role": "user", "content": "Step budget almost used. Give the final JSON now."})
            elif self.context and trace.max_prompt_tokens >= CONTEXT_STOP * self.context and not full_warned:
                # Ollama silently drops the start of an over-long prompt (the instructions): stop reading in time
                full_warned = True
                messages.append(
                    {
                        "role": "user",
                        "content": "The context window is nearly full. Stop reading; give the final JSON now.",
                    }
                )
        trace.seconds = round(time.perf_counter() - t0, 2)
        self._warn_context(trace)
        if fallback:
            trace.dropped_rules = fallback[1]
            return fallback[0], trace
        raise RuntimeError(
            f"agent did not return valid JSON in {trace.steps} steps ({trace.tool_calls} tool calls, finish_reason "
            f"{finish}); last error: {str(error)[:400]}; last output: {str(final_text)[:300]!r}"
        )

    def _complete(self, messages: list[dict[str, Any]], trace: Trace, tools: bool = True) -> tuple[Any, str | None]:
        kwargs: dict[str, Any] = dict(model=self.model, messages=messages, temperature=self.temperature)
        if tools:
            kwargs["tools"] = self.tools.specs()
        if not self.stream:
            resp = self.client.chat.completions.create(**kwargs)
            self._count(resp, trace)
            return resp.choices[0].message, getattr(resp.choices[0], "finish_reason", None)
        chunks = self.client.chat.completions.create(**kwargs, stream=True, stream_options={"include_usage": True})
        msg, finish, usage = merge_stream(chunks)
        self._count(SimpleNamespace(usage=usage), trace)
        return msg, finish

    @staticmethod
    def _count(resp, trace: Trace) -> None:
        usage = getattr(resp, "usage", None)
        if usage:
            trace.prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
            trace.completion_tokens += getattr(usage, "completion_tokens", 0) or 0
            trace.max_prompt_tokens = max(trace.max_prompt_tokens, getattr(usage, "prompt_tokens", 0) or 0)

    def _warn_context(self, trace: Trace) -> None:
        if self.context and trace.max_prompt_tokens >= 0.9 * self.context:
            print(
                f"WARNING: a request used {trace.max_prompt_tokens} of {self.context} context tokens; the model may "
                "have lost the start of the conversation. Raise the context length or lower --max-steps.",
                file=sys.stderr,
            )


def merge_stream(chunks) -> tuple[Any, str | None, Any]:
    """Join streamed chunks back into one message (content + tool calls), its finish_reason and usage."""
    content: list[str] = []
    calls: dict[int, dict[str, str]] = {}
    finish = usage = None
    for chunk in chunks:
        usage = getattr(chunk, "usage", None) or usage
        for choice in getattr(chunk, "choices", None) or []:
            finish = getattr(choice, "finish_reason", None) or finish
            delta = choice.delta
            if getattr(delta, "content", None):
                content.append(delta.content)
            for i, tc in enumerate(getattr(delta, "tool_calls", None) or []):
                idx = getattr(tc, "index", None)
                if idx is None:  # servers without index: a new id starts a new call
                    new_id = getattr(tc, "id", None)
                    last = max(calls) if calls else None
                    idx = last if last is not None and (not new_id or calls[last]["id"] in ("", new_id)) else len(calls)
                    idx += i
                slot = calls.setdefault(idx, {"id": "", "name": "", "arguments": ""})
                slot["id"] = getattr(tc, "id", None) or slot["id"]
                fn = getattr(tc, "function", None)
                if fn is not None:
                    slot["name"] += getattr(fn, "name", None) or ""
                    slot["arguments"] += getattr(fn, "arguments", None) or ""
    tool_calls = [
        SimpleNamespace(
            id=c["id"] or f"call_{i}", function=SimpleNamespace(name=c["name"], arguments=c["arguments"] or "{}")
        )
        for i, c in sorted(calls.items())
    ]
    return SimpleNamespace(content="".join(content), tool_calls=tool_calls), finish, usage


def _parse(text: str, model_cls: type[BaseModel], program: str | None = None):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()  # reasoning models (Qwen3, DeepSeek-R1)
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
    start, end = text.find("{"), text.rfind("}")
    if text.lstrip().startswith("["):  # a bare list of rules
        start, end = text.find("["), text.rfind("]")
    if start < 0 or end < 0:
        return None, "no JSON object found", 0
    try:
        data = loads_lenient(text[start : end + 1])
    except json.JSONDecodeError as exc:
        return None, f"not valid JSON: {exc}", 0
    data, dropped = coerce(data, model_cls, program)
    try:
        return model_cls.model_validate(data), None, dropped
    except ValidationError as exc:
        return None, str(exc)[:800], dropped
