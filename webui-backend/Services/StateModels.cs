namespace SRAWebHost.Services;

public sealed record SraStatusDto(bool Running, int? Pid, string ExecutablePath, int Port, string? Detail = null);

public sealed record SraStartResult(bool Ok, bool Started, int? Pid, string Message);

public sealed record LogEntryDto(string Time, string Level, string Message);

public sealed record ConfigSummaryDto(string Name, string Description);

public sealed record ConfigDetailDto(string Name, object Data);
