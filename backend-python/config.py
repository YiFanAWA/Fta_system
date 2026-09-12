import os
from pathlib import Path


def _load_local_env() -> None:
	env_path = Path(__file__).with_name(".env")
	if not env_path.exists():
		return

	for line in env_path.read_text(encoding="utf-8").splitlines():
		text = line.strip()
		if not text or text.startswith("#") or "=" not in text:
			continue

		key, value = text.split("=", 1)
		key = key.strip()
		value = value.strip().strip('"').strip("'")
		if key and key not in os.environ:
			os.environ[key] = value


_load_local_env()


QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_BASE_URL = os.getenv(
	"QWEN_BASE_URL",
	"https://dashscope.aliyuncs.com/compatible-mode/v1",
)
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")


def _first_non_empty(*values: str) -> str:
	for v in values:
		if isinstance(v, str) and v.strip():
			return v.strip()
	return ""


OPENAI_API_KEY = _first_non_empty(os.getenv("OPENAI_API_KEY", ""), QWEN_API_KEY)
OPENAI_API_BASE = _first_non_empty(
	os.getenv("OPENAI_API_BASE", ""),
	os.getenv("OPENAI_BASE_URL", ""),
	QWEN_BASE_URL,
)
OPENAI_MODEL = _first_non_empty(os.getenv("OPENAI_MODEL", ""), QWEN_MODEL, "qwen-plus")
OPENAI_TIMEOUT_SECONDS = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "120"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

OPENFTA_PATH = os.getenv("OPENFTA_PATH", r"C:\Program Files\OpenFTA\openfta.exe")