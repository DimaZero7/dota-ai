"""Select one completed match and preserve the selection for later stages."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .clients import OpenDotaClient
from .exceptions import MatchSelectionError


def select_latest_match(
    *, account_id: int, client: OpenDotaClient
) -> dict[str, Any]:
    if type(account_id) is not int or not 0 < account_id < 2**32 - 1:
        raise MatchSelectionError("A valid Dota account_id is required.")

    history_path = f"/players/{account_id}/recentMatches"
    history = client.get(history_path)
    checked_at = datetime.now(timezone.utc)
    if not isinstance(history, list):
        raise MatchSelectionError("OpenDota returned an invalid match history.")

    completed = [
        row for row in history
        if isinstance(row, dict)
        and type(row.get("match_id")) is int
        and type(row.get("start_time")) is int
        and type(row.get("duration")) is int
        and row["duration"] > 0
        and type(row.get("radiant_win")) is bool
        and row["start_time"] + row["duration"] <= checked_at.timestamp()
    ]
    if not completed:
        raise MatchSelectionError("No completed matches found in the available history.")

    latest = max(completed, key=lambda row: (row["start_time"], row["match_id"]))
    match_path = f"/matches/{latest['match_id']}"
    match = client.get(match_path)
    if not isinstance(match, dict) or match.get("match_id") != latest["match_id"]:
        raise MatchSelectionError("Match details do not match the selected history entry.")
    for field in ("start_time", "duration", "radiant_win"):
        if match.get(field) != latest[field]:
            raise MatchSelectionError(f"History and match details disagree: {field}.")
    players = match.get("players")
    if not isinstance(players, list):
        raise MatchSelectionError("Match participants are unavailable.")
    participants = [
        p for p in players
        if isinstance(p, dict) and p.get("account_id") == account_id
    ]
    if len(participants) != 1:
        raise MatchSelectionError("The player's participation could not be verified.")
    player = participants[0]
    if (
        player.get("hero_id") != latest.get("hero_id")
        or player.get("player_slot") != latest.get("player_slot")
    ):
        raise MatchSelectionError("History and match details disagree on the player.")

    heroes = client.get("/constants/heroes")
    modes = client.get("/constants/game_mode")
    lobbies = client.get("/constants/lobby_type")
    patches = client.get("/constants/patch")
    if (
        not all(isinstance(value, dict) for value in (heroes, modes, lobbies))
        or not isinstance(patches, list)
    ):
        raise MatchSelectionError("OpenDota returned invalid reference data.")
    patch = next((p for p in patches if p.get("id") == match.get("patch")), {})
    slot = player.get("player_slot")
    is_radiant = slot < 128 if type(slot) is int else None

    return {
        "account_id": account_id,
        "match_id": latest["match_id"],
        "history_checked_at_utc": checked_at.isoformat(),
        "context_checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "OpenDota",
        "history_url": client.base_url + history_path,
        "match_url": client.base_url + match_path,
        "reference_urls": [
            client.base_url + "/constants/" + name
            for name in ("heroes", "game_mode", "lobby_type", "patch")
        ],
        "history_entries_returned": len(history),
        "selection_basis": "Latest completed match by start_time in the returned recent history.",
        "limitations": [
            "Only OpenDota recent history was checked; it is not the complete account history.",
            "Newer matches may be missing because of indexing delays or data visibility restrictions.",
            "The patch label is OpenDota's mapping; an exact letter subpatch is not established.",
        ],
        "participation_verified": True,
        "selected_history_entry": latest,
        "start_time_utc": datetime.fromtimestamp(
            match["start_time"], timezone.utc
        ).isoformat(),
        "duration_seconds": match["duration"],
        "hero_id": player.get("hero_id"),
        "hero_name": heroes.get(str(player.get("hero_id")), {}).get("localized_name"),
        "game_mode_id": match.get("game_mode"),
        "game_mode_name": modes.get(
            str(match.get("game_mode")), {}
        ).get("name"),
        "lobby_type_id": match.get("lobby_type"),
        "lobby_type_name": lobbies.get(
            str(match.get("lobby_type")), {}
        ).get("name"),
        "patch_id": match.get("patch"),
        "patch_name": patch.get("name"),
        "exact_subpatch": None,
        "player_slot": slot,
        "is_radiant": is_radiant,
        "player_won": (
            match["radiant_win"] == is_radiant
            if is_radiant is not None else None
        ),
    }


def get_or_select_match(
    *, account_id: int, client: OpenDotaClient, output_path: Path
) -> dict[str, Any]:
    if output_path.exists():
        try:
            selection = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise MatchSelectionError("Could not read the saved selection.") from exc
        if (
            not isinstance(selection, dict)
            or selection.get("account_id") != account_id
            or type(selection.get("match_id")) is not int
        ):
            raise MatchSelectionError("The saved selection is invalid or belongs to another player.")
        return selection

    selection = select_latest_match(account_id=account_id, client=client)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents a repeated or concurrent run from replacing the match.
    with output_path.open("x", encoding="utf-8") as output:
        json.dump(selection, output, ensure_ascii=False, indent=2)
        output.write("\n")
    return selection
