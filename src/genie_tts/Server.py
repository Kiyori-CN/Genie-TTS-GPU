import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import queue
import struct
import threading
import time
from urllib.parse import parse_qs
import uuid
import wave
from typing import Any, AsyncIterator, Optional, Callable, Union, Dict, List
import logging

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel

from .Audio.ReferenceAudio import ReferenceAudio
from .Core.TTSPlayer import tts_player
from .ModelManager import model_manager
from .Profiling import profile_recorder, profile_span
from .Utils.Shared import context
from .Utils.Language import normalize_language

logger = logging.getLogger(__name__)

_reference_audios: Dict[str, dict] = {}
SUPPORTED_AUDIO_EXTS = {'.wav', '.flac', '.ogg', '.aiff', '.aif'}
RAW_AUDIO_FORMAT = "pcm_s16le"
RAW_AUDIO_MEDIA_TYPE = "application/octet-stream"
STREAM_WAV_AUDIO_FORMAT = "wav_stream_pcm_s16le"
LEGADO_DEFAULT_CHARACTER = "feibi"
JOB_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "UserData" / "Jobs"
TERMINAL_JOB_STATUSES = {"completed", "failed", "cancelled"}

app = FastAPI()


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


class TTSPayload(BaseModel):
    character_name: str
    text: str
    split_sentence: bool = False
    save_path: Optional[str] = None


class TTSJobPayload(BaseModel):
    character_name: str
    text: str
    split_sentence: bool = True


class ProfilePayload(BaseModel):
    enabled: Optional[bool] = None
    clear: bool = False
    include_events: bool = True


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class TTSJobRecord:
    job_id: str
    character_name: str
    text: str
    split_sentence: bool
    output_path: str
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
            "output_path": self.output_path,
            "output_exists": Path(self.output_path).exists(),
            "output_bytes": self.output_bytes,
            "generated_pcm_bytes": self.generated_pcm_bytes,
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
        record = TTSJobRecord(
            job_id=job_id,
            character_name=payload.character_name,
            text=payload.text,
            split_sentence=payload.split_sentence,
            output_path=output_path,
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

        if not self._reserve_tts_session(record):
            return

        pcm_chunks = bytearray()

        def chunk_callback(chunk: Optional[bytes]) -> None:
            if chunk is None:
                return
            pcm_chunks.extend(chunk)
            with self._lock:
                current = self._jobs.get(job_id)
                if current:
                    current.generated_pcm_bytes = len(pcm_chunks)
                    current.message = f"Generated {len(pcm_chunks)} PCM bytes."

        try:
            with self._lock:
                if record.cancel_requested:
                    self._finish_locked(record, "cancelled", "cancelled", "Cancelled before synthesis started.")
                    tts_player.release_session()
                    return
                record.stage = "synthesizing"
                record.message = "Synthesizing audio."

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

            wav_bytes = pcm_bytes_to_wav(bytes(pcm_chunks))
            output_path = Path(record.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(wav_bytes)
            duration = read_wav_duration(output_path)

            with self._lock:
                record.output_bytes = len(wav_bytes)
                record.audio_duration_seconds = duration
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
        record.finished_at = utc_now()
        record.finished_monotonic = time.perf_counter()


job_manager = TTSJobManager(JOB_OUTPUT_DIR)


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
) -> AsyncIterator[bytes]:
    start = time.perf_counter()
    byte_count = 0
    chunk_count = 0
    completed = False
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
    finally:
        if not completed:
            tts_player.stop()
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


async def stream_wav_tts_response(payload: TTSPayload, endpoint: str, wait_timeout_seconds: float) -> StreamingResponse:
    validate_tts_payload(payload)
    loop = asyncio.get_running_loop()
    stream_queue = await start_tts_task_after_wait(payload, loop, wait_timeout_seconds)
    return StreamingResponse(
        profiled_wav_stream_generator(stream_queue, endpoint, estimate_stream_wav_data_size(payload.text)),
        media_type="audio/wav",
        headers=stream_wav_headers(),
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
    return await stream_wav_tts_response(payload, "/tts/stream.wav", wait_timeout)


@app.api_route("/tts/legado.wav", methods=["GET", "POST"])
async def tts_legado_wav_endpoint(request: Request):
    payload = await parse_tts_request_payload(request, default_split_sentence=True)
    wait_timeout = parse_wait_timeout(request)
    return await stream_wav_tts_response(payload, "/tts/legado.wav", wait_timeout)


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
    validate_tts_character(payload.character_name)
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty.")
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


@app.get("/health")
def health_endpoint():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/runtime")
def runtime_endpoint():
    """Return current ONNX Runtime environment information."""
    runtime_info = model_manager.get_runtime_info()
    runtime_info["api_audio"] = {
        "raw_endpoint": "/tts/raw",
        "raw_alias_endpoint": "/tts",
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
