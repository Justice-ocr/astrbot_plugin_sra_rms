using System.Diagnostics;
using System.Net.Sockets;
using Microsoft.Extensions.Options;
using SRAWebHost.Config;

namespace SRAWebHost.Services;

public sealed class SraServerSupervisor(IOptionsMonitor<SraServerOptions> options)
{
    private readonly object _gate = new();
    private Process? _process;

    public async Task<object> GetStateAsync(CancellationToken ct)
    {
        var portOpen = await IsPortOpenAsync(ct);
        lock (_gate)
        {
            var running = (_process is { HasExited: false }) || portOpen;
            return new SraStatusDto(
                running,
                running ? _process?.Id : null,
                ResolveExecutablePath(options.CurrentValue.ExecutablePath),
                options.CurrentValue.Port,
                _process is { HasExited: false } ? "running" : (portOpen ? "listening" : "stopped"));
        }
    }

    public async Task<object> EnsureStartedAsync(CancellationToken ct)
    {
        if (await IsPortOpenAsync(ct))
            return new SraStartResult(true, false, null, "SRA server already listening");

        lock (_gate)
        {
            if (_process is not null && !_process.HasExited)
                return new SraStartResult(true, false, _process.Id, "SRA server already running");

            var exe = ResolveExecutablePath(options.CurrentValue.ExecutablePath);
            if (!File.Exists(exe))
                return new SraStartResult(false, false, null, $"SRA server not found: {exe}");

            var workDir = string.IsNullOrWhiteSpace(options.CurrentValue.WorkingDirectory)
                ? Path.GetDirectoryName(exe) ?? AppContext.BaseDirectory
                : ResolvePath(options.CurrentValue.WorkingDirectory);

            var startInfo = new ProcessStartInfo
            {
                FileName = exe,
                WorkingDirectory = workDir,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            if (options.CurrentValue.Port > 0)
                startInfo.ArgumentList.Add($"--urls=http://127.0.0.1:{options.CurrentValue.Port}");
            if (!string.IsNullOrWhiteSpace(options.CurrentValue.ApiKey))
                startInfo.Environment["ApiKey"] = options.CurrentValue.ApiKey;

            _process = Process.Start(startInfo);
            return new SraStartResult(true, _process is not null, _process?.Id, "SRA server started");
        }
    }

    private static string ResolvePath(string path)
    {
        return Path.IsPathRooted(path)
            ? Path.GetFullPath(path)
            : ResolveRelativePath(path);
    }

    private static string ResolveRelativePath(string path)
    {
        var candidates = new List<string>
        {
            Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, path)),
            Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), path))
        };

        var current = new DirectoryInfo(AppContext.BaseDirectory);
        for (var i = 0; i < 6 && current is not null; i++, current = current.Parent)
        {
            candidates.Add(Path.GetFullPath(Path.Combine(current.FullName, path)));
        }

        foreach (var candidate in candidates)
        {
            if (File.Exists(candidate) || Directory.Exists(candidate))
                return candidate;
        }

        return candidates[0];
    }

    private string ResolveExecutablePath(string path) => ResolvePath(path);

    private async Task<bool> IsPortOpenAsync(CancellationToken ct)
    {
        try
        {
            using var client = new TcpClient();
            var connectTask = client.ConnectAsync("127.0.0.1", options.CurrentValue.Port);
            var completed = await Task.WhenAny(connectTask, Task.Delay(250, ct));
            return completed == connectTask && client.Connected;
        }
        catch
        {
            return false;
        }
    }
}
