import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from core.openai_model_client import OpenAICompatibleModelClient  # noqa: E402


class _FakeCompletions:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return {"choices": [{"message": {"content": "{}"}}]}


class _FakeClient:
    def __init__(self, completions):
        self.chat = type("Chat", (), {"completions": completions})()


class OpenAIModelClientTests(unittest.TestCase):
    def test_requests_deterministic_temperature(self):
        client = OpenAICompatibleModelClient(
            api_key="test-key",
            model="test-model",
            timeout_seconds=5,
        )
        completions = _FakeCompletions()
        client._client = _FakeClient(completions)

        self.assertEqual("{}", client.complete("extract"))
        self.assertEqual(0, completions.kwargs["temperature"])

    def test_sdk_retry_limit_is_explicit_and_can_be_disabled(self):
        with patch("core.openai_model_client.openai.OpenAI") as sdk_client:
            OpenAICompatibleModelClient(
                api_key="test-key",
                model="test-model",
                timeout_seconds=5,
                sdk_max_retries=0,
            )

        self.assertEqual(0, sdk_client.call_args.kwargs["max_retries"])

    def test_sdk_retry_limit_rejects_invalid_values(self):
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            OpenAICompatibleModelClient(
                api_key="test-key", model="test-model", timeout_seconds=5,
                sdk_max_retries=-1,
            )
        with self.assertRaisesRegex(TypeError, "must be an integer"):
            OpenAICompatibleModelClient(
                api_key="test-key", model="test-model", timeout_seconds=5,
                sdk_max_retries=True,
            )


if __name__ == "__main__":
    unittest.main()
