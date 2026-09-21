"""OpenAI-compatible implementation of the provider-neutral ModelClient port."""

from typing import Any

import openai

from model_client import ModelClientError


class OpenAICompatibleModelClient:
    """Call an OpenAI-compatible chat completion endpoint."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
        base_url: str | None = None,
    ) -> None:
        if not isinstance(api_key, str):
            raise TypeError("api_key must be a string")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string")
        if isinstance(timeout_seconds, bool) or not isinstance(
            timeout_seconds, (int, float)
        ):
            raise TypeError("timeout_seconds must be a number")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        if base_url is not None and not isinstance(base_url, str):
            raise TypeError("base_url must be a string or None")

        self._api_key = api_key.strip()
        self._model = model.strip()
        self._timeout_seconds = float(timeout_seconds)
        self._base_url = base_url.strip() if base_url else None
        self._client: Any | None = None

        if self._api_key and hasattr(openai, "OpenAI"):
            client_kwargs: dict[str, Any] = {"api_key": self._api_key}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url
            self._client = openai.OpenAI(**client_kwargs)

    def complete(self, prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        if not self._api_key:
            raise ModelClientError(
                "provider_auth_failed",
                "model provider credentials are not configured",
            )

        try:
            response = self._request(prompt)
            content = self._read_content(response)
        except ModelClientError:
            raise
        except Exception as exc:
            raise self._translate_provider_error(exc) from exc

        if not isinstance(content, str):
            raise ModelClientError(
                "invalid_model_response",
                "model provider returned a non-text response",
            )
        return content.strip()

    def _request(self, prompt: str) -> Any:
        if self._client is not None:
            return self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                timeout=self._timeout_seconds,
            )

        # Compatibility path for legacy openai<1 installations.
        openai.api_key = self._api_key
        if self._base_url:
            openai.api_base = self._base_url
        return openai.ChatCompletion.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            request_timeout=self._timeout_seconds,
        )

    @staticmethod
    def _read_content(response: Any) -> Any:
        if hasattr(response, "choices"):
            choices = response.choices or []
            if not choices:
                return ""
            return getattr(getattr(choices[0], "message", None), "content", "") or ""

        choices = response.get("choices", []) if isinstance(response, dict) else []
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "") or ""

    @staticmethod
    def _translate_provider_error(exc: Exception) -> ModelClientError:
        if isinstance(exc, openai.AuthenticationError):
            return ModelClientError(
                "provider_auth_failed",
                "model provider rejected the credentials",
            )
        if isinstance(exc, openai.PermissionDeniedError):
            return ModelClientError(
                "provider_permission_denied",
                "model provider denied the request",
            )
        if isinstance(exc, openai.RateLimitError):
            return ModelClientError(
                "provider_rate_limited",
                "model provider rate limit was exceeded",
                retryable=True,
            )
        if isinstance(exc, openai.APITimeoutError):
            return ModelClientError(
                "provider_request_timeout",
                "model provider request timed out",
                retryable=True,
            )
        if isinstance(exc, openai.APIConnectionError):
            return ModelClientError(
                "provider_connection_error",
                "connection to model provider failed",
                retryable=True,
            )
        if isinstance(exc, openai.APIStatusError):
            status_code = getattr(exc, "status_code", None)
            retryable = status_code == 408 or (
                isinstance(status_code, int) and status_code >= 500
            )
            message = (
                f"model provider returned HTTP status {status_code}"
                if status_code is not None
                else "model provider returned an HTTP error"
            )
            return ModelClientError(
                "provider_http_error",
                message,
                retryable=retryable,
            )
        if isinstance(exc, openai.APIError):
            return ModelClientError(
                "provider_error",
                "model provider returned an API error",
            )
        return ModelClientError(
            "provider_unexpected_error",
            "unexpected model provider failure",
        )
