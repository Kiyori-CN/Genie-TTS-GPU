# Genie-TTS-GPU

A Windows speech workspace for local and LAN use, built on Genie-TTS and GPT-SoVITS with CPU/CUDA runtime selection, a WebUI, HTTP APIs, and long-form jobs.

[简体中文](./README_zh.md) | [English](./README.md)

Use it for audiobook, novel, and document narration through a local or LAN service. Prefer complete buffered WAV for readers; chunked stream WAV remains available for low-latency experiments and compatible clients.

## Start Here

- [Project tour (中文)](Docs/Showcase.md): actual WebUI captures, workflows, and evidence for repository-specific work.
- [API contract](Docs/API-Service.md): direct synthesis, long-form jobs, and reader response modes.
- [Architecture](Docs/Architecture.md): inference, job, provider, and client boundaries.
- [Maintenance](Docs/Maintenance.md): runtime checks and real synthesis validation.

![Actual WebUI from the public source revision](Docs/assets/showcase/webui-desktop.png)

The capture uses a local CPU configuration with no model loaded. It is not proof of GPU synthesis or speech quality.

## What the Repository Includes

Git contains source, scripts, documentation, and examples. **A source checkout is not a ready-to-run integration bundle.**
Prepare package-local Python, dependencies, model resources, and reference audio separately; they are not tracked in Git.
Current Windows examples use `E:\Genie-TTS`; see [maintenance](Docs/Maintenance.md) for the required layout.
Do not describe a source ZIP without runtimes and models as a one-click installer.

## Package Rules

- Use `E:\Genie-TTS\Runtime\.venv\Scripts\python.exe` for validation and local
  tooling.
- Do not depend on system Python, global pip, global CUDA Toolkit folders,
  user `PATH`, or machine-wide environment variables for normal operation.
- Do not add `Runtime`, `GenieData`, `CharacterModels`, `test`, or `UserData` to
  git. They are package-local runtime/model/output artifacts.
- CUDA support belongs in the package-local runtime. The NVIDIA display driver
  and Windows system DLLs remain OS/driver boundaries.
- Do not claim GPU TTS works only because `CUDAExecutionProvider` is listed as
  available. Check each loaded ONNX session's actual provider list from
  `/runtime`.

## Quick Start

Start the local WebUI and LAN-accessible API in one step:

```cmd
E:\Genie-TTS\go-webui.bat
```

The launcher uses `E:\Genie-TTS\Runtime\.venv\Scripts\python.exe`, defaults to
`cuda`, listens on `0.0.0.0`, opens `http://127.0.0.1:<port>/ui`, and prints the
current LAN IPv4 WebUI URL. Command-line overrides are passed through, for
example `go-webui.bat --runtime cpu --port 8001 --no-open`.

Start a local CUDA API server:

```powershell
E:\Genie-TTS\Scripts\start-internal-api.ps1 -Runtime cuda -HostName 127.0.0.1 -Port 8000
```

Start a LAN-accessible CUDA API server:

```powershell
E:\Genie-TTS\Scripts\start-internal-api.ps1 -Runtime cuda -HostName 0.0.0.0 -Port 8000
```

Use `-Runtime cpu` for the CPU fallback path. Runtime mode should be selected
before loading character models.

Load the default Chinese validation character `feibi`:

```powershell
$base = 'http://127.0.0.1:8000'
$loadBody = @{
    character_name = 'feibi'
    onnx_model_dir = 'E:\Genie-TTS\CharacterModels\v2ProPlus\feibi\tts_models'
    language = 'Chinese'
} | ConvertTo-Json
Invoke-RestMethod -Uri "$base/load_character" -Method Post -ContentType 'application/json' -Body $loadBody
```

Set the reference audio:

```powershell
$referenceBody = @{
    character_name = 'feibi'
    audio_path = 'E:\Genie-TTS\CharacterModels\v2ProPlus\feibi\prompt_wav\zh_vo_Main_Linaxita_2_1_10_26.wav'
    audio_text = '在此之前，请您务必继续享受旅居拉古那的时光。'
    language = 'Chinese'
} | ConvertTo-Json
Invoke-RestMethod -Uri "$base/set_reference_audio" -Method Post -ContentType 'application/json' -Body $referenceBody
```

Generate a complete buffered WAV through the Legado-compatible endpoint:

```powershell
New-Item -ItemType Directory -Force -Path E:\Genie-TTS\test | Out-Null
$ttsBody = @{
    character_name = 'feibi'
    text = '清晨的城市逐渐苏醒，街边的灯光还没有完全熄灭。她合上手里的书，抬头望向窗外，决定把今天的计划重新整理一遍。'
    split_sentence = $true
} | ConvertTo-Json
Invoke-WebRequest -Uri "$base/tts/legado.wav?wait_timeout=300&mode=buffered" -Method Post -ContentType 'application/json' -Body $ttsBody -OutFile E:\Genie-TTS\test\feibi-legado-buffered.wav
```

For Android/Legado, start the server with `-HostName 0.0.0.0`, replace the
placeholder IP in `Examples\legado_http_tts_buffered.json`, and use
`/tts/legado.wav?wait_timeout=300&mode=buffered` for the stable listening path.
The non-buffered `/tts/legado.wav?wait_timeout=300` path streams chunked WAV and
is useful when first-audio latency matters more than Android media compatibility.

Machine validation proves API behavior, WAV structure, and runtime/provider
state. It does not prove Chinese pronunciation, segmentation, or content
completeness. Generated Chinese audio still needs listening or another
audio-content inspection step.

## Main Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Process health check. |
| `GET /ui` | Browser inference panel for load/reference/TTS/job testing. |
| `GET /ui/config` | WebUI defaults plus current local and LAN access URLs. |
| `GET /runtime` | ONNX Runtime version, selected providers, available providers, loaded characters, and actual session providers. |
| `POST /runtime/configure` | Select providers for subsequently loaded ONNX sessions. |
| `GET /status` | Busy state, active TTS session, queued/running jobs, and recent reader request diagnostics. |
| `POST /load_character` | Load/register an ONNX character model. |
| `POST /set_reference_audio` | Set and preprocess reference audio/transcript for a character. |
| `POST /tts` | Compatibility alias for raw PCM streaming. |
| `POST /tts/raw` | Low-latency raw PCM S16LE stream. |
| `POST /tts/wav` | Complete WAV response after synthesis finishes. |
| `GET/POST /tts/stream.wav` | Generic WAV stream endpoint. |
| `GET/POST /tts/legado.wav` | Reader/Legado-compatible WAV endpoint; supports `mode=stream` and `mode=buffered`. |
| `POST /jobs/tts` | Queue a long-form TTS job and poll/download it through `/jobs`. |
| `POST /stop` | Stop the current TTS task. |
| `POST /clear_reference_audio_cache` | Clear cached reference-audio preprocessing. |

Detailed request/response contracts live in [Docs/API-Service.md](./Docs/API-Service.md).

## Audio Formats

- Raw PCM: `POST /tts/raw` returns `application/octet-stream` bytes with
  `X-Genie-Audio-Format: pcm_s16le`, 32000 Hz, mono, 16-bit little-endian PCM.
- Stream WAV: `mode=stream` on `/tts/legado.wav` or `/tts/stream.wav` returns
  `audio/wav` immediately and streams generated PCM chunks behind a WAV header.
  It has lower startup latency but may not be accepted by every Android media
  stack because the final data size is unknown at response start.
- Buffered complete WAV: `mode=buffered` on `/tts/legado.wav` waits for synthesis
  to finish in memory and returns a normal complete `audio/wav` response. This
  is the current stable Legado reading mode.
- Complete WAV: `POST /tts/wav` also returns a complete `audio/wav` file and is
  suited to clients that need a normal file response.

## Validation Commands

Run these after documentation-only or low-risk maintenance changes:

```powershell
git -C E:\Genie-TTS diff --check
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m compileall E:\Genie-TTS\src
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m py_compile "E:\Genie-TTS\Tutorial\English\API Server Tutorial.py" "E:\Genie-TTS\Examples\api_client.py" "E:\Genie-TTS\Examples\api_job_client.py"
```

Run the package/runtime checks before claiming runtime health:

```powershell
E:\Genie-TTS\Scripts\verify-internal-runtime.ps1
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m pip check
```

Run real HTTP validation after API, server, runtime, or script changes:

```powershell
E:\Genie-TTS\Scripts\verify-internal-api.ps1 -Runtime cuda
E:\Genie-TTS\Scripts\verify-legado-stream-api.ps1 -Runtime cuda
E:\Genie-TTS\Scripts\verify-job-api.ps1 -Runtime cuda
```

The verification scripts create temporary files under `test` and remove their
own outputs unless a keep-output option is explicitly used. Do not delete older
test artifacts unless you can prove they were created by the current run.

## Examples

- `Examples\api_client.py`: loads `feibi`, sets reference audio, calls
  `/tts/raw`, `/tts/legado.wav`, `/tts/legado.wav?mode=buffered`, and `/tts/wav`.
- `Examples\api_job_client.py`: submits `/jobs/tts`, polls `/jobs/{job_id}`, and
  downloads `/jobs/{job_id}/wav`.
- `Examples\legado_http_tts.json`: Legado httpTTS source for streaming WAV.
- `Examples\legado_http_tts_buffered.json`: Legado httpTTS source for buffered
  complete WAV, currently the stable Android/Legado reading option.

Example client run against an already-started local server:

```powershell
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe E:\Genie-TTS\Examples\api_client.py --base-url http://127.0.0.1:8000
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe E:\Genie-TTS\Examples\api_job_client.py --base-url http://127.0.0.1:8000
```

## Documentation Map

- [README_zh.md](./README_zh.md): Simplified Chinese quick start for the same
  local integration package.
- [Docs/API-Service.md](./Docs/API-Service.md): detailed API contract, endpoint
  semantics, headers, error behavior, and client examples.
- [Docs/Architecture.md](./Docs/Architecture.md): current module boundaries,
  data flow, and known maintenance pressure points.
- [Docs/Maintenance.md](./Docs/Maintenance.md): validation chains, release
  checks, troubleshooting, and cleanup rules.
- [AGENTS.md](./AGENTS.md): execution rules for future Codex/AI agents working
  in this repository.

## Development Notes

- Keep source dependencies CPU-friendly in `requirements.txt`; use
  `requirements-cuda.txt` for the package-local CUDA overlay.
- Preserve existing endpoints unless a compatibility migration is documented.
- Keep CPU fallback, CUDA runtime selection, `/runtime`, `/status`, job API, and
  Legado buffered compatibility stable while developing new features.
- Do not deep-rewrite decoder loops, ONNX Runtime IO Binding, batching, or
  inference-core behavior without a measured CPU/GPU baseline and real TTS
  correctness proof.
- Use longer Chinese passages with `split_sentence=true` for synthesis
  validation. Very short phrases do not exercise the audiobook/listening path.

## Upstream Lineage

Genie-TTS is based on the open-source GPT-SoVITS ecosystem and supports
GPT-SoVITS V2/V2ProPlus style ONNX models for Japanese, English, Chinese, and
Korean inference. This repository's active maintenance focus is the local
Windows integration package and its API/runtime reliability rather than generic
pip installation packaging.
