"""Observed coverage and explicit comparisons, without equating unlike events."""

import json
from collections import Counter, defaultdict
from pathlib import Path

from .exceptions import StratzError
from .queries import named_type
from .services import save_json


def state(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, (list, dict, str)) and not value:
        return "empty"
    if value is False:
        return "false"
    if type(value) in (int, float) and value == 0:
        return "zero"
    return "value"


def field_inventory(record: dict, type_name: str, types: dict, excluded: set,
                    path: str) -> dict:
    fields = {f["name"]: f for f in types[type_name]["fields"] or []}
    result = {}
    for name in sorted(fields.keys() | record.keys()):
        child_path = f"{path}.{name}"
        if name not in record:
            result[name] = {"state": "not_requested" if child_path in excluded else "missing"}
            continue
        value = record[name]
        item = {"state": state(value), "type": type(value).__name__}
        if isinstance(value, (dict, list)):
            item["count"] = len(value)
        if name in fields:
            ref = named_type(fields[name]["type"])
            if ref["kind"] == "OBJECT":
                if isinstance(value, dict):
                    item["fields"] = field_inventory(value, ref["name"], types, excluded, child_path)
                elif isinstance(value, list):
                    # Summarize child key coverage; raw responses preserve each event.
                    counts = defaultdict(Counter)
                    for entry in value:
                        if isinstance(entry, dict):
                            for key in {f["name"] for f in types[ref["name"]]["fields"] or []} | entry.keys():
                                counts[key][state(entry[key]) if key in entry else ("not_requested" if f"{child_path}.{key}" in excluded else "missing")] += 1
                    item["child_fields"] = dict(counts)
        result[name] = item
    return result


def write_reports(*, snapshot: Path, opendota_snapshot: Path | None) -> None:
    match = json.loads((snapshot / "match.json").read_bytes())
    metadata = json.loads((snapshot / "metadata.json").read_text(encoding="utf-8"))
    schema = json.loads((snapshot / "schema/schema.json").read_bytes())
    types = {t["name"]: t for t in schema["data"]["__schema"]["types"]}
    excluded = {p["path"] for p in metadata["not_requested"]}
    target = next(p for p in match["players"] if p["steamAccountId"] == metadata["account_id"])
    inventory = {
        "match_id": match["id"], "account_id": metadata["account_id"],
        "notes": ["not_requested is distinct from missing; null and empty do not establish a cause.",
                  "Array child_fields count observed entries; empty/null parents prevent observing their descendants.",
                  "Raw files preserve all nested data. Estimates and detected events are source interpretations."],
        "match_fields": field_inventory(match, "MatchType", types, excluded, "match"),
        "players": [{"steamAccountId": p["steamAccountId"], "playerSlot": p["playerSlot"],
                     "fields": field_inventory(p, "MatchPlayerType", types, excluded, "match.players")} for p in match["players"]],
        "not_requested": metadata["not_requested"],
    }
    # Full observed paths also include nested objects inside array elements.
    paths = defaultdict(Counter)
    def walk(value: object, path: str) -> None:
        paths[path][state(value)] += 1
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for child in value:
                walk(child, path + "[]")
    walk(match, "match")
    inventory["observed_nested_paths"] = dict(sorted(paths.items()))
    save_json(snapshot / "inventory.json", inventory)
    comparisons = []
    if opendota_snapshot is not None:
        od = json.loads((opendota_snapshot / "match.json").read_bytes())
        if od["match_id"] != match["id"]:
            raise StratzError("OpenDota comparison snapshot belongs to a different match.")
        op = next(p for p in od["players"] if p.get("account_id") == metadata["account_id"])
        for sk, ok in (("kills", "kills"), ("deaths", "deaths"), ("assists", "assists"),
                       ("numLastHits", "last_hits"), ("numDenies", "denies"), ("goldPerMinute", "gold_per_min"),
                       ("experiencePerMinute", "xp_per_min"), ("networth", "net_worth"), ("heroDamage", "hero_damage"),
                       ("towerDamage", "tower_damage"), ("heroHealing", "hero_healing")):
            comparisons.append({"stratz_field": sk, "opendota_field": ok, "stratz": target.get(sk),
                                "opendota": op.get(ok), "equal": sk in target and ok in op and target[sk] == op[ok]})
        save_json(snapshot / "comparison.json", {"match_id": match["id"], "target_final_stats": comparisons,
                  "opendota_snapshot": opendota_snapshot.as_posix().split("data/", 1)[-1]})
    for language in ("ru", "en"):
        ru = language == "ru"
        lines = [f"# STRATZ: {match['id']}", "",
                 f"Source: https://api.stratz.com/graphql · UTC: {metadata['requests'][0]['retrieved_at_utc']}", "",
                 "[Metadata](metadata.json) · [Inventory](inventory.json) · [Merged data](match.json)", "",
                 f"Status: **{metadata['status']}**. Requests: **{len(metadata['requests'])}**. Players: **{len(match['players'])}**.", "",
                 ("Для каждого запроса сохранены GraphQL, variables.json и исходный ответ; корневой match.json объединён по playerSlot. "
                  "Токен находится только в локальной конфигурации. Большие JSON исключены из Git."
                  if ru else "Each request retains GraphQL, variables.json, and the raw response; root match.json is merged by playerSlot. "
                  "The token is stored only in local configuration. Large JSON files are excluded from Git."), "",
                 "## " + ("Реальные лимиты" if ru else "Observed limits"), "",
                 "```json", json.dumps(metadata["requests"][0]["rate_limit_headers"], indent=2), "```", ""]
        for heading, record in (("Match", {k: v for k, v in match.items() if k != "players"}),
                                (f"Player {metadata['account_id']}", {k: v for k, v in target.items() if k not in ("stats", "playbackData")}),
                                ("Player stats", target.get("stats") or {}),
                                ("Player playback", target.get("playbackData") or {}),
                                ("Match playback", match.get("playbackData") or {})):
            lines += [f"## {heading}", "", "| Field | State | Value / Count |", "| --- | --- | --- |"]
            for key, value in record.items():
                shown = len(value) if isinstance(value, (list, dict)) else value
                lines.append(f"| `{key}` | {state(value)} | {shown} |")
            lines.append("")
        lines += ["## " + ("Сравнение с OpenDota" if ru else "OpenDota comparison"), "",
                  "| STRATZ field | OpenDota field | STRATZ | OpenDota | Equal |", "| --- | --- | --- | --- | --- |"]
        for row in comparisons:
            lines.append(f"| {row['stratz_field']} | {row['opendota_field']} | {row['stratz']} | {row['opendota']} | {row['equal']} |")
        if not comparisons:
            lines.append("Comparison unavailable: no complete local OpenDota snapshot.")
        lines += ["", "## " + ("Дополнения и ограничения" if ru else "Additions and limitations"), "",
                  ("STRATZ добавляет временные события позиций, здоровья, применения способностей и предметов, "
                   "получения золота/опыта, урона и лечения. Это позволяет разбирать последовательность действий подробнее, чем по агрегатам OpenDota. "
                   "Обнаруженные признаки смертей (например, isWardWalkThrough и isAttemptTpOut), оценки линий, роли и intentionalFeeding "
                   "являются интерпретациями STRATZ, а не доказательством намерений игрока. IMP и winRates в этом ответе отсутствуют (null)."
                   if ru else "STRATZ adds timestamped position, health, ability/item use, gold/experience, damage, and healing events. "
                   "These offer more sequence detail than OpenDota aggregates. Death flags (such as isWardWalkThrough and isAttemptTpOut), "
                   "lane outcomes, roles, and intentionalFeeding are STRATZ interpretations, not proof of player intent. IMP and winRates are null here."), "",
                  ("Числа событий разных сервисов напрямую не равнозначны: STRATZ chatEvents содержит типизированные игровые события, "
                   "а не только текст чата; itemPurchases может иметь иной состав, чем purchase_log. Длина рядов тоже отличается: "
                   "нельзя совмещать их по индексу без проверки времени и смысла показателя. Счётчик assists и список assistEvents "
                   "внутри STRATZ могут расходиться. Координаты и события playback не означают полного покадрового реплея. "
                   "Пустые roshanEvents/buildingEvents не доказывают отсутствия этих событий в игре."
                   if ru else "Event counts are not directly equivalent: STRATZ chatEvents includes typed game events, not just chat text; "
                   "itemPurchases may differ in scope from purchase_log. Series lengths differ and must not be aligned by index without "
                   "checking timing and meaning. The assists counter may differ from assistEvents within STRATZ. Playback coordinates/events "
                   "are not a complete tick-level replay. Empty roshanEvents/buildingEvents do not prove no such events occurred."), "",
                  ("Нули и false сохранены как значения; null, empty, missing и not_requested различаются в inventory.json. "
                   "Не запрашивались переходы к истории профилей, справочникам героев/способностей, объектам турниров/команд и средним показателям других матчей. "
                   "Список исключений сохранён ниже. Все остальные доступные поля выбранных веток запрошены по сохранённой схеме; "
                   "это не гарантия полноты данных сервиса."
                   if ru else "Zero and false are values; inventory.json distinguishes null, empty, missing, and not_requested. "
                   "Profile history, hero/ability references, league/team relationships, and other-match averages were not requested. "
                   "Exclusions are listed below. Remaining available fields of the selected branches were requested from the saved schema; "
                   "this does not guarantee service data completeness."), ""]
        for entry in metadata["not_requested"]:
            lines.append(f"- `{entry['path']}`: {entry['reason']}.")
        (snapshot / f"report.{language}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
