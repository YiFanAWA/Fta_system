from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "backend-python/api_server.py",
    "backend-python/app/api_server.py",
    "backend-python/contracts/__init__.py",
    "backend-python/core/__init__.py",
    "backend-python/domains/__init__.py",
    "backend-python/extraction/__init__.py",
    "backend-python/fta/__init__.py",
    "backend-python/rag/__init__.py",
    "backend-python/workflows/__init__.py",
    "backend-python/.env.example",
    "backend-python/requirements.txt",
    "frontend/package.json",
    "frontend/src/main.js",
    "evaluation/quality_eval/run_eval_benchmark.py",
    "docs/api-usage.md",
)
LEGACY_ROOT_FILES = (
    "api_server.py",
    "ai_module.py",
    "main.py",
    "pppppp",
    "API_USAGE.md",
    "DOCKER_DEPLOYMENT.md",
)

IMPLEMENTATION_FILES_MUST_BE_PACKAGED = (
    "agent_workflow.py",
    "ai_module.py",
    "aerospace_adapter.py",
    "common_fault_schema.py",
    "config.py",
    "domain_router.py",
    "extraction_contract.py",
    "fault_extractor.py",
    "generic_retrieval_pipeline.py",
    "rag_service.py",
    "response_policy.py",
    "siemens_s210_adapter.py",
)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [item for item in result.stdout.decode("utf-8").split("\0") if item]


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    for relative in LEGACY_ROOT_FILES:
        if (ROOT / relative).exists():
            errors.append(f"legacy root file remains: {relative}")

    for filename in IMPLEMENTATION_FILES_MUST_BE_PACKAGED:
        if (ROOT / "backend-python" / filename).exists():
            errors.append(f"backend implementation remains flat: backend-python/{filename}")

    for relative in tracked_files():
        parts = Path(relative).parts
        if relative == ".env" or "__pycache__" in parts or ".vscode" in parts:
            errors.append(f"forbidden tracked file: {relative}")
        if parts and parts[0] == "outputs":
            errors.append(f"forbidden tracked runtime output: {relative}")
        if len(parts) >= 2 and parts[0] == "frontend" and parts[1] == "dist":
            errors.append(f"forbidden tracked frontend build: {relative}")

    if errors:
        print("\n".join(errors))
        return 1

    print("repository layout verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
