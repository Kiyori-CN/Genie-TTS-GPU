# AGENTS.md

Project workspace: `E:\Genie-TTS`.

This repository is now maintained as a self-contained Genie-TTS integration
package. The goal is not just source development: the folder must be able to
carry its own Python runtime, Python packages, ONNX Runtime CPU/GPU runtimes,
CUDA/cuDNN user-mode DLLs, model resources, API server scripts, and validation
tools.

The sibling directory `E:\Genie-TTS GUI` is a packaged/runtime comparison source
from an earlier build. Do not edit it. Use it only as a read-only source for
manual comparison or one-time resource migration when explicitly needed. The
active package root is `E:\Genie-TTS`.

## Package Model

- Treat `E:\Genie-TTS` as the complete integration package root.
- Do not rely on system Python, global pip, global CUDA Toolkit, user PATH, or
  machine-wide environment variables for normal operation.
- Keep all package-owned runtime components inside this folder:
  - `Runtime\Python`: package-local Python base runtime.
  - `Runtime\.venv`: package-local virtual environment and Python packages.
  - `Runtime\.venv\Lib\site-packages\nvidia\*\bin`: CUDA/cuDNN user-mode DLLs
    installed by package-local pip wheels.
  - `GenieData`: package-local shared resources, including HuBERT, speaker
    encoder, G2P resources, and optional RoBERTa assets.
  - `CharacterModels`: package-local voice/model resources.
- It is acceptable to depend on Windows system DLLs and the installed NVIDIA
  display driver, including `nvcuda.dll`; those are driver/OS boundaries and
  cannot be bundled like Python packages. Do not depend on global CUDA Toolkit
  directories.
- Runtime folders and model resources are local package artifacts and should
  stay out of git by default. Keep rebuild scripts and requirements files in
  source control.

## Current Product Goal

Build Genie-TTS into a local/remote TTS service suitable for long-form listening
workflows such as audiobook, novel, and document narration. The backend must
support both CPU and GPU inference paths, and expose an API that external tools
can call reliably.

Required capabilities:

- CPU ONNX inference path remains stable and usable as a fallback.
- GPU ONNX inference through ONNX Runtime execution providers, especially
  `CUDAExecutionProvider`, works from the package-local runtime.
- Runtime can be selected as `cpu`, `cuda`, `directml`, or `auto`.
- Runtime status reports selected providers, available providers, loaded models,
  and each ONNX session's actual `get_providers()` result.
- External API supports local and LAN/remote callers through FastAPI.
- Streaming TTS supports low-latency playback for listening/reading workflows.
- Complete WAV response remains available for clients that need a normal file.
- Legado/reader playback remains compatible through `/tts/legado.wav`; current
  stable Android/Legado listening uses `mode=buffered`.
- Long-form queued generation remains available through the `/jobs/tts` job API.
- `/status` remains available for busy/session/job/recent-reader diagnostics.
- The API is documented clearly enough for third-party clients to implement.
- High-efficiency inference is a continuing target: reduce avoidable CPU/GPU
  transfers, improve batching/segmentation where safe, and investigate ONNX
  Runtime IO Binding or decoder-loop redesign after correctness is proven.

## Immediate Priority: Chinese Inference

The next development priority is to finish and verify Chinese inference
adaptation before broad performance rewrites. Future inference tests should use
the local Chinese v2ProPlus character by default:

- Character root: `E:\Genie-TTS\CharacterModels\v2ProPlus\feibi`.
- ONNX model directory:
  `E:\Genie-TTS\CharacterModels\v2ProPlus\feibi\tts_models`.
- Reference audio:
  `E:\Genie-TTS\CharacterModels\v2ProPlus\feibi\prompt_wav\zh_vo_Main_Linaxita_2_1_10_26.wav`.
- Reference transcript: `在此之前，请您务必继续享受旅居拉古那的时光。`
- Language: `Chinese`.

Use longer Chinese passages for synthesis validation rather than very short
phrases. Default to smart sentence splitting (`split_sentence=true`) so the API
and queueing path are exercised in a listening/audiobook-like workflow.

Generated WAV/raw files can be structurally valid while the spoken content is
still wrong, incomplete, mispronounced, or poorly segmented. Treat machine
checks as format/runtime validation only. Always report that the user must
listen to or otherwise inspect generated audio before considering Chinese TTS
quality correct.

## Project Structure

Important source files:

- `Main.py`: PySide6 GUI launcher.
- `src\genie_tts\ModelManager.py`: ONNX Runtime session creation, provider
  selection, CUDA DLL preload, model cache, runtime reporting.
- `src\genie_tts\Core\Inference.py`: core TTS inference loop and decoder path.
- `src\genie_tts\Core\TTSPlayer.py`: text queue, audio queue, streaming chunks,
  playback/save handling, and TTS session status snapshots.
- `src\genie_tts\Server.py`: FastAPI app, `/health`, `/runtime`, `/status`,
  `/tts`, `/tts/raw`, `/tts/wav`, `/tts/stream.wav`, `/tts/legado.wav`, job API,
  reader diagnostics, load/unload/reference endpoints, and profiling endpoints.
- `src\genie_tts\Internal.py`: public Python API functions.
- `src\genie_tts\__init__.py`: package export surface.
- `src\genie_tts\GUI\GUI.py`: main GUI widgets.
- `src\genie_tts\GUI\ServerManager.py`: GUI worker calling inference functions.
- `Docs\API-Service.md`: detailed HTTP API contract.
- `Docs\Architecture.md`: factual module boundaries and current data flows.
- `Docs\Maintenance.md`: validation chain, troubleshooting, cleanup, and release
  checklist.
- `Examples\api_client.py`: standard-library client for load/reference/raw,
  Legado stream, Legado buffered, and WAV requests.
- `Examples\api_job_client.py`: standard-library client for queued job API.
- `Examples\legado_http_tts.json`: Legado streaming WAV source template.
- `Examples\legado_http_tts_buffered.json`: Legado buffered WAV source template.
- `Tutorial\English\API Server Tutorial.py`: API usage tutorial.
- `requirements.txt`: CPU-friendly base dependency list.
- `requirements-cuda.txt`: package-local CUDA overlay dependencies.
- `Scripts\verify-internal-runtime.ps1`: verifies internal Python and CUDA EP
  session creation.
- `Scripts\start-internal-api.ps1`: starts the API using only package-local
  runtime paths.
- `Scripts\verify-internal-api.ps1`: starts a temporary internal API server and
  validates real HTTP raw PCM/WAV TTS using package-local runtime paths.
- `Scripts\verify-legado-stream-api.ps1`: validates Legado stream and buffered
  WAV paths plus `/status` diagnostics.
- `Scripts\verify-job-api.ps1`: validates long-form job submit/poll/download WAV
  behavior.
- `Scripts\profile-internal-api.ps1`: optional local profiling harness.

Important local package artifacts, normally ignored by git:

- `Runtime\Python`: local CPython runtime.
- `Runtime\.venv`: local virtual environment.
- `GenieData`: local shared runtime resources.
- `CharacterModels`: local character model resources.
- `test`: local validation outputs.
- `UserData`: local runtime state, including job WAV outputs under
  `UserData\Jobs`.

## Runtime and Dependency Rules

- Default source dependencies must remain CPU-friendly. Do not replace the base
  dependency list with GPU-only dependencies.
- CUDA support belongs in the package-local runtime and `requirements-cuda.txt`.
- Do not add bundled Python, CUDA, or model directories to process/user/machine
  global PATH. Use scripts that set child-process environment variables only.
- Do not use ambient `python` for validation unless the task explicitly concerns
  global Python. Prefer:
  `E:\Genie-TTS\Runtime\.venv\Scripts\python.exe`.
- Package-local scripts should set at least:
  - `PYTHONNOUSERSITE=1`
  - `PYTHONPATH` scoped to this package when needed
  - `GENIE_DATA_DIR=E:\Genie-TTS\GenieData`
  - child-process `PATH` containing only package runtime paths plus required
    Windows system directories.
- For CUDA, ensure package-local NVIDIA wheels provide required DLLs. Current
  expected overlay includes:
  - `onnxruntime-gpu==1.22.0`
  - `nvidia-cuda-runtime-cu12`
  - `nvidia-cuda-nvrtc-cu12`
  - `nvidia-cublas-cu12`
  - `nvidia-cudnn-cu12`
  - `nvidia-cufft-cu12`
  - `nvidia-nvjitlink-cu12`
- The current source base may pin CPU `onnxruntime==1.22.1`; GPU overlay uses
  `onnxruntime-gpu==1.22.0` because that is the available GPU wheel close to the
  base pin. Verify actual imports after installation.

## API Contract

Preserve existing endpoints unless a compatibility migration is documented.

Core endpoints:

- `GET /health`: process health.
- `GET /runtime`: ONNX Runtime version, selected provider mode, selected
  providers, available providers, loaded characters, per-session providers,
  shared model providers, and API audio metadata.
- `GET /status`: lightweight busy/session/job/recent-reader diagnostics. It
  reports recent reader text length and short hash, not the full text.
- `POST /load_character`: load/register a character model.
- `POST /unload_character`: unload a character model.
- `POST /set_reference_audio`: set reference audio and transcript.
- `POST /tts`: compatibility alias for raw PCM streaming.
- `POST /tts/raw`: explicit raw PCM streaming endpoint for low-latency clients.
- `POST /tts/wav`: complete WAV response after synthesis finishes.
- `GET/POST /tts/stream.wav`: generic stream WAV endpoint.
- `GET/POST /tts/legado.wav`: reader/Legado WAV endpoint. Supports
  `mode=stream` and `mode=buffered`; `mode=buffered` is the current stable
  Android/Legado reading path.
- `POST /jobs/tts`: submit a queued long-form TTS job.
- `GET /jobs`: list recent jobs.
- `GET /jobs/{job_id}`: inspect a queued/running/completed/failed/cancelled job.
- `POST /jobs/{job_id}/cancel`: cancel a queued or running job.
- `GET /jobs/{job_id}/wav`: download a completed job WAV.
- `POST /stop`: stop current TTS task.
- `POST /clear_reference_audio_cache`: clear reference audio cache.

Audio format rules:

- Raw streaming is PCM S16LE, 32000 Hz, mono. Do not advertise it as complete
  WAV.
- Raw streaming responses should include explicit format headers such as
  `X-Genie-Audio-Format`, `X-Genie-Sample-Rate`, `X-Genie-Channels`, and
  `X-Genie-Sample-Width`.
- Complete WAV responses use `audio/wav` and must be readable by normal WAV
  clients.
- Stream WAV responses use `audio/wav` with a WAV header followed by chunked PCM
  data. They are lower latency but less compatible with some Android media
  stacks because the final data size is not known at response start.
- Buffered Legado responses use `audio/wav` and return a complete in-memory WAV
  after synthesis finishes. Prefer this for stable Android/Legado listening.
- For listening/audiobook scenarios, prioritize stable streaming, clear end
  signals, recoverable errors, and predictable chunk formats.

## Reader and Legado Status

- `mode=buffered` on `/tts/legado.wav?wait_timeout=300&mode=buffered` is the
  current stable Android/Legado listening route.
- `mode=stream` on `/tts/legado.wav?wait_timeout=300` remains available for
  low-latency clients and compatibility experiments.
- `/tts/legado.wav` accepts JSON, form bodies, and query parameters. It accepts
  Legado-style text aliases such as `speakText`; if no character is provided,
  it defaults to `feibi`.
- `/status` should be used when diagnosing reader playback. It reports busy
  state, active session state, job state, and recent reader request metadata.
- Do not treat a valid buffered WAV or stream WAV structure as proof that the
  Chinese spoken content is correct. Listening/content inspection is still
  required.

## Documentation Boundaries

- `README.md` is the human quick-start and orientation document for this local
  integration package.
- `README_zh.md` is the Simplified Chinese quick-start for the same local
  integration package. Keep it semantically aligned with `README.md`.
- `Docs\API-Service.md` is the detailed endpoint contract and should remain the
  source of truth for request/response semantics.
- `Docs\Architecture.md` is the factual module-boundary and data-flow document.
- `Docs\Maintenance.md` is the validation, troubleshooting, cleanup, and
  release checklist document.
- `AGENTS.md` is for future Codex/AI agents. Do not turn it into a user tutorial.

## Development Flow

1. Start with facts.
   - Read `AGENTS.md`.
   - Check `git status --short --branch`.
   - Check `git remote -v`, recent log, and current diff before assuming branch
     or remote state.
   - Inspect current diffs before editing.
   - Use `rg` for code search.

2. Validate the package-local environment before changing code.
   - Run `E:\Genie-TTS\Scripts\verify-internal-runtime.ps1`.
   - Confirm Python `base_prefix` and stdlib are inside `E:\Genie-TTS\Runtime`.
   - Confirm `CUDAExecutionProvider` can create a real ONNX session, not just
     appear in `ort.get_available_providers()`.

3. Keep CPU and GPU as separate correctness targets.
   - CPU: must always remain available and verified.
   - GPU provider visible: not enough.
   - GPU session created: useful milestone.
   - End-to-end TTS with model sessions reporting CUDA providers and playable
     output: required before claiming GPU TTS works.

4. Make backend/API changes before GUI changes.
   - Add or adjust Python API and FastAPI behavior first.
   - Validate with real HTTP requests.
   - Add GUI controls only after backend semantics are stable.

5. Keep changes small and reviewable.
   - Avoid unrelated refactors.
   - Preserve public function names unless a migration path is provided.
   - Preserve HTTP endpoint names unless the compatibility migration is
     documented in `Docs\API-Service.md`.
   - Do not delete/reset user changes.
   - Do not make destructive git operations unless explicitly asked.

6. For performance work, proceed only after correctness proof.
   - Measure CPU and GPU baselines with the same character/reference/text.
   - Separate model load time from synthesis time.
   - Report session providers for every model.
   - Investigate decoder-loop GPU transfer overhead, IO Binding, batching,
     sentence splitting, cache reuse, and warm-up separately.

## Validation Expectations

Minimum validation after documentation-only or low-risk maintenance changes:

```powershell
git -C E:\Genie-TTS diff --check
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m compileall E:\Genie-TTS\src
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m py_compile "E:\Genie-TTS\Tutorial\English\API Server Tutorial.py" "E:\Genie-TTS\Examples\api_client.py" "E:\Genie-TTS\Examples\api_job_client.py"
```

Minimum validation after backend/runtime/script changes:

```powershell
E:\Genie-TTS\Scripts\verify-internal-runtime.ps1
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m compileall E:\Genie-TTS\src
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m py_compile "E:\Genie-TTS\Tutorial\English\API Server Tutorial.py" "E:\Genie-TTS\Examples\api_client.py" "E:\Genie-TTS\Examples\api_job_client.py"
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m pip check
E:\Genie-TTS\Scripts\verify-internal-api.ps1 -Runtime cuda
E:\Genie-TTS\Scripts\verify-legado-stream-api.ps1 -Runtime cuda
E:\Genie-TTS\Scripts\verify-job-api.ps1 -Runtime cuda
```

Provider check:

```powershell
@'
import onnxruntime as ort
print(ort.__version__)
print(ort.get_available_providers())
print(ort.get_device())
'@ | E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -
```

API and TTS validation should use real loopback HTTP requests. Verify at least:

- `GET /health` returns 200.
- `GET /runtime` returns selected providers and API audio metadata.
- `POST /load_character` loads a known local model.
- `POST /set_reference_audio` accepts a known local reference audio.
- `POST /tts/raw` streams non-empty PCM bytes with raw audio headers.
- `POST /tts/wav` returns a valid WAV readable by Python `wave`.

For default Chinese TTS validation, use `feibi`, a longer Chinese text passage,
and `split_sentence=true`. Save generated files under `test` only as temporary
validation artifacts, then clean them unless they are intentionally kept for a
specific comparison.

For GPU validation, additionally verify:

- `configure_runtime("cuda")` returns `CUDAExecutionProvider` first.
- A minimal ONNX session reports `['CUDAExecutionProvider', 'CPUExecutionProvider']`.
- Real TTS output is generated.
- `/runtime` after TTS reports CUDA providers for loaded character sessions and
  shared models such as HuBERT and speaker verification.

## Reporting Rules

When reporting progress, distinguish these states clearly:

- Internal package Python exists and is being used.
- CUDA/cuDNN DLLs are package-local and loaded through child-process paths.
- CPU path preserved.
- GPU provider is available.
- GPU provider is selected.
- ONNX Runtime actually created sessions with CUDA provider.
- End-to-end TTS generated valid audio.
- API streaming and WAV responses were verified by real HTTP requests.

Do not claim GPU acceleration is complete merely because
`CUDAExecutionProvider` appears in `ort.get_available_providers()`. Do not claim
the integration package is self-contained if Python stdlib, Python packages,
CUDA/cuDNN DLLs, GenieData, or CharacterModels are still being loaded from
outside `E:\Genie-TTS`.
