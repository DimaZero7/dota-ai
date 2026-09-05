"""Authenticated read-only GraphQL requests, without logging credentials."""

import hashlib
import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .exceptions import StratzError


class StratzClient:
    url = "https://api.stratz.com/graphql"

    def __init__(self, *, token: str, timeout: float = 45) -> None:
        if not isinstance(token, str) or not token.strip():
            raise StratzError("Set [stratz].token in local src/config.toml.")
        self._token = token.strip()
        self.timeout = timeout

    def query(self, query: str, variables: dict) -> tuple[bytes, dict]:
        if not query.lstrip().startswith(("query", "{")):
            raise StratzError("Only read-only GraphQL queries are supported.")
        request = Request(self.url, data=json.dumps({"query": query, "variables": variables}).encode(),
                          headers={"Authorization": f"Bearer {self._token}",
                                   "Content-Type": "application/json", "User-Agent": "STRATZ_API"})
        try:
            response = urlopen(request, timeout=self.timeout)
        except HTTPError as exc:
            response = exc  # Preserve the error response as evidence, including rate limits.
        except (URLError, OSError) as exc:
            raise StratzError("STRATZ network request failed; credentials were not logged.") from None
        with response:
            body = response.read()
            # Never persist a credential if a server unexpectedly echoes it.
            if self._token.encode() in body:
                raise StratzError("Response contained the credential; response was not saved.")
            return body, {
                "url": self.url, "method": "POST", "status": response.status,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                "rate_limit_headers": {k: v for k, v in response.headers.items() if "ratelimit" in k.lower()},
            }
