from __future__ import annotations

import os
import sys

from .base import CACHE_DIR, DEFAULT_TTL_HOURS, CacheOnlyProvider, Provider
from .http_json import HttpJsonProvider

_registry: dict[str, Provider] = {}
_initialized = False
_warned_fields: set[tuple[str, str]] = set()


def _ttl_hours_for(env_prefix: str) -> float:
    raw = os.environ.get(f"{env_prefix}_CACHE_TTL_HOURS")
    if raw is None or raw == "":
        return DEFAULT_TTL_HOURS
    try:
        return float(raw)
    except ValueError:
        print(
            f"invalid {env_prefix}_CACHE_TTL_HOURS={raw!r}; using default",
            file=sys.stderr,
        )
        return DEFAULT_TTL_HOURS


def init() -> None:
    """Register providers based on environment configuration. Idempotent."""
    global _initialized
    _registry.clear()

    stats_url = os.environ.get("STATS_URL")
    print(stats_url)
    if stats_url:
        _registry["stats"] = HttpJsonProvider(
            name="stats",
            url=stats_url,
            token=os.environ.get("STATS_TOKEN") or None,
            ttl_hours=_ttl_hours_for("STATS"),
        )
    elif (CACHE_DIR / "stats.json").exists():
        # No live source configured, but a previously-committed cache exists.
        # Fall back to it so the README renders with last-good values rather
        # than visible templates.
        _registry["stats"] = CacheOnlyProvider(name="stats")

    _initialized = True


def resolve(provider_name: str, field: str) -> str | None:
    """Return the resolved string value, or None if unavailable."""
    if not _initialized:
        init()
    provider = _registry.get(provider_name)
    if provider is None:
        return None
    data = provider.fetch()
    if data is None:
        return None
    if field not in data:
        key = (provider_name, field)
        if key not in _warned_fields:
            print(
                f"[{provider_name}] field {field!r} not in response "
                f"(available: {sorted(data)})",
                file=sys.stderr,
            )
            _warned_fields.add(key)
        return None
    return str(data[field])
