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


DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv(
	"DEEPSEEK_BASE_URL",
	"https://api.deepseek.com",
)
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")

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


OPENAI_API_KEY = _first_non_empty(
	os.getenv("OPENAI_API_KEY", ""),
	DEEPSEEK_API_KEY,
	QWEN_API_KEY,
)
OPENAI_API_BASE = _first_non_empty(
	os.getenv("OPENAI_API_BASE", ""),
	os.getenv("OPENAI_BASE_URL", ""),
	DEEPSEEK_BASE_URL if DEEPSEEK_API_KEY else QWEN_BASE_URL,
)
OPENAI_MODEL = _first_non_empty(
	os.getenv("OPENAI_MODEL", ""),
	DEEPSEEK_MODEL if DEEPSEEK_API_KEY else QWEN_MODEL,
	"qwen-plus",
)
OPENAI_TIMEOUT_SECONDS = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "120"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

OPENFTA_PATH = os.getenv("OPENFTA_PATH", r"C:\Program Files\OpenFTA\openfta.exe")

EXTRACTION_DB_PATH = os.getenv(
	"EXTRACTION_DB_PATH",
	str(Path(__file__).with_name("outputs") / "extraction_workflow.sqlite3"),
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
S210_GOLD_PATH = os.getenv(
	"S210_GOLD_PATH",
	str(
		PROJECT_ROOT
		/ "evaluation"
		/ "quality_eval"
		/ "datasets"
		/ "siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json"
	),
)
S210_EMBEDDING_MODEL = os.getenv("S210_EMBEDDING_MODEL", "BAAI/bge-m3")
S210_RERANKER_MODEL = os.getenv(
	"S210_RERANKER_MODEL",
	"BAAI/bge-reranker-v2-m3",
)
S210_MODEL_CACHE_DIR = os.getenv(
	"S210_MODEL_CACHE_DIR",
	str(PROJECT_ROOT / "tmp" / "retrieval_models" / "huggingface"),
)
S210_RAG_DEVICE = os.getenv("S210_RAG_DEVICE", "cpu")

ALLOW_AUTOMATIC_NOT_REQUIRED_RELEASE = os.getenv(
	"ALLOW_AUTOMATIC_NOT_REQUIRED_RELEASE",
	"false",
).strip().lower() in {"1", "true", "yes", "on"}
