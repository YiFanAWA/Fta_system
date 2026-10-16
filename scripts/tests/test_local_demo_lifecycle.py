"""Real dedicated CLI children, no API import in the test process and no model calls."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
from time import monotonic
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from evaluation.quality_eval.run_m3_local_demo_acceptance_v1 import start, finish, execute, PYTHON, ENTRY, host


class LocalDemoLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = host.load_inputs()

    def test_parent_redirector_exit_stops_actual_host_not_unknown_process(self):
        with tempfile.TemporaryDirectory(prefix="fta-owned-demo-") as directory:
            workspace = Path(directory) / "demo"
            process, threads, logs, ready = start(workspace, 30)
            self.assertIsNotNone(ready)
            self.assertEqual(process.pid, ready["parent_pid"])
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel.WaitForSingleObject.restype = wintypes.DWORD
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = kernel.OpenProcess(0x100000, False, ready["pid"])
            self.assertTrue(handle)
            try:
                process.terminate()  # Exact Popen handle created in this test, never a port-selected PID.
                result = finish(process, threads, logs, timeout=8)
                self.assertEqual(0, kernel.WaitForSingleObject(handle, 5000))
                # Forced parent loss may also close inherited stdio; do not require a graceful-stop log.
                with socket.socket() as probe:
                    probe.settimeout(1)
                    self.assertNotEqual(0, probe.connect_ex(("127.0.0.1", int(ready["url"].rsplit(":", 1)[1]))))
                self.assertTrue((workspace / "storage/workflow.sqlite3").is_file())
                import sqlite3
                connection = sqlite3.connect(workspace / "storage/workflow.sqlite3")
                try:
                    self.assertEqual("ok", connection.execute("PRAGMA integrity_check").fetchone()[0])
                finally:
                    connection.close()
            finally:
                kernel.CloseHandle(handle)

    def test_sqlite_sidecar_link_refused_by_actual_cli_before_native_write(self):
        with tempfile.TemporaryDirectory(prefix="fta-owned-demo-") as directory:
            workspace = host.prepare_workspace(Path(directory) / "demo", self.inputs)
            sentinel = Path(directory) / "owned-sentinel"
            sentinel.write_bytes(b"not-user-data-unchanged")
            for suffix in ("-journal", "-wal", "-shm"):
                with self.subTest(suffix=suffix):
                    linked = workspace / ("storage/workflow.sqlite3" + suffix)
                    os.link(sentinel, linked)
                    result = execute([str(PYTHON), "-B", "-X", "utf8", str(ENTRY), "--workspace", str(workspace), "--port", "0"])
                    self.assertEqual(1, result["exit_code"])
                    self.assertIn("regular_single_link_file_required", result["stdout"])
                    self.assertNotIn("local_demo_ready", result["stdout"])
                    self.assertEqual(b"not-user-data-unchanged", sentinel.read_bytes())
                    self.assertFalse((workspace / "storage/workflow.sqlite3").exists())
                    linked.unlink()

    def test_unregistered_pyc_refused_by_actual_cli_before_import(self):
        with tempfile.TemporaryDirectory(prefix="fta-owned-demo-") as directory:
            workspace = host.prepare_workspace(Path(directory) / "demo", self.inputs)
            path = workspace / "backend-python/core/__pycache__"
            path.mkdir()
            (path / "config.cpython-311.pyc").write_bytes(b"never-execute")
            result = execute([str(PYTHON), "-B", "-X", "utf8", str(ENTRY), "--workspace", str(workspace), "--port", "0"])
            self.assertEqual(1, result["exit_code"])
            self.assertIn("unexpected_workspace_executable_or_file", result["stdout"])
            self.assertNotIn("local_demo_ready", result["stdout"])

    def test_actual_console_ctrl_c_stops_own_hidden_console_before_deadline(self):
        with tempfile.TemporaryDirectory(prefix="fta-owned-demo-") as directory:
            process, threads, logs, ready = start(Path(directory) / "demo", 60, hidden_console=True)
            self.assertIsNotNone(ready)
            self.assertEqual(process.pid, ready["parent_pid"])
            signal_script = (
                "import ctypes,sys; from ctypes import wintypes; k=ctypes.WinDLL('kernel32',use_last_error=True); "
                "k.FreeConsole(); "
                "k.AttachConsole.argtypes=[wintypes.DWORD]; k.AttachConsole.restype=wintypes.BOOL; "
                "assert k.AttachConsole(int(sys.argv[1])),ctypes.get_last_error(); "
                "assert k.SetConsoleCtrlHandler(None,True),ctypes.get_last_error(); "
                "assert k.GenerateConsoleCtrlEvent(0,0),ctypes.get_last_error(); k.FreeConsole(); print('own_console_ctrl_c_sent')"
            )
            started = monotonic()
            signal_result = execute([str(PYTHON), "-B", "-c", signal_script, str(ready["pid"])], timeout=5)
            result = finish(process, threads, logs, timeout=8)
            self.assertEqual(0, signal_result["exit_code"])
            self.assertLess(monotonic() - started, 10)
            self.assertEqual(0, result["exit_code"])
            self.assertIn('"event": "local_demo_stopped"', result["stdout"])


if __name__ == "__main__":
    unittest.main()
