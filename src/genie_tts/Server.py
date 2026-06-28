import asyncio
import io
import os
import time
import wave
from typing import AsyncIterator, Optional, Callable, Union, Dict
import logging

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, StreamingResponse
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


class ProfilePayload(BaseModel):
    enabled: Optional[bool] = None
    clear: bool = False
    include_events: bool = True


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


async def audio_stream_generator(queue: asyncio.Queue) -> AsyncIterator[bytes]:
    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        yield chunk


async def profiled_audio_stream_generator(queue: asyncio.Queue, endpoint: str) -> AsyncIterator[bytes]:
    start = time.perf_counter()
    byte_count = 0
    chunk_count = 0
    try:
        async for chunk in audio_stream_generator(queue):
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


def validate_tts_payload(payload: TTSPayload) -> None:
    if payload.character_name not in _reference_audios:
        raise HTTPException(status_code=404, detail="Reference audio not set for this character.")
    if not model_manager.has_character(payload.character_name):
        raise HTTPException(status_code=404, detail="Character model is not loaded.")


def start_tts_task(payload: TTSPayload, loop: asyncio.AbstractEventLoop) -> asyncio.Queue:
    stream_queue: asyncio.Queue[Union[bytes, None]] = asyncio.Queue()
    try:
        tts_player.reserve_session()
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

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


def pcm_bytes_to_wav(pcm_bytes: bytes) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(tts_player.channels)
        wav_file.setsampwidth(tts_player.bytes_per_sample)
        wav_file.setframerate(tts_player.sample_rate)
        wav_file.writeframes(pcm_bytes)
    return buffer.getvalue()


async def raw_tts_response(payload: TTSPayload) -> StreamingResponse:
    validate_tts_payload(payload)
    loop = asyncio.get_running_loop()
    stream_queue = start_tts_task(payload, loop)
    return StreamingResponse(
        profiled_audio_stream_generator(stream_queue, "/tts/raw"),
        media_type=RAW_AUDIO_MEDIA_TYPE,
        headers=raw_audio_headers(),
    )


@app.post("/tts")
async def tts_endpoint(payload: TTSPayload):
    return await raw_tts_response(payload)


@app.post("/tts/raw")
async def tts_raw_endpoint(payload: TTSPayload):
    return await raw_tts_response(payload)


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


@app.post("/stop")
def stop_endpoint():
    try:
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
        "wav_endpoint": "/tts/wav",
        "raw_media_type": RAW_AUDIO_MEDIA_TYPE,
        "raw_format": RAW_AUDIO_FORMAT,
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
