"""Queued background Genie-TTS job API client example.

This example uses only the Python standard library so it can be copied into
document conversion or offline audiobook tooling without adding dependencies.
For uninterrupted Legado reader playback, use /tts/legado.wav instead.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


DEFAULT_TEXT = (
    "清晨的城市逐渐苏醒，街边的灯光还没有完全熄灭。"
    "她合上手里的书，抬头望向窗外，决定把今天的计划重新整理一遍。"
    "为了模拟小说和文档朗读的实际场景，这段文本会被自动切分成多个句子，"
    "并连续生成可以下载的语音。随后，客户端会轮询后台任务进度，"
    "等待服务端写出完整的 WAV 文件，再把它保存到本地用于离线处理。"
)


def repo_default(path: str) -> str:
    repo_root = Path(__file__).resolve().parents[1]
    return str(repo_root / path)


def headers_to_dict(headers) -> Dict[str, str]:
    return {key.lower(): value for key, value in dict(headers).items()}


def request_json(base_url: str, method: str, path: str, payload: Optional[dict] = None, timeout: int = 120) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        base_url + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"{method} {path} failed with HTTP {exc.code}: {body}") from exc


def request_bytes(base_url: str, method: str, path: str, timeout: int = 300) -> Tuple[bytes, Dict[str, str], float]:
    request = urllib.request.Request(base_url + path, method=method)
    chunks = []
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks), headers_to_dict(response.headers), time.perf_counter() - start
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"{method} {path} failed with HTTP {exc.code}: {body}") from exc


def wait_for_job(base_url: str, job_id: str, poll_seconds: float, timeout_seconds: float) -> Dict[str, Any]:
    deadline = time.perf_counter() + timeout_seconds
    while True:
        job = request_json(base_url, "GET", f"/jobs/{job_id}")
        progress = job.get("progress") or {}
        parallel = job.get("parallel") or {}
        print(json.dumps({
            "job_id": job["job_id"],
            "status": job["status"],
            "stage": job["stage"],
            "message": job["message"],
            "generated_pcm_bytes": job["generated_pcm_bytes"],
            "segments": f"{progress.get('completed_segments', 0)}/{progress.get('total_segments', 0)}",
            "chars": f"{progress.get('completed_chars', 0)}/{progress.get('total_chars', 0)}",
            "percent": progress.get("percent"),
            "eta_seconds": progress.get("estimated_remaining_seconds"),
            "parallel": parallel,
            "output_bytes": job["output_bytes"],
            "elapsed_seconds": job["elapsed_seconds"],
        }, ensure_ascii=False))
        if job["status"] in {"completed", "failed", "cancelled"}:
            return job
        if time.perf_counter() > deadline:
            raise TimeoutError(f"Job {job_id} did not finish within {timeout_seconds} seconds")
        time.sleep(poll_seconds)


def inspect_wav(path: Path) -> Dict[str, Any]:
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Submit and download a queued Genie-TTS job.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--character", default="feibi")
    parser.add_argument(
        "--model-dir",
        default=repo_default(r"CharacterModels\v2ProPlus\feibi\tts_models"),
        help="Model directory path as seen by the API server.",
    )
    parser.add_argument(
        "--reference-audio",
        default=repo_default(r"CharacterModels\v2ProPlus\feibi\prompt_wav\zh_vo_Main_Linaxita_2_1_10_26.wav"),
        help="Reference audio path as seen by the API server.",
    )
    parser.add_argument("--reference-text", default="在此之前，请您务必继续享受旅居拉古那的时光。")
    parser.add_argument("--language", default="Chinese")
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--split-sentence", action="store_true", default=True)
    parser.add_argument("--no-split-sentence", dest="split_sentence", action="store_false")
    parser.add_argument("--parallel", dest="parallel_enabled", action="store_true", help="Enable CUDA job segment parallelism.")
    parser.add_argument("--parallel-workers", default="2", help="Requested CUDA job threads, for example 2, 4, 8, 12, or auto.")
    parser.add_argument("--skip-load", action="store_true", help="Assume the character is already loaded.")
    parser.add_argument("--skip-reference", action="store_true", help="Assume reference audio is already configured.")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    parser.add_argument("--timeout-seconds", type=float, default=600.0)
    parser.add_argument("--output-dir", default=repo_default("test"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("health=", request_json(args.base_url, "GET", "/health"))
    print("runtime=", json.dumps(request_json(args.base_url, "GET", "/runtime"), ensure_ascii=False, indent=2))

    if not args.skip_load:
        print("load_character=")
        print(request_json(args.base_url, "POST", "/load_character", {
            "character_name": args.character,
            "onnx_model_dir": args.model_dir,
            "language": args.language,
        }, timeout=180))

    if not args.skip_reference:
        print("set_reference_audio=")
        print(request_json(args.base_url, "POST", "/set_reference_audio", {
            "character_name": args.character,
            "audio_path": args.reference_audio,
            "audio_text": args.reference_text,
            "language": args.language,
        }, timeout=120))

    submitted = request_json(args.base_url, "POST", "/jobs/tts", {
        "character_name": args.character,
        "text": args.text,
        "split_sentence": args.split_sentence,
        "parallel_enabled": args.parallel_enabled,
        "parallel_workers": args.parallel_workers if args.parallel_enabled else 1,
    }, timeout=120)
    job_id = submitted["job_id"]
    print("submitted=", json.dumps(submitted, ensure_ascii=False, indent=2))

    job = wait_for_job(args.base_url, job_id, args.poll_seconds, args.timeout_seconds)
    if job["status"] != "completed":
        raise RuntimeError(f"Job {job_id} ended with status {job['status']}: {job.get('error_detail')}")

    wav_bytes, headers, download_elapsed = request_bytes(args.base_url, "GET", f"/jobs/{job_id}/wav")
    wav_path = output_dir / f"{args.character}-job-{job_id}.wav"
    wav_path.write_bytes(wav_bytes)
    wav_info = inspect_wav(wav_path)

    summary: Dict[str, Any] = {
        "job_id": job_id,
        "job": job,
        "download": {
            "headers": headers,
            "bytes": len(wav_bytes),
            "elapsed_seconds": download_elapsed,
            "output": str(wav_path),
            "wave": wav_info,
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
