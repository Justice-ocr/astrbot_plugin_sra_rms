# SRA WebUI

Browser-based management UI for SRA.

## Goal
Run `SRA-server.exe` on boot, then use a Vue + Element Plus web UI to manage configs, tasks, and logs.

## Stack
- Backend: ASP.NET Core Minimal API
- Frontend: Vue 3 + Element Plus + TypeScript
- Realtime logs: SSE

## Layout
- `webui-backend/`: host and API adapter
- `webui-frontend/`: Vue client

## Ports
- SRA server: `5073`
- WebUI host: `5074`

## Runtime
- SRA本体: .NET 10
- WebUI host: .NET 10

## Current status
- Backend host proxies the real SRA server API
- Frontend is a Vue + Element Plus control panel
- Default backend target is `..\\StarRailAssistant-sync\\SRA-local-output\\SRA-server.exe`

## Run
1. Build frontend: `cd webui-frontend && pnpm build`
2. Run host: `dotnet run --project webui-backend\\SRAWebHost.csproj`
3. Open `http://127.0.0.1:5074`

## Notes
- SRA auto-start is controlled by the host config.
- Logs are available as history plus SSE stream.
- Config and settings are edited as raw JSON.
