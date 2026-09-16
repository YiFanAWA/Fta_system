"""Provider-neutral port for text generation model clients."""

import time
from typing import Callable, Protocol


class ModelClientError(Exception):
    """A provider-neutral error raised by a model client."""

    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        if not isinstance(code, str) or not code.strip():
            raise ValueError("code must be a non-empty string")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message must be a non-empty string")
        if not isinstance(retryable, bool):
            raise TypeError("retryable must be a boolean")

        super().__init__(message.strip())
        self.code = code.strip()
        self.message = message.strip()
        self.retryable = retryable


class ModelClient(Protocol):
    """The minimal capability required by a remote extraction adapter."""

    def complete(self, prompt: str) -> str:
        """Return the model's raw text response for a prompt."""
        ...


class CallableModelClient:
    """A concrete ModelClient backed by an injected completion function."""

    def __init__(self, completion: Callable[[str], str]) -> None:
        self._completion = completion

    def complete(self, prompt: str) -> str:
        response = self._completion(prompt)
        if not isinstance(response, str):
            raise ModelClientError(
                "invalid_model_response",
                "completion function returned a non-text response",
            )
        return response


class RetryingModelClient:
    """Add bounded retry behavior to any ModelClient."""

    def __init__(
        self,
        client: ModelClient,
        *,
        max_retries: int = 2,
        delay_seconds: float = 2.0,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        if not isinstance(max_retries, int) or isinstance(max_retries, bool):
            raise ValueError("max_retries must be an integer")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if not isinstance(delay_seconds, (int, float)) or isinstance(delay_seconds, bool):
            raise ValueError("delay_seconds must be numeric")
        if delay_seconds < 0:
            raise ValueError("delay_seconds cannot be negative")

        self._client = client
        self._max_retries = max_retries
        self._delay_seconds = float(delay_seconds)
        self._sleep = sleep_fn

    def complete(self, prompt: str) -> str:
        attempts = self._max_retries + 1
        for attempt in range(attempts):
            try:
                return self._client.complete(prompt)
            except ModelClientError as exc:
                is_last_attempt = attempt == attempts - 1
                if not exc.retryable or is_last_attempt:
                    raise
                self._sleep(self._delay_seconds)

        # This branch is unreachable, but keeps the method total and explicit.
        raise ModelClientError(
            "retry_exhausted",
            "model request retries were exhausted",
        )
