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
    [string]$Text = '清晨的城市逐渐苏醒，街边的灯光还没有完全熄灭。她合上手里的书，抬头望向窗外，决定把今天的计划重新整理一遍，然后继续完成那段漫长而细致的旅程。为了模拟小说和文档朗读的实际场景，这段文本会被自动切分成多个句子，并连续生成可以播放的语音。',
    [bool]$SplitSentence = $true,
    [ValidateSet('raw', 'wav')]
    [string]$Endpoint = 'wav',
    [int]$WarmupRuns = 1,
    [int]$MeasureRuns = 3,
    [int]$GpuSampleIntervalMs = 250,
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
$ReportPath = Join-Path $OutputDir ("profile-api-{0}-{1}-{2}.json" -f $Runtime, $CharacterName, (Get-Date -Format 'yyyyMMdd-HHmmss'))

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
$psi.Environment['GENIE_PROFILE'] = '1'
$psi.Environment['PATH'] = $env:PATH
[void]$psi.ArgumentList.Add('-u')
[void]$psi.ArgumentList.Add('-c')
[void]$psi.ArgumentList.Add($serverCode)

$server = [System.Diagnostics.Process]::new()
$server.StartInfo = $psi
[void]$server.Start()

$env:GENIE_PROFILE_BASE_URL = $BaseUrl
$env:GENIE_PROFILE_RUNTIME = $Runtime
$env:GENIE_PROFILE_CHARACTER = $CharacterName
$env:GENIE_PROFILE_MODEL_DIR = $ModelDir
$env:GENIE_PROFILE_REFERENCE_AUDIO = $ReferenceAudio
$env:GENIE_PROFILE_REFERENCE_TEXT = $ReferenceText
$env:GENIE_PROFILE_LANGUAGE = $Language
$env:GENIE_PROFILE_TEXT = $Text
$env:GENIE_PROFILE_SPLIT_SENTENCE = if ($SplitSentence) { 'true' } else { 'false' }
$env:GENIE_PROFILE_ENDPOINT = $Endpoint
$env:GENIE_PROFILE_WARMUP_RUNS = [string]$WarmupRuns
$env:GENIE_PROFILE_MEASURE_RUNS = [string]$MeasureRuns
$env:GENIE_PROFILE_GPU_SAMPLE_INTERVAL = [string]($GpuSampleIntervalMs / 1000.0)
$env:GENIE_PROFILE_OUTPUT_DIR = $OutputDir
$env:GENIE_PROFILE_REPORT_PATH = $ReportPath

$clientScript = @'
import json
import os
import shutil
import statistics
import subprocess
import threading
import time
import urllib.request
import wave
from pathlib import Path

base = os.environ["GENIE_PROFILE_BASE_URL"]
runtime = os.environ["GENIE_PROFILE_RUNTIME"]
character = os.environ["GENIE_PROFILE_CHARACTER"]
model_dir = Path(os.environ["GENIE_PROFILE_MODEL_DIR"])
reference_audio = Path(os.environ["GENIE_PROFILE_REFERENCE_AUDIO"])
reference_text = os.environ["GENIE_PROFILE_REFERENCE_TEXT"]
language = os.environ["GENIE_PROFILE_LANGUAGE"]
text = os.environ["GENIE_PROFILE_TEXT"]
split_sentence = os.environ["GENIE_PROFILE_SPLIT_SENTENCE"].lower() in {"1", "true", "yes", "y"}
endpoint = os.environ["GENIE_PROFILE_ENDPOINT"]
warmup_runs = int(os.environ["GENIE_PROFILE_WARMUP_RUNS"])
measure_runs = int(os.environ["GENIE_PROFILE_MEASURE_RUNS"])
gpu_sample_interval = float(os.environ["GENIE_PROFILE_GPU_SAMPLE_INTERVAL"])
output_dir = Path(os.environ["GENIE_PROFILE_OUTPUT_DIR"])
report_path = Path(os.environ["GENIE_PROFILE_REPORT_PATH"])
output_dir.mkdir(parents=True, exist_ok=True)


def normalize_headers(headers):
    return {key.lower(): value for key, value in dict(headers).items()}


def request_json(method, path, payload=None, timeout=60):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        base + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, normalize_headers(response.headers), json.loads(response.read().decode("utf-8"))


def post_bytes(path, payload, timeout=300):
    request = urllib.request.Request(
        base + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    chunks = []
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            chunks.append(chunk)
        elapsed = time.perf_counter() - start
        return response.status, normalize_headers(response.headers), b"".join(chunks), elapsed


def timed_json(method, path, payload=None, timeout=180):
    start = time.perf_counter()
    status, headers, body = request_json(method, path, payload, timeout=timeout)
    return {"status": status, "elapsed_seconds": time.perf_counter() - start, "body": body, "headers": headers}


class GpuSampler:
    def __init__(self, interval):
        self.interval = interval
        self.samples = []
        self.error = None
        self._stop = threading.Event()
        self._thread = None
        self._nvidia_smi = shutil.which("nvidia-smi") or shutil.which("nvidia-smi.exe")

    def start(self):
        if not self._nvidia_smi:
            self.error = "nvidia-smi was not found on PATH"
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self):
        query = [
            self._nvidia_smi,
            "--query-gpu=utilization.gpu,utilization.memory,memory.used,power.draw",
            "--format=csv,noheader,nounits",
        ]
        while not self._stop.is_set():
            try:
                output = subprocess.check_output(query, text=True, stderr=subprocess.STDOUT, timeout=3).strip()
                if output:
                    first_line = output.splitlines()[0]
                    parts = [part.strip() for part in first_line.split(",")]
                    def to_float(value):
                        if not value or value == "N/A":
                            return None
                        try:
                            return float(value)
                        except ValueError:
                            return None

                    self.samples.append({
                        "timestamp": time.time(),
                        "gpu_util_percent": to_float(parts[0]) if len(parts) > 0 else None,
                        "memory_util_percent": to_float(parts[1]) if len(parts) > 1 else None,
                        "memory_used_mb": to_float(parts[2]) if len(parts) > 2 else None,
                        "power_draw_w": to_float(parts[3]) if len(parts) > 3 else None,
                    })
            except Exception as exc:
                self.error = str(exc)
            time.sleep(self.interval)

    def summary(self):
        result = {"sample_count": len(self.samples), "error": self.error}
        for key in ("gpu_util_percent", "memory_util_percent", "memory_used_mb", "power_draw_w"):
            values = [sample[key] for sample in self.samples if sample.get(key) is not None]
            if values:
                result[key] = {
                    "avg": statistics.fmean(values),
                    "max": max(values),
                    "min": min(values),
                }
        return result


def audio_duration_seconds(body, headers, output_path):
    if headers.get("x-genie-audio-format") == "pcm_s16le":
        sample_rate = int(headers.get("x-genie-sample-rate", "32000"))
        channels = int(headers.get("x-genie-channels", "1"))
        sample_width = int(headers.get("x-genie-sample-width", "2"))
        return len(body) / float(sample_rate * channels * sample_width)
    with wave.open(str(output_path), "rb") as wav_file:
        return wav_file.getnframes() / float(wav_file.getframerate())


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

runtime_before = request_json("GET", "/runtime")[2]
profile_enabled = request_json("POST", "/profile", {"enabled": True, "clear": True, "include_events": False})[2]

setup = {
    "load_character": timed_json("POST", "/load_character", {
        "character_name": character,
        "onnx_model_dir": str(model_dir),
        "language": language,
    }, timeout=240),
    "set_reference_audio": timed_json("POST", "/set_reference_audio", {
        "character_name": character,
        "audio_path": str(reference_audio),
        "audio_text": reference_text,
        "language": language,
    }, timeout=180),
}

payload = {
    "character_name": character,
    "text": text,
    "split_sentence": split_sentence,
}
endpoint_path = "/tts/raw" if endpoint == "raw" else "/tts/wav"
suffix = "raw" if endpoint == "raw" else "wav"

warmup_results = []
for index in range(warmup_runs):
    status, headers, body, elapsed = post_bytes(endpoint_path, payload, timeout=360)
    warmup_results.append({
        "run": index + 1,
        "status": status,
        "bytes": len(body),
        "elapsed_seconds": elapsed,
        "format": headers.get("x-genie-audio-format"),
    })

setup_profile = request_json("GET", "/profile", timeout=120)[2]
request_json("POST", "/profile", {"enabled": True, "clear": True, "include_events": False}, timeout=120)

sampler = GpuSampler(gpu_sample_interval)
sampler.start()
measurements = []
try:
    for index in range(measure_runs):
        status, headers, body, elapsed = post_bytes(endpoint_path, payload, timeout=360)
        output_path = output_dir / f"profile-api-{runtime}-{character}-{endpoint}-run{index + 1}.{suffix}"
        output_path.write_bytes(body)
        duration = audio_duration_seconds(body, headers, output_path)
        measurements.append({
            "run": index + 1,
            "status": status,
            "bytes": len(body),
            "elapsed_seconds": elapsed,
            "audio_duration_seconds": duration,
            "real_time_factor": elapsed / duration if duration else None,
            "format": headers.get("x-genie-audio-format"),
            "headers": {
                "content_type": headers.get("content-type"),
                "x_genie_audio_format": headers.get("x-genie-audio-format"),
                "x_genie_sample_rate": headers.get("x-genie-sample-rate"),
                "x_genie_channels": headers.get("x-genie-channels"),
                "x_genie_sample_width": headers.get("x-genie-sample-width"),
            },
            "output": str(output_path),
        })
finally:
    sampler.stop()

profile_after = request_json("GET", "/profile", timeout=120)[2]
runtime_after = request_json("GET", "/runtime", timeout=120)[2]

elapsed_values = [item["elapsed_seconds"] for item in measurements]
rtf_values = [item["real_time_factor"] for item in measurements if item["real_time_factor"] is not None]
aggregate = {
    "measure_runs": len(measurements),
    "elapsed_avg_seconds": statistics.fmean(elapsed_values) if elapsed_values else None,
    "elapsed_min_seconds": min(elapsed_values) if elapsed_values else None,
    "elapsed_max_seconds": max(elapsed_values) if elapsed_values else None,
    "rtf_avg": statistics.fmean(rtf_values) if rtf_values else None,
    "rtf_min": min(rtf_values) if rtf_values else None,
    "rtf_max": max(rtf_values) if rtf_values else None,
}

report = {
    "base_url": base,
    "runtime": runtime,
    "endpoint": endpoint_path,
    "character": character,
    "language": language,
    "split_sentence": split_sentence,
    "text_chars": len(text),
    "profile_enabled_response": profile_enabled,
    "runtime_before": runtime_before,
    "setup": setup,
    "warmup": warmup_results,
    "setup_profile": setup_profile,
    "measurements": measurements,
    "aggregate": aggregate,
    "gpu": sampler.summary(),
    "profile": profile_after,
    "runtime_after": runtime_after,
}
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "report": str(report_path),
    "aggregate": aggregate,
    "gpu": report["gpu"],
    "profile_summary": profile_after.get("summary", {}),
}, ensure_ascii=False, indent=2))
'@

try {
    $clientScript | & $Python -
    if ($LASTEXITCODE -ne 0) {
        throw "API profiling failed with exit code $LASTEXITCODE"
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
