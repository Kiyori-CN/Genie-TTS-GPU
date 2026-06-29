const el = (id) => document.getElementById(id);

const STORAGE_KEY = "genie-webui-language";
const AUTO_REFRESH_INTERVAL_MS = 5000;
const MODES = ["cuda", "cpu", "directml", "auto"];
const LANGUAGE_STRINGS = {
  zh: {
    pageTitle: "Genie-TTS WebUI",
    languageButton: "EN",
    languageTitle: "切换到英文界面",
    healthPending: "健康 -",
    healthOk: "健康 正常",
    healthWarn: "健康 警告",
    healthError: "健康 异常",
    activityIdle: "空闲",
    activityBusy: "忙碌",
    apiLabel: "API",
    localLabel: "本机",
    lanLabel: "局域网",
    copyApiTitle: "复制 API 基址",
    copyLocalTitle: "复制本机 WebUI 地址",
    copyLanTitle: "复制局域网 WebUI 地址",
    refreshTitle: "刷新运行状态",
    stopTitle: "停止当前合成",
    autoRefresh: "自动刷新",
    autoRefreshTitle: "启用或关闭周期刷新",
    unloadSessionsLabel: "卸载已加载会话",
    unloadSessionsTitle: "切换运行模式时同时释放已加载模型会话",
    runtimeTitle: "运行时",
    runtimeModeLabel: "运行模式",
    applyRuntime: "应用",
    modeLabel: "模式",
    selectedLabel: "已选 provider",
    availableLabel: "可用 provider",
    loadedLabel: "已加载角色",
    sessionProvidersTitle: "会话 provider",
    activityTitle: "活动",
    busyLabel: "忙碌",
    activeSessionLabel: "会话",
    jobsLabel: "作业",
    readerLabel: "阅读器",
    synthesisTitle: "合成",
    notLoaded: "未加载",
    characterNameLabel: "角色名",
    languageLabel: "语言",
    modelDirLabel: "ONNX 模型目录",
    referenceAudioLabel: "参考音频路径",
    referenceTextLabel: "参考文本",
    inputTextLabel: "输入文本",
    splitSentenceLabel: "智能分句",
    endpointModeLabel: "端点",
    modeCompleteWav: "完整 WAV - /tts/wav",
    modeLegadoBuffered: "Legado buffered - 稳定",
    modeLegadoStream: "Legado stream - 低延迟",
    modeStreamWav: "Stream WAV - 通用",
    modeRawPcm: "Raw PCM - 直下",
    modeJob: "队列作业 - 长文本",
    loadCharacter: "加载",
    setReference: "参考",
    prepare: "加载 + 参考",
    clearCache: "清缓存",
    restoreDefaults: "恢复默认",
    generate: "生成",
    outputTitle: "输出",
    requestIdle: "空闲",
    rawPcmTitle: "Raw PCM",
    rawPcmDesc: "pcm_s16le，32000 Hz，单声道",
    streamWavTitle: "Stream WAV",
    streamWavDesc: "分块 audio/wav",
    bufferedWavTitle: "Buffered WAV",
    bufferedWavDesc: "合成结束后返回完整文件",
    jobWavTitle: "Job WAV",
    jobWavDesc: "队列作业输出文件",
    downloadOutput: "下载输出",
    responseModeLabel: "模式",
    responseBytesLabel: "字节",
    responseElapsedLabel: "耗时",
    responseFormatLabel: "格式",
    jobTitle: "作业",
    cancelJob: "取消",
    jobIdLabel: "作业 id",
    jobStatusLabel: "状态",
    jobStageLabel: "阶段",
    jobMessageLabel: "消息",
    logTitle: "日志",
    clearLogTitle: "清空日志",
    runtimeJsonTitle: "运行时 JSON",
    statusJsonTitle: "状态 JSON",
    characterRequired: "角色名是必填项。",
    inputRequired: "输入文本是必填项。",
    loadFieldsRequired: "角色名、模型目录和语言是必填项。",
    referenceFieldsRequired: "角色名、参考音频、参考文本和语言是必填项。",
    unsupportedMode: "不支持的端点模式：{mode}",
    runtimeConfigured: "运行模式已应用：{mode}",
    runtimeApplied: "运行模式已应用",
    loadSuccess: "角色已加载",
    referenceSuccess: "参考音频已设置",
    preparedReady: "就绪",
    preparedReload: "需要重载角色",
    requestStarted: "开始请求：{format}",
    requestReady: "{format} 已就绪",
    requestError: "错误：{message}",
    audioReady: "音频已就绪：{format}，{bytes} 字节，{elapsed}s",
    jobSubmitted: "已提交作业：{jobId}",
    jobCompleted: "作业已完成：{jobId}",
    jobFailed: "作业 {status}：{jobId}",
    jobCancelRequested: "已请求取消作业：{jobId}",
    jobPollingFailed: "作业轮询失败：{message}",
    stopRequested: "已请求停止",
    requestAborted: "请求已中止",
    refreshFailed: "刷新失败：{message}",
    initLoaded: "WebUI 已加载",
    initFailed: "初始化失败：{message}",
    noLanDetected: "没有检测到可用的局域网 IPv4",
    providerNotLoaded: "未加载",
    yes: "是",
    no: "否",
    activeMetric: "活跃",
    queuedMetric: "排队",
    runningMetric: "运行",
    recentMetric: "最近",
    charsMetric: "字符",
    wordsMetric: "词",
    linesMetric: "行",
    sentencesMetric: "句",
    paragraphsMetric: "段",
    copySuccess: "已复制：{label}",
    copyFailed: "复制失败：{message}",
    cacheCleared: "参考音频缓存已清除",
    defaultsRestored: "默认值已恢复",
  },
  en: {
    pageTitle: "Genie-TTS WebUI",
    languageButton: "中文",
    languageTitle: "Switch to Chinese UI",
    healthPending: "Health -",
    healthOk: "Health OK",
    healthWarn: "Health warn",
    healthError: "Health error",
    activityIdle: "Idle",
    activityBusy: "Busy",
    apiLabel: "API",
    localLabel: "Local",
    lanLabel: "LAN",
    copyApiTitle: "Copy API base URL",
    copyLocalTitle: "Copy local WebUI URL",
    copyLanTitle: "Copy LAN WebUI URL",
    refreshTitle: "Refresh runtime state",
    stopTitle: "Stop current synthesis",
    autoRefresh: "Auto refresh",
    autoRefreshTitle: "Enable or disable periodic refresh",
    unloadSessionsLabel: "Unload loaded sessions",
    unloadSessionsTitle: "Release loaded model sessions when applying runtime mode",
    runtimeTitle: "Runtime",
    runtimeModeLabel: "Runtime mode",
    applyRuntime: "Apply",
    modeLabel: "Mode",
    selectedLabel: "Selected provider",
    availableLabel: "Available provider",
    loadedLabel: "Loaded characters",
    sessionProvidersTitle: "Session providers",
    activityTitle: "Activity",
    busyLabel: "Busy",
    activeSessionLabel: "Session",
    jobsLabel: "Jobs",
    readerLabel: "Reader",
    synthesisTitle: "Synthesis",
    notLoaded: "Not loaded",
    characterNameLabel: "Character name",
    languageLabel: "Language",
    modelDirLabel: "ONNX model directory",
    referenceAudioLabel: "Reference audio path",
    referenceTextLabel: "Reference text",
    inputTextLabel: "Input text",
    splitSentenceLabel: "Smart sentence split",
    endpointModeLabel: "Endpoint",
    modeCompleteWav: "Complete WAV - /tts/wav",
    modeLegadoBuffered: "Legado buffered - stable",
    modeLegadoStream: "Legado stream - low latency",
    modeStreamWav: "Stream WAV - generic",
    modeRawPcm: "Raw PCM - download",
    modeJob: "Queued job - long text",
    loadCharacter: "Load",
    setReference: "Reference",
    prepare: "Load + reference",
    clearCache: "Clear cache",
    restoreDefaults: "Defaults",
    generate: "Generate",
    outputTitle: "Output",
    requestIdle: "Idle",
    rawPcmTitle: "Raw PCM",
    rawPcmDesc: "pcm_s16le, 32000 Hz, mono",
    streamWavTitle: "Stream WAV",
    streamWavDesc: "chunked audio/wav",
    bufferedWavTitle: "Buffered WAV",
    bufferedWavDesc: "complete file after synthesis",
    jobWavTitle: "Job WAV",
    jobWavDesc: "queued output file",
    downloadOutput: "Download output",
    responseModeLabel: "Mode",
    responseBytesLabel: "Bytes",
    responseElapsedLabel: "Elapsed",
    responseFormatLabel: "Format",
    jobTitle: "Job",
    cancelJob: "Cancel",
    jobIdLabel: "Job id",
    jobStatusLabel: "Status",
    jobStageLabel: "Stage",
    jobMessageLabel: "Message",
    logTitle: "Log",
    clearLogTitle: "Clear log",
    runtimeJsonTitle: "Runtime JSON",
    statusJsonTitle: "Status JSON",
    characterRequired: "Character name is required.",
    inputRequired: "Input text is required.",
    loadFieldsRequired: "Character name, model directory, and language are required.",
    referenceFieldsRequired: "Character, reference audio, reference text, and language are required.",
    unsupportedMode: "Unsupported endpoint mode: {mode}",
    runtimeConfigured: "Runtime configured: {mode}",
    runtimeApplied: "Runtime applied",
    loadSuccess: "Character loaded",
    referenceSuccess: "Reference audio set",
    preparedReady: "Ready",
    preparedReload: "Reload character",
    requestStarted: "Request started: {format}",
    requestReady: "{format} ready",
    requestError: "Error: {message}",
    audioReady: "Audio ready: {format}, {bytes} bytes, {elapsed}s",
    jobSubmitted: "Job submitted: {jobId}",
    jobCompleted: "Job completed: {jobId}",
    jobFailed: "Job {status}: {jobId}",
    jobCancelRequested: "Job cancel requested: {jobId}",
    jobPollingFailed: "Job polling failed: {message}",
    stopRequested: "Stop requested",
    requestAborted: "Request aborted",
    refreshFailed: "Refresh failed: {message}",
    initLoaded: "WebUI loaded",
    initFailed: "Init failed: {message}",
    noLanDetected: "No LAN IPv4 detected",
    providerNotLoaded: "Not loaded",
    yes: "Yes",
    no: "No",
    activeMetric: "Active",
    queuedMetric: "Queued",
    runningMetric: "Running",
    recentMetric: "Recent",
    charsMetric: "chars",
    wordsMetric: "words",
    linesMetric: "lines",
    sentencesMetric: "sentences",
    paragraphsMetric: "paragraphs",
    copySuccess: "Copied: {label}",
    copyFailed: "Copy failed: {message}",
    cacheCleared: "Reference audio cache cleared",
    defaultsRestored: "Defaults restored",
  },
};

let config = null;
let activeAudioUrl = null;
let activeJobTimer = null;
let activeRefreshTimer = null;
let activeLanguage = "zh";
let activeTtsController = null;
let refreshAllInFlight = false;
let lastRuntimeSnapshot = null;
let lastStatusSnapshot = null;
let lastRequestSummary = null;
let lastHealthState = {kind: "pending", detail: null};
let lastPreparedState = "not_loaded";
let lastRequestBadge = {key: "requestIdle", state: "muted", values: {}};

function nowStamp() {
  return new Date().toLocaleTimeString();
}

function getStrings() {
  return LANGUAGE_STRINGS[activeLanguage] || LANGUAGE_STRINGS.zh;
}

function formatText(template, values = {}) {
  return String(template).replace(/\{([a-zA-Z0-9_]+)\}/g, (match, key) => (
    Object.prototype.hasOwnProperty.call(values, key) ? String(values[key]) : match
  ));
}

function t(key, values = {}) {
  const strings = getStrings();
  return formatText(strings[key] || LANGUAGE_STRINGS.zh[key] || key, values);
}

function setDocumentLanguage(language) {
  document.documentElement.lang = language === "en" ? "en" : "zh-CN";
  document.title = t("pageTitle");
}

function setLanguage(language, persist = true) {
  activeLanguage = language === "en" ? "en" : "zh";
  if (persist) {
    localStorage.setItem(STORAGE_KEY, activeLanguage);
  }
  setDocumentLanguage(activeLanguage);
  applyTranslations();
  renderDynamicState();
}

function detectInitialLanguage() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === "en" || saved === "zh") {
    return saved;
  }
  const browserLanguage = (navigator.language || navigator.userLanguage || "").toLowerCase();
  return browserLanguage.startsWith("en") ? "en" : "zh";
}

function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.getAttribute("data-i18n");
    if (!key) return;
    node.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-title]").forEach((node) => {
    const key = node.getAttribute("data-i18n-title");
    if (!key) return;
    node.title = t(key);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((node) => {
    const key = node.getAttribute("data-i18n-aria-label");
    if (!key) return;
    node.setAttribute("aria-label", t(key));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    const key = node.getAttribute("data-i18n-placeholder");
    if (!key) return;
    node.placeholder = t(key);
  });
  document.querySelectorAll("[data-i18n-option]").forEach((node) => {
    const key = node.getAttribute("data-i18n-option");
    if (!key) return;
    node.textContent = t(key);
  });
}

function renderDynamicState() {
  el("languageToggle").textContent = t("languageButton");
  el("languageToggle").title = t("languageTitle");
  renderAccess(config?.access || null);
  renderHealthBadge();
  renderPreparedBadge();
  renderRequestBadge();
  renderRequestSummary();
  renderRuntime(lastRuntimeSnapshot);
  renderStatus(lastStatusSnapshot);
  updateTextStats();
}

function renderHealthBadge() {
  if (lastHealthState.kind === "ok") {
    setBadge(el("healthBadge"), t("healthOk"), "ok");
  } else if (lastHealthState.kind === "warn") {
    const text = lastHealthState.detail ? `${t("healthWarn")}: ${lastHealthState.detail}` : t("healthWarn");
    setBadge(el("healthBadge"), text, "warn");
  } else if (lastHealthState.kind === "error") {
    setBadge(el("healthBadge"), t("healthError"), "error");
  } else {
    setBadge(el("healthBadge"), t("healthPending"), "muted");
  }
}

function setHealthBadge(kind, detail = null) {
  lastHealthState = {kind, detail};
  renderHealthBadge();
}

function renderPreparedBadge() {
  if (lastPreparedState === "reload") {
    setBadge(el("preparedBadge"), t("preparedReload"), "warn");
  } else if (lastPreparedState === "busy") {
    setBadge(el("preparedBadge"), t("activityBusy"), "warn");
  } else if (lastPreparedState === "error") {
    setBadge(el("preparedBadge"), t("healthError"), "error");
  } else if (lastPreparedState === "not_loaded") {
    setBadge(el("preparedBadge"), t("notLoaded"), "muted");
  } else {
    setBadge(el("preparedBadge"), t("preparedReady"), "ok");
  }
}

function renderRequestBadge() {
  setBadge(el("requestBadge"), t(lastRequestBadge.key, lastRequestBadge.values), lastRequestBadge.state);
}

function setRequestBadge(key, state = "muted", values = {}) {
  lastRequestBadge = {key, state, values};
  renderRequestBadge();
}

function appendLog(message, data = null) {
  const box = el("logBox");
  const line = `[${nowStamp()}] ${message}`;
  const extra = data ? `\n${JSON.stringify(data, null, 2)}` : "";
  box.textContent = `${line}${extra}\n${box.textContent}`.slice(0, 24000);
}

function setBadge(node, text, state = "muted") {
  if (!node) return;
  node.textContent = text;
  node.className = `badge ${state}`;
}

function clearNode(node) {
  if (!node) return;
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function setPills(node, items = []) {
  if (!node) return;
  clearNode(node);
  const values = items.filter(Boolean);
  if (!values.length) {
    node.textContent = "-";
    return;
  }
  for (const item of values) {
    const pill = document.createElement("span");
    const detail = typeof item === "string" ? {label: item} : item;
    pill.className = `pill ${detail.state || "muted"}`;
    pill.textContent = detail.label || "-";
    if (detail.title) {
      pill.title = detail.title;
    }
    node.appendChild(pill);
  }
}

function shortProvider(provider) {
  const known = {
    CUDAExecutionProvider: "CUDA",
    CPUExecutionProvider: "CPU",
    DmlExecutionProvider: "DirectML",
  };
  return provider ? (known[provider] || provider.replace(/ExecutionProvider$/, "")) : t("providerNotLoaded");
}

function providerPillState(provider) {
  if (!provider) return "warn";
  if (provider === "CUDAExecutionProvider" || provider === "DmlExecutionProvider") return "ok";
  if (provider === "CPUExecutionProvider") return "muted";
  return "warn";
}

function providerPills(providers, emptyState = "warn") {
  const values = Array.isArray(providers) && providers.length ? providers : [null];
  return values.map((provider) => ({
    label: shortProvider(provider),
    title: provider || t("providerNotLoaded"),
    state: provider ? providerPillState(provider) : emptyState,
  }));
}

function providerListText(providers) {
  const values = Array.isArray(providers) && providers.length ? providers : [null];
  return values.map(shortProvider).join(", ");
}

function formatBytes(value) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return String(value);
  }
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / 1024 / 1024).toFixed(2)} MB`;
}

function formatSeconds(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  return `${number.toFixed(2)}s`;
}

function runtimeBadgeInfo(runtime) {
  const mode = runtime?.runtime_mode || "-";
  const providers = runtime?.selected_providers || [];
  const primary = providers[0] || null;
  const label = primary ? `${mode} · ${shortProvider(primary)}` : mode;
  if (primary === "CUDAExecutionProvider" || primary === "DmlExecutionProvider") {
    return {label, state: "ok"};
  }
  if (!primary && ["cuda", "directml", "auto"].includes(mode)) {
    return {label, state: "warn"};
  }
  if (["cuda", "directml", "auto"].includes(mode) && primary === "CPUExecutionProvider") {
    return {label, state: "warn"};
  }
  return {label, state: "muted"};
}

function jsonPreview(id, value) {
  el(id).textContent = value ? JSON.stringify(value, null, 2) : "-";
}

async function readError(response) {
  const type = response.headers.get("content-type") || "";
  if (type.includes("application/json")) {
    try {
      const data = await response.json();
      return data.detail || data.message || JSON.stringify(data);
    } catch (error) {
      return `${response.status} ${response.statusText}`;
    }
  }
  const text = await response.text();
  return text || `${response.status} ${response.statusText}`;
}

function abortActiveTtsRequest() {
  if (activeTtsController) {
    activeTtsController.abort();
    activeTtsController = null;
  }
}

async function apiJson(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      ...(options.body ? {"Content-Type": "application/json"} : {}),
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json();
}

async function apiBlob(path, payload) {
  abortActiveTtsRequest();
  const controller = new AbortController();
  activeTtsController = controller;
  try {
    const response = await fetch(path, {
      method: "POST",
      signal: controller.signal,
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(await readError(response));
    }
    return {
      blob: await response.blob(),
      headers: response.headers,
      status: response.status,
    };
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(t("requestAborted"));
    }
    throw error;
  } finally {
    if (activeTtsController === controller) {
      activeTtsController = null;
    }
  }
}

function clearAudio() {
  if (activeAudioUrl) {
    URL.revokeObjectURL(activeAudioUrl);
    activeAudioUrl = null;
  }
  el("audioPlayer").pause();
  el("audioPlayer").removeAttribute("src");
  el("audioPlayer").load();
  const link = el("downloadLink");
  link.removeAttribute("href");
  link.classList.add("disabled");
}

function setAudio(blob, filename) {
  clearAudio();
  activeAudioUrl = URL.createObjectURL(blob);
  el("audioPlayer").src = activeAudioUrl;
  el("audioPlayer").load();
  const link = el("downloadLink");
  link.href = activeAudioUrl;
  link.download = filename;
  link.classList.remove("disabled");
}

function setAudioUrl(url, filename) {
  clearAudio();
  el("audioPlayer").src = url;
  el("audioPlayer").load();
  const link = el("downloadLink");
  link.href = url;
  link.download = filename;
  link.classList.remove("disabled");
}

function setDownloadOnly(blob, filename) {
  clearAudio();
  activeAudioUrl = URL.createObjectURL(blob);
  const link = el("downloadLink");
  link.href = activeAudioUrl;
  link.download = filename;
  link.classList.remove("disabled");
}

function clearJobView() {
  el("jobBox").classList.add("hidden");
  el("jobId").textContent = "-";
  el("jobStatus").textContent = "-";
  el("jobStage").textContent = "-";
  el("jobMessage").textContent = "-";
}

function setRequestSummary({mode = "-", bytes = "-", elapsed = "-", format = "-"} = {}) {
  lastRequestSummary = {mode, bytes, elapsed, format};
  renderRequestSummary();
}

function renderRequestSummary() {
  const summary = lastRequestSummary || {mode: "-", bytes: "-", elapsed: "-", format: "-"};
  el("responseMode").textContent = summary.mode;
  el("responseBytes").textContent = typeof summary.bytes === "number" ? formatBytes(summary.bytes) : summary.bytes;
  el("responseElapsed").textContent = summary.elapsed;
  el("responseFormat").textContent = summary.format;
}

function updateTextStats() {
  const text = el("inputText")?.value || "";
  const trimmed = text.trim();
  const lines = text ? text.split(/\r?\n/).filter((line) => line.trim()).length : 0;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  const sentenceMatches = trimmed.match(/[。！？!?\.]+/g) || [];
  const sentences = trimmed ? Math.max(1, sentenceMatches.length) : 0;
  const paragraphs = trimmed ? trimmed.split(/\n\s*\n/).filter(Boolean).length : 0;
  const metrics = activeLanguage === "en"
    ? [
      `${text.length} ${t("charsMetric")}`,
      `${words} ${t("wordsMetric")}`,
      `${sentences} ${t("sentencesMetric")}`,
      `${lines} ${t("linesMetric")}`,
    ]
    : [
      `${text.length} ${t("charsMetric")}`,
      `${sentences} ${t("sentencesMetric")}`,
      `${paragraphs} ${t("paragraphsMetric")}`,
      `${lines} ${t("linesMetric")}`,
    ];
  el("textStats").textContent = metrics.join(" · ");
}

function setPreparedBadge(kind = "ready") {
  lastPreparedState = kind;
  renderPreparedBadge();
}

function selectedPayload() {
  return {
    character_name: el("characterName").value.trim(),
    text: el("inputText").value.trim(),
    split_sentence: el("splitSentence").checked,
  };
}

function loadCharacterPayload() {
  return {
    character_name: el("characterName").value.trim(),
    onnx_model_dir: el("modelDir").value.trim(),
    language: el("language").value.trim(),
  };
}

function referencePayload() {
  return {
    character_name: el("characterName").value.trim(),
    audio_path: el("referenceAudio").value.trim(),
    audio_text: el("referenceText").value,
    language: el("language").value.trim(),
  };
}

function ensureTextPayload(payload) {
  if (!payload.character_name) {
    throw new Error(t("characterRequired"));
  }
  if (!payload.text) {
    throw new Error(t("inputRequired"));
  }
}

function endpointForMode(mode) {
  const endpoints = config?.endpoints || {};
  if (mode === "wav") {
    return {path: endpoints.complete_wav, filename: "genie-tts-complete.wav", format: t("modeCompleteWav")};
  }
  if (mode === "legado-buffered") {
    return {path: endpoints.legado_buffered, filename: "genie-tts-legado-buffered.wav", format: t("modeLegadoBuffered")};
  }
  if (mode === "legado-stream") {
    return {path: endpoints.legado_stream, filename: "genie-tts-legado-stream.wav", format: t("modeLegadoStream")};
  }
  if (mode === "stream-wav") {
    return {path: endpoints.stream_wav || "/tts/stream.wav", filename: "genie-tts-stream.wav", format: t("modeStreamWav")};
  }
  if (mode === "raw") {
    return {path: endpoints.raw || "/tts/raw", filename: "genie-tts-raw.pcm", format: t("modeRawPcm")};
  }
  return null;
}

function streamUrlForEndpoint(path, payload) {
  const [basePath, queryString = ""] = path.split("?");
  const params = new URLSearchParams(queryString);
  params.set("character_name", payload.character_name);
  params.set("text", payload.text);
  params.set("split_sentence", payload.split_sentence ? "true" : "false");
  return `${basePath}?${params.toString()}`;
}

function canUseGetStream(payload) {
  return payload.text.length <= 1800;
}

function fillDefaults(defaults) {
  const modeSelect = el("runtimeMode");
  modeSelect.innerHTML = "";
  const modes = defaults.runtime_modes || MODES;
  for (const mode of modes) {
    const option = document.createElement("option");
    option.value = mode;
    option.textContent = mode;
    modeSelect.appendChild(option);
  }

  el("characterName").value = defaults.character_name;
  el("modelDir").value = defaults.onnx_model_dir;
  el("language").value = defaults.language;
  el("referenceAudio").value = defaults.reference_audio_path;
  el("referenceText").value = defaults.reference_text;
  el("inputText").value = defaults.input_text;
  el("splitSentence").checked = Boolean(defaults.split_sentence);
  el("unloadSessions").checked = Boolean(defaults.unload_sessions);
  modeSelect.value = modes.includes(defaults.runtime_mode) ? defaults.runtime_mode : modes[0];
  updateTextStats();
}

function renderAccess(access) {
  const lanList = el("lanList");
  clearNode(lanList);
  if (!access) {
    el("apiBase").textContent = "-";
    el("localUrl").textContent = "-";
    el("lanUrl").textContent = "-";
    lanList.classList.add("hidden");
    return;
  }
  const lanUrls = access.lan_urls || [];
  el("apiBase").textContent = access.api_base_url || "-";
  el("localUrl").textContent = access.local_url || "-";
  el("lanUrl").textContent = lanUrls.length ? lanUrls[0] : t("noLanDetected");
  el("copyLanBtn").title = lanUrls.length
    ? `${t("copyLanTitle")}: ${lanUrls.join("  ")}`
    : t("copyLanTitle");

  lanList.classList.toggle("hidden", !lanUrls.length);
  lanUrls.forEach((url, index) => {
    const button = document.createElement("button");
    const label = `${t("lanLabel")} ${index + 1}`;
    button.type = "button";
    button.className = "lan-pill";
    button.title = `${t("copyLanTitle")}: ${url}`;
    const prefix = document.createElement("span");
    prefix.textContent = label;
    const value = document.createElement("strong");
    value.textContent = url;
    button.append(prefix, value);
    button.addEventListener("click", () => withButton(button, () => copyText(url, label)));
    lanList.appendChild(button);
  });
}

function renderRuntime(runtime) {
  lastRuntimeSnapshot = runtime;
  if (!runtime) {
    jsonPreview("runtimeJson", null);
    el("runtimeCurrent").textContent = "-";
    el("selectedProviders").textContent = "-";
    el("availableProviders").textContent = "-";
    el("loadedCharacters").textContent = "-";
    el("sessionProviders").textContent = "-";
    setBadge(el("runtimeBadge"), "-", "muted");
    return;
  }
  jsonPreview("runtimeJson", runtime);
  el("runtimeCurrent").textContent = runtime.runtime_mode || "-";
  setPills(el("selectedProviders"), providerPills(runtime.selected_providers || []));
  setPills(el("availableProviders"), providerPills(runtime.available_providers || [], "muted"));
  setPills(el("loadedCharacters"), (runtime.loaded_characters || []).map((character) => ({
    label: character,
    state: "ok",
  })));

  const loaded = runtime.loaded_models || {};
  const shared = runtime.shared_models || {};
  const lines = [];
  for (const [character, models] of Object.entries(loaded)) {
    lines.push(`[${character}]`);
    for (const [name, providers] of Object.entries(models || {})) {
      lines.push(`  ${name}: ${providerListText(providers)}`);
    }
  }
  if (!lines.length) {
    lines.push("-");
  }
  if (Object.keys(shared).length) {
    lines.push("[shared]");
    for (const [name, providers] of Object.entries(shared)) {
      lines.push(`  ${name}: ${providerListText(providers)}`);
    }
  }
  el("sessionProviders").textContent = lines.join("\n");

  const badge = runtimeBadgeInfo(runtime);
  setBadge(el("runtimeBadge"), badge.label, badge.state);
}

function renderStatus(status) {
  lastStatusSnapshot = status;
  if (!status) {
    jsonPreview("statusJson", null);
    el("busyState").textContent = "-";
    el("activeSession").textContent = "-";
    el("jobState").textContent = "-";
    el("readerState").textContent = "-";
    updateActivityBadge();
    return;
  }
  jsonPreview("statusJson", status);
  setPills(el("busyState"), [{
    label: t(status.busy ? "yes" : "no"),
    state: status.busy ? "warn" : "muted",
  }]);
  setPills(el("activeSession"), [{
    label: t(status.active_tts_session ? "yes" : "no"),
    state: status.active_tts_session ? "warn" : "muted",
  }]);

  const jobs = status.jobs || {};
  const reader = status.reader_requests || {};
  const activeJobs = jobs.active?.length || 0;
  const queued = jobs.queued_count || 0;
  const running = jobs.running_count || 0;
  const recentReaders = reader.recent?.length || 0;
  setPills(el("jobState"), [
    {label: `${t("activeMetric")} ${activeJobs}`, state: activeJobs ? "warn" : "muted"},
    {label: `${t("queuedMetric")} ${queued}`, state: queued ? "warn" : "muted"},
    {label: `${t("runningMetric")} ${running}`, state: running ? "warn" : "muted"},
  ]);
  setPills(el("readerState"), [
    {label: `${t("activeMetric")} ${reader.active_count || 0}`, state: reader.active_count ? "warn" : "muted"},
    {label: `${t("recentMetric")} ${recentReaders}`, state: recentReaders ? "ok" : "muted"},
  ]);

  const active = Boolean(status.busy);
  setBadge(el("activityBadge"), active ? t("activityBusy") : t("activityIdle"), active ? "warn" : "muted");
}

async function refreshHealth() {
  try {
    const health = await apiJson(config.endpoints.health, {method: "GET"});
    if (health.status === "ok") {
      setHealthBadge("ok");
    } else {
      setHealthBadge("warn", health.status || "unknown");
    }
    return health;
  } catch (error) {
    setHealthBadge("error", error.message);
    return null;
  }
}

async function refreshRuntime() {
  const runtime = await apiJson(config.endpoints.runtime, {method: "GET"});
  renderRuntime(runtime);
  return runtime;
}

async function refreshStatus() {
  const status = await apiJson(config.endpoints.status, {method: "GET"});
  renderStatus(status);
  return status;
}

async function refreshAll() {
  if (refreshAllInFlight) {
    return {runtime: lastRuntimeSnapshot, status: lastStatusSnapshot};
  }
  refreshAllInFlight = true;
  try {
    const results = await Promise.allSettled([
      refreshHealth(),
      refreshRuntime(),
      refreshStatus(),
    ]);
    const failures = results.filter((result) => result.status === "rejected");
    if (failures.length) {
      appendLog(t("refreshFailed", {
        message: failures.map((result) => result.reason?.message || String(result.reason)).join("; "),
      }));
    }
    const [health, runtime, status] = results.map((result) => (
      result.status === "fulfilled" ? result.value : null
    ));
    return {health, runtime, status};
  } finally {
    refreshAllInFlight = false;
  }
}

function ensureConfig() {
  if (!config) {
    throw new Error("UI configuration not loaded.");
  }
}

async function applyRuntime() {
  ensureConfig();
  const mode = el("runtimeMode").value;
  const unloadSessions = el("unloadSessions").checked;
  const result = await apiJson(config.endpoints.runtime_configure, {
    method: "POST",
    body: JSON.stringify({mode, unload_sessions: unloadSessions}),
  });
  appendLog(t("runtimeConfigured", {mode}), result);
  if (result.reload_required_for_loaded_sessions) {
    setPreparedBadge("reload");
  } else {
    setPreparedBadge("ready");
  }
  await refreshAll();
}

async function loadCharacter() {
  ensureConfig();
  const payload = loadCharacterPayload();
  if (!payload.character_name || !payload.onnx_model_dir || !payload.language) {
    throw new Error(t("loadFieldsRequired"));
  }
  const result = await apiJson(config.endpoints.load_character, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  appendLog(t("loadSuccess"), result);
  setPreparedBadge("ready");
  await refreshRuntime();
}

async function setReference() {
  ensureConfig();
  const payload = referencePayload();
  if (!payload.character_name || !payload.audio_path || !payload.audio_text || !payload.language) {
    throw new Error(t("referenceFieldsRequired"));
  }
  const result = await apiJson(config.endpoints.set_reference_audio, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  appendLog(t("referenceSuccess"), result);
  setPreparedBadge("ready");
  await refreshRuntime();
}

async function clearReferenceCache() {
  ensureConfig();
  const result = await apiJson(config.endpoints.clear_reference_audio_cache || "/clear_reference_audio_cache", {
    method: "POST",
    body: "{}",
  });
  appendLog(t("cacheCleared"), result);
  setPreparedBadge("ready");
}

async function restoreDefaults() {
  ensureConfig();
  fillDefaults(config.defaults);
  setPreparedBadge("not_loaded");
  setRequestSummary();
  appendLog(t("defaultsRestored"));
}

async function prepareCharacter() {
  await loadCharacter();
  await setReference();
}

async function generateAudio() {
  ensureConfig();
  const mode = el("endpointMode").value;
  if (mode === "job") {
    await submitJob();
    return;
  }

  const payload = selectedPayload();
  ensureTextPayload(payload);
  const endpoint = endpointForMode(mode);
  if (!endpoint) {
    throw new Error(t("unsupportedMode", {mode}));
  }
  clearAudio();
  clearJobView();
  setPreparedBadge("busy");
  appendLog(t("requestStarted", {format: endpoint.format}));
  setRequestBadge("requestStarted", "warn", {format: endpoint.format});
  if (["legado-stream", "stream-wav"].includes(mode) && canUseGetStream(payload)) {
    const streamUrl = streamUrlForEndpoint(endpoint.path, payload);
    setAudioUrl(streamUrl, endpoint.filename);
    setRequestSummary({mode, bytes: "stream", elapsed: "live", format: "audio/wav"});
    setRequestBadge("requestStarted", "warn", {format: endpoint.format});
    el("audioPlayer").play().catch(() => {});
    await refreshStatus();
    return;
  }
  const started = performance.now();
  const result = await apiBlob(endpoint.path, payload);
  const elapsed = ((performance.now() - started) / 1000).toFixed(2);
  const format = result.headers.get("X-Genie-Audio-Format") || result.headers.get("content-type") || "unknown";
  const innerFormat = result.headers.get("X-Genie-Inner-Audio-Format") || "-";
  const responseMode = mode === "raw" ? "raw" : mode;
  if (mode === "raw") {
    setDownloadOnly(result.blob, endpoint.filename);
  } else {
    setAudio(result.blob, endpoint.filename);
  }
  setRequestSummary({mode: responseMode, bytes: result.blob.size, elapsed: `${elapsed}s`, format});
  setRequestBadge("requestReady", "ok", {format: endpoint.format});
  setPreparedBadge("ready");
  appendLog(t("audioReady", {format: endpoint.format, bytes: result.blob.size, elapsed}), {
    status: result.status,
    audio_format: format,
    inner_audio_format: innerFormat,
  });
  await refreshStatus();
  await refreshRuntime();
}

async function submitJob() {
  ensureConfig();
  const payload = selectedPayload();
  ensureTextPayload(payload);
  clearAudio();
  clearJobView();
  el("jobBox").classList.remove("hidden");
  setRequestBadge("activityBusy", "warn");
  const result = await apiJson(config.endpoints.job_submit, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const jobId = result.job_id;
  el("jobId").textContent = jobId;
  updateJobView(result.job || {status: "queued", stage: "queued", message: "Queued for synthesis."});
  setRequestSummary({mode: "job", bytes: "-", elapsed: "-", format: "job"});
  setRequestBadge("jobSubmitted", "warn", {jobId});
  appendLog(t("jobSubmitted", {jobId}), result.job);
  pollJob(jobId);
}

function updateJobView(job) {
  el("jobStatus").textContent = job.status || "-";
  el("jobStage").textContent = job.stage || "-";
  el("jobMessage").textContent = job.message || job.error_detail || "-";
}

function pollJob(jobId) {
  if (activeJobTimer) {
    clearInterval(activeJobTimer);
  }

  const tick = async () => {
    try {
      const job = await apiJson(config.endpoints.job_status.replace("{job_id}", jobId), {method: "GET"});
      updateJobView(job);
      if (job.status === "completed") {
        clearInterval(activeJobTimer);
        activeJobTimer = null;
        const wavPath = config.endpoints.job_wav.replace("{job_id}", jobId);
        setAudioUrl(wavPath, `${jobId}.wav`);
        setRequestSummary({mode: "job", bytes: job.output_bytes || 0, elapsed: formatSeconds(job.elapsed_seconds), format: "audio/wav"});
        setRequestBadge("jobCompleted", "ok", {jobId});
        appendLog(t("jobCompleted", {jobId}), {
          bytes: job.output_bytes || 0,
          wav_url: wavPath,
          output_path: job.output_path,
        });
        await refreshStatus();
        await refreshRuntime();
      } else if (["failed", "cancelled"].includes(job.status)) {
        clearInterval(activeJobTimer);
        activeJobTimer = null;
        setRequestBadge("jobFailed", job.status === "failed" ? "error" : "warn", {status: job.status, jobId});
        appendLog(t("jobFailed", {status: job.status, jobId}), job);
      }
    } catch (error) {
      clearInterval(activeJobTimer);
      activeJobTimer = null;
      setRequestBadge("jobPollingFailed", "error", {message: error.message});
      appendLog(t("jobPollingFailed", {message: error.message}));
    }
  };

  tick();
  activeJobTimer = setInterval(tick, 2000);
}

async function cancelJob() {
  const jobId = el("jobId").textContent.trim();
  if (!jobId || jobId === "-") {
    return;
  }
  const result = await apiJson(config.endpoints.job_cancel.replace("{job_id}", jobId), {method: "POST", body: "{}"});
  appendLog(t("jobCancelRequested", {jobId}), result);
  updateJobView(result);
  setRequestBadge("jobFailed", "warn", {status: result.status || "cancelled", jobId});
  if (["cancelled", "failed", "completed"].includes(result.status) && activeJobTimer) {
    clearInterval(activeJobTimer);
    activeJobTimer = null;
  }
  await refreshStatus();
}

async function stopTts() {
  ensureConfig();
  let result = null;
  try {
    result = await apiJson(config.endpoints.stop || "/stop", {method: "POST", body: "{}"});
  } finally {
    abortActiveTtsRequest();
    if (lastRequestSummary?.elapsed === "live") {
      clearAudio();
    } else {
      el("audioPlayer").pause();
    }
  }
  appendLog(t("stopRequested"), result);
  setRequestBadge("stopRequested", "warn");
  await refreshStatus();
}

async function clearLog() {
  el("logBox").textContent = "";
}

async function copyText(value, label) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
      appendLog(t("copySuccess", {label}));
      return;
    }
  } catch (error) {
    // Fall through to the legacy path for non-secure LAN origins.
  }
  try {
    const textArea = document.createElement("textarea");
    textArea.value = value;
    textArea.setAttribute("readonly", "");
    textArea.style.position = "fixed";
    textArea.style.left = "-9999px";
    document.body.appendChild(textArea);
    textArea.select();
    const copied = document.execCommand("copy");
    document.body.removeChild(textArea);
    if (!copied) {
      throw new Error("clipboard unavailable");
    }
  } catch (error) {
    throw new Error(t("copyFailed", {message: error.message || error}));
  }
  appendLog(t("copySuccess", {label}));
}

function extractLanValue() {
  return config?.access?.lan_urls?.[0] || null;
}

async function copyApiBase() {
  await copyText(el("apiBase").textContent.trim(), t("apiLabel"));
}

async function copyLocalUrl() {
  await copyText(el("localUrl").textContent.trim(), t("localLabel"));
}

async function copyLanUrl() {
  const value = extractLanValue();
  if (!value) {
    throw new Error(t("noLanDetected"));
  }
  await copyText(value, t("lanLabel"));
}

function updateActivityBadge() {
  const busy = Boolean(lastStatusSnapshot?.busy);
  setBadge(el("activityBadge"), busy ? t("activityBusy") : t("activityIdle"), busy ? "warn" : "muted");
}

function scheduleAutoRefresh() {
  if (activeRefreshTimer) {
    clearInterval(activeRefreshTimer);
    activeRefreshTimer = null;
  }
  if (el("autoRefresh").checked) {
    activeRefreshTimer = setInterval(() => {
      withButton(el("refreshAllBtn"), refreshAll);
    }, AUTO_REFRESH_INTERVAL_MS);
  }
}

async function withButton(button, action) {
  button.disabled = true;
  try {
    await action();
  } catch (error) {
    appendLog(error.message || String(error));
    setRequestBadge("requestError", "error", {message: error.message || "error"});
    if (lastPreparedState === "busy") {
      setPreparedBadge("error");
    }
  } finally {
    button.disabled = false;
  }
}

function bindAudioEvents() {
  const player = el("audioPlayer");
  player.addEventListener("playing", () => {
    if (lastRequestSummary?.elapsed === "live") {
      setRequestBadge("requestStarted", "warn", {format: lastRequestSummary.format});
    }
  });
  player.addEventListener("ended", () => {
    if (lastRequestSummary?.elapsed === "live") {
      setRequestBadge("requestReady", "ok", {format: lastRequestSummary.format});
      setPreparedBadge("ready");
      refreshStatus().catch(() => {});
    }
  });
  player.addEventListener("error", () => {
    if (player.currentSrc) {
      setRequestBadge("requestError", "error", {message: "audio playback failed"});
    }
  });
}

async function init() {
  config = await apiJson("/ui/config", {method: "GET"});
  setLanguage(detectInitialLanguage(), false);
  fillDefaults(config.defaults);
  renderAccess(config.access);
  clearAudio();
  clearJobView();
  setRequestSummary();
  setPreparedBadge("not_loaded");

  el("refreshAllBtn").addEventListener("click", () => withButton(el("refreshAllBtn"), refreshAll));
  el("applyRuntimeBtn").addEventListener("click", () => withButton(el("applyRuntimeBtn"), applyRuntime));
  el("loadCharacterBtn").addEventListener("click", () => withButton(el("loadCharacterBtn"), loadCharacter));
  el("setReferenceBtn").addEventListener("click", () => withButton(el("setReferenceBtn"), setReference));
  el("prepareBtn").addEventListener("click", () => withButton(el("prepareBtn"), prepareCharacter));
  el("generateBtn").addEventListener("click", () => withButton(el("generateBtn"), generateAudio));
  el("stopBtn").addEventListener("click", () => withButton(el("stopBtn"), stopTts));
  el("cancelJobBtn").addEventListener("click", () => withButton(el("cancelJobBtn"), cancelJob));
  el("clearCacheBtn").addEventListener("click", () => withButton(el("clearCacheBtn"), clearReferenceCache));
  el("restoreDefaultsBtn").addEventListener("click", () => withButton(el("restoreDefaultsBtn"), restoreDefaults));
  el("clearLogBtn").addEventListener("click", () => withButton(el("clearLogBtn"), clearLog));
  el("languageToggle").addEventListener("click", () => {
    setLanguage(activeLanguage === "en" ? "zh" : "en");
    appendLog(t("languageTitle"));
  });
  el("copyApiBtn").addEventListener("click", () => withButton(el("copyApiBtn"), copyApiBase));
  el("copyLocalBtn").addEventListener("click", () => withButton(el("copyLocalBtn"), copyLocalUrl));
  el("copyLanBtn").addEventListener("click", () => withButton(el("copyLanBtn"), copyLanUrl));
  el("autoRefresh").addEventListener("change", scheduleAutoRefresh);
  el("inputText").addEventListener("input", updateTextStats);
  el("runtimeMode").addEventListener("change", () => {
    setBadge(el("runtimeBadge"), el("runtimeMode").value, "muted");
  });
  bindAudioEvents();

  appendLog(t("initLoaded"));
  await refreshAll();
  scheduleAutoRefresh();
}

init().catch((error) => {
  appendLog(t("initFailed", {message: error.message || error}));
  setBadge(el("healthBadge"), t("healthError"), "error");
});
