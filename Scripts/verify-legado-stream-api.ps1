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
    [string]$Text = '为了验证阅读软件的网络朗读兼容性，我们使用稍长的中文段落进行测试。服务端需要先返回低延迟的分块 WAV，再返回兼容性更强的 buffered WAV，并确认两种响应都能生成有效音频。',
    [bool]$SplitSentence = $true,
    [string]$OutputDir = '',
    [switch]$KeepOutputs
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
$StreamWavOut = Join-Path $OutputDir "verify-legado-$Runtime-$CharacterName-stream.wav"
$StreamStandardWavOut = Join-Path $OutputDir "verify-legado-$Runtime-$CharacterName-stream-standardized.wav"
$BufferedWavOut = Join-Path $OutputDir "verify-legado-$Runtime-$CharacterName-buffered.wav"

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

$env:GENIE_LEGADO_BASE_URL = $BaseUrl
$env:GENIE_LEGADO_RUNTIME = $Runtime
$env:GENIE_LEGADO_CHARACTER = $CharacterName
$env:GENIE_LEGADO_MODEL_DIR = $ModelDir
$env:GENIE_LEGADO_REFERENCE_AUDIO = $ReferenceAudio
$env:GENIE_LEGADO_REFERENCE_TEXT = $ReferenceText
$env:GENIE_LEGADO_LANGUAGE = $Language
$env:GENIE_LEGADO_TEXT = $Text
$env:GENIE_LEGADO_SPLIT_SENTENCE = if ($SplitSentence) { 'true' } else { 'false' }
$env:GENIE_LEGADO_STREAM_OUT = $StreamWavOut
$env:GENIE_LEGADO_STREAM_STANDARD_OUT = $StreamStandardWavOut
$env:GENIE_LEGADO_BUFFERED_OUT = $BufferedWavOut
$env:GENIE_LEGADO_KEEP_OUTPUTS = if ($KeepOutputs) { 'true' } else { 'false' }

$clientScript = @'
import json
import os
import time
import urllib.request
import wave
from pathlib import Path

base = os.environ["GENIE_LEGADO_BASE_URL"]
runtime = os.environ["GENIE_LEGADO_RUNTIME"]
character = os.environ["GENIE_LEGADO_CHARACTER"]
model_dir = Path(os.environ["GENIE_LEGADO_MODEL_DIR"])
reference_audio = Path(os.environ["GENIE_LEGADO_REFERENCE_AUDIO"])
reference_text = os.environ["GENIE_LEGADO_REFERENCE_TEXT"]
language = os.environ["GENIE_LEGADO_LANGUAGE"]
text = os.environ["GENIE_LEGADO_TEXT"]
split_sentence = os.environ["GENIE_LEGADO_SPLIT_SENTENCE"].lower() in {"1", "true", "yes", "y"}
stream_wav_out = Path(os.environ["GENIE_LEGADO_STREAM_OUT"])
stream_standard_wav_out = Path(os.environ["GENIE_LEGADO_STREAM_STANDARD_OUT"])
buffered_wav_out = Path(os.environ["GENIE_LEGADO_BUFFERED_OUT"])
keep_outputs = os.environ["GENIE_LEGADO_KEEP_OUTPUTS"].lower() in {"1", "true", "yes", "y"}
output_paths = [stream_wav_out, stream_standard_wav_out, buffered_wav_out]


def cleanup_outputs():
    if keep_outputs:
        return
    for path in output_paths:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass


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
        body = response.read().decode("utf-8")
        return response.status, normalize_headers(response.headers), json.loads(body)


def post_bytes(path, payload, timeout=300):
    request = urllib.request.Request(
        base + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        chunks = []
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            chunks.append(chunk)
        return response.status, normalize_headers(response.headers), b"".join(chunks), time.perf_counter() - start


def raw_pcm_to_wav(pcm_bytes, path, sample_rate=32000, channels=1, sample_width=2):
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)


def inspect_wav(path):
    with wave.open(str(path), "rb") as wav_file:
        frames = wav_file.getnframes()
        sample_rate = wav_file.getframerate()
        return {
            "channels": wav_file.getnchannels(),
            "sample_width": wav_file.getsampwidth(),
            "sample_rate": sample_rate,
            "frames": frames,
            "duration_seconds": frames / float(sample_rate),
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


try:
    last_error = None
    for _ in range(120):
        try:
            health_status, _, health = request_json("GET", "/health", timeout=2)
            if health_status == 200 and health.get("status") == "ok":
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
    assert runtime_before["api_audio"]["legado_stream_wav_endpoint"] == "/tts/legado.wav", runtime_before["api_audio"]
    assert runtime_before["api_audio"]["status_endpoint"] == "/status", runtime_before["api_audio"]
    assert "buffered" in runtime_before["api_audio"].get("reader_response_modes", []), runtime_before["api_audio"]

    status_status, _, status_before = request_json("GET", "/status")
    assert status_status == 200 and status_before["status"] == "ok", status_before
    assert not status_before["active_tts_session"], status_before

    load_status, _, load_result = request_json("POST", "/load_character", {
        "character_name": character,
        "onnx_model_dir": str(model_dir),
        "language": language,
    }, timeout=180)
    assert load_status == 200 and load_result["status"] == "success", load_result

    ref_status, _, ref_result = request_json("POST", "/set_reference_audio", {
        "character_name": character,
        "audio_path": str(reference_audio),
        "audio_text": reference_text,
        "language": language,
    }, timeout=60)
    assert ref_status == 200 and ref_result["status"] == "success", ref_result

    payload = {
        "character_name": character,
        "text": text,
        "split_sentence": split_sentence,
    }

    stream_status, stream_headers, stream_body, stream_elapsed = post_bytes(
        "/tts/legado.wav?wait_timeout=300",
        payload,
        timeout=300,
    )
    stream_wav_out.write_bytes(stream_body)
    assert stream_status == 200
    assert stream_headers.get("content-type", "").startswith("audio/wav"), stream_headers
    assert stream_headers.get("x-genie-audio-format") == "wav_stream_pcm_s16le", stream_headers
    assert stream_headers.get("x-genie-inner-audio-format") == "pcm_s16le", stream_headers
    assert stream_headers.get("x-genie-stream-mode") == "http_chunked", stream_headers
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

    status_after_stream = request_json("GET", "/status")[2]
    last_stream = status_after_stream["last_reader_request"]
    assert last_stream["endpoint"] == "/tts/legado.wav", last_stream
    assert last_stream["mode"] == "stream", last_stream
    assert last_stream["status"] == "completed", last_stream
    assert last_stream["text_chars"] == len(text), last_stream
    assert len(last_stream["text_sha256_12"]) == 12, last_stream
    assert "text" not in last_stream, last_stream

    buffered_status, buffered_headers, buffered_body, buffered_elapsed = post_bytes(
        "/tts/legado.wav?wait_timeout=300&mode=buffered",
        payload,
        timeout=300,
    )
    buffered_wav_out.write_bytes(buffered_body)
    assert buffered_status == 200
    assert buffered_headers.get("content-type", "").startswith("audio/wav"), buffered_headers
    assert buffered_headers.get("x-genie-audio-format") == "wav_pcm_s16le", buffered_headers
    assert buffered_headers.get("x-genie-inner-audio-format") == "pcm_s16le", buffered_headers
    assert buffered_headers.get("x-genie-stream-mode") == "buffered", buffered_headers
    assert buffered_headers.get("x-genie-sample-rate") == "32000", buffered_headers
    assert buffered_headers.get("x-genie-channels") == "1", buffered_headers
    assert buffered_headers.get("x-genie-sample-width") == "2", buffered_headers
    buffered_wav_info = inspect_wav(buffered_wav_out)
    assert buffered_wav_info["channels"] == 1, buffered_wav_info
    assert buffered_wav_info["sample_width"] == 2, buffered_wav_info
    assert buffered_wav_info["sample_rate"] == 32000, buffered_wav_info
    assert buffered_wav_info["frames"] > 0, buffered_wav_info

    status_after_buffered = request_json("GET", "/status")[2]
    last_buffered = status_after_buffered["last_reader_request"]
    assert last_buffered["endpoint"] == "/tts/legado.wav", last_buffered
    assert last_buffered["mode"] == "buffered", last_buffered
    assert last_buffered["status"] == "completed", last_buffered
    assert last_buffered["text_chars"] == len(text), last_buffered
    assert len(last_buffered["text_sha256_12"]) == 12, last_buffered
    assert "text" not in last_buffered, last_buffered

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
        "selected_providers": runtime_after["selected_providers"],
        "character": character,
        "text_chars": len(text),
        "split_sentence": split_sentence,
        "load_character": load_result,
        "set_reference_audio": ref_result,
        "stream": {
            "status": stream_status,
            "headers": {
                "Content-Type": stream_headers.get("content-type"),
                "X-Genie-Audio-Format": stream_headers.get("x-genie-audio-format"),
                "X-Genie-Inner-Audio-Format": stream_headers.get("x-genie-inner-audio-format"),
                "X-Genie-Stream-Mode": stream_headers.get("x-genie-stream-mode"),
                "X-Genie-Sample-Rate": stream_headers.get("x-genie-sample-rate"),
                "X-Genie-Channels": stream_headers.get("x-genie-channels"),
                "X-Genie-Sample-Width": stream_headers.get("x-genie-sample-width"),
            },
            "bytes": len(stream_body),
            "pcm_bytes": len(stream_pcm),
            "elapsed_seconds": stream_elapsed,
            "wave": stream_wav_info,
            "output": str(stream_wav_out),
            "standardized_output": str(stream_standard_wav_out),
        },
        "buffered": {
            "status": buffered_status,
            "headers": {
                "Content-Type": buffered_headers.get("content-type"),
                "X-Genie-Audio-Format": buffered_headers.get("x-genie-audio-format"),
                "X-Genie-Inner-Audio-Format": buffered_headers.get("x-genie-inner-audio-format"),
                "X-Genie-Stream-Mode": buffered_headers.get("x-genie-stream-mode"),
                "X-Genie-Sample-Rate": buffered_headers.get("x-genie-sample-rate"),
                "X-Genie-Channels": buffered_headers.get("x-genie-channels"),
                "X-Genie-Sample-Width": buffered_headers.get("x-genie-sample-width"),
            },
            "bytes": len(buffered_body),
            "elapsed_seconds": buffered_elapsed,
            "wave": buffered_wav_info,
            "output": str(buffered_wav_out),
        },
        "status": {
            "busy_after_requests": status_after_buffered["busy"],
            "last_reader_request": last_buffered,
            "recent_reader_count": len(status_after_buffered["reader_requests"]["recent"]),
        },
        "provider_summary": {
            "loaded_models": runtime_after["loaded_models"].get(character, {}),
            "shared_models": runtime_after["shared_models"],
        },
        "outputs_kept": keep_outputs,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
finally:
    cleanup_outputs()
'@

try {
    $clientScript | & $Python -
    if ($LASTEXITCODE -ne 0) {
        throw "Legado stream API validation failed with exit code $LASTEXITCODE"
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
