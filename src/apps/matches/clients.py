"""Read-only access to OpenDota for match selection."""

import json
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from .exceptions import MatchSelectionError


class OpenDotaClient:
    base_url = "https://api.opendota.com/api"

    def __init__(self, *, timeout: float = 30) -> None:
        self.timeout = timeout

    def get(self, path: str) -> Any:
        request = Request(
            self.base_url + path,
            headers={"Accept": "application/json", "User-Agent": "DotaAI/0.1"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise MatchSelectionError(f"OpenDota request failed: {path}: {exc}") from exc
