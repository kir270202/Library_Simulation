from __future__ import annotations

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


def run_simulation(config: dict[str, Any]) -> dict[str, Any]:
    """Run one simulated library day and return JSON-serializable metrics."""
    simulation_minutes = _positive_float(config, "simulation_minutes", 480)
    sample_interval = max(_positive_float(config, "sample_interval", 10), 1)
    arrivals_per_hour = _positive_float(config, "arrivals_per_hour", 32)
    mean_stay_minutes = max(_positive_float(config, "mean_stay_minutes", 125), 0.1)
    max_wait_minutes = _positive_float(config, "max_wait_minutes", 25)

    capacities = {
        key: max(int(config.get("resources", {}).get(key, 0)), 0) for key in RESOURCE_KEYS
    }
    probabilities = _normalize_probabilities(config.get("demand_probabilities", {}))
    rng = np.random.default_rng(config.get("seed"))
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
        "interpretation": build_interpretation(summary, resource_results, config),
        "config": {
            "scenario": config.get("name", config.get("key", "Szenario")),
            "simulation_minutes": simulation_minutes,
            "resources": capacities,
            "arrivals_per_hour": arrivals_per_hour,
            "mean_stay_minutes": mean_stay_minutes,
            "max_wait_minutes": max_wait_minutes,
            "reservation_enabled": reservation_enabled,
            "reservation_share": reservation_share,
            "resource_labels": RESOURCE_LABELS,
        },
    }
