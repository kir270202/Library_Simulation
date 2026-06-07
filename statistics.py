from __future__ import annotations

from typing import Any


RESOURCE_KEYS = ("study_seats", "pc_workstations", "group_rooms")

RESOURCE_LABELS = {
    "study_seats": "Einzelarbeitsplaetze",
    "pc_workstations": "PC-Arbeitsplaetze",
    "group_rooms": "Gruppenraeume",
}


def create_metric_buckets() -> dict[str, dict[str, Any]]:
    return {
        key: {
            "served": 0,
            "rejected": 0,
            "waiting_times": [],
            "usage_minutes": 0.0,
            "max_queue_length": 0,
            "arrived_people": 0,
            "served_people": 0,
            "rejected_people": 0,
        }
        for key in RESOURCE_KEYS
    }


def finalize_results(
    metrics: dict[str, dict[str, Any]],
    capacities: dict[str, int],
    simulation_minutes: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    resources: dict[str, Any] = {}
    total_arrivals = 0
    total_served = 0
    total_rejected = 0
    total_people = 0

    for key in RESOURCE_KEYS:
        bucket = metrics[key]
        served = int(bucket["served"])
        rejected = int(bucket["rejected"])
        total_arrivals += served + rejected
        total_served += served
        total_rejected += rejected
        total_people += int(bucket["arrived_people"])

        waiting_times = bucket["waiting_times"]
        avg_wait = sum(waiting_times) / len(waiting_times) if waiting_times else 0.0
        capacity = capacities.get(key, 0)
        if capacity > 0 and simulation_minutes > 0:
            utilization = bucket["usage_minutes"] / (capacity * simulation_minutes) * 100
        else:
            utilization = 0.0

        resources[key] = {
            "label": RESOURCE_LABELS[key],
            "served": served,
            "rejected": rejected,
            "avg_waiting_time": round(avg_wait, 2),
            "utilization": round(min(utilization, 100.0), 2),
            "max_queue_length": int(bucket["max_queue_length"]),
            "arrived_people": int(bucket["arrived_people"]),
            "served_people": int(bucket["served_people"]),
            "rejected_people": int(bucket["rejected_people"]),
        }

    rejection_rate = (total_rejected / total_arrivals * 100) if total_arrivals else 0.0
    summary = {
        "total_arrivals": total_arrivals,
        "total_served": total_served,
        "total_rejected": total_rejected,
        "rejection_rate": round(rejection_rate, 2),
        "total_people": total_people,
    }

    return summary, resources
