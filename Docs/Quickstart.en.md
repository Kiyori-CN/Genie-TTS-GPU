# Genie-TTS-GPU setup and first synthesis

[中文](Quickstart.md) · [English](Quickstart.en.md) · [Project home](../README.md)

This guide assumes a prepared Windows package. It does not install Python, dependencies, or models. Paths use `E:\Genie-TTS`; source checkout alone is insufficient.

## What the Repository Includes

Git contains source, scripts, documentation, and examples. **A source checkout is not a ready-to-run integration bundle.**
Prepare package-local Python, dependencies, model resources, and reference audio separately; they are not tracked in Git.
Current Windows examples use `E:\Genie-TTS`; see [maintenance](Maintenance.md) for the required layout.
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

After preparing the package, explicitly select CPU and listen on loopback:

```cmd
E:\Genie-TTS\go-webui.bat --host 127.0.0.1 --runtime cpu
```

The launcher uses `E:\Genie-TTS\Runtime\.venv\Scripts\python.exe` and opens
`http://127.0.0.1:<port>/ui`. The command above explicitly selects local CPU;
running without arguments requests `cuda` and binds `0.0.0.0`. A busy port may
be replaced with a free port, so use the printed address. For a fixed port, use
`--port 8000 --strict-port`; `--no-open` disables automatic browser opening.

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


## Check the result

A loaded model and valid WAV are separate from correct spoken content. Listen to the output and check missing words, pronunciation, sentence boundaries and completeness. Choose CUDA before loading models, then inspect actual session providers in `/runtime`; provider availability alone does not prove GPU synthesis.

Use [API-Service.md](API-Service.md) for exact endpoint semantics, [Troubleshooting.md](Troubleshooting.md) for symptoms, and [Maintenance.md](Maintenance.md) for developer validation.
