"""Generate bounded match queries from the schema returned by STRATZ."""

INTROSPECTION = """query Schema {
  __schema { queryType { name } types { kind name fields(includeDeprecated:true) {
    name description args { name defaultValue type { kind name ofType { kind name ofType { kind name ofType { kind name } } } } }
    type { kind name ofType { kind name ofType { kind name ofType { kind name } } } }
  } } }
}"""

# These relationships leave match data for profile histories, reference data, or cycles.
EXCLUDED = {"match", "steamAccount", "hero", "abilityType", "league", "radiantTeam", "direTeam", "series", "heroAverage", "dotaPlus"}


def named_type(reference: dict) -> dict:
    while reference.get("ofType"):
        reference = reference["ofType"]
    return reference


def selection_set(type_name: str, types: dict, *, skipped: list,
                  path: str = "match", ancestors: tuple = (), exclude: set | None = None) -> str:
    fields = []
    for field in types[type_name]["fields"] or []:
        name = field["name"]
        child_path = f"{path}.{name}"
        reason = None
        kind = named_type(field["type"])
        if name in EXCLUDED or name in (exclude or set()):
            reason = "reference/profile/aggregate relationship or collected in a separate query"
        elif any(a["type"]["kind"] == "NON_NULL" and a["defaultValue"] is None for a in field["args"]):
            reason = "required arguments need a deliberate value"
        elif kind["kind"] not in ("SCALAR", "ENUM", "OBJECT"):
            reason = "unsupported composite type"
        elif kind["kind"] == "OBJECT" and (kind["name"] in ancestors or len(ancestors) >= 8):
            reason = "cycle or depth boundary"
        if reason:
            skipped.append({"path": child_path, "reason": reason})
            continue
        if kind["kind"] in ("SCALAR", "ENUM"):
            fields.append(name)
        else:
            child = selection_set(kind["name"], types, skipped=skipped, path=child_path,
                                  ancestors=(*ancestors, type_name))
            if child:
                fields.append(f"{name} {{ {child} }}")
    return " ".join(fields)


def build_queries(schema: dict) -> tuple[dict[str, str], list]:
    types = {t["name"]: t for t in schema["data"]["__schema"]["types"]}
    skipped = []
    root = selection_set("MatchType", types, skipped=skipped, exclude={"players"})
    player = selection_set("MatchPlayerType", types, skipped=skipped, path="match.players", exclude={"stats", "playbackData"})
    stats = selection_set("MatchPlayerStatsType", types, skipped=skipped, path="match.players.stats")
    playback = selection_set("MatchPlayerPlaybackDataType", types, skipped=skipped, path="match.players.playbackData")
    return {
        "overview": f"query MatchOverview($id: Long!) {{ match(id:$id) {{ {root} players {{ {player} }} }} }}",
        "stats": f"query MatchStats($id: Long!) {{ match(id:$id) {{ id players {{ steamAccountId playerSlot heroId stats {{ {stats} }} }} }} }}",
        "playback": f"query PlayerPlayback($id: Long!, $account: Long!) {{ match(id:$id) {{ id players(steamAccountId:$account) {{ steamAccountId playerSlot heroId playbackData {{ {playback} }} }} }} }}",
    }, skipped
