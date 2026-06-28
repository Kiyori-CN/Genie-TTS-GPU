"""External Genie-TTS API client example.

This example intentionally uses only the Python standard library so it can be
copied into third-party tools without adding a requests dependency.
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
    "她合上手里的书，抬头望向窗外，决定把今天的计划重新整理一遍，"
    "然后继续完成那段漫长而细致的旅程。"
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


def post_bytes(base_url: str, path: str, payload: dict, timeout: int = 300) -> Tuple[bytes, Dict[str, str], float]:
    request = urllib.request.Request(
        base_url + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
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
        raise RuntimeError(f"POST {path} failed with HTTP {exc.code}: {body}") from exc


def raw_pcm_to_wav(raw_bytes: bytes, wav_path: Path, sample_rate: int, channels: int, sample_width: int) -> None:
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(raw_bytes)


def streaming_wav_pcm_bytes(stream_bytes: bytes) -> bytes:
    if len(stream_bytes) <= 44 or stream_bytes[:4] != b"RIFF" or stream_bytes[8:12] != b"WAVE":
        raise ValueError("Response is not a WAV stream with a 44-byte PCM header.")
    return stream_bytes[44:]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Call a running Genie-TTS FastAPI server.")
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
    parser.add_argument("--skip-load", action="store_true", help="Assume the character is already loaded.")
    parser.add_argument("--skip-reference", action="store_true", help="Assume reference audio is already configured.")
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

    payload = {
        "character_name": args.character,
        "text": args.text,
        "split_sentence": args.split_sentence,
    }

    raw_bytes, raw_headers, raw_elapsed = post_bytes(args.base_url, "/tts/raw", payload)
    raw_path = output_dir / f"{args.character}-api.raw"
    raw_wav_path = output_dir / f"{args.character}-api-from-raw.wav"
    raw_path.write_bytes(raw_bytes)
    raw_pcm_to_wav(
        raw_bytes,
        raw_wav_path,
        int(raw_headers.get("x-genie-sample-rate", "32000")),
        int(raw_headers.get("x-genie-channels", "1")),
        int(raw_headers.get("x-genie-sample-width", "2")),
    )

    stream_bytes, stream_headers, stream_elapsed = post_bytes(args.base_url, "/tts/legado.wav?wait_timeout=300", payload)
    stream_path = output_dir / f"{args.character}-api-legado-stream.wav"
    stream_wrapped_wav_path = output_dir / f"{args.character}-api-legado-stream-standardized.wav"
    stream_path.write_bytes(stream_bytes)
    raw_pcm_to_wav(
        streaming_wav_pcm_bytes(stream_bytes),
        stream_wrapped_wav_path,
        int(stream_headers.get("x-genie-sample-rate", "32000")),
        int(stream_headers.get("x-genie-channels", "1")),
        int(stream_headers.get("x-genie-sample-width", "2")),
    )

    wav_bytes, wav_headers, wav_elapsed = post_bytes(args.base_url, "/tts/wav", payload)
    wav_path = output_dir / f"{args.character}-api.wav"
    wav_path.write_bytes(wav_bytes)

    summary: Dict[str, Any] = {
        "base_url": args.base_url,
        "raw": {
            "headers": raw_headers,
            "bytes": len(raw_bytes),
            "elapsed_seconds": raw_elapsed,
            "raw_output": str(raw_path),
            "wav_wrapper_output": str(raw_wav_path),
        },
        "legado_stream_wav": {
            "headers": stream_headers,
            "bytes": len(stream_bytes),
            "pcm_bytes": max(0, len(stream_bytes) - 44),
            "elapsed_seconds": stream_elapsed,
            "stream_output": str(stream_path),
            "standardized_wav_output": str(stream_wrapped_wav_path),
        },
        "wav": {
            "headers": wav_headers,
            "bytes": len(wav_bytes),
            "elapsed_seconds": wav_elapsed,
            "output": str(wav_path),
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
