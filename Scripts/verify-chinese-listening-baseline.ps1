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
    [string]$OutputDir = '',
    [switch]$IncludeStream,
    [switch]$IncludeJob,
    [switch]$CleanOutputs,
    [int]$PollSeconds = 2,
    [int]$TimeoutSeconds = 900
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
    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $OutputDir = Join-Path $RepoRoot "test\chinese-listening-baseline-$Runtime-$CharacterName-$timestamp"
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

$env:GENIE_LISTENING_REPO_ROOT = $RepoRoot
$env:GENIE_LISTENING_BASE_URL = $BaseUrl
$env:GENIE_LISTENING_RUNTIME = $Runtime
$env:GENIE_LISTENING_CHARACTER = $CharacterName
$env:GENIE_LISTENING_MODEL_DIR = $ModelDir
$env:GENIE_LISTENING_REFERENCE_AUDIO = $ReferenceAudio
$env:GENIE_LISTENING_REFERENCE_TEXT = $ReferenceText
$env:GENIE_LISTENING_LANGUAGE = $Language
$env:GENIE_LISTENING_OUTPUT_DIR = $OutputDir
$env:GENIE_LISTENING_INCLUDE_STREAM = if ($IncludeStream) { 'true' } else { 'false' }
$env:GENIE_LISTENING_INCLUDE_JOB = if ($IncludeJob) { 'true' } else { 'false' }
$env:GENIE_LISTENING_CLEAN_OUTPUTS = if ($CleanOutputs) { 'true' } else { 'false' }
$env:GENIE_LISTENING_POLL_SECONDS = [string]$PollSeconds
$env:GENIE_LISTENING_TIMEOUT_SECONDS = [string]$TimeoutSeconds

$clientScript = @'
import datetime as _dt
import hashlib
import json
import os
import time
import urllib.request
import wave
from pathlib import Path

repo_root = Path(os.environ["GENIE_LISTENING_REPO_ROOT"])
base = os.environ["GENIE_LISTENING_BASE_URL"]
runtime = os.environ["GENIE_LISTENING_RUNTIME"]
character = os.environ["GENIE_LISTENING_CHARACTER"]
model_dir = Path(os.environ["GENIE_LISTENING_MODEL_DIR"])
reference_audio = Path(os.environ["GENIE_LISTENING_REFERENCE_AUDIO"])
reference_text = os.environ["GENIE_LISTENING_REFERENCE_TEXT"]
language = os.environ["GENIE_LISTENING_LANGUAGE"]
output_dir = Path(os.environ["GENIE_LISTENING_OUTPUT_DIR"])
include_stream = os.environ["GENIE_LISTENING_INCLUDE_STREAM"].lower() in {"1", "true", "yes", "y"}
include_job = os.environ["GENIE_LISTENING_INCLUDE_JOB"].lower() in {"1", "true", "yes", "y"}
clean_outputs = os.environ["GENIE_LISTENING_CLEAN_OUTPUTS"].lower() in {"1", "true", "yes", "y"}
poll_seconds = float(os.environ["GENIE_LISTENING_POLL_SECONDS"])
timeout_seconds = float(os.environ["GENIE_LISTENING_TIMEOUT_SECONDS"])

samples = [
    {
        "id": "narration_scene",
        "title": "Narration scene",
        "text": "清晨的城市逐渐苏醒，街边的灯光还没有完全熄灭。她合上手里的书，抬头望向窗外，听见远处传来第一班电车缓慢进站的声音。今天的行程很长，她决定先把昨晚遗漏的线索重新整理一遍，再出门去寻找那封没有署名的信。",
        "focus": "旁白连续性、长句停顿、叙事语气稳定性",
    },
    {
        "id": "dialogue_turns",
        "title": "Dialogue turns",
        "text": "“你确定要现在出发吗？”同伴压低声音问。她没有立刻回答，只是把地图折好，放进外套内侧的口袋里。“如果再等下去，港口的雾就会散开，我们反而更容易被发现。”这句话说完以后，屋子里安静了几秒钟。",
        "focus": "引号、问句、停顿、对话切换是否自然",
    },
    {
        "id": "punctuation_dense",
        "title": "Punctuation dense prose",
        "text": "会议记录、旧照片、半张车票，以及那枚被磨得发亮的铜质钥匙，全都被摆在桌面上；每一样东西看起来都很普通，却又像是互相指向同一个答案。她试着把日期、地点和人名逐一对应，直到窗外的雨声忽然变大。",
        "focus": "顿号、分号、逗号密集文本的断句和节奏",
    },
    {
        "id": "chapter_transition",
        "title": "Chapter transition",
        "text": "第二章结束的时候，主角终于离开了那座停满旧船的码头。新的章节从一封迟到三年的回信开始，信纸边缘已经泛黄，墨迹却依然清晰。读者需要在这一段里听出时间跨度，也需要听出人物重新下定决心的变化。",
        "focus": "章节过渡、情绪变化、信息完整性",
    },
]

generated_paths = []
server_job_paths = []


def utc_now():
    return _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z")


def text_sha12(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


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


def request_bytes(method, path, timeout=300):
    request = urllib.request.Request(base + path, method=method)
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        chunks = []
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            chunks.append(chunk)
        return response.status, normalize_headers(response.headers), b"".join(chunks), time.perf_counter() - start


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


def raw_pcm_to_wav(pcm_bytes, path, sample_rate=32000, channels=1, sample_width=2):
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)


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


def assert_wav_info(info):
    assert info["channels"] == 1, info
    assert info["sample_width"] == 2, info
    assert info["sample_rate"] == 32000, info
    assert info["frames"] > 0, info


def safe_unlink(path):
    try:
        resolved = Path(path).resolve()
        resolved.relative_to(repo_root.resolve())
        if resolved.exists() and resolved.is_file():
            resolved.unlink()
    except (OSError, ValueError):
        pass


def cleanup_outputs():
    if not clean_outputs:
        return
    for path in generated_paths:
        safe_unlink(path)
    for path in server_job_paths:
        safe_unlink(path)


def wait_for_health():
    last_error = None
    for _ in range(120):
        try:
            status, _, health = request_json("GET", "/health", timeout=2)
            if status == 200 and health.get("status") == "ok":
                return
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Server did not become healthy: {last_error!r}")


def compact_headers(headers):
    return {
        "Content-Type": headers.get("content-type"),
        "X-Genie-Audio-Format": headers.get("x-genie-audio-format"),
        "X-Genie-Inner-Audio-Format": headers.get("x-genie-inner-audio-format"),
        "X-Genie-Stream-Mode": headers.get("x-genie-stream-mode"),
        "X-Genie-Sample-Rate": headers.get("x-genie-sample-rate"),
        "X-Genie-Channels": headers.get("x-genie-channels"),
        "X-Genie-Sample-Width": headers.get("x-genie-sample-width"),
    }


def verify_session_providers(runtime_info, expected_provider):
    loaded_models = runtime_info["loaded_models"].get(character, {})
    assert loaded_models, runtime_info["loaded_models"]
    for model_name, providers in loaded_models.items():
        assert expected_provider in providers, (model_name, providers)
    for shared_name, providers in runtime_info["shared_models"].items():
        if providers:
            assert expected_provider in providers, (shared_name, providers)


try:
    output_dir.mkdir(parents=True, exist_ok=True)
    wait_for_health()

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

    sample_reports = []
    for index, sample in enumerate(samples, start=1):
        sample_id = sample["id"]
        payload = {
            "character_name": character,
            "text": sample["text"],
            "split_sentence": True,
        }
        wav_path = output_dir / f"{index:02d}-{sample_id}-legado-buffered.wav"
        status, headers, body, elapsed = post_bytes(
            "/tts/legado.wav?wait_timeout=300&mode=buffered",
            payload,
            timeout=timeout_seconds,
        )
        wav_path.write_bytes(body)
        generated_paths.append(wav_path)
        assert status == 200
        assert headers.get("content-type", "").startswith("audio/wav"), headers
        assert headers.get("x-genie-audio-format") == "wav_pcm_s16le", headers
        assert headers.get("x-genie-inner-audio-format") == "pcm_s16le", headers
        assert headers.get("x-genie-stream-mode") == "buffered", headers
        assert headers.get("x-genie-sample-rate") == "32000", headers
        assert headers.get("x-genie-channels") == "1", headers
        assert headers.get("x-genie-sample-width") == "2", headers
        wav_info = inspect_wav(wav_path)
        assert_wav_info(wav_info)

        _, _, status_after = request_json("GET", "/status", timeout=60)
        last_reader = status_after["last_reader_request"]
        assert last_reader["endpoint"] == "/tts/legado.wav", last_reader
        assert last_reader["mode"] == "buffered", last_reader
        assert last_reader["status"] == "completed", last_reader
        assert last_reader["text_chars"] == len(sample["text"]), last_reader
        assert len(last_reader["text_sha256_12"]) == 12, last_reader
        assert "text" not in last_reader, last_reader

        sample_reports.append({
            "id": sample_id,
            "title": sample["title"],
            "focus": sample["focus"],
            "text_chars": len(sample["text"]),
            "text_sha256_12": text_sha12(sample["text"]),
            "endpoint": "/tts/legado.wav?wait_timeout=300&mode=buffered",
            "split_sentence": True,
            "status": status,
            "headers": compact_headers(headers),
            "bytes": len(body),
            "elapsed_seconds": elapsed,
            "wave": wav_info,
            "output": str(wav_path),
            "last_reader_request": last_reader,
            "needs_listening_review": True,
        })

    stream_report = None
    if include_stream:
        sample = samples[0]
        payload = {
            "character_name": character,
            "text": sample["text"],
            "split_sentence": True,
        }
        stream_path = output_dir / "00-stream-compatibility.wav"
        standardized_path = output_dir / "00-stream-compatibility-standardized.wav"
        status, headers, body, elapsed = post_bytes(
            "/tts/legado.wav?wait_timeout=300",
            payload,
            timeout=timeout_seconds,
        )
        stream_path.write_bytes(body)
        generated_paths.append(stream_path)
        generated_paths.append(standardized_path)
        assert status == 200
        assert headers.get("content-type", "").startswith("audio/wav"), headers
        assert headers.get("x-genie-audio-format") == "wav_stream_pcm_s16le", headers
        assert headers.get("x-genie-inner-audio-format") == "pcm_s16le", headers
        assert headers.get("x-genie-stream-mode") == "http_chunked", headers
        assert len(body) > 44 and body[:4] == b"RIFF" and body[8:12] == b"WAVE", len(body)
        pcm_body = body[44:]
        assert len(pcm_body) > 0 and len(pcm_body) % 2 == 0, len(pcm_body)
        raw_pcm_to_wav(pcm_body, standardized_path)
        wav_info = inspect_wav(standardized_path)
        assert_wav_info(wav_info)
        _, _, status_after = request_json("GET", "/status", timeout=60)
        last_reader = status_after["last_reader_request"]
        assert last_reader["mode"] == "stream", last_reader
        stream_report = {
            "sample_id": sample["id"],
            "status": status,
            "headers": compact_headers(headers),
            "bytes": len(body),
            "pcm_bytes": len(pcm_body),
            "elapsed_seconds": elapsed,
            "wave": wav_info,
            "output": str(stream_path),
            "standardized_output": str(standardized_path),
            "last_reader_request": last_reader,
        }

    job_report = None
    if include_job:
        job_text = "\n".join(sample["text"] for sample in samples)
        submit_status, _, submit_result = request_json("POST", "/jobs/tts", {
            "character_name": character,
            "text": job_text,
            "split_sentence": True,
        }, timeout=120)
        assert submit_status == 202, submit_result
        job_id = submit_result["job_id"]
        deadline = time.perf_counter() + timeout_seconds
        poll_count = 0
        while True:
            job_status, _, job = request_json("GET", f"/jobs/{job_id}", timeout=60)
            assert job_status == 200
            poll_count += 1
            if job["status"] in {"completed", "failed", "cancelled"}:
                break
            if time.perf_counter() > deadline:
                raise TimeoutError(f"Job {job_id} did not finish within {timeout_seconds} seconds")
            time.sleep(poll_seconds)
        if job["status"] != "completed":
            raise RuntimeError(f"Job {job_id} ended with status {job['status']}: {job.get('error_detail')}")
        if job.get("output_path"):
            server_job_paths.append(Path(job["output_path"]))

        download_status, headers, body, elapsed = request_bytes("GET", f"/jobs/{job_id}/wav", timeout=timeout_seconds)
        job_path = output_dir / f"job-{job_id}.wav"
        job_path.write_bytes(body)
        generated_paths.append(job_path)
        assert download_status == 200
        assert headers.get("x-genie-audio-format") == "wav_pcm_s16le", headers
        wav_info = inspect_wav(job_path)
        assert_wav_info(wav_info)
        job_report = {
            "job_id": job_id,
            "text_chars": len(job_text),
            "text_sha256_12": text_sha12(job_text),
            "poll_count": poll_count,
            "final_job": job,
            "download": {
                "status": download_status,
                "headers": compact_headers(headers),
                "bytes": len(body),
                "elapsed_seconds": elapsed,
                "wave": wav_info,
                "output": str(job_path),
            },
        }

    runtime_after = request_json("GET", "/runtime", timeout=120)[2]
    verify_session_providers(runtime_after, expected_provider)
    status_after_all = request_json("GET", "/status", timeout=60)[2]

    report = {
        "report_version": 1,
        "created_at_utc": utc_now(),
        "machine_validation_scope": "API behavior, WAV structure, runtime provider state, and reader/job diagnostics only. Chinese pronunciation, segmentation, prosody, and content completeness require human listening review.",
        "base_url": base,
        "runtime": runtime,
        "selected_providers": runtime_after["selected_providers"],
        "available_providers": runtime_after["available_providers"],
        "character": {
            "character_name": character,
            "language": language,
            "model_dir": str(model_dir),
            "reference_audio": str(reference_audio),
            "reference_text_sha256_12": text_sha12(reference_text),
        },
        "options": {
            "include_stream": include_stream,
            "include_job": include_job,
            "clean_outputs": clean_outputs,
            "poll_seconds": poll_seconds,
            "timeout_seconds": timeout_seconds,
        },
        "load_character": load_result,
        "set_reference_audio": ref_result,
        "samples": sample_reports,
        "stream": stream_report,
        "job": job_report,
        "status": {
            "busy_after_requests": status_after_all["busy"],
            "last_reader_request": status_after_all.get("last_reader_request"),
            "recent_reader_count": len(status_after_all["reader_requests"]["recent"]),
            "jobs": status_after_all.get("jobs"),
        },
        "provider_summary": {
            "loaded_models": runtime_after["loaded_models"].get(character, {}),
            "shared_models": runtime_after["shared_models"],
        },
        "listening_review_template": {
            "reviewer": "",
            "reviewed_at": "",
            "overall_result": "pass / needs_fix / blocked",
            "checks": [
                "spoken content matches input without obvious omissions or repeats",
                "sentence splitting and pauses are acceptable for long-form listening",
                "pronunciation and tone are acceptable for Chinese narration",
                "dialogue punctuation does not cause disruptive rhythm",
                "buffered Legado output plays to completion on target device",
            ],
            "notes": "",
        },
        "outputs_kept": not clean_outputs,
        "output_dir": str(output_dir),
    }
    report_path = output_dir / "chinese-listening-baseline-report.json"
    report["report_path"] = str(report_path)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
finally:
    cleanup_outputs()
'@

try {
    $clientScript | & $Python -
    if ($LASTEXITCODE -ne 0) {
        throw "Chinese listening baseline validation failed with exit code $LASTEXITCODE"
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
