"""Collect the frozen match through bounded, separately preserved queries."""

import json
import hashlib
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from .clients import StratzClient
from .exceptions import StratzError
from .queries import INTROSPECTION, build_queries


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_overview(match: dict, selection: dict) -> None:
    if not isinstance(match, dict) or match.get("id") != selection["match_id"]:
        raise StratzError("STRATZ did not return the frozen match.")
    for field, expected in (("startDateTime", selection["selected_history_entry"]["start_time"]),
                            ("durationSeconds", selection["duration_seconds"]),
                            ("didRadiantWin", selection["selected_history_entry"]["radiant_win"])):
        if match.get(field) != expected:
            raise StratzError(f"Frozen match context mismatch: {field}.")
    players = match.get("players")
    if not isinstance(players, list) or len(players) != 10 or any(not isinstance(p, dict) for p in players):
        raise StratzError("Expected all 10 participants.")
    if len({p.get("playerSlot") for p in players}) != 10:
        raise StratzError("Participant slots are not unique.")
    target = [p for p in players if p.get("steamAccountId") == selection["account_id"]]
    if len(target) != 1 or target[0].get("heroId") != selection["hero_id"]:
        raise StratzError("Frozen target participant mismatch.")


def collect_match(*, selection_path: Path, account_id: int, output_root: Path,
                  client: StratzClient, pause: Callable[[float], None] = time.sleep,
                  reuse_verified_queries: bool = False) -> Path:
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    if type(account_id) is not int or selection.get("account_id") != account_id:
        raise StratzError("Configured account differs from the frozen selection.")
    match_id = selection.get("match_id")
    if type(match_id) is not int or match_id <= 0:
        raise StratzError("Invalid frozen match_id.")
    output = output_root / str(match_id) / "stratz" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    output.mkdir(parents=True, exist_ok=False)
    metadata = {"source": "STRATZ", "match_id": match_id, "account_id": account_id,
                "status": "collecting", "requests": [], "issues": []}

    def persist() -> None:
        save_json(output / "metadata.json", metadata)

    def fetch(name: str, query: str, variables: dict, *, schema: bool = False) -> dict:
        if metadata["requests"]:
            pause(1.1)  # Conservative pacing below the observed per-second/minute limits.
        folder = output / name
        folder.mkdir()
        (folder / "query.graphql").write_text(query + "\n", encoding="utf-8")
        save_json(folder / "variables.json", variables)
        filename = "schema.json" if schema else "match.json"
        cached=None
        if reuse_verified_queries:
            for old_meta in reversed(sorted(output.parent.glob('*/metadata.json'))):
                if old_meta.parent==output:continue
                old=json.loads(old_meta.read_text(encoding='utf-8'))
                if old.get('match_id')!=match_id or old.get('account_id')!=account_id:continue
                record=next((r for r in old.get('requests',[]) if r.get('file')==f'{name}/{filename}' and r.get('status')==200),None)
                old_folder=old_meta.parent/name
                if not record or not all((old_folder/f).exists() for f in ('query.graphql','variables.json',filename)):continue
                if (old_folder/'query.graphql').read_text(encoding='utf-8').strip()!=query.strip() or json.loads((old_folder/'variables.json').read_text(encoding='utf-8'))!=variables:continue
                old_body=(old_folder/filename).read_bytes()
                if len(old_body)!=record['bytes'] or hashlib.sha256(old_body).hexdigest()!=record['sha256']:continue
                if json.loads(old_body).get('errors'):continue
                cached=(old_body,{**record,'reused_from':str(old_meta.parent.relative_to(output_root))})
                break
        body, provenance = cached if cached is not None else client.query(query, variables)
        (folder / filename).write_bytes(body)
        metadata["requests"].append({**provenance, "file": f"{name}/{filename}"})
        persist()
        if provenance["status"] != 200:
            raise StratzError(f"HTTP {provenance['status']} in {name}; no automatic retry.")
        payload = json.loads(body)
        if payload.get("errors"):
            metadata["issues"].append({"query": name, "errors": payload["errors"]})
        persist()
        return payload

    persist()
    try:
        schema = fetch("schema", INTROSPECTION, {}, schema=True)
        queries, skipped = build_queries(schema)
        metadata["not_requested"] = [s for s in skipped if s["path"] not in (
            "match.players", "match.players.stats", "match.players.playbackData")]
        overview = fetch("overview", queries["overview"], {"id": match_id})
        match = (overview.get("data") or {}).get("match")
        validate_overview(match, selection)
        save_json(output / "match.json", match)
        participants = {p["playerSlot"]: p for p in match["players"]}

        def merge(payload: dict, section: str, expected_slots: set) -> None:
            fragment = (payload.get("data") or {}).get("match")
            if not fragment or fragment.get("id") != match_id:
                metadata["issues"].append({"section": section, "reason": "match absent or mismatched"})
                return
            seen = set()
            for player in fragment.get("players") or []:
                slot = player.get("playerSlot")
                if slot not in expected_slots or slot in seen:
                    raise StratzError("Unexpected or duplicate participant in response.")
                original = participants[slot]
                if any(player.get(k) != original.get(k) for k in ("steamAccountId", "heroId")):
                    raise StratzError("Participant identity differs between queries.")
                seen.add(slot)
                if section in player:
                    original[section] = player[section]
                else:
                    metadata["issues"].append({"section": section, "slot": slot, "reason": "requested field missing"})
            if seen != expected_slots:
                metadata["issues"].append({"section": section, "reason": "participants missing"})
            save_json(output / "match.json", match)

        merge(fetch("stats", queries["stats"], {"id": match_id}), "stats", set(participants))
        for slot, player in participants.items():
            account = player.get("steamAccountId")
            if type(account) is not int or account <= 0:
                metadata["issues"].append({"section": "playbackData", "slot": slot, "reason": "account unavailable for filtered query"})
                continue
            merge(fetch(f"playback-{slot}", queries["playback"], {"id": match_id, "account": account}), "playbackData", {slot})
        metadata["status"] = "partial" if metadata["issues"] else "complete"
        metadata["merged_file_note"] = "match.json at snapshot root combines responses by playerSlot; per-query files retain exact response bytes."
        persist()
    except (StratzError, OSError, ValueError, KeyError, TypeError) as exc:
        metadata["status"] = "failed"
        metadata["failure"] = str(exc)
        persist()
        raise StratzError(f"Collection failed; evidence: {output}. {exc}") from None
    return output
