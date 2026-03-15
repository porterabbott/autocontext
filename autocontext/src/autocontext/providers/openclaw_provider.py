"""OpenClaw CLI provider — routes LLM calls through `openclaw agent`.

Uses Spencer's existing OpenAI Max plan via OpenClaw's OAuth routing.
No separate API keys required.
"""

from __future__ import annotations

import json
import subprocess
import uuid

from autocontext.providers.base import CompletionResult, LLMProvider, ProviderError


class OpenClawProvider(LLMProvider):
    """LLM provider that shells out to ``openclaw agent`` CLI.

    This routes all LLM calls through OpenClaw's gateway, which handles
    OAuth and model routing via the user's existing subscription (e.g.,
    OpenAI ChatGPT Max).  No separate API keys are needed.

    The provider creates an isolated session per call to avoid state
    leaking between agent roles (competitor, analyst, coach, etc.).
    """

    def __init__(
        self,
        model: str | None = None,
        openclaw_bin: str | None = None,
        thinking: str = "off",
        timeout_seconds: int = 120,
    ) -> None:
        self._model = model or "openai-codex/gpt-5.3-codex"
        self._openclaw_bin = openclaw_bin or "openclaw"
        self._thinking = thinking
        self._timeout = timeout_seconds

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> CompletionResult:
        resolved_model = model or self._model
        session_id = f"autoctx-{uuid.uuid4().hex[:12]}"

        # Build the combined prompt — openclaw agent takes a single message
        combined = f"<system>\n{system_prompt}\n</system>\n\n{user_prompt}"

        cmd = [
            self._openclaw_bin,
            "agent",
            "--session-id", session_id,
            "--message", combined,
            "--thinking", self._thinking,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise ProviderError(
                f"openclaw agent timed out after {self._timeout}s"
            ) from exc
        except FileNotFoundError as exc:
            raise ProviderError(
                f"openclaw CLI not found at {self._openclaw_bin!r}. "
                "Ensure OpenClaw is installed and in PATH."
            ) from exc

        if result.returncode != 0:
            stderr = result.stderr.strip()[:500] if result.stderr else "(no stderr)"
            raise ProviderError(
                f"openclaw agent failed (exit {result.returncode}): {stderr}"
            )

        text = result.stdout.strip()
        if not text:
            raise ProviderError("openclaw agent returned empty response")

        return CompletionResult(
            text=text,
            model=resolved_model,
        )

    def default_model(self) -> str:
        return self._model

    @property
    def name(self) -> str:
        return "OpenClawProvider"
