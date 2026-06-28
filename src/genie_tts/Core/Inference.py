import onnxruntime as ort
import numpy as np
from typing import List, Optional
import threading
import logging
import os
import time

from ..Audio.ReferenceAudio import ReferenceAudio
from ..GetPhonesAndBert import get_phones_and_bert
from ..Profiling import profile_recorder, profile_span

MAX_T2S_LEN = 1000
logger = logging.getLogger(__name__)


class GENIE:
    def __init__(self):
        self.stop_event: threading.Event = threading.Event()
        seed = os.getenv("GENIE_TTS_SEED")
        self.seed: Optional[int] = int(seed) if seed else None

    def _set_seed_if_needed(self) -> None:
        if self.seed is not None:
            ort.set_seed(self.seed)

    def tts(
            self,
            text: str,
            prompt_audio: ReferenceAudio,
            encoder: ort.InferenceSession,
            first_stage_decoder: ort.InferenceSession,
            stage_decoder: ort.InferenceSession,
            vocoder: ort.InferenceSession,
            prompt_encoder: Optional[ort.InferenceSession],
            language: str = 'japanese',
    ) -> Optional[np.ndarray]:
        text = '。' + text  # 防止漏第一句。
        with profile_span("g2p", language=language, text_chars=len(text)):
            text_seq, text_bert = get_phones_and_bert(text, language=language)

        with profile_span("t2s_total", language=language, text_tokens=int(text_seq.shape[-1])):
            semantic_tokens: np.ndarray = self.t2s_cpu(
                ref_seq=prompt_audio.phonemes_seq,
                ref_bert=prompt_audio.text_bert,
                text_seq=text_seq,
                text_bert=text_bert,
                ssl_content=prompt_audio.ssl_content,
                encoder=encoder,
                first_stage_decoder=first_stage_decoder,
                stage_decoder=stage_decoder,
            )

        eos_indices = np.where(semantic_tokens >= 1024)  # 剔除不合法的元素，例如 EOS Token。
        if len(eos_indices[0]) > 0:
            first_eos_index = eos_indices[-1][0]
            semantic_tokens = semantic_tokens[..., :first_eos_index]

        if prompt_encoder is None:
            with profile_span(
                    "vits",
                    providers=vocoder.get_providers(),
                    semantic_tokens=int(semantic_tokens.shape[-1]),
            ):
                return vocoder.run(None, {
                    "text_seq": text_seq,
                    "pred_semantic": semantic_tokens,
                    "ref_audio": prompt_audio.audio_32k
                })[0]
        else:
            # V2ProPlus 新增。
            prompt_audio.update_global_emb(prompt_encoder=prompt_encoder)
            with profile_span(
                    "vits",
                    providers=vocoder.get_providers(),
                    semantic_tokens=int(semantic_tokens.shape[-1]),
            ):
                audio_chunk = vocoder.run(None, {
                    "text_seq": text_seq,
                    "pred_semantic": semantic_tokens,
                    "ge": prompt_audio.global_emb,
                    "ge_advanced": prompt_audio.global_emb_advanced,
                })[0]
            return audio_chunk

    def t2s_cpu(
            self,
            ref_seq: np.ndarray,
            ref_bert: np.ndarray,
            text_seq: np.ndarray,
            text_bert: np.ndarray,
            ssl_content: np.ndarray,
            encoder: ort.InferenceSession,
            first_stage_decoder: ort.InferenceSession,
            stage_decoder: ort.InferenceSession,
    ) -> Optional[np.ndarray]:
        """在CPU上运行T2S模型"""
        # Encoder
        with profile_span("t2s_encoder", providers=encoder.get_providers()):
            x, prompts = encoder.run(
                None,
                {
                    "ref_seq": ref_seq,
                    "text_seq": text_seq,
                    "ref_bert": ref_bert,
                    "text_bert": text_bert,
                    "ssl_content": ssl_content,
                },
            )

        # First Stage Decoder
        with profile_span("t2s_first_stage_decoder", providers=first_stage_decoder.get_providers()):
            y, y_emb, *present_key_values = first_stage_decoder.run(
                None, {"x": x, "prompts": prompts}
            )

        if "CUDAExecutionProvider" in stage_decoder.get_providers():
            try:
                return self._t2s_stage_decoder_cuda(
                    stage_decoder,
                    y,
                    y_emb,
                    present_key_values,
                )
            except Exception as e:
                logger.warning("CUDA stage decoder fast path failed; falling back to standard run: %s", e)

        semantic_tokens = self._t2s_stage_decoder_standard(
            stage_decoder,
            y,
            y_emb,
            present_key_values,
        )
        return semantic_tokens

    def _trim_semantic_tokens(self, y: np.ndarray, generated_steps: int) -> np.ndarray:
        semantic_tokens = y[:, -generated_steps:] if generated_steps else y[:, -1:]
        if semantic_tokens.shape[-1] > 0 and semantic_tokens[0, -1] >= 1024:
            semantic_tokens = semantic_tokens[:, :-1]
        return np.expand_dims(semantic_tokens, axis=0)

    def _t2s_stage_decoder_standard(
            self,
            stage_decoder: ort.InferenceSession,
            y: np.ndarray,
            y_emb: np.ndarray,
            present_key_values: List[np.ndarray],
    ) -> Optional[np.ndarray]:
        input_names: List[str] = [inp.name for inp in stage_decoder.get_inputs()]
        generated_steps: int = 0
        self._set_seed_if_needed()
        start = time.perf_counter()
        try:
            for _ in range(0, 500):
                if self.stop_event.is_set():
                    return None
                input_feed = {
                    name: data
                    for name, data in zip(input_names, [y, y_emb, *present_key_values])
                }
                outputs = stage_decoder.run(None, input_feed)
                y, y_emb, stop_condition_tensor, *present_key_values = outputs
                generated_steps += 1

                if bool(np.asarray(stop_condition_tensor).any()):
                    break
        finally:
            profile_recorder.record(
                "t2s_stage_decoder_standard",
                time.perf_counter() - start,
                {
                    "providers": stage_decoder.get_providers(),
                    "generated_steps": generated_steps,
                },
            )

        return self._trim_semantic_tokens(y, generated_steps)

    def _t2s_stage_decoder_cuda(
            self,
            stage_decoder: ort.InferenceSession,
            y: np.ndarray,
            y_emb: np.ndarray,
            present_key_values: List[np.ndarray],
    ) -> Optional[np.ndarray]:
        input_names: List[str] = [inp.name for inp in stage_decoder.get_inputs()]
        output_names: List[str] = [out.name for out in stage_decoder.get_outputs()]
        y_ort = ort.OrtValue.ortvalue_from_numpy(y, "cuda", 0)
        y_emb_ort = ort.OrtValue.ortvalue_from_numpy(y_emb, "cuda", 0)
        present_key_value_orts = [
            ort.OrtValue.ortvalue_from_numpy(value, "cuda", 0)
            for value in present_key_values
        ]

        generated_steps: int = 0
        self._set_seed_if_needed()
        start = time.perf_counter()
        try:
            for _ in range(0, 500):
                if self.stop_event.is_set():
                    return None

                io_binding = stage_decoder.io_binding()
                for name, value in zip(input_names, [y_ort, y_emb_ort, *present_key_value_orts]):
                    io_binding.bind_ortvalue_input(name, value)

                io_binding.bind_output(output_names[0], "cuda", 0)
                io_binding.bind_output(output_names[1], "cuda", 0)
                io_binding.bind_output(output_names[2], "cpu", 0)
                for name in output_names[3:]:
                    io_binding.bind_output(name, "cuda", 0)

                stage_decoder.run_with_iobinding(io_binding)
                y_ort, y_emb_ort, stop_condition_ort, *present_key_value_orts = io_binding.get_outputs()
                generated_steps += 1

                if bool(np.asarray(stop_condition_ort.numpy()).any()):
                    break
        finally:
            profile_recorder.record(
                "t2s_stage_decoder_cuda_iobinding",
                time.perf_counter() - start,
                {
                    "providers": stage_decoder.get_providers(),
                    "generated_steps": generated_steps,
                },
            )

        return self._trim_semantic_tokens(y_ort.numpy(), generated_steps)


tts_client: GENIE = GENIE()
