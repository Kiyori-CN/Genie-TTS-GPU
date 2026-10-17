# Genie-TTS-GPU

**A Windows speech workbench for local and LAN clients.** Built on Genie-TTS / GPT-SoVITS, with CPU/CUDA runtime selection, WebUI, HTTP APIs, long-text jobs and reader integration.

[简体中文](README.md) · [English](README.en.md) · [Setup](Docs/Quickstart.en.md) · [API reference](Docs/API-Service.md)

## What you can do

| Scenario | Entry |
| --- | --- |
| Test a voice in a browser | Load a character, set reference audio and text, generate and listen in WebUI |
| Create longer narration | Submit jobs, inspect progress, cancel, and download the completed WAV |
| Connect an Android reader | Prefer the Legado buffered WAV example; verify your client separately |
| Add speech to a program | Choose raw PCM, streaming WAV or complete WAV through HTTP |
| Inspect device and task state | Check actual model providers in `/runtime` and tasks in `/status` |

![Real CPU WebUI with no character loaded](Docs/assets/showcase/webui-desktop.png)

Captured on 2026-10-17 in CPU mode with no character loaded. This shows interface state, not verified GPU performance or speech quality. See the [project tour (中文)](Docs/Showcase.md).

## Prepare the package

**This source repository is not a ready-to-run bundle.** A ZIP or clone does not include Python, dependencies, shared resources, character models or reference audio. Prepare these separately with permission to use the resources.

The current scripts target Windows and use `E:\Genie-TTS` as the example layout:

| Directory | Purpose |
| --- | --- |
| `Runtime/Python`, `Runtime/.venv` | Package-local Python and dependencies; separate CPU base and CUDA overlay |
| `GenieData` | Shared G2P, HuBERT and speaker resources |
| `CharacterModels` | Your permitted ONNX character models and reference audio |
| `UserData` | Local state and job audio outputs |

CUDA requires a compatible NVIDIA driver and package-local CUDA/cuDNN dependencies. Follow the [setup and first synthesis guide](Docs/Quickstart.en.md); normal operation should not depend on system Python, global CUDA or changes to machine PATH.

## Try local synthesis first

After preparing the package, explicitly choose CPU and loopback:

```cmd
E:\Genie-TTS\go-webui.bat --host 127.0.0.1 --runtime cpu
```

1. Open the printed local `/ui` address and confirm the runtime mode.
2. Supply the character, model directory, language, reference audio and matching transcript; load and set the reference.
3. Generate a complete WAV from your own text and listen for completeness and pronunciation.
4. To use CUDA, select it before loading models and inspect their actual session providers; follow the [detailed steps](Docs/Quickstart.en.md).

Double-clicking without arguments requests CUDA and binds `0.0.0.0`. A busy port may be replaced with a free one; use the printed address. The command above explicitly selects local CPU without changing launcher defaults.

## Choose an integration

| Need | Entry | Consideration |
| --- | --- | --- |
| File or ordinary player | `/tts/wav` | Complete WAV after synthesis |
| Android / Legado | `/tts/legado.wav?mode=buffered` | Preferred compatibility path; phone playback needs validation |
| Longer queued work | `/jobs/tts` | Submit, poll, then download completed WAV |
| Low-latency client | `/tts/raw` or stream WAV | Different formats and client compatibility requirements |

Request recipes are in [Quickstart](Docs/Quickstart.en.md); exact fields, errors and concurrency are defined by the [API contract](Docs/API-Service.md). Replace the address in the [reader template](Examples/legado_http_tts_buffered.json) with a computer address reachable from your phone. On a phone, `127.0.0.1` refers to the phone itself.

## Documentation

- [Setup and first synthesis](Docs/Quickstart.en.md) · [中文步骤](Docs/Quickstart.md)
- [Troubleshooting (中文)](Docs/Troubleshooting.md)
- [HTTP API](Docs/API-Service.md) · [Direct client](Examples/api_client.py) · [Job client](Examples/api_job_client.py)
- [Architecture](Docs/Architecture.md) · [Project tour (中文)](Docs/Showcase.md)
- [Maintenance and verification](Docs/Maintenance.md)

## Scope and upstream

The HTTP service has no built-in public authentication or access control; do not expose it to untrusted networks. API health, WAV structure, CUDA session creation and correct spoken content are separate checks. Listen to the output; no unmeasured speedup is claimed.

Model and inference foundations come from [Genie-TTS](https://github.com/High-Logic/Genie-TTS) / [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS). This repository focuses on Windows integration, services, WebUI, jobs and client compatibility. Source terms are in [LICENSE](LICENSE); model, voice, upstream component and generated-audio conditions must be checked separately.
