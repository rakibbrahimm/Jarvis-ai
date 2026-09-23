"""
RAKIB 2.0 — Multi-Engine AI Router
Providers are adapters; no proprietary provider code is copied.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AIResponse:
    text: str
    provider: str
    success: bool = True


class RAKIBRouter:

    def __init__(self):
        self.providers = {}

    def register(self, name: str, handler):
        if callable(handler):
            self.providers[name] = handler

    def available(self):
        return list(self.providers.keys())

    def ask(self, command: str, preferred: Optional[str] = None):
        command = (command or "").strip()

        if not command:
            return AIResponse(
                text="I did not receive a command.",
                provider="rakib-core"
            )

        order = []

        if preferred and preferred in self.providers:
            order.append(preferred)

        for name in self.providers:
            if name not in order:
                order.append(name)

        for name in order:
            try:
                result = self.providers[name](command)

                if result:
                    return AIResponse(
                        text=str(result).strip(),
                        provider=name
                    )

            except Exception as exc:
                print(f"RAKIB ROUTER: {name} failed: {exc}")

        return AIResponse(
            text="RAKIB could not get a response from the available AI engines.",
            provider="rakib-router",
            success=False
        )
