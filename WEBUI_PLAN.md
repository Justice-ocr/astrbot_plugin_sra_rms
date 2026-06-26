# SRA WebUI Plan

## Goal
Build an independent browser-based WebUI for SRA, with a lightweight always-on host, configuration editing, live logs, and task control.

## Stack
- Backend: ASP.NET Core Minimal API
- Frontend: Vue 3 + Element Plus + TypeScript
- Realtime logs: SSE first, SignalR later if needed

## Initial scope
- Health endpoint
- Static homepage
- Configuration read/write
- Task start/stop/status
- Log history + stream
- Auto-start SRA backend from the WebUI host

## Packaging direction
- Ship `SRA-server.exe` and `SRAWebHost.exe` together in one release folder.
- Keep both on the same .NET major version to minimize runtime installs.
- Default user entrypoint: run `SRAWebHost.exe`, then open `http://127.0.0.1:5074`.

## Next steps
1. Finish backend proxy and startup flow.
2. Bind the Vue UI to real config and log endpoints.
3. Verify build/publish and browser launch.
4. Add bootstrap docs for boot-time startup and remote access.
