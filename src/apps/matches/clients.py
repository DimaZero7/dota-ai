"""Compatibility adapter for the match selection service."""

from typing import Any

from src.apps.opendota.clients import OpenDotaClient as BaseOpenDotaClient
from src.apps.opendota.exceptions import OpenDotaError

from .exceptions import MatchSelectionError


class OpenDotaClient(BaseOpenDotaClient):
    def get(self, path: str) -> Any:
        try:
            return super().get(path)
        except OpenDotaError as exc:
            raise MatchSelectionError(str(exc)) from exc
