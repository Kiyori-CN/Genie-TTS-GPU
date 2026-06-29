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
5. `POST /tts/legado.wav` or `POST /tts/stream.wav` for reader playback,
   `POST /tts/raw` for raw PCM clients, `POST /tts/wav` for a complete WAV, or
   `POST /jobs/tts` for a queued background job
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

### GET/POST /tts/legado.wav and /tts/stream.wav

This is the preferred reader/listening endpoint for `D:\10_Project\legado` and
similar HTTP TTS clients. The default `mode=stream` path prioritizes low
latency: it returns `audio/wav` immediately with a WAV header, then streams
generated PCM chunks as HTTP response chunks. It does not create a server-side
audio file before playback.

If a reader app or Android media stack starts playback but stops after a few
sentences, use `mode=buffered` on the same endpoint:
`/tts/legado.wav?wait_timeout=300&mode=buffered`. Buffered mode still does not
write a server-side audio file, but it waits for synthesis to finish in memory
and returns a complete WAV response with an exact length. This mode prioritizes
Android/Legado player compatibility over first-audio latency, and is more
compatible with players that do not tolerate chunked WAV streams whose final
data size is not known at response start.

`/tts/legado.wav` is a stable alias for Legado httpTTS sources. `/tts/stream.wav`
is the generic name for other streaming WAV clients. Both endpoints accept JSON,
form bodies, or query parameters. Field aliases are accepted so Legado rules can
use the normal `speakText` variable:

```json
{
  "character_name": "feibi",
  "text": "清晨的城市逐渐苏醒，街边的灯光还没有完全熄灭。",
  "split_sentence": true
}
```

Accepted text fields: `text`, `speakText`, `speak_text`, or `q`.
Accepted character fields: `character_name`, `character`, `speaker`, or
`voice`. If omitted, the default character is `feibi`. `split_sentence`
defaults to `true` on these reader endpoints.

Response headers:

```text
Content-Type: audio/wav
X-Genie-Audio-Format: wav_stream_pcm_s16le
X-Genie-Inner-Audio-Format: pcm_s16le
X-Genie-Sample-Rate: 32000
X-Genie-Channels: 1
X-Genie-Sample-Width: 2
X-Genie-Stream-Mode: http_chunked
```

Buffered compatibility mode response headers include:

```text
Content-Type: audio/wav
X-Genie-Audio-Format: wav_pcm_s16le
X-Genie-Inner-Audio-Format: pcm_s16le
X-Genie-Sample-Rate: 32000
X-Genie-Channels: 1
X-Genie-Sample-Width: 2
X-Genie-Stream-Mode: buffered
```

The reader endpoints wait up to `wait_timeout` seconds for the single TTS
session lock before returning `409`. The default is `300`, which is better for
Legado continuous paragraph playback than failing immediately when the previous
paragraph is still finishing. `/tts/raw` and `/tts/wav` keep their existing
fast-`409` behavior.

Legado import example is provided at `E:\Genie-TTS\Examples\legado_http_tts.json`.
Before importing it, replace the placeholder IP `http://192.168.1.100:8000`
with the PC's LAN IP and start the API server with `-HostName 0.0.0.0`. In
Legado, enable online reading and turn on the streaming audio option
(`streamReadAloudAudio`) for the best continuous playback path.

For players that interrupt chunked WAV playback, import
`E:\Genie-TTS\Examples\legado_http_tts_buffered.json` or change the URL suffix to
`/tts/legado.wav?wait_timeout=300&mode=buffered`. This trades first-audio
latency for a standard complete WAV response. The buffered template also uses
the placeholder IP `http://192.168.1.100:8000`; replace it with the PC's LAN IP
before importing.

Minimal Legado httpTTS rule shape:

```json
{
  "name": "Genie-TTS Feibi Stream",
  "url": "@js:genieTtsUrl(speakText, speakSpeed);",
  "contentType": "audio/wav",
  "concurrentRate": "1500",
  "jsLib": "function genieTtsUrl(speakText, speakSpeed) {\n  var baseUrl = 'http://192.168.1.100:8000';\n  var body = JSON.stringify({character_name:'feibi', text:String(speakText || ''), split_sentence:true});\n  return baseUrl + '/tts/legado.wav?wait_timeout=300,' + JSON.stringify({method:'POST', headers:{'Content-Type':'application/json'}, body:body});\n}\n"
}
```

### Long-Form Job API

The job API is intended for background audiobook, novel, and document tasks that
submit longer text, poll progress, cancel if needed, and download a completed
WAV. It is not the default path for Legado's uninterrupted reading playback;
use `/tts/legado.wav` for that. Existing `/tts`, `/tts/raw`, `/tts/stream.wav`,
`/tts/legado.wav`, and `/tts/wav` behavior is unchanged.

The server keeps one job worker per process. This matches the current
`TTSPlayer` model: only one active inference session should run at a time.
Direct `/tts/raw` and `/tts/wav` requests still receive `409` while a job is
actively synthesizing. If a job is waiting for a direct request to finish, it can
be cancelled without stopping that direct request.

Job output WAV files are written under `E:\Genie-TTS\UserData\Jobs` by default.
`UserData/` is ignored by git and should be treated as runtime state.

#### POST /jobs/tts

Submit a queued long-form TTS job. `split_sentence` defaults to `true` for this
endpoint.

Request:

```json
{
  "character_name": "feibi",
  "text": "清晨的城市逐渐苏醒，街边的灯光还没有完全熄灭。她合上手里的书，抬头望向窗外，决定把今天的计划重新整理一遍。为了模拟小说和文档朗读的实际场景，这段文本会被自动切分成多个句子，并连续生成可以下载的语音。",
  "split_sentence": true
}
```

Response is HTTP `202`:

```json
{
  "job_id": "7f6f0d0d5b2d4f3a8b6d7f0f8d1e6a44",
  "job": {
    "job_id": "7f6f0d0d5b2d4f3a8b6d7f0f8d1e6a44",
    "status": "queued",
    "text_chars": 92,
    "split_sentence": true,
    "stage": "queued",
    "message": "Queued for synthesis.",
    "output_path": "E:\\Genie-TTS\\UserData\\Jobs\\7f6f0d0d5b2d4f3a8b6d7f0f8d1e6a44.wav",
    "audio_format": "wav_pcm_s16le",
    "media_type": "audio/wav",
    "sample_rate": 32000,
    "channels": 1,
    "sample_width": 2
  }
}
```

#### GET /jobs

List recent jobs, newest first:

```json
{
  "jobs": [
    {
      "job_id": "7f6f0d0d5b2d4f3a8b6d7f0f8d1e6a44",
      "status": "running",
      "stage": "synthesizing",
      "generated_pcm_bytes": 262144,
      "elapsed_seconds": 18.4
    }
  ]
}
```

#### GET /jobs/{job_id}

Return current job status. Possible statuses are `queued`, `running`,
`completed`, `failed`, and `cancelled`.

Important fields:

```text
created_at, started_at, finished_at  UTC timestamps
text_chars                           input text length
split_sentence                       whether smart sentence splitting was used
stage, message                       current progress message
output_path, output_exists           package-local WAV path and existence flag
output_bytes                         complete WAV bytes after completion
generated_pcm_bytes                  generated raw PCM bytes while running
audio_duration_seconds               WAV duration after completion
elapsed_seconds                      total wall time since creation
queue_wait_seconds                   time spent before synthesis started
processing_elapsed_seconds           synthesis/write time after start
error_detail                         failure detail when status is failed
```

#### POST /jobs/{job_id}/cancel

Cancel a queued or running job. Cancelling a completed, failed, or already
cancelled job returns `409`.

#### GET /jobs/{job_id}/wav

Download the completed job WAV. The response is a normal complete `audio/wav`
file with 32000 Hz, mono, 16-bit PCM audio. If the job is not complete yet, the
server returns `409`.

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
409  Reader stream wait_timeout expired before the TTS session became available.
409  Job WAV is not ready, or the requested job is already in a terminal state.
410  Completed job metadata exists but the WAV file is missing from disk.
500  Model loading, inference, or server-side processing failed.
```

The API currently accepts one active TTS session per process. External callers
should serialize requests or handle `409` with retry/backoff. For Legado reader
playback, prefer `/tts/legado.wav?wait_timeout=300` so paragraph requests wait
instead of failing during normal preloading.

## Client Example

Start the server, then run:

```powershell
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe E:\Genie-TTS\Examples\api_client.py --base-url http://127.0.0.1:8000
```

The example loads `feibi`, sets reference audio, calls `/tts/raw`,
`/tts/legado.wav`, and `/tts/wav`, and writes validation artifacts under
`E:\Genie-TTS\test`. The Legado stream artifact is saved only for local
inspection; normal reader playback consumes the HTTP stream directly.

Legado source template:

```powershell
Get-Content E:\Genie-TTS\Examples\legado_http_tts.json -Raw
```

Replace the example LAN IP, import the JSON as an `httpTTS` source in Legado,
and start Genie-TTS with `-HostName 0.0.0.0` so the Android device can reach it.

Queued long-form job example:

```powershell
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe E:\Genie-TTS\Examples\api_job_client.py --base-url http://127.0.0.1:8000
```

The job example loads `feibi`, sets reference audio, submits `/jobs/tts`, polls
`/jobs/{job_id}`, downloads `/jobs/{job_id}/wav`, and validates the downloaded
WAV with the Python standard `wave` module.

## Validation and Profiling

Full API verification with real HTTP raw PCM, Legado streaming WAV, and
complete WAV requests:

```powershell
E:\Genie-TTS\Scripts\verify-internal-api.ps1 -Runtime cuda
```

Full long-form job API verification:

```powershell
E:\Genie-TTS\Scripts\verify-job-api.ps1 -Runtime cuda
```

Repeatable API profiling with warm-up, measured runs, stage timings, and GPU
sampling when `nvidia-smi` is available:

```powershell
E:\Genie-TTS\Scripts\profile-internal-api.ps1 -Runtime cuda -Endpoint wav -WarmupRuns 1 -MeasureRuns 3
```

The profiling script writes a JSON report under `E:\Genie-TTS\test` and leaves
per-run audio artifacts there for inspection.
