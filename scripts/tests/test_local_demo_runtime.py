"""Local host policy tests; never import the user's live backend or credentials."""
import asyncio
from dataclasses import replace
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch
import httpx
from starlette.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import local_demo_runtime as host
import start_local_demo as cli


class LocalDemoRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = host.load_inputs()

    def test_frozen_inventory_and_no_extra_dependency(self):
        self.assertEqual((101, 33, 3), (len(self.inputs.sources), len(self.inputs.build), len(self.inputs.inputs)))
        self.assertNotIn("app.api_server", sys.modules)

    def test_environment_clears_keys_proxy_and_startup_hooks(self):
        source = {"deepseek_api_key": "do-not-keep", "AZURE_OPENAI_KEY": "also-secret", "HTTPS_PROXY": "proxy",
                  "PYTHONPATH": "unsafe", "SystemRoot": "C:/Windows", "PATH": "system"}
        with tempfile.TemporaryDirectory() as directory:
            env = host.environment(source, Path(directory), self.inputs)
        self.assertEqual("C:/Windows", env["SystemRoot"])
        self.assertEqual("", env["DEEPSEEK_API_KEY"])
        self.assertFalse(any(value in ("do-not-keep", "also-secret", "proxy", "unsafe") for value in env.values()))
        self.assertEqual("1", env["HF_HUB_OFFLINE"])
        self.assertEqual("0", env["OPENAI_MAX_RETRIES"])
        self.assertEqual("do-not-keep", source["deepseek_api_key"])

    def test_workspace_mirror_and_restart_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "demo"
            self.assertEqual(target, host.prepare_workspace(target, self.inputs))
            self.assertFalse((target / "backend-python/.env").exists())
            self.assertFalse((target / "storage/workflow.sqlite3").exists())
            self.assertEqual(target, host.prepare_workspace(target, self.inputs))
            source = target / self.inputs.sources[0]["path"]
            source.write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(host.DemoError, "workspace_source_drift"):
                host.prepare_workspace(target, self.inputs)
            self.assertEqual("changed", source.read_text())

    def test_unowned_existing_directory_not_adopted(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with self.assertRaises((host.DemoError, FileNotFoundError)):
                host.prepare_workspace(target, self.inputs)
            self.assertEqual([], list(target.iterdir()))

    def test_broad_workspace_forbidden(self):
        for target in (self.inputs.root, self.inputs.root.parent, Path(self.inputs.root.anchor)):
            with self.subTest(target=target), self.assertRaisesRegex(host.DemoError, "workspace_too_broad"):
                host.prepare_workspace(target, self.inputs)

    def test_lease_exclusion_and_release(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with host.workspace_lease(target):
                with self.assertRaisesRegex(host.DemoError, "workspace_already_running"):
                    with host.workspace_lease(target):
                        self.fail("second owner entered")
            with host.workspace_lease(target):
                pass

    def test_occupied_port_refused_without_terminating_owner(self):
        listener = host.bind_listener(0)
        try:
            with self.assertRaisesRegex(host.DemoError, "local_port_unavailable"):
                host.bind_listener(listener.getsockname()[1])
            self.assertGreater(listener.fileno(), -1)
        finally:
            listener.close()

    def test_guard_refuses_network_process_dotenv_and_other_database(self):
        with tempfile.TemporaryDirectory() as directory:
            guard = host.RuntimeGuard(Path(directory))
            for event, args in (("socket.connect", (None, ("127.0.0.1", 9))),
                                ("socket.getaddrinfo", ("api.deepseek.com", 443)),
                                ("subprocess.Popen", ("python",)),
                                ("open", (str(Path(directory) / ".env"), "r", 0)),
                                ("sqlite3.connect", (str(Path(directory) / "other.sqlite3"),))):
                with self.subTest(event=event), self.assertRaises(host.DemoError):
                    guard(event, args)
            guard("sqlite3.connect", (str(Path(directory) / "storage/workflow.sqlite3"),))

    def test_guard_allows_only_runtime_output_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            guard = host.RuntimeGuard(target)
            guard("open", (str(target / "storage/workflow.sqlite3"), "wb", 0))
            for path in (target / host.MARKER, target / "backend-python/core/config.py", target.parent / "other"):
                with self.assertRaisesRegex(host.DemoError, "write_outside_demo_storage"):
                    guard("open", (str(path), "wb", 0))

    def test_exact_os_discard_sink_is_not_persistent_outside_write(self):
        import os
        with tempfile.TemporaryDirectory() as directory:
            guard = host.RuntimeGuard(Path(directory))
            guard("open", (os.devnull, "w", os.O_WRONLY))
            self.assertFalse(guard.denied)

    def test_os_denial_preserves_permission_error_for_standard_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            guard = host.RuntimeGuard(Path(directory))
            with self.assertRaises(PermissionError):
                guard("subprocess.Popen", ("cmd",))
            self.assertIn("subprocess.Popen", guard.denied)

    def test_hardlinked_database_is_not_adopted(self):
        import os
        with tempfile.TemporaryDirectory() as directory:
            target = host.prepare_workspace(Path(directory) / "demo", self.inputs)
            original = Path(directory) / "outside.sqlite3"
            original.write_bytes(b"not a database")
            os.link(original, target / "storage/workflow.sqlite3")
            with self.assertRaisesRegex(host.DemoError, "single_link"):
                host.prepare_workspace(target, self.inputs)

    def test_unregistered_bytecode_or_source_is_not_adopted(self):
        with tempfile.TemporaryDirectory() as directory:
            target = host.prepare_workspace(Path(directory) / "demo", self.inputs)
            hidden = target / "backend-python/core/__pycache__"
            hidden.mkdir()
            (hidden / "config.cpython-311.pyc").write_bytes(b"untrusted")
            with self.assertRaisesRegex(host.DemoError, "unexpected_workspace"):
                host.prepare_workspace(target, self.inputs)

    def test_sqlite_sidecars_are_checked_before_native_open(self):
        import os
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "storage").mkdir()
            guard = host.RuntimeGuard(target)
            sentinel = target / "sentinel"
            sentinel.write_bytes(b"untouched")
            for suffix in ("-journal", "-wal", "-shm"):
                linked = Path(str(guard.database) + suffix)
                os.link(sentinel, linked)
                with self.assertRaisesRegex(host.DemoError, "single_link"):
                    guard("sqlite3.connect", (str(guard.database),))
                linked.unlink()
                self.assertEqual(b"untouched", sentinel.read_bytes())

    def test_check_does_not_start_or_create_workspace(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(cli, "serve", side_effect=AssertionError("forbidden")), \
                patch("builtins.print"):
            target = Path(directory) / "not-created"
            self.assertEqual(0, cli.main(["--workspace", str(target), "--check"]))
            self.assertFalse(target.exists())

    def test_missing_dependency_prevents_any_workspace_or_server(self):
        import importlib.metadata
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(cli.importlib.metadata, "version", side_effect=importlib.metadata.PackageNotFoundError), \
                patch.object(cli, "bind_listener", side_effect=AssertionError("forbidden")), patch("builtins.print"):
            self.assertEqual(1, cli.main(["--workspace", str(Path(directory) / "absent")]))


class OfflineHostPolicyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.calls = 0
        async def app(scope, receive, send):
            self.calls += 1
            packet = await receive() if scope["method"] == "POST" else None
            await JSONResponse({"observed_bytes": len(packet["body"]) if packet else 0})(scope, receive, send)
        self.policy = host.OfflineHostPolicy(app, Path(self.temporary.name), 8081, ("/js/app.js",))
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.policy), base_url="http://127.0.0.1:8081")

    async def asyncTearDown(self):
        await self.client.aclose()
        self.temporary.cleanup()

    async def test_offline_capabilities_not_fake_rag_success(self):
        for path in ("/api/rag/query", "/api/fta/extract", "/api/fta/full_generate", "/api/kg/query"):
            self.assertEqual(503, (await self.client.post(path, json={})).status_code)
        self.assertEqual(0, self.calls)

    async def test_foreign_origin_and_host_are_rejected(self):
        self.assertEqual(403, (await self.client.get("/", headers={"Origin": "https://foreign.example"})).status_code)
        self.assertEqual(403, (await self.client.get("/", headers={"Host": "foreign.example"})).status_code)
        self.assertEqual(0, self.calls)

    async def test_exact_static_inventory_only(self):
        for path in ("/", "/js/app.js", "/api/health"):
            self.assertEqual(200, (await self.client.get(path)).status_code)
        for path in ("/docs", "/secret.txt", "/api/download/anything"):
            self.assertEqual(503, (await self.client.get(path)).status_code)

    async def test_body_byte_limit_and_request_budget(self):
        path = "/api/fta/semantic-preview/validate"
        self.assertEqual(413, (await self.client.post(path, content=b"x" * (host.MAX_BODY + 1))).status_code)
        self.assertEqual(0, self.calls)
        self.assertEqual(200, (await self.client.post(path, content=b"x" * host.MAX_BODY)).status_code)
        self.policy.posts = 64
        self.assertEqual(429, (await self.client.post(path, content=b"{}")).status_code)

    async def test_concurrent_request_is_rejected_not_queued(self):
        async with self.policy.busy:
            self.assertEqual(429, (await self.client.post("/api/fta/semantic-preview/validate", json={})).status_code)
        self.assertEqual(0, self.calls)

    async def test_csp_prevents_saved_foreign_api_address_from_becoming_permission(self):
        response = await self.client.get("/")
        self.assertIn("connect-src 'self'", response.headers["content-security-policy"])
        self.assertIn("worker-src 'none'", response.headers["content-security-policy"])

    async def test_storage_failure_is_structured_before_application(self):
        with patch.object(host, "disk_usage", side_effect=host.DemoError("demo_storage_limit_exceeded")):
            response = await self.client.post("/api/fta/semantic-preview/validate", json={})
        self.assertEqual(503, response.status_code)
        self.assertEqual("demo_storage_limit_exceeded", response.json()["detail"]["code"])
        self.assertEqual(0, self.calls)


if __name__ == "__main__":
    unittest.main()
