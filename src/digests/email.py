from dataclasses import dataclass, field
from typing import Protocol


class EmailSender(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


@dataclass
class FakeEmailSender:
    sent: list[tuple[str, str, str]] = field(default_factory=list)

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))


@dataclass
class RaisingEmailSender:
    """Always fails, so tests can exercise the unsent path without a socket."""

    message: str = "smtp said no"

    def send(self, to: str, subject: str, body: str) -> None:
        raise RuntimeError(self.message)
