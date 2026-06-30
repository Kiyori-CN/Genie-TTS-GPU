# 文件: .../Core/TTSPlayer.py

import queue
import os
import threading
import time

import numpy as np
import wave
from typing import Optional, List, Callable, Dict, Any
import logging

from ..Utils.TextSplitter import TextSplitter
from ..Core.Inference import tts_client
from ..ModelManager import model_manager
from ..Profiling import profile_span
from ..Utils.Shared import context
from ..Utils.Utils import clear_queue

logger = logging.getLogger(__name__)

STREAM_END = 'STREAM_END'  # 这是一个特殊的标记，表示文本流结束
AUDIO_STREAM_END = 'AUDIO_STREAM_END'  # 新增：特殊的标记，表示音频流播放结束


class TTSPlayer:
    def __init__(self, sample_rate: int = 32000):
        self._text_splitter = TextSplitter()

        self.sample_rate: int = sample_rate
        self.channels: int = 1
        self.bytes_per_sample: int = 2  # 16-bit audio

        self._text_queue: queue.Queue = queue.Queue()
        self._audio_queue: queue.Queue = queue.Queue()

        self._stop_event: threading.Event = threading.Event()
        self._tts_done_event: threading.Event = threading.Event()
        self._playback_done_event: threading.Event = threading.Event()  # 新增：用于标记播放完成
        self._api_lock: threading.Lock = threading.Lock()
        self._progress_lock: threading.Lock = threading.Lock()

        self._tts_worker: Optional[threading.Thread] = None
        self._playback_worker: Optional[threading.Thread] = None

        self._play: bool = False
        self._current_save_path: Optional[str] = None
        self._session_audio_chunks: List[np.ndarray] = []
        self._split: bool = False

        self._chunk_callback: Optional[Callable[[Optional[bytes]], None]] = None
        self._target_rms: float = 10 ** (-23.0 / 20.0)
        self._max_gain: float = 1.55
        self._min_gain: float = 0.65
        self._final_max_gain: float = 1.15
        self._final_min_gain: float = 0.85
        self._peak_limit: float = 0.92
        self._silence_rms: float = 10 ** (-45.0 / 20.0)
        self._loudness_window_samples: int = int(0.25 * self.sample_rate)
        self._loudness_hop_samples: int = int(0.05 * self.sample_rate)
        self._tail_silence_samples: int = int(0.16 * self.sample_rate)
        self._session_active: bool = False
        self._next_segment_index: int = 0
        self._progress: Dict[str, Any] = self._new_progress_snapshot()

    def _new_progress_snapshot(self) -> Dict[str, Any]:
        return {
            "stage": "idle",
            "message": "Idle.",
            "total_chars": 0,
            "completed_chars": 0,
            "total_segments": 0,
            "completed_segments": 0,
            "current_segment_index": 0,
            "current_segment_chars": 0,
            "generated_pcm_bytes": 0,
            "generated_wav_bytes": 0,
            "split_sentence": False,
            "playback_enabled": False,
            "save_path_active": False,
            "started_monotonic": None,
            "finished_monotonic": None,
        }

    def _reset_progress(self, split: bool, play: bool, save_path: Optional[str]) -> None:
        with self._progress_lock:
            self._next_segment_index = 0
            self._progress = self._new_progress_snapshot()
            self._progress.update({
                "stage": "starting",
                "message": "TTS session started.",
                "split_sentence": bool(split),
                "playback_enabled": bool(play),
                "save_path_active": save_path is not None,
                "started_monotonic": time.perf_counter(),
                "finished_monotonic": None,
            })

    def _queue_progress(self, segments: List[str], total_chars: int) -> None:
        with self._progress_lock:
            self._progress["total_chars"] += max(0, total_chars)
            self._progress["total_segments"] += len(segments)
            self._progress["stage"] = "queued"
            self._progress["message"] = f"Queued {self._progress['total_segments']} text segments."

    def _mark_segment_started(self, segment_index: int, segment_chars: int) -> None:
        with self._progress_lock:
            self._progress["stage"] = "synthesizing"
            self._progress["current_segment_index"] = segment_index
            self._progress["current_segment_chars"] = segment_chars
            self._progress["message"] = (
                f"Synthesizing segment {segment_index}/{self._progress['total_segments'] or '?'} ."
            ).replace(" .", ".")

    def _mark_segment_completed(self, segment_index: int, segment_chars: int, pcm_bytes: int) -> None:
        with self._progress_lock:
            self._progress["completed_segments"] = max(self._progress["completed_segments"], segment_index)
            completed_chars = self._progress["completed_chars"] + max(0, segment_chars)
            total_chars = self._progress["total_chars"]
            self._progress["completed_chars"] = min(completed_chars, total_chars) if total_chars else completed_chars
            self._progress["generated_pcm_bytes"] += max(0, pcm_bytes)
            self._progress["message"] = (
                f"Completed segment {self._progress['completed_segments']}/{self._progress['total_segments'] or '?'} ."
            ).replace(" .", ".")

    def _finish_progress(self, stage: str, message: str) -> None:
        with self._progress_lock:
            total_chars = self._progress["total_chars"]
            total_segments = self._progress["total_segments"]
            if stage == "completed":
                self._progress["completed_chars"] = total_chars
                self._progress["completed_segments"] = total_segments
            self._progress["stage"] = stage
            self._progress["message"] = message
            self._progress["finished_monotonic"] = time.perf_counter()

    def _set_progress_wav_bytes(self, wav_bytes: int) -> None:
        with self._progress_lock:
            self._progress["generated_wav_bytes"] = max(0, wav_bytes)

    def progress_snapshot(self) -> Dict[str, Any]:
        with self._progress_lock:
            progress = dict(self._progress)

        now = time.perf_counter()
        started = progress.pop("started_monotonic", None)
        finished = progress.pop("finished_monotonic", None)
        if started is None:
            elapsed = 0.0
        else:
            elapsed = (finished if finished is not None else now) - started

        total_segments = int(progress.get("total_segments") or 0)
        completed_segments = int(progress.get("completed_segments") or 0)
        total_chars = int(progress.get("total_chars") or 0)
        completed_chars = int(progress.get("completed_chars") or 0)
        if progress.get("stage") == "completed":
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

        bytes_per_second = self.sample_rate * self.channels * self.bytes_per_sample
        generated_pcm_bytes = int(progress.get("generated_pcm_bytes") or 0)
        progress.update({
            "elapsed_seconds": elapsed,
            "estimated_remaining_seconds": estimated_remaining,
            "estimated_total_seconds": estimated_total,
            "percent": percent,
            "audio_duration_estimate_seconds": generated_pcm_bytes / float(bytes_per_second) if bytes_per_second else 0.0,
        })
        return progress

    @staticmethod
    def _preprocess_for_playback(audio_float: np.ndarray) -> bytes:
        audio_int16 = (np.clip(audio_float.squeeze(), -1.0, 1.0) * 32767).astype(np.int16)
        return audio_int16.tobytes()

    def _build_loudness_envelope(self, audio: np.ndarray) -> np.ndarray:
        if audio.size <= self._loudness_hop_samples:
            return np.ones(audio.size, dtype=np.float32)

        window = max(1, min(self._loudness_window_samples, audio.size))
        hop = max(1, self._loudness_hop_samples)
        starts = list(range(0, audio.size, hop))
        frame_gains: List[float] = []
        centers: List[float] = []

        for start in starts:
            stop = min(start + window, audio.size)
            frame = audio[start:stop]
            if frame.size == 0:
                continue
            rms = float(np.sqrt(np.mean(frame * frame)) + 1e-12)
            if rms < self._silence_rms:
                gain = 1.0
            else:
                gain = float(np.clip(self._target_rms / rms, self._min_gain, self._max_gain))
            frame_gains.append(gain)
            centers.append(start + 0.5 * (stop - start))

        if not frame_gains:
            return np.ones(audio.size, dtype=np.float32)

        smoothed = np.asarray(frame_gains, dtype=np.float32)
        for i in range(1, smoothed.size):
            previous = float(smoothed[i - 1])
            desired = float(smoothed[i])
            alpha = 0.55 if desired < previous else 0.18
            smoothed[i] = previous + alpha * (desired - previous)

        positions = np.arange(audio.size, dtype=np.float32)
        return np.interp(
            positions,
            np.asarray(centers, dtype=np.float32),
            smoothed,
            left=float(smoothed[0]),
            right=float(smoothed[-1]),
        ).astype(np.float32)

    def _prepare_audio_chunk(self, audio_float: np.ndarray) -> np.ndarray:
        audio = np.asarray(audio_float, dtype=np.float32).squeeze()
        if audio.ndim != 1:
            audio = audio.reshape(-1)
        if audio.size == 0:
            return audio

        audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
        audio = audio * self._build_loudness_envelope(audio)

        active = np.abs(audio) > 1e-4
        if np.count_nonzero(active) > int(0.08 * self.sample_rate):
            rms = float(np.sqrt(np.mean(audio[active] * audio[active])) + 1e-12)
            gain = float(np.clip(self._target_rms / rms, self._final_min_gain, self._final_max_gain))
            audio = audio * gain

        peak = float(np.max(np.abs(audio)))
        if peak > self._peak_limit:
            audio = audio * (self._peak_limit / peak)

        if self._tail_silence_samples > 0:
            audio = np.concatenate([
                audio,
                np.zeros(self._tail_silence_samples, dtype=np.float32),
            ])

        return audio.astype(np.float32, copy=False)

    def _tts_worker_loop(self):
        """从文本队列取句子，生成音频，并通过回调函数或音频队列分发。"""
        while not self._stop_event.is_set():
            try:
                task = self._text_queue.get(timeout=1)
                if task is None or self._stop_event.is_set():
                    break
            except queue.Empty:
                continue

            try:
                if task is STREAM_END:
                    if self._current_save_path and self._session_audio_chunks:
                        self._save_session_audio()

                    # 在TTS工作线程完成时，通过回调发送结束信号
                    if self._chunk_callback:
                        self._chunk_callback(None)

                    # 新增：如果开启了播放，通知音频队列流已结束
                    if self._play:
                        self._audio_queue.put(AUDIO_STREAM_END)

                    self._tts_done_event.set()
                    if not self._stop_event.is_set():
                        self._finish_progress("completed", "TTS synthesis completed.")
                    self._session_active = False
                    continue

                if isinstance(task, dict):
                    sentence = str(task.get("text") or "")
                    segment_index = int(task.get("segment_index") or 0)
                    segment_chars = int(task.get("segment_chars") or len(sentence))
                else:
                    sentence = str(task)
                    segment_index = 0
                    segment_chars = len(sentence)

                gsv_model = model_manager.get(context.current_speaker)
                if not gsv_model or not context.current_prompt_audio:
                    logger.error("Missing model or reference audio.")
                    continue

                tts_client.stop_event.clear()
                self._mark_segment_started(segment_index, segment_chars)
                with profile_span("sentence_tts_total", language=gsv_model.LANGUAGE, text_chars=len(sentence)):
                    audio_chunk = tts_client.tts(
                        text=sentence,
                        prompt_audio=context.current_prompt_audio,
                        encoder=gsv_model.T2S_ENCODER,
                        first_stage_decoder=gsv_model.T2S_FIRST_STAGE_DECODER,
                        stage_decoder=gsv_model.T2S_STAGE_DECODER,
                        vocoder=gsv_model.VITS,
                        prompt_encoder=gsv_model.PROMPT_ENCODER,
                        language=gsv_model.LANGUAGE,
                    )

                if audio_chunk is not None:
                    with profile_span("audio_postprocess", samples=int(np.asarray(audio_chunk).size)):
                        audio_chunk = self._prepare_audio_chunk(audio_chunk)

                    if self._play:
                        self._audio_queue.put(audio_chunk)
                    if self._current_save_path:
                        self._session_audio_chunks.append(audio_chunk)

                    # 使用回调函数处理流式数据
                    if self._chunk_callback:
                        with profile_span("audio_pcm_encode", samples=int(np.asarray(audio_chunk).size)):
                            audio_data = self._preprocess_for_playback(audio_chunk)
                        self._mark_segment_completed(segment_index, segment_chars, len(audio_data))
                        self._chunk_callback(audio_data)
                    else:
                        pcm_bytes = len(self._preprocess_for_playback(audio_chunk))
                        self._mark_segment_completed(segment_index, segment_chars, pcm_bytes)

            except Exception as e:
                logger.error(f"A critical error occurred while processing the TTS task: {e}", exc_info=True)
                # 发生错误时，也要确保发送结束信号
                if self._chunk_callback:
                    self._chunk_callback(None)
                self._tts_done_event.set()
                self._finish_progress("failed", str(e))
                self._session_active = False

    def _playback_worker_loop(self):
        try:
            import sounddevice as sd
            with sd.OutputStream(samplerate=self.sample_rate,
                                 channels=self.channels,
                                 dtype='float32') as stream:
                while not self._stop_event.is_set():
                    try:
                        audio_chunk = self._audio_queue.get(timeout=1)
                        if audio_chunk is None:
                            break
                        if audio_chunk is AUDIO_STREAM_END:
                            self._playback_done_event.set()
                            continue
                        stream.write(audio_chunk.squeeze())
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(f"Error during audio playback: {e}", exc_info=True)

        except Exception as e:
            logger.warning(f"Failed to initialize sounddevice: {e}. Audio playback will be skipped.")
            # 如果音频设备初始化失败，即使不播放，也要消费队列中的结束信号，防止主线程死锁
            while not self._stop_event.is_set():
                try:
                    item = self._audio_queue.get(timeout=0.5)
                    if item is None:
                        break
                    if item is AUDIO_STREAM_END:
                        self._playback_done_event.set()
                except queue.Empty:
                    continue

    def _save_session_audio(self):
        try:
            with profile_span("wav_save", chunks=len(self._session_audio_chunks)):
                full_audio = np.concatenate(self._session_audio_chunks, axis=0)
                with wave.open(self._current_save_path, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.bytes_per_sample)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(self._preprocess_for_playback(full_audio))
                if self._current_save_path and os.path.exists(self._current_save_path):
                    self._set_progress_wav_bytes(os.path.getsize(self._current_save_path))
            logger.info(f"Audio successfully saved to {os.path.abspath(self._current_save_path)}")
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
        finally:
            self._session_audio_chunks = []
            self._current_save_path = None

    def start_session(
            self,
            play: bool = False,
            split: bool = False,
            save_path: Optional[str] = None,
            chunk_callback: Optional[Callable[[Optional[bytes]], None]] = None,
            reserved_session: bool = False,
    ):
        with self._api_lock:
            if self._session_active and not reserved_session:
                raise RuntimeError("A TTS session is already active.")

            self._tts_done_event.clear()
            self._playback_done_event.clear()  # 新增：重置播放完成事件
            self._chunk_callback = chunk_callback
            self._stop_event.clear()

            if self._tts_worker is None or not self._tts_worker.is_alive():
                self._tts_worker = threading.Thread(target=self._tts_worker_loop, daemon=True)
                self._tts_worker.start()

            if self._playback_worker is None or not self._playback_worker.is_alive():
                self._playback_worker = threading.Thread(target=self._playback_worker_loop, daemon=True)
                self._playback_worker.start()

            clear_queue(self._text_queue)
            clear_queue(self._audio_queue)

            self._play = play
            self._split = split
            self._current_save_path = save_path
            self._session_audio_chunks = []
            self._reset_progress(split, play, save_path)
            self._session_active = True

    def reserve_session(self) -> None:
        with self._api_lock:
            if self._session_active:
                raise RuntimeError("A TTS session is already active.")
            self._session_active = True

    def release_session(self) -> None:
        with self._api_lock:
            self._session_active = False

    def status_snapshot(self) -> dict:
        with self._api_lock:
            return {
                "session_active": self._session_active,
                "stop_requested": self._stop_event.is_set(),
                "tts_done": self._tts_done_event.is_set(),
                "playback_done": self._playback_done_event.is_set(),
                "tts_worker_alive": self._tts_worker is not None and self._tts_worker.is_alive(),
                "playback_worker_alive": self._playback_worker is not None and self._playback_worker.is_alive(),
                "text_queue_size": self._text_queue.qsize(),
                "audio_queue_size": self._audio_queue.qsize(),
                "split_sentence": self._split,
                "playback_enabled": self._play,
                "save_path_active": self._current_save_path is not None,
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "sample_width": self.bytes_per_sample,
                "progress": self.progress_snapshot(),
            }

    def feed(self, text_chunk: str):
        with self._api_lock:
            if not text_chunk:
                return
            if self._split:
                with profile_span("text_split", text_chars=len(text_chunk)):
                    stripped = text_chunk.strip()
                    sentences = self._text_splitter.split(stripped) or [stripped]
            else:
                sentences = [text_chunk]

            self._queue_progress(sentences, len(text_chunk.strip()))
            for sentence in sentences:
                self._next_segment_index += 1
                self._text_queue.put({
                    "text": sentence,
                    "segment_index": self._next_segment_index,
                    "segment_chars": len(sentence),
                })

    def end_session(self):
        with self._api_lock:
            self._text_queue.put(STREAM_END)

    def stop(self):
        with self._api_lock:
            if self._tts_worker is None and self._playback_worker is None:
                return
            if self._stop_event.is_set():
                return
            tts_client.stop_event.set()
            self._stop_event.set()
            self._tts_done_event.set()
            self._finish_progress("stopped", "TTS stop requested.")
            self._session_active = False
            self._text_queue.put(None)
            self._audio_queue.put(None)
            if self._tts_worker and self._tts_worker.is_alive():
                self._tts_worker.join()
            if self._playback_worker and self._playback_worker.is_alive():
                self._playback_worker.join()
            self._tts_worker = None
            self._playback_worker = None

    def wait_for_tts_completion(self):
        if self._tts_done_event.is_set():
            return
        self._tts_done_event.wait()

    def wait_for_playback_done(self):
        # 1. 首先等待TTS生成全部完成
        self.wait_for_tts_completion()

        # 2. 如果开启了播放且没有被强制停止，则等待播放结束
        if self._play and not self._stop_event.is_set():
            if not self._playback_done_event.is_set():
                self._playback_done_event.wait()


tts_player: TTSPlayer = TTSPlayer()
