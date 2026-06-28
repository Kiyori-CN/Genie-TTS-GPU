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
    [string]$RawText = '清晨的城市逐渐苏醒，街边的灯光还没有完全熄灭。她合上手里的书，抬头望向窗外，决定把今天的计划重新整理一遍，然后继续完成那段漫长而细致的旅程。',
    [string]$WavText = '为了确认中文推理链路是否稳定，我们需要使用稍长一点的文本进行测试。请让系统自动切分句子，连续生成多段语音，并在生成后由用户亲自检查音频内容是否完整、自然、准确。',
    [bool]$SplitSentence = $true,
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
$RawOut = Join-Path $OutputDir "verify-api-$Runtime-$CharacterName.raw"
$StreamWavOut = Join-Path $OutputDir "verify-api-$Runtime-$CharacterName-stream.wav"
$StreamStandardWavOut = Join-Path $OutputDir "verify-api-$Runtime-$CharacterName-stream-standardized.wav"
$WavOut = Join-Path $OutputDir "verify-api-$Runtime-$CharacterName.wav"

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

$env:GENIE_VERIFY_BASE_URL = $BaseUrl
$env:GENIE_VERIFY_RUNTIME = $Runtime
$env:GENIE_VERIFY_CHARACTER = $CharacterName
$env:GENIE_VERIFY_MODEL_DIR = $ModelDir
$env:GENIE_VERIFY_REFERENCE_AUDIO = $ReferenceAudio
$env:GENIE_VERIFY_REFERENCE_TEXT = $ReferenceText
$env:GENIE_VERIFY_LANGUAGE = $Language
$env:GENIE_VERIFY_RAW_TEXT = $RawText
$env:GENIE_VERIFY_WAV_TEXT = $WavText
$env:GENIE_VERIFY_SPLIT_SENTENCE = if ($SplitSentence) { 'true' } else { 'false' }
$env:GENIE_VERIFY_RAW_OUT = $RawOut
$env:GENIE_VERIFY_STREAM_WAV_OUT = $StreamWavOut
$env:GENIE_VERIFY_STREAM_STANDARD_WAV_OUT = $StreamStandardWavOut
$env:GENIE_VERIFY_WAV_OUT = $WavOut

$clientScript = @'
import json
import os
import time
import urllib.request
import wave
from pathlib import Path

base = os.environ["GENIE_VERIFY_BASE_URL"]
runtime = os.environ["GENIE_VERIFY_RUNTIME"]
character = os.environ["GENIE_VERIFY_CHARACTER"]
model_dir = Path(os.environ["GENIE_VERIFY_MODEL_DIR"])
reference_audio = Path(os.environ["GENIE_VERIFY_REFERENCE_AUDIO"])
reference_text = os.environ["GENIE_VERIFY_REFERENCE_TEXT"]
language = os.environ["GENIE_VERIFY_LANGUAGE"]
raw_text = os.environ["GENIE_VERIFY_RAW_TEXT"]
wav_text = os.environ["GENIE_VERIFY_WAV_TEXT"]
split_sentence = os.environ["GENIE_VERIFY_SPLIT_SENTENCE"].lower() in {"1", "true", "yes", "y"}
raw_out = Path(os.environ["GENIE_VERIFY_RAW_OUT"])
stream_wav_out = Path(os.environ["GENIE_VERIFY_STREAM_WAV_OUT"])
stream_standard_wav_out = Path(os.environ["GENIE_VERIFY_STREAM_STANDARD_WAV_OUT"])
wav_out = Path(os.environ["GENIE_VERIFY_WAV_OUT"])


def normalize_headers(headers):
    return {key.lower(): value for key, value in dict(headers).items()}


def read_json(method, path, payload=None, timeout=60):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        base + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return response.status, normalize_headers(response.headers), json.loads(body)


def post_bytes(path, payload, timeout=300):
    request = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        chunks = []
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            chunks.append(chunk)
        return response.status, normalize_headers(response.headers), b"".join(chunks)


def raw_pcm_to_wav(pcm_bytes, path, sample_rate=32000, channels=1, sample_width=2):
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)


def inspect_wav(path):
    with wave.open(str(path), "rb") as wav_file:
        return {
            "channels": wav_file.getnchannels(),
            "sample_width": wav_file.getsampwidth(),
            "sample_rate": wav_file.getframerate(),
            "frames": wav_file.getnframes(),
            "duration_seconds": wav_file.getnframes() / wav_file.getframerate(),
        }


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


last_error = None
for _ in range(120):
    try:
        status, _, health = read_json("GET", "/health", timeout=2)
        if status == 200 and health.get("status") == "ok":
            break
    except Exception as exc:
        last_error = exc
        time.sleep(1)
else:
    raise RuntimeError(f"Server did not become healthy: {last_error!r}")

runtime_status, _, runtime_before = read_json("GET", "/runtime")
assert runtime_status == 200
assert runtime_before["runtime_mode"] == runtime, runtime_before
expected_provider = expected_first_provider(runtime, runtime_before["selected_providers"])
assert runtime_before["selected_providers"][0] == expected_provider, runtime_before
assert runtime_before["api_audio"]["raw_format"] == "pcm_s16le", runtime_before["api_audio"]
assert runtime_before["api_audio"]["legado_stream_wav_endpoint"] == "/tts/legado.wav", runtime_before["api_audio"]
assert runtime_before["api_audio"]["sample_rate"] == 32000, runtime_before["api_audio"]

load_status, _, load_result = read_json("POST", "/load_character", {
    "character_name": character,
    "onnx_model_dir": str(model_dir),
    "language": language,
}, timeout=180)
assert load_status == 200 and load_result["status"] == "success", load_result

ref_status, _, ref_result = read_json("POST", "/set_reference_audio", {
    "character_name": character,
    "audio_path": str(reference_audio),
    "audio_text": reference_text,
    "language": language,
}, timeout=60)
assert ref_status == 200 and ref_result["status"] == "success", ref_result

raw_payload = {
    "character_name": character,
    "text": raw_text,
    "split_sentence": split_sentence,
}
raw_start = time.perf_counter()
raw_status, raw_headers, raw_body = post_bytes("/tts/raw", raw_payload, timeout=300)
raw_elapsed = time.perf_counter() - raw_start
raw_out.write_bytes(raw_body)
assert raw_status == 200
assert raw_headers.get("x-genie-audio-format") == "pcm_s16le", raw_headers
assert raw_headers.get("x-genie-sample-rate") == "32000", raw_headers
assert raw_headers.get("x-genie-channels") == "1", raw_headers
assert raw_headers.get("x-genie-sample-width") == "2", raw_headers
assert len(raw_body) > 0 and len(raw_body) % 2 == 0, len(raw_body)

runtime_after_raw = read_json("GET", "/runtime")[2]
loaded_models = runtime_after_raw["loaded_models"][character]
for model_name, providers in loaded_models.items():
    assert expected_provider in providers, (model_name, providers)

cn_hubert_providers = runtime_after_raw["shared_models"]["cn_hubert"]
assert cn_hubert_providers and expected_provider in cn_hubert_providers, cn_hubert_providers
speaker_providers = runtime_after_raw["shared_models"].get("speaker_verification")
if speaker_providers is not None:
    assert expected_provider in speaker_providers, speaker_providers

stream_start = time.perf_counter()
stream_status, stream_headers, stream_body = post_bytes("/tts/legado.wav?wait_timeout=300", raw_payload, timeout=300)
stream_elapsed = time.perf_counter() - stream_start
stream_wav_out.write_bytes(stream_body)
assert stream_status == 200
assert stream_headers.get("content-type", "").startswith("audio/wav"), stream_headers
assert stream_headers.get("x-genie-audio-format") == "wav_stream_pcm_s16le", stream_headers
assert stream_headers.get("x-genie-inner-audio-format") == "pcm_s16le", stream_headers
assert stream_headers.get("x-genie-sample-rate") == "32000", stream_headers
assert stream_headers.get("x-genie-channels") == "1", stream_headers
assert stream_headers.get("x-genie-sample-width") == "2", stream_headers
assert len(stream_body) > 44 and stream_body[:4] == b"RIFF" and stream_body[8:12] == b"WAVE", len(stream_body)
stream_pcm = stream_body[44:]
assert len(stream_pcm) > 0 and len(stream_pcm) % 2 == 0, len(stream_pcm)
raw_pcm_to_wav(stream_pcm, stream_standard_wav_out)
stream_wav_info = inspect_wav(stream_standard_wav_out)
assert stream_wav_info["channels"] == 1, stream_wav_info
assert stream_wav_info["sample_width"] == 2, stream_wav_info
assert stream_wav_info["sample_rate"] == 32000, stream_wav_info
assert stream_wav_info["frames"] > 0, stream_wav_info

wav_payload = {
    "character_name": character,
    "text": wav_text,
    "split_sentence": split_sentence,
}
wav_start = time.perf_counter()
wav_status, wav_headers, wav_body = post_bytes("/tts/wav", wav_payload, timeout=300)
wav_elapsed = time.perf_counter() - wav_start
wav_out.write_bytes(wav_body)
assert wav_status == 200
assert wav_headers.get("x-genie-audio-format") == "wav_pcm_s16le", wav_headers
assert wav_headers.get("x-genie-sample-rate") == "32000", wav_headers
assert wav_headers.get("x-genie-channels") == "1", wav_headers
assert wav_headers.get("x-genie-sample-width") == "2", wav_headers
with wave.open(str(wav_out), "rb") as wav_file:
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

runtime_after_wav = read_json("GET", "/runtime")[2]
summary = {
    "base_url": base,
    "runtime_before": {
        "runtime_mode": runtime_before["runtime_mode"],
        "selected_providers": runtime_before["selected_providers"],
        "available_providers": runtime_before["available_providers"],
        "api_audio": runtime_before["api_audio"],
    },
    "split_sentence": split_sentence,
    "load_character": load_result,
    "set_reference_audio": ref_result,
    "raw": {
        "status": raw_status,
        "headers": {
            "Content-Type": raw_headers.get("content-type"),
            "X-Genie-Audio-Format": raw_headers.get("x-genie-audio-format"),
            "X-Genie-Sample-Rate": raw_headers.get("x-genie-sample-rate"),
            "X-Genie-Channels": raw_headers.get("x-genie-channels"),
            "X-Genie-Sample-Width": raw_headers.get("x-genie-sample-width"),
        },
        "bytes": len(raw_body),
        "elapsed_seconds": raw_elapsed,
        "output": str(raw_out),
    },
    "legado_stream_wav": {
        "status": stream_status,
        "headers": {
            "Content-Type": stream_headers.get("content-type"),
            "X-Genie-Audio-Format": stream_headers.get("x-genie-audio-format"),
            "X-Genie-Inner-Audio-Format": stream_headers.get("x-genie-inner-audio-format"),
            "X-Genie-Sample-Rate": stream_headers.get("x-genie-sample-rate"),
            "X-Genie-Channels": stream_headers.get("x-genie-channels"),
            "X-Genie-Sample-Width": stream_headers.get("x-genie-sample-width"),
        },
        "bytes": len(stream_body),
        "pcm_bytes": len(stream_pcm),
        "elapsed_seconds": stream_elapsed,
        "wave": stream_wav_info,
        "stream_output": str(stream_wav_out),
        "standardized_wav_output": str(stream_standard_wav_out),
    },
    "wav": {
        "status": wav_status,
        "headers": {
            "Content-Type": wav_headers.get("content-type"),
            "X-Genie-Audio-Format": wav_headers.get("x-genie-audio-format"),
            "X-Genie-Sample-Rate": wav_headers.get("x-genie-sample-rate"),
            "X-Genie-Channels": wav_headers.get("x-genie-channels"),
            "X-Genie-Sample-Width": wav_headers.get("x-genie-sample-width"),
        },
        "bytes": len(wav_body),
        "elapsed_seconds": wav_elapsed,
        "wave": wav_info,
        "output": str(wav_out),
    },
    "runtime_after_wav": {
        "loaded_models": runtime_after_wav["loaded_models"],
        "shared_models": runtime_after_wav["shared_models"],
    },
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
'@

try {
    $clientScript | & $Python -
    if ($LASTEXITCODE -ne 0) {
        throw "API validation failed with exit code $LASTEXITCODE"
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
