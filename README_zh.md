# Genie-TTS Windows 整合包

[简体中文](./README_zh.md) | [English](./README.md)

本仓库维护的是位于 `E:\Genie-TTS` 的自包含 Genie-TTS CPU/GPU Windows 整合包。它不只是源码目录：正常形态下，这个目录应同时携带包内 Python 运行时、虚拟环境、ONNX Runtime CPU/GPU 包、包内 CUDA/cuDNN 用户态 DLL、模型资源、API 服务脚本、示例和验证工具。

当前产品目标是一个可本机或局域网调用的 FastAPI TTS 服务，用于有声书、小说、文档朗读等长时间听书场景。CPU 推理必须持续作为 fallback 可用；CUDA 推理由包内 ONNX Runtime execution provider 选择和加载。

当前阅读器结论：`/tts/legado.wav` 的 `mode=buffered` 是 Android/Legado 稳定听书路径；`mode=stream` 保留为低延迟实验路径，以及给能正确处理 chunked WAV 的客户端使用。

## 包内运行规则

- 验证和本地工具统一使用 `E:\Genie-TTS\Runtime\.venv\Scripts\python.exe`。
- 正常运行不要依赖系统 Python、全局 pip、全局 CUDA Toolkit、用户 `PATH` 或机器级环境变量。
- 不要把 `Runtime`、`GenieData`、`CharacterModels`、`test`、`UserData` 加入 git；这些是包内运行时、模型或输出产物。
- CUDA 支持应来自包内运行时和包内 NVIDIA wheel DLL；NVIDIA 显卡驱动和 Windows 系统 DLL 属于系统/驱动边界。
- 不要仅因为 `CUDAExecutionProvider` 出现在 available providers 中就宣称 GPU TTS 完成。必须看 `/runtime` 中各个已加载 ONNX session 的实际 provider 列表。

## 快速开始

一键启动本地 WebUI 和局域网可访问 API：

```cmd
E:\Genie-TTS\go-webui.bat
```

启动器使用 `E:\Genie-TTS\Runtime\.venv\Scripts\python.exe`，默认 `cuda`、
监听 `0.0.0.0`，会打开 `http://127.0.0.1:<port>/ui`，并在终端打印当前实
际局域网 IPv4 WebUI 地址。命令行参数可直接透传，例如
`go-webui.bat --runtime cpu --port 8001 --no-open`。

启动本机 CUDA API：

```powershell
E:\Genie-TTS\Scripts\start-internal-api.ps1 -Runtime cuda -HostName 127.0.0.1 -Port 8000
```

启动局域网可访问 CUDA API：

```powershell
E:\Genie-TTS\Scripts\start-internal-api.ps1 -Runtime cuda -HostName 0.0.0.0 -Port 8000
```

CPU fallback 使用 `-Runtime cpu`。运行时模式应在加载角色模型前选择。

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

## 主要端点

| 端点 | 用途 |
| --- | --- |
| `GET /health` | 进程健康检查。 |
| `GET /ui` | 浏览器推理面板，用于加载角色、设置 reference、TTS 和 job 测试。 |
| `GET /ui/config` | WebUI 默认参数，以及当前本机/局域网访问地址。 |
| `GET /runtime` | ONNX Runtime 版本、选中 providers、可用 providers、已加载角色和实际 session providers。 |
| `POST /runtime/configure` | 为后续加载的 ONNX sessions 选择 provider。 |
| `GET /status` | busy 状态、当前 TTS session、队列/运行中 job、最近 reader 请求诊断。 |
| `POST /load_character` | 加载/注册 ONNX 角色模型。 |
| `POST /set_reference_audio` | 为角色设置并预处理参考音频和文本。 |
| `POST /tts` | raw PCM streaming 兼容别名。 |
| `POST /tts/raw` | 低延迟 raw PCM S16LE 流。 |
| `POST /tts/wav` | 推理完成后返回完整 WAV。 |
| `GET/POST /tts/stream.wav` | 通用 WAV stream 端点。 |
| `GET/POST /tts/legado.wav` | 阅读器/Legado 兼容 WAV 端点，支持 `mode=stream` 和 `mode=buffered`。 |
| `POST /jobs/tts` | 提交长文本 TTS job，并通过 `/jobs` 轮询/下载。 |
| `POST /stop` | 停止当前 TTS 任务。 |
| `POST /clear_reference_audio_cache` | 清理参考音频预处理缓存。 |

详细请求/响应合同见 [Docs/API-Service.md](./Docs/API-Service.md)。

## 音频格式

- Raw PCM：`POST /tts/raw` 返回 `application/octet-stream`，响应头包含 `X-Genie-Audio-Format: pcm_s16le`，音频为 32000 Hz、mono、16-bit little-endian PCM。
- Stream WAV：`/tts/legado.wav` 或 `/tts/stream.wav` 的 `mode=stream` 会立即返回 `audio/wav`，先发送 WAV header，再通过 HTTP chunk 追加生成的 PCM。启动延迟更低，但部分 Android media stack 不接受响应开始时未知最终长度的 chunked WAV。
- Buffered complete WAV：`/tts/legado.wav` 的 `mode=buffered` 会等待内存中合成完成，再返回普通完整 `audio/wav`。这是当前 Legado 稳定阅读模式。
- Complete WAV：`POST /tts/wav` 同样返回完整 `audio/wav`，适合需要普通文件响应的客户端。

## 验证命令

文档或低风险维护改动后运行：

```powershell
git -C E:\Genie-TTS diff --check
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m compileall E:\Genie-TTS\src
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m py_compile "E:\Genie-TTS\Tutorial\English\API Server Tutorial.py" "E:\Genie-TTS\Examples\api_client.py" "E:\Genie-TTS\Examples\api_job_client.py"
```

声称 runtime 健康前运行：

```powershell
E:\Genie-TTS\Scripts\verify-internal-runtime.ps1
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m pip check
```

改动 API、server、runtime 或脚本后运行真实 HTTP 验证：

```powershell
E:\Genie-TTS\Scripts\verify-internal-api.ps1 -Runtime cuda
E:\Genie-TTS\Scripts\verify-legado-stream-api.ps1 -Runtime cuda
E:\Genie-TTS\Scripts\verify-job-api.ps1 -Runtime cuda
```

验证脚本默认在 `test` 下创建临时文件，并会清理自己的输出，除非显式要求保留。不要删除历史测试产物，除非能证明它们是当前验证运行生成的。

## 示例

- `Examples\api_client.py`：加载 `feibi`、设置 reference、调用 `/tts/raw`、`/tts/legado.wav`、`/tts/legado.wav?mode=buffered` 和 `/tts/wav`。
- `Examples\api_job_client.py`：提交 `/jobs/tts`、轮询 `/jobs/{job_id}`、下载 `/jobs/{job_id}/wav`。
- `Examples\legado_http_tts.json`：Legado streaming WAV httpTTS 模板。
- `Examples\legado_http_tts_buffered.json`：Legado buffered complete WAV httpTTS 模板，当前推荐给 Android/Legado 稳定阅读。

对已经启动的本机服务运行示例客户端：

```powershell
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe E:\Genie-TTS\Examples\api_client.py --base-url http://127.0.0.1:8000
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe E:\Genie-TTS\Examples\api_job_client.py --base-url http://127.0.0.1:8000
```

## 文档地图

- [README.md](./README.md)：同一整合包的英文快速开始。
- [Docs/API-Service.md](./Docs/API-Service.md)：详细 API 合同、端点语义、响应头、错误行为和客户端示例。
- [Docs/Architecture.md](./Docs/Architecture.md)：当前模块边界、数据流和维护压力点。
- [Docs/Maintenance.md](./Docs/Maintenance.md)：验证链、发布检查、故障排查和清理规则。
- [AGENTS.md](./AGENTS.md)：未来 Codex/AI agent 在本仓库工作的执行准则。

## 开发注意事项

- `requirements.txt` 保持 CPU-friendly；包内 CUDA overlay 放在 `requirements-cuda.txt`。
- 保留现有 endpoint，除非已在 `Docs/API-Service.md` 中记录兼容迁移。
- 开发新功能时优先保持 CPU fallback、CUDA runtime 选择、`/runtime`、`/status`、job API 和 Legado buffered 兼容路径稳定。
- 不要在缺少 CPU/GPU baseline 和真实 TTS correctness 证明时深改 decoder loop、ONNX Runtime IO Binding、batching 或推理核心。
- 中文验证使用较长文本和 `split_sentence=true`。很短的短句不能覆盖听书/阅读路径。

## 上游来源

Genie-TTS 基于开源 GPT-SoVITS 生态，支持 GPT-SoVITS V2/V2ProPlus 风格 ONNX 模型，可用于日语、英语、中文和韩语推理。本仓库当前维护重点是本地 Windows 整合包，以及 API/runtime 的稳定性和可验证性，而不是通用 pip 安装包说明。
