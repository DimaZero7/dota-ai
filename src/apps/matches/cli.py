"""Run from the repository root: python -m src.apps.matches.cli."""

import json
import sys

from src.settings import BASE_DIR, config_toml

from .clients import OpenDotaClient
from .exceptions import MatchSelectionError
from .services import get_or_select_match


def main() -> int:
    try:
        account_id = config_toml.get("player", {}).get("account_id")
        selection = get_or_select_match(
            account_id=account_id,
            client=OpenDotaClient(),
            output_path=BASE_DIR.parent / "data" / "selected_match.json",
        )
    except (MatchSelectionError, OSError) as exc:
        print(f"Match selection failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(selection, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
