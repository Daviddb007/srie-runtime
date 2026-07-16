"""Cognitive Provider — AI as a pluggable OS service.
The Runtime never talks to LLMs directly. It talks to the Provider interface.
Studio never knows which model is being used."""
from __future__ import annotations
from abc import ABC, abstractmethod


class CognitiveProvider(ABC):

    @abstractmethod
    def reason(self, prompt: str, context: dict | None = None) -> str: ...

    @abstractmethod
    def summarize(self, text: str, max_length: int = 200) -> str: ...

    @abstractmethod
    def plan(self, goal: str, context: dict | None = None) -> list[dict]: ...

    @abstractmethod
    def explain(self, topic: str, context: dict | None = None) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def available(self) -> bool: ...


class NoOpProvider(CognitiveProvider):
    """Default provider. Returns structured responses without AI."""

    def reason(self, prompt: str, context: dict | None = None) -> str:
        return "SRIE processed your request. Enable a Cognitive Provider (OpenAI, Claude, Gemini) for detailed reasoning."

    def summarize(self, text: str, max_length: int = 200) -> str:
        return text[:max_length] + "..." if len(text) > max_length else text

    def plan(self, goal: str, context: dict | None = None) -> list[dict]:
        return [{"step": "analyze", "description": f"Analyze: {goal}"}]

    def explain(self, topic: str, context: dict | None = None) -> str:
        return f"SRIE analyzed: {topic}"

    @property
    def name(self) -> str: return "noop"

    @property
    def available(self) -> bool: return True


class CognitiveService:
    """Runtime service that manages Cognitive Providers.
    Studio calls sdk.reason(), sdk.summarize(), etc.
    The CognitiveService decides which provider to use."""

    def __init__(self):
        self._providers: dict[str, CognitiveProvider] = {}
        self._active: str = "noop"
        self._register(NoOpProvider())

    def _register(self, provider: CognitiveProvider) -> None:
        self._providers[provider.name] = provider

    def use(self, provider_name: str) -> bool:
        if provider_name in self._providers:
            self._active = provider_name
            return True
        return False

    @property
    def active_provider(self) -> str:
        return self._active

    @property
    def available_providers(self) -> list[str]:
        return [n for n, p in self._providers.items() if p.available]

    def reason(self, prompt: str, context: dict | None = None) -> str:
        return self._providers[self._active].reason(prompt, context)

    def summarize(self, text: str, max_length: int = 200) -> str:
        return self._providers[self._active].summarize(text, max_length)

    def plan(self, goal: str, context: dict | None = None) -> list[dict]:
        return self._providers[self._active].plan(goal, context)

    def explain(self, topic: str, context: dict | None = None) -> str:
        return self._providers[self._active].explain(topic, context)
