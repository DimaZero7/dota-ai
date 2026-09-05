"""Free OpenDota requests with response provenance and no API key."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from .exceptions import OpenDotaError


class OpenDotaClient:
    base_url = "https://api.opendota.com/api"

    def __init__(self, *, timeout: float = 30) -> None:
        self.timeout = timeout

    def fetch(self, path: str, *, method: str = "GET") -> tuple[bytes, dict]:
        request = Request(
            self.base_url + path,
            method=method,
            data=b"" if method == "POST" else None,
            headers={"Accept": "application/json", "User-Agent": "DotaAI/0.1"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read()
                json.loads(body)
                metadata = {
                    "url": request.full_url,
                    "method": method,
                    "status": response.status,
                    "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "rate_limit_headers": {
                        key: value for key, value in response.headers.items()
                        if key.lower().startswith("x-rate-limit-")
                    },
                }
                return body, metadata
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise OpenDotaError(f"OpenDota {method} {path} failed: {exc}") from exc

    def get(self, path: str) -> Any:
        body, _ = self.fetch(path)
        return json.loads(body)
