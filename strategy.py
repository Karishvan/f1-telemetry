from typing import Dict, List

PIT_LOSS_MS = 22_000

COMPOUND_MAX_LAPS = {
    "SOFT": 30,
    "MEDIUM": 42,
    "HARD": 55,
    "INTERMEDIATE": 35,
    "WET": 45,
}
MIN_STINT_LAPS = 5


def _stint_cost_ms(base_pace_ms: float, deg_ms_per_lap: float, n_laps: int) -> float:
    deg = max(0.0, deg_ms_per_lap)
    return n_laps * base_pace_ms + deg * n_laps * (n_laps - 1) / 2


def optimize_strategy(
    compounds_data: Dict[str, Dict],
    total_laps: int,
    pit_loss_ms: int = PIT_LOSS_MS,
    max_stops: int = 3,
) -> List[Dict]:
    """
    DP pit stop strategy optimizer.

    compounds_data: {compound: {base_pace_ms: float, deg_ms_per_lap: float}}
    Returns up to 5 unique strategies sorted by estimated total time (ascending).

    Uses F1 rules: minimum 2 different compounds, minimum MIN_STINT_LAPS per stint.
    Pit loss of pit_loss_ms ms is charged on every stint after the first.
    """
    # dp[(lap, frozenset_of_used_compounds)] = (total_time_ms, stints_list)
    dp: Dict = {(0, frozenset()): (0.0, [])}

    for lap in range(total_laps):
        relevant = [(k, v) for k, v in dp.items() if k[0] == lap]
        for (_, used_compounds), (cur_time, stints) in relevant:
            if len(stints) > max_stops:
                continue
            is_first = len(stints) == 0

            for compound, cdata in compounds_data.items():
                max_n = min(COMPOUND_MAX_LAPS.get(compound, 42), total_laps - lap)
                for n in range(MIN_STINT_LAPS, max_n + 1):
                    new_lap = lap + n
                    pit = 0 if is_first else pit_loss_ms
                    cost = pit + _stint_cost_ms(cdata["base_pace_ms"], cdata["deg_ms_per_lap"], n)
                    new_time = cur_time + cost
                    new_used = used_compounds | frozenset([compound])
                    new_key = (new_lap, new_used)
                    new_stints = stints + [
                        {"compound": compound, "start_lap": lap + 1, "end_lap": new_lap, "laps": n}
                    ]
                    if new_key not in dp or dp[new_key][0] > new_time:
                        dp[new_key] = (new_time, new_stints)

    results = []
    for (final_lap, used_compounds), (total_time_ms, stints) in dp.items():
        if final_lap == total_laps and len(used_compounds) >= 2:
            results.append({
                "estimated_time_s": round(total_time_ms / 1000, 1),
                "num_pit_stops": len(stints) - 1,
                "pit_stop_laps": [s["end_lap"] for s in stints[:-1]],
                "stints": [{**s, "stint": i + 1} for i, s in enumerate(stints)],
            })

    results.sort(key=lambda x: x["estimated_time_s"])

    # Deduplicate by compound sequence + stint lengths
    seen: set = set()
    unique: List[Dict] = []
    for r in results:
        key = tuple((s["compound"], s["laps"]) for s in r["stints"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
        if len(unique) >= 5:
            break

    return unique
