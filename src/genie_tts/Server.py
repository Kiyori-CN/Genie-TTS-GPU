import asyncio
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import io
import ipaddress
import json
import locale
import os
from pathlib import Path
import queue
import re
import shutil
import sys
import socket
import struct
import subprocess
import threading
import time
from urllib.parse import parse_qs
import uuid
import wave
from typing import Any, AsyncIterator, Optional, Callable, Union, Dict, List
import logging

import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .Audio.ReferenceAudio import ReferenceAudio
from .Core.Inference import GENIE
from .Core.TTSPlayer import tts_player
from .ModelManager import model_manager
from .Profiling import profile_recorder, profile_span
from .Utils.Shared import context
from .Utils.Language import normalize_language
from .Utils.TextSplitter import TextSplitter

logger = logging.getLogger(__name__)

_reference_audios: Dict[str, dict] = {}
SUPPORTED_AUDIO_EXTS = {'.wav', '.flac', '.ogg', '.aiff', '.aif'}
RAW_AUDIO_FORMAT = "pcm_s16le"
RAW_AUDIO_MEDIA_TYPE = "application/octet-stream"
STREAM_WAV_AUDIO_FORMAT = "wav_stream_pcm_s16le"
LEGADO_DEFAULT_CHARACTER = "feibi"
REPO_ROOT = Path(__file__).resolve().parents[2]
WEBUI_DIR = Path(__file__).resolve().parent / "WebUI"
JOB_OUTPUT_DIR = REPO_ROOT / "UserData" / "Jobs"
WEBUI_USER_DATA_DIR = REPO_ROOT / "UserData" / "WebUI"
USER_CHARACTER_PRESETS_FILE = WEBUI_USER_DATA_DIR / "character-presets.json"
CHARACTER_MODELS_DIR = REPO_ROOT / "CharacterModels"
CONVERSION_OUTPUT_ROOT = CHARACTER_MODELS_DIR / "Converted"
START_WEBUI_SCRIPT = REPO_ROOT / "Scripts" / "start-webui.py"
PACKAGE_PYTHON_EXE = REPO_ROOT / "Runtime" / ".venv" / "Scripts" / "python.exe"
TERMINAL_JOB_STATUSES = {"completed", "failed", "cancelled"}
TERMINAL_CONVERSION_STATUSES = {"completed", "failed", "cancelled"}
TERMINAL_READER_STATUSES = {"completed", "failed", "interrupted", "rejected"}


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(str(raw).strip())
    except ValueError:
        logger.warning("Ignoring invalid integer environment value %s=%r", name, raw)
        return default
    return max(minimum, min(value, maximum))


ABSOLUTE_MAX_PARALLEL_WORKERS = 32
MAX_PARALLEL_WORKERS = _env_int("GENIE_TTS_MAX_PARALLEL_WORKERS", 8, 2, ABSOLUTE_MAX_PARALLEL_WORKERS)
DEFAULT_PARALLEL_WORKERS = min(
    MAX_PARALLEL_WORKERS,
    _env_int("GENIE_TTS_DEFAULT_PARALLEL_WORKERS", 2, 1, ABSOLUTE_MAX_PARALLEL_WORKERS),
)
DEFAULT_REFERENCE_TEXT = "在此之前，请您务必继续享受旅居拉古那的时光。"
DEFAULT_INPUT_TEXT = (
    "清晨的城市逐渐苏醒，街边的灯光还没有完全熄灭。"
    "她合上手里的书，抬头望向窗外，决定把今天的计划重新整理一遍。"
)
LANGUAGE_OPTIONS = ["Chinese", "English", "Japanese", "Hybrid-Chinese-English", "Korean"]
MEMORY_POLICY_NAME = "single_session_serial"
MEMORY_POLICY_NAME_ZH = "单会话串行"
MEMORY_POLICY_SUMMARY_ZH = "每个进程只允许一个 TTSPlayer 活跃会话；队列作业会先占用同一把会话锁。"
JOB_PARALLEL_REASON = (
    "Real parallel synthesis is available only for queued jobs on CUDA. "
    "Direct, stream, and reader paths keep the single-session model."
)
JOB_PARALLEL_REASON_ZH = "真实并行仅用于 CUDA 模式下的长文本队列作业；快速试听、流式和阅读路径保持单会话。"
JOB_PARALLEL_UNAVAILABLE_REASON = (
    "GPU job parallel synthesis requires CUDAExecutionProvider as the selected runtime provider."
)
JOB_PARALLEL_UNAVAILABLE_REASON_ZH = "GPU 并行作业需要当前运行时选择 CUDAExecutionProvider。"
JOB_ONLY_PARALLEL_REASON = (
    "Only queued jobs can safely split text, retry/cancel in the background, and reassemble ordered segments. "
    "Direct, stream, and reader calls must preserve immediate playback/response order."
)
JOB_ONLY_PARALLEL_REASON_ZH = (
    "只有队列作业能安全分段、后台取消/恢复，并按原文顺序合并音频。"
    "快速试听、流式和阅读调用必须保持即时播放和响应顺序。"
)
VRAM_POLICY_NOTE = (
    "CUDA memory is controlled by the NVIDIA driver and ONNX Runtime. "
    "This service can release idle sessions and tune job workers, but it cannot turn system RAM into CUDA VRAM."
)
VRAM_POLICY_NOTE_ZH = (
    "CUDA 显存由 NVIDIA 驱动和 ONNX Runtime 管理；本服务只能释放空闲会话、清理缓存并调节作业线程数，"
    "不能把系统内存变成 CUDA 显存。"
)

PARALLEL_WORKERS_INVALID_DETAIL = {
    "message": "parallel_workers must be an integer greater than 1 or 'auto'.",
    "message_zh": "parallel_workers 必须是大于 1 的整数或 auto。",
    "allowed_examples": ["2", "4", "8", "auto"],
}

app = FastAPI()
app.mount("/ui/assets", StaticFiles(directory=str(WEBUI_DIR), check_dir=False), name="webui_assets")

IPV4_RE = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
RFC1918_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)
VIRTUAL_ADAPTER_MARKERS = (
    "loopback",
    "vethernet",
    "virtual",
    "vmware",
    "virtualbox",
    "bluetooth",
    "tunnel",
    "tap",
    "wsl",
    "hyper-v",
    "meta",
)


def is_lan_ipv4_address(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return ip.version == 4 and any(ip in network for network in RFC1918_NETWORKS)


def adapter_looks_virtual(adapter_name: str) -> bool:
    lowered = adapter_name.lower()
    return any(marker in lowered for marker in VIRTUAL_ADAPTER_MARKERS)


def add_lan_address(addresses: List[str], value: str) -> None:
    if is_lan_ipv4_address(value) and value not in addresses:
        addresses.append(value)


def ipv4_candidates(text: str) -> List[str]:
    return IPV4_RE.findall(text)


def ipconfig_lan_ipv4_addresses() -> List[str]:
    addresses: List[str] = []
    try:
        completed = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            encoding=locale.getpreferredencoding(False),
            errors="replace",
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return addresses

    blocks = completed.stdout.replace("\r\n", "\n").split("\n\n")
    for block in blocks:
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if not lines or not lines[0].rstrip().endswith(":"):
            continue
        adapter_name = lines[0].rstrip(":")
        if adapter_looks_virtual(adapter_name):
            continue

        gateway_lines: List[str] = []
        for index, line in enumerate(lines):
            if "Gateway" in line or "网关" in line:
                gateway_lines.append(line)
                if index + 1 < len(lines) and lines[index + 1].startswith(" "):
                    gateway_lines.append(lines[index + 1])
        has_lan_gateway = any(
            is_lan_ipv4_address(part)
            for line in gateway_lines
            for part in ipv4_candidates(line)
        )
        if not has_lan_gateway:
            continue

        for line in lines:
            if "IPv4" not in line:
                continue
            for part in ipv4_candidates(line):
                add_lan_address(addresses, part)
    return addresses


def socket_lan_ipv4_addresses() -> List[str]:
    addresses: List[str] = []
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET, socket.SOCK_DGRAM):
            add_lan_address(addresses, item[4][0])
    except OSError:
        pass
    return addresses


def get_lan_ipv4_addresses() -> List[str]:
    """Return current LAN IPv4 addresses for displaying access URLs."""
    addresses: List[str] = []
    for address in ipconfig_lan_ipv4_addresses() or socket_lan_ipv4_addresses():
        add_lan_address(addresses, address)
    return addresses


def access_urls_for_request(request: Request) -> Dict[str, object]:
    scheme = request.url.scheme
    port = request.url.port or (443 if request.url.scheme == "https" else 80)
    lan_addresses = get_lan_ipv4_addresses()
    local_api_base_url = f"{scheme}://127.0.0.1:{port}"
    lan_api_base_urls = [f"{scheme}://{address}:{port}" for address in lan_addresses]
    return {
        "api_base_url": str(request.base_url).rstrip("/"),
        "local_api_base_url": local_api_base_url,
        "lan_api_base_urls": lan_api_base_urls,
        "local_url": f"{local_api_base_url}/ui",
        "lan_urls": [f"{base_url}/ui" for base_url in lan_api_base_urls],
        "lan_ipv4_addresses": lan_addresses,
    }


def infer_language_from_reference(text: str, wav_name: str = "") -> str:
    sample = f"{text or ''} {wav_name or ''}"
    if re.search(r"[\u3040-\u30ff]", sample):
        return "Japanese"
    if re.search(r"[\u4e00-\u9fff]", sample):
        return "Chinese"
    if re.search(r"[\uac00-\ud7af]", sample):
        return "Korean"
    return "English"


def load_prompt_wav_manifest(character_root: Path) -> Dict[str, Dict[str, str]]:
    manifest_path = character_root / "prompt_wav.json"
    if not manifest_path.exists():
        return {}
    try:
        with manifest_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        logger.warning("Failed to read prompt_wav manifest: %s", manifest_path, exc_info=True)
        return {}
    if not isinstance(data, dict):
        return {}
    result: Dict[str, Dict[str, str]] = {}
    for key, value in data.items():
        if not isinstance(value, dict):
            continue
        wav_name = str(value.get("wav") or "").strip()
        if not wav_name:
            continue
        result[str(key)] = {
            "wav": wav_name,
            "text": str(value.get("text") or ""),
        }
    return result


def reference_candidates_for_character(character_root: Path) -> List[Dict[str, object]]:
    prompt_dir = character_root / "prompt_wav"
    manifest = load_prompt_wav_manifest(character_root)
    candidates: List[Dict[str, object]] = []
    seen_paths = set()

    for name, item in manifest.items():
        audio_path = prompt_dir / item["wav"]
        if not audio_path.exists():
            continue
        path_text = str(audio_path)
        seen_paths.add(path_text.lower())
        text = item.get("text", "")
        candidates.append({
            "name": name,
            "label": f"{name} / {audio_path.name}",
            "audio_path": path_text,
            "audio_text": text,
            "language": infer_language_from_reference(text, audio_path.name),
            "exists": True,
        })

    if prompt_dir.is_dir():
        for audio_path in sorted(prompt_dir.iterdir(), key=lambda item: item.name.lower()):
            if not audio_path.is_file() or audio_path.suffix.lower() not in SUPPORTED_AUDIO_EXTS:
                continue
            path_text = str(audio_path)
            if path_text.lower() in seen_paths:
                continue
            candidates.append({
                "name": audio_path.stem,
                "label": audio_path.name,
                "audio_path": path_text,
                "audio_text": "",
                "language": infer_language_from_reference("", audio_path.name),
                "exists": True,
            })
    return candidates


def sort_character_key(item: Dict[str, object]) -> tuple:
    name = str(item.get("name") or "")
    source_rank = 1 if item.get("source") == "user" else 0
    return (
        source_rank,
        0 if name == LEGADO_DEFAULT_CHARACTER else 1,
        str(item.get("family") or ""),
        name,
    )


def preset_id_for(name: str, family: str = "", source: str = "auto") -> str:
    raw = f"{source}:{family}:{name}".lower()
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def normalize_character_preset(raw: Dict[str, object], source: str = "user") -> Optional[Dict[str, object]]:
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("name") or raw.get("character_name") or "").strip()
    model_dir = str(raw.get("onnx_model_dir") or raw.get("model_dir") or "").strip()
    if not name or not model_dir:
        return None
    language = normalize_language(str(raw.get("language") or "Chinese"))
    family = str(raw.get("family") or "").strip()
    reference_audio_path = str(raw.get("reference_audio_path") or raw.get("audio_path") or "").strip()
    reference_text = str(raw.get("reference_text") or raw.get("audio_text") or "").strip()
    reference_name = str(raw.get("reference_name") or "").strip()
    preset_id = str(raw.get("id") or raw.get("preset_id") or preset_id_for(name, family, source)).strip()
    label = str(raw.get("label") or "").strip()
    if not label:
        label = f"{name} / {family}" if family else name
    references = raw.get("reference_options")
    if not isinstance(references, list):
        references = []
    if reference_audio_path and not any(
            str(item.get("audio_path") or "") == reference_audio_path
            for item in references
            if isinstance(item, dict)
    ):
        references = [{
            "name": reference_name or Path(reference_audio_path).stem,
            "label": f"{reference_name or Path(reference_audio_path).stem} / {Path(reference_audio_path).name}",
            "audio_path": reference_audio_path,
            "audio_text": reference_text,
            "language": language,
            "exists": Path(reference_audio_path).exists(),
        }, *references]
    return {
        "id": preset_id,
        "name": name,
        "label": label,
        "family": family,
        "root_dir": str(raw.get("root_dir") or Path(model_dir).parent),
        "onnx_model_dir": model_dir,
        "language": language,
        "reference_audio_path": reference_audio_path,
        "reference_text": reference_text,
        "reference_name": reference_name,
        "reference_options": references,
        "source": source,
        "deletable": source == "user",
    }


def discover_character_presets() -> List[Dict[str, object]]:
    presets: List[Dict[str, object]] = []
    if not CHARACTER_MODELS_DIR.is_dir():
        return presets

    for tts_models_dir in sorted(CHARACTER_MODELS_DIR.rglob("tts_models"), key=lambda item: str(item).lower()):
        if not tts_models_dir.is_dir():
            continue
        if not any(child.suffix.lower() == ".onnx" for child in tts_models_dir.iterdir() if child.is_file()):
            continue
        character_root = tts_models_dir.parent
        character_name = character_root.name
        try:
            family = str(character_root.relative_to(CHARACTER_MODELS_DIR).parent)
        except ValueError:
            family = ""
        if family == ".":
            family = ""
        references = reference_candidates_for_character(character_root)
        default_reference = next((item for item in references if item["name"] == "Normal"), None)
        if default_reference is None and references:
            default_reference = references[0]
        language = str(default_reference.get("language")) if default_reference else "Chinese"
        presets.append({
            "id": preset_id_for(character_name, family, "auto"),
            "name": character_name,
            "label": f"{character_name} / {family}" if family else character_name,
            "family": family,
            "root_dir": str(character_root),
            "onnx_model_dir": str(tts_models_dir),
            "language": language,
            "reference_audio_path": str(default_reference.get("audio_path")) if default_reference else "",
            "reference_text": str(default_reference.get("audio_text")) if default_reference else "",
            "reference_name": str(default_reference.get("name")) if default_reference else "",
            "reference_options": references,
            "source": "auto",
            "deletable": False,
        })

    presets.sort(key=sort_character_key)
    return presets


def load_user_character_presets() -> List[Dict[str, object]]:
    if not USER_CHARACTER_PRESETS_FILE.exists():
        return []
    try:
        data = json.loads(USER_CHARACTER_PRESETS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("Failed to read WebUI character presets: %s", USER_CHARACTER_PRESETS_FILE, exc_info=True)
        return []
    raw_items = data.get("presets") if isinstance(data, dict) else data
    if not isinstance(raw_items, list):
        return []
    result: List[Dict[str, object]] = []
    seen: set[str] = set()
    for raw in raw_items:
        preset = normalize_character_preset(raw, source="user")
        if not preset:
            continue
        preset_id = str(preset["id"])
        if preset_id in seen:
            continue
        seen.add(preset_id)
        result.append(preset)
    result.sort(key=sort_character_key)
    return result


def save_user_character_presets(presets: List[Dict[str, object]]) -> None:
    WEBUI_USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    clean_presets = [
        normalize_character_preset(preset, source="user")
        for preset in presets
    ]
    clean_presets = [preset for preset in clean_presets if preset]
    payload = {
        "version": 1,
        "updated_at": utc_now(),
        "presets": clean_presets,
    }
    USER_CHARACTER_PRESETS_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def merged_character_presets() -> List[Dict[str, object]]:
    auto_presets = discover_character_presets()
    user_presets = load_user_character_presets()
    merged = [*auto_presets, *user_presets]
    merged.sort(key=sort_character_key)
    return merged


def default_character_preset(presets: List[Dict[str, object]]) -> Dict[str, object]:
    default = next((item for item in presets if item.get("name") == LEGADO_DEFAULT_CHARACTER), None)
    if default:
        return default
    if presets:
        return presets[0]
    default_character_root = CHARACTER_MODELS_DIR / "v2ProPlus" / LEGADO_DEFAULT_CHARACTER
    return {
        "id": preset_id_for(LEGADO_DEFAULT_CHARACTER, "v2ProPlus", "auto"),
        "name": LEGADO_DEFAULT_CHARACTER,
        "label": "feibi / v2ProPlus",
        "family": "v2ProPlus",
        "root_dir": str(default_character_root),
        "onnx_model_dir": str(default_character_root / "tts_models"),
        "language": "Chinese",
        "reference_audio_path": str(default_character_root / "prompt_wav" / "zh_vo_Main_Linaxita_2_1_10_26.wav"),
        "reference_text": DEFAULT_REFERENCE_TEXT,
        "reference_name": "Normal",
        "reference_options": [{
            "name": "Normal",
            "label": "Normal / zh_vo_Main_Linaxita_2_1_10_26.wav",
            "audio_path": str(default_character_root / "prompt_wav" / "zh_vo_Main_Linaxita_2_1_10_26.wav"),
            "audio_text": DEFAULT_REFERENCE_TEXT,
            "language": "Chinese",
            "exists": (default_character_root / "prompt_wav" / "zh_vo_Main_Linaxita_2_1_10_26.wav").exists(),
        }],
        "source": "auto",
        "deletable": False,
    }


def current_listen_config(request: Optional[Request] = None) -> Dict[str, object]:
    current_port = int(os.environ.get("GENIE_WEBUI_PORT") or (request.url.port if request else 8000) or 8000)
    current_host = os.environ.get("GENIE_WEBUI_HOST", "")
    if not current_host:
        host_header = request.headers.get("host", "") if request else ""
        request_host = host_header.rsplit(":", 1)[0] if host_header else ""
        current_host = "0.0.0.0" if request_host not in {"127.0.0.1", "localhost"} else "127.0.0.1"
    runtime_mode = os.environ.get("GENIE_WEBUI_RUNTIME") or model_manager.get_runtime_info().get("runtime_mode", "cuda")
    lan_addresses = get_lan_ipv4_addresses()
    host_options = [
        {
            "value": "0.0.0.0",
            "label": "0.0.0.0 / LAN",
            "description": "Listen on all IPv4 interfaces for local and LAN clients.",
            "recommended": True,
        },
        {
            "value": "127.0.0.1",
            "label": "127.0.0.1 / local only",
            "description": "Listen only on this PC; Android reader clients cannot reach it.",
            "recommended": False,
        },
    ]
    for address in lan_addresses:
        host_options.append({
            "value": address,
            "label": f"{address} / specific LAN IP",
            "description": "Bind to this network adapter only.",
            "recommended": False,
        })
    return {
        "host": current_host,
        "port": current_port,
        "runtime": runtime_mode,
        "restart_supported": START_WEBUI_SCRIPT.exists(),
        "restart_script": str(START_WEBUI_SCRIPT),
        "python": str(PACKAGE_PYTHON_EXE if PACKAGE_PYTHON_EXE.exists() else Path(sys.executable)),
        "host_options": host_options,
        "port_options": [8000, 7860, 5000, 0],
        "lan_ipv4_addresses": lan_addresses,
        "restart_note": "Changing host or port starts a new package-local WebUI process and then stops this process.",
    }


def service_busy() -> bool:
    tts_status = tts_player.status_snapshot()
    job_status = job_manager.status_snapshot()
    reader_status = reader_request_tracker.snapshot()
    return bool(
        tts_status["session_active"]
        or job_status["has_active_job"]
        or reader_status["active_count"]
        or conversion_job_manager.has_active_job()
    )


def legado_jslib(base_url: str, character_name: str, mode: str) -> str:
    mode_query = "&mode=buffered" if mode == "buffered" else ""
    return (
        "function genieTtsUrl(speakText, speakSpeed) {\n"
        f"    var baseUrl = '{base_url}';\n"
        "    var body = JSON.stringify({\n"
        f"        character_name: '{character_name}',\n"
        "        text: String(speakText || ''),\n"
        "        split_sentence: true\n"
        "    });\n"
        "    var option = {\n"
        "        method: 'POST',\n"
        "        headers: {'Content-Type': 'application/json'},\n"
        "        body: body\n"
        "    };\n"
        f"    return baseUrl + '/tts/legado.wav?wait_timeout=300{mode_query},' + JSON.stringify(option);\n"
        "}\n"
    )


def legado_json_template(base_url: str, character_name: str, mode: str) -> Dict[str, str]:
    mode_label = "Buffered" if mode == "buffered" else "Stream"
    return {
        "name": f"Genie-TTS {character_name} {mode_label}",
        "url": "@js:genieTtsUrl(speakText, speakSpeed);",
        "contentType": "audio/wav",
        "concurrentRate": "1500",
        "enabledCookieJar": False,
        "jsLib": legado_jslib(base_url, character_name, mode),
    }


def legado_copy_fields(template: Dict[str, str]) -> List[Dict[str, str]]:
    return [
        {"key": "name", "label": "name", "value": template.get("name", "")},
        {"key": "url", "label": "url", "value": template.get("url", "")},
        {"key": "contentType", "label": "Content-Type", "value": template.get("contentType", "")},
        {"key": "concurrentRate", "label": "concurrentRate", "value": template.get("concurrentRate", "")},
    ]


def reader_webui_config(access: Dict[str, object], character_name: str) -> Dict[str, object]:
    local_base = str(access.get("local_api_base_url") or access.get("api_base_url") or "").rstrip("/")
    lan_bases = [str(item).rstrip("/") for item in access.get("lan_api_base_urls") or []]
    lan_base = lan_bases[0] if lan_bases else ""
    template_base = lan_base or local_base
    buffered_suffix = "/tts/legado.wav?wait_timeout=300&mode=buffered"
    stream_suffix = "/tts/legado.wav?wait_timeout=300"
    recommended_template = legado_json_template(template_base, character_name, "buffered") if template_base else {}
    stream_template = legado_json_template(template_base, character_name, "stream") if template_base else {}
    return {
        "settings": {
            "character_name": character_name,
            "split_sentence": True,
            "wait_timeout_seconds": 300,
            "recommended_mode": "buffered",
            "stream_mode": "stream",
        },
        "urls": {
            "api_base_url": str(access.get("api_base_url") or ""),
            "local_api_base_url": local_base,
            "lan_api_base_url": lan_base,
            "lan_api_base_urls": lan_bases,
            "legado_buffered_url": f"{template_base}{buffered_suffix}" if template_base else buffered_suffix,
            "legado_stream_url": f"{template_base}{stream_suffix}" if template_base else stream_suffix,
        },
        "templates": {
            "recommended_jslib": legado_jslib(template_base, character_name, "buffered") if template_base else "",
            "recommended_json": recommended_template,
            "recommended_fields": legado_copy_fields(recommended_template) if recommended_template else [],
            "stream_jslib": legado_jslib(template_base, character_name, "stream") if template_base else "",
            "stream_json": stream_template,
            "stream_fields": legado_copy_fields(stream_template) if stream_template else [],
        },
    }


def nvidia_smi_candidate_paths() -> List[Path]:
    candidates = [
        Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "nvidia-smi.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "NVIDIA Corporation" / "NVSMI" / "nvidia-smi.exe",
        Path(os.environ.get("ProgramW6432", r"C:\Program Files")) / "NVIDIA Corporation" / "NVSMI" / "nvidia-smi.exe",
    ]
    result: List[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = str(candidate).lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        if candidate.exists():
            result.append(candidate)
    return result


def sample_nvidia_gpu_memory() -> Dict[str, object]:
    nvidia_smi_paths = nvidia_smi_candidate_paths()
    if not nvidia_smi_paths:
        return {
            "available": False,
            "source": "nvidia-smi",
            "error": "nvidia-smi.exe was not found in known NVIDIA install locations.",
            "gpus": [],
        }

    executable = nvidia_smi_paths[0]
    query = "index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu"
    try:
        completed = subprocess.run(
            [str(executable), f"--query-gpu={query}", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=4,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "available": False,
            "source": str(executable),
            "error": str(exc),
            "gpus": [],
        }

    if completed.returncode != 0:
        return {
            "available": False,
            "source": str(executable),
            "error": completed.stderr.strip() or completed.stdout.strip() or f"nvidia-smi exited with {completed.returncode}",
            "gpus": [],
        }

    gpus: List[Dict[str, object]] = []
    for row in csv.reader(io.StringIO(completed.stdout)):
        if len(row) < 7:
            continue
        index, name, total, used, free, utilization, temperature = [item.strip() for item in row[:7]]
        try:
            total_mib = int(float(total))
            used_mib = int(float(used))
            free_mib = int(float(free))
            utilization_percent = int(float(utilization))
            temperature_c = int(float(temperature))
        except ValueError:
            continue
        gpus.append({
            "index": index,
            "name": name,
            "memory_total_mib": total_mib,
            "memory_used_mib": used_mib,
            "memory_free_mib": free_mib,
            "memory_used_percent": round((used_mib / total_mib * 100.0), 1) if total_mib else None,
            "utilization_gpu_percent": utilization_percent,
            "temperature_c": temperature_c,
        })

    return {
        "available": bool(gpus),
        "source": str(executable),
        "error": None if gpus else "nvidia-smi returned no GPU rows.",
        "gpus": gpus,
    }


_LAST_PROCESS_CPU_SAMPLE: Optional[tuple[float, float]] = None
_LAST_SYSTEM_CPU_SAMPLE: Optional[tuple[int, int]] = None


def _filetime_to_int(value) -> int:
    return (int(value.dwHighDateTime) << 32) + int(value.dwLowDateTime)


def sample_system_cpu_percent() -> Optional[float]:
    global _LAST_SYSTEM_CPU_SAMPLE
    if not sys.platform.startswith("win"):
        return None
    try:
        import ctypes
        from ctypes import wintypes

        idle_time = wintypes.FILETIME()
        kernel_time = wintypes.FILETIME()
        user_time = wintypes.FILETIME()
        if not ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(idle_time),
                ctypes.byref(kernel_time),
                ctypes.byref(user_time),
        ):
            return None
        idle = _filetime_to_int(idle_time)
        total = _filetime_to_int(kernel_time) + _filetime_to_int(user_time)
        if _LAST_SYSTEM_CPU_SAMPLE is None:
            _LAST_SYSTEM_CPU_SAMPLE = (idle, total)
            return None
        last_idle, last_total = _LAST_SYSTEM_CPU_SAMPLE
        _LAST_SYSTEM_CPU_SAMPLE = (idle, total)
        total_delta = total - last_total
        idle_delta = idle - last_idle
        if total_delta <= 0:
            return None
        return round(max(0.0, min(100.0, (1.0 - idle_delta / total_delta) * 100.0)), 1)
    except Exception:
        return None


def sample_process_system_usage() -> Dict[str, object]:
    global _LAST_PROCESS_CPU_SAMPLE
    now_wall = time.perf_counter()
    now_cpu = time.process_time()
    cpu_percent = None
    if _LAST_PROCESS_CPU_SAMPLE is not None:
        last_wall, last_cpu = _LAST_PROCESS_CPU_SAMPLE
        elapsed_wall = max(1e-6, now_wall - last_wall)
        cpu_count = max(1, os.cpu_count() or 1)
        cpu_percent = round(max(0.0, (now_cpu - last_cpu) / elapsed_wall / cpu_count * 100.0), 1)
    _LAST_PROCESS_CPU_SAMPLE = (now_wall, now_cpu)

    process_memory = {"available": False}
    if sys.platform.startswith("win"):
        try:
            import ctypes
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            psapi = ctypes.WinDLL("psapi.dll")
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
                wintypes.DWORD,
            ]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            if psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                rss_bytes = int(counters.WorkingSetSize)
                process_memory = {
                    "available": True,
                    "rss_bytes": rss_bytes,
                    "rss_mib": round(rss_bytes / 1024 / 1024, 1),
                    "peak_rss_mib": round(int(counters.PeakWorkingSetSize) / 1024 / 1024, 1),
                }
        except Exception:
            process_memory = {"available": False}
    else:
        try:
            import resource
            max_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            rss_bytes = int(max_rss) * 1024
            process_memory = {
                "available": True,
                "rss_bytes": rss_bytes,
                "rss_mib": round(rss_bytes / 1024 / 1024, 1),
            }
        except Exception:
            process_memory = {"available": False}

    system_memory = {"available": False}
    if sys.platform.startswith("win"):
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                used = int(status.ullTotalPhys - status.ullAvailPhys)
                total = int(status.ullTotalPhys)
                system_memory = {
                    "available": True,
                    "memory_load_percent": int(status.dwMemoryLoad),
                    "total_bytes": total,
                    "available_bytes": int(status.ullAvailPhys),
                    "used_bytes": used,
                    "total_mib": round(total / 1024 / 1024, 1),
                    "used_mib": round(used / 1024 / 1024, 1),
                    "available_mib": round(int(status.ullAvailPhys) / 1024 / 1024, 1),
                }
        except Exception:
            system_memory = {"available": False}

    return {
        "process_cpu_percent": cpu_percent,
        "system_cpu_percent": sample_system_cpu_percent(),
        "process_memory": process_memory,
        "system_memory": system_memory,
    }


def reference_cache_size() -> int:
    cache = getattr(ReferenceAudio, "_prompt_cache", None)
    try:
        return len(cache) if cache is not None else 0
    except TypeError:
        return 0


def cuda_job_parallel_available() -> bool:
    runtime = model_manager.get_runtime_info()
    selected = runtime.get("selected_providers") or []
    return bool(selected and selected[0] == "CUDAExecutionProvider")


def character_sessions_use_cuda(character_name: str) -> Optional[bool]:
    model = model_manager.get(character_name)
    if model is None:
        return None
    sessions = [
        model.T2S_ENCODER,
        model.T2S_FIRST_STAGE_DECODER,
        model.T2S_STAGE_DECODER,
        model.VITS,
        model.PROMPT_ENCODER,
    ]
    providers = [
        session.get_providers()
        for session in sessions
        if session is not None
    ]
    if not providers:
        return None
    return all(provider_list and provider_list[0] == "CUDAExecutionProvider" for provider_list in providers)


def cuda_parallel_available_for_character(character_name: str) -> bool:
    if not cuda_job_parallel_available():
        return False
    session_cuda = character_sessions_use_cuda(character_name)
    return session_cuda is not False


def job_parallel_capability() -> Dict[str, object]:
    available = cuda_job_parallel_available()
    worker_options = [str(value) for value in range(2, MAX_PARALLEL_WORKERS + 1)]
    return {
        "configuration_supported": available,
        "execution_supported": available,
        "strategy": "gpu_segment_parallel" if available else "single_session_serial",
        "default_workers": DEFAULT_PARALLEL_WORKERS if available else 1,
        "max_workers": MAX_PARALLEL_WORKERS,
        "absolute_max_workers": ABSOLUTE_MAX_PARALLEL_WORKERS,
        "custom_workers_supported": True,
        "worker_options": worker_options + ["auto"],
        "reason": JOB_PARALLEL_REASON if available else JOB_PARALLEL_UNAVAILABLE_REASON,
        "reason_zh": JOB_PARALLEL_REASON_ZH if available else JOB_PARALLEL_UNAVAILABLE_REASON_ZH,
    }


def runtime_memory_policy_snapshot(sample_gpu: bool = True) -> Dict[str, object]:
    runtime = model_manager.get_runtime_info()
    selected = runtime.get("selected_providers") or []
    selected_primary = selected[0] if selected else None
    loaded_characters = runtime.get("loaded_characters") or []
    shared_models = runtime.get("shared_models") or {}
    gpu_memory = sample_nvidia_gpu_memory() if sample_gpu else {
        "available": False,
        "source": "not_sampled",
        "error": None,
        "gpus": [],
    }
    system_usage = sample_process_system_usage()
    parallel_capability = job_parallel_capability()
    busy = service_busy()

    return {
        "status": "ok",
        "policy": {
            "name": MEMORY_POLICY_NAME,
            "name_zh": MEMORY_POLICY_NAME_ZH,
            "summary": "One active TTSPlayer session per process; queued jobs run through the same session lock.",
            "summary_zh": MEMORY_POLICY_SUMMARY_ZH,
            "busy": busy,
            "loaded_character_count": len(loaded_characters),
            "loaded_characters": loaded_characters,
            "shared_models_loaded": [name for name, providers in shared_models.items() if providers],
            "reference_cache_size": reference_cache_size(),
            "vram_note": VRAM_POLICY_NOTE,
            "vram_note_zh": VRAM_POLICY_NOTE_ZH,
        },
        "gpu_memory": gpu_memory,
        "system_usage": system_usage,
        "runtime": {
            "runtime_mode": runtime.get("runtime_mode"),
            "selected_provider": selected_primary,
            "selected_providers": selected,
            "available_providers": runtime.get("available_providers") or [],
        },
        "parallel": {
            "direct_stream_reader": "single_session_only",
            "job_strategy": parallel_capability["strategy"],
            **parallel_capability,
            "job_only_reason": JOB_ONLY_PARALLEL_REASON,
            "job_only_reason_zh": JOB_ONLY_PARALLEL_REASON_ZH,
        },
        "actions": {
            "refresh": {"enabled": True},
            "release_idle_sessions": {
                "enabled": not busy,
                "blocked_reason": "Service is busy." if busy else None,
                "blocked_reason_zh": "服务忙碌。" if busy else None,
            },
            "clear_reference_cache": {"enabled": True},
        },
        "recommendations": [
            "Use /jobs/tts for long text so output order, cancellation, and recovery can be managed by job state.",
            "Release idle sessions before switching runtime or loading another large character.",
            "Raise worker count only after measuring VRAM headroom and same-text job duration.",
            "CUDA cannot borrow system RAM as VRAM through this API; reduce workers if VRAM pressure appears.",
        ],
        "recommendations_zh": [
            "长文本优先使用 /jobs/tts，让输出顺序、取消和恢复都由作业状态管理。",
            "切换运行时或加载其他大角色前，先释放空闲会话。",
            "提高线程数前，先测量显存余量和同一文本的作业耗时。",
            "本 API 不能让 CUDA 借用系统内存当显存；出现显存压力时应降低线程数。",
        ],
    }


def endpoint_catalog() -> List[Dict[str, str]]:
    return [
        {
            "method": "GET",
            "path": "/health",
            "purpose_zh": "进程健康检查。",
            "purpose_en": "Process health check.",
            "response_zh": "JSON 状态。",
            "response_en": "JSON status.",
            "use_case_zh": "探活、启动验证。",
            "use_case_en": "Liveness and startup checks.",
        },
        {
            "method": "GET",
            "path": "/runtime",
            "purpose_zh": "查看运行模式、可用提供方、已加载模型和实际会话提供方。",
            "purpose_en": "Inspect runtime mode, providers, loaded models, and actual session providers.",
            "response_zh": "JSON 运行时快照。",
            "response_en": "JSON runtime snapshot.",
            "use_case_zh": "确认 CUDA 或 CPU 实际是否生效。",
            "use_case_en": "Confirm whether CUDA or CPU is actually active.",
        },
        {
            "method": "GET",
            "path": "/characters",
            "purpose_zh": "扫描本地 CharacterModels 并合并用户手动预设。",
            "purpose_en": "Scan local CharacterModels and merge user-created presets.",
            "response_zh": "JSON 预设、模型目录和参考音频候选。",
            "response_en": "JSON presets, model directories, and reference choices.",
            "use_case_zh": "WebUI 下拉框、自动识别和一键切换角色。",
            "use_case_en": "WebUI dropdowns, auto discovery, and one-click switching.",
        },
        {
            "method": "POST",
            "path": "/characters/presets",
            "purpose_zh": "保存当前 WebUI 角色、模型、语言和参考音频为手动预设。",
            "purpose_en": "Save the current WebUI character, model, language, and reference audio as a user preset.",
            "response_zh": "JSON 预设和合并后的列表。",
            "response_en": "JSON saved preset and merged list.",
            "use_case_zh": "自定义角色组合后持久化，下次打开仍可套用。",
            "use_case_en": "Persist custom voice combinations for later reuse.",
        },
        {
            "method": "DELETE",
            "path": "/characters/presets/{preset_id}",
            "purpose_zh": "删除手动预设；自动扫描角色不会被删除。",
            "purpose_en": "Delete a user preset; auto-discovered characters are not removed.",
            "response_zh": "JSON 删除结果和合并后的列表。",
            "response_en": "JSON deletion result and merged list.",
            "use_case_zh": "清理用户自建预设。",
            "use_case_en": "Clean up user-created presets.",
        },
        {
            "method": "POST",
            "path": "/convert/gpt-sovits/scan",
            "purpose_zh": "扫描本机 GPT-SoVITS V2/V2ProPlus 文件夹，匹配 .ckpt 和 .pth。",
            "purpose_en": "Scan local GPT-SoVITS V2/V2ProPlus folders and match .ckpt/.pth pairs.",
            "response_zh": "JSON 扫描结果、模型类型和输出目录。",
            "response_en": "JSON scan results, detected model type, and output directories.",
            "use_case_zh": "转换前确认输入文件夹是否有效。",
            "use_case_en": "Validate conversion folders before submitting a job.",
        },
        {
            "method": "POST",
            "path": "/convert/gpt-sovits",
            "purpose_zh": "提交 GPT-SoVITS 到 GENIE ONNX 格式的后台转换任务。",
            "purpose_en": "Submit a background GPT-SoVITS to GENIE ONNX conversion job.",
            "response_zh": "202 JSON，包含转换作业 ID。",
            "response_en": "202 JSON with conversion job ID.",
            "use_case_zh": "把训练得到的 .ckpt/.pth 导出为 tts_models。",
            "use_case_en": "Export trained .ckpt/.pth pairs into tts_models.",
        },
        {
            "method": "GET",
            "path": "/convert/gpt-sovits/jobs",
            "purpose_zh": "列出近期转换任务。",
            "purpose_en": "List recent conversion jobs.",
            "response_zh": "JSON 转换作业列表。",
            "response_en": "JSON conversion job list.",
            "use_case_zh": "查看转换历史和输出目录。",
            "use_case_en": "Inspect conversion history and output directories.",
        },
        {
            "method": "GET",
            "path": "/convert/gpt-sovits/jobs/{job_id}",
            "purpose_zh": "查询单个转换任务的进度、日志和输出目录。",
            "purpose_en": "Inspect one conversion job's progress, logs, and output directories.",
            "response_zh": "JSON 转换作业快照。",
            "response_en": "JSON conversion job snapshot.",
            "use_case_zh": "WebUI 轮询转换进度。",
            "use_case_en": "WebUI polling for conversion progress.",
        },
        {
            "method": "GET",
            "path": "/status",
            "purpose_zh": "轻量活动诊断；包含会话、作业、阅读请求和进度。",
            "purpose_en": "Lightweight activity diagnostics for session, jobs, reader requests, and progress.",
            "response_zh": "JSON 状态；阅读请求只返回长度和短哈希，不返回原文。",
            "response_en": "JSON status; reader text is represented by length and short hash only.",
            "use_case_zh": "轮询进度、排查听书请求。",
            "use_case_en": "Progress polling and reader playback diagnostics.",
        },
        {
            "method": "POST",
            "path": "/runtime/configure",
            "purpose_zh": "选择后续加载会话的提供方顺序。",
            "purpose_en": "Select provider order for sessions loaded after the call.",
            "response_zh": "JSON 配置结果。",
            "response_en": "JSON configuration result.",
            "use_case_zh": "WebUI 只暴露 cpu/cuda/auto；其他兼容模式不作为功能入口。",
            "use_case_en": "The WebUI exposes cpu/cuda/auto; other compatibility modes are not product UI entries.",
        },
        {
            "method": "GET",
            "path": "/runtime/memory",
            "purpose_zh": "查看 CPU、内存、GPU、显存、缓存和单会话策略。",
            "purpose_en": "Inspect CPU, RAM, GPU, VRAM, caches, and the single-session policy.",
            "response_zh": "JSON 显存/策略快照；不返回文本内容。",
            "response_en": "JSON memory and policy snapshot; request text is not returned.",
            "use_case_zh": "判断是否需要释放会话、清缓存或降低线程数。",
            "use_case_en": "Decide whether to release sessions, clear cache, or reduce workers.",
        },
        {
            "method": "POST",
            "path": "/runtime/memory/action",
            "purpose_zh": "执行安全内存动作：刷新、释放空闲会话或清参考缓存。",
            "purpose_en": "Run safe memory actions: refresh, release idle sessions, or clear reference cache.",
            "response_zh": "JSON 动作结果和最新策略；忙碌时返回 409。",
            "response_en": "JSON action result and latest policy; returns 409 while busy.",
            "use_case_zh": "WebUI 资源维护；不提供伪显存共享开关。",
            "use_case_en": "WebUI resource maintenance without fake shared-VRAM controls.",
        },
        {
            "method": "GET",
            "path": "/server/listen",
            "purpose_zh": "查看当前监听 host/port、可选 LAN IP 和重启支持状态。",
            "purpose_en": "Inspect current listen host/port, LAN IP choices, and restart support.",
            "response_zh": "JSON 监听配置。",
            "response_en": "JSON listen configuration.",
            "use_case_zh": "判断 WebUI 是否真的对局域网开放。",
            "use_case_en": "Determine whether the WebUI is actually exposed to LAN clients.",
        },
        {
            "method": "POST",
            "path": "/server/restart",
            "purpose_zh": "用新的 host/port/runtime 启动包内 WebUI 进程，并延迟停止当前进程。",
            "purpose_en": "Start a package-local WebUI process with new host/port/runtime and stop the current process after a delay.",
            "response_zh": "202 JSON，包含新访问 URL；忙碌时返回 409。",
            "response_en": "202 JSON with new access URLs; returns 409 while busy.",
            "use_case_zh": "从网页端切换监听 IP 或端口。",
            "use_case_en": "Switch listen IP or port from the WebUI.",
        },
        {
            "method": "POST",
            "path": "/load_character",
            "purpose_zh": "加载角色 ONNX 模型。",
            "purpose_en": "Load character ONNX models.",
            "response_zh": "JSON 成功/错误。",
            "response_en": "JSON success or error.",
            "use_case_zh": "合成前准备角色。",
            "use_case_en": "Prepare a character before synthesis.",
        },
        {
            "method": "POST",
            "path": "/unload_character",
            "purpose_zh": "卸载角色模型会话。",
            "purpose_en": "Unload a character model session.",
            "response_zh": "JSON 成功/错误。",
            "response_en": "JSON success or error.",
            "use_case_zh": "释放显存或重新加载提供方。",
            "use_case_en": "Free memory or reload providers.",
        },
        {
            "method": "POST",
            "path": "/set_reference_audio",
            "purpose_zh": "设置并预处理参考音频和参考文本。",
            "purpose_en": "Set and preprocess reference audio and prompt text.",
            "response_zh": "JSON 成功/错误。",
            "response_en": "JSON success or error.",
            "use_case_zh": "合成前建立音色条件。",
            "use_case_en": "Prepare voice conditioning before synthesis.",
        },
        {
            "method": "POST",
            "path": "/clear_reference_audio_cache",
            "purpose_zh": "清理参考音频缓存。",
            "purpose_en": "Clear cached reference-audio preprocessing.",
            "response_zh": "JSON 成功/错误。",
            "response_en": "JSON success or error.",
            "use_case_zh": "参考音频变更后的维护操作。",
            "use_case_en": "Maintenance after changing reference audio.",
        },
        {
            "method": "POST",
            "path": "/tts/raw",
            "purpose_zh": "低延迟 raw PCM 流。",
            "purpose_en": "Low-latency raw PCM stream.",
            "response_zh": "application/octet-stream，pcm_s16le。",
            "response_en": "application/octet-stream, pcm_s16le.",
            "use_case_zh": "自定义客户端直接解码 PCM。",
            "use_case_en": "Custom clients that decode PCM directly.",
        },
        {
            "method": "POST",
            "path": "/tts/wav",
            "purpose_zh": "合成完成后返回完整 WAV。",
            "purpose_en": "Return a complete WAV after synthesis finishes.",
            "response_zh": "audio/wav 完整文件。",
            "response_en": "Complete audio/wav file.",
            "use_case_zh": "需要普通文件响应的客户端。",
            "use_case_en": "Clients that need a normal file response.",
        },
        {
            "method": "GET/POST",
            "path": "/tts/stream.wav",
            "purpose_zh": "通用分块 WAV 流。",
            "purpose_en": "Generic chunked WAV stream.",
            "response_zh": "audio/wav，开头 WAV 头 + 后续 PCM 分块。",
            "response_en": "audio/wav with an initial WAV header followed by PCM chunks.",
            "use_case_zh": "低延迟播放实验。",
            "use_case_en": "Low-latency playback experiments.",
        },
        {
            "method": "GET/POST",
            "path": "/tts/legado.wav",
            "purpose_zh": "阅读器/Legado 专用 WAV 端点；推荐 mode=buffered。",
            "purpose_en": "Reader/Legado WAV endpoint; mode=buffered is recommended.",
            "response_zh": "audio/wav，流式或缓冲。",
            "response_en": "audio/wav, stream or buffered.",
            "use_case_zh": "安卓阅读/听书。",
            "use_case_en": "Android reader and audiobook playback.",
        },
        {
            "method": "POST",
            "path": "/jobs/tts",
            "purpose_zh": "提交长文本后台作业。",
            "purpose_en": "Submit a queued long-text TTS job.",
            "response_zh": "202 JSON，包含作业 ID、进度和并行状态。",
            "response_en": "202 JSON with job ID, progress, and parallel status.",
            "use_case_zh": "小说、文档、长段落生成。",
            "use_case_en": "Novel, document, and long-passage generation.",
        },
        {
            "method": "GET",
            "path": "/jobs",
            "purpose_zh": "列出近期作业。",
            "purpose_en": "List recent jobs.",
            "response_zh": "JSON 作业列表。",
            "response_en": "JSON job list.",
            "use_case_zh": "恢复或检查历史任务。",
            "use_case_en": "Recover or inspect recent work.",
        },
        {
            "method": "GET",
            "path": "/jobs/{job_id}",
            "purpose_zh": "查询单个作业状态和进度。",
            "purpose_en": "Inspect a single job status and progress.",
            "response_zh": "JSON 作业快照。",
            "response_en": "JSON job snapshot.",
            "use_case_zh": "轮询 ETA、分段、输出字节。",
            "use_case_en": "Poll ETA, segments, and output bytes.",
        },
        {
            "method": "POST",
            "path": "/jobs/{job_id}/cancel",
            "purpose_zh": "取消排队或运行中的作业。",
            "purpose_en": "Cancel a queued or running job.",
            "response_zh": "JSON 作业快照或 409。",
            "response_en": "JSON job snapshot or 409.",
            "use_case_zh": "停止长文本后台生成。",
            "use_case_en": "Stop queued long-form generation.",
        },
        {
            "method": "GET",
            "path": "/jobs/{job_id}/wav",
            "purpose_zh": "下载已完成作业的 WAV。",
            "purpose_en": "Download a completed job WAV.",
            "response_zh": "audio/wav 完整文件。",
            "response_en": "Complete audio/wav file.",
            "use_case_zh": "保存长文本输出。",
            "use_case_en": "Save long-form output.",
        },
        {
            "method": "POST",
            "path": "/stop",
            "purpose_zh": "停止当前 TTS 会话，并请求运行中作业取消。",
            "purpose_en": "Stop the current TTS session and request running-job cancellation.",
            "response_zh": "JSON 成功/错误。",
            "response_en": "JSON success or error.",
            "use_case_zh": "紧急停止播放/合成。",
            "use_case_en": "Emergency stop for playback or synthesis.",
        },
        {
            "method": "GET/POST",
            "path": "/profile",
            "purpose_zh": "读取或控制进程内性能采样。",
            "purpose_en": "Read or control in-process profiling.",
            "response_zh": "JSON 性能事件和汇总。",
            "response_en": "JSON profiling events and summaries.",
            "use_case_zh": "性能排查。",
            "use_case_en": "Performance diagnostics.",
        },
        {
            "method": "GET",
            "path": "/ui",
            "purpose_zh": "打开无构建 WebUI。",
            "purpose_en": "Serve the no-build WebUI.",
            "response_zh": "HTML。",
            "response_en": "HTML.",
            "use_case_zh": "浏览器操作入口。",
            "use_case_en": "Browser control surface.",
        },
        {
            "method": "GET",
            "path": "/ui/config",
            "purpose_zh": "返回 WebUI 默认值、阅读器模板、端点目录和动态访问 URL。",
            "purpose_en": "Return WebUI defaults, reader templates, endpoint catalog, and dynamic access URLs.",
            "response_zh": "JSON 配置。",
            "response_en": "JSON configuration.",
            "use_case_zh": "WebUI 启动配置。",
            "use_case_en": "WebUI startup configuration.",
        },
    ]


class CharacterPayload(BaseModel):
    character_name: str
    onnx_model_dir: str
    language: str


class UnloadCharacterPayload(BaseModel):
    character_name: str


class ReferenceAudioPayload(BaseModel):
    character_name: str
    audio_path: str
    audio_text: str
    language: str


class CharacterPresetPayload(BaseModel):
    name: str
    label: Optional[str] = None
    family: Optional[str] = None
    onnx_model_dir: str
    language: str = "Chinese"
    reference_audio_path: Optional[str] = ""
    reference_text: Optional[str] = ""
    reference_name: Optional[str] = ""


class TTSPayload(BaseModel):
    character_name: str
    text: str
    split_sentence: bool = False
    save_path: Optional[str] = None


class TTSJobPayload(BaseModel):
    character_name: str
    text: str
    split_sentence: bool = True
    parallel_enabled: bool = False
    parallel_workers: Union[int, str] = 1


class ConversionScanPayload(BaseModel):
    folders: List[str]
    output_root: Optional[str] = None
    overwrite: bool = False


class ConversionSubmitPayload(BaseModel):
    folders: List[str]
    output_root: Optional[str] = None
    overwrite: bool = False


class RuntimeConfigurePayload(BaseModel):
    mode: str
    unload_sessions: bool = False


class ServerRestartPayload(BaseModel):
    host: str
    port: int
    runtime: Optional[str] = None


class MemoryActionPayload(BaseModel):
    action: str


class ProfilePayload(BaseModel):
    enabled: Optional[bool] = None
    clear: bool = False
    include_events: bool = True


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


_progress_splitter = TextSplitter()


def parse_parallel_workers_request(value: Union[int, str, None]) -> tuple[Union[int, str], int, bool]:
    if isinstance(value, str):
        raw = value.strip().lower()
        if raw == "auto":
            return "auto", DEFAULT_PARALLEL_WORKERS, True
        if not re.fullmatch(r"\d+", raw):
            raise HTTPException(status_code=400, detail=PARALLEL_WORKERS_INVALID_DETAIL)
        parsed = int(raw)
    elif isinstance(value, bool):
        raise HTTPException(status_code=400, detail=PARALLEL_WORKERS_INVALID_DETAIL)
    elif isinstance(value, int):
        parsed = int(value)
    elif isinstance(value, float) and value.is_integer():
        parsed = int(value)
    elif isinstance(value, float):
        raise HTTPException(status_code=400, detail=PARALLEL_WORKERS_INVALID_DETAIL)
    else:
        parsed = 1
    if parsed < 1:
        raise HTTPException(status_code=400, detail=PARALLEL_WORKERS_INVALID_DETAIL)
    return parsed, parsed, False


def normalize_parallel_workers(value: Union[int, str, None]) -> int:
    _, workers, _ = parse_parallel_workers_request(value)
    return workers


def manual_parallel_workers_for_segments(requested_workers: int, segment_count: int) -> tuple[int, str, str]:
    workers = max(2, min(requested_workers, MAX_PARALLEL_WORKERS, segment_count))
    limits: list[str] = []
    limits_zh: list[str] = []
    if requested_workers > MAX_PARALLEL_WORKERS:
        limits.append(f"server max {MAX_PARALLEL_WORKERS}")
        limits_zh.append(f"服务上限 {MAX_PARALLEL_WORKERS}")
    if requested_workers > segment_count:
        limits.append(f"{segment_count} text segments")
        limits_zh.append(f"{segment_count} 个文本分段")
    if limits:
        reason = (
            f"Requested {requested_workers} CUDA workers; using {workers} because "
            + " and ".join(limits)
            + " limit effective parallelism."
        )
        reason_zh = (
            f"请求 {requested_workers} 个 CUDA 线程；实际使用 {workers} 个，因为"
            + "、".join(limits_zh)
            + "限制了有效并行数。"
        )
    else:
        reason = f"Using {workers} requested CUDA workers for {segment_count} text segments."
        reason_zh = f"按请求使用 {workers} 个 CUDA 线程处理 {segment_count} 个文本分段。"
    return workers, reason, reason_zh


def auto_parallel_workers_for_segments(segments: List[str]) -> tuple[int, str, str]:
    segment_count = len(segments)
    if segment_count < 2:
        return 1, "Only one text segment is available; parallel synthesis would add overhead.", "文本只有一个分段，并行会增加额外开销。"

    workers = min(segment_count, MAX_PARALLEL_WORKERS)
    gpu_memory = sample_nvidia_gpu_memory()
    reason = f"Auto selected {workers} workers for {segment_count} segments."
    reason_zh = f"自动按 {segment_count} 个分段选择 {workers} 个线程。"
    if gpu_memory.get("available"):
        gpus = gpu_memory.get("gpus") or []
        free_values = [
            int(gpu.get("memory_free_mib") or 0)
            for gpu in gpus
            if isinstance(gpu, dict)
        ]
        free_mib = max(free_values) if free_values else 0
        if free_mib < 1800:
            workers = min(workers, 2)
            reason = f"Auto selected {workers} workers because free VRAM is about {free_mib} MiB."
            reason_zh = f"显存空闲约 {free_mib} MiB，自动限制为 {workers} 个线程。"
        elif free_mib < 3200:
            workers = min(workers, 3)
            reason = f"Auto selected {workers} workers with about {free_mib} MiB free VRAM."
            reason_zh = f"显存空闲约 {free_mib} MiB，自动选择 {workers} 个线程。"
        else:
            reason = f"Auto selected {workers} workers with about {free_mib} MiB free VRAM."
            reason_zh = f"显存空闲约 {free_mib} MiB，自动选择 {workers} 个线程。"
    return max(2, workers), reason, reason_zh


def reject_unsupported_parallel_request(payload: TTSJobPayload) -> None:
    if not bool(payload.parallel_enabled):
        return
    requested_workers, parallel_workers, requested_auto = parse_parallel_workers_request(payload.parallel_workers)
    if not requested_auto and parallel_workers <= 1:
        raise HTTPException(status_code=400, detail=PARALLEL_WORKERS_INVALID_DETAIL)
    if cuda_parallel_available_for_character(payload.character_name) and (requested_auto or parallel_workers > 1):
        return
    session_cuda = character_sessions_use_cuda(payload.character_name)
    reason = JOB_PARALLEL_UNAVAILABLE_REASON
    reason_zh = JOB_PARALLEL_UNAVAILABLE_REASON_ZH
    if not cuda_job_parallel_available():
        reason = JOB_PARALLEL_UNAVAILABLE_REASON
        reason_zh = JOB_PARALLEL_UNAVAILABLE_REASON_ZH
    elif session_cuda is False:
        reason = "The character is already loaded with non-CUDA ONNX sessions. Reload it after selecting CUDA."
        reason_zh = "该角色已经用非 CUDA 会话加载。请在选择 CUDA 后重新加载角色。"
    raise HTTPException(
        status_code=409,
        detail={
            "message": "GPU job parallel inference is not available for this request.",
            "reason": reason,
            "strategy": "single_session_serial",
            "effective": False,
            "requested_workers": requested_workers,
            "reason_zh": reason_zh,
            "allowed_payload": {
                "parallel_enabled": False,
                "parallel_workers": 1,
            },
        },
    )


def count_text_segments(text: str, split_sentence: bool) -> List[str]:
    stripped = text.strip()
    if not stripped:
        return []
    if split_sentence:
        return _progress_splitter.split(stripped) or [stripped]
    return [stripped]


def base_progress_snapshot(text: str, split_sentence: bool, stage: str = "queued") -> Dict[str, object]:
    segments = count_text_segments(text, split_sentence)
    return {
        "stage": stage,
        "message": "Queued for synthesis.",
        "total_chars": len(text.strip()),
        "completed_chars": 0,
        "total_segments": len(segments),
        "completed_segments": 0,
        "current_segment_index": 0,
        "current_segment_chars": 0,
        "generated_pcm_bytes": 0,
        "generated_wav_bytes": 0,
        "elapsed_seconds": 0.0,
        "estimated_remaining_seconds": None,
        "estimated_total_seconds": None,
        "percent": 0.0,
        "audio_duration_estimate_seconds": 0.0,
    }


def progress_with_timing(
        progress: Dict[str, object],
        started_monotonic: Optional[float],
        finished_monotonic: Optional[float],
        status: str,
) -> Dict[str, object]:
    result = dict(progress or {})
    now = time.perf_counter()
    if started_monotonic is None:
        elapsed = 0.0
    else:
        elapsed = (finished_monotonic if finished_monotonic is not None else now) - started_monotonic

    total_segments = int(result.get("total_segments") or 0)
    completed_segments = int(result.get("completed_segments") or 0)
    total_chars = int(result.get("total_chars") or 0)
    completed_chars = int(result.get("completed_chars") or 0)
    if status == "completed":
        completed_segments = total_segments
        completed_chars = total_chars
        percent = 100.0
        estimated_total = elapsed
        estimated_remaining = 0.0
    elif total_segments > 0:
        percent = min(99.9, max(0.0, completed_segments / total_segments * 100.0))
        if completed_segments > 0:
            estimated_total = elapsed * (total_segments / completed_segments)
            estimated_remaining = max(0.0, estimated_total - elapsed)
        else:
            estimated_total = None
            estimated_remaining = None
    elif total_chars > 0:
        percent = min(99.9, max(0.0, completed_chars / total_chars * 100.0))
        if completed_chars > 0:
            estimated_total = elapsed * (total_chars / completed_chars)
            estimated_remaining = max(0.0, estimated_total - elapsed)
        else:
            estimated_total = None
            estimated_remaining = None
    else:
        percent = 0.0
        estimated_total = None
        estimated_remaining = None

    bytes_per_second = tts_player.sample_rate * tts_player.channels * tts_player.bytes_per_sample
    generated_pcm_bytes = int(result.get("generated_pcm_bytes") or 0)
    result.update({
        "completed_segments": completed_segments,
        "completed_chars": completed_chars,
        "elapsed_seconds": elapsed,
        "estimated_remaining_seconds": estimated_remaining,
        "estimated_total_seconds": estimated_total,
        "percent": percent,
        "audio_duration_estimate_seconds": generated_pcm_bytes / float(bytes_per_second) if bytes_per_second else 0.0,
    })
    return result


@dataclass
class TTSJobRecord:
    job_id: str
    character_name: str
    text: str
    split_sentence: bool
    output_path: str
    progress: Dict[str, object]
    parallel_enabled: bool = False
    parallel_workers: int = 1
    parallel_requested_workers: Union[int, str] = 1
    parallel_workers_auto: bool = False
    parallel_effective: bool = False
    parallel_effective_workers: int = 1
    parallel_strategy: str = "single_session_serial"
    parallel_reason: str = JOB_PARALLEL_REASON
    parallel_reason_zh: str = JOB_PARALLEL_REASON_ZH
    status: str = "queued"
    created_at: str = field(default_factory=utc_now)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    stage: str = "queued"
    message: str = "Queued for synthesis."
    output_bytes: int = 0
    generated_pcm_bytes: int = 0
    audio_duration_seconds: Optional[float] = None
    error_detail: Optional[str] = None
    cancel_requested: bool = False
    cancel_event: Optional[threading.Event] = field(default=None, repr=False, compare=False)
    created_monotonic: float = field(default_factory=time.perf_counter)
    started_monotonic: Optional[float] = None
    finished_monotonic: Optional[float] = None

    def to_dict(self) -> Dict[str, object]:
        now = time.perf_counter()
        finished_or_now = self.finished_monotonic if self.finished_monotonic is not None else now
        elapsed = finished_or_now - self.created_monotonic
        if self.started_monotonic is None:
            processing_elapsed = 0.0
            queue_wait = elapsed
        else:
            processing_elapsed = finished_or_now - self.started_monotonic
            queue_wait = self.started_monotonic - self.created_monotonic

        progress = progress_with_timing(
            self.progress,
            self.started_monotonic,
            self.finished_monotonic,
            self.status,
        )
        parallel = {
            "enabled": self.parallel_enabled,
            "requested_workers": self.parallel_requested_workers,
            "effective": self.parallel_effective,
            "effective_workers": self.parallel_effective_workers if self.parallel_effective else 1,
            "strategy": self.parallel_strategy,
            "max_workers": MAX_PARALLEL_WORKERS,
            "reason": self.parallel_reason,
            "reason_zh": self.parallel_reason_zh,
            "auto": self.parallel_workers_auto,
        }
        progress["parallel"] = parallel

        return {
            "job_id": self.job_id,
            "status": self.status,
            "character_name": self.character_name,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "text_chars": len(self.text),
            "split_sentence": self.split_sentence,
            "stage": self.stage,
            "message": self.message,
            "progress": progress,
            "parallel": parallel,
            "total_segments": progress.get("total_segments"),
            "completed_segments": progress.get("completed_segments"),
            "completed_chars": progress.get("completed_chars"),
            "estimated_remaining_seconds": progress.get("estimated_remaining_seconds"),
            "estimated_total_seconds": progress.get("estimated_total_seconds"),
            "percent": progress.get("percent"),
            "output_path": self.output_path,
            "output_exists": Path(self.output_path).exists(),
            "output_bytes": self.output_bytes,
            "generated_pcm_bytes": progress.get("generated_pcm_bytes", self.generated_pcm_bytes),
            "audio_duration_seconds": self.audio_duration_seconds,
            "elapsed_seconds": elapsed,
            "queue_wait_seconds": queue_wait,
            "processing_elapsed_seconds": processing_elapsed,
            "error_detail": self.error_detail,
            "audio_format": "wav_pcm_s16le",
            "media_type": "audio/wav",
            "sample_rate": tts_player.sample_rate,
            "channels": tts_player.channels,
            "sample_width": tts_player.bytes_per_sample,
        }


@dataclass
class ReaderRequestRecord:
    request_id: str
    endpoint: str
    mode: str
    character_name: str
    text_chars: int
    text_sha256_12: str
    split_sentence: bool
    wait_timeout_seconds: float
    status: str = "received"
    started_at: str = field(default_factory=utc_now)
    finished_at: Optional[str] = None
    audio_bytes: int = 0
    chunks: int = 0
    error_detail: Optional[str] = None
    started_monotonic: float = field(default_factory=time.perf_counter)
    finished_monotonic: Optional[float] = None

    def to_dict(self) -> Dict[str, object]:
        now = time.perf_counter()
        finished_or_now = self.finished_monotonic if self.finished_monotonic is not None else now
        return {
            "request_id": self.request_id,
            "endpoint": self.endpoint,
            "mode": self.mode,
            "character_name": self.character_name,
            "text_chars": self.text_chars,
            "text_sha256_12": self.text_sha256_12,
            "split_sentence": self.split_sentence,
            "wait_timeout_seconds": self.wait_timeout_seconds,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed_seconds": finished_or_now - self.started_monotonic,
            "audio_bytes": self.audio_bytes,
            "chunks": self.chunks,
            "error_detail": self.error_detail,
        }


class ReaderRequestTracker:
    def __init__(self, max_records: int = 50):
        self.max_records = max_records
        self._records: Dict[str, ReaderRequestRecord] = {}
        self._order: List[str] = []
        self._lock = threading.Lock()

    def start(self, payload: TTSPayload, endpoint: str, mode: str, wait_timeout_seconds: float) -> str:
        request_id = uuid.uuid4().hex
        record = ReaderRequestRecord(
            request_id=request_id,
            endpoint=endpoint,
            mode=mode,
            character_name=payload.character_name,
            text_chars=len(payload.text),
            text_sha256_12=hashlib.sha256(payload.text.encode("utf-8")).hexdigest()[:12],
            split_sentence=payload.split_sentence,
            wait_timeout_seconds=wait_timeout_seconds,
        )
        with self._lock:
            self._records[request_id] = record
            self._order.append(request_id)
            self._trim_locked()
        return request_id

    def update(self, request_id: Optional[str], status: str) -> None:
        if request_id is None:
            return
        with self._lock:
            record = self._records.get(request_id)
            if record:
                record.status = status

    def finish(
            self,
            request_id: Optional[str],
            status: str,
            audio_bytes: int = 0,
            chunks: int = 0,
            error_detail: Optional[str] = None,
    ) -> None:
        if request_id is None:
            return
        with self._lock:
            record = self._records.get(request_id)
            if record is None:
                return
            record.status = status
            record.audio_bytes = audio_bytes
            record.chunks = chunks
            record.error_detail = truncate_error(error_detail)
            record.finished_at = utc_now()
            record.finished_monotonic = time.perf_counter()

    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            records = [
                self._records[request_id]
                for request_id in reversed(self._order)
                if request_id in self._records
            ]
            active = [record.to_dict() for record in records if record.status not in TERMINAL_READER_STATUSES]
            recent = [record.to_dict() for record in records[:10]]
            return {
                "active_count": len(active),
                "active": active,
                "last": recent[0] if recent else None,
                "recent": recent,
            }

    def _trim_locked(self) -> None:
        while len(self._order) > self.max_records:
            oldest = self._order.pop(0)
            self._records.pop(oldest, None)


class TTSJobManager:
    def __init__(self, output_dir: Path, max_jobs: int = 100):
        self.output_dir = output_dir
        self.max_jobs = max_jobs
        self._jobs: Dict[str, TTSJobRecord] = {}
        self._order: List[str] = []
        self._queue: queue.Queue[str] = queue.Queue()
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._worker_loop, name="GenieTTSJobWorker", daemon=True)
        self._worker.start()

    def submit(self, payload: TTSJobPayload) -> TTSJobRecord:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        job_id = uuid.uuid4().hex
        output_path = str(self.output_dir / f"{job_id}.wav")
        parallel_enabled = bool(payload.parallel_enabled)
        if parallel_enabled:
            requested_workers, parallel_workers, parallel_workers_auto = parse_parallel_workers_request(payload.parallel_workers)
        else:
            requested_workers = 1
            parallel_workers = 1
            parallel_workers_auto = False
        progress = base_progress_snapshot(payload.text, payload.split_sentence)
        record = TTSJobRecord(
            job_id=job_id,
            character_name=payload.character_name,
            text=payload.text,
            split_sentence=payload.split_sentence,
            output_path=output_path,
            progress=progress,
            parallel_enabled=parallel_enabled,
            parallel_workers=parallel_workers,
            parallel_requested_workers=requested_workers,
            parallel_workers_auto=parallel_workers_auto,
            parallel_strategy="gpu_segment_parallel" if parallel_enabled and (parallel_workers_auto or parallel_workers > 1) else "single_session_serial",
            parallel_reason=JOB_PARALLEL_REASON if parallel_enabled else JOB_PARALLEL_REASON,
            parallel_reason_zh=JOB_PARALLEL_REASON_ZH,
        )
        with self._lock:
            self._jobs[job_id] = record
            self._order.append(job_id)
            self._trim_locked()
        self._queue.put(job_id)
        return record

    def list_jobs(self) -> List[Dict[str, object]]:
        with self._lock:
            return [self._jobs[job_id].to_dict() for job_id in reversed(self._order) if job_id in self._jobs]

    def get(self, job_id: str) -> TTSJobRecord:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise KeyError(job_id)
            return record

    def snapshot(self, job_id: str) -> Dict[str, object]:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise KeyError(job_id)
            return record.to_dict()

    def cancel(self, job_id: str, message: str = "Cancellation requested.") -> Dict[str, object]:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise KeyError(job_id)
            if record.status in TERMINAL_JOB_STATUSES:
                raise ValueError(f"Job '{job_id}' is already {record.status}.")
            record.cancel_requested = True
            if record.cancel_event is not None:
                record.cancel_event.set()
            record.message = message
            if record.status == "queued":
                self._finish_locked(record, "cancelled", "cancelled", "Cancelled before synthesis started.")
                return record.to_dict()
            running_tts = record.status == "running" and record.stage == "synthesizing"

        if running_tts:
            tts_player.stop()
            with self._lock:
                record = self._jobs[job_id]
                record.message = message
        return self.snapshot(job_id)

    def cancel_running(self, message: str) -> Optional[str]:
        running_job_id = None
        with self._lock:
            for job_id in self._order:
                record = self._jobs.get(job_id)
                if record and record.status == "running":
                    record.cancel_requested = True
                    record.message = message
                    running_job_id = job_id
                    break
        return running_job_id

    def has_active_job(self) -> bool:
        with self._lock:
            return any(
                record.status in {"queued", "running"} and not record.cancel_requested
                for record in self._jobs.values()
            )

    def status_snapshot(self) -> Dict[str, object]:
        with self._lock:
            records = [
                self._jobs[job_id]
                for job_id in reversed(self._order)
                if job_id in self._jobs
            ]
            active = [
                record.to_dict()
                for record in records
                if record.status in {"queued", "running"} and not record.cancel_requested
            ]
            return {
                "has_active_job": bool(active),
                "queued_count": sum(1 for record in records if record.status == "queued" and not record.cancel_requested),
                "running_count": sum(1 for record in records if record.status == "running" and not record.cancel_requested),
                "active": active,
                "last": records[0].to_dict() if records else None,
            }

    def _trim_locked(self) -> None:
        while len(self._order) > self.max_jobs:
            oldest = self._order.pop(0)
            record = self._jobs.get(oldest)
            if record and record.status not in TERMINAL_JOB_STATUSES:
                self._order.insert(0, oldest)
                break
            self._jobs.pop(oldest, None)

    def _worker_loop(self) -> None:
        while True:
            job_id = self._queue.get()
            try:
                self._run_job(job_id)
            except Exception as exc:
                logger.error("Unhandled job worker error for %s: %s", job_id, exc, exc_info=True)
                with self._lock:
                    record = self._jobs.get(job_id)
                    if record and record.status not in TERMINAL_JOB_STATUSES:
                        self._finish_locked(record, "failed", "failed", "Unhandled job worker error.", str(exc))
            finally:
                self._queue.task_done()

    def _run_job(self, job_id: str) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None or record.status == "cancelled":
                return
            record.status = "running"
            record.started_at = utc_now()
            record.started_monotonic = time.perf_counter()
            record.stage = "waiting_for_tts_session"
            record.message = "Waiting for the TTS session lock."
            record.progress["stage"] = record.stage
            record.progress["message"] = record.message

        if not self._reserve_tts_session(record):
            return

        if record.parallel_enabled:
            self._run_parallel_job(job_id, record)
            return

        pcm_chunks = bytearray()

        def chunk_callback(chunk: Optional[bytes]) -> None:
            if chunk is None:
                return
            pcm_chunks.extend(chunk)
            with self._lock:
                current = self._jobs.get(job_id)
                if current:
                    progress = tts_player.progress_snapshot()
                    progress["generated_pcm_bytes"] = len(pcm_chunks)
                    progress["stage"] = "synthesizing"
                    progress["message"] = f"Generated {len(pcm_chunks)} PCM bytes."
                    current.progress = progress
                    current.generated_pcm_bytes = len(pcm_chunks)
                    current.message = progress["message"]

        try:
            with self._lock:
                if record.cancel_requested:
                    self._finish_locked(record, "cancelled", "cancelled", "Cancelled before synthesis started.")
                    tts_player.release_session()
                    return
                record.stage = "synthesizing"
                record.message = "Synthesizing audio."
                record.progress["stage"] = record.stage
                record.progress["message"] = record.message

            context.current_speaker = record.character_name
            context.current_prompt_audio = prepare_reference_audio(record.character_name)
            tts_player.start_session(
                play=False,
                split=record.split_sentence,
                save_path=None,
                chunk_callback=chunk_callback,
                reserved_session=True,
            )
            tts_player.feed(record.text)
            tts_player.end_session()
            tts_player.wait_for_tts_completion()

            latest_progress = tts_player.progress_snapshot()
            latest_progress["generated_pcm_bytes"] = len(pcm_chunks)
            with self._lock:
                current = self._jobs.get(job_id)
                if current:
                    current.progress = latest_progress
                    current.generated_pcm_bytes = len(pcm_chunks)

            with self._lock:
                cancelled = record.cancel_requested
            if cancelled:
                with self._lock:
                    self._finish_locked(record, "cancelled", "cancelled", "Cancelled during synthesis.")
                return

            if not pcm_chunks:
                raise RuntimeError("TTS completed without generating audio bytes.")

            with self._lock:
                record.stage = "writing_wav"
                record.message = "Writing WAV output."
                record.progress["stage"] = record.stage
                record.progress["message"] = record.message

            wav_bytes = pcm_bytes_to_wav(bytes(pcm_chunks))
            output_path = Path(record.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(wav_bytes)
            duration = read_wav_duration(output_path)

            with self._lock:
                record.output_bytes = len(wav_bytes)
                record.audio_duration_seconds = duration
                record.progress["generated_wav_bytes"] = len(wav_bytes)
                record.progress["generated_pcm_bytes"] = len(pcm_chunks)
                self._finish_locked(record, "completed", "completed", "Job completed successfully.")
            profile_recorder.record(
                "job_wav_response",
                record.finished_monotonic - record.started_monotonic if record.finished_monotonic and record.started_monotonic else 0,
                {"endpoint": "/jobs/tts", "bytes": len(wav_bytes), "job_id": job_id},
            )
        except Exception as exc:
            tts_player.release_session()
            with self._lock:
                current = self._jobs.get(job_id)
                if current and current.status not in TERMINAL_JOB_STATUSES:
                    if current.cancel_requested:
                        self._finish_locked(current, "cancelled", "cancelled", "Cancelled during synthesis.")
                    else:
                        self._finish_locked(current, "failed", "failed", "TTS job failed.", str(exc))

    def _run_parallel_job(self, job_id: str, record: TTSJobRecord) -> None:
        cancel_event = threading.Event()
        record.cancel_event = cancel_event
        started = time.perf_counter()
        try:
            prompt_audio = prepare_reference_audio(record.character_name)
            segments = count_text_segments(record.text, record.split_sentence)
            if not segments:
                raise RuntimeError("Text must not be empty.")

            if record.parallel_workers_auto:
                workers, worker_reason, worker_reason_zh = auto_parallel_workers_for_segments(segments)
            elif len(segments) < 2:
                workers = 1
                worker_reason = "Only one text segment is available; parallel synthesis would add overhead."
                worker_reason_zh = "文本只有一个分段，并行会增加额外开销。"
            else:
                workers, worker_reason, worker_reason_zh = manual_parallel_workers_for_segments(
                    record.parallel_workers,
                    len(segments),
                )

            with self._lock:
                if record.cancel_requested:
                    self._finish_locked(record, "cancelled", "cancelled", "Cancelled before synthesis started.")
                    return
                record.parallel_effective = workers > 1
                record.parallel_effective_workers = workers if workers > 1 else 1
                record.parallel_strategy = "gpu_segment_parallel" if workers > 1 else "single_session_serial"
                record.parallel_reason = worker_reason
                record.parallel_reason_zh = worker_reason_zh
                record.stage = "parallel_synthesizing" if workers > 1 else "synthesizing"
                record.message = (
                    f"GPU parallel synthesis started with {workers} workers."
                    if workers > 1
                    else "Synthesizing one segment without parallel workers."
                )
                record.progress["stage"] = record.stage
                record.progress["message"] = record.message
                record.progress["parallel_workers"] = workers
                record.progress["requested_parallel_workers"] = record.parallel_requested_workers
                record.progress["max_parallel_workers"] = MAX_PARALLEL_WORKERS
                record.progress["parallel_reason"] = worker_reason
                record.progress["parallel_reason_zh"] = worker_reason_zh

            total_chars = sum(len(segment) for segment in segments)
            results: Dict[int, bytes] = {}
            completed_chars = 0
            generated_pcm_bytes = 0

            def run_one(index: int, segment: str) -> tuple[int, bytes, int]:
                return (
                    index,
                    synthesize_segment_pcm(record.character_name, prompt_audio, segment, cancel_event),
                    len(segment),
                )

            if workers > 1:
                with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="GenieTTSJobGPU") as executor:
                    future_to_index = {
                        executor.submit(run_one, index, segment): index
                        for index, segment in enumerate(segments, start=1)
                    }
                    completed_iterable = (
                        future.result()
                        for future in as_completed(future_to_index)
                    )
                    for index, pcm_bytes, segment_chars in completed_iterable:
                        with self._lock:
                            current = self._jobs.get(job_id)
                            if current is None:
                                cancel_event.set()
                                break
                            if current.cancel_requested:
                                cancel_event.set()
                                break
                        if cancel_event.is_set():
                            break
                        if not pcm_bytes:
                            raise RuntimeError(f"Parallel segment {index} completed without audio bytes.")
                        results[index] = pcm_bytes
                        completed_chars += segment_chars
                        generated_pcm_bytes += len(pcm_bytes)
                        with self._lock:
                            current = self._jobs.get(job_id)
                            if current:
                                current.generated_pcm_bytes = generated_pcm_bytes
                                current.message = f"Completed {len(results)}/{len(segments)} parallel segments."
                                current.progress.update({
                                    "stage": "parallel_synthesizing",
                                    "message": current.message,
                                    "total_chars": total_chars,
                                    "completed_chars": completed_chars,
                                    "total_segments": len(segments),
                                    "completed_segments": len(results),
                                    "current_segment_index": index,
                                    "current_segment_chars": segment_chars,
                                    "generated_pcm_bytes": generated_pcm_bytes,
                                    "parallel_workers": workers,
                                    "requested_parallel_workers": current.parallel_requested_workers,
                                    "max_parallel_workers": MAX_PARALLEL_WORKERS,
                                })
            else:
                for index, segment in enumerate(segments, start=1):
                    with self._lock:
                        current = self._jobs.get(job_id)
                        if current is None:
                            cancel_event.set()
                            break
                        if current.cancel_requested:
                            cancel_event.set()
                            break
                    index, pcm_bytes, segment_chars = run_one(index, segment)
                    if cancel_event.is_set():
                        break
                    if not pcm_bytes:
                        raise RuntimeError(f"Segment {index} completed without audio bytes.")
                    results[index] = pcm_bytes
                    completed_chars += segment_chars
                    generated_pcm_bytes += len(pcm_bytes)
                    with self._lock:
                        current = self._jobs.get(job_id)
                        if current:
                            current.generated_pcm_bytes = generated_pcm_bytes
                            current.message = f"Completed {len(results)}/{len(segments)} segments."
                            current.progress.update({
                                "stage": "synthesizing",
                                "message": current.message,
                                "total_chars": total_chars,
                                "completed_chars": completed_chars,
                                "total_segments": len(segments),
                                "completed_segments": len(results),
                                "current_segment_index": index,
                                "current_segment_chars": segment_chars,
                                "generated_pcm_bytes": generated_pcm_bytes,
                                "parallel_workers": workers,
                                "requested_parallel_workers": current.parallel_requested_workers,
                                "max_parallel_workers": MAX_PARALLEL_WORKERS,
                            })

            with self._lock:
                cancelled = bool(self._jobs.get(job_id) and self._jobs[job_id].cancel_requested)
            if cancelled or cancel_event.is_set():
                with self._lock:
                    current = self._jobs.get(job_id)
                    if current and current.status not in TERMINAL_JOB_STATUSES:
                        self._finish_locked(current, "cancelled", "cancelled", "Cancelled during parallel synthesis.")
                return

            missing = [index for index in range(1, len(segments) + 1) if index not in results]
            if missing:
                raise RuntimeError(f"Parallel synthesis missing segments: {missing}")

            pcm_bytes_joined = b"".join(results[index] for index in range(1, len(segments) + 1))
            if not pcm_bytes_joined:
                raise RuntimeError("Parallel TTS completed without generating audio bytes.")

            with self._lock:
                record.stage = "writing_wav"
                record.message = "Writing WAV output."
                record.progress["stage"] = record.stage
                record.progress["message"] = record.message

            wav_bytes = pcm_bytes_to_wav(pcm_bytes_joined)
            output_path = Path(record.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(wav_bytes)
            duration = read_wav_duration(output_path)
            wall_seconds = max(1e-6, time.perf_counter() - started)
            chars_per_second = round(total_chars / wall_seconds, 2) if total_chars else 0.0

            with self._lock:
                record.output_bytes = len(wav_bytes)
                record.generated_pcm_bytes = len(pcm_bytes_joined)
                record.audio_duration_seconds = duration
                record.progress["generated_wav_bytes"] = len(wav_bytes)
                record.progress["generated_pcm_bytes"] = len(pcm_bytes_joined)
                record.progress["parallel_wall_seconds"] = round(wall_seconds, 3)
                record.progress["parallel_chars_per_second"] = chars_per_second
                record.progress["effective_parallel_workers"] = workers if workers > 1 else 1
                self._finish_locked(
                    record,
                    "completed",
                    "completed",
                    "Parallel job completed successfully." if workers > 1 else "Job completed successfully.",
                )
            profile_recorder.record(
                "job_parallel_wav_response",
                wall_seconds,
                {
                    "endpoint": "/jobs/tts",
                    "bytes": len(wav_bytes),
                    "job_id": job_id,
                    "workers": workers,
                    "segments": len(segments),
                    "chars": total_chars,
                    "chars_per_second": chars_per_second,
                },
            )
        except Exception as exc:
            cancel_event.set()
            with self._lock:
                current = self._jobs.get(job_id)
                if current and current.status not in TERMINAL_JOB_STATUSES:
                    if current.cancel_requested:
                        self._finish_locked(current, "cancelled", "cancelled", "Cancelled during parallel synthesis.")
                    else:
                        self._finish_locked(current, "failed", "failed", "Parallel TTS job failed.", str(exc))
        finally:
            record.cancel_event = None
            tts_player.release_session()

    def _reserve_tts_session(self, record: TTSJobRecord) -> bool:
        while True:
            with self._lock:
                if record.cancel_requested:
                    self._finish_locked(record, "cancelled", "cancelled", "Cancelled before synthesis started.")
                    return False
            try:
                tts_player.reserve_session()
                return True
            except RuntimeError:
                time.sleep(0.25)

    def _finish_locked(
            self,
            record: TTSJobRecord,
            status: str,
            stage: str,
            message: str,
            error_detail: Optional[str] = None,
    ) -> None:
        record.status = status
        record.stage = stage
        record.message = message
        record.error_detail = error_detail
        record.progress["stage"] = stage
        record.progress["message"] = message
        if status == "completed":
            record.progress["completed_chars"] = record.progress.get("total_chars", 0)
            record.progress["completed_segments"] = record.progress.get("total_segments", 0)
            record.progress["percent"] = 100.0
            record.progress["estimated_remaining_seconds"] = 0.0
        record.finished_at = utc_now()
        record.finished_monotonic = time.perf_counter()


def safe_output_name(folder: Path) -> str:
    name = re.sub(r"[<>:\"/\\|?*\x00-\x1f]+", "_", folder.name.strip())
    name = re.sub(r"\s+", "_", name).strip("._ ")
    return name or hashlib.sha1(str(folder).encode("utf-8")).hexdigest()[:12]


def epoch_from_model_filename(path: Path) -> int:
    match = re.search(r"e(\d+)", path.name, flags=re.IGNORECASE)
    return int(match.group(1)) if match else 0


def latest_model_file(files: List[Path]) -> Optional[Path]:
    if not files:
        return None
    return max(files, key=lambda item: (epoch_from_model_filename(item), item.stat().st_mtime))


def find_gpt_sovits_pair(directory: Path) -> tuple[Optional[Path], Optional[Path]]:
    try:
        files = [item for item in directory.iterdir() if item.is_file()]
    except OSError:
        return None, None
    ckpt = latest_model_file([item for item in files if item.suffix.lower() == ".ckpt"])
    pth = latest_model_file([item for item in files if item.suffix.lower() == ".pth"])
    return ckpt, pth


def normalize_conversion_folders(folders: List[str]) -> List[Path]:
    result: List[Path] = []
    seen: set[str] = set()
    for raw in folders or []:
        value = str(raw or "").strip().strip('"')
        if not value:
            continue
        path = Path(value).expanduser()
        try:
            key = str(path.resolve()).lower()
        except OSError:
            key = str(path.absolute()).lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def conversion_output_root(output_root: Optional[str] = None) -> Path:
    value = str(output_root or "").strip().strip('"')
    return Path(value).expanduser() if value else CONVERSION_OUTPUT_ROOT


def conversion_output_dir(source_folder: Path, output_root: Path) -> Path:
    return output_root / safe_output_name(source_folder) / "tts_models"


def scan_conversion_sources(
        folders: List[str],
        output_root: Optional[str] = None,
        overwrite: bool = False,
) -> Dict[str, object]:
    root = conversion_output_root(output_root)
    items: List[Dict[str, object]] = []
    valid_count = 0
    for folder in normalize_conversion_folders(folders):
        folder_exists = folder.is_dir()
        ckpt_path, pth_path = find_gpt_sovits_pair(folder) if folder_exists else (None, None)
        output_dir = conversion_output_dir(folder, root)
        output_exists = output_dir.exists() and any(output_dir.iterdir()) if output_dir.exists() else False
        valid = bool(folder_exists and ckpt_path and pth_path and (overwrite or not output_exists))
        if valid:
            valid_count += 1
        if not folder_exists:
            reason = "文件夹不存在。"
        elif not ckpt_path or not pth_path:
            reason = "需要同一文件夹内同时存在 .ckpt 和 .pth 文件。"
        elif output_exists and not overwrite:
            reason = "输出目录已有内容；勾选覆盖后才能转换。"
        else:
            reason = "可转换。"
        pth_size = pth_path.stat().st_size if pth_path and pth_path.exists() else 0
        model_type = "v2ProPlus" if pth_size > 150 * 1024 * 1024 else "v2"
        items.append({
            "source_folder": str(folder),
            "source_exists": folder_exists,
            "ckpt_path": str(ckpt_path) if ckpt_path else "",
            "pth_path": str(pth_path) if pth_path else "",
            "pth_size_bytes": pth_size,
            "detected_model_type": model_type if pth_path else "",
            "output_dir": str(output_dir),
            "output_exists": output_exists,
            "valid": valid,
            "reason": reason,
        })
    return {
        "output_root": str(root),
        "overwrite": overwrite,
        "count": len(items),
        "valid_count": valid_count,
        "items": items,
    }


@dataclass
class ConversionJobRecord:
    job_id: str
    items: List[Dict[str, object]]
    output_root: str
    overwrite: bool = False
    status: str = "queued"
    stage: str = "queued"
    message: str = "等待开始转换。"
    created_at: str = field(default_factory=utc_now)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    error_detail: Optional[str] = None
    created_monotonic: float = field(default_factory=time.perf_counter)
    started_monotonic: Optional[float] = None
    finished_monotonic: Optional[float] = None

    def log(self, message: str, level: str = "INFO") -> None:
        line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {level} - {message}"
        self.logs.append(line)
        if len(self.logs) > 300:
            self.logs = self.logs[-300:]

    def to_dict(self) -> Dict[str, object]:
        now = time.perf_counter()
        finished_or_now = self.finished_monotonic if self.finished_monotonic is not None else now
        elapsed = finished_or_now - self.created_monotonic
        total = len(self.items)
        done = sum(1 for item in self.items if item.get("status") in TERMINAL_CONVERSION_STATUSES)
        success = sum(1 for item in self.items if item.get("status") == "completed")
        failed = sum(1 for item in self.items if item.get("status") == "failed")
        percent = 100.0 if self.status == "completed" else (done / total * 100.0 if total else 0.0)
        return {
            "job_id": self.job_id,
            "status": self.status,
            "stage": self.stage,
            "message": self.message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed_seconds": elapsed,
            "output_root": self.output_root,
            "overwrite": self.overwrite,
            "total": total,
            "completed": success,
            "failed": failed,
            "done": done,
            "percent": percent,
            "items": self.items,
            "logs": self.logs[-120:],
            "error_detail": self.error_detail,
        }


class ConversionJobManager:
    def __init__(self, max_jobs: int = 30):
        self.max_jobs = max_jobs
        self._jobs: Dict[str, ConversionJobRecord] = {}
        self._order: List[str] = []
        self._queue: queue.Queue[str] = queue.Queue()
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._worker_loop, name="GenieTTSConversionWorker", daemon=True)
        self._worker.start()

    def submit(self, payload: ConversionSubmitPayload) -> ConversionJobRecord:
        scan = scan_conversion_sources(payload.folders, payload.output_root, payload.overwrite)
        valid_items = [dict(item) for item in scan["items"] if item.get("valid")]
        if not valid_items:
            raise ValueError("没有可转换的文件夹。请确认每个文件夹内有一对 .ckpt 和 .pth 文件。")
        job_id = uuid.uuid4().hex
        for item in valid_items:
            item["status"] = "queued"
            item["message"] = item.get("reason") or "等待转换。"
            item["started_at"] = None
            item["finished_at"] = None
            item["error_detail"] = None
        record = ConversionJobRecord(
            job_id=job_id,
            items=valid_items,
            output_root=str(scan["output_root"]),
            overwrite=bool(payload.overwrite),
        )
        record.log(f"已提交 {len(valid_items)} 个转换项。")
        with self._lock:
            self._jobs[job_id] = record
            self._order.append(job_id)
            self._trim_locked()
        self._queue.put(job_id)
        return record

    def list_jobs(self) -> List[Dict[str, object]]:
        with self._lock:
            return [self._jobs[job_id].to_dict() for job_id in reversed(self._order) if job_id in self._jobs]

    def snapshot(self, job_id: str) -> Dict[str, object]:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise KeyError(job_id)
            return record.to_dict()

    def has_active_job(self) -> bool:
        with self._lock:
            return any(record.status in {"queued", "running"} for record in self._jobs.values())

    def _trim_locked(self) -> None:
        while len(self._order) > self.max_jobs:
            oldest = self._order.pop(0)
            record = self._jobs.get(oldest)
            if record and record.status not in TERMINAL_CONVERSION_STATUSES:
                self._order.insert(0, oldest)
                break
            self._jobs.pop(oldest, None)

    def _worker_loop(self) -> None:
        while True:
            job_id = self._queue.get()
            try:
                self._run_job(job_id)
            except Exception as exc:
                logger.error("Unhandled conversion worker error for %s: %s", job_id, exc, exc_info=True)
                with self._lock:
                    record = self._jobs.get(job_id)
                    if record and record.status not in TERMINAL_CONVERSION_STATUSES:
                        self._finish_locked(record, "failed", "failed", "转换任务失败。", str(exc))
            finally:
                self._queue.task_done()

    def _run_job(self, job_id: str) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return
            record.status = "running"
            record.stage = "running"
            record.message = "正在转换。"
            record.started_at = utc_now()
            record.started_monotonic = time.perf_counter()
            record.log("转换任务开始。")

        for index, item in enumerate(list(record.items), start=1):
            output_dir = Path(str(item.get("output_dir") or ""))
            ckpt_path = str(item.get("ckpt_path") or "")
            pth_path = str(item.get("pth_path") or "")
            try:
                with self._lock:
                    item["status"] = "running"
                    item["message"] = "正在转换。"
                    item["started_at"] = utc_now()
                    record.stage = "running"
                    record.message = f"正在转换 {index}/{len(record.items)}：{Path(str(item.get('source_folder'))).name}"
                    record.log(record.message)
                if output_dir.exists() and record.overwrite:
                    shutil.rmtree(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                from .Converter.Converter import convert

                convert(
                    torch_ckpt_path=ckpt_path,
                    torch_pth_path=pth_path,
                    output_dir=str(output_dir),
                )
                with self._lock:
                    item["status"] = "completed"
                    item["message"] = "转换完成。"
                    item["finished_at"] = utc_now()
                    record.log(f"转换完成：{output_dir}")
            except Exception as exc:
                with self._lock:
                    item["status"] = "failed"
                    item["message"] = "转换失败。"
                    item["error_detail"] = truncate_error(str(exc), limit=1000)
                    item["finished_at"] = utc_now()
                    record.log(f"转换失败：{item.get('source_folder')}，{exc}", "ERROR")

        with self._lock:
            failed = any(item.get("status") == "failed" for item in record.items)
            completed = sum(1 for item in record.items if item.get("status") == "completed")
            if completed and not failed:
                self._finish_locked(record, "completed", "completed", "全部转换完成。")
            elif completed:
                self._finish_locked(record, "failed", "failed", f"部分转换完成，{completed}/{len(record.items)} 成功。")
            else:
                self._finish_locked(record, "failed", "failed", "全部转换失败。")

    def _finish_locked(
            self,
            record: ConversionJobRecord,
            status: str,
            stage: str,
            message: str,
            error_detail: Optional[str] = None,
    ) -> None:
        record.status = status
        record.stage = stage
        record.message = message
        record.error_detail = truncate_error(error_detail)
        record.finished_at = utc_now()
        record.finished_monotonic = time.perf_counter()
        record.log(message, "ERROR" if status == "failed" else "INFO")


job_manager = TTSJobManager(JOB_OUTPUT_DIR)
conversion_job_manager = ConversionJobManager()
reader_request_tracker = ReaderRequestTracker()


def truncate_error(error_detail: Optional[str], limit: int = 500) -> Optional[str]:
    if error_detail is None:
        return None
    value = str(error_detail)
    if len(value) <= limit:
        return value
    return value[:limit - 3] + "..."


def exception_detail(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        return str(exc.detail)
    return str(exc)


def exception_status(exc: Exception) -> str:
    if isinstance(exc, HTTPException) and 400 <= exc.status_code < 500:
        return "rejected"
    return "failed"


def prepare_reference_audio(character_name: str) -> ReferenceAudio:
    reference = _reference_audios[character_name]
    with profile_span("api_prepare_reference", character_name=character_name):
        prompt_audio = ReferenceAudio(
            prompt_wav=reference['audio_path'],
            prompt_text=reference['audio_text'],
            language=reference['language'],
        )
    gsv_model = model_manager.get(character_name)
    if gsv_model and gsv_model.PROMPT_ENCODER:
        prompt_audio.update_global_emb(gsv_model.PROMPT_ENCODER)
    return prompt_audio


def clone_reference_for_parallel(prompt_audio: ReferenceAudio) -> ReferenceAudio:
    clone = object.__new__(ReferenceAudio)
    clone.text = prompt_audio.text
    clone.language = prompt_audio.language
    clone.phonemes_seq = np.array(prompt_audio.phonemes_seq, copy=True)
    clone.text_bert = np.array(prompt_audio.text_bert, copy=True)
    clone.audio_32k = np.array(prompt_audio.audio_32k, copy=True)
    clone.audio_16k = np.array(prompt_audio.audio_16k, copy=True)
    clone.ssl_content = np.array(prompt_audio.ssl_content, copy=True)
    clone.global_emb = np.array(prompt_audio.global_emb, copy=True) if prompt_audio.global_emb is not None else None
    clone.global_emb_advanced = (
        np.array(prompt_audio.global_emb_advanced, copy=True)
        if prompt_audio.global_emb_advanced is not None else None
    )
    clone._initialized = True
    return clone


def synthesize_segment_pcm(
        character_name: str,
        prompt_audio: ReferenceAudio,
        text: str,
        cancel_event: threading.Event,
) -> bytes:
    if cancel_event.is_set():
        return b""
    gsv_model = model_manager.get(character_name)
    if not gsv_model:
        raise RuntimeError(f"Character model is not loaded: {character_name}")
    worker_client = GENIE()
    worker_client.stop_event = cancel_event
    audio_chunk = worker_client.tts(
        text=text,
        prompt_audio=clone_reference_for_parallel(prompt_audio),
        encoder=gsv_model.T2S_ENCODER,
        first_stage_decoder=gsv_model.T2S_FIRST_STAGE_DECODER,
        stage_decoder=gsv_model.T2S_STAGE_DECODER,
        vocoder=gsv_model.VITS,
        prompt_encoder=gsv_model.PROMPT_ENCODER,
        language=gsv_model.LANGUAGE,
    )
    if audio_chunk is None or cancel_event.is_set():
        return b""
    audio_chunk = tts_player._prepare_audio_chunk(audio_chunk)
    return tts_player._preprocess_for_playback(audio_chunk)


@app.post("/load_character")
def load_character_endpoint(payload: CharacterPayload):
    try:
        loaded = model_manager.load_character(
            character_name=payload.character_name,
            model_dir=payload.onnx_model_dir,
            language=normalize_language(payload.language),
        )
        if not loaded:
            raise HTTPException(status_code=500, detail=f"Failed to load character '{payload.character_name}'.")
        if payload.character_name in _reference_audios:
            prepare_reference_audio(payload.character_name)
        return {"status": "success", "message": f"Character '{payload.character_name}' loaded."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/unload_character")
def unload_character_endpoint(payload: UnloadCharacterPayload):
    try:
        model_manager.remove_character(character_name=payload.character_name)
        return {"status": "success", "message": f"Character '{payload.character_name}' unloaded."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/set_reference_audio")
def set_reference_audio_endpoint(payload: ReferenceAudioPayload):
    ext = os.path.splitext(payload.audio_path)[1].lower()
    if ext not in SUPPORTED_AUDIO_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Audio format '{ext}' is not supported. Supported formats: {SUPPORTED_AUDIO_EXTS}",
        )
    _reference_audios[payload.character_name] = {
        'audio_path': payload.audio_path,
        'audio_text': payload.audio_text,
        'language': normalize_language(payload.language),
    }
    prepare_reference_audio(payload.character_name)
    return {"status": "success", "message": f"Reference audio for '{payload.character_name}' set."}


def run_tts_in_background(
        character_name: str,
        text: str,
        split_sentence: bool,
        save_path: Optional[str],
        chunk_callback: Callable[[Optional[bytes]], None],
        reserved_session: bool = False,
):
    try:
        context.current_speaker = character_name
        context.current_prompt_audio = prepare_reference_audio(character_name)
        tts_player.start_session(
            play=False,
            split=split_sentence,
            save_path=save_path,
            chunk_callback=chunk_callback,
            reserved_session=reserved_session,
        )
        tts_player.feed(text)
        tts_player.end_session()
        tts_player.wait_for_tts_completion()
    except Exception as e:
        logger.error(f"Error in TTS background task: {e}", exc_info=True)
        tts_player.release_session()
        chunk_callback(None)


async def audio_stream_generator(queue: asyncio.Queue, stop_on_disconnect: bool = False) -> AsyncIterator[bytes]:
    completed = False
    try:
        while True:
            chunk = await queue.get()
            if chunk is None:
                completed = True
                break
            yield chunk
    finally:
        if stop_on_disconnect and not completed:
            tts_player.stop()


async def profiled_audio_stream_generator(
        queue: asyncio.Queue,
        endpoint: str,
        stop_on_disconnect: bool = False,
) -> AsyncIterator[bytes]:
    start = time.perf_counter()
    byte_count = 0
    chunk_count = 0
    try:
        async for chunk in audio_stream_generator(queue, stop_on_disconnect=stop_on_disconnect):
            byte_count += len(chunk)
            chunk_count += 1
            yield chunk
    finally:
        profile_recorder.record(
            "http_stream",
            time.perf_counter() - start,
            {"endpoint": endpoint, "bytes": byte_count, "chunks": chunk_count},
        )


def raw_audio_headers() -> Dict[str, str]:
    return {
        "X-Genie-Audio-Format": RAW_AUDIO_FORMAT,
        "X-Genie-Sample-Rate": str(tts_player.sample_rate),
        "X-Genie-Channels": str(tts_player.channels),
        "X-Genie-Sample-Width": str(tts_player.bytes_per_sample),
    }


def stream_wav_headers() -> Dict[str, str]:
    return {
        **raw_audio_headers(),
        "X-Genie-Audio-Format": STREAM_WAV_AUDIO_FORMAT,
        "X-Genie-Inner-Audio-Format": RAW_AUDIO_FORMAT,
        "X-Genie-Stream-Mode": "http_chunked",
        "Cache-Control": "no-store",
        "Content-Disposition": 'inline; filename="genie-tts-stream.wav"',
    }


def estimate_stream_wav_data_size(text: str) -> int:
    block_align = tts_player.channels * tts_player.bytes_per_sample
    byte_rate = tts_player.sample_rate * block_align
    estimated_seconds = max(30.0, min(3600.0, len(text) * 0.55))
    estimated_size = int(byte_rate * estimated_seconds)
    estimated_size += block_align - (estimated_size % block_align)
    return min(estimated_size, 0x7FFFF000)


def streaming_wav_header(data_size: int) -> bytes:
    channels = tts_player.channels
    sample_width = tts_player.bytes_per_sample
    sample_rate = tts_player.sample_rate
    bits_per_sample = sample_width * 8
    block_align = channels * sample_width
    byte_rate = sample_rate * block_align
    riff_size = min(36 + data_size, 0xFFFFFFFF)
    return b"".join([
        b"RIFF",
        struct.pack("<I", riff_size),
        b"WAVE",
        b"fmt ",
        struct.pack("<IHHIIHH", 16, 1, channels, sample_rate, byte_rate, block_align, bits_per_sample),
        b"data",
        struct.pack("<I", data_size),
    ])


async def profiled_wav_stream_generator(
        queue: asyncio.Queue,
        endpoint: str,
        estimated_data_size: int,
        reader_request_id: Optional[str] = None,
) -> AsyncIterator[bytes]:
    start = time.perf_counter()
    byte_count = 0
    chunk_count = 0
    completed = False
    error_detail = None
    try:
        header = streaming_wav_header(estimated_data_size)
        byte_count += len(header)
        chunk_count += 1
        yield header
        while True:
            chunk = await queue.get()
            if chunk is None:
                completed = True
                break
            byte_count += len(chunk)
            chunk_count += 1
            yield chunk
    except Exception as exc:
        error_detail = exception_detail(exc)
        raise
    finally:
        if not completed:
            tts_player.stop()
        if completed:
            reader_request_tracker.finish(reader_request_id, "completed", byte_count, chunk_count)
        elif error_detail:
            reader_request_tracker.finish(reader_request_id, "failed", byte_count, chunk_count, error_detail)
        else:
            reader_request_tracker.finish(reader_request_id, "interrupted", byte_count, chunk_count)
        profile_recorder.record(
            "http_wav_stream",
            time.perf_counter() - start,
            {"endpoint": endpoint, "bytes": byte_count, "chunks": chunk_count},
        )


def validate_tts_character(character_name: str) -> None:
    if character_name not in _reference_audios:
        raise HTTPException(status_code=404, detail="Reference audio not set for this character.")
    if not model_manager.has_character(character_name):
        raise HTTPException(status_code=404, detail="Character model is not loaded.")


def validate_tts_payload(payload: TTSPayload) -> None:
    validate_tts_character(payload.character_name)


def start_reserved_tts_task(payload: TTSPayload, loop: asyncio.AbstractEventLoop) -> asyncio.Queue:
    stream_queue: asyncio.Queue[Union[bytes, None]] = asyncio.Queue()

    def tts_chunk_callback(chunk: Optional[bytes]):
        loop.call_soon_threadsafe(stream_queue.put_nowait, chunk)

    try:
        loop.run_in_executor(
            None,
            run_tts_in_background,
            payload.character_name,
            payload.text,
            payload.split_sentence,
            payload.save_path,
            tts_chunk_callback,
            True,
        )
    except Exception:
        tts_player.release_session()
        raise
    return stream_queue


def start_tts_task(payload: TTSPayload, loop: asyncio.AbstractEventLoop) -> asyncio.Queue:
    if job_manager.has_active_job():
        raise HTTPException(status_code=409, detail="A queued TTS job is using or waiting for the TTS session.")
    try:
        tts_player.reserve_session()
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return start_reserved_tts_task(payload, loop)


async def start_tts_task_after_wait(
        payload: TTSPayload,
        loop: asyncio.AbstractEventLoop,
        wait_timeout_seconds: float,
) -> asyncio.Queue:
    deadline = time.perf_counter() + max(0.0, wait_timeout_seconds)
    last_error = "A TTS session is already active."
    while True:
        if not job_manager.has_active_job():
            try:
                tts_player.reserve_session()
                return start_reserved_tts_task(payload, loop)
            except RuntimeError as exc:
                last_error = str(exc)
        else:
            last_error = "A queued TTS job is using or waiting for the TTS session."

        if time.perf_counter() >= deadline:
            raise HTTPException(status_code=409, detail=last_error)
        await asyncio.sleep(0.1)


def pcm_bytes_to_wav(pcm_bytes: bytes) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(tts_player.channels)
        wav_file.setsampwidth(tts_player.bytes_per_sample)
        wav_file.setframerate(tts_player.sample_rate)
        wav_file.writeframes(pcm_bytes)
    return buffer.getvalue()


def read_wav_duration(path: Union[str, Path]) -> float:
    with wave.open(str(path), "rb") as wav_file:
        return wav_file.getnframes() / float(wav_file.getframerate())


def parse_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return default


def first_present(data: Dict[str, Any], names: List[str], default: Any = None) -> Any:
    for name in names:
        value = data.get(name)
        if value is not None:
            return value
    return default


def parse_wait_timeout(request: Request, default: float = 300.0) -> float:
    value = request.query_params.get("wait_timeout")
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="wait_timeout must be a number of seconds.") from exc
    return max(0.0, min(parsed, 1800.0))


def parse_reader_mode(request: Request) -> str:
    value = first_present(
        dict(request.query_params),
        ["mode", "response_mode", "stream_mode"],
        "stream",
    )
    mode = str(value).strip().lower()
    if mode in {"stream", "streaming", "chunked", "http_chunked"}:
        return "stream"
    if mode in {"buffer", "buffered", "complete", "complete_wav", "wav"}:
        return "buffered"
    raise HTTPException(status_code=400, detail="mode must be 'stream' or 'buffered'.")


async def parse_tts_request_payload(request: Request, default_split_sentence: bool) -> TTSPayload:
    values: Dict[str, Any] = dict(request.query_params)
    content_type = request.headers.get("content-type", "").lower()
    body = await request.body()
    if body:
        if "application/json" in content_type:
            try:
                parsed = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=400, detail="Invalid JSON request body.") from exc
            if not isinstance(parsed, dict):
                raise HTTPException(status_code=400, detail="JSON body must be an object.")
            values.update(parsed)
        else:
            parsed_form = parse_qs(body.decode("utf-8", "replace"), keep_blank_values=True)
            values.update({key: item[-1] for key, item in parsed_form.items()})

    text = first_present(values, ["text", "speakText", "speak_text", "q"])
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty.")

    character_name = first_present(values, ["character_name", "character", "speaker", "voice"], LEGADO_DEFAULT_CHARACTER)
    split_sentence = parse_bool(
        first_present(values, ["split_sentence", "splitSentence", "split"]),
        default=default_split_sentence,
    )
    return TTSPayload(character_name=str(character_name), text=text, split_sentence=split_sentence)


async def raw_tts_response(payload: TTSPayload) -> StreamingResponse:
    validate_tts_payload(payload)
    loop = asyncio.get_running_loop()
    stream_queue = start_tts_task(payload, loop)
    return StreamingResponse(
        profiled_audio_stream_generator(stream_queue, "/tts/raw", stop_on_disconnect=True),
        media_type=RAW_AUDIO_MEDIA_TYPE,
        headers=raw_audio_headers(),
    )


async def stream_wav_tts_response(
        payload: TTSPayload,
        endpoint: str,
        wait_timeout_seconds: float,
        reader_request_id: Optional[str] = None,
) -> StreamingResponse:
    try:
        validate_tts_payload(payload)
        loop = asyncio.get_running_loop()
        reader_request_tracker.update(reader_request_id, "waiting_for_session")
        stream_queue = await start_tts_task_after_wait(payload, loop, wait_timeout_seconds)
        reader_request_tracker.update(reader_request_id, "streaming")
        return StreamingResponse(
            profiled_wav_stream_generator(
                stream_queue,
                endpoint,
                estimate_stream_wav_data_size(payload.text),
                reader_request_id=reader_request_id,
            ),
            media_type="audio/wav",
            headers={
                **stream_wav_headers(),
                "X-Genie-Reader-Mode": "stream",
            },
        )
    except Exception as exc:
        reader_request_tracker.finish(reader_request_id, exception_status(exc), error_detail=exception_detail(exc))
        raise


async def buffered_wav_tts_response(
        payload: TTSPayload,
        endpoint: str,
        wait_timeout_seconds: float,
        reader_request_id: Optional[str] = None,
) -> Response:
    start = time.perf_counter()
    byte_count = 0
    chunk_count = 0
    pcm_chunks = bytearray()
    try:
        validate_tts_payload(payload)
        loop = asyncio.get_running_loop()
        reader_request_tracker.update(reader_request_id, "waiting_for_session")
        stream_queue = await start_tts_task_after_wait(payload, loop, wait_timeout_seconds)
        reader_request_tracker.update(reader_request_id, "buffering")
        async for chunk in audio_stream_generator(stream_queue):
            pcm_chunks.extend(chunk)
            chunk_count += 1
        wav_bytes = pcm_bytes_to_wav(bytes(pcm_chunks))
        byte_count = len(wav_bytes)
        reader_request_tracker.finish(reader_request_id, "completed", byte_count, chunk_count)
        return Response(
            content=wav_bytes,
            media_type="audio/wav",
            headers={
                **raw_audio_headers(),
                "X-Genie-Audio-Format": "wav_pcm_s16le",
                "X-Genie-Inner-Audio-Format": RAW_AUDIO_FORMAT,
                "X-Genie-Stream-Mode": "buffered",
                "X-Genie-Reader-Mode": "buffered",
                "Cache-Control": "no-store",
                "Content-Disposition": 'inline; filename="genie-tts-buffered.wav"',
            },
        )
    except Exception as exc:
        reader_request_tracker.finish(reader_request_id, exception_status(exc), byte_count, chunk_count, exception_detail(exc))
        raise
    finally:
        profile_recorder.record(
            "http_wav_buffered_response",
            time.perf_counter() - start,
            {"endpoint": endpoint, "bytes": byte_count},
        )


@app.post("/tts")
async def tts_endpoint(payload: TTSPayload):
    return await raw_tts_response(payload)


@app.post("/tts/raw")
async def tts_raw_endpoint(payload: TTSPayload):
    return await raw_tts_response(payload)


@app.api_route("/tts/stream.wav", methods=["GET", "POST"])
async def tts_stream_wav_endpoint(request: Request):
    payload = await parse_tts_request_payload(request, default_split_sentence=True)
    wait_timeout = parse_wait_timeout(request)
    mode = parse_reader_mode(request)
    request_id = reader_request_tracker.start(payload, "/tts/stream.wav", mode, wait_timeout)
    if mode == "buffered":
        return await buffered_wav_tts_response(payload, "/tts/stream.wav", wait_timeout, request_id)
    return await stream_wav_tts_response(payload, "/tts/stream.wav", wait_timeout, request_id)


@app.api_route("/tts/legado.wav", methods=["GET", "POST"])
async def tts_legado_wav_endpoint(request: Request):
    payload = await parse_tts_request_payload(request, default_split_sentence=True)
    wait_timeout = parse_wait_timeout(request)
    mode = parse_reader_mode(request)
    request_id = reader_request_tracker.start(payload, "/tts/legado.wav", mode, wait_timeout)
    if mode == "buffered":
        return await buffered_wav_tts_response(payload, "/tts/legado.wav", wait_timeout, request_id)
    return await stream_wav_tts_response(payload, "/tts/legado.wav", wait_timeout, request_id)


@app.post("/tts/wav")
async def tts_wav_endpoint(payload: TTSPayload):
    start = time.perf_counter()
    byte_count = 0
    validate_tts_payload(payload)
    loop = asyncio.get_running_loop()
    stream_queue = start_tts_task(payload, loop)
    pcm_chunks = bytearray()
    try:
        async for chunk in audio_stream_generator(stream_queue):
            pcm_chunks.extend(chunk)
        wav_bytes = pcm_bytes_to_wav(bytes(pcm_chunks))
        byte_count = len(wav_bytes)
        return Response(
            content=wav_bytes,
            media_type="audio/wav",
            headers={
                **raw_audio_headers(),
                "X-Genie-Audio-Format": "wav_pcm_s16le",
                "X-Genie-Inner-Audio-Format": RAW_AUDIO_FORMAT,
                "Cache-Control": "no-store",
                "Content-Disposition": 'inline; filename="genie-tts-complete.wav"',
            },
        )
    finally:
        profile_recorder.record(
            "http_wav_response",
            time.perf_counter() - start,
            {"endpoint": "/tts/wav", "bytes": byte_count},
        )


@app.post("/jobs/tts", status_code=202)
def submit_tts_job_endpoint(payload: TTSJobPayload):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty.")
    validate_tts_character(payload.character_name)
    reject_unsupported_parallel_request(payload)
    record = job_manager.submit(payload)
    return {"job_id": record.job_id, "job": record.to_dict()}


@app.get("/jobs")
def list_jobs_endpoint():
    return {"jobs": job_manager.list_jobs()}


@app.get("/jobs/{job_id}")
def get_job_endpoint(job_id: str):
    try:
        return job_manager.snapshot(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found.") from exc


@app.post("/jobs/{job_id}/cancel")
def cancel_job_endpoint(job_id: str):
    try:
        return job_manager.cancel(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/jobs/{job_id}/wav")
def download_job_wav_endpoint(job_id: str):
    try:
        record = job_manager.get(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found.") from exc
    if record.status != "completed":
        raise HTTPException(status_code=409, detail=f"Job is {record.status}; WAV is not ready.")
    output_path = Path(record.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=410, detail="Job WAV output is missing.")
    return FileResponse(
        output_path,
        media_type="audio/wav",
        filename=f"{job_id}.wav",
        headers={
            **raw_audio_headers(),
            "X-Genie-Audio-Format": "wav_pcm_s16le",
            "X-Genie-Job-Id": job_id,
        },
    )


@app.post("/stop")
def stop_endpoint():
    try:
        job_manager.cancel_running("Stopped through /stop.")
        tts_player.stop()
        return {"status": "success", "message": "TTS stopped."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear_reference_audio_cache")
def clear_reference_audio_cache_endpoint():
    try:
        ReferenceAudio.clear_cache()
        return {"status": "success", "message": "Reference audio cache cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ui")
@app.get("/ui/")
def webui_endpoint():
    """Serve the browser TTS inference panel."""
    index_path = WEBUI_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="WebUI index.html was not found.")
    response = FileResponse(index_path)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/ui/config")
def webui_config_endpoint(request: Request):
    """Return WebUI defaults and dynamic local/LAN access URLs."""
    characters = merged_character_presets()
    default_preset = default_character_preset(characters)
    default_character = str(default_preset.get("name") or LEGADO_DEFAULT_CHARACTER)
    access = access_urls_for_request(request)
    listen = current_listen_config(request)
    return {
        "defaults": {
            "runtime_mode": "cuda",
            "runtime_modes": ["cuda", "cpu", "auto"],
            "character_name": default_character,
            "preset_id": str(default_preset.get("id") or ""),
            "onnx_model_dir": str(default_preset.get("onnx_model_dir") or ""),
            "language": str(default_preset.get("language") or "Chinese"),
            "reference_audio_path": str(default_preset.get("reference_audio_path") or ""),
            "reference_text": str(default_preset.get("reference_text") or DEFAULT_REFERENCE_TEXT),
            "reference_name": str(default_preset.get("reference_name") or "Normal"),
            "input_text": DEFAULT_INPUT_TEXT,
            "split_sentence": True,
            "unload_sessions": False,
            "parallel_enabled": False,
            "parallel_workers": 1,
        },
        "characters": characters or [default_preset],
        "presets": characters or [default_preset],
        "languages": LANGUAGE_OPTIONS,
        "parallel": job_parallel_capability(),
        "memory_policy": runtime_memory_policy_snapshot(sample_gpu=False),
        "endpoints": {
            "ui": "/ui",
            "ui_config": "/ui/config",
            "characters": "/characters",
            "character_presets": "/characters/presets",
            "character_preset": "/characters/presets/{preset_id}",
            "conversion_scan": "/convert/gpt-sovits/scan",
            "conversion_submit": "/convert/gpt-sovits",
            "conversion_jobs": "/convert/gpt-sovits/jobs",
            "conversion_job_status": "/convert/gpt-sovits/jobs/{job_id}",
            "server_listen": "/server/listen",
            "server_restart": "/server/restart",
            "runtime_memory": "/runtime/memory",
            "runtime_memory_action": "/runtime/memory/action",
            "load_character": "/load_character",
            "unload_character": "/unload_character",
            "set_reference_audio": "/set_reference_audio",
            "runtime_configure": "/runtime/configure",
            "runtime": "/runtime",
            "status": "/status",
            "health": "/health",
            "profile": "/profile",
            "raw": "/tts/raw",
            "stream_wav": "/tts/stream.wav?wait_timeout=300",
            "complete_wav": "/tts/wav",
            "legado_buffered": "/tts/legado.wav?wait_timeout=300&mode=buffered",
            "legado_stream": "/tts/legado.wav?wait_timeout=300",
            "stop": "/stop",
            "clear_reference_audio_cache": "/clear_reference_audio_cache",
            "job_submit": "/jobs/tts",
            "job_list": "/jobs",
            "job_status": "/jobs/{job_id}",
            "job_cancel": "/jobs/{job_id}/cancel",
            "job_wav": "/jobs/{job_id}/wav",
        },
        "access": access,
        "listen": listen,
        "conversion": {
            "output_root": str(CONVERSION_OUTPUT_ROOT),
            "supported_inputs": [".ckpt", ".pth"],
            "output_layout": "CharacterModels\\Converted\\<name>\\tts_models",
            "requires_torch": True,
        },
        "reader": reader_webui_config(access, default_character),
        "endpoint_catalog": endpoint_catalog(),
        "audio_formats": {
            "raw_pcm": {
                "endpoint": "/tts/raw",
                "media_type": RAW_AUDIO_MEDIA_TYPE,
                "format": RAW_AUDIO_FORMAT,
                "playable_in_browser": False,
            },
            "stream_wav": {
                "endpoints": ["/tts/stream.wav", "/tts/legado.wav"],
                "media_type": "audio/wav",
                "format": STREAM_WAV_AUDIO_FORMAT,
                "complete_file": False,
            },
            "buffered_wav": {
                "endpoint": "/tts/legado.wav?mode=buffered",
                "media_type": "audio/wav",
                "format": "wav_pcm_s16le",
                "complete_file": True,
            },
            "complete_wav": {
                "endpoint": "/tts/wav",
                "media_type": "audio/wav",
                "format": "wav_pcm_s16le",
                "complete_file": True,
            },
            "job_wav": {
                "endpoint": "/jobs/{job_id}/wav",
                "media_type": "audio/wav",
                "format": "wav_pcm_s16le",
                "complete_file": True,
            },
        },
    }


@app.get("/characters")
def characters_endpoint():
    """Return discovered and user-saved local character presets."""
    auto_characters = discover_character_presets()
    user_presets = load_user_character_presets()
    characters = merged_character_presets()
    return {
        "character_models_dir": str(CHARACTER_MODELS_DIR),
        "user_presets_file": str(USER_CHARACTER_PRESETS_FILE),
        "count": len(characters),
        "auto_count": len(auto_characters),
        "user_count": len(user_presets),
        "default_character": default_character_preset(characters).get("name"),
        "default_preset_id": default_character_preset(characters).get("id"),
        "characters": characters,
        "presets": characters,
    }


@app.post("/characters/presets")
def save_character_preset_endpoint(payload: CharacterPresetPayload):
    """Save a WebUI user character preset."""
    model_dir = Path(payload.onnx_model_dir)
    if not model_dir.is_dir():
        raise HTTPException(status_code=400, detail=f"ONNX model directory does not exist: {payload.onnx_model_dir}")
    reference_audio_path = str(payload.reference_audio_path or "").strip()
    if reference_audio_path and not Path(reference_audio_path).is_file():
        raise HTTPException(status_code=400, detail=f"Reference audio file does not exist: {reference_audio_path}")

    raw_preset = {
        "name": payload.name.strip(),
        "label": (payload.label or "").strip(),
        "family": (payload.family or "").strip(),
        "onnx_model_dir": str(model_dir),
        "language": normalize_language(payload.language),
        "reference_audio_path": reference_audio_path,
        "reference_text": payload.reference_text or "",
        "reference_name": payload.reference_name or "",
    }
    preset = normalize_character_preset(raw_preset, source="user")
    if not preset:
        raise HTTPException(status_code=400, detail="Preset name and ONNX model directory are required.")

    user_presets = [
        item for item in load_user_character_presets()
        if str(item.get("id")) != str(preset.get("id"))
    ]
    user_presets.append(preset)
    save_user_character_presets(user_presets)
    merged = merged_character_presets()
    return {
        "status": "success",
        "message": "Character preset saved.",
        "preset": preset,
        "count": len(merged),
        "characters": merged,
        "presets": merged,
    }


@app.delete("/characters/presets/{preset_id}")
def delete_character_preset_endpoint(preset_id: str):
    """Delete a user-created WebUI character preset."""
    normalized_id = str(preset_id or "").strip()
    if not normalized_id:
        raise HTTPException(status_code=400, detail="Preset id is required.")
    user_presets = load_user_character_presets()
    remaining = [item for item in user_presets if str(item.get("id")) != normalized_id]
    if len(remaining) == len(user_presets):
        auto_match = next((item for item in discover_character_presets() if str(item.get("id")) == normalized_id), None)
        if auto_match:
            raise HTTPException(status_code=409, detail="Auto-discovered presets cannot be deleted.")
        raise HTTPException(status_code=404, detail=f"User preset not found: {normalized_id}")
    save_user_character_presets(remaining)
    merged = merged_character_presets()
    return {
        "status": "success",
        "message": "Character preset deleted.",
        "deleted_preset_id": normalized_id,
        "count": len(merged),
        "characters": merged,
        "presets": merged,
    }


@app.post("/convert/gpt-sovits/scan")
def scan_gpt_sovits_conversion_endpoint(payload: ConversionScanPayload):
    """Scan local GPT-SoVITS folders for .ckpt/.pth pairs without importing PyTorch."""
    return scan_conversion_sources(payload.folders, payload.output_root, payload.overwrite)


@app.post("/convert/gpt-sovits", status_code=202)
def submit_gpt_sovits_conversion_endpoint(payload: ConversionSubmitPayload):
    """Submit a background GPT-SoVITS to GENIE conversion job."""
    try:
        record = conversion_job_manager.submit(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"job_id": record.job_id, "job": record.to_dict()}


@app.get("/convert/gpt-sovits/jobs")
def list_gpt_sovits_conversion_jobs_endpoint():
    """Return recent GPT-SoVITS conversion jobs."""
    return {"jobs": conversion_job_manager.list_jobs()}


@app.get("/convert/gpt-sovits/jobs/{job_id}")
def get_gpt_sovits_conversion_job_endpoint(job_id: str):
    """Return a single GPT-SoVITS conversion job snapshot."""
    try:
        return conversion_job_manager.snapshot(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Conversion job not found.") from exc


@app.get("/server/listen")
def server_listen_endpoint(request: Request):
    """Return current listener and restart metadata for WebUI controls."""
    access = access_urls_for_request(request)
    return {
        "status": "ok",
        "listen": current_listen_config(request),
        "access": access,
        "busy": service_busy(),
    }


def normalized_restart_host(host: str) -> str:
    value = str(host or "").strip()
    allowed = {"0.0.0.0", "127.0.0.1", "localhost"}
    lan_addresses = set(get_lan_ipv4_addresses())
    if value in allowed or value in lan_addresses:
        return "127.0.0.1" if value == "localhost" else value
    raise HTTPException(status_code=400, detail=f"Unsupported listen host: {value}")


def normalized_restart_port(port: int) -> int:
    try:
        value = int(port)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Port must be an integer.") from exc
    if value == 0:
        return value
    if 1 <= value <= 65535:
        return value
    raise HTTPException(status_code=400, detail="Port must be 0 or between 1 and 65535.")


def schedule_process_exit(delay_seconds: float = 1.25) -> None:
    def exit_current_process() -> None:
        time.sleep(delay_seconds)
        os._exit(0)

    threading.Thread(target=exit_current_process, daemon=True).start()


@app.post("/server/restart", status_code=202)
def server_restart_endpoint(payload: ServerRestartPayload, request: Request):
    """Restart the package-local WebUI/API process with a different host or port."""
    if service_busy():
        raise HTTPException(status_code=409, detail="Cannot restart while TTS, jobs, or reader requests are active.")
    if not START_WEBUI_SCRIPT.exists():
        raise HTTPException(status_code=500, detail=f"WebUI launcher was not found: {START_WEBUI_SCRIPT}")

    host = normalized_restart_host(payload.host)
    port = normalized_restart_port(payload.port)
    runtime = payload.runtime or os.environ.get("GENIE_WEBUI_RUNTIME") or model_manager.get_runtime_info().get("runtime_mode", "cuda")
    if runtime not in {"cpu", "cuda", "directml", "auto"}:
        raise HTTPException(status_code=400, detail=f"Unsupported runtime mode: {runtime}")

    python_exe = PACKAGE_PYTHON_EXE if PACKAGE_PYTHON_EXE.exists() else Path(sys.executable)
    command = [
        str(python_exe),
        str(START_WEBUI_SCRIPT),
        "--host",
        host,
        "--port",
        str(port),
        "--runtime",
        runtime,
        "--no-open",
        "--strict-port",
    ]
    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["GENIE_WEBUI_HOST"] = host
    env["GENIE_WEBUI_PORT"] = str(port)
    env["GENIE_WEBUI_RUNTIME"] = runtime

    helper_code = (
        "import os, subprocess, sys, time\n"
        "delay=float(sys.argv[1]); cwd=sys.argv[2]; log_dir=sys.argv[3]; command=sys.argv[4:]\n"
        "time.sleep(delay)\n"
        "os.makedirs(log_dir, exist_ok=True)\n"
        "out=open(os.path.join(log_dir, 'webui-restart.out.log'), 'ab', buffering=0)\n"
        "err=open(os.path.join(log_dir, 'webui-restart.err.log'), 'ab', buffering=0)\n"
        "flags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)\n"
        "subprocess.Popen(command, cwd=cwd, stdout=out, stderr=err, close_fds=True, creationflags=flags)\n"
    )
    log_dir = REPO_ROOT / "UserData" / "Logs"
    helper_command = [
        str(python_exe),
        "-c",
        helper_code,
        "1.6",
        str(REPO_ROOT),
        str(log_dir),
        *command,
    ]
    try:
        subprocess.Popen(
            helper_command,
            cwd=str(REPO_ROOT),
            env=env,
            close_fds=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to start restart helper: {exc}") from exc

    scheme = request.url.scheme
    local_url = f"{scheme}://127.0.0.1:{port}/ui" if port else "pending"
    lan_urls = [f"{scheme}://{address}:{port}/ui" for address in get_lan_ipv4_addresses()] if port else []
    schedule_process_exit()
    return {
        "status": "restarting",
        "message": "A new WebUI process is being started. This process will exit shortly.",
        "host": host,
        "port": port,
        "runtime": runtime,
        "local_url": local_url,
        "lan_urls": lan_urls,
        "command": command,
    }


@app.get("/health")
def health_endpoint():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/runtime/configure")
def configure_runtime_endpoint(payload: RuntimeConfigurePayload):
    """Configure ONNX Runtime providers for sessions loaded after this call."""
    loaded_before = list(model_manager.character_to_model.keys())
    if payload.unload_sessions:
        tts_status = tts_player.status_snapshot()
        job_status = job_manager.status_snapshot()
        reader_status = reader_request_tracker.snapshot()
        if tts_status["session_active"] or job_status["has_active_job"] or reader_status["active_count"]:
            raise HTTPException(status_code=409, detail="Cannot unload sessions while TTS is busy.")

    try:
        result = model_manager.configure_runtime(payload.mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if payload.unload_sessions:
        model_manager.unload_runtime_sessions()
    loaded_characters = list(model_manager.character_to_model.keys())
    reload_required = bool(loaded_characters or (payload.unload_sessions and loaded_before))
    if payload.unload_sessions and loaded_before:
        message = "Runtime configured and loaded sessions were unloaded. Reload character models before synthesis."
    elif payload.unload_sessions:
        message = "Runtime configured. No loaded sessions needed unloading."
    elif loaded_characters:
        message = "Runtime configured. Already loaded ONNX sessions keep their previous providers until reloaded."
    else:
        message = "Runtime configured. Load character models after this call to use the selected providers."
    return {
        "status": "success",
        "runtime": result,
        "loaded_characters": loaded_characters,
        "unloaded_characters": loaded_before if payload.unload_sessions else [],
        "unload_requested": bool(payload.unload_sessions),
        "sessions_unloaded": bool(payload.unload_sessions and loaded_before),
        "reload_required_for_loaded_sessions": reload_required,
        "message": message,
    }


@app.get("/runtime/memory")
def runtime_memory_endpoint():
    """Return GPU memory telemetry and the current memory/concurrency policy."""
    return runtime_memory_policy_snapshot(sample_gpu=True)


@app.post("/runtime/memory/action")
def runtime_memory_action_endpoint(payload: MemoryActionPayload):
    """Run safe memory/concurrency actions exposed by the WebUI."""
    action = str(payload.action or "").strip().lower()
    if action in {"refresh", ""}:
        return runtime_memory_policy_snapshot(sample_gpu=True)

    if action == "clear_reference_cache":
        ReferenceAudio.clear_cache()
        snapshot = runtime_memory_policy_snapshot(sample_gpu=True)
        snapshot.update({
            "action": action,
            "message": "Reference audio cache cleared.",
        })
        return snapshot

    if action == "release_idle_sessions" and service_busy():
        raise HTTPException(status_code=409, detail="Cannot change memory/runtime policy while TTS, jobs, or reader requests are active.")

    if action == "release_idle_sessions":
        loaded_before = list(model_manager.character_to_model.keys())
        model_manager.unload_runtime_sessions()
        snapshot = runtime_memory_policy_snapshot(sample_gpu=True)
        snapshot.update({
            "action": action,
            "unloaded_characters": loaded_before,
            "message": "Loaded model sessions were released. Reload character models before synthesis.",
        })
        return snapshot

    raise HTTPException(
        status_code=400,
        detail="Unsupported memory action. Use refresh, release_idle_sessions, or clear_reference_cache.",
    )


@app.get("/status")
def status_endpoint():
    """Return lightweight service activity diagnostics without request text."""
    tts_status = tts_player.status_snapshot()
    job_status = job_manager.status_snapshot()
    reader_status = reader_request_tracker.snapshot()
    conversion_jobs = conversion_job_manager.list_jobs()
    active_conversion_jobs = [
        item for item in conversion_jobs
        if item.get("status") in {"queued", "running"}
    ]
    active_progress = None
    if tts_status["session_active"]:
        active_progress = tts_status.get("progress")
    elif job_status["active"]:
        active_progress = job_status["active"][0].get("progress")
    return {
        "status": "ok",
        "busy": bool(
            tts_status["session_active"]
            or job_status["has_active_job"]
            or reader_status["active_count"]
            or active_conversion_jobs
        ),
        "active_tts_session": tts_status["session_active"],
        "tts_player": tts_status,
        "jobs": job_status,
        "conversion_jobs": {
            "has_active_job": bool(active_conversion_jobs),
            "active_count": len(active_conversion_jobs),
            "active": active_conversion_jobs,
            "last": conversion_jobs[0] if conversion_jobs else None,
        },
        "reader_requests": reader_status,
        "last_reader_request": reader_status["last"],
        "active_progress": active_progress,
    }


@app.get("/runtime")
def runtime_endpoint():
    """Return current ONNX Runtime environment information."""
    runtime_info = model_manager.get_runtime_info()
    runtime_info["job_parallel"] = job_parallel_capability()
    runtime_info["api_audio"] = {
        "raw_endpoint": "/tts/raw",
        "raw_alias_endpoint": "/tts",
        "status_endpoint": "/status",
        "stream_wav_endpoint": "/tts/stream.wav",
        "legado_stream_wav_endpoint": "/tts/legado.wav",
        "wav_endpoint": "/tts/wav",
        "job_submit_endpoint": "/jobs/tts",
        "job_list_endpoint": "/jobs",
        "job_status_endpoint": "/jobs/{job_id}",
        "job_cancel_endpoint": "/jobs/{job_id}/cancel",
        "job_wav_endpoint": "/jobs/{job_id}/wav",
        "job_output_dir": str(JOB_OUTPUT_DIR),
        "raw_media_type": RAW_AUDIO_MEDIA_TYPE,
        "raw_format": RAW_AUDIO_FORMAT,
        "stream_wav_media_type": "audio/wav",
        "stream_wav_format": STREAM_WAV_AUDIO_FORMAT,
        "reader_response_modes": ["stream", "buffered"],
        "reader_buffered_query": "mode=buffered",
        "job_parallel": runtime_info["job_parallel"],
        "sample_rate": tts_player.sample_rate,
        "channels": tts_player.channels,
        "sample_width": tts_player.bytes_per_sample,
    }
    return runtime_info


@app.get("/profile")
def profile_endpoint():
    """Return in-process profiling events and stage timing summaries."""
    return profile_recorder.snapshot(include_events=True)


@app.post("/profile")
def update_profile_endpoint(payload: ProfilePayload):
    """Enable, disable, or clear profiling without restarting the API server."""
    if payload.enabled is not None:
        profile_recorder.set_enabled(payload.enabled)
    if payload.clear:
        profile_recorder.clear()
    return profile_recorder.snapshot(include_events=payload.include_events)


def start_server(host: str = "127.0.0.1", port: int = 8000, workers: int = 1):
    uvicorn.run(app, host=host, port=port, workers=workers)


if __name__ == "__main__":
    start_server(host="0.0.0.0", port=8000, workers=1)
