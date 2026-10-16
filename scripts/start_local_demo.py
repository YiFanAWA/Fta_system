"""Start the existing UI/API as a bounded offline local demonstration."""
from argparse import ArgumentParser
import asyncio
import importlib.metadata
import json
import os
from pathlib import Path
import sys

from local_demo_runtime import (ROOT, DemoError, bind_listener, environment, load_inputs,
                                prepare_workspace, serve, workspace_lease)


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--max-seconds", type=int, default=1800)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        expected = ROOT / ".venv/Scripts/python.exe"
        if os.name != "nt" or Path(sys.executable).resolve() != expected.resolve() or sys.version_info < (3, 11):
            raise DemoError("project_python_311_required_no_fallback")
        if not 1 <= args.max_seconds <= 7200 or not 0 <= args.port <= 65535:
            raise DemoError("invalid_demo_budget_or_port")
        for name in ("fastapi", "uvicorn", "pydantic", "httpx", "openai", "neo4j", "lxml"):
            try:
                importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError as error:
                raise DemoError("demo_dependency_missing") from error
        inputs = load_inputs()
        if args.check:
            print(json.dumps({"event": "local_demo_preflight_passed", "source_count": len(inputs.sources),
                "build_files": len(inputs.build), "provider_enabled": False, "workspace_created": False}))
            return 0
        listener = bind_listener(args.port)
        try:
            workspace = prepare_workspace(args.workspace, inputs)
            with workspace_lease(workspace):
                # This is the user-launched dedicated process, never the shell's environment.
                child_env = environment(dict(os.environ), workspace, inputs)
                os.environ.clear()
                os.environ.update(child_env)
                asyncio.run(serve(workspace, inputs, listener, args.max_seconds))
        finally:
            listener.close()
        return 0
    except DemoError as error:
        print(json.dumps({"event": "local_demo_blocked", "code": error.code,
                          "operation_path": error.operation_path, "operation": error.operation,
                          "caller": error.caller, "provider_requests": 0}), flush=True)
        return 1
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        print(json.dumps({"event": "local_demo_blocked", "code": "local_demo_startup_or_runtime_failed",
                          "failure_type": type(error).__name__, "provider_requests": 0}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
