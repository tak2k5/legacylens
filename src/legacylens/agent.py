"""Tool-using agent over an OpenAI-compatible chat API (OpenAI, vLLM, LiteLLM gateway, ...).

Two jobs: extract business rules of one program, and answer an onboarding question. Both end in JSON that is
validated with Pydantic, then every citation is checked against the source by `citations.verify`.

A loop guard stops the agent from repeating the same tool call (the token-burning loop seen with enterprise
agents), and every run records token usage so the cost of each answer is known.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ValidationError

from .citations import verify
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
    repairs: int = 0
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

    # ---------- public jobs ----------
    def extract_rules(self, program: str, lang: str = "en") -> tuple[RuleSet, list[dict], Trace]:
        prog = self.index.program(program)
        system = SYSTEM_RULES.format(schema=json.dumps(RuleSet.model_json_schema()))
        user = (
            f"Extract the business rules of program {prog.program_id}. Write purpose, summary, condition and "
            f"outcome in {LANGUAGES.get(lang, 'English')}; keep COBOL names, codes and messages as in the code."
            f"\n\nOutline:\n{self.tools.program_outline(prog.program_id)}"
        )
        result, trace = self._run(system, user, RuleSet)
        checks = [verify(rule, self.index) for rule in result.rules]
        return result, checks, trace

    def ask(self, question: str) -> tuple[Answer, list[dict], Trace]:
        system = SYSTEM_ASK.format(schema=json.dumps(Answer.model_json_schema()))
        programs = ", ".join(sorted(self.index.programs))
        result, trace = self._run(system, f"Programs in the code base: {programs}\n\nQuestion: {question}", Answer)
        checks = [verify(c, self.index) for c in result.citations]
        return result, checks, trace

    # ---------- loop ----------
    def _run(self, system: str, user: str, model_cls: type[BaseModel]) -> tuple[Any, Trace]:
        trace = Trace()
        guard = LoopGuard()
        t0 = time.perf_counter()
        messages: list[dict[str, Any]] = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        final_text = None
        while trace.steps < self.max_steps:
            if trace.steps and self.pause:
                time.sleep(self.pause)
            trace.steps += 1
            resp = self.client.chat.completions.create(
                model=self.model, messages=messages, tools=self.tools.specs(), temperature=self.temperature
            )
            self._count(resp, trace)
            msg = resp.choices[0].message
            tool_calls = getattr(msg, "tool_calls", None) or []
            if not tool_calls:
                final_text = msg.content or ""
                parsed, error = _parse(final_text, model_cls)
                if parsed is not None:
                    trace.seconds = round(time.perf_counter() - t0, 2)
                    return parsed, trace
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
        trace.seconds = round(time.perf_counter() - t0, 2)
        raise RuntimeError(
            f"agent did not return valid JSON in {trace.steps} steps; last output: {str(final_text)[:300]}"
        )

    @staticmethod
    def _count(resp, trace: Trace) -> None:
        usage = getattr(resp, "usage", None)
        if usage:
            trace.prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
            trace.completion_tokens += getattr(usage, "completion_tokens", 0) or 0


def _parse(text: str, model_cls: type[BaseModel]):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        return None, "no JSON object found"
    try:
        return model_cls.model_validate_json(text[start : end + 1]), None
    except ValidationError as exc:
        return None, str(exc)[:800]
