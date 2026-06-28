# Genie-TTS API Service

This document describes the self-contained Windows integration package under
`E:\Genie-TTS`. It assumes the API server runs from the package-local Python
runtime and does not require system Python, global CUDA Toolkit paths, or global
PATH edits.

## Start the Server

Local-only CUDA server:

```powershell
E:\Genie-TTS\Scripts\start-internal-api.ps1 -Runtime cuda -HostName 127.0.0.1 -Port 8000
```

LAN-accessible CUDA server:

```powershell
E:\Genie-TTS\Scripts\start-internal-api.ps1 -Runtime cuda -HostName 0.0.0.0 -Port 8000
```

CPU fallback server:

```powershell
E:\Genie-TTS\Scripts\start-internal-api.ps1 -Runtime cpu -HostName 127.0.0.1 -Port 8000
```

Runtime mode must be selected before model loading. Valid modes are `cpu`,
`cuda`, `directml`, and `auto`. The server should normally use one worker.
Multiple workers duplicate model memory and do not share loaded characters.

## Default Chinese Character

For local Chinese validation, use the bundled v2ProPlus character:

```text
character_name: feibi
language: Chinese
onnx_model_dir: E:\Genie-TTS\CharacterModels\v2ProPlus\feibi\tts_models
reference_audio: E:\Genie-TTS\CharacterModels\v2ProPlus\feibi\prompt_wav\zh_vo_Main_Linaxita_2_1_10_26.wav
reference_text: 在此之前，请您务必继续享受旅居拉古那的时光。
```

Use longer Chinese passages with `split_sentence=true` for audiobook-style
validation. Generated files can be structurally valid while the spoken content
is still wrong or incomplete, so final Chinese quality still requires listening
or another audio-content inspection step.

## Core Flow

1. `GET /health`
2. `GET /runtime`
3. `POST /load_character`
4. `POST /set_reference_audio`
5. `POST /tts/raw` for raw streaming, or `POST /tts/wav` for a complete WAV
6. `GET /runtime` again to confirm actual model session providers

`POST /set_reference_audio` performs real preprocessing. It loads reference
audio, runs HuBERT, and for v2ProPlus characters prepares speaker/reference
embeddings when the prompt encoder is available. Treat it as a warm-up step,
not as a cheap metadata assignment.

## Endpoints

### GET /health

Returns process health:

```json
{"status": "ok"}
```

### GET /runtime

Returns ONNX Runtime version, selected providers, available providers, loaded
characters, per-character session providers, shared model providers, and API
audio metadata. For GPU claims, inspect the actual session provider lists under
`loaded_models` and `shared_models`, not only `available_providers`.

### POST /load_character

Request:

```json
{
  "character_name": "feibi",
  "onnx_model_dir": "E:\\Genie-TTS\\CharacterModels\\v2ProPlus\\feibi\\tts_models",
  "language": "Chinese"
}
```

Success:

```json
{"status": "success", "message": "Character 'feibi' loaded."}
```

### POST /set_reference_audio

Request:

```json
{
  "character_name": "feibi",
  "audio_path": "E:\\Genie-TTS\\CharacterModels\\v2ProPlus\\feibi\\prompt_wav\\zh_vo_Main_Linaxita_2_1_10_26.wav",
  "audio_text": "在此之前，请您务必继续享受旅居拉古那的时光。",
  "language": "Chinese"
}
```

Success:

```json
{"status": "success", "message": "Reference audio for 'feibi' set."}
```

### POST /tts/raw

Streams raw PCM bytes as they are produced. Compatibility alias: `POST /tts`.

Request:

```json
{
  "character_name": "feibi",
  "text": "清晨的城市逐渐苏醒，街边的灯光还没有完全熄灭。她合上手里的书，抬头望向窗外，决定把今天的计划重新整理一遍。",
  "split_sentence": true
}
```

Response body is not a WAV file. It is raw audio with these headers:

```text
Content-Type: application/octet-stream
X-Genie-Audio-Format: pcm_s16le
X-Genie-Sample-Rate: 32000
X-Genie-Channels: 1
X-Genie-Sample-Width: 2
```

Clients should decode it as PCM S16LE, 32000 Hz, mono, 16-bit.

### POST /tts/wav

Uses the same request body as `/tts/raw`, but waits until synthesis finishes and
returns a complete `audio/wav` file. Use this endpoint when the caller needs a
normal file response rather than low-latency streaming.

### POST /stop

Stops the current TTS task.

### POST /clear_reference_audio_cache

Clears cached reference-audio preprocessing results.

### GET /profile and POST /profile

Profiling is disabled unless `GENIE_PROFILE=1` is set or `POST /profile` enables
it. These endpoints are intended for local benchmarking, not public exposure.

Enable and clear profiling:

```json
{"enabled": true, "clear": true, "include_events": false}
```

`GET /profile` returns per-stage events and aggregate summaries for stages such
as `g2p`, `t2s_encoder`, `t2s_first_stage_decoder`,
`t2s_stage_decoder_cuda_iobinding`, `vits`, `audio_postprocess`, `http_stream`,
and `http_wav_response`.

## Error Semantics

Common client-visible errors:

```text
400  Unsupported reference audio file extension.
404  Character model is not loaded, or reference audio is not set.
409  A TTS session is already active. Retry after the current request finishes or call /stop.
500  Model loading, inference, or server-side processing failed.
```

The API currently accepts one active TTS session per process. External callers
should serialize requests or handle `409` with retry/backoff.

## Client Example

Start the server, then run:

```powershell
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe E:\Genie-TTS\Examples\api_client.py --base-url http://127.0.0.1:8000
```

The example loads `feibi`, sets reference audio, calls both `/tts/raw` and
`/tts/wav`, and writes outputs under `E:\Genie-TTS\test`.

## Validation and Profiling

Full API verification with real HTTP raw PCM and WAV requests:

```powershell
E:\Genie-TTS\Scripts\verify-internal-api.ps1 -Runtime cuda
```

Repeatable API profiling with warm-up, measured runs, stage timings, and GPU
sampling when `nvidia-smi` is available:

```powershell
E:\Genie-TTS\Scripts\profile-internal-api.ps1 -Runtime cuda -Endpoint wav -WarmupRuns 1 -MeasureRuns 3
```

The profiling script writes a JSON report under `E:\Genie-TTS\test` and leaves
per-run audio artifacts there for inspection.
