# astrbot_plugin_sra_rms

> 反馈交流群：
>
> - 本插件交流群: 1098236107 (QQ, 入群口令: sra插件)
> - SRA 交流群: 994571792 (QQ)

AstrBot 插件，用于远程管理崩坏：星穹铁道辅助工具 [SRA (StarRailAssistant)](https://github.com/Shasnow/StarRailAssistant)。通过 SRAFrontend.Server 提供的 HTTP API，在聊天平台中执行任务、查看状态与日志。

## 功能

- 任务管理：运行 / 停止 SRA 任务
- 状态查询：查看 SRA 任务运行状态
- 日志查看：获取 SRA 服务器最近日志
- 配置列表：查看 SRA 已保存配置，支持序号运行
- 活动记录：插件所有原子行为自动记录，可查看摘要
- 指令白名单：按平台 / 消息类型 / 账号限制使用权限
- 多语言：WebUI 配置项支持中英文

## 前置要求

1. 已部署 AstrBot（>= v4.16）
2. 已部署 SRA 并启用 SRAFrontend.Server（默认端口 5073）

## 安装

在 AstrBot WebUI 的插件市场页面搜索 `astrbot_plugin_sra_rms` 安装，或手动克隆到插件目录：

```bash
git clone https://github.com/MiaoR1Zibing/astrbot_plugin_sra_rms.git
```

## 配置

安装后在 AstrBot WebUI 的插件配置页填写：

| 配置项          | 说明                                      | 默认值    |
| --------------- | ----------------------------------------- | --------- |
| SRA Server 地址 | 填SRA中你设置的地址(不带:1234之类的)      | localhost |
| SRA Server 端口 | 填SRA中你设置的端口(在这里填冒号后的数字) | 5000      |
| 启用指令白名单  | 开启后仅白名单用户可用                    | false     |
| 指令白名单      | 平台 / 消息类型 / 账号 三维匹配(平台选all通配)   | 空        |

## 指令

所有指令以 `/sra` 为前缀。发送 `/sra help` 可查看指令大全。

| 指令                   | 说明                                                                              | 示例                                                   |
| ---------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `/sra help`            | 查看指令大全                                                                      | `/sra help`                                            |
| `/sra run [配置]`      | 运行任务。不带参数加载默认配置 "default"；传序号需先查看 configs；传 all 运行全部 | `/sra run` `/sra run 2` `/sra run farm` `/sra run all` |
| `/sra stop`            | 停止当前运行中的任务                                                              | `/sra stop`                                            |
| `/sra status`          | 查看任务运行状态                                                                  | `/sra status`                                          |
| `/sra logs [数量]`     | 获取 SRA 最近日志，默认 100 条                                                    | `/sra logs` `/sra logs 50`                             |
| `/sra configs`         | 查看 SRA 已保存配置列表（带序号）                                                 | `/sra configs`                                         |
| `/sra activity [数量]` | 查看本插件活动摘要，默认 20 条                                                    | `/sra activity`                                        |

### run 指令的参数匹配

1. 不带参数 → 加载默认配置 "default"
2. 纯数字序号 → 先拉取配置列表，按序号映射到配置名
3. `all` → 运行全部已保存配置
4. 其他字符串 → 直接作为配置名传给 SRA

## 数据存储

所有插件数据存储在 AstrBot 外部数据目录，不污染插件自身目录：

```
<AstrBot数据目录>/plugin_data/astrbot_plugin_sra_rms/
├── astrbot_plugin_sra_rms_activity.log    # 活动日志
└── activity_archive_*.log                 # 归档日志（超过5000条自动轮转）
```

## 相关仓库

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) - 本插件运行的聊天机器人框架
- [StarRailAssistant](https://github.com/Shasnow/StarRailAssistant) - 崩坏：星穹铁道辅助工具
