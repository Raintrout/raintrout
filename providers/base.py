from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
DEFAULT_TTL_HOURS = 24.0


class Provider(Protocol):
    name: str

    def fetch(self) -> dict[str, Any] | None: ...


class CachedProvider:
    """Wraps a live fetch with disk caching, TTL, and stale-fallback semantics.

    On fetch():
      1. If cache exists and age < ttl_hours, return cached data.
      2. Otherwise call _live_fetch(); on success write cache and return.
      3. On live failure, return stale cache if present (with a warning).
      4. Otherwise return None.
    """

    def __init__(self, name: str, ttl_hours: float = DEFAULT_TTL_HOURS) -> None:
        self.name = name
        self.ttl_hours = ttl_hours
        self._memo: dict[str, Any] | None = None
        self._memoized = False

    def _cache_path(self) -> Path:
        return CACHE_DIR / f"{self.name}.json"

    def _read_cache(self) -> tuple[dict[str, Any], datetime] | None:
        path = self._cache_path()
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            data = payload["data"]
            ts = datetime.fromisoformat(payload["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            print(f"[{self.name}] failed to read cache: {exc}", file=sys.stderr)
            return None
        if not isinstance(data, dict):
            print(f"[{self.name}] cache payload data is not an object", file=sys.stderr)
            return None
        return data, ts

    def _write_cache(self, data: dict[str, Any]) -> None:
        path = self._cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)

    def _live_fetch(self) -> dict[str, Any]:
        raise NotImplementedError

    def has_cache(self) -> bool:
        return self._cache_path().exists()

    def fetch(self) -> dict[str, Any] | None:
        if self._memoized:
            return self._memo

        cache = self._read_cache()
        now = datetime.now(timezone.utc)

        if cache is not None:
            data, ts = cache
            age_hours = (now - ts).total_seconds() / 3600.0
            if age_hours < self.ttl_hours:
                self._memo, self._memoized = data, True
                return data

        try:
            data = self._live_fetch()
        except Exception as exc:
            print(f"[{self.name}] live fetch failed: {exc}", file=sys.stderr)
            if cache is not None:
                stale_data, ts = cache
                age_hours = (now - ts).total_seconds() / 3600.0
                print(
                    f"[{self.name}] using stale cache (age {age_hours:.1f}h)",
                    file=sys.stderr,
                )
                self._memo, self._memoized = stale_data, True
                return stale_data
            self._memo, self._memoized = None, True
            return None

        self._write_cache(data)
        self._memo, self._memoized = data, True
        return data


class CacheOnlyProvider(CachedProvider):
    """Returns cached data only; never attempts a live fetch. Used as a fallback
    when no live source is configured but a previously committed cache exists."""

    def fetch(self) -> dict[str, Any] | None:
        if self._memoized:
            return self._memo
        cache = self._read_cache()
        if cache is None:
            self._memo, self._memoized = None, True
            return None
        data, _ts = cache
        self._memo, self._memoized = data, True
        return data
