"""Run: python -m src.apps.stratz.cli."""

import json
import sys

from src.settings import BASE_DIR, config_toml

from .clients import StratzClient
from .exceptions import StratzError
from .services import collect_match
from .reports import write_reports


def main() -> int:
    try:
        output = collect_match(
            selection_path=BASE_DIR.parent / "data/selected_match.json",
            account_id=config_toml.get("player", {}).get("account_id"),
            output_root=BASE_DIR.parent / "data/matches",
            client=StratzClient(token=config_toml.get("stratz", {}).get("token")),
        )
        metadata = json.loads((output / "metadata.json").read_text(encoding="utf-8"))
        baselines = []
        for candidate in sorted((output.parent.parent / "opendota").glob("*/metadata.json")):
            baseline = json.loads(candidate.read_text(encoding="utf-8"))
            if baseline.get("status") == "complete" and (candidate.parent / "match.json").exists():
                baselines.append(candidate.parent)
        write_reports(snapshot=output, opendota_snapshot=baselines[-1] if baselines else None)
        print(json.dumps({"output": str(output), "status": metadata["status"], "requests": len(metadata["requests"])}, ensure_ascii=False))
        return 0 if metadata["status"] == "complete" else 2
    except (StratzError, OSError, ValueError) as exc:
        print(f"STRATZ collection failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
