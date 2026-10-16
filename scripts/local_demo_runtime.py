"""Local-only demo host. Consumes frozen inputs; owns no fault/RAG/FTA semantics."""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
import importlib
import json
import os
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
PROFILE = "evaluation/quality_eval/runs/first_delivery_local_config_v1_2026-10-13.json"
SOURCES = "evaluation/quality_eval/runs/first_delivery_m3_live_rag_v4_2026-10-16/source_stage.json"
BUILD_LOCK = "evaluation/quality_eval/runs/first_delivery_m3_live_runtime_lock_v4_2026-10-16.json"
IDENTITIES = {
    PROFILE: "bd8deaa2b89357485afefd1ed5c9666b98947092086b0dd3061a2a695af44ade",
    SOURCES: "01f9edbf3079b6a600857cd0dfc886bf7e2d1f33e40f3ff7e4750f73ac982ad1",
    BUILD_LOCK: "dcef9bcd9b80379322f9d35013d9a11853801a2ede9551dc4828c29268aef8f2",
}
BUILD_PREFIX = "tmp/first_delivery_m3_mobile_layout_build_v1/"
MAX_BODY = 256 * 1024
MAX_DISK = 32 * 1024 * 1024
MARKER = "local-demo.json"


class DemoError(Exception):
    def __init__(self, code: str, *, operation_path=None, operation=None, caller=None):
        self.code, self.operation_path = code, operation_path
        self.operation, self.caller = operation, caller
        super().__init__(code)


class DemoOperationDenied(DemoError, PermissionError):
    """OS operation denial must preserve the standard PermissionError contract."""


def plain_path(path: Path, *, file=False) -> Path:
    path = Path(os.path.abspath(path))
    for member in (path, *path.parents):
        if member.exists() or member.is_symlink():
            info = member.lstat()
            if member.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
                raise DemoError("linked_path_forbidden")
    if file and (not path.is_file() or path.stat().st_nlink != 1):
        raise DemoError("regular_single_link_file_required")
    return path


def digest(path: Path, *, maximum=32 * 1024 * 1024):
    path = plain_path(path, file=True)
    if path.stat().st_size > maximum:
        raise DemoError("asset_size_exceeded")
    value = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            value.update(chunk)
    return value.hexdigest()


def read_json(path, *, expected=None, maximum=4 * 1024 * 1024):
    path = plain_path(path, file=True)
    if path.stat().st_size > maximum or expected is not None and digest(path, maximum=maximum) != expected:
        raise DemoError("input_identity_or_size_mismatch")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as error:
        raise DemoError("invalid_runtime_json") from error
    if type(value) is not dict:
        raise DemoError("runtime_object_required")
    return value


def repo_path(root, name):
    if type(name) is not str or "\\" in name or ":" in name or ".." in name.split("/"):
        raise DemoError("invalid_asset_path")
    path = plain_path(root / name, file=True)
    if not path.is_relative_to(root):
        raise DemoError("asset_outside_source_root")
    return path


@dataclass(frozen=True)
class DemoInputs:
    root: Path
    sources: tuple
    build: tuple
    overrides: dict
    inputs: tuple

    @property
    def identity(self):
        raw = json.dumps({"identities": IDENTITIES, "root": self.root.as_posix()}, sort_keys=True).encode()
        return sha256(raw).hexdigest()


def load_inputs(root=ROOT):
    root = plain_path(root).resolve(strict=True)
    values = {name: read_json(repo_path(root, name), expected=expected) for name, expected in IDENTITIES.items()}
    sources = values[SOURCES]["source_copies"]
    build = [row for row in values[BUILD_LOCK]["runtime"] if row["path"].startswith(BUILD_PREFIX)]
    inputs = values[PROFILE]["minimum_local_input_references"]
    if len(sources) != 101 or len(build) != 33 or len(inputs) != 3:
        raise DemoError("frozen_input_inventory_changed")
    for rows in (sources, build, inputs):
        if len({row["path"] for row in rows}) != len(rows):
            raise DemoError("duplicate_input_path")
        size = 0
        for row in rows:
            path = repo_path(root, row["path"])
            size += path.stat().st_size
            if digest(path) != row["sha256"]:
                raise DemoError("frozen_asset_drift")
        if size > 128 * 1024 * 1024:
            raise DemoError("inventory_byte_limit")
    if any(not row["path"].startswith("backend-python/") or not row["path"].endswith(".py") for row in sources):
        raise DemoError("source_inventory_not_python_only")
    return DemoInputs(root, tuple(sources), tuple(build), dict(values[PROFILE]["core_environment_overrides"]), tuple(inputs))


def prepare_workspace(workspace, inputs):
    workspace = plain_path(workspace)
    if workspace == inputs.root or inputs.root.is_relative_to(workspace) or workspace == Path(workspace.anchor):
        raise DemoError("workspace_too_broad")
    if workspace.is_relative_to(inputs.root) and (workspace == inputs.root / "tmp" or not workspace.is_relative_to(inputs.root / "tmp")):
        raise DemoError("in_repository_workspace_must_be_named_tmp_child")
    if not workspace.parent.is_dir():
        raise DemoError("workspace_parent_missing")
    expected = {"kind": "local_research_demo_v1", "workspace": workspace.as_posix(),
                "input_identity": inputs.identity, "source_count": len(inputs.sources), "provider_enabled": False}
    if workspace.exists():
        if read_json(workspace / MARKER, maximum=4096) != expected:
            raise DemoError("existing_workspace_not_owned_or_version_mismatch")
        stage = workspace / "backend-python"
        actual = set()
        for number, path in enumerate(stage.rglob("*")):
            if number >= 512:
                raise DemoError("workspace_source_inventory_limit")
            plain_path(path)
            if path.is_relative_to(stage / "outputs"):
                continue
            if path.is_file():
                actual.add(path.relative_to(workspace).as_posix())
        if actual != {row["path"] for row in inputs.sources}:
            raise DemoError("unexpected_workspace_executable_or_file")
        for row in inputs.sources:
            if digest(workspace / row["path"]) != row["sha256"]:
                raise DemoError("workspace_source_drift")
        database = plain_path(workspace / "storage/workflow.sqlite3")
        if database.exists():
            plain_path(database, file=True)
        return workspace
    workspace.mkdir()
    # Leave partial files on failure, with no ready marker. Never overwrite/retry silently.
    for row in inputs.sources:
        original = repo_path(inputs.root, row["path"])
        target = workspace / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = original.read_bytes()
        if sha256(raw).hexdigest() != row["sha256"]:
            raise DemoError("source_changed_during_prepare")
        with target.open("xb") as stream:
            stream.write(raw)
    (workspace / "storage").mkdir()
    with (workspace / MARKER).open("x", encoding="utf-8") as stream:
        json.dump(expected, stream, ensure_ascii=False, sort_keys=True)
    return workspace


def environment(base, workspace, inputs):
    # Do not inherit provider credentials, proxies, PYTHONPATH, startup hooks, etc.
    safe = {key: value for key, value in base.items() if key.upper() in
            {"SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "TEMP", "TMP", "USERPROFILE", "APPDATA", "LOCALAPPDATA"}}
    values = dict(inputs.overrides)
    values["EXTRACTION_DB_PATH"] = str(workspace / "storage/workflow.sqlite3")
    values["S210_MODEL_CACHE_DIR"] = str(workspace / "disabled-model-cache")
    roles = {row["role"]: inputs.root / row["path"] for row in inputs.inputs}
    values["S210_GOLD_PATH"] = str(roles["gold"])
    values["S210_RELATION_REGISTRY_PATH"] = str(roles["relations"])
    safe.update(values)
    safe.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "HF_HUB_OFFLINE": "1",
                 "TRANSFORMERS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1"})
    return safe


@contextmanager
def workspace_lease(workspace):
    import msvcrt
    path = plain_path(workspace / "host.lease")
    if path.exists() and (not path.is_file() or path.stat().st_nlink != 1 or path.stat().st_size > 1):
        raise DemoError("invalid_workspace_lease")
    with path.open("a+b") as stream:
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise DemoError("workspace_already_running") from error
        try:
            if path.stat().st_size == 0:
                stream.write(b"0")
                stream.flush()
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def bind_listener(port):
    if type(port) is not int or not 0 <= port <= 65535:
        raise DemoError("invalid_local_port")
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        listener.bind(("127.0.0.1", port))
        listener.listen(16)
        return listener
    except OSError as error:
        listener.close()
        raise DemoError("local_port_unavailable_no_process_terminated") from error


class RuntimeGuard:
    def __init__(self, workspace):
        self.workspace = workspace
        self.database = workspace / "storage/workflow.sqlite3"
        self.writes = (workspace / "storage", workspace / "backend-python/outputs")
        self.denied = set()

    def deny(self, code):
        self.denied.add(code)
        raise DemoError(code)

    def writable(self, value):
        path = plain_path(Path(os.fsdecode(value)))
        if path.exists() and path.is_file() and path.stat().st_nlink != 1:
            self.deny("hardlinked_runtime_file_forbidden")
        if not any(path == root or path.is_relative_to(root) for root in self.writes):
            self.denied.add("write_outside_demo_storage")
            raise DemoError("write_outside_demo_storage", operation_path=str(path))

    def __call__(self, event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system", "os.startfile"}:
            import traceback
            self.denied.add(event)
            frames = traceback.extract_stack(limit=6)
            raise DemoOperationDenied("offline_host_external_operation_forbidden", operation=event,
                caller=[{"file": frame.filename, "line": frame.lineno, "function": frame.name}
                        for frame in frames[:-1]])
        if event == "sqlite3.connect":
            if plain_path(Path(os.fsdecode(args[0]))) != self.database:
                self.deny("non_demo_database_forbidden")
            validate_sqlite_files(self.database)
        if event == "open" and isinstance(args[0], (str, bytes)):
            if os.fsdecode(args[0]).casefold() == os.devnull.casefold():
                return  # Exact OS discard sink, not an arbitrary external file/device.
            if Path(os.fsdecode(args[0])).name.casefold() == ".env":
                self.deny("dotenv_read_forbidden")
            mode, flags = args[1], args[2]
            if isinstance(mode, str) and any(char in mode for char in "wax+") or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
                self.writable(args[0])
        if event in {"os.mkdir", "os.remove", "os.rmdir"}:
            self.writable(args[0])
        if event in {"os.rename", "os.replace"}:
            self.writable(args[0]); self.writable(args[1])
        if event in {"os.symlink", "os.link"}:
            self.deny("runtime_link_creation_forbidden")


def validate_sqlite_files(database):
    for suffix in ("", "-journal", "-wal", "-shm"):
        path = plain_path(Path(str(database) + suffix))
        if path.exists():
            plain_path(path, file=True)


def disk_usage(workspace):
    total = 0
    for base in (workspace / "storage", workspace / "backend-python/outputs"):
        if base.exists():
            for number, path in enumerate(base.rglob("*")):
                if number >= 256:
                    raise DemoError("demo_file_count_exceeded")
                plain_path(path)
                if path.is_file():
                    total += path.stat().st_size
                    if total > MAX_DISK:
                        raise DemoError("demo_storage_limit_exceeded")
    return total


class OfflineHostPolicy:
    """Transport capabilities only. Fault validation remains in the original API."""
    def __init__(self, app, workspace, port, static_paths=()):
        self.app, self.workspace, self.port = app, workspace, port
        self.static_paths = frozenset(static_paths) | {"/"}
        self.busy = asyncio.Lock()
        self.posts = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            return await self.app(scope, receive, send)
        if scope["type"] != "http":
            return await send({"type": "websocket.close", "code": 1008})
        from starlette.responses import JSONResponse
        original_send = send
        async def protected_send(message):
            if message["type"] == "http.response.start":
                message = dict(message)
                message["headers"] = [(key, value) for key, value in message.get("headers", [])
                                      if key.lower() != b"content-security-policy"] + [
                    (b"content-security-policy", b"default-src 'self'; connect-src 'self'; img-src 'self' data:; "
                     b"style-src 'self' 'unsafe-inline'; script-src 'self' 'wasm-unsafe-eval'; "
                     b"font-src 'self' data:; worker-src 'none'; object-src 'none'; base-uri 'none'; "
                     b"frame-ancestors 'none'; form-action 'self'")]
            await original_send(message)
        send = protected_send

        async def reject(code, status):
            message = "本地演示未启用此能力；未调用云端模型。" if code == "local_demo_capability_disabled" else code
            response = JSONResponse({"detail": {"code": code, "message": message}}, status_code=status)
            await response(scope, receive, send)

        headers = {key.lower(): value for key, value in scope["headers"]}
        authority = f"127.0.0.1:{self.port}".encode()
        if headers.get(b"host") != authority or headers.get(b"origin", b"http://" + authority) != b"http://" + authority:
            return await reject("local_demo_origin_forbidden", 403)
        path, method = scope["path"], scope["method"]
        allowed = method == "POST" and path == "/api/fta/semantic-preview/validate" \
            or method == "GET" and path in self.static_paths | {"/api/health", "/openapi.json"}
        if not allowed:
            return await reject("local_demo_capability_disabled", 503)
        if method == "GET":
            return await self.app(scope, receive, send)
        if self.busy.locked() or self.posts >= 64:
            return await reject("local_demo_request_budget_exceeded", 429)
        async with self.busy:
            self.posts += 1
            response_started = False
            try:
                disk_usage(self.workspace)
                async with asyncio.timeout(30):
                    body = bytearray()
                    while True:
                        packet = await receive()
                        if packet["type"] == "http.disconnect":
                            return
                        chunk = packet.get("body", b"")
                        if len(body) + len(chunk) > MAX_BODY:
                            return await reject("local_demo_body_limit_exceeded", 413)
                        body.extend(chunk)
                        if not packet.get("more_body", False):
                            break
                    sent, response_size, response_started = False, 0, False
                    async def replay():
                        nonlocal sent
                        if sent:
                            return {"type": "http.disconnect"}
                        sent = True
                        return {"type": "http.request", "body": bytes(body)}
                    async def bounded_send(message):
                        nonlocal response_size, response_started
                        if message["type"] == "http.response.start":
                            response_started = True
                        response_size += len(message.get("body", b""))
                        if response_size > 1024 * 1024:
                            raise DemoError("local_demo_response_limit_exceeded")
                        await send(message)
                    await self.app(scope, replay, bounded_send)
                    disk_usage(self.workspace)
            except TimeoutError:
                if response_started:
                    raise DemoError("local_demo_timeout_after_response_started")
                return await reject("local_demo_request_timeout", 504)
            except DemoError as error:
                if response_started:
                    raise  # Never emit a second status after response headers.
                return await reject(error.code, 503)


async def serve(workspace, inputs, listener, duration):
    from local_demo_windows import bind_host, ParentHandle
    job = bind_host()
    parent = ParentHandle()
    stage = workspace / "backend-python"
    # Environment was explicitly bound by the CLI before this first backend import.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(stage))
    os.chdir(stage)
    guard = RuntimeGuard(workspace)
    validate_sqlite_files(guard.database)
    sys.addaudithook(guard)
    api = importlib.import_module("app.api_server")
    if not Path(api.__file__).resolve().is_relative_to(stage):
        raise DemoError("api_import_outside_demo_source")
    for name, module in tuple(sys.modules.items()):
        if name.split(".")[0] in {"app", "core", "contracts", "extraction", "fta", "rag", "domains", "retrieval", "workflows"}:
            filename = getattr(module, "__file__", None)
            if filename is not None and not Path(filename).resolve().is_relative_to(stage):
                raise DemoError("backend_import_outside_demo_source")
    import uvicorn
    from fastapi.staticfiles import StaticFiles
    api.app.mount("/", StaticFiles(directory=str(inputs.root / BUILD_PREFIX), html=True), name="local-demo-static")
    port = listener.getsockname()[1]
    app = OfflineHostPolicy(api.app, workspace, port,
        ("/" + row["path"].removeprefix(BUILD_PREFIX) for row in inputs.build))
    class Server(uvicorn.Server):
        async def startup(self, sockets=None):
            await super().startup(sockets=sockets)
            print(json.dumps({"event": "local_demo_ready", "url": f"http://127.0.0.1:{port}",
                "pid": os.getpid(), "parent_pid": parent.pid, "windows_job": job,
                "workspace": str(workspace), "provider_enabled": False,
                "liveness_only": True, "max_seconds": duration}, ensure_ascii=False), flush=True)
    server = Server(uvicorn.Config(app, log_level="error", access_log=False, timeout_keep_alive=5,
        timeout_graceful_shutdown=10, limit_concurrency=8, backlog=16))
    task = asyncio.create_task(server.serve(sockets=[listener]))
    async def watch_parent():
        while not task.done():
            try:
                exited = parent.exited()
            except OSError:
                server.should_exit = True
                return
            if exited:
                server.should_exit = True
                return
            await asyncio.sleep(0.25)  # Bounded lifecycle watchdog, not a request retry or readiness delay.
    watcher = asyncio.create_task(watch_parent())
    try:
        await asyncio.wait_for(asyncio.shield(task), timeout=duration)
    except (TimeoutError, asyncio.CancelledError):
        server.should_exit = True
        await asyncio.wait_for(task, timeout=12)
    finally:
        watcher.cancel()
        try:
            await watcher
        except asyncio.CancelledError:
            pass
        parent.close()
        for name in ("fta.kg_builder", "fta.kg_reasoner"):
            driver = getattr(sys.modules.get(name), "driver", None)
            if driver is not None:
                driver.close()
        print(json.dumps({"event": "local_demo_stopped", "pid": os.getpid(),
            "database_retained": (workspace / "storage/workflow.sqlite3").is_file(),
            "denied_operations": sorted(guard.denied), "provider_requests": 0,
            "heavy_models_loaded": any(name in sys.modules for name in ("torch", "transformers", "sentence_transformers"))},
            ensure_ascii=False), flush=True)
