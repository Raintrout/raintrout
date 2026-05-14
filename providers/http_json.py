from __future__ import annotations

import json
import urllib.request
from typing import Any

from .base import DEFAULT_TTL_HOURS, CachedProvider


class HttpJsonProvider(CachedProvider):
    def __init__(
        self,
        name: str,
        url: str,
        token: str | None = None,
        ttl_hours: float = DEFAULT_TTL_HOURS,
        timeout_seconds: float = 10.0,
    ) -> None:
        super().__init__(name=name, ttl_hours=ttl_hours)
        self.url = url
        self.token = token
        self.timeout_seconds = timeout_seconds

    def _live_fetch(self) -> dict[str, Any]:
        req = urllib.request.Request(self.url, headers={
            "Accept": "application/json",
            "User-Agent": "raintrout/1.0",
        })
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
            raw = response.read()
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise TypeError(
                f"endpoint did not return a JSON object: got {type(data).__name__}"
            )
        return data
