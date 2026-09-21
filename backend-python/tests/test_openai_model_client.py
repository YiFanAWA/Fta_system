import sys
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
