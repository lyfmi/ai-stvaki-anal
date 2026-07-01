"""Groq API error types."""
from __future__ import annotations


class GroqApiError(RuntimeError):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Groq API error {status_code}: {detail}")

    @property
    def is_rate_limit(self) -> bool:
        text = self.detail.lower()
        return self.status_code == 429 or "rate_limit" in text or "rate limit" in text
