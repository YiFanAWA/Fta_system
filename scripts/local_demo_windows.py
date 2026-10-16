"""Windows-only process ownership boundary for the dedicated local demo host."""
import ctypes
from ctypes import wintypes
import os


class BasicLimits(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]


class IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in ("ReadOperationCount", "WriteOperationCount",
        "OtherOperationCount", "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", BasicLimits), ("IoInfo", IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


def bind_host():
    """Bind only this dedicated Python host, never its shell or Codex parent."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetConsoleCP.restype = wintypes.UINT
    kernel.SetConsoleCtrlHandler.argtypes = [ctypes.c_void_p, wintypes.BOOL]
    kernel.SetConsoleCtrlHandler.restype = wintypes.BOOL
    console_attached = kernel.GetConsoleCP() != 0
    if console_attached and not kernel.SetConsoleCtrlHandler(None, False):
        raise ctypes.WinError(ctypes.get_last_error())
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
    kernel.QueryInformationJobObject.restype = wintypes.BOOL
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateJobObjectW(None, None)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    assigned = False
    try:
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000 | 0x8 | 0x200
        limits.BasicLimitInformation.ActiveProcessLimit = 1
        limits.JobMemoryLimit = 1024 ** 3
        if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.AssignProcessToJobObject(handle, kernel.GetCurrentProcess()):
            raise ctypes.WinError(ctypes.get_last_error())
        assigned = True
        observed = ExtendedLimits()
        if not kernel.QueryInformationJobObject(handle, 9, ctypes.byref(observed), ctypes.sizeof(observed), None):
            raise ctypes.WinError(ctypes.get_last_error())
        if observed.BasicLimitInformation.LimitFlags != limits.BasicLimitInformation.LimitFlags \
                or observed.JobMemoryLimit != limits.JobMemoryLimit:
            raise RuntimeError("demo Windows job differs from actual requested limits")
        # Intentionally process-lifetime. Closing this assigned kill-on-close job here would kill this host.
        return {"bound_host_pid": os.getpid(), "active_process_limit": observed.BasicLimitInformation.ActiveProcessLimit,
                "commit_limit_bytes": observed.JobMemoryLimit, "kill_on_handle_close": True,
                "console_ctrl_c_enabled": console_attached}
    finally:
        if not assigned:
            kernel.CloseHandle(handle)


class ParentHandle:
    def __init__(self):
        self.pid = os.getppid()
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = self.kernel.OpenProcess(0x100000, False, self.pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())

    def exited(self):
        value = self.kernel.WaitForSingleObject(self.handle, 0)
        if value not in (0, 258):
            raise ctypes.WinError(ctypes.get_last_error())
        return value == 0

    def close(self):
        self.kernel.CloseHandle(self.handle)
