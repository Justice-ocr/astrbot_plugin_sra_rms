---
title: "AstrBot 插件编写规范"
date: 2026-06-17
description: AstrBot 插件开发完整指南，涵盖环境准备、目录结构、指令处理、LLM集成、配置系统、UI页面等全部核心功能
source:
  - ./01_插件开发指南.md
  - ./02_最小实例.md
  - ./03_监听消息事件.md
  - ./04_发送消息.md
  - ./05_插件配置.md
  - ./06_插件页面.md
  - ./07_插件国际化.md
  - ./08_AI与工具调用.md
  - ./09_存储.md
  - ./10_文转图.md
  - ./11_会话控制.md
  - ./12_杂项.md
  - ./13_发布插件.md
---

# AstrBot 插件编写规范

## 概述

本文档是 AstrBot 插件开发的完整规范指南，包含从环境准备到发布的全流程说明。

> 详细的单项内容请参考 `./doc` 目录下的专题文档。

---

## 目录

- [快速开始](./02_最小实例.md) - 5 分钟搭建最小插件
- [环境准备](./01_插件开发指南.md#环境准备) - 获取模板、克隆项目、调试插件
- [插件目录结构](./01_插件开发指南.md#插件目录结构) - 目录规范与文件说明
- [metadata.yaml 规范](./01_插件开发指南.md#metadatayaml-规范) - 插件元数据配置
- [main.py 编写规范](./02_最小实例.md) - 插件核心代码结构
- [指令系统](./03_监听消息事件.md) - 命令、指令组、过滤器、事件钩子
- [消息处理](./03_监听消息事件.md#消息与事件) - 消息链、消息对象、事件类型
- [发送消息](./04_发送消息.md) - 被动消息、主动消息、富媒体消息
- [插件配置](./05_插件配置.md) - Schema 定义、WebUI 可视化配置
- [插件页面](./06_插件页面.md) - 自定义 Dashboard 页面开发
- [插件国际化](./07_插件国际化.md) - 多语言支持
- [AI 与工具调用](./08_AI与工具调用.md) - LLM 集成、Tool 定义、Agent 开发
- [存储方案](./09_存储.md) - KV 存储与大文件规范
- [文转图](./10_文转图.md) - HTML/Jinja2 模板渲染
- [会话控制](./11_会话控制.md) - 多轮对话实现
- [平台适配器](./14_平台适配器开发.md) - 自定义平台接入
- [HTTP API](./15_HTTP_API.md) - 外部系统集成接口
- [开发原则](./01_插件开发指南.md#开发原则) - 代码规范与最佳实践
- [发布插件](./13_发布插件.md) - 插件市场上架流程

---

## 插件目录结构

详细说明请参见 [插件开发指南](./01_插件开发指南.md#插件目录结构)。

```
astrbot_plugin_xxx/           # 插件目录，推荐以 astrbot_plugin_ 开头
├── metadata.yaml             # 【必须】插件元数据
├── main.py                   # 【必须】主逻辑文件
├── _conf_schema.json         # 【可选】配置文件 Schema
├── logo.png                  # 【可选】插件 Logo，256x256，1:1 比例
├── requirements.txt          # 【可选】Python 依赖
├── skills/                   # 【可选】技能文件目录
├── pages/                    # 【可选】Dashboard 页面目录
└── .astrbot-plugin/          # 【可选】国际化文件
    └── i18n/
        ├── zh-CN.json
        └── en-US.json
```

---

## metadata.yaml 规范

详细字段说明请参见 [插件开发指南](./01_插件开发指南.md#metadatayaml-规范)。

```yaml
# 必须字段
name: astrbot_plugin_xxx      # 唯一标识，与目录名一致
version: v0.1                 # 版本号，格式：v1.1.1 或 v1.1
author: 作者名                 # 作者

# 可选字段
display_name: 插件展示名       # WebUI 展示名称（需要 v4.5.0+）
desc: 插件简短描述              # 详细描述
short_desc: 一句话介绍         # 卡片短描述
repo: https://github.com/xxx   # 仓库地址
support_platforms:             # 支持的平台列表
  - telegram
  - discord
astrbot_version: ">=4.16,<5"  # AstrBot 版本约束（PEP 440）
```

---

## main.py 编写规范

最小实例请参见 [最小实例](./02_最小实例.md)。

### 基础结构

```python
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("插件标识", "作者", "描述", "版本号", "仓库地址")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """插件初始化，可选实现"""
        pass

    # 指令 handler
    @filter.command("指令名")
    async def my_command(self, event: AstrMessageEvent):
        """指令描述，建议填写"""
        user_name = event.get_sender_name()
        yield event.plain_result(f"Hello, {user_name}!")

    async def terminate(self):
        """插件卸载/停用时调用，可选实现"""
        pass
```

### 核心要点

1. **插件类必须继承 `Star` 类**
2. **构造函数必须接受 `context: Context` 参数**
3. **所有 handler 必须是 `async def`**
4. **handler 前两个参数必须是 `self` 和 `event`**
5. **使用 `yield` 返回结果**（生成器模式）

---

## 指令系统

详细说明请参见 [监听消息事件](./03_监听消息事件.md)。

### @filter.command 装饰器

```python
@filter.command("指令名")
async def my_command(self, event: AstrMessageEvent):
    """指令描述"""
    user_name = event.get_sender_name()
    message_str = event.message_str
    yield event.plain_result(f"回复内容")
```

### 带参指令

```python
@filter.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    # /add 1 2 -> 结果是: 3
    yield event.plain_result(f"结果是: {a + b}!")
```

### 指令组

```python
@filter.command_group("math")
def math():
    pass

@math.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a + b}")

@math.command("sub")
async def sub(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a - b}")
```

### 事件类型过滤

```python
# 只接收私聊消息
@filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
async def on_private_message(self, event: AstrMessageEvent):
    yield event.plain_result("收到了一条私聊消息。")

# 仅管理员可用
@filter.permission_type(filter.PermissionType.ADMIN)
@filter.command("test")
async def test(self, event: AstrMessageEvent):
    pass
```

### 事件钩子

详细说明请参见 [监听消息事件 - 事件钩子](./03_监听消息事件.md#事件钩子)。

| 钩子 | 说明 |
|------|------|
| `@filter.on_astrbot_loaded()` | Bot 初始化完成时 |
| `@filter.on_waiting_llm_request()` | 等待 LLM 请求时 |
| `@filter.on_llm_request()` | LLM 请求时 |
| `@filter.on_llm_response()` | LLM 请求完成时 |
| `@filter.on_decorating_result()` | 发送消息前 |
| `@filter.after_message_sent()` | 发送消息后 |

---

## 消息处理

详细说明请参见 [监听消息事件 - 消息与事件](./03_监听消息事件.md#消息与事件)。

### AstrMessageEvent 常用属性

| 属性/方法 | 说明 |
|-----------|------|
| `message_str` | 消息纯文本 |
| `get_messages()` | 获取消息链 |
| `get_sender_name()` | 获取发送者名称 |
| `sender_id` | 发送者 ID |
| `session_id` | 会话 ID |
| `group_id` | 群 ID（群消息时） |
| `message_obj` | 原始消息对象 |

### 消息组件

```python
from astrbot.api.message_components import *

# 常用组件
Text("内容")                    # 纯文本
Image(file_path="本地路径")      # 本地图片
Image(url="网络地址")            # 网络图片
At(user_id=123456)              # At 某人
Face(id=123)                    # 表情
Record(file="path.silk")        # 语音
Video.fromURL(url="...")        # 视频
File(file="path.txt")           # 文件
MentionAll()                    # 提及所有人
```

---

## 发送消息

详细说明请参见 [发送消息](./04_发送消息.md)。

### 被动消息（回复）

```python
yield event.plain_result("纯文本消息")
yield event.image_result("path/to/image.jpg")
yield event.image_result("https://example.com/image.jpg")
yield event.chain_result([...])  # 富文本消息链
```

### 主动消息

```python
from astrbot.api.event import MessageChain

umo = event.unified_msg_origin
message_chain = MessageChain().message("Hello!")
await self.context.send_message(event.unified_msg_origin, message_chain)
```

### 富文本消息链

```python
yield event.chain_result([
    Text("来看这个图："),
    Image.fromURL("https://example.com/image.jpg"),
    Image.fromFileSystem("path/to/image.jpg"),
])
```

---

## 插件配置

详细说明请参见 [插件配置](./05_插件配置.md)。

### _conf_schema.json 结构

```json
{
    "token": {
        "description": "Bot Token",
        "type": "string"
    },
    "enable": {
        "description": "是否启用",
        "type": "bool",
        "default": true
    },
    "count": {
        "description": "数量",
        "type": "int",
        "default": 10
    }
}
```

### 配置类型

| type | 说明 |
|------|------|
| `string` | 字符串 |
| `text` | 多行文本（大的 textarea） |
| `int` | 整数 |
| `float` | 浮点数 |
| `bool` | 布尔值 |
| `object` | 嵌套对象 |
| `list` | 列表 |
| `dict` | 字典 |
| `file` | 文件上传（v4.13.0+） |
| `template_list` | 模板列表（v4.10.4+） |

### 在插件中使用配置

```python
from astrbot.api import AstrBotConfig

class ConfigPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        # self.config.save_config() # 保存配置
```

---

## 插件页面

详细说明请参见 [插件页面](./06_插件页面.md)。

### 目录结构

```
pages/
└── my-page/
    ├── index.html
    ├── app.js
    └── style.css
```

### 注册后端 API

```python
from quart import jsonify

context.register_web_api(
    f"/{PLUGIN_NAME}/ping",
    self.page_ping,
    ["GET"],
    "Page ping",
)

async def page_ping(self):
    return jsonify({"message": "pong"})
```

### Bridge API (前端)

| 方法 | 说明 |
|------|------|
| `ready()` | 等待 bridge 就绪 |
| `apiGet(endpoint)` | GET 请求 |
| `apiPost(endpoint, body)` | POST 请求 |
| `upload(endpoint, file)` | 文件上传 |
| `subscribeSSE(endpoint, handlers)` | 订阅 SSE |

---

## AI 与工具调用

详细说明请参见 [AI 与工具调用](./08_AI与工具调用.md)。

### 调用大模型

```python
umo = event.unified_msg_origin
provider_id = await self.context.get_current_chat_provider_id(umo=umo)

llm_resp = await self.context.llm_generate(
    chat_provider_id=provider_id,
    prompt="Hello, world!",
)
# llm_resp.completion_text 获取返回文本
```

### 定义 Tool

```python
from pydantic import Field
from pydantic.dataclasses import dataclass
from astrbot.core.agent.tool import FunctionTool, ToolExecResult

@dataclass
class BilibiliTool(FunctionTool[AstrAgentContext]):
    name: str = "bilibili_videos"
    description: str = "A tool to fetch Bilibili videos."
    parameters: dict = Field(default_factory=lambda: {
        "type": "object",
        "properties": {
            "keywords": {"type": "string", "description": "Keywords to search."},
        },
        "required": ["keywords"],
    })

    async def call(self, context, **kwargs) -> ToolExecResult:
        return "视频搜索结果..."
```

### 注册 Tool

```python
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.context.add_llm_tools(BilibiliTool(), ...)
```

### 调用 Agent

```python
llm_resp = await self.context.tool_loop_agent(
    event=event,
    chat_provider_id=prov_id,
    prompt="搜索 bilibili 视频",
    tools=ToolSet([BilibiliTool()]),
    max_steps=30,
    tool_call_timeout=60,
)
```

---

## 存储方案

详细说明请参见 [存储](./09_存储.md)。

### KV 存储

```python
await self.put_kv_data("key", value)
value = await self.get_kv_data("key", default=None)
await self.delete_kv_data("key")
```

### 大文件存储

```python
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

plugin_data_path = get_astrbot_data_path() / "plugin_data" / self.name
```

---

## 文转图

详细说明请参见 [文转图](./10_文转图.md)。

### 基础用法

```python
url = await self.text_to_image(text)
yield event.image_result(url)
```

### 自定义 HTML 模板

```python
TMPL = '''
<div style="font-size: 32px;">
    <h1>Todo List</h1>
    <ul>
        {% for item in items %}
        <li>{{ item }}</li>
        {% endfor %}
    </ul>
</div>
'''

url = await self.html_render(TMPL, {"items": ["吃饭", "睡觉"]})
yield event.image_result(url)
```

---

## 会话控制

详细说明请参见 [会话控制](./11_会话控制.md)。

```python
from astrbot.core.utils.session_waiter import session_waiter, SessionController

@filter.command("成语接龙")
async def idiom_game(self, event: AstrMessageEvent):
    yield event.plain_result("请发送一个成语~")

    @session_waiter(timeout=60, record_history_chains=False)
    async def wait_handler(controller: SessionController, event: AstrMessageEvent):
        idiom = event.message_str
        if idiom == "退出":
            controller.stop()
            return
        await event.send(event.plain_result(f"你说了: {idiom}"))
        controller.keep(timeout=60, reset_timeout=True)

    await wait_handler(event)
```

---

## 异步编程规范

详细说明请参见 [插件开发指南 - 开发原则](./01_插件开发指南.md#开发原则)。

### 必须使用异步网络库

- ✅ 使用 `aiohttp` 或 `httpx`（异步）
- ❌ 不要使用 `requests`（同步阻塞）

```python
# 正确
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com")

# 错误
import requests  # 不要用！
```

---

## 开发原则

详细说明请参见 [插件开发指南 - 开发原则](./01_插件开发指南.md#开发原则)。

1. **功能需经过测试**
2. **良好的注释**
3. **错误处理** - 使用 try/except
4. **数据持久化** - 存储到 `data` 目录
5. **代码格式化** - 使用 `ruff`
6. **异步网络请求** - 使用 `aiohttp` 或 `httpx`

### 推荐错误处理

```python
@filter.command("mycmd")
async def my_command(self, event: AstrMessageEvent):
    try:
        result = await some_async_call()
        yield event.plain_result(result)
    except Exception as e:
        logger.error(f"命令执行失败: {e}")
        yield event.plain_result("处理失败，请稍后重试")
```

### 代码格式化

```bash
ruff format .
ruff check .
```

---

## 完整示例

```python
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import *

@register("astrbot_plugin_example", "作者", "插件描述", "v1.0.0")
class ExamplePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info("示例插件初始化")

    @filter.command("hello")
    async def hello(self, event: AstrMessageEvent):
        """打招呼指令"""
        user_name = event.get_sender_name()
        yield event.plain_result(f"你好，{user_name}！")

    @filter.command("pic")
    async def send_pic(self, event: AstrMessageEvent):
        """发送图片指令"""
        yield event.chain_result([
            Text("这是一张图片："),
            Image(url="https://example.com/demo.png")
        ])

    async def terminate(self):
        logger.info("示例插件已卸载")
```

---

## 参考资源

| 资源 | 链接 |
|------|------|
| 官方文档 | https://docs.astrbot.app/dev/star/plugin-new.html |
| 插件模板 | https://github.com/Soulter/helloworld |
| 开发者 QQ 群 | 975206796 |
| 插件市场 | https://plugins.astrbot.app/ |

---

## 文档更新日志

| 日期 | 说明 |
|------|------|
| 2026-06-17 | 初始整理，基于官方文档 v4.16+ |
