---
title: "16 - AstrBot配置详解"
date: 2026-06-17
description: AstrBot 配置文件 data/cmd_config.json 完整字段说明
---

# AstrBot 配置文件

## data/cmd_config.json

AstrBot 的配置文件是一个 JSON 格式的文件。AstrBot 会在启动时读取这个文件，并根据文件中的配置来初始化 AstrBot，其路径位于 `data/cmd_config.json`。

在 AstrBot v4.0.0 版本及之后，我们引入了多配置文件的概念。`data/cmd_config.json` 作为默认配置文件 `default`。其他您在 WebUI 新建的配置文件会存储在 `data/config/` 目录下，以 `abconf_` 开头。

---

## 目录

- [config_version](#config_version)
- [platform_settings](#platform_settings)
  - [unique_session](#platform_settingsunique_session)
  - [rate_limit](#platform_settingsrate_limit)
  - [reply_prefix](#platform_settingsreply_prefix)
  - [forward_threshold](#platform_settingsforward_threshold)
  - [enable_id_white_list](#platform_settingsenable_id_white_list)
  - [id_whitelist](#platform_settingsid_whitelist)
  - [id_whitelist_log](#platform_settingsid_whitelist_log)
  - [wl_ignore_admin_on_group](#platform_settingswl_ignore_admin_on_group--platform_settingswl_ignore_admin_on_friend)
  - [reply_with_mention](#platform_settingsreply_with_mention)
  - [reply_with_quote](#platform_settingsreply_with_quote)
  - [segmented_reply](#platform_settingssegmented_reply)
  - [no_permission_reply](#platform_settingsno_permission_reply)
  - [empty_mention_waiting](#platform_settingsempty_mention_waiting)
  - [friend_message_needs_wake_prefix](#platform_settingsfriend_message_needs_wake_prefix)
  - [ignore_bot_self_message](#platform_settingsignore_bot_self_message)
  - [ignore_at_all](#platform_settingsignore_at_all)
- [provider](#provider)
- [provider_settings](#provider_settings)
  - [enable](#provider_settingsenable)
  - [default_provider_id](#provider_settingsdefault_provider_id)
  - [default_image_caption_provider_id](#provider_settingsdefault_image_caption_provider_id)
  - [image_caption_prompt](#provider_settingsimage_caption_prompt)
  - [wake_prefix](#provider_settingswake_prefix)
  - [web_search](#provider_settingsweb_search)
  - [websearch_provider](#provider_settingswebsearch_provider)
  - [datetime_system_prompt](#provider_settingsdatetime_system_prompt)
  - [default_personality](#provider_settingsdefault_personality)
  - [prompt_prefix](#provider_settingsprompt_prefix)
  - [max_context_length](#provider_settingsmax_context_length)
  - [streaming_response](#provider_settingsstreaming_response)
  - [show_tool_use_status](#provider_settingsshow_tool_use_status)
  - [max_agent_step](#provider_settingsmax_agent_step)
  - [tool_call_timeout](#provider_settingstool_call_timeout)
- [provider_stt_settings](#provider_stt_settings)
- [provider_tts_settings](#provider_tts_settings)
- [provider_ltm_settings](#provider_ltm_settings)
- [content_safety](#content_safety)
- [admins_id](#admins_id)
- [t2i](#t2i)
- [http_proxy / no_proxy](#http_proxy--no_proxy)
- [dashboard](#dashboard)
- [timezone](#timezone)

---

## config_version

配置文件版本，请勿修改。

---

## platform_settings

消息平台适配器的通用设置。

### platform_settings.unique_session

是否启用会话隔离。默认为 `false`。启用后，在群组或者频道中，每个人的对话的上下文都是独立的。

### platform_settings.rate_limit

当消息速率超过限制时的处理策略。`time` 为时间窗口，`count` 为消息数量，`strategy` 为限制策略。`stall` 为等待，`discard` 为丢弃。

### platform_settings.reply_prefix

回复消息时的固定前缀字符串。默认为空。

### platform_settings.forward_threshold

目前仅 QQ 平台适配器适用。消息转发阈值。当回复内容超过一定字数后，机器人会将消息折叠成 QQ 群聊的"转发消息"。

### platform_settings.enable_id_white_list

是否启用 ID 白名单。默认为 `true`。启用后，只有在白名单中的 ID 发来的消息才会被处理。

### platform_settings.id_whitelist

ID 白名单。填写后，将只处理所填写的 ID 发来的消息事件。可以使用 `/sid` 指令获取在某个平台上的会话 ID。

### platform_settings.id_whitelist_log

是否打印未通过 ID 白名单的消息日志。默认为 `true`。

### platform_settings.wl_ignore_admin_on_group & platform_settings.wl_ignore_admin_on_friend

- `wl_ignore_admin_on_group`: 管理员发送的群组消息是否无视 ID 白名单。默认为 `true`。
- `wl_ignore_admin_on_friend`: 管理员发送的私聊消息是否无视 ID 白名单。默认为 `true`。

### platform_settings.reply_with_mention

是否在回复消息时 @ 提到用户。默认为 `false`。

### platform_settings.reply_with_quote

是否在回复消息时引用用户的消息。默认为 `false`。

### platform_settings.segmented_reply

分段回复设置。

| 字段 | 说明 |
|------|------|
| `enable` | 是否启用分段回复。默认为 `false` |
| `only_llm_result` | 是否仅对 LLM 生成的回复进行分段。默认为 `true` |
| `interval_method` | 分段间隔方法，可选 `random` 或 `log` |
| `interval` | 分段间隔时间 |
| `words_count_threshold` | 分段回复的字数上限。默认为 `150` |
| `regex` | 用于分隔一段消息的正则表达式 |
| `content_cleanup_rule` | 移除分段后的内容中的指定内容 |

### platform_settings.no_permission_reply

是否在用户没有权限时回复无权限的提示消息。默认为 `true`。

### platform_settings.empty_mention_waiting

是否启用空 @ 等待机制。默认为 `true`。启用后，当用户发送一条仅包含 @ 机器人的消息时，机器人会等待用户在 60 秒内发送下一条消息。

### platform_settings.friend_message_needs_wake_prefix

是否在消息平台的私聊消息中需要唤醒前缀。默认为 `false`。

### platform_settings.ignore_bot_self_message

是否忽略机器人自己发送的消息。默认为 `false`。

### platform_settings.ignore_at_all

是否忽略 @ 全体成员的消息。默认为 `false`。

---

## provider

此配置项仅在 `data/cmd_config.json` 中生效。已配置的模型服务提供商的配置列表。

---

## provider_settings

大语言模型提供商的通用设置。

| 配置项 | 说明 |
|--------|------|
| `enable` | 是否启用大语言模型聊天。默认为 `true` |
| `default_provider_id` | 默认的对话模型提供商 ID |
| `default_image_caption_provider_id` | 默认的图像描述模型提供商 ID |
| `image_caption_prompt` | 图像描述的提示词模板 |
| `wake_prefix` | 使用 LLM 聊天额外的触发条件 |
| `web_search` | 是否启用 AstrBot 自带的网页搜索能力 |
| `websearch_provider` | 网页搜索提供商类型，可选 `tavily`、`bocha`、`baidu_ai_search`、`brave` |
| `datetime_system_prompt` | 是否在系统提示词中加上当前机器的日期时间 |
| `default_personality` | 默认使用的人格的 ID |
| `prompt_prefix` | 用户提示词，可使用 `{{prompt}}` 作为用户输入的占位符 |
| `max_context_length` | 当对话上下文超出这个数量时丢弃最旧的部分。-1 为不限制 |
| `streaming_response` | 是否启用流式响应 |
| `show_tool_use_status` | 是否显示工具使用状态 |
| `max_agent_step` | Agent 最大步骤数限制。默认为 `30` |
| `tool_call_timeout` | 工具调用的最大超时时间（秒），默认为 `60` |

---

## provider_stt_settings

语音转文本服务提供商的通用设置。

| 配置项 | 说明 |
|--------|------|
| `enable` | 是否启用语音转文本服务 |
| `provider_id` | 语音转文本服务提供商 ID |

---

## provider_tts_settings

文本转语音服务提供商的通用设置。

| 配置项 | 说明 |
|--------|------|
| `enable` | 是否启用文本转语音服务 |
| `provider_id` | 文本转语音服务提供商 ID |
| `dual_output` | 是否启用双输出 |
| `use_file_service` | 是否启用文件服务 |

---

## provider_ltm_settings

群聊上下文感知服务提供商的通用设置。

| 配置项 | 说明 |
|--------|------|
| `group_icl_enable` | 是否启用群聊上下文感知 |
| `group_message_max_cnt` | 群聊消息的最大记录数量。默认为 `100` |
| `image_caption` | 是否记录群聊中的图片并生成描述 |
| `active_reply` | 主动回复设置 |

---

## content_safety

内容安全设置。

| 配置项 | 说明 |
|--------|------|
| `also_use_in_response` | 是否在 LLM 回复中也进行内容安全检查 |
| `internal_keywords` | 内部关键词检测设置 |
| `baidu_aip` | 百度 AI 内容审核设置 |

---

## admins_id

管理员 ID 列表。此外，还可以使用 `/op`, `/deop` 指令来添加或删除管理员。

---

## t2i

是否启用文本转图像功能。默认为 `false`。

| 配置项 | 说明 |
|--------|------|
| `t2i_word_threshold` | 文转图的字数阈值。默认为 `150` |
| `t2i_strategy` | 渲染策略，可选 `local` 或 `remote` |
| `t2i_endpoint` | AstrBot API 的地址 |
| `t2i_use_file_service` | 是否启用文件服务 |

---

## http_proxy / no_proxy

HTTP 代理设置。如 `http://localhost:7890`。`no_proxy` 列出不使用代理的地址列表。

---

## dashboard

AstrBot WebUI 配置。

```json
"dashboard": {
    "enable": true,
    "username": "astrbot",
    "password": "<your_password_md5>",
    "jwt_secret": "",
    "host": "0.0.0.0",
    "port": 6185
}
```

---

## timezone

时区设置。默认为 `Asia/Shanghai`。

---

**文档信息**

- 原始文档: https://docs.astrbot.app/dev/astrbot-config.html
- 整理时间: 2026-06-17
