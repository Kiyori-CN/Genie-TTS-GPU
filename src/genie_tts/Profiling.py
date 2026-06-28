import contextlib
import os
import statistics
import threading
import time
from typing import Dict, Iterator, List, Optional


def _env_enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


class ProfileRecorder:
    def __init__(self, enabled: bool = False, max_events: int = 2000):
        self.enabled = enabled
        self.max_events = max_events
        self._events: List[dict] = []
        self._lock = threading.Lock()

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def record(self, name: str, elapsed_seconds: float, metadata: Optional[Dict[str, object]] = None) -> None:
        if not self.enabled:
            return
        event = {
            "name": name,
            "elapsed_seconds": float(elapsed_seconds),
            "timestamp": time.time(),
            "thread": threading.current_thread().name,
            "metadata": dict(metadata or {}),
        }
        with self._lock:
            self._events.append(event)
            overflow = len(self._events) - self.max_events
            if overflow > 0:
                del self._events[:overflow]

    @contextlib.contextmanager
    def span(self, name: str, metadata: Optional[Dict[str, object]] = None) -> Iterator[None]:
        if not self.enabled:
            yield
            return
        start = time.perf_counter()
        try:
            yield
        finally:
            self.record(name, time.perf_counter() - start, metadata)

    def snapshot(self, include_events: bool = True) -> dict:
        with self._lock:
            events = [dict(event) for event in self._events]
        result = {
            "enabled": self.enabled,
            "event_count": len(events),
            "summary": self.summary(events),
        }
        if include_events:
            result["events"] = events
        return result

    @staticmethod
    def summary(events: List[dict]) -> Dict[str, dict]:
        grouped: Dict[str, List[float]] = {}
        for event in events:
            grouped.setdefault(event["name"], []).append(float(event["elapsed_seconds"]))

        summary: Dict[str, dict] = {}
        for name, values in grouped.items():
            sorted_values = sorted(values)
            count = len(sorted_values)
            p90_index = min(count - 1, int(count * 0.9))
            summary[name] = {
                "count": count,
                "total_seconds": sum(sorted_values),
                "avg_seconds": statistics.fmean(sorted_values),
                "min_seconds": sorted_values[0],
                "p50_seconds": statistics.median(sorted_values),
                "p90_seconds": sorted_values[p90_index],
                "max_seconds": sorted_values[-1],
            }
        return summary


profile_recorder = ProfileRecorder(enabled=_env_enabled("GENIE_PROFILE"))


def profile_span(name: str, metadata: Optional[Dict[str, object]] = None, **metadata_kwargs: object):
    span_metadata = dict(metadata or {})
    if metadata_kwargs:
        span_metadata.update(metadata_kwargs)
    return profile_recorder.span(name, span_metadata)
