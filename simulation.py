from __future__ import annotations

import math
from typing import Any

import numpy as np
import simpy

from statistics import (
    RESOURCE_KEYS,
    RESOURCE_LABELS,
    build_interpretation,
    create_metric_buckets,
    finalize_results,
)


def _normalize_probabilities(probabilities: dict[str, float]) -> list[float]:
    values = [max(float(probabilities.get(key, 0.0)), 0.0) for key in RESOURCE_KEYS]
    total = sum(values)
    if total <= 0:
        return [1 / len(RESOURCE_KEYS)] * len(RESOURCE_KEYS)
    return [value / total for value in values]


def _positive_float(config: dict[str, Any], key: str, default: float) -> float:
    try:
        return max(float(config.get(key, default)), 0.0)
    except (TypeError, ValueError):
        return default


def _resource_request(resource: simpy.Resource, priority: int | None = None) -> simpy.events.Event:
    if isinstance(resource, simpy.PriorityResource):
        return resource.request(priority=priority or 1)
    return resource.request()


def _clean_number(value: Any, digits: int = 2) -> float:
    number = float(value)
    if not math.isfinite(number):
        return 0.0
    return round(number, digits)


def _mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def _std(values: list[float]) -> float:
    return float(np.std(values, ddof=1)) if len(values) > 1 else 0.0


def _stat_block(values: list[float]) -> dict[str, Any]:
    mean = _mean(values)
    std = _std(values)
    if len(values) > 1:
        half_width = 1.96 * std / math.sqrt(len(values))
    else:
        half_width = 0.0
    return {
        "mean": _clean_number(mean),
        "standard_deviation": _clean_number(std),
        "confidence_interval_95": {
            "lower": _clean_number(mean - half_width),
            "upper": _clean_number(mean + half_width),
        },
    }


def _spawn_day_seeds(base_seed: int | None, replications: int, exam_days: int) -> list[list[int]]:
    seed_sequence = np.random.SeedSequence(base_seed)
    children = seed_sequence.spawn(replications * exam_days)
    seeds = [int(child.generate_state(1, dtype=np.uint32)[0]) for child in children]
    return [
        seeds[replication * exam_days : (replication + 1) * exam_days]
        for replication in range(replications)
    ]


def run_single_day(config: dict[str, Any], seed: int | None = None) -> dict[str, Any]:
    """Run one independent simulated opening day and return JSON-serializable metrics."""
    simulation_minutes = _positive_float(
        config,
        "opening_minutes_per_day",
        _positive_float(config, "simulation_minutes", 480),
    )
    sample_interval = max(_positive_float(config, "sample_interval", 10), 1)
    arrivals_per_hour = _positive_float(config, "arrivals_per_hour", 32)
    mean_stay_minutes = max(_positive_float(config, "mean_stay_minutes", 125), 0.1)
    max_wait_minutes = _positive_float(config, "max_wait_minutes", 25)

    capacities = {
        key: max(int(config.get("resources", {}).get(key, 0)), 0) for key in RESOURCE_KEYS
    }
    probabilities = _normalize_probabilities(config.get("demand_probabilities", {}))
    rng = np.random.default_rng(config.get("seed") if seed is None else seed)
    env = simpy.Environment()

    reservation_enabled = bool(config.get("reservation_enabled", False))
    reservation_share = min(max(float(config.get("reservation_share", 0.0)), 0.0), 1.0)

    resources: dict[str, simpy.Resource | None] = {}
    for key, capacity in capacities.items():
        if capacity <= 0:
            resources[key] = None
        elif key == "group_rooms" and reservation_enabled:
            resources[key] = simpy.PriorityResource(env, capacity=capacity)
        else:
            resources[key] = simpy.Resource(env, capacity=capacity)

    metrics = create_metric_buckets()
    timeline: list[dict[str, float | int]] = []

    def make_timeline_row(time_value: float | None = None) -> dict[str, float | int]:
        row: dict[str, float | int] = {
            "time": round(float(env.now if time_value is None else time_value), 2)
        }
        for resource_key in RESOURCE_KEYS:
            resource = resources[resource_key]
            occupied = int(resource.count) if resource is not None else 0
            queue_length = len(resource.queue) if resource is not None else 0
            metrics[resource_key]["max_queue_length"] = max(
                metrics[resource_key]["max_queue_length"], queue_length
            )
            row[f"{resource_key}_occupied"] = occupied
            row[f"{resource_key}_queue"] = queue_length
        return row

    def choose_resource_type() -> str:
        return str(rng.choice(RESOURCE_KEYS, p=probabilities))

    def sample_stay_duration(resource_key: str) -> float:
        resource_multiplier = {
            "study_seats": 1.0,
            "pc_workstations": 0.9,
            "group_rooms": 1.15,
        }[resource_key]
        mean = max(mean_stay_minutes * resource_multiplier, 0.1)
        low = max(0.1, mean * 0.35)
        high = max(low + 1.0, mean * 1.9)
        return float(rng.triangular(low, mean, high))

    def sample_group_size(resource_key: str) -> int:
        if resource_key == "group_rooms":
            return int(rng.integers(2, 7))
        return 1

    def reject_immediately(resource_key: str, group_size: int) -> None:
        bucket = metrics[resource_key]
        bucket["rejected"] += 1
        bucket["rejected_people"] += group_size

    def student_process(student_id: int) -> simpy.events.Event:
        resource_key = choose_resource_type()
        group_size = sample_group_size(resource_key)
        bucket = metrics[resource_key]
        bucket["arrived_people"] += group_size
        resource = resources[resource_key]

        if resource is None:
            reject_immediately(resource_key, group_size)
            return

        arrival_time = env.now
        priority = 1
        if resource_key == "group_rooms" and reservation_enabled:
            has_reservation = rng.random() < reservation_share
            priority = 0 if has_reservation else 1

        # The timeout models a student's maximum willingness to wait.
        with _resource_request(resource, priority=priority) as request:
            bucket["max_queue_length"] = max(
                bucket["max_queue_length"], len(resource.queue)
            )
            result = yield request | env.timeout(max_wait_minutes)
            if request not in result:
                reject_immediately(resource_key, group_size)
                return

            waiting_time = env.now - arrival_time
            stay_duration = sample_stay_duration(resource_key)
            visible_usage = min(stay_duration, max(simulation_minutes - env.now, 0.0))

            bucket["served"] += 1
            bucket["served_people"] += group_size
            bucket["waiting_times"].append(waiting_time)
            bucket["usage_minutes"] += visible_usage

            yield env.timeout(stay_duration)

    def arrival_process() -> simpy.events.Event:
        if arrivals_per_hour <= 0:
            return

        mean_interarrival = 60.0 / arrivals_per_hour
        student_id = 0
        while True:
            yield env.timeout(float(rng.exponential(mean_interarrival)))
            if env.now > simulation_minutes:
                break
            student_id += 1
            env.process(student_process(student_id))

    def monitor_process() -> simpy.events.Event:
        while env.now <= simulation_minutes:
            timeline.append(make_timeline_row())
            yield env.timeout(sample_interval)

    env.process(arrival_process())
    env.process(monitor_process())
    env.run(until=simulation_minutes)

    if not timeline or timeline[-1]["time"] < simulation_minutes:
        timeline.append(make_timeline_row(simulation_minutes))

    summary, resource_results = finalize_results(metrics, capacities, simulation_minutes)
    return {
        "summary": summary,
        "resources": resource_results,
        "timeline": timeline,
        "config": {
            "scenario": config.get("name", config.get("key", "Szenario")),
            "simulation_minutes": simulation_minutes,
            "opening_minutes_per_day": simulation_minutes,
            "resources": capacities,
            "arrivals_per_hour": arrivals_per_hour,
            "mean_stay_minutes": mean_stay_minutes,
            "max_wait_minutes": max_wait_minutes,
            "reservation_enabled": reservation_enabled,
            "reservation_share": reservation_share,
            "seed": config.get("seed"),
            "resource_labels": RESOURCE_LABELS,
        },
    }


def _daily_row(day: int, day_results: list[dict[str, Any]]) -> dict[str, Any]:
    arrivals = [float(result["summary"]["total_arrivals"]) for result in day_results]
    served = [float(result["summary"]["total_served"]) for result in day_results]
    rejected = [float(result["summary"]["total_rejected"]) for result in day_results]
    rejection_rates = [float(result["summary"]["rejection_rate"]) for result in day_results]
    waiting_times = [float(result["summary"]["average_waiting_time"]) for result in day_results]
    max_queues = [
        max(float(resource["max_queue_length"]) for resource in result["resources"].values())
        for result in day_results
    ]

    row: dict[str, Any] = {
        "day": day,
        "arrivals": _clean_number(_mean(arrivals)),
        "served": _clean_number(_mean(served)),
        "rejected": _clean_number(_mean(rejected)),
        "rejection_rate": _clean_number(_mean(rejection_rates)),
        "average_waiting_time": _clean_number(_mean(waiting_times)),
        "maximum_queue_length": _clean_number(_mean(max_queues)),
        "resources": {},
    }
    for key in RESOURCE_KEYS:
        row["resources"][key] = {
            "served": _clean_number(_mean([float(result["resources"][key]["served"]) for result in day_results])),
            "rejected": _clean_number(_mean([float(result["resources"][key]["rejected"]) for result in day_results])),
            "utilization": _clean_number(_mean([float(result["resources"][key]["utilization"]) for result in day_results])),
            "max_queue_length": _clean_number(_mean([float(result["resources"][key]["max_queue_length"]) for result in day_results])),
        }
    return row


def _aggregate_timeline(all_day_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_time: dict[float, list[dict[str, Any]]] = {}
    for result in all_day_results:
        for row in result["timeline"]:
            by_time.setdefault(float(row["time"]), []).append(row)

    averaged: list[dict[str, Any]] = []
    for time_value in sorted(by_time):
        rows = by_time[time_value]
        average_row: dict[str, Any] = {"time": _clean_number(time_value)}
        for key in RESOURCE_KEYS:
            average_row[f"{key}_occupied"] = _clean_number(
                _mean([float(row[f"{key}_occupied"]) for row in rows])
            )
            average_row[f"{key}_queue"] = _clean_number(
                _mean([float(row[f"{key}_queue"]) for row in rows])
            )
        averaged.append(average_row)
    return averaged


def _aggregate_resources(replication_results: list[list[dict[str, Any]]]) -> dict[str, Any]:
    resources: dict[str, Any] = {}
    for key in RESOURCE_KEYS:
        served = []
        rejected = []
        arrived_people = []
        served_people = []
        rejected_people = []
        wait_totals = []
        wait_counts = []
        utilization_values = []
        max_queue_values = []

        for replication in replication_results:
            served.append(sum(float(day["resources"][key]["served"]) for day in replication))
            rejected.append(sum(float(day["resources"][key]["rejected"]) for day in replication))
            arrived_people.append(sum(float(day["resources"][key]["arrived_people"]) for day in replication))
            served_people.append(sum(float(day["resources"][key]["served_people"]) for day in replication))
            rejected_people.append(sum(float(day["resources"][key]["rejected_people"]) for day in replication))
            wait_totals.append(sum(float(day["resources"][key]["waiting_time_total"]) for day in replication))
            wait_counts.append(sum(float(day["resources"][key]["waiting_count"]) for day in replication))
            utilization_values.append(_mean([float(day["resources"][key]["utilization"]) for day in replication]))
            max_queue_values.append(max(float(day["resources"][key]["max_queue_length"]) for day in replication))

        mean_served = _mean(served)
        mean_rejected = _mean(rejected)
        mean_arrivals = mean_served + mean_rejected
        total_wait = sum(wait_totals)
        total_wait_count = sum(wait_counts)
        avg_wait = total_wait / total_wait_count if total_wait_count else 0.0
        resources[key] = {
            "label": RESOURCE_LABELS[key],
            "served": _clean_number(mean_served),
            "rejected": _clean_number(mean_rejected),
            "rejection_rate": _clean_number((mean_rejected / mean_arrivals * 100) if mean_arrivals else 0.0),
            "avg_waiting_time": _clean_number(avg_wait),
            "utilization": _clean_number(_mean(utilization_values)),
            "max_queue_length": _clean_number(_mean(max_queue_values)),
            "arrived_people": _clean_number(_mean(arrived_people)),
            "served_people": _clean_number(_mean(served_people)),
            "rejected_people": _clean_number(_mean(rejected_people)),
        }
    return resources


def run_exam_period(config: dict[str, Any]) -> dict[str, Any]:
    """Run separate opening days and aggregate an examination period."""
    exam_days = max(int(config.get("exam_days", 14)), 1)
    opening_minutes = _positive_float(
        config,
        "opening_minutes_per_day",
        _positive_float(config, "simulation_minutes", 480),
    )
    replications = max(int(config.get("replications", 30)), 1)
    base_seed = config.get("seed")
    if base_seed in ("", None):
        base_seed = None

    period_config = dict(config)
    period_config["opening_minutes_per_day"] = opening_minutes
    period_config["simulation_minutes"] = opening_minutes

    day_seeds = _spawn_day_seeds(base_seed, replications, exam_days)
    replication_results: list[list[dict[str, Any]]] = []
    all_day_results: list[dict[str, Any]] = []

    for replication_index in range(replications):
        days: list[dict[str, Any]] = []
        for day_index in range(exam_days):
            day_result = run_single_day(
                period_config,
                seed=day_seeds[replication_index][day_index],
            )
            days.append(day_result)
            all_day_results.append(day_result)
        replication_results.append(days)

    period_arrivals = [
        sum(float(day["summary"]["total_arrivals"]) for day in replication)
        for replication in replication_results
    ]
    period_served = [
        sum(float(day["summary"]["total_served"]) for day in replication)
        for replication in replication_results
    ]
    period_rejected = [
        sum(float(day["summary"]["total_rejected"]) for day in replication)
        for replication in replication_results
    ]
    period_wait_totals = [
        sum(float(day["summary"]["waiting_time_total"]) for day in replication)
        for replication in replication_results
    ]
    period_wait_counts = [
        sum(float(day["summary"]["waiting_count"]) for day in replication)
        for replication in replication_results
    ]
    period_rejection_rates = [
        (period_rejected[index] / period_arrivals[index] * 100) if period_arrivals[index] else 0.0
        for index in range(replications)
    ]
    period_average_waits = [
        (period_wait_totals[index] / period_wait_counts[index]) if period_wait_counts[index] else 0.0
        for index in range(replications)
    ]

    daily_results = [
        _daily_row(
            day_index + 1,
            [replication[day_index] for replication in replication_results],
        )
        for day_index in range(exam_days)
    ]
    busiest_day = max(daily_results, key=lambda row: row["arrivals"]) if daily_results else {"day": 0, "arrivals": 0}

    total_arrivals = _mean(period_arrivals)
    total_served = _mean(period_served)
    total_rejected = _mean(period_rejected)
    summary = {
        "exam_days": exam_days,
        "replications": replications,
        "opening_minutes_per_day": _clean_number(opening_minutes),
        "total_arrivals": _clean_number(total_arrivals),
        "total_served": _clean_number(total_served),
        "total_rejected": _clean_number(total_rejected),
        "rejection_rate": _clean_number(_mean(period_rejection_rates)),
        "average_waiting_time": _clean_number(_mean(period_average_waits)),
        "busiest_day": int(busiest_day["day"]),
        "busiest_day_arrivals": _clean_number(busiest_day["arrivals"]),
        "total_people": _clean_number(
            _mean([
                sum(float(day["summary"]["total_people"]) for day in replication)
                for replication in replication_results
            ])
        ),
        "statistics": {
            "total_arrivals": _stat_block(period_arrivals),
            "rejection_rate": _stat_block(period_rejection_rates),
            "average_waiting_time": _stat_block(period_average_waits),
        },
        "totals_meaning": (
            "Die Summen beschreiben eine durchschnittliche vollständige Prüfungsphase "
            "über alle Wiederholungen, nicht die Summe aller Wiederholungen."
        ),
    }
    resources = _aggregate_resources(replication_results)
    timeline = _aggregate_timeline(all_day_results)

    return {
        "summary": summary,
        "resources": resources,
        "daily_results": daily_results,
        "average_daily_timeline": timeline,
        "timeline": timeline,
        "interpretation": build_interpretation(summary, resources, period_config, daily_results),
        "config": {
            "scenario": period_config.get("name", period_config.get("key", "Szenario")),
            "exam_days": exam_days,
            "replications": replications,
            "simulation_minutes": opening_minutes,
            "opening_minutes_per_day": opening_minutes,
            "resources": {
                key: max(int(period_config.get("resources", {}).get(key, 0)), 0)
                for key in RESOURCE_KEYS
            },
            "arrivals_per_hour": _positive_float(period_config, "arrivals_per_hour", 32),
            "mean_stay_minutes": max(_positive_float(period_config, "mean_stay_minutes", 125), 0.1),
            "max_wait_minutes": _positive_float(period_config, "max_wait_minutes", 25),
            "reservation_enabled": bool(period_config.get("reservation_enabled", False)),
            "reservation_share": min(max(float(period_config.get("reservation_share", 0.0)), 0.0), 1.0),
            "seed": base_seed,
            "resource_labels": RESOURCE_LABELS,
        },
    }


def run_simulation(config: dict[str, Any]) -> dict[str, Any]:
    """Compatibility wrapper for the default web endpoint."""
    return run_exam_period(config)
