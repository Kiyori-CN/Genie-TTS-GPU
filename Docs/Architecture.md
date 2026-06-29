# Genie-TTS Architecture Notes

This document records the current architecture of the `E:\Genie-TTS`
self-contained Windows integration package. It is intentionally factual and
does not describe a desired future rewrite.

## Package Model

`E:\Genie-TTS` is the active package root. Normal operation should resolve
runtime components from inside this folder:

- `Runtime\Python`: package-local CPython base runtime.
- `Runtime\.venv`: package-local virtual environment and Python packages.
- `Runtime\.venv\Lib\site-packages\nvidia\*\bin`: CUDA/cuDNN user-mode DLLs
  provided by package-local NVIDIA wheels.
- `GenieData`: shared model resources such as HuBERT, speaker verification,
  G2P resources, and optional Chinese RoBERTa assets.
- `CharacterModels`: voice/model resources, including the default Chinese
  `v2ProPlus\feibi` validation character.
- `UserData`: runtime state such as queued job WAV outputs.
- `test`: local validation outputs.

Only source, scripts, requirements, examples, and documentation should be
tracked by git. Runtime/model/output folders are local artifacts.

## Runtime and Dependency Boundary

The PowerShell scripts under `Scripts\` establish a child-process environment
for package-local execution. They set `PYTHONNOUSERSITE=1`, set or clear
`PYTHONPATH` as needed, set `GENIE_DATA_DIR`, and construct a child-process
`PATH` with the package runtime and package-local NVIDIA wheel DLL folders.

The package may rely on Windows system DLLs and the installed NVIDIA display
driver, including `nvcuda.dll`. It should not rely on global Python, global pip,
global CUDA Toolkit directories, or user/machine `PATH` for normal operation.

## API Server Layer

Source: `src\genie_tts\Server.py`.

The FastAPI server owns the HTTP contract and request coordination:

- Character and reference endpoints: `/load_character`, `/unload_character`,
  `/set_reference_audio`, `/clear_reference_audio_cache`.
- Direct TTS endpoints: `/tts`, `/tts/raw`, `/tts/wav`.
- Reader endpoints: `/tts/stream.wav`, `/tts/legado.wav`.
- Job endpoints: `/jobs/tts`, `/jobs`, `/jobs/{job_id}`,
  `/jobs/{job_id}/cancel`, `/jobs/{job_id}/wav`.
- Diagnostics: `/health`, `/runtime`, `/status`, `/profile`.

The server also defines audio response helpers for raw PCM, stream WAV, and
complete WAV responses. It performs request parsing for JSON, form, and query
parameter bodies on the reader endpoints, including aliases such as `speakText`
for Legado rules.

## Model and Provider Layer

Source: `src\genie_tts\ModelManager.py`.

`ModelManager` owns ONNX Runtime provider selection, CUDA DLL preload attempts,
shared model sessions, character model sessions, model cache maps, and runtime
reporting.

Important runtime states:

- `runtime_mode`: requested mode such as `cpu`, `cuda`, `directml`, or `auto`.
- `selected_providers`: provider order requested for new ONNX sessions.
- `available_providers`: providers reported by the imported ONNX Runtime wheel.
- `loaded_models`: actual `get_providers()` results for each loaded character
  model session.
- `shared_models`: actual providers for shared models such as HuBERT, speaker
  verification, and RoBERTa.

`CUDAExecutionProvider` appearing in `available_providers` is only a capability
signal. The runtime is not proven until a real session is created and its
provider list reports CUDA.

## TTS Session and Player Layer

Source: `src\genie_tts\Core\TTSPlayer.py`.

`TTSPlayer` coordinates the single active TTS session, text queueing,
audio queueing, generated chunks, playback/save handling, stop requests, and a
`status_snapshot()` used by `/status`.

The current concurrency model is intentionally conservative: one active TTS
session per process. Direct TTS requests fail fast with `409` when the session
is occupied, while reader endpoints can wait for the session lock through
`wait_timeout`.

## Public Python API Layer

Source: `src\genie_tts\Internal.py` and `src\genie_tts\__init__.py`.

This layer exposes package-level functions such as `load_character`,
`set_reference_audio`, `tts`, `tts_async`, `stop`, `configure_runtime`, and
`get_runtime_info`. The FastAPI server and GUI worker code use this layer where
appropriate, so public function names should be preserved unless a migration is
planned and documented.

## Job API Layer

Source: `TTSJobManager` and `TTSJobRecord` in `src\genie_tts\Server.py`.

The job API is for queued long-form tasks that can be submitted, polled,
cancelled, and downloaded as complete WAV files. Output files are written under
`UserData\Jobs` by default. A single worker thread matches the current
single-session inference model.

Job statuses are `queued`, `running`, `completed`, `failed`, and `cancelled`.
Completed job WAV downloads are served from disk through `/jobs/{job_id}/wav`.

## Reader and Legado Compatibility Layer

Sources: reader helpers and endpoints in `src\genie_tts\Server.py`, templates
under `Examples\legado_http_tts*.json`, and
`Scripts\verify-legado-stream-api.ps1`.

Reader endpoints accept JSON, form, or query parameter input and default to the
`feibi` character when no character is supplied. They also default
`split_sentence=true` to match listening/audiobook usage.

Current behavior:

- `mode=stream`: returns a WAV header immediately and streams generated PCM as
  chunked HTTP. This keeps first-audio latency lower but can be rejected or
  interrupted by some Android media stacks.
- `mode=buffered`: waits for synthesis to finish in memory and returns a
  complete WAV response with a concrete length. This is the current stable
  Android/Legado path.

`/status` includes recent reader diagnostics without storing or returning the
full request text. It reports text length and a short content hash instead.

## Validation Scripts

- `Scripts\verify-internal-runtime.ps1`: verifies package-local Python,
  import/runtime state, and CUDA EP session creation.
- `Scripts\start-internal-api.ps1`: starts a package-local API server with a
  selected runtime mode.
- `Scripts\verify-internal-api.ps1`: starts a temporary server and validates
  `/health`, `/runtime`, load/reference setup, raw PCM, Legado stream WAV,
  Legado buffered WAV, complete WAV, and provider reporting.
- `Scripts\verify-legado-stream-api.ps1`: focused Legado verification for both
  stream and buffered modes plus `/status` diagnostics.
- `Scripts\verify-job-api.ps1`: verifies queued job submission, polling,
  download, WAV structure, and provider reporting.
- `Scripts\profile-internal-api.ps1`: optional profiling harness for raw or WAV
  endpoints with warm-up/measurement runs and a JSON report.

## API Data Flow

Direct complete WAV flow:

1. Client calls `/load_character`.
2. `ModelManager` creates character ONNX sessions using the currently selected
   provider order.
3. Client calls `/set_reference_audio`.
4. Reference preprocessing runs shared models and caches character reference
   state.
5. Client calls `/tts/wav`.
6. `TTSPlayer` reserves the single TTS session, synthesizes PCM chunks, and the
   server wraps the result as a complete WAV response.
7. Client calls `/runtime` to verify actual loaded session providers.

Legado buffered flow:

1. Legado sends text to `/tts/legado.wav?wait_timeout=300&mode=buffered`.
2. The server parses Legado aliases, registers a reader diagnostic record, and
   waits for the TTS session lock if needed.
3. `TTSPlayer` synthesizes audio in memory.
4. The server returns a complete WAV response and updates `/status` reader
   diagnostics.

Job flow:

1. Client submits `/jobs/tts`.
2. `TTSJobManager` stores a record and wakes the single worker thread.
3. The worker reserves the TTS session, writes a WAV under `UserData\Jobs`, and
   updates job progress fields.
4. Client polls `/jobs/{job_id}` and downloads `/jobs/{job_id}/wav` after
   completion.

## Current Maintenance Pressure Points

- `src\genie_tts\Server.py` now contains endpoint definitions, reader parsing,
  job management, WAV helpers, status diagnostics, and profiling endpoints. It
  is understandable but broad; future refactors should be small and backed by
  HTTP verification.
- Endpoint semantics are split between code, `Docs\API-Service.md`, examples,
  and validation scripts. README should stay a quick path and link to the API
  contract rather than duplicate every detail.
- Terms should remain consistent: reader mode, `stream`, `buffered`, raw PCM,
  stream WAV, complete WAV, runtime provider, and session provider.
- Verification scripts share setup patterns. If they are refactored later, keep
  child-process environment construction explicit and package-local.
- Performance work should not start from implementation guesses. Measure CPU
  and GPU baselines with the same character, reference audio, text, runtime
  mode, and endpoint before changing decoder loops, IO Binding, batching, or
  sentence splitting behavior.
