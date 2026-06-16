"""SRA HTTP 客户端 - 封装对 SRAFrontend.Server 的 REST API 调用。

对应接口：
  POST /Task/run     - 运行任务
  POST /Task/stop    - 停止任务
  GET  /Task/status  - 获取任务状态
  GET  /Task/logs    - 获取最近日志
  GET  /Configs      - 获取所有配置名称列表
"""

import time
from typing import Optional

import httpx

from .activity_logger import ActivityLogger


class SRAClient:
    """异步 HTTP 客户端，封装 SRA Server 的 TaskController 接口。"""

    def __init__(self, host: str = "localhost", port: int = 5000, activity: Optional[ActivityLogger] = None):
        self._base = f"http://{host}:{port}"
        self._activity = activity

    def _url(self, path: str) -> str:
        return f"{self._base}{path}"

    def _log_activity(self, category: str, desc: str, result: str, elapsed: float, detail: Optional[str] = None):
        """统一记录原子行为，仅在此层记录一次，避免与 main.py 重复。"""
        if self._activity:
            self._activity.log(category, desc, result, elapsed, detail)

    @staticmethod
    def _parse_json(resp: httpx.Response) -> tuple[Optional[object], Optional[str]]:
        """解析响应 JSON，处理非 JSON 响应和错误状态码。

        Returns:
            (parsed_data, error_msg)。成功时 error_msg 为 None。
        """
        # 检查 HTTP 状态码
        if resp.status_code >= 400:
            return None, f"HTTP {resp.status_code}: {resp.text[:200]}"
        # 检查空响应
        text = resp.text.strip()
        if not text:
            return None, "SRA服务器返回空响应"
        # 尝试解析 JSON
        try:
            return resp.json(), None
        except Exception as e:
            return None, f"响应解析失败({e}): {text[:200]}"

    async def run_task(self, config_name: Optional[str] = "default") -> dict:
        """运行 SRA 任务。

        按 SRA Server 规范：
          - 指定 config_name: 加载该已保存配置运行
          - 未指定(None): 默认加载 "default" 配置运行
          - 空字符串(""): 运行全部已保存配置

        Args:
            config_name: 配置名，默认 "default"。

        Returns:
            {"success": bool, "message": str}
        """
        t0 = time.perf_counter()
        body: dict = {}
        if config_name:
            body["ConfigName"] = config_name

        url = self._url("/Task/run")
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=body)
                data, err = self._parse_json(resp)
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            self._log_activity("sra_api", f"POST /Task/run config={config_name or 'all'}", "fail", elapsed, str(e))
            return {"success": False, "message": f"请求失败: {e}"}

        elapsed = (time.perf_counter() - t0) * 1000
        if err:
            self._log_activity("sra_api", f"POST /Task/run config={config_name or 'all'}", "fail", elapsed, err)
            return {"success": False, "message": err}
        data = data or {}
        ok = bool(data.get("success")) if isinstance(data, dict) else False
        self._log_activity(
            "sra_api",
            f"POST /Task/run config={config_name or 'all'}",
            "ok" if ok else "fail",
            elapsed,
            f"HTTP {resp.status_code}",
        )
        return data

    async def stop_task(self) -> dict:
        """停止 SRA 任务。"""
        t0 = time.perf_counter()
        url = self._url("/Task/stop")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url)
                data, err = self._parse_json(resp)
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            self._log_activity("sra_api", "POST /Task/stop", "fail", elapsed, str(e))
            return {"success": False, "message": f"请求失败: {e}"}

        elapsed = (time.perf_counter() - t0) * 1000
        if err:
            self._log_activity("sra_api", "POST /Task/stop", "fail", elapsed, err)
            return {"success": False, "message": err}
        data = data or {}
        ok = bool(data.get("success")) if isinstance(data, dict) else False
        self._log_activity("sra_api", "POST /Task/stop", "ok" if ok else "fail", elapsed, f"HTTP {resp.status_code}")
        return data

    async def get_status(self) -> dict:
        """获取 SRA 任务运行状态。

        兼容 SRA Server 两种返回格式：
          - 纯 bool: true / false
          - 结构体: {"running": true}

        Returns:
            {"running": bool}
        """
        t0 = time.perf_counter()
        url = self._url("/Task/status")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                raw, err = self._parse_json(resp)
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            self._log_activity("sra_api", "GET /Task/status", "fail", elapsed, str(e))
            return {"running": False, "error": str(e)}

        elapsed = (time.perf_counter() - t0) * 1000
        if err:
            self._log_activity("sra_api", "GET /Task/status", "fail", elapsed, err)
            return {"running": False, "error": err}

        # 兼容纯 bool 与 {"running": bool} 两种格式
        if isinstance(raw, bool):
            running = raw
        elif isinstance(raw, dict):
            running = bool(raw.get("running", False))
        else:
            running = False

        self._log_activity("sra_api", "GET /Task/status", "ok", elapsed, f"HTTP {resp.status_code}")
        return {"running": running}

    async def get_logs(self, count: int = 100) -> dict:
        """获取 SRA 最近日志。

        兼容 SRA Server 两种返回格式：
          - 纯列表: ["log1", "log2"]
          - 结构体: {"logs": ["log1", "log2"]}

        Args:
            count: 获取条数，默认 100（SRA 规范）

        Returns:
            {"logs": [str, ...]}
        """
        t0 = time.perf_counter()
        url = self._url(f"/Task/logs?count={count}")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                raw, err = self._parse_json(resp)
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            self._log_activity("sra_api", f"GET /Task/logs count={count}", "fail", elapsed, str(e))
            return {"logs": [], "error": str(e)}

        elapsed = (time.perf_counter() - t0) * 1000
        if err:
            self._log_activity("sra_api", f"GET /Task/logs count={count}", "fail", elapsed, err)
            return {"logs": [], "error": err}

        # 兼容纯 list 与 {"logs": [...]} 两种格式
        if isinstance(raw, list):
            logs = raw
        elif isinstance(raw, dict):
            logs = raw.get("logs", [])
            if not isinstance(logs, list):
                logs = []
        else:
            logs = []

        self._log_activity("sra_api", f"GET /Task/logs count={count}", "ok", elapsed, f"返回 {len(logs)} 条")
        return {"logs": logs}

    async def list_configs(self) -> dict:
        """获取 SRA 所有已保存配置名称列表。

        兼容 SRA Server 两种返回格式：
          - 纯列表: ["default", "farm"]
          - 结构体: {"configs": ["default", "farm"]}

        Returns:
            {"configs": [str, ...]}
        """
        t0 = time.perf_counter()
        url = self._url("/Configs")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                raw, err = self._parse_json(resp)
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            self._log_activity("sra_api", "GET /Configs", "fail", elapsed, str(e))
            return {"configs": [], "error": str(e)}

        elapsed = (time.perf_counter() - t0) * 1000
        if err:
            self._log_activity("sra_api", "GET /Configs", "fail", elapsed, err)
            return {"configs": [], "error": err}

        # 兼容纯 list 与 {"configs": [...]} 两种格式
        if isinstance(raw, list):
            configs = raw
        elif isinstance(raw, dict):
            configs = raw.get("configs", [])
            if not isinstance(configs, list):
                configs = []
        else:
            configs = []

        self._log_activity("sra_api", "GET /Configs", "ok", elapsed, f"返回 {len(configs)} 个")
        return {"configs": configs}
