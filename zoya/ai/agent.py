"""Autonomous AI agent framework for task execution and decision-making."""

from __future__ import annotations

import builtins
import json
import re
from collections.abc import Callable, Iterator
from typing import Any, TypedDict


class Tool:
    def __init__(self, name: str, description: str, func: Callable[..., str]) -> None:
        if not name or not isinstance(name, str):
            raise ValueError("Tool name must be a non-empty string")
        if not description or not isinstance(description, str):
            raise ValueError("Tool description must be a non-empty string")
        if not callable(func):
            raise ValueError("Tool func must be callable")
        self.name = name
        self.description = description
        self.func = func

    def execute(self, **kwargs: Any) -> str:
        return self.func(**kwargs)

    def __repr__(self) -> str:
        return f"Tool({self.name}: {self.description})"


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if not isinstance(tool, Tool):
            raise ValueError("Must register a Tool instance")
        self._tools[tool.name] = tool

    def register_all(self, tools: builtins.list[Tool]) -> None:
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list(self) -> builtins.list[Tool]:
        return list(self._tools.values())

    def descriptions(self) -> str:
        if not self._tools:
            return "No tools available."
        lines: list[str] = []
        for tool in self._tools.values():
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)

    def remove(self, name: str) -> None:
        self._tools.pop(name, None)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


class AgentMemory:
    def __init__(self) -> None:
        self._messages: list[dict[str, str]] = []

    def add(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})

    def get_history(self) -> list[dict[str, str]]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self) -> Iterator[dict[str, str]]:
        return iter(self._messages)


class AgentConfig(TypedDict, total=False):
    provider: Any
    tools: Any
    memory: Any
    system_prompt: str
    max_iterations: int
    temperature: float
    max_tokens: int


class AgentError(Exception):
    pass


class Agent:
    def __init__(self, config: AgentConfig) -> None:
        self.provider = config.get("provider")
        if self.provider is None:
            raise AgentError("LLM provider is required")

        self.tools: ToolRegistry = config.get("tools") or ToolRegistry()
        if not isinstance(self.tools, ToolRegistry):
            raise AgentError("tools must be a ToolRegistry instance")

        self.memory: AgentMemory = config.get("memory") or AgentMemory()
        if not isinstance(self.memory, AgentMemory):
            raise AgentError("memory must be an AgentMemory instance")

        self.system_prompt = config.get("system_prompt", "You are a helpful AI assistant.")
        self.max_iterations = config.get("max_iterations", 10)
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1024)

    def _build_prompt(self, prompt: str) -> str:
        tool_descriptions = self.tools.descriptions()
        history_lines: list[str] = []
        for msg in self.memory.get_history():
            role = msg["role"].capitalize()
            history_lines.append(f"{role}: {msg['content']}")

        conversation = "\n".join(history_lines) if history_lines else ""

        parts = [
            self.system_prompt,
            "",
            "You have access to the following tools:",
            tool_descriptions,
            "",
            "When you need to use a tool, respond with:",
            "Action: <tool_name>",
            'Action Input: {"param": "value"}',
            "",
            "After you receive the observation, continue reasoning.",
            "When you have the final answer, respond with:",
            "Answer: <your final response>",
            "",
            "Conversation:",
            conversation,
            f"User: {prompt}",
            "Assistant:",
        ]
        return "\n".join(parts)

    def _parse_tool_call(self, response: str) -> tuple[str, dict[str, Any]] | None:
        action_match = re.search(
            r"Action:\s*(\w[\w_-]*)\s*\n\s*Action Input:\s*(\{.*?\}|`[^`]+`|.+?)(?=\n|$)",
            response,
            re.DOTALL,
        )
        if action_match:
            tool_name = action_match.group(1).strip()
            raw_input = action_match.group(2).strip().strip("`")
            try:
                tool_input = json.loads(raw_input)
            except (json.JSONDecodeError, ValueError):
                tool_input = {"input": raw_input}
            return tool_name, tool_input

        json_match = re.search(
            r'\{\s*"function"\s*:\s*"(\w[\w_-]*)"\s*,\s*"arguments"\s*:\s*(\{.*?\})\s*\}',
            response,
            re.DOTALL,
        )
        if json_match:
            tool_name = json_match.group(1).strip()
            try:
                tool_input = json.loads(json_match.group(2))
            except (json.JSONDecodeError, ValueError):
                tool_input = {}
            return tool_name, tool_input

        func_call_match = re.search(
            r'function_call["\']?\s*[:=]\s*["\'](\w[\w_-]*)["\'].*?arguments["\']?\s*[:=]\s*(\{.*?\})',
            response,
            re.DOTALL,
        )
        if func_call_match:
            tool_name = func_call_match.group(1).strip()
            try:
                tool_input = json.loads(func_call_match.group(2))
            except (json.JSONDecodeError, ValueError):
                tool_input = {}
            return tool_name, tool_input

        return None

    def _call_llm(self, prompt: str) -> str:
        return self.provider(prompt, temperature=self.temperature, max_tokens=self.max_tokens)

    def run(self, prompt: str) -> str:
        self.memory.add("user", prompt)

        for _iteration in range(self.max_iterations):
            full_prompt = self._build_prompt(prompt)
            response = self._call_llm(full_prompt)

            if response.startswith("Answer:"):
                answer = response[len("Answer:") :].strip()
                self.memory.add("assistant", answer)
                return answer

            answer_match = re.search(r"Answer:\s*(.*)", response, re.DOTALL)
            if answer_match:
                answer = answer_match.group(1).strip()
                self.memory.add("assistant", answer)
                return answer

            parsed = self._parse_tool_call(response)
            if parsed is None:
                self.memory.add("assistant", response.strip())
                return response.strip()

            tool_name, tool_input = parsed
            tool = self.tools.get(tool_name)
            if tool is None:
                result = f"Error: Unknown tool '{tool_name}'. Available tools:\n{self.tools.descriptions()}"
            else:
                try:
                    result = tool.execute(**tool_input)
                except Exception as e:
                    result = f"Tool execution error: {e}"

            self.memory.add("assistant", f"Action: {tool_name}")
            self.memory.add("tool", result)

        return "Error: Max iterations reached without final answer."

    def stream(self, prompt: str) -> Iterator[str]:

        self.memory.add("user", prompt)

        for iteration in range(self.max_iterations):
            full_prompt = self._build_prompt(prompt)
            response = self._call_llm(full_prompt)

            if response.startswith("Answer:"):
                answer = response[len("Answer:") :].strip()
                self.memory.add("assistant", answer)
                yield answer
                return

            answer_match = re.search(r"Answer:\s*(.*)", response, re.DOTALL)
            if answer_match:
                answer = answer_match.group(1).strip()
                self.memory.add("assistant", answer)
                yield answer
                return

            parsed = self._parse_tool_call(response)
            if parsed is None:
                self.memory.add("assistant", response.strip())
                yield response.strip()
                return

            tool_name, tool_input = parsed
            tool = self.tools.get(tool_name)
            if tool is None:
                result = f"Error: Unknown tool '{tool_name}'."
            else:
                try:
                    result = tool.execute(**tool_input)
                except Exception as e:
                    result = f"Tool execution error: {e}"

            self.memory.add("assistant", f"Action: {tool_name}")
            self.memory.add("tool", result)

            yield f"Step {iteration + 1}: Used {tool_name} -> {result}\n"

        yield "Error: Max iterations reached."

    def reset(self) -> None:
        self.memory.clear()

    def add_tool(self, tool: Tool) -> None:
        if not isinstance(tool, Tool):
            raise AgentError("Must add a Tool instance")
        self.tools.register(tool)


def create_agent(provider=None, tools=None, memory=None, **kwargs) -> Agent:
    config: AgentConfig = {
        "provider": provider,
        "tools": tools or ToolRegistry(),
        "memory": memory or AgentMemory(),
        "system_prompt": kwargs.get("system_prompt", "You are a helpful AI assistant."),
        "max_iterations": kwargs.get("max_iterations", 10),
        "temperature": kwargs.get("temperature", 0.7),
        "max_tokens": kwargs.get("max_tokens", 1024),
    }
    return Agent(config)


class PlanningAgent(Agent):
    def _create_plan(self, task: str) -> list[str]:
        plan_prompt = (
            f"{self.system_prompt}\n\n"
            f"Break the following task into a numbered list of steps.\n"
            f"Each step should be a single, actionable unit of work.\n"
            f"Output only the steps, one per line, starting with 'Step N:'.\n\n"
            f"Task: {task}"
        )
        response = self._call_llm(plan_prompt)

        steps: list[str] = []
        for line in response.strip().split("\n"):
            line = line.strip()
            match = re.match(r"(?:Step\s*(\d+)[:.)\s]*)(.*)", line, re.IGNORECASE)
            if match:
                steps.append(match.group(2).strip())
            elif line and not line.startswith("#"):
                steps.append(line)

        if not steps:
            steps = [task]

        return steps

    def _execute_step(self, step: str, context: str) -> str:
        step_prompt = (
            f"{self.system_prompt}\n\n"
            f"Overall task context:\n{context}\n\n"
            f"Current step to execute:\n{step}\n\n"
            f"Execute this step using the available tools as needed."
        )
        return self.run(step_prompt)

    def run(self, prompt: str) -> str:
        steps = self._create_plan(prompt)
        context_parts: list[str] = [
            f"Task: {prompt}",
            "Plan:\n" + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps)),
        ]

        for i, step in enumerate(steps):
            result = self._execute_step(step, "\n".join(context_parts))
            context_parts.append(f"Step {i + 1}: {step}")
            context_parts.append(f"Result: {result}")

        summary_prompt = (
            f"{self.system_prompt}\n\n"
            f"Based on the following execution results, provide a final summary answer.\n\n"
            f"{chr(10).join(context_parts)}"
        )
        final_response = self._call_llm(summary_prompt)

        answer_match = re.search(r"Answer:\s*(.*)", final_response, re.DOTALL)
        if answer_match:
            return answer_match.group(1).strip()
        return final_response.strip()
