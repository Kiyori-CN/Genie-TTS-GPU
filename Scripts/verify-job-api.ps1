param(
    [ValidateSet('cpu', 'cuda', 'directml', 'auto')]
    [string]$Runtime = 'cuda',
    [string]$HostName = '127.0.0.1',
    [int]$Port = 0,
    [string]$CharacterName = 'feibi',
    [string]$ModelDir = '',
    [string]$ReferenceAudio = '',
    [string]$ReferenceText = '在此之前，请您务必继续享受旅居拉古那的时光。',
    [string]$Language = 'Chinese',
    [string]$Text = '清晨的城市逐渐苏醒，街边的灯光还没有完全熄灭。她合上手里的书，抬头望向窗外，决定把今天的计划重新整理一遍。为了模拟小说和文档朗读的实际场景，这段文本会被自动切分成多个句子，并连续生成可以下载的语音。随后，客户端会轮询任务进度，等待服务端写出完整的 WAV 文件，再把它保存到本地供播放器使用。',
    [bool]$SplitSentence = $true,
    [int]$PollSeconds = 2,
    [int]$TimeoutSeconds = 900,
    [string]$OutputDir = ''
)

$ErrorActionPreference = 'Stop'

function Get-FreeTcpPort {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse('127.0.0.1'), 0)
    try {
        $listener.Start()
        return $listener.LocalEndpoint.Port
    }
    finally {
        $listener.Stop()
    }
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot 'Runtime\.venv\Scripts\python.exe'
$RuntimePython = Join-Path $RepoRoot 'Runtime\Python'
$RuntimeVenvScripts = Join-Path $RepoRoot 'Runtime\.venv\Scripts'
$SitePackages = Join-Path $RepoRoot 'Runtime\.venv\Lib\site-packages'

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Internal Python was not found: $Python"
}

if ([string]::IsNullOrWhiteSpace($ModelDir)) {
    $ModelDir = Join-Path $RepoRoot "CharacterModels\v2ProPlus\$CharacterName\tts_models"
}
if ([string]::IsNullOrWhiteSpace($ReferenceAudio)) {
    $ReferenceAudio = Join-Path $RepoRoot "CharacterModels\v2ProPlus\$CharacterName\prompt_wav\zh_vo_Main_Linaxita_2_1_10_26.wav"
}
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $RepoRoot 'test'
}
if ($Port -eq 0) {
    $Port = Get-FreeTcpPort
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$env:PYTHONNOUSERSITE = '1'
$env:PYTHONPATH = $RepoRoot
$env:GENIE_DATA_DIR = Join-Path $RepoRoot 'GenieData'

$InternalPathParts = @(
    $RuntimeVenvScripts,
    $RuntimePython,
    (Join-Path $RuntimePython 'Scripts'),
    "$env:SystemRoot\System32",
    $env:SystemRoot
)

$NvidiaRoot = Join-Path $SitePackages 'nvidia'
if (Test-Path -LiteralPath $NvidiaRoot) {
    Get-ChildItem -LiteralPath $NvidiaRoot -Directory | ForEach-Object {
        $bin = Join-Path $_.FullName 'bin'
        if (Test-Path -LiteralPath $bin) {
            $InternalPathParts = @($bin) + $InternalPathParts
        }
    }
}

$env:PATH = $InternalPathParts -join ';'

$ClientHost = $HostName
if ($HostName -eq '0.0.0.0' -or $HostName -eq '::') {
    $ClientHost = '127.0.0.1'
}
$BaseUrl = "http://${ClientHost}:$Port"
$DownloadOut = Join-Path $OutputDir "verify-job-api-$Runtime-$CharacterName.wav"

$serverCode = @"
import genie_tts as genie

print('runtime=', genie.configure_runtime('$Runtime'), flush=True)
genie.start_server(host='$HostName', port=$Port, workers=1)
"@

$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $Python
$psi.WorkingDirectory = $RepoRoot
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.Environment['PYTHONNOUSERSITE'] = '1'
$psi.Environment['PYTHONPATH'] = $RepoRoot
$psi.Environment['GENIE_DATA_DIR'] = Join-Path $RepoRoot 'GenieData'
$psi.Environment['PATH'] = $env:PATH
[void]$psi.ArgumentList.Add('-u')
[void]$psi.ArgumentList.Add('-c')
[void]$psi.ArgumentList.Add($serverCode)

$server = [System.Diagnostics.Process]::new()
$server.StartInfo = $psi
[void]$server.Start()

$env:GENIE_JOB_BASE_URL = $BaseUrl
$env:GENIE_JOB_RUNTIME = $Runtime
$env:GENIE_JOB_CHARACTER = $CharacterName
$env:GENIE_JOB_MODEL_DIR = $ModelDir
$env:GENIE_JOB_REFERENCE_AUDIO = $ReferenceAudio
$env:GENIE_JOB_REFERENCE_TEXT = $ReferenceText
$env:GENIE_JOB_LANGUAGE = $Language
$env:GENIE_JOB_TEXT = $Text
$env:GENIE_JOB_SPLIT_SENTENCE = if ($SplitSentence) { 'true' } else { 'false' }
$env:GENIE_JOB_POLL_SECONDS = [string]$PollSeconds
$env:GENIE_JOB_TIMEOUT_SECONDS = [string]$TimeoutSeconds
$env:GENIE_JOB_DOWNLOAD_OUT = $DownloadOut

$clientScript = @'
import json
import os
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

base = os.environ["GENIE_JOB_BASE_URL"]
runtime = os.environ["GENIE_JOB_RUNTIME"]
character = os.environ["GENIE_JOB_CHARACTER"]
model_dir = Path(os.environ["GENIE_JOB_MODEL_DIR"])
reference_audio = Path(os.environ["GENIE_JOB_REFERENCE_AUDIO"])
reference_text = os.environ["GENIE_JOB_REFERENCE_TEXT"]
language = os.environ["GENIE_JOB_LANGUAGE"]
text = os.environ["GENIE_JOB_TEXT"]
split_sentence = os.environ["GENIE_JOB_SPLIT_SENTENCE"].lower() in {"1", "true", "yes", "y"}
poll_seconds = float(os.environ["GENIE_JOB_POLL_SECONDS"])
timeout_seconds = float(os.environ["GENIE_JOB_TIMEOUT_SECONDS"])
download_out = Path(os.environ["GENIE_JOB_DOWNLOAD_OUT"])


def normalize_headers(headers):
    return {key.lower(): value for key, value in dict(headers).items()}


def request_json(method, path, payload=None, timeout=120):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        base + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, normalize_headers(response.headers), json.loads(response.read().decode("utf-8"))


def request_bytes(method, path, timeout=300):
    request = urllib.request.Request(base + path, method=method)
    chunks = []
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            chunks.append(chunk)
        return response.status, normalize_headers(response.headers), b"".join(chunks), time.perf_counter() - start


def expected_first_provider(mode, selected_providers):
    if mode == "cpu":
        return "CPUExecutionProvider"
    if mode == "cuda":
        return "CUDAExecutionProvider"
    if mode == "directml":
        return "DmlExecutionProvider"
    if mode == "auto":
        return selected_providers[0]
    raise AssertionError(f"Unsupported runtime mode: {mode!r}")


def provider_summary(runtime_info):
    return {
        "selected_providers": runtime_info["selected_providers"],
        "available_providers": runtime_info["available_providers"],
        "loaded_models": runtime_info["loaded_models"].get(character, {}),
        "shared_models": runtime_info["shared_models"],
    }


last_error = None
for _ in range(120):
    try:
        status, _, health = request_json("GET", "/health", timeout=2)
        if status == 200 and health.get("status") == "ok":
            break
    except Exception as exc:
        last_error = exc
        time.sleep(1)
else:
    raise RuntimeError(f"Server did not become healthy: {last_error!r}")

runtime_status, _, runtime_before = request_json("GET", "/runtime")
assert runtime_status == 200
assert runtime_before["runtime_mode"] == runtime, runtime_before
expected_provider = expected_first_provider(runtime, runtime_before["selected_providers"])
assert runtime_before["selected_providers"][0] == expected_provider, runtime_before
assert runtime_before["api_audio"]["job_submit_endpoint"] == "/jobs/tts", runtime_before["api_audio"]

load_status, _, load_result = request_json("POST", "/load_character", {
    "character_name": character,
    "onnx_model_dir": str(model_dir),
    "language": language,
}, timeout=240)
assert load_status == 200 and load_result["status"] == "success", load_result

ref_status, _, ref_result = request_json("POST", "/set_reference_audio", {
    "character_name": character,
    "audio_path": str(reference_audio),
    "audio_text": reference_text,
    "language": language,
}, timeout=180)
assert ref_status == 200 and ref_result["status"] == "success", ref_result

submit_start = time.perf_counter()
submit_status, _, submit_result = request_json("POST", "/jobs/tts", {
    "character_name": character,
    "text": text,
    "split_sentence": split_sentence,
}, timeout=120)
submit_elapsed = time.perf_counter() - submit_start
assert submit_status == 202, submit_result
job_id = submit_result["job_id"]

cancel_submit_status, _, cancel_submit_result = request_json("POST", "/jobs/tts", {
    "character_name": character,
    "text": "这是一条用于验证排队取消接口的短任务，应该在开始合成前被取消。",
    "split_sentence": True,
}, timeout=120)
assert cancel_submit_status == 202, cancel_submit_result
cancel_job_id = cancel_submit_result["job_id"]
cancel_status, _, cancel_result = request_json("POST", f"/jobs/{cancel_job_id}/cancel", timeout=60)
assert cancel_status == 200, cancel_result
assert cancel_result["status"] == "cancelled", cancel_result

jobs_status, _, jobs_result = request_json("GET", "/jobs", timeout=60)
assert jobs_status == 200
assert any(item["job_id"] == job_id for item in jobs_result["jobs"]), jobs_result

deadline = time.perf_counter() + timeout_seconds
polls = []
while True:
    job_status, _, job = request_json("GET", f"/jobs/{job_id}", timeout=60)
    assert job_status == 200
    polls.append({
        "status": job["status"],
        "stage": job["stage"],
        "message": job["message"],
        "generated_pcm_bytes": job["generated_pcm_bytes"],
        "output_bytes": job["output_bytes"],
        "elapsed_seconds": job["elapsed_seconds"],
    })
    if job["status"] in {"completed", "failed", "cancelled"}:
        break
    if time.perf_counter() > deadline:
        raise TimeoutError(f"Job {job_id} did not finish within {timeout_seconds} seconds")
    time.sleep(poll_seconds)

if job["status"] != "completed":
    raise RuntimeError(f"Job {job_id} ended with status {job['status']}: {job.get('error_detail')}")
assert job["output_bytes"] > 44, job
assert job["audio_duration_seconds"] and job["audio_duration_seconds"] > 0, job
assert job["output_exists"] is True, job

download_status, download_headers, wav_body, download_elapsed = request_bytes("GET", f"/jobs/{job_id}/wav", timeout=300)
assert download_status == 200
assert download_headers.get("x-genie-audio-format") == "wav_pcm_s16le", download_headers
assert download_headers.get("x-genie-sample-rate") == "32000", download_headers
assert download_headers.get("x-genie-channels") == "1", download_headers
assert download_headers.get("x-genie-sample-width") == "2", download_headers
download_out.write_bytes(wav_body)

with wave.open(str(download_out), "rb") as wav_file:
    wav_info = {
        "channels": wav_file.getnchannels(),
        "sample_width": wav_file.getsampwidth(),
        "sample_rate": wav_file.getframerate(),
        "frames": wav_file.getnframes(),
        "duration_seconds": wav_file.getnframes() / wav_file.getframerate(),
    }
assert wav_info["channels"] == 1, wav_info
assert wav_info["sample_width"] == 2, wav_info
assert wav_info["sample_rate"] == 32000, wav_info
assert wav_info["frames"] > 0, wav_info

runtime_after = request_json("GET", "/runtime", timeout=120)[2]
loaded_models = runtime_after["loaded_models"][character]
for model_name, providers in loaded_models.items():
    assert expected_provider in providers, (model_name, providers)
for shared_name, providers in runtime_after["shared_models"].items():
    if providers:
        assert expected_provider in providers, (shared_name, providers)

summary = {
    "base_url": base,
    "runtime": runtime,
    "job_id": job_id,
    "submit_elapsed_seconds": submit_elapsed,
    "split_sentence": split_sentence,
    "text_chars": len(text),
    "cancel_check": {
        "job_id": cancel_job_id,
        "status": cancel_result["status"],
        "stage": cancel_result["stage"],
    },
    "poll_count": len(polls),
    "final_job": job,
    "download": {
        "bytes": len(wav_body),
        "elapsed_seconds": download_elapsed,
        "output": str(download_out),
        "wave": wav_info,
    },
    "provider_summary": provider_summary(runtime_after),
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
'@

try {
    $clientScript | & $Python -
    if ($LASTEXITCODE -ne 0) {
        throw "Job API validation failed with exit code $LASTEXITCODE"
    }
}
finally {
    if ($server -and -not $server.HasExited) {
        $server.Kill()
        [void]$server.WaitForExit(10000)
    }
    $stdout = $server.StandardOutput.ReadToEnd()
    $stderr = $server.StandardError.ReadToEnd()
    if ($stdout.Trim()) {
        "SERVER_STDOUT_BEGIN"
        $stdout.Trim()
        "SERVER_STDOUT_END"
    }
    if ($stderr.Trim()) {
        "SERVER_STDERR_BEGIN"
        $stderr.Trim()
        "SERVER_STDERR_END"
    }
}
