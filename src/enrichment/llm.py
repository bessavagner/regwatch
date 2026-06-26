from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Summary:
    summary: str
    category: str
    confidence: float


class LLMClient(Protocol):
    def summarize(self, act_text: str, terms: list[str]) -> Summary: ...


class FakeLLMClient:
    def __init__(self, result: Summary):
        self._result = result

    def summarize(self, act_text: str, terms: list[str]) -> Summary:
        return self._result


class RaisingLLMClient:
    def summarize(self, act_text: str, terms: list[str]) -> Summary:
        raise RuntimeError("LLM unavailable")
