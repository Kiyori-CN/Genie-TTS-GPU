# Genie-TTS Maintenance Guide

This guide is for routine maintenance of the `E:\Genie-TTS` integration
package. It focuses on keeping the package self-contained, verifiable, and safe
to hand off before feature work continues.

## Start Each Round With Facts

Run these before editing:

```powershell
Get-Content E:\Genie-TTS\AGENTS.md
git -C E:\Genie-TTS status --short --branch --untracked-files=all
git -C E:\Genie-TTS remote -v
git -C E:\Genie-TTS log -5 --oneline --decorate
git -C E:\Genie-TTS diff --stat
```

Expected repository baseline for the current package:

- Active root: `E:\Genie-TTS`.
- Remote: `https://github.com/Kiyori-CN/Genie-TTS-GPU.git`.
- Do not restore the original `High-Logic/Genie-TTS.git` remote unless the user
  explicitly asks.
- Sibling `E:\Genie-TTS GUI` is read-only comparison material.

## Stable Validation Chain

For documentation-only or low-risk maintenance changes:

```powershell
git -C E:\Genie-TTS diff --check
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m compileall E:\Genie-TTS\src
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m py_compile "E:\Genie-TTS\Tutorial\English\API Server Tutorial.py" "E:\Genie-TTS\Examples\api_client.py" "E:\Genie-TTS\Examples\api_job_client.py"
```

For backend, runtime, script, API, or dependency changes, add:

```powershell
E:\Genie-TTS\Scripts\verify-internal-runtime.ps1
E:\Genie-TTS\Runtime\.venv\Scripts\python.exe -m pip check
E:\Genie-TTS\Scripts\verify-internal-api.ps1 -Runtime cuda
E:\Genie-TTS\Scripts\verify-legado-stream-api.ps1 -Runtime cuda
E:\Genie-TTS\Scripts\verify-job-api.ps1 -Runtime cuda
```

Use `-Runtime cpu` separately when a change could affect CPU fallback. Do not
present a CUDA-only pass as proof that CPU fallback remains healthy.

## Runtime Health Checklist

When reporting runtime health, separate these states:

- Package-local Python exists and is being used.
- `PYTHONNOUSERSITE=1` isolates user-site packages.
- `GENIE_DATA_DIR` points to `E:\Genie-TTS\GenieData`.
- Package-local CUDA/cuDNN DLL folders are on the child-process `PATH`.
- `CUDAExecutionProvider` is available from ONNX Runtime.
- Runtime mode selected CUDA first through `configure_runtime("cuda")`.
- A minimal ONNX session can actually create with CUDA.
- Loaded TTS model sessions and shared model sessions report CUDA providers in
  `/runtime` after real TTS.
- Real TTS generated non-empty audio with valid structure.
- The generated Chinese content still needs listening/content inspection.

## Default Chinese Validation Character

Use this character unless the task explicitly needs another voice:

```text
character_name: feibi
language: Chinese
onnx_model_dir: E:\Genie-TTS\CharacterModels\v2ProPlus\feibi\tts_models
reference_audio: E:\Genie-TTS\CharacterModels\v2ProPlus\feibi\prompt_wav\zh_vo_Main_Linaxita_2_1_10_26.wav
reference_text: 在此之前，请您务必继续享受旅居拉古那的时光。
```

Prefer longer Chinese text and `split_sentence=true` so validation exercises the
listening/audiobook path rather than only a short single phrase.

## API and Reader Stability Rules

- Preserve existing endpoint names unless a migration is documented.
- Keep `/tts` as the compatibility alias for raw PCM streaming.
- Keep `/tts/raw` as raw PCM S16LE, 32000 Hz, mono. Do not document it as WAV.
- Keep `/tts/wav` as a complete WAV response.
- Keep `/tts/stream.wav` as the generic stream WAV endpoint.
- Keep `/tts/legado.wav` as the Legado/reader endpoint.
- Treat `mode=buffered` on `/tts/legado.wav` as the current stable
  Android/Legado listening path.
- Treat `mode=stream` as the low-latency stream path for compatible clients and
  experiments.
- Keep `/status` available for busy/session/job/recent-reader diagnostics.
- Keep `/runtime` provider reporting detailed enough to show actual session
  providers, not just the selected provider list.

## Git and Artifact Rules

Allowed source areas normally include:

- `AGENTS.md`, `README.md`, `README_zh.md`, `Docs\*.md`, `Examples\*.py`,
  `Examples\*.json`, `Scripts\*.ps1`, `src\`, `requirements*.txt`,
  `pyproject.toml`, and `.gitignore`.

Do not stage these package/runtime artifacts:

- `Runtime\`
- `GenieData\`
- `CharacterModels\`
- `UserData\`
- `test\`
- `__pycache__\`
- `*.pyc`
- Generated raw, WAV, JSON profile, or temporary validation outputs unless a
  task explicitly asks to preserve them as source fixtures.

Before committing:

```powershell
git -C E:\Genie-TTS status --short --branch --untracked-files=all
git -C E:\Genie-TTS diff --cached --stat
git -C E:\Genie-TTS diff --cached --check
```

Inspect the staged diff before committing so runtime/model/output files do not
enter git by accident.

## Temporary Output Cleanup

Validation scripts write under `test` by default. Some scripts remove their own
temporary audio outputs unless a keep flag is used, but the directory can also
contain older comparison artifacts.

Cleanup rule:

- Remove only files you can identify as created by the current validation run.
- Do not wipe `test` broadly during maintenance.
- Do not remove `UserData\Jobs` outputs unless the task explicitly asks or you
  can prove they are disposable outputs from the current run.

## Troubleshooting

### CUDA provider is visible but sessions use CPU

Check `/runtime` after loading the character and generating real TTS. If
`available_providers` lists CUDA but `loaded_models` or `shared_models` report
CPU only, treat CUDA session creation as unproven or failed. Re-run
`Scripts\verify-internal-runtime.ps1` and inspect package-local NVIDIA DLL paths
before changing source logic.

### Reader playback starts then stops early

Use buffered Legado mode:

```text
/tts/legado.wav?wait_timeout=300&mode=buffered
```

This returns a complete WAV after synthesis finishes in memory. It trades
first-audio latency for Android media-stack compatibility.

### Direct TTS returns 409

The server currently supports one active TTS session per process. Serialize
callers, retry after the active request finishes, use reader endpoints with
`wait_timeout`, or use the job API for queued long-form generation.

### Job WAV is missing

`/jobs/{job_id}/wav` returns `410` when metadata exists but the output file is
gone from disk. Check `UserData\Jobs` cleanup history and rerun the job if the
file was removed.

### Machine checks pass but Chinese sounds wrong

Treat machine validation as structural/runtime proof only. Chinese pronunciation,
prosody, sentence segmentation, and content completeness still require listening
or another audio-content inspection workflow.

## Release/Push Checklist

1. Confirm the worktree starts from a known baseline.
2. Make narrow changes only in the required source/doc areas.
3. Run the validation chain appropriate to the touched files.
4. Check for unexpected generated files.
5. Stage only intended source/doc files.
6. Inspect staged diff and run `git diff --cached --check`.
7. Commit with a specific message.
8. Push to `origin master` only after validation passes.
9. Confirm final `git status --short --branch --untracked-files=all` and remote
   alignment.

## Future Development Priority

Keep correctness ahead of performance rewrites:

1. Preserve CPU fallback and CUDA runtime selection.
2. Preserve API endpoint compatibility and Legado buffered stability.
3. Improve Chinese inference correctness and listening validation.
4. Measure CPU/GPU baselines before optimization.
5. Investigate decoder-loop transfers, IO Binding, batching, segmentation, and
   warm-up only after the baseline is reproducible.
