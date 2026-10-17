# Genie-TTS-GPU 环境准备与首次合成

[中文](Quickstart.md) · [English](Quickstart.en.md) · [Project home](../README.md)

本页面向准备本地环境及接入 API 的用户。命令以 `E:\Genie-TTS` 为例，前提是包内 Python、依赖及模型已准备完成；本页不是自动安装脚本。

## 获取与准备

GitHub 仓库只包含源码、脚本、文档和示例。**下载源码不等于下载可直接运行的完整整合包**：
包内 Python、依赖、模型与参考音频需要自行准备；它们不进入 Git。
当前脚本以 `E:\Genie-TTS` 的 Windows 布局为例，完整要求见[维护说明](Maintenance.md)。
不要把未包含运行环境和模型的源码 ZIP 当作一键安装包。

## 包内运行规则

- 验证和本地工具统一使用 `E:\Genie-TTS\Runtime\.venv\Scripts\python.exe`。
- 正常运行不要依赖系统 Python、全局 pip、全局 CUDA Toolkit、用户 `PATH` 或机器级环境变量。
- 不要把 `Runtime`、`GenieData`、`CharacterModels`、`test`、`UserData` 加入 git；这些是包内运行时、模型或输出产物。
- CUDA 支持应来自包内运行时和包内 NVIDIA wheel DLL；NVIDIA 显卡驱动和 Windows 系统 DLL 属于系统/驱动边界。
- 不要仅因为 `CUDAExecutionProvider` 出现在 available providers 中就宣称 GPU TTS 完成。必须看 `/runtime` 中各个已加载 ONNX session 的实际 provider 列表。

## 快速开始

准备完成后，先显式选择 CPU 并仅监听本机：

```cmd
E:\Genie-TTS\go-webui.bat --host 127.0.0.1 --runtime cpu
```

启动器使用 `E:\Genie-TTS\Runtime\.venv\Scripts\python.exe`，打开实际端口的
`http://127.0.0.1:<port>/ui`。上面命令明确选择本机 CPU；不带参数运行时才默认请求
`cuda` 并监听 `0.0.0.0`。端口占用可能改用空闲端口，以终端输出为准；需要固定端口时用
`--port 8000 --strict-port`。`--no-open` 可关闭自动打开浏览器。

启动本机 CUDA API：

```powershell
E:\Genie-TTS\Scripts\start-internal-api.ps1 -Runtime cuda -HostName 127.0.0.1 -Port 8000
```

启动局域网可访问 CUDA API：

```powershell
E:\Genie-TTS\Scripts\start-internal-api.ps1 -Runtime cuda -HostName 0.0.0.0 -Port 8000
```

选择 CPU 使用 `-Runtime cpu`。运行时模式应在加载角色模型前选择。

加载默认中文验证角色 `feibi`：

```powershell
$base = 'http://127.0.0.1:8000'
$loadBody = @{
    character_name = 'feibi'
    onnx_model_dir = 'E:\Genie-TTS\CharacterModels\v2ProPlus\feibi\tts_models'
    language = 'Chinese'
} | ConvertTo-Json
Invoke-RestMethod -Uri "$base/load_character" -Method Post -ContentType 'application/json' -Body $loadBody
```

设置参考音频：

```powershell
$referenceBody = @{
    character_name = 'feibi'
    audio_path = 'E:\Genie-TTS\CharacterModels\v2ProPlus\feibi\prompt_wav\zh_vo_Main_Linaxita_2_1_10_26.wav'
    audio_text = '在此之前，请您务必继续享受旅居拉古那的时光。'
    language = 'Chinese'
} | ConvertTo-Json
Invoke-RestMethod -Uri "$base/set_reference_audio" -Method Post -ContentType 'application/json' -Body $referenceBody
```

通过 Legado 兼容端点生成完整 buffered WAV：

```powershell
New-Item -ItemType Directory -Force -Path E:\Genie-TTS\test | Out-Null
$ttsBody = @{
    character_name = 'feibi'
    text = '清晨的城市逐渐苏醒，街边的灯光还没有完全熄灭。她合上手里的书，抬头望向窗外，决定把今天的计划重新整理一遍。'
    split_sentence = $true
} | ConvertTo-Json
Invoke-WebRequest -Uri "$base/tts/legado.wav?wait_timeout=300&mode=buffered" -Method Post -ContentType 'application/json' -Body $ttsBody -OutFile E:\Genie-TTS\test\feibi-legado-buffered.wav
```

Android/Legado 使用时，先用 `-HostName 0.0.0.0` 启动服务，再替换 `Examples\legado_http_tts_buffered.json` 里的示例 IP，并优先使用 `/tts/legado.wav?wait_timeout=300&mode=buffered`。非 buffered 的 `/tts/legado.wav?wait_timeout=300` 会返回 chunked WAV，更适合低延迟测试或兼容该格式的播放器。

机器验证只能证明 API 行为、WAV 结构和 runtime/provider 状态正常；不能证明中文发音、断句和内容完整性正确。生成的中文音频仍需要用户试听或通过其他音频内容检查确认。


## 核对结果

先检查模型加载、参考音频与文本匹配，再生成完整 WAV 并试听，核对漏字、错读、断句与完整性。切换 CUDA 应在加载模型前完成，并在 `/runtime` 核对实际 session providers；仅看到可用 GPU 提供方不代表 GPU 合成正确。

详细请求语义见 [API 合同](API-Service.md)，问题按[故障排查](Troubleshooting.md)定位，维护者按[维护指南](Maintenance.md)执行验证。
