const bridge = window.AstrBotPluginPage;

const serverInfo = document.getElementById("serverInfo");
const statusPill = document.getElementById("statusPill");
const configSelect = document.getElementById("configSelect");
const configName = document.getElementById("configName");
const configEditor = document.getElementById("configEditor");
const taskResult = document.getElementById("taskResult");
const configResult = document.getElementById("configResult");
const logsOutput = document.getElementById("logsOutput");
const logCount = document.getElementById("logCount");

function printResult(target, value) {
  target.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function setBusy(button, busy) {
  button.disabled = busy;
  button.classList.toggle("busy", busy);
}

function normalizeConfigs(payload) {
  if (Array.isArray(payload)) return payload;
  if (payload && Array.isArray(payload.configs)) return payload.configs;
  return [];
}

async function loadInfo() {
  const info = await bridge.apiGet("info");
  serverInfo.textContent = info.base_url ? `SRA Server: ${info.base_url}` : "SRA Server 未初始化";
}

async function refreshStatus() {
  const payload = await bridge.apiGet("status");
  if (payload.error) {
    statusPill.textContent = "连接失败";
    statusPill.dataset.state = "error";
    printResult(taskResult, payload);
    return;
  }
  statusPill.textContent = payload.running ? "运行中" : "空闲";
  statusPill.dataset.state = payload.running ? "running" : "idle";
}

async function refreshConfigs() {
  const payload = await bridge.apiGet("configs");
  const configs = normalizeConfigs(payload);
  configSelect.replaceChildren();

  for (const name of configs) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    configSelect.appendChild(option);
  }

  if (configs.length === 0) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "暂无配置";
    configSelect.appendChild(option);
  }

  const firstConfig = configs[0] || "";
  configName.value = configSelect.value || firstConfig;
  if (firstConfig) {
    await loadConfig(firstConfig);
  }
}

async function loadConfig(name = configName.value || configSelect.value) {
  const safeName = String(name || "").trim();
  if (!safeName) {
    printResult(configResult, "请先选择或输入配置名。");
    return;
  }
  configName.value = safeName;
  const payload = await bridge.apiGet("config", { name: safeName });
  if (payload.error) {
    printResult(configResult, payload);
    return;
  }
  configEditor.value = JSON.stringify(payload.config ?? {}, null, 2);
  printResult(configResult, `已读取配置：${safeName}`);
}

async function saveConfig() {
  const safeName = configName.value.trim();
  if (!safeName) {
    printResult(configResult, "配置名不能为空。");
    return;
  }

  let parsed;
  try {
    parsed = JSON.parse(configEditor.value);
  } catch (error) {
    printResult(configResult, `JSON 格式错误：${error.message}`);
    return;
  }

  const payload = await bridge.apiPost("config", { name: safeName, config: parsed });
  printResult(configResult, payload);
  if (payload.success) {
    await refreshConfigs();
    configSelect.value = safeName;
  }
}

async function runTask(config) {
  const payload = await bridge.apiPost("run", { configName: config });
  printResult(taskResult, payload);
  await refreshStatus();
}

async function stopTask() {
  const payload = await bridge.apiPost("stop", {});
  printResult(taskResult, payload);
  await refreshStatus();
}

async function refreshLogs() {
  const count = Math.min(Math.max(Number(logCount.value) || 100, 1), 500);
  const payload = await bridge.apiGet("logs", { count });
  if (payload.error) {
    printResult(logsOutput, payload);
    return;
  }
  const logs = Array.isArray(payload.logs) ? payload.logs : [];
  logsOutput.textContent = logs.length ? logs.join("\n") : "暂无日志。";
}

function bindActions() {
  document.getElementById("refreshStatusBtn").addEventListener("click", refreshStatus);
  document.getElementById("refreshLogsBtn").addEventListener("click", refreshLogs);
  document.getElementById("reloadConfigBtn").addEventListener("click", () => loadConfig());
  document.getElementById("saveConfigBtn").addEventListener("click", async (event) => {
    setBusy(event.currentTarget, true);
    try {
      await saveConfig();
    } finally {
      setBusy(event.currentTarget, false);
    }
  });

  document.getElementById("runBtn").addEventListener("click", () => runTask(configSelect.value || configName.value));
  document.getElementById("runAllBtn").addEventListener("click", () => runTask(""));
  document.getElementById("stopBtn").addEventListener("click", stopTask);

  configSelect.addEventListener("change", () => {
    configName.value = configSelect.value;
    loadConfig(configSelect.value);
  });
}

async function boot() {
  await bridge.ready();
  bindActions();
  await loadInfo();
  await Promise.allSettled([refreshStatus(), refreshConfigs(), refreshLogs()]);
}

boot().catch((error) => {
  serverInfo.textContent = `页面初始化失败：${error.message}`;
  statusPill.textContent = "错误";
  statusPill.dataset.state = "error";
});
