"""Outgoing notifications (email OTP, Telegram). Real transports plug in here; the
in-memory outbox is used in dev/tests."""
from dataclasses import dataclass, field


@dataclass
class Notifier:
    outbox: list[dict] = field(default_factory=list)

    def send_email(self, to: str, subject: str, body: str) -> None:
        self.outbox.append({"channel": "email", "to": to, "subject": subject, "body": body})

    def send_telegram(self, chat_id: str, text: str) -> None:
        self.outbox.append({"channel": "telegram", "to": chat_id, "body": text})


notifier = Notifier()
