"""AstrBot 插件 - SRA 调度器 (StarRailAssistant Remote Manager)

通过 `/sra` 指令组远程管理崩铁辅助工具 SRA, 调用 SRAFrontend.Server HTTP API。
"""
from pathlib import Path

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

from .activity_logger import ActivityLogger
from .sra_client import SRAClient

PLUGIN_NAME = "astrbot_plugin_sra_rms"

# 交流群信息
SUPPORT_INFO = (
    "\n\n如需帮助，欢迎加群交流：\n"
    "• 本插件交流群: 1098236107 (QQ, 入群口令: sra插件)\n"
    "• SRA 交流群: 994571792 (QQ)\n"
)


@register(PLUGIN_NAME, "MiaoR1Zibing", "用于调用崩铁辅助工具SRA(受限于SRA server提供的接口)。远程执行任务、查看状态与日志。\n   ⭐本插件交流群:1098236107   ⭐SRA交流群:994571792", "v0.4.0", "https://github.com/MiaoR1Zibing/astrbot_plugin_sra_rms")
class SRAPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self._client: SRAClient | None = None
        self._activity: ActivityLogger | None = None

    # -- 生命周期 ----------------------------------------------------------------

    async def initialize(self):
        """插件初始化：建立活动日志和 SRA HTTP 客户端。"""
        data_dir = Path(get_astrbot_data_path()) / "plugin_data" / PLUGIN_NAME
        data_dir.mkdir(parents=True, exist_ok=True)

        self._activity = ActivityLogger(data_dir, PLUGIN_NAME)
        self._activity.log("lifecycle", "插件初始化", "ok")

        host = self.config.get("sra_host", "localhost")
        port = self.config.get("sra_port", 5000)
        self._client = SRAClient(host=host, port=port, activity=self._activity)

        wl_on = self.config.get("enable_whitelist", False)
        wl_count = len(self.config.get("whitelist_users", []) or [])
        logger.info(f"[SRA] 插件已初始化, SRA Server = http://{host}:{port}, 白名单={'on' if wl_on else 'off'}({wl_count})")

    async def terminate(self):
        """插件卸载时记录退出日志。"""
        if self._activity:
            self._activity.log("lifecycle", "插件卸载", "ok")
        logger.info("[SRA] 插件已卸载")

    # -- 辅助方法 ----------------------------------------------------------------

    def _check_whitelist(self, event: AstrMessageEvent) -> bool:
        """检查当前事件是否通过白名单。

        白名单条目结构: {platform, msg_type, account_id}
        - platform: 匹配平台类型名(如 aiocqhttp)，"all" 视为通配
        - msg_type: all/group/private
        - account_id: 匹配 UMO 末尾的会话ID(账号/群号)

        判断策略: 优先用 event 方法获取信息,UMO 作为辅助
        - 平台: event.get_platform_name() → 平台类型名(如 aiocqhttp)
        - 消息类型: event.get_message_type() → MessageType 枚举
        - 会话ID: UMO 末尾段
        """
        if not self.config.get("enable_whitelist", False):
            return True

        whitelist = self.config.get("whitelist_users", []) or []
        if not whitelist:
            return False

        # 优先用方法获取
        platform_name = event.get_platform_name() or ""
        msg_type = event.get_message_type() or ""
        is_group = msg_type.value == "GroupMessage"

        # UMO 仅用于提取会话ID(末尾段)
        umo = event.unified_msg_origin or ""
        parts = umo.split(":", 2)
        umo_account = parts[2] if len(parts) == 3 else umo

        for entry in whitelist:
            e_platform = entry.get("platform", "all")
            e_msg_type = entry.get("msg_type", "all")
            e_account = str(entry.get("account_id", "")).strip()

            # 平台匹配: 用 get_platform_name() 取平台类型名
            if e_platform and e_platform != "all" and e_platform != platform_name:
                continue
            # 消息类型匹配
            if e_msg_type == "all":
                pass
            elif e_msg_type == "group" and not is_group:
                continue
            elif e_msg_type == "private" and is_group:
                continue
            # 账号匹配：UMO 会话ID 命中即可
            if not e_account:
                continue
            if e_account == umo_account:
                return True
        return False

    async def _ensure_client(self, event: AstrMessageEvent):
        """确保适配器已初始化，返回 (client, error_msg)。client 为 None 时 error_msg 不为空。"""
        if self._client is None:
            return None, "❌SRA适配器尚未初始化,请检查插件配置。" + SUPPORT_INFO
        return self._client, None

    # -- 指令组 ----------------------------------------------------------------

    @filter.command_group("sra")
    def sra(self):
        """SRA 远程管理指令组"""

    # === /sra help ===

    @sra.command("help")
    async def cmd_help(self, event: AstrMessageEvent):
        """查看 SRA 指令大全。"""
        if not self._check_whitelist(event):
            return
        lines = [
            "==SRA-RMS指令大全==",
            "/sra run [配置]",
            " ↑ 启动任务,可传序号或配置名",
            "    不传参数则缺省default",
            "/sra run all",
            " ↑ 启动全部任务",
            "/sra stop",
            " ↑ 停止当前任务",
            "/sra status",
            " ↑ 查看运行状态",
            "/sra logs [数量]",
            " ↑ 获取最近日志,默认100条",
            "/sra configs",
            " ↑ 查看已保存配置列表(带序号)",
            "/sra activity [数量]",
            " ↑ 查看行为日志,默认20条",
            "/sra help",
            " ↑ 显示本帮助",
        ]
        yield event.plain_result("\n".join(lines))

    # === /sra run ===

    @sra.command("run")
    async def cmd_run(self, event: AstrMessageEvent, config_name: str | None = None):
        """运行 SRA 任务。不带参数加载默认配置 "default"。可传序号或配置名。传 "all" 运行全部。"""
        if not self._check_whitelist(event):
            return
        client, err = await self._ensure_client(event)
        if client is None:
            yield event.plain_result(err)
            return

        # 不带参数 → 加载默认配置 "default"
        # 传 "all" → 运行全部已保存配置(空 body)
        resolved_name = config_name
        if config_name is None:
            resolved_name = "default"
        elif config_name == "all":
            resolved_name = ""
        elif config_name.isdigit():
            # 序号匹配：拉取配置列表做序号映射
            cfg_result = await client.list_configs()
            configs = cfg_result.get("configs", [])
            if "error" in cfg_result:
                yield event.plain_result(f"❌无法获取配置列表:{cfg_result['error']}" + SUPPORT_INFO)
                return
            idx = int(config_name)
            if idx < 1 or idx > len(configs):
                yield event.plain_result(f"❌序号超出范围,共{len(configs)}个配置,请用/sra configs查看。")
                return
            resolved_name = configs[idx - 1]

        try:
            result = await client.run_task(resolved_name)
        except Exception as e:
            yield event.plain_result(f"❌运行失败:{e}" + SUPPORT_INFO)
            return
        if result.get("success"):
            yield event.plain_result("✅任务已启动")
        else:
            yield event.plain_result(f"❌运行失败:{result.get('message', '未知错误')}")

    # === /sra stop ===

    @sra.command("stop")
    async def cmd_stop(self, event: AstrMessageEvent):
        """停止当前运行中的 SRA 任务。"""
        if not self._check_whitelist(event):
            return
        client, err = await self._ensure_client(event)
        if client is None:
            yield event.plain_result(err)
            return

        try:
            result = await client.stop_task()
        except Exception as e:
            yield event.plain_result(f"❌停止失败:{e}" + SUPPORT_INFO)
            return
        if result.get("success"):
            yield event.plain_result("✅已发送停止信号")
        else:
            yield event.plain_result(f"⚠️{result.get('message', '未知错误')}")

    # === /sra status ===

    @sra.command("status")
    async def cmd_status(self, event: AstrMessageEvent):
        """查看 SRA 任务运行状态。"""
        if not self._check_whitelist(event):
            return
        client, err = await self._ensure_client(event)
        if client is None:
            yield event.plain_result(err)
            return

        try:
            result = await client.get_status()
        except Exception as e:
            yield event.plain_result(f"❌无法获取状态:{e}" + SUPPORT_INFO)
            return
        running = result.get("running", False)
        if "error" in result:
            yield event.plain_result(f"❌无法获取状态:{result['error']}" + SUPPORT_INFO)
        elif running:
            yield event.plain_result("🟢SRA任务运行中")
        else:
            yield event.plain_result("⚪SRA当前无运行中的任务")

    # === /sra logs ===

    @sra.command("logs")
    async def cmd_logs(self, event: AstrMessageEvent, count: int = 100):
        """获取 SRA Server 最近日志。可指定数量，默认 100 条。用法: /sra logs [数量]"""
        if not self._check_whitelist(event):
            return
        client, err = await self._ensure_client(event)
        if client is None:
            yield event.plain_result(err)
            return

        try:
            result = await client.get_logs(count)
        except Exception as e:
            yield event.plain_result(f"❌获取日志失败:{e}" + SUPPORT_INFO)
            return
        raw_logs = result.get("logs", [])
        if "error" in result and not raw_logs:
            yield event.plain_result(f"❌获取日志失败:{result['error']}" + SUPPORT_INFO)
            return

        if not raw_logs:
            yield event.plain_result("📭SRA服务器暂无日志。")
            return

        # 截取不超过 15 条，避免消息过长
        display = raw_logs[-15:]
        header = f"📋SRA最近日志(共{len(raw_logs)}条):\n"
        body = "\n".join(f"  {line}" for line in display)
        yield event.plain_result(header + body)

    # === /sra activity ===

    @sra.command("activity")
    async def cmd_activity(self, event: AstrMessageEvent, count: int = 20):
        """查看本插件的活动摘要。可指定条数，默认 20 条。用法: /sra activity [数量]"""
        if not self._check_whitelist(event):
            return
        if self._activity is None:
            yield event.plain_result("❌活动日志尚未初始化。" + SUPPORT_INFO)
            return

        summary = self._activity.get_summary(count)
        yield event.plain_result(summary)

    # === /sra configs ===

    @sra.command("configs")
    async def cmd_configs(self, event: AstrMessageEvent):
        """查看 SRA Server 上所有已保存配置列表（带序号）。"""
        if not self._check_whitelist(event):
            return
        client, err = await self._ensure_client(event)
        if client is None:
            yield event.plain_result(err)
            return

        try:
            result = await client.list_configs()
        except Exception as e:
            yield event.plain_result(f"❌获取配置列表失败:{e}" + SUPPORT_INFO)
            return
        configs = result.get("configs", [])
        if "error" in result:
            yield event.plain_result(f"❌获取配置列表失败:{result['error']}" + SUPPORT_INFO)
            return

        if not configs:
            yield event.plain_result("📭SRA服务器暂无已保存配置。")
            return

        lines = [f"SRA已保存配置(共{len(configs)}个):"]
        for i, name in enumerate(configs, 1):
            lines.append(f"  {i}.{name}")
        yield event.plain_result("\n".join(lines))
