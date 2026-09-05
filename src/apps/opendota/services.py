"""Preserve one frozen match and describe its actual OpenDota coverage."""

import json
from datetime import datetime, timezone
from pathlib import Path

from .clients import OpenDotaClient
from .exceptions import OpenDotaError
from .inventory import build_inventory, render_report


def validate_match(*, match: dict, selection: dict) -> None:
    if not isinstance(match, dict) or match.get("match_id") != selection["match_id"]:
        raise OpenDotaError("Response does not match the frozen match_id.")
    players = match.get("players")
    if not isinstance(players, list) or len(players) != 10:
        raise OpenDotaError("Expected all 10 match participants.")
    if any(not isinstance(p, dict) or type(p.get("player_slot")) is not int for p in players):
        raise OpenDotaError("Invalid participant record.")
    if len({p["player_slot"] for p in players}) != 10:
        raise OpenDotaError("Duplicate player slots.")
    targets = [p for p in players if p.get("account_id") == selection["account_id"]]
    if len(targets) != 1 or any(
        targets[0].get(key) != selection[key] for key in ("hero_id", "player_slot")
    ):
        raise OpenDotaError("Target participant differs from the frozen selection.")
    history = selection["selected_history_entry"]
    for key in ("start_time", "duration", "radiant_win", "game_mode", "lobby_type"):
        if match.get(key) != history[key]:
            raise OpenDotaError(f"Match context differs from the frozen selection: {key}.")


def collect_match(*, selection_path: Path, account_id: int,
                  output_root: Path, client: OpenDotaClient) -> dict:
    try:
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise OpenDotaError(f"Cannot read the frozen selection: {exc}") from exc
    if (not isinstance(selection, dict) or type(account_id) is not int
            or account_id <= 0 or selection.get("account_id") != account_id
            or type(selection.get("match_id")) is not int or selection["match_id"] <= 0):
        raise OpenDotaError("Invalid frozen selection or a different configured account.")
    match_id = selection["match_id"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    output = output_root / str(match_id) / "opendota" / stamp
    output.mkdir(parents=True, exist_ok=False)
    metadata = {
        "source": "OpenDota", "match_id": match_id, "account_id": account_id,
        "match_url": f"{client.base_url}/matches/{match_id}",
        "status": "collecting", "parse_status": "unknown",
        "parse_requested": False, "requests": [],
    }

    def save_json(name: str, value: dict) -> None:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def fetch(path: str, filename: str) -> dict:
        body, request = client.fetch(path)
        (output / filename).write_bytes(body)
        metadata["requests"].append({**request, "file": filename})
        save_json("metadata.json", metadata)
        return json.loads(body)

    save_json("metadata.json", metadata)
    try:
        match = fetch(f"/matches/{match_id}", "match.json")
        metadata["match_retrieved_at_utc"] = metadata["requests"][-1]["retrieved_at_utc"]
        validate_match(match=match, selection=selection)
        parsed_flag = (match.get("od_data") or {}).get("has_parsed")
        parsed = parsed_flag is True and type(match.get("version")) is int and match["version"] > 0
        metadata["parse_status"] = "already_parsed" if parsed else "not_confirmed"
        metadata["parse_reason"] = (
            "OpenDota reports has_parsed=true and a positive parser version; no repeat parse is needed."
            if parsed else "Parsed data is not confirmed. No parse was requested automatically; investigate before requesting one."
        )
        schema = fetch("", "schema.json")
        inventory = build_inventory(match=match, schema=schema, account_id=account_id)
        save_json("inventory.json", inventory)
        metadata["status"] = "complete" if parsed else "needs_parse_review"
        save_json("metadata.json", metadata)
        for language in ("ru", "en"):
            (output / f"report.{language}.md").write_text(
                render_report(match=match, inventory=inventory, metadata=metadata, language=language), encoding="utf-8",
            )
    except (OpenDotaError, OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        metadata["status"] = "failed"
        metadata["error"] = str(exc)
        save_json("metadata.json", metadata)
        raise OpenDotaError(f"Collection failed; preserved evidence in {output}: {exc}") from exc
    return {"match_id": match_id, "status": metadata["status"],
            "parse_status": metadata["parse_status"], "output": str(output),
            "players": len(match["players"]), "match_fields": len(match)}
