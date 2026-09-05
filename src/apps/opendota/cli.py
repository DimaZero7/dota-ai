"""Run from the repository root: python -m src.apps.opendota.cli."""

import json
import sys

from src.settings import BASE_DIR, config_toml

from .clients import OpenDotaClient
from .exceptions import OpenDotaError
from .services import collect_match


def main() -> int:
    try:
        result = collect_match(
            selection_path=BASE_DIR.parent / "data" / "selected_match.json",
            account_id=config_toml.get("player", {}).get("account_id"),
            output_root=BASE_DIR.parent / "data" / "matches",
            client=OpenDotaClient(),
        )
    except (OpenDotaError, OSError) as exc:
        print(f"OpenDota collection failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
