---
title: 'SRA HTTP Server 参考'
date: 2026-06-17
description: StarRailAssistant SRAFrontend.Server HTTP服务实现与接口参考
source: E:\_1code\python\StarRailAssistant\SRAFrontend\SRAFrontend.Server
---

# SRAFrontend.Server HTTP 服务实现参考

## 概述

SRAFrontend.Server 是 StarRailAssistant 项目的前端后端服务，采用 **ASP.NET Core** 构建，提供 RESTful API 和 SSE 实时日志流。

## 技术栈

- **框架**: ASP.NET Core 8.0 (Minimal API + Controllers)
- **API 文档**: OpenAPI / Swagger (内置)
- **实时通信**: Server-Sent Events (SSE)
- **端口**: `http://localhost:5073` (默认 HTTP)

---

## 目录结构

```
SRAFrontend.Server/
├── Program.cs                           # 应用入口
├── SRAFrontend.Server.csproj            # 项目文件
├── Properties/
│   └── launchSettings.json              # 启动配置
├── Controllers/
│   ├── TaskController.cs                # 任务管理接口
│   ├── SettingsController.cs            # 设置管理接口
│   └── ConfigsController.cs             # 配置管理接口
└── Services/
    ├── LogStreamService.cs              # 日志流服务 (SSE)
    └── HostedService.cs                 # 生命周期托管服务
```

---

## 服务注册 (Program.cs)

```csharp
var builder = WebApplication.CreateBuilder(args);

// 注册服务
builder.Services.AddSingleton<PyBackendService>();       // Python 后端进程管理
builder.Services.AddSingleton<CliBackendService>();      // CLI 后端进程管理
builder.Services.AddSingleton<IBackendService, BackendServiceProxy>(); // 后端服务代理
builder.Services.AddSingleton<SettingsService>();        // 设置服务
builder.Services.AddSingleton<CacheService>();            // 缓存服务
builder.Services.AddSingleton<ConfigService>();           // 配置服务
builder.Services.AddSingleton<LogStreamService>();       // 日志流服务
builder.Services.AddHostedService<HostedService>();       // 生命周期托管
builder.Services.AddControllers();                         // 控制器
builder.Services.AddOpenApi();                            // OpenAPI

var app = builder.Build();

// 配置 HTTP 管道
app.MapOpenApi();
app.UseSwaggerUI(options => { options.SwaggerEndpoint("/openapi/v1.json", "v1"); });
// app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();
app.Run();
```

---

## 接口一览

### 1. TaskController - 任务管理

| 方法 | 路径                | 功能         | 说明                                                                 |
| ---- | ------------------- | ------------ | -------------------------------------------------------------------- |
| POST | `/Task/run`         | 运行任务     | 支持三种模式：空参数(全部)、Config(内联配置)、ConfigName(加载已保存) |
| POST | `/Task/stop`        | 停止任务     | 发送停止信号                                                         |
| GET  | `/Task/status`      | 获取状态     | 返回 bool，任务是否运行中                                            |
| GET  | `/Task/logs`        | 获取最近日志 | `?count=100` 指定数量，默认100条                                     |
| GET  | `/Task/logs/stream` | SSE日志流    | 实时推送日志到客户端                                                 |

#### POST /Task/run

**请求体 (RunRequest)**:

```json
{
  "ConfigName": "my_config", // 可选：加载已保存配置
  "Config": {
    // 可选：内联完整配置
    "Name": "config_name"
    // ... TasksConfig 完整结构
  },
  "Persist": false // 可选：是否持久化内联配置
}
```

**响应**:

```json
// 成功
{ "success": true, "message": "Task started" }

// 冲突
{ "success": false, "message": "A task is already running" }
```

#### GET /Task/logs/stream (SSE)

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: [2026-06-17 10:00:00] 任务开始运行...
data: [2026-06-17 10:00:01] 检测到图像...
data: [2026-06-17 10:00:02] 点击了按钮...
```

---

### 2. SettingsController - 设置管理

| 方法 | 路径        | 功能         |
| ---- | ----------- | ------------ |
| GET  | `/Settings` | 获取全部设置 |
| PUT  | `/Settings` | 部分更新设置 |

#### GET /Settings

返回完整的 `AppSettings` 对象。

#### PUT /Settings

支持部分更新，请求体示例：

```json
{
  "advanced": {
    "backend.remote.enabled": true
  }
}
```

---

### 3. ConfigsController - 配置管理

| 方法   | 路径                    | 功能                 |
| ------ | ----------------------- | -------------------- |
| GET    | `/Configs`              | 获取所有配置名称列表 |
| GET    | `/Configs/{configName}` | 获取指定配置完整内容 |
| POST   | `/Configs/{configName}` | 新建配置             |
| PUT    | `/Configs/{configName}` | 更新配置             |
| DELETE | `/Configs/{configName}` | 删除配置             |

---

## 核心服务

### LogStreamService - 日志流服务

```csharp
public sealed class LogStreamService : IDisposable
{
    // 订阅后端日志
    public IAsyncEnumerable<string> Subscribe(CancellationToken cancellationToken = default);

    // 获取最近的日志条目
    public List<string> GetRecentLogs(int count = 100);
}
```

**实现特点**:

- 使用 `Channel<string>` 实现异步日志流
- 维护最近 500 条日志缓存
- 支持多个 SSE 客户端同时订阅
- 使用 `WeakReference` 自动清理断开连接的客户端
- 日志通过 `IBackendService.Outputted` 事件注入

---

### HostedService - 生命周期服务

```csharp
public class HostedService : IHostedService
{
    public Task StartAsync(CancellationToken cancellationToken);  // 加载配置/设置/缓存
    public Task StopAsync(CancellationToken cancellationToken);  // 保存配置/设置/缓存，停止后端
}
```

---

## 后端服务接口 (IBackendService)

| 成员                        | 说明                    |
| --------------------------- | ----------------------- |
| `IsTaskRunning`             | 任务是否运行中          |
| `event Outputted`           | 后端输出事件 (日志来源) |
| `StartBackend(args)`        | 启动后端进程            |
| `TaskRunAsync(configName?)` | 运行任务                |
| `TaskStopAsync()`           | 停止任务                |
| `StopBackend()`             | 停止后端进程            |

---

## 启动配置 (launchSettings.json)

```json
{
  "profiles": {
    "http": {
      "commandName": "Project",
      "applicationUrl": "http://localhost:5073",
      "environmentVariables": {
        "ASPNETCORE_ENVIRONMENT": "Development"
      }
    },
    "https": {
      "commandName": "Project",
      "applicationUrl": "https://localhost:7216;http://localhost:5073"
    }
  }
}
```

---

## 关键设计模式

### 1. SSE (Server-Sent Events)

用于实时推送日志到前端，无需 WebSocket：

```csharp
Response.Headers.ContentType = "text/event-stream";
Response.Headers.Cache-Control = "no-cache";
Response.Headers.Connection = "keep-alive";

await foreach (var line in logStream.Subscribe(token))
{
    await Response.WriteAsync($"data: {line}\n\n", token);
    await Response.Body.FlushAsync(token);
}
```

### 2. 部分更新 (SettingsController)

通过反射实现 JSON path 风格的部分更新：

```json
// 请求
{ "advanced": { "backend.remote.enabled": true } }

// 内部实现：找到对应的 Section 对象，用反射设置字段
```

### 3. 三种任务运行模式

| 模式 | ConfigName | Config | 行为                     |
| ---- | ---------- | ------ | ------------------------ |
| 1    | null       | null   | 运行全部已保存配置       |
| 2    | null       | 有     | 运行内联配置，可选持久化 |
| 3    | 有         | null   | 加载指定配置并运行       |

---

## 与 AstrBot 插件集成参考

如需在本项目中实现类似的 HTTP 服务：

1. **使用 ASP.NET Core Minimal API** 或 **Quart** (Python)
2. **SSE 实现**: 使用 `yield` 生成器模式推送流式数据
3. **服务注册**: 类似 `Context.register_web_api()`
4. **生命周期管理**: 在 `initialize()` 启动服务，在 `terminate()` 停止服务

---

**文档信息**

- 原始源码: `E:\_1code\python\StarRailAssistant\SRAFrontend\SRAFrontend.Server`
- 整理时间: 2026-06-17
