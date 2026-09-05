"""Describe observed fields without treating zero or False as missing data."""

from collections import Counter, defaultdict
from typing import Any


def value_state(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, (list, dict, str)) and len(value) == 0:
        return "empty"
    if value is False:
        return "false"
    if type(value) in (int, float) and value == 0:
        return "zero"
    return "value"


def describe_fields(record: dict, expected: set[str]) -> dict:
    result = {}
    for field in sorted(expected | record.keys()):
        if field not in record:
            result[field] = {"state": "missing", "documented": field in expected}
            continue
        value = record[field]
        description = {
            "state": value_state(value),
            "type": type(value).__name__,
            "documented": field in expected,
        }
        if isinstance(value, (list, dict)):
            description["count"] = len(value)
        result[field] = description
    return result


def build_inventory(*, match: dict, schema: dict, account_id: int) -> dict:
    properties = schema["components"]["schemas"]["MatchResponse"]["properties"]
    player_properties = properties["players"]["items"]["properties"]
    players = match["players"]
    # Union of documented fields and fields observed in any participant.
    player_fields = set(player_properties)
    observed_player_fields = set().union(*(p.keys() for p in players))
    all_player_fields = player_fields | observed_player_fields
    paths = defaultdict(Counter)

    def walk(value: Any, path: str) -> None:
        paths[path][value_state(value)] += 1
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for child in value:
                walk(child, f"{path}[]")

    walk(match, "$")
    return {
        "match_id": match["match_id"],
        "account_id": account_id,
        "schema_version": schema.get("info", {}).get("version"),
        "notes": [
            "missing means absent from this response, not necessarily an API defect.",
            "Expected fields come from the saved API schema and observed player union.",
            "null and empty are distinct; neither establishes why data is unavailable.",
            "zero and false are real values. Empty event lists can mean no such events.",
            "Nested paths aggregate observed array elements; raw JSON preserves values and indices.",
        ],
        "match_fields": describe_fields(match, set(properties)),
        "players": [
            {
                "account_id": p.get("account_id"),
                "player_slot": p["player_slot"],
                "hero_id": p.get("hero_id"),
                "is_target": p.get("account_id") == account_id,
                "fields": {
                    name: {**description, "documented": name in player_fields}
                    for name, description in describe_fields(p, all_player_fields).items()
                },
            }
            for p in players
        ],
        "observed_nested_paths": dict(sorted(paths.items())),
    }


def render_report(*, match: dict, inventory: dict, metadata: dict, language: str) -> str:
    ru = language == "ru"
    title = "Данные OpenDota" if ru else "OpenDota data"
    target = next(p for p in match["players"] if p.get("account_id") == inventory["account_id"])
    target_fields = next(p["fields"] for p in inventory["players"] if p["is_target"])
    lines = [
        f"# {title}: {match['match_id']}", "",
        f"Source: {metadata['match_url']}",
        f"Retrieved UTC: {metadata['match_retrieved_at_utc']}", "",
        "[Raw JSON](match.json) · [Provenance](metadata.json) · [Field inventory](inventory.json)", "",
        f"Players: **{len(match['players'])}**. Parser version: **{match.get('version')}**.",
        f"Parse status: `{metadata['parse_status']}`. `od_data`: `{match.get('od_data')}`.", "",
        ("Исходный ответ сохранён целиком. Отчёт описывает наличие данных, а не качество игры."
         if ru else "The complete response is preserved. This report describes data availability, not gameplay quality."), "",
        "## " + ("События матча" if ru else "Match events"), "",
        "| Field | State | Count |", "| --- | --- | --- |",
    ]
    for field in ("objectives", "teamfights", "chat", "pauses", "picks_bans", "draft_timings", "radiant_gold_adv", "radiant_xp_adv"):
        info = inventory["match_fields"][field]
        lines.append(f"| `{field}` | {info['state']} | {info.get('count', '—')} |")
    lines += ["", "## " + ("Все участники" if ru else "All participants"), "",
              "| Slot | Account | Hero ID | K/D/A | GPM | XPM | LH |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for player in match["players"]:
        kda = "/".join(str(player.get(k)) for k in ("kills", "deaths", "assists"))
        lines.append(f"| {player['player_slot']} | {player.get('account_id')} | {player.get('hero_id')} | {kda} | {player.get('gold_per_min')} | {player.get('xp_per_min')} | {player.get('last_hits')} |")
    lines += ["", f"## " + ("Твой игрок" if ru else "Target player") + f": {inventory['account_id']}", "",
              "| Field | State | Value / Count |", "| --- | --- | --- |"]
    fields = (
        "kills", "deaths", "assists", "net_worth", "gold_per_min", "xp_per_min",
        "last_hits", "denies", "hero_damage", "tower_damage", "hero_healing",
        "times", "gold_t", "xp_t", "lh_t", "dn_t", "purchase_log",
        "ability_upgrades_arr", "ability_uses", "ability_targets", "item_uses",
        "damage_inflictor", "damage_targets", "kills_log", "buyback_log",
        "runes_log", "obs_log", "sen_log", "obs_left_log", "sen_left_log",
        "camps_stacked", "lane_pos", "actions", "pings", "connection_log",
        "neutral_tokens_log", "neutral_item_history", "benchmarks",
    )
    for field in fields:
        info = target_fields.get(field, {"state": "missing"})
        displayed = info.get("count", target.get(field, "—"))
        lines.append(f"| `{field}` | {info['state']} | {displayed} |")
    lines += ["", "## " + ("Пропуски и ограничения" if ru else "Gaps and limitations"), ""]
    for label, descriptions in (("Match", inventory["match_fields"]), ("Target player", target_fields)):
        for state in ("missing", "null", "empty"):
            names = [f"`{key}`" for key, value in descriptions.items() if value["state"] == state]
            lines.append(f"- {label}, **{state}**: " + (", ".join(names) or "—") + ".")
    lines += ["", (
        "`missing` — ключа нет; `null` — явное отсутствие значения; `empty` — пустая структура или строка; "
        "`zero` и `false` — реальные значения. Отсутствие необязательного поля схемы не означает ошибку; "
        "пустой список событий может означать, что событий не было. Причина пропусков API не установлена. "
        "Подробная проверка наличия полей для каждого из 10 игроков и вложенных путей находится в inventory.json. "
        "Готовые оценки OpenDota (например, benchmarks и lane_efficiency) не являются исходными событиями. "
        "Поминутные ряды не заменяют покадровый реплей. Наличие replay_url не подтверждает доступность файла."
        if ru else
        "missing means no key; null is an explicit null; empty is an empty collection or string; "
        "zero and false are real values. Optional schema fields need not appear, and empty event lists may mean no events occurred. "
        "The cause of gaps is not established. inventory.json describes every participant and observed nested paths. "
        "OpenDota estimates such as benchmarks and lane_efficiency are not raw events. "
        "Minute-level series do not replace a tick-level replay. A replay_url does not establish file availability."
    ), ""]
    return "\n".join(lines)
