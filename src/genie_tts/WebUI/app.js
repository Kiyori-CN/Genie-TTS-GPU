const el = (id) => document.getElementById(id);

const STORAGE_KEY = "genie-webui-language";
const AUTO_REFRESH_INTERVAL_MS = 5000;
const MODES = ["cuda", "cpu", "auto"];
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
    navRuntime: "运行时",
    navSynthesis: "合成",
    navOutput: "输出",
    navConversion: "转换",
    navReader: "阅读",
    navEndpoints: "端点",
    navActivity: "活动",
    runtimeTitle: "运行时",
    runtimeModeLabel: "运行模式",
    applyRuntime: "应用",
    listenModuleTitle: "监听",
    listenHostLabel: "监听 IP",
    listenPortLabel: "端口",
    applyListen: "应用监听",
    listenCurrentLabel: "当前",
    listenReachLabel: "可达",
    listenLocalOnly: "仅本机",
    listenLanReady: "局域网可用",
    listenRestartSupported: "支持重启",
    listenManualRestart: "需手动重启",
    listenAllInterfaces: "全部网卡",
    listenLocalOnlyOption: "仅本机",
    listenSpecificLan: "指定局域网 IP",
    autoPort: "自动",
    listenRestarting: "服务正在重启到 {host}:{port}",
    listenUnchanged: "监听未变化：{host}:{port}",
    listenRestartFailed: "监听切换失败：{message}",
    listenBusy: "服务忙碌时不能重启监听。",
    modeLabel: "模式",
    selectedLabel: "已选提供方",
    availableLabel: "可用提供方",
    loadedLabel: "已加载角色",
    sessionProvidersTitle: "会话提供方",
    memoryModuleTitle: "资源监控",
    memoryCpuLabel: "CPU",
    memoryRamLabel: "内存",
    memoryProcessLabel: "进程",
    memoryGpuLabel: "GPU",
    memoryVramLabel: "显存",
    memoryPolicyLabel: "策略",
    memoryParallelLabel: "并行",
    memoryCacheLabel: "缓存",
    memoryProcessCpuLabel: "进程 CPU",
    memorySystemCpuLabel: "系统 CPU",
    memoryGpuUtilLabel: "GPU 利用率",
    memoryModelsUnit: "模型",
    memoryRefsUnit: "参考",
    refreshMemory: "刷新资源",
    releaseSessions: "释放会话",
    clearMemoryCache: "清参考缓存",
    memoryUnavailable: "未采样",
    memoryReleaseDone: "已释放空闲模型会话",
    memoryCacheCleared: "已清理参考缓存",
    memoryActionFailed: "内存动作失败：{message}",
    memoryBusy: "服务忙碌，不能释放会话",
    memoryNoteVram: "CUDA 显存由驱动和 ONNX Runtime 管理；这里可以释放会话、清缓存和调节作业线程数，但不能把系统内存变成显存。",
    jobOnlyParallel: "仅长文本作业",
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
    presetSelectLabel: "角色预设",
    applyPreset: "套用预设",
    savePreset: "保存当前",
    deletePreset: "删除手动",
    refreshPresets: "重新扫描",
    presetAuto: "自动识别",
    presetManual: "手动",
    presetHintAuto: "自动识别：{name}。可套用，不能删除；路径仍可手动编辑后另存为手动预设。",
    presetHintManual: "手动预设：{name}。可套用、覆盖保存或删除；路径输入框支持自定义文件路径。",
    presetHintNone: "请选择预设，或直接编辑角色名和路径后保存为手动预设。",
    presetAutoCannotDelete: "自动识别预设不能删除。",
    presetSaved: "已保存预设：{name}",
    presetDeleted: "已删除预设：{name}",
    presetApplied: "已切换角色预设：{name}",
    presetCount: "{count} 个预设",
    referenceOptionCount: "{count} 个参考",
    noReferenceOptions: "没有参考音频",
    voiceModuleTitle: "角色与参考",
    textModuleTitle: "文本输入",
    endpointModuleTitle: "合成路径",
    inputTextLabel: "输入文本",
    textFileTitle: "TXT 文件",
    textFilePickerLabel: "选择 .txt 文件",
    clearTextFile: "清除文件",
    splitSentenceLabel: "智能分句",
    parallelEnabledLabel: "并行推理",
    parallelToggleTitle: "仅长文本作业且 CUDA 可用时启用真实 GPU 分段并行",
    parallelWorkersLabel: "线程数",
    parallelWorkersPlaceholder: "auto 或数字",
    parallelCapabilityLabel: "执行能力",
    parallelCapabilitySerial: "单会话串行",
    parallelCapabilityGpu: "GPU 分段并行",
    parallelCapabilityUnavailable: "真实并行未启用",
    endpointModeLabel: "端点",
    endpointGroupRecommended: "推荐",
    endpointGroupLowLatency: "低延迟 / 开发",
    endpointGroupLongText: "长文本",
    modeCompleteWav: "快速试听 - /tts/wav",
    modeLegadoBuffered: "听书稳定 - 缓冲",
    modeLegadoStream: "听书低延迟 - 流式",
    modeStreamWav: "通用流式 - WAV 文件",
    modeRawPcm: "开发调试 - 原始 PCM",
    modeJob: "长文本作业 - 有序文件",
    endpointHintWav: "普通浏览器试听和短文本输出，合成结束后得到完整 WAV。",
    endpointHintLegadoBuffered: "推荐给阅读/听书；等待合成完成后返回完整 WAV，兼容性最好。",
    endpointHintLegadoStream: "低延迟听书实验；部分 Android 播放栈可能不稳定。",
    endpointHintStreamWav: "通用分块 WAV 流，适合自定义播放器实验。",
    endpointHintRaw: "开发用 PCM S16LE，不是 WAV，浏览器不能直接播放。",
    endpointHintJob: "长文本后台生成，支持轮询、取消和下载完整 WAV；并行设置只在这里有意义。",
    loadCharacter: "加载",
    setReference: "参考",
    prepare: "加载 + 参考",
    clearCache: "清缓存",
    restoreDefaults: "恢复默认",
    generate: "生成",
    outputTitle: "输出",
    requestIdle: "空闲",
    rawPcmTitle: "原始 PCM",
    rawPcmDesc: "pcm_s16le，32000 Hz，单声道",
    streamWavTitle: "流式 WAV",
    streamWavDesc: "分块 audio/wav",
    bufferedWavTitle: "缓冲 WAV",
    bufferedWavDesc: "合成结束后返回完整文件",
    jobWavTitle: "作业 WAV",
    jobWavDesc: "队列作业输出文件",
    downloadOutput: "下载输出",
    responseModeLabel: "模式",
    responseBytesLabel: "字节",
    responseElapsedLabel: "耗时",
    responseFormatLabel: "格式",
    jobTitle: "作业",
    cancelJob: "取消",
    clearJob: "清除",
    jobIdLabel: "作业 id",
    jobStatusLabel: "状态",
    jobStageLabel: "阶段",
    jobMessageLabel: "消息",
    progressTitle: "进度",
    progressStageLabel: "阶段",
    progressMessageLabel: "消息",
    progressSegmentsLabel: "分段",
    progressCharsLabel: "字符",
    progressElapsedLabel: "已用",
    progressEtaLabel: "预计剩余",
    progressBytesLabel: "音频",
    progressModeLabel: "端点",
    progressParallelLabel: "并行",
    logTitle: "日志",
    clearLogTitle: "清空日志",
    runtimeJsonTitle: "运行时 JSON",
    statusJsonTitle: "状态 JSON",
    characterRequired: "角色名是必填项。",
    inputRequired: "输入文本是必填项。",
    loadFieldsRequired: "角色名、模型目录和语言是必填项。",
    referenceFieldsRequired: "角色名、参考音频、参考文本和语言是必填项。",
    characterNotLoadedHelp: "角色未加载。请先点击“加载 + 参考”。",
    referenceNotSetHelp: "参考音频未设置。请先点击“加载 + 参考”或“参考”。",
    unsupportedMode: "不支持的端点模式：{mode}",
    runtimeConfigured: "运行模式已应用：{mode}",
    runtimeApplied: "运行模式已应用",
    loadSuccess: "角色已加载",
    referenceSuccess: "参考音频已设置",
    preparedReady: "就绪",
    preparedModelLoaded: "待参考",
    preparedReload: "需要重载角色",
    preparedError: "准备失败",
    requestStarted: "开始请求：{format}",
    requestReady: "{format} 已就绪",
    requestError: "错误：{message}",
    audioReady: "音频已就绪：{format}，{bytes} 字节，{elapsed}s",
    jobSubmitted: "已提交作业：{jobId}",
    jobCompleted: "作业已完成：{jobId}",
    jobFailed: "作业 {status}：{jobId}",
    jobCancelRequested: "已请求取消作业：{jobId}",
    jobPollingFailed: "作业轮询失败：{message}",
    jobAlreadyActive: "WebUI 正在跟踪一个作业，请先等待完成或取消当前作业。",
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
    parallelOff: "关闭",
    parallelRequested: "请求 {workers} 个线程",
    parallelEffective: "生效 {workers} 个线程",
    parallelRejected: "不提交未实现的并行请求",
    parallelInvalidWorkers: "线程数必须是 auto 或大于 1 的整数。",
    serialFallback: "串行回退",
    singleSessionSerial: "单会话串行",
    gpuSegmentParallel: "GPU 分段并行",
    etaPending: "估算中",
    stageQueued: "排队中",
    stageWaiting: "等待会话锁",
    stageSynthesizing: "合成中",
    stageParallelSynthesizing: "GPU 分段并行合成中",
    stageWritingWav: "写入 WAV",
    stageCompleted: "完成",
    stageCancelled: "已取消",
    stageFailed: "失败",
    progressQueuedMessage: "已进入队列，等待开始合成。",
    progressWaitingMessage: "正在等待 TTS 会话锁。",
    progressSynthesizingMessage: "正在合成音频。",
    progressParallelStartMessage: "GPU 分段并行已启动，线程数：{workers}。",
    progressParallelDoneMessage: "已完成 {done}/{total} 个并行分段。",
    progressWritingMessage: "正在写入 WAV 输出。",
    progressCompletedMessage: "作业已完成。",
    progressParallelCompletedMessage: "并行作业已完成。",
    progressCancelledMessage: "作业已取消。",
    progressFailedMessage: "作业失败。",
    audioCleared: "音频已清除",
    playbackFailed: "音频播放失败",
    copySuccess: "已复制：{label}",
    copyFailed: "复制失败：{message}",
    cacheCleared: "参考音频缓存已清除",
    defaultsRestored: "默认值已恢复",
    readerSettingsTitle: "阅读 / Legado",
    readerRecommended: "推荐缓冲模式",
    readerApiBaseLabel: "API 基址",
    readerLanBaseLabel: "LAN 基址",
    readerBufferedLabel: "缓冲 URL",
    readerStreamLabel: "流式 URL",
    readerCharacterLabel: "默认角色",
    readerSplitLabel: "分句",
    readerTimeoutLabel: "等待超时",
    readerModeLabel: "推荐模式",
    readerJsLibLabel: "推荐 jsLib",
    readerJsonLabel: "可导入 JSON",
    copyApiBase: "复制 API",
    copyLanBase: "复制 LAN",
    copyBufferedUrl: "复制缓冲 URL",
    copyStreamUrl: "复制流式 URL",
    copyJsLib: "复制 jsLib",
    copyJsonTemplate: "复制 JSON",
    copyField: "复制",
    copiedShort: "已复制",
    unavailable: "不可用",
    endpointCatalogTitle: "端点",
    endpointCount: "{count} 个端点",
    endpointResponseLabel: "返回",
    endpointUseCaseLabel: "场景",
    parallelUnavailable: "当前后端只有单活跃会话；WebUI 不提交未实现的并行请求",
    activityPanelTitle: "活动",
    activityDirectTitle: "直接",
    activityStreamTitle: "流式",
    activityJobTitle: "作业",
    activityReaderTitle: "阅读",
    activitySummary: "已记录 {count} 条 · {active} 活动中",
    activityEmpty: "暂无记录",
    readerExternalRequest: "{character} · {chars} 字符",
    fileLoaded: "已加载文件：{name}",
    fileCleared: "已清除文件选择",
    fileLoadFailed: "文件读取失败：{message}",
    runtimeModeCuda: "CUDA",
    runtimeModeCpu: "CPU",
    runtimeModeAuto: "自动",
    languageChinese: "中文",
    languageEnglish: "英文",
    languageJapanese: "日文",
    languageHybridChineseEnglish: "中英混合",
    languageKorean: "韩文",
    readerModeBuffered: "缓冲模式",
    readerModeStream: "流式模式",
    conversionTitle: "模型转换",
    conversionIdle: "未扫描",
    conversionInputTitle: "GPT-SoVITS 文件夹",
    conversionFoldersLabel: "源文件夹路径",
    conversionFoldersPlaceholder: "每行一个本机文件夹路径，文件夹内需要同时包含 .ckpt 和 .pth",
    conversionOutputRootLabel: "输出根目录",
    conversionOverwriteLabel: "覆盖已有输出",
    conversionOverwriteTitle: "仅覆盖本次转换生成的目标 tts_models 目录",
    scanConversion: "扫描",
    startConversion: "开始转换",
    refreshConversion: "刷新任务",
    conversionValidLabel: "有效",
    conversionJobLabel: "任务",
    conversionProgressLabel: "进度",
    conversionLogTitle: "转换日志",
    conversionNoFolders: "请先输入至少一个本机文件夹路径。",
    conversionScanDone: "扫描完成：{valid}/{total} 个可转换。",
    conversionSubmitted: "转换任务已提交：{jobId}",
    conversionCompleted: "转换完成：{done}/{total}",
    conversionFailed: "转换失败：{message}",
    conversionQueued: "等待转换",
    conversionRunning: "转换中",
    conversionReady: "可转换",
    conversionInvalid: "不可转换",
    conversionOutputHint: "转换后点击“重新扫描”即可自动识别新角色。",
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
    navRuntime: "Runtime",
    navSynthesis: "Synthesis",
    navOutput: "Output",
    navConversion: "Convert",
    navReader: "Reader",
    navEndpoints: "Endpoints",
    navActivity: "Activity",
    runtimeTitle: "Runtime",
    runtimeModeLabel: "Runtime mode",
    applyRuntime: "Apply",
    listenModuleTitle: "Listener",
    listenHostLabel: "Listen IP",
    listenPortLabel: "Port",
    applyListen: "Apply listener",
    listenCurrentLabel: "Current",
    listenReachLabel: "Reach",
    listenLocalOnly: "local only",
    listenLanReady: "LAN ready",
    listenRestartSupported: "restart",
    listenManualRestart: "manual",
    listenAllInterfaces: "all interfaces",
    listenLocalOnlyOption: "local only",
    listenSpecificLan: "specific LAN IP",
    autoPort: "auto",
    listenRestarting: "Restarting service on {host}:{port}",
    listenUnchanged: "Listener unchanged: {host}:{port}",
    listenRestartFailed: "Listener switch failed: {message}",
    listenBusy: "Cannot restart listener while the service is busy.",
    modeLabel: "Mode",
    selectedLabel: "Selected provider",
    availableLabel: "Available provider",
    loadedLabel: "Loaded characters",
    sessionProvidersTitle: "Session providers",
    memoryModuleTitle: "Resource monitor",
    memoryCpuLabel: "CPU",
    memoryRamLabel: "RAM",
    memoryProcessLabel: "Process",
    memoryGpuLabel: "GPU",
    memoryVramLabel: "VRAM",
    memoryPolicyLabel: "Policy",
    memoryParallelLabel: "Parallel",
    memoryCacheLabel: "Cache",
    memoryProcessCpuLabel: "Process CPU",
    memorySystemCpuLabel: "System CPU",
    memoryGpuUtilLabel: "GPU util",
    memoryModelsUnit: "models",
    memoryRefsUnit: "refs",
    refreshMemory: "Refresh memory",
    releaseSessions: "Release sessions",
    clearMemoryCache: "Clear ref cache",
    memoryUnavailable: "not sampled",
    memoryReleaseDone: "Released idle model sessions",
    memoryCacheCleared: "Reference cache cleared",
    memoryActionFailed: "Memory action failed: {message}",
    memoryBusy: "Service is busy; cannot release sessions",
    memoryNoteVram: "CUDA VRAM is managed by the driver and ONNX Runtime. This panel can release sessions, clear cache, and tune workers; it cannot turn system RAM into VRAM.",
    jobOnlyParallel: "real parallel belongs to jobs only",
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
    presetSelectLabel: "Voice preset",
    applyPreset: "Apply preset",
    savePreset: "Save current",
    deletePreset: "Delete user",
    refreshPresets: "Rescan",
    presetAuto: "auto",
    presetManual: "user",
    presetHintAuto: "Auto-discovered: {name}. It can be applied but not deleted; edit paths and save as a user preset when needed.",
    presetHintManual: "User preset: {name}. It can be applied, overwritten, or deleted; path fields support custom file paths.",
    presetHintNone: "Choose a preset, or edit the character and paths directly before saving a user preset.",
    presetAutoCannotDelete: "Auto-discovered presets cannot be deleted.",
    presetSaved: "Preset saved: {name}",
    presetDeleted: "Preset deleted: {name}",
    presetApplied: "Character preset applied: {name}",
    presetCount: "{count} presets",
    referenceOptionCount: "{count} references",
    noReferenceOptions: "No reference audio",
    voiceModuleTitle: "Voice and reference",
    textModuleTitle: "Text input",
    endpointModuleTitle: "Synthesis route",
    inputTextLabel: "Input text",
    textFileTitle: "TXT file",
    textFilePickerLabel: "Choose .txt file",
    clearTextFile: "Clear file",
    splitSentenceLabel: "Smart sentence split",
    parallelEnabledLabel: "Parallel inference",
    parallelToggleTitle: "Enable real GPU segment parallelism only for long-text jobs when CUDA is available",
    parallelWorkersLabel: "Workers",
    parallelWorkersPlaceholder: "auto or number",
    parallelCapabilityLabel: "Execution",
    parallelCapabilitySerial: "single-session serial",
    parallelCapabilityGpu: "GPU segment parallel",
    parallelCapabilityUnavailable: "real parallel disabled",
    endpointModeLabel: "Endpoint",
    endpointGroupRecommended: "Recommended",
    endpointGroupLowLatency: "Low latency / developer",
    endpointGroupLongText: "Long text",
    modeCompleteWav: "Quick listen - /tts/wav",
    modeLegadoBuffered: "Reader stable - buffered",
    modeLegadoStream: "Reader low latency - stream",
    modeStreamWav: "Generic stream - WAV",
    modeRawPcm: "Developer raw - PCM",
    modeJob: "Long text job - ordered file",
    endpointHintWav: "Best for browser preview and short text. Returns a complete WAV after synthesis.",
    endpointHintLegadoBuffered: "Recommended for reader/audiobook use. Waits for synthesis and returns a compatible complete WAV.",
    endpointHintLegadoStream: "Low-latency reader experiment. Some Android media stacks may be unstable.",
    endpointHintStreamWav: "Generic chunked WAV stream for custom player experiments.",
    endpointHintRaw: "Developer PCM S16LE. This is not WAV and is not directly playable in the browser.",
    endpointHintJob: "Background long-text generation with polling, cancellation, and completed WAV download. Parallel settings only belong here.",
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
    clearJob: "Clear",
    jobIdLabel: "Job id",
    jobStatusLabel: "Status",
    jobStageLabel: "Stage",
    jobMessageLabel: "Message",
    progressTitle: "Progress",
    progressStageLabel: "Stage",
    progressMessageLabel: "Message",
    progressSegmentsLabel: "Segments",
    progressCharsLabel: "Chars",
    progressElapsedLabel: "Elapsed",
    progressEtaLabel: "ETA",
    progressBytesLabel: "Audio",
    progressModeLabel: "Endpoint",
    progressParallelLabel: "Parallel",
    logTitle: "Log",
    clearLogTitle: "Clear log",
    runtimeJsonTitle: "Runtime JSON",
    statusJsonTitle: "Status JSON",
    characterRequired: "Character name is required.",
    inputRequired: "Input text is required.",
    loadFieldsRequired: "Character name, model directory, and language are required.",
    referenceFieldsRequired: "Character, reference audio, reference text, and language are required.",
    characterNotLoadedHelp: "Character model is not loaded. Use Load + reference first.",
    referenceNotSetHelp: "Reference audio is not set. Use Load + reference or Reference first.",
    unsupportedMode: "Unsupported endpoint mode: {mode}",
    runtimeConfigured: "Runtime configured: {mode}",
    runtimeApplied: "Runtime applied",
    loadSuccess: "Character loaded",
    referenceSuccess: "Reference audio set",
    preparedReady: "Ready",
    preparedModelLoaded: "Need reference",
    preparedReload: "Reload character",
    preparedError: "Setup failed",
    requestStarted: "Request started: {format}",
    requestReady: "{format} ready",
    requestError: "Error: {message}",
    audioReady: "Audio ready: {format}, {bytes} bytes, {elapsed}s",
    jobSubmitted: "Job submitted: {jobId}",
    jobCompleted: "Job completed: {jobId}",
    jobFailed: "Job {status}: {jobId}",
    jobCancelRequested: "Job cancel requested: {jobId}",
    jobPollingFailed: "Job polling failed: {message}",
    jobAlreadyActive: "The WebUI is already tracking a job. Wait for it or cancel it first.",
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
    parallelOff: "off",
    parallelRequested: "requested {workers} workers",
    parallelEffective: "active {workers} workers",
    parallelRejected: "not sending unavailable parallel request",
    parallelInvalidWorkers: "Workers must be auto or an integer greater than 1.",
    serialFallback: "serial fallback",
    singleSessionSerial: "single-session serial",
    gpuSegmentParallel: "GPU segment parallel",
    etaPending: "estimating",
    stageQueued: "queued",
    stageWaiting: "waiting for session",
    stageSynthesizing: "synthesizing",
    stageParallelSynthesizing: "GPU segment parallel",
    stageWritingWav: "writing WAV",
    stageCompleted: "completed",
    stageCancelled: "cancelled",
    stageFailed: "failed",
    progressQueuedMessage: "Queued for synthesis.",
    progressWaitingMessage: "Waiting for the TTS session lock.",
    progressSynthesizingMessage: "Synthesizing audio.",
    progressParallelStartMessage: "GPU parallel synthesis started with {workers} workers.",
    progressParallelDoneMessage: "Completed {done}/{total} parallel segments.",
    progressWritingMessage: "Writing WAV output.",
    progressCompletedMessage: "Job completed successfully.",
    progressParallelCompletedMessage: "Parallel job completed successfully.",
    progressCancelledMessage: "Job cancelled.",
    progressFailedMessage: "Job failed.",
    audioCleared: "audio cleared",
    playbackFailed: "audio playback failed",
    copySuccess: "Copied: {label}",
    copyFailed: "Copy failed: {message}",
    cacheCleared: "Reference audio cache cleared",
    defaultsRestored: "Defaults restored",
    readerSettingsTitle: "Reader / Legado",
    readerRecommended: "buffered recommended",
    readerApiBaseLabel: "API base",
    readerLanBaseLabel: "LAN base",
    readerBufferedLabel: "Buffered URL",
    readerStreamLabel: "Stream URL",
    readerCharacterLabel: "Default character",
    readerSplitLabel: "Split",
    readerTimeoutLabel: "Wait timeout",
    readerModeLabel: "Recommended mode",
    readerJsLibLabel: "Recommended jsLib",
    readerJsonLabel: "Import JSON",
    copyApiBase: "Copy API",
    copyLanBase: "Copy LAN",
    copyBufferedUrl: "Copy buffered",
    copyStreamUrl: "Copy stream",
    copyJsLib: "Copy jsLib",
    copyJsonTemplate: "Copy JSON",
    copyField: "Copy",
    copiedShort: "Copied",
    unavailable: "Unavailable",
    endpointCatalogTitle: "Endpoints",
    endpointCount: "{count} endpoints",
    endpointResponseLabel: "Returns",
    endpointUseCaseLabel: "Use",
    parallelUnavailable: "The current backend has one active session; the WebUI does not send unavailable parallel requests",
    activityPanelTitle: "Activity",
    activityDirectTitle: "Direct",
    activityStreamTitle: "Stream",
    activityJobTitle: "Job",
    activityReaderTitle: "Reader",
    activitySummary: "Recorded {count} · {active} active",
    activityEmpty: "No entries yet",
    readerExternalRequest: "{character} · {chars} chars",
    fileLoaded: "Loaded file: {name}",
    fileCleared: "Cleared file selection",
    fileLoadFailed: "File read failed: {message}",
    conversionTitle: "Model converter",
    conversionIdle: "not scanned",
    conversionInputTitle: "GPT-SoVITS folders",
    conversionFoldersLabel: "Source folder paths",
    conversionFoldersPlaceholder: "One local folder path per line. Each folder must contain one .ckpt and one .pth file.",
    conversionOutputRootLabel: "Output root",
    conversionOverwriteLabel: "Overwrite output",
    conversionOverwriteTitle: "Only overwrite the target tts_models directories generated by this conversion",
    scanConversion: "Scan",
    startConversion: "Start conversion",
    refreshConversion: "Refresh job",
    conversionValidLabel: "Valid",
    conversionJobLabel: "Job",
    conversionProgressLabel: "Progress",
    conversionLogTitle: "Conversion log",
    conversionNoFolders: "Enter at least one local folder path first.",
    conversionScanDone: "Scan finished: {valid}/{total} convertible.",
    conversionSubmitted: "Conversion job submitted: {jobId}",
    conversionCompleted: "Conversion completed: {done}/{total}",
    conversionFailed: "Conversion failed: {message}",
    conversionQueued: "queued",
    conversionRunning: "running",
    conversionReady: "convertible",
    conversionInvalid: "invalid",
    conversionOutputHint: "After conversion, click Rescan to auto-discover the new character.",
  },
};

let config = null;
let activeAudioUrl = null;
let activeJobTimer = null;
let activeConversionTimer = null;
let activeRefreshTimer = null;
let activeProgressTimer = null;
let activeAudioActivity = null;
let activeJobActivity = null;
let activeLanguage = "zh";
let activeTtsController = null;
let refreshAllInFlight = false;
let lastRuntimeSnapshot = null;
let lastStatusSnapshot = null;
let lastMemorySnapshot = null;
let lastRequestSummary = null;
let lastConversionScan = null;
let lastConversionJob = null;
let lastProgressContext = null;
let lastTextFile = null;
let selectedReferenceName = "";
let listenDirty = false;
let activeSynthesisInFlight = false;
let activeJobInFlight = false;
let lastHealthState = {kind: "pending", detail: null};
let lastPreparedState = "not_loaded";
let lastRequestBadge = {key: "requestIdle", state: "muted", values: {}};
const ACTIVITY_CATEGORIES = ["direct", "stream", "job", "reader"];
const ACTIVITY_LIMIT = 8;
let activitySequence = 0;
let activityJournal = {
  direct: [],
  stream: [],
  job: [],
  reader: [],
};
let activityIndex = new Map();

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
  document.querySelectorAll("[data-i18n-label]").forEach((node) => {
    const key = node.getAttribute("data-i18n-label");
    if (!key) return;
    node.setAttribute("label", t(key));
  });
}

function renderDynamicState() {
  el("languageToggle").textContent = t("languageButton");
  el("languageToggle").title = t("languageTitle");
  refreshDynamicSelectLabels();
  renderAccess(config?.access || null);
  renderHealthBadge();
  renderPreparedBadge();
  renderRequestBadge();
  renderRequestSummary();
  renderListenConfig(config?.listen || null);
  renderReaderConfig(readerConfigForCurrentSelection());
  renderEndpointCatalog(config?.endpoint_catalog || []);
  renderConversionScan(lastConversionScan);
  renderConversionJob(lastConversionJob);
  renderRuntime(lastRuntimeSnapshot);
  renderMemoryPolicy(lastMemorySnapshot || config?.memory_policy || null);
  renderStatus(lastStatusSnapshot);
  updateTextStats();
  updateProgressView(lastProgressContext?.progress || null, lastProgressContext);
  renderActivityJournal();
  updateModeControls();
}

function refreshDynamicSelectLabels() {
  const runtimeSelect = el("runtimeMode");
  if (runtimeSelect) {
    Array.from(runtimeSelect.options || []).forEach((option) => {
      option.textContent = runtimeModeLabel(option.value);
      option.title = option.value;
    });
  }
  const languageSelect = el("language");
  if (languageSelect) {
    Array.from(languageSelect.options || []).forEach((option) => {
      option.textContent = languageDisplayLabel(option.value);
      option.title = option.value;
    });
  }
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
    setBadge(el("preparedBadge"), t("preparedError"), "error");
  } else if (lastPreparedState === "model_loaded") {
    setBadge(el("preparedBadge"), t("preparedModelLoaded"), "warn");
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

function setText(id, value) {
  const node = el(id);
  if (node) {
    node.textContent = value || "-";
  }
}

function setTextFileMeta(value) {
  lastTextFile = value || null;
  const meta = el("textFileMeta");
  if (!meta) return;
  if (!value) {
    meta.textContent = "-";
    return;
  }
  const sizeText = Number.isFinite(Number(value.size)) ? formatBytes(Number(value.size)) : "-";
  meta.textContent = `${value.name || "-"} · ${sizeText}`;
}

function clearTextFileSelection(silent = false) {
  const input = el("textFileInput");
  if (input) {
    input.value = "";
  }
  setTextFileMeta(null);
  if (!silent) {
    appendLog(t("fileCleared"));
  }
}

async function loadTextFileFromInput(file) {
  if (!file) {
    clearTextFileSelection(true);
    return;
  }
  const name = String(file.name || "");
  if (!name.toLowerCase().endsWith(".txt") && file.type !== "text/plain") {
    throw new Error(t("unavailable"));
  }
  const content = await file.text();
  el("inputText").value = content;
  updateTextStats();
  setTextFileMeta({name: file.name, size: file.size});
  appendLog(t("fileLoaded", {name: file.name}), {name: file.name, size: file.size, chars: content.length});
}

function textFileLoadFromEvent(event) {
  const file = event?.target?.files?.[0] || null;
  if (!file) {
    clearTextFileSelection();
    return;
  }
  loadTextFileFromInput(file).catch((error) => {
    appendLog(t("fileLoadFailed", {message: error.message || error}));
  });
}

function copyReaderField(fieldKey, button = null) {
  const labelMap = {
    name: "name",
    url: "url",
    contentType: "Content-Type",
    concurrentRate: "concurrentRate",
  };
  const value = readerConfigForCurrentSelection()?.templates?.recommended_json?.[fieldKey];
  return copyText(value, labelMap[fieldKey] || fieldKey, button);
}

function clearActivityJournal() {
  activitySequence = 0;
  activityIndex = new Map();
  activityJournal = {
    direct: [],
    stream: [],
    job: [],
    reader: [],
  };
  renderActivityJournal();
}

function activityCategoryLabel(category) {
  const labels = {
    direct: t("activityDirectTitle"),
    stream: t("activityStreamTitle"),
    job: t("activityJobTitle"),
    reader: t("activityReaderTitle"),
  };
  return labels[category] || category;
}

function classifyActivity(endpoint = "", mode = "") {
  const value = String(endpoint || mode || "").toLowerCase();
  if (value.includes("legado") || value.includes("stream") || value.includes("reader")) {
    return value.includes("job") ? "job" : (value.includes("stream") ? "stream" : "reader");
  }
  if (value.includes("/jobs/")) {
    return "job";
  }
  if (value.includes("job")) {
    return "job";
  }
  return "direct";
}

function activityCategoryForMode(mode = "", endpoint = "") {
  if (mode === "job" || String(endpoint).includes("/jobs")) return "job";
  if (mode === "legado-buffered") return "reader";
  if (mode === "legado-stream" || mode === "stream-wav") return "stream";
  return classifyActivity(endpoint, mode);
}

function normalizeActivityPill(state) {
  if (["ok", "warn", "error"].includes(state)) {
    return state;
  }
  return "muted";
}

function formatActivityTime(stamp = null) {
  if (!stamp) return nowStamp();
  if (typeof stamp === "string" && stamp.length >= 8) {
    return stamp.slice(11, 19);
  }
  return nowStamp();
}

function formatActivityElapsed(seconds) {
  const value = Number(seconds);
  return Number.isFinite(value) ? formatSeconds(value) : "-";
}

function activityMetaPills(entry) {
  const pills = [];
  if (entry.status) {
    pills.push({label: String(entry.status).toUpperCase(), state: normalizeActivityPill(entry.status_state || entry.status_pill_state || "muted")});
  }
  if (entry.mode) {
    pills.push({label: String(entry.mode), state: "muted"});
  }
  if (entry.elapsed_seconds != null) {
    pills.push({label: formatActivityElapsed(entry.elapsed_seconds), state: "muted"});
  }
  if (entry.bytes != null) {
    pills.push({label: formatBytes(Number(entry.bytes) || 0), state: "muted"});
  }
  if (entry.progress) {
    const progress = entry.progress;
    if (Number.isFinite(Number(progress.percent))) {
      pills.push({label: formatPercent(progress.percent), state: progress.stage === "failed" ? "error" : (Number(progress.percent) >= 100 ? "ok" : "warn")});
    }
    if (Number.isFinite(Number(progress.completed_segments)) || Number.isFinite(Number(progress.total_segments))) {
      pills.push({label: `${progress.completed_segments || 0}/${progress.total_segments || 0}`, state: "muted"});
    }
    if (Number.isFinite(Number(progress.estimated_remaining_seconds))) {
      pills.push({label: `ETA ${formatEta(progress.estimated_remaining_seconds)}`, state: "muted"});
    }
  }
  if (entry.parallel) {
    pills.push({label: parallelText(entry.parallel), state: entry.parallel.effective ? "ok" : "warn"});
  }
  if (entry.error) {
    pills.push({label: t("healthError"), state: "error", title: entry.error});
  }
  return pills;
}

function renderActivityEntry(entry) {
  const item = document.createElement("article");
  item.className = "activity-item";
  const head = document.createElement("div");
  head.className = "activity-item-head";
  const title = document.createElement("div");
  title.className = "activity-item-title";
  title.textContent = entry.title || entry.endpoint || entry.mode || entry.category || "-";
  const time = document.createElement("span");
  time.className = "activity-item-time";
  time.textContent = formatActivityTime(entry.timestamp);
  head.append(title, time);
  item.appendChild(head);

  const body = document.createElement("div");
  body.className = "activity-item-body";
  body.textContent = entry.progress
    ? localizedProgressMessage(entry.progress, entry.message || entry.detail || entry.endpoint)
    : (entry.message || entry.detail || entry.endpoint || "-");
  item.appendChild(body);

  const meta = document.createElement("div");
  meta.className = "activity-item-meta";
  const pills = activityMetaPills(entry);
  if (pills.length) {
    for (const pillSpec of pills) {
      const pill = document.createElement("span");
      pill.className = `pill ${pillSpec.state || "muted"}`;
      pill.textContent = pillSpec.label;
      if (pillSpec.title) {
        pill.title = pillSpec.title;
      }
      meta.appendChild(pill);
    }
    item.appendChild(meta);
  }
  return item;
}

function renderActivityCategory(category, nodeId) {
  const list = el(nodeId);
  const entries = activityJournal[category] || [];
  clearNode(list);
  const active = entries.some((entry) => entry.state === "running" || entry.state === "pending");
  setBadge(el(`${category}ActivityBadge`), `${entries.length}`, active ? "warn" : "muted");
  if (!entries.length) {
    const empty = document.createElement("div");
    empty.className = "activity-item";
    empty.textContent = t("activityEmpty");
    list.appendChild(empty);
    return;
  }
  for (const entry of entries) {
    list.appendChild(renderActivityEntry(entry));
  }
}

function renderActivityJournal() {
  const total = ACTIVITY_CATEGORIES.reduce((sum, category) => sum + (activityJournal[category]?.length || 0), 0);
  const active = ACTIVITY_CATEGORIES.reduce((sum, category) => sum + (activityJournal[category] || []).filter((entry) => entry.state === "running" || entry.state === "pending").length, 0);
  setBadge(el("activityJournalBadge"), t("activitySummary", {count: total, active}), total ? "ok" : "muted");
  renderActivityCategory("direct", "directActivityList");
  renderActivityCategory("stream", "streamActivityList");
  renderActivityCategory("job", "jobActivityList");
  renderActivityCategory("reader", "readerActivityList");
}

function readerActivityState(status) {
  const value = String(status || "").toLowerCase();
  if (["completed"].includes(value)) return "ok";
  if (["failed", "rejected"].includes(value)) return "error";
  if (["interrupted", "cancelled"].includes(value)) return "warn";
  return "running";
}

function syncReaderActivities(reader = {}) {
  const records = [...(reader.recent || [])].reverse();
  for (const record of records) {
    const state = readerActivityState(record.status);
    journalActivity("reader", {
      endpoint: record.endpoint || "/tts/legado.wav",
      mode: record.mode || "-",
      title: record.endpoint || "/tts/legado.wav",
      message: t("readerExternalRequest", {
        character: record.character_name || "-",
        chars: record.text_chars || 0,
      }),
      state,
      status: record.status || "received",
      status_state: state === "running" ? "warn" : state,
      elapsed_seconds: record.elapsed_seconds,
      bytes: record.audio_bytes || 0,
      error: record.error_detail || null,
      timestamp: record.started_at,
    }, `reader-${record.request_id}`);
  }
}

function pushActivity(category, entry = {}, key = null) {
  const safeCategory = ACTIVITY_CATEGORIES.includes(category) ? category : classifyActivity(entry.endpoint, entry.mode);
  const id = key || entry.activity_id || `${safeCategory}-${++activitySequence}`;
  const current = activityIndex.get(id) || {activity_id: id, category: safeCategory, state: "pending"};
  const next = {
    ...current,
    ...entry,
    activity_id: id,
    category: safeCategory,
    timestamp: entry.timestamp || current.timestamp || new Date().toISOString(),
    state: entry.state || current.state || "pending",
  };
  activityIndex.set(id, next);
  const list = activityJournal[safeCategory] || (activityJournal[safeCategory] = []);
  const index = list.findIndex((item) => item.activity_id === id);
  if (index >= 0) {
    list[index] = next;
  } else {
    list.unshift(next);
  }
  if (list.length > ACTIVITY_LIMIT) {
    const removed = list.splice(ACTIVITY_LIMIT);
    for (const item of removed) {
      activityIndex.delete(item.activity_id);
    }
  }
  renderActivityJournal();
  return next;
}

function completeActivity(activityId, patch = {}) {
  if (!activityId) return null;
  const current = activityIndex.get(activityId);
  if (!current) return null;
  return pushActivity(current.category, {
    ...current,
    ...patch,
    state: patch.state || "ok",
    timestamp: patch.timestamp || current.timestamp,
  }, activityId);
}

function beginActivity(category, entry = {}, key = null) {
  return pushActivity(category, {
    state: "pending",
    status: "pending",
    status_state: "warn",
    ...entry,
  }, key);
}

function jsonByteSize(value) {
  try {
    return new Blob([JSON.stringify(value)]).size;
  } catch (error) {
    return null;
  }
}

function startRequestActivity({endpoint = "-", mode = "-", title = null, message = null, category = null, progress = null, parallel = null} = {}) {
  const entry = beginActivity(category || activityCategoryForMode(mode, endpoint), {
    endpoint,
    mode,
    title: title || endpoint,
    message: message || endpoint,
    state: "running",
    status: "running",
    status_state: "warn",
    elapsed_seconds: 0,
    progress,
    parallel,
  });
  return {
    activityId: entry.activity_id,
    started: performance.now(),
  };
}

function finishRequestActivity(activity, {status = "ok", state = "ok", message = null, bytes = null, error = null, progress = null, parallel = null, statusState = null} = {}) {
  if (!activity?.activityId) return;
  const elapsed = (performance.now() - activity.started) / 1000;
  completeActivity(activity.activityId, {
    state,
    status,
    status_state: statusState || (state === "error" ? "error" : (state === "warn" ? "warn" : "ok")),
    elapsed_seconds: elapsed,
    bytes,
    message,
    error,
    progress,
    parallel,
  });
}

function journalActivity(category, entry = {}, key = null) {
  return pushActivity(category, entry, key);
}

function resetActivityState() {
  clearActivityJournal();
}

function setButtonBusy(button, busy) {
  if (!button) return;
  button.disabled = Boolean(busy);
  button.classList.toggle("is-loading", Boolean(busy));
  button.setAttribute("aria-busy", busy ? "true" : "false");
}

function updateActionAvailability() {
  const busy = activeSynthesisInFlight || activeJobInFlight || Boolean(activeJobTimer);
  const conversionBusy = Boolean(activeConversionTimer);
  const generate = el("generateBtn");
  if (generate) {
    generate.disabled = busy;
    generate.classList.toggle("is-loading", activeSynthesisInFlight || activeJobInFlight);
    generate.setAttribute("aria-busy", activeSynthesisInFlight || activeJobInFlight ? "true" : "false");
  }
  const prepareBusy = lastPreparedState === "busy";
  for (const id of ["loadCharacterBtn", "setReferenceBtn", "prepareBtn", "applyRuntimeBtn", "applyListenBtn", "restoreDefaultsBtn"]) {
    const button = el(id);
    if (!button) continue;
    button.disabled = activeSynthesisInFlight || activeJobInFlight || prepareBusy;
  }
  const cancelJob = el("cancelJobBtn");
  if (cancelJob) {
    cancelJob.disabled = !activeJobTimer;
  }
  const clearJob = el("clearJobBtn");
  if (clearJob) {
    clearJob.disabled = activeJobInFlight || Boolean(activeJobTimer);
  }
  const startConversionButton = el("startConversionBtn");
  if (startConversionButton) {
    startConversionButton.disabled = conversionBusy;
  }
  const scanConversionButton = el("scanConversionBtn");
  if (scanConversionButton) {
    scanConversionButton.disabled = conversionBusy;
  }
  updateMemoryActionAvailability();
}

function activeLocaleField(item, base) {
  return item?.[`${base}_${activeLanguage}`] || item?.[`${base}_zh`] || item?.[`${base}_en`] || "-";
}

function validCopyValue(value) {
  const text = String(value || "").trim();
  if (!text || text === "-") {
    throw new Error(t("unavailable"));
  }
  return text;
}

function shortProvider(provider) {
  const known = {
    CUDAExecutionProvider: "CUDA",
    CPUExecutionProvider: "CPU",
  };
  return provider ? (known[provider] || provider.replace(/ExecutionProvider$/, "")) : t("providerNotLoaded");
}

function providerPillState(provider) {
  if (!provider) return "warn";
  if (provider === "CUDAExecutionProvider") return "ok";
  if (provider === "CPUExecutionProvider") return "muted";
  return "muted";
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

function runtimeModeLabel(mode) {
  const value = String(mode || "").toLowerCase();
  const labels = {
    cuda: t("runtimeModeCuda"),
    cpu: t("runtimeModeCpu"),
    auto: t("runtimeModeAuto"),
  };
  return labels[value] || mode || "-";
}

function languageDisplayLabel(language) {
  const value = String(language || "").trim();
  const labels = {
    Chinese: t("languageChinese"),
    English: t("languageEnglish"),
    Japanese: t("languageJapanese"),
    "Hybrid-Chinese-English": t("languageHybridChineseEnglish"),
    Korean: t("languageKorean"),
  };
  return labels[value] || value || "-";
}

function readerModeLabel(mode) {
  const value = String(mode || "").toLowerCase();
  if (value === "buffered") {
    return t("readerModeBuffered");
  }
  if (value === "stream") {
    return t("readerModeStream");
  }
  return mode || "-";
}

function strategyLabel(strategy) {
  if (strategy === "gpu_segment_parallel") {
    return t("gpuSegmentParallel");
  }
  if (strategy === "single_session_serial") {
    return t("singleSessionSerial");
  }
  return strategy || "-";
}

function localizedField(item, key) {
  if (!item) return "";
  return activeLanguage === "zh"
    ? (item[`${key}_zh`] || item[key] || "")
    : (item[key] || item[`${key}_zh`] || "");
}

function localizedReason(info) {
  if (!info) return "";
  return localizedField(info, "reason");
}

function localizedBlockedReason(action) {
  return localizedField(action, "blocked_reason");
}

function stageLabel(stage) {
  const labels = {
    queued: t("stageQueued"),
    waiting_for_tts_session: t("stageWaiting"),
    synthesizing: t("stageSynthesizing"),
    parallel_synthesizing: t("stageParallelSynthesizing"),
    writing_wav: t("stageWritingWav"),
    completed: t("stageCompleted"),
    cancelled: t("stageCancelled"),
    failed: t("stageFailed"),
  };
  return labels[stage] || stage || "-";
}

function localizedProgressMessage(progress = {}, fallback = "") {
  const stage = progress.stage || "";
  if (activeLanguage !== "zh") {
    return progress.message || fallback || "-";
  }
  const message = String(progress.message || fallback || "");
  const completed = Number(progress.completed_segments || 0);
  const total = Number(progress.total_segments || 0);
  const workers = progress.parallel_workers || progress.requested_workers || "-";
  if (stage === "queued" || message === "Queued for synthesis.") {
    return t("progressQueuedMessage");
  }
  if (stage === "waiting_for_tts_session" || message === "Waiting for the TTS session lock.") {
    return t("progressWaitingMessage");
  }
  if (stage === "synthesizing" || message === "Synthesizing audio.") {
    return t("progressSynthesizingMessage");
  }
  if (stage === "parallel_synthesizing") {
    if (completed > 0 || total > 0) {
      return t("progressParallelDoneMessage", {done: completed, total: total || "?"});
    }
    return t("progressParallelStartMessage", {workers});
  }
  if (stage === "writing_wav" || message === "Writing WAV output.") {
    return t("progressWritingMessage");
  }
  if (stage === "completed") {
    return message.includes("Parallel") ? t("progressParallelCompletedMessage") : t("progressCompletedMessage");
  }
  if (stage === "cancelled") {
    return t("progressCancelledMessage");
  }
  if (stage === "failed") {
    return t("progressFailedMessage");
  }
  return message || "-";
}

function firstGpuMemory(memory = {}) {
  const gpus = memory?.gpu_memory?.gpus || [];
  return gpus.length ? gpus[0] : null;
}

function formatVramGpu(gpu) {
  if (!gpu) {
    return t("memoryUnavailable");
  }
  const name = gpu.name || "GPU";
  const temperature = Number.isFinite(Number(gpu.temperature_c))
    ? ` · ${gpu.temperature_c} C`
    : "";
  return `${name}${temperature}`;
}

function formatGpuUtilization(gpu) {
  if (!gpu || !Number.isFinite(Number(gpu.utilization_gpu_percent))) {
    return t("memoryUnavailable");
  }
  return `${gpu.utilization_gpu_percent}%`;
}

function formatVramUsage(gpu) {
  if (!gpu) {
    return t("memoryUnavailable");
  }
  const used = Number(gpu.memory_used_mib || 0);
  const total = Number(gpu.memory_total_mib || 0);
  const percent = Number.isFinite(Number(gpu.memory_used_percent))
    ? `${Number(gpu.memory_used_percent).toFixed(1)}%`
    : "-";
  return `${used} / ${total} MiB · ${percent}`;
}

function formatCpuUsage(systemUsage) {
  const processValue = systemUsage?.process_cpu_percent;
  const systemValue = systemUsage?.system_cpu_percent;
  const processText = Number.isFinite(Number(processValue)) ? `${Number(processValue).toFixed(1)}%` : t("memoryUnavailable");
  const systemText = Number.isFinite(Number(systemValue)) ? `${Number(systemValue).toFixed(1)}%` : t("memoryUnavailable");
  if (processText === t("memoryUnavailable") && systemText === t("memoryUnavailable")) {
    return t("memoryUnavailable");
  }
  return `${t("memoryProcessCpuLabel")} ${processText} · ${t("memorySystemCpuLabel")} ${systemText}`;
}

function formatSystemMemory(systemUsage) {
  const memory = systemUsage?.system_memory || {};
  if (!memory.available) {
    return t("memoryUnavailable");
  }
  const used = Number(memory.used_mib || 0).toFixed(0);
  const total = Number(memory.total_mib || 0).toFixed(0);
  const percent = Number.isFinite(Number(memory.memory_load_percent))
    ? `${memory.memory_load_percent}%`
    : "-";
  return `${used} / ${total} MiB · ${percent}`;
}

function formatProcessMemory(systemUsage) {
  const memory = systemUsage?.process_memory || {};
  if (!memory.available) {
    return t("memoryUnavailable");
  }
  return `${Number(memory.rss_mib || 0).toFixed(1)} MiB`;
}

function renderMemoryPolicy(memory) {
  lastMemorySnapshot = memory || null;
  const gpu = firstGpuMemory(memory);
  const gpuAvailable = Boolean(memory?.gpu_memory?.available && gpu);
  const policy = memory?.policy || {};
  const parallel = memory?.parallel || {};
  const runtime = memory?.runtime || {};
  const systemUsage = memory?.system_usage || {};
  const busy = Boolean(policy.busy);

  setBadge(el("memoryBadge"), busy ? t("activityBusy") : (gpuAvailable ? "VRAM" : t("memoryUnavailable")), busy ? "warn" : (gpuAvailable ? "ok" : "muted"));
  setText("memoryCpuState", formatCpuUsage(systemUsage));
  setText("memoryRamState", formatSystemMemory(systemUsage));
  setText("memoryProcessState", formatProcessMemory(systemUsage));
  setText("memoryGpuState", `${formatVramGpu(gpu)} · ${t("memoryGpuUtilLabel")} ${formatGpuUtilization(gpu)}`);
  setText("memoryVramState", formatVramUsage(gpu));
  setPills(el("memoryPolicyState"), [
    {label: strategyLabel(policy.name || "single_session_serial"), state: "warn"},
    {label: shortProvider(runtime.selected_provider), state: providerPillState(runtime.selected_provider)},
  ]);
  setPills(el("memoryParallelState"), [
    {label: strategyLabel(parallel.job_strategy || parallel.strategy || "single_session_serial"), state: parallel.execution_supported ? "ok" : "warn"},
    {label: t("jobOnlyParallel"), state: "muted"},
  ]);
  setPills(el("memoryCacheState"), [
    {label: `${policy.loaded_character_count || 0} ${t("memoryModelsUnit")}`, state: policy.loaded_character_count ? "warn" : "muted"},
    {label: `${policy.reference_cache_size || 0} ${t("memoryRefsUnit")}`, state: policy.reference_cache_size ? "warn" : "muted"},
  ]);
  const note = localizedField(policy, "vram_note") || t("memoryNoteVram");
  setText("memoryNote", note);
  updateMemoryActionAvailability();
}

function renderParallelCapability(parallel) {
  const info = parallel || config?.parallel || lastRuntimeSnapshot?.job_parallel || {};
  const executionSupported = Boolean(info.execution_supported);
  const stateLabel = executionSupported
    ? strategyLabel(info.strategy || "gpu_segment_parallel")
    : t("parallelCapabilitySerial");
  const state = executionSupported ? "ok" : "warn";
  setBadge(el("parallelCapabilityState"), stateLabel, state);
  setText("parallelCapabilityReason", localizedReason(info) || t("parallelUnavailable"));
  renderParallelWorkerOptions(info);
}

function renderParallelWorkerOptions(parallel = config?.parallel || lastRuntimeSnapshot?.job_parallel || {}) {
  const datalist = el("parallelWorkerOptions");
  if (!datalist) return;
  clearNode(datalist);
  const maxWorkers = Math.max(2, Number(parallel?.max_workers || 8));
  const options = Array.isArray(parallel?.worker_options) && parallel.worker_options.length
    ? parallel.worker_options
    : [...Array(maxWorkers - 1)].map((_, index) => String(index + 2)).concat(["auto"]);
  const seen = new Set();
  for (const value of options) {
    const text = String(value).trim();
    if (!text || seen.has(text)) continue;
    seen.add(text);
    const option = document.createElement("option");
    option.value = text;
    datalist.appendChild(option);
  }
}

function updateMemoryActionAvailability() {
  const actions = lastMemorySnapshot?.actions || config?.memory_policy?.actions || {};
  const busy = activeSynthesisInFlight || activeJobInFlight || Boolean(activeJobTimer) || Boolean(lastMemorySnapshot?.policy?.busy);
  const mapping = {
    releaseSessionsBtn: actions.release_idle_sessions,
  };
  for (const [id, action] of Object.entries(mapping)) {
    const button = el(id);
    if (!button) continue;
    const enabled = Boolean(action?.enabled) && !busy;
    button.disabled = !enabled;
    button.title = localizedBlockedReason(action) || (busy ? t("memoryBusy") : "");
  }
  const refresh = el("refreshMemoryBtn");
  if (refresh) {
    refresh.disabled = false;
  }
  const clearCache = el("clearMemoryCacheBtn");
  if (clearCache) {
    clearCache.disabled = false;
  }
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
  if (number < 60) {
    return `${number.toFixed(1)}s`;
  }
  const total = Math.round(number);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`;
  }
  return `${minutes}m ${seconds}s`;
}

function formatEta(value) {
  const number = Number(value);
  return Number.isFinite(number) ? formatSeconds(number) : t("etaPending");
}

function formatPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "0%";
  }
  const clamped = Math.max(0, Math.min(100, number));
  return `${clamped.toFixed(clamped >= 99.95 || clamped < 1 ? 0 : 1)}%`;
}

function estimatedSegmentCount(text, splitSentence) {
  const trimmed = String(text || "").trim();
  if (!trimmed) return 0;
  if (!splitSentence) return 1;
  const normalized = trimmed.replace(/\r?\n+/g, "");
  const roughParts = normalized
    .split(/(?<=[。！？!?\.])|(?<=[，、；;:：])(?=.{40,})/u)
    .map((part) => part.trim())
    .filter(Boolean);
  return Math.max(1, roughParts.length);
}

function currentParallelSelection() {
  const parallelConfig = config?.parallel || lastRuntimeSnapshot?.job_parallel || {};
  const available = Boolean(parallelConfig.execution_supported);
  const isJobMode = el("endpointMode")?.value === "job";
  const enabled = Boolean(available && isJobMode && el("parallelEnabled")?.checked);
  const requested = enabled ? normalizedParallelWorkersInput() : "1";
  return {
    enabled,
    requested_workers: requested,
    effective: false,
    strategy: parallelConfig.strategy || "single_session_serial",
    reason: localizedReason(parallelConfig),
  };
}

function normalizedParallelWorkersInput() {
  const input = el("parallelWorkers");
  const parallelConfig = config?.parallel || lastRuntimeSnapshot?.job_parallel || {};
  const fallback = String(parallelConfig.default_workers || "2");
  const raw = rawParallelWorkersInput();
  if (raw === "auto") {
    return "auto";
  }
  if (!/^\d+$/.test(raw)) {
    return fallback;
  }
  const parsed = Number.parseInt(raw, 10);
  return parsed >= 2 ? String(parsed) : fallback;
}

function rawParallelWorkersInput() {
  return String(el("parallelWorkers")?.value || "").trim().toLowerCase();
}

function isValidParallelWorkersInput(value = rawParallelWorkersInput()) {
  if (value === "auto") {
    return true;
  }
  if (!/^\d+$/.test(value)) {
    return false;
  }
  return Number.parseInt(value, 10) >= 2;
}

function normalizeParallelWorkersField() {
  const input = el("parallelWorkers");
  if (!input) return;
  const normalized = normalizedParallelWorkersInput();
  if (input.value.trim().toLowerCase() !== normalized) {
    input.value = normalized;
  }
}

function parallelText(parallel) {
  const info = parallel || currentParallelSelection();
  if (!info.enabled) {
    return info.strategy ? `${t("parallelOff")} · ${strategyLabel(info.strategy)}` : t("parallelOff");
  }
  if (info.effective) {
    const workers = info.effective_workers || info.requested_workers || "auto";
    return `${t("parallelEffective", {workers})} · ${strategyLabel(info.strategy || "gpu_segment_parallel")}`;
  }
  const workers = info.requested_workers || info.effective_workers || "auto";
  const label = t("parallelRequested", {workers});
  return `${label} · ${strategyLabel(info.strategy || "single_session_serial")}`;
}

function runtimeBadgeInfo(runtime) {
  const mode = runtime?.runtime_mode || "-";
  const providers = runtime?.selected_providers || [];
  const primary = providers[0] || null;
  const label = primary ? `${mode} · ${shortProvider(primary)}` : mode;
  if (primary === "CUDAExecutionProvider") {
    return {label, state: "ok"};
  }
  if (!primary && ["cuda", "auto"].includes(mode)) {
    return {label, state: "warn"};
  }
  if (["cuda", "auto"].includes(mode) && primary === "CPUExecutionProvider") {
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
      const detail = data.detail || data.message || data;
      if (typeof detail === "string") {
        return detail;
      }
      if (detail && typeof detail === "object") {
        return localizedField(detail, "message") || localizedReason(detail) || JSON.stringify(detail);
      }
      return JSON.stringify(data);
    } catch (error) {
      return `${response.status} ${response.statusText}`;
    }
  }
  const text = await response.text();
  return text || `${response.status} ${response.statusText}`;
}

function userFacingErrorMessage(message) {
  const value = String(message || "");
  if (value.includes("Reference audio not set")) {
    return t("referenceNotSetHelp");
  }
  if (value.includes("Character model is not loaded")) {
    return t("characterNotLoadedHelp");
  }
  return value;
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
    throw new Error(userFacingErrorMessage(await readError(response)));
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
      throw new Error(userFacingErrorMessage(await readError(response)));
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
  if (activeAudioActivity) {
    finishRequestActivity(activeAudioActivity, {status: "interrupted", state: "warn", message: "audio cleared", progress: lastProgressContext?.progress});
    activeAudioActivity = null;
    stopProgressPolling();
    activeSynthesisInFlight = false;
  }
  if (activeAudioUrl) {
    URL.revokeObjectURL(activeAudioUrl);
    activeAudioUrl = null;
  }
  el("audioPlayer").pause();
  el("audioPlayer").removeAttribute("src");
  el("audioPlayer").load();
  el("audioPlayer").classList.add("media-hidden");
  const link = el("downloadLink");
  link.removeAttribute("href");
  link.classList.add("disabled");
  link.classList.add("media-hidden");
  updateActionAvailability();
}

function setAudio(blob, filename) {
  clearAudio();
  activeAudioUrl = URL.createObjectURL(blob);
  el("audioPlayer").src = activeAudioUrl;
  el("audioPlayer").classList.remove("media-hidden");
  el("audioPlayer").load();
  const link = el("downloadLink");
  link.href = activeAudioUrl;
  link.download = filename;
  link.classList.remove("disabled");
  link.classList.remove("media-hidden");
}

function setAudioUrl(url, filename) {
  clearAudio();
  el("audioPlayer").src = url;
  el("audioPlayer").classList.remove("media-hidden");
  el("audioPlayer").load();
  const link = el("downloadLink");
  link.href = url;
  link.download = filename;
  link.classList.remove("disabled");
  link.classList.remove("media-hidden");
}

function setDownloadOnly(blob, filename) {
  clearAudio();
  activeAudioUrl = URL.createObjectURL(blob);
  const link = el("downloadLink");
  link.href = activeAudioUrl;
  link.download = filename;
  link.classList.remove("disabled");
  link.classList.remove("media-hidden");
}

function clearJobView() {
  if (activeJobTimer) {
    clearInterval(activeJobTimer);
    activeJobTimer = null;
  }
  activeJobActivity = null;
  el("jobBox").classList.add("hidden");
  el("jobId").textContent = "-";
  el("jobStatus").textContent = "-";
  el("jobStage").textContent = "-";
  el("jobMessage").textContent = "-";
  updateActionAvailability();
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

function emptyProgress() {
  return {
    stage: "-",
    message: "-",
    total_chars: 0,
    completed_chars: 0,
    total_segments: 0,
    completed_segments: 0,
    generated_pcm_bytes: 0,
    generated_wav_bytes: 0,
    elapsed_seconds: 0,
    estimated_remaining_seconds: null,
    percent: 0,
  };
}

function initialProgressForPayload(payload, stage = "queued") {
  const totalChars = payload?.text?.length || 0;
  return {
    ...emptyProgress(),
    stage,
    message: stage,
    total_chars: totalChars,
    total_segments: estimatedSegmentCount(payload?.text || "", Boolean(payload?.split_sentence)),
  };
}

function setProgressContext(context = null) {
  lastProgressContext = context;
}

function updateProgressView(progress = null, context = lastProgressContext) {
  const value = progress || emptyProgress();
  if (context) {
    lastProgressContext = {
      ...context,
      progress: value,
    };
  }
  const percent = Math.max(0, Math.min(100, Number(value.percent) || 0));
  el("progressFill").style.width = `${percent}%`;
  const progressState = value.stage === "failed" ? "error" : (percent >= 100 ? "ok" : (percent > 0 ? "warn" : "muted"));
  setBadge(el("progressPercent"), formatPercent(percent), progressState);
  el("progressStage").textContent = stageLabel(value.stage);
  el("progressMessage").textContent = localizedProgressMessage(value);
  el("progressSegments").textContent = `${value.completed_segments || 0}/${value.total_segments || 0}`;
  el("progressChars").textContent = `${value.completed_chars || 0}/${value.total_chars || 0}`;
  el("progressElapsed").textContent = formatSeconds(value.elapsed_seconds || 0);
  el("progressEta").textContent = Number.isFinite(Number(value.estimated_remaining_seconds))
    ? formatEta(value.estimated_remaining_seconds)
    : t("etaPending");
  const pcmBytes = Number(value.generated_pcm_bytes || 0);
  const wavBytes = Number(value.generated_wav_bytes || 0);
  el("progressBytes").textContent = wavBytes > 0
    ? `${formatBytes(wavBytes)} WAV`
    : `${formatBytes(pcmBytes)} PCM`;
  el("progressMode").textContent = context?.modeLabel || context?.mode || "-";
  el("progressParallel").textContent = parallelText(value.parallel || context?.parallel || null);
}

function resetProgressView(context = null) {
  setProgressContext(context);
  updateProgressView(context?.progress || null, context);
}

function markProgressFailed(message) {
  if (!lastProgressContext?.progress) {
    return;
  }
  const current = lastProgressContext.progress;
  const mutableStages = new Set([
    "requesting",
    "submitting",
    "queued",
    "starting",
    "waiting_for_tts_session",
    "synthesizing",
    "writing_wav",
  ]);
  if (!mutableStages.has(current.stage)) {
    return;
  }
  updateProgressView({
    ...current,
    stage: "failed",
    message: message || "failed",
    estimated_remaining_seconds: null,
  }, lastProgressContext);
}

function updateCurrentProgressParallelSelection() {
  if (!lastProgressContext) {
    return;
  }
  lastProgressContext = {
    ...lastProgressContext,
    parallel: currentParallelSelection(),
  };
  updateProgressView(lastProgressContext.progress || null, lastProgressContext);
}

function stopProgressPolling() {
  if (activeProgressTimer) {
    clearInterval(activeProgressTimer);
    activeProgressTimer = null;
  }
}

function startProgressPolling(context) {
  stopProgressPolling();
  setProgressContext(context);
  activeProgressTimer = setInterval(() => {
    refreshStatus().catch((error) => appendLog(t("refreshFailed", {message: error.message || error})));
  }, 1000);
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
  updateActionAvailability();
}

function preparedStateAfterRuntime(result) {
  if (result.reload_required_for_loaded_sessions) {
    return "reload";
  }
  const loaded = result.loaded_characters || [];
  const current = el("characterName").value.trim();
  if (!loaded.includes(current)) {
    return "not_loaded";
  }
  return lastPreparedState === "ready" ? "ready" : "model_loaded";
}

function selectedPayload() {
  return {
    character_name: el("characterName").value.trim(),
    text: el("inputText").value.trim(),
    split_sentence: el("splitSentence").checked,
  };
}

function selectedJobPayload() {
  const parallel = currentParallelSelection();
  if (parallel.enabled) {
    if (!isValidParallelWorkersInput()) {
      throw new Error(t("parallelInvalidWorkers"));
    }
  }
  return {
    ...selectedPayload(),
    parallel_enabled: parallel.enabled,
    parallel_workers: parallel.enabled ? parallel.requested_workers : 1,
  };
}

function endpointModeHint(mode = el("endpointMode")?.value || "wav") {
  const hints = {
    wav: t("endpointHintWav"),
    "legado-buffered": t("endpointHintLegadoBuffered"),
    "legado-stream": t("endpointHintLegadoStream"),
    "stream-wav": t("endpointHintStreamWav"),
    raw: t("endpointHintRaw"),
    job: t("endpointHintJob"),
  };
  return hints[mode] || "-";
}

function updateModeControls() {
  const parallelConfig = config?.parallel || lastRuntimeSnapshot?.job_parallel || {};
  const isJob = el("endpointMode").value === "job";
  const canParallel = Boolean(isJob && parallelConfig.execution_supported);
  el("parallelEnabled").disabled = !canParallel;
  el("parallelWorkers").disabled = !canParallel || !el("parallelEnabled").checked;
  el("parallelControls").classList.toggle("disabled-field", !canParallel);
  el("parallelControls").title = canParallel ? t("parallelToggleTitle") : (localizedReason(parallelConfig) || t("parallelUnavailable"));
  if (!canParallel) {
    el("parallelEnabled").checked = false;
  }
  renderParallelWorkerOptions(parallelConfig);
  setText("endpointModeHint", endpointModeHint());
  if (lastProgressContext) {
    updateCurrentProgressParallelSelection();
  }
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

function setSelectOptions(select, items = [], selectedValue = "") {
  clearNode(select);
  for (const item of items) {
    const option = document.createElement("option");
    if (typeof item === "string") {
      option.value = item;
      option.textContent = item;
    } else {
      option.value = item.value ?? item.name ?? "";
      option.textContent = item.label ?? item.name ?? item.value ?? "";
      if (item.title || item.description) {
        option.title = item.title || item.description;
      }
    }
    select.appendChild(option);
  }
  if (selectedValue && Array.from(select.options).some((option) => option.value === selectedValue)) {
    select.value = selectedValue;
  } else if (select.options.length) {
    select.selectedIndex = 0;
  }
}

function fillDataListOptions(list, items = []) {
  clearNode(list);
  const seen = new Set();
  for (const item of items) {
    const value = typeof item === "string" ? item : (item.value ?? item.name ?? "");
    if (!value || seen.has(value)) continue;
    seen.add(value);
    const option = document.createElement("option");
    option.value = value;
    if (typeof item !== "string" && (item.label || item.title || item.description)) {
      option.label = item.label || item.title || item.description;
    }
    list.appendChild(option);
  }
}

function ensureSelectValue(select, value, label = null) {
  const normalized = String(value || "");
  if (!normalized) return;
  if (!Array.from(select.options).some((option) => option.value === normalized)) {
    const option = document.createElement("option");
    option.value = normalized;
    option.textContent = label || normalized;
    select.appendChild(option);
  }
  select.value = normalized;
}

function presetSourceLabel(preset) {
  return preset?.source === "user" ? t("presetManual") : t("presetAuto");
}

function presetOptionLabel(preset) {
  const base = preset?.label || preset?.name || "-";
  return `${base} · ${presetSourceLabel(preset)}`;
}

function fillPresetOptions(presets = [], selectedId = "") {
  const items = presets.map((preset) => ({
    value: preset.id || `${preset.source || "auto"}:${preset.name}`,
    label: presetOptionLabel(preset),
    title: preset.root_dir || preset.onnx_model_dir || "",
  }));
  setSelectOptions(el("presetSelect"), items, selectedId);
  if (selectedId) {
    const selectedExists = Array.from(el("presetSelect").options).some((option) => option.value === selectedId);
    if (selectedExists) {
      el("presetSelect").value = selectedId;
    }
  }
  updatePresetHint();
}

function currentPreset() {
  const selectedId = el("presetSelect")?.value || "";
  return (config?.characters || []).find((preset) => String(preset.id || "") === selectedId) || null;
}

function fillCharacterOptions(characters = [], selectedName = "") {
  const items = characters.map((character) => ({
    value: character.name,
    label: character.label || character.name,
    title: character.root_dir || "",
  }));
  fillDataListOptions(el("characterNameOptions"), items);
  el("characterName").value = selectedName || el("characterName").value || "";
  el("characterName").title = t("presetCount", {count: characters.length});
}

function fillModelDirOptions(characters = [], selectedDir = "") {
  const seen = new Set();
  const items = [];
  for (const character of characters) {
    const dir = character.onnx_model_dir || "";
    if (!dir || seen.has(dir)) continue;
    seen.add(dir);
    items.push({
      value: dir,
      label: `${character.name} / ${character.family || "model"}`,
      title: dir,
    });
  }
  fillDataListOptions(el("modelDirOptions"), items);
  el("modelDir").value = selectedDir || el("modelDir").value || "";
}

function fillLanguageOptions(languages = [], selectedLanguage = "") {
  const values = Array.from(new Set(languages.filter(Boolean)));
  setSelectOptions(el("language"), values.map((language) => ({
    value: language,
    label: languageDisplayLabel(language),
    title: language,
  })), selectedLanguage);
  ensureSelectValue(el("language"), selectedLanguage);
}

function findCharacterPreset(name) {
  const target = String(name || "").trim().toLowerCase();
  return (config?.characters || []).find((character) => String(character.name || "").toLowerCase() === target) || null;
}

function findPresetByIdOrName(value) {
  const target = String(value || "").trim().toLowerCase();
  return (config?.characters || []).find((preset) => (
    String(preset.id || "").toLowerCase() === target
    || String(preset.name || "").toLowerCase() === target
  )) || null;
}

function findReferenceOption(preset, audioPathOrName) {
  const target = String(audioPathOrName || "").trim().toLowerCase();
  return (preset?.reference_options || []).find((reference) => (
    String(reference.audio_path || "").toLowerCase() === target
    || String(reference.name || "").toLowerCase() === target
  )) || null;
}

function fillReferenceOptions(preset, selectedAudioPath = "") {
  const references = preset?.reference_options || [];
  const items = references.map((reference) => ({
    value: reference.audio_path,
    label: reference.label || reference.name || reference.audio_path,
    title: reference.audio_path,
  }));
  fillDataListOptions(el("referenceAudioOptions"), items);
  el("referenceAudio").value = selectedAudioPath || preset?.reference_audio_path || el("referenceAudio").value || "";
}

function applyReferenceOption(audioPathOrName) {
  const preset = currentPreset() || findCharacterPreset(el("characterName").value);
  const reference = findReferenceOption(preset, audioPathOrName) || findReferenceOption(preset, preset?.reference_audio_path);
  if (!reference) {
    selectedReferenceName = "";
    return;
  }
  selectedReferenceName = reference.name || "";
  el("referenceAudio").value = reference.audio_path || "";
  el("referenceText").value = reference.audio_text || "";
  if (reference.language) {
    el("language").value = reference.language;
  }
}

function applyCharacterPreset(name, announce = false) {
  const preset = findPresetByIdOrName(name);
  if (!preset) return;
  if (preset.id) {
    el("presetSelect").value = preset.id;
  }
  el("characterName").value = preset.name;
  fillModelDirOptions(config?.characters || [], preset.onnx_model_dir || "");
  el("modelDir").value = preset.onnx_model_dir || el("modelDir").value || "";
  fillLanguageOptions(config?.languages || [], preset.language || el("language").value);
  el("language").value = preset.language || el("language").value;
  fillReferenceOptions(preset, preset.reference_audio_path || "");
  applyReferenceOption(preset.reference_audio_path || preset.reference_name || "");
  if (!el("referenceText").value && preset.reference_text) {
    el("referenceText").value = preset.reference_text;
  }
  setPreparedBadge("not_loaded");
  renderReaderConfig(readerConfigForCurrentSelection());
  updatePresetHint();
  if (announce) {
    appendLog(t("presetApplied", {name: preset.label || preset.name}), preset);
  }
}

function updatePresetHint() {
  const preset = currentPreset();
  if (!preset) {
    setText("presetHint", t("presetHintNone"));
    const deleteButton = el("deletePresetBtn");
    if (deleteButton) deleteButton.disabled = true;
    return;
  }
  const deletable = Boolean(preset.deletable || preset.source === "user");
  const detail = t(deletable ? "presetHintManual" : "presetHintAuto", {
    name: preset.label || preset.name || "-",
  });
  setText("presetHint", detail);
  const deleteButton = el("deletePresetBtn");
  if (deleteButton) {
    deleteButton.disabled = !deletable;
    deleteButton.title = deletable ? t("deletePreset") : t("presetAutoCannotDelete");
  }
}

function fillDefaults(defaults) {
  const modeSelect = el("runtimeMode");
  modeSelect.innerHTML = "";
  const modes = defaults.runtime_modes || MODES;
  for (const mode of modes) {
    const option = document.createElement("option");
    option.value = mode;
    option.textContent = runtimeModeLabel(mode);
    option.title = mode;
    modeSelect.appendChild(option);
  }

  fillPresetOptions(config?.characters || [], defaults.preset_id || "");
  fillCharacterOptions(config?.characters || [], defaults.character_name);
  fillModelDirOptions(config?.characters || [], defaults.onnx_model_dir);
  fillLanguageOptions(config?.languages || [defaults.language].filter(Boolean), defaults.language);

  el("characterName").value = defaults.character_name;
  el("modelDir").value = defaults.onnx_model_dir;
  el("language").value = defaults.language;
  el("referenceText").value = defaults.reference_text;
  const preset = findPresetByIdOrName(defaults.preset_id || defaults.character_name);
  if (preset?.id) {
    el("presetSelect").value = preset.id;
  }
  fillReferenceOptions(preset, defaults.reference_audio_path);
  el("referenceAudio").value = defaults.reference_audio_path;
  selectedReferenceName = defaults.reference_name || "";
  el("inputText").value = defaults.input_text;
  el("splitSentence").checked = Boolean(defaults.split_sentence);
  el("unloadSessions").checked = Boolean(defaults.unload_sessions);
  el("parallelEnabled").checked = Boolean(defaults.parallel_enabled);
  renderParallelWorkerOptions(config?.parallel || null);
  el("parallelWorkers").value = String(defaults.parallel_workers || config?.parallel?.default_workers || "2");
  el("conversionOutputRoot").value = config?.conversion?.output_root || "";
  renderConversionScan(null);
  el("conversionLog").textContent = t("conversionOutputHint");
  modeSelect.value = modes.includes(defaults.runtime_mode) ? defaults.runtime_mode : modes[0];
  updateTextStats();
  updateModeControls();
  renderListenConfig(config?.listen || null);
  renderParallelCapability(config?.parallel || null);
  updatePresetHint();
  resetProgressView();
}

function renderListenConfig(listen, force = false) {
  if (!listen) {
    setText("listenCurrent", "-");
    setText("listenReach", "-");
    return;
  }
  const preserveInput = listenDirty && !force;
  const selectedHost = preserveInput ? el("listenHost").value : (listen.host || "0.0.0.0");
  const selectedPort = preserveInput ? el("listenPort").value : String(listen.port ?? 8000);
  const hostOptions = listen.host_options || [];
  setSelectOptions(el("listenHost"), hostOptions.map((item) => ({
    value: item.value,
    label: listenHostOptionLabel(item),
    title: listenHostOptionTitle(item),
  })), selectedHost);
  const portOptions = el("listenPortOptions");
  clearNode(portOptions);
  for (const port of listen.port_options || [8000, 7860, 5000, 0]) {
    const option = document.createElement("option");
    option.value = String(port);
    option.label = port === 0 ? t("autoPort") : String(port);
    portOptions.appendChild(option);
  }
  el("listenPort").value = selectedPort;
  const current = `${listen.host || "-"}:${listen.port ?? "-"}`;
  setText("listenCurrent", current);
  const lanReady = listen.host === "0.0.0.0" || (listen.lan_ipv4_addresses || []).includes(listen.host);
  setPills(el("listenReach"), [
    {label: lanReady ? t("listenLanReady") : t("listenLocalOnly"), state: lanReady ? "ok" : "warn"},
    {label: listen.restart_supported ? t("listenRestartSupported") : t("listenManualRestart"), state: listen.restart_supported ? "ok" : "warn"},
  ]);
}

function listenHostOptionLabel(item) {
  const value = String(item?.value || "");
  if (activeLanguage !== "zh") {
    return item?.label || value;
  }
  if (value === "0.0.0.0") {
    return `0.0.0.0 / ${t("listenAllInterfaces")}`;
  }
  if (value === "127.0.0.1") {
    return `127.0.0.1 / ${t("listenLocalOnlyOption")}`;
  }
  return `${value} / ${t("listenSpecificLan")}`;
}

function listenHostOptionTitle(item) {
  const value = String(item?.value || "");
  if (activeLanguage !== "zh") {
    return item?.description || item?.label || value;
  }
  if (value === "0.0.0.0") {
    return `${value}：${t("listenAllInterfaces")}，${t("listenLanReady")}`;
  }
  if (value === "127.0.0.1") {
    return `${value}：${t("listenLocalOnly")}`;
  }
  return `${value}：${t("listenSpecificLan")}`;
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
    button.addEventListener("click", () => withButton(button, () => copyText(url, label, button)));
    lanList.appendChild(button);
  });
}

function legadoJsLibTemplate(baseUrl, characterName, mode = "buffered") {
  const modeQuery = mode === "buffered" ? "&mode=buffered" : "";
  return [
    "function genieTtsUrl(speakText, speakSpeed) {",
    `    var baseUrl = '${baseUrl || ""}';`,
    "    var body = JSON.stringify({",
    `        character_name: '${characterName || ""}',`,
    "        text: String(speakText || ''),",
    "        split_sentence: true",
    "    });",
    "    var option = {",
    "        method: 'POST',",
    "        headers: {'Content-Type': 'application/json'},",
    "        body: body",
    "    };",
    `    return baseUrl + '/tts/legado.wav?wait_timeout=300${modeQuery},' + JSON.stringify(option);`,
    "}",
    "",
  ].join("\n");
}

function readerConfigForCurrentSelection() {
  const baseReader = config?.reader || {};
  const urls = {...(baseReader.urls || {})};
  const characterName = el("characterName")?.value?.trim() || config?.defaults?.character_name || "feibi";
  const baseUrl = urls.lan_api_base_url || urls.local_api_base_url || urls.api_base_url || "";
  const bufferedUrl = baseUrl ? `${baseUrl}/tts/legado.wav?wait_timeout=300&mode=buffered` : (urls.legado_buffered_url || "");
  const streamUrl = baseUrl ? `${baseUrl}/tts/legado.wav?wait_timeout=300` : (urls.legado_stream_url || "");
  const recommendedJson = {
    name: `Genie-TTS ${characterName} Buffered`,
    url: "@js:genieTtsUrl(speakText, speakSpeed);",
    contentType: "audio/wav",
    concurrentRate: "1500",
    enabledCookieJar: false,
    jsLib: legadoJsLibTemplate(baseUrl, characterName, "buffered"),
  };
  return {
    ...baseReader,
    settings: {
      ...(baseReader.settings || {}),
      character_name: characterName,
      split_sentence: true,
      wait_timeout_seconds: 300,
      recommended_mode: "buffered",
    },
    urls: {
      ...urls,
      legado_buffered_url: bufferedUrl,
      legado_stream_url: streamUrl,
    },
    templates: {
      ...(baseReader.templates || {}),
      recommended_jslib: recommendedJson.jsLib,
      recommended_json: recommendedJson,
      recommended_fields: [
        {key: "name", label: "name", value: recommendedJson.name},
        {key: "url", label: "url", value: recommendedJson.url},
        {key: "contentType", label: "Content-Type", value: recommendedJson.contentType},
        {key: "concurrentRate", label: "concurrentRate", value: recommendedJson.concurrentRate},
      ],
    },
  };
}

function renderReaderConfig(reader) {
  const settings = reader?.settings || {};
  const urls = reader?.urls || {};
  const templates = reader?.templates || {};
  setText("readerApiBase", urls.local_api_base_url || urls.api_base_url || "-");
  setText("readerLanApiBase", urls.lan_api_base_url || t("noLanDetected"));
  setText("readerBufferedUrl", urls.legado_buffered_url || "-");
  setText("readerStreamUrl", urls.legado_stream_url || "-");
  setText("readerDefaultCharacter", settings.character_name || "-");
  setText("readerSplitSentence", t(settings.split_sentence ? "yes" : "no"));
  setText("readerWaitTimeout", settings.wait_timeout_seconds ? `${settings.wait_timeout_seconds}s` : "-");
  setText("readerMode", readerModeLabel(settings.recommended_mode || "buffered"));
  setText("readerJsLib", templates.recommended_jslib || "-");
  setText("readerJsonTemplate", Object.keys(templates.recommended_json || {}).length
    ? JSON.stringify(templates.recommended_json, null, 2)
    : "-");
  const readerFields = templates.recommended_fields || [];
  const fieldMap = Object.fromEntries(readerFields.map((field) => [field.key, field.value]));
  setText("readerFieldName", fieldMap.name || templates.recommended_json?.name || "-");
  setText("readerFieldUrl", fieldMap.url || templates.recommended_json?.url || "-");
  setText("readerFieldContentType", fieldMap.contentType || templates.recommended_json?.contentType || "-");
  setText("readerFieldConcurrentRate", fieldMap.concurrentRate || templates.recommended_json?.concurrentRate || "-");
  setBadge(el("readerBadge"), t("readerRecommended"), "ok");
}

function renderEndpointCatalog(endpoints = []) {
  const list = el("endpointCatalog");
  clearNode(list);
  setBadge(el("endpointCountBadge"), t("endpointCount", {count: endpoints.length}), "muted");
  if (!endpoints.length) {
    list.textContent = "-";
    return;
  }
  for (const endpoint of endpoints) {
    const row = document.createElement("article");
    row.className = "endpoint-row";

    const head = document.createElement("div");
    head.className = "endpoint-head";
    const method = document.createElement("span");
    method.className = "method-pill";
    method.textContent = endpoint.method || "-";
    const path = document.createElement("code");
    path.textContent = endpoint.path || "-";
    head.append(method, path);

    const purpose = document.createElement("p");
    purpose.textContent = activeLocaleField(endpoint, "purpose");

    const details = document.createElement("dl");
    details.className = "endpoint-details";
    const responseTerm = document.createElement("dt");
    responseTerm.textContent = t("endpointResponseLabel");
    const responseDetail = document.createElement("dd");
    responseDetail.textContent = activeLocaleField(endpoint, "response");
    const useTerm = document.createElement("dt");
    useTerm.textContent = t("endpointUseCaseLabel");
    const useDetail = document.createElement("dd");
    useDetail.textContent = activeLocaleField(endpoint, "use_case");
    details.append(responseTerm, responseDetail, useTerm, useDetail);

    row.append(head, purpose, details);
    list.appendChild(row);
  }
}

function conversionFoldersFromInput() {
  return String(el("conversionFolders")?.value || "")
    .split(/\r?\n|;/)
    .map((line) => line.trim().replace(/^["']|["']$/g, ""))
    .filter(Boolean);
}

function conversionPayload() {
  const folders = conversionFoldersFromInput();
  if (!folders.length) {
    throw new Error(t("conversionNoFolders"));
  }
  return {
    folders,
    output_root: el("conversionOutputRoot")?.value?.trim() || config?.conversion?.output_root || "",
    overwrite: Boolean(el("conversionOverwrite")?.checked),
  };
}

function conversionStateLabel(status) {
  const value = String(status || "").toLowerCase();
  if (value === "queued") return t("conversionQueued");
  if (value === "running") return t("conversionRunning");
  if (value === "completed") return t("stageCompleted");
  if (value === "failed") return t("stageFailed");
  return status || "-";
}

function conversionStateClass(status, valid = null) {
  const value = String(status || "").toLowerCase();
  if (valid === true || value === "completed") return "ok";
  if (valid === false || value === "failed") return "error";
  if (value === "queued" || value === "running") return "warn";
  return "muted";
}

function renderConversionItems(items = []) {
  const list = el("conversionList");
  clearNode(list);
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "conversion-item";
    empty.textContent = "-";
    list.appendChild(empty);
    return;
  }
  for (const item of items) {
    const row = document.createElement("article");
    row.className = "conversion-item";
    const head = document.createElement("div");
    head.className = "conversion-item-head";
    const title = document.createElement("div");
    title.className = "conversion-item-title";
    title.textContent = item.source_folder || "-";
    const badge = document.createElement("span");
    const status = item.status || "";
    badge.className = `badge ${conversionStateClass(item.status, item.valid)}`;
    badge.textContent = status ? conversionStateLabel(status) : (item.valid ? t("conversionReady") : t("conversionInvalid"));
    head.append(title, badge);

    const body = document.createElement("div");
    body.className = "conversion-item-body";
    const lines = [
      `${item.detected_model_type || "-"} · ${item.reason || item.message || "-"}`,
      `ckpt: ${item.ckpt_path || "-"}`,
      `pth: ${item.pth_path || "-"}`,
      `out: ${item.output_dir || "-"}`,
    ];
    if (item.error_detail) {
      lines.push(`error: ${item.error_detail}`);
    }
    for (const line of lines) {
      const code = document.createElement("code");
      code.textContent = line;
      body.appendChild(code);
    }
    row.append(head, body);
    list.appendChild(row);
  }
}

function renderConversionScan(scan = null) {
  lastConversionScan = scan || null;
  const items = scan?.items || [];
  const validCount = Number(scan?.valid_count || 0);
  const total = Number(scan?.count || items.length || 0);
  setText("conversionOutputRootState", scan?.output_root || config?.conversion?.output_root || "-");
  setPills(el("conversionValidState"), [
    {label: `${validCount}/${total}`, state: validCount ? "ok" : "warn"},
    {label: scan?.overwrite ? t("conversionOverwriteLabel") : t("conversionIdle"), state: scan?.overwrite ? "warn" : "muted"},
  ]);
  setText("conversionJobState", lastConversionJob?.job_id || "-");
  setText("conversionProgressState", "-");
  setBadge(el("conversionBadge"), scan ? t("conversionScanDone", {valid: validCount, total}) : t("conversionIdle"), validCount ? "ok" : "muted");
  renderConversionItems(items);
}

function renderConversionJob(job = null) {
  lastConversionJob = job || null;
  if (!job) {
    setText("conversionJobState", "-");
    setText("conversionProgressState", "-");
    return;
  }
  const state = conversionStateClass(job.status);
  setBadge(el("conversionBadge"), `${conversionStateLabel(job.status)} · ${formatPercent(job.percent || 0)}`, state);
  setText("conversionOutputRootState", job.output_root || "-");
  setPills(el("conversionValidState"), [
    {label: `${job.completed || 0}/${job.total || 0}`, state: job.completed ? "ok" : "muted"},
    {label: `${job.failed || 0} ${t("stageFailed")}`, state: job.failed ? "error" : "muted"},
  ]);
  setText("conversionJobState", job.job_id || "-");
  setText("conversionProgressState", `${formatPercent(job.percent || 0)} · ${job.message || "-"}`);
  renderConversionItems(job.items || []);
  el("conversionLog").textContent = (job.logs || []).join("\n") || "-";
}

async function scanConversion() {
  ensureConfig();
  const payload = conversionPayload();
  const endpoint = config?.endpoints?.conversion_scan || "/convert/gpt-sovits/scan";
  const result = await apiJson(endpoint, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  renderConversionScan(result);
  el("conversionLog").textContent = `${t("conversionScanDone", {valid: result.valid_count || 0, total: result.count || 0})}\n${t("conversionOutputHint")}`;
  appendLog(t("conversionScanDone", {valid: result.valid_count || 0, total: result.count || 0}), result);
  return result;
}

async function startConversion() {
  ensureConfig();
  const payload = conversionPayload();
  const endpoint = config?.endpoints?.conversion_submit || "/convert/gpt-sovits";
  const result = await apiJson(endpoint, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  renderConversionJob(result.job || null);
  appendLog(t("conversionSubmitted", {jobId: result.job_id}), result);
  pollConversionJob(result.job_id);
  return result;
}

async function refreshConversionJob() {
  if (!lastConversionJob?.job_id) {
    if (lastConversionScan) {
      renderConversionScan(lastConversionScan);
      return lastConversionScan;
    }
    return scanConversion();
  }
  const endpoint = (config?.endpoints?.conversion_job_status || "/convert/gpt-sovits/jobs/{job_id}")
    .replace("{job_id}", encodeURIComponent(lastConversionJob.job_id));
  const job = await apiJson(endpoint, {method: "GET"});
  renderConversionJob(job);
  return job;
}

function pollConversionJob(jobId) {
  if (activeConversionTimer) {
    clearInterval(activeConversionTimer);
    activeConversionTimer = null;
  }
  const tick = async () => {
    try {
      const endpoint = (config?.endpoints?.conversion_job_status || "/convert/gpt-sovits/jobs/{job_id}")
        .replace("{job_id}", encodeURIComponent(jobId));
      const job = await apiJson(endpoint, {method: "GET"});
      renderConversionJob(job);
      if (["completed", "failed", "cancelled"].includes(job.status)) {
        clearInterval(activeConversionTimer);
        activeConversionTimer = null;
        appendLog(
          job.status === "completed"
            ? t("conversionCompleted", {done: job.completed || 0, total: job.total || 0})
            : t("conversionFailed", {message: job.message || job.error_detail || job.status}),
          job,
        );
        await refreshCharacterPresets();
      }
    } catch (error) {
      clearInterval(activeConversionTimer);
      activeConversionTimer = null;
      setBadge(el("conversionBadge"), t("conversionFailed", {message: error.message || error}), "error");
      appendLog(t("conversionFailed", {message: error.message || error}));
    }
  };
  tick();
  activeConversionTimer = setInterval(tick, 1800);
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
  renderParallelCapability(runtime.job_parallel || config?.parallel || null);
  if (lastMemorySnapshot) {
    renderMemoryPolicy({
      ...lastMemorySnapshot,
      runtime: {
        ...(lastMemorySnapshot.runtime || {}),
        runtime_mode: runtime.runtime_mode,
        selected_provider: runtime.selected_provider,
        selected_providers: runtime.selected_providers,
        available_providers: runtime.available_providers,
      },
    });
  }
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
  const conversionJobs = status.conversion_jobs || {};
  const reader = status.reader_requests || {};
  syncReaderActivities(reader);
  const activeJobs = jobs.active?.length || 0;
  const queued = jobs.queued_count || 0;
  const running = jobs.running_count || 0;
  const recentReaders = reader.recent?.length || 0;
  setPills(el("jobState"), [
    {label: `${t("activeMetric")} ${activeJobs}`, state: activeJobs ? "warn" : "muted"},
    {label: `${t("queuedMetric")} ${queued}`, state: queued ? "warn" : "muted"},
    {label: `${t("runningMetric")} ${running}`, state: running ? "warn" : "muted"},
    {label: `${t("navConversion")} ${conversionJobs.active_count || 0}`, state: conversionJobs.active_count ? "warn" : "muted"},
  ]);
  setPills(el("readerState"), [
    {label: `${t("activeMetric")} ${reader.active_count || 0}`, state: reader.active_count ? "warn" : "muted"},
    {label: `${t("recentMetric")} ${recentReaders}`, state: recentReaders ? "ok" : "muted"},
  ]);

  if (status.active_progress && lastProgressContext) {
    lastProgressContext.progress = status.active_progress;
    updateProgressView(status.active_progress, lastProgressContext);
  }

  const active = Boolean(status.busy);
  setBadge(el("activityBadge"), active ? t("activityBusy") : t("activityIdle"), active ? "warn" : "muted");
  renderActivityJournal();
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

async function refreshMemoryPolicy() {
  const endpoint = config?.endpoints?.runtime_memory;
  if (!endpoint) {
    renderMemoryPolicy(config?.memory_policy || null);
    return config?.memory_policy || null;
  }
  const memory = await apiJson(endpoint, {method: "GET"});
  renderMemoryPolicy(memory);
  return memory;
}

async function refreshStatus() {
  const status = await apiJson(config.endpoints.status, {method: "GET"});
  renderStatus(status);
  return status;
}

async function refreshListenConfig() {
  if (!config?.endpoints?.server_listen) {
    return null;
  }
  const result = await apiJson(config.endpoints.server_listen, {method: "GET"});
  config.listen = result.listen || config.listen;
  config.access = result.access || config.access;
  renderAccess(config.access);
  renderListenConfig(config.listen);
  renderReaderConfig(readerConfigForCurrentSelection());
  return result;
}

async function refreshCharacterPresets() {
  if (!config?.endpoints?.characters) {
    return null;
  }
  const result = await apiJson(config.endpoints.characters, {method: "GET"});
  config.characters = result.characters || config.characters || [];
  config.presets = result.presets || config.characters;
  const currentPresetId = el("presetSelect")?.value || result.default_preset_id || "";
  fillPresetOptions(config.characters, currentPresetId);
  fillCharacterOptions(config.characters, el("characterName").value);
  fillModelDirOptions(config.characters, el("modelDir").value);
  const selectedPreset = findPresetByIdOrName(currentPresetId) || findCharacterPreset(el("characterName").value);
  if (selectedPreset) {
    applyCharacterPreset(selectedPreset.id || selectedPreset.name);
  } else {
    updatePresetHint();
  }
  return result;
}

function currentPresetPayload() {
  const name = el("characterName").value.trim();
  const modelDir = el("modelDir").value.trim();
  if (!name || !modelDir) {
    throw new Error(t("loadFieldsRequired"));
  }
  return {
    name,
    label: name,
    family: currentPreset()?.family || "",
    onnx_model_dir: modelDir,
    language: el("language").value.trim() || "Chinese",
    reference_audio_path: el("referenceAudio").value.trim(),
    reference_text: el("referenceText").value,
    reference_name: selectedReferenceName || "",
  };
}

async function saveCurrentPreset() {
  ensureConfig();
  const endpoint = config?.endpoints?.character_presets || "/characters/presets";
  const payload = currentPresetPayload();
  const activity = startRequestActivity({
    endpoint,
    mode: "direct",
    title: endpoint,
    message: payload.name,
    category: "direct",
  });
  let result;
  try {
    result = await apiJson(endpoint, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (error) {
    finishRequestActivity(activity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error)});
    throw error;
  }
  config.characters = result.characters || result.presets || config.characters || [];
  config.presets = result.presets || config.characters;
  fillPresetOptions(config.characters, result.preset?.id || "");
  fillCharacterOptions(config.characters, payload.name);
  fillModelDirOptions(config.characters, payload.onnx_model_dir);
  const preset = result.preset || findPresetByIdOrName(payload.name);
  if (preset) {
    applyCharacterPreset(preset.id || preset.name, false);
  }
  finishRequestActivity(activity, {status: "ok", message: t("presetSaved", {name: payload.name}), bytes: jsonByteSize(result)});
  appendLog(t("presetSaved", {name: payload.name}), result);
  return result;
}

async function deleteSelectedPreset() {
  ensureConfig();
  const preset = currentPreset();
  if (!preset) {
    throw new Error(t("presetHintNone"));
  }
  if (!(preset.deletable || preset.source === "user")) {
    throw new Error(t("presetAutoCannotDelete"));
  }
  const endpointTemplate = config?.endpoints?.character_preset || "/characters/presets/{preset_id}";
  const endpoint = endpointTemplate.replace("{preset_id}", encodeURIComponent(preset.id));
  const activity = startRequestActivity({
    endpoint,
    mode: "direct",
    title: endpoint,
    message: preset.label || preset.name,
    category: "direct",
  });
  let result;
  try {
    result = await apiJson(endpoint, {method: "DELETE"});
  } catch (error) {
    finishRequestActivity(activity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error)});
    throw error;
  }
  config.characters = result.characters || result.presets || config.characters || [];
  config.presets = result.presets || config.characters;
  const fallback = findCharacterPreset(config.defaults?.character_name) || config.characters[0];
  fillPresetOptions(config.characters, fallback?.id || "");
  fillCharacterOptions(config.characters, fallback?.name || "");
  fillModelDirOptions(config.characters, fallback?.onnx_model_dir || "");
  if (fallback) {
    applyCharacterPreset(fallback.id || fallback.name, false);
  } else {
    updatePresetHint();
  }
  finishRequestActivity(activity, {status: "ok", message: t("presetDeleted", {name: preset.label || preset.name}), bytes: jsonByteSize(result)});
  appendLog(t("presetDeleted", {name: preset.label || preset.name}), result);
  return result;
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
      refreshMemoryPolicy(),
      refreshStatus(),
      refreshListenConfig(),
    ]);
    const failures = results.filter((result) => result.status === "rejected");
    if (failures.length) {
      appendLog(t("refreshFailed", {
        message: failures.map((result) => result.reason?.message || String(result.reason)).join("; "),
      }));
    }
    const [health, runtime, memory, status, listen] = results.map((result) => (
      result.status === "fulfilled" ? result.value : null
    ));
    return {health, runtime, memory, status, listen};
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
  const endpoint = config.endpoints.runtime_configure;
  const activity = startRequestActivity({
    endpoint,
    mode: "direct",
    title: endpoint,
    message: mode,
    category: "direct",
  });
  let result;
  try {
    result = await apiJson(endpoint, {
      method: "POST",
      body: JSON.stringify({mode, unload_sessions: unloadSessions}),
    });
  } catch (error) {
    finishRequestActivity(activity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error)});
    throw error;
  }
  finishRequestActivity(activity, {status: "ok", message: t("runtimeConfigured", {mode}), bytes: jsonByteSize(result)});
  appendLog(t("runtimeConfigured", {mode}), result);
  setPreparedBadge(preparedStateAfterRuntime(result));
  await refreshAll();
}

async function runMemoryAction(action, successKey) {
  ensureConfig();
  const endpoint = config.endpoints.runtime_memory_action || "/runtime/memory/action";
  const activity = startRequestActivity({
    endpoint,
    mode: "direct",
    title: endpoint,
    message: action,
    category: "direct",
  });
  let result;
  try {
    result = await apiJson(endpoint, {
      method: "POST",
      body: JSON.stringify({action}),
    });
  } catch (error) {
    finishRequestActivity(activity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error)});
    throw new Error(t("memoryActionFailed", {message: error.message || String(error)}));
  }
  finishRequestActivity(activity, {status: "ok", message: t(successKey), bytes: jsonByteSize(result)});
  appendLog(t(successKey), result);
  renderMemoryPolicy(result);
  if (action === "release_idle_sessions") {
    setPreparedBadge("not_loaded");
  }
  await refreshAll();
  return result;
}

async function refreshMemory(button) {
  const endpoint = config?.endpoints?.runtime_memory || "/runtime/memory";
  const activity = startRequestActivity({endpoint, mode: "direct", title: endpoint, message: t("refreshMemory"), category: "direct"});
  try {
    const result = await refreshMemoryPolicy();
    finishRequestActivity(activity, {status: "ok", message: t("refreshMemory"), bytes: jsonByteSize(result)});
    return result;
  } catch (error) {
    finishRequestActivity(activity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error)});
    throw error;
  }
}

async function releaseIdleSessions() {
  return runMemoryAction("release_idle_sessions", "memoryReleaseDone");
}

async function clearMemoryReferenceCache() {
  return runMemoryAction("clear_reference_cache", "memoryCacheCleared");
}

async function applyListen() {
  ensureConfig();
  const endpoint = config.endpoints.server_restart || "/server/restart";
  const payload = {
    host: el("listenHost").value,
    port: Number(el("listenPort").value || 0),
    runtime: el("runtimeMode").value || config?.listen?.runtime || config?.defaults?.runtime_mode || "cuda",
  };
  if (!Number.isInteger(payload.port) || payload.port < 0 || payload.port > 65535) {
    throw new Error(t("listenRestartFailed", {message: "invalid port"}));
  }
  const current = config.listen || {};
  if (payload.host === current.host && payload.port === Number(current.port || 0)) {
    appendLog(t("listenUnchanged", {host: payload.host, port: payload.port}), {unchanged: true});
    listenDirty = false;
    renderListenConfig(config.listen, true);
    return;
  }
  const activity = startRequestActivity({endpoint, mode: "direct", title: endpoint, category: "direct"});
  let result;
  try {
    result = await apiJson(endpoint, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (error) {
    finishRequestActivity(activity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error)});
    if (String(error.message || "").includes("busy") || String(error.message || "").includes("active")) {
      throw new Error(t("listenBusy"));
    }
    throw new Error(t("listenRestartFailed", {message: error.message || error}));
  }
  finishRequestActivity(activity, {status: "restarting", state: "warn", message: result.message || "restarting", bytes: jsonByteSize(result)});
  listenDirty = false;
  appendLog(t("listenRestarting", {host: payload.host, port: payload.port}), result);
  setRequestBadge("requestStarted", "warn", {format: `${payload.host}:${payload.port}`});
  if (activeRefreshTimer) {
    clearInterval(activeRefreshTimer);
    activeRefreshTimer = null;
  }
  setTimeout(() => {
    const target = result.lan_urls?.[0] || result.local_url;
    if (target && target !== "pending") {
      window.location.href = target;
    }
  }, 2800);
}

async function loadCharacter() {
  ensureConfig();
  const payload = loadCharacterPayload();
  if (!payload.character_name || !payload.onnx_model_dir || !payload.language) {
    throw new Error(t("loadFieldsRequired"));
  }
  const endpoint = config.endpoints.load_character;
  const activity = startRequestActivity({
    endpoint,
    mode: "direct",
    title: endpoint,
    message: payload.character_name,
    category: "direct",
  });
  let result;
  try {
    result = await apiJson(endpoint, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (error) {
    finishRequestActivity(activity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error)});
    throw error;
  }
  finishRequestActivity(activity, {status: "ok", message: t("loadSuccess"), bytes: jsonByteSize(result)});
  appendLog(t("loadSuccess"), result);
  setPreparedBadge("model_loaded");
  await refreshRuntime();
}

async function setReference() {
  ensureConfig();
  const payload = referencePayload();
  if (!payload.character_name || !payload.audio_path || !payload.audio_text || !payload.language) {
    throw new Error(t("referenceFieldsRequired"));
  }
  const endpoint = config.endpoints.set_reference_audio;
  const activity = startRequestActivity({
    endpoint,
    mode: "direct",
    title: endpoint,
    message: payload.character_name,
    category: "direct",
  });
  let result;
  try {
    result = await apiJson(endpoint, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (error) {
    finishRequestActivity(activity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error)});
    throw error;
  }
  finishRequestActivity(activity, {status: "ok", message: t("referenceSuccess"), bytes: jsonByteSize(result)});
  appendLog(t("referenceSuccess"), result);
  setPreparedBadge("ready");
  await refreshRuntime();
}

async function clearReferenceCache() {
  ensureConfig();
  const endpoint = config.endpoints.clear_reference_audio_cache || "/clear_reference_audio_cache";
  const activity = startRequestActivity({endpoint, mode: "direct", title: endpoint, category: "direct"});
  let result;
  try {
    result = await apiJson(endpoint, {
      method: "POST",
      body: "{}",
    });
  } catch (error) {
    finishRequestActivity(activity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error)});
    throw error;
  }
  finishRequestActivity(activity, {status: "ok", message: t("cacheCleared"), bytes: jsonByteSize(result)});
  appendLog(t("cacheCleared"), result);
  setPreparedBadge("ready");
}

async function restoreDefaults() {
  ensureConfig();
  stopProgressPolling();
  activeSynthesisInFlight = false;
  activeJobInFlight = false;
  fillDefaults(config.defaults);
  applyCharacterPreset(config.defaults.character_name);
  renderReaderConfig(readerConfigForCurrentSelection());
  setPreparedBadge("not_loaded");
  setRequestBadge("requestIdle", "muted");
  setRequestSummary();
  resetProgressView();
  appendLog(t("defaultsRestored"));
  updateActionAvailability();
}

async function prepareCharacter() {
  await loadCharacter();
  await setReference();
  setRequestBadge("preparedReady", "ok");
}

async function generateAudio() {
  ensureConfig();
  stopProgressPolling();
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
  activeSynthesisInFlight = true;
  updateActionAvailability();
  clearAudio();
  if (!activeJobTimer) {
    clearJobView();
  }
  setPreparedBadge("busy");
  appendLog(t("requestStarted", {format: endpoint.format}));
  setRequestBadge("requestStarted", "warn", {format: endpoint.format});
  const progressContext = {
    mode,
    modeLabel: endpoint.format,
    parallel: {enabled: false},
    progress: initialProgressForPayload(payload, "requesting"),
  };
  const activity = startRequestActivity({
    endpoint: endpoint.path,
    mode,
    title: endpoint.path,
    message: endpoint.format,
    category: activityCategoryForMode(mode, endpoint.path),
    progress: progressContext.progress,
  });
  resetProgressView(progressContext);
  if (["legado-stream", "stream-wav"].includes(mode) && canUseGetStream(payload)) {
    const streamUrl = streamUrlForEndpoint(endpoint.path, payload);
    setAudioUrl(streamUrl, endpoint.filename);
    activeSynthesisInFlight = true;
    activeAudioActivity = activity;
    setRequestSummary({mode, bytes: "stream", elapsed: "live", format: "audio/wav"});
    setRequestBadge("requestStarted", "warn", {format: endpoint.format});
    startProgressPolling(progressContext);
    el("audioPlayer").play().catch(() => {});
    refreshStatus().catch((error) => appendLog(t("refreshFailed", {message: error.message || error})));
    return;
  }
  const started = performance.now();
  startProgressPolling(progressContext);
  let result;
  try {
    result = await apiBlob(endpoint.path, payload);
  } catch (error) {
    finishRequestActivity(activity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error), progress: lastProgressContext?.progress || progressContext.progress});
    throw error;
  } finally {
    stopProgressPolling();
    activeSynthesisInFlight = false;
    updateActionAvailability();
  }
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
  updateProgressView({
    ...(lastProgressContext?.progress || progressContext.progress),
    stage: "completed",
    completed_chars: payload.text.length,
    total_chars: payload.text.length,
    completed_segments: estimatedSegmentCount(payload.text, payload.split_sentence),
    total_segments: estimatedSegmentCount(payload.text, payload.split_sentence),
    generated_wav_bytes: mode === "raw" ? 0 : result.blob.size,
    generated_pcm_bytes: mode === "raw" ? result.blob.size : (lastProgressContext?.progress?.generated_pcm_bytes || 0),
    elapsed_seconds: Number(elapsed),
    estimated_remaining_seconds: 0,
    percent: 100,
  }, progressContext);
  finishRequestActivity(activity, {
    status: result.status || "ok",
    state: "ok",
    message: endpoint.format,
    bytes: result.blob.size,
    progress: lastProgressContext?.progress || progressContext.progress,
  });
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
  if (activeJobTimer) {
    throw new Error(t("jobAlreadyActive"));
  }
  const payload = selectedJobPayload();
  ensureTextPayload(payload);
  activeJobInFlight = true;
  updateActionAvailability();
  clearAudio();
  clearJobView();
  el("jobBox").classList.remove("hidden");
  setRequestBadge("activityBusy", "warn");
  resetProgressView({
    mode: "job",
    modeLabel: t("modeJob"),
    parallel: currentParallelSelection(),
    progress: initialProgressForPayload(payload, "submitting"),
  });
  activeJobActivity = startRequestActivity({
    endpoint: config.endpoints.job_submit,
    mode: "job",
    title: config.endpoints.job_submit,
    message: t("modeJob"),
    category: "job",
    progress: lastProgressContext?.progress,
    parallel: currentParallelSelection(),
  });
  let result;
  try {
    result = await apiJson(config.endpoints.job_submit, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (error) {
    finishRequestActivity(activeJobActivity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error), progress: lastProgressContext?.progress, parallel: currentParallelSelection()});
    activeJobActivity = null;
    activeJobInFlight = false;
    updateActionAvailability();
    throw error;
  }
  const jobId = result.job_id;
  el("jobId").textContent = jobId;
  updateJobView(result.job || {status: "queued", stage: "queued", message: "Queued for synthesis."});
  setRequestSummary({mode: "job", bytes: "-", elapsed: "-", format: "job"});
  setRequestBadge("jobSubmitted", "warn", {jobId});
  appendLog(t("jobSubmitted", {jobId}), result.job);
  pollJob(jobId);
  activeJobInFlight = false;
  updateActionAvailability();
}

function updateJobActivity(job) {
  if (!activeJobActivity?.activityId || !job) {
    return;
  }
  const status = job.status || "running";
  const terminal = ["completed", "failed", "cancelled"].includes(status);
  const state = status === "completed" ? "ok" : (status === "failed" ? "error" : (status === "cancelled" ? "warn" : "running"));
  const statusState = state === "running" ? "warn" : state;
  const jobId = job.job_id || el("jobId").textContent.trim();
  const endpoint = jobId && jobId !== "-"
    ? config.endpoints.job_status.replace("{job_id}", jobId)
    : config.endpoints.job_submit;
  const progress = job.progress || lastProgressContext?.progress || null;
  const bytes = job.output_bytes || progress?.generated_wav_bytes || progress?.generated_pcm_bytes || null;
  const elapsed = (performance.now() - activeJobActivity.started) / 1000;
  journalActivity("job", {
    endpoint,
    mode: "job",
    title: endpoint,
    message: job.message || job.error_detail || job.stage || status,
    state,
    status,
    status_state: statusState,
    elapsed_seconds: elapsed,
    bytes,
    progress,
    parallel: job.parallel || currentParallelSelection(),
    error: job.error_detail || null,
  }, activeJobActivity.activityId);
  if (terminal) {
    activeJobActivity = null;
  }
}

function updateJobView(job) {
  el("jobStatus").textContent = stageLabel(job.status);
  el("jobStage").textContent = stageLabel(job.stage);
  el("jobMessage").textContent = localizedProgressMessage(job.progress || {stage: job.stage, message: job.message}, job.error_detail || job.message || "-");
  const context = {
    mode: "job",
    modeLabel: t("modeJob"),
    parallel: job.parallel || currentParallelSelection(),
    progress: job.progress || null,
  };
  setProgressContext(context);
  updateProgressView(job.progress || initialProgressForPayload(selectedPayload(), job.stage || "queued"), context);
  updateJobActivity(job);
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
        updateActionAvailability();
        await refreshStatus();
        await refreshRuntime();
      } else if (["failed", "cancelled"].includes(job.status)) {
        clearInterval(activeJobTimer);
        activeJobTimer = null;
        setRequestBadge("jobFailed", job.status === "failed" ? "error" : "warn", {status: job.status, jobId});
        appendLog(t("jobFailed", {status: job.status, jobId}), job);
        updateActionAvailability();
      }
    } catch (error) {
      clearInterval(activeJobTimer);
      activeJobTimer = null;
      finishRequestActivity(activeJobActivity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error), progress: lastProgressContext?.progress, parallel: currentParallelSelection()});
      activeJobActivity = null;
      setRequestBadge("jobPollingFailed", "error", {message: error.message});
      appendLog(t("jobPollingFailed", {message: error.message}));
      updateActionAvailability();
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
  const endpoint = config.endpoints.job_cancel.replace("{job_id}", jobId);
  const activity = startRequestActivity({endpoint, mode: "job", title: endpoint, category: "job", parallel: currentParallelSelection()});
  let result;
  try {
    result = await apiJson(endpoint, {method: "POST", body: "{}"});
  } catch (error) {
    finishRequestActivity(activity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error)});
    throw error;
  }
  finishRequestActivity(activity, {status: result.status || "cancel_requested", state: "warn", message: result.message || t("jobCancelRequested", {jobId}), bytes: jsonByteSize(result), progress: result.progress, parallel: result.parallel});
  appendLog(t("jobCancelRequested", {jobId}), result);
  updateJobView(result);
  setRequestBadge("jobFailed", "warn", {status: result.status || "cancelled", jobId});
  if (["cancelled", "failed", "completed"].includes(result.status) && activeJobTimer) {
    clearInterval(activeJobTimer);
    activeJobTimer = null;
  }
  updateActionAvailability();
  await refreshStatus();
}

async function stopTts() {
  ensureConfig();
  const endpoint = config.endpoints.stop || "/stop";
  const activity = startRequestActivity({endpoint, mode: "direct", title: endpoint, category: "direct"});
  let result = null;
  try {
    result = await apiJson(endpoint, {method: "POST", body: "{}"});
    finishRequestActivity(activity, {status: "ok", state: "warn", message: t("stopRequested"), bytes: jsonByteSize(result)});
  } catch (error) {
    finishRequestActivity(activity, {status: "error", state: "error", message: error.message || String(error), error: error.message || String(error)});
    throw error;
  } finally {
    abortActiveTtsRequest();
    stopProgressPolling();
    activeSynthesisInFlight = false;
    activeJobInFlight = false;
    if (activeAudioActivity) {
      finishRequestActivity(activeAudioActivity, {status: "stopped", state: "warn", message: t("stopRequested"), progress: lastProgressContext?.progress});
      activeAudioActivity = null;
    }
    if (lastRequestSummary?.elapsed === "live") {
      clearAudio();
    } else {
      el("audioPlayer").pause();
    }
    updateActionAvailability();
  }
  appendLog(t("stopRequested"), result);
  setRequestBadge("stopRequested", "warn");
  await refreshStatus();
}

async function clearLog() {
  el("logBox").textContent = "";
  clearActivityJournal();
}

function flashCopied(button) {
  if (!button) return;
  window.clearTimeout(Number(button.dataset.copyTimer || 0));
  if (button.children.length) {
    button.classList.add("copy-flash");
    const timer = window.setTimeout(() => {
      button.classList.remove("copy-flash");
      button.dataset.copyTimer = "0";
    }, 900);
    button.dataset.copyTimer = String(timer);
    return;
  }
  const original = button.textContent;
  button.textContent = t("copiedShort");
  const timer = window.setTimeout(() => {
    button.textContent = original;
    button.dataset.copyTimer = "0";
  }, 1200);
  button.dataset.copyTimer = String(timer);
}

async function copyText(value, label, button = null) {
  const text = validCopyValue(value);
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      appendLog(t("copySuccess", {label}));
      flashCopied(button);
      return;
    }
  } catch (error) {
    // Fall through to the legacy path for non-secure LAN origins.
  }
  try {
    const textArea = document.createElement("textarea");
    textArea.value = text;
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
  flashCopied(button);
}

function extractLanValue() {
  return config?.access?.lan_urls?.[0] || null;
}

async function copyApiBase(button) {
  await copyText(el("apiBase").textContent.trim(), t("apiLabel"), button);
}

async function copyLocalUrl(button) {
  await copyText(el("localUrl").textContent.trim(), t("localLabel"), button);
}

async function copyLanUrl(button) {
  const value = extractLanValue();
  if (!value) {
    throw new Error(t("noLanDetected"));
  }
  await copyText(value, t("lanLabel"), button);
}

async function copyReaderApiBase(button) {
  const reader = readerConfigForCurrentSelection();
  await copyText(reader?.urls?.local_api_base_url || reader?.urls?.api_base_url, t("readerApiBaseLabel"), button);
}

async function copyReaderLanBase(button) {
  await copyText(readerConfigForCurrentSelection()?.urls?.lan_api_base_url, t("readerLanBaseLabel"), button);
}

async function copyLegadoBufferedUrl(button) {
  await copyText(readerConfigForCurrentSelection()?.urls?.legado_buffered_url, t("readerBufferedLabel"), button);
}

async function copyLegadoStreamUrl(button) {
  await copyText(readerConfigForCurrentSelection()?.urls?.legado_stream_url, t("readerStreamLabel"), button);
}

async function copyLegadoJsLib(button) {
  await copyText(readerConfigForCurrentSelection()?.templates?.recommended_jslib, t("readerJsLibLabel"), button);
}

async function copyLegadoJson(button) {
  const template = readerConfigForCurrentSelection()?.templates?.recommended_json;
  await copyText(template && Object.keys(template).length ? JSON.stringify(template, null, 2) : "", t("readerJsonLabel"), button);
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
  setButtonBusy(button, true);
  try {
    await action(button);
  } catch (error) {
    appendLog(error.message || String(error));
    const isCopyButton = button.id?.startsWith("copy")
      || button.classList.contains("address-chip")
      || button.classList.contains("lan-pill");
    if (!isCopyButton) {
      setRequestBadge("requestError", "error", {message: error.message || "error"});
      markProgressFailed(error.message || String(error));
    }
    if (!isCopyButton && lastPreparedState === "busy") {
      setPreparedBadge("error");
    }
  } finally {
    setButtonBusy(button, false);
    updateActionAvailability();
  }
}

function bindAudioEvents() {
  const player = el("audioPlayer");
  player.addEventListener("playing", () => {
    if (lastRequestSummary?.elapsed === "live") {
      if (activeAudioActivity) {
        journalActivity(activityCategoryForMode(lastProgressContext?.mode, player.currentSrc), {
          state: "running",
          status: "playing",
          status_state: "warn",
          message: lastRequestSummary.format || "audio/wav",
          progress: lastProgressContext?.progress,
        }, activeAudioActivity.activityId);
      }
      setRequestBadge("requestStarted", "warn", {format: lastRequestSummary.format});
    }
  });
  player.addEventListener("ended", () => {
    if (lastRequestSummary?.elapsed === "live") {
      stopProgressPolling();
      activeSynthesisInFlight = false;
      if (activeAudioActivity) {
        finishRequestActivity(activeAudioActivity, {status: "completed", state: "ok", message: lastRequestSummary.format || "audio/wav", progress: lastProgressContext?.progress});
        activeAudioActivity = null;
      }
      setRequestBadge("requestReady", "ok", {format: lastRequestSummary.format});
      setPreparedBadge("ready");
      updateActionAvailability();
      refreshStatus().catch(() => {});
    }
  });
  player.addEventListener("error", () => {
    if (player.currentSrc) {
      stopProgressPolling();
      activeSynthesisInFlight = false;
      if (activeAudioActivity) {
        finishRequestActivity(activeAudioActivity, {status: "error", state: "error", message: "audio playback failed", error: "audio playback failed", progress: lastProgressContext?.progress});
        activeAudioActivity = null;
      }
      setRequestBadge("requestError", "error", {message: "audio playback failed"});
      setPreparedBadge("error");
      updateActionAvailability();
    }
  });
}

async function init() {
  config = await apiJson("/ui/config", {method: "GET"});
  setLanguage(detectInitialLanguage(), false);
  fillDefaults(config.defaults);
  applyCharacterPreset(config.defaults.character_name);
  renderAccess(config.access);
  renderListenConfig(config.listen);
  renderReaderConfig(readerConfigForCurrentSelection());
  clearAudio();
  clearJobView();
  setRequestSummary();
  setPreparedBadge("not_loaded");

  el("refreshAllBtn").addEventListener("click", () => withButton(el("refreshAllBtn"), refreshAll));
  el("applyRuntimeBtn").addEventListener("click", () => withButton(el("applyRuntimeBtn"), applyRuntime));
  el("applyListenBtn").addEventListener("click", () => withButton(el("applyListenBtn"), applyListen));
  el("refreshMemoryBtn").addEventListener("click", () => withButton(el("refreshMemoryBtn"), refreshMemory));
  el("releaseSessionsBtn").addEventListener("click", () => withButton(el("releaseSessionsBtn"), releaseIdleSessions));
  el("clearMemoryCacheBtn").addEventListener("click", () => withButton(el("clearMemoryCacheBtn"), clearMemoryReferenceCache));
  el("loadCharacterBtn").addEventListener("click", () => withButton(el("loadCharacterBtn"), loadCharacter));
  el("setReferenceBtn").addEventListener("click", () => withButton(el("setReferenceBtn"), setReference));
  el("prepareBtn").addEventListener("click", () => withButton(el("prepareBtn"), prepareCharacter));
  el("generateBtn").addEventListener("click", () => withButton(el("generateBtn"), generateAudio));
  el("stopBtn").addEventListener("click", () => withButton(el("stopBtn"), stopTts));
  el("cancelJobBtn").addEventListener("click", () => withButton(el("cancelJobBtn"), cancelJob));
  el("clearJobBtn").addEventListener("click", () => clearJobView());
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
  el("copyReaderApiBtn").addEventListener("click", () => withButton(el("copyReaderApiBtn"), copyReaderApiBase));
  el("copyReaderLanBtn").addEventListener("click", () => withButton(el("copyReaderLanBtn"), copyReaderLanBase));
  el("copyLegadoBufferedBtn").addEventListener("click", () => withButton(el("copyLegadoBufferedBtn"), copyLegadoBufferedUrl));
  el("copyLegadoStreamBtn").addEventListener("click", () => withButton(el("copyLegadoStreamBtn"), copyLegadoStreamUrl));
  el("copyLegadoJsLibBtn").addEventListener("click", () => withButton(el("copyLegadoJsLibBtn"), copyLegadoJsLib));
  el("copyLegadoJsonBtn").addEventListener("click", () => withButton(el("copyLegadoJsonBtn"), copyLegadoJson));
  el("copyReaderFieldNameBtn").addEventListener("click", () => withButton(el("copyReaderFieldNameBtn"), (button) => copyReaderField("name", button)));
  el("copyReaderFieldUrlBtn").addEventListener("click", () => withButton(el("copyReaderFieldUrlBtn"), (button) => copyReaderField("url", button)));
  el("copyReaderFieldContentTypeBtn").addEventListener("click", () => withButton(el("copyReaderFieldContentTypeBtn"), (button) => copyReaderField("contentType", button)));
  el("copyReaderFieldConcurrentRateBtn").addEventListener("click", () => withButton(el("copyReaderFieldConcurrentRateBtn"), (button) => copyReaderField("concurrentRate", button)));
  el("autoRefresh").addEventListener("change", scheduleAutoRefresh);
  el("inputText").addEventListener("input", updateTextStats);
  el("textFileInput").addEventListener("change", textFileLoadFromEvent);
  el("clearTextFileBtn").addEventListener("click", () => withButton(el("clearTextFileBtn"), () => clearTextFileSelection()));
  el("presetSelect").addEventListener("change", updatePresetHint);
  el("applyPresetBtn").addEventListener("click", () => withButton(el("applyPresetBtn"), () => applyCharacterPreset(el("presetSelect").value || el("characterName").value, true)));
  el("savePresetBtn").addEventListener("click", () => withButton(el("savePresetBtn"), saveCurrentPreset));
  el("deletePresetBtn").addEventListener("click", () => withButton(el("deletePresetBtn"), deleteSelectedPreset));
  el("refreshPresetsBtn").addEventListener("click", () => withButton(el("refreshPresetsBtn"), refreshCharacterPresets));
  el("scanConversionBtn").addEventListener("click", () => withButton(el("scanConversionBtn"), scanConversion));
  el("startConversionBtn").addEventListener("click", () => withButton(el("startConversionBtn"), startConversion));
  el("refreshConversionBtn").addEventListener("click", () => withButton(el("refreshConversionBtn"), refreshConversionJob));
  el("characterName").addEventListener("input", () => {
    const match = findCharacterPreset(el("characterName").value);
    if (match) {
      if (match.id) {
        el("presetSelect").value = match.id;
      }
      fillModelDirOptions(config?.characters || [], match.onnx_model_dir || el("modelDir").value);
      if (!el("modelDir").value && match.onnx_model_dir) {
        el("modelDir").value = match.onnx_model_dir;
      }
      fillReferenceOptions(match, el("referenceAudio").value || match.reference_audio_path || "");
      if (match.language) {
        el("language").value = match.language;
      }
      updatePresetHint();
    }
    renderReaderConfig(readerConfigForCurrentSelection());
    setPreparedBadge("reload");
  });
  el("modelDir").addEventListener("input", () => {
    const match = (config?.characters || []).find((character) => character.onnx_model_dir === el("modelDir").value);
    if (match) {
      if (match.id) {
        el("presetSelect").value = match.id;
      }
      el("characterName").value = match.name || el("characterName").value;
      fillReferenceOptions(match, el("referenceAudio").value);
      updatePresetHint();
    } else {
      setPreparedBadge("reload");
    }
  });
  el("referenceAudio").addEventListener("input", () => {
    applyReferenceOption(el("referenceAudio").value);
    renderReaderConfig(readerConfigForCurrentSelection());
    setPreparedBadge("reload");
  });
  el("listenHost").addEventListener("change", () => {
    listenDirty = true;
  });
  el("listenPort").addEventListener("input", () => {
    listenDirty = true;
  });
  el("parallelEnabled").addEventListener("change", () => {
    updateModeControls();
    updateCurrentProgressParallelSelection();
  });
  el("parallelWorkers").addEventListener("input", updateCurrentProgressParallelSelection);
  el("parallelWorkers").addEventListener("change", () => {
    normalizeParallelWorkersField();
    updateCurrentProgressParallelSelection();
  });
  el("endpointMode").addEventListener("change", updateModeControls);
  el("runtimeMode").addEventListener("change", () => {
    setBadge(el("runtimeBadge"), el("runtimeMode").value, "muted");
    updateModeControls();
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
