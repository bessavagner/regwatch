from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Summary:
    summary: str
    category: str
    # What the model could check in the act text, as opposed to its opinion of
    # itself. Defaulted so a provider that omits one produces a lower-ranked
    # match rather than an enrichment failure -- and so the ~40 existing
    # Summary(...) constructions in the tests stay valid.
    names_party: bool = False
    has_amount: bool = False
    has_deadline: bool = False

    @property
    def signal_score(self) -> int:
        """0-3. One orderable column instead of three sorts."""
        return sum((self.names_party, self.has_amount, self.has_deadline))


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
