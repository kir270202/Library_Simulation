from __future__ import annotations

from typing import Any


RESOURCE_KEYS = ("study_seats", "pc_workstations", "group_rooms")

RESOURCE_LABELS = {
    "study_seats": "Einzelarbeitsplätze",
    "pc_workstations": "PC-Arbeitsplätze",
    "group_rooms": "Gruppenräume",
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


def build_interpretation(
    summary: dict[str, Any],
    resources: dict[str, Any],
    config: dict[str, Any],
) -> list[str]:
    """Create a short, human-readable interpretation for the current run."""
    if summary["total_arrivals"] == 0:
        return [
            "Es gab in diesem Lauf keine Ankünfte. Für aussagekräftige Ergebnisse sollte die Ankunftsrate erhöht werden.",
        ]

    bottleneck_key = max(
        RESOURCE_KEYS,
        key=lambda key: (
            resources[key]["rejected"],
            resources[key]["max_queue_length"],
            resources[key]["utilization"],
        ),
    )
    bottleneck = resources[bottleneck_key]
    rejection_rate = float(summary["rejection_rate"])
    interpretation: list[str] = []

    if (
        bottleneck["rejected"] > 0
        or bottleneck["max_queue_length"] > 0
        or bottleneck["utilization"] >= 85
    ):
        interpretation.append(
            "Hauptengpass ist wahrscheinlich "
            f"{bottleneck['label']}: {bottleneck['rejected']} Abweisungen, "
            f"maximale Warteschlange {bottleneck['max_queue_length']} und "
            f"{bottleneck['utilization']:.2f}% Auslastung."
        )
    else:
        interpretation.append(
            "Im aktuellen Lauf entsteht kein deutlicher Engpass; die Ressourcen wirken für diese Nachfrage ausreichend."
        )

    if rejection_rate >= 20:
        interpretation.append(
            f"Die Ablehnungsrate ist mit {rejection_rate:.2f}% hoch und deutet auf spürbare Kapazitätsprobleme hin."
        )
    elif rejection_rate >= 5:
        interpretation.append(
            f"Die Ablehnungsrate ist mit {rejection_rate:.2f}% merkbar, aber noch nicht extrem."
        )
    else:
        interpretation.append(
            f"Die Ablehnungsrate ist mit {rejection_rate:.2f}% niedrig."
        )

    if config.get("reservation_enabled"):
        interpretation.append(
            "Das Reservierungssystem ist als Priorität für Gruppenräume aktiv. Für die Bewertung sollte dieses Szenario mit der Prüfungsphase ohne Reservierung verglichen werden."
        )
    elif resources["group_rooms"]["rejected"] > 0 or resources["group_rooms"]["max_queue_length"] > 0:
        interpretation.append(
            "Bei Gruppenräumen könnte ein Reservierungssystem oder zusätzliche Kapazität geprüft werden."
        )

    if bottleneck["utilization"] >= 90:
        interpretation.append(
            "Sehr hohe Auslastung ist nicht automatisch gut, weil sie Warteschlangen und Ablehnungen begünstigen kann."
        )
    else:
        interpretation.append(
            f"Naheliegende Maßnahme: Kapazität und Nachfrageverteilung bei {bottleneck['label']} weiter beobachten."
        )

    return interpretation
