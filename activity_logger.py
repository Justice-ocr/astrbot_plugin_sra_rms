"""原子行为日志记录模块 - 记录插件所有关键操作到外部 data 目录。"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from astrbot.api import logger as astr_logger


class ActivityLogger:
    """记录插件所有原子行为到 JSON Lines 文件。

    每条记录包含：时间戳、行为分类、描述、结果状态、耗时(ms)、详情。
    自动轮转：单文件超过 5000 条后归档。
    """

    def __init__(self, data_dir: Path, plugin_name: str):
        self._log_dir = data_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._file = self._log_dir / f"{plugin_name}_activity.log"
        self._max_entries = 5000

    def _rotate(self):
        if not self._file.exists():
            return
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                count = sum(1 for _ in f)
        except Exception:
            count = 0
        if count < self._max_entries:
            return
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive = self._log_dir / f"activity_archive_{ts}.log"
        try:
            os.rename(self._file, archive)
        except OSError:
            pass

    def _write(self, entry: dict):
        self._rotate()
        try:
            with open(self._file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            astr_logger.error(f"[ActivityLogger] 写入日志失败: {e}")

    def log(
        self,
        category: str,
        description: str,
        result: str = "ok",
        elapsed_ms: float = 0.0,
        detail: Optional[str] = None,
    ):
        """记录一条原子行为。

        Args:
            category: 行为分类，如 sra_api / command / lifecycle
            description: 行为描述
            result: 结果状态 ok / fail / warn
            elapsed_ms: 耗时(毫秒)
            detail: 补充详情
        """
        entry = {
            "time": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "description": description,
            "result": result,
            "elapsed_ms": round(elapsed_ms, 2),
        }
        if detail:
            entry["detail"] = detail
        self._write(entry)

    def get_recent(self, count: int = 50) -> list[dict]:
        """获取最近 N 条行为记录。"""
        entries: list[dict] = []
        if not self._file.exists():
            return entries
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            astr_logger.error(f"[ActivityLogger] 读取日志失败: {e}")
        return entries[-count:]

    def get_summary(self, count: int = 20) -> str:
        """获取总结版日志，返回纯文本可读内容，不使用 markdown 语法。"""
        entries = self.get_recent(count)
        if not entries:
            return "暂无活动记录。"

        lines = [f"SRA 插件活动摘要 (最近 {len(entries)} 条)"]
        for e in entries:
            status_icon = {"ok": "[OK]", "fail": "[FAIL]", "warn": "[WARN]"}.get(e.get("result", ""), "[?]")
            t = e.get("time", "")[:19].replace("T", " ")
            desc = e.get("description", "")
            ms = e.get("elapsed_ms", 0)
            lines.append(f"  {status_icon} {t} {desc} ({ms:.0f}ms)")
        return "\n".join(lines)
