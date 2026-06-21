"""Local SRA process launcher.

This module only starts the executable configured in AstrBot WebUI. It does not
accept command-line text from chat messages or plugin pages.
"""

import subprocess
import time
from pathlib import Path
from typing import Optional

from .activity_logger import ActivityLogger


class SRAProcessManager:
    """Start and track a locally configured SRA executable."""

    def __init__(
        self,
        executable_path: str = "",
        working_directory: str = "",
        activity: Optional[ActivityLogger] = None,
    ):
        self._executable_path = str(executable_path or "").strip().strip('"')
        self._working_directory = str(working_directory or "").strip().strip('"')
        self._activity = activity
        self._process: subprocess.Popen | None = None

    @property
    def configured(self) -> bool:
        return bool(self._executable_path)

    @property
    def executable_path(self) -> str:
        return self._executable_path

    @property
    def working_directory(self) -> str:
        return self._working_directory

    def _log(self, result: str, elapsed: float, detail: str = ""):
        if self._activity:
            self._activity.log("sra_process", "启动 SRA Server", result, elapsed, detail)

    def status(self) -> dict:
        running = self._process is not None and self._process.poll() is None
        return {
            "configured": self.configured,
            "executable_path": self._executable_path,
            "working_directory": self._working_directory,
            "started_by_plugin": self._process is not None,
            "pid": self._process.pid if running and self._process is not None else None,
            "process_running": running,
        }

    def start(self) -> dict:
        """Start the configured SRA executable as a normal child process."""
        t0 = time.perf_counter()

        if self._process is not None and self._process.poll() is None:
            elapsed = (time.perf_counter() - t0) * 1000
            return {"success": True, "message": f"SRA 进程已由插件启动，PID={self._process.pid}", **self.status()}

        if not self._executable_path:
            elapsed = (time.perf_counter() - t0) * 1000
            msg = "尚未配置 SRA 可执行文件路径"
            self._log("fail", elapsed, msg)
            return {"success": False, "message": msg, **self.status()}

        executable = Path(self._executable_path)
        if not executable.exists() or not executable.is_file():
            elapsed = (time.perf_counter() - t0) * 1000
            msg = f"SRA 可执行文件不存在: {executable}"
            self._log("fail", elapsed, msg)
            return {"success": False, "message": msg, **self.status()}

        if executable.suffix.lower() != ".exe":
            elapsed = (time.perf_counter() - t0) * 1000
            msg = "出于安全限制，只允许启动已配置的 .exe 文件"
            self._log("fail", elapsed, msg)
            return {"success": False, "message": msg, **self.status()}

        if self._working_directory:
            cwd = Path(self._working_directory)
            if not cwd.exists() or not cwd.is_dir():
                elapsed = (time.perf_counter() - t0) * 1000
                msg = f"SRA 工作目录不存在: {cwd}"
                self._log("fail", elapsed, msg)
                return {"success": False, "message": msg, **self.status()}
        else:
            cwd = executable.parent

        try:
            self._process = subprocess.Popen(
                [str(executable)],
                cwd=str(cwd),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            self._log("fail", elapsed, str(e))
            return {"success": False, "message": f"启动失败: {e}", **self.status()}

        elapsed = (time.perf_counter() - t0) * 1000
        self._log("ok", elapsed, f"PID={self._process.pid}, cwd={cwd}")
        return {"success": True, "message": f"已启动 SRA 进程，PID={self._process.pid}", **self.status()}
